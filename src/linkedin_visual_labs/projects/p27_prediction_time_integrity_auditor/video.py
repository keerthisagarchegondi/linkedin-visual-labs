"""Animated Project 7 LinkedIn video from frozen Step 5 evidence."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.design_tokens import (
    canvas_contract,
    hex_to_rgba,
    load_visual_contract,
    palette_color,
    scale_box,
    scale_value,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.text_layout import (
    balanced_greedy_wrap,
    draw_tracked_text,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.visual_primitives import (
    draw_card,
    draw_neural_edge,
    draw_neural_node,
    draw_status_pill,
    linear_gradient,
)

VIDEO_WIDTH: Final = 1080
VIDEO_HEIGHT: Final = 1350
VIDEO_FPS: Final = 30
VIDEO_DURATION_SECONDS: Final = 45.0
VIDEO_FRAME_COUNT: Final = int(VIDEO_FPS * VIDEO_DURATION_SECONDS)

STEP5_FINGERPRINT: Final = "7954203abe1cb0f5457c3658f2105cd16a0800528e81723ee970d259afe60ed0"

PRIMARY_VIDEO_FILENAME: Final = "project7_prediction_time_integrity.mp4"

WEB_VIDEO_FILENAME: Final = "project7_prediction_time_integrity_web.mp4"

THUMBNAIL_FILENAME: Final = "project7_video_thumbnail.png"

VIDEO_MANIFEST_FILENAME: Final = "video_manifest.json"

KEYFRAME_TIMES: Final[tuple[float, ...]] = (
    2.25,
    6.5,
    10.5,
    14.75,
    19.0,
    23.0,
    27.25,
    31.75,
    37.0,
    42.5,
)

KEYFRAME_FILENAMES: Final[tuple[str, ...]] = (
    "scene_01_S1.png",
    "scene_02_S2.png",
    "scene_03_S3.png",
    "scene_04_S4.png",
    "scene_05_S5.png",
    "scene_06_S6.png",
    "scene_07_S7.png",
    "scene_08_S8.png",
    "scene_09_S9.png",
    "scene_10_S10.png",
)

CLAIM_IDS_USED: Final[tuple[str, ...]] = (
    "P7-C001",
    "P7-C002",
    "P7-C003",
    "P7-C004",
    "P7-C006",
    "P7-C008",
)

BACKGROUND: Final = (13, 18, 28)
PANEL: Final = (24, 31, 44)
TEXT: Final = (244, 247, 250)
MUTED: Final = (174, 184, 197)
ACCENT: Final = (82, 158, 255)
ACCENT_2: Final = (125, 231, 205)
WARN: Final = (255, 190, 92)
BLOCK: Final = (248, 113, 113)
PASS: Final = (99, 218, 139)
GRID: Final = (61, 72, 91)


@dataclass(
    frozen=True,
    slots=True,
)
class VideoContract:
    width: int = VIDEO_WIDTH
    height: int = VIDEO_HEIGHT
    fps: int = VIDEO_FPS
    duration_seconds: float = VIDEO_DURATION_SECONDS
    frame_count: int = VIDEO_FRAME_COUNT

    def to_dict(
        self,
    ) -> dict[str, object]:
        return {
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration_seconds": self.duration_seconds,
            "frame_count": self.frame_count,
        }


def load_video_evidence(
    assets_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    """Load frozen public evidence only."""

    release_raw: object = json.loads(
        (assets_root / "release_data.json").read_text(encoding="utf-8")
    )

    claims_raw: object = json.loads(
        (assets_root / "claim_register.json").read_text(encoding="utf-8")
    )

    if not isinstance(
        release_raw,
        dict,
    ):
        raise TypeError("release_data.json is not an object.")

    if not isinstance(
        claims_raw,
        dict,
    ):
        raise TypeError("claim_register.json is not an object.")

    if release_raw.get("step5_fingerprint_sha256") != STEP5_FINGERPRINT:
        raise RuntimeError("Video release-data fingerprint drift.")

    if release_raw.get("release_status") != "PASS":
        raise RuntimeError("Step 5 release is not PASS.")

    return release_raw, claims_raw


def file_sha256(
    path: Path,
) -> str:
    """Return SHA256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def _font(
    size: int,
    *,
    bold: bool = False,
) -> Any:
    candidates: list[Path] = []
    if bold:
        candidates.extend(
            (
                Path(r"C:\Windows\Fonts\arialbd.ttf"),
                Path(r"C:\Windows\Fonts\segoeuib.ttf"),
            )
        )
    else:
        candidates.extend(
            (
                Path(r"C:\Windows\Fonts\arial.ttf"),
                Path(r"C:\Windows\Fonts\segoeui.ttf"),
            )
        )

    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(
                str(path),
                size=size,
            )

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"

    return ImageFont.truetype(
        name,
        size=size,
    )


def _ease(
    value: float,
) -> float:
    value = max(
        0.0,
        min(
            1.0,
            value,
        ),
    )

    return value * value * (3.0 - 2.0 * value)


def _progress(
    t: float,
    start: float,
    end: float,
) -> float:
    if end <= start:
        return 1.0

    return _ease((t - start) / (end - start))


def _canvas() -> Image.Image:
    return Image.new(
        "RGB",
        (
            VIDEO_WIDTH,
            VIDEO_HEIGHT,
        ),
        BACKGROUND,
    )


def _draw_text_center(
    draw: Any,
    xy: tuple[int, int],
    text: str,
    font: Any,
    fill: tuple[int, int, int] = TEXT,
) -> None:
    box = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=font,
    )

    width = box[2] - box[0]

    draw.text(
        (
            xy[0] - width // 2,
            xy[1],
        ),
        text,
        font=font,
        fill=fill,
    )


def _title(
    draw: Any,
    title: str,
    subtitle: str,
) -> None:
    draw.text(
        (
            72,
            65,
        ),
        title,
        font=_font(
            52,
            bold=True,
        ),
        fill=TEXT,
    )

    draw.text(
        (
            74,
            132,
        ),
        subtitle,
        font=_font(
            25,
        ),
        fill=MUTED,
    )


def _footer(
    draw: Any,
    label: str,
) -> None:
    draw.text(
        (
            72,
            1290,
        ),
        label,
        font=_font(
            20,
            bold=True,
        ),
        fill=MUTED,
    )


def _panel(
    draw: Any,
    box: tuple[
        int,
        int,
        int,
        int,
    ],
    *,
    radius: int = 28,
) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=PANEL,
    )


def _bar(
    draw: Any,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    progress: float,
    label: str,
    value: str,
    color: tuple[int, int, int],
) -> None:
    draw.text(
        (
            x,
            y - 44,
        ),
        label,
        font=_font(
            25,
            bold=True,
        ),
        fill=TEXT,
    )

    draw.rounded_rectangle(
        (
            x,
            y,
            x + width,
            y + height,
        ),
        radius=height // 2,
        fill=GRID,
    )

    visible = int(
        width
        * max(
            0.0,
            min(
                1.0,
                progress,
            ),
        )
    )

    if visible > 0:
        draw.rounded_rectangle(
            (
                x,
                y,
                x + visible,
                y + height,
            ),
            radius=height // 2,
            fill=color,
        )

    draw.text(
        (
            x + width + 24,
            y - 5,
        ),
        value,
        font=_font(
            24,
            bold=True,
        ),
        fill=TEXT,
    )


def _case_model_row(
    release: dict[str, Any],
    case_id: str,
    model_id: str,
) -> dict[str, Any]:
    rows = release["leakage_model_results"]

    if not isinstance(
        rows,
        list,
    ):
        raise RuntimeError("leakage_model_results missing.")

    matches = [
        row
        for row in rows
        if (
            isinstance(
                row,
                dict,
            )
            and row.get("case_id") == case_id
            and row.get("model_id") == model_id
        )
    ]

    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one leakage result for {case_id}/{model_id}.")

    return matches[0]


def _approved_claim_ids(
    claims: dict[str, Any],
) -> set[str]:
    raw = claims.get("claims")

    if not isinstance(
        raw,
        list,
    ):
        raise RuntimeError("Claim register entries missing.")

    approved = {
        str(claim.get("claim_id"))
        for claim in raw
        if (
            isinstance(
                claim,
                dict,
            )
            and claim.get("approved_for_public_use") is True
        )
    }

    missing = set(CLAIM_IDS_USED) - approved

    if missing:
        raise RuntimeError(f"Video references unapproved claims: {sorted(missing)}")

    return approved


