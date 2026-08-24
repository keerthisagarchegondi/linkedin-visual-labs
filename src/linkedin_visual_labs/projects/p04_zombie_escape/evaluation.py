"""Deterministic evaluation for Project 2 headline routing methods."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, cast

HEADLINE_METHODS: Final[tuple[str, ...]] = (
    "dijkstra",
    "ml",
    "dl",
)

METHOD_ORDER: Final[dict[str, int]] = {
    method_id: index for index, method_id in enumerate(HEADLINE_METHODS)
}

REALIZED_RISK_WEIGHT: Final[float] = 4.0

FLOAT_TIE_DIGITS: Final[int] = 12


@dataclass(frozen=True, slots=True)
class EvaluatedRoute:
    """Realized hidden-truth evaluation for one headline route."""

    city_id: str
    method_id: str
    route_valid: bool
    distance: float
    travel_time: float
    true_cumulative_risk: float
    maximum_local_true_risk: float
    high_risk_cells_crossed: int
    oracle_true_cumulative_risk: float
    oracle_risk_regret: float
    realized_objective: float
    best_headline_realized_objective: float
    normalized_objective_regret: float
    city_winner: bool


@dataclass(frozen=True, slots=True)
class CityEvaluation:
    """Headline-method comparison for one showcase city."""

    city_id: str
    winner_method: str
    best_headline_realized_objective: float
    oracle_true_cumulative_risk: float
    methods: tuple[EvaluatedRoute, ...]


@dataclass(frozen=True, slots=True)
class OverallMethodEvaluation:
    """Cross-city aggregate metrics for one headline method."""

    method_id: str
    city_wins: int
    mean_normalized_objective_regret: float
    mean_realized_objective: float
    mean_true_cumulative_risk: float
    mean_oracle_risk_regret: float
    mean_travel_time: float
    mean_distance: float


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Complete deterministic Step 7 evaluation."""

    cities: tuple[CityEvaluation, ...]
    methods: tuple[OverallMethodEvaluation, ...]
    overall_winner: str


@dataclass(frozen=True, slots=True)
class EvaluationArtifacts:
    """Paths written by the Step 7 evaluation pipeline."""

    summary_path: Path
    route_comparison_path: Path
    overall_comparison_path: Path


def realized_objective(
    *,
    travel_time: float,
    true_cumulative_risk: float,
) -> float:
    """Score one route using realized hidden-truth risk."""
    _require_finite_nonnegative(
        "travel_time",
        travel_time,
    )

    _require_finite_nonnegative(
        "true_cumulative_risk",
        true_cumulative_risk,
    )

    return travel_time + REALIZED_RISK_WEIGHT * true_cumulative_risk


def normalized_objective_regret(
    *,
    method_objective: float,
    best_headline_objective: float,
) -> float:
    """Normalize regret to the best headline method within one city."""
    _require_finite_nonnegative(
        "method_objective",
        method_objective,
    )

    if not math.isfinite(best_headline_objective) or best_headline_objective <= 0.0:
        raise ValueError("best_headline_objective must be finite and positive")

    difference = method_objective - best_headline_objective

    if difference < -1.0e-12:
        raise ValueError("method objective cannot be below the best headline objective")

    return (
        max(
            0.0,
            difference,
        )
        / best_headline_objective
    )


