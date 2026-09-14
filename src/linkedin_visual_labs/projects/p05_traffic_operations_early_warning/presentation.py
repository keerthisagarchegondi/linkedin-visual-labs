"""Fail-closed, source-pixel-free presentation inputs for Steps 12--14."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .detection import checksum
from .evidence import artifact, verify_index
from .validation import verify_claim

TITLE = "Ten minutes of traffic in one frame"
TABS = ("Dashboard", "Video", "Method", "Results", "About")
KEYFRAMES = (0, 150, 300, 450, 600, 750, 900, 1050, 1200, 1349)
RIGHTS = (
    "AI City Challenge 2021 Track 1 | Internal academic analysis. "
    "Source imagery redistribution is not approved. These visuals contain no source pixels."
)


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected an evidence object")
    return value


def clock(value: float | None) -> str:
    if value is None:
        return "Not reportable"
    return f"{int(value) // 60:02d}:{int(value) % 60:02d}"


def validate_release(release: dict[str, Any]) -> None:
    if release.get("analytical_status") != "VERIFIED" or release.get("repository_gates") != "PASS":
        raise ValueError("Release evidence is not verified")
    if not release["publication"]["aggregate_analytical_content_approved"]:
        raise ValueError("Aggregate content is not approved")
    if not release.get("claims"):
        raise ValueError("Missing approved claims")
    for claim in release["claims"]:
        verify_claim(claim)
        if not claim["approved_for_publication"] or claim["reviewer_status"] != "APPROVED":
            raise ValueError("Unapproved claim")
    result = release["result"]
    if result["result_classification"] != "NO_VISIBLE_QUEUE_EVENT":
        raise ValueError("This editorial treatment requires a new review for another result")
    if result["visible_queue_timestamp"] is not None or result["lead_time_seconds"] is not None:
        raise ValueError("Inconsistent absent-outcome result")
    if result["warning_timestamp"] is None:
        raise ValueError("Warning story requires a qualified warning")


def checked_path(root: Path, item: dict[str, Any]) -> Path:
    path = root / str(item["path"])
    if not path.resolve().is_relative_to(root.resolve()) or checksum(path) != item["sha256"]:
        raise ValueError("Stale or foreign presentation evidence")
    return path


def normalize_coordinates(frame: pd.DataFrame, width: int, height: int) -> pd.DataFrame:
    if width <= 0 or height <= 0:
        raise ValueError("Invalid source dimensions")
    normalized = frame.copy()
    normalized["reference_x"] = normalized.reference_x / width
    normalized["reference_y"] = normalized.reference_y / height
    if (
        not normalized[["reference_x", "reference_y"]]
        .apply(lambda column: column.between(0, 1).all())
        .all()
    ):
        raise ValueError("Trajectory coordinates outside original image")
    return normalized


@dataclass(frozen=True)
class Presentation:
    """Only verified tabular/JSON inputs; no decoder or source-image interface."""

    root: Path
    output: Path
    release: dict[str, Any]
    geometry: dict[str, Any]
    trajectories: pd.DataFrame
    journeys: pd.DataFrame
    metrics: pd.DataFrame
    rules: dict[str, Any]
    sensitivity: pd.DataFrame
    index: dict[str, Any]

    @property
    def warning(self) -> str:
        return clock(self.release["result"]["warning_timestamp"])

    @property
    def counts(self) -> dict[str, Any]:
        return dict(self.release["eligibility"])

    def summary(self) -> dict[str, Any]:
        return {
            "result": self.release["result"],
            "metric_changes": self.release["metric_changes"],
            "eligibility": self.counts,
            "recommendation": self.release["recommendation"],
            "baseline": self.release["baseline"],
            "comparison_interval": self.release["screened_comparison_interval"],
            "unmatched_warning": self.release["unmatched_warning"],
            "sensitivity_warning_range": [
                float(self.sensitivity.warning_timestamp.min()),
                float(self.sensitivity.warning_timestamp.max()),
            ],
            "static_interval": [1200, 1800],
            "counts_scope": "Full 0-1800 second episode; not the ten-minute interval",
            "rights": RIGHTS,
            "source_pixels": False,
            "release_ready": False,
        }


def load_presentation(root: Path) -> Presentation:
    output = root / "outputs/p05_traffic_operations_early_warning"
    data = output / "data"
    index = read_object(data / "evidence_index.json")
    verify_index(root, index)
    release = read_object(checked_path(root, index["artifacts"]["release_data.json"]))
    validate_release(release)
    for claim in release["claims"]:
        checked_path(root, {"path": claim["evidence_path"], "sha256": claim["evidence_sha256"]})
    state = read_object(root / "docs/projects/p05_traffic_operations_early_warning/STATE.json")
    checked_path(root, state["block_3_validation"]["release_data"])
    checked_path(root, state["block_3_validation"]["evidence"])
    manifest = read_object(output / "manifests/validation_manifest.json")
    for item in manifest["outputs"]:
        checked_path(root, item)
    upstream = read_object(checked_path(root, manifest["upstream"]))
    if upstream["status"] != "PASS" or not all(upstream["summary"]["checks"].values()):
        raise ValueError("Unreconciled trajectories")
    derived = dict(index["artifacts"])
    warning_manifest = read_object(checked_path(root, manifest["warning_manifest"]))
    metrics_manifest = read_object(checked_path(root, warning_manifest["metrics_manifest"]))
    for reviewed in (warning_manifest, metrics_manifest):
        image_path = checked_path(root, reviewed["diagnostic_image"])
        derived[image_path.name] = artifact(root, image_path)
    for item in upstream["outputs"]:
        path = checked_path(root, item)
        derived[path.name] = item
    geometry_path = checked_path(root, upstream["geometry"])
    source_path = checked_path(root, upstream["source_manifest"])
    source_metadata = read_object(source_path)["admission"]["metadata"]
    rules_path = checked_path(root, manifest["configuration"])
    derived["calibration.json"] = artifact(root, geometry_path)
    derived["source_manifest.json"] = artifact(root, source_path)
    derived["block3.json"] = artifact(root, rules_path)
    derived["frozen_evidence_index.json"] = artifact(root, data / "evidence_index.json")
    trajectories = pd.read_parquet(checked_path(root, derived["trajectories.parquet"]))
    trajectories = normalize_coordinates(
        trajectories, source_metadata["width"], source_metadata["height"]
    )
    return Presentation(
        root,
        output,
        release,
        read_object(geometry_path),
        trajectories,
        pd.read_parquet(checked_path(root, derived["journeys.parquet"])),
        pd.read_parquet(checked_path(root, derived["operational_metrics.parquet"])),
        read_object(rules_path),
        pd.read_parquet(checked_path(root, derived["sensitivity_results.parquet"])),
        {
            "schema_version": "1.0",
            "artifacts": derived,
            "approval_scope": "User-authorized derived-only Block 4 rendering; Step 15 pending",
        },
    )


def interval_tracks(frame: pd.DataFrame, start: float, end: float) -> pd.DataFrame:
    if end - start != 600:
        raise ValueError("Static interval must be continuous ten minutes")
    return frame[
        (frame.source_timestamp >= start) & (frame.source_timestamp < end) & frame.confirmed
    ].sort_values(["track_id", "source_timestamp"])


def captions(p: Presentation) -> list[tuple[str, str, str]]:
    counts = p.counts
    result = p.release["result"]
    changes = p.release["metric_changes"]
    density = changes["density_window_mean"]
    flow = changes["throughput"]
    movement = changes["movement_index"]
    imbalance = changes["inflow_outflow_imbalance"]
    transitions = result["transitions"][:3]
    persistence = p.rules["queue"]["persistence_seconds"]
    return [
        (
            "THE BUSINESS QUESTION",
            "Can a camera flag deterioration?",
            "Before a queue becomes operationally obvious.",
        ),
        (
            "DETECT  /  TRACK",
            "Pixels become anonymous movement.",
            "Derived track markers; no source imagery or persistent identity.",
        ),
        (
            "THE ACTUAL RESULT",
            f"WARNING  {p.warning}",
            "Visible queue: Not qualified. Lead time: Not reportable.",
        ),
        (
            "DEFINE THE OPERATION",
            "Congestion is not one metric.",
            f"Density {density['baseline_median']:.2f} to "
            f"{density['screened_interval_median']:.2f}; "
            f"exits {flow['baseline_median']:g} to {flow['screened_interval_median']:g} /60s.",
        ),
        (
            "RECONCILE BEFORE MEASURING",
            "Only eligible journeys feed dwell.",
            f"{counts['candidate_tracks']} candidates / "
            f"{counts['eligible_confirmed_tracks']} confirmed / "
            f"{counts['completed_dwell_samples']} completed. Full episode.",
        ),
        (
            "LEADING SIGNALS",
            "Several signals deteriorated together.",
            f"Net inflow {imbalance['baseline_median']:g} to "
            f"{imbalance['screened_interval_median']:g}; movement "
            f"{movement['relative_change']:+.1%}. Mixed signals remain visible.",
        ),
        (
            "PERSISTENCE, THEN WARNING",
            "A state change needs evidence.",
            "  >  ".join(f"{t['state']} {clock(t['timestamp'])}" for t in transitions),
        ),
        (
            "AN INDEPENDENT OUTCOME",
            "The warning fired. The queue rule did not.",
            f"The separate queue rule did not satisfy {persistence:g}s persistence. "
            "No lead-time claim.",
        ),
        (
            "A CONDITIONAL RESPONSE",
            "Consider escalating for review.",
            p.release["recommendation"]["wording"]
            + " Alternative: "
            + p.release["recommendation"]["alternative_action"].title()
            + ". Illustrative response.",
        ),
        (
            "CAMERA > METRIC > WARNING > EVIDENCE > ACTION",
            "Better alerts start with restraint.",
            "Better alerts start with knowing when not to overclaim.",
        ),
    ]
