# Step 4 — Evaluation and retrospective governance

This implements PRODUCT_CONTRACT.md without redefining it. It reads the frozen Step 3 predictions and prepared M5 data. It does not fit models or implement labor, inventory, rendering, or videos.

## Input and deterministic evidence

`commerce evaluate` validates 2,240 unique date/store/category/model keys against the common 560-observation holdout crossed with the four approved models. Prepared actuals are authoritative. Missing source fields, null keys, missing/duplicate/extra grid keys, changed hashes or wrong real-data classification stop canonical evaluation. Candidate-level audit logic additionally represents malformed predictions in adversarial tests. Invalid forecasts retain coverage and rejection evidence.

The CLI verifies the complete Step 3 manifest and SHA-256 of both inputs. It requires the prior hash-bound Step 3 deterministic/mutation record, default `.cache/step3-real-validation.json`; `--validation-record` accepts another repository-local copy. Its input hashes must match, and its real mutation rerun must have passed with zero difference. Missing or failed proof stops evaluation, rather than assuming success. The typed API requires an explicit deterministic_validated argument; false makes every model ineligible. The evaluator independently reruns all tables with shuffled input rows and compares every output at rtol=1e-10, atol=1e-8 before publication. Forecast files are never changed.

## Metric formulas

For valid postprocessed forecasts f and actual demand y:

| Metric | Formula |
|---|---|
| Signed error | f − y; positive is overforecast, negative underforecast. |
| Absolute error | abs(f − y). |
| WAPE | sum(abs(f − y)) / sum(y). |
| MAE | sum(abs(f − y)) / n_valid. |
| Bias | sum(f − y) / sum(y). |
| Underforecast rate | count(f < y) / n_valid. |
| Overforecast rate | count(f > y) / n_valid. Exact matches belong to neither. |
| Completeness | n_valid_unique_expected / n_expected; local candidates require 28/28. |
| Clipping rate | count(finite unique raw < 0) / count(finite unique raw). |
| Unit shortfall | sum(max(y − f, 0)). |
| Unit excess | sum(max(f − y, 0)). |

Direction rates use valid observations, as requested for Step 4, and always accompany valid/expected counts and completeness. Missing/invalid rows are never interpreted as correct. demand_volume includes all expected actual demand; actual_units is the denominator on valid coverage. Incomplete metrics are explicitly partial and cannot qualify a champion. Invalid predictions are never converted to zero.

Zero-demand denominators yield null WAPE/bias and undefined_zero_demand status. Empty groups yield null ratios/MAE, count zero and undefined_empty status. MAE may remain defined for zero-demand observations. Empty event/ordinary and SNAP groups remain explicit. CSV nulls are blank cells accompanied by statuses. Network ratios pool errors and demand for each model; they never average local WAPE. Network-by-model is also the model-level scorecard; there is no meaningless total that counts actual demand four times.

Outputs cover network/model, store, category, store-category, weekday, event/ordinary, state-specific SNAP-active/inactive, and horizon 1–28. Event means either event name is nonempty. Event/SNAP differences use the same model, include both groups' sample counts, and are observed associations, not causal claims.

## Eligibility, tie-breaking and comparisons

The YAML absolute-bias guardrail remains 0.10, inclusive. Eligibility requires one forecast on every one of the 28 expected dates; no extras, missing rows or duplicates; 100% valid coverage; finite raw/final values; nonnegative final forecasts; correct actual labels; successful/warning model status; and passing postprocessing. The latter requires forecast_units=max(raw_forecast_units,0) and was_clipped=(raw_forecast_units<0). Bias must be defined and within the unchanged guardrail. Deterministic validation must pass. candidate_eligibility.csv retains every rejection reason.

Eligible candidates sort by lowest unrounded WAPE, then fixed exact-tie order: seasonal_naive, holt_winters, hist_gradient_boosting, mlp. champions.csv has one row for each of 20 series and at most 20 selections. Null champion_model has exactly: **No eligible champion—review required**. The guardrail is never relaxed.

Comparisons include baseline WAPE/bias, champion WAPE/MAE/bias, WAPE-fraction difference, percentage-point improvement (100 times the difference), and relative improvement (difference/baseline WAPE). A zero baseline makes relative improvement null; incomplete baseline coverage makes comparison undefined. Baseline champions have zero absolute improvement. Negative improvement is retained if a lower-error baseline is ineligible.

