# Project 5 — Quick-Commerce Control Tower

Which forecasting approach should own each store-category, and how should a fixed labor pool respond? This public-M5 portfolio prototype compares four methods, governs local champions, turns forecast misses into an investigation backlog and validates constrained staffing decisions. It measures historical forecast accuracy and conditional illustrative operations, not company production impact.

## Reproduce the release

From the repository root in the project Python 3.13 environment:

```powershell
.\.venv\Scripts\python.exe -m linkedin_visual_labs commerce acquire-data
.\.venv\Scripts\python.exe -m linkedin_visual_labs commerce run-all
.\.venv\Scripts\python.exe -m linkedin_visual_labs commerce validate
```

`acquire-data` verifies/reuses the two pinned real M5 cache files, downloading only when absent. For offline transfer, use `acquire-data --local-directory <repository-local-directory>` with the same checksum-verified CSVs. `run-all` requires that real cache; it never switches to fixture data. It runs preparation, feature construction and forecasting, an independent refit after adversarial holdout-target mutation, evaluation/governance/SQL diagnostics, labor/scenarios/inventory, rendering, full media validation and artifact-bound manual-acceptance verification. It writes `outputs/p25_quick_commerce_control_tower/manifests/run_manifest.json` and fresh `forecast_validation.json`.

Stages stop on failure and the run manifest records the failed stage instead of preserving a stale completion claim. Exact predictor/prediction/interpretation and non-runtime model-status equality are required for the real mutation proof. Evaluation binds that proof to prepared-data/prediction hashes and configuration. Individual `doctor`, `prepare-data`, `forecast`, `evaluate`, `optimize`, `render` and `validate` commands remain available. Diagnostics are part of `evaluate`, avoiding a duplicate analytical route. The default `evaluate` proof is the new output manifest, not a developer's local Step 3 cache.

The configuration and architecture remain unchanged: typed project contracts, shared path/randomness/media utilities, memory-efficient DuckDB aggregation, sklearn/statsmodels forecasting, SQL/Python metric reconciliation and scipy HiGHS. Help/doctor are read-only. Tests use deterministic isolated fixtures; they do not require the real cache. `prepare-data --fixture` and `forecast --fixture` remain explicit synthetic test modes, separate from release orchestration.

## What the release contains

- Public M5 demand: 10 stores × FOODS/HOUSEHOLD = 20 series, 1,941 dates, 38,820 aggregate rows; one final 28-day holdout, 560 observations and 2,240 forecasts.
- Seasonal naïve, Holt-Winters, HGB and MLP (128/64/32), with demand features ending no later than t−28 and training-only preprocessing.
- HGB leads the network at 7.94% WAPE. Local ownership is 9 HGB, 7 MLP, 3 Holt-Winters and one review state (TX_3 / FOODS). The 19-series local portfolio comparison is retrospective.
- Forecast-only proportional/optimized labor plans with fixed capacity, Base/+15% demand/−10% productivity scenarios and an explicitly synthetic inventory proxy.
- A self-contained seven-tab HTML report with 28 charts, a 1080 × 1350 champion PNG and two animated 30-second, 30-fps H.264/yuv420p videos.

Step 6D manual recruiter acceptance is PASS. `manual_acceptance.json` records the four reviewed artifact hashes; reruns retain that acceptance only when all four match exactly. This is a user review, not automated browser inspection. A platform change that alters media bytes requires renewed acceptance rather than silently inheriting it. The original plan/contract video duration is superseded by the explicitly approved 30-second presentation requests; analytical and claim boundaries remain in force.

## Methods and recruiter walkthrough

| Read next | Contents |
|---|---|
| [Data and methods](data_and_methods.md) | M5 lineage, schema, preparation, source/cache checks and feature cutoffs |
| [Forecasting](forecasting_and_methods.md) | Four fixed methods, target/features, preprocessing, clipping, determinism and failure policy |
| [Evaluation and governance](evaluation_and_governance.md) | WAPE/MAE/bias, eligibility, local selection, SQL reconciliation and diagnostic priorities |
| [Operations and inventory](operations_and_inventory.md) | Workload conversion, LP objective/constraints, contingency, scenarios and synthetic inventory |
| [Presentation walkthrough](presentation_and_walkthrough.md) | Recruiter reading order, feature importance, final allocation, production inputs and video narratives |
| [Validation and release review](validation.md) | Historical evidence, manual acceptance, full Step 7 checks, exact scope and release recommendation |

## Known limits and production next steps

No method is eligible globally; TX_3 / FOODS remains unassigned with a separately labeled seasonal-naïve labor contingency. Local champions were selected and scored on the same holdout. Feature importance is a bounded in-sample permutation interpretation, not causality; event/SNAP associations have sample limitations.

The optimizer reallocates capacity and reduces configured Base critical store-days from 47 to 19, while retrospective actual uncovered workload increases from 1,494.77 to 1,540.91 hours. Equal priorities and illustrative productivity do not encode full operational economics. Calibrate service priorities, shortage/SLA costs, actual productivity, shifts, labor availability, inventory/replenishment and uncertainty; validate changes on untouched periods before production use. Synthetic inventory is neither observed stock nor a replenishment optimizer. No DoorDash data or operating impact is claimed.

Generated outputs, raw data, models, caches and reference previews remain ignored. A validated Project 5 pipeline does not make a dirty checkout transfer-safe or erase unrelated full-suite/environment failures. Consult the final Step 7 release review before publication. No staging, commit or push is performed by these commands.
