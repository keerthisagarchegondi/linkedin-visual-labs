"""Frozen-evidence presentation contract and original-PNG palette extraction.

This module never invokes analytical stages. Visual parameters are presentation
choices, not detector, tracking, metric or queue parameters.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

from .detection import checksum

BUILD = "PROJECT6_4.C.B"
STATUS = "PENDING_SOURCE_PERMISSION"
TOKENS = {
    "background_primary": "#091522",
    "background_secondary": "#0B1A2A",
    "panel_fill": "#081623",
    "panel_border": "#667788",
    "trajectory_primary": "#1CBCDD",
    "trajectory_secondary": "#2F80ED",
    "trajectory_history_start": "#2F80ED",
    "trajectory_history_end": "#1CBCDD",
    "density_low": "#2F80ED",
    "density_mid": "#1CBCDD",
    "density_high": "#F2A93B",
    "entry_color": "#1CBCDD",
    "exit_color": "#2BA668",
    "warning_watch": "#F2A93B",
    "warning_active": "#F2A93B",
    "alert_critical": "#E04F4F",
    "validation_pass": "#2BA668",
    "validation_not_confirmed": "#667788",
    "text_primary": "#FFFFFF",
    "text_secondary": "#DBE4ED",
    "text_muted": "#667788",
    "grid": "#667788",
    "zone_outline": "#2F80ED",
    "box_default": "#1CBCDD",
    "box_highlight": "#F2A93B",
}
STYLE: dict[str, Any] = {
    "box_width": 3,
    "box_corner_width": 4,
    "history_width": 2,
    "recent_width": 3,
    "history_alpha": [22, 115],
    "recent_alpha": [130, 245],
    "contour_alpha": [95, 145, 190, 230],
    "contour_width": 3,
    "density_fill_alpha_max": 68,
    "glow_radius": 4,
    "glow_alpha_factor": 0.45,
    "panel_alpha": 225,
}
NAMES = (
    "01_video_00s_hook",
    "02_video_05s_flow_metrics",
    "03_video_10s_warning_validation",
    "04_video_15s_tracking",
    "05_video_20s_spatial_pressure",
    "06_video_25s_multi_metric",
    "07_video_30s_state_machine",
    "08_video_35s_validation",
    "09_video_40s_action",
    "10_video_45s_close",
)
# Start, end, original-source start, headline, supporting narrative.
SCENES: tuple[tuple[float, float, float, str, str], ...] = (
    (
        0,
        4,
        1431,
        "BUSY TRAFFIC ≠ CONGESTION",
        "Traffic-camera analytics detect pressure, then independently check for a sustained queue.",
    ),
    (4, 9, 1435, "TRAFFIC PRESSURE WAS BUILDING", "DETECT → TRACK → FLOW METRICS → WARNING"),
    (
        9,
        15,
        1440,
        "WARNING. CONGESTION NOT CONFIRMED.",
        "Higher accumulation + positive imbalance, while traffic continued to discharge.",
    ),
    (
        15,
        20,
        1425,
        "VEHICLES BECOME MOVEMENT EVIDENCE",
        "Anonymous tracks retain original timestamps. Occlusions and fragments remain limitations.",
    ),
    (
        20,
        25,
        1440,
        "ACCUMULATION INSIDE THE ZONE",
        "Contours show accumulated track observations, not physical vehicle density "
        "or a congestion hotspot.",
    ),
    (
        25,
        30,
        1450,
        "NO SINGLE METRIC DEFINES CONGESTION",
        "Occupancy and imbalance rose. Throughput and movement continued; not every "
        "metric deteriorated.",
    ),
    (
        30,
        35,
        1438,
        "MULTIPLE SIGNALS. PERSISTENCE. HYSTERESIS.",
        "NORMAL 23:00 → WATCH 23:03 → WARNING 24:00 → NORMAL 28:57",
    ),
    (
        35,
        40,
        1600,
        "PRESSURE QUALIFIED. QUEUE RULE DID NOT.",
        "The independent configured queue check withheld an unsupported congestion claim.",
    ),
    (
        40,
        44,
        1730,
        "CONSIDER ESCALATING FOR REVIEW",
        "Illustrative response: REVIEW / MONITOR. This prototype does not control traffic.",
    ),
    (
        44,
        45,
        1734,
        "DETECT PRESSURE. VALIDATE CONGESTION.",
        "CAMERA → FLOW → WARNING → VALIDATE → ACT",
    ),
)


def extract_tokens(paths: list[Path]) -> dict[str, Any]:
    """Count exact RGB pixels; fail if a proposed representative token is absent."""
    counts: Counter[tuple[int, ...]] = Counter()
    for path in sorted(paths):
        with Image.open(path) as image:
            counts.update(image.convert("RGB").getdata())
    evidence = {}
    for key, value in TOKENS.items():
        rgb = tuple(bytes.fromhex(value[1:]))
        if counts[rgb] == 0:
            raise ValueError(f"Unsampled original color: {key}")
        evidence[key] = {"hex": value, "exact_pixel_count": counts[rgb]}
    return {
        "build": BUILD,
        "PUBLICATION_STATUS": STATUS,
        "tokens": TOKENS,
        "sampling": evidence,
        "style": STYLE,
        "originals": [{"path": str(p), "sha256": checksum(p)} for p in sorted(paths)],
        "method": "Exact full-resolution RGB counts across original video PNGs.",
        "limits": "Colors are directly observed. Original PNGs show opaque zones and cyan "
        "rectangles, not an identifiable contour-transfer/alpha formula. Blue-cyan-amber "
        "gradient, smaller corner emphasis, fading, translucent fill and glow are documented "
        "adaptations. Alpha cannot be uniquely recovered from composited PNGs.",
    }


def scene_index(seconds: float) -> int:
    if not 0 <= seconds < 45:
        raise ValueError("Presentation time outside [0,45)")
    return next(i for i, scene in enumerate(SCENES) if scene[0] <= seconds < scene[1])


def canonical_metrics(audit: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Validate audited selectors before any display formatting."""
    snapshot = audit["fixed_window_comparisons"][1]
    records = {r["metric_id"]: r for r in audit["records"]}
    if (snapshot["entry"], snapshot["exit"], snapshot["imbalance"]) != (8, 3, 5):
        raise ValueError("New flow result requires editorial review")
    if abs(snapshot["density_mean"] - 3.7) > 1e-10:
        raise ValueError("Stale occupancy")
    if abs(snapshot["movement_index"] - 0.011305435163455783) > 1e-12:
        raise ValueError("Stale movement")
    if records["warning_state"]["exact_value"] != "WARNING":
        raise ValueError("Unsupported state")
    return [
        ("TRAFFIC STATE", "WARNING", "At original time 24:00"),
        ("MEAN ZONE OCCUPANCY", f"{snapshot['density_mean']:.2f}", "Observed tracks / 60s mean"),
        ("ENTRY-EXIT BALANCE", f"{snapshot['imbalance']:+d}", "8 eligible entries / 3 exits"),
        ("THROUGHPUT", str(snapshot["exit"]), "Eligible exits / 60s"),
        ("RELATIVE MOVEMENT", f"{snapshot['movement_index']:.7f}", "Image diagonals/s"),
    ]


