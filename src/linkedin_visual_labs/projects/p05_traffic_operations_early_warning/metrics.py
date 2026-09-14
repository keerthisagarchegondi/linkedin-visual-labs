"""Original-time metrics from reconciled observations; no detector dependency."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MetricPlan:
    window_seconds: int = 60
    formal_window_seconds: int = 300
    cadence_seconds: int = 1
    minimum_dwell_samples: int = 3
    minimum_movement_samples: int = 10
    baseline_start: int = 1260
    baseline_end: int = 1380
    trend_seconds: int = 30

    def __post_init__(self) -> None:
        if self.formal_window_seconds != 300 or self.cadence_seconds != 1:
            raise ValueError("formal window and original-time cadence are locked")
        if (
            min(
                self.window_seconds,
                self.minimum_dwell_samples,
                self.minimum_movement_samples,
                self.trend_seconds,
            )
            <= 0
        ):
            raise ValueError("positive metric parameters required")
        if (
            self.baseline_start < 0
            or self.baseline_end - self.baseline_start <= self.window_seconds
        ):
            raise ValueError("baseline must contain full operational windows")


def percentile(values: list[float], q: float) -> float | None:
    return None if not values else float(np.percentile(values, q, method="linear"))


def deviation(value: float | None, reference: float | None) -> float | None:
    if (
        value is None
        or reference is None
        or not math.isfinite(value)
        or not math.isfinite(reference)
        or reference == 0
    ):
        return None
    return (value - reference) / abs(reference)


def eligible_inputs(
    tracks: pd.DataFrame,
    trajectories: pd.DataFrame,
    crossings: pd.DataFrame,
    journeys: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if not tracks.detection_id.is_unique or not trajectories.detection_id.is_unique:
        raise ValueError("duplicate observations")
    if crossings.duplicated(["track_id", "event_type"]).any():
        raise ValueError("duplicate crossing")
    if not journeys.track_id.is_unique or set(journeys.track_id) != set(tracks.track_id):
        raise ValueError("journey partition mismatch")
    for _, group in tracks.groupby("track_id"):
        if (
            not group.source_timestamp.is_monotonic_increasing
            or group.source_timestamp.duplicated().any()
        ):
            raise ValueError("nonmonotonic track")
    bad_ids = set(tracks.loc[tracks.relative_movement_per_second > 0.15, "track_id"])
    mask = (
        tracks.confirmed_at_observation
        & tracks.confirmed
        & tracks.roi_eligible
        & ~tracks.track_id.isin(bad_ids)
    )
    accepted = tracks[mask].copy()
    positions = accepted.merge(
        trajectories[["detection_id", "queue_zone", "low_motion_active", "observation_gap"]],
        on="detection_id",
        validate="one_to_one",
    )
    if len(positions) != len(accepted):
        raise ValueError("missing trajectory")
    confirmation = accepted.groupby("track_id").source_timestamp.min()
    events = crossings[crossings.track_id.isin(confirmation.index)].copy()
    events["available_timestamp"] = [
        max(float(t), float(confirmation.loc[tid]))
        for tid, t in zip(events.track_id, events.source_timestamp, strict=True)
    ]
    completed = journeys[
        journeys.completed_eligible & journeys.track_id.isin(confirmation.index)
    ].copy()
    if (completed.entry_timestamp >= completed.exit_timestamp).any() or (
        completed.gap_count != 0
    ).any():
        raise ValueError("invalid completed journey")
    completed["dwell_seconds"] = completed.exit_timestamp - completed.entry_timestamp
    completed["available_timestamp"] = [
        max(float(t), float(confirmation.loc[tid]))
        for tid, t in zip(completed.track_id, completed.exit_timestamp, strict=True)
    ]
    if not np.allclose(
        completed.dwell_seconds.to_numpy(dtype=float),
        completed.completed_elapsed_seconds.to_numpy(dtype=float),
    ):
        raise ValueError("completed dwell mismatch")
    quality = {
        "candidate_tracks": int(tracks.track_id.nunique()),
        "eligible_confirmed_tracks": int(accepted.track_id.nunique()),
        "input_observations": len(tracks),
        "eligible_observations": len(accepted),
        "excluded_observations": int((~mask).sum()),
        "unconfirmed_or_preconfirmation_observations": int(
            (~tracks.confirmed_at_observation).sum()
        ),
        "invalid_jump_tracks": len(bad_ids),
        "outside_roi_observations": int((~tracks.roi_eligible).sum()),
        "eligible_crossings": len(events),
        "eligible_entries": int((events.event_type == "ENTRY").sum()),
        "eligible_exits": int((events.event_type == "EXIT").sum()),
        "completed_dwell_samples": len(completed),
        "incomplete_journeys_excluded_from_dwell": len(journeys) - len(completed),
        "confirmation_policy": (
            "Known confirmation only; historical crossing available no earlier than confirmation."
        ),
        "cohort_limit": (
            "Audited journey eligibility is retrospective quality screening; "
            "not independent online performance validation."
        ),
    }
    return positions, events, completed, quality


def calculate(
    positions: pd.DataFrame,
    events: pd.DataFrame,
    completed: pd.DataFrame,
    frames: list[dict[str, Any]],
    duration_seconds: int,
    plan: MetricPlan | None = None,
) -> pd.DataFrame:
    cfg = plan or MetricPlan()
    frame_times = {float(f["source_timestamp"]): int(f["frame_index"]) for f in frames}
    if len(frame_times) != len(frames):
        raise ValueError("duplicate frame clock")
    groups = {
        float(group.source_timestamp.iloc[0]): group
        for _, group in positions.groupby("source_timestamp")
    }
    rows: list[dict[str, Any]] = []
    for tick in range(duration_seconds):
        t = float(tick)
        frame = groups.get(float(t))
        available = float(t) in frame_times
        n = 0 if frame is None else int(frame.track_id.nunique())
        movements = (
            []
            if frame is None
            else [
                float(v)
                for v in frame.loc[~frame.observation_gap, "relative_movement_per_second"].dropna()
            ]
        )
        queue = 0 if frame is None else int((frame.queue_zone & frame.low_motion_active).sum())
        row: dict[str, Any] = {
            "timestamp": float(t),
            "frame_available": available,
            "occupancy_count": n if available else None,
            "density_count": n if available else None,
            "queue_zone_occupancy": (0 if frame is None else int(frame.queue_zone.sum()))
            if available
            else None,
            "low_motion_count": queue if available else None,
            "queue_count": queue if available else None,
            "movement_instant": percentile(movements, 50) if available else None,
            "movement_observation_count": len(movements) if available else 0,
            "density_quality": "AVAILABLE" if available else "UNAVAILABLE_FRAME",
        }
        rows.append(row)
    table = pd.DataFrame(rows)
    for i in range(len(table)):
        t = float(i)
        window = table[(table.timestamp > t - cfg.window_seconds) & (table.timestamp <= t)]
        warm = i >= cfg.window_seconds
        coverage = float(window.frame_available.mean())
        available = warm and coverage == 1
        table.loc[i, "window_coverage"] = coverage
        table.loc[i, "window_available"] = available
        table.loc[i, "window_quality"] = (
            "AVAILABLE" if available else "WARMUP" if not warm else "UNAVAILABLE_FRAME"
        )
        for seconds, suffix in ((cfg.window_seconds, ""), (cfg.formal_window_seconds, "_300s")):
            es = events[
                (events.source_timestamp > t - seconds)
                & (events.source_timestamp <= t)
                & (events.available_timestamp <= t)
            ]
            valid = i >= seconds and bool(
                table.loc[max(0, i - seconds + 1) : i, "frame_available"].all()
            )
            incoming = int(es.loc[es.event_type == "ENTRY", "track_id"].nunique())
            outgoing = int(es.loc[es.event_type == "EXIT", "track_id"].nunique())
            for name, value in (
                ("entries", incoming),
                ("throughput", outgoing),
                ("inflow_outflow_imbalance", incoming - outgoing),
            ):
                table.loc[i, name + suffix] = value if valid else np.nan
        ds = completed[
            (completed.exit_timestamp > t - cfg.window_seconds)
            & (completed.exit_timestamp <= t)
            & (completed.available_timestamp <= t)
        ]
        values = [float(v) for v in ds.dwell_seconds]
        table.loc[i, "dwell_sample_size"] = len(values)
        supported = available and len(values) >= cfg.minimum_dwell_samples
        for name, q in (
            ("median_completed_dwell_seconds", 50),
            ("dwell_p10_seconds", 10),
            ("dwell_p90_seconds", 90),
        ):
            table.loc[i, name] = percentile(values, q) if supported else np.nan
        table.loc[i, "dwell_quality"] = (
            "AVAILABLE"
            if supported
            else "SPARSE_COMPLETED_SAMPLE"
            if available
            else "UNAVAILABLE_WINDOW"
        )
        table.loc[i, "density_window_mean"] = (
            float(window.density_count.mean()) if available else np.nan
        )
        samples = [float(v) for v in window.movement_instant.dropna()]
        table.loc[i, "movement_sample_size"] = len(samples)
        table.loc[i, "movement_index"] = (
            percentile(samples, 50)
            if available and len(samples) >= cfg.minimum_movement_samples
            else np.nan
        )
    table["density_trend"] = (
        table.density_window_mean - table.density_window_mean.shift(cfg.trend_seconds)
    ) / cfg.trend_seconds
    persistence = 0.0
    previous: float | None = None
    durations = []
    for record in table.to_dict("records"):
        if record["frame_available"] and record["queue_count"] >= 1:
            if previous is None:
                previous = float(record["timestamp"])
            persistence = float(record["timestamp"]) - previous
        else:
            previous = None
            persistence = 0.0
        durations.append(persistence)
    table["queue_persistence_seconds"] = durations
    return table


BASELINE_METRICS = (
    "density_window_mean",
    "median_completed_dwell_seconds",
    "throughput",
    "movement_index",
    "queue_count",
    "inflow_outflow_imbalance",
)


def baseline(table: pd.DataFrame, plan: MetricPlan | None = None) -> dict[str, Any]:
    cfg = plan or MetricPlan()
    selected = table[
        (table.timestamp >= cfg.baseline_start + cfg.window_seconds)
        & (table.timestamp < cfg.baseline_end)
    ]
    statistics: dict[str, Any] = {}
    for key in BASELINE_METRICS:
        values = [float(v) for v in selected[key].dropna()]
        median = percentile(values, 50)
        statistics[key] = {
            "median": median,
            "p10": percentile(values, 10),
            "p90": percentile(values, 90),
            "sample_size": len(values),
            "mad": percentile([abs(v - median) for v in values], 50)
            if median is not None
            else None,
        }
    density = statistics["density_window_mean"]
    valid = bool(
        len(selected) > 0
        and selected.window_available.all()
        and density["median"] is not None
        and density["p90"] - density["p10"] <= max(3, 1.5 * density["median"])
        and statistics["throughput"]["median"] is not None
        and statistics["movement_index"]["median"] is not None
    )
    return {
        "interval": [cfg.baseline_start, cfg.baseline_end],
        "comparison_timestamps": [cfg.baseline_start + cfg.window_seconds, cfg.baseline_end],
        "configuration": asdict(cfg),
        "threshold_classification": "CONFIGURED_ASSUMPTION",
        "statistics": statistics,
        "status": "PASS_LIMITED_SCREENING_BASELINE" if valid else "BASELINE_QUALITY_BLOCKED",
        "selection_reason": (
            "Screened baseline retained if full windows and bounded density spread; "
            "no lead-time criterion."
        ),
        "limitations": [
            "120s baseline cannot provide full300s within-baseline windows.",
            "Overlapping windows are not independent samples.",
            "Sparse dwell remains unavailable; no baseline percentage against zero.",
        ],
    }


def normalize(table: pd.DataFrame, summary: dict[str, Any]) -> pd.DataFrame:
    result = table.copy()
    for key in BASELINE_METRICS:
        ref = summary["statistics"][key]["median"]
        result[key + "_baseline"] = ref
        result[key + "_relative_deviation"] = [
            deviation(float(v), ref) if pd.notna(v) else None for v in result[key]
        ]
    return result
