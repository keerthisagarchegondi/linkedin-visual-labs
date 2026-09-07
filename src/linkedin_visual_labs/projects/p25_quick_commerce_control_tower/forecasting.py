"""Four fixed forecasting methods; holdout labels never enter the method interface."""

from __future__ import annotations

import json
import warnings
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Literal, Protocol

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.tsa.holtwinters import (  # type: ignore[import-untyped]
    ExponentialSmoothing as ExponentialSmoothing,
)
from threadpoolctl import threadpool_limits  # type: ignore[import-untyped]

from linkedin_visual_labs.common.media import write_generation_manifest
from linkedin_visual_labs.common.random_state import derive_seed
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    common_holdout,
    file_hash,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.features import (
    build_features,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import (
    PROJECT_ID,
    CommerceConfig,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext

ModelName = Literal["seasonal_naive", "holt_winters", "hist_gradient_boosting", "mlp"]
MODEL_NAMES: tuple[ModelName, ...] = (
    "seasonal_naive",
    "holt_winters",
    "hist_gradient_boosting",
    "mlp",
)
CATEGORICAL = [
    "store_id",
    "category",
    "weekday",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
]
PREDICTION_COLUMNS = [
    *GRAIN,
    "model_name",
    "actual_units",
    "raw_forecast_units",
    "forecast_units",
    "was_clipped",
    "model_status",
]


@dataclass(frozen=True)
class ForecastInputs:
    """One origin, training history/targets and future predictors; no future targets."""

    origin: pd.Timestamp
    history: pd.DataFrame
    training: pd.DataFrame
    training_target: pd.Series[float]
    future: pd.DataFrame


@dataclass(frozen=True)
class ModelStatus:
    model_name: str
    store_id: str
    category: str
    fit_status: str
    fallback_used: bool
    convergence_status: str
    iterations: int | None
    warning_summary: str
    error_summary: str
    training_seconds: float
    prediction_seconds: float
    prediction_count: int
    clipping_count: int
    clipping_rate: float


@dataclass(frozen=True)
class MethodResult:
    raw: pd.DataFrame
    statuses: tuple[ModelStatus, ...]
    interpretation: pd.DataFrame


@dataclass(frozen=True)
class ForecastResult:
    predictions: pd.DataFrame
    statuses: pd.DataFrame
    interpretation: pd.DataFrame


class ForecastMethod(Protocol):
    """The same target-free prediction interface for every approved method."""

    def forecast(self, inputs: ForecastInputs, config: CommerceConfig) -> MethodResult: ...


def model_seed(config: CommerceConfig, name: str) -> int:
    return derive_seed(config.seed, f"{PROJECT_ID}:{name}") % (2**32)


def make_inputs(daily: pd.DataFrame, config: CommerceConfig) -> ForecastInputs:
    split = common_holdout(daily)
    features = build_features(daily, config.features)
    return ForecastInputs(
        origin=split.origin,
        history=split.training[[*GRAIN, "demand"]].sort_values(GRAIN).reset_index(drop=True),
        training=features.training.reset_index().drop(columns="date"),
        training_target=features.training_target.reset_index(drop=True),
        future=features.holdout.reset_index(),
    )


def _raw(
    keys: pd.DataFrame, name: ModelName, values: NDArray[np.float64], status: str
) -> pd.DataFrame:
    if values.shape != (len(keys),) or not np.isfinite(values).all():
        raise DataError(f"{name}: missing or nonfinite predictions")
    result = keys[GRAIN].copy()
    result["model_name"] = name
    result["raw_forecast_units"] = values
    result["model_status"] = status
    return result


def _status(
    name: ModelName,
    store: str,
    category: str,
    raw: pd.DataFrame,
    caught: list[warnings.WarningMessage],
    error: str,
    training: float,
    prediction: float,
    iterations: int | None = None,
    fitted: bool = True,
) -> ModelStatus:
    messages = " | ".join(f"{w.category.__name__}: {w.message}" for w in caught)
    converged = not any(w.category.__name__ == "ConvergenceWarning" for w in caught)
    count = len(raw)
    clipped = int((raw["raw_forecast_units"] < 0).sum()) if count else 0
    return ModelStatus(
        name,
        store,
        category,
        "failed" if error else ("warning" if caught else "success"),
        False,
        "failed"
        if error
        else ("not_applicable" if not fitted else ("success" if converged else "warning")),
        iterations,
        messages,
        error,
        training,
        prediction,
        count,
        clipped,
        clipped / count if count else 0.0,
    )


@dataclass(frozen=True)
class SeasonalNaive:
    def forecast(self, inputs: ForecastInputs, config: CommerceConfig) -> MethodResult:
        start = perf_counter()
        history = inputs.history.set_index(GRAIN)["demand"]
        keys = inputs.future[GRAIN].copy()
        lookup = keys.copy()
        lookup["date"] = lookup["date"] - pd.Timedelta(days=config.forecasting.seasonal_naive.lag)
        values = history.reindex(pd.MultiIndex.from_frame(lookup)).to_numpy(dtype=float)
        raw = _raw(keys, "seasonal_naive", values, "success")
        status = _status(
            "seasonal_naive", "ALL", "ALL", raw, [], "", 0.0, perf_counter() - start, fitted=False
        )
        return MethodResult(raw, (status,), pd.DataFrame())


@dataclass(frozen=True)
class HoltWinters:
    def forecast(self, inputs: ForecastInputs, config: CommerceConfig) -> MethodResult:
        parts: list[pd.DataFrame] = []
        statuses: list[ModelStatus] = []
        for (store, category), keys in inputs.future.groupby(["store_id", "category"], sort=True):
            values = (
                inputs.history.loc[
                    inputs.history["store_id"].eq(str(store))
                    & inputs.history["category"].eq(str(category))
                ]
                .sort_values("date")["demand"]
                .to_numpy(dtype=float)
            )
            raw = pd.DataFrame()
            error = ""
            train_seconds = prediction_seconds = 0.0
            with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=1):
                warnings.simplefilter("always")
                start = perf_counter()
                try:
                    estimator = ExponentialSmoothing(
                        values,
                        initialization_method="estimated",
                        **config.forecasting.holt_winters.model_dump(),
                    )
                    fitted = estimator.fit(optimized=True, use_brute=False)
                    train_seconds = perf_counter() - start
                    start = perf_counter()
                    predictions = np.asarray(fitted.forecast(28), dtype=float)
                    raw = _raw(
                        keys.sort_values("date"),
                        "holt_winters",
                        predictions,
                        "warning" if caught else "success",
                    )
                    prediction_seconds = perf_counter() - start
                except Exception as exc:
                    # Preserve the original third-party local fit failure type and message.
                    error = f"{type(exc).__name__}: {exc}"
                    if not train_seconds:
                        train_seconds = perf_counter() - start
                    else:
                        prediction_seconds = perf_counter() - start
            statuses.append(
                _status(
                    "holt_winters",
                    str(store),
                    str(category),
                    raw,
                    caught,
                    error,
                    train_seconds,
                    prediction_seconds,
                )
            )
            if not raw.empty:
                parts.append(raw)
        return MethodResult(
            pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(),
            tuple(statuses),
            pd.DataFrame(),
        )


def make_pooled_estimator(
    name: Literal["hist_gradient_boosting", "mlp"],
    config: CommerceConfig,
    columns: list[str],
) -> Pipeline:
    """Dense stable one-hot vocabulary; all learned preprocessing belongs to fit(training)."""
    numeric = [column for column in columns if column not in CATEGORICAL]
    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
            ("numeric", StandardScaler() if name == "mlp" else "passthrough", numeric),
        ],
        remainder="drop",
    )
    if name == "hist_gradient_boosting":
        estimator = HistGradientBoostingRegressor(
            random_state=model_seed(config, name),
            **config.forecasting.hist_gradient_boosting.model_dump(),
        )
        return Pipeline([("preprocessing", preprocessor), ("estimator", estimator)])
    neural = MLPRegressor(
        random_state=model_seed(config, name), **config.forecasting.mlp.model_dump()
    )
    # Training-only target standardization improves conditioning; predictions return demand units.
    target_scaled = TransformedTargetRegressor(regressor=neural, transformer=StandardScaler())
    return Pipeline([("preprocessing", preprocessor), ("estimator", target_scaled)])


