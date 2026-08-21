"""Deterministic city-generator tests for Project 2."""

from __future__ import annotations

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityId,
    GridPosition,
    TerrainType,
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
    generate_all_cities,
    generate_city,
)


def _cities() -> tuple[GeneratedCity, ...]:
    return generate_all_cities(load_zombie_config())


def test_exact_three_showcase_cities_are_generated() -> None:
    cities = _cities()

    assert tuple(city.city_id for city in cities) == (
        CityId.PHOENIX,
        CityId.NEW_YORK,
        CityId.CHICAGO,
    )


def test_each_city_has_exact_36_by_36_grid() -> None:
    for city in _cities():
        assert city.grid.rows == 36
        assert city.grid.columns == 36

        assert len(city.cells) == 1_296

        assert len({cell.position for cell in city.cells}) == 1_296


def test_every_city_start_and_destination_are_traversable() -> None:
    for city in _cities():
        assert city.is_traversable(city.definition.start)

        assert city.is_traversable(city.definition.destination)


def test_every_city_has_start_destination_connectivity() -> None:
    for city in _cities():
        assert city.has_start_destination_connectivity()


def test_all_risk_values_remain_inside_unit_interval() -> None:
    for city in _cities():
        for cell in city.cells:
            assert 0.0 <= cell.observed_risk <= 1.0

            assert 0.0 <= cell.true_risk <= 1.0


def test_hidden_true_risk_is_not_identical_to_observed_risk() -> None:
    for city in _cities():
        differing = [
            cell
            for cell in city.cells
            if (
                cell.terrain is not TerrainType.BUILDING
                and abs(cell.observed_risk - cell.true_risk) > 1e-9
            )
        ]

        assert differing


def test_showcase_generation_is_exactly_deterministic() -> None:
    config = load_zombie_config()

    first = generate_all_cities(config)

    second = generate_all_cities(config)

    assert first == second


def test_individual_city_generation_matches_bulk_generation() -> None:
    config = load_zombie_config()

    bulk = {city.city_id: city for city in generate_all_cities(config)}

    for city_id in CityId:
        assert (
            generate_city(
                config,
                city_id,
            )
            == bulk[city_id]
        )


def test_new_york_is_more_building_dense_than_phoenix() -> None:
    config = load_zombie_config()

    phoenix = generate_city(
        config,
        CityId.PHOENIX,
    )

    new_york = generate_city(
        config,
        CityId.NEW_YORK,
    )

    assert new_york.terrain_count(TerrainType.BUILDING) > phoenix.terrain_count(
        TerrainType.BUILDING
    )


def test_phoenix_has_substantial_open_space() -> None:
    config = load_zombie_config()

    phoenix = generate_city(
        config,
        CityId.PHOENIX,
    )

    assert phoenix.terrain_count(TerrainType.OPEN_SPACE) > 0


def test_chicago_has_synthetic_barrier_and_limited_bridges() -> None:
    config = load_zombie_config()

    chicago = generate_city(
        config,
        CityId.CHICAGO,
    )

    assert chicago.synthetic_barrier_cells

    bridge_rows = {
        6,
        18,
        30,
    }

    for row in bridge_rows:
        for column in (
            17,
            18,
        ):
            assert (
                chicago.cell(
                    GridPosition(
                        row,
                        column,
                    )
                ).terrain
                is TerrainType.ARTERIAL
            )

    for position in chicago.synthetic_barrier_cells:
        assert position.row not in bridge_rows

        assert position.column in {
            17,
            18,
        }

        assert chicago.cell(position).terrain is TerrainType.BUILDING


def test_building_cells_have_zero_risk() -> None:
    for city in _cities():
        for cell in city.cells:
            if cell.terrain is TerrainType.BUILDING:
                assert cell.observed_risk == 0.0
                assert cell.true_risk == 0.0


def test_traversable_neighbor_order_remains_deterministic() -> None:
    config = load_zombie_config()

    phoenix = generate_city(
        config,
        CityId.PHOENIX,
    )

    position = GridPosition(
        17,
        16,
    )

    first = phoenix.traversable_neighbors(position)

    second = phoenix.traversable_neighbors(position)

    assert first == second
