"""Offline four-model integration and adversarial forecast contract regressions."""

from __future__ import annotations

import json
import warnings
from dataclasses import fields, replace
from pathlib import Path
from typing import Any, Literal
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from typer.testing import CliRunner

from linkedin_visual_labs.cli import app
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import forecasting as f
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    common_holdout,
    file_hash,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    PipelineContext,
    build_pipeline_context,
)


@pytest.fixture(scope="module")
def config() -> CommerceConfig:
    return load_commerce_config()


@pytest.fixture(scope="module")
def result(daily: pd.DataFrame, config: CommerceConfig) -> f.ForecastResult:
    return f.forecast_arena(daily, config)


def test_canonical_complete(result: f.ForecastResult, daily: pd.DataFrame) -> None:
    frame = result.predictions
    assert list(frame.columns) == f.PREDICTION_COLUMNS
    assert len(frame) == 2240
    assert not frame.duplicated([*GRAIN, "model_name"]).any()
    assert frame.groupby("model_name").size().to_dict() == dict.fromkeys(f.MODEL_NAMES, 560)
    assert frame.groupby(["model_name", "store_id", "category"]).size().eq(28).all()
    expected = set(common_holdout(daily).holdout["date"])
    for _, group in frame.groupby("model_name"):
        assert set(group["date"]) == expected
    assert np.isfinite(frame[["actual_units", "raw_forecast_units", "forecast_units"]]).all().all()
    assert frame["forecast_units"].ge(0).all()
    assert not result.statuses["fallback_used"].any()
    assert result.statuses["prediction_count"].sum() == 2240
    assert result.statuses[["training_seconds", "prediction_seconds"]].ge(0).all().all()


def test_seasonal_naive_exact_history(daily: pd.DataFrame, config: CommerceConfig) -> None:
    inputs = f.make_inputs(daily, config)
    output = f.SeasonalNaive().forecast(inputs, config)
    expected = inputs.history.copy()
    expected["date"] = expected["date"] + pd.Timedelta(days=28)
    joined = output.raw.merge(expected, on=GRAIN, validate="one_to_one")
    assert len(joined) == 560
    np.testing.assert_array_equal(joined["raw_forecast_units"], joined["demand"])
    assert output.statuses[0].training_seconds == 0
    assert output.statuses[0].convergence_status == "not_applicable"
    pd.testing.assert_frame_equal(output.raw, f.SeasonalNaive().forecast(inputs, config).raw)


def test_model_mutation_and_rerun(
    daily: pd.DataFrame,
    config: CommerceConfig,
    result: f.ForecastResult,
) -> None:
    changed = daily.copy()
    changed.loc[changed["date"] > common_holdout(daily).origin, "demand"] += 1_000_000
    for data in (daily.copy(), changed):
        rerun = f.forecast_arena(data, config)
        pd.testing.assert_frame_equal(
            result.predictions.drop(columns="actual_units"),
            rerun.predictions.drop(columns="actual_units"),
            rtol=1e-10,
            atol=1e-8,
        )
        pd.testing.assert_frame_equal(
            result.interpretation, rerun.interpretation, rtol=1e-10, atol=1e-8
        )
        pd.testing.assert_frame_equal(
            result.statuses.drop(columns=["training_seconds", "prediction_seconds"]),
            rerun.statuses.drop(columns=["training_seconds", "prediction_seconds"]),
        )
    np.testing.assert_array_equal(
        rerun.predictions["actual_units"],
        result.predictions["actual_units"] + 1_000_000,
    )


def test_interface_has_no_holdout_targets(daily: pd.DataFrame, config: CommerceConfig) -> None:
    inputs = f.make_inputs(daily, config)
    assert {field.name for field in fields(inputs)} == {
        "origin",
        "history",
        "training",
        "training_target",
        "future",
    }
    assert inputs.history["date"].max() == inputs.origin
    assert inputs.future["date"].min() == inputs.origin + pd.Timedelta(days=1)
    assert not {"actual_units", "demand", "lag_1", "lag_7"}.intersection(inputs.training.columns)
    assert not {"actual_units", "demand"}.intersection(inputs.future.columns)
    assert set(inputs.training.columns) == set(inputs.future.columns) - {"date"}


