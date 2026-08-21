"""Exact routing-engine tests for Project 2."""

from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityDefinition,
    CityId,
    CityProfile,
    GridCell,
    GridDefinition,
    GridPosition,
    MethodId,
    MovementRule,
    PlannerCostEngine,
    RoutePlanner,
    TerrainType,
    astar_shortest_path,
    build_headline_route_result,
    compute_route_evaluation_with_threshold,
    dijkstra_shortest_path,
    mapping_risk_lookup,
    observed_dijkstra_route,
    oracle_astar_route,
    validate_path_legality,
)
from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
)
from linkedin_visual_labs.projects.p04_zombie_escape.routing import (
    RoutePlanningError,
)


def _engine() -> PlannerCostEngine:
    return PlannerCostEngine(
        step_distance=1.0,
        risk_weight=4.0,
        speed_multipliers={
            TerrainType.BUILDING: 0.0,
            TerrainType.LOCAL_ROAD: 1.0,
            TerrainType.ARTERIAL: 1.35,
            TerrainType.SLOW_TERRAIN: 0.70,
            TerrainType.OPEN_SPACE: 0.85,
        },
    )


def _city(
    *,
    rows: int,
    columns: int,
    start: GridPosition,
    destination: GridPosition,
    buildings: set[GridPosition] | None = None,
    observed_risk: dict[GridPosition, float] | None = None,
    true_risk: dict[GridPosition, float] | None = None,
    terrain_overrides: dict[
        GridPosition,
        TerrainType,
    ]
    | None = None,
) -> GeneratedCity:
    building_positions = set() if buildings is None else buildings

    observed = {} if observed_risk is None else observed_risk

    truth = {} if true_risk is None else true_risk

    overrides = {} if terrain_overrides is None else terrain_overrides

    grid = GridDefinition(
        rows=rows,
        columns=columns,
        movement=MovementRule.FOUR_NEIGHBOR,
        allow_diagonal=False,
        step_distance=1.0,
    )

    definition = CityDefinition(
        city_id=CityId.PHOENIX,
        display_name="Exact Test City",
        inspiration_only=True,
        seed=1,
        start=start,
        destination=destination,
        profile=CityProfile(
            block_density="test",
            intersection_density="test",
            arterial_width="test",
            choke_point_density="test",
            hidden_risk_structure="test",
            synthetic_barrier="none",
        ),
    )

    cells: list[GridCell] = []

    for row in range(rows):
        for column in range(columns):
            position = GridPosition(
                row,
                column,
            )

            terrain = overrides.get(
                position,
                TerrainType.LOCAL_ROAD,
            )

            if position in building_positions:
                terrain = TerrainType.BUILDING

            cells.append(
                GridCell(
                    position=position,
                    terrain=terrain,
                    observed_risk=(
                        0.0
                        if terrain is TerrainType.BUILDING
                        else observed.get(
                            position,
                            0.0,
                        )
                    ),
                    true_risk=(
                        0.0
                        if terrain is TerrainType.BUILDING
                        else truth.get(
                            position,
                            0.0,
                        )
                    ),
                )
            )

    return GeneratedCity(
        definition=definition,
        grid=grid,
        cells=tuple(cells),
        visible_zombie_zones=(),
        hidden_risk_hotspots=(),
        synthetic_barrier_cells=(),
    )


def _zero_risk(
    city: GeneratedCity,
) -> dict[GridPosition, float]:
    return {cell.position: 0.0 for cell in city.cells}


def test_dijkstra_exact_route_uses_deterministic_tie_break() -> None:
    city = _city(
        rows=3,
        columns=3,
        start=GridPosition(
            2,
            0,
        ),
        destination=GridPosition(
            0,
            2,
        ),
    )

    result = dijkstra_shortest_path(
        city,
        cost_engine=_engine(),
        risk_lookup=mapping_risk_lookup(_zero_risk(city)),
    )

    assert result.planner is RoutePlanner.DIJKSTRA

    assert result.path == (
        GridPosition(
            2,
            0,
        ),
        GridPosition(
            1,
            0,
        ),
        GridPosition(
            0,
            0,
        ),
        GridPosition(
            0,
            1,
        ),
        GridPosition(
            0,
            2,
        ),
    )

    assert result.objective_cost == pytest.approx(4.0)


def test_astar_exact_route_matches_dijkstra_on_equal_cost_grid() -> None:
    city = _city(
        rows=3,
        columns=3,
        start=GridPosition(
            2,
            0,
        ),
        destination=GridPosition(
            0,
            2,
        ),
    )

    risks = mapping_risk_lookup(_zero_risk(city))

    dijkstra = dijkstra_shortest_path(
        city,
        cost_engine=_engine(),
        risk_lookup=risks,
    )

    astar = astar_shortest_path(
        city,
        cost_engine=_engine(),
        risk_lookup=risks,
    )

    assert astar.planner is RoutePlanner.ASTAR

    assert astar.path == dijkstra.path

    assert astar.objective_cost == pytest.approx(dijkstra.objective_cost)


