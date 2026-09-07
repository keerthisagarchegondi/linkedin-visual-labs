# Step 3 forecasting methods

`forecasting.py` implements the typed `ForecastMethod.forecast(ForecastInputs, CommerceConfig) -> MethodResult` protocol. `ForecastInputs` is a frozen dataclass containing the common immutable origin, training-only demand history, training predictors, separate training targets, and future predictors. It contains no holdout targets. `make_inputs` uses the unchanged Step 2 split and feature builder. Calendar/event/SNAP fields are treated as known at issuance. Estimators cannot access evaluation labels through this interface.

`SeasonalNaive`, `HoltWinters`, and the two configured `PooledForecaster` instances implement that same interface. `forecast_arena` freezes their predictions before `canonical_predictions` attaches actual demand for audit. No evaluation/governance, champion selection, diagnostic ranking, or operational optimization is performed.

## Fixed configurations

The existing YAML and its typed contracts are unchanged. No holdout-based tuning or parameter searches were performed.

| Method | Configuration |
|---|---|
| Seasonal naive | Exactly lag 28, zero fitted parameters, training history only. |
| Holt-Winters | 20 local statsmodels ExponentialSmoothing models; seasonal_periods=7, seasonal=add, trend=add, damped_trend=true; initialization_method=estimated; fit optimized=true, use_brute=false. Each forecasts 28 steps without refitting. |
| HistGradientBoostingRegressor | One pooled model; max_iter=200, learning_rate=0.1, max_leaf_nodes=31, l2_regularization=1.0, early_stopping=false, namespaced fixed random_state. |
| MLPRegressor | One pooled model; hidden_layer_sizes=(128,64,32), activation=relu, solver=adam, max_iter=500, alpha=0.0001, learning_rate_init=0.001, early_stopping=false, namespaced fixed random_state. |

Unspecified estimator defaults come from the dependency versions recorded in predictions.metadata.json. The same file records the full project YAML and execution settings. Project seed is 47; model random states use the shared `derive_seed(47, "p25_quick_commerce_control_tower:<method>") % 2**32`. The importance seed uses the same namespace with `importance`. Numerical libraries run with one thread during fitting/prediction; this also bounds CPU usage.

Pooled predictors are the approved Step 2 historical lags and shifted means plus calendar, state SNAP, store, and category. Date identifies rows and is not a numeric model input. Store, category, weekday, and both event name/type pairs receive dense deterministic one-hot encoding fitted on training data only; unknown categories map to all-zero indicators. Month, SNAP, and historical demand features are numeric. HGB receives numeric values without scaling. MLP uses a training-only StandardScaler for numeric predictors and a separate training-only StandardScaler for the target through TransformedTargetRegressor, which returns predictions in original demand units. No random validation set is created, and no holdout actual is passed to either scaler or encoder.

## Failures and canonical output

The approved IMPLEMENTATION_PLAN.md risk table says: **Model fails or produces invalid output: Record failure and exclude it; never substitute another method under its name.** Consequently seasonal-naive fallback for failed Holt-Winters fits is prohibited in this implementation. Deliberately failed fits retain the original exception type/message and have fallback_used=false and zero predictions. Other local Holt-Winters fits continue so status evidence is complete. Canonical publication requires all four methods to finish successfully with finite output; warnings with valid finite forecasts may be retained.

`model_status.parquet` records model identity, local series or ALL pooled scope, fit_status, fallback_used, convergence_status, iterations where available, warning/error summaries, training_seconds, prediction_seconds, prediction_count, clipping_count, and clipping_rate. Seasonal naive has zero training time and not_applicable convergence. Warning class names and messages are preserved. MLP ConvergenceWarning remains visible alongside valid forecasts. Runtime is observational, never a selection criterion.

The canonical grain is date/store_id/category/model_name. It must match the complete expected 2,240-key grid, exactly 560 rows per model and 28 dates per method-series. Columns are date, store_id, category, model_name, actual_units, raw_forecast_units, forecast_units, was_clipped, model_status. NaN, infinity, missing keys and duplicates are rejected. Finite negative raw predictions are preserved and clipped only in forecast_units; clipping flags and counts remain auditable.

The real command requires verified real prepared data. Fixture mode is explicit and isolated. A failed run writes status plus complete=false metadata and removes stale canonical predictions/importance at that same output location to prevent treating earlier results as the failed run's output. It does not create replacement forecasts or silently switch datasets.

## Bounded interpretation

The HGB table permutes each original predictor three times on the final 256 chronologically ordered training-feature rows (including store/category identity), using the fixed importance seed. It records mean/std increase in absolute error, sample size, repetition count, feature name, and `training_in_sample_interpretation` classification. This is a bounded global sensitivity summary of the pooled model, with in-sample and recent-training-sample limitations; it is not a holdout interpretation or an unbiased generalization estimate. It never selects features or tunes models. No SHAP subsystem is used.

## Outputs and reproducibility

Under `outputs/p25_quick_commerce_control_tower/data/`:

- predictions.parquet
- predictions.metadata.json
- model_status.parquet
- hist_gradient_boosting_importance.parquet

Explicit fixture mode uses the corresponding `data/fixture/` directory. All are ignored generated artifacts. The manifest records source SHA-256, configuration, dependency versions, seeds, date ranges, status evidence, execution settings and the prediction hash.

Deterministic checks compare the same inputs/configuration/seeds using rtol=1e-10 and atol=1e-8 for numerical forecasts. Runtime fields are excluded. Cross-version/platform byte identity is not promised. The unchanged real data range is 2011-01-29 through 2016-05-22, with common origin 2016-04-24 and holdout 2016-04-25 through 2016-05-22. Pooled models omit only the existing initial 56-day feature warmup; local methods retain the complete training history. All use the identical final 560 observations.

Offline tests verify independent lag-28 equality, 20 local weekly fits, original-error recording with prohibited fallback, actual estimator configurations, training-only encoder/scaler statistics, convergence warnings, the full prediction grid, clipping and invalid output rejection, manifest/CLI behavior, deterministic reruns, and unchanged forecasts after mutating every holdout actual. Real execution and measured results are recorded in validation.md.
