"""Showcase-city routing integration tests."""

from __future__ import annotations

import math

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityId,
    PlannerCostEngine,
    astar_shortest_path,
    compute_route_evaluation_with_threshold,
    generate_all_cities,
    load_zombie_config,
    observed_dijkstra_route,
    observed_risk_lookup,
    oracle_astar_route,
    validate_path_legality,
)


def test_every_showcase_city_has_legal_dijkstra_route() -> None:
    config = load_zombie_config()

    engine = PlannerCostEngine.from_config(config)

    for city in generate_all_cities(config):
        route = observed_dijkstra_route(
            city,
            cost_engine=engine,
        )

        validate_path_legality(
            city,
            route.path,
        )


def test_every_showcase_city_has_legal_oracle_route() -> None:
    config = load_zombie_config()

    engine = PlannerCostEngine.from_config(config)

    for city in generate_all_cities(config):
        route = oracle_astar_route(
            city,
            cost_engine=engine,
        )

        validate_path_legality(
            city,
            route.path,
        )


def test_dijkstra_and_astar_agree_on_observed_objective() -> None:
    config = load_zombie_config()

    engine = PlannerCostEngine.from_config(config)

    for city in generate_all_cities(config):
        risk = observed_risk_lookup(city)

        dijkstra = observed_dijkstra_route(
            city,
            cost_engine=engine,
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


def test_dijkstra_routes_are_exactly_deterministic() -> None:
    config = load_zombie_config()

    engine = PlannerCostEngine.from_config(config)

    for city in generate_all_cities(config):
        first = observed_dijkstra_route(
            city,
            cost_engine=engine,
        )

        second = observed_dijkstra_route(
            city,
            cost_engine=engine,
        )

        assert first == second


def test_astar_routes_are_exactly_deterministic() -> None:
    config = load_zombie_config()

    engine = PlannerCostEngine.from_config(config)

    for city in generate_all_cities(config):
        risk = observed_risk_lookup(city)

        first = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=risk,
        )

        second = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=risk,
        )

        assert first == second


def test_route_metrics_are_valid_for_every_showcase_city() -> None:
    config = load_zombie_config()

    engine = PlannerCostEngine.from_config(config)

    threshold = config.experiment.risk.high_risk_threshold

    for city in generate_all_cities(config):
        route = observed_dijkstra_route(
            city,
            cost_engine=engine,
        )

        evaluation = compute_route_evaluation_with_threshold(
            city,
            route.path,
            cost_engine=engine,
            high_risk_threshold=threshold,
        )

        assert evaluation.route_valid is True

        assert evaluation.distance > 0.0

        assert evaluation.travel_time > 0.0

        assert evaluation.true_cumulative_risk >= 0.0

        assert 0.0 <= evaluation.maximum_local_true_risk <= 1.0

        assert evaluation.high_risk_cells_crossed >= 0


def test_showcase_city_identity_is_preserved() -> None:
    cities = generate_all_cities(load_zombie_config())

    assert tuple(city.city_id for city in cities) == (
        CityId.PHOENIX,
        CityId.NEW_YORK,
        CityId.CHICAGO,
    )
