"""Tests for Bayesian Dice domain models."""

from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    DecisionState,
    DecisionThresholds,
    DiceModelError,
    ProbabilityVector,
)


def test_probability_vector_accepts_fair_die() -> None:
    vector = ProbabilityVector.from_sequence([1.0 / 6.0] * 6)

    assert len(vector.values) == 6
    assert sum(vector.values) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "values",
    [
        [0.5, 0.5],
        [0.2] * 6,
        [0.2, 0.2, 0.2, 0.2, 0.2, -0.0 + -0.1],
        [0.2, 0.2, 0.2, 0.2, 0.2, float("nan")],
    ],
)
def test_probability_vector_rejects_invalid_values(
    values: list[float],
) -> None:
    with pytest.raises(DiceModelError):
        ProbabilityVector.from_sequence(values)


def test_probability_vector_rejects_boolean() -> None:
    with pytest.raises(DiceModelError):
        ProbabilityVector.from_sequence([True, 0.2, 0.2, 0.2, 0.2, 0.2])


def test_decision_thresholds_classify_all_three_states() -> None:
    thresholds = DecisionThresholds(
        fair_threshold=0.05,
        loaded_threshold=0.95,
    )

    assert thresholds.classify(0.01) is DecisionState.FAIR
    assert thresholds.classify(0.50) is DecisionState.UNCERTAIN
    assert thresholds.classify(0.99) is DecisionState.LOADED


def test_decision_thresholds_include_exact_boundaries() -> None:
    thresholds = DecisionThresholds(
        fair_threshold=0.05,
        loaded_threshold=0.95,
    )

    assert thresholds.classify(0.05) is DecisionState.FAIR
    assert thresholds.classify(0.95) is DecisionState.LOADED


@pytest.mark.parametrize(
    ("fair_threshold", "loaded_threshold"),
    [
        (0.95, 0.05),
        (-0.01, 0.95),
        (0.05, 1.01),
        (0.50, 0.50),
    ],
)
def test_decision_thresholds_reject_invalid_ordering(
    fair_threshold: float,
    loaded_threshold: float,
) -> None:
    with pytest.raises(DiceModelError):
        DecisionThresholds(
            fair_threshold=fair_threshold,
            loaded_threshold=loaded_threshold,
        )
