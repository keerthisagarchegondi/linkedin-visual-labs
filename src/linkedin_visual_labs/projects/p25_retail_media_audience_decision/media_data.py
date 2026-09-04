"""Criteo media-performance layer for Project 4 Step 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, cast

import numpy as np
import pandas as pd

SOURCE_DATASET: Final[str] = "CRITEO_ATTRIBUTION"

EVIDENCE_CLASS: Final[str] = "ANONYMIZED_MEDIA_IMPRESSION_EVIDENCE"

COST_METRIC_LABEL: Final[str] = "Media Cost Index"

TIME_AXIS_TYPE: Final[str] = "SOURCE_RELATIVE_DAY"

EXPECTED_SAMPLE_ROWS: Final[int] = 1_996_592


@dataclass(frozen=True)
class MediaFrames:
    """Governed Criteo KPI and time-series frames."""

    media_kpis: pd.DataFrame
    media_timeseries: pd.DataFrame
    metadata: dict[str, object]


def _safe_rate(
    numerator: float,
    denominator: float,
) -> float:
    if denominator <= 0:
        return 0.0

    return float(numerator / denominator)


def _int_scalar(
    value: object,
) -> int:
    return int(
        cast(
            Any,
            value,
        )
    )


def _float_scalar(
    value: object,
) -> float:
    return float(
        cast(
            Any,
            value,
        )
    )


def canonicalize_criteo(
    source: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and normalize the required Criteo fields."""

    required = {
        "timestamp",
        "campaign",
        "conversion",
        "conversion_timestamp",
        "conversion_id",
        "click",
        "cost",
    }

    missing = sorted(required - {str(column) for column in source.columns})

    if missing:
        raise ValueError(f"Criteo normalized schema missing fields: {missing}")

    frame = source.copy()

    for column in (
        "timestamp",
        "conversion",
        "conversion_timestamp",
        "conversion_id",
        "click",
        "cost",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    return frame


def validate_criteo(
    frame: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_SAMPLE_ROWS,
) -> dict[str, object]:
    """Validate source semantics without inventing journey relationships."""

    if expected_rows is not None and len(frame) != expected_rows:
        raise ValueError(
            "Frozen Criteo sample row count changed: "
            f"expected={expected_rows}, observed={len(frame)}"
        )

    click_values = set(frame["click"].dropna().astype(int).unique())

    if not click_values.issubset(
        {
            0,
            1,
        }
    ):
        raise ValueError("Criteo click indicator is not binary.")

    conversion_values = set(frame["conversion"].dropna().astype(int).unique())

    if not conversion_values.issubset(
        {
            0,
            1,
        }
    ):
        raise ValueError("Criteo conversion indicator is not binary.")

    clicks = _int_scalar(frame["click"].sum())

    if clicks > len(frame):
        raise ValueError("Criteo clicks exceed impressions.")

    converted = frame.loc[frame["conversion"] == 1]

    if converted.empty:
        raise ValueError("Criteo contains no conversion evidence.")

    if (converted["conversion_id"] < 0).any():
        raise ValueError("Converted rows contain invalid conversion_id.")

    if (converted["conversion_timestamp"] < converted["timestamp"]).any():
        raise ValueError("A Criteo conversion precedes its impression timestamp.")

    cost = frame["cost"].to_numpy(dtype=float)

    if not np.isfinite(cost).all():
        raise ValueError("Media Cost Index contains non-finite values.")

    if (cost < 0).any():
        raise ValueError("Media Cost Index contains negative values.")

    return {
        "sample_row_count": len(frame),
        "binary_click_indicator": True,
        "binary_conversion_indicator": True,
        "clicks_not_greater_than_impressions": True,
        "conversion_timestamp_not_before_impression": True,
        "cost_nonnegative_and_finite": True,
        "source_timestamp_monotonic": bool(frame["timestamp"].is_monotonic_increasing),
    }


def unique_conversion_count(
    frame: pd.DataFrame,
) -> int:
    """Count unique conversion IDs, not repeated impression links."""

    converted = frame.loc[(frame["conversion"] == 1) & (frame["conversion_id"] >= 0)]

    return int(converted["conversion_id"].nunique())


def _media_record(
    frame: pd.DataFrame,
    *,
    aggregation_level: str,
    campaign_id: str,
    conversion_label: str,
    conversion_additivity: str,
) -> dict[str, object]:
    impressions = len(frame)

    clicks = _int_scalar(frame["click"].sum())

    conversions = unique_conversion_count(frame)

    cost = _float_scalar(frame["cost"].sum())

    return {
        "source_dataset": SOURCE_DATASET,
        "evidence_class": EVIDENCE_CLASS,
        "aggregation_level": aggregation_level,
        "campaign_id": campaign_id,
        "impression_count": impressions,
        "click_count": clicks,
        "ctr": _safe_rate(
            clicks,
            impressions,
        ),
        "conversion_count": conversions,
        "conversion_rate_per_impression": _safe_rate(
            conversions,
            impressions,
        ),
        "conversion_rate_per_click": _safe_rate(
            conversions,
            clicks,
        ),
        "media_cost_index": cost,
        "cost_metric_label": COST_METRIC_LABEL,
        "media_cost_index_per_conversion": _safe_rate(
            cost,
            conversions,
        ),
        "conversion_evidence_label": conversion_label,
        "campaign_conversion_additivity": conversion_additivity,
    }


def build_media_frames(
    source: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_SAMPLE_ROWS,
) -> MediaFrames:
    """Build overall, campaign, and source-relative media evidence."""

    frame = canonicalize_criteo(source)

    validation = validate_criteo(
        frame,
        expected_rows=expected_rows,
    )

    overall = _media_record(
        frame,
        aggregation_level="OVERALL",
        campaign_id="__ALL__",
        conversion_label=("DEDUPLICATED_UNIQUE_CONVERSION_ID_OVERALL"),
        conversion_additivity=("NOT_APPLICABLE_OVERALL"),
    )

    campaign_records: list[dict[str, object]] = []

    for campaign, group in frame.groupby(
        "campaign",
        sort=True,
        dropna=False,
    ):
        campaign_records.append(
            _media_record(
                group,
                aggregation_level="CAMPAIGN",
                campaign_id=str(campaign),
                conversion_label=("UNIQUE_CONVERSION_ID_LINKED_TO_CAMPAIGN_IMPRESSIONS"),
                conversion_additivity=("NON_ADDITIVE_ACROSS_CAMPAIGNS"),
            )
        )

    media_kpis = pd.concat(
        [
            pd.DataFrame([overall]),
            pd.DataFrame(campaign_records),
        ],
        ignore_index=True,
    )

    frame["_impression_day"] = np.floor(frame["timestamp"] / 86400.0).astype(int)

    impression_series = (
        frame.groupby(
            "_impression_day",
            sort=True,
        )
        .agg(
            impression_count=(
                "timestamp",
                "size",
            ),
            click_count=(
                "click",
                "sum",
            ),
            media_cost_index=(
                "cost",
                "sum",
            ),
        )
        .reset_index()
        .rename(columns={"_impression_day": ("source_relative_day")})
    )

    conversion_events = (
        frame.loc[
            (frame["conversion"] == 1) & (frame["conversion_id"] >= 0),
            [
                "conversion_id",
                "conversion_timestamp",
            ],
        ]
        .sort_values(
            [
                "conversion_id",
                "conversion_timestamp",
            ],
            kind="mergesort",
        )
        .drop_duplicates(
            subset=["conversion_id"],
            keep="first",
        )
        .copy()
    )

    conversion_events["source_relative_day"] = np.floor(
        conversion_events["conversion_timestamp"] / 86400.0
    ).astype(int)

    conversion_series = (
        conversion_events.groupby(
            "source_relative_day",
            sort=True,
        )["conversion_id"]
        .nunique()
        .rename("conversion_completion_count")
        .reset_index()
    )

    media_timeseries = (
        impression_series.merge(
            conversion_series,
            on="source_relative_day",
            how="outer",
            validate="one_to_one",
        )
        .fillna(0)
        .sort_values(
            "source_relative_day",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    for column in (
        "impression_count",
        "click_count",
        "conversion_completion_count",
    ):
        media_timeseries[column] = media_timeseries[column].astype(int)

    media_timeseries["ctr"] = np.where(
        media_timeseries["impression_count"] > 0,
        media_timeseries["click_count"] / media_timeseries["impression_count"],
        0.0,
    )

    media_timeseries["source_dataset"] = SOURCE_DATASET

    media_timeseries["evidence_class"] = EVIDENCE_CLASS

    media_timeseries["time_axis_type"] = TIME_AXIS_TYPE

    media_timeseries["cost_metric_label"] = COST_METRIC_LABEL

    media_timeseries["conversion_time_basis"] = "CONVERSION_COMPLETION_TIMESTAMP"

    media_timeseries["daily_conversion_rate_policy"] = "NOT_COMPUTED_MIXED_EVENT_TIME_DENOMINATOR"

    overall_impressions = _int_scalar(overall["impression_count"])

    overall_clicks = _int_scalar(overall["click_count"])

    overall_conversions = _int_scalar(overall["conversion_count"])

    overall_cost = _float_scalar(overall["media_cost_index"])

    if _int_scalar(media_timeseries["impression_count"].sum()) != overall_impressions:
        raise ValueError("Media time-series impressions do not reconcile.")

    if _int_scalar(media_timeseries["click_count"].sum()) != overall_clicks:
        raise ValueError("Media time-series clicks do not reconcile.")

    if _int_scalar(media_timeseries["conversion_completion_count"].sum()) != overall_conversions:
        raise ValueError("Media conversion-completion series does not reconcile.")

    if not np.isclose(
        _float_scalar(media_timeseries["media_cost_index"].sum()),
        overall_cost,
        rtol=1e-12,
        atol=1e-9,
    ):
        raise ValueError("Media Cost Index time series does not reconcile.")

    campaigns = media_kpis.loc[media_kpis["aggregation_level"] == "CAMPAIGN"]

    if _int_scalar(campaigns["impression_count"].sum()) != overall_impressions:
        raise ValueError("Campaign impressions do not reconcile.")

    if _int_scalar(campaigns["click_count"].sum()) != overall_clicks:
        raise ValueError("Campaign clicks do not reconcile.")

    if not np.isclose(
        _float_scalar(campaigns["media_cost_index"].sum()),
        overall_cost,
        rtol=1e-12,
        atol=1e-9,
    ):
        raise ValueError("Campaign Media Cost Index does not reconcile.")

    metadata: dict[str, object] = {
        "source_dataset": SOURCE_DATASET,
        "evidence_class": EVIDENCE_CLASS,
        "impression_definition": ("one normalized Criteo row / displayed impression"),
        "click_definition": ("binary clicked-impression indicator"),
        "overall_conversion_definition": (
            "unique conversion_id among conversion-linked impressions"
        ),
        "campaign_conversion_policy": ("non-additive across campaigns"),
        "conversion_rate_primary_label": ("conversion rate per impression"),
        "conversion_rate_secondary_label": ("conversion rate per click"),
        "cost_metric_label": COST_METRIC_LABEL,
        "cost_semantics": ("transformed source cost index; not currency, spend, CPA, or ROAS"),
        "time_axis_type": TIME_AXIS_TYPE,
        "validation": validation,
    }

    metadata["media_timeseries_semantics"] = {
        "impression_count": ("displayed impressions bucketed by impression timestamp"),
        "click_count": ("clicked impressions bucketed by impression timestamp"),
        "media_cost_index": ("transformed cost bucketed by impression timestamp"),
        "conversion_completion_count": (
            "deduplicated unique conversions bucketed by conversion completion timestamp"
        ),
        "ctr": ("clicks / impressions; numerator and denominator share impression timestamp basis"),
    }

    metadata["daily_conversion_rate_policy"] = (
        "not computed because conversion completions use conversion "
        "timestamps while impressions/clicks use impression timestamps; "
        "same-day division would mix event-time populations"
    )

    metadata["conversion_cohort_attribution_policy"] = "not invented in Step 6"

    return MediaFrames(
        media_kpis=media_kpis,
        media_timeseries=media_timeseries,
        metadata=metadata,
    )