def first15_contract() -> dict[str, Any]:
    """Coverage is tied to scene intervals; human comprehension remains a review."""
    concepts = {
        "traffic_camera_source": (0, "Traffic-camera analytics"),
        "detect_and_track": (1, "DETECT → TRACK"),
        "operational_metrics": (1, "FLOW METRICS"),
        "warning_exists": (2, "TRAFFIC WARNING / QUALIFIED"),
        "warning_time": (2, "24:00 original source time"),
        "independent_check": (2, "Independent sustained-queue rule"),
        "congestion_not_confirmed": (2, "CONGESTION / NOT CONFIRMED"),
        "avoid_unsupported_escalation": (
            2,
            "Withhold a congestion claim; consider review / monitor",
        ),
        "conditional_action": (2, "Consider REVIEW / MONITOR"),
    }
    return {
        "build": BUILD,
        "checks": {
            key: {
                "scene": index,
                "visible_interval": list(SCENES[index][:2]),
                "required_text": wording,
                "completed_before_15": SCENES[index][1] <= 15,
            }
            for key, (index, wording) in concepts.items()
        },
        "automated_status": "PENDING_RENDER_VALIDATION",
        "human_comprehension": "REVIEW_REQUIRED",
        "claim_limit": "Withholding an unsupported claim is observable rule behavior; "
        "reduced false alarms/escalations is not independently measured.",
    }


def validate_first15(transcripts: dict[int, list[str]]) -> dict[str, Any]:
    """Check text actually passed to the renderer, not only planned captions."""
    contract = first15_contract()
    required = {
        "traffic_camera_source": (0, ("TRAFFIC-CAMERA",)),
        "detect_and_track": (1, ("DETECT", "TRACK")),
        "operational_metrics": (1, ("FLOW METRICS", "3.70", "+5", "0.0113054")),
        "warning_exists": (2, ("TRAFFIC WARNING", "QUALIFIED")),
        "warning_time": (2, ("24:00",)),
        "independent_check": (2, ("INDEPENDENT SUSTAINED-QUEUE RULE",)),
        "congestion_not_confirmed": (2, ("CONGESTION", "NOT CONFIRMED")),
        "avoid_unsupported_escalation": (2, ("WITHHOLD A CONGESTION CLAIM",)),
        "conditional_action": (2, ("CONSIDER REVIEW / MONITOR",)),
    }
    for key, (index, phrases) in required.items():
        rendered = " ".join(transcripts.get(index, [])).upper()
        contract["checks"][key]["rendered"] = all(p in rendered for p in phrases)
    contract["automated_status"] = (
        "PASS" if all(c["rendered"] for c in contract["checks"].values()) else "FAIL"
    )
    return contract
