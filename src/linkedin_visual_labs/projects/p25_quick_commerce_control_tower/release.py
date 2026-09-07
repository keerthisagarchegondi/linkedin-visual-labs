"""Real-data release orchestration and fresh, hash-bound validation evidence."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd

from linkedin_visual_labs.common.media import write_generation_manifest
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    data,
    evaluation,
    forecasting,
    operations,
    rendering,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext


def validate_forecast_run(context: PipelineContext) -> Path:
    """Refit after adversarial holdout mutation; only matching actual labels may change."""
    daily_path = context.paths.data / "demand_daily.parquet"
    prediction_path = context.paths.data / "predictions.parquet"
    daily = pd.read_parquet(daily_path)
    data.validate_daily(daily)
    split = data.common_holdout(daily)
    if (
        len(daily) != 38820
        or daily["date"].nunique() != 1941
        or not daily["data_classification"].eq("public_real_m5").all()
    ):
        raise data.DataError("Release requires the complete real M5 scope")
    original = pd.read_parquet(prediction_path)
    changed = daily.copy()
    changed.loc[changed["date"] > split.origin, "demand"] += 1_000_000
    first_inputs = forecasting.make_inputs(daily, context.configuration)
    changed_inputs = forecasting.make_inputs(changed, context.configuration)
    for field in ("history", "training", "future"):
        pd.testing.assert_frame_equal(getattr(first_inputs, field), getattr(changed_inputs, field))
    pd.testing.assert_series_equal(first_inputs.training_target, changed_inputs.training_target)
    repeated = forecasting.forecast_arena(changed, context.configuration)
    pd.testing.assert_frame_equal(
        original.drop(columns="actual_units"),
        repeated.predictions.drop(columns="actual_units"),
        check_exact=True,
    )
    np.testing.assert_array_equal(
        original["actual_units"] + 1_000_000, repeated.predictions["actual_units"]
    )
    statuses = pd.read_parquet(context.paths.data / "model_status.parquet")
    variable = ["training_seconds", "prediction_seconds"]
    pd.testing.assert_frame_equal(
        statuses.drop(columns=variable), repeated.statuses.drop(columns=variable), check_exact=True
    )
    pd.testing.assert_frame_equal(
        pd.read_parquet(context.paths.data / "hist_gradient_boosting_importance.parquet"),
        repeated.interpretation,
        check_exact=True,
    )
    if statuses["prediction_count"].sum() != 2240 or statuses["fallback_used"].any():
        raise data.DataError("Model status does not reconcile with canonical forecasts")
    np.testing.assert_array_equal(
        original["forecast_units"], original["raw_forecast_units"].clip(lower=0)
    )
    np.testing.assert_array_equal(original["was_clipped"], original["raw_forecast_units"] < 0)
    if statuses["clipping_count"].sum() != original["was_clipped"].sum():
        raise data.DataError("Clipping status does not reconcile")
    path = context.paths.manifests / "forecast_validation.json"
    write_generation_manifest(
        {
            "classification": "public_real_m5",
            "prepared_sha256": data.file_hash(daily_path),
            "predictions_sha256": data.file_hash(prediction_path),
            "configuration": context.configuration.model_dump(mode="json"),
            "real_mutation_rerun": "PASS",
            "max_raw_difference": 0.0,
            "predictor_mutation": "PASS",
            "status_and_clipping_reconciliation": "PASS",
            "rows": len(original),
            "origin": str(split.origin.date()),
            "holdout_rows": len(split.holdout),
        },
        path,
    )
    return path


def manual_acceptance(context: PipelineContext) -> dict[str, Any]:
    """Carry user acceptance only when every reviewed artifact is still byte-identical."""
    record = context.paths.repository_root / (
        "docs/projects/p25_quick_commerce_control_tower/manual_acceptance.json"
    )
    payload: dict[str, Any] = json.loads(record.read_text(encoding="utf-8"))
    expected_paths = {
        "reports/control_tower.html",
        "images/champion_model_map.png",
        "video/forecast_model_arena.mp4",
        "video/forecast_to_labor_optimizer.mp4",
    }
    if payload.get("result") != "PASS" or set(payload["artifact_sha256"]) != expected_paths:
        raise data.DataError("Manual acceptance record is incomplete")
    for name, expected in payload["artifact_sha256"].items():
        if data.file_hash(context.resolve_output_path(name)) != expected:
            raise data.DataError(
                f"Reviewed artifact changed; fresh manual acceptance needed: {name}"
            )
    return {**payload, "record_sha256": data.file_hash(record), "artifact_hash_match": True}


def run_all(context: PipelineContext) -> Path:
    """Run approved real stages in order; stop on defects without fixture fallback."""
    context.paths.create()
    manifest_path = context.paths.manifests / "run_manifest.json"
    state: dict[str, Any] = {"complete": False, "workflow": "run-all", "completed_stages": []}
    write_generation_manifest(state, manifest_path)
    timings: dict[str, float] = {}
    stage = "preparation"
    try:
        tick = perf_counter()
        data.prepare_data(context)  # Validates/reuses pinned real cache; no implicit fixture.
        timings[stage] = perf_counter() - tick
        state["completed_stages"].append(stage)
        for stage, action in (
            ("forecasting", forecasting.run_forecast),
            ("leakage_validation", validate_forecast_run),
        ):
            tick = perf_counter()
            action(context)
            timings[stage] = perf_counter() - tick
            state["completed_stages"].append(stage)
        stage = "evaluation_and_diagnostics"
        tick = perf_counter()
        proof = context.paths.manifests / "forecast_validation.json"
        evaluation.run_evaluation(context, proof)
        timings[stage] = perf_counter() - tick
        state["completed_stages"].append(stage)
        for stage, action in (
            ("operations_scenarios_inventory", operations.run_operations),
            ("presentation_and_validation", rendering.render_outputs),
        ):
            tick = perf_counter()
            action(context)
            timings[stage] = perf_counter() - tick
            state["completed_stages"].append(stage)
        stage = "manual_acceptance_integrity"
        acceptance = manual_acceptance(context)
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(
            complete=True,
            workflow="run-all",
            completed_stages=[*state["completed_stages"], stage],
            pipeline_runtimes_seconds=timings,
            forecast_validation=json.loads(proof.read_text(encoding="utf-8")),
            manual_acceptance=acceptance,
            validation_status="automated_artifacts_passed_user_manual_acceptance_preserved",
            readiness="STEP 7 PIPELINE VALIDATED; REPOSITORY GATES REVIEW REQUIRED",
        )
        write_generation_manifest(manifest, manifest_path)
    except Exception as exc:
        state.update(failed_stage=stage, error=f"{type(exc).__name__}: {exc}")
        write_generation_manifest(state, manifest_path)
        raise
    return manifest_path
