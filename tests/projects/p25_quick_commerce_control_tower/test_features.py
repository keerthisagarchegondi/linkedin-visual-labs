"""Strong holdout mutation and exact information-window regression tests."""

from __future__ import annotations

import pandas as pd
import pytest
from pydantic import ValidationError

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import DataError
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.features import build_features
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import FeatureConfig


def test_all_holdout_demand_mutation(daily: pd.DataFrame) -> None:
    config = load_commerce_config().features
    before = build_features(daily, config)
    mutated = daily.copy()
    mask = mutated["date"] > before.origin
    assert mask.sum() == 560
    mutated.loc[mask, "demand"] = mutated.loc[mask, "demand"] * 100 + 99999
    after = build_features(mutated, config)
    pd.testing.assert_frame_equal(before.holdout, after.holdout)
    pd.testing.assert_frame_equal(before.training, after.training)
    pd.testing.assert_frame_equal(before.provenance, after.provenance)
    pd.testing.assert_series_equal(before.training_target, after.training_target)
    assert not before.holdout_target.equals(after.holdout_target)
    assert "demand" not in before.holdout.columns
    assert len(before.holdout) == 560


def test_exact_lags_rolling_and_cutoffs(daily: pd.DataFrame) -> None:
    result = build_features(daily, load_commerce_config().features)
    truth = daily.set_index(["date", "store_id", "category"])["demand"]
    for _, row in result.holdout.reset_index().iterrows():
        date = pd.Timestamp(row["date"])
        store = str(row["store_id"])
        category = str(row["category"])
        for lag in (28, 35, 42, 49, 56):
            assert row[f"lag_{lag}"] == truth.loc[(date - pd.Timedelta(days=lag), store, category)]
        expected = (
            sum(
                truth.loc[(date - pd.Timedelta(days=lag), store, category)] for lag in range(28, 35)
            )
            / 7
        )
        assert row["mean_7_ending_lag_28"] == pytest.approx(expected)
    assert (result.provenance["source_end"] <= result.origin).all()
    assert (
        result.provenance["source_end"] <= result.provenance["date"] - pd.Timedelta(days=28)
    ).all()
    assert (result.provenance["source_start"] <= result.provenance["source_end"]).all()
    assert result.training.index.get_level_values("date").max() == result.origin


@pytest.mark.parametrize("lags", [(1,), (7,), (27, 28), (28, 28), (56, 28), ()])
def test_prohibited_lags_rejected(lags: tuple[int, ...]) -> None:
    with pytest.raises(ValidationError):
        FeatureConfig(lags=lags, rolling_windows=(7, 14), rolling_end_lag=28)


def test_near_target_rolling_rejected() -> None:
    raw = load_commerce_config().features.model_dump()
    raw["rolling_end_lag"] = 1
    with pytest.raises(ValidationError):
        FeatureConfig.model_validate(raw)


def test_exact_cutoff_dependency_boundary(daily: pd.DataFrame) -> None:
    config = load_commerce_config().features
    before = build_features(daily, config)
    modified = daily.copy()
    modified.loc[modified["d"].eq("d_58"), "demand"] += 1000
    after = build_features(modified, config)
    first_date = before.origin + pd.Timedelta(days=1)  # d_85 can use at most d_57.
    before_rows = before.holdout.reset_index()
    after_rows = after.holdout.reset_index()
    pd.testing.assert_frame_equal(
        before_rows.loc[before_rows["date"].eq(first_date)],
        after_rows.loc[after_rows["date"].eq(first_date)],
    )
    second_date = first_date + pd.Timedelta(days=1)  # d_86 lag 28 must now change.
    assert (
        (
            after_rows.loc[after_rows["date"].eq(second_date), "lag_28"]
            - before_rows.loc[before_rows["date"].eq(second_date), "lag_28"]
        )
        .eq(1000)
        .all()
    )


@pytest.mark.parametrize("name", ["lag_1", "target_encoding", "scaler_fit", "random_validation"])
def test_unapproved_feature_transforms_rejected(name: str) -> None:
    raw = load_commerce_config().features.model_dump()
    raw[name] = True
    with pytest.raises(ValidationError):
        FeatureConfig.model_validate(raw)


def test_insufficient_history_is_not_imputed(daily: pd.DataFrame) -> None:
    shortened = daily.loc[daily["date"] >= daily["date"].max() - pd.Timedelta(days=49)]
    with pytest.raises(DataError, match="insufficient history"):
        build_features(shortened, load_commerce_config().features)
