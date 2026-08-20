"""Tests for Bayesian Dice model comparison."""

from __future__ import annotations

import csv
import math
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    DecisionState,
    load_dice_config,
    simulate_scenario,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.inference import (
    DiceInferenceError,
    log_marginal_likelihood_h0,
    log_marginal_likelihood_h1,
    posterior_loaded_probability,
    posterior_predictive_probabilities,
    sequential_inference,
    write_posterior_history_csv,
)


def test_h0_empty_counts_have_log_likelihood_zero() -> None:
    config = load_dice_config()

    result = log_marginal_likelihood_h0(
        [0, 0, 0, 0, 0, 0],
        config.model.fair_probabilities.values,
    )

    assert result == pytest.approx(0.0)


def test_h1_empty_counts_have_log_likelihood_zero() -> None:
    config = load_dice_config()

    result = log_marginal_likelihood_h1(
        [0, 0, 0, 0, 0, 0],
        config.model.dirichlet_alpha,
    )

    assert result == pytest.approx(
        0.0,
        abs=1.0e-12,
    )


def test_h0_single_roll_matches_log_one_sixth() -> None:
    config = load_dice_config()

    result = log_marginal_likelihood_h0(
        [1, 0, 0, 0, 0, 0],
        config.model.fair_probabilities.values,
    )

    assert result == pytest.approx(
        math.log(1.0 / 6.0),
        abs=1.0e-12,
    )


def test_h1_single_roll_matches_one_sixth_under_symmetric_prior() -> None:
    config = load_dice_config()

    result = log_marginal_likelihood_h1(
        [1, 0, 0, 0, 0, 0],
        config.model.dirichlet_alpha,
    )

    assert result == pytest.approx(
        math.log(1.0 / 6.0),
        abs=1.0e-12,
    )


def test_known_two_roll_repeat_case_matches_closed_form() -> None:
    config = load_dice_config()

    counts = [2, 0, 0, 0, 0, 0]

    log_h0 = log_marginal_likelihood_h0(
        counts,
        config.model.fair_probabilities.values,
    )

    log_h1 = log_marginal_likelihood_h1(
        counts,
        config.model.dirichlet_alpha,
    )

    expected_h0 = math.log(1.0 / 36.0)

    expected_h1 = math.log(1.0 / 21.0)

    assert log_h0 == pytest.approx(
        expected_h0,
        abs=1.0e-12,
    )

    assert log_h1 == pytest.approx(
        expected_h1,
        abs=1.0e-12,
    )


def test_known_two_distinct_roll_case_matches_closed_form() -> None:
    config = load_dice_config()

    counts = [1, 1, 0, 0, 0, 0]

    log_h0 = log_marginal_likelihood_h0(
        counts,
        config.model.fair_probabilities.values,
    )

    log_h1 = log_marginal_likelihood_h1(
        counts,
        config.model.dirichlet_alpha,
    )

    expected_h0 = math.log(1.0 / 36.0)

    expected_h1 = math.log(1.0 / 42.0)

    assert log_h0 == pytest.approx(
        expected_h0,
        abs=1.0e-12,
    )

    assert log_h1 == pytest.approx(
        expected_h1,
        abs=1.0e-12,
    )


def test_prior_only_posterior_equals_prior() -> None:
    posterior = posterior_loaded_probability(
        log_marginal_h0=0.0,
        log_marginal_h1=0.0,
        prior_loaded_probability=0.5,
    )

    assert posterior == pytest.approx(
        0.5,
        abs=1.0e-12,
    )


def test_strong_bias_raises_loaded_probability() -> None:
    config = load_dice_config()

    counts = [
        5,
        5,
        5,
        5,
        5,
        75,
    ]

    log_h0 = log_marginal_likelihood_h0(
        counts,
        config.model.fair_probabilities.values,
    )

    log_h1 = log_marginal_likelihood_h1(
        counts,
        config.model.dirichlet_alpha,
    )

    posterior = posterior_loaded_probability(
        log_marginal_h0=log_h0,
        log_marginal_h1=log_h1,
        prior_loaded_probability=0.5,
    )

    assert posterior > 0.95


