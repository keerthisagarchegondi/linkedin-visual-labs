"""Research-figure rendering from frozen Project 7 Step 5 evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import matplotlib
import numpy as np

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.figure import Figure

CANVAS_DPI: Final = 144
EXPECTED_STEP5_FINGERPRINT: Final = (
    "7954203abe1cb0f5457c3658f2105cd16a0800528e81723ee970d259afe60ed0"
)

FIGURE_FILES: Final[tuple[str, ...]] = (
    "audit_pipeline.png",
    "business_targeting_distortion.png",
    "calibration_comparison.png",
    "feature_availability_contract.png",
    "leakage_inflation_map.png",
    "model_performance_comparison.png",
    "split_integrity_comparison.png",
)


def _load_json(path: Path) -> dict[str, Any]:
    payload: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise TypeError(f"{path.name} is not a JSON object.")

    return payload


def load_release_context(
    assets_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load only frozen Step 5 public evidence."""

    release = _load_json(assets_root / "release_data.json")

    claims = _load_json(assets_root / "claim_register.json")

    if release.get("step5_fingerprint_sha256") != EXPECTED_STEP5_FINGERPRINT:
        raise RuntimeError("Step 5 release fingerprint drift.")

    if release.get("release_status") != "PASS":
        raise RuntimeError("Step 5 release is not PASS.")

    return release, claims


def _save(
    fig: Figure,
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        path,
        dpi=CANVAS_DPI,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    if not path.is_file() or path.stat().st_size < 10_000:
        raise RuntimeError(f"Figure render failed: {path.name}")


def _baseline_lookup(
    release: dict[str, Any],
    pipeline_id: str,
    partition: str,
) -> list[dict[str, Any]]:
    """Return exactly two baseline model rows.

    Frozen Step 5 baseline partitions use ``test`` and
    ``validation``. ``chronological_test`` is a semantic
    visualization request and resolves deterministically to the
    frozen ``test`` partition without modifying release evidence.
    """

    rows = release["baseline_model_results"]

    if not isinstance(
        rows,
        list,
    ):
        raise RuntimeError("baseline_model_results missing.")

    resolved_partition = "test" if partition == "chronological_test" else partition

    matches = [
        row
        for row in rows
        if (
            isinstance(
                row,
                dict,
            )
            and row.get("pipeline_id") == pipeline_id
            and row.get("partition") == resolved_partition
        )
    ]

    if not matches:
        raise RuntimeError(f"No baseline rows for {pipeline_id}/{resolved_partition}.")

    if len(matches) != 2:
        raise RuntimeError(
            f"Expected exactly two model rows for "
            f"{pipeline_id}/{resolved_partition}; "
            f"found {len(matches)}."
        )

    model_ids = {str(row.get("model_id")) for row in matches}

    expected_models = {
        "logistic_regression",
        "histogram_gradient_boosting",
    }

    if model_ids != expected_models:
        raise RuntimeError(f"Unexpected baseline models: {sorted(model_ids)}")

    return sorted(
        matches,
        key=lambda row: str(row["model_id"]),
    )


def render_audit_pipeline(
    release: dict[str, Any],
    output: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.7))

    labels = (
        "Feature\navailability",
        "Temporal\nsplit",
        "Transformation\nboundary",
        "Duplicate\noverlap",
        "Calibration\nstability",
        "Release\ngate",
    )

    x = np.arange(len(labels))

    ax.plot(
        x,
        np.zeros_like(x),
        marker="o",
        linewidth=2.5,
        markersize=10,
    )

    for index, label in enumerate(labels):
        ax.text(
            index,
            0.08,
            label,
            ha="center",
            va="bottom",
            fontsize=12,
            weight="bold",
        )

    ax.text(
        len(labels) - 1,
        -0.11,
        str(release["safe_release_decision"]),
        ha="center",
        fontsize=18,
        weight="bold",
    )

    ax.set_ylim(-0.25, 0.35)
    ax.set_xlim(-0.4, len(labels) - 0.6)
    ax.axis("off")

    ax.set_title(
        "Prediction-Time Integrity Audit Pipeline",
        fontsize=20,
        weight="bold",
    )

    _save(fig, output)


def render_business_targeting_distortion(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release["leakage_model_results"]

    if not isinstance(rows, list):
        raise RuntimeError("leakage_model_results missing.")

    s1 = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("case_id") == "S1_CURRENT_CALL_DURATION"
    ]

    labels = [str(row["model_id"]).replace("_", "\n") for row in s1]

    values = [float(row["campaign_yield_overstatement"]) for row in s1]

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.bar(labels, values)

    ax.axhline(0, linewidth=1)

    ax.set_ylabel("Overstated conversions / 1,000 ranked calls")

    ax.set_title(
        "Business Targeting Distortion from Current-Call Duration",
        fontsize=18,
        weight="bold",
    )

    for index, value in enumerate(values):
        ax.text(
            index,
            value,
            f"{value:.1f}",
            ha="center",
            va="bottom",
            fontsize=11,
        )

    _save(fig, output)


def render_calibration_comparison(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release["leakage_model_results"]

    if not isinstance(rows, list):
        raise RuntimeError("leakage_model_results missing.")

    s1 = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("case_id") == "S1_CURRENT_CALL_DURATION"
    ]

    labels = [str(row["model_id"]).replace("_", "\n") for row in s1]

    safe = [float(row["safe_expected_calibration_error"]) for row in s1]

    leaked = [float(row["leaked_expected_calibration_error"]) for row in s1]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.bar(x - width / 2, safe, width, label="Safe")
    ax.bar(x + width / 2, leaked, width, label="Leaked")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Expected calibration error")
    ax.legend()

    ax.set_title(
        "Calibration Error: Safe vs Leaked Evaluation",
        fontsize=18,
        weight="bold",
    )

    _save(fig, output)