def evaluate_routes_payload(
    payload: Mapping[str, object],
) -> EvaluationSummary:
    """Evaluate a complete Step 6 routes payload."""
    if payload.get("stage") != "step6_complete":
        raise ValueError("Step 7 requires routes.json stage='step6_complete'")

    if payload.get("headline_methods_complete") is not True:
        raise ValueError("Step 7 requires all headline routes")

    raw_cities = _as_sequence(
        payload.get("cities"),
        label="cities",
    )

    if not raw_cities:
        raise ValueError("routes payload contains no cities")

    city_evaluations: list[CityEvaluation] = []

    for raw_city in raw_cities:
        city = _as_mapping(
            raw_city,
            label="city",
        )

        city_id = _as_string(
            city.get("city_id"),
            label="city_id",
        )

        methods = _as_mapping(
            city.get("methods"),
            label=f"{city_id}.methods",
        )

        if set(methods) != set(HEADLINE_METHODS):
            raise ValueError(f"{city_id}: headline method set must equal {HEADLINE_METHODS}")

        oracle = _as_mapping(
            city.get("oracle"),
            label=f"{city_id}.oracle",
        )

        oracle_true_risk = _oracle_true_cumulative_risk(
            oracle,
            label=f"{city_id}.oracle",
        )

        scored: dict[
            str,
            tuple[
                float,
                dict[str, object],
            ],
        ] = {}

        for method_id in HEADLINE_METHODS:
            route = _as_mapping(
                methods[method_id],
                label=(f"{city_id}.{method_id}"),
            )

            metrics = _route_metrics(
                route,
                label=(f"{city_id}.{method_id}"),
            )

            objective = realized_objective(
                travel_time=cast(
                    float,
                    metrics["travel_time"],
                ),
                true_cumulative_risk=cast(
                    float,
                    metrics["true_cumulative_risk"],
                ),
            )

            scored[method_id] = (
                objective,
                metrics,
            )

        winner_method = min(
            HEADLINE_METHODS,
            key=lambda method_id: _city_winner_key(
                method_id,
                scored[method_id][0],
                scored[method_id][1],
            ),
        )

        best_objective = scored[winner_method][0]

        route_evaluations: list[EvaluatedRoute] = []

        for method_id in HEADLINE_METHODS:
            objective, metrics = scored[method_id]

            true_risk = cast(
                float,
                metrics["true_cumulative_risk"],
            )

            computed_oracle_regret = max(
                0.0,
                true_risk - oracle_true_risk,
            )

            persisted_oracle_regret = cast(
                float,
                metrics["oracle_risk_regret"],
            )

            if not math.isclose(
                computed_oracle_regret,
                persisted_oracle_regret,
                rel_tol=1.0e-9,
                abs_tol=1.0e-9,
            ):
                raise ValueError(
                    f"{city_id}.{method_id}: "
                    "persisted oracle risk regret "
                    "does not match oracle benchmark"
                )

            route_evaluations.append(
                EvaluatedRoute(
                    city_id=city_id,
                    method_id=method_id,
                    route_valid=cast(
                        bool,
                        metrics["route_valid"],
                    ),
                    distance=cast(
                        float,
                        metrics["distance"],
                    ),
                    travel_time=cast(
                        float,
                        metrics["travel_time"],
                    ),
                    true_cumulative_risk=(true_risk),
                    maximum_local_true_risk=cast(
                        float,
                        metrics["maximum_local_true_risk"],
                    ),
                    high_risk_cells_crossed=cast(
                        int,
                        metrics["high_risk_cells_crossed"],
                    ),
                    oracle_true_cumulative_risk=(oracle_true_risk),
                    oracle_risk_regret=(persisted_oracle_regret),
                    realized_objective=objective,
                    best_headline_realized_objective=(best_objective),
                    normalized_objective_regret=(
                        normalized_objective_regret(
                            method_objective=objective,
                            best_headline_objective=(best_objective),
                        )
                    ),
                    city_winner=(method_id == winner_method),
                )
            )

        city_evaluations.append(
            CityEvaluation(
                city_id=city_id,
                winner_method=winner_method,
                best_headline_realized_objective=(best_objective),
                oracle_true_cumulative_risk=(oracle_true_risk),
                methods=tuple(route_evaluations),
            )
        )

    method_summaries = tuple(
        _aggregate_method(
            method_id,
            city_evaluations,
        )
        for method_id in HEADLINE_METHODS
    )

    overall_winner = min(
        HEADLINE_METHODS,
        key=lambda method_id: _overall_winner_key(
            next(summary for summary in method_summaries if (summary.method_id == method_id))
        ),
    )

    return EvaluationSummary(
        cities=tuple(city_evaluations),
        methods=method_summaries,
        overall_winner=overall_winner,
    )


