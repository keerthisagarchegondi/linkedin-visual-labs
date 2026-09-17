from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.metrics import (
    evaluate_probabilities,
    expected_calibration_error,
    top_decile_metrics,
)


def test_metric_formulas_are_bounded_and_reconciled() -> None:
    y = [
        0,
        0,
        1,
        1,
        0,
        1,
        0,
        1,
        0,
        1,
    ]

    p = [
        0.05,
        0.10,
        0.90,
        0.80,
        0.20,
        0.70,
        0.30,
        0.60,
        0.40,
        0.95,
    ]

    result = evaluate_probabilities(
        y,
        p,
    )

    assert 0.0 <= result.roc_auc <= 1.0
    assert 0.0 <= result.pr_auc <= 1.0
    assert 0.0 <= result.brier_score <= 1.0
    assert 0.0 <= result.expected_calibration_error <= 1.0

    assert result.target_prevalence == pytest.approx(0.5)

    assert math.isfinite(result.calibration_slope)


def test_top_decile_metric_on_ten_rows_is_top_one() -> None:
    rate, lift, per_1000 = top_decile_metrics(
        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.99, 0.6, 0.7, 0.8, 0.9],
    )

    assert rate == 1.0
    assert lift == 10.0
    assert per_1000 == 1000.0


def test_ece_rejects_invalid_bin_count() -> None:
    with pytest.raises(
        ValueError,
        match="bins must be positive",
    ):
        expected_calibration_error(
            [0, 1],
            [0.1, 0.9],
            bins=0,
        )


def test_metrics_reject_invalid_probability_domain() -> None:
    with pytest.raises(
        ValueError,
        match=r"\[0, 1\]",
    ):
        evaluate_probabilities(
            [0, 1],
            [0.1, 1.1],
        )
