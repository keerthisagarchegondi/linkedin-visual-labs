"""Domain-model tests for Project 2."""

from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityId,
    GridCell,
    GridDefinition,
    GridPosition,
    MethodId,
    MovementRule,
    RouteMetrics,
    RouteResult,
    TerrainType,
    ZombieModelError,
    load_zombie_config,
)


def test_grid_position_rejects_negative_coordinates() -> None:
    with pytest.raises(
        ZombieModelError,
        match="row",
    ):
        GridPosition(
            row=-1,
            column=0,
        )


def test_grid_definition_contains_positions() -> None:
    grid = GridDefinition(
        rows=36,
        columns=36,
        movement=MovementRule.FOUR_NEIGHBOR,
        allow_diagonal=False,
        step_distance=1.0,
    )

    assert grid.contains(
        GridPosition(
            0,
            0,
        )
    )

    assert grid.contains(
        GridPosition(
            35,
            35,
        )
    )

    assert not grid.contains(
        GridPosition(
            36,
            0,
        )
    )


def test_typed_config_start_destinations_are_in_bounds() -> None:
    config = load_zombie_config()

    for city in config.cities:
        assert config.experiment.grid.contains(city.start)

        assert config.experiment.grid.contains(city.destination)


def test_grid_cell_validates_risk_range() -> None:
    cell = GridCell(
        position=GridPosition(
            row=1,
            column=1,
        ),
        terrain=TerrainType.LOCAL_ROAD,
        observed_risk=0.25,
        true_risk=0.75,
    )

    assert cell.observed_risk == 0.25
    assert cell.true_risk == 0.75

    with pytest.raises(
        ZombieModelError,
        match="true_risk",
    ):
        GridCell(
            position=GridPosition(
                row=1,
                column=1,
            ),
            terrain=TerrainType.LOCAL_ROAD,
            observed_risk=0.25,
            true_risk=1.1,
        )


def test_route_result_has_typed_future_solver_contract() -> None:
    start = GridPosition(
        row=1,
        column=1,
    )

    destination = GridPosition(
        row=1,
        column=2,
    )

    route = RouteResult(
        city_id=CityId.PHOENIX,
        method_id=MethodId.DIJKSTRA,
        start=start,
        destination=destination,
        path=(
            start,
            destination,
        ),
        route_valid=True,
        metrics=RouteMetrics(
            distance=1.0,
            travel_time=1.0,
            true_cumulative_risk=0.2,
            maximum_local_true_risk=0.2,
            high_risk_cells_crossed=0,
            oracle_risk_regret=0.0,
        ),
    )

    assert route.path[0] == start

    assert route.path[-1] == destination


def test_route_result_rejects_wrong_start() -> None:
    with pytest.raises(
        ZombieModelError,
        match="start",
    ):
        RouteResult(
            city_id=CityId.CHICAGO,
            method_id=MethodId.ML,
            start=GridPosition(
                0,
                0,
            ),
            destination=GridPosition(
                0,
                2,
            ),
            path=(
                GridPosition(
                    0,
                    1,
                ),
                GridPosition(
                    0,
                    2,
                ),
            ),
            route_valid=True,
            metrics=RouteMetrics(
                distance=1.0,
                travel_time=1.0,
                true_cumulative_risk=0.0,
                maximum_local_true_risk=0.0,
                high_risk_cells_crossed=0,
                oracle_risk_regret=0.0,
            ),
        )
