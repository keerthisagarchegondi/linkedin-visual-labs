"""Hillstrom normalization tests."""

from __future__ import annotations

import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters import (
    hillstrom,
)


def fixture_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    features = pd.DataFrame(
        {
            "recency": [2, 1, 3],
            "history": [100.0, 50.0, 75.0],
            "history_segment": [
                "100-200",
                "1-100",
                "1-100",
            ],
            "mens": [1, 0, 1],
            "womens": [0, 1, 0],
            "zip_code": [
                "Urban",
                "Rural",
                "Surburban",
            ],
            "newbie": [0, 1, 0],
            "channel": [
                "Phone",
                "Web",
                "Multichannel",
            ],
        }
    )

    targets = pd.DataFrame(
        {
            "visit": [1, 0, 1],
            "conversion": [1, 0, 0],
            "spend": [40.0, 0.0, 0.0],
        }
    )

    treatment = pd.Series(
        [
            "Mens E-Mail",
            "No E-Mail",
            "Womens E-Mail",
        ],
        name="segment",
    )

    return (
        features,
        targets,
        treatment,
    )


def test_hillstrom_normalization_is_deterministic() -> None:
    features, targets, treatment = fixture_data()

    first = hillstrom.normalize_hillstrom(
        features,
        targets,
        treatment,
    )

    second = hillstrom.normalize_hillstrom(
        features,
        targets,
        treatment,
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )

    assert first["anonymous_customer_id"].is_unique
    assert "customer_id" not in first.columns


def test_hillstrom_rejects_missing_column() -> None:
    features, targets, treatment = fixture_data()

    features = features.drop(
        columns=[
            "history",
        ]
    )

    with pytest.raises(
        ValueError,
        match="missing required columns",
    ):
        hillstrom.normalize_hillstrom(
            features,
            targets,
            treatment,
        )


def test_hillstrom_rejects_negative_spend() -> None:
    features, targets, treatment = fixture_data()

    targets.loc[
        0,
        "spend",
    ] = -1.0

    with pytest.raises(
        ValueError,
        match="spend must be nonnegative",
    ):
        hillstrom.normalize_hillstrom(
            features,
            targets,
            treatment,
        )