def _scene_apparent_success(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    safe = float(row["safe_roc_auc"])

    leaked = float(row["leaked_roc_auc"])

    p = _progress(
        t,
        0.0,
        2.8,
    )

    value = safe + (leaked - safe) * p

    _title(
        draw,
        "The model looks production-ready.",
        "Until you ask when each feature actually exists.",
    )

    _panel(
        draw,
        (
            80,
            250,
            1000,
            1050,
        ),
    )

    _draw_text_center(
        draw,
        (
            540,
            330,
        ),
        "APPARENT ROC AUC",
        _font(
            28,
            bold=True,
        ),
        MUTED,
    )

    _draw_text_center(
        draw,
        (
            540,
            405,
        ),
        f"{value:.3f}",
        _font(
            118,
            bold=True,
        ),
        ACCENT,
    )

    gauge_x = 170
    gauge_y = 650
    gauge_width = 740

    draw.rounded_rectangle(
        (
            gauge_x,
            gauge_y,
            gauge_x + gauge_width,
            gauge_y + 70,
        ),
        radius=35,
        fill=GRID,
    )

    fill = int(
        gauge_width
        * max(
            0.0,
            min(
                1.0,
                value,
            ),
        )
    )

    draw.rounded_rectangle(
        (
            gauge_x,
            gauge_y,
            gauge_x + fill,
            gauge_y + 70,
        ),
        radius=35,
        fill=ACCENT,
    )

    draw.text(
        (
            170,
            775,
        ),
        f"Prediction-time-safe reference: {safe:.3f}",
        font=_font(
            27,
        ),
        fill=MUTED,
    )

    draw.text(
        (
            170,
            830,
        ),
        "Current-call duration included",
        font=_font(
            27,
            bold=True,
        ),
        fill=WARN,
    )

    _footer(
        draw,
        "Observed dataset condition • Claim P7-C002",
    )


def _scene_suspicious_feature(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    roc = float(row["reported_effect_roc_auc"])

    pr = float(row["reported_effect_pr_auc"])

    yield_over = float(row["campaign_yield_overstatement"])

    p = _progress(
        t,
        3.0,
        6.7,
    )

    _title(
        draw,
        "A suspicious signal appears.",
        "Duration exists during the call—not when ranking happens.",
    )

    _panel(
        draw,
        (
            75,
            240,
            1005,
            1110,
        ),
    )

    draw.text(
        (
            130,
            305,
        ),
        "Measured duration leakage effects",
        font=_font(
            32,
            bold=True,
        ),
        fill=TEXT,
    )

    # No feature importance was frozen in Step 5.
    # These bars show measured leakage effects instead of
    # fabricating importance values.

    _bar(
        draw,
        x=140,
        y=455,
        width=560,
        height=54,
        progress=p
        * min(
            1.0,
            roc / 0.15,
        ),
        label="ROC AUC uplift",
        value=f"+{roc:.3f}",
        color=ACCENT,
    )

    _bar(
        draw,
        x=140,
        y=650,
        width=560,
        height=54,
        progress=p
        * min(
            1.0,
            pr / 0.15,
        ),
        label="PR AUC uplift",
        value=f"+{pr:.3f}",
        color=ACCENT_2,
    )

    _bar(
        draw,
        x=140,
        y=845,
        width=560,
        height=54,
        progress=p
        * min(
            1.0,
            yield_over / 180.0,
        ),
        label="Yield overstatement",
        value=f"+{yield_over:.1f}/1k",
        color=WARN,
    )

    draw.text(
        (
            140,
            995,
        ),
        "Feature-importance values were not frozen,",
        font=_font(
            23,
        ),
        fill=MUTED,
    )

    draw.text(
        (
            140,
            1030,
        ),
        "so this video does not invent them.",
        font=_font(
            23,
            bold=True,
        ),
        fill=MUTED,
    )

    _footer(
        draw,
        "Measured effects from S1_CURRENT_CALL_DURATION",
    )


def _scene_timeline(
    image: Image.Image,
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    _title(
        draw,
        "Prediction time is a hard boundary.",
        "A feature is usable only if it exists before the decision.",
    )

    _panel(
        draw,
        (
            70,
            270,
            1010,
            1070,
        ),
    )

    start_x = 150
    end_x = 920
    y = 600

    draw.line(
        (
            start_x,
            y,
            end_x,
            y,
        ),
        fill=MUTED,
        width=8,
    )

    positions = (
        (
            230,
            "Before call",
            PASS,
        ),
        (
            460,
            "Prediction",
            ACCENT,
        ),
        (
            680,
            "During call",
            WARN,
        ),
        (
            890,
            "After outcome",
            BLOCK,
        ),
    )

    for x, label, color in positions:
        draw.ellipse(
            (
                x - 16,
                y - 16,
                x + 16,
                y + 16,
            ),
            fill=color,
        )

        _draw_text_center(
            draw,
            (
                x,
                y + 55,
            ),
            label,
            _font(
                22,
                bold=True,
            ),
            color,
        )

    p = _progress(
        t,
        7.0,
        10.7,
    )

    duration_x = int(460 + (680 - 460) * p)

    draw.rounded_rectangle(
        (
            duration_x - 125,
            380,
            duration_x + 125,
            475,
        ),
        radius=24,
        fill=WARN,
    )

    _draw_text_center(
        draw,
        (
            duration_x,
            404,
        ),
        "duration",
        _font(
            29,
            bold=True,
        ),
        BACKGROUND,
    )

    draw.line(
        (
            duration_x,
            475,
            duration_x,
            570,
        ),
        fill=WARN,
        width=5,
    )

    draw.text(
        (
            150,
            840,
        ),
        "Prediction happens here",
        font=_font(
            33,
            bold=True,
        ),
        fill=ACCENT,
    )

    draw.text(
        (
            150,
            900,
        ),
        "duration exists later → BLOCK",
        font=_font(
            30,
            bold=True,
        ),
        fill=BLOCK,
    )

    _footer(
        draw,
        "Prediction-time availability contract",
    )


def _scene_honest_reveal(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    leaked = float(row["leaked_roc_auc"])

    safe = float(row["safe_roc_auc"])

    p = _progress(
        t,
        11.0,
        14.7,
    )

    _title(
        draw,
        "The model did not become worse.",
        "The evaluation became honest.",
    )

    _panel(
        draw,
        (
            75,
            265,
            1005,
            1060,
        ),
    )

    left = 175
    right = 625
    top = 430
    bottom = 900

    draw.rectangle(
        (
            left,
            top,
            left + 230,
            bottom,
        ),
        fill=GRID,
    )

    leaked_height = int(400 * leaked)

    draw.rectangle(
        (
            left,
            bottom - leaked_height,
            left + 230,
            bottom,
        ),
        fill=WARN,
    )

    draw.rectangle(
        (
            right,
            top,
            right + 230,
            bottom,
        ),
        fill=GRID,
    )

    safe_visible = int(400 * (leaked + (safe - leaked) * p))

    draw.rectangle(
        (
            right,
            bottom - safe_visible,
            right + 230,
            bottom,
        ),
        fill=ACCENT_2,
    )

    _draw_text_center(
        draw,
        (
            left + 115,
            940,
        ),
        "Leaked",
        _font(
            28,
            bold=True,
        ),
        WARN,
    )

    _draw_text_center(
        draw,
        (
            right + 115,
            940,
        ),
        "Prediction-safe",
        _font(
            28,
            bold=True,
        ),
        ACCENT_2,
    )

    _draw_text_center(
        draw,
        (
            left + 115,
            350,
        ),
        f"{leaked:.3f}",
        _font(
            48,
            bold=True,
        ),
        TEXT,
    )

    _draw_text_center(
        draw,
        (
            right + 115,
            350,
        ),
        f"{safe:.3f}",
        _font(
            48,
            bold=True,
        ),
        TEXT,
    )

    draw.text(
        (
            160,
            1020,
        ),
        "Leakage case: BLOCK",
        font=_font(
            25,
            bold=True,
        ),
        fill=BLOCK,
    )

    draw.text(
        (
            610,
            1020,
        ),
        "Safe pipeline: PASS",
        font=_font(
            25,
            bold=True,
        ),
        fill=PASS,
    )

    _footer(
        draw,
        "Claim P7-C001 • Safe pipeline release PASS",
    )


def _scene_split(
    image: Image.Image,
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    _title(
        draw,
        "Random mixing can hide time.",
        "Deployability evidence uses source-order chronology.",
    )

    _panel(
        draw,
        (
            65,
            250,
            1015,
            1110,
        ),
    )

    p = _progress(
        t,
        15.0,
        19.7,
    )

    count = 40

    for index in range(count):
        random_x = 130 + (index * 163) % 820

        random_y = 380 + (index * 91) % 500

        if index < 28:
            target_x = 115 + (index % 7) * 62

            target_y = 380 + (index // 7) * 105

            color = ACCENT

        elif index < 34:
            local = index - 28

            target_x = 600 + (local % 3) * 62

            target_y = 380 + (local // 3) * 105

            color = WARN

        else:
            local = index - 34

            target_x = 820 + (local % 3) * 62

            target_y = 380 + (local // 3) * 105

            color = ACCENT_2

        x = int(random_x + (target_x - random_x) * p)

        y = int(random_y + (target_y - random_y) * p)

        draw.ellipse(
            (
                x - 15,
                y - 15,
                x + 15,
                y + 15,
            ),
            fill=color,
        )

    draw.text(
        (
            115,
            955,
        ),
        "Past training • 70%",
        font=_font(
            25,
            bold=True,
        ),
        fill=ACCENT,
    )

    draw.text(
        (
            555,
            955,
        ),
        "Later validation • 15%",
        font=_font(
            25,
            bold=True,
        ),
        fill=WARN,
    )

    draw.text(
        (
            790,
            1010,
        ),
        "Future test • 15%",
        font=_font(
            25,
            bold=True,
        ),
        fill=ACCENT_2,
    )

    _footer(
        draw,
        "Chronological source-order evaluation • Claims P7-C003 / P7-C004",
    )


def _scene_transformation(
    image: Image.Image,
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    _title(
        draw,
        "Transformation order matters.",
        "Supervised transformations must be learned on training data only.",
    )

    _panel(
        draw,
        (
            65,
            250,
            1015,
            1120,
        ),
    )

    p = _progress(
        t,
        20.0,
        24.7,
    )

    y_bad = 460
    y_good = 820

    labels_bad = (
        "Full dataset",
        "Supervised\ntransform",
        "Split",
    )

    labels_good = (
        "Split first",
        "Fit on\ntraining",
        "Transform\nval/test",
    )

    for row_y, labels, valid in (
        (
            y_bad,
            labels_bad,
            False,
        ),
        (
            y_good,
            labels_good,
            True,
        ),
    ):
        for index, label in enumerate(labels):
            x = 120 + index * 330

            visible = p >= index / 3

            fill = PASS if valid else BLOCK

            draw.rounded_rectangle(
                (
                    x,
                    row_y,
                    x + 235,
                    row_y + 120,
                ),
                radius=25,
                fill=fill if visible else GRID,
            )

            lines = label.split("\n")

            for line_index, line in enumerate(lines):
                _draw_text_center(
                    draw,
                    (
                        x + 117,
                        row_y + 34 + line_index * 34,
                    ),
                    line,
                    _font(
                        22,
                        bold=True,
                    ),
                    BACKGROUND if visible else MUTED,
                )

            if index < 2:
                draw.line(
                    (
                        x + 245,
                        row_y + 60,
                        x + 310,
                        row_y + 60,
                    ),
                    fill=MUTED,
                    width=6,
                )

        draw.text(
            (
                870,
                row_y + 38,
            ),
            "VALID" if valid else "BLOCK",
            font=_font(
                25,
                bold=True,
            ),
            fill=PASS if valid else BLOCK,
        )

    draw.text(
        (
            120,
            345,
        ),
        "Contaminated",
        font=_font(
            26,
            bold=True,
        ),
        fill=BLOCK,
    )

    draw.text(
        (
            120,
            705,
        ),
        "Prediction-safe",
        font=_font(
            26,
            bold=True,
        ),
        fill=PASS,
    )

    _footer(
        draw,
        "Controlled transformation-boundary injection",
    )


def _scene_duplicate(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    overlap = int(release["independent_validation"]["duplicate_train_test_overlap"])

    _title(
        draw,
        "Train and test must be independent.",
        "Duplicate rows crossing the boundary contaminate evaluation.",
    )

    _panel(
        draw,
        (
            65,
            250,
            1015,
            1110,
        ),
    )

    train_box = (
        120,
        385,
        445,
        910,
    )

    test_box = (
        635,
        385,
        960,
        910,
    )

    draw.rounded_rectangle(
        train_box,
        radius=28,
        outline=ACCENT,
        width=5,
    )

    draw.rounded_rectangle(
        test_box,
        radius=28,
        outline=ACCENT_2,
        width=5,
    )

    _draw_text_center(
        draw,
        (
            282,
            320,
        ),
        "TRAIN",
        _font(
            28,
            bold=True,
        ),
        ACCENT,
    )

    _draw_text_center(
        draw,
        (
            797,
            320,
        ),
        "TEST",
        _font(
            28,
            bold=True,
        ),
        ACCENT_2,
    )

    p = _progress(
        t,
        25.0,
        29.6,
    )

    sample = 12

    for index in range(sample):
        y = 430 + index * 37

        x1 = 405
        x2 = int(x1 + (670 - x1) * p)

        draw.line(
            (
                x1,
                y,
                x2,
                y + 24,
            ),
            fill=BLOCK,
            width=4,
        )

        draw.ellipse(
            (
                x1 - 8,
                y - 8,
                x1 + 8,
                y + 8,
            ),
            fill=BLOCK,
        )

        draw.ellipse(
            (
                x2 - 8,
                y + 16,
                x2 + 8,
                y + 32,
            ),
            fill=BLOCK,
        )

    _draw_text_center(
        draw,
        (
            540,
            970,
        ),
        f"{overlap}",
        _font(
            72,
            bold=True,
        ),
        BLOCK,
    )

    _draw_text_center(
        draw,
        (
            540,
            1060,
        ),
        "detected duplicate overlaps",
        _font(
            25,
            bold=True,
        ),
        TEXT,
    )

    _footer(
        draw,
        "Controlled injection • Claim P7-C006",
    )


def _scene_metric_correction(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    p = _progress(
        t,
        30.0,
        34.7,
    )

    _title(
        draw,
        "Metric correction changes the decision.",
        "Leaked and prediction-time-safe results tell different stories.",
    )

    _panel(
        draw,
        (
            65,
            245,
            1015,
            1130,
        ),
    )

    primary = (
        (
            "ROC AUC",
            float(row["safe_roc_auc"]),
            float(row["leaked_roc_auc"]),
        ),
        (
            "PR AUC",
            float(row["safe_pr_auc"]),
            float(row["leaked_pr_auc"]),
        ),
        (
            "Conversions / 1k",
            float(row["safe_conversions_per_1000"]),
            float(row["leaked_conversions_per_1000"]),
        ),
    )

    y = 360

    for label, safe, leaked in primary:
        draw.text(
            (
                120,
                y,
            ),
            label,
            font=_font(
                24,
                bold=True,
            ),
            fill=TEXT,
        )

        draw.text(
            (
                455,
                y,
            ),
            f"{safe:.3f}" if safe < 10 else f"{safe:.1f}",
            font=_font(
                27,
                bold=True,
            ),
            fill=ACCENT_2,
        )

        current_leaked = safe + (leaked - safe) * p

        draw.text(
            (
                720,
                y,
            ),
            f"{current_leaked:.3f}" if current_leaked < 10 else f"{current_leaked:.1f}",
            font=_font(
                27,
                bold=True,
            ),
            fill=WARN,
        )

        draw.line(
            (
                120,
                y + 55,
                940,
                y + 55,
            ),
            fill=GRID,
            width=2,
        )

        y += 175

    draw.text(
        (
            450,
            300,
        ),
        "SAFE",
        font=_font(
            21,
            bold=True,
        ),
        fill=ACCENT_2,
    )

    draw.text(
        (
            715,
            300,
        ),
        "LEAKED",
        font=_font(
            21,
            bold=True,
        ),
        fill=WARN,
    )

    safe_brier = float(row["safe_brier_score"])

    leaked_brier = float(row["leaked_brier_score"])

    safe_lift = float(row["safe_top_decile_lift"])

    leaked_lift = float(row["leaked_top_decile_lift"])

    draw.text(
        (
            120,
            930,
        ),
        (f"Brier: {safe_brier:.3f} safe vs {leaked_brier:.3f} leaked"),
        font=_font(
            23,
        ),
        fill=MUTED,
    )

    draw.text(
        (
            120,
            982,
        ),
        (f"Top-decile lift: {safe_lift:.2f} safe vs {leaked_lift:.2f} leaked"),
        font=_font(
            23,
        ),
        fill=MUTED,
    )

    _footer(
        draw,
        "Measured metrics • frozen Step 5 release data",
    )


def _scene_calibration(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    safe_slope = float(row["safe_calibration_slope"])

    safe_intercept = float(row["safe_calibration_intercept"])

    leaked_slope = float(row["leaked_calibration_slope"])

    leaked_intercept = float(row["leaked_calibration_intercept"])

    safe_ece = float(row["safe_expected_calibration_error"])

    leaked_ece = float(row["leaked_expected_calibration_error"])

    _title(
        draw,
        "Calibration must survive honest evaluation.",
        "Predicted probabilities should correspond to observed outcomes.",
    )

    _panel(
        draw,
        (
            70,
            245,
            1010,
            1115,
        ),
    )

    left = 165
    top = 360
    size = 680

    draw.line(
        (
            left,
            top + size,
            left + size,
            top + size,
        ),
        fill=MUTED,
        width=4,
    )

    draw.line(
        (
            left,
            top,
            left,
            top + size,
        ),
        fill=MUTED,
        width=4,
    )

    draw.line(
        (
            left,
            top + size,
            left + size,
            top,
        ),
        fill=GRID,
        width=3,
    )

    p = _progress(
        t,
        35.0,
        39.7,
    )

    def point(
        x_value: float,
        slope: float,
        intercept: float,
    ) -> tuple[int, int]:
        y_value = max(
            0.0,
            min(
                1.0,
                intercept + slope * x_value,
            ),
        )

        return (
            int(left + x_value * size),
            int(top + size - y_value * size),
        )

    samples = 30

    safe_points = [
        point(
            i / (samples - 1),
            safe_slope,
            safe_intercept,
        )
        for i in range(samples)
    ]

    leaked_points = [
        point(
            i / (samples - 1),
            leaked_slope,
            leaked_intercept,
        )
        for i in range(samples)
    ]

    visible = max(
        2,
        int(samples * p),
    )

    draw.line(
        safe_points[:visible],
        fill=ACCENT_2,
        width=7,
    )

    draw.line(
        leaked_points[:visible],
        fill=WARN,
        width=7,
    )

    draw.text(
        (
            875,
            445,
        ),
        "Safe",
        font=_font(
            22,
            bold=True,
        ),
        fill=ACCENT_2,
    )

    draw.text(
        (
            875,
            495,
        ),
        f"ECE {safe_ece:.3f}",
        font=_font(
            20,
        ),
        fill=MUTED,
    )

    draw.text(
        (
            875,
            600,
        ),
        "Leaked",
        font=_font(
            22,
            bold=True,
        ),
        fill=WARN,
    )

    draw.text(
        (
            875,
            650,
        ),
        f"ECE {leaked_ece:.3f}",
        font=_font(
            20,
        ),
        fill=MUTED,
    )

    draw.text(
        (
            165,
            1075,
        ),
        "Calibration fit derived from frozen slope/intercept values",
        font=_font(
            20,
        ),
        fill=MUTED,
    )

    _footer(
        draw,
        "No synthetic calibration bins were invented",
    )


def _scene_gate(
    image: Image.Image,
    release: dict[str, Any],
    t: float,
) -> None:
    draw = ImageDraw.Draw(image)

    status = str(release["safe_release_decision"])

    _title(
        draw,
        "Deployment requires an integrity gate.",
        "Evidence first. Metrics second. Release only when both hold.",
    )

    _panel(
        draw,
        (
            70,
            245,
            1010,
            1090,
        ),
    )

    checks = (
        "Feature availability",
        "Temporal split",
        "Transformation boundary",
        "Duplicate overlap",
        "Calibration stability",
    )

    p = _progress(
        t,
        40.0,
        44.3,
    )

    for index, label in enumerate(checks):
        threshold = (index + 1) / len(checks)

        visible = p >= threshold

        y = 350 + index * 120

        draw.ellipse(
            (
                135,
                y,
                183,
                y + 48,
            ),
            fill=PASS if visible else GRID,
        )

        if visible:
            draw.line(
                (
                    146,
                    y + 23,
                    158,
                    y + 36,
                    176,
                    y + 10,
                ),
                fill=BACKGROUND,
                width=5,
            )

        draw.text(
            (
                220,
                y + 4,
            ),
            label,
            font=_font(
                27,
                bold=True,
            ),
            fill=TEXT if visible else MUTED,
        )

    gate_color = PASS if status == "PASS" else WARN if status == "WARN" else BLOCK

    draw.rounded_rectangle(
        (
            690,
            900,
            930,
            1010,
        ),
        radius=30,
        fill=gate_color,
    )

    _draw_text_center(
        draw,
        (
            810,
            930,
        ),
        status,
        _font(
            40,
            bold=True,
        ),
        BACKGROUND,
    )

    _draw_text_center(
        draw,
        (
            540,
            1160,
        ),
        "Evaluation integrity is a production requirement—",
        _font(
            28,
            bold=True,
        ),
        TEXT,
    )

    _draw_text_center(
        draw,
        (
            540,
            1203,
        ),
        "not a documentation task.",
        _font(
            28,
            bold=True,
        ),
        TEXT,
    )

    _footer(
        draw,
        "Safe release decision • Claim P7-C001",
    )


# =====================================================================
# VISUAL UPLIFT V1.0
# Frozen ten-scene renderer.
#
# Encoder / probe / output machinery below this section is intentionally
# preserved from the historical Step 6 release.
# =====================================================================

UPLIFT_SCENE_SCHEDULE: Final[
    tuple[
        tuple[
            str,
            float,
            float,
        ],
        ...,
    ]
] = (
    ("S1", 0.0, 4.5),
    ("S2", 4.5, 8.5),
    ("S3", 8.5, 12.5),
    ("S4", 12.5, 17.0),
    ("S5", 17.0, 21.0),
    ("S6", 21.0, 25.0),
    ("S7", 25.0, 29.5),
    ("S8", 29.5, 34.0),
    ("S9", 34.0, 40.0),
    ("S10", 40.0, 45.0),
)


_UPLIFT_MODEL_LABELS: Final = {
    "histogram_gradient_boosting": ("Histogram Gradient Boosting"),
    "logistic_regression": ("Logistic Regression"),
}


_UPLIFT_CASE_LABELS: Final = {
    "S1_CURRENT_CALL_DURATION": ("Current-call duration"),
    "S2_RANDOM_TEMPORAL_MIXING": ("Random temporal mixing"),
    "S3_GLOBAL_SUPERVISED_TRANSFORMATION": ("Global supervised transform"),
    "S4_DUPLICATE_OVERLAP": ("Duplicate overlap"),
    "S5_POST_OUTCOME_CONFIRMATION_PROXY": ("Post-outcome proxy"),
}


def uplift_scene_id_for_time(
    t: float,
) -> str:
    """Return frozen V1.0 scene ID for a video timestamp."""

    clamped = max(
        0.0,
        min(
            VIDEO_DURATION_SECONDS - 1.0 / VIDEO_FPS,
            t,
        ),
    )

    for (
        scene_id,
        start,
        end,
    ) in UPLIFT_SCENE_SCHEDULE:
        if start <= clamped < end:
            return scene_id

    return "S10"


def _uplift_scene_window(
    t: float,
) -> tuple[
    str,
    float,
    float,
    float,
]:
    """Return scene ID, start, end and local eased progress."""

    scene_id = uplift_scene_id_for_time(t)

    for (
        candidate,
        start,
        end,
    ) in UPLIFT_SCENE_SCHEDULE:
        if candidate == scene_id:
            duration = end - start

            local = max(
                0.0,
                min(
                    1.0,
                    (t - start) / duration,
                ),
            )

            return (
                scene_id,
                start,
                end,
                _ease(local),
            )

    raise RuntimeError(f"Unknown uplift scene: {scene_id}")


def _uplift_canvas() -> Image.Image:
    """Return supersampled frozen Visual Contract canvas."""

    contract = canvas_contract()

    return Image.new(
        "RGBA",
        (
            contract.internal_width_px,
            contract.internal_height_px,
        ),
        hex_to_rgba(palette_color("bg")),
    )


def _uplift_rect(
    image: Image.Image,
    box: tuple[
        int | float,
        int | float,
        int | float,
        int | float,
    ],
    *,
    fill: str,
    radius: int = 0,
    outline: str | None = None,
    width: int = 1,
) -> None:
    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    scaled = scale_box(box)

    if radius > 0:
        draw.rounded_rectangle(
            scaled,
            radius=scale_value(radius),
            fill=hex_to_rgba(fill),
            outline=(hex_to_rgba(outline) if outline else None),
            width=scale_value(width),
        )
    else:
        draw.rectangle(
            scaled,
            fill=hex_to_rgba(fill),
            outline=(hex_to_rgba(outline) if outline else None),
            width=scale_value(width),
        )


def _uplift_text(
    image: Image.Image,
    x: int | float,
    y: int | float,
    text: str,
    *,
    role: str,
    color: str,
    anchor: str = "la",
) -> None:
    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    draw_tracked_text(
        draw,
        (
            scale_value(x),
            scale_value(y),
        ),
        text,
        role=role,
        fill=color,
        anchor=anchor,
        supersampled=True,
    )


def _uplift_wrapped(
    image: Image.Image,
    x: int,
    y: int,
    text: str,
    *,
    role: str,
    color: str,
    max_width: int,
    max_lines: int,
    line_height: int,
) -> int:
    lines = balanced_greedy_wrap(
        text,
        role=role,
        max_width_px=max_width,
        max_lines=max_lines,
        min_words_on_last_line=2,
    )

    cursor = y

    for line in lines:
        _uplift_text(
            image,
            x,
            cursor,
            line,
            role=role,
            color=color,
        )

        cursor += line_height

    return cursor


def _uplift_shadow_card(
    image: Image.Image,
    box: tuple[
        int,
        int,
        int,
        int,
    ],
    *,
    fill: str = "#FFFFFF",
    border: str = "#DEE6F0",
) -> None:
    x1, y1, x2, y2 = scale_box(box)

    shadow = Image.new(
        "RGBA",
        image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        shadow,
        "RGBA",
    )

    draw.rounded_rectangle(
        (
            x1,
            y1 + scale_value(8),
            x2,
            y2 + scale_value(8),
        ),
        radius=scale_value(16),
        fill=(
            14,
            28,
            47,
            20,
        ),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(scale_value(14)))

    image.alpha_composite(shadow)

    draw_card(
        image,
        box,
        fill=fill,
        border=border,
        radius_px=16,
    )


def _uplift_header(
    image: Image.Image,
) -> None:
    contract = load_visual_contract()

    header = contract["header"]

    _uplift_rect(
        image,
        (
            0,
            0,
            1080,
            84,
        ),
        fill=str(header["background_color"]),
    )

    _uplift_text(
        image,
        24,
        18,
        str(header["left_project_kicker"]["text"]),
        role="header_kicker",
        color=str(header["left_project_kicker"]["color"]),
    )

    _uplift_text(
        image,
        24,
        36,
        str(header["left_title"]["text"]),
        role="header_title",
        color=str(header["left_title"]["color"]),
    )

    pill = header["right_pill"]

    x = int(pill["x_px"])

    y = int(pill["y_px"])

    width = int(pill["width_px"])

    height = int(pill["height_px"])

    gradient = linear_gradient(
        (
            scale_value(width),
            scale_value(height),
        ),
        hex_to_rgba(str(pill["fill_gradient"][0])),
        hex_to_rgba(str(pill["fill_gradient"][1])),
    )

    mask = Image.new(
        "L",
        gradient.size,
        0,
    )

    mask_draw = ImageDraw.Draw(mask)

    mask_draw.rounded_rectangle(
        (
            0,
            0,
            gradient.size[0] - 1,
            gradient.size[1] - 1,
        ),
        radius=scale_value(14),
        fill=255,
    )

    image.paste(
        gradient,
        (
            scale_value(x),
            scale_value(y),
        ),
        mask,
    )

    _uplift_text(
        image,
        x + width / 2,
        y + 6,
        str(pill["text"]),
        role="header_pill",
        color=str(pill["text_color"]),
        anchor="ma",
    )


def _uplift_footer(
    image: Image.Image,
    t: float,
) -> None:
    contract = load_visual_contract()

    footer = contract["footer_progress"]

    _uplift_rect(
        image,
        (
            0,
            1304,
            1080,
            1332,
        ),
        fill=str(footer["background_color"]),
    )

    progress = max(
        0.0,
        min(
            1.0,
            t / VIDEO_DURATION_SECONDS,
        ),
    )

    track = footer["progress_track"]

    x = float(track["x_px"])

    y = float(track["y_px"])

    width = float(track["width_px"])

    height = float(track["height_px"])

    _uplift_rect(
        image,
        (
            x,
            y,
            x + width,
            y + height,
        ),
        fill=str(track["track_color"]),
    )

    _uplift_rect(
        image,
        (
            x,
            y,
            x + width * progress,
            y + height,
        ),
        fill=str(track["fill_color"]),
    )

    knob_x = x + width * progress

    knob_y = y + height / 2

    knob = scale_value(int(track["knob_radius_px"]))

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    draw.ellipse(
        (
            scale_value(knob_x) - knob,
            scale_value(knob_y) - knob,
            scale_value(knob_x) + knob,
            scale_value(knob_y) + knob,
        ),
        fill=hex_to_rgba(str(track["fill_color"])),
    )

    seconds = max(
        0,
        min(
            44,
            int(t),
        ),
    )

    timestamp = f"00:{seconds:02d} / 00:45"

    _uplift_text(
        image,
        1030,
        1310,
        timestamp,
        role="timestamp",
        color="#D8E0EA",
        anchor="ra",
    )


def _uplift_headline(
    image: Image.Image,
    scene_id: str,
) -> int:
    contract = load_visual_contract()

    scene = next(item for item in contract["scene_sequence"] if item["scene_id"] == scene_id)

    lines = tuple(str(value) for value in scene["headline"])

    accent_index = scene.get("accent_line_index")

    accent = scene.get("accent_color")

    y = 124

    for index, line in enumerate(lines):
        color = (
            str(accent)
            if (accent is not None and accent_index == index)
            else palette_color("text_primary")
        )

        role = (
            "hero_headline_accent"
            if (accent is not None and accent_index == index)
            else "hero_headline"
        )

        _uplift_text(
            image,
            48,
            y,
            line,
            role=role,
            color=color,
        )

        y += 58

    return y


def _uplift_metric(
    image: Image.Image,
    *,
    x: int,
    y: int,
    label: str,
    value: str,
    tone: str = "info",
    width: int = 220,
) -> None:
    palette = {
        "info": (
            "#EAF3FF",
            "#CFE0FF",
            "#3C82F6",
        ),
        "pass": (
            "#EAF8F0",
            "#CDEFD9",
            "#1F9E62",
        ),
        "warn": (
            "#FFF4E5",
            "#F8D7A5",
            "#CC7A00",
        ),
        "block": (
            "#FFECEC",
            "#F7C1C1",
            "#E45858",
        ),
    }

    fill, border, text_color = palette[tone]

    _uplift_rect(
        image,
        (
            x,
            y,
            x + width,
            y + 86,
        ),
        fill=fill,
        radius=14,
        outline=border,
    )

    _uplift_text(
        image,
        x + 16,
        y + 12,
        label,
        role="micro",
        color=palette_color("text_secondary"),
    )

    _uplift_text(
        image,
        x + 16,
        y + 39,
        value,
        role="card_value_small",
        color=text_color,
    )


def _uplift_bar(
    image: Image.Image,
    *,
    x: int,
    y: int,
    width: int,
    ratio: float,
    color: str,
    label: str,
    value: str,
) -> None:
    ratio = max(
        0.0,
        min(
            1.0,
            ratio,
        ),
    )

    _uplift_text(
        image,
        x,
        y,
        label,
        role="body",
        color=palette_color("text_secondary"),
    )

    _uplift_text(
        image,
        x + width,
        y,
        value,
        role="body_bold",
        color=palette_color("text_primary"),
        anchor="ra",
    )

    _uplift_rect(
        image,
        (
            x,
            y + 32,
            x + width,
            y + 50,
        ),
        fill="#EAF0F6",
        radius=8,
    )

    _uplift_rect(
        image,
        (
            x,
            y + 32,
            x
            + max(
                4,
                width * ratio,
            ),
            y + 50,
        ),
        fill=color,
        radius=8,
    )


def _uplift_baseline_row(
    release: dict[str, Any],
    *,
    model_id: str,
    partition: str,
) -> dict[str, Any]:
    raw = release.get("baseline_model_results")

    if not isinstance(
        raw,
        list,
    ):
        raise RuntimeError("baseline_model_results missing.")

    matches = [
        row
        for row in raw
        if (
            isinstance(
                row,
                dict,
            )
            and row.get("pipeline_id") == "C_PREDICTION_TIME_SAFE"
            and row.get("model_id") == model_id
            and row.get("partition") == partition
        )
    ]

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one Pipeline C baseline row "
            f"for {model_id}/{partition}; "
            f"found {len(matches)}."
        )

    return matches[0]


def _uplift_scene_s1(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S1",
    )

    validation = _uplift_baseline_row(
        release,
        model_id=("histogram_gradient_boosting"),
        partition="validation",
    )

    roc = float(validation["roc_auc"])

    pr = float(validation["pr_auc"])

    s1 = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 36,
            1032,
            1058,
        ),
    )

    visible_roc = roc * p
    visible_pr = pr * p

    _uplift_metric(
        image,
        x=82,
        y=bottom + 86,
        label="VALIDATION ROC AUC",
        value=f"{visible_roc:.3f}",
        tone="info",
        width=270,
    )

    _uplift_metric(
        image,
        x=380,
        y=bottom + 86,
        label="VALIDATION PR AUC",
        value=f"{visible_pr:.3f}",
        tone="info",
        width=270,
    )

    _uplift_metric(
        image,
        x=678,
        y=bottom + 86,
        label="SAFE RELEASE",
        value=str(release["safe_release_decision"]),
        tone="pass",
        width=270,
    )

    _uplift_bar(
        image,
        x=82,
        y=bottom + 250,
        width=866,
        ratio=visible_roc,
        color=palette_color("blue_500"),
        label="Headline validation signal",
        value=f"{visible_roc:.3f}",
    )

    _uplift_wrapped(
        image,
        82,
        bottom + 370,
        (
            "One production-time violation is enough "
            "to invalidate an otherwise strong-looking score."
        ),
        role="subhead",
        color=palette_color("text_secondary"),
        max_width=780,
        max_lines=3,
        line_height=26,
    )

    draw_status_pill(
        image,
        xy=(
            82,
            bottom + 520,
        ),
        text=str(s1["actual_auditor_result"]),
        status="block",
    )


def _uplift_scene_s2(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S2",
    )

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    roc_effect = float(row["reported_effect_roc_auc"])

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 34,
            1032,
            1080,
        ),
        fill="#FFFDFD",
        border="#F7C1C1",
    )

    _uplift_metric(
        image,
        x=80,
        y=bottom + 76,
        label="VIOLATING FEATURE",
        value="duration",
        tone="block",
        width=260,
    )

    _uplift_metric(
        image,
        x=368,
        y=bottom + 76,
        label="AVAILABILITY",
        value="DURING ACTION",
        tone="warn",
        width=272,
    )

    _uplift_metric(
        image,
        x=668,
        y=bottom + 76,
        label="AUDITOR RESULT",
        value="BLOCK",
        tone="block",
        width=276,
    )

    start = (
        196,
        bottom + 350,
    )

    middle = (
        540,
        bottom + 350,
    )

    end = (
        884,
        bottom + 350,
    )

    draw_neural_edge(
        image,
        start=start,
        end=middle,
    )

    draw_neural_edge(
        image,
        start=middle,
        end=end,
    )

    draw_neural_node(
        image,
        center=start,
        active=False,
    )

    draw_neural_node(
        image,
        center=middle,
        active=True,
    )

    draw_neural_node(
        image,
        center=end,
        active=False,
    )

    particle_x = start[0] + (end[0] - start[0]) * p

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    radius = scale_value(5)

    px = scale_value(particle_x)

    py = scale_value(start[1])

    draw.ellipse(
        (
            px - radius,
            py - radius,
            px + radius,
            py + radius,
        ),
        fill=hex_to_rgba(palette_color("red_600")),
    )

    _uplift_text(
        image,
        196,
        bottom + 408,
        "Prediction",
        role="micro",
        color=palette_color("text_secondary"),
        anchor="ma",
    )

    _uplift_text(
        image,
        540,
        bottom + 408,
        "Current call",
        role="micro",
        color=palette_color("red_600"),
        anchor="ma",
    )

    _uplift_text(
        image,
        884,
        bottom + 408,
        "Outcome",
        role="micro",
        color=palette_color("text_secondary"),
        anchor="ma",
    )

    _uplift_metric(
        image,
        x=80,
        y=bottom + 530,
        label="MEASURED ROC-AUC EFFECT",
        value=f"+{roc_effect:.3f}",
        tone="block",
        width=330,
    )

    _uplift_wrapped(
        image,
        448,
        bottom + 534,
        (
            "The value exists after ranking starts, "
            "so the model has information unavailable "
            "at deployment time."
        ),
        role="body",
        color=palette_color("text_secondary"),
        max_width=470,
        max_lines=4,
        line_height=24,
    )


def _uplift_scene_s3(
    image: Image.Image,
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S3",
    )

    rows = (
        (
            "Age / job / education",
            "PRE-DECISION",
            "pass",
            "ALLOW",
        ),
        (
            "Previous campaign context",
            "PRE-DECISION",
            "pass",
            "ALLOW",
        ),
        (
            "Campaign",
            "UNKNOWN",
            "block",
            "BLOCK",
        ),
        (
            "Duration",
            "DURING ACTION",
            "block",
            "BLOCK",
        ),
        (
            "Outcome proxy",
            "POST OUTCOME",
            "block",
            "BLOCK",
        ),
    )

    start_y = bottom + 28

    visible_rows = max(
        1,
        min(
            len(rows),
            int(p * (len(rows) + 1)),
        ),
    )

    for index, (
        feature,
        availability,
        status,
        result,
    ) in enumerate(rows):
        y = start_y + index * 150

        _uplift_shadow_card(
            image,
            (
                48,
                y,
                1032,
                y + 126,
            ),
        )

        if index < visible_rows:
            _uplift_text(
                image,
                72,
                y + 22,
                feature,
                role="card_title",
                color=palette_color("text_primary"),
            )

            _uplift_text(
                image,
                72,
                y + 60,
                availability,
                role="micro",
                color=palette_color("text_secondary"),
            )

            draw_status_pill(
                image,
                xy=(
                    860,
                    y + 48,
                ),
                text=result,
                status=status,
            )


def _uplift_scene_s4(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S4",
    )

    raw = release.get("leakage_model_results")

    if not isinstance(
        raw,
        list,
    ):
        raise RuntimeError("leakage_model_results missing.")

    cases = []

    for case_id in (
        "S1_CURRENT_CALL_DURATION",
        "S2_RANDOM_TEMPORAL_MIXING",
        "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
        "S4_DUPLICATE_OVERLAP",
        "S5_POST_OUTCOME_CONFIRMATION_PROXY",
    ):
        matches = [
            row
            for row in raw
            if (
                isinstance(
                    row,
                    dict,
                )
                and row.get("case_id") == case_id
            )
        ]

        if not matches:
            raise RuntimeError(f"Missing leakage case: {case_id}")

        status = str(matches[0]["actual_auditor_result"])

        cases.append(
            (
                case_id,
                status,
            )
        )

    for index, (
        case_id,
        status,
    ) in enumerate(cases):
        y = bottom + 32 + index * 158

        _uplift_shadow_card(
            image,
            (
                48,
                y,
                1032,
                y + 130,
            ),
        )

        _uplift_metric(
            image,
            x=72,
            y=y + 22,
            label=f"SCENARIO {index + 1}",
            value=(f"S{index + 1}"),
            tone="info",
            width=150,
        )

        _uplift_wrapped(
            image,
            250,
            y + 30,
            _UPLIFT_CASE_LABELS[case_id],
            role="body_bold",
            color=palette_color("text_primary"),
            max_width=440,
            max_lines=2,
            line_height=24,
        )

        if p >= (index + 1) / len(cases):
            draw_status_pill(
                image,
                xy=(
                    864,
                    y + 50,
                ),
                text=status,
                status=("block" if status == "BLOCK" else "warn"),
            )


def _uplift_scene_s5(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S5",
    )

    row = _case_model_row(
        release,
        "S2_RANDOM_TEMPORAL_MIXING",
        "histogram_gradient_boosting",
    )

    chronological = float(row["safe_roc_auc"])

    random = float(row["leaked_roc_auc"])

    gap = float(release["independent_validation"]["temporal_roc_auc_gap"])

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 52,
            1032,
            1050,
        ),
    )

    _uplift_metric(
        image,
        x=80,
        y=bottom + 98,
        label="VALIDATED GAP",
        value=f"+{gap:.3f}",
        tone="warn",
        width=250,
    )

    _uplift_bar(
        image,
        x=80,
        y=bottom + 280,
        width=870,
        ratio=(chronological * p),
        color=palette_color("blue_500"),
        label="Chronological holdout",
        value=f"{chronological:.3f}",
    )

    _uplift_bar(
        image,
        x=80,
        y=bottom + 410,
        width=870,
        ratio=(random * p),
        color=palette_color("amber_600"),
        label="Random temporal mixing",
        value=f"{random:.3f}",
    )

    _uplift_wrapped(
        image,
        80,
        bottom + 590,
        (
            "Random mixing lets later-period information "
            "change the apparent answer. Deployment uses "
            "chronological evidence."
        ),
        role="subhead",
        color=palette_color("text_secondary"),
        max_width=830,
        max_lines=3,
        line_height=26,
    )


def _uplift_scene_s6(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S6",
    )

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    before = float(row["leaked_roc_auc"])

    after = float(row["safe_roc_auc"])

    inflation = float(row["reported_effect_roc_auc"])

    animated = before + (after - before) * p

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 42,
            1032,
            1050,
        ),
    )

    _uplift_text(
        image,
        540,
        bottom + 118,
        "ROC AUC",
        role="card_title",
        color=palette_color("text_secondary"),
        anchor="ma",
    )

    _uplift_text(
        image,
        540,
        bottom + 180,
        f"{animated:.3f}",
        role="hero_headline_accent",
        color=palette_color("blue_500"),
        anchor="ma",
    )

    _uplift_metric(
        image,
        x=160,
        y=bottom + 340,
        label="LEAKED",
        value=f"{before:.3f}",
        tone="block",
        width=280,
    )

    _uplift_metric(
        image,
        x=640,
        y=bottom + 340,
        label="PREDICTION-SAFE",
        value=f"{after:.3f}",
        tone="pass",
        width=280,
    )

    _uplift_metric(
        image,
        x=400,
        y=bottom + 500,
        label="LEAKAGE INFLATION",
        value=f"+{inflation:.3f}",
        tone="warn",
        width=280,
    )


def _uplift_scene_s7(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S7",
    )

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    safe = float(row["safe_conversions_per_1000"])

    leaked = float(row["leaked_conversions_per_1000"])

    delta = float(row["campaign_yield_overstatement"])

    maximum = (
        max(
            safe,
            leaked,
        )
        * 1.05
    )

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 42,
            1032,
            1080,
        ),
    )

    _uplift_metric(
        image,
        x=80,
        y=bottom + 86,
        label="PLANNING OVERSTATEMENT",
        value=f"+{delta:.1f} / 1K",
        tone="block",
        width=320,
    )

    _uplift_bar(
        image,
        x=80,
        y=bottom + 280,
        width=870,
        ratio=(safe / maximum * p),
        color=palette_color("blue_500"),
        label="Supported safe test yield",
        value=f"{safe:.1f} / 1K",
    )

    _uplift_bar(
        image,
        x=80,
        y=bottom + 420,
        width=870,
        ratio=(leaked / maximum * p),
        color=palette_color("red_600"),
        label="Leaked planning yield",
        value=f"{leaked:.1f} / 1K",
    )

    _uplift_wrapped(
        image,
        80,
        bottom + 608,
        (
            "Evaluation error becomes a business-planning error "
            "when inflated ranking performance is converted into "
            "campaign expectations."
        ),
        role="subhead",
        color=palette_color("text_secondary"),
        max_width=830,
        max_lines=4,
        line_height=26,
    )


def _uplift_scene_s8(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S8",
    )

    checks = (
        "Feature availability",
        "Temporal split",
        "Transform boundary",
        "Duplicate overlap",
        "Calibration",
    )

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 30,
            1032,
            1084,
        ),
    )

    lane_y = bottom + 312

    start_x = 116
    gap = 186

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    draw.rounded_rectangle(
        scale_box(
            (
                88,
                lane_y,
                980,
                lane_y + 18,
            )
        ),
        radius=scale_value(9),
        fill=hex_to_rgba("#EAF0F6"),
    )

    for index, label in enumerate(checks):
        x = start_x + index * gap

        _uplift_rect(
            image,
            (
                x - 70,
                lane_y - 80,
                x + 70,
                lane_y - 26,
            ),
            fill="#FFFFFF",
            radius=12,
            outline="#CBD6E3",
        )

        _uplift_text(
            image,
            x,
            lane_y - 64,
            str(index + 1),
            role="card_title",
            color=palette_color("navy_800"),
            anchor="ma",
        )

        _uplift_wrapped(
            image,
            x - 70,
            lane_y + 54,
            label,
            role="micro",
            color=palette_color("text_secondary"),
            max_width=140,
            max_lines=2,
            line_height=14,
        )

    token_x = 88 + (892 * p)

    _uplift_rect(
        image,
        (
            token_x - 12,
            lane_y + 1,
            token_x + 12,
            lane_y + 17,
        ),
        fill=palette_color("red_600"),
        radius=6,
    )

    draw_neural_edge(
        image,
        start=(
            180,
            bottom + 620,
        ),
        end=(
            540,
            bottom + 620,
        ),
    )

    draw_neural_edge(
        image,
        start=(
            540,
            bottom + 620,
        ),
        end=(
            900,
            bottom + 620,
        ),
    )

    draw_neural_node(
        image,
        center=(
            180,
            bottom + 620,
        ),
    )

    draw_neural_node(
        image,
        center=(
            540,
            bottom + 620,
        ),
        active=True,
    )

    draw_neural_node(
        image,
        center=(
            900,
            bottom + 620,
        ),
    )

    draw_status_pill(
        image,
        xy=(
            470,
            bottom + 726,
        ),
        text=str(release["safe_release_decision"]),
        status="pass",
    )


