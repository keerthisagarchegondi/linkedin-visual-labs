from __future__ import annotations

import pytest
from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.design_tokens import (
    EXPECTED_CONTRACT_SHA256,
    canvas_contract,
    contract_sha256,
    font_path_for_role,
    frozen_scene_ids,
    hex_to_rgb,
    scale_box,
    scale_value,
    scene_duration_total,
    status_style,
    typography_style,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.text_layout import (
    font_for_role,
    measure_tracked_text,
    wrap_for_role,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.visual_primitives import (
    apply_glow,
    draw_card,
    draw_neural_edge,
    draw_neural_node,
    draw_status_pill,
    linear_gradient,
)


def test_contract_checksum() -> None:
    assert contract_sha256() == EXPECTED_CONTRACT_SHA256


def test_canvas() -> None:
    contract = canvas_contract()

    assert contract.width_px == 1080
    assert contract.height_px == 1350
    assert contract.internal_width_px == 2160
    assert contract.internal_height_px == 2700
    assert contract.fps == 30
    assert contract.duration_seconds == 45.0


def test_scene_contract() -> None:
    assert frozen_scene_ids() == (
        "S1",
        "S2",
        "S3",
        "S4",
        "S5",
        "S6",
        "S7",
        "S8",
        "S9",
        "S10",
    )

    assert scene_duration_total() == pytest.approx(45.0)


def test_colors_and_scaling() -> None:
    assert hex_to_rgb("#3C82F6") == (
        60,
        130,
        246,
    )

    assert scale_value(48) == 96

    assert scale_box((10, 20, 30, 40)) == (
        20,
        40,
        60,
        80,
    )


def test_fonts() -> None:
    for role in (
        "hero_headline",
        "hero_headline_accent",
        "body",
        "status_label",
        "timestamp",
    ):
        assert font_path_for_role(role).is_file()
        assert font_for_role(role).size > 0


def test_typography() -> None:
    headline = typography_style("hero_headline")

    assert headline.size_px == 54
    assert headline.line_height_px == 58
    assert headline.max_width_px == 720
    assert headline.max_lines == 2

    assert (
        measure_tracked_text(
            "Prediction-Time Integrity",
            role="hero_headline",
            supersampled=False,
        )
        > 0
    )


def test_wrap() -> None:
    lines = wrap_for_role(
        "The model looked production-ready.",
        role="hero_headline",
    )

    assert 1 <= len(lines) <= 2


def test_status() -> None:
    assert status_style("pass").text == "#1F9E62"

    assert status_style("block").text == "#E45858"


def test_primitives() -> None:
    canvas = Image.new(
        "RGBA",
        (2160, 2700),
        (244, 247, 251, 255),
    )

    draw_card(
        canvas,
        (48, 320, 500, 486),
    )

    draw_status_pill(
        canvas,
        xy=(70, 344),
        text="PASS",
        status="pass",
    )

    draw_neural_edge(
        canvas,
        start=(650, 390),
        end=(850, 470),
    )

    draw_neural_node(
        canvas,
        center=(650, 390),
    )

    draw_neural_node(
        canvas,
        center=(850, 470),
        active=True,
    )

    assert canvas.getbbox() is not None


def test_gradient() -> None:
    gradient = linear_gradient(
        (5, 2),
        (0, 0, 0, 255),
        (255, 255, 255, 255),
    )

    assert gradient.getpixel((0, 0)) == (
        0,
        0,
        0,
        255,
    )

    assert gradient.getpixel((4, 0)) == (
        255,
        255,
        255,
        255,
    )


def test_glow() -> None:
    image = Image.new(
        "RGBA",
        (40, 40),
        (255, 255, 255, 255),
    )

    result = apply_glow(
        image,
        color="#3C82F6",
        radius_px=7,
        opacity=0.10,
    )

    assert result.size == image.size
