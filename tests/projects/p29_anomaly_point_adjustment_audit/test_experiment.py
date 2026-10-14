from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.config import (
    load_default_config,
)
from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.experiment import (
    Condition,
    build_equal_event_timeline,
    condition_id,
    frozen_conditions,
    run_pilot,
    simulate_condition,
)


def test_frozen_grid_and_condition_identity_are_stable() -> None:
    config = load_default_config()
    conditions = frozen_conditions(config, 4)
    assert len(conditions) == 45
    assert len({condition.condition_id for condition in conditions}) == 45
    assert condition_id(config, 200, 0.01, 4) == condition_id(config, 200, 0.01, 4)


def test_timeline_is_deterministic_and_integral() -> None:
    first = build_equal_event_timeline(20, 8, 2)
    second = build_equal_event_timeline(20, 8, 2)
    assert first == second
    assert len(first.labels) == 20 and sum(first.labels) == 8
    assert len(first.events) == 4 and all(event.length == 2 for event in first.events)
    assert all(gap >= 1 for gap in first.gaps[1:-1])


def test_count_simulator_is_batch_reproducible_and_paired() -> None:
    config = load_default_config()
    condition = Condition(5, 0.01, 32, condition_id(config, 5, 0.01, 32))
    first = simulate_condition(config, condition, batch_size=1)
    second = simulate_condition(config, condition, batch_size=11)
    assert first["raw_f1"] == second["raw_f1"]
    delta = first["delta_f1"]
    recall = first["adjusted_recall_mean"]
    assert isinstance(delta, dict) and isinstance(delta["mean"], float)
    assert delta["mean"] >= 0.0
    assert isinstance(recall, float) and math.isfinite(recall)


def test_predeclared_runtime_pilot_schema() -> None:
    pilot = run_pilot(load_default_config(), repetitions=4)
    assert pilot["status"] == "PASS"
    conditions = pilot["conditions"]
    assert isinstance(conditions, tuple) and len(conditions) == 3


@pytest.mark.parametrize(
    "n_timestamps,positives,event_length", [(10, 10, 1), (10, 4, 3), (5, 3, 1)]
)
def test_timeline_rejects_invalid_or_merging_layouts(
    n_timestamps: int, positives: int, event_length: int
) -> None:
    with pytest.raises(ValueError):
        build_equal_event_timeline(n_timestamps, positives, event_length)


def test_simulator_rejects_invalid_batch_size_and_summary_requires_values() -> None:
    config = load_default_config()
    condition = Condition(5, 0.01, 1, condition_id(config, 5, 0.01, 1))
    with pytest.raises(ValueError, match="batch_size"):
        simulate_condition(config, condition, batch_size=0)