def _uplift_scene_s9(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    _uplift_rect(
        image,
        (
            0,
            84,
            1080,
            1304,
        ),
        fill=palette_color("navy_900"),
    )

    bottom = _uplift_headline(
        image,
        "S9",
    )

    row = _case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    status = str(row["actual_auditor_result"])

    _uplift_rect(
        image,
        (
            80,
            bottom + 72,
            1000,
            1080,
        ),
        fill="#18314B",
        radius=20,
        outline="#274B70",
    )

    _uplift_text(
        image,
        540,
        bottom + 130,
        "DEPLOYMENT GATE",
        role="card_title",
        color="#B9C6D8",
        anchor="ma",
    )

    reveal = "BLOCK" if p >= 0.30 else "..."

    _uplift_text(
        image,
        540,
        bottom + 196,
        reveal,
        role="hero_headline_accent",
        color=palette_color("red_600"),
        anchor="ma",
    )

    _uplift_metric(
        image,
        x=132,
        y=bottom + 390,
        label="CRITICAL FINDING",
        value="duration",
        tone="block",
        width=300,
    )

    _uplift_metric(
        image,
        x=648,
        y=bottom + 390,
        label="AVAILABILITY",
        value="DURING ACTION",
        tone="warn",
        width=300,
    )

    if p >= 0.55:
        _uplift_wrapped(
            image,
            132,
            bottom + 560,
            (
                "Required corrective action: remove unavailable "
                "prediction-time inputs and rerun deployment-aligned "
                "evaluation before release."
            ),
            role="subhead",
            color="#D8E0EA",
            max_width=800,
            max_lines=4,
            line_height=26,
        )

    if p >= 0.80:
        draw_status_pill(
            image,
            xy=(
                486,
                bottom + 750,
            ),
            text=status,
            status="block",
        )


def _uplift_scene_s10(
    image: Image.Image,
    release: dict[str, Any],
    p: float,
) -> None:
    bottom = _uplift_headline(
        image,
        "S10",
    )

    validation = release["independent_validation"]

    _uplift_shadow_card(
        image,
        (
            48,
            bottom + 40,
            1032,
            1072,
        ),
    )

    cards = (
        (
            "SCENARIOS",
            str(validation["scenario_count"]),
            "info",
        ),
        (
            "MODEL RESULTS",
            str(validation["model_result_count"]),
            "info",
        ),
        (
            "RECONCILED EFFECTS",
            str(validation["reconciled_metric_effect_count"]),
            "pass",
        ),
        (
            "MISMATCHES",
            str(validation["metric_effect_mismatch_count"]),
            "pass",
        ),
    )

    positions = (
        (
            82,
            bottom + 100,
        ),
        (
            558,
            bottom + 100,
        ),
        (
            82,
            bottom + 250,
        ),
        (
            558,
            bottom + 250,
        ),
    )

    visible = max(
        1,
        min(
            4,
            int(p * 5),
        ),
    )

    for index, (
        label,
        value,
        tone,
    ) in enumerate(cards):
        if index >= visible:
            continue

        x, y = positions[index]

        _uplift_metric(
            image,
            x=x,
            y=y,
            label=label,
            value=value,
            tone=tone,
            width=392,
        )

    if p >= 0.68:
        _uplift_wrapped(
            image,
            82,
            bottom + 470,
            (
                "Frozen evidence package: benchmark results, leakage "
                "scenarios, independent reconciliation, claim register, "
                "research figures, and deterministic media."
            ),
            role="subhead",
            color=palette_color("text_secondary"),
            max_width=850,
            max_lines=4,
            line_height=26,
        )

    if p >= 0.86:
        draw_status_pill(
            image,
            xy=(
                482,
                bottom + 700,
            ),
            text=str(release["safe_release_decision"]),
            status="pass",
        )


def render_frame(
    release: dict[str, Any],
    claims: dict[str, Any],
    t: float,
) -> Image.Image:
    """Render one frozen Visual Contract V1.0 video frame."""

    _approved_claim_ids(claims)

    t = max(
        0.0,
        min(
            VIDEO_DURATION_SECONDS - 1.0 / VIDEO_FPS,
            t,
        ),
    )

    (
        scene_id,
        _start,
        _end,
        progress,
    ) = _uplift_scene_window(t)

    image = _uplift_canvas()

    if scene_id == "S1":
        _uplift_scene_s1(
            image,
            release,
            progress,
        )

    elif scene_id == "S2":
        _uplift_scene_s2(
            image,
            release,
            progress,
        )

    elif scene_id == "S3":
        _uplift_scene_s3(
            image,
            progress,
        )

    elif scene_id == "S4":
        _uplift_scene_s4(
            image,
            release,
            progress,
        )

    elif scene_id == "S5":
        _uplift_scene_s5(
            image,
            release,
            progress,
        )

    elif scene_id == "S6":
        _uplift_scene_s6(
            image,
            release,
            progress,
        )

    elif scene_id == "S7":
        _uplift_scene_s7(
            image,
            release,
            progress,
        )

    elif scene_id == "S8":
        _uplift_scene_s8(
            image,
            release,
            progress,
        )

    elif scene_id == "S9":
        _uplift_scene_s9(
            image,
            release,
            progress,
        )

    elif scene_id == "S10":
        _uplift_scene_s10(
            image,
            release,
            progress,
        )

    else:
        raise RuntimeError(f"Unknown uplift scene: {scene_id}")

    _uplift_header(image)

    _uplift_footer(
        image,
        t,
    )

    contract = canvas_contract()

    final = image.convert("RGB").resize(
        (
            contract.width_px,
            contract.height_px,
        ),
        Image.Resampling.LANCZOS,
    )

    return final


def _ffmpeg_path() -> Path:
    """Resolve deterministic FFmpeg executable."""

    discovered = shutil.which("ffmpeg")

    if discovered:
        return Path(discovered).resolve()

    try:
        import imageio_ffmpeg  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError("No FFmpeg provider available.") from exc

    path = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()

    if not path.is_file():
        raise RuntimeError("imageio-ffmpeg executable missing.")

    return path


def _ffprobe_path(
    ffmpeg: Path,
) -> Path:
    """Resolve ffprobe next to FFmpeg or from PATH."""

    discovered = shutil.which("ffprobe")

    if discovered:
        return Path(discovered).resolve()

    candidates = (
        ffmpeg.with_name("ffprobe.exe"),
        ffmpeg.with_name("ffprobe.EXE"),
        ffmpeg.with_name("ffprobe"),
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise RuntimeError("ffprobe could not be resolved.")


def _encode_primary(
    release: dict[str, Any],
    claims: dict[str, Any],
    output: Path,
) -> None:
    """Encode primary 1080x1350 H.264 video from generated frames."""

    ffmpeg = _ffmpeg_path()

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        str(ffmpeg),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s:v",
        f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}",
        "-r",
        str(VIDEO_FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if process.stdin is None:
        raise RuntimeError("FFmpeg stdin unavailable.")

    try:
        for frame_index in range(VIDEO_FRAME_COUNT):
            t = frame_index / VIDEO_FPS

            frame = render_frame(
                release,
                claims,
                t,
            )

            process.stdin.write(frame.tobytes())

            if frame_index % 150 == 0:
                print(
                    "VIDEO FRAME",
                    frame_index,
                    "/",
                    VIDEO_FRAME_COUNT,
                )

    finally:
        process.stdin.close()

    return_code = process.wait()

    stderr = process.stderr.read() if process.stderr is not None else b""

    if return_code != 0:
        raise RuntimeError(
            "FFmpeg primary encode failed:\n"
            + stderr.decode(
                "utf-8",
                errors="replace",
            )
        )

    if not output.is_file() or output.stat().st_size < 100_000:
        raise RuntimeError("Primary video output invalid.")


def _encode_web(
    primary: Path,
    output: Path,
) -> None:
    """Encode optimized web copy."""

    ffmpeg = _ffmpeg_path()

    command = [
        str(ffmpeg),
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(primary),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Web video encode failed:\n"
            + result.stderr.decode(
                "utf-8",
                errors="replace",
            )
        )

    if not output.is_file() or output.stat().st_size < 100_000:
        raise RuntimeError("Web video output invalid.")


def _probe_video(
    path: Path,
) -> dict[str, Any]:
    """Probe encoded video using ffprobe."""

    ffmpeg = _ffmpeg_path()

    ffprobe = _ffprobe_path(ffmpeg)

    command = [
        str(ffprobe),
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        (
            "stream=codec_name,pix_fmt,width,height,"
            "avg_frame_rate,nb_frames,duration:"
            "format=duration,size"
        ),
        "-of",
        "json",
        str(path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError("ffprobe failed:\n" + result.stderr)

    payload: object = json.loads(result.stdout)

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError("ffprobe JSON invalid.")

    streams = payload.get("streams")

    if (
        not isinstance(
            streams,
            list,
        )
        or len(streams) != 1
        or not isinstance(
            streams[0],
            dict,
        )
    ):
        raise RuntimeError("Expected one ffprobe video stream.")

    stream = streams[0]

    format_data = payload.get("format")

    if not isinstance(
        format_data,
        dict,
    ):
        raise RuntimeError("ffprobe format metadata missing.")

    frame_rate = str(
        stream.get(
            "avg_frame_rate",
            "0/1",
        )
    )

    numerator_text, denominator_text = frame_rate.split(
        "/",
        1,
    )

    numerator = float(numerator_text)

    denominator = float(denominator_text)

    fps = numerator / denominator if denominator else 0.0

    duration_text = stream.get("duration") or format_data.get("duration")

    if duration_text is None:
        raise RuntimeError("ffprobe duration metadata missing.")

    return {
        "path": path.name,
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "codec": str(stream.get("codec_name")),
        "pixel_format": str(stream.get("pix_fmt")),
        "frame_rate": fps,
        "nb_frames": (
            int(stream["nb_frames"])
            if str(
                stream.get(
                    "nb_frames",
                    "",
                )
            ).isdigit()
            else None
        ),
        "duration_seconds": float(duration_text),
        "size_bytes": int(
            format_data.get(
                "size",
                path.stat().st_size,
            )
        ),
        "sha256": file_sha256(path),
    }


def _validate_probe(
    probe: dict[str, Any],
) -> None:
    """Validate media contract from ffprobe result."""

    if probe["width"] != VIDEO_WIDTH:
        raise RuntimeError(f"Video width mismatch: {probe}")

    if probe["height"] != VIDEO_HEIGHT:
        raise RuntimeError(f"Video height mismatch: {probe}")

    if probe["codec"] != "h264":
        raise RuntimeError(f"Video codec mismatch: {probe}")

    if probe["pixel_format"] != "yuv420p":
        raise RuntimeError(f"Video pixel format mismatch: {probe}")

    if not math.isclose(
        float(probe["frame_rate"]),
        VIDEO_FPS,
        rel_tol=0.0,
        abs_tol=0.01,
    ):
        raise RuntimeError(f"Video frame rate mismatch: {probe}")

    duration = float(probe["duration_seconds"])

    if not (44.0 <= duration <= 46.5):
        raise RuntimeError(f"Video duration outside contract: {probe}")

    frame_count = probe.get("nb_frames")

    if (
        isinstance(
            frame_count,
            int,
        )
        and abs(frame_count - VIDEO_FRAME_COUNT) > 1
    ):
        raise RuntimeError(f"Video frame count mismatch: {probe}")


def _write_keyframes(
    release: dict[str, Any],
    claims: dict[str, Any],
    keyframe_root: Path,
) -> tuple[Path, ...]:
    """Render ten deterministic checkpoint PNGs."""

    keyframe_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = []

    for timestamp, filename in zip(
        KEYFRAME_TIMES,
        KEYFRAME_FILENAMES,
        strict=True,
    ):
        frame = render_frame(
            release,
            claims,
            timestamp,
        )

        path = keyframe_root / filename

        frame.save(
            path,
            format="PNG",
            optimize=True,
        )

        outputs.append(path)

    return tuple(outputs)


def _write_contact_sheet(
    keyframes: tuple[Path, ...],
    output: Path,
) -> None:
    """Create frozen Visual Contract 5x2 keyframe contact sheet."""

    if len(keyframes) != 10:
        raise RuntimeError("Contact sheet requires ten keyframes.")

    thumb_width = 180
    thumb_height = 225
    columns = 5
    rows = 2
    padding = 20

    sheet_width = columns * thumb_width + (columns + 1) * padding

    sheet_height = rows * thumb_height + (rows + 1) * padding

    sheet = Image.new(
        "RGB",
        (
            sheet_width,
            sheet_height,
        ),
        palette_color("bg"),
    )

    for index, path in enumerate(keyframes):
        with Image.open(path) as source:
            thumb = source.convert("RGB").resize(
                (
                    thumb_width,
                    thumb_height,
                ),
                Image.Resampling.LANCZOS,
            )

        column = index % columns
        row = index // columns

        x = padding + column * (thumb_width + padding)

        y = padding + row * (thumb_height + padding)

        sheet.paste(
            thumb,
            (
                x,
                y,
            ),
        )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    sheet.save(
        output,
        format="PNG",
        optimize=True,
    )


def _write_thumbnail(
    release: dict[str, Any],
    claims: dict[str, Any],
    output: Path,
) -> None:
    """Render primary social thumbnail."""

    frame = render_frame(
        release,
        claims,
        12.8,
    )

    frame.save(
        output,
        format="PNG",
        optimize=True,
    )


def build_video_outputs(
    assets_root: Path,
) -> dict[str, Any]:
    """Build and validate every required Step 6 video artifact."""

    release, claims = load_video_evidence(assets_root)

    approved = _approved_claim_ids(claims)

    if not set(CLAIM_IDS_USED).issubset(approved):
        raise RuntimeError("Claim approval validation failed.")

    video_root = assets_root / "video"

    keyframe_root = video_root / "keyframes"

    video_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    keyframe_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    primary = video_root / PRIMARY_VIDEO_FILENAME

    web = video_root / WEB_VIDEO_FILENAME

    thumbnail = video_root / THUMBNAIL_FILENAME

    manifest_path = video_root / VIDEO_MANIFEST_FILENAME

    contact_sheet = video_root / "project7_prediction_time_integrity_contact_sheet.png"

    _encode_primary(
        release,
        claims,
        primary,
    )

    _encode_web(
        primary,
        web,
    )

    keyframes = _write_keyframes(
        release,
        claims,
        keyframe_root,
    )

    _write_contact_sheet(
        keyframes,
        contact_sheet,
    )

    _write_thumbnail(
        release,
        claims,
        thumbnail,
    )

    primary_probe = _probe_video(primary)

    web_probe = _probe_video(web)

    _validate_probe(primary_probe)

    _validate_probe(web_probe)

    release_path = assets_root / "release_data.json"

    keyframe_records = [
        {
            "index": index + 1,
            "timestamp_seconds": timestamp,
            "filename": path.name,
            "sha256": file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for index, (
            timestamp,
            path,
        ) in enumerate(
            zip(
                KEYFRAME_TIMES,
                keyframes,
                strict=True,
            )
        )
    ]

    manifest: dict[
        str,
        Any,
    ] = {
        "scope": "PROJECT7_STEP6_VIDEO",
        "contract": VideoContract().to_dict(),
        "primary_video": primary_probe,
        "web_video": web_probe,
        "thumbnail": {
            "filename": thumbnail.name,
            "sha256": file_sha256(thumbnail),
            "size_bytes": thumbnail.stat().st_size,
        },
        "keyframes": keyframe_records,
        "keyframe_count": len(keyframes),
        "keyframe_contact_sheet": {
            "filename": contact_sheet.name,
            "sha256": file_sha256(contact_sheet),
            "size_bytes": contact_sheet.stat().st_size,
        },
        "claim_ids": list(CLAIM_IDS_USED),
        "release_data": {
            "filename": release_path.name,
            "sha256": file_sha256(release_path),
            "step5_fingerprint_sha256": STEP5_FINGERPRINT,
        },
        "evidence_policy": {
            "business_logic_recomputed": False,
            "preview_metrics_used": False,
            "fabricated_feature_importance": False,
            "fabricated_calibration_bins": False,
            "feature_effect_animation_source": ("S1 measured leakage effects"),
            "calibration_animation_source": ("frozen slope/intercept/ECE values"),
        },
        "muted_comprehension": True,
        "audio_required": False,
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest["manifest_sha256"] = file_sha256(manifest_path)

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return manifest
