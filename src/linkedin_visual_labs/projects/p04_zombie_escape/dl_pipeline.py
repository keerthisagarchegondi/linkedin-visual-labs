"""End-to-end deep-learning pipeline for Zombie Escape."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
    generate_all_cities,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_model import (
    TrainedDLRiskModel,
    persist_dl_risk_model,
    predict_dense_risk,
    train_dl_risk_model,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_tensors import (
    city_to_tensor,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    GridPosition,
    MethodId,
    RouteResult,
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
class DLPipelineResult:
    """Artifacts produced by one complete Step 6 pipeline."""

    checkpoint_path: Path
    metadata_path: Path
    predicted_risk_maps_path: Path
    routes_path: Path


def run_dl_pipeline(
    context: ZombiePipelineContext,
    *,
    epochs: int = 8,
    batch_size: int = 32,
    training_city_limit: int | None = None,
    validation_city_limit: int | None = None,
    benchmark_city_limit: int | None = None,
) -> DLPipelineResult:
    """Run deterministic CNN training, prediction, and DL routing."""
    config = context.configuration

    trained = train_dl_risk_model(
        config,
        random_seed=(config.training.seeds.dl_model),
        epochs=epochs,
        batch_size=batch_size,
        training_city_limit=(training_city_limit),
        validation_city_limit=(validation_city_limit),
        benchmark_city_limit=(benchmark_city_limit),
    )

    model_directory = context.resolve_output_path(context.outputs.models.dl)

    checkpoint_path, metadata_path = persist_dl_risk_model(
        trained,
        model_directory,
    )

    cities = generate_all_cities(config)

    dl_maps = predict_showcase_dl_risk_maps(
        trained,
        cities,
    )

    predicted_risk_maps_path = context.resolve_output_path(context.outputs.data.predicted_risk_maps)

    merge_dl_predictions(
        predicted_risk_maps_path,
        dl_maps,
    )

    routes_path = context.resolve_output_path(context.outputs.data.routes)

    solve_all_routes_from_persisted_predictions(context)

    return DLPipelineResult(
        checkpoint_path=checkpoint_path,
        metadata_path=metadata_path,
        predicted_risk_maps_path=(predicted_risk_maps_path),
        routes_path=routes_path,
    )


def predict_showcase_dl_risk_maps(
    trained: TrainedDLRiskModel,
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
    """Predict dense risk for every traversable showcase cell."""
    result: dict[
        str,
        dict[
            GridPosition,
            float,
        ],
    ] = {}

    for city in cities:
        tensor = city_to_tensor(city)

        prediction = predict_dense_risk(
            trained.model,
            tensor.inputs,
        )

        city_map: dict[
            GridPosition,
            float,
        ] = {}

        for position in city.traversable_positions():
            city_map[position] = float(
                prediction[
                    0,
                    position.row,
                    position.column,
                ].item()
            )

        result[city.city_id.value] = city_map

    return result


def merge_dl_predictions(
    path: Path,
    maps: dict[
        str,
        dict[
            GridPosition,
            float,
        ],
    ],
) -> None:
    """Preserve Step 5 ML predictions and append a DL prediction section."""
    if not path.is_file():
        raise FileNotFoundError("Step 5 predicted_risk_maps.json is required before Step 6")

    payload = json.loads(path.read_text(encoding="utf-8"))

    payload["stage"] = "classical_ml_and_dl"

    payload["dl"] = {
        "risk_estimator": ("convolutional_neural_network"),
        "cities": {
            city_id: [
                {
                    "row": position.row,
                    "column": (position.column),
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


def solve_all_routes_from_persisted_predictions(
    context: ZombiePipelineContext,
) -> Path:
    """Build Dijkstra, ML, DL, and Oracle routes from persisted risk maps."""
    prediction_path = context.resolve_output_path(context.outputs.data.predicted_risk_maps)

    if not prediction_path.is_file():
        raise FileNotFoundError("predicted_risk_maps.json is required")

    prediction_payload = json.loads(prediction_path.read_text(encoding="utf-8"))

    ml_maps = _deserialize_maps(prediction_payload["cities"])

    dl_section = prediction_payload.get("dl")

    if not isinstance(
        dl_section,
        dict,
    ):
        raise RuntimeError("DL predictions are missing from predicted_risk_maps.json")

    dl_maps = _deserialize_maps(dl_section["cities"])

    config = context.configuration

    cities = generate_all_cities(config)

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

        oracle_true_risk = oracle_evaluation.true_cumulative_risk

        ml_route = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=mapping_risk_lookup(ml_maps[city.city_id.value]),
        )

        dl_route = astar_shortest_path(
            city,
            cost_engine=engine,
            risk_lookup=mapping_risk_lookup(dl_maps[city.city_id.value]),
        )

        baseline_result = build_headline_route_result(
            city,
            method_id=MethodId.DIJKSTRA,
            planned_path=baseline,
            cost_engine=engine,
            high_risk_threshold=threshold,
            oracle_true_cumulative_risk=(oracle_true_risk),
        )

        ml_result = build_headline_route_result(
            city,
            method_id=MethodId.ML,
            planned_path=ml_route,
            cost_engine=engine,
            high_risk_threshold=threshold,
            oracle_true_cumulative_risk=(oracle_true_risk),
        )

        dl_result = build_headline_route_result(
            city,
            method_id=MethodId.DL,
            planned_path=dl_route,
            cost_engine=engine,
            high_risk_threshold=threshold,
            oracle_true_cumulative_risk=(oracle_true_risk),
        )

        city_payloads.append(
            {
                "city_id": (city.city_id.value),
                "methods": {
                    "dijkstra": (_route_payload(baseline_result)),
                    "ml": (_route_payload(ml_result)),
                    "dl": (_route_payload(dl_result)),
                },
                "oracle": {
                    "path": [
                        {
                            "row": item.row,
                            "column": (item.column),
                        }
                        for item in oracle.path
                    ],
                    "true_cumulative_risk": (oracle_true_risk),
                },
            }
        )

    routes_path = context.resolve_output_path(context.outputs.data.routes)

    routes_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    routes_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "stage": "step6_complete",
                "headline_methods_complete": True,
                "available_headline_methods": [
                    "dijkstra",
                    "ml",
                    "dl",
                ],
                "pending_headline_methods": [],
                "cities": city_payloads,
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return routes_path


def _deserialize_maps(
    raw: object,
) -> dict[
    str,
    dict[
        GridPosition,
        float,
    ],
]:
    if not isinstance(
        raw,
        dict,
    ):
        raise TypeError("Prediction cities must be a mapping")

    result: dict[
        str,
        dict[
            GridPosition,
            float,
        ],
    ] = {}

    for city_id, rows in raw.items():
        if not isinstance(
            city_id,
            str,
        ):
            raise TypeError("Prediction city ID must be a string")

        if not isinstance(
            rows,
            list,
        ):
            raise TypeError("Prediction city rows must be a list")

        city_map: dict[
            GridPosition,
            float,
        ] = {}

        for item in rows:
            if not isinstance(
                item,
                dict,
            ):
                raise TypeError("Prediction row must be an object")

            position = GridPosition(
                row=int(item["row"]),
                column=int(item["column"]),
            )

            city_map[position] = float(item["predicted_risk"])

        result[city_id] = city_map

    return result


def _route_payload(
    result: RouteResult,
) -> dict[
    str,
    Any,
]:
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
