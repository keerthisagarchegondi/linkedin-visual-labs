from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.metrics import (
    ConfusionCounts,
    confusion_counts,
)


def test_confusion_counts_and_rates() -> None:
    counts = confusion_counts((1, 1, 0, 0), (1, 0, 1, 0))
    assert counts == ConfusionCounts(1, 1, 1, 1)
    assert counts.precision == 0.5
    assert counts.recall == 0.5
    assert counts.f1 == 0.5


def test_nullable_zero_denominator_conventions() -> None:
    all_negative = confusion_counts((0, 0), (0, 0))
    assert all_negative.precision is None
    assert all_negative.recall is None
    assert all_negative.f1 is None
    missed_positive = confusion_counts((1, 0), (0, 0))
    assert missed_positive.precision is None
    assert missed_positive.recall == 0.0
    assert missed_positive.f1 == 0.0


def test_metric_input_and_count_validation() -> None:
    with pytest.raises(ValueError):
        confusion_counts((1,), (1, 0))
    with pytest.raises(ValueError):
        confusion_counts((1,), (2,))
    with pytest.raises(ValueError):
        ConfusionCounts(-1, 0, 0, 0)
