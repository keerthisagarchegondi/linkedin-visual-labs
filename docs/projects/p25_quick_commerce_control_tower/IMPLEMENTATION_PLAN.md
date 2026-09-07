# Project 5 — Approved revised implementation plan

This document preserves the complete revised plan approved in the conversation. The plan describes future implementation; only an explicitly requested step is authorized. The subsequent documentation/governance request additionally specifies the final video titles and approximately 45–60 second durations, recorded in PRODUCT_CONTRACT.md.

This revised plan incorporates all mandatory corrections. It preserves the approved architecture, analytical decisions, and deliverables. **No implementation, file changes, package installation, or Git mutations are authorized at this stage.**

**1. Repository assessment and scope**

The previous read-only inspection confirmed:

- Active branch: `project/p26-quick-commerce-control-tower`.
- Internal package: `p25_quick_commerce_control_tower`.
- Setuptools packaging with `src/linkedin_visual_labs`.
- Python requirement: `>=3.13,<3.14`.
- Central dependencies and development tools in `pyproject.toml`.
- Typer applications exported through `projects/__init__.py` and registered in the top-level CLI.
- Shared utilities for paths, YAML configuration, structured logging, randomness, plotting, animation, media validation, and manifests.
- Pytest conventions using typed tests, fixtures, `tmp_path`, and `CliRunner`.
- General GitHub Actions CI running formatting, Ruff, strict mypy, and pytest.
- Existing repository continuity tooling that checks environment, identity, ancestry, cleanliness, and synchronization.
- Seven supplied reference assets under `reference/project5/`, with synthetic preview results.
- Working-tree status showing `?? reference/`.

Reuse the existing infrastructure. Keep unrelated project code, dependencies, tests, and workflows untouched.

The reference assets remain local. Use their visual styling and layout as inspiration; the approved product requirements govern narrative and analysis.

**2. Proposed project tree**

All paths below are relative to `D:\linkedin-visual-labs-git\linkedin-visual-labs`. These are planned additions only.

```text
configs/
  p25_quick_commerce_control_tower.yaml

sql/p25_quick_commerce_control_tower/
  aggregate_demand.sql
  prediction_errors.sql
  network_scorecard.sql
  store_category_scorecard.sql
  event_analysis.sql
  snap_analysis.sql
  day_of_week_analysis.sql
  under_over_rankings.sql
  high_volume_exceptions.sql
  dri_exception_queue.sql

src/linkedin_visual_labs/projects/p25_quick_commerce_control_tower/
  __init__.py
  cli.py
  config.py
  models.py
  data.py
  features.py
  forecasting.py
  evaluation.py
  diagnostics.py
  optimization.py
  inventory.py
  visualization.py
  video.py
  reporting.py
  validation.py
  pipeline.py

tests/projects/p25_quick_commerce_control_tower/
  __init__.py
  conftest.py
  test_config.py
  test_models.py
  test_data.py
  test_features.py
  test_leakage.py
  test_forecasting.py
  test_evaluation.py
  test_champion_governance.py
  test_diagnostics.py
  test_optimization.py
  test_inventory.py
  test_visualization.py
  test_video.py
  test_reporting.py
  test_validation.py
  test_cli.py
  test_pipeline.py
  test_project_contract.py

tests/fixtures/p25_quick_commerce_control_tower/
  config.yaml
  sales_train_evaluation.csv
  calendar.csv
  expected_aggregates.csv
  fixture_manifest.json

docs/projects/p25_quick_commerce_control_tower/
  IMPLEMENTATION_PLAN.md
  PRODUCT_CONTRACT.md
  README.md
  data_and_methods.md
  governance_and_assumptions.md
  storyboard.md
  validation.md
```

`IMPLEMENTATION_PLAN.md` will store the final approved plan when implementation is authorized.

`PRODUCT_CONTRACT.md` will be the authoritative recruiter-facing analytical and narrative contract. Supporting documentation will elaborate on it without redefining its requirements.

Generated outputs:

```text
outputs/p25_quick_commerce_control_tower/
  data/
    demand_daily.parquet
    predictions.parquet
    model_status.csv
    store_category_scorecard.csv
    network_scorecard.csv
    champions.csv
    model_disagreement.csv
    event_analysis.csv
    snap_analysis.csv
    day_of_week_analysis.csv
    under_over_rankings.csv
    high_volume_exceptions.csv
    dri_exception_queue.csv
    labor_allocations.csv
    labor_tradeoffs.csv
    scenario_summary.csv
    inventory_proxy.csv
  images/
    champion_model_map.png
  video/
    forecast_model_arena.mp4
    forecast_to_labor_optimizer.mp4
  reports/
    control_tower.html
  manifests/
    run_manifest.json
```

