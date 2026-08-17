"""Tests for deterministic Bayesian Dice simulation."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    DiceModelError,
    DiceSimulationError,
    ProbabilityVector,
    count_faces,
    cumulative_roll_records,
    generate_fair_rolls,
    generate_loaded_rolls,
    generate_rolls,
    load_dice_config,
    simulate_scenario,
    simulation_required_fields,
    summarize_simulation,
    validate_rolls,
    validate_simulation_payload,
    write_roll_history_csv,
    write_simulation_json,
)


def test_fair_probability_vector_sums_to_one() -> None:
    probabilities = ProbabilityVector.from_sequence([1.0 / 6.0] * 6)

    assert sum(probabilities.values) == pytest.approx(
        1.0,
        abs=1.0e-12,
    )


@pytest.mark.parametrize(
    "values",
    [
        [0.20] * 6,
        [0.10] * 5,
        [0.20, 0.20, 0.20, 0.20, 0.30, -0.10],
        [0.20, 0.20, 0.20, 0.20, 0.20, float("nan")],
    ],
)
def test_invalid_probability_vectors_are_rejected(
    values: list[float],
) -> None:
    with pytest.raises(DiceModelError):
        ProbabilityVector.from_sequence(values)


def test_same_seed_produces_same_rolls() -> None:
    probabilities = ProbabilityVector.from_sequence([0.12, 0.12, 0.12, 0.12, 0.12, 0.40])

    first = generate_rolls(
        probabilities,
        roll_count=180,
        seed=1,
    )

    second = generate_rolls(
        probabilities,
        roll_count=180,
        seed=1,
    )

    assert first == second


def test_different_seeds_produce_different_rolls() -> None:
    probabilities = ProbabilityVector.from_sequence([0.12, 0.12, 0.12, 0.12, 0.12, 0.40])

    first = generate_rolls(
        probabilities,
        roll_count=180,
        seed=1,
    )

    second = generate_rolls(
        probabilities,
        roll_count=180,
        seed=2,
    )

    assert first != second


def test_generated_faces_are_between_one_and_six() -> None:
    rolls = generate_fair_rolls(
        roll_count=1_000,
        seed=101,
    )

    assert len(rolls) == 1_000
    assert min(rolls) >= 1
    assert max(rolls) <= 6


def test_loaded_generator_rejects_uniform_vector() -> None:
    fair = ProbabilityVector.from_sequence([1.0 / 6.0] * 6)

    with pytest.raises(
        DiceSimulationError,
        match="non-uniform",
    ):
        generate_loaded_rolls(
            fair,
            roll_count=100,
            seed=1,
        )


def test_loaded_generator_accepts_loaded_vector() -> None:
    loaded = ProbabilityVector.from_sequence([0.15, 0.15, 0.15, 0.15, 0.15, 0.25])

    rolls = generate_loaded_rolls(
        loaded,
        roll_count=180,
        seed=202,
    )

    assert len(rolls) == 180


def test_counts_match_generated_rolls() -> None:
    config = load_dice_config()

    result = simulate_scenario(
        config,
        "clearly_loaded",
    )

    assert count_faces(result.rolls) == result.final_counts

    assert sum(result.final_counts) == result.roll_count


def test_cumulative_counts_track_roll_sequence() -> None:
    rolls = (
        1,
        6,
        6,
        2,
    )

    records = cumulative_roll_records(rolls)

    assert [record.cumulative_counts for record in records] == [
        (1, 0, 0, 0, 0, 0),
        (1, 0, 0, 0, 0, 1),
        (1, 0, 0, 0, 0, 2),
        (1, 1, 0, 0, 0, 2),
    ]

    assert records[-1].roll_index == 4


def test_validate_rolls_rejects_invalid_face() -> None:
    with pytest.raises(
        DiceSimulationError,
        match="1 through 6",
    ):
        validate_rolls([1, 2, 7])


def test_default_simulation_uses_showcase_scenario() -> None:
    config = load_dice_config()

    result = simulate_scenario(config)

    assert result.scenario_id == config.showcase_scenario

    assert result.scenario_id == "clearly_loaded"
    assert result.seed == 1
    assert result.roll_count == 180


@pytest.mark.parametrize(
    "scenario_id",
    [
        "fair",
        "mildly_loaded",
        "clearly_loaded",
    ],
)
def test_every_configured_scenario_simulates(
    scenario_id: str,
) -> None:
    config = load_dice_config()

    result = simulate_scenario(
        config,
        scenario_id,
    )

    assert result.scenario_id == scenario_id
    assert len(result.rolls) == 180
    assert sum(result.final_counts) == 180


def test_simulation_summary_is_internally_consistent() -> None:
    config = load_dice_config()

    result = simulate_scenario(
        config,
        "fair",
    )

    summary = summarize_simulation(result)

    face_counts = summary["face_counts"]

    assert isinstance(
        face_counts,
        dict,
    )

    assert sum(int(value) for value in face_counts.values()) == 180

    empirical = summary["empirical_probabilities"]

    assert isinstance(
        empirical,
        list,
    )

    assert sum(float(value) for value in empirical) == pytest.approx(
        1.0,
        abs=1.0e-12,
    )


def test_simulation_json_serialization(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    result = simulate_scenario(
        config,
        "clearly_loaded",
    )

    output = tmp_path / "simulation.json"

    write_simulation_json(
        result,
        output,
    )

    payload = json.loads(
        output.read_text(
            encoding="utf-8",
        )
    )

    validate_simulation_payload(payload)

    for field in simulation_required_fields():
        assert field in payload

    assert payload["project_id"] == "p01_bayesian_dice"
    assert payload["scenario_id"] == "clearly_loaded"
    assert payload["seed"] == 1
    assert payload["roll_count"] == 180
    assert len(payload["rolls"]) == 180


def test_simulation_json_is_deterministic(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    result = simulate_scenario(
        config,
        "clearly_loaded",
    )

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_simulation_json(
        result,
        first,
    )

    write_simulation_json(
        result,
        second,
    )

    assert first.read_bytes() == second.read_bytes()


def test_roll_history_csv_serialization(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    result = simulate_scenario(
        config,
        "mildly_loaded",
    )

    output = tmp_path / "rolls.csv"

    write_roll_history_csv(
        result,
        output,
    )

    with output.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 180

    assert rows[0]["roll_index"] == "1"
    assert rows[-1]["roll_index"] == "180"

    final_count_total = sum(int(rows[-1][f"count_{face}"]) for face in range(1, 7))

    assert final_count_total == 180