def render_feature_availability_contract(
    output: Path,
) -> None:
    features = (
        ("Age / job / education", "Pre-decision", "Allowed"),
        ("Previous campaign context", "Pre-decision", "Allowed"),
        ("Campaign", "Unknown", "Blocked"),
        ("Duration", "During action", "Blocked"),
        ("Outcome confirmation proxy", "Post outcome", "Blocked"),
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.axis("off")

    table = ax.table(
        cellText=features,
        colLabels=(
            "Feature group",
            "Availability",
            "Prediction-time status",
        ),
        loc="center",
        cellLoc="left",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2)

    ax.set_title(
        "Prediction-Time Feature Availability Contract",
        fontsize=19,
        weight="bold",
        pad=24,
    )

    _save(fig, output)


def render_leakage_inflation_map(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release["leakage_inflation"]

    if not isinstance(rows, list):
        raise RuntimeError("leakage_inflation missing.")

    selected = [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("metric")
        in {
            "roc_auc",
            "pr_auc",
            "conversions_per_1000",
        }
    ]

    cases = sorted({str(row["case_id"]) for row in selected})

    metrics = (
        "roc_auc",
        "pr_auc",
        "conversions_per_1000",
    )

    matrix = np.zeros(
        (
            len(cases),
            len(metrics),
        )
    )

    for row in selected:
        case_index = cases.index(str(row["case_id"]))

        metric_index = metrics.index(str(row["metric"]))

        matrix[
            case_index,
            metric_index,
        ] = max(
            matrix[
                case_index,
                metric_index,
            ],
            float(row["leakage_inflation"]),
        )

    fig, ax = plt.subplots(figsize=(10, 6.5))

    image = ax.imshow(
        matrix,
        aspect="auto",
    )

    ax.set_yticks(np.arange(len(cases)))
    ax.set_yticklabels(
        [case.replace("S", "S", 1).replace("_", " ") for case in cases],
        fontsize=9,
    )

    ax.set_xticks(np.arange(len(metrics)))
    ax.set_xticklabels(
        (
            "ROC AUC",
            "PR AUC",
            "Conversions / 1,000",
        )
    )

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                f"{matrix[i, j]:.3f}",
                ha="center",
                va="center",
                fontsize=9,
            )

    fig.colorbar(
        image,
        ax=ax,
        label="Direction-normalized leakage inflation",
    )

    ax.set_title(
        "Leakage Inflation Across Integrity Scenarios",
        fontsize=18,
        weight="bold",
    )

    _save(fig, output)


def render_model_performance_comparison(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = _baseline_lookup(
        release,
        "C_PREDICTION_TIME_SAFE",
        "chronological_test",
    )

    labels = [str(row["model_id"]).replace("_", "\n") for row in rows]

    roc = [float(row["roc_auc"]) for row in rows]

    pr = [float(row["pr_auc"]) for row in rows]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.bar(x - width / 2, roc, width, label="ROC AUC")
    ax.bar(x + width / 2, pr, width, label="PR AUC")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.legend()

    ax.set_title(
        "Prediction-Time-Safe Model Performance",
        fontsize=18,
        weight="bold",
    )

    _save(fig, output)


def render_split_integrity_comparison(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release["leakage_model_results"]

    if not isinstance(rows, list):
        raise RuntimeError("leakage_model_results missing.")

    s2 = [
        row
        for row in rows
        if isinstance(row, dict) and row.get("case_id") == "S2_RANDOM_TEMPORAL_MIXING"
    ]

    labels = [str(row["model_id"]).replace("_", "\n") for row in s2]

    random_roc = [float(row["leaked_roc_auc"]) for row in s2]

    chronological_roc = [float(row["safe_roc_auc"]) for row in s2]

    x = np.arange(len(labels))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.bar(
        x - width / 2,
        chronological_roc,
        width,
        label="Chronological",
    )

    ax.bar(
        x + width / 2,
        random_roc,
        width,
        label="Random",
    )

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_ylabel("ROC AUC")
    ax.legend()

    ax.set_title(
        "Random vs Chronological Evaluation",
        fontsize=18,
        weight="bold",
    )

    _save(fig, output)


def render_all_figures(
    assets_root: Path,
) -> tuple[Path, ...]:
    """Render every required Step 6 research figure."""

    release, _ = load_release_context(assets_root)

    images = assets_root / "images"

    outputs = (
        images / "audit_pipeline.png",
        images / "business_targeting_distortion.png",
        images / "calibration_comparison.png",
        images / "feature_availability_contract.png",
        images / "leakage_inflation_map.png",
        images / "model_performance_comparison.png",
        images / "split_integrity_comparison.png",
    )

    render_audit_pipeline(
        release,
        outputs[0],
    )

    render_business_targeting_distortion(
        release,
        outputs[1],
    )

    render_calibration_comparison(
        release,
        outputs[2],
    )

    render_feature_availability_contract(
        outputs[3],
    )

    render_leakage_inflation_map(
        release,
        outputs[4],
    )

    render_model_performance_comparison(
        release,
        outputs[5],
    )

    render_split_integrity_comparison(
        release,
        outputs[6],
    )

    return outputs
