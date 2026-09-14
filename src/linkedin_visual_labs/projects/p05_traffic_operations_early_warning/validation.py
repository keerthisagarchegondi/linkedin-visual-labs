"""Independent scalar recomputation from raw tracked observations and crossings."""

from __future__ import annotations

import math
from statistics import median
from typing import Any

import pandas as pd

from .calibration import Geometry, Point
from .models import ClaimClassification


def quantile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    left = int(position)
    right = min(left + 1, len(ordered) - 1)
    return ordered[left] + (position - left) * (ordered[right] - ordered[left])


def assert_number(actual: Any, expected: float | None, label: str) -> None:
    if expected is None:
        if not pd.isna(actual):
            raise ValueError(f"{label}: expected unavailable")
    elif pd.isna(actual) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"{label}: {actual} != {expected}")


def recompute_metrics(
    tracks: pd.DataFrame,
    crossings: pd.DataFrame,
    journeys: pd.DataFrame,
    frames: list[dict[str, Any]],
    geometry: Geometry,
    metrics: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    samples: dict[float, list[dict[str, Any]]] = {}
    confirmation: dict[int, float] = {}
    histories: dict[int, list[dict[str, Any]]] = {}
    for _, group in tracks.groupby("track_id", sort=True):
        raw = [{str(k): v for k, v in r.items()} for r in group.to_dict("records")]
        identity = int(raw[0]["track_id"])
        histories[identity] = raw
        if len(raw) < 3:
            continue
        if any(
            pd.notna(r["relative_movement_per_second"]) and r["relative_movement_per_second"] > 0.15
            for r in raw
        ):
            continue
        confirmation[identity] = float(raw[2]["source_timestamp"])
        slow_start: float | None = None
        for index, r in enumerate(raw):
            t = float(r["source_timestamp"])
            movement = None
            if index:
                previous = raw[index - 1]
                dt = t - float(previous["source_timestamp"])
                if 0 < dt <= 1:
                    movement = (
                        math.hypot(
                            r["reference_x"] - previous["reference_x"],
                            r["reference_y"] - previous["reference_y"],
                        )
                        / math.hypot(1280, 720)
                        / dt
                    )
            if movement is not None and movement < 0.002:
                if slow_start is None:
                    slow_start = float(raw[index - 1]["source_timestamp"])
            else:
                slow_start = None
            if index < 2:
                continue
            p = Point(x=r["reference_x"] / 1280, y=r["reference_y"] / 720)
            if not r["roi_eligible"] or not geometry.roi.contains(p):
                raise ValueError("excluded-region track")
            samples.setdefault(t, []).append(
                {
                    "track_id": identity,
                    "movement": movement,
                    "queue_zone": geometry.queue_zone.contains(p),
                    "slow": slow_start is not None and t - slow_start >= 3,
                }
            )
    events = [
        {str(k): v for k, v in r.items()}
        for r in crossings.to_dict("records")
        if int(r["track_id"]) in confirmation
    ]
    keys = [(r["track_id"], r["event_type"]) for r in events]
    if len(set(keys)) != len(keys):
        raise ValueError("independent duplicate crossing")
    completed: list[tuple[int, float, float]] = []
    for identity, raw in histories.items():
        event_times = {
            r["event_type"]: float(r["source_timestamp"])
            for r in events
            if r["track_id"] == identity
        }
        if set(event_times) != {"ENTRY", "EXIT"}:
            continue
        gaps = [
            float(raw[i]["source_timestamp"]) - float(raw[i - 1]["source_timestamp"])
            for i in range(1, len(raw))
        ]
        if event_times["ENTRY"] < event_times["EXIT"] and all(g <= 1 for g in gaps):
            completed.append(
                (identity, event_times["EXIT"], event_times["EXIT"] - event_times["ENTRY"])
            )
    if {i for i, _, _ in completed} != set(journeys.loc[journeys.completed_eligible, "track_id"]):
        raise ValueError("independent completed cohort mismatch")
    frame_times = {float(r["source_timestamp"]) for r in frames}
    expected_rows: list[dict[str, Any]] = []
    w = int(config["window_seconds"])
    for t in range(len(metrics)):
        current = samples.get(float(t), [])
        valid = float(t) in frame_times
        movement_values = [float(s["movement"]) for s in current if s["movement"] is not None]
        expected = {
            "timestamp": float(t),
            "density_count": float(len(current)) if valid else None,
            "queue_zone_occupancy": float(sum(s["queue_zone"] for s in current)) if valid else None,
            "queue_count": float(sum(s["queue_zone"] and s["slow"] for s in current))
            if valid
            else None,
            "movement_instant": median(movement_values) if movement_values and valid else None,
        }
        expected_rows.append(expected)
        available = t >= w and all(float(i) in frame_times for i in range(t - w + 1, t + 1))
        window = expected_rows[max(0, t - w + 1) : t + 1]
        ds = [
            d for identity, end, d in completed if t - w < end <= t and confirmation[identity] <= t
        ]
        expected["dwell_sample_size"] = float(len(ds))
        expected["median_completed_dwell_seconds"] = (
            median(ds) if available and len(ds) >= config["minimum_dwell_samples"] else None
        )
        expected["dwell_p10_seconds"] = (
            quantile(ds, 10) if expected["median_completed_dwell_seconds"] is not None else None
        )
        expected["dwell_p90_seconds"] = (
            quantile(ds, 90) if expected["median_completed_dwell_seconds"] is not None else None
        )
        expected["density_window_mean"] = (
            sum(float(r["density_count"]) for r in window) / w if available else None
        )
        ms = [float(r["movement_instant"]) for r in window if r["movement_instant"] is not None]
        expected["movement_index"] = (
            median(ms) if available and len(ms) >= config["minimum_movement_samples"] else None
        )
        for seconds, suffix in ((w, ""), (300, "_300s")):
            good = t >= seconds and all(
                float(i) in frame_times for i in range(t - seconds + 1, t + 1)
            )
            selected = [
                r
                for r in events
                if t - seconds < float(r["source_timestamp"]) <= t
                and confirmation[int(r["track_id"])] <= t
            ]
            incoming = len({r["track_id"] for r in selected if r["event_type"] == "ENTRY"})
            outgoing = len({r["track_id"] for r in selected if r["event_type"] == "EXIT"})
            expected["entries" + suffix] = float(incoming) if good else None
            expected["throughput" + suffix] = float(outgoing) if good else None
            expected["inflow_outflow_imbalance" + suffix] = (
                float(incoming - outgoing) if good else None
            )
        actual = metrics.iloc[t]
        assert_number(actual["window_available"], float(available), f"window availability@{t}")
        assert_number(actual["occupancy_count"], expected["density_count"], f"occupancy@{t}")
        assert_number(actual["low_motion_count"], expected["queue_count"], f"low motion@{t}")
        lag = int(config["trend_seconds"])
        older = expected_rows[t - lag]["density_window_mean"] if t >= lag else None
        trend = (
            None
            if older is None or expected["density_window_mean"] is None
            else (expected["density_window_mean"] - older) / lag
        )
        assert_number(actual["density_trend"], trend, f"trend@{t}")
        for key, value in expected.items():
            assert_number(actual[key], value, f"{key}@{t}")
    return {
        "status": "PASS",
        "evaluations_checked": len(metrics),
        "eligible_crossings": len(events),
        "entries": sum(r["event_type"] == "ENTRY" for r in events),
        "exits": sum(r["event_type"] == "EXIT" for r in events),
        "completed_dwell_sample_size": len(completed),
        "completed_dwell_median_seconds": median([d for _, _, d in completed])
        if completed
        else None,
        "pathway": (
            "Scalar original observations; geometry/low-motion recomputed; paired dwell; "
            "Python statistics; no metrics evaluator calls."
        ),
    }


def independent_onsets(metrics: pd.DataFrame, configuration: dict[str, Any]) -> dict[str, Any]:
    w = configuration["warning"]
    q = configuration["queue"]
    start = configuration["evaluation_start"]
    queue_onset = None
    warning_onset = None
    queue_streak = 0
    warning_streak = 0
    previous: float | None = None
    for r in metrics.to_dict("records"):
        t = float(r["timestamp"])
        if previous is not None and t - previous != 1:
            queue_streak = warning_streak = 0
        valid = (
            t >= start
            and bool(r["window_available"])
            and all(
                pd.notna(r[k])
                for k in (
                    "density_window_mean",
                    "throughput",
                    "movement_index",
                    "inflow_outflow_imbalance",
                    "density_trend",
                )
            )
        )
        votes = 0
        if valid:
            votes = sum(
                [
                    r["density_window_mean"] >= w["density_threshold"],
                    r["throughput"] <= w["throughput_ceiling"],
                    r["movement_index"] <= w["movement_ceiling"],
                    r["inflow_outflow_imbalance"] >= w["imbalance_threshold"],
                    r["density_trend"] >= w["trend_threshold"],
                ]
            )
        warning_streak = warning_streak + 1 if valid and votes >= w["minimum_drivers"] else 0
        good = (
            t >= start
            and bool(r["frame_available"])
            and all(
                pd.notna(r[k]) for k in ("queue_count", "queue_zone_occupancy", "movement_index")
            )
        )
        queue_candidate = (
            good
            and r["queue_count"] >= q["queue_count"]
            and r["queue_zone_occupancy"] >= q["zone_occupancy"]
            and r["movement_index"] <= q["movement_ceiling"]
        )
        queue_streak = queue_streak + 1 if queue_candidate else 0
        if warning_onset is None and warning_streak >= w["persistence_seconds"] + 1:
            warning_onset = t
        if queue_onset is None and queue_streak >= q["persistence_seconds"] + 1:
            queue_onset = t
        previous = t
    return {
        "warning_timestamp": warning_onset,
        "visible_queue_timestamp": queue_onset,
        "lead_time_seconds": None
        if warning_onset is None or queue_onset is None
        else queue_onset - warning_onset,
    }


def verify_onsets(summary: dict[str, Any], expected: dict[str, Any]) -> None:
    for key, value in expected.items():
        assert_number(summary[key], value, key)


def verify_recommendation(
    recommendation: dict[str, Any], summary: dict[str, Any], enabled: list[str]
) -> None:
    for key in ("recommended_action", "alternative_action"):
        if recommendation[key] is not None and recommendation[key] not in enabled:
            raise ValueError("disabled action")
    if recommendation["recommended_action"] is not None and not recommendation[
        "wording"
    ].startswith("Consider "):
        raise ValueError("unconditional action")
    expected = ([summary["primary_driver"]] if summary.get("primary_driver") else []) + summary.get(
        "supporting_drivers", []
    )
    if recommendation["supporting_metric_ids"] != expected:
        raise ValueError("recommendation evidence mismatch")
    assert_number(
        recommendation["evidence_timestamp"],
        summary["warning_timestamp"],
        "recommendation timestamp",
    )


def verify_claim(claim: dict[str, Any]) -> None:
    required = {
        "claim_id",
        "claim_text",
        "classification",
        "evidence_path",
        "calculation",
        "unit",
        "caveat",
        "approved_for_publication",
        "reviewer_status",
    }
    if not required <= claim.keys():
        raise ValueError("incomplete claim")
    ClaimClassification(claim["classification"])
    if claim["approved_for_publication"] and (
        claim["classification"] in ("PREVIEW_ONLY", "UNSUPPORTED")
        or claim["reviewer_status"] != "APPROVED"
    ):
        raise ValueError("unsupported claim approval")
    if claim["approved_for_publication"] and not claim.get("evidence_sha256"):
        raise ValueError("approved claim lacks evidence hash")


def verify_baseline(metrics: pd.DataFrame, summary: dict[str, Any]) -> None:
    start, end = summary["comparison_timestamps"]
    records = metrics[(metrics.timestamp >= start) & (metrics.timestamp < end)].to_dict("records")
    for name, stats in summary["statistics"].items():
        values = [float(r[name]) for r in records if pd.notna(r[name])]
        med = median(values) if values else None
        expected = {
            "median": med,
            "p10": quantile(values, 10),
            "p90": quantile(values, 90),
            "mad": median([abs(v - med) for v in values]) if med is not None else None,
            "sample_size": float(len(values)),
        }
        for key, value in expected.items():
            assert_number(stats[key], value, f"baseline {name}:{key}")
        for row in metrics.to_dict("records"):
            actual = row[name + "_relative_deviation"]
            raw = row[name]
            change = (
                None if pd.isna(raw) or med is None or med == 0 else (float(raw) - med) / abs(med)
            )
            assert_number(actual, change, f"normalization {name}@{row['timestamp']}")