Use the shared output categories and path-containment checks. Create `reports/` beneath the project output root without expanding the shared category enumeration.

**3. Exact existing files to modify**

| File | Planned modification |
|---|---|
| `.gitignore` | Add the exact exclusion `reference/project5/`, preserving every existing rule. |
| `pyproject.toml` | Add DuckDB and statsmodels. Add narrowly scoped third-party typing configuration only if necessary. |
| `src/linkedin_visual_labs/projects/__init__.py` | Export `commerce_app`. |
| `src/linkedin_visual_labs/cli.py` | Register the `commerce` Typer application. |
| `src/linkedin_visual_labs/common/animation.py` | Support explicit encoder selection using scoped Matplotlib configuration, preserving existing defaults. |
| `src/linkedin_visual_labs/common/media.py` | Support explicit packaged FFmpeg probing and validation without requiring PATH-based ffprobe. Preserve existing callers. |
| `tests/test_cli.py` | Verify `commerce` registration and help. |
| `tests/common/test_animation.py` | Test explicit encoder selection and backward compatibility. |
| `tests/common/test_media.py` | Test packaged probing, decoding, failure handling, and compatibility. |
| `README.md` | Add the Project 5 summary, commands, and documentation link. |

The exact new ignore entry will be:

```gitignore
reference/project5/
```

During implementation, verify that these assets are ignored and absent from any staging allowlist. Do not stage or commit the previews. Other untracked material under `reference/`, if present, must not be swept into a commit.

**`contracts/repository_continuity.json` remains unchanged by default.** Modify it later only if an existing continuity gate explicitly requires a Project 5-compatible update. Before that change, explain the exact gate requirement and why the update is necessary. Preserve repository identity, ancestry, and all earlier-project baselines.

No workflow modification is currently required: general CI already installs project dependencies and discovers the new tests.

**4. Complete dependency reconciliation**

This classification uses the inspected `pyproject.toml`.

| Package | Status | Decision |
|---|---|---|
| `duckdb` | Absent and genuinely required, therefore added | Memory-efficient aggregation and requested SQL diagnostics. Proposed minimum: `>=1.2`. |
| `pyarrow` | Already present and reused | Existing `>=18`; Parquet evidence and aggregate interchange. |
| `scikit-learn` | Already present and reused | Existing `>=1.6`; gradient boosting, MLP, encoding, and scaling. |
| `statsmodels` | Absent and genuinely required, therefore added | Dedicated Holt-Winters implementation. Proposed minimum: `>=0.14.4`. |
| `scipy` | Already present and reused | Existing `>=1.14`; `linprog` with HiGHS. |
| `plotly` | Already present and reused | Existing `>=5.24`; interactive report charts with JavaScript embedded locally in the HTML. |
| `kaleido` | Unnecessary, therefore not added | Matplotlib produces PNGs and video frames; no Plotly static export is needed. |
| `Jinja2` | Unnecessary, therefore not added | A bounded typed report renderer with standard-library HTML escaping is sufficient. |
| `imageio` | Already present and reused | Existing `>=2.36`; media reading and validation support. |
| `imageio-ffmpeg` | Already present and reused | Existing `>=0.5`; packaged FFmpeg executable and streaming media support. |
| `matplotlib` | Already present and reused | Existing `>=3.9`; champion map, animation frames, and shared visual components. |

Validate proposed dependency minimums against Python 3.13 during implementation. Record exact resolved versions in the manifest.

Do not add TensorFlow, PyTorch, Prophet, GPU libraries, or additional forecasting frameworks. **Retain the existing PyTorch dependency and all dependencies required by unrelated projects.**

**5. Data acquisition and caching**

The portfolio run uses real public M5 demand history:

- Ten stores.
- FOODS and HOUSEHOLD.
- Twenty store-category daily series.
- One common final 28-day observed holdout.
- Calendar event names/types and state-specific SNAP fields.

