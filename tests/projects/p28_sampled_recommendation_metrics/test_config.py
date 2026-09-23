from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.config import (
    Project8Config,
    load_default_config,
)


def test_default_config_matches_frozen_contract() -> None:
    config = load_default_config()

    assert config.n_items == 10_000
    assert config.reference_negative_draws == 99
    assert config.source_protocol_repetitions == 1_000
    assert config.validation_repetitions == 10_000
    assert config.root_seed == 20260923


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("n_items", True),
        ("reference_negative_draws", 1.0),
        ("source_protocol_repetitions", False),
        ("validation_repetitions", 10.0),
        ("root_seed", 1.5),
    ],
)
def test_rejects_non_plain_integer_fields(
    field: str,
    value: object,
) -> None:
    kwargs = {
        "n_items": 10_000,
        "reference_negative_draws": 99,
        "source_protocol_repetitions": 1_000,
        "validation_repetitions": 10_000,
        "root_seed": 20260923,
        "sensitivity_grid_negative_draws": (1, 99),
    }

    kwargs[field] = value

    with pytest.raises(TypeError):
        Project8Config(**kwargs)


def test_rejects_unknown_config_key() -> None:
    with pytest.raises(ValueError, match="unknown config keys"):
        Project8Config.from_mapping(
            {
                "n_items": 10_000,
                "reference_negative_draws": 99,
                "source_protocol_repetitions": 1_000,
                "validation_repetitions": 10_000,
                "root_seed": 20260923,
                "sensitivity_grid_negative_draws": [1, 99],
                "unexpected": 1,
            }
        )
