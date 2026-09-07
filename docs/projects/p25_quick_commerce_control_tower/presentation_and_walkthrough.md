# Step 6D — Modeling transparency and prototype calibration

The explicit Step 6D request authorizes presentation refinement only and retains the 30-second video override from Step 6B/6C. The approved plan, product contract, analytical results and champion PNG are unchanged. Step 7 hardening is documented in validation.md; presentation remains frozen.

## HTML reading order

Overview → Forecast Arena → Champion Map → Forecast Diagnostics → Labor Optimizer → Scenario Lab → Governance / DRI. All 27 previous charts remain, with one additional HGB importance chart. The core arc is Context → Data → Forecast Decision → Diagnosis → Operating Decision → Prototype Validation → Next Best Action.

Decision 01 explains that HGB is the strongest single network-wide method at 7.94% WAPE, but a global model (one method everywhere) does not pass governance on all 20 series. Local champions are the best eligible methods for individual store-categories within one governed framework, not 20 separate projects. TX_3 / FOODS is routed to review rather than given an ineligible model. The unchanged distribution is 9 HGB, 7 MLP, 3 Holt-Winters, 1 review state. The 19-series local portfolio has 7.38% WAPE versus 10.19% on identical seasonal-naïve coverage: a retrospective 2.80 percentage-point difference, selected and scored on the same holdout.

The Executive Decision explains what the prototype captured: fixed-capacity redistribution and Base configured critical store-days of 47 → 19. It then discloses what needs calibration: actual uncovered workload increased from 1,494.77 to 1,540.91 hours under equal priorities. The current objective needs richer operational economics before production use.

## Modeling transparency

The Forecast Arena disclosure defines the target as daily demand units at date × store × category. Independent variables are lags 28/35/42/49/56, 7- and 14-day historical means ending at t−28, weekday/month, both calendar event name/type slots, state-specific SNAP, store and category.

Preparation validates schemas, identifiers, ordered d_N columns, required categories, continuous dates, unique canonical grain, nonnegative integer demand, full calendar coverage and SNAP mapping. DuckDB aggregates item-level wide data before unpivoting the small result. Published raw checksums and SHA-256 support verified deterministic caching. Missing demand/required canonical values are rejected, not imputed. Empty event labels are legitimate; absent optional second-event fields become empty strings. Warmup rows without complete historical features are excluded only from model-ready training; the complete holdout remains.

Every demand-derived input is available at origin. Lag 28+ avoids reading actual demand from inside the 28-day forecast window. Event/SNAP schedules are assumed known at origin. Seasonal naïve has no scaling; Holt-Winters fits local series without feature standardization. HGB passes numeric inputs through and one-hot encodes store, category, weekday and event fields. MLP uses the same encoding plus training-only numeric StandardScaler and training-only target scaling with inverse transformation to demand units. Its layers remain 128/64/32.

Validation separates forecast performance (WAPE, MAE, signed bias) from eligibility (28 unique dates, finite values, nonnegative recorded postprocessing, absolute bias ≤10%, deterministic validation). Lowest eligible WAPE wins with stable tie-breaking; no eligible method prompts review.

## Which signals mattered most?

The new chart reads the unchanged Step 3 hist_gradient_boosting_importance.parquet. It shows the top eight raw input features, measured mean MAE increases and permutation standard deviations. It does not group or normalize values. Bars compare effects directly in daily demand units.

| Rank | Feature | Mean MAE increase |
|---|---|---:|
| 1 | lag_28 | 209.683618 |
| 2 | mean_7_ending_lag_28 | 201.437829 |
| 3 | lag_35 | 65.697076 |
| 4 | lag_42 | 60.843618 |
| 5 | weekday | 46.128927 |
| 6 | mean_14_ending_lag_28 | 38.719103 |
| 7 | lag_49 | 36.699602 |
| 8 | lag_56 | 29.090967 |

Label: **Retrospective model interpretation**. This is bounded in-sample evidence: last 256 training feature rows, three permutations per input, not holdout importance or tuning evidence. Contributions are predictive, not causal; correlated lags can share signal. Standard deviations are not confidence intervals. The complete raw artifact is embedded as canonical evidence, including zero values for signals that did not contribute in this particular sample.

## Diagnostics and operating decisions

Diagnostics convert misses into an action backlog: Forecast error → prioritize → investigate → form hypothesis → test experiment → recalibrate/retrain. WI_2 / FOODS, CA_1 / FOODS and TX_3 / FOODS are the highest-priority review opportunities. Pattern, measured evidence, operational implication and experiment remain distinct; no root cause is invented.

The final Base allocation remains the average over all 28 dates:

| Store | Optimized hours/day | Difference vs proportional |
|---|---:|---:|
| CA_1 | 50.05 | +3.24 |
| CA_2 | 49.73 | +2.56 |
| CA_3 | 58.10 | -10.63 |
| CA_4 | 29.18 | +1.15 |
| TX_1 | 38.88 | +2.08 |
| TX_2 | 45.73 | +2.59 |
| TX_3 | 42.79 | +2.24 |
| WI_1 | 29.25 | -9.40 |
| WI_2 | 61.13 | +3.59 |
| WI_3 | 43.83 | +2.58 |

