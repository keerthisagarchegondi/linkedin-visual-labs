"""Deep-learning prediction and routing tests for Project 2."""

from __future__ import annotations

from linkedin_visual_labs.projects.p04_zombie_escape import (
    PlannerCostEngine,
    astar_shortest_path,
    generate_all_cities,
    load_zombie_config,
    mapping_risk_lookup,
    validate_path_legality,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_model import (
    TrainedDLRiskModel,
    train_dl_risk_model,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_pipeline import (
    predict_showcase_dl_risk_maps,
)


def _small_model() -> TrainedDLRiskModel:
    return train_dl_risk_model(
        load_zombie_config(),
        random_seed=4305,
        epochs=1,
        batch_size=4,
        training_city_limit=8,
        validation_city_limit=3,
        benchmark_city_limit=3,
    )


def test_dl_maps_cover_every_traversable_showcase_cell() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    maps = predict_showcase_dl_risk_maps(
        _small_model(),
        cities,
    )

    for city in cities:
        assert set(maps[city.city_id.value]) == set(city.traversable_positions())


def test_dl_predictions_remain_inside_unit_interval() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    maps = predict_showcase_dl_risk_maps(
        _small_model(),
        cities,
    )

    for city_map in maps.values():
        assert all(0.0 <= prediction <= 1.0 for prediction in city_map.values())


def test_dl_prediction_is_deterministic() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    model = _small_model()

    first = predict_showcase_dl_risk_maps(
        model,
        cities,
    )

    second = predict_showcase_dl_risk_maps(
        model,
        cities,
    )

    assert first == second


def test_dl_predictions_produce_legal_astar_routes() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    maps = predict_showcase_dl_risk_maps(
        _small_model(),
        cities,
    )

    engine = PlannerCostEngine.from_config(config)

    for city in cities:
        route = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=mapping_risk_lookup(maps[city.city_id.value]),
        )

        validate_path_legality(
            city,
            route.path,
        )


def test_dl_astar_routes_are_deterministic() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    maps = predict_showcase_dl_risk_maps(
        _small_model(),
        cities,
    )

    engine = PlannerCostEngine.from_config(config)

    for city in cities:
        risk_lookup = mapping_risk_lookup(maps[city.city_id.value])

        first = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=risk_lookup,
        )

        second = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=risk_lookup,
        )

        assert first == second
