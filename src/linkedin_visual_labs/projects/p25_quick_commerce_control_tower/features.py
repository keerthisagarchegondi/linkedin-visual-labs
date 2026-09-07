"""Direct-horizon features with explicit source windows; no fitting or prediction."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial

import pandas as pd

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    common_holdout,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import FeatureConfig

KNOWN_AT_ORIGIN = [
    "store_id",
    "category",
    "weekday",
    "month",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
    "snap",
]


@dataclass(frozen=True)
class FeatureSet:
    """Separate predictors/labels and explicit historical provenance for the common holdout."""

    training: pd.DataFrame
    holdout: pd.DataFrame
    training_target: pd.Series[float]
    holdout_target: pd.Series[float]
    provenance: pd.DataFrame
    origin: pd.Timestamp
    historical_columns: tuple[str, ...]


def feature_windows(config: FeatureConfig) -> dict[str, tuple[int, int]]:
    """Map feature name to oldest/newest demand-source offsets before target date."""
    windows = {f"lag_{lag}": (lag, lag) for lag in config.lags}
    for width in config.rolling_windows:
        windows[f"mean_{width}_ending_lag_{config.rolling_end_lag}"] = (
            config.rolling_end_lag + width - 1,
            config.rolling_end_lag,
        )
    return windows


def _shifted_mean(series: pd.Series[float], *, lag: int, width: int) -> pd.Series[float]:
    return series.shift(lag).rolling(width, min_periods=width).mean()


def build_features(daily: pd.DataFrame, config: FeatureConfig) -> FeatureSet:
    """Use prior-origin demand and known calendars, keeping labels separate."""
    split = common_holdout(daily)
    frame = daily.sort_values(["store_id", "category", "date"]).reset_index(drop=True)
    if not set(KNOWN_AT_ORIGIN).issubset(frame.columns):
        raise DataError("known-at-origin calendar feature fields are missing")
    windows = feature_windows(config)
    grouped = frame.groupby(["store_id", "category"], sort=False)["demand"]
    for lag in config.lags:
        frame[f"lag_{lag}"] = grouped.shift(lag)
    for width in config.rolling_windows:
        frame[f"mean_{width}_ending_lag_{config.rolling_end_lag}"] = grouped.transform(
            partial(_shifted_mean, lag=config.rolling_end_lag, width=width)
        )
    historical = list(windows)
    holdout_mask = frame["date"] > split.origin
    if frame.loc[holdout_mask, historical].isna().any().any():
        raise DataError("insufficient history for complete holdout features")
    # Only initial training warmup rows are excluded from model-ready features;
    # the prepared daily dataset and all 560 holdout observations remain intact.
    training_mask = ~holdout_mask & frame[historical].notna().all(axis=1)
    if not training_mask.any():
        raise DataError("no training features remain after historical warmup")
    columns = ["date", *KNOWN_AT_ORIGIN, *historical]
    training = frame.loc[training_mask, columns].set_index(GRAIN).sort_index()
    holdout = frame.loc[holdout_mask, columns].set_index(GRAIN).sort_index()
    labels = frame.set_index(GRAIN)["demand"].astype(float)
    provenance_parts: list[pd.DataFrame] = []
    for name, (oldest, newest) in windows.items():
        part = frame.loc[holdout_mask, GRAIN].copy()
        part["feature"] = name
        part["source_start"] = part["date"] - pd.to_timedelta(oldest, unit="D")
        part["source_end"] = part["date"] - pd.to_timedelta(newest, unit="D")
        part["forecast_origin"] = split.origin
        if (part["source_end"] > split.origin).any() or (
            part["source_end"] > part["date"] - pd.Timedelta(days=28)
        ).any():
            raise DataError("historical feature cutoff exceeds the direct-horizon boundary")
        provenance_parts.append(part)
    return FeatureSet(
        training=training,
        holdout=holdout,
        training_target=labels.loc[training.index],
        holdout_target=labels.loc[holdout.index],
        provenance=pd.concat(provenance_parts, ignore_index=True).sort_values([*GRAIN, "feature"]),
        origin=split.origin,
        historical_columns=tuple(historical),
    )
