from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.analytics import (
    event_hit_probability,
    exact_finite_run_f1,
    expected_adjusted_counts,
    expected_adjusted_recall,
    expected_raw_counts,
    paired_counts_from_event_hits,
    ratio_of_expected_counts_f1,
)
from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.metrics import ConfusionCounts


def test_event_hit_probability_boundary_and_length_properties() -> None:
    assert event_hit_probability(5, 0.0) == 0.0
    assert event_hit_probability(5, 1.0) == 1.0
    assert math.isclose(event_hit_probability(1, 0.17), 0.17)
    assert math.isclose(event_hit_probability(200, 0.01), 1.0 - 0.99**200)


def test_expected_counts_and_ratio_reference() -> None:
    raw = expected_raw_counts((2, 3), 0.1, 5)
    adjusted = expected_adjusted_counts((2, 3), 0.1, 5)
    assert raw.true_positive == 0.5
    assert raw.false_positive == adjusted.false_positive == 0.5
    assert adjusted.true_positive > raw.true_positive
    assert expected_adjusted_recall((2, 3), 0.1) == adjusted.true_positive / 5
    assert ratio_of_expected_counts_f1(adjusted) == adjusted.f1


def test_paired_counts_sufficient_statistics() -> None:
    paired = paired_counts_from_event_hits((3, 2), (1, 0), 2, 4)
    assert paired.raw == ConfusionCounts(1, 2, 4, 2)
    assert paired.adjusted == ConfusionCounts(3, 2, 2, 2)


def test_exact_enumeration_probability_and_pa_inflation() -> None:
    result = exact_finite_run_f1((1, 1, 0), 0.5)
    assert math.isclose(result.probability_mass, 1.0)
    assert result.expected_adjusted_f1 >= result.expected_raw_f1


@pytest.mark.parametrize("q", [-0.1, 1.1])
def test_analytical_validation(q: float) -> None:
    with pytest.raises(ValueError):
        event_hit_probability(1, q)
    with pytest.raises(ValueError):
        exact_finite_run_f1((0, 0), 0.5)


def test_sufficient_counts_and_enumerator_validation() -> None:
    with pytest.raises(ValueError):
        expected_raw_counts((), 0.5, 1)
    with pytest.raises(ValueError):
        expected_adjusted_counts((1,), 0.5, -1)
    with pytest.raises(ValueError):
        paired_counts_from_event_hits((2,), (3,), 0, 1)
    with pytest.raises(ValueError):
        paired_counts_from_event_hits((2,), (1,), 2, 1)
    with pytest.raises(ValueError):
        exact_finite_run_f1((1, 0), 0.5, maximum_positions=0)
    with pytest.raises(ValueError):
        exact_finite_run_f1((1, 0, 1), 0.5, maximum_positions=2)
