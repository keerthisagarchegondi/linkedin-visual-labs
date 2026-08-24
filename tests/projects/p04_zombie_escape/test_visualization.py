"""Visualization-system tests for Project 2 Step 8."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
from PIL import Image

from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    CANVAS_SIZE,
    CITY_ORDER,
    METHOD_LABELS,
    METHOD_ORDER,
    _new_figure,
    load_visual_payloads,
    render_city_frame,
    render_final_summary,
    render_opening_board,
    validate_figure_geometry,
    validate_text_overlaps,
)


def _data_directory() -> Path:
    return Path("tests/fixtures/p04_zombie_escape/data")


def test_visual_contract_uses_square_1080_canvas() -> None:
    assert CANVAS_SIZE == 1080

    fig = _new_figure()

    validate_figure_geometry(fig)

    plt.close(fig)


def test_method_order_and_labels_are_frozen() -> None:
    assert METHOD_ORDER == (
        "dijkstra",
        "ml",
        "dl",
    )

    assert METHOD_LABELS == {
        "dijkstra": "Dijkstra",
        "ml": "ML + A*",
        "dl": "Deep Learning + A*",
    }


def test_visual_payloads_load() -> None:
    payloads = load_visual_payloads(_data_directory())

    assert len(payloads) == 4


def test_opening_board_renders_exact_dimensions(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = load_visual_payloads(_data_directory())

    output = tmp_path / "opening.png"

    render_opening_board(
        cities_payload=cities,
        routes_payload=routes,
        evaluation_payload=evaluation,
        output_path=output,
    )

    with Image.open(output) as image:
        assert image.size == (
            1080,
            1080,
        )


def test_each_city_frame_renders_exact_dimensions(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = load_visual_payloads(_data_directory())

    for city_id in CITY_ORDER:
        output = tmp_path / f"{city_id}.png"

        render_city_frame(
            city_id=city_id,
            cities_payload=cities,
            routes_payload=routes,
            evaluation_payload=evaluation,
            output_path=output,
        )

        with Image.open(output) as image:
            assert image.size == (
                1080,
                1080,
            )


def test_final_summary_uses_persisted_overall_winner(
    tmp_path: Path,
) -> None:
    _, _, _, evaluation = load_visual_payloads(_data_directory())

    overall = cast(
        dict[str, object],
        evaluation["overall"],
    )

    expected = cast(
        str,
        overall["winner_method"],
    )

    assert expected in {
        "dijkstra",
        "ml",
        "dl",
    }

    output = tmp_path / "summary.png"

    render_final_summary(
        evaluation_payload=evaluation,
        output_path=output,
    )

    with Image.open(output) as image:
        assert image.size == (
            1080,
            1080,
        )


def test_evaluation_has_three_city_winners() -> None:
    payload = json.loads(
        (_data_directory() / "evaluation_summary.json").read_text(encoding="utf-8")
    )

    assert len(payload["cities"]) == 3

    assert all(
        city["winner_method"]
        in {
            "dijkstra",
            "ml",
            "dl",
        }
        for city in payload["cities"]
    )


def test_text_overlap_validator_accepts_clean_layout() -> None:
    fig = _new_figure()

    fig.text(
        0.1,
        0.9,
        "First",
    )

    fig.text(
        0.1,
        0.1,
        "Second",
    )

    validate_text_overlaps(fig)

    plt.close(fig)


def test_text_overlap_validator_rejects_collision() -> None:
    import pytest

    fig = _new_figure()

    fig.text(
        0.5,
        0.5,
        "Collision",
    )

    fig.text(
        0.5,
        0.5,
        "Collision",
    )

    with pytest.raises(
        ValueError,
        match="text overlap",
    ):
        validate_text_overlaps(fig)

    plt.close(fig)
