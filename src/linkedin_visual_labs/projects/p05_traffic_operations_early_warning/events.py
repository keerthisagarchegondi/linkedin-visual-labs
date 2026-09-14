"""Observed-only trajectories and censored journeys; no aggregate traffic metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from .calibration import Geometry, Line, Point, cross, segments_intersect
from .detection import Detection


@dataclass(frozen=True)
class EventConfig:
    maximum_gap_seconds: float = 1.0
    crossing_hysteresis: float = 0.001
    low_motion_per_second: float = 0.002
    low_motion_persistence_seconds: float = 3.0

    def __post_init__(self) -> None:
        values = (
            self.maximum_gap_seconds,
            self.crossing_hysteresis,
            self.low_motion_per_second,
            self.low_motion_persistence_seconds,
        )
        if any(not math.isfinite(v) or v <= 0 for v in values):
            raise ValueError("event settings must be positive and finite")


def point(d: Detection) -> Point:
    return Point(x=d.reference_x / 1280, y=d.reference_y / 720)


def side(p: Point, line: Line) -> float:
    return cross(line.start, line.end, p) / math.hypot(
        line.end.x - line.start.x, line.end.y - line.start.y
    )


def directed_crossing(
    a: Point, b: Point, line: Line, direction: tuple[float, float], hysteresis: float
) -> bool:
    return (
        abs(side(a, line)) >= hysteresis
        and abs(side(b, line)) >= hysteresis
        and side(a, line) * side(b, line) < 0
        and (b.x - a.x) * direction[0] + (b.y - a.y) * direction[1] > 0
        and segments_intersect(a, b, line.start, line.end)
    )


def derive_track(
    track_id: int,
    observations: list[Detection],
    confirmed: bool,
    geometry: Geometry,
    config: EventConfig | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Crossing completion uses current observed timestamp, never interpolated time.

    Confirmation retrospectively admits observed history, explicitly recorded as
    such. A gap resets persistence and crossing anchors; no synthetic positions.
    """
    cfg = config or EventConfig()
    if not observations or any(not d.roi_eligible for d in observations):
        raise ValueError("expected nonempty ROI track")
    if any(b.source_timestamp <= a.source_timestamp for a, b in pairwise(observations)):
        raise ValueError("nonmonotonic trajectory")
    if len({d.detection_id for d in observations}) != len(observations):
        raise ValueError("duplicate trajectory detection")
    trajectories: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    anchors: dict[str, Detection] = {}
    crossings: dict[str, float] = {}
    slow_start: float | None = None
    slow_active = False
    gap_count = 0
    previous: Detection | None = None
    queue_previous: bool | None = None
    for d in observations:
        p = point(d)
        queue = geometry.queue_zone.contains(p)
        dt = None if previous is None else d.source_timestamp - previous.source_timestamp
        gap = dt is not None and dt > cfg.maximum_gap_seconds
        speed = (
            None
            if previous is None or dt is None or gap
            else math.hypot(
                d.reference_x - previous.reference_x, d.reference_y - previous.reference_y
            )
            / math.hypot(1280, 720)
            / float(dt)
        )
        if gap:
            anchors.clear()
            gap_count += 1
        base = {
            "track_id": track_id,
            "frame_index": d.frame_index,
            "source_timestamp": d.source_timestamp,
            "detection_id": d.detection_id,
        }

        def emit(
            kind: str, earliest: float, censored: bool = False, event_base: dict[str, Any] = base
        ) -> None:
            events.append(
                {
                    **event_base,
                    "event_type": kind,
                    "interval_start_timestamp": earliest,
                    "censored": censored,
                }
            )

        if confirmed:
            if previous is None:
                emit("OBSERVED_START_INSIDE", d.source_timestamp, True)
            if queue_previous is not None and queue != queue_previous:
                emit(
                    "QUEUE_ZONE_ENTER" if queue else "QUEUE_ZONE_LEAVE",
                    previous.source_timestamp if previous else d.source_timestamp,
                    gap,
                )
            for name, line, direction in (
                ("ENTRY", geometry.entry, geometry.entry_direction),
                ("EXIT", geometry.exit, geometry.exit_direction),
            ):
                anchor = anchors.get(name)
                if (
                    name not in crossings
                    and anchor is not None
                    and d.source_timestamp - anchor.source_timestamp <= cfg.maximum_gap_seconds
                    and directed_crossing(
                        point(anchor), p, line, direction, cfg.crossing_hysteresis
                    )
                ):
                    crossings[name] = d.source_timestamp
                    emit(name, anchor.source_timestamp)
                if abs(side(p, line)) >= cfg.crossing_hysteresis:
                    anchors[name] = d
            slow = speed is not None and speed < cfg.low_motion_per_second
            if slow:
                if slow_start is None:
                    slow_start = previous.source_timestamp if previous else d.source_timestamp
                if (
                    not slow_active
                    and d.source_timestamp - slow_start >= cfg.low_motion_persistence_seconds
                ):
                    emit("LOW_MOTION_START", slow_start)
                    slow_active = True
            else:
                if slow_active:
                    emit(
                        "LOW_MOTION_END",
                        previous.source_timestamp if previous else d.source_timestamp,
                        gap,
                    )
                slow_active = False
                slow_start = None
        trajectories.append(
            {
                **base,
                "reference_x": d.reference_x,
                "reference_y": d.reference_y,
                "confirmed": confirmed,
                "queue_zone": queue,
                "relative_movement_per_second": speed,
                "observation_gap": gap,
                "low_motion_active": slow_active,
            }
        )
        previous, queue_previous = d, queue
    entry, exit_time = crossings.get("ENTRY"), crossings.get("EXIT")
    completed = (
        confirmed
        and entry is not None
        and exit_time is not None
        and entry < exit_time
        and gap_count == 0
    )
    classification = (
        "SHORT_FRAGMENT"
        if not confirmed
        else "COMPLETED"
        if completed
        else "ENTRY_ONLY"
        if entry is not None and exit_time is None
        else "EXIT_ONLY"
        if entry is None and exit_time is not None
        else "INVALID_OR_GAPPED_PAIR"
        if entry is not None and exit_time is not None
        else "CENSORED_NO_BOUNDARIES"
    )
    if confirmed:
        last = observations[-1]
        events.append(
            {
                "track_id": track_id,
                "frame_index": last.frame_index,
                "source_timestamp": last.source_timestamp,
                "detection_id": last.detection_id,
                "event_type": "OBSERVED_END_INSIDE",
                "interval_start_timestamp": last.source_timestamp,
                "censored": True,
            }
        )
        if slow_active:
            events.append(
                {
                    "track_id": track_id,
                    "frame_index": last.frame_index,
                    "source_timestamp": last.source_timestamp,
                    "detection_id": last.detection_id,
                    "event_type": "LOW_MOTION_CENSORED",
                    "interval_start_timestamp": slow_start,
                    "censored": True,
                }
            )
    journey = {
        "track_id": track_id,
        "classification": classification,
        "entry_timestamp": entry,
        "exit_timestamp": exit_time,
        "completed_eligible": completed,
        "completed_elapsed_seconds": exit_time - entry
        if completed and exit_time is not None and entry is not None
        else None,
        "gap_count": gap_count,
        "started_inside": True,
        "ended_inside": True,
        "confirmed": confirmed,
        "low_motion_censored": slow_active,
        "eligibility_mode": "RETROSPECTIVE_OBSERVED_HISTORY",
    }
    return trajectories, events, journey
