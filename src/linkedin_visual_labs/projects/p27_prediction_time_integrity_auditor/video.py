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

from PIL import Image, ImageDraw, ImageFont

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
    0.0,
    5.0,
    10.0,
    15.0,
    20.0,
    25.0,
    30.0,
    35.0,
    40.0,
    44.8,
)

KEYFRAME_FILENAMES: Final[tuple[str, ...]] = (
    "01_00s.png",
    "02_05s.png",
    "03_10s.png",
    "04_15s.png",
    "05_20s.png",
    "06_25s.png",
    "07_30s.png",
    "08_35s.png",
    "09_40s.png",
    "10_45s.png",
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


def render_frame(
    release: dict[str, Any],
    claims: dict[str, Any],
    t: float,
) -> Image.Image:
    """Render one deterministic video frame."""

    _approved_claim_ids(claims)

    t = max(
        0.0,
        min(
            VIDEO_DURATION_SECONDS - 1.0 / VIDEO_FPS,
            t,
        ),
    )

    image = _canvas()

    if t < 3.0:
        _scene_apparent_success(
            image,
            release,
            t,
        )

    elif t < 7.0:
        _scene_suspicious_feature(
            image,
            release,
            t,
        )

    elif t < 11.0:
        _scene_timeline(
            image,
            t,
        )

    elif t < 15.0:
        _scene_honest_reveal(
            image,
            release,
            t,
        )

    elif t < 20.0:
        _scene_split(
            image,
            t,
        )

    elif t < 25.0:
        _scene_transformation(
            image,
            t,
        )

    elif t < 30.0:
        _scene_duplicate(
            image,
            release,
            t,
        )

    elif t < 35.0:
        _scene_metric_correction(
            image,
            release,
            t,
        )

    elif t < 40.0:
        _scene_calibration(
            image,
            release,
            t,
        )

    else:
        _scene_gate(
            image,
            release,
            t,
        )

    return image


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
    """Create 2x5 keyframe contact sheet."""

    if len(keyframes) != 10:
        raise RuntimeError("Contact sheet requires ten keyframes.")

    thumb_width = 324
    thumb_height = 405

    sheet = Image.new(
        "RGB",
        (
            thumb_width * 2,
            thumb_height * 5,
        ),
        BACKGROUND,
    )

    for index, path in enumerate(keyframes):
        with Image.open(path) as source:
            thumb = source.resize(
                (
                    thumb_width,
                    thumb_height,
                ),
                Image.Resampling.LANCZOS,
            )

        x = (index % 2) * thumb_width

        y = (index // 2) * thumb_height

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

    keyframe_root = assets_root / "video_keyframes"

    images_root = assets_root / "images"

    video_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    keyframe_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    images_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    primary = video_root / PRIMARY_VIDEO_FILENAME

    web = video_root / WEB_VIDEO_FILENAME

    thumbnail = video_root / THUMBNAIL_FILENAME

    manifest_path = video_root / VIDEO_MANIFEST_FILENAME

    contact_sheet = images_root / "video_keyframe_contact_sheet.png"

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
