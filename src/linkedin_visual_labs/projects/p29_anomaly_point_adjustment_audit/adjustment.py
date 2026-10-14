"""Label-aware retrospective standard point adjustment, isolated from raw scoring."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from .segments import Event, extract_events


def _as_binary_array(values: Sequence[int], *, name: str) -> NDArray[np.int64]:
    if any(type(value) is not int or value not in (0, 1) for value in values):
        raise ValueError(f"{name} must contain only binary integers")
    return np.asarray(tuple(values), dtype=np.int64)


def point_adjust(labels: Sequence[int], raw_predictions: Sequence[int]) -> NDArray[np.int64]:
    """Return a fresh PA prediction vector without mutating or aliasing raw predictions.

    For each ground-truth event, one raw positive credits the whole event. Positions outside
    ground-truth events are left exactly as they were in the raw prediction vector.
    """
    label_array = _as_binary_array(labels, name="labels")
    raw_array = _as_binary_array(raw_predictions, name="raw_predictions")
    if label_array.size != raw_array.size:
        raise ValueError("labels and raw_predictions must have the same length")
    adjusted = raw_array.copy()
    for event in extract_events(tuple(int(value) for value in label_array)):
        if bool(np.any(raw_array[event.start : event.stop] == 1)):
            adjusted[event.start : event.stop] = 1
    return adjusted


def adjusted_events(labels: Sequence[int]) -> tuple[Event, ...]:
    """Expose the events PA evaluates without retaining mutable timeline state."""
    return extract_events(labels)
