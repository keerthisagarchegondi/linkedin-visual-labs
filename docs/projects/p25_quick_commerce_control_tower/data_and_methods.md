# Step 2 — Data provenance and feature contracts

## Real source

The pinned source is [Zenodo record 10203108](https://zenodo.org/records/10203108), DOI `10.5281/zenodo.10203108`. Only the following files are downloaded:

| File | URL | Published MD5 |
|---|---|---|
| sales_train_evaluation.csv | https://zenodo.org/records/10203108/files/sales_train_evaluation.csv?download=1 | b806dfc9f30a745102b708c09951f6aa |
| calendar.csv | https://zenodo.org/records/10203108/files/calendar.csv?download=1 | 3ffeab2991b0c8e861d008b39ea4c95c |

Files are streamed into repository-local `.part` files, checked against the published MD5 and source schema, independently SHA-256 hashed, and atomically promoted. Adjacent metadata records source URL, size, hashes, acquisition time, and whether bytes came from the download or explicit local input. Verified-cache reuse checks the metadata and rehashes the file. A missing or corrupt metadata record fails explicitly. No fixture or alternate mirror is used to recover a real-data failure.

Cache: `data/raw/p25_quick_commerce_control_tower/`. DuckDB spill: `.cache/p25_quick_commerce_control_tower/duckdb_spill/`. Existing Git rules ignore both locations. Local-file input must remain within this repository and match the same pinned real bytes.

## Aggregation and calendar validation

The sales header must contain the six M5 identifiers followed by the ordered complete `d_1` through `d_N` sequence. Real mode requires the evaluation edition's 1,941 observed days; it does not accept a truncated file. Source checks reject missing identifiers, duplicate item-store rows, incorrect stores/states, and invalid selected demand counts. Actual zeros remain zeros.

DuckDB scans the raw CSV as a wide view, filters FOODS/HOUSEHOLD, and sums day columns by store, state, and category. Only the twenty-row wide aggregate is materialized before unpivot. The only item-level pandas data is the small identifier table used for validation, not demand history. Configured limits are two threads and a 1GB DuckDB memory budget with repository-local spill. This budget is not a measured process-RSS bound. Memory errors must stop rather than reduce the analytical scope; batching was unnecessary for the verified run.

Calendar dates must be unique and continuous along the observed `d_N` sequence. Required weekday and month values must agree with actual dates. Missing observed dates and invalid SNAP flags fail validation. Event fields are retained, and absent optional second-event fields become empty strings. Future calendar dates do not enlarge the demand holdout.

Final grain is `date × store_id × category`, with state, observed-day identifier, demand, weekday, month, both event name/type pairs, all three source SNAP flags, the selected state SNAP indicator, and data classification. Every date must contain exactly the same twenty store-category combinations. Retaining original state SNAP flags makes the selected indicator auditable.

Real output: `outputs/p25_quick_commerce_control_tower/data/demand_daily.parquet`, with adjacent `demand_daily.metadata.json`. Explicit fixture output is instead under `data/fixture/`. Parquet is validated before atomic promotion. Prepared metadata contains source provenance, observed/training/holdout ranges, dimensions, resource configuration, and the Parquet hash. It is preparation metadata, not the final future portfolio run manifest.

## Common holdout

One forecast origin is the final training date. The final 28 observed dates are held out for all 20 series. The verified real source produces:

- 38,820 daily rows across 1,941 dates and 20 series.
- Training: 2011-01-29 through 2016-04-24 (38,260 rows).
- Holdout: 2016-04-25 through 2016-05-22 (560 rows).
- Holdout observed identifiers: `d_1914` through `d_1941`.

Those results follow schema and grain validation; they are not inferred from future calendar rows or separate per-series tails.

## Direct-horizon feature API

`build_features(daily, config.features)` returns a `FeatureSet` containing separate training/holdout predictors, separate actual targets, the common origin, historical feature names, and a holdout provenance table. Predictors use a date/store/category index; identity keys remain available for later training-only encoding. No encoding, scaling, feature selection, fitting, forecast generation, or evaluation is performed here.

| Feature | Demand source window relative to target date t |
|---|---|
| lag_28 | t-28 |
| lag_35 | t-35 |
| lag_42 | t-42 |
| lag_49 | t-49 |
| lag_56 | t-56 |
| mean_7_ending_lag_28 | t-34 through t-28 inclusive |
| mean_14_ending_lag_28 | t-41 through t-28 inclusive |

Calendar weekday, month, event names/types, and state SNAP status are assumed known at issuance for each target date. This assumption is explicit; they are not inferred from holdout demand.

The provenance table identifies target date, store, category, feature, source start/end, and origin. Every holdout feature's latest source date is at most both `t-28` and the forecast origin. Config validation rejects unsafe lags, near-target rolling endpoints, unknown transformations, and implicit scaler/target-encoding/random-validation options.

The initial 56 training dates lack complete historical features and are excluded only from the model-ready training feature table. The full prepared demand table is unchanged, and all 560 holdout rows remain. The real run yields 37,140 feature-training rows, 560 feature-holdout rows, 14 predictor columns plus identity index, and 3,920 historical holdout-provenance rows. Missing holdout history is an error; it is never imputed from holdout actuals.

Automated tests alter every holdout demand value and require identical predictors and provenance. An additional boundary test changes d_58: d_85 features remain identical because their latest permitted source is d_57, while d_86 lag 28 changes as expected. The mutation check also passed against the real prepared dataset. This protects feature generation; model-fitting leakage tests belong to the later forecasting implementation.

## Test-only fixture

The independent fixture contains 50 item rows, 112 observed demand days, 117 calendar days, twenty selected series, weekly patterns, real zero counts, events, and differing state SNAP flags. Two items per selected series test summation; HOBBIES items test exclusion. Its 2,240 expected aggregate rows use an independently constructed closed-form formula documented with hashes in the fixture directory. They were not generated by the DuckDB transformation being tested.

## Claim boundaries

Demand is public real M5 history; feature preparation is measured computation. Fixtures are synthetic test-only data. Labor assumptions remain illustrative but unused in Step 2. No forecasts, accuracy metrics, champions, operational impacts, inventory results, or media were produced. No DoorDash data or claimed DoorDash impact is involved.
