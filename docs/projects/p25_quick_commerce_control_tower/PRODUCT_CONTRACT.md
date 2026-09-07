# Project 5 — Quick-Commerce Forecast Model Arena & Network Optimizer

This is the authoritative analytical and recruiter-facing narrative contract for Project 5. Supporting code, configuration, SQL, documentation, evidence tables, dashboard, images, captions, and videos must satisfy it. The approved implementation sequence is preserved in IMPLEMENTATION_PLAN.md. Neither document authorizes work beyond the user's explicitly requested step.

- Repository: `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
- Active branch: `project/p26-quick-commerce-control-tower`.
- Internal package: `p25_quick_commerce_control_tower`.
- Preserve the existing repository architecture and quality gates.
- Use `reference/project5/` only for local styling and layout inspiration. Its synthetic preview metrics are never final evidence. Keep the exact ignore rule `reference/project5/` and never stage or commit those assets.

## 1. Business question and intended outcome

**Which forecasts should own each store-category, why do they miss, and how should a constrained labor network respond?**

The product is a recruiter-facing public-data portfolio prototype showing forecast-accuracy ownership: compare forecasting methods, diagnose variance, select and govern a champion/challenger portfolio, and translate demand into constrained labor and limited inventory decisions. Recommendations must follow measured evidence and disclosed assumptions. A more sophisticated model is not inherently a better operating choice.

The operating workflow is:

**Forecast → Select → Diagnose → Allocate → Stress-test.**

## 2. Data scope and provenance

- Public real M5 demand history for the portfolio run.
- 10 stores.
- FOODS and HOUSEHOLD categories.
- 20 store-category daily series aggregated from item-level demand.
- One common final 28-day observed holdout: 560 store-category-date observations.
- Calendar event fields, including event names and types.
- State-specific SNAP fields joined to the correct store state.
- Demand history and source checksums recorded in the run manifest.

Prefer credential-free programmatic acquisition with a verified real-data cache. Determine the holdout from observed sales columns; future calendar rows do not extend the observed demand period. Reject corrupt data, missing dates, duplicate keys, invalid demand, and incomplete joins. Preserve genuine zero demand.

Aggregate the wide M5 file efficiently with DuckDB before unpivoting the small store-category result. Do not load unnecessary item-level history into pandas memory. A resource fallback may batch aggregation without reducing data scope.

The automated-test fixture is tiny, deterministic, explicitly synthetic/test-only, and separate from real portfolio evidence. A real-data acquisition failure must never silently substitute synthetic demand.

Calendar and SNAP features assume their schedules are known at forecast issuance. State this assumption; do not infer unavailable future information from realized demand.

## 3. Four-model forecast arena

| Method | Plain-English explanation | Required implementation |
|---|---|---|
| Seasonal naïve | Repeat the demand observed four weeks earlier. | Lag 28. |
| Holt-Winters | Smooth the historical level and documented trend while learning a repeating weekly pattern. | Weekly seasonality, with fixed documented specification. |
| Gradient boosting | Learn nonlinear relationships between safe historical demand, store/category identity, and calendar conditions. | `HistGradientBoostingRegressor`. |
| Neural challenger | Learn demand relationships through three connected hidden layers after training-only scaling. | `MLPRegressor(hidden_layer_sizes=(128, 64, 32))`. |

All methods forecast the same 28 expected dates from the same origin. Preserve method identity, fixed seeds, settings, training coverage, fit status, convergence information, and raw predictions.

**Model sophistication is not the decision rule.** Eligibility and measured WAPE determine champions. A baseline may win. Do not promise that any challenger improves accuracy.

Do not add TensorFlow, PyTorch, LSTM, Transformer forecasting, Prophet, GPU dependencies, or broad hyperparameter searches. Preserve existing dependencies used by unrelated projects, including existing PyTorch.

## 4. Leakage contract

- No actual holdout demand may enter predictors through lag 1, lag 7, rolling 7, rolling 14, preprocessing, hidden validation, model selection, or feature transformations.
- Lag 28 and longer are permitted for the direct 28-day holdout when every source demand observation lies before the common forecast origin.
- Rolling features must have safe endpoints. A seven-day rolling feature for date `t` may end at `t−28`; it must not end at `t−1`.
- Encoders, scalers, and transformations are fitted only on training data.
- Disable automatic random early-stopping validation. Any later approved validation procedure must respect chronology and remain inside training data.
- Fix feature choices and hyperparameters before examining holdout outcomes.
- Automated leakage tests are mandatory, including mutation of all holdout actual demand while confirming that features and forecasts remain unchanged.

The ban on holdout-driven model selection applies to fitting, tuning, feature design, and hidden validation. The explicitly approved retrospective champion selection below uses holdout errors after forecasts are frozen. That exception must be disclosed and cannot feed back into fitted forecasts or be presented as prospective evaluation.

## 5. Metrics and comparison rules

Let actual demand be `y`, postprocessed forecast be `f`, and signed error be `f − y`.

| Metric | Contract |
|---|---|
| WAPE | `sum(abs(f − y)) / sum(y)`. |
| MAE | Mean `abs(f − y)` in daily demand units. |
| Forecast bias | `sum(f − y) / sum(y)`; positive is overforecast, negative is underforecast. |
| Underforecast rate | Number of expected dates with a valid forecast below actual divided by the number of expected dates. |
| Overforecast rate | Number of expected dates with a valid forecast above actual divided by the number of expected dates. Exact matches count in neither direction. |
| Event-day WAPE | WAPE on dates with a calendar event. |
| Ordinary-day WAPE | WAPE on dates without a calendar event. |
| SNAP-day WAPE | WAPE where the store state's SNAP flag is active. |
| Non-SNAP WAPE | WAPE where the store state's SNAP flag is inactive. |
| Prediction completeness | Valid unique expected predictions divided by 28 for each method-series. |
| Model disagreement | Per-date range across valid model forecasts divided by a documented training-derived demand scale, then summarized per series. Show the number of contributing models; insufficient model coverage is an explicit status. |
| Negative clipping rate | Count of finite negative raw forecasts divided by count of finite raw forecasts. Preserve raw and clipped values. |

Missing or invalid forecasts are reported explicitly, never silently dropped to improve a score. Incomplete results cannot qualify for selection. Direction rates must be shown with completeness so missing predictions are not interpreted as correct predictions.

Use pooled numerators and denominators for network WAPE. Do not average local WAPEs as the network headline. Empty subgroups and zero-demand denominators receive an explicit undefined status. Do not invent a zero WAPE or infinite percentage to hide an undefined calculation.

Baseline improvement must identify whether it is a percentage-point WAPE difference or relative improvement. Relative improvement against zero baseline WAPE is undefined. Every comparison uses identical observation coverage.

## 6. Champion eligibility and selection

Select champions separately for every store-category. An eligible model must satisfy all of the following:

1. Exactly 28 expected dates, with no extra or duplicate dates.
2. No missing, NaN, or infinite predictions.
3. Nonnegative forecasts after documented postprocessing.
4. Absolute bias inside the configured guardrail; the approved initial configurable guardrail is 10%.
5. Deterministic validation passes.

Among eligible models, the lowest-WAPE model wins. Apply documented stable tie-breaking. Preserve rejected candidates and their rejection reasons in evidence.

Clip finite negative predictions to zero and report the clipping rate; clipping does not repair missing or infinite values.

Every store-category has one selected champion when any candidate qualifies, otherwise the explicit state:

**No eligible champion—review required.**

Never relax guardrails automatically. A valid seasonal-naïve contingency may support a separately labeled illustrative labor plan, but it is not an eligible champion if it failed governance. Disclose contingency coverage in operational results.

The global eligible winner must qualify across all required series and have the lowest pooled WAPE among global eligible candidates. If none qualifies, show an explicit unavailable state.

### Retrospective local-champion caveat

**Local champion portfolio performance is retrospective because selection and summary use the same holdout. Do not present it as an unbiased future-performance estimate.**

Separate the global model comparison, local champion distribution, and retrospective selected-portfolio performance. Later untouched evaluation is required for a prospective production-promotion claim. No selection feedback may alter the already-frozen holdout forecasts.

## 7. Diagnostic story and exception queue

Use DuckDB SQL to produce network and store-category scorecards, event/ordinary analysis, SNAP/non-SNAP analysis, day-of-week analysis, underforecast and overforecast rankings, high-volume exceptions, and a Forecast Accuracy DRI exception queue.

Every root-cause item must follow:

**Observed pattern → measured evidence → operational implication → recommended experiment**

Evidence must be numerical and deterministic: include affected series/dates, sample count, comparison group, metric values, and the ranking basis. Use stable ordering and documented priority rules based on volume, shortfall, bias, disagreement, and repeated misses.

Do not claim causation from event, SNAP, or calendar associations unless the data actually supports causal evidence. In this historical backtest, ordinary subgroup comparisons are associations. Label causal explanations as hypotheses to test, not established root causes.

Recommendations must name a model, data, or process experiment and a suggested owner. Do not claim repeatability beyond the observed evidence. Sparse groups receive an insufficient-evidence status rather than an invented explanation.

## 8. Labor optimization contract

### Inputs and illustrative assumptions

Champion forecasts convert to workload under clearly illustrative category productivity assumptions. For store `s` and date `d`, workload is the sum across categories of forecast units divided by units per labor-hour.

Required inputs are:

- Forecasts, with champion or contingency provenance.
- Illustrative category productivity in units per labor-hour.
- Minimum store staffing.
- Maximum store staffing.
- Documented shift length to convert staffing limits into labor-hours.
- Daily network labor cap.
- Labor cost per hour.
- Priority-weighted uncovered-workload penalty.

Priority weights are configured assumptions and cannot be selected from holdout errors to manufacture an improvement. Continuous labor-hours represent a capacity plan rather than an integer employee schedule.

### Constraints and objective

Let `h[s,d]` be allocated labor-hours, `u[s,d]` uncovered workload-hours, `w[s,d]` required workload-hours, `c[s,d]` hourly labor cost, and `penalty[s,d]` the priority-weighted uncovered-hour penalty.

Minimize:

```text
sum(c[s,d] * h[s,d] + penalty[s,d] * u[s,d])
```

Subject to:

```text
minimum_hours[s,d] <= h[s,d] <= maximum_hours[s,d]
sum_over_stores(h[s,d]) <= network_cap[d]    for every date d
u[s,d] >= w[s,d] - h[s,d]
u[s,d] >= 0
```

Use a proportional heuristic baseline and `scipy.optimize.linprog` with HiGHS. The heuristic first meets minima and then distributes remaining capacity proportionally to workload while respecting maxima. Both plans use the same inputs, capacity, cost, and priority assumptions.

### Fixed-capacity narrative and reporting

**The optimizer reallocates fixed available capacity. The optimizer never creates labor.**

Report improved shortages, worsened shortages, remaining gaps, service-versus-cost trade-offs, labor used, unused capacity, labor cost, uncovered hours, weighted penalty, and critical store-days. Define the critical-store-day threshold in configuration and disclose it with the results.

An optimal objective does not guarantee improvement in every individual store or every service metric. Show the lower-priority trade-offs. If either method leaves capacity unused, disclose it explicitly instead of claiming identical hours were used.

Infeasible staffing limits fail the scenario with constraint evidence; do not increase capacity automatically. A solver failure may retain a feasible heuristic as a labeled fallback, without claiming an optimized result.

## 9. Scenario definitions

| Scenario | Required transformation | Capacity |
|---|---|---|
| Base | Original forecasts and illustrative productivity. | Fixed configured daily caps. |
| +15% demand | Forecast demand multiplied by 1.15. | Unchanged. |
| -10% productivity | Productivity multiplied by 0.90, so required workload increases by `1 / 0.90`. | Unchanged. |

Recompute both plans for every scenario. Show updated labor shortfall, critical store-days, remaining trade-offs, and an evidence-backed recommended response. A proposed capacity change is a recommendation outside the fixed-capacity scenario, not a hidden change to its calculation.

## 10. Limited inventory proxy

- Synthetic on-hand inventory only.
- Forecast days of cover.
- Deterministic stockout-risk status based on documented assumptions and thresholds.
- Clearly labeled illustrative wherever shown.
- Not a probability estimate.
- Not a replenishment optimizer.

Use deterministic construction of synthetic inventory and explicit zero-demand handling. The proxy must not expand into ordering, supplier, SKU replenishment, or inventory optimization work.

## 11. Complete dashboard contract

The report must be one self-contained HTML file. Embed all required scripts, styles, chart data, and images so it works without network access. Use the same canonical evidence as tables and media. Reference styling may inspire the design, but this contract overrides the old preview narrative.

### Header

- Business question.
- Public M5 scope.
- 10 stores × 2 categories: FOODS and HOUSEHOLD.
- Common final 28-day holdout.
- Real versus illustrative data statement.
- Forecast → Select → Diagnose → Allocate → Stress-test.

### Executive Decision

- Global eligible winner or explicit unavailable state.
- Local champion distribution.
- Improvement versus seasonal naïve, with comparison type and coverage stated.
- Highest-priority forecast exception.
- Labor-risk impact under illustrative operating assumptions.
- Three evidence-backed operating recommendations.
- Visible retrospective classification for any selected-portfolio performance.

### Model Arena

- Plain-English explanation of all four models.
- Same-holdout statement.
- Definitions of WAPE, MAE, bias, completeness, and disagreement.
- Champion eligibility and selection rule.
- Model sophistication is not the selection rule.
- Invalid/incomplete candidate status without concealed failures.

### Champion Model Map

- 10 store rows.
- FOODS and HOUSEHOLD columns.
- Champion/status in each of the 20 cells.
- WAPE.
- Bias.
- Improvement versus seasonal naïve.
- High-disagreement review flag.
- Summary counts by model and an explicit count/status for unassigned series.
- Undefined metrics are labeled, not replaced with fabricated values.

### Why Forecasts Missed

For prioritized exceptions show:

- Observed pattern.
- Numerical evidence.
- Operational implication.
- Recommended experiment.

Include evidence coverage and distinguish association from causation.

### Labor Optimizer

- Inputs.
- Illustrative productivity, staffing, capacity, cost, and priority assumptions.
- Constraints.
- Objective.
- Proportional versus optimized comparison.
- Fixed-capacity explanation.
- Service-versus-cost trade-off.
- Remaining shortages, including worsened shortages.
- Labor used and unused capacity.

### Scenario Lab

- Base.
- +15% demand.
- -10% productivity.
- Updated labor shortfall.
- Critical store-days.
- Recommended response.
- Limited inventory proxy, explicitly synthetic and illustrative.

### Governance and Assumptions

Clearly distinguish:

- Public real M5 historical demand.
- Measured historical backtest.
- Retrospective local champion selection.
- Illustrative productivity.
- Illustrative labor capacity.
- Synthetic inventory.
- Prototype optimization.
- No DoorDash data.
- No claimed or measured DoorDash impact.

### Forecast Accuracy DRI

Describe how the owner would:

- Maintain and monitor champion/challenger models.
- Monitor WAPE, bias, completeness, clipping, and model disagreement alongside operational impact.
- Maintain a repeatable variance-driver backlog grounded in measured evidence.
- Prioritize model, data, and process experiments.
- Define and publish retraining thresholds and review windows.
- Define and publish recalibration thresholds for persistent directional bias.
- Define and publish escalation thresholds for invalid predictions, no eligible champion, disagreement, and operational shortfall.
- Coordinate Operations, Product, Engineering, and Data Science.

Thresholds and review windows must be explicit in the eventual configuration and report, not hidden in prose or tuned to claim better holdout results. Operations owns capacity and service assumptions; Product coordinates decision usefulness; Engineering owns reliable data and execution; Data Science owns forecast evaluation, leakage controls, and challenger experiments. Present these as proposed ownership practices for the prototype, not evidence of an operating production service.

## 12. Complete video contracts

Every scene must contain explanatory captions and remain understandable while muted. Captions must convey the analytical point, evidence, and relevant limitation without requiring narration. Final claims must be generated from measured evidence rather than copied from preview text.

Each final recruiter video is approximately 45–60 seconds. Use deterministic scene timing with sufficient reading time. Show the actual outcome even when a challenger or optimizer does not improve a metric.

### Video 1 — Forecast Model Arena

**Title: Four Forecasting Methods Enter. Which One Should Run the Network?**

1. **Business question and real M5 scope.** Introduce ten stores, two categories, twenty daily series, and the ownership decision. Caption the public-data provenance.
2. **Common 28-day holdout and leakage boundary.** Show the training/holdout separation and explain that all methods forecast the same dates without actual holdout demand entering features.
3. **Four methods explained plainly.** Explain lag-28 seasonal naïve, weekly Holt-Winters, gradient boosting, and the 128/64/32 MLP challenger. State that sophistication is not the selection rule.
4. **Measured global scorecard and baseline comparison.** Show comparable WAPE and bias, completeness/eligibility, and improvement or deterioration against seasonal naïve. Show unavailable status when necessary.
5. **Local champion map and review flags.** Show the 10 × 2 map, champion distribution, local errors/bias, baseline comparison, and high-disagreement review flags. Preserve no-eligible-champion states.
6. **Eligibility, disagreement, retrospective caveat, and ownership loop.** Explain the guardrails and lowest-WAPE rule, why disagreement prompts review, and why local-portfolio performance is retrospective. Close with the forecast owner's monitoring and experiment loop.

### Video 2 — Forecast-to-Labor Optimizer

**Title: The Best Forecast Still Needs an Operating Decision**

1. **Champion forecasts become workload under illustrative assumptions.** Explain units-to-hours conversion and any disclosed contingency coverage.
2. **Staffing bounds, fixed network capacity, costs, and objective.** Show minimum/maximum staffing, daily cap, labor cost, and priority-weighted uncovered-workload penalty.
3. **Proportional versus optimized allocation.** Compare the heuristic with HiGHS using identical assumptions and capacity. Caption that reallocation cannot create labor.
4. **Improved shortages, remaining gaps, and service-versus-cost trade-off.** Show improved and worsened shortages, uncovered hours, cost, labor used, and unused capacity. Do not imply that every store improves.
5. **Base and both stress scenarios.** Show +15% demand and productivity × 0.90 with capacity fixed, updated shortfall, critical store-days, and recommended responses.
6. **Fixed-capacity operating loop, response recommendations, and provenance.** Connect forecast review, staffing decisions, stress testing, and coordination. State that labor inputs are illustrative, optimization is a prototype, and there is no DoorDash data or claimed DoorDash impact.

## 13. Classification and claim boundaries

| Content | Required classification |
|---|---|
| Historical demand | Public real M5 historical demand; cite source and record provenance. |
| Individual model holdout results | Measured historical backtest on a common frozen horizon. |
| Locally selected portfolio | Retrospective selection and summary on the same holdout, not an unbiased future estimate. |
| Productivity, staffing limits, network cap, costs, priorities | Illustrative operating assumptions. |
| On-hand inventory | Synthetic and illustrative. |
| Allocation and stress-test outcomes | Prototype optimization results conditional on disclosed forecasts and assumptions. |
| Fixture and supplied previews | Synthetic/test or styling reference; never final portfolio evidence. |
| DoorDash connection | No DoorDash data. No claimed or measured DoorDash impact. |

Do not substitute simulated shortages avoided for measured company service improvement. Numerical operational effects must be labeled as conditional prototype results. No causal claim follows merely from event, SNAP, or calendar subgroup differences.

## 14. Output acceptance criteria

- One 1080 × 1350 champion-model PNG, with all required map fields and readable safe margins.
- Two 1080 × 1350 H.264 MP4 videos.
- 30 fps.
- `yuv420p`.
- Approximately 45–60 seconds per final recruiter video.
- Explanatory captions in every scene; both videos understandable while muted.
- One self-contained HTML report implementing every required dashboard section.
- CSV/Parquet evidence tables sufficient to reproduce every headline number and diagnostic ranking.
- One run manifest containing configuration, seed, Git revision when available, source hashes, dependency versions, model status/settings, dimensions, runtime, measured metrics, optimizer status, assumptions, artifact hashes, and validation results.
- Packaged deterministic FFmpeg resolution with executable/version provenance.
- No silent PATH dependency for encoding or validation.
- No preview metrics used as final evidence.

Validate actual dimensions, codec, frame rate, pixel format, duration, frame count, and full decoding. Inspect caption readability, text overflow, and scene transitions. Validate HTML offline and reconcile report, image, video, and table values against the canonical evidence.

Automated leakage, metric, governance, SQL, optimization, fixture end-to-end, and output-contract tests are mandatory during their respective implementation steps. Full Ruff formatting/lint, strict mypy, pytest, and applicable repository quality gates must pass without weakening existing tests. Record unavailable or failed states honestly; do not claim overall product completion when required acceptance criteria remain unmet.

Keep downloaded raw data, caches, fitted models, local previews, and generated large media out of Git. Do not modify unrelated projects. The continuity contract remains unchanged unless an existing gate explicitly requires an explained compatible update preserving identity, ancestry, and earlier-project baselines.