def test_observed_risk_can_make_longer_route_optimal() -> None:
    start = GridPosition(
        1,
        0,
    )

    destination = GridPosition(
        1,
        4,
    )

    risky_middle = {
        GridPosition(
            1,
            1,
        ): 1.0,
        GridPosition(
            1,
            2,
        ): 1.0,
        GridPosition(
            1,
            3,
        ): 1.0,
    }

    city = _city(
        rows=3,
        columns=5,
        start=start,
        destination=destination,
        observed_risk=risky_middle,
    )

    result = observed_dijkstra_route(
        city,
        cost_engine=_engine(),
    )

    assert (
        GridPosition(
            1,
            2,
        )
        not in result.path
    )

    assert len(result.path) == 7


def test_dijkstra_avoids_buildings() -> None:
    city = _city(
        rows=3,
        columns=3,
        start=GridPosition(
            1,
            0,
        ),
        destination=GridPosition(
            1,
            2,
        ),
        buildings={
            GridPosition(
                1,
                1,
            ),
        },
    )

    result = observed_dijkstra_route(
        city,
        cost_engine=_engine(),
    )

    assert (
        GridPosition(
            1,
            1,
        )
        not in result.path
    )

    validate_path_legality(
        city,
        result.path,
    )


def test_unreachable_destination_raises() -> None:
    city = _city(
        rows=3,
        columns=3,
        start=GridPosition(
            2,
            0,
        ),
        destination=GridPosition(
            0,
            2,
        ),
        buildings={
            GridPosition(
                0,
                1,
            ),
            GridPosition(
                1,
                2,
            ),
            GridPosition(
                1,
                1,
            ),
        },
    )

    with pytest.raises(
        RoutePlanningError,
        match="No legal route",
    ):
        observed_dijkstra_route(
            city,
            cost_engine=_engine(),
        )


def test_path_legality_rejects_diagonal_move() -> None:
    city = _city(
        rows=2,
        columns=2,
        start=GridPosition(
            0,
            0,
        ),
        destination=GridPosition(
            1,
            1,
        ),
    )

    with pytest.raises(
        RoutePlanningError,
        match="non-cardinal",
    ):
        validate_path_legality(
            city,
            (
                GridPosition(
                    0,
                    0,
                ),
                GridPosition(
                    1,
                    1,
                ),
            ),
        )


def test_path_legality_rejects_building_crossing() -> None:
    city = _city(
        rows=1,
        columns=3,
        start=GridPosition(
            0,
            0,
        ),
        destination=GridPosition(
            0,
            2,
        ),
        buildings={
            GridPosition(
                0,
                1,
            ),
        },
    )

    with pytest.raises(
        RoutePlanningError,
        match="impassable",
    ):
        validate_path_legality(
            city,
            (
                GridPosition(
                    0,
                    0,
                ),
                GridPosition(
                    0,
                    1,
                ),
                GridPosition(
                    0,
                    2,
                ),
            ),
        )


def test_route_metrics_use_true_risk_not_observed_risk() -> None:
    city = _city(
        rows=1,
        columns=3,
        start=GridPosition(
            0,
            0,
        ),
        destination=GridPosition(
            0,
            2,
        ),
        observed_risk={
            GridPosition(
                0,
                1,
            ): 0.0,
            GridPosition(
                0,
                2,
            ): 0.0,
        },
        true_risk={
            GridPosition(
                0,
                1,
            ): 0.7,
            GridPosition(
                0,
                2,
            ): 0.2,
        },
    )

    path = (
        GridPosition(
            0,
            0,
        ),
        GridPosition(
            0,
            1,
        ),
        GridPosition(
            0,
            2,
        ),
    )

    evaluation = compute_route_evaluation_with_threshold(
        city,
        path,
        cost_engine=_engine(),
        high_risk_threshold=0.65,
    )

    assert evaluation.distance == pytest.approx(2.0)

    assert evaluation.travel_time == pytest.approx(2.0)

    assert evaluation.true_cumulative_risk == pytest.approx(0.9)

    assert evaluation.maximum_local_true_risk == pytest.approx(0.7)

    assert evaluation.high_risk_cells_crossed == 1

    assert evaluation.route_valid is True


def test_route_metrics_respect_terrain_speed() -> None:
    destination = GridPosition(
        0,
        2,
    )

    city = _city(
        rows=1,
        columns=3,
        start=GridPosition(
            0,
            0,
        ),
        destination=destination,
        terrain_overrides={
            GridPosition(
                0,
                1,
            ): TerrainType.ARTERIAL,
            destination: TerrainType.SLOW_TERRAIN,
        },
    )

    path = (
        GridPosition(
            0,
            0,
        ),
        GridPosition(
            0,
            1,
        ),
        destination,
    )

    evaluation = compute_route_evaluation_with_threshold(
        city,
        path,
        cost_engine=_engine(),
        high_risk_threshold=0.65,
    )

    expected_time = 1.0 / 1.35 + 1.0 / 0.70

    assert evaluation.travel_time == pytest.approx(expected_time)


