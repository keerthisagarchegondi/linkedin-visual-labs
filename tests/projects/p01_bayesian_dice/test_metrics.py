"""Tests for deterministic Bayesian Dice calibration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    load_dice_config,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.metrics import (
    CalibrationObservation,
    DiceCalibrationError,
    build_posterior_calibration_buckets,
    calibration_seed,
    evaluate_acceptance,
    evaluate_calibration_observation,
    load_calibration_acceptance_targets,
    run_calibration,
    summarize_scenario_observations,
    write_validation_json,
)


def test_calibration_seed_is_deterministic() -> None:
    config = load_dice_config()

    first = calibration_seed(
        config,
        "fair",
        0,
    )

    second = calibration_seed(
        config,
        "fair",
        0,
    )

    assert first == second


def test_calibration_seed_changes_by_repetition() -> None:
    config = load_dice_config()

    first = calibration_seed(
        config,
        "fair",
        0,
    )

    second = calibration_seed(
        config,
        "fair",
        1,
    )

    assert first != second


def test_calibration_seed_changes_by_scenario() -> None:
    config = load_dice_config()

    fair = calibration_seed(
        config,
        "fair",
        0,
    )

    loaded = calibration_seed(
        config,
        "clearly_loaded",
        0,
    )

    assert fair != loaded


def test_negative_repetition_index_is_rejected() -> None:
    config = load_dice_config()

    with pytest.raises(
        DiceCalibrationError,
        match="non-negative",
    ):
        calibration_seed(
            config,
            "fair",
            -1,
        )


def test_single_calibration_observation_is_reproducible() -> None:
    config = load_dice_config()

    first = evaluate_calibration_observation(
        config,
        "clearly_loaded",
        3,
    )

    second = evaluate_calibration_observation(
        config,
        "clearly_loaded",
        3,
    )

    assert first == second


def test_scenario_summary_calculates_rates() -> None:
    observations = (
        CalibrationObservation(
            scenario_id="fair",
            repetition_index=0,
            seed=1,
            truth_loaded=False,
            detected_loaded=True,
            detection_roll=10,
            final_posterior_loaded=0.20,
        ),
        CalibrationObservation(
            scenario_id="fair",
            repetition_index=1,
            seed=2,
            truth_loaded=False,
            detected_loaded=False,
            detection_roll=None,
            final_posterior_loaded=0.01,
        ),
    )

    metrics = summarize_scenario_observations(
        "fair",
        observations,
    )

    assert metrics.repetitions == 2
    assert metrics.detection_count == 1
    assert metrics.detection_rate == pytest.approx(0.5)
    assert metrics.miss_rate == pytest.approx(0.5)
    assert metrics.average_detection_roll == pytest.approx(10.0)


def test_posterior_calibration_buckets_cover_all_observations() -> None:
    observations = (
        CalibrationObservation(
            scenario_id="fair",
            repetition_index=0,
            seed=1,
            truth_loaded=False,
            detected_loaded=False,
            detection_roll=None,
            final_posterior_loaded=0.05,
        ),
        CalibrationObservation(
            scenario_id="clearly_loaded",
            repetition_index=0,
            seed=2,
            truth_loaded=True,
            detected_loaded=True,
            detection_roll=10,
            final_posterior_loaded=0.95,
        ),
        CalibrationObservation(
            scenario_id="mildly_loaded",
            repetition_index=0,
            seed=3,
            truth_loaded=True,
            detected_loaded=False,
            detection_roll=None,
            final_posterior_loaded=1.0,
        ),
    )

    buckets = build_posterior_calibration_buckets(
        observations,
        bucket_count=10,
    )

    assert len(buckets) == 10

    assert sum(bucket.observation_count for bucket in buckets) == 3

    assert buckets[0].observation_count == 1
    assert buckets[9].observation_count == 2


def test_acceptance_targets_load_from_yaml() -> None:
    config = load_dice_config()

    targets = load_calibration_acceptance_targets(config)

    assert targets.maximum_false_positive_rate == pytest.approx(0.05)

    assert targets.minimum_clearly_loaded_true_positive_rate == pytest.approx(0.95)

    assert targets.maximum_clearly_loaded_miss_rate == pytest.approx(0.05)

    assert targets.maximum_clearly_loaded_average_detection_roll == pytest.approx(90.0)


def test_acceptance_evaluation_is_machine_readable() -> None:
    config = load_dice_config()

    targets = load_calibration_acceptance_targets(config)

    checks = evaluate_acceptance(
        false_positive_rate=0.04,
        clearly_loaded_true_positive_rate=0.98,
        clearly_loaded_miss_rate=0.02,
        clearly_loaded_average_detection_roll=42.0,
        targets=targets,
    )

    assert checks == {
        "false_positive_rate": True,
        "clearly_loaded_true_positive_rate": True,
        "clearly_loaded_miss_rate": True,
        "clearly_loaded_average_detection_roll": True,
    }


def test_small_calibration_is_deterministic() -> None:
    config = load_dice_config()

    first = run_calibration(
        config,
        repetitions_per_scenario=10,
        include_prior_sensitivity=False,
    )

    second = run_calibration(
        config,
        repetitions_per_scenario=10,
        include_prior_sensitivity=False,
    )

    assert first.as_dict() == second.as_dict()


def test_small_calibration_has_all_scenarios() -> None:
    config = load_dice_config()

    report = run_calibration(
        config,
        repetitions_per_scenario=10,
        include_prior_sensitivity=False,
    )

    assert set(report.scenario_metrics) == {
        "fair",
        "mildly_loaded",
        "clearly_loaded",
    }

    assert len(report.posterior_calibration_buckets) == 10


def test_prior_sensitivity_contains_configured_priors() -> None:
    config = load_dice_config()

    report = run_calibration(
        config,
        repetitions_per_scenario=5,
        include_prior_sensitivity=True,
    )

    actual = [entry["prior_loaded_probability"] for entry in report.prior_sensitivity]

    assert actual == list(config.calibration.prior_sensitivity)


def test_validation_json_is_machine_readable(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    report = run_calibration(
        config,
        repetitions_per_scenario=5,
        include_prior_sensitivity=False,
    )

    output = tmp_path / "validation.json"

    write_validation_json(
        report,
        output,
    )

    payload = json.loads(
        output.read_text(
            encoding="utf-8",
        )
    )

    required = {
        "project_id",
        "repetitions_per_scenario",
        "false_positive_rate",
        "clearly_loaded_true_positive_rate",
        "clearly_loaded_miss_rate",
        "clearly_loaded_average_detection_roll",
        "mildly_loaded_detection_rate",
        "posterior_calibration_buckets",
        "prior_sensitivity",
        "acceptance_checks",
        "acceptance_passed",
    }

    assert required <= payload.keys()