Preferred source: the previously inspected public [Zenodo M5 record](https://zenodo.org/records/10203108), containing `sales_train_evaluation.csv`, `calendar.csv`, and published checksums.

Implementation will:

1. Stream only those two files into temporary download files.
2. Apply timeouts and bounded retries.
3. Verify published checksums and calculate SHA-256.
4. Validate required columns, identifiers, and day coverage.
5. Atomically promote validated files into the ignored raw-data cache.
6. Record source identifiers, URLs, hashes, sizes, and acquisition time.
7. Reuse verified cached files for offline reruns.

Cache locations:

```text
data/raw/p25_quick_commerce_control_tower/
.cache/p25_quick_commerce_control_tower/
```

Support explicit local-file inputs. A secondary mirror may be enabled only after revision pinning and content-equivalence verification.

Determine the holdout from observed demand columns, not future calendar rows. Expect evaluation columns through `d_1941` and holdout `d_1914`–`d_1941`; validate rather than silently assuming them.

Do not download sell prices or unrelated files. A missing real dataset stops a real-data run; it never triggers synthetic replacement.

Fixture mode is explicit, offline, and visibly classified as test data.

**6. Memory-efficient aggregation**

Aggregate the wide sales data before unpivoting:

1. Validate identifiers and the complete ordered `d_N` column list.
2. Scan the CSV with DuckDB using explicit types.
3. Filter the required categories and stores.
4. Sum day columns by store, state, and category.
5. Materialize the resulting twenty-row wide aggregate.
6. Unpivot that small aggregate.
7. Join calendar information and the appropriate state SNAP field.
8. Validate and save sorted daily Parquet.
9. Load only the aggregate into pandas for modeling.

For 1,941 observed days, expected cardinality is 38,820 aggregate rows, including 560 holdout rows.

Configure DuckDB threads, memory limits, and spill paths. Measure process memory rather than treating the database memory setting as a complete process cap.

If necessary, aggregate day columns in deterministic batches. Do not shorten the dataset, discard stores, or materialize the full item-day history in pandas.

Reject duplicate keys, missing dates, invalid demand values, and incomplete calendar joins. Preserve genuine zeros.

**7. Configuration and forecasting design**

Use fully annotated project contracts for data, models, evaluation, governance, labor assumptions, scenarios, media, and outputs.

Reuse shared YAML loading, structured logging, path validation, and namespaced seeds. Explicitly adapt derived seeds to scikit-learn’s accepted range.

| Method | Fixed implementation |
|---|---|
| Seasonal naïve | Lag 28 for every holdout forecast. |
| Holt-Winters | One model per series with additive weekly seasonality and a documented fixed trend specification. |
| HistGradientBoostingRegressor | Pooled model with series identifiers, calendar fields, and leakage-safe historical features. |
| MLPRegressor | Pooled neural challenger with hidden layers `(128, 64, 32)`, training-only scaling, fixed seed, and bounded iterations. |

Fit all models before the same forecast origin and predict the same 28 dates.

Features may include lag 28, 35, and 56 and rolling summaries shifted by at least 28 days. For example, a seven-day rolling feature for date `t` ends at `t−28`.

Prohibit holdout actuals through lag 1, lag 7, rolling 7, rolling 14, preprocessing, model selection, or hidden validation paths.

Fit encoders and scalers exclusively on training data. Disable automatic random early-stopping validation. Fix hyperparameters before examining holdout outcomes; do not perform broad searches.

Treat event and SNAP schedules as known-at-origin calendar inputs and document that assumption.

Preserve raw predictions. Clip finite negative predictions to zero and record clipping. Missing, NaN, and infinite predictions remain failures.

**8. Evaluation and champion governance**

| Metric | Definition |
|---|---|
| WAPE | Sum of absolute errors divided by sum of actual demand. |
| MAE | Mean absolute error in daily units. |
| Forecast bias | Sum of prediction minus actual, divided by sum of actual; positive means overforecast. |
| Underforecast rate | Proportion of expected dates with valid predictions below actual. |
| Overforecast rate | Proportion above actual; exact matches belong to neither direction. |
| Event/ordinary WAPE | WAPE calculated separately within each subgroup. |
| Completeness | Valid unique expected predictions divided by 28. |
| Disagreement | Per-date model forecast range normalized by a training-derived demand scale; summarized by series. |
| Clipping rate | Negative raw finite predictions divided by finite raw predictions. |

Expose missing-prediction status alongside direction rates; incomplete models must not appear successful because observations were omitted. Report undefined denominators and empty subgroups explicitly.

Compute network WAPE from pooled errors and demand, not an unweighted mean of local WAPEs.

A model is eligible for a store-category only when it:

- Covers all 28 expected dates exactly once.
- Has finite predictions.
- Has nonnegative forecasts after documented processing.
- Meets the configured absolute-bias guardrail.
- Passes deterministic validation.

Use an initial configurable absolute-bias guardrail of 10%. Select the lowest-WAPE eligible model, with stable documented tie-breaking.

Select at most one champion per store-category. If none qualifies, retain **“No eligible champion—review required.”** Never relax the guardrail automatically.

A valid seasonal-naïve forecast may support a separately labeled contingency labor plan. It must not be represented as an eligible champion when it failed governance.

Report the global eligible winner, local champion distribution, and retrospective local-champion portfolio separately. A global candidate must qualify across the required series.

**The local portfolio is selected using the same holdout on which it is summarized. Its performance is retrospective and is not an unbiased estimate of future performance.** Production promotion requires subsequent untouched evaluation.

**9. SQL diagnostics and analytical narrative**

Create the requested diagnostics from one canonical error relation:

- Network scorecard.
- Store-category scorecard.
- Event versus ordinary days.
- SNAP versus non-SNAP days.
- Day-of-week analysis.
- Underforecast and overforecast rankings.
- High-volume exceptions.
- Forecast-DRI exception queue.

Every root-cause item follows:

**Observed pattern → measured evidence → operational implication → recommended experiment.**

Evidence includes numeric comparisons, sample sizes, affected series/dates, and ranking basis. Priorities combine configurable demand volume, unit shortfall, bias, disagreement, and repeat misses.

Use deterministic rules and stable sorting. Distinguish observed association from causal explanation. Do not invent causes or claim recurrence beyond what the evidence supports.

Suggested experiments may address model features, calendar quality, recalibration, data checks, or operating processes. Each queue item identifies a suggested owner and review action.

**10. Labor optimization and inventory**

Convert category forecasts into store-day workload using illustrative productivity:

\[
w_{s,d}=\sum_c \frac{\widehat y_{s,c,d}}{p_c}
\]

Decision variables are labor-hours \(h_{s,d}\) and uncovered workload \(u_{s,d}\).

\[
\min \sum_{s,d}\left(c_{s,d}h_{s,d}+\lambda_{s,d}u_{s,d}\right)
\]

Subject to:

\[
h^{min}_{s,d}\le h_{s,d}\le h^{max}_{s,d}
\]

\[
\sum_s h_{s,d}\le H_d
\]

\[
u_{s,d}\ge w_{s,d}-h_{s,d},\qquad u_{s,d}\ge0
\]

Inputs include productivity, minimum/maximum staffing converted to hours, daily network capacity, labor cost, and uncovered-workload penalties. Priority weights are configured assumptions, never chosen from holdout errors to manufacture improvement.

Use `scipy.optimize.linprog(method="highs")`. Continuous hours represent planning capacity rather than integer employee schedules.

The proportional heuristic satisfies minima, then distributes remaining capacity by workload while respecting maxima. Both methods use identical inputs and available capacity.

Report hours used and unused, labor cost, uncovered hours, weighted penalty, critical store-days, improved shortages, and worsened shortages. The optimizer reallocates fixed available capacity; it cannot create labor. If either plan leaves hours unused, disclose that explicitly.

Scenarios:

| Scenario | Change |
|---|---|
| Base | Original forecast and productivity assumptions. |
| +15% demand | Multiply demand by 1.15; keep capacity fixed. |
| −10% productivity | Multiply productivity by 0.90; keep capacity fixed. |

The productivity shock increases required workload by `1 / 0.90`. Recompute both allocation methods and show shortfall, critical store-days, trade-offs, and recommended responses for each scenario.

Inventory remains limited to synthetic on-hand quantities, forecast-based days of cover, and an illustrative stockout-risk flag. It is neither a probability estimate nor a replenishment optimizer.

**11. Authoritative product contract and outputs**

`PRODUCT_CONTRACT.md` will specify the business question:

*Which forecasts should own each store-category, why do they miss, and how should a constrained labor network respond?*

It will cover the full data scope, four-model arena, common holdout, leakage policy, eligibility and selection rules, retrospective caveat, diagnostics format, labor inputs/constraints/objective, fixed-capacity story, scenarios, inventory classification, narratives, and acceptance criteria.

The dashboard sections will be defined completely:

| Section | Required content |
|---|---|
| Header | Business question, data scope, real-data/assumption statement, and Forecast → Select → Diagnose → Allocate → Stress-test workflow. |
| Executive Decision | Global winner or explicit unavailable state, champion distribution, highest-risk exception, baseline comparison, labor-risk impact, and three evidence-backed recommendations. |
| Model Arena | Plain-English methods, identical holdout, metric definitions, champion rule, and explanation that sophistication is not the selection criterion. |
| Champion Model Map | Twenty cells showing champion/status, WAPE, bias, improvement versus seasonal naïve, and high-disagreement review flag. |
| Why Forecasts Missed | Prioritized four-part diagnostic stories with numerical evidence. |
| Labor Optimizer | Inputs, constraints, objective, proportional comparison, fixed capacity, cost/service trade-offs, and remaining shortages. |
| Scenario Lab | All three scenarios, updated shortfall, critical store-days, and recommended response. |
| Governance and Assumptions | Public real data, measured historical backtest, illustrative productivity/capacity, synthetic inventory, prototype optimization, and retrospective-selection caveat. |
| Forecast Accuracy DRI | Champion/challenger maintenance; monitoring; repeatable variance drivers; experiments; retraining, recalibration, escalation thresholds; and coordination across Operations, Product, Engineering, and Data Science. |

The contract will explicitly state **no DoorDash data and no claimed or measured DoorDash impact**.

The two complete video narratives:

| Scene | Forecast Model Arena | Forecast-to-Labor Optimizer |
|---|---|---|
| 1 | Business question, real M5 scope, twenty series. | Forecast-to-workload flow and illustrative assumptions. |
| 2 | Same 28-day holdout and leakage boundary. | Staffing bounds, network capacity, costs, and objective. |
| 3 | Four methods explained plainly. | Proportional versus optimized allocation. |
| 4 | Measured global scorecard and baseline comparison. | Improved shortages, remaining gaps, and service/cost trade-off. |
| 5 | Local champion map, bias, improvement, review flags. | Base and both shocks with updated risk and responses. |
| 6 | Eligibility, disagreement, retrospective caveat, ownership loop. | Fixed-capacity operating loop, recommendations, and provenance. |

Every scene contains explanatory captions and remains understandable while muted. Captions and results come from the canonical evidence, not preview text.

Deliver:

- One 1080 × 1350 champion-map PNG.
- Two 1080 × 1350 H.264 MP4s, 30 fps, `yuv420p`.
- One self-contained HTML report with embedded Plotly JavaScript, data, styles, and required images.
- CSV/Parquet evidence.
- One run manifest.

Resolve packaged FFmpeg explicitly, reject silent PATH fallback, and record executable/version provenance. Stream frames to avoid retaining full videos in memory.

**12. Implementation sequence**

Once implementation is authorized:

1. Add the exact local-reference ignore rule and verify exclusion.
2. Save the approved plan and authoritative product contract.
3. Add typed configuration, package structure, and CLI registration.
4. Add deterministic fixtures and independently calculated expected results.
5. Implement real acquisition, cache validation, and DuckDB aggregation.
6. Implement the split and leakage-tested features.
7. Implement all four forecast methods and status recording.
8. Implement metrics, champion governance, and disagreement.
9. Implement SQL diagnostics and evidence-backed narratives.
10. Implement proportional labor allocation, HiGHS optimization, and scenarios.
11. Add the limited inventory proxy.
12. Extend shared media support with compatibility tests.
13. Render the PNG, captioned videos, HTML, evidence, and manifest.
14. Run offline integration, full repository checks, and real-data validation.
15. Inspect the final artifacts and document measured results and limitations.

Planned CLI commands under `python -m linkedin_visual_labs commerce`:

`doctor`, `acquire-data`, `prepare-data`, `forecast`, `evaluate`, `diagnose`, `optimize`, `render`, `validate`, and `run-all`.

**13. Automated tests**

| Layer | Required coverage |
|---|---|
| Configuration | Invalid horizons, categories, seeds, paths, model identities, thresholds, and staffing bounds. |
| Acquisition/cache | Verified offline reuse, corruption, interruption, schema mismatch, explicit fixture mode, and no synthetic fallback. |
| Aggregation | Known totals, category filtering, dates, state SNAP joins, null/duplicate rejection, and equivalent batch aggregation. |
| Leakage/features | Boundary dates, rolling endpoints, training-only transforms, and holdout mutation leaving features and forecasts unchanged. |
| Forecasting | Exact lag-28 behavior, weekly Holt-Winters, exact MLP architecture, deterministic reruns, and failure/convergence status. |
| Evaluation | Hand-calculated metrics, sign conventions, empty subgroups, zero denominators, clipping, and missing/duplicate predictions. |
| Governance | Each eligibility failure, ties, baseline wins, and explicit no-champion state. |
| Diagnostics | Independently expected SQL results, stable ranking, join cardinality, and complete evidence stories. |
| Labor | Known small LP optimum, feasible heuristic, capacity conservation, bounds, infeasibility, objective comparison, and exact shock arithmetic. |
| Inventory | Synthetic classification, cover arithmetic, and zero-demand handling. |
| Visualization/report | Required cells, sections, narrative fields, escaping, offline resources, and captions. |
| Media | Actual short packaged-FFmpeg encode/decode, exact dimensions, metadata, truncation, and missing executable behavior. |
| Pipeline | One offline fixture end-to-end run producing all analytical layers and short media artifacts. |
| Repository | Existing tests unchanged and new top-level CLI tests. |

The tiny deterministic fixture will cover twenty series over approximately 112 days, multiple items per series, an excluded category, weekly patterns, events, SNAP variation, and independent expected aggregates.

Fixture results must never appear as real portfolio evidence.

**14. Output validation and manifest**

Validate:

- Exact PNG and video dimensions.
- H.264 codec, pixel format, frame rate, duration, frame count, and successful full decoding.
- Legible captions, safe margins, no text overflow, and clear scene transitions.
- Required dashboard content and functionality with network access disabled.
- Consistent numeric results across tables, charts, captions, and executive recommendations.
- Correct treatment of undefined metrics and unavailable champions.
- No preview metrics carried into final artifacts.
- All required provenance and assumption labels.

The single run manifest records configuration, seed, Git revision when available, source hashes, dependency versions, training/holdout dates, model settings/status, dimensions, stage and total runtime, measured metrics, optimizer status, assumptions, artifact hashes, and validation outcomes.

Deterministic comparisons exclude inherently variable timestamps and runtime. Numeric tolerances are documented; byte-identical video files across environments are not assumed.

**15. Risks and deterministic fallbacks**

| Risk | Response |
|---|---|
| Data source unavailable | Verified real cache or explicit local real files; otherwise stop. |
| Corrupt or different dataset edition | Reject it and report the mismatch. |
| Aggregation memory pressure | Deterministic day-column batching without reducing scope. |
| Model fails or produces invalid output | Record failure and exclude it; never substitute another method under its name. |
| No model meets governance | Explicit no-champion state; only a disclosed valid contingency for planning. |
| Labor bounds infeasible | Fail the scenario with constraint evidence; do not increase capacity. |
| Solver fails | Preserve a feasible heuristic as a labeled fallback, without claiming optimization success. |
| No forecast or service improvement | Report the measured outcome without altering assumptions to force a win. |
| Sparse diagnostic subgroup | Show sample size and insufficient-evidence status. |
| Cross-platform numerical variation | Fixed seeds/settings, recorded versions, stable ordering, and declared tolerances. |
| Continuity gate requires a contract update | Explain its exact requirement first; preserve identity, ancestry, and earlier baselines. |

**16. Definition of done**

Project 5 is complete when:

- Real M5 data yields the required twenty series and common 28-day holdout.
- All four methods are attempted with reproducible status and leakage evidence.
- Champion governance and no-eligible-champion handling are explicit.
- All requested diagnostics, labor comparisons, and scenarios are generated.
- Capacity is conserved and remaining trade-offs are visible.
- Inventory and labor assumptions are clearly classified.
- The PNG, two muted-readable videos, HTML, evidence tables, and manifest pass validation.
- `IMPLEMENTATION_PLAN.md` and `PRODUCT_CONTRACT.md` reflect the approved implementation.
- The report distinguishes public-real, measured, illustrative, synthetic, and prototype results.
- No DoorDash data or DoorDash impact is claimed.
- `ruff format --check .`, `ruff check .`, `mypy src tests`, `pytest`, and applicable existing repository gates pass without weakened checks.
- A dirty or unsynchronized repository is never described as transfer-safe.
- `reference/project5/` is ignored and its assets remain unstaged and uncommitted.
- Raw data, caches, models, and generated media remain outside version control.
- The continuity contract remains unchanged unless an existing gate explicitly requires an explained compatible update.
- Unrelated projects remain untouched.

No files have been changed for this revision. Implementation remains stopped.