def write_evaluation_artifacts(
    summary: EvaluationSummary,
    *,
    data_directory: Path,
) -> EvaluationArtifacts:
    """Write Step 7 JSON and CSV comparison artifacts."""
    data_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_path = data_directory / "evaluation_summary.json"

    route_comparison_path = data_directory / "route_comparison.csv"

    overall_comparison_path = data_directory / "overall_comparison.csv"

    summary_path.write_text(
        json.dumps(
            _summary_payload(
                summary,
                route_comparison_path=(route_comparison_path),
                overall_comparison_path=(overall_comparison_path),
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    _write_route_comparison(
        summary,
        route_comparison_path,
    )

    _write_overall_comparison(
        summary,
        overall_comparison_path,
    )

    return EvaluationArtifacts(
        summary_path=summary_path,
        route_comparison_path=(route_comparison_path),
        overall_comparison_path=(overall_comparison_path),
    )


def run_evaluation(
    routes_path: Path,
) -> EvaluationArtifacts:
    """Evaluate persisted Step 6 routes and write Step 7 artifacts."""
    if not routes_path.is_file():
        raise FileNotFoundError(f"routes artifact not found: {routes_path}")

    payload = cast(
        dict[str, object],
        json.loads(routes_path.read_text(encoding="utf-8")),
    )

    summary = evaluate_routes_payload(payload)

    return write_evaluation_artifacts(
        summary,
        data_directory=routes_path.parent,
    )


def _oracle_true_cumulative_risk(
    oracle: Mapping[str, object],
    *,
    label: str,
) -> float:
    return _as_nonnegative_float(
        oracle.get("true_cumulative_risk"),
        label=(f"{label}.true_cumulative_risk"),
    )


def _route_metrics(
    route: Mapping[str, object],
    *,
    label: str,
) -> dict[str, object]:
    if route.get("route_valid") is not True:
        raise ValueError(f"{label}: route is invalid")

    metrics = _as_mapping(
        route.get("metrics"),
        label=f"{label}.metrics",
    )

    distance = _as_nonnegative_float(
        metrics.get("distance"),
        label=f"{label}.distance",
    )

    travel_time = _as_nonnegative_float(
        metrics.get("travel_time"),
        label=f"{label}.travel_time",
    )

    true_risk = _as_nonnegative_float(
        metrics.get("true_cumulative_risk"),
        label=(f"{label}.true_cumulative_risk"),
    )

    max_risk = _as_nonnegative_float(
        metrics.get("maximum_local_true_risk"),
        label=(f"{label}.maximum_local_true_risk"),
    )

    if max_risk > 1.0:
        raise ValueError(f"{label}: maximum local risk exceeds 1")

    high_risk_cells = _as_nonnegative_int(
        metrics.get("high_risk_cells_crossed"),
        label=(f"{label}.high_risk_cells_crossed"),
    )

    oracle_risk_regret = _as_nonnegative_float(
        metrics.get("oracle_risk_regret"),
        label=(f"{label}.oracle_risk_regret"),
    )

    return {
        "route_valid": True,
        "distance": distance,
        "travel_time": travel_time,
        "true_cumulative_risk": (true_risk),
        "maximum_local_true_risk": (max_risk),
        "high_risk_cells_crossed": (high_risk_cells),
        "oracle_risk_regret": (oracle_risk_regret),
    }


def _city_winner_key(
    method_id: str,
    objective: float,
    metrics: Mapping[str, object],
) -> tuple[
    float,
    float,
    float,
    float,
    int,
]:
    return (
        round(
            objective,
            FLOAT_TIE_DIGITS,
        ),
        round(
            cast(
                float,
                metrics["true_cumulative_risk"],
            ),
            FLOAT_TIE_DIGITS,
        ),
        round(
            cast(
                float,
                metrics["travel_time"],
            ),
            FLOAT_TIE_DIGITS,
        ),
        round(
            cast(
                float,
                metrics["distance"],
            ),
            FLOAT_TIE_DIGITS,
        ),
        METHOD_ORDER[method_id],
    )


def _aggregate_method(
    method_id: str,
    cities: Sequence[CityEvaluation],
) -> OverallMethodEvaluation:
    routes = [
        next(route for route in city.methods if (route.method_id == method_id)) for city in cities
    ]

    city_count = len(routes)

    if city_count <= 0:
        raise ValueError("cannot aggregate zero cities")

    return OverallMethodEvaluation(
        method_id=method_id,
        city_wins=sum(route.city_winner for route in routes),
        mean_normalized_objective_regret=(
            sum(route.normalized_objective_regret for route in routes) / city_count
        ),
        mean_realized_objective=(sum(route.realized_objective for route in routes) / city_count),
        mean_true_cumulative_risk=(
            sum(route.true_cumulative_risk for route in routes) / city_count
        ),
        mean_oracle_risk_regret=(sum(route.oracle_risk_regret for route in routes) / city_count),
        mean_travel_time=(sum(route.travel_time for route in routes) / city_count),
        mean_distance=(sum(route.distance for route in routes) / city_count),
    )


def _overall_winner_key(
    summary: OverallMethodEvaluation,
) -> tuple[
    float,
    int,
    float,
    float,
    int,
]:
    return (
        round(
            summary.mean_normalized_objective_regret,
            FLOAT_TIE_DIGITS,
        ),
        -summary.city_wins,
        round(
            summary.mean_true_cumulative_risk,
            FLOAT_TIE_DIGITS,
        ),
        round(
            summary.mean_travel_time,
            FLOAT_TIE_DIGITS,
        ),
        METHOD_ORDER[summary.method_id],
    )


def _summary_payload(
    summary: EvaluationSummary,
    *,
    route_comparison_path: Path,
    overall_comparison_path: Path,
) -> dict[str, object]:
    cities = []

    for city in summary.cities:
        methods = {
            route.method_id: {
                key: value
                for key, value in asdict(route).items()
                if key
                not in {
                    "city_id",
                    "method_id",
                }
            }
            for route in city.methods
        }

        cities.append(
            {
                "city_id": city.city_id,
                "winner_method": (city.winner_method),
                "best_headline_realized_objective": (city.best_headline_realized_objective),
                "oracle": {
                    "role": ("true-risk benchmark only"),
                    "eligible_for_winner": False,
                    "true_cumulative_risk": (city.oracle_true_cumulative_risk),
                },
                "methods": methods,
            }
        )

    return {
        "schema_version": 1,
        "stage": "step7_evaluated",
        "headline_methods": list(HEADLINE_METHODS),
        "evaluation_objective": {
            "formula": ("travel_time + 4.0 * true_cumulative_risk"),
            "risk_weight": (REALIZED_RISK_WEIGHT),
        },
        "cross_city_normalization": {
            "metric": ("normalized_objective_regret"),
            "formula": (
                "(method_realized_objective - "
                "best_headline_realized_objective) "
                "/ best_headline_realized_objective"
            ),
            "reference": ("best headline method within city"),
        },
        "oracle": {
            "eligible_for_winner": False,
            "role": ("true-risk benchmark only"),
        },
        "city_winner_tie_break": [
            "realized_objective",
            "true_cumulative_risk",
            "travel_time",
            "distance",
            "method_order",
        ],
        "overall_winner_tie_break": [
            "mean_normalized_objective_regret",
            "city_wins_descending",
            "mean_true_cumulative_risk",
            "mean_travel_time",
            "method_order",
        ],
        "cities": cities,
        "overall": {
            "winner_method": (summary.overall_winner),
            "methods": [asdict(method) for method in summary.methods],
        },
        "comparison_tables": {
            "routes": (route_comparison_path.name),
            "overall": (overall_comparison_path.name),
        },
    }


def _write_route_comparison(
    summary: EvaluationSummary,
    path: Path,
) -> None:
    fieldnames = [
        "city_id",
        "method_id",
        "route_valid",
        "distance",
        "travel_time",
        "true_cumulative_risk",
        "maximum_local_true_risk",
        "high_risk_cells_crossed",
        "oracle_true_cumulative_risk",
        "oracle_risk_regret",
        "realized_objective",
        "best_headline_realized_objective",
        "normalized_objective_regret",
        "city_winner",
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for city in summary.cities:
            for route in city.methods:
                writer.writerow(asdict(route))


def _write_overall_comparison(
    summary: EvaluationSummary,
    path: Path,
) -> None:
    fieldnames = [
        "method_id",
        "city_wins",
        "mean_normalized_objective_regret",
        "mean_realized_objective",
        "mean_true_cumulative_risk",
        "mean_oracle_risk_regret",
        "mean_travel_time",
        "mean_distance",
        "overall_winner",
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for method in summary.methods:
            row = asdict(method)

            row["overall_winner"] = method.method_id == summary.overall_winner

            writer.writerow(row)


def _as_mapping(
    value: object,
    *,
    label: str,
) -> Mapping[str, object]:
    if not isinstance(
        value,
        dict,
    ):
        raise TypeError(f"{label} must be an object")

    return cast(
        Mapping[str, object],
        value,
    )


def _as_sequence(
    value: object,
    *,
    label: str,
) -> Sequence[object]:
    if not isinstance(
        value,
        list,
    ):
        raise TypeError(f"{label} must be a list")

    return cast(
        Sequence[object],
        value,
    )


def _as_string(
    value: object,
    *,
    label: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise TypeError(f"{label} must be a string")

    return value


def _as_nonnegative_float(
    value: object,
    *,
    label: str,
) -> float:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{label} must be numeric")

    result = float(value)

    _require_finite_nonnegative(
        label,
        result,
    )

    return result


def _as_nonnegative_int(
    value: object,
    *,
    label: str,
) -> int:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        int,
    ):
        raise TypeError(f"{label} must be an integer")

    if value < 0:
        raise ValueError(f"{label} must be nonnegative")

    return value


def _require_finite_nonnegative(
    label: str,
    value: float,
) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{label} must be finite and nonnegative")
