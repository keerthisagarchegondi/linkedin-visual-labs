"""Exact Step 7 evaluation and winner-rule tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p04_zombie_escape.evaluation import (
    HEADLINE_METHODS,
    REALIZED_RISK_WEIGHT,
    evaluate_routes_payload,
    normalized_objective_regret,
    realized_objective,
    write_evaluation_artifacts,
)


def _route(
    *,
    travel_time: float,
    risk: float,
    oracle_risk: float,
    distance: float = 20.0,
    max_risk: float = 0.5,
    high_risk_cells: int = 0,
) -> dict[str, object]:
    return {
        "route_valid": True,
        "start": {
            "row": 0,
            "column": 0,
        },
        "destination": {
            "row": 1,
            "column": 1,
        },
        "path": [
            {
                "row": 0,
                "column": 0,
            },
            {
                "row": 1,
                "column": 1,
            },
        ],
        "metrics": {
            "distance": distance,
            "travel_time": travel_time,
            "true_cumulative_risk": risk,
            "maximum_local_true_risk": max_risk,
            "high_risk_cells_crossed": high_risk_cells,
            "oracle_risk_regret": max(
                0.0,
                risk - oracle_risk,
            ),
        },
    }


def _city(
    city_id: str,
    *,
    oracle_risk: float,
    dijkstra: dict[str, object],
    ml: dict[str, object],
    dl: dict[str, object],
) -> dict[str, object]:
    return {
        "city_id": city_id,
        "methods": {
            "dijkstra": dijkstra,
            "ml": ml,
            "dl": dl,
        },
        "oracle": {
            "path": [
                {
                    "row": 0,
                    "column": 0,
                },
                {
                    "row": 1,
                    "column": 1,
                },
            ],
            "true_cumulative_risk": oracle_risk,
        },
    }


def _payload(
    cities: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "stage": "step6_complete",
        "headline_methods_complete": True,
        "available_headline_methods": [
            "dijkstra",
            "ml",
            "dl",
        ],
        "pending_headline_methods": [],
        "cities": cities,
    }


def test_realized_objective_uses_frozen_risk_weight() -> None:
    assert REALIZED_RISK_WEIGHT == 4.0

    assert realized_objective(
        travel_time=10.0,
        true_cumulative_risk=2.0,
    ) == pytest.approx(18.0)


def test_normalized_regret_is_relative_to_best_headline() -> None:
    assert normalized_objective_regret(
        method_objective=12.0,
        best_headline_objective=10.0,
    ) == pytest.approx(0.2)

    assert normalized_objective_regret(
        method_objective=10.0,
        best_headline_objective=10.0,
    ) == pytest.approx(0.0)


def test_city_winner_uses_lowest_realized_objective() -> None:
    oracle_risk = 0.5

    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=8.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=9.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    assert summary.cities[0].winner_method == "ml"


def test_city_objective_tie_prefers_lower_true_risk() -> None:
    oracle_risk = 0.5

    # dijkstra = 10 + 4*1 = 14
    # ml       =  6 + 4*2 = 14
    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=6.0,
            risk=2.0,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=12.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    assert summary.cities[0].winner_method == "dijkstra"


def test_city_full_metric_tie_prefers_shorter_distance() -> None:
    oracle_risk = 0.5

    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=10.0,
            risk=1.0,
            distance=25.0,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=10.0,
            risk=1.0,
            distance=20.0,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=12.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    assert summary.cities[0].winner_method == "ml"


def test_city_exact_tie_uses_frozen_method_order() -> None:
    oracle_risk = 0.5

    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    assert HEADLINE_METHODS == (
        "dijkstra",
        "ml",
        "dl",
    )

    assert summary.cities[0].winner_method == "dijkstra"


def test_oracle_is_never_winner_eligible() -> None:
    oracle_risk = 0.1

    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=12.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=11.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    assert summary.overall_winner in {
        "dijkstra",
        "ml",
        "dl",
    }

    assert summary.overall_winner != "oracle"


def test_oracle_risk_regret_is_nonnegative_excess_risk() -> None:
    oracle_risk = 2.0

    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=10.0,
            risk=1.5,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=10.0,
            risk=2.5,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=10.0,
            risk=2.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    routes = {route.method_id: route for route in summary.cities[0].methods}

    assert routes["dijkstra"].oracle_risk_regret == pytest.approx(0.0)

    assert routes["ml"].oracle_risk_regret == pytest.approx(0.5)

    assert routes["dl"].oracle_risk_regret == pytest.approx(0.0)


def test_overall_winner_uses_mean_normalized_regret() -> None:
    cities = []

    for index, base in enumerate(
        (
            10.0,
            20.0,
            30.0,
        ),
        start=1,
    ):
        oracle_risk = 0.0

        cities.append(
            _city(
                f"city_{index}",
                oracle_risk=oracle_risk,
                dijkstra=_route(
                    travel_time=base * 1.20,
                    risk=0.0,
                    oracle_risk=oracle_risk,
                ),
                ml=_route(
                    travel_time=base * 1.10,
                    risk=0.0,
                    oracle_risk=oracle_risk,
                ),
                dl=_route(
                    travel_time=base * 1.05,
                    risk=0.0,
                    oracle_risk=oracle_risk,
                ),
            )
        )

    summary = evaluate_routes_payload(_payload(cities))

    assert summary.overall_winner == "dl"

    dl_summary = next(method for method in summary.methods if method.method_id == "dl")

    assert dl_summary.city_wins == 3

    assert dl_summary.mean_normalized_objective_regret == pytest.approx(0.0)


def test_writer_creates_machine_readable_outputs(
    tmp_path: Path,
) -> None:
    oracle_risk = 0.5

    city = _city(
        "city_a",
        oracle_risk=oracle_risk,
        dijkstra=_route(
            travel_time=12.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        ml=_route(
            travel_time=11.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
        dl=_route(
            travel_time=10.0,
            risk=1.0,
            oracle_risk=oracle_risk,
        ),
    )

    summary = evaluate_routes_payload(_payload([city]))

    artifacts = write_evaluation_artifacts(
        summary,
        data_directory=tmp_path,
    )

    assert artifacts.summary_path.is_file()
    assert artifacts.route_comparison_path.is_file()
    assert artifacts.overall_comparison_path.is_file()

    payload = json.loads(artifacts.summary_path.read_text(encoding="utf-8"))

    assert payload["stage"] == "step7_evaluated"

    assert payload["oracle"]["eligible_for_winner"] is False

    assert payload["cross_city_normalization"]["reference"] == "best headline method within city"

    with artifacts.route_comparison_path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        route_rows = list(csv.DictReader(handle))

    with artifacts.overall_comparison_path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        overall_rows = list(csv.DictReader(handle))

    assert len(route_rows) == 3
    assert len(overall_rows) == 3
