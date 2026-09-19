"""Project 7 research-figure rendering.

All public research figures consume frozen Step 5 evidence and use
the frozen Step 6 visual system. Rendering is deterministic and
supersampled at 2x before LANCZOS downsampling.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Final

from PIL import Image, ImageDraw, ImageFilter

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.design_tokens import (
    canvas_contract,
    hex_to_rgba,
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
    draw_status_pill,
    linear_gradient,
)

CANVAS_DPI: Final = 144

EXPECTED_STEP5_FINGERPRINT: Final = (
    "7954203abe1cb0f5457c3658f2105cd16a0800528e81723ee970d259afe60ed0"
)

FIGURE_FILES: Final[tuple[str, ...]] = (
    "audit_pipeline.png",
    "business_targeting_distortion.png",
    "calibration_comparison.png",
    "feature_availability_contract.png",
    "leakage_inflation_map.png",
    "model_performance_comparison.png",
    "split_integrity_comparison.png",
)

_MODEL_LABELS: Final = {
    "histogram_gradient_boosting": "Histogram Gradient Boosting",
    "logistic_regression": "Logistic Regression",
}

_SCENARIO_LABELS: Final = {
    "S1_CURRENT_CALL_DURATION": "S1 · Current-call duration",
    "S2_RANDOM_TEMPORAL_MIXING": "S2 · Random temporal mixing",
    "S3_GLOBAL_SUPERVISED_TRANSFORMATION": "S3 · Global supervised transform",
    "S4_DUPLICATE_OVERLAP": "S4 · Duplicate overlap",
    "S5_POST_OUTCOME_CONFIRMATION_PROXY": "S5 · Post-outcome proxy",
}


def _load_json(
    path: Path,
) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(f"Expected JSON object: {path}")

    return payload


def load_release_context(
    assets_root: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    """Load frozen Step 5 release evidence."""

    release = _load_json(assets_root / "release_data.json")

    claims = _load_json(assets_root / "claim_register.json")

    fingerprint = release.get("step5_fingerprint_sha256")

    if fingerprint != EXPECTED_STEP5_FINGERPRINT:
        raise RuntimeError("Step 5 release fingerprint mismatch.")

    return (
        release,
        claims,
    )


def _baseline_lookup(
    release: dict[str, Any],
    pipeline_id: str,
    partition: str,
) -> list[dict[str, Any]]:
    """Return deterministic baseline model rows."""

    raw = release.get("baseline_model_results")

    if not isinstance(
        raw,
        list,
    ):
        raise RuntimeError("baseline_model_results missing.")

    accepted_partitions = {
        partition,
    }

    if partition == "chronological_test":
        accepted_partitions.add("test")

    rows = [
        row
        for row in raw
        if isinstance(
            row,
            dict,
        )
        and row.get("pipeline_id") == pipeline_id
        and str(row.get("partition")) in accepted_partitions
    ]

    rows.sort(key=lambda row: str(row.get("model_id")))

    if not rows:
        raise RuntimeError(f"No matching baseline rows for {pipeline_id}/{partition}.")

    return rows


def _internal_canvas() -> Image.Image:
    contract = canvas_contract()

    return Image.new(
        "RGBA",
        (
            contract.internal_width_px,
            contract.internal_height_px,
        ),
        hex_to_rgba(palette_color("bg")),
    )


def _draw_rect(
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

    if radius:
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


def _soft_card(
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
    """Draw visual-contract card with soft shadow."""

    x1, y1, x2, y2 = box

    sx1, sy1, sx2, sy2 = scale_box(box)

    margin = scale_value(36)

    shadow_layer = Image.new(
        "RGBA",
        image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    shadow_draw = ImageDraw.Draw(
        shadow_layer,
        "RGBA",
    )

    shadow_draw.rounded_rectangle(
        (
            sx1,
            sy1 + scale_value(8),
            sx2,
            sy2 + scale_value(8),
        ),
        radius=scale_value(16),
        fill=(
            14,
            28,
            47,
            22,
        ),
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(scale_value(14)))

    image.alpha_composite(shadow_layer)

    _ = margin

    draw_card(
        image,
        (
            x1,
            y1,
            x2,
            y2,
        ),
        fill=fill,
        border=border,
        radius_px=16,
    )


def _text(
    image: Image.Image,
    x: int | float,
    y: int | float,
    value: str,
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
        value,
        role=role,
        fill=color,
        anchor=anchor,
        supersampled=True,
    )


def _wrapped_text(
    image: Image.Image,
    x: int,
    y: int,
    value: str,
    *,
    role: str,
    color: str,
    max_width: int,
    line_height: int,
    max_lines: int,
) -> int:
    lines = balanced_greedy_wrap(
        value,
        role=role,
        max_width_px=max_width,
        max_lines=max_lines,
        min_words_on_last_line=2,
    )

    cursor = y

    for line in lines:
        _text(
            image,
            x,
            cursor,
            line,
            role=role,
            color=color,
        )

        cursor += line_height

    return cursor


def _common_header(
    image: Image.Image,
    *,
    title: str,
    subtitle: str,
    tag: str,
) -> None:
    """Draw frozen research-figure chrome."""

    _draw_rect(
        image,
        (
            0,
            0,
            1080,
            84,
        ),
        fill=palette_color("navy_900"),
    )

    _text(
        image,
        48,
        18,
        "PROJECT 7 · LEAKAGEBENCH",
        role="header_kicker",
        color=palette_color("blue_400"),
    )

    _text(
        image,
        48,
        42,
        "Prediction-Time Integrity Auditor",
        role="header_title",
        color=palette_color("white"),
    )

    tag_width = max(
        148,
        min(
            280,
            28 + len(tag) * 7,
        ),
    )

    gradient = linear_gradient(
        (
            scale_value(tag_width),
            scale_value(30),
        ),
        hex_to_rgba("#F9D28B"),
        hex_to_rgba("#F6E2B7"),
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
        radius=scale_value(15),
        fill=255,
    )

    image.paste(
        gradient,
        (
            scale_value(1080 - 48 - tag_width),
            scale_value(27),
        ),
        mask,
    )

    _text(
        image,
        (1080 - 48 - tag_width / 2),
        36,
        tag,
        role="header_pill",
        color=palette_color("navy_900"),
        anchor="ma",
    )

    title_bottom = _wrapped_text(
        image,
        48,
        122,
        title,
        role="hero_headline",
        color=palette_color("text_primary"),
        max_width=900,
        line_height=58,
        max_lines=2,
    )

    _wrapped_text(
        image,
        48,
        title_bottom + 14,
        subtitle,
        role="subhead",
        color=palette_color("text_secondary"),
        max_width=900,
        line_height=26,
        max_lines=3,
    )

    _draw_rect(
        image,
        (
            48,
            302,
            1032,
            304,
        ),
        fill="#E6EDF5",
    )


def _footer(
    image: Image.Image,
    *,
    source: str,
) -> None:
    _draw_rect(
        image,
        (
            48,
            1284,
            1032,
            1286,
        ),
        fill="#E6EDF5",
    )

    _text(
        image,
        48,
        1302,
        source,
        role="micro",
        color=palette_color("text_muted"),
    )

    _text(
        image,
        1032,
        1302,
        "MEASURED / DERIVED FROM FROZEN STEP 5 EVIDENCE",
        role="micro",
        color=palette_color("text_muted"),
        anchor="ra",
    )


def _metric_badge(
    image: Image.Image,
    *,
    x: int,
    y: int,
    label: str,
    value: str,
    tone: str = "info",
    width: int = 220,
) -> None:
    styles = {
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

    fill, border, accent = styles[tone]

    _draw_rect(
        image,
        (
            x,
            y,
            x + width,
            y + 82,
        ),
        fill=fill,
        radius=14,
        outline=border,
    )

    _text(
        image,
        x + 16,
        y + 12,
        label,
        role="micro",
        color=palette_color("text_secondary"),
    )

    _text(
        image,
        x + 16,
        y + 36,
        value,
        role="card_value_small",
        color=accent,
    )


def _horizontal_bar(
    image: Image.Image,
    *,
    x: int,
    y: int,
    width: int,
    value: float,
    maximum: float,
    fill: str,
    label: str,
    value_label: str,
) -> None:
    ratio = (
        0.0
        if maximum <= 0
        else max(
            0.0,
            min(
                1.0,
                value / maximum,
            ),
        )
    )

    _text(
        image,
        x,
        y,
        label,
        role="body",
        color=palette_color("text_secondary"),
    )

    _text(
        image,
        x + width,
        y,
        value_label,
        role="body_bold",
        color=palette_color("text_primary"),
        anchor="ra",
    )

    _draw_rect(
        image,
        (
            x,
            y + 30,
            x + width,
            y + 48,
        ),
        fill="#EAF0F6",
        radius=9,
    )

    _draw_rect(
        image,
        (
            x,
            y + 30,
            x
            + max(
                4,
                width * ratio,
            ),
            y + 48,
        ),
        fill=fill,
        radius=9,
    )


def _finalize(
    image: Image.Image,
    output: Path,
) -> None:
    """LANCZOS downsample and deterministic PNG save."""

    contract = canvas_contract()

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final = image.convert("RGB").resize(
        (
            contract.width_px,
            contract.height_px,
        ),
        Image.Resampling.LANCZOS,
    )

    final.save(
        output,
        format="PNG",
        optimize=False,
    )

    if not output.is_file() or output.stat().st_size < 20_000:
        raise RuntimeError(f"Figure render failed: {output.name}")


def render_audit_pipeline(
    release: dict[str, Any],
    output: Path,
) -> None:
    image = _internal_canvas()

    _common_header(
        image,
        title="Prediction-Time Integrity Audit Pipeline",
        subtitle=("Six checks connect prediction-time evidence to the automated release decision."),
        tag="RELEASE GATE",
    )

    labels = (
        (
            "01",
            "Feature availability",
            "Was each input known at the prediction moment?",
        ),
        (
            "02",
            "Temporal split",
            "Does evaluation preserve deployment-time ordering?",
        ),
        (
            "03",
            "Transformation boundary",
            "Were supervised transforms fit inside training only?",
        ),
        (
            "04",
            "Duplicate overlap",
            "Can train/test record overlap inflate evaluation?",
        ),
        (
            "05",
            "Calibration stability",
            "Do predicted probabilities remain trustworthy?",
        ),
        (
            "06",
            "Release gate",
            "Block deployment when integrity evidence fails.",
        ),
    )

    positions = (
        (
            48,
            350,
        ),
        (
            552,
            350,
        ),
        (
            48,
            560,
        ),
        (
            552,
            560,
        ),
        (
            48,
            770,
        ),
        (
            552,
            770,
        ),
    )

    for (
        number,
        title,
        note,
    ), (
        x,
        y,
    ) in zip(
        labels,
        positions,
        strict=True,
    ):
        _soft_card(
            image,
            (
                x,
                y,
                x + 480,
                y + 174,
            ),
        )

        _metric_badge(
            image,
            x=x + 18,
            y=y + 18,
            label="CHECK",
            value=number,
            width=84,
        )

        _text(
            image,
            x + 120,
            y + 24,
            title,
            role="card_title",
            color=palette_color("text_primary"),
        )

        _wrapped_text(
            image,
            x + 120,
            y + 58,
            note,
            role="body",
            color=palette_color("text_secondary"),
            max_width=320,
            line_height=24,
            max_lines=3,
        )

    draw_neural_edge(
        image,
        start=(
            288,
            524,
        ),
        end=(
            288,
            560,
        ),
    )

    draw_neural_edge(
        image,
        start=(
            792,
            524,
        ),
        end=(
            792,
            560,
        ),
    )

    draw_neural_edge(
        image,
        start=(
            288,
            734,
        ),
        end=(
            288,
            770,
        ),
    )

    draw_neural_edge(
        image,
        start=(
            792,
            734,
        ),
        end=(
            792,
            770,
        ),
    )

    decision = str(release["safe_release_decision"])

    _soft_card(
        image,
        (
            264,
            1000,
            816,
            1198,
        ),
        fill="#EAF8F0",
        border="#CDEFD9",
    )

    _text(
        image,
        540,
        1030,
        "SAFE PIPELINE RELEASE DECISION",
        role="card_title",
        color=palette_color("text_secondary"),
        anchor="ma",
    )

    _text(
        image,
        540,
        1070,
        decision,
        role="hero_headline_accent",
        color=palette_color("green_600"),
        anchor="ma",
    )

    draw_status_pill(
        image,
        xy=(
            482,
            1140,
        ),
        text=decision,
        status="pass",
    )

    _footer(
        image,
        source="release_data.json · safe_release_decision",
    )

    _finalize(
        image,
        output,
    )


def render_business_targeting_distortion(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release.get("leakage_model_results")

    if not isinstance(
        rows,
        list,
    ):
        raise RuntimeError("leakage_model_results missing.")

    s1 = [
        row
        for row in rows
        if isinstance(
            row,
            dict,
        )
        and row.get("case_id") == "S1_CURRENT_CALL_DURATION"
    ]

    s1.sort(key=lambda row: str(row["model_id"]))

    if len(s1) != 2:
        raise RuntimeError("Expected two S1 model rows.")

    image = _internal_canvas()

    _common_header(
        image,
        title=("Business Targeting Distortion from Current-Call Duration"),
        subtitle=("Top-decile conversion yield under the safe and leaked S1 evaluations."),
        tag="OBSERVED S1",
    )

    maximum = max(float(row["leaked_conversions_per_1000"]) for row in s1) * 1.08

    y_positions = (
        360,
        730,
    )

    for row, y in zip(
        s1,
        y_positions,
        strict=True,
    ):
        model_id = str(row["model_id"])

        label = _MODEL_LABELS.get(
            model_id,
            model_id,
        )

        safe = float(row["safe_conversions_per_1000"])

        leaked = float(row["leaked_conversions_per_1000"])

        delta = float(row["campaign_yield_overstatement"])

        _soft_card(
            image,
            (
                48,
                y,
                1032,
                y + 300,
            ),
        )

        _text(
            image,
            72,
            y + 24,
            label,
            role="card_title",
            color=palette_color("text_primary"),
        )

        _metric_badge(
            image,
            x=790,
            y=y + 18,
            label="OVERSTATEMENT",
            value=f"+{delta:.1f}",
            tone="block",
            width=218,
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 100,
            width=880,
            value=safe,
            maximum=maximum,
            fill=palette_color("blue_500"),
            label="Safe",
            value_label=f"{safe:.1f} / 1,000",
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 184,
            width=880,
            value=leaked,
            maximum=maximum,
            fill=palette_color("red_600"),
            label="Leaked",
            value_label=f"{leaked:.1f} / 1,000",
        )

    _metric_badge(
        image,
        x=48,
        y=1110,
        label="EVIDENCE CLASS",
        value="OBSERVED",
        tone="warn",
        width=230,
    )

    _metric_badge(
        image,
        x=302,
        y=1110,
        label="AUDITOR RESULT",
        value="BLOCK",
        tone="block",
        width=230,
    )

    _footer(
        image,
        source=("release_data.json · S1_CURRENT_CALL_DURATION"),
    )

    _finalize(
        image,
        output,
    )


def render_calibration_comparison(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release.get("leakage_model_results")

    if not isinstance(
        rows,
        list,
    ):
        raise RuntimeError("leakage_model_results missing.")

    selected = [
        row
        for row in rows
        if isinstance(
            row,
            dict,
        )
        and row.get("case_id") == "S1_CURRENT_CALL_DURATION"
    ]

    selected.sort(key=lambda row: str(row["model_id"]))

    image = _internal_canvas()

    _common_header(
        image,
        title="Calibration Error: Safe vs Leaked Evaluation",
        subtitle=(
            "Expected calibration error (ECE). Lower values indicate smaller probability error."
        ),
        tag="CALIBRATION",
    )

    maximum = max(float(row["leaked_expected_calibration_error"]) for row in selected) * 1.12

    for row, y in zip(
        selected,
        (
            380,
            760,
        ),
        strict=True,
    ):
        model_id = str(row["model_id"])

        safe = float(row["safe_expected_calibration_error"])

        leaked = float(row["leaked_expected_calibration_error"])

        _soft_card(
            image,
            (
                48,
                y,
                1032,
                y + 304,
            ),
        )

        _text(
            image,
            72,
            y + 24,
            _MODEL_LABELS.get(
                model_id,
                model_id,
            ),
            role="card_title",
            color=palette_color("text_primary"),
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 94,
            width=860,
            value=safe,
            maximum=maximum,
            fill=palette_color("blue_500"),
            label="Safe ECE",
            value_label=f"{safe:.3f}",
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 180,
            width=860,
            value=leaked,
            maximum=maximum,
            fill=palette_color("red_600"),
            label="Leaked ECE",
            value_label=f"{leaked:.3f}",
        )

    _footer(
        image,
        source=("release_data.json · safe/leaked expected_calibration_error"),
    )

    _finalize(
        image,
        output,
    )


def render_feature_availability_contract(
    output: Path,
) -> None:
    """Render the frozen prediction-time availability contract."""

    rows = (
        (
            "Age / job / education",
            "PRE-DECISION",
            "pass",
            "ALLOWED",
        ),
        (
            "Previous campaign context",
            "PRE-DECISION",
            "pass",
            "ALLOWED",
        ),
        (
            "Campaign",
            "UNKNOWN",
            "block",
            "BLOCKED",
        ),
        (
            "Duration",
            "DURING ACTION",
            "block",
            "BLOCKED",
        ),
        (
            "Outcome confirmation proxy",
            "POST OUTCOME",
            "block",
            "BLOCKED",
        ),
    )

    image = _internal_canvas()

    _common_header(
        image,
        title="Prediction-Time Feature Availability Contract",
        subtitle=(
            "Feature admissibility is determined by whether the "
            "value is known when the prediction is made."
        ),
        tag="FEATURE CONTRACT",
    )

    y = 360

    for (
        feature,
        availability,
        status,
        decision,
    ) in rows:
        _soft_card(
            image,
            (
                48,
                y,
                1032,
                y + 142,
            ),
        )

        _text(
            image,
            72,
            y + 24,
            feature,
            role="card_title",
            color=palette_color("text_primary"),
        )

        _text(
            image,
            72,
            y + 66,
            availability,
            role="micro",
            color=palette_color("text_secondary"),
        )

        draw_status_pill(
            image,
            xy=(
                852,
                y + 52,
            ),
            text=decision,
            status=status,
        )

        y += 160

    _metric_badge(
        image,
        x=48,
        y=1180,
        label="PREDICTION MOMENT",
        value="BEFORE CALL",
        tone="info",
        width=254,
    )

    _footer(
        image,
        source=("feature_availability_contract.json · frozen Step 1 semantics"),
    )

    _finalize(
        image,
        output,
    )


def render_leakage_inflation_map(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release.get("leakage_inflation")

    if not isinstance(
        rows,
        list,
    ):
        raise RuntimeError("leakage_inflation missing.")

    metrics = (
        "roc_auc",
        "pr_auc",
        "conversions_per_1000",
    )

    cases = tuple(
        sorted(
            {
                str(row["case_id"])
                for row in rows
                if isinstance(
                    row,
                    dict,
                )
                and row.get("metric") in metrics
            }
        )
    )

    matrix: dict[
        tuple[
            str,
            str,
        ],
        float,
    ] = {}

    for case_id in cases:
        for metric in metrics:
            values = [
                float(row["leakage_inflation"])
                for row in rows
                if isinstance(
                    row,
                    dict,
                )
                and str(row.get("case_id")) == case_id
                and row.get("metric") == metric
            ]

            if not values:
                raise RuntimeError(f"Missing inflation values: {case_id}/{metric}")

            matrix[
                (
                    case_id,
                    metric,
                )
            ] = max(values)

    image = _internal_canvas()

    _common_header(
        image,
        title="Leakage Inflation Across Integrity Scenarios",
        subtitle=(
            "Direction-normalized inflation from frozen Step 5 "
            "results; each cell shows the maximum across models."
        ),
        tag="5 SCENARIOS",
    )

    column_x = (
        520,
        692,
        864,
    )

    column_titles = (
        "ROC AUC",
        "PR AUC",
        "CONV / 1K",
    )

    for x, title in zip(
        column_x,
        column_titles,
        strict=True,
    ):
        _text(
            image,
            x,
            352,
            title,
            role="micro",
            color=palette_color("text_secondary"),
            anchor="ma",
        )

    row_y = 402

    all_values = [abs(value) for value in matrix.values()]

    max_value = max(all_values)

    for case_id in cases:
        _text(
            image,
            48,
            row_y + 26,
            _SCENARIO_LABELS.get(
                case_id,
                case_id,
            ),
            role="body",
            color=palette_color("text_primary"),
        )

        for x, metric in zip(
            column_x,
            metrics,
            strict=True,
        ):
            value = matrix[
                (
                    case_id,
                    metric,
                )
            ]

            normalized = (
                0.0
                if max_value == 0
                else min(
                    1.0,
                    abs(value) / max_value,
                )
            )

            if metric == "conversions_per_1000":
                fill = "#FFECEC" if value > 0 else "#EAF3FF"

                text_color = "#E45858" if value > 0 else "#3C82F6"

            else:
                red_alpha = round(30 + 120 * normalized)

                overlay = Image.new(
                    "RGBA",
                    (
                        scale_value(148),
                        scale_value(88),
                    ),
                    (
                        228,
                        88,
                        88,
                        red_alpha,
                    ),
                )

                base_fill = "#FFF8F8"

                _draw_rect(
                    image,
                    (
                        x - 74,
                        row_y,
                        x + 74,
                        row_y + 88,
                    ),
                    fill=base_fill,
                    radius=14,
                    outline="#F7C1C1",
                )

                image.alpha_composite(
                    overlay,
                    (
                        scale_value(x - 74),
                        scale_value(row_y),
                    ),
                )

                fill = ""
                text_color = "#102539"

            if fill:
                _draw_rect(
                    image,
                    (
                        x - 74,
                        row_y,
                        x + 74,
                        row_y + 88,
                    ),
                    fill=fill,
                    radius=14,
                    outline="#F7C1C1",
                )

            formatted = f"{value:.3f}" if metric != "conversions_per_1000" else f"{value:.1f}"

            _text(
                image,
                x,
                row_y + 28,
                formatted,
                role="card_value_small",
                color=text_color,
                anchor="ma",
            )

        row_y += 154

    _footer(
        image,
        source=("release_data.json · leakage_inflation · direction-normalized"),
    )

    _finalize(
        image,
        output,
    )


def render_model_performance_comparison(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = _baseline_lookup(
        release,
        "C_PREDICTION_TIME_SAFE",
        "chronological_test",
    )

    image = _internal_canvas()

    _common_header(
        image,
        title="Prediction-Time-Safe Model Performance",
        subtitle=("Pipeline C · chronological test · prediction-time-safe feature set."),
        tag="SAFE PIPELINE C",
    )

    for row, y in zip(
        rows,
        (
            370,
            760,
        ),
        strict=True,
    ):
        model_id = str(row["model_id"])

        roc = float(row["roc_auc"])

        pr = float(row["pr_auc"])

        conversions = float(row["conversions_per_1000"])

        lift = float(row["top_decile_lift"])

        _soft_card(
            image,
            (
                48,
                y,
                1032,
                y + 310,
            ),
        )

        _text(
            image,
            72,
            y + 24,
            _MODEL_LABELS.get(
                model_id,
                model_id,
            ),
            role="card_title",
            color=palette_color("text_primary"),
        )

        _metric_badge(
            image,
            x=72,
            y=y + 78,
            label="ROC AUC",
            value=f"{roc:.3f}",
            tone="info",
            width=196,
        )

        _metric_badge(
            image,
            x=286,
            y=y + 78,
            label="PR AUC",
            value=f"{pr:.3f}",
            tone="info",
            width=196,
        )

        _metric_badge(
            image,
            x=500,
            y=y + 78,
            label="CONV / 1K",
            value=f"{conversions:.1f}",
            tone="pass",
            width=196,
        )

        _metric_badge(
            image,
            x=714,
            y=y + 78,
            label="TOP-DECILE LIFT",
            value=f"{lift:.2f}x",
            tone="pass",
            width=264,
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 194,
            width=860,
            value=roc,
            maximum=1.0,
            fill=palette_color("blue_500"),
            label="ROC AUC",
            value_label=f"{roc:.3f}",
        )

    _footer(
        image,
        source=("release_data.json · baseline_model_results · C_PREDICTION_TIME_SAFE"),
    )

    _finalize(
        image,
        output,
    )


def render_split_integrity_comparison(
    release: dict[str, Any],
    output: Path,
) -> None:
    rows = release.get("leakage_model_results")

    if not isinstance(
        rows,
        list,
    ):
        raise RuntimeError("leakage_model_results missing.")

    selected = [
        row
        for row in rows
        if isinstance(
            row,
            dict,
        )
        and row.get("case_id") == "S2_RANDOM_TEMPORAL_MIXING"
    ]

    selected.sort(key=lambda row: str(row["model_id"]))

    image = _internal_canvas()

    _common_header(
        image,
        title="Random vs Chronological Evaluation",
        subtitle=(
            "Scenario S2 compares random temporal mixing with "
            "the deployment-aligned chronological evaluation."
        ),
        tag="SPLIT INTEGRITY",
    )

    gap = float(release["independent_validation"]["temporal_roc_auc_gap"])

    _metric_badge(
        image,
        x=48,
        y=350,
        label="VALIDATED ROC-AUC GAP",
        value=f"{gap:+.3f}",
        tone="warn",
        width=310,
    )

    for row, y in zip(
        selected,
        (
            490,
            840,
        ),
        strict=True,
    ):
        model_id = str(row["model_id"])

        chronological = float(row["safe_roc_auc"])

        random = float(row["leaked_roc_auc"])

        _soft_card(
            image,
            (
                48,
                y,
                1032,
                y + 286,
            ),
        )

        _text(
            image,
            72,
            y + 24,
            _MODEL_LABELS.get(
                model_id,
                model_id,
            ),
            role="card_title",
            color=palette_color("text_primary"),
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 90,
            width=860,
            value=chronological,
            maximum=1.0,
            fill=palette_color("blue_500"),
            label="Chronological",
            value_label=f"{chronological:.3f}",
        )

        _horizontal_bar(
            image,
            x=72,
            y=y + 176,
            width=860,
            value=random,
            maximum=1.0,
            fill=palette_color("amber_600"),
            label="Random",
            value_label=f"{random:.3f}",
        )

    _footer(
        image,
        source=("release_data.json · S2_RANDOM_TEMPORAL_MIXING"),
    )

    _finalize(
        image,
        output,
    )


def render_all_figures(
    assets_root: Path,
) -> tuple[Path, ...]:
    """Render every required Step 6 research figure."""

    release, _claims = load_release_context(assets_root)

    images = assets_root / "images"

    outputs = tuple(images / filename for filename in FIGURE_FILES)

    render_audit_pipeline(
        release,
        outputs[0],
    )

    render_business_targeting_distortion(
        release,
        outputs[1],
    )

    render_calibration_comparison(
        release,
        outputs[2],
    )

    render_feature_availability_contract(
        outputs[3],
    )

    render_leakage_inflation_map(
        release,
        outputs[4],
    )

    render_model_performance_comparison(
        release,
        outputs[5],
    )

    render_split_integrity_comparison(
        release,
        outputs[6],
    )

    return outputs


def figure_sha256(
    path: Path,
) -> str:
    """Return deterministic rendered-file fingerprint."""

    return hashlib.sha256(path.read_bytes()).hexdigest()