def test_oracle_uses_true_risk_explicitly() -> None:
    risky_truth = {
        GridPosition(
            1,
            1,
        ): 1.0,
        GridPosition(
            1,
            2,
        ): 1.0,
        GridPosition(
            1,
            3,
        ): 1.0,
    }

    city = _city(
        rows=3,
        columns=5,
        start=GridPosition(
            1,
            0,
        ),
        destination=GridPosition(
            1,
            4,
        ),
        true_risk=risky_truth,
    )

    observed = observed_dijkstra_route(
        city,
        cost_engine=_engine(),
    )

    oracle = oracle_astar_route(
        city,
        cost_engine=_engine(),
    )

    assert (
        GridPosition(
            1,
            2,
        )
        in observed.path
    )

    assert (
        GridPosition(
            1,
            2,
        )
        not in oracle.path
    )


def test_oracle_regret_is_computed_from_true_cumulative_risk() -> None:
    evaluation = compute_route_evaluation_with_threshold(
        _city(
            rows=1,
            columns=3,
            start=GridPosition(
                0,
                0,
            ),
            destination=GridPosition(
                0,
                2,
            ),
            true_risk={
                GridPosition(
                    0,
                    1,
                ): 0.6,
                GridPosition(
                    0,
                    2,
                ): 0.2,
            },
        ),
        (
            GridPosition(
                0,
                0,
            ),
            GridPosition(
                0,
                1,
            ),
            GridPosition(
                0,
                2,
            ),
        ),
        cost_engine=_engine(),
        high_risk_threshold=0.65,
    )

    metrics = evaluation.to_route_metrics(oracle_true_cumulative_risk=0.3)

    assert metrics.oracle_risk_regret == pytest.approx(0.5)


def test_headline_route_result_contains_final_metrics() -> None:
    city = _city(
        rows=1,
        columns=3,
        start=GridPosition(
            0,
            0,
        ),
        destination=GridPosition(
            0,
            2,
        ),
    )

    planned = observed_dijkstra_route(
        city,
        cost_engine=_engine(),
    )

    result = build_headline_route_result(
        city,
        method_id=MethodId.DIJKSTRA,
        planned_path=planned,
        cost_engine=_engine(),
        high_risk_threshold=0.65,
        oracle_true_cumulative_risk=0.0,
    )

    assert result.city_id is CityId.PHOENIX

    assert result.method_id is MethodId.DIJKSTRA

    assert result.route_valid is True

    assert result.path == planned.path


def test_invalid_risk_map_value_is_rejected() -> None:
    city = _city(
        rows=1,
        columns=2,
        start=GridPosition(
            0,
            0,
        ),
        destination=GridPosition(
            0,
            1,
        ),
    )

    risk = mapping_risk_lookup(
        {
            GridPosition(
                0,
                0,
            ): 0.0,
            GridPosition(
                0,
                1,
            ): 1.5,
        }
    )

    with pytest.raises(
        RoutePlanningError,
        match=r"\[0, 1\]",
    ):
        dijkstra_shortest_path(
            city,
            cost_engine=_engine(),
            risk_lookup=risk,
        )


def test_missing_predicted_risk_cell_is_rejected() -> None:
    city = _city(
        rows=1,
        columns=2,
        start=GridPosition(
            0,
            0,
        ),
        destination=GridPosition(
            0,
            1,
        ),
    )

    risk = mapping_risk_lookup(
        {
            GridPosition(
                0,
                0,
            ): 0.0,
        }
    )

    with pytest.raises(
        RoutePlanningError,
        match="missing position",
    ):
        astar_shortest_path(
            city,
            cost_engine=_engine(),
            risk_lookup=risk,
        )


def test_astar_and_dijkstra_have_equal_optimal_cost_on_showcase_city() -> None:
    from linkedin_visual_labs.projects.p04_zombie_escape import (
        generate_city,
        load_zombie_config,
        observed_risk_lookup,
    )

    config = load_zombie_config()

    city = generate_city(
        config,
        CityId.CHICAGO,
    )

    engine = PlannerCostEngine.from_config(config)

    risk = observed_risk_lookup(city)

    dijkstra = dijkstra_shortest_path(
        city,
        cost_engine=engine,
        risk_lookup=risk,
    )

    astar = astar_shortest_path(
        city,
        cost_engine=engine,
        risk_lookup=risk,
    )

    assert math.isclose(
        dijkstra.objective_cost,
        astar.objective_cost,
        rel_tol=0.0,
        abs_tol=1e-9,
    )
