"""End-to-end classical ML pipeline for Zombie Escape."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
    generate_all_cities,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_data import (
    generate_training_dataset,
    write_training_dataset,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_features import (
    showcase_feature_frame,
    validate_no_feature_leakage,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_model import (
    TrainedMLRiskModel,
    persist_ml_risk_model,
    predict_risk,
    train_ml_risk_model,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    GridPosition,
    MethodId,
)
from linkedin_visual_labs.projects.p04_zombie_escape.pipeline import (
    ZombiePipelineContext,
)
from linkedin_visual_labs.projects.p04_zombie_escape.routing import (
    PlannerCostEngine,
    astar_shortest_path,
    build_headline_route_result,
    compute_route_evaluation_with_threshold,
    mapping_risk_lookup,
    observed_dijkstra_route,
    oracle_astar_route,
)


@dataclass(frozen=True, slots=True)
class MLPipelineResult:
    """Paths and metrics produced by one deterministic ML pipeline run."""

    training_dataset_path: Path
    model_path: Path
    metadata_path: Path
    predicted_risk_maps_path: Path
    routes_path: Path


def run_ml_pipeline(
    context: ZombiePipelineContext,
) -> MLPipelineResult:
    """Run complete Step 5 classical ML pipeline."""
    config = context.configuration

    validate_no_feature_leakage()

    dataset = generate_training_dataset(config)

    training_dataset_path = context.resolve_output_path(context.outputs.data.training_dataset)

    write_training_dataset(
        dataset,
        training_dataset_path,
    )

    trained = train_ml_risk_model(
        dataset,
        random_seed=(config.training.seeds.ml_model),
    )

    model_directory = context.resolve_output_path(context.outputs.models.ml)

    model_path, metadata_path = persist_ml_risk_model(
        trained,
        model_directory,
    )

    cities = generate_all_cities(config)

    predicted_maps = predict_showcase_risk_maps(
        trained,
        cities,
    )

    predicted_risk_maps_path = context.resolve_output_path(context.outputs.data.predicted_risk_maps)

    _write_predicted_maps(
        predicted_maps,
        predicted_risk_maps_path,
    )

    routes_path = context.resolve_output_path(context.outputs.data.routes)

    _write_step5_routes(
        context,
        cities,
        predicted_maps,
        routes_path,
    )

    return MLPipelineResult(
        training_dataset_path=(training_dataset_path),
        model_path=model_path,
        metadata_path=metadata_path,
        predicted_risk_maps_path=(predicted_risk_maps_path),
        routes_path=routes_path,
    )


def predict_showcase_risk_maps(
    trained: TrainedMLRiskModel,
    cities: tuple[
        GeneratedCity,
        ...,
    ],
) -> dict[
    str,
    dict[
        GridPosition,
        float,
    ],
]:
    """Predict risk for every traversable showcase cell."""
    result: dict[
        str,
        dict[
            GridPosition,
            float,
        ],
    ] = {}

    for city in cities:
        frame, positions = showcase_feature_frame(city)

        predictions = predict_risk(
            trained,
            frame,
        )

        city_map = {
            position: float(prediction)
            for position, prediction in zip(
                positions,
                predictions,
                strict=True,
            )
        }

        result[city.city_id.value] = city_map

    return result


def _write_predicted_maps(
    maps: dict[
        str,
        dict[
            GridPosition,
            float,
        ],
    ],
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "schema_version": 1,
        "stage": "classical_ml",
        "risk_estimator": ("gradient_boosting"),
        "cities": {
            city_id: [
                {
                    "row": position.row,
                    "column": position.column,
                    "predicted_risk": risk,
                }
                for position, risk in sorted(risk_map.items())
            ]
            for city_id, risk_map in sorted(maps.items())
        },
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_step5_routes(
    context: ZombiePipelineContext,
    cities: tuple[
        GeneratedCity,
        ...,
    ],
    predicted_maps: dict[
        str,
        dict[
            GridPosition,
            float,
        ],
    ],
    path: Path,
) -> None:
    config = context.configuration

    engine = PlannerCostEngine.from_config(config)

    threshold = config.experiment.risk.high_risk_threshold

    city_payloads = []

    for city in cities:
        baseline = observed_dijkstra_route(
            city,
            cost_engine=engine,
        )

        oracle = oracle_astar_route(
            city,
            cost_engine=engine,
        )

        oracle_evaluation = compute_route_evaluation_with_threshold(
            city,
            oracle.path,
            cost_engine=engine,
            high_risk_threshold=threshold,
        )

        ml_risk = predicted_maps[city.city_id.value]

        ml_route = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=mapping_risk_lookup(ml_risk),
        )

        baseline_result = build_headline_route_result(
            city,
            method_id=MethodId.DIJKSTRA,
            planned_path=baseline,
            cost_engine=engine,
            high_risk_threshold=threshold,
            oracle_true_cumulative_risk=(oracle_evaluation.true_cumulative_risk),
        )

        ml_result = build_headline_route_result(
            city,
            method_id=MethodId.ML,
            planned_path=ml_route,
            cost_engine=engine,
            high_risk_threshold=threshold,
            oracle_true_cumulative_risk=(oracle_evaluation.true_cumulative_risk),
        )

        city_payloads.append(
            {
                "city_id": (city.city_id.value),
                "methods": {
                    "dijkstra": (_route_payload(baseline_result)),
                    "ml": (_route_payload(ml_result)),
                },
                "oracle": {
                    "path": [
                        {
                            "row": item.row,
                            "column": item.column,
                        }
                        for item in oracle.path
                    ],
                    "true_cumulative_risk": (oracle_evaluation.true_cumulative_risk),
                },
            }
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": ("step5_partial"),
                "headline_methods_complete": False,
                "available_headline_methods": [
                    "dijkstra",
                    "ml",
                ],
                "pending_headline_methods": [
                    "dl",
                ],
                "cities": city_payloads,
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _route_payload(
    result: object,
) -> dict[str, object]:
    from linkedin_visual_labs.projects.p04_zombie_escape.models import (
        RouteResult,
    )

    if not isinstance(
        result,
        RouteResult,
    ):
        raise TypeError("Expected RouteResult")

    return {
        "route_valid": (result.route_valid),
        "start": {
            "row": result.start.row,
            "column": (result.start.column),
        },
        "destination": {
            "row": (result.destination.row),
            "column": (result.destination.column),
        },
        "path": [
            {
                "row": item.row,
                "column": item.column,
            }
            for item in result.path
        ],
        "metrics": {
            "distance": (result.metrics.distance),
            "travel_time": (result.metrics.travel_time),
            "true_cumulative_risk": (result.metrics.true_cumulative_risk),
            "maximum_local_true_risk": (result.metrics.maximum_local_true_risk),
            "high_risk_cells_crossed": (result.metrics.high_risk_cells_crossed),
            "oracle_risk_regret": (result.metrics.oracle_risk_regret),
        },
    }
