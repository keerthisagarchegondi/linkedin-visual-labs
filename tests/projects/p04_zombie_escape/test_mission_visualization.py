"""Mission visualization Version-2.1 regression tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from linkedin_visual_labs.projects.p04_zombie_escape.mission_visualization import (
    FULL_MAP_MIN_ASPECT,
    HEADING_HEIGHT,
    METHOD_LAYER_HEIGHT,
    MINI_MAP_MIN_ASPECT,
    MISSION_ENDPOINTS,
    RESULT_HEIGHT,
    SWARM_COUNTS,
    SWARM_ENDPOINT_CLEARANCE,
    SWARM_MIN_COLUMN_SPAN,
    SWARM_MIN_DISTANCE,
    SWARM_MIN_ROW_SPAN,
    SWARM_SECTOR_PLAN,
    MissionBox,
    MissionTextPlacement,
    final_card_boxes,
    final_map_box,
    method_map_box,
    minimum_swarm_distance,
    mission_contract_payload,
    opening_card_boxes,
    opening_map_box,
    render_city_frame,
    render_final_summary,
    render_opening_board,
    select_zombie_hotspots,
    swarm_sector,
    swarm_spans,
    validate_frame_geometry,
    validate_swarm_distribution,
    validate_text_placements,
)
from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    METHOD_ORDER,
    _cell_position,
    _cells,
    _city_payload,
    _terrain_name,
    load_visual_payloads,
)


def _payloads() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    return load_visual_payloads(Path("outputs/p04_zombie_escape/data"))


def test_exact_frame_geometry() -> None:
    assert HEADING_HEIGHT == 45
    assert METHOD_LAYER_HEIGHT == 330
    assert RESULT_HEIGHT == 45

    assert HEADING_HEIGHT + METHOD_LAYER_HEIGHT * 3 + RESULT_HEIGHT == 1080

    validate_frame_geometry()


def test_method_maps_are_horizontal() -> None:
    for method_id in METHOD_ORDER:
        box = method_map_box(method_id)

        assert box.aspect_ratio >= FULL_MAP_MIN_ASPECT


def test_opening_has_nine_horizontal_maps() -> None:
    cards = opening_card_boxes()

    assert len(cards) == 9

    for card in cards:
        assert opening_map_box(card).aspect_ratio >= MINI_MAP_MIN_ASPECT


def test_final_has_three_horizontal_maps() -> None:
    cards = final_card_boxes()

    assert len(cards) == 3

    for card in cards:
        assert final_map_box(card).aspect_ratio >= MINI_MAP_MIN_ASPECT


def test_swarms_are_deterministic() -> None:
    cities, _, _, _ = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        city = _city_payload(
            cities,
            city_id,
        )

        first = select_zombie_hotspots(
            city,
            city_id=city_id,
        )

        second = select_zombie_hotspots(
            city,
            city_id=city_id,
        )

        assert first == second

        assert len(first) == (SWARM_COUNTS[city_id])


def test_each_swarm_occupies_distinct_planned_sector() -> None:
    cities, _, _, _ = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        hotspots = select_zombie_hotspots(
            _city_payload(
                cities,
                city_id,
            ),
            city_id=city_id,
        )

        sectors = {
            swarm_sector(
                row,
                column,
            )
            for (
                row,
                column,
                _risk,
            ) in hotspots
        }

        assert sectors == set(SWARM_SECTOR_PLAN[city_id])

        assert len(sectors) == len(hotspots)


def test_swarm_city_span_is_large() -> None:
    cities, _, _, _ = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        hotspots = select_zombie_hotspots(
            _city_payload(
                cities,
                city_id,
            ),
            city_id=city_id,
        )

        row_span, column_span = swarm_spans(hotspots)

        assert row_span >= SWARM_MIN_ROW_SPAN

        assert column_span >= SWARM_MIN_COLUMN_SPAN


def test_swarm_minimum_distance() -> None:
    cities, _, _, _ = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        hotspots = select_zombie_hotspots(
            _city_payload(
                cities,
                city_id,
            ),
            city_id=city_id,
        )

        assert minimum_swarm_distance(hotspots) >= SWARM_MIN_DISTANCE


def test_swarm_distribution_validator() -> None:
    cities, _, _, _ = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        hotspots = select_zombie_hotspots(
            _city_payload(
                cities,
                city_id,
            ),
            city_id=city_id,
        )

        validate_swarm_distribution(
            hotspots,
            city_id=city_id,
        )


def test_swarms_avoid_buildings_and_endpoints() -> None:
    cities, _, _, _ = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        city = _city_payload(
            cities,
            city_id,
        )

        terrain = {_cell_position(cell): _terrain_name(cell).lower() for cell in _cells(city)}

        start, destination = MISSION_ENDPOINTS[city_id]

        hotspots = select_zombie_hotspots(
            city,
            city_id=city_id,
        )

        for (
            row,
            column,
            _risk,
        ) in hotspots:
            assert (
                "building"
                not in terrain[
                    (
                        row,
                        column,
                    )
                ]
            )

            for endpoint in (
                start,
                destination,
            ):
                distance = abs(row - endpoint[0]) + abs(column - endpoint[1])

                assert distance >= SWARM_ENDPOINT_CLEARANCE


def test_text_overlap_validator() -> None:
    validate_text_placements(
        [
            MissionTextPlacement(
                "A",
                MissionBox(
                    10,
                    10,
                    100,
                    40,
                ),
            ),
            MissionTextPlacement(
                "B",
                MissionBox(
                    150,
                    10,
                    250,
                    40,
                ),
            ),
        ]
    )

    with pytest.raises(
        ValueError,
        match="tracked text overlap",
    ):
        validate_text_placements(
            [
                MissionTextPlacement(
                    "A",
                    MissionBox(
                        10,
                        10,
                        120,
                        60,
                    ),
                ),
                MissionTextPlacement(
                    "B",
                    MissionBox(
                        20,
                        15,
                        130,
                        65,
                    ),
                ),
            ]
        )


def test_base_city_frame_does_not_draw_final_route(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = _payloads()

    with patch(
        "linkedin_visual_labs.projects.p04_zombie_escape.mission_visualization._draw_final_route"
    ) as draw_final:
        render_city_frame(
            city_id="new_york",
            cities_payload=cities,
            routes_payload=routes,
            evaluation_payload=evaluation,
            output_path=(tmp_path / "base.png"),
        )

        draw_final.assert_not_called()


def test_explicit_final_route_overlay_draws_three_routes(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = _payloads()

    with patch(
        "linkedin_visual_labs.projects.p04_zombie_escape.mission_visualization._draw_final_route"
    ) as draw_final:
        render_city_frame(
            city_id="new_york",
            cities_payload=cities,
            routes_payload=routes,
            evaluation_payload=evaluation,
            output_path=(tmp_path / "final.png"),
            route_overlay="final",
        )

        assert draw_final.call_count == 3


def test_search_contract_hides_initial_route() -> None:
    contract = mission_contract_payload()

    base = contract["base_city_frame"]

    assert isinstance(
        base,
        dict,
    )

    assert base["route_overlay"] == "none"

    animation = contract["search_animation"]

    assert isinstance(
        animation,
        dict,
    )

    assert animation["fake_search_tree_allowed"] is False

    assert animation["final_route_initially_visible"] is False


def test_opening_board_renders_1080(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = _payloads()

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


def test_all_base_city_frames_render_1080(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = _payloads()

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
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


def test_final_summary_renders_1080(
    tmp_path: Path,
) -> None:
    cities, _, routes, evaluation = _payloads()

    output = tmp_path / "summary.png"

    render_final_summary(
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
