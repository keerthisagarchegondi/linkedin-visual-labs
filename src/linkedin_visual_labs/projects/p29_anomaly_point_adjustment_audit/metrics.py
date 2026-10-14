"""Raw pointwise confusion counts and explicitly nullable rate metrics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

BinaryVector = Sequence[int] | NDArray[np.int64]


def _validate_binary_pair(labels: BinaryVector, predictions: BinaryVector) -> None:
    if len(labels) != len(predictions):
        raise ValueError("labels and predictions must have the same length")
    if any(
        (type(value) is not int and not isinstance(value, np.integer)) or value not in (0, 1)
        for value in labels
    ):
        raise ValueError("labels must contain only binary integers")
    if any(
        (type(value) is not int and not isinstance(value, np.integer)) or value not in (0, 1)
        for value in predictions
    ):
        raise ValueError("predictions must contain only binary integers")


@dataclass(frozen=True, slots=True)
class ConfusionCounts:
    """Immutable pointwise confusion counts."""

    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int

    def __post_init__(self) -> None:
        if any(
            type(value) is not int or value < 0
            for value in (
                self.true_positive,
                self.false_positive,
                self.false_negative,
                self.true_negative,
            )
        ):
            raise ValueError("confusion counts must be non-negative integers")

    @property
    def precision(self) -> float | None:
        denominator = self.true_positive + self.false_positive
        return None if denominator == 0 else self.true_positive / denominator

    @property
    def recall(self) -> float | None:
        denominator = self.true_positive + self.false_negative
        return None if denominator == 0 else self.true_positive / denominator

    @property
    def f1(self) -> float | None:
        """Return F1, or None when neither labels nor predictions are positive."""
        denominator = 2 * self.true_positive + self.false_positive + self.false_negative
        return None if denominator == 0 else 2 * self.true_positive / denominator


def confusion_counts(labels: BinaryVector, predictions: BinaryVector) -> ConfusionCounts:
    """Compute immutable confusion counts from explicit binary pointwise vectors."""
    _validate_binary_pair(labels, predictions)
    true_positive = false_positive = false_negative = true_negative = 0
    for label, prediction in zip(labels, predictions, strict=True):
        if label == 1 and prediction == 1:
            true_positive += 1
        elif label == 0 and prediction == 1:
            false_positive += 1
        elif label == 1:
            false_negative += 1
        else:
            true_negative += 1
    return ConfusionCounts(true_positive, false_positive, false_negative, true_negative)