def test_hw_local_configuration_and_no_fallback(
    daily: pd.DataFrame,
    config: CommerceConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = f.ExponentialSmoothing
    calls: list[dict[str, Any]] = []

    def local(values: Any, **kwargs: Any) -> Any:
        calls.append(kwargs)
        assert len(values) == 84
        if len(calls) == 1:
            raise RuntimeError("deliberate local fit failure")
        return original(values, **kwargs)

    monkeypatch.setattr(f, "ExponentialSmoothing", local)
    output = f.HoltWinters().forecast(f.make_inputs(daily, config), config)
    assert len(calls) == 20
    for call in calls:
        assert call == {
            **config.forecasting.holt_winters.model_dump(),
            "initialization_method": "estimated",
        }
        assert call["seasonal_periods"] == 7
    assert len(output.raw) == 19 * 28
    failed = output.statuses[0]
    assert failed.fit_status == "failed"
    assert failed.error_summary == "RuntimeError: deliberate local fit failure"
    assert not failed.fallback_used
    assert failed.prediction_count == 0
    assert output.raw.groupby(["store_id", "category"]).size().eq(28).all()


@pytest.mark.parametrize("name", ["hist_gradient_boosting", "mlp"])
def test_estimator_and_training_only_preprocessing(
    name: Literal["hist_gradient_boosting", "mlp"],
    daily: pd.DataFrame,
    config: CommerceConfig,
) -> None:
    inputs = f.make_inputs(daily, config)
    estimator = f.make_pooled_estimator(name, config, list(inputs.training.columns))
    final = estimator.named_steps["estimator"]
    model = final.regressor if name == "mlp" else final
    assert isinstance(model, MLPRegressor if name == "mlp" else HistGradientBoostingRegressor)
    parameters = model.get_params()
    assert parameters["random_state"] == f.model_seed(config, name)
    assert 0 <= parameters["random_state"] < 2**32
    assert parameters["early_stopping"] is False
    if name == "mlp":
        assert parameters["hidden_layer_sizes"] == (128, 64, 32)
        assert parameters["activation"] == "relu"
        assert parameters["alpha"] == config.forecasting.mlp.alpha
        assert parameters["max_iter"] == 500
    else:
        assert parameters["max_iter"] == 200
        assert parameters["max_leaf_nodes"] == 31
        assert parameters["l2_regularization"] == 1.0
    # Fit only preprocessing here, inspecting its learned statistics and unknown-category handling.
    preprocessor = estimator.named_steps["preprocessing"]
    preprocessor.fit(inputs.training)
    encoder = preprocessor.named_transformers_["categorical"]
    for column, vocabulary in zip(f.CATEGORICAL, encoder.categories_, strict=True):
        assert set(vocabulary) == set(inputs.training[column])
    changed = inputs.future.drop(columns="date").copy()
    changed["event_name_1"] = "unseen_future_event"
    changed["lag_28"] = 1e9
    preprocessor.transform(changed)
    assert "unseen_future_event" not in encoder.categories_[3]
    if name == "mlp":
        numeric = [c for c in inputs.training if c not in f.CATEGORICAL]
        np.testing.assert_allclose(
            preprocessor.named_transformers_["numeric"].mean_,
            inputs.training[numeric].mean().to_numpy(),
        )


def test_mlp_warning_and_target_scaling(
    daily: pd.DataFrame,
    config: CommerceConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = config.model_dump()
    settings["forecasting"]["mlp"]["max_iter"] = 1
    altered = CommerceConfig.model_validate(settings)
    original = f.make_pooled_estimator
    captured: list[Any] = []

    def capture(*args: Any, **kwargs: Any) -> Any:
        estimator = original(*args, **kwargs)
        captured.append(estimator)
        return estimator

    monkeypatch.setattr(f, "make_pooled_estimator", capture)
    inputs = f.make_inputs(daily, altered)
    result = f.PooledForecaster("mlp").forecast(inputs, altered)
    status = result.statuses[0]
    assert status.fit_status == "warning"
    assert status.convergence_status == "warning"
    assert status.iterations == 1
    assert "ConvergenceWarning" in status.warning_summary
    assert len(result.raw) == 560
    assert result.raw["model_status"].eq("warning").all()
    scaler = captured[0].named_steps["estimator"].transformer_
    np.testing.assert_allclose(scaler.mean_, [inputs.training_target.mean()])


def test_importance_contract(
    result: f.ForecastResult, daily: pd.DataFrame, config: CommerceConfig
) -> None:
    importance = result.interpretation
    assert set(importance["feature"]) == set(f.make_inputs(daily, config).training.columns)
    assert importance["classification"].eq("training_in_sample_interpretation").all()
    assert importance["sample_rows"].eq(256).all()
    assert importance["repeats"].eq(3).all()
    assert np.isfinite(importance[["mean_mae_increase", "std_mae_increase"]]).all().all()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_rejected(invalid: float, result: f.ForecastResult, daily: pd.DataFrame) -> None:
    raw = result.predictions.copy()
    raw.loc[0, "raw_forecast_units"] = invalid
    with pytest.raises(DataError, match=r"missing|nonfinite"):
        f.canonical_predictions(raw.drop(columns="actual_units"), common_holdout(daily).holdout)


@pytest.mark.parametrize(
    "defect", ["missing", "duplicate", "extra_date", "wrong_model", "null_key"]
)
def test_grid_rejection(defect: str, result: f.ForecastResult, daily: pd.DataFrame) -> None:
    raw = result.predictions.drop(columns="actual_units").copy()
    if defect == "missing":
        raw = raw.iloc[1:]
    elif defect == "duplicate":
        raw = pd.concat([raw, raw.iloc[:1]], ignore_index=True)
    elif defect == "extra_date":
        raw.loc[0, "date"] = pd.Timestamp("2099-01-01")
    elif defect == "wrong_model":
        raw.loc[0, "model_name"] = "unknown"
    else:
        raw.loc[0, "store_id"] = None
    with pytest.raises(DataError):
        f.canonical_predictions(raw, common_holdout(daily).holdout)


def test_finite_negative_clipping(result: f.ForecastResult, daily: pd.DataFrame) -> None:
    raw = result.predictions.drop(columns="actual_units").copy()
    raw.loc[:2, "raw_forecast_units"] = [-10.0, 0.0, 12.5]
    output = f.canonical_predictions(raw, common_holdout(daily).holdout)
    np.testing.assert_array_equal(output.loc[:2, "raw_forecast_units"], [-10, 0, 12.5])
    np.testing.assert_array_equal(output.loc[:2, "forecast_units"], [0, 0, 12.5])
    assert output.loc[:2, "was_clipped"].tolist() == [True, False, False]


def _context_with_source(tmp_path: Path, daily: pd.DataFrame) -> PipelineContext:
    original = build_pipeline_context()
    context = replace(original, paths=replace(original.paths, output_root=tmp_path))
    source = context.resolve_output_path("data/fixture/demand_daily.parquet")
    source.parent.mkdir(parents=True)
    frame = daily.assign(data_classification="synthetic_test_only")
    frame.to_parquet(source, index=False)
    source.with_suffix(".metadata.json").write_text(
        json.dumps(
            {
                "parquet_sha256": file_hash(source),
                "classification": "synthetic_test_only",
            }
        )
    )
    return context


def test_output_and_cli(
    tmp_path: Path,
    daily: pd.DataFrame,
    result: f.ForecastResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context_with_source(tmp_path, daily)
    monkeypatch.setattr(f, "forecast_arena", lambda *_: result)
    output = f.run_forecast(context, fixture=True)
    pd.testing.assert_frame_equal(pd.read_parquet(output), result.predictions)
    manifest = json.loads(output.with_suffix(".metadata.json").read_text())
    assert manifest["complete"] is True
    # Missing iteration counts are JSON null, never nonstandard NaN literals.
    json.dumps(manifest, allow_nan=False)
    assert manifest["status_rows"][0]["iterations"] is None
    assert output.with_name("model_status.parquet").exists()
    assert output.with_name("hist_gradient_boosting_importance.parquet").exists()
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import cli

    monkeypatch.setattr(cli, "build_pipeline_context", lambda *_: context)
    response = CliRunner().invoke(app, ["commerce", "forecast", "--fixture"])
    assert response.exit_code == 0, response.output
    assert "SYNTHETIC TEST ONLY" in response.output
    response = CliRunner().invoke(app, ["commerce", "forecast"])
    assert response.exit_code == 1


def test_failure_status_persisted_no_stale_predictions(
    tmp_path: Path,
    daily: pd.DataFrame,
    result: f.ForecastResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context_with_source(tmp_path, daily)
    output = context.resolve_output_path("data/fixture/predictions.parquet")
    output.write_text("previous successful result")
    failed = result.statuses.copy()
    failed.loc[0, "fit_status"] = "failed"
    failed.loc[0, "error_summary"] = "RuntimeError: intentional"
    monkeypatch.setattr(
        f, "forecast_arena", lambda *_: f.ForecastResult(pd.DataFrame(), failed, pd.DataFrame())
    )
    with pytest.raises(DataError, match="no fallback permitted"):
        f.run_forecast(context, fixture=True)
    assert not output.exists()
    statuses = pd.read_parquet(output.with_name("model_status.parquet"))
    assert statuses.loc[0, "error_summary"] == "RuntimeError: intentional"
    assert json.loads(output.with_suffix(".metadata.json").read_text())["complete"] is False


def test_prepared_checksum_rejected(tmp_path: Path, daily: pd.DataFrame) -> None:
    context = _context_with_source(tmp_path, daily)
    source = context.resolve_output_path("data/fixture/demand_daily.parquet")
    source.write_bytes(b"corrupt")
    with pytest.raises(DataError, match="checksum"):
        f.run_forecast(context, fixture=True)


def test_pooled_failure_recording(
    daily: pd.DataFrame, config: CommerceConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    estimator = Mock()
    estimator.fit.side_effect = ValueError("intentional estimator failure")
    monkeypatch.setattr(f, "make_pooled_estimator", lambda *_: estimator)
    output = f.PooledForecaster("mlp").forecast(f.make_inputs(daily, config), config)
    assert output.raw.empty
    assert output.statuses[0].fit_status == "failed"
    assert output.statuses[0].error_summary == "ValueError: intentional estimator failure"


def test_clipping_status_and_warning_recording(
    daily: pd.DataFrame, config: CommerceConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    estimator = Mock()
    estimator.named_steps = {"estimator": Mock(regressor_=Mock(n_iter_=1))}

    def fit(*args: Any) -> None:
        warnings.warn("deliberate nonconvergence", ConvergenceWarning, stacklevel=2)

    estimator.fit.side_effect = fit
    estimator.predict.return_value = np.full(560, -2.0)
    monkeypatch.setattr(f, "make_pooled_estimator", lambda *_: estimator)
    output = f.PooledForecaster("mlp").forecast(f.make_inputs(daily, config), config)
    assert output.statuses[0].clipping_count == 560
    assert output.statuses[0].clipping_rate == 1.0
    assert output.statuses[0].convergence_status == "warning"


def test_arena_failure_blocks_publication(
    daily: pd.DataFrame, config: CommerceConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(f, "ExponentialSmoothing", Mock(side_effect=RuntimeError("failed")))
    result = f.forecast_arena(daily, config)
    assert result.predictions.empty
    hw = result.statuses.loc[result.statuses["model_name"].eq("holt_winters")]
    assert len(hw) == 20
    assert hw["fit_status"].eq("failed").all()
    assert not hw["fallback_used"].any()