def training_importance(
    estimator: Pipeline,
    inputs: ForecastInputs,
    config: CommerceConfig,
) -> pd.DataFrame:
    """Bounded in-sample interpretation, never a tuning or feature-selection input."""
    sample = inputs.training.tail(256).reset_index(drop=True)
    actual = inputs.training_target.tail(len(sample)).to_numpy(dtype=float)
    baseline = float(np.mean(np.abs(np.asarray(estimator.predict(sample)) - actual)))
    rng = np.random.default_rng(model_seed(config, "importance"))
    rows: list[dict[str, str | float | int]] = []
    for column in sample.columns:
        differences: list[float] = []
        for _ in range(3):
            permuted = sample.copy()
            permuted[column] = rng.permutation(permuted[column].to_numpy())
            loss = float(np.mean(np.abs(np.asarray(estimator.predict(permuted)) - actual)))
            differences.append(loss - baseline)
        rows.append(
            {
                "model_name": "hist_gradient_boosting",
                "feature": str(column),
                "mean_mae_increase": float(np.mean(differences)),
                "std_mae_increase": float(np.std(differences)),
                "sample_rows": len(sample),
                "repeats": 3,
                "classification": "training_in_sample_interpretation",
                "sample_policy": "last_256_training_feature_rows",
                "not_for_tuning": "true",
            }
        )
    return pd.DataFrame(rows).sort_values("feature").reset_index(drop=True)


