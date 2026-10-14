"""Immutable extraction of maximal positive anomaly-event segments."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Event:
    """A half-open, maximal contiguous positive interval."""

    start: int
    stop: int

    def __post_init__(self) -> None:
        if type(self.start) is not int or type(self.stop) is not int or self.start < 0:
            raise ValueError("event bounds must be non-negative integers")
        if self.stop <= self.start:
            raise ValueError("event stop must be greater than event start")

    @property
    def length(self) -> int:
        """Return the number of timestamps in this half-open interval."""
        return self.stop - self.start


def _validate_binary_vector(values: Sequence[int], *, name: str) -> None:
    if any(type(value) is not int or value not in (0, 1) for value in values):
        raise ValueError(f"{name} must contain only binary integers")


def extract_events(labels: Sequence[int]) -> tuple[Event, ...]:
    """Return every maximal contiguous run of positive labels, in order."""
    _validate_binary_vector(labels, name="labels")
    events: list[Event] = []
    start: int | None = None
    for index, label in enumerate(labels):
        if label == 1 and start is None:
            start = index
        elif label == 0 and start is not None:
            events.append(Event(start=start, stop=index))
            start = None
    if start is not None:
        events.append(Event(start=start, stop=len(labels)))
    return tuple(events)
