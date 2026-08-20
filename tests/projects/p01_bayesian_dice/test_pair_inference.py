"""Tests for six-model Bayesian pair-sum inference."""

from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    PAIR_CASE_IDS,
    DecisionState,
    ProbabilityVector,
    derive_pair_model_pmfs,
    derive_pair_sum_pmf,
    find_first_state_roll,
    find_stable_decision_roll,
    infer_all_pair_cases,
    infer_pair_case,
    load_dice_config,
    normalize_model_posteriors,
    simulate_all_pair_cases,
    simulate_pair_case,
)


def test_fair_fair_sum_pmf_matches_standard_two_dice_distribution() -> None:
    fair = ProbabilityVector.from_sequence([1.0 / 6.0] * 6)

    actual = derive_pair_sum_pmf(
        fair,
        fair,
    )

    expected = tuple(
        value / 36.0
        for value in (
            1,
            2,
            3,
            4,
            5,
            6,
            5,
            4,
            3,
            2,
            1,
        )
    )

    assert actual == pytest.approx(
        expected,
        abs=1.0e-12,
    )


def test_pair_sum_convolution_is_symmetric() -> None:
    config = load_dice_config()

    fair = config.die_type("unloaded").probabilities

    partial = config.die_type("partially_loaded").probabilities

    assert derive_pair_sum_pmf(
        fair,
        partial,
    ) == pytest.approx(
        derive_pair_sum_pmf(
            partial,
            fair,
        ),
        abs=1.0e-12,
    )


def test_all_six_model_pmfs_are_valid_and_distinct() -> None:
    config = load_dice_config()

    pmfs = derive_pair_model_pmfs(config.pair_experiment)

    assert tuple(pmfs) == PAIR_CASE_IDS

    assert len({pmf.probabilities for pmf in pmfs.values()}) == 6

    for pmf in pmfs.values():
        assert len(pmf.probabilities) == 11

        assert math.fsum(pmf.probabilities) == pytest.approx(
            1.0,
            abs=1.0e-12,
        )


def test_prior_only_model_posteriors_match_model_priors() -> None:
    config = load_dice_config()

    posterior = normalize_model_posteriors(
        [0.0] * 6,
        config.pair_experiment.model_priors.values,
    )

    expected = tuple(
        config.pair_experiment.model_priors.values[model_id] for model_id in PAIR_CASE_IDS
    )

    assert posterior == pytest.approx(
        expected,
        abs=1.0e-12,
    )


def test_one_observation_posterior_matches_direct_bayes_formula() -> None:
    config = load_dice_config()

    experiment = config.pair_experiment

    pmfs = derive_pair_model_pmfs(experiment)

    observed_sum = 12

    likelihoods = [pmfs[model_id].probability(observed_sum) for model_id in PAIR_CASE_IDS]

    log_likelihoods = [math.log(value) for value in likelihoods]

    posterior = normalize_model_posteriors(
        log_likelihoods,
        experiment.model_priors.values,
    )

    raw_weights = [
        experiment.model_priors.values[model_id] * likelihood
        for model_id, likelihood in zip(
            PAIR_CASE_IDS,
            likelihoods,
            strict=True,
        )
    ]

    denominator = math.fsum(raw_weights)

    expected = tuple(value / denominator for value in raw_weights)

    assert posterior == pytest.approx(
        expected,
        abs=1.0e-12,
    )


def test_posterior_normalization_handles_near_degenerate_pp_evidence() -> None:
    config = load_dice_config()

    log_likelihoods = (
        -16578.98360429575,
        -16429.385804309637,
        -16409.531700590356,
        -16382.739377272426,
        -16516.569937849818,
        -16908.04787711518,
    )

    posterior = normalize_model_posteriors(
        log_likelihoods,
        config.pair_experiment.model_priors.values,
    )

    assert math.fsum(posterior) == pytest.approx(
        1.0,
        abs=1.0e-15,
    )

    assert all(0.0 <= value <= 1.0 for value in posterior)

    assert posterior[PAIR_CASE_IDS.index("PP")] > 0.999999999

    assert max(
        range(len(posterior)),
        key=posterior.__getitem__,
    ) == PAIR_CASE_IDS.index("PP")