@dataclass(frozen=True)
class PooledForecaster:
    name: Literal["hist_gradient_boosting", "mlp"]

    def forecast(self, inputs: ForecastInputs, config: CommerceConfig) -> MethodResult:
        estimator = make_pooled_estimator(self.name, config, list(inputs.training.columns))
        raw = pd.DataFrame()
        error = ""
        iterations: int | None = None
        train_seconds = prediction_seconds = 0.0
        with warnings.catch_warnings(record=True) as caught, threadpool_limits(limits=1):
            warnings.simplefilter("always")
            start = perf_counter()
            try:
                estimator.fit(inputs.training, inputs.training_target)
                train_seconds = perf_counter() - start
                final = estimator.named_steps["estimator"]
                iterations = int(final.regressor_.n_iter_ if self.name == "mlp" else final.n_iter_)
                start = perf_counter()
                values = np.asarray(
                    estimator.predict(inputs.future.drop(columns="date")), dtype=float
                )
                raw = _raw(inputs.future, self.name, values, "warning" if caught else "success")
                prediction_seconds = perf_counter() - start
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                if not train_seconds:
                    train_seconds = perf_counter() - start
                else:
                    prediction_seconds = perf_counter() - start
            importance = (
                training_importance(estimator, inputs, config)
                if not error and self.name == "hist_gradient_boosting"
                else pd.DataFrame()
            )
        status = _status(
            self.name,
            "ALL",
            "ALL",
            raw,
            caught,
            error,
            train_seconds,
            prediction_seconds,
            iterations,
        )
        return MethodResult(raw, (status,), importance)


def canonical_predictions(raw: pd.DataFrame, actual: pd.DataFrame) -> pd.DataFrame:
    """Reconcile the entire expected grid before attaching evaluation labels or clipping."""
    if (
        len(actual) != 560
        or actual[GRAIN].isna().any().any()
        or actual.duplicated(GRAIN).any()
        or actual["date"].nunique() != 28
        or not actual.groupby("date").size().eq(20).all()
        or len(actual.groupby(["store_id", "category"])) != 20
        or not actual.groupby(["store_id", "category"]).size().eq(28).all()
    ):
        raise DataError("actual holdout must contain the common 560 unique expected keys")
    required = {*GRAIN, "model_name", "raw_forecast_units", "model_status"}
    if not required.issubset(raw.columns) or raw[list(required)].isna().any().any():
        raise DataError("missing forecast fields")
    grain = [*GRAIN, "model_name"]
    expected = actual[GRAIN].merge(pd.DataFrame({"model_name": MODEL_NAMES}), how="cross")
    if raw.duplicated(grain).any() or not pd.MultiIndex.from_frame(raw[grain]).sort_values().equals(
        pd.MultiIndex.from_frame(expected[grain]).sort_values()
    ):
        raise DataError("forecasts must cover exactly the common 2240 model-series-date keys")
    values = raw["raw_forecast_units"].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise DataError("nonfinite forecasts cannot be clipped or published")
    result = raw.merge(actual[[*GRAIN, "demand"]], on=GRAIN, validate="many_to_one")
    result = result.rename(columns={"demand": "actual_units"})
    result["forecast_units"] = result["raw_forecast_units"].clip(lower=0)
    result["was_clipped"] = result["raw_forecast_units"] < 0
    return result[PREDICTION_COLUMNS].sort_values(["model_name", *GRAIN]).reset_index(drop=True)