def test_posterior_predictive_probabilities_sum_to_one() -> None:
    config = load_dice_config()

    probabilities = posterior_predictive_probabilities(
        [10, 20, 30, 40, 50, 60],
        config.model.dirichlet_alpha,
    )

    assert len(probabilities) == 6

    assert sum(probabilities) == pytest.approx(
        1.0,
        abs=1.0e-12,
    )


def test_predictive_probabilities_match_dirichlet_formula() -> None:
    config = load_dice_config()

    probabilities = posterior_predictive_probabilities(
        [1, 0, 0, 0, 0, 0],
        config.model.dirichlet_alpha,
    )

    assert probabilities[0] == pytest.approx(
        2.0 / 7.0,
        abs=1.0e-12,
    )

    for probability in probabilities[1:]:
        assert probability == pytest.approx(
            1.0 / 7.0,
            abs=1.0e-12,
        )


@pytest.mark.parametrize(
    "scenario_id",
    [
        "fair",
        "mildly_loaded",
        "clearly_loaded",
    ],
)
def test_sequential_posteriors_remain_valid(
    scenario_id: str,
) -> None:
    config = load_dice_config()

    simulation = simulate_scenario(
        config,
        scenario_id,
    )

    inference = sequential_inference(
        simulation,
        model=config.model,
        thresholds=config.decision,
    )

    assert len(inference.records) == 180

    for record in inference.records:
        assert 0.0 <= record.posterior_loaded <= 1.0
        assert 0.0 <= record.posterior_fair <= 1.0

        assert (record.posterior_loaded + record.posterior_fair) == pytest.approx(
            1.0,
            abs=1.0e-12,
        )

        assert sum(record.predictive_probabilities) == pytest.approx(
            1.0,
            abs=1.0e-12,
        )

        assert math.isfinite(record.log_marginal_h0)

        assert math.isfinite(record.log_marginal_h1)

        assert math.isfinite(record.log_bayes_factor_h1_h0)


def test_clearly_loaded_showcase_crosses_loaded_threshold() -> None:
    config = load_dice_config()

    simulation = simulate_scenario(
        config,
        "clearly_loaded",
    )

    inference = sequential_inference(
        simulation,
        model=config.model,
        thresholds=config.decision,
    )

    assert inference.first_loaded_detection_roll is not None

    assert inference.final_decision_state is DecisionState.LOADED

    assert inference.final_posterior_loaded >= 0.95


def test_fair_showcase_does_not_finish_loaded() -> None:
    config = load_dice_config()

    simulation = simulate_scenario(
        config,
        "fair",
    )

    inference = sequential_inference(
        simulation,
        model=config.model,
        thresholds=config.decision,
    )

    assert inference.final_decision_state is not DecisionState.LOADED


def test_configured_roll_count_has_no_underflow_or_nonfinite_values() -> None:
    config = load_dice_config()

    simulation = simulate_scenario(
        config,
        "clearly_loaded",
    )

    inference = sequential_inference(
        simulation,
        model=config.model,
        thresholds=config.decision,
    )

    for record in inference.records:
        assert math.isfinite(record.log_marginal_h0)

        assert math.isfinite(record.log_marginal_h1)

        assert math.isfinite(record.posterior_loaded)


def test_posterior_history_csv_has_expected_schema(
    tmp_path: Path,
) -> None:
    config = load_dice_config()

    simulation = simulate_scenario(
        config,
        "clearly_loaded",
    )

    inference = sequential_inference(
        simulation,
        model=config.model,
        thresholds=config.decision,
    )

    path = tmp_path / "posterior_history.csv"

    write_posterior_history_csv(
        inference,
        path,
    )

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 180

    assert rows[0]["roll_index"] == "1"
    assert rows[-1]["roll_index"] == "180"

    assert "posterior_loaded" in rows[0]
    assert "predictive_face_6" in rows[0]
    assert "decision_state" in rows[0]


def test_invalid_counts_are_rejected() -> None:
    config = load_dice_config()

    with pytest.raises(DiceInferenceError):
        log_marginal_likelihood_h1(
            [1, 2, 3],
            config.model.dirichlet_alpha,
        )

    with pytest.raises(DiceInferenceError):
        log_marginal_likelihood_h1(
            [1, 2, 3, 4, 5, -1],
            config.model.dirichlet_alpha,
        )
