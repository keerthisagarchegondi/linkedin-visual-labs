"""Classical ML feature tests."""

from __future__ import annotations

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityId,
    generate_city,
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_features import (
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    observable_features,
    showcase_feature_frame,
    validate_no_feature_leakage,
)


def test_true_risk_is_not_in_feature_contract() -> None:
    validate_no_feature_leakage()

    assert LABEL_COLUMN == "true_risk"

    assert LABEL_COLUMN not in FEATURE_COLUMNS


def test_showcase_feature_frame_contains_only_observable_features() -> None:
    config = load_zombie_config()

    city = generate_city(
        config,
        CityId.PHOENIX,
    )

    frame, positions = showcase_feature_frame(city)

    assert tuple(frame.columns) == FEATURE_COLUMNS

    assert len(frame) == len(positions)

    assert "true_risk" not in frame.columns


def test_feature_extraction_is_deterministic() -> None:
    config = load_zombie_config()

    city = generate_city(
        config,
        CityId.NEW_YORK,
    )

    position = city.traversable_positions()[100]

    assert observable_features(
        city,
        position,
    ) == observable_features(
        city,
        position,
    )
