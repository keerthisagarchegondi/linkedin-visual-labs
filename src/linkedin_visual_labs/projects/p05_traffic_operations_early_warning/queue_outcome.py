"""Independent persistent queue-state outcome; consumes no warning signal."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class QueueRule:
    queue_count: int = 2
    zone_occupancy: int = 3
    movement_ceiling: float = 0.005
    persistence_seconds: int = 120

    def __post_init__(self) -> None:
        if (
            min(self.queue_count, self.zone_occupancy, self.persistence_seconds) <= 0
            or not math.isfinite(self.movement_ceiling)
            or self.movement_ceiling <= 0
        ):
            raise ValueError("invalid queue rule")


def evaluate_queue(metrics: pd.DataFrame, rule: QueueRule, evaluation_start: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    start: float | None = None
    previous: float | None = None
    for row in metrics.to_dict("records"):
        t = float(row["timestamp"])
        if previous is not None and t <= previous:
            raise ValueError("nonmonotonic queue grid")
        if previous is not None and t - previous != 1:
            start = None
        values = [row[k] for k in ("queue_count", "queue_zone_occupancy", "movement_index")]
        valid = (
            t >= evaluation_start
            and bool(row["frame_available"])
            and all(pd.notna(v) for v in values)
        )
        candidate = (
            valid
            and values[0] >= rule.queue_count
            and values[1] >= rule.zone_occupancy
            and values[2] <= rule.movement_ceiling
        )
        if candidate:
            if start is None:
                start = t
        else:
            start = None
        duration = 0.0 if start is None else t - start
        rows.append(
            {
                "timestamp": t,
                "quality": "AVAILABLE" if valid else "UNAVAILABLE_OR_CALIBRATION",
                "queue_candidate": bool(candidate),
                "persistence_seconds": duration,
                "visible_queue": bool(candidate and duration >= rule.persistence_seconds),
            }
        )
        previous = t
    return pd.DataFrame(rows)
