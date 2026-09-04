from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.media_data import (
    COST_METRIC_LABEL,
    SOURCE_DATASET,
    build_media_frames,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)


def _fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [
                10,
                20,
                30,
                86410,
                86420,
            ],
            "campaign": [
                1,
                1,
                2,
                2,
                2,
            ],
            "conversion": [
                1,
                1,
                0,
                1,
                0,
            ],
            "conversion_timestamp": [
                100,
                100,
                -1,
                86500,
                -1,
            ],
            "conversion_id": [
                10,
                10,
                -1,
                20,
                -1,
            ],
            "click": [
                1,
                0,
                1,
                1,
                0,
            ],
            "cost": [
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
            ],
        }
    )


def test_media_kpis_reconcile() -> None:
    frames = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    overall = frames.media_kpis.loc[frames.media_kpis["aggregation_level"] == "OVERALL"].iloc[0]

    assert int(overall["impression_count"]) == 5

    assert int(overall["click_count"]) == 3

    assert int(overall["conversion_count"]) == 2

    assert np.isclose(
        float(overall["ctr"]),
        3.0 / 5.0,
    )

    assert np.isclose(
        float(overall["media_cost_index"]),
        15.0,
    )


def test_conversion_id_is_deduplicated() -> None:
    frames = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    overall = frames.media_kpis.iloc[0]

    assert int(overall["conversion_count"]) == 2


def test_media_cost_is_not_currency_labeled() -> None:
    frames = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    assert set(frames.media_kpis["cost_metric_label"]) == {COST_METRIC_LABEL}

    assert COST_METRIC_LABEL == ("Media Cost Index")


def test_time_series_reconciles_overall() -> None:
    frames = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    overall = frames.media_kpis.iloc[0]

    assert int(frames.media_timeseries["impression_count"].sum()) == int(
        overall["impression_count"]
    )

    assert int(frames.media_timeseries["click_count"].sum()) == int(overall["click_count"])

    assert int(frames.media_timeseries["conversion_count"].sum()) == int(
        overall["conversion_count"]
    )


def test_campaign_conversion_evidence_is_nonadditive() -> None:
    frames = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    campaigns = frames.media_kpis.loc[frames.media_kpis["aggregation_level"] == "CAMPAIGN"]

    assert campaigns["campaign_conversion_additivity"].eq("NON_ADDITIVE_ACROSS_CAMPAIGNS").all()


def test_conversion_before_impression_fails() -> None:
    frame = _fixture()

    frame.loc[
        0,
        "conversion_timestamp",
    ] = 1

    with pytest.raises(
        ValueError,
        match="precedes",
    ):
        build_media_frames(
            frame,
            expected_rows=None,
        )


def test_media_determinism() -> None:
    first = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    second = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    assert stable_frame_hash(first.media_kpis) == stable_frame_hash(second.media_kpis)

    assert stable_frame_hash(first.media_timeseries) == stable_frame_hash(second.media_timeseries)


def test_media_source_evidence_is_explicit() -> None:
    frames = build_media_frames(
        _fixture(),
        expected_rows=None,
    )

    assert set(frames.media_kpis["source_dataset"]) == {SOURCE_DATASET}

    assert SOURCE_DATASET == ("CRITEO_ATTRIBUTION")
