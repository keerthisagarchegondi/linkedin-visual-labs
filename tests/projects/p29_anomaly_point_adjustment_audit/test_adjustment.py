from __future__ import annotations

from itertools import product

import numpy as np
import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.adjustment import (
    adjusted_events,
    point_adjust,
)
from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.metrics import (
    confusion_counts,
)


def test_point_adjustment_is_fresh_and_preserves_outside_predictions() -> None:
    labels = (0, 1, 1, 0, 1, 0)
    raw = (1, 0, 1, 0, 0, 1)
    adjusted = point_adjust(labels, raw)
    assert np.array_equal(adjusted, np.array((1, 1, 1, 0, 0, 1)))
    assert tuple(raw) == (1, 0, 1, 0, 0, 1)
    adjusted[0] = 0
    assert raw[0] == 1


def test_pa_f1_never_decreases_for_exhaustive_small_binary_vectors() -> None:
    for labels in product((0, 1), repeat=5):
        for raw in product((0, 1), repeat=5):
            raw_f1 = confusion_counts(labels, raw).f1
            adjusted_f1 = confusion_counts(labels, point_adjust(labels, raw)).f1
            if raw_f1 is not None and adjusted_f1 is not None:
                assert adjusted_f1 >= raw_f1


def test_adjustment_validates_inputs_and_exposes_events() -> None:
    assert adjusted_events((0, 1, 1))[-1].length == 2
    with pytest.raises(ValueError):
        point_adjust((0, 1), (0,))
    with pytest.raises(ValueError):
        point_adjust((0, 2), (0, 1))
