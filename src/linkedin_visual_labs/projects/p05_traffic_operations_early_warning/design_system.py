"""Shared tokens sampled from the approved Project 6 PNGs, never analytical inputs."""

from __future__ import annotations

BG = "#091522"
HEADER = "#0B1A2A"
PANEL = "#081623"
INK = "#FFFFFF"
MUTED = "#B7C7D5"
AMBER = "#F2A93B"
CYAN = "#1CBCDD"
BLUE = "#2F80ED"
GREEN = "#2BA668"
RED = "#E04F4F"
PURPLE = "#8655FF"
LIGHT = "#F4F7FA"
DARK_INK = "#152738"
SECONDARY = "#526B82"
BORDER = "#DAE2EA"
CREAM = "#FFF6E1"
FONT_FAMILY = "DejaVu Sans"
VIDEO_SIZE = (1080, 1350)
REPORT_SIZE = (1600, 1000)
HERO_BOX = (0, 103, 1080, 851)
CAPTION_BOX = (55, 890, 1030, 1245)
VIDEO_REFERENCES = (
    "01_video_00s_hook.png",
    "02_video_05s_detection.png",
    "03_video_10s_teaser_result.png",
    "04_video_15s_metric_definition.png",
    "05_video_20s_tracking_challenge.png",
    "06_video_25s_operational_metrics.png",
    "07_video_30s_warning_logic.png",
    "08_video_35s_lead_time.png",
    "09_video_40s_action.png",
    "10_video_45s_close.png",
)
TAB_REFERENCES = (
    "01_dashboard_tab.png",
    "02_video_tab.png",
    "03_method_tab.png",
    "04_results_tab.png",
    "05_about_tab.png",
)
OVERLAY_BOXES: tuple[tuple[int, int, int, int] | None, ...] = (
    None,
    None,
    (676, 151, 1040, 813),
    (560, 171, 1034, 815),
    None,
    (690, 470, 1015, 700),
    (636, 146, 1038, 818),
    None,
    (456, 241, 1020, 765),
    None,
)


def ease(progress: float) -> float:
    """Presentation interpolation only; never rescales the analytical clock."""
    value = min(1.0, max(0.0, progress))
    return value * value * (3 - 2 * value)


def css_tokens() -> str:
    return (
        f":root{{--bg:{LIGHT};--panel:{INK};--text:{DARK_INK};--muted:{SECONDARY};"
        f"--dark:{HEADER};--amber:{AMBER};--blue:{BLUE};--green:{GREEN};"
        f"--cyan:{CYAN};--red:{RED};--border:{BORDER};--cream:{CREAM};}}"
    )
