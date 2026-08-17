"""Tests for centralized plotting and visual components."""

from __future__ import annotations

import pytest

from linkedin_visual_labs.common.plotting import (
    DEFAULT_CANVAS,
    DEFAULT_THEME,
    CanvasSpec,
    add_metric_card,
    add_progress_gauge,
    add_route_legend,
    categorical_colors,
    create_canvas,
    route_style,
)
from linkedin_visual_labs.common.validation import ValidationError


def test_default_canvas_matches_linkedin_specification() -> None:
    assert DEFAULT_CANVAS.width_px == 1080
    assert DEFAULT_CANVAS.height_px == 1350
    assert DEFAULT_CANVAS.dpi == 100
    assert DEFAULT_CANVAS.safe_margin_px == 60


def test_create_canvas_has_exact_pixel_dimensions() -> None:
    figure, axes = create_canvas()

    width_inches, height_inches = figure.get_size_inches()

    assert round(width_inches * figure.dpi) == 1080
    assert round(height_inches * figure.dpi) == 1350

    position = axes.get_position()

    assert position.x0 == pytest.approx(
        60 / 1080,
    )
    assert position.y0 == pytest.approx(
        60 / 1350,
    )


def test_theme_has_single_centralized_categorical_palette() -> None:
    colors = categorical_colors()

    assert len(colors) == 6
    assert len(set(colors)) == 6


@pytest.mark.parametrize(
    ("objective", "expected_label"),
    [
        ("shortest", "Shortest"),
        ("fastest", "Fastest"),
        ("safest", "Safest"),
    ],
)
def test_route_style_is_centralized(
    objective: str,
    expected_label: str,
) -> None:
    style = route_style(objective)

    assert style.label == expected_label
    assert style.color


def test_route_style_rejects_unknown_objective() -> None:
    with pytest.raises(ValidationError):
        route_style("best")


def test_metric_card_creates_expected_artists() -> None:
    _, axes = create_canvas()

    artists = add_metric_card(
        axes,
        x=0.05,
        y=0.80,
        label="Detection roll",
        value="47",
    )

    assert artists.label.get_text() == "Detection roll"
    assert artists.value.get_text() == "47"


def test_progress_gauge_width_tracks_progress() -> None:
    _, axes = create_canvas()

    gauge = add_progress_gauge(
        axes,
        x=0.10,
        y=0.20,
        width=0.60,
        height=0.03,
        progress=0.25,
        label="Loaded probability",
    )

    assert gauge.background.get_width() == pytest.approx(
        0.60,
    )

    assert gauge.fill.get_width() == pytest.approx(
        0.15,
    )


def test_progress_gauge_rejects_invalid_probability() -> None:
    _, axes = create_canvas()

    with pytest.raises(ValidationError):
        add_progress_gauge(
            axes,
            x=0.10,
            y=0.20,
            width=0.60,
            height=0.03,
            progress=1.5,
            label="Invalid",
        )


def test_route_legend_contains_three_objectives() -> None:
    _, axes = create_canvas()

    legend = add_route_legend(axes)

    labels = [text.get_text() for text in legend.get_texts()]

    assert labels == [
        "Shortest",
        "Fastest",
        "Safest",
    ]


def test_canvas_rejects_invalid_safe_margin() -> None:
    with pytest.raises(ValidationError):
        CanvasSpec(
            width_px=100,
            height_px=100,
            dpi=100,
            safe_margin_px=50,
        )


def test_theme_background_is_applied() -> None:
    figure, axes = create_canvas()

    assert figure.get_facecolor()
    assert axes.get_facecolor()
    assert DEFAULT_THEME.background.startswith("#")
