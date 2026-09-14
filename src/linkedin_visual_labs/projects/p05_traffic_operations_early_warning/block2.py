"""Reproducible detection-to-event artifact writers, bounded before Step 8."""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

import pandas as pd

from .calibration import Geometry
from .detection import Detection, checksum
from .events import EventConfig, derive_track
from .tracking import Tracker, TrackingConfig


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.json")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_table(path: Path, value: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial.parquet")
    value.to_parquet(temporary, index=False)
    temporary.replace(path)


def reconcile(
    detections: pd.DataFrame,
    tracks: pd.DataFrame,
    trajectories: pd.DataFrame,
    events: pd.DataFrame,
    journeys: pd.DataFrame,
) -> dict[str, bool]:
    """Reject orphan, duplicated, retimed or fabricated downstream observations."""
    checks: dict[str, bool] = {}
    checks["unique_detection_keys"] = bool(detections.detection_id.is_unique)
    checks["unique_track_observation_keys"] = bool(tracks.detection_id.is_unique)
    checks["track_observations_have_source_detection"] = bool(
        tracks.detection_id.isin(detections.detection_id).all()
    )
    joined = tracks.merge(detections, on="detection_id", suffixes=("_track", "_detection"))
    checks["track_observations_unchanged"] = len(joined) == len(tracks) and all(
        bool((joined[f"{f.name}_track"] == joined[f"{f.name}_detection"]).all())
        for f in fields(Detection)
        if f.name != "detection_id"
    )
    checks["roi_only_tracks"] = bool(tracks.roi_eligible.all())
    checks["trajectory_keys_match_tracks"] = bool(trajectories.detection_id.is_unique) and set(
        trajectories.detection_id
    ) == set(tracks.detection_id)
    time_join = trajectories.merge(tracks, on="detection_id", suffixes=("_trajectory", "_track"))
    checks["trajectory_clock_and_identity_unchanged"] = all(
        bool((time_join[f"{k}_trajectory"] == time_join[f"{k}_track"]).all())
        for k in ("track_id", "source_timestamp", "frame_index", "reference_x", "reference_y")
    )
    checks["unique_event_ids"] = bool(events.event_id.is_unique)
    event_join = events.merge(tracks, on="detection_id", suffixes=("_event", "_track"))
    checks["events_link_to_observed_confirmed_tracks"] = (
        len(event_join) == len(events)
        and bool(event_join.confirmed.all())
        and all(
            bool((event_join[f"{k}_event"] == event_join[f"{k}_track"]).all())
            for k in ("track_id", "source_timestamp", "frame_index")
        )
    )
    checks["event_intervals_not_backdated"] = bool(
        (events.interval_start_timestamp <= events.source_timestamp).all()
    )
    crossing = events[events.event_type.isin(["ENTRY", "EXIT"])]
    checks["unique_directional_crossings"] = not bool(
        crossing.duplicated(["track_id", "event_type"]).any()
    )
    checks["journeys_partition_tracks"] = bool(journeys.track_id.is_unique) and set(
        journeys.track_id
    ) == set(tracks.track_id)
    completed = journeys[journeys.completed_eligible]
    checks["completed_journeys_are_gap_free_ordered_pairs"] = bool(
        (completed.entry_timestamp < completed.exit_timestamp).all()
        and (completed.gap_count == 0).all()
    )
    checks["censored_journeys_have_no_completed_elapsed"] = bool(
        journeys.loc[~journeys.completed_eligible, "completed_elapsed_seconds"].isna().all()
    )
    for name, column in (("ENTRY", "entry_timestamp"), ("EXIT", "exit_timestamp")):
        actual = (
            crossing[crossing.event_type == name].set_index("track_id").source_timestamp.to_dict()
        )
        reported = journeys.dropna(subset=[column]).set_index("track_id")[column].to_dict()
        checks[f"{name.lower()}_counts_and_times_reconcile"] = actual == reported
    return checks


