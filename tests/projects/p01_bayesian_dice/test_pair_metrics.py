"""Tests for canonical pair experiment metrics and validation outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import cast

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    PAIR_CASE_IDS,
    PAIR_HISTORY_COLUMNS,
    DecisionState,
    DiceProjectConfig,
    PairInferenceResult,
    PairSimulationResult,
    build_pair_case_summaries,
    build_pair_validation_report,
    infer_all_pair_cases,
    load_dice_config,
    pair_summary_payload,
    simulate_all_pair_cases,
    write_pair_case_histories_csv,
    write_pair_case_summary_json,
    write_pair_validation_json,
)

type CanonicalExperiment = tuple[
    DiceProjectConfig,
    PairSimulationResult,
    PairInferenceResult,
]


@pytest.fixture(scope="module")
def canonical_experiment() -> CanonicalExperiment:
    """Return the deterministic six-case canonical experiment."""
    config = load_dice_config()

    simulation = simulate_all_pair_cases(config)

    inference = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    return (
        config,
        simulation,
        inference,
    )


def test_pair_case_summaries_cover_all_six_cases(
    canonical_experiment: CanonicalExperiment,
) -> None:
    _, simulation, inference = canonical_experiment

    summaries = build_pair_case_summaries(
        simulation,
        inference,
    )

    assert tuple(summaries) == PAIR_CASE_IDS


def test_pair_case_summaries_use_stable_decision_roll(
    canonical_experiment: CanonicalExperiment,
) -> None:
    _, simulation, inference = canonical_experiment

    summaries = build_pair_case_summaries(
        simulation,
        inference,
    )

    for case_id in PAIR_CASE_IDS:
        summary = summaries[case_id]

        result = inference.case(case_id)

        assert summary.stable_decision_roll == result.stable_decision_roll

        assert summary.stable_decision_state is result.stable_decision_state


def test_summary_truth_states_are_correct(
    canonical_experiment: CanonicalExperiment,
) -> None:
    _, simulation, inference = canonical_experiment

    summaries = build_pair_case_summaries(
        simulation,
        inference,
    )

    assert summaries["UU"].expected_final_state is DecisionState.FAIR

    for case_id in (
        "UP",
        "UF",
        "PP",
        "PF",
        "FF",
    ):
        assert summaries[case_id].expected_final_state is DecisionState.LOADED


def test_summary_payload_has_authoritative_contract(
    canonical_experiment: CanonicalExperiment,
) -> None:
    config, simulation, inference = canonical_experiment

    payload = pair_summary_payload(
        config,
        simulation,
        inference,
    )

    assert payload["roll_count_per_case"] == 10_000

    assert payload["total_observation_count"] == 60_000

    assert payload["headline_roll_metric"] == "stable_decision_roll"

    assert payload["loaded_probability_definition"] == "1 - posterior(M_UU)"

    raw_case_order = payload["case_order"]

    assert isinstance(
        raw_case_order,
        list,
    )

    case_order = cast(
        list[str],
        raw_case_order,
    )

    assert tuple(case_order) == PAIR_CASE_IDS


def test_validation_report_passes_canonical_experiment(
    canonical_experiment: CanonicalExperiment,
) -> None:
    config, simulation, inference = canonical_experiment

    report = build_pair_validation_report(
        config,
        simulation,
        inference,
    )

    assert report.passed is True

    assert report.total_observation_count == 60_000

    assert report.headline_roll_metric == "stable_decision_roll"

    assert all(check.passed for check in report.checks)


@pytest.mark.parametrize(
    "case_id",
    PAIR_CASE_IDS,
)
def test_validation_contains_case_specific_stable_checks(
    canonical_experiment: CanonicalExperiment,
    case_id: str,
) -> None:
    config, simulation, inference = canonical_experiment

    report = build_pair_validation_report(
        config,
        simulation,
        inference,
    )

    checks = {check.check_id: check for check in report.checks}

    assert checks[f"case.{case_id}.stable_decision_exists"].passed

    assert checks[f"case.{case_id}.stable_suffix"].passed

    assert checks[f"case.{case_id}.stable_roll_earliest"].passed


def test_history_csv_contains_exactly_60000_rows(
    canonical_experiment: CanonicalExperiment,
    tmp_path: Path,
) -> None:
    _, _, inference = canonical_experiment

    path = tmp_path / "pair_case_histories.csv"

    write_pair_case_histories_csv(
        inference,
        path,
    )

    with path.open(
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        fieldnames = tuple(reader.fieldnames or ())

        rows = list(reader)

    assert fieldnames == PAIR_HISTORY_COLUMNS

    assert len(rows) == 60_000

    assert rows[0]["case_id"] == "UU"

    assert rows[-1]["case_id"] == "FF"

    assert rows[0]["roll_index"] == "1"

    assert rows[-1]["roll_index"] == "10000"


def test_summary_json_is_deterministic(
    canonical_experiment: CanonicalExperiment,
    tmp_path: Path,
) -> None:
    config, simulation, inference = canonical_experiment

    first = tmp_path / "summary_first.json"

    second = tmp_path / "summary_second.json"

    write_pair_case_summary_json(
        config,
        simulation,
        inference,
        first,
    )

    write_pair_case_summary_json(
        config,
        simulation,
        inference,
        second,
    )

    assert first.read_bytes() == second.read_bytes()


def test_validation_json_is_deterministic(
    canonical_experiment: CanonicalExperiment,
    tmp_path: Path,
) -> None:
    config, simulation, inference = canonical_experiment

    report = build_pair_validation_report(
        config,
        simulation,
        inference,
    )

    first = tmp_path / "validation_first.json"

    second = tmp_path / "validation_second.json"

    write_pair_validation_json(
        report,
        first,
    )

    write_pair_validation_json(
        report,
        second,
    )

    assert first.read_bytes() == second.read_bytes()


def test_validation_json_contains_no_failed_checks(
    canonical_experiment: CanonicalExperiment,
    tmp_path: Path,
) -> None:
    config, simulation, inference = canonical_experiment

    report = build_pair_validation_report(
        config,
        simulation,
        inference,
    )

    path = tmp_path / "pair_validation.json"

    write_pair_validation_json(
        report,
        path,
    )

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert isinstance(
        payload,
        dict,
    )

    assert payload["passed"] is True

    assert payload["failed_check_ids"] == []
