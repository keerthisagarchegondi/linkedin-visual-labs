from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.funnel_data import (
    SOURCE_DATASET,
    build_funnel_frames,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "evidence_class": ["test"] * 10,
            "timestamp": np.arange(10),
            "visitor_id": [
                1,
                1,
                1,
                2,
                2,
                3,
                3,
                4,
                5,
                6,
            ],
            "event": [
                "view",
                "addtocart",
                "transaction",
                "view",
                "addtocart",
                "view",
                "transaction",
                "view",
                "view",
                "view",
            ],
            "item_id": [
                10,
                10,
                10,
                20,
                20,
                30,
                30,
                40,
                50,
                60,
            ],
            "transaction_id": [
                np.nan,
                np.nan,
                100,
                np.nan,
                np.nan,
                np.nan,
                200,
                np.nan,
                np.nan,
                np.nan,
            ],
        }
    )


def test_normalized_retailrocket_aliases_resolve() -> None:
    frames = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    schema = frames.metadata["source_schema"]

    assert isinstance(
        schema,
        dict,
    )

    assert schema["visitor"] == "visitor_id"

    assert schema["item"] == "item_id"

    assert schema["transaction"] == "transaction_id"


def test_funnel_counts_and_rates() -> None:
    frames = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    funnel = frames.conversion_funnel.set_index("stage")

    assert (
        int(
            cast(
                Any,
                funnel.loc[
                    "VIEW",
                    "event_count",
                ],
            )
        )
        == 6
    )

    assert (
        int(
            cast(
                Any,
                funnel.loc[
                    "ADD_TO_CART",
                    "event_count",
                ],
            )
        )
        == 2
    )

    assert (
        int(
            cast(
                Any,
                funnel.loc[
                    "TRANSACTION",
                    "event_count",
                ],
            )
        )
        == 2
    )

    assert np.isclose(
        float(
            cast(
                Any,
                funnel.loc[
                    "VIEW",
                    "view_to_cart_rate",
                ],
            )
        ),
        2.0 / 6.0,
    )

    assert np.isclose(
        float(
            cast(
                Any,
                funnel.loc[
                    "VIEW",
                    "view_to_transaction_rate",
                ],
            )
        ),
        2.0 / 6.0,
    )


def test_funnel_conserves_event_rows() -> None:
    frames = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    assert int(frames.conversion_funnel["event_count"].sum()) == len(_fixture())


def test_funnel_ordering() -> None:
    frames = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    counts = frames.conversion_funnel.sort_values("stage_order")["event_count"].to_numpy(dtype=int)

    assert counts[0] >= counts[1] >= counts[2]


def test_funnel_is_event_volume_not_person_probability() -> None:
    frames = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    assert frames.conversion_funnel["rate_basis"].eq("EVENT_VOLUME_RATIO").all()

    assert "not claimed as person-level sequential" in str(frames.metadata["rate_basis"])


def test_funnel_source_boundary_explicit() -> None:
    frames = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    assert set(frames.conversion_funnel["source_dataset"]) == {SOURCE_DATASET}

    assert SOURCE_DATASET == ("RETAILROCKET")

    assert "separate from Criteo" in str(frames.metadata["source_boundary_policy"])


def test_funnel_determinism() -> None:
    first = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    second = build_funnel_frames(
        _fixture(),
        expected_rows=None,
    )

    assert stable_frame_hash(first.conversion_funnel) == stable_frame_hash(second.conversion_funnel)