def build_tracking(
    detection_path: Path,
    frame_summary_path: Path,
    output: Path,
    config: TrackingConfig | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    detections = pd.read_parquet(detection_path)
    summary = json.loads(frame_summary_path.read_text(encoding="utf-8"))
    groups = {
        f: [Detection(**{str(k): v for k, v in d.items()}) for d in group.to_dict("records")]
        for f, group in detections.groupby("frame_index")
    }
    tracker = Tracker(config)
    for frame in summary["frames"]:
        tracker.update(frame["source_timestamp"], groups.get(frame["frame_index"], []))
    rows: list[dict[str, Any]] = []
    inventory: list[dict[str, Any]] = []
    for track in tracker.tracks:
        previous: Detection | None = None
        for hit_count, (detection, stage) in enumerate(
            zip(track.observations, track.stages, strict=True), start=1
        ):
            displacement = (
                None
                if previous is None
                else math.hypot(
                    detection.reference_x - previous.reference_x,
                    detection.reference_y - previous.reference_y,
                )
            )
            relative_movement = (
                None
                if previous is None or displacement is None
                else (
                    displacement
                    / math.hypot(1280, 720)
                    / (detection.source_timestamp - previous.source_timestamp)
                )
            )
            rows.append(
                {
                    **asdict(detection),
                    "track_id": track.track_id,
                    "confirmed": track.confirmed,
                    "association_stage": stage,
                    "confirmed_at_observation": hit_count >= tracker.config.confirmation_hits,
                    "track_age_seconds": detection.source_timestamp
                    - track.observations[0].source_timestamp,
                    "hit_count": hit_count,
                    "lost_frame_count": 0
                    if previous is None
                    else max(0, detection.analysis_frame_index - previous.analysis_frame_index - 1),
                    "displacement_source_pixels": displacement,
                    "relative_movement_per_second": relative_movement,
                }
            )
            previous = detection
        inventory.append(
            {
                "track_id": track.track_id,
                "confirmed": track.confirmed,
                "observations": len(track.observations),
                "first_timestamp": track.observations[0].source_timestamp,
                "last_timestamp": track.last.source_timestamp,
                "duration_seconds": track.last.source_timestamp
                - track.observations[0].source_timestamp,
                "terminal_status": track.status,
                "recoveries": track.recoveries,
            }
        )
    if not rows:
        raise ValueError("no tracks; tracking quality blocked")
    write_table(output / "data/tracks.parquet", pd.DataFrame(rows))
    write_table(output / "data/track_inventory.parquet", pd.DataFrame(inventory))
    result = {
        "config": asdict(tracker.config),
        "track_count": len(inventory),
        "confirmed_count": sum(t.confirmed for t in tracker.tracks),
        "single_observation_count": sum(len(t.observations) == 1 for t in tracker.tracks),
        "short_under_2_seconds": sum(q["duration_seconds"] < 2 for q in inventory),
        "recoveries": sum(t.recoveries for t in tracker.tracks),
        "duplicate_births_suppressed": tracker.duplicate_births_suppressed,
        "wall_seconds": time.perf_counter() - started,
        "observed_rows": len(rows),
        "median_track_duration_seconds": float(
            pd.Series([q["duration_seconds"] for q in inventory]).median()
        ),
        "short_track_rate_under_2_seconds": sum(q["duration_seconds"] < 2 for q in inventory)
        / len(inventory),
        "invalid_observed_jump_count": sum(
            r["relative_movement_per_second"] is not None
            and r["relative_movement_per_second"] > tracker.config.maximum_movement_per_second
            for r in rows
        ),
        "lost_or_removed_confirmed_tracks": sum(
            t.confirmed and t.status in ("LOST", "REMOVED") for t in tracker.tracks
        ),
        "recovered_track_count": sum(t.recoveries > 0 for t in tracker.tracks),
        "fragmentation_indicator": (
            "Unconfirmed count and short-track rate are proxies; not measured identity switches."
        ),
        "accuracy_claim": None,
        "ground_truth": "NOT_AVAILABLE",
        "interpretation": "Fragmentation proxies are not identity-switch accuracy.",
        "detections_sha256": checksum(detection_path),
        "frame_summary_sha256": checksum(frame_summary_path),
    }
    write_json(output / "data/track_quality_summary.json", result)
    return result


def build_events(
    output: Path, geometry: Geometry, config: EventConfig | None = None
) -> dict[str, Any]:
    started = time.perf_counter()
    tracks = pd.read_parquet(output / "data/tracks.parquet")
    keys = [f.name for f in fields(Detection)]
    trajectories: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    journeys: list[dict[str, Any]] = []
    for _, group in tracks.groupby("track_id", sort=True):
        t, e, j = derive_track(
            int(group.track_id.iloc[0]),
            [
                Detection(**{str(k): v for k, v in r.items()})
                for r in group[keys].to_dict("records")
            ],
            bool(group.confirmed.iloc[0]),
            geometry,
            config,
        )
        trajectories.extend(t)
        events.extend(e)
        journeys.append(j)
    if not events:
        raise ValueError("no confirmed track events; event quality blocked")
    trajectory_table = pd.DataFrame(trajectories)
    event_table = pd.DataFrame(events)
    event_table.insert(0, "event_id", [f"event:{i}" for i in range(len(event_table))])
    journey_table = pd.DataFrame(journeys)
    checks = reconcile(
        pd.read_parquet(output / "data/detections.parquet"),
        tracks,
        trajectory_table,
        event_table,
        journey_table,
    )
    result = {
        "config": asdict(config or EventConfig()),
        "classification_counts": journey_table.classification.value_counts().to_dict(),
        "event_counts": event_table.event_type.value_counts().to_dict(),
        "trajectory_rows": len(trajectories),
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "wall_seconds": time.perf_counter() - started,
    }
    write_json(output / "data/event_reconciliation.json", result)
    if not all(checks.values()):
        raise ValueError("event reconciliation failed")
    write_table(output / "data/trajectories.parquet", trajectory_table)
    crossings = event_table.event_type.isin(["ENTRY", "EXIT"])
    write_table(output / "data/crossing_events.parquet", event_table[crossings])
    write_table(output / "data/zone_events.parquet", event_table[~crossings])
    write_table(output / "data/journeys.parquet", journey_table)
    quality_path = output / "data/track_quality_summary.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    quality["completed_eligible_tracks"] = int(journey_table.completed_eligible.sum())
    quality["incomplete_tracks"] = int((~journey_table.completed_eligible).sum())
    write_json(quality_path, quality)
    return result