def test_first_state_roll() -> None:
    states = (
        DecisionState.UNCERTAIN,
        DecisionState.UNCERTAIN,
        DecisionState.LOADED,
        DecisionState.LOADED,
    )

    assert (
        find_first_state_roll(
            states,
            DecisionState.LOADED,
        )
        == 3
    )

    assert (
        find_first_state_roll(
            states,
            DecisionState.FAIR,
        )
        is None
    )


def test_stable_decision_roll_uses_final_permanent_suffix() -> None:
    states = (
        DecisionState.UNCERTAIN,
        DecisionState.LOADED,
        DecisionState.UNCERTAIN,
        DecisionState.LOADED,
        DecisionState.LOADED,
        DecisionState.LOADED,
    )

    assert find_stable_decision_roll(states) == 4


def test_stable_decision_roll_for_fair_suffix() -> None:
    states = (
        DecisionState.UNCERTAIN,
        DecisionState.FAIR,
        DecisionState.UNCERTAIN,
        DecisionState.FAIR,
        DecisionState.FAIR,
    )

    assert find_stable_decision_roll(states) == 4


def test_stable_decision_is_none_when_final_state_uncertain() -> None:
    states = (
        DecisionState.LOADED,
        DecisionState.UNCERTAIN,
    )

    assert find_stable_decision_roll(states) is None


@pytest.mark.parametrize(
    "case_id",
    PAIR_CASE_IDS,
)
def test_every_pair_case_produces_10000_valid_inference_records(
    case_id: str,
) -> None:
    config = load_dice_config()

    simulation = simulate_pair_case(
        config.pair_experiment,
        case_id,
    )

    result = infer_pair_case(
        config.pair_experiment,
        simulation,
    )

    assert len(result.records) == 10_000

    for record in result.records:
        assert len(record.model_posteriors) == 6

        assert math.fsum(record.model_posteriors) == pytest.approx(
            1.0,
            abs=1.0e-12,
        )

        assert record.posterior_fair == pytest.approx(
            record.posterior_for("UU"),
            abs=1.0e-12,
        )

        assert record.posterior_loaded == pytest.approx(
            1.0 - record.posterior_fair,
            abs=1.0e-12,
        )

        assert 0.0 <= record.posterior_loaded <= 1.0


def test_all_six_cases_produce_60000_inference_records() -> None:
    config = load_dice_config()

    simulation = simulate_all_pair_cases(config)

    result = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    assert result.total_record_count == 60_000


def test_uu_finishes_fair_with_stable_decision() -> None:
    config = load_dice_config()

    simulation = simulate_pair_case(
        config.pair_experiment,
        "UU",
    )

    result = infer_pair_case(
        config.pair_experiment,
        simulation,
    )

    assert result.final_decision_state is DecisionState.FAIR

    assert result.stable_decision_roll is not None

    assert result.stable_decision_state is DecisionState.FAIR

    assert result.final_posterior_loaded <= 0.05


@pytest.mark.parametrize(
    "case_id",
    (
        "UP",
        "UF",
        "PP",
        "PF",
        "FF",
    ),
)
def test_loaded_cases_finish_loaded_with_stable_decision(
    case_id: str,
) -> None:
    config = load_dice_config()

    simulation = simulate_pair_case(
        config.pair_experiment,
        case_id,
    )

    result = infer_pair_case(
        config.pair_experiment,
        simulation,
    )

    assert result.final_decision_state is DecisionState.LOADED

    assert result.stable_decision_roll is not None

    assert result.stable_decision_state is DecisionState.LOADED

    assert result.final_posterior_loaded >= 0.95


def test_stable_decision_roll_is_truthful_for_all_cases() -> None:
    config = load_dice_config()

    simulation = simulate_all_pair_cases(config)

    inference = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    for case_id in PAIR_CASE_IDS:
        result = inference.case(case_id)

        assert result.stable_decision_roll is not None

        stable_index = result.stable_decision_roll - 1

        final_state = result.final_decision_state

        assert all(record.decision_state is final_state for record in result.records[stable_index:])

        if stable_index > 0:
            assert result.records[stable_index - 1].decision_state is not final_state
