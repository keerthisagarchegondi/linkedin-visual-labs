"""Release ordering, failure states and artifact-bound user acceptance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from linkedin_visual_labs.common.media import write_generation_manifest
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    data,
    evaluation,
    forecasting,
    operations,
    presentation_evidence,
    release,
    rendering,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    DEFAULT_CONFIG_PATH,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import DataError, file_hash
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    PipelineContext,
    build_pipeline_context,
)


@pytest.fixture()
def context(tmp_path: Path) -> PipelineContext:
    original = build_pipeline_context()
    (tmp_path / "src/linkedin_visual_labs").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / DEFAULT_CONFIG_PATH).write_bytes(
        (original.paths.repository_root / DEFAULT_CONFIG_PATH).read_bytes()
    )
    return build_pipeline_context(repository_root=tmp_path)


@pytest.mark.parametrize(
    "failure",
    [None, "prepare", "forecast", "proof", "evaluate", "operations", "render", "acceptance"],
)
def test_run_all_order_and_fail_closed(
    context: PipelineContext,
    monkeypatch: pytest.MonkeyPatch,
    failure: str | None,
) -> None:
    calls: list[str] = []

    def action(name: str) -> Any:
        def perform(ctx: PipelineContext, *args: Any) -> Path | dict[str, str]:
            assert ctx is context
            calls.append(name)
            if name == failure:
                raise DataError("deliberate stage failure")
            if name == "evaluate":
                assert args == (ctx.paths.manifests / "forecast_validation.json",)
            if name == "proof":
                write_generation_manifest(
                    {"fresh": True}, ctx.paths.manifests / "forecast_validation.json"
                )
            if name == "render":
                write_generation_manifest(
                    {"artifacts": {}}, ctx.paths.manifests / "run_manifest.json"
                )
            if name == "acceptance":
                return {"result": "PASS"}
            return ctx.paths.manifests

        return perform

    for module, attr, name in (
        (data, "prepare_data", "prepare"),
        (forecasting, "run_forecast", "forecast"),
        (release, "validate_forecast_run", "proof"),
        (evaluation, "run_evaluation", "evaluate"),
        (operations, "run_operations", "operations"),
        (rendering, "render_outputs", "render"),
        (release, "manual_acceptance", "acceptance"),
    ):
        monkeypatch.setattr(module, attr, action(name))
    if failure:
        with pytest.raises(DataError, match="deliberate"):
            release.run_all(context)
    else:
        assert release.run_all(context) == context.paths.manifests / "run_manifest.json"
    sequence = ["prepare", "forecast", "proof", "evaluate", "operations", "render", "acceptance"]
    assert calls == (sequence[: sequence.index(failure) + 1] if failure else sequence)
    manifest = json.loads((context.paths.manifests / "run_manifest.json").read_text())
    assert manifest["complete"] is (failure is None)
    if failure:
        assert "failed_stage" in manifest and "readiness" not in manifest
    else:
        assert manifest["forecast_validation"] == {"fresh": True}
        assert manifest["manual_acceptance"]["result"] == "PASS"


@pytest.mark.parametrize("defect", [None, "changed", "missing", "unapproved"])
def test_manual_acceptance_requires_exact_reviewed_artifacts(
    context: PipelineContext,
    defect: str | None,
) -> None:
    names = [
        "reports/control_tower.html",
        "images/champion_model_map.png",
        "video/forecast_model_arena.mp4",
        "video/forecast_to_labor_optimizer.mp4",
    ]
    hashes = {}
    for name in names:
        path = context.resolve_output_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"hypothetical reviewed bytes")
        hashes[name] = file_hash(path)
    if defect == "changed":
        context.resolve_output_path(names[0]).write_bytes(b"unreviewed bytes")
    if defect == "missing":
        hashes.pop(names[0])
    record = (
        context.paths.repository_root
        / "docs/projects/p25_quick_commerce_control_tower/manual_acceptance.json"
    )
    record.parent.mkdir(parents=True)
    write_generation_manifest(
        {"result": "FAIL" if defect == "unapproved" else "PASS", "artifact_sha256": hashes}, record
    )
    if defect:
        with pytest.raises(DataError, match="acceptance"):
            release.manual_acceptance(context)
    else:
        assert release.manual_acceptance(context)["artifact_hash_match"] is True


@pytest.mark.parametrize("defect", ["determinism", "sql", "evaluation", "importance"])
def test_presentation_rejects_failed_provenance(context: PipelineContext, defect: str) -> None:
    context.paths.create()
    root = context.paths.data
    for name in (
        "predictions.parquet",
        "demand_daily.parquet",
        "champions.csv",
        "hist_gradient_boosting_importance.parquet",
    ):
        (root / name).write_bytes(b"never read as analytical values")
    predicted = file_hash(root / "predictions.parquet")
    daily = file_hash(root / "demand_daily.parquet")
    stages: dict[str, Any] = {
        "demand_daily": {"classification": "public_real_m5", "parquet_sha256": daily},
        "predictions": {"predictions_sha256": predicted, "interpretation_sha256": "wrong"},
        "evaluation": {
            "artifact_sha256": {},
            "predictions_sha256": predicted,
            "prepared_sha256": daily,
            "deterministic_evaluation_rerun": "PASS",
            "sql_python_reconciliation": "PASS",
        },
        "operations": {
            "artifact_sha256": {},
            "complete": True,
            "actuals_used_for_allocation": False,
            "deterministic_rerun": "PASS",
            "configuration": context.configuration.model_dump(mode="json"),
            "predictions_sha256": predicted,
            "champions_sha256": file_hash(root / "champions.csv"),
        },
    }
    if defect == "determinism":
        stages["operations"]["deterministic_rerun"] = "FAIL"
    elif defect == "sql":
        stages["evaluation"]["sql_python_reconciliation"] = "FAIL"
    elif defect == "evaluation":
        stages["evaluation"]["deterministic_evaluation_rerun"] = "FAIL"
    for name in ("demand_daily", "predictions", "evaluation"):
        write_generation_manifest(stages[name], root / f"{name}.metadata.json")
    stages["operations"]["evaluation_sha256"] = file_hash(root / "evaluation.metadata.json")
    write_generation_manifest(stages["operations"], root / "operations.metadata.json")
    with pytest.raises(
        ValueError, match="interpretation" if defect == "importance" else "provenance"
    ):
        presentation_evidence.load_evidence(context)
