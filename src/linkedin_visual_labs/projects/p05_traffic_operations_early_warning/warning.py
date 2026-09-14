"""Leading deterioration state machine, signed results and bounded sensitivity."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

import pandas as pd

from .queue_outcome import QueueRule, evaluate_queue


@dataclass(frozen=True)
class WarningRule:
    density_threshold: float
    throughput_ceiling: float
    movement_ceiling: float
    imbalance_threshold: float = 2
    trend_threshold: float = 0.005
    minimum_drivers: int = 3
    persistence_seconds: int = 30
    critical_seconds: int = 60
    reset_seconds: int = 15

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(v)
            for v in (
                self.density_threshold,
                self.throughput_ceiling,
                self.movement_ceiling,
                self.imbalance_threshold,
                self.trend_threshold,
            )
        ):
            raise ValueError("nonfinite warning rule")
        if (
            min(
                self.density_threshold,
                self.movement_ceiling,
                self.persistence_seconds,
                self.critical_seconds,
                self.reset_seconds,
            )
            <= 0
            or not 1 <= self.minimum_drivers <= 5
            or self.throughput_ceiling < 0
        ):
            raise ValueError("invalid warning rule")


def drivers(row: dict[str, Any], rule: WarningRule) -> list[str]:
    predicates = [
        ("DENSITY_LEVEL", row["density_window_mean"] >= rule.density_threshold),
        ("INFLOW_OUTFLOW_IMBALANCE", row["inflow_outflow_imbalance"] >= rule.imbalance_threshold),
        ("THROUGHPUT_DECLINE", row["throughput"] <= rule.throughput_ceiling),
        ("MOVEMENT_DECLINE", row["movement_index"] <= rule.movement_ceiling),
        ("DENSITY_TREND", row["density_trend"] >= rule.trend_threshold),
    ]
    return [name for name, active in predicates if active]


def evaluate_warning(
    metrics: pd.DataFrame, rule: WarningRule, evaluation_start: float
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    state: str | None = None
    warning_start: float | None = None
    critical_start: float | None = None
    reset_start: float | None = None
    previous: float | None = None
    for raw in metrics.to_dict("records"):
        row = {str(k): v for k, v in raw.items()}
        t = float(row["timestamp"])
        if previous is not None and t <= previous:
            raise ValueError("nonmonotonic warning grid")
        contiguous = previous is None or t - previous == 1
        if not contiguous:
            warning_start = critical_start = reset_start = None
            state = None
        valid = (
            t >= evaluation_start
            and bool(row["window_available"])
            and all(
                pd.notna(row[k])
                for k in (
                    "density_window_mean",
                    "throughput",
                    "movement_index",
                    "inflow_outflow_imbalance",
                    "density_trend",
                )
            )
        )
        active = drivers(row, rule) if valid else []
        if not valid:
            warning_start = critical_start = reset_start = None
            state = None
        else:
            if len(active) >= rule.minimum_drivers:
                if warning_start is None:
                    warning_start = t
            else:
                warning_start = None
            if len(active) >= 4:
                if critical_start is None:
                    critical_start = t
            else:
                critical_start = None
            if len(active) <= 1:
                if reset_start is None:
                    reset_start = t
            else:
                reset_start = None
            qualifies = warning_start is not None and t - warning_start >= rule.persistence_seconds
            critical = critical_start is not None and t - critical_start >= rule.critical_seconds
            if critical:
                state = "CRITICAL"
            elif qualifies:
                state = "WARNING"
            elif state in ("WARNING", "CRITICAL"):
                if reset_start is not None and t - reset_start >= rule.reset_seconds:
                    state = "NORMAL" if not active else "WATCH"
            else:
                state = "WATCH" if active else "NORMAL"
        full_warning = (
            valid and warning_start is not None and t - warning_start >= rule.persistence_seconds
        )
        rows.append(
            {
                "timestamp": t,
                "state": state,
                "quality": "AVAILABLE" if valid else "UNAVAILABLE_OR_CALIBRATION",
                "driver_count": len(active),
                "drivers": "|".join(active),
                "primary_driver": active[0] if active else None,
                "warning_persistence_seconds": 0.0 if warning_start is None else t - warning_start,
                "warning_qualified": bool(full_warning),
            }
        )
        previous = t
    return pd.DataFrame(rows)


def first_time(table: pd.DataFrame, flag: str) -> float | None:
    selected = table.loc[table[flag], "timestamp"]
    return None if selected.empty else float(selected.iloc[0])


def result(warning: float | None, queue: float | None) -> dict[str, Any]:
    if queue is None:
        classification = "NO_VISIBLE_QUEUE_EVENT"
    elif warning is None:
        classification = "NO_VALID_WARNING"
    elif queue > warning:
        classification = "POSITIVE_EARLY_WARNING"
    elif queue == warning:
        classification = "WARNING_AT_VISIBLE_ONSET"
    else:
        classification = "LATE_WARNING"
    return {
        "warning_timestamp": warning,
        "visible_queue_timestamp": queue,
        "lead_time_seconds": None if warning is None or queue is None else queue - warning,
        "result_classification": classification,
    }


def baseline_false_warnings(
    metrics: pd.DataFrame, rule: WarningRule, start: float, end: float
) -> dict[str, Any]:
    timeline = evaluate_warning(
        metrics[(metrics.timestamp >= start) & (metrics.timestamp < end)], rule, start
    )
    active = timeline.state.isin(["WARNING", "CRITICAL"])
    episodes = int((active & ~active.shift(fill_value=False)).sum())
    valid = int((timeline.quality == "AVAILABLE").sum())
    return {
        "baseline_false_warning_count": episodes,
        "warning_seconds": int(active.sum()),
        "evaluable_seconds": valid,
        "proportion": float(active.sum() / valid) if valid else None,
        "caveat": ("In-sample baseline diagnostic; not held-out false-alarm accuracy."),
    }


def variants(warning: WarningRule, queue: QueueRule) -> list[tuple[str, WarningRule, QueueRule]]:
    return [
        ("PRIMARY", warning, queue),
        (
            "DENSITY_MINUS_20_PERCENT",
            replace(warning, density_threshold=warning.density_threshold * 0.8),
            queue,
        ),
        (
            "DENSITY_PLUS_20_PERCENT",
            replace(warning, density_threshold=warning.density_threshold * 1.2),
            queue,
        ),
        (
            "QUEUE_PERSISTENCE_MINUS_30_SECONDS",
            warning,
            replace(queue, persistence_seconds=max(1, queue.persistence_seconds - 30)),
        ),
        (
            "QUEUE_PERSISTENCE_PLUS_30_SECONDS",
            warning,
            replace(queue, persistence_seconds=queue.persistence_seconds + 30),
        ),
    ]


def sensitivity(
    metrics: pd.DataFrame,
    warning: WarningRule,
    queue: QueueRule,
    evaluation_start: float,
    baseline_start: float,
    baseline_end: float,
) -> pd.DataFrame:
    rows = []
    for name, w, q in variants(warning, queue):
        wt = evaluate_warning(metrics, w, evaluation_start)
        qt = evaluate_queue(metrics, q, evaluation_start)
        rows.append(
            {
                "variant": name,
                **result(first_time(wt, "warning_qualified"), first_time(qt, "visible_queue")),
                **baseline_false_warnings(metrics, w, baseline_start, baseline_end),
            }
        )
    return pd.DataFrame(rows)
