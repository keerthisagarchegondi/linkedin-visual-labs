"""Frozen baseline metrics for Project 7."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)


@dataclass(frozen=True, slots=True)
class MetricBundle:
    """One frozen evaluation metric record."""

    roc_auc: float
    pr_auc: float
    brier_score: float
    expected_calibration_error: float
    top_decile_response_rate: float
    top_decile_lift: float
    conversions_per_1000: float
    false_positive_contacts: int
    target_prevalence: float
    calibration_intercept: float
    calibration_slope: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def expected_calibration_error(
    y_true: Sequence[int],
    probabilities: Sequence[float],
    *,
    bins: int = 10,
) -> float:
    """Equal-width expected calibration error."""

    if bins <= 0:
        raise ValueError("bins must be positive.")

    y = np.asarray(
        y_true,
        dtype=float,
    )

    p = np.asarray(
        probabilities,
        dtype=float,
    )

    if y.shape != p.shape:
        raise ValueError("Targets/probabilities must have equal shape.")

    edges = np.linspace(
        0.0,
        1.0,
        bins + 1,
    )

    total = len(y)

    if total == 0:
        raise ValueError("Cannot evaluate an empty prediction set.")

    error = 0.0

    for index in range(bins):
        lower = edges[index]
        upper = edges[index + 1]

        mask = (p >= lower) & (p <= upper) if index == bins - 1 else (p >= lower) & (p < upper)

        count = int(mask.sum())

        if count == 0:
            continue

        observed = float(y[mask].mean())

        predicted = float(p[mask].mean())

        error += count / total * abs(observed - predicted)

    return float(error)


def top_decile_metrics(
    y_true: Sequence[int],
    probabilities: Sequence[float],
) -> tuple[float, float, float]:
    """Response rate, lift and conversions/1,000 for top-ranked decile."""

    y = np.asarray(
        y_true,
        dtype=float,
    )

    p = np.asarray(
        probabilities,
        dtype=float,
    )

    if len(y) == 0:
        raise ValueError("Cannot rank an empty prediction set.")

    count = max(
        1,
        math.ceil(len(y) * 0.10),
    )

    ranked = np.argsort(
        -p,
        kind="stable",
    )

    top = ranked[:count]

    prevalence = float(y.mean())

    response_rate = float(y[top].mean())

    lift = response_rate / prevalence if prevalence > 0 else 0.0

    return (
        response_rate,
        lift,
        response_rate * 1000.0,
    )


def practical_calibration_parameters(
    y_true: Sequence[int],
    probabilities: Sequence[float],
) -> tuple[float, float]:
    """Approximate calibration intercept/slope on model log odds."""

    y = np.asarray(
        y_true,
        dtype=int,
    )

    p = np.asarray(
        probabilities,
        dtype=float,
    )

    if len(set(y.tolist())) < 2:
        return (
            float("nan"),
            float("nan"),
        )

    clipped = np.clip(
        p,
        1e-6,
        1.0 - 1e-6,
    )

    logits = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)

    calibrator = LogisticRegression(
        C=1_000_000.0,
        solver="lbfgs",
        max_iter=1000,
    )

    calibrator.fit(
        logits,
        y,
    )

    return (
        float(calibrator.intercept_[0]),
        float(calibrator.coef_[0][0]),
    )


def evaluate_probabilities(
    y_true: Sequence[int],
    probabilities: Sequence[float],
    *,
    threshold: float = 0.50,
) -> MetricBundle:
    """Calculate the frozen Step 2 baseline metric set."""

    y = np.asarray(
        y_true,
        dtype=int,
    )

    p = np.asarray(
        probabilities,
        dtype=float,
    )

    if y.shape != p.shape:
        raise ValueError("Targets/probabilities must have equal shape.")

    if len(y) == 0:
        raise ValueError("Cannot evaluate an empty prediction set.")

    if np.any((p < 0.0) | (p > 1.0)):
        raise ValueError("Probabilities must lie in [0, 1].")

    y_list = y.tolist()
    p_list = p.tolist()

    response_rate, lift, per_1000 = top_decile_metrics(
        y_list,
        p_list,
    )

    predicted_positive = p >= threshold

    false_positives = int((predicted_positive & (y == 0)).sum())

    intercept, slope = practical_calibration_parameters(
        y_list,
        p_list,
    )

    return MetricBundle(
        roc_auc=float(
            roc_auc_score(
                y,
                p,
            )
        ),
        pr_auc=float(
            average_precision_score(
                y,
                p,
            )
        ),
        brier_score=float(
            brier_score_loss(
                y,
                p,
            )
        ),
        expected_calibration_error=(
            expected_calibration_error(
                y_list,
                p_list,
            )
        ),
        top_decile_response_rate=response_rate,
        top_decile_lift=lift,
        conversions_per_1000=per_1000,
        false_positive_contacts=false_positives,
        target_prevalence=float(y.mean()),
        calibration_intercept=intercept,
        calibration_slope=slope,
    )
