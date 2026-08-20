"""Tests for deterministic pair-of-dice simulation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    PAIR_CASE_IDS,
    PairDiceSimulationError,
    count_pair_sums,
    cumulative_pair_sum_records,
    generate_pair_rolls,
    load_dice_config,
    simulate_all_pair_cases,
    simulate_pair_case,
    validate_pair_simulation_payload,
    validate_pair_sums,
    write_pair_simulation_json,
)


def test_pair_roll_generation_is_deterministic() -> None:
    config = load_dice_config()
    pair = config.pair_experiment

    case = pair.pair_case("UF")

    first_die = pair.die_type(case.die_1_type)

    second_die = pair.die_type(case.die_2_type)

    first = generate_pair_rolls(
        first_die.probabilities,
        second_die.probabilities,
        roll_count=100,
        seed=case.seed,
    )

    second = generate_pair_rolls(
        first_die.probabilities,
        second_die.probabilities,
        roll_count=100,
        seed=case.seed,
    )

    assert first == second


def test_pair_roll_generation_changes_with_seed() -> None:
    config = load_dice_config()
    pair = config.pair_experiment

    first_die = pair.die_type("unloaded")

    second_die = pair.die_type("fully_loaded")

    first = generate_pair_rolls(
        first_die.probabilities,
        second_die.probabilities,
        roll_count=500,
        seed=100,
    )

    second = generate_pair_rolls(
        first_die.probabilities,
        second_die.probabilities,
        roll_count=500,
        seed=101,
    )

    assert first != second


def test_pair_rolls_retain_physical_faces_and_correct_sum() -> None:
    config = load_dice_config()
    pair = config.pair_experiment

    die = pair.die_type("unloaded")

    rolls = generate_pair_rolls(
        die.probabilities,
        die.probabilities,
        roll_count=1_000,
        seed=1101,
    )

    assert len(rolls) == 1_000

    for roll in rolls:
        assert 1 <= roll.die_1_face <= 6
        assert 1 <= roll.die_2_face <= 6

        assert roll.observed_sum == (roll.die_1_face + roll.die_2_face)

        assert 2 <= roll.observed_sum <= 12


@pytest.mark.parametrize(
    "case_id",
    PAIR_CASE_IDS,
)
def test_every_canonical_pair_case_has_10000_rolls(
    case_id: str,
) -> None:
    config = load_dice_config()

    result = simulate_pair_case(
        config.pair_experiment,
        case_id,
    )

    assert result.case_id == case_id
    assert result.roll_count == 10_000

    assert len(result.die_1_rolls) == 10_000

    assert len(result.die_2_rolls) == 10_000

    assert len(result.sums) == 10_000

    assert sum(result.final_sum_counts) == 10_000


def test_all_pair_cases_have_60000_total_observations() -> None:
    config = load_dice_config()

    result = simulate_all_pair_cases(config)

    assert set(result.cases) == set(PAIR_CASE_IDS)

    assert result.total_observation_count == 60_000


def test_all_pair_case_sequences_are_deterministic() -> None:
    config = load_dice_config()

    first = simulate_all_pair_cases(config)

    second = simulate_all_pair_cases(config)

    for case_id in PAIR_CASE_IDS:
        assert first.case(case_id) == second.case(case_id)


def test_canonical_case_sequences_are_distinct() -> None:
    config = load_dice_config()

    result = simulate_all_pair_cases(config)

    sequences = {result.case(case_id).sums for case_id in PAIR_CASE_IDS}

    assert len(sequences) == 6


def test_pair_sum_counts_match_sequence() -> None:
    config = load_dice_config()

    result = simulate_pair_case(
        config.pair_experiment,
        "PF",
    )

    assert count_pair_sums(result.sums) == result.final_sum_counts


def test_cumulative_pair_sum_records_are_consistent() -> None:
    sums = (
        7,
        12,
        7,
        2,
    )

    records = cumulative_pair_sum_records(sums)

    assert len(records) == 4

    assert records[-1].cumulative_sum_counts == (
        1,
        0,
        0,
        0,
        0,
        2,
        0,
        0,
        0,
        0,
        1,
    )

    for record in records:
        assert sum(record.cumulative_sum_counts) == record.roll_index


@pytest.mark.parametrize(
    "values",
    [
        [1, 7, 8],
        [2, 7, 13],
        [2, True, 7],
        [2, 7, 8.0],
    ],
)
def test_invalid_pair_sums_are_rejected(
    values: list[object],
) -> None:
    with pytest.raises(
        PairDiceSimulationError,
    ):
        validate_pair_sums(values)


def test_pair_simulation_json_serialization(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    result = simulate_all_pair_cases(config)

    output = tmp_path / "pair_simulation.json"

    write_pair_simulation_json(
        result,
        output,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))

    validate_pair_simulation_payload(payload)

    assert payload["project_id"] == "p01_bayesian_dice"

    assert payload["roll_count_per_case"] == 10_000

    assert payload["total_observation_count"] == 60_000

    assert set(payload["cases"]) == set(PAIR_CASE_IDS)


def test_pair_simulation_json_is_deterministic(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    result = simulate_all_pair_cases(config)

    first = tmp_path / "first.json"

    second = tmp_path / "second.json"

    write_pair_simulation_json(
        result,
        first,
    )

    write_pair_simulation_json(
        result,
        second,
    )

    assert first.read_bytes() == second.read_bytes()