Total average used capacity remains 448.67 hours/day, from a 480-hour cap. Eight stores gain hours on average; CA_3 and WI_1 lose hours. The optimizer reallocates available hours; it creates no labor.

**PROTOTYPE VALIDATION — DID THE OBJECTIVE CAPTURE THE RIGHT OUTCOME?** asks:

1. Constraint performance: yes; fixed capacity, staffing bounds, nonnegative allocation and workload constraints were respected.
2. Allocation behavior: yes; Base configured critical store-days decrease 47 → 19.
3. Retrospective outcome: not yet; actual uncovered workload increases 1,494.77 → 1,540.91 hours. All three tested scenarios retain the worse optimized retrospective coverage.
4. Next calibration: the engine functions as designed, but its first-pass objective captures only part of the operating decision. This conditional comparison is not a causal or production impact estimate.

Production-readiness and optimizer-input disclosures cover differentiated service priorities; category-specific shortage/SLA economics; actual productivity; employee shifts and local staffing rules; labor availability; peak-period service targets and event policies; inventory; replenishment; and uncertainty. The prototype intentionally uses equal priorities and illustrative productivity. Actual operational economics and untouched-period validation are required before deployment.

## Integrated Governance / DRI

One four-block operating loop: MONITOR (WAPE/bias/completeness/disagreement), REVIEW (ineligible series/exceptions/persistent drivers), EXPERIMENT (features/recalibration/retraining/objective/assumptions), DEPLOY / ESCALATE (validated challengers, ambiguous series, untouched-period objective checks). Review cadence, original numeric triggers and cross-functional ownership remain in one disclosure. Metric definitions are not repeated. The final takeaway explains the end-to-end prototype, retrospective forecast improvement and operational inputs needed next, without claiming production impact.

One visible provenance statement uses public M5 retail demand and illustrative labor/inventory wording. Stricter no-DoorDash-data/no-DoorDash-impact language remains in technical contracts.

## Videos

Both retain the persistent animated ten-store network, 1080 × 1350 H.264 yuv420p output, 30 fps and 30 seconds. Their first payoff is complete by 15 seconds, followed by a second hook and final answer at 27 seconds. Technical preparation details belong in HTML.

### forecast_model_arena

| Time | Animated beat | Muted caption |
|---|---|---|
| 0–3s | One forecast model for every store? | One network contains different demand patterns. |
| 3–7s | Four approaches. The SAME 28 days. | 20 series. Four approaches. Same 28-day holdout. No holdout leakage. |
| 7–11s | HGB leads: 7.94% WAPE | Strongest network score. Lines show a priority review opportunity. |
| 11–15s | Different stores favor different approaches. | No model qualified everywhere. RETROSPECTIVE selection is not future performance. |
| 15–23s | Which forecast should run each store? | TX_3 / FOODS: no eligible champion. Governance routes this exception to review. |
| 23–27s | Where should the owner investigate next? | WI_2 / FOODS. CA_1 / FOODS. TX_3 / FOODS. High-value improvement opportunities. |
| 27–30s | Use governed local champions. | Review the exceptions. Improve the features. Re-test. |

### forecast_to_labor_optimizer

| Time | Animated beat | Muted caption |
|---|---|---|
| 0–3s | 480 labor hours. Ten stores. | Where should the hours go? |
| 3–7s | Demand becomes required labor. | Illustrative productivity assumptions convert forecast units into workload hours. |
| 7–11s | Proportional versus optimized allocation. | Move the same hours between stores. Labor is reallocated, not created. |
| 11–15s | HiGHS moves the SAME labor hours. | Configured critical days decrease; actual uncovered hours increase. Same capacity, different allocation. |
| 15–22s | The allocation engine worked. | Actual coverage worsened under equal priorities. The objective needs richer business inputs. |
| 22–27s | What is missing from the decision? | Service priorities, productivity, shift constraints, shortage costs and inventory / replenishment. |
| 27–30s | Forecast better. Encode the business objective better. | Then optimize. Validate on an untouched period before adoption. |

Video 1 closes with “One network. Different demand patterns. Use governed local champions.” and “Review the exceptions. Improve the features. Re-test.” It retains no-global-eligibility, TX_3 / FOODS review and the retrospective caveat.

Video 2 explains “The allocation engine worked. The objective needs richer business inputs.” The configured 47 → 19 and actual 1,494.77 → 1,540.91 comparisons remain visible. Missing-input activation now includes shift constraints and inventory/replenishment. It closes “Forecast better. Encode the business objective better. Then optimize.”

## Validation boundary

No browser geometry is claimed: prior local-file browser policy blocked that surface, and no workaround was attempted. Automated validation covers embedded resources, chart/evidence reconciliation, isolated actual tab-controller execution, responsive CSS contracts, PIL text geometry, full media decode and decoded-frame comparisons. The user subsequently accepted browser interaction, layout and muted pacing in the Step 6D manual review (PASS); that acceptance is bound to the four artifact hashes in manual_acceptance.json. See validation.md for command/results and the exact Step 6D scope.
