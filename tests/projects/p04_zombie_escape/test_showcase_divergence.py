"""Project-2 Step-3R showcase-divergence regression tests."""

from __future__ import annotations

import json
from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape.showcase_divergence import (
    BENCHMARK_SEED,
    CANDIDATE_SHOWCASE_SEEDS,
    COMMON_OBJECTIVE,
    DL_SEED,
    ESTIMATOR_CONTRACT,
    HEADLINE_METHODS,
    MAXIMUM_MEAN_EDGE_JACCARD,
    MAXIMUM_PAIR_EDGE_JACCARD,
    MINIMUM_MAXIMUM_ROUTE_SEPARATION,
    MINIMUM_UNIQUE_ROUTE_COUNT,
    MINIMUM_VISIBLY_DIVERGENT_PAIRS,
    ML_SEED,
    SHOWCASE_CITY_ORDER,
    TRAINING_SEED,
    VALIDATION_SEED,
    VISIBLE_PAIR_MAX_EDGE_JACCARD,
    corridor_count,
    evaluate_showcase_divergence,
    has_observable_estimator_ambiguity,
    search_contract_payload,
)
from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    load_visual_payloads,
)


def _routes() -> dict[str, object]:
    _, _, routes, _ = load_visual_payloads(Path("tests/fixtures/p04_zombie_escape/data"))

    return routes


def test_headline_method_contract() -> None:
    assert HEADLINE_METHODS == (
        "dijkstra",
        "ml",
        "dl",
    )

    assert COMMON_OBJECTIVE == ("travel_time + 4.0 * estimated_zombie_risk")


def test_estimators_are_distinct() -> None:
    assert set(ESTIMATOR_CONTRACT) == set(HEADLINE_METHODS)

    assert len(set(ESTIMATOR_CONTRACT.values())) == 3


def test_acceptance_thresholds_are_frozen() -> None:
    assert MINIMUM_UNIQUE_ROUTE_COUNT == 3

    assert MINIMUM_VISIBLY_DIVERGENT_PAIRS == 2

    assert VISIBLE_PAIR_MAX_EDGE_JACCARD == 0.85

    assert MAXIMUM_MEAN_EDGE_JACCARD == 0.88

    assert MAXIMUM_PAIR_EDGE_JACCARD == 0.97

    assert MINIMUM_MAXIMUM_ROUTE_SEPARATION == 3


def test_candidate_order_is_frozen() -> None:
    assert len(CANDIDATE_SHOWCASE_SEEDS) == 24

    assert CANDIDATE_SHOWCASE_SEEDS[0] == (
        5201,
        5301,
        5401,
    )


def test_candidate_seeds_do_not_overlap_immutable_seeds() -> None:
    immutable = {
        TRAINING_SEED,
        VALIDATION_SEED,
        BENCHMARK_SEED,
        ML_SEED,
        DL_SEED,
    }

    candidates = {seed for triple in (CANDIDATE_SHOWCASE_SEEDS) for seed in triple}

    assert not (immutable & candidates)


def test_search_contract_is_first_acceptable() -> None:
    contract = search_contract_payload()

    assert contract["selection_policy"] == "first_acceptable_candidate"

    assert contract["candidate_order_is_frozen"] is True

    assert contract["showcase_is_not_benchmark"] is True


def test_current_frozen_showcase_is_accepted() -> None:
    summary = evaluate_showcase_divergence(_routes())

    assert summary.accepted

    assert summary.accepted_city_count == len(SHOWCASE_CITY_ORDER)


def test_every_showcase_city_has_three_corridors() -> None:
    summary = evaluate_showcase_divergence(_routes())

    for city in summary.cities:
        assert corridor_count(city) == 3


def test_every_showcase_city_has_estimator_ambiguity() -> None:
    summary = evaluate_showcase_divergence(_routes())

    for city in summary.cities:
        assert has_observable_estimator_ambiguity(city)


def test_manifest_exists_and_is_accepted() -> None:
    path = Path("configs/p04_zombie_escape_showcase_contract.json")

    assert path.is_file()

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["selection_policy"] == "first_acceptable_candidate"

    assert payload["accepted_divergence"]["accepted"] is True


def test_manifest_preserves_immutable_seeds() -> None:
    payload = json.loads(
        Path("configs/p04_zombie_escape_showcase_contract.json").read_text(encoding="utf-8")
    )

    seeds = payload["immutable_seeds"]

    assert seeds["training"] == TRAINING_SEED

    assert seeds["validation"] == VALIDATION_SEED

    assert seeds["benchmark"] == BENCHMARK_SEED

    assert seeds["ml"] == ML_SEED

    assert seeds["dl"] == DL_SEED
