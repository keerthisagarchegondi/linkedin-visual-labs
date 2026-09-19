"""Deterministic Project 7 Step 6 visual primitives."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.design_tokens import (
    RGBA,
    hex_to_rgba,
    load_visual_contract,
    palette_color,
    scale_box,
    scale_value,
    status_style,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.text_layout import (
    draw_tracked_text,
    measure_tracked_text,
)


def linear_gradient(
    size: tuple[int, int],
    start: RGBA,
    end: RGBA,
) -> Image.Image:
    width, height = size

    result = Image.new(
        "RGBA",
        size,
        start,
    )

    draw = ImageDraw.Draw(result)

    denominator = max(
        width - 1,
        1,
    )

    for x in range(width):
        ratio = x / denominator

        color = tuple(
            round(start[index] + (end[index] - start[index]) * ratio) for index in range(4)
        )

        draw.line(
            (x, 0, x, height - 1),
            fill=color,
        )

    return result


def draw_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    *,
    fill: str = "#FFFFFF",
    border: str = "#DEE6F0",
    radius_px: int = 16,
) -> None:
    draw = ImageDraw.Draw(
        canvas,
        "RGBA",
    )

    draw.rounded_rectangle(
        scale_box(box),
        radius=scale_value(radius_px),
        fill=hex_to_rgba(fill),
        outline=hex_to_rgba(border),
        width=scale_value(1),
    )


def draw_status_pill(
    canvas: Image.Image,
    *,
    xy: tuple[int, int],
    text: str,
    status: str,
) -> tuple[int, int, int, int]:
    visual = status_style(status)

    contract = load_visual_contract()
    raw = contract["status_pills"]

    height = int(raw["height_px"])
    padding = int(raw["padding_x_px"])

    width = round(
        measure_tracked_text(
            text,
            role="status_label",
            supersampled=False,
        )
        + 2 * padding
    )

    x, y = xy

    box = (
        x,
        y,
        x + width,
        y + height,
    )

    draw = ImageDraw.Draw(
        canvas,
        "RGBA",
    )

    draw.rounded_rectangle(
        scale_box(box),
        radius=scale_value(int(raw["radius_px"])),
        fill=hex_to_rgba(visual.fill),
        outline=hex_to_rgba(visual.border),
        width=scale_value(1),
    )

    draw_tracked_text(
        draw,
        (
            scale_value(x + width / 2),
            scale_value(y + 5),
        ),
        text,
        role="status_label",
        fill=visual.text,
        anchor="ma",
    )

    return box


def draw_neural_edge(
    canvas: Image.Image,
    *,
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    motif = load_visual_contract()["visual_motifs"]["neural_network_flow"]

    draw = ImageDraw.Draw(
        canvas,
        "RGBA",
    )

    draw.line(
        (
            scale_value(start[0]),
            scale_value(start[1]),
            scale_value(end[0]),
            scale_value(end[1]),
        ),
        fill=hex_to_rgba("#69A2FF"),
        width=scale_value(int(motif["edge_width_px"])),
    )


def draw_neural_node(
    canvas: Image.Image,
    *,
    center: tuple[int, int],
    active: bool = False,
) -> None:
    motif = load_visual_contract()["visual_motifs"]["neural_network_flow"]

    radius = scale_value(int(motif["node_radius_px"]))

    x = scale_value(center[0])
    y = scale_value(center[1])

    draw = ImageDraw.Draw(
        canvas,
        "RGBA",
    )

    if active:
        glow = scale_value(int(motif["active_node_glow_radius_px"]))

        draw.ellipse(
            (
                x - glow,
                y - glow,
                x + glow,
                y + glow,
            ),
            fill=(
                60,
                130,
                246,
                28,
            ),
        )

    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius,
        ),
        fill=(255, 255, 255, 255),
        outline=hex_to_rgba(palette_color("blue_500")),
        width=scale_value(2),
    )


def apply_glow(
    source: Image.Image,
    *,
    color: str,
    radius_px: int,
    opacity: float,
) -> Image.Image:
    if not 0 <= opacity <= 1:
        raise ValueError(opacity)

    source = source.convert("RGBA")

    alpha = source.getchannel("A").filter(ImageFilter.GaussianBlur(scale_value(radius_px)))

    r, g, b, _ = hex_to_rgba(color)

    glow = Image.new(
        "RGBA",
        source.size,
        (r, g, b, 0),
    )

    glow.putalpha(alpha.point(lambda value: round(value * opacity)))

    result = Image.new(
        "RGBA",
        source.size,
        (0, 0, 0, 0),
    )

    result.alpha_composite(glow)
    result.alpha_composite(source)

    return result
