"""Classical ML routing integration tests."""

from __future__ import annotations

import pandas as pd

from linkedin_visual_labs.projects.p04_zombie_escape import (
    PlannerCostEngine,
    astar_shortest_path,
    generate_all_cities,
    load_zombie_config,
    mapping_risk_lookup,
    validate_path_legality,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_data import (
    _generate_split,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_model import (
    TrainedMLRiskModel,
    train_ml_risk_model,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_pipeline import (
    predict_showcase_risk_maps,
)


def _trained_small_model() -> TrainedMLRiskModel:
    config = load_zombie_config()

    dataset = pd.concat(
        [
            _generate_split(
                config,
                split="training",
                count=30,
                base_seed=8201,
            ),
            _generate_split(
                config,
                split="validation",
                count=10,
                base_seed=8202,
            ),
            _generate_split(
                config,
                split="benchmark",
                count=10,
                base_seed=8203,
            ),
        ],
        ignore_index=True,
    )

    return train_ml_risk_model(
        dataset,
        random_seed=4304,
    )


def test_showcase_ml_prediction_maps_cover_all_traversable_cells() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    maps = predict_showcase_risk_maps(
        _trained_small_model(),
        cities,
    )

    for city in cities:
        assert set(maps[city.city_id.value]) == set(city.traversable_positions())


def test_ml_predictions_produce_legal_astar_routes() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    maps = predict_showcase_risk_maps(
        _trained_small_model(),
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


def test_showcase_prediction_is_deterministic() -> None:
    config = load_zombie_config()

    cities = generate_all_cities(config)

    trained = _trained_small_model()

    first = predict_showcase_risk_maps(
        trained,
        cities,
    )

    second = predict_showcase_risk_maps(
        trained,
        cities,
    )

    assert first == second
