"""Criteo and Retailrocket normalization tests."""

from __future__ import annotations

import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters import (
    criteo,
    retailrocket,
)


def test_criteo_chunk_normalizes() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [2, 1],
            "uid": [10, 9],
            "campaign": [3, 2],
            "conversion": [0, 1],
            "conversion_timestamp": [0, 5],
            "conversion_id": [0, 7],
            "attribution": [0, 1],
            "click": [0, 1],
            "cost": [0.2, 0.3],
            "cpo": [0.0, 1.2],
            "time_since_last_click": [4, 2],
        }
    )

    normalized = criteo.normalize_criteo_chunk(frame)

    assert "media_user_id" in normalized.columns
    assert "uid" not in normalized.columns
    assert "user_id" not in normalized.columns


def test_criteo_rejects_invalid_click() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [1],
            "uid": [9],
            "campaign": [2],
            "conversion": [0],
            "conversion_timestamp": [0],
            "conversion_id": [0],
            "attribution": [0],
            "click": [2],
            "cost": [0.2],
            "cpo": [0.0],
            "time_since_last_click": [4],
        }
    )

    with pytest.raises(
        ValueError,
        match="click must be binary",
    ):
        criteo.normalize_criteo_chunk(frame)


def retailrocket_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [
                3,
                1,
                2,
            ],
            "visitorid": [
                5,
                5,
                5,
            ],
            "event": [
                "transaction",
                "view",
                "addtocart",
            ],
            "itemid": [
                100,
                100,
                100,
            ],
            "transactionid": [
                7,
                None,
                None,
            ],
        }
    )


def test_retailrocket_normalizes_three_event_types() -> None:
    normalized = retailrocket.normalize_events(retailrocket_fixture())

    assert set(normalized["event"]) == {
        "view",
        "addtocart",
        "transaction",
    }

    assert list(normalized["timestamp"]) == [
        1,
        2,
        3,
    ]


def test_retailrocket_rejects_unknown_event() -> None:
    frame = retailrocket_fixture()

    frame.loc[
        0,
        "event",
    ] = "purchase"

    with pytest.raises(
        ValueError,
        match="Unexpected Retailrocket event",
    ):
        retailrocket.normalize_events(frame)
