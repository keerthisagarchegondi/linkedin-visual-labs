"""Real Criteo multi-touch attribution for Project 4 Step 7."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, cast

import numpy as np
import pandas as pd

SOURCE_DATASET: Final[str] = "CRITEO_ATTRIBUTION"

EVIDENCE_CLASS: Final[str] = "ANONYMIZED_MEDIA_ATTRIBUTION_EVIDENCE"

CAUSAL_INTERPRETATION: Final[str] = "DESCRIPTIVE_ATTRIBUTION_NOT_CAUSAL_INCREMENTALITY"

EXPECTED_SAMPLE_ROWS: Final[int] = 1_996_592
EXPECTED_RAW_CONVERSION_IDS: Final[int] = 83_059
EXPECTED_CONVERSION_EVENTS: Final[int] = 83_155

LOOKBACK_DAYS: Final[int] = 30
SECONDS_PER_DAY: Final[int] = 86_400

TIME_DECAY_HALF_LIFE_DAYS: Final[float] = 7.0

POSITION_FIRST_SHARE: Final[float] = 0.40
POSITION_LAST_SHARE: Final[float] = 0.40
POSITION_MIDDLE_SHARE: Final[float] = 0.20

ATTRIBUTION_METHODS: Final[tuple[str, ...]] = (
    "FIRST_TOUCH",
    "LAST_TOUCH",
    "LINEAR",
    "POSITION_BASED",
    "TIME_DECAY",
)

JOURNEY_KEY_COLUMNS: Final[tuple[str, str]] = (
    "media_user_id",
    "conversion_id",
)


@dataclass(frozen=True)
class AttributionOutputs:
    """Recruiter-facing Step 7 attribution evidence."""

    attribution_comparison: pd.DataFrame
    attribution_method_sensitivity: pd.DataFrame
    metadata: dict[str, object]


def _int_scalar(value: object) -> int:
    return int(cast(Any, value))


def _float_scalar(value: object) -> float:
    return float(cast(Any, value))


def canonicalize_attribution_source(
    source: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_SAMPLE_ROWS,
) -> pd.DataFrame:
    """Validate the normalized real Criteo attribution source."""

    required = {
        "timestamp",
        "media_user_id",
        "campaign",
        "conversion",
        "conversion_timestamp",
        "conversion_id",
        "click",
        "cost",
    }

    missing = sorted(required - {str(column) for column in source.columns})

    if missing:
        raise ValueError(f"Criteo attribution schema missing: {missing}")

    if expected_rows is not None and len(source) != expected_rows:
        raise ValueError(
            f"Frozen Criteo row count changed: expected={expected_rows}, observed={len(source)}"
        )

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

    if frame["media_user_id"].isna().any():
        raise ValueError("media_user_id contains null values.")

    if not set(frame["click"].astype(int).unique()).issubset({0, 1}):
        raise ValueError("click is not binary.")

    if not set(frame["conversion"].astype(int).unique()).issubset({0, 1}):
        raise ValueError("conversion is not binary.")

    if (frame["cost"] < 0).any():
        raise ValueError("Media Cost Index contains negative values.")

    frame["_source_row"] = np.arange(
        len(frame),
        dtype=np.int64,
    )

    return frame


def reconstruct_journeys(
    source: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_SAMPLE_ROWS,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Reconstruct proven real Criteo conversion journeys."""

    frame = canonicalize_attribution_source(
        source,
        expected_rows=expected_rows,
    )

    frame = frame.sort_values(
        [
            "media_user_id",
            "timestamp",
            "_source_row",
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    converted = frame.loc[(frame["conversion"] == 1) & (frame["conversion_id"] >= 0)].copy()

    if converted.empty:
        raise ValueError("No real conversion evidence found.")

    raw_conversion_ids = int(converted["conversion_id"].nunique())

    conversion_events = converted[
        [
            "media_user_id",
            "conversion_id",
            "conversion_timestamp",
        ]
    ].drop_duplicates()

    composite_event_count = len(conversion_events)

    if expected_rows == EXPECTED_SAMPLE_ROWS and raw_conversion_ids != EXPECTED_RAW_CONVERSION_IDS:
        raise ValueError("Raw conversion-id count changed.")

    if (
        expected_rows == EXPECTED_SAMPLE_ROWS
        and composite_event_count != EXPECTED_CONVERSION_EVENTS
    ):
        raise ValueError("Composite conversion-event count changed.")

    timestamps_per_journey = converted.groupby(
        list(JOURNEY_KEY_COLUMNS),
        sort=False,
    )["conversion_timestamp"].nunique()

    if (timestamps_per_journey != 1).any():
        raise ValueError("Composite journey key maps to multiple conversion timestamps.")

    age_seconds = converted["conversion_timestamp"] - converted["timestamp"]

    if (age_seconds < 0).any():
        raise ValueError("Conversion-linked impression occurs after conversion.")

    eligible = converted.loc[age_seconds <= LOOKBACK_DAYS * SECONDS_PER_DAY].copy()

    eligible["_age_days"] = (
        eligible["conversion_timestamp"] - eligible["timestamp"]
    ) / SECONDS_PER_DAY

    eligible_events = eligible[
        [
            "media_user_id",
            "conversion_id",
        ]
    ].drop_duplicates()

    if len(eligible_events) != composite_event_count:
        raise ValueError("30-day lookback drops one or more real conversion events.")

    eligible = eligible.sort_values(
        [
            "media_user_id",
            "conversion_id",
            "timestamp",
            "_source_row",
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    eligible["journey_id"] = (
        eligible["media_user_id"].astype("string")
        + "::"
        + eligible["conversion_id"].astype("int64").astype("string")
    )

    eligible["touch_position"] = (
        eligible.groupby(
            list(JOURNEY_KEY_COLUMNS),
            sort=False,
        )
        .cumcount()
        .astype(int)
    )

    eligible["touch_count"] = (
        eligible.groupby(
            list(JOURNEY_KEY_COLUMNS),
            sort=False,
        )["conversion_id"]
        .transform("size")
        .astype(int)
    )

    journey_summary = (
        eligible.groupby(
            list(JOURNEY_KEY_COLUMNS),
            sort=True,
        )
        .agg(
            conversion_timestamp=(
                "conversion_timestamp",
                "first",
            ),
            first_touch_timestamp=(
                "timestamp",
                "min",
            ),
            last_touch_timestamp=(
                "timestamp",
                "max",
            ),
            touch_count=(
                "timestamp",
                "size",
            ),
        )
        .reset_index()
    )

    if (journey_summary["last_touch_timestamp"] > journey_summary["conversion_timestamp"]).any():
        raise ValueError("Journey contains a post-conversion touch.")

    all_users = set(frame["media_user_id"].unique())

    converting_users = set(converted["media_user_id"].unique())

    nonconverting_users = all_users - converting_users

    touch_counts = journey_summary["touch_count"]

    metadata: dict[str, object] = {
        "source_dataset": SOURCE_DATASET,
        "evidence_class": EVIDENCE_CLASS,
        "causal_interpretation": CAUSAL_INTERPRETATION,
        "source_rows": len(frame),
        "source_unique_users": len(all_users),
        "real_converting_users": len(converting_users),
        "real_nonconverting_users": len(nonconverting_users),
        "raw_unique_conversion_ids": raw_conversion_ids,
        "real_conversion_events": composite_event_count,
        "journey_key_columns": list(JOURNEY_KEY_COLUMNS),
        "journey_key_policy": (
            "media_user_id + conversion_id; proven to determine exactly one conversion_timestamp"
        ),
        "raw_conversion_id_reuse_count": (composite_event_count - raw_conversion_ids),
        "lookback_days": LOOKBACK_DAYS,
        "eligible_conversion_events": len(eligible_events),
        "eligible_touch_rows": len(eligible),
        "one_touch_journeys": int((touch_counts == 1).sum()),
        "two_touch_journeys": int((touch_counts == 2).sum()),
        "three_plus_touch_journeys": int((touch_counts >= 3).sum()),
        "touch_count_mean": float(touch_counts.mean()),
        "touch_count_max": int(touch_counts.max()),
        "conversion_cutoff_policy": ("only touches at or before the source conversion timestamp"),
        "nonconverter_policy": (
            "identified from real Criteo users and receives zero conversion attribution credit"
        ),
        "source_attribution_field_policy": (
            "source attribution field is not used by the five Project 4 attribution methods"
        ),
    }

    return eligible, metadata


def _journey_group_key(
    touches: pd.DataFrame,
) -> pd.Series:
    return touches["journey_id"]


def _first_touch_weights(
    touches: pd.DataFrame,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    weights = (touches["touch_position"].to_numpy(dtype=int) == 0).astype(np.float64)

    return cast(
        np.ndarray[Any, np.dtype[np.float64]],
        weights,
    )


def _last_touch_weights(
    touches: pd.DataFrame,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    position = touches["touch_position"].to_numpy(dtype=int)

    count = touches["touch_count"].to_numpy(dtype=int)

    weights = (position == count - 1).astype(np.float64)

    return cast(
        np.ndarray[Any, np.dtype[np.float64]],
        weights,
    )


def _linear_weights(
    touches: pd.DataFrame,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    count = touches["touch_count"].to_numpy(dtype=np.float64)

    weights = 1.0 / count

    return cast(
        np.ndarray[Any, np.dtype[np.float64]],
        weights,
    )


def _position_based_weights(
    touches: pd.DataFrame,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    position = touches["touch_position"].to_numpy(dtype=int)

    count = touches["touch_count"].to_numpy(dtype=int)

    weights = np.zeros(
        len(touches),
        dtype=np.float64,
    )

    one = count == 1
    two = count == 2
    multi = count >= 3

    weights[one] = 1.0
    weights[two] = 0.5

    first = multi & (position == 0)

    last = multi & (position == count - 1)

    middle = multi & ~first & ~last

    weights[first] = POSITION_FIRST_SHARE
    weights[last] = POSITION_LAST_SHARE

    weights[middle] = POSITION_MIDDLE_SHARE / (count[middle] - 2)

    return cast(
        np.ndarray[Any, np.dtype[np.float64]],
        weights,
    )


def _time_decay_weights(
    touches: pd.DataFrame,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    age_days = touches["_age_days"].to_numpy(dtype=np.float64)

    raw = np.power(
        0.5,
        age_days / TIME_DECAY_HALF_LIFE_DAYS,
    )

    raw_series = pd.Series(
        raw,
        index=touches.index,
        dtype=float,
    )

    denominator = (
        raw_series.groupby(
            _journey_group_key(touches),
            sort=False,
        )
        .transform("sum")
        .to_numpy(dtype=np.float64)
    )

    if (denominator <= 0).any():
        raise ValueError("Invalid time-decay denominator.")

    weights = raw / denominator

    return cast(
        np.ndarray[Any, np.dtype[np.float64]],
        weights,
    )


def attribution_weights(
    touches: pd.DataFrame,
    method: str,
) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Generic deterministic attribution protocol."""

    if method == "FIRST_TOUCH":
        return _first_touch_weights(touches)

    if method == "LAST_TOUCH":
        return _last_touch_weights(touches)

    if method == "LINEAR":
        return _linear_weights(touches)

    if method == "POSITION_BASED":
        return _position_based_weights(touches)

    if method == "TIME_DECAY":
        return _time_decay_weights(touches)

    raise ValueError(f"Unsupported attribution method: {method}")


def _validate_weights(
    touches: pd.DataFrame,
    weights: np.ndarray[Any, np.dtype[np.float64]],
    *,
    method: str,
) -> None:
    if len(weights) != len(touches):
        raise ValueError(f"{method} returned wrong weight count.")

    if not np.isfinite(weights).all():
        raise ValueError(f"{method} produced non-finite weights.")

    if (weights < -1e-12).any():
        raise ValueError(f"{method} produced negative weights.")

    totals = (
        pd.Series(
            weights,
            index=touches.index,
            dtype=float,
        )
        .groupby(
            _journey_group_key(touches),
            sort=False,
        )
        .sum()
    )

    if not np.allclose(
        totals.to_numpy(dtype=float),
        1.0,
        rtol=1e-10,
        atol=1e-10,
    ):
        raise ValueError(f"{method} weights do not conserve to one per journey.")


def _campaign_credit(
    touches: pd.DataFrame,
    *,
    method: str,
) -> pd.DataFrame:
    weights = attribution_weights(
        touches,
        method,
    )

    _validate_weights(
        touches,
        weights,
        method=method,
    )

    credit = pd.DataFrame(
        {
            "campaign_id": touches["campaign"].astype("string"),
            "attributed_conversion_credit": weights,
        }
    )

    grouped_credit = credit.groupby(
        "campaign_id",
        sort=True,
    )["attributed_conversion_credit"].sum()

    campaign = pd.DataFrame(
        {
            "campaign_id": grouped_credit.index.astype("string"),
            "attributed_conversion_credit": (grouped_credit.to_numpy(dtype=float)),
        }
    )

    journey_count = int(touches["journey_id"].nunique())

    total_credit = _float_scalar(campaign["attributed_conversion_credit"].sum())

    if not np.isclose(
        total_credit,
        float(journey_count),
        rtol=1e-10,
        atol=1e-8,
    ):
        raise ValueError(f"{method} campaign credit does not reconcile.")

    campaign["method"] = method

    campaign["attribution_share"] = campaign["attributed_conversion_credit"] / total_credit

    campaign["campaign_rank"] = (
        campaign["attributed_conversion_credit"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    campaign["source_dataset"] = SOURCE_DATASET
    campaign["evidence_class"] = EVIDENCE_CLASS
    campaign["causal_interpretation"] = CAUSAL_INTERPRETATION

    result = campaign.reindex(
        columns=[
            "source_dataset",
            "evidence_class",
            "causal_interpretation",
            "method",
            "campaign_id",
            "attributed_conversion_credit",
            "attribution_share",
            "campaign_rank",
        ]
    ).copy()

    return result


def _build_sensitivity(
    comparison: pd.DataFrame,
) -> pd.DataFrame:
    pivot = comparison.pivot(
        index="campaign_id",
        columns="method",
        values="attributed_conversion_credit",
    ).fillna(0.0)

    missing = set(ATTRIBUTION_METHODS) - set(pivot.columns)

    if missing:
        raise ValueError(f"Missing attribution methods: {sorted(missing)}")

    pivot = pivot.loc[
        :,
        list(ATTRIBUTION_METHODS),
    ].copy()

    sensitivity = pivot.reset_index().rename(
        columns={
            "FIRST_TOUCH": "first_touch_credit",
            "LAST_TOUCH": "last_touch_credit",
            "LINEAR": "linear_credit",
            "POSITION_BASED": "position_based_credit",
            "TIME_DECAY": "time_decay_credit",
        }
    )

    credit_columns = [
        "first_touch_credit",
        "last_touch_credit",
        "linear_credit",
        "position_based_credit",
        "time_decay_credit",
    ]

    sensitivity["mean_method_credit"] = sensitivity[credit_columns].mean(axis=1)

    sensitivity["min_method_credit"] = sensitivity[credit_columns].min(axis=1)

    sensitivity["max_method_credit"] = sensitivity[credit_columns].max(axis=1)

    sensitivity["method_credit_range"] = (
        sensitivity["max_method_credit"] - sensitivity["min_method_credit"]
    )

    sensitivity["method_credit_std"] = sensitivity[credit_columns].std(
        axis=1,
        ddof=0,
    )

    sensitivity["first_vs_last_shift"] = (
        sensitivity["last_touch_credit"] - sensitivity["first_touch_credit"]
    )

    sensitivity["absolute_first_vs_last_shift"] = sensitivity["first_vs_last_shift"].abs()

    sensitivity["channel_credit_sensitivity"] = np.where(
        sensitivity["mean_method_credit"] > 0,
        sensitivity["method_credit_range"] / sensitivity["mean_method_credit"],
        0.0,
    )

    sensitivity["source_dataset"] = SOURCE_DATASET
    sensitivity["evidence_class"] = EVIDENCE_CLASS
    sensitivity["causal_interpretation"] = CAUSAL_INTERPRETATION

    result = sensitivity.loc[
        :,
        [
            "source_dataset",
            "evidence_class",
            "causal_interpretation",
            "campaign_id",
            "first_touch_credit",
            "last_touch_credit",
            "linear_credit",
            "position_based_credit",
            "time_decay_credit",
            "first_vs_last_shift",
            "absolute_first_vs_last_shift",
            "mean_method_credit",
            "min_method_credit",
            "max_method_credit",
            "method_credit_range",
            "method_credit_std",
            "channel_credit_sensitivity",
        ],
    ].copy()

    result = result.sort_values(
        [
            "channel_credit_sensitivity",
            "campaign_id",
        ],
        ascending=[
            False,
            True,
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    return result


def build_attribution_outputs(
    source: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_SAMPLE_ROWS,
) -> AttributionOutputs:
    """Run all five methods on real Criteo conversion events."""

    touches, journey_metadata = reconstruct_journeys(
        source,
        expected_rows=expected_rows,
    )

    campaign_frames = [
        _campaign_credit(
            touches,
            method=method,
        )
        for method in ATTRIBUTION_METHODS
    ]

    comparison = (
        pd.concat(
            campaign_frames,
            ignore_index=True,
        )
        .sort_values(
            [
                "method",
                "campaign_rank",
                "campaign_id",
            ],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    journey_count = int(touches["journey_id"].nunique())

    method_totals = comparison.groupby(
        "method",
        sort=True,
    )["attributed_conversion_credit"].sum()

    if set(method_totals.index) != set(ATTRIBUTION_METHODS):
        raise ValueError("Exactly five methods were not produced.")

    if not np.allclose(
        method_totals.to_numpy(dtype=float),
        float(journey_count),
        rtol=1e-10,
        atol=1e-8,
    ):
        raise ValueError("Method totals do not reconcile.")

    sensitivity = _build_sensitivity(comparison)

    sensitivity_map = {
        "FIRST_TOUCH": "first_touch_credit",
        "LAST_TOUCH": "last_touch_credit",
        "LINEAR": "linear_credit",
        "POSITION_BASED": "position_based_credit",
        "TIME_DECAY": "time_decay_credit",
    }

    for method, column in sensitivity_map.items():
        if not np.isclose(
            _float_scalar(sensitivity[column].sum()),
            float(journey_count),
            rtol=1e-10,
            atol=1e-8,
        ):
            raise ValueError(f"Sensitivity does not reconcile for {method}.")

    # --------------------------------------------------------
    # Real journey-topology sensitivity evidence.
    #
    # Attribution methods can differ at touch level while
    # collapsing to identical campaign credit when every
    # multi-touch journey stays inside one campaign.
    # --------------------------------------------------------

    journey_touch_counts = touches.groupby(
        "journey_id",
        sort=False,
    ).size()

    journey_campaign_counts = touches.groupby(
        "journey_id",
        sort=False,
    )["campaign"].nunique()

    first_campaign = (
        touches.groupby(
            "journey_id",
            sort=False,
        )["campaign"]
        .first()
        .astype("string")
    )

    last_campaign = (
        touches.groupby(
            "journey_id",
            sort=False,
        )["campaign"]
        .last()
        .astype("string")
    )

    multi_touch_journeys = _int_scalar((journey_touch_counts > 1).sum())

    cross_campaign_journeys = _int_scalar((journey_campaign_counts > 1).sum())

    same_campaign_multi_touch_journeys = _int_scalar(
        ((journey_touch_counts > 1) & (journey_campaign_counts == 1)).sum()
    )

    first_last_campaign_different_journeys = _int_scalar((first_campaign != last_campaign).sum())

    campaigns_with_method_sensitivity = _int_scalar(
        (sensitivity["method_credit_range"] > 1e-12).sum()
    )

    campaigns_with_first_last_shift = _int_scalar(
        (sensitivity["absolute_first_vs_last_shift"] > 1e-12).sum()
    )

    max_method_credit_range = _float_scalar(sensitivity["method_credit_range"].max())

    max_absolute_first_last_shift = _float_scalar(sensitivity["absolute_first_vs_last_shift"].max())

    if cross_campaign_journeys == 0:
        if (
            campaigns_with_method_sensitivity != 0
            or campaigns_with_first_last_shift != 0
            or not np.isclose(
                max_method_credit_range,
                0.0,
                atol=1e-12,
            )
            or not np.isclose(
                max_absolute_first_last_shift,
                0.0,
                atol=1e-12,
            )
        ):
            raise ValueError("Campaign sensitivity exists despite zero cross-campaign journeys.")

        method_sensitivity_status = "MEASURED_ZERO_NO_CROSS_CAMPAIGN_PATHS"

    elif campaigns_with_method_sensitivity > 0:
        method_sensitivity_status = "MEASURED_NONZERO_CROSS_CAMPAIGN_PATHS"

    else:
        method_sensitivity_status = "MEASURED_ZERO_AGGREGATE_CANCELLATION"

    sensitivity["method_sensitivity_status"] = method_sensitivity_status

    sensitivity["method_sensitivity_policy"] = "MEASURED_NOT_REQUIRED_NONZERO"

    sensitivity["cross_campaign_journey_count"] = cross_campaign_journeys

    sensitivity["multi_touch_journey_count"] = multi_touch_journeys

    metadata: dict[str, object] = {
        **journey_metadata,
        "attribution_methods": list(ATTRIBUTION_METHODS),
        "attribution_method_count": len(ATTRIBUTION_METHODS),
        "position_based_policy": {
            "one_touch": "100%",
            "two_touch": "50% / 50%",
            "three_plus_first_share": (POSITION_FIRST_SHARE),
            "three_plus_last_share": (POSITION_LAST_SHARE),
            "three_plus_middle_share": (POSITION_MIDDLE_SHARE),
        },
        "time_decay_half_life_days": (TIME_DECAY_HALF_LIFE_DAYS),
        "time_decay_policy": (
            "0.5 ** (days_before_conversion / 7), normalized within composite conversion event"
        ),
        "generic_attribution_protocol": (
            "each method allocates exactly one descriptive "
            "conversion credit per proven real conversion event"
        ),
        "synthetic_fixture_policy": ("tiny deterministic fixtures are test-only"),
        "synthetic_recruiter_facing_rows": 0,
        "recruiter_facing_evidence": ("real frozen Criteo media journeys only"),
        "causal_separation_policy": (
            "descriptive media attribution remains distinct from Step 5 randomized incrementality"
        ),
        "method_total_credit": {
            method: float(method_totals.loc[method]) for method in ATTRIBUTION_METHODS
        },
        "campaign_count": int(sensitivity["campaign_id"].nunique()),
        "multi_touch_journeys": (multi_touch_journeys),
        "same_campaign_multi_touch_journeys": (same_campaign_multi_touch_journeys),
        "cross_campaign_journeys": (cross_campaign_journeys),
        "first_last_campaign_different_journeys": (first_last_campaign_different_journeys),
        "campaigns_with_method_sensitivity": (campaigns_with_method_sensitivity),
        "campaigns_with_first_last_shift": (campaigns_with_first_last_shift),
        "max_method_credit_range": (max_method_credit_range),
        "max_absolute_first_last_shift": (max_absolute_first_last_shift),
        "method_sensitivity_status": (method_sensitivity_status),
        "method_sensitivity_policy": ("MEASURED_NOT_REQUIRED_NONZERO"),
        "method_sensitivity_interpretation": (
            "campaign-level method differences are measured rather "
            "than required to be nonzero; zero sensitivity is valid "
            "when real multi-touch journeys do not cross campaigns"
        ),
    }

    return AttributionOutputs(
        attribution_comparison=comparison,
        attribution_method_sensitivity=sensitivity,
        metadata=metadata,
    )
