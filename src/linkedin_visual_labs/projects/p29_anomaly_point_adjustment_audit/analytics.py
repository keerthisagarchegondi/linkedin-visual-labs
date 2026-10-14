"""Independent analytical and exact finite-case references for Project 9."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from math import expm1, log1p

from .adjustment import point_adjust
from .metrics import ConfusionCounts, confusion_counts


def _validate_event_lengths(event_lengths: Sequence[int]) -> tuple[int, ...]:
    lengths = tuple(event_lengths)
    if not lengths or any(type(length) is not int or length <= 0 for length in lengths):
        raise ValueError("event_lengths must be a non-empty sequence of positive integers")
    return lengths


def _validate_probability(q: float) -> None:
    if type(q) not in (float, int) or not 0.0 <= float(q) <= 1.0:
        raise ValueError("q must be a probability in [0, 1]")


def _validate_n0(n0: int) -> None:
    if type(n0) is not int or n0 < 0:
        raise ValueError("n0 must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class ExpectedCounts:
    """Expected (possibly fractional) pointwise confusion counts."""

    true_positive: float
    false_positive: float
    false_negative: float
    true_negative: float

    @property
    def f1(self) -> float | None:
        denominator = 2.0 * self.true_positive + self.false_positive + self.false_negative
        return None if denominator == 0.0 else 2.0 * self.true_positive / denominator


@dataclass(frozen=True, slots=True)
class PairedConfusionCounts:
    """Raw and PA counts derived from the same event-hit and outside-FP artifact."""

    raw: ConfusionCounts
    adjusted: ConfusionCounts


@dataclass(frozen=True, slots=True)
class FiniteEnumerationResult:
    """Exact probability-weighted F1 references for a small positive-label timeline."""

    probability_mass: float
    expected_raw_f1: float
    expected_adjusted_f1: float


def event_hit_probability(length: int, q: float) -> float:
    """Return ``1 - (1-q)**length`` using numerically stable elementary functions."""
    _validate_event_lengths((length,))
    _validate_probability(q)
    if float(q) == 1.0:
        return 1.0
    return -expm1(length * log1p(-float(q)))


def expected_raw_counts(event_lengths: Sequence[int], q: float, n0: int) -> ExpectedCounts:
    """Return raw-score expected counts under independent Bernoulli alerts."""
    lengths = _validate_event_lengths(event_lengths)
    _validate_probability(q)
    _validate_n0(n0)
    positives = sum(lengths)
    probability = float(q)
    return ExpectedCounts(
        true_positive=positives * probability,
        false_positive=n0 * probability,
        false_negative=positives * (1.0 - probability),
        true_negative=n0 * (1.0 - probability),
    )


def expected_adjusted_counts(event_lengths: Sequence[int], q: float, n0: int) -> ExpectedCounts:
    """Return PA expected counts; only event true-positive credit changes."""
    lengths = _validate_event_lengths(event_lengths)
    _validate_probability(q)
    _validate_n0(n0)
    probability = float(q)
    true_positive = sum(length * event_hit_probability(length, probability) for length in lengths)
    positives = sum(lengths)
    return ExpectedCounts(
        true_positive=true_positive,
        false_positive=n0 * probability,
        false_negative=positives - true_positive,
        true_negative=n0 * (1.0 - probability),
    )


def expected_adjusted_recall(event_lengths: Sequence[int], q: float) -> float:
    """Return expected PA recall for the specified positive-event layout."""
    lengths = _validate_event_lengths(event_lengths)
    positives = sum(lengths)
    return sum(length * event_hit_probability(length, q) for length in lengths) / positives


def ratio_of_expected_counts_f1(counts: ExpectedCounts) -> float | None:
    """Return F1 applied to expected counts, never an exact expected finite-run F1."""
    return counts.f1


def paired_counts_from_event_hits(
    event_lengths: Sequence[int], event_hits: Sequence[int], outside_false_positives: int, n0: int
) -> PairedConfusionCounts:
    """Derive paired raw/PA counts from sufficient event and normal-region counts."""
    lengths = _validate_event_lengths(event_lengths)
    if len(event_hits) != len(lengths):
        raise ValueError("event_hits must have one value per event")
    if any(type(hit) is not int for hit in event_hits):
        raise ValueError("event_hits must contain integers")
    if any(hit < 0 or hit > length for hit, length in zip(event_hits, lengths, strict=True)):
        raise ValueError("each event hit count must be in [0, event length]")
    _validate_n0(n0)
    if type(outside_false_positives) is not int or not 0 <= outside_false_positives <= n0:
        raise ValueError("outside_false_positives must be in [0, n0]")
    positives = sum(lengths)
    raw_true_positive = sum(event_hits)
    adjusted_true_positive = sum(
        length for hit, length in zip(event_hits, lengths, strict=True) if hit > 0
    )
    raw = ConfusionCounts(
        raw_true_positive,
        outside_false_positives,
        positives - raw_true_positive,
        n0 - outside_false_positives,
    )
    adjusted = ConfusionCounts(
        adjusted_true_positive,
        outside_false_positives,
        positives - adjusted_true_positive,
        n0 - outside_false_positives,
    )
    return PairedConfusionCounts(raw=raw, adjusted=adjusted)


def exact_finite_run_f1(
    labels: Sequence[int], q: float, *, maximum_positions: int = 16
) -> FiniteEnumerationResult:
    """Enumerate all Bernoulli prediction vectors for a tiny, positive-label timeline.

    This is an oracle for tests and finite examples only. It deliberately rejects large
    timelines and all-normal labels, where the declared nullable F1 convention has an
    undefined all-negative state rather than a universally meaningful expected F1.
    """
    label_values = tuple(labels)
    if not label_values or any(
        type(label) is not int or label not in (0, 1) for label in label_values
    ):
        raise ValueError("labels must be a non-empty binary integer sequence")
    if sum(label_values) == 0:
        raise ValueError("exact F1 enumeration requires at least one positive label")
    if type(maximum_positions) is not int or maximum_positions < 1:
        raise ValueError("maximum_positions must be a positive integer")
    if len(label_values) > maximum_positions:
        raise ValueError("timeline exceeds the exact enumeration maximum")
    _validate_probability(q)
    probability = float(q)
    total_mass = raw_total = adjusted_total = 0.0
    for prediction_values in product((0, 1), repeat=len(label_values)):
        ones = sum(prediction_values)
        weight = probability**ones * (1.0 - probability) ** (len(label_values) - ones)
        raw_f1 = confusion_counts(label_values, prediction_values).f1
        adjusted_f1 = confusion_counts(
            label_values, point_adjust(label_values, prediction_values)
        ).f1
        if raw_f1 is None or adjusted_f1 is None:
            raise AssertionError("positive-label timelines must have defined F1")
        total_mass += weight
        raw_total += weight * raw_f1
        adjusted_total += weight * adjusted_f1
    return FiniteEnumerationResult(total_mass, raw_total, adjusted_total)
