"""Presentation-only speed ramps, semantic colors and causal history selection."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from .presentation_v2 import SCENES, TOKENS, scene_index

BUILD = "PROJECT6_4.C.C"
COLORS = {
    **TOKENS,
    "box_default": "#F4F7FA",
    "box_highlight": "#F4F7FA",
    "trajectory_primary": "#835CF6",
    "trajectory_secondary": "#62439A",
    "trajectory_history_start": "#38245C",
    "trajectory_history_end": "#835CF6",
    "density_low": "#30205F",
    "density_mid": "#835CF6",
    "density_high": "#EC4899",
    "entry_color": "#2BA668",
    "exit_color": "#F4CC63",
    "warning_watch": "#F2A93B",
    "warning_active": "#E04F4F",
    "zone_outline": "#8D849B",
    "validation_not_confirmed": "#B7C7D5",
}
# Original source start, starting speed, ending speed. Last scene decelerates
# over 0.75 display seconds and holds for 0.25 seconds.
RAMPS = (
    (1320.0, 8.0, 10.0),
    (1378.0, 6.0, 8.0),
    (1380.0, 10.0, 12.0),
    (1438.0, 8.0, 10.0),
    (1445.0, 12.0, 15.0),
    (1420.0, 10.0, 12.0),
    (1376.0, 12.0, 14.0),
    (1500.0, 6.0, 8.0),
    (1710.0, 8.0, 10.0),
    (1746.0, 8.0, 0.0),
)


def source_time(display_time: float, *, quantized: bool = True) -> float:
    index = scene_index(display_time)
    start, speed0, speed1 = RAMPS[index]
    elapsed = display_time - SCENES[index][0]
    duration = SCENES[index][1] - SCENES[index][0]
    if index == 9:
        elapsed, duration = min(elapsed, 0.75), 0.75
    value = start + speed0 * elapsed + (speed1 - speed0) * elapsed**2 / (2 * duration)
    return math.floor(value * 10 + 1e-7) / 10 if quantized else value


def history_at(tracks: pd.DataFrame, timestamp: float, seconds: float = 45) -> pd.DataFrame:
    if seconds <= 0:
        raise ValueError("History duration must be positive")
    return tracks[
        (tracks.source_timestamp > timestamp - seconds) & (tracks.source_timestamp <= timestamp)
    ].copy()


def trail_alpha(age: float, duration: float = 60) -> int:
    if age < 0 or age >= duration:
        return 0
    return round(230 * math.pow(1 - age / duration, 1.3))


def playback_contract() -> dict[str, Any]:
    return {
        "build": BUILD,
        "analytics_timebase": "ORIGINAL_SOURCE_TIME",
        "presentation_playback": "ACCELERATED_FOR_VISUALIZATION",
        "scenes": [
            {
                "display_start": scene[0],
                "display_end": scene[1],
                "source_start": ramp[0],
                "speed_start": ramp[1],
                "speed_end": ramp[2],
                "source_end": source_time(scene[1] - 1e-6, quantized=False),
            }
            for scene, ramp in zip(SCENES, RAMPS, strict=True)
        ],
        "ramp": "Linear speed ramp; integrated source time, floored to original 10fps frame.",
        "state_scene_exception": "12-14x permits the observed 23:03 WATCH and 24:00 WARNING "
        "transitions within five display seconds; no timestamp adjustment.",
        "render_cadence": "15 unique presentation frames/s repeated twice to 30fps.",
        "contour_history_seconds": 45,
        "trail_history_seconds": 60,
        "future_observations": False,
        "close_hold_seconds": 0.25,
        "kpi_scope": "Fixed audited 24:00 snapshot (1380,1440], not current montage readings.",
    }


def validate_colors(values: dict[str, str]) -> None:
    roles = (
        "box_default",
        "trajectory_primary",
        "density_high",
        "entry_color",
        "exit_color",
        "warning_active",
    )
    selected = [values[key] for key in roles]
    if len(set(selected)) != len(roles) or "#1CBCDD" in selected:
        raise ValueError("DEPRECATED_VISUAL_STYLE or insufficient semantic differentiation")


def require_fresh(outputs: list[Path], dependencies: list[Path]) -> None:
    threshold = max(p.stat().st_mtime_ns for p in dependencies)
    if any(p.stat().st_mtime_ns <= threshold for p in outputs):
        raise ValueError("Stale production output")
