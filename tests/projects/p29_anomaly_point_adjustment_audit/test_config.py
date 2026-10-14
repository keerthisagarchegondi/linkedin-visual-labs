from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.config import (
    Project9Config,
    load_default_config,
)


def _values() -> dict[str, object]:
    return {
        field: getattr(load_default_config(), field)
        for field in Project9Config.__dataclass_fields__
    }


def test_canonical_config_is_frozen() -> None:
    config = load_default_config()
    assert (config.n_timestamps, config.anomalous_timestamps, config.prevalence) == (
        20_000,
        1_000,
        0.05,
    )
    assert config.primary_event_length == 200
    assert config.primary_alert_probability == 0.01


@pytest.mark.parametrize(
    "field,value",
    [("n_timestamps", 0), ("anomalous_timestamps", 20_000), ("initial_repetitions", 0)],
)
def test_invalid_integer_fields_fail(field: str, value: object) -> None:
    values = _values()
    values[field] = value
    with pytest.raises(ValueError):
        Project9Config(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field,value",
    [
        ("event_lengths", (1, 5, 5)),
        ("event_lengths", (1, 3)),
        ("alert_probabilities", (-0.1, 0.1)),
        ("alert_probabilities", (0.1, 1.1)),
    ],
)
def test_invalid_grids_fail(field: str, value: object) -> None:
    values = _values()
    values[field] = value
    with pytest.raises(ValueError):
        Project9Config(**values)  # type: ignore[arg-type]