def forecast_arena(daily: pd.DataFrame, config: CommerceConfig) -> ForecastResult:
    inputs = make_inputs(daily, config)
    methods: tuple[ForecastMethod, ...] = (
        SeasonalNaive(),
        HoltWinters(),
        PooledForecaster("hist_gradient_boosting"),
        PooledForecaster("mlp"),
    )
    results = [method.forecast(inputs, config) for method in methods]
    statuses = pd.DataFrame([asdict(status) for result in results for status in result.statuses])
    raw = pd.concat([result.raw for result in results if not result.raw.empty], ignore_index=True)
    # A failed fit is evidence, not a disguised fallback. No partial canonical table is published.
    predictions = (
        pd.DataFrame(columns=PREDICTION_COLUMNS)
        if statuses["fit_status"].eq("failed").any()
        else canonical_predictions(raw, common_holdout(daily).holdout)
    )
    return ForecastResult(predictions, statuses, results[2].interpretation)


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".parquet.part")
    try:
        frame.to_parquet(temporary, index=False)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def run_forecast(context: PipelineContext, *, fixture: bool = False) -> Path:
    """Read verified prepared data offline and publish forecasts plus explicit status evidence."""
    prefix = "data/fixture" if fixture else "data"
    source = context.resolve_output_path(f"{prefix}/demand_daily.parquet")
    metadata = json.loads(source.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    classification = "synthetic_test_only" if fixture else "public_real_m5"
    if (
        metadata["parquet_sha256"] != file_hash(source)
        or metadata["classification"] != classification
    ):
        raise DataError("prepared data checksum/classification mismatch")
    daily = pd.read_parquet(source)
    if not daily["data_classification"].eq(classification).all():
        raise DataError("prepared row classification mismatch")
    split = common_holdout(daily)
    result = forecast_arena(daily, context.configuration)
    output = context.resolve_output_path(f"{prefix}/predictions.parquet")
    status_path = context.resolve_output_path(f"{prefix}/model_status.parquet")
    interpretation_path = context.resolve_output_path(
        f"{prefix}/hist_gradient_boosting_importance.parquet"
    )
    _write_parquet(result.statuses, status_path)
    success = len(result.predictions) == 2240
    manifest = {
        "complete": success,
        "classification": classification,
        "source_sha256": file_hash(source),
        "configuration": context.configuration.model_dump(mode="json"),
        "dependency_versions": {
            package: version(package)
            for package in ("numpy", "scipy", "scikit-learn", "statsmodels", "threadpoolctl")
        },
        "execution_settings": {
            "numerical_threads": 1,
            "holt_winters_initialization": "estimated",
            "holt_winters_fit": {"optimized": True, "use_brute": False},
            "categorical_encoding": "training-only dense one-hot; unknown category ignored",
            "mlp_numeric_scaler": "training-only StandardScaler",
            "mlp_target_scaler": "training-only StandardScaler; inverse to demand units",
        },
        "seeds": {
            name: model_seed(context.configuration, name) for name in (*MODEL_NAMES, "importance")
        },
        "training_start": str(split.training["date"].min().date()),
        "forecast_origin": str(split.origin.date()),
        "holdout_start": str(split.holdout["date"].min().date()),
        "holdout_end": str(split.holdout["date"].max().date()),
        "prediction_rows": len(result.predictions),
        "fallback_policy": "prohibited_by_approved_plan",
        "status_rows": result.statuses.astype(object)
        .where(result.statuses.notna(), None)
        .to_dict(orient="records"),
        "determinism": (
            "single numerical thread; fixed seeds; rtol=1e-10, atol=1e-8; excludes runtimes"
        ),
        "interpretation": (
            "3 permutations of last 256 training rows; in-sample, not used for tuning"
        ),
    }
    if success:
        _write_parquet(result.predictions, output)
        _write_parquet(result.interpretation, interpretation_path)
        manifest["predictions_sha256"] = file_hash(output)
        manifest["interpretation_sha256"] = file_hash(interpretation_path)
        manifest["model_status_sha256"] = file_hash(status_path)
    else:
        # Prevent stale successful forecasts from being mistaken for this failed run.
        output.unlink(missing_ok=True)
        interpretation_path.unlink(missing_ok=True)
    write_generation_manifest(manifest, output.with_suffix(".metadata.json"))
    if not success:
        raise DataError(f"forecast run incomplete; no fallback permitted; inspect {status_path}")
    return output
