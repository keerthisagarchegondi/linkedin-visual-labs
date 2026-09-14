"""Aggregate-only analytical evidence freeze and diagnostic charts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .block2 import write_json
from .detection import checksum
from .validation import verify_claim


def artifact(root: Path, path: Path) -> dict[str, Any]:
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("foreign evidence path")
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": checksum(path),
        "bytes": path.stat().st_size,
    }


def verify_index(root: Path, index: dict[str, Any]) -> None:
    for item in index["artifacts"].values():
        path = root / item["path"]
        if not path.resolve().is_relative_to(root.resolve()) or checksum(path) != item["sha256"]:
            raise ValueError("evidence hash/path mismatch")


def create_release(root: Path, output: Path, configuration: dict[str, Any]) -> dict[str, Any]:
    data = output / "data"
    metrics = pd.read_parquet(data / "operational_metrics.parquet")
    baseline = json.loads((data / "baseline_summary.json").read_text(encoding="utf-8"))
    warning = json.loads((data / "warning_summary.json").read_text(encoding="utf-8"))
    validation = json.loads((data / "validation_results.json").read_text(encoding="utf-8"))
    recommendation = json.loads((data / "recommendation.json").read_text(encoding="utf-8"))
    quality = json.loads((data / "metric_quality_summary.json").read_text(encoding="utf-8"))
    if validation["status"] != "PASS":
        raise ValueError("validation gate failed")
    degraded = metrics[(metrics.timestamp >= 1440) & (metrics.timestamp < 1650)]
    changes: dict[str, Any] = {}
    for name, stats in baseline["statistics"].items():
        values = degraded[name].dropna()
        value = None if values.empty else float(values.median())
        ref = stats["median"]
        changes[name] = {
            "baseline_median": ref,
            "screened_interval_median": value,
            "sample_size": len(values),
            "relative_change": None
            if value is None or ref is None or ref == 0
            else (value - ref) / abs(ref),
        }
    wt = pd.read_parquet(data / "warning_timeline.parquet")
    active = wt.state.isin(["WARNING", "CRITICAL"]) & (
        wt.timestamp >= configuration["evaluation_start"]
    )
    unmatched = {
        "warning_episodes_without_qualifying_queue": int(
            (active & ~active.shift(fill_value=False)).sum()
        )
        if warning["visible_queue_timestamp"] is None
        else None,
        "warning_state_seconds": int(active.sum()),
        "caveat": (
            "No target outcome qualified; an unmatched warning is not demonstrated early warning. "
            "Ground-truth false-positive accuracy remains unknown."
        ),
    }
    claims: list[dict[str, Any]] = []

    def claim(
        identity: str, text: str, classification: str, file: str, calculation: str, unit: str
    ) -> None:
        path = data / file
        record = {
            "claim_id": identity,
            "claim_text": text,
            "classification": classification,
            "evidence_path": path.relative_to(root).as_posix(),
            "evidence_sha256": checksum(path),
            "calculation": calculation,
            "unit": unit,
            "caveat": (
                "Configured, model-derived analysis; no independent accuracy or physical "
                "queue-absence claim. Aggregate content approval does not authorize source imagery."
            ),
            "approved_for_publication": True,
            "reviewer_status": "APPROVED",
            "approval_scope": "AGGREGATE_ANALYTICAL_CONTENT_ONLY",
            "last_validated_step": 11,
        }
        verify_claim(record)
        claims.append(record)

    claim(
        "P6-B3-01",
        f"The configured warning first qualified at {warning['warning_timestamp']} source seconds."
        if warning["warning_timestamp"] is not None
        else "No warning satisfied full persistence.",
        "DERIVED",
        "warning_summary.json",
        "First full warning persistence completion after baseline",
        "source seconds",
    )
    claim(
        "P6-B3-02",
        (
            f"Result: {warning['result_classification']}; "
            "qualifying queue onset and lead time are unavailable."
        )
        if warning["visible_queue_timestamp"] is None
        else f"Signed configured lead time: {warning['lead_time_seconds']} seconds.",
        "DERIVED",
        "warning_summary.json",
        "Independent queue outcome and signed onset arithmetic",
        "classification; seconds or null",
    )
    claim(
        "P6-B3-03",
        (
            f"Baseline warning exposure: {warning['baseline_false_warning']['warning_seconds']} "
            f"of {warning['baseline_false_warning']['evaluable_seconds']} evaluable seconds."
        ),
        "DERIVED",
        "warning_summary.json",
        "In-sample exposure with frozen rule",
        "seconds",
    )
    claim(
        "P6-B3-04",
        (
            f"Completed dwell uses {quality['completed_dwell_samples']} eligible journeys; "
            "incomplete journeys are excluded."
        ),
        "DERIVED",
        "metric_quality_summary.json",
        "Reconciled complete gap-free crossing pairs",
        "journeys",
    )
    claim(
        "P6-B3-05",
        recommendation["wording"],
        "ILLUSTRATIVE_RECOMMENDATION",
        "recommendation.json",
        "Enabled prototype review action linked to actual warning drivers",
        "conditional action",
    )
    claim(
        "P6-B3-06",
        (
            "Operational comparisons use an explicit 60-second fast-track window; "
            "the formal window remains 300 seconds."
        ),
        "CONFIGURED_ASSUMPTION",
        "baseline_summary.json",
        "Baseline interval duration and declared window policy",
        "seconds",
    )
    caveats = [
        "Only 1380-1800s is the post-baseline evaluation interval.",
        "The 120s baseline is limited; overlapping windows are not independent.",
        "Baseline dwell unavailable: fewer than 3 complete samples per operational window.",
        "Fragmentation and geometric overlap can contaminate counts; no accuracy claim.",
        "Zero qualifying queue evidence does not prove absence of a physically visible queue.",
        "Signal-cycle duration unmeasured; 120s persistence is a configured transient filter.",
        "No causal impact, production deployment or live-monitoring claim.",
    ]
    release = {
        "schema_version": "1.0",
        "analytical_status": "RECOMPUTATION_VERIFIED",
        "repository_gates": "PENDING_FINAL_FULL_RUN",
        "project": "Project 6 — Traffic Operations Early-Warning System",
        "result": warning,
        "baseline": baseline,
        "screened_comparison_interval": [1440, 1650],
        "metric_changes": changes,
        "eligibility": quality,
        "unmatched_warning": unmatched,
        "recommendation": recommendation,
        "claims": claims,
        "limitations": caveats,
        "publication": {
            "aggregate_analytical_content_approved": True,
            "raw_footage_approved": False,
            "source_excerpts_approved": False,
            "transformed_source_imagery_approved": False,
            "final_artifact_release_approved": False,
        },
        "evidence_index": "data/evidence_index.json",
        "only_analytical_source_for_final_rendering": True,
    }
    write_json(data / "claim_register.json", {"claims": claims})
    write_json(data / "release_data.json", release)
    paths = [
        "operational_metrics.parquet",
        "baseline_summary.json",
        "metric_quality_summary.json",
        "warning_timeline.parquet",
        "queue_outcome_timeline.parquet",
        "warning_summary.json",
        "sensitivity_results.parquet",
        "recommendation.json",
        "validation_results.json",
        "claim_register.json",
        "release_data.json",
    ]
    index = {
        "schema_version": "1.0",
        "artifacts": {name: artifact(root, data / name) for name in paths},
        "public_source_imagery_approved": False,
    }
    verify_index(root, index)
    write_json(data / "evidence_index.json", index)
    return release


def diagnostic_charts(output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = output / "data"
    metrics = pd.read_parquet(data / "operational_metrics.parquet")
    warnings = pd.read_parquet(data / "warning_timeline.parquet")
    queue = pd.read_parquet(data / "queue_outcome_timeline.parquet")
    figure, axes = plt.subplots(4, 1, figsize=(12, 9), sharex=True, layout="constrained")
    for axis, column, label in zip(
        axes,
        ["density_window_mean", "throughput", "movement_index", "queue_count"],
        [
            "Mean zone vehicles /60s",
            "Eligible exits /60s",
            "Image diagonals /second",
            "Low-motion queue vehicles",
        ],
        strict=True,
    ):
        axis.plot(metrics.timestamp, metrics[column], linewidth=1)
        axis.set_ylabel(label)
        axis.axvspan(1260, 1380, color="green", alpha=0.12)
        axis.grid(alpha=0.2)
    axes[-1].set_xlabel("Original source seconds")
    figure.suptitle("Internal metric diagnostics | shaded candidate baseline | no accuracy claim")
    figure.savefig(output / "images/metric_trends.png", dpi=110)
    plt.close(figure)
    figure, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True, layout="constrained")
    codes = {"NORMAL": 0, "WATCH": 1, "WARNING": 2, "CRITICAL": 3}
    axes[0].step(warnings.timestamp, warnings.state.map(codes), where="post")
    axes[0].set_yticks([0, 1, 2, 3], list(codes))
    axes[0].set_ylabel("Warning state")
    axes[1].step(
        queue.timestamp, queue.visible_queue.astype(int), where="post", label="Qualified outcome"
    )
    axes[1].set_ylim(-0.1, 1.1)
    axes[1].set_ylabel("Configured queue outcome")
    axes[1].set_xlabel("Original source seconds")
    axes[1].set_xlim(1260, 1800)
    figure.suptitle("Internal outcome / warning audit | null queue onset implies null lead time")
    figure.savefig(output / "images/warning_queue_timeline.png", dpi=110)
    plt.close(figure)