Global eligibility requires qualifying in all 20 series, followed by lowest pooled WAPE with the same tie order. No globally eligible model is explicit. Champion counts and selected-portfolio summaries are separate. The portfolio and its baseline comparison use exactly the same covered series, disclose coverage, and never fill unassigned series.

**Every local selection, distribution, selected-portfolio summary and queue artifact is retrospective.** Selection and summary use the same holdout; these are not unbiased future-performance estimates. Frozen forecasts receive no selection feedback.

## Disagreement and review flags

Date/store/category disagreement = range of valid model forecasts / max(mean training demand for that series, 1 unit). The scale uses only training dates through the origin; its floor never changes WAPE denominators. Date evidence includes model count, training mean and scale. Fewer than two methods gives null and insufficient_model_coverage; two/three gives partial, four complete. Series disagreement is the mean of available date values, with date count, minimum model coverage and maximum retained.

The fixed YAML review rule is **mean disagreement > 0.50**. It was set before real Step 4 scoring and is not adjusted for visual interest. Undefined values are accompanied by coverage status, not represented as zero.

## SQL/Python reconciliation

prediction_errors.sql constructs signed/absolute/shortfall/excess errors. metric_rollup.sql independently pools all levels and preserves empty subgroup grids. Required network, store-category, event, SNAP, weekday, under/over, high-volume and DRI SQL files are executed. champion_map.sql emits a dataset only; champion_counts.sql independently ranks eligible candidates.

Python separately calculates all metric columns, counts, keys and statuses for every group, including network, store-category, event and SNAP. These reconcile with SQL at rtol=1e-10, atol=1e-8, including null locations; drift stops evaluation. Python champion counts must equal independent SQL winner counts. SQL ordering is explicit and numerical execution uses one thread.

## Exception logic fixed before real scoring

Under/over rankings order unit shortfall, unit excess, absolute bias and WAPE, with dimension/model tie-breaks. WAPE ranking requires the configured minimum seven observations. High-volume exceptions order absolute unit error, then demand volume, then store/category/date/model. They preserve actual/forecast units, signed/absolute errors, volume and champion status.

The queue has one subject per series: its champion, or unassigned_baseline_review_only when no champion qualifies. This is a review subject, not a substitute champion or portfolio forecast. Other model problems remain in rankings and scorecards.

Let V be actual volume over the 560 unique observations, D a subject series' volume, U its shortfall, A its absolute error, b its bias, g its disagreement and r its underforecast rate. Priority denominator max(V,1) is for diagnostics only. Fixed YAML weights and components:

| Component | Formula | Weight |
|---|---|---:|
| Volume | D/max(V,1) | 0.10 |
| Shortfall | U/max(V,1) | 0.30 |
| Absolute error | A/max(V,1), or volume-share × WAPE for complete coverage | 0.25 |
| Bias exposure | volume-share × abs(b) | 0.15 |
| Disagreement exposure | volume-share × g | 0.10 |
| Repeated underforecast exposure | volume-share × r | 0.10 |

Priority is the weighted sum, descending, with store/category/model ties. The configured top-ten flag leaves the full queue available. Undefined components contribute no numerical evidence and carry incomplete_evidence status. Volume weighting stops tiny-denominator percentages dominating material misses. Weights are disclosed assumptions, not fitted or causal findings.

Event-versus-ordinary narrative comparisons need at least seven observations in each group and defined WAPE. Otherwise evidence states insufficient evidence and makes no event attribution. No event penalty is added without supporting evidence. Each deterministic narrative contains observed_pattern, measured evidence with counts/period/model/series/comparison/ranking basis, a plausible planning risk, and a recommended later experiment with an owner. No LLM is used. Recommendations are proposals, not measured results. No DoorDash data or impact is claimed.

Evidence files are under outputs/p25_quick_commerce_control_tower/data/. evaluation.metadata.json records input/proof/config/SQL/artifact hashes and reconciliation/determinism results. See validation.md for the exact real measurements, full file inventory, command ledger and known repository failures.


## Step 7 reproducibility closeout

`commerce run-all` now produces fresh `outputs/p25_quick_commerce_control_tower/manifests/forecast_validation.json` by independently refitting after holdout-target mutation. `commerce evaluate` uses this record by default and verifies its prepared-data hash, prediction hash and configuration against the current run. The earlier Step 3 cache record described above is historical evidence, not a release prerequisite. Failed or absent proof stops evaluation. No metric, governance threshold or diagnostic ranking changed.
