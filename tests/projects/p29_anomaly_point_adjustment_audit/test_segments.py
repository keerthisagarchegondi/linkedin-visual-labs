from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.segments import (
    Event,
    extract_events,
)


def test_extract_events_returns_maximal_half_open_runs() -> None:
    events = extract_events((0, 1, 1, 0, 1, 0, 0, 1))
    assert events == (Event(1, 3), Event(4, 5), Event(7, 8))
    assert tuple(event.length for event in events) == (2, 1, 1)


@pytest.mark.parametrize("labels", [(), (0, 0), (1,), (1, 1)])
def test_extract_events_handles_empty_and_boundaries(labels: tuple[int, ...]) -> None:
    assert extract_events(labels) == (() if 1 not in labels else (Event(0, len(labels)),))


def test_event_and_vector_validation() -> None:
    with pytest.raises(ValueError):
        Event(2, 2)
    with pytest.raises(ValueError):
        Event(-1, 2)
    with pytest.raises(ValueError):
        extract_events((0, 2))
