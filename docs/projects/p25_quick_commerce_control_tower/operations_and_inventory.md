# Step 5 — Illustrative labor scenarios and synthetic inventory

This implements only the approved operations step. PRODUCT_CONTRACT.md remains authoritative and unchanged. No final dashboard, PNG, HTML, or video is implemented.

## Frozen operational provenance and actual separation

The optimize CLI reads predictions.parquet and champions.csv and verifies their hashes against the successful Step 4 evaluation manifest. It does not change model settings, predictions, metrics, eligibility or champions. Eligible local champions supply forecasts. For TX_3/FOODS (and any other unassigned series), the product contract permits a valid seasonal-naive planning contingency. Rows explicitly carry forecast_role=contingency_forecast, contingency_used=true, champion_status=no_eligible_champion and forecast_source_model=seasonal_naive. This is never an eligible champion.

OperationalDemand separates planning from actuals. The planning DataFrame contains forecast/provenance fields only. Workload generation rejects actual_units. DayProblem contains store IDs, forecast-derived hours, bounds, capacity, cost, penalties and tolerance; no realized targets or Step 4 exception severity enter the solver. Actuals are joined only after every allocation decision. The operational-demand audit output includes actual_units for retrospective comparison.

Champion selection itself remains retrospective because it used this same holdout. Forecast-based operational results therefore inherit that selection caveat, even though the allocation algorithm never consumes actual demand. No production or DoorDash impact is claimed.

## Illustrative assumptions fixed before scenario results

All values are loaded from YAML, never inferred from desired results:

| Assumption | Value |
|---|---|
| FOODS productivity | 90 demand units per labor-hour |
| HOUSEHOLD productivity | 60 demand units per labor-hour |
| Minimum staffing | 2 people-equivalents × 8-hour shift = 16 hours/store-day |
| Maximum staffing | 12 people-equivalents × 8-hour shift = 96 hours/store-day |
| Fixed network cap | 480 labor-hours/date, or 13,440 over 28 dates |
| Labor cost | 22 illustrative currency units/labor-hour |
| Uncovered-workload penalty | 100 illustrative currency units/uncovered labor-hour × priority |
| Store priority weights | 1.0 for every store; independent of realized errors |
| Critical store-day | uncovered forecast workload >8 labor-hours |
| Numerical solver tolerance | 1e-7 |

These are illustrative continuous capacity plans, not integer employee schedules or observed operating values. Positivity, category coverage and staffing bounds are validated. The existing public configuration validator rejects infeasible network minima. The lower-level allocation layer independently returns infeasible plus minimum-total/cap/bounds evidence, without increasing capacity or relaxing limits.

## Workload and proportional allocation

Category required hours = forecast_units × scenario demand multiplier / (category productivity × scenario productivity multiplier). Store-day required hours sum the two category contributions. category_workload.csv preserves units, productivity, contribution and contingency source.

The deterministic heuristic allocates minima first. Remaining capacity is distributed proportionally to unmet forecast workload, capping each increment at both remaining staffing room and unmet need. Capacity freed by saturation is redistributed iteratively. It stops when capacity is exhausted or no store can use more without exceeding workload/maxima. Minima may exceed low forecast need; excess labor beyond mandatory minima is not forced merely to consume the budget. Input ordering is stable by store.

## Linear program

For each date, h_s is allocated labor-hours and u_s is uncovered workload. scipy.optimize.linprog(method="highs") minimizes:

sum_s(cost_per_hour × h_s + uncovered_hour_penalty × priority_s × u_s)

subject to minimum_hours_s <= h_s <= maximum_hours_s, sum_s(h_s) <= daily_network_hours, u_s >= required_hours_s - h_s and u_s >=0. HiGHS primal/dual feasibility tolerance is configured; no secondary objective or artificial tie perturbation changes the approved objective. Stable store order yields repeatable solutions within tolerance.

Both methods receive identical workload, bounds, capacity, cost and priorities. Validated optimized objective must be no worse than proportional objective within relative 1e-7 numerical tolerance. Returned variables, constraints, objective and workload relationship are checked. A solver failure retains its original status/message and the separate feasible baseline, not fabricated optimized rows. Scenario summaries mark failures and leave solution metrics null. No result is labeled as a successful optimizer fallback.

The optimizer reallocates a fixed available capacity. It creates neither labor nor productivity and does not reduce required workload. With equal priorities and a linear penalty, multiple allocations can have identical objectives. Stable solver ordering may redistribute shortage among these ties; there is no claim that this is a measured business-priority improvement. With differing configured priorities, higher-penalty shortages may improve at lower-priority stores' expense. When labor costs exceed penalties, leaving capacity unused may be optimal. All used/unused capacity, shortage trade-offs and costs remain visible.

## Scenarios and retrospective comparisons

- Base: original forecasts/productivity.
- +15% demand: forecast ×1.15; productivity, staffing and capacity unchanged.
- -10% productivity: productivity ×0.90; forecast, staffing and capacity unchanged. Workload scales by exactly 1/0.90, not 1.10.

The 28-day × 10-store grain is preserved in each method/scenario. Summaries report required/allocated/uncovered/weighted hours, labor cost, objective, unused capacity and critical store-days. Distinct stores at min/max/constrained and counts of store-days are separate. Tradeoff signs are optimized minus proportional: positive hours_delta means gained hours; positive uncovered_delta means worsened shortage. Flags use the configured tolerance. tradeoff_summary distinguishes store-days from distinct stores gaining/losing or improving/worsening across the period; a store can appear in both sets on different dates.

After allocation, measured holdout demand is divided by the same scenario productivity assumptions to compute retrospective actual workload. The +15% forecast-demand scenario does not pretend actual demand was observed 15% higher; actuals remain unchanged. The productivity shock changes the illustrative conversion of the same measured actual demand. retrospective_labor.csv and retrospective_summary.csv explicitly classify this backtest evidence and never feed it to allocation decisions.

## Deliberately limited inventory proxy

Each date/store/category receives an independent synthetic on-hand snapshot, not a simulated replenishment or depletion path. Project seed 47 uses the shared namespaced RNG keyed by project/inventory/store/category/date, so row order cannot change results. For a target date, mean forecast demand is calculated over that date and the next six available forecast dates. At the end of the 28-day horizon the window shortens explicitly; actual window length and status are retained.

Draw a synthetic cover multiplier uniformly from configured [0,7) days. synthetic_on_hand_units=floor(window_mean_forecast_units × multiplier). days_of_cover=synthetic_on_hand_units/window_mean_forecast_units. No preview values or actual inventory are used.

Zero mean forecast creates zero synthetic stock, null cover and undefined_zero_demand status; Healthy is the disclosed no-forecast-demand convention, not a stockout assurance. Positive mean below 0.01 is labeled low_forecast_demand and uses exact arithmetic without denominator flooring. Missing, negative, nonfinite or discontinuous forecast inputs are rejected. Risk cutoffs are fixed before seeing distributions: Expedite below 1 day, Reorder from 1 to below 2, Monitor from 2 to below 4, Healthy at least 4 days. Every row has synthetic=true and illustrative=true.

This is not a stockout probability, replenishment optimizer, lead-time model or purchase recommendation. No supplier, purchase-order, M5 inventory or DoorDash inventory data is available or claimed. Inventory outputs never influence forecasts, evaluation, champion selection or labor allocation.

## Outputs and checks

Under outputs/p25_quick_commerce_control_tower/data/: operational_demand.csv, category_workload.csv, labor_allocations.csv, labor_tradeoffs.csv, tradeoff_summary.csv, scenario_summary.csv, solver_status.csv, retrospective_labor.csv, retrospective_summary.csv, inventory_proxy.csv and operations.metadata.json. The manifest binds upstream hashes, full configuration, contingency coverage, deterministic rerun, and generated hashes. An incomplete solver run records failure evidence and exits nonzero.

Offline tests cover independent conversion, contingency provenance, typed target exclusion, whole-holdout actual mutation, heuristic saturation, constraints, objective dominance, deterministic solving, infeasibility/failure, fixed-capacity scenario arithmetic, synthetic inventory/risk/zero/low/missing data, and verified artifact/CLI behavior. See validation.md for measured real results and exact command outcomes. Step 6 remains unauthorized until requested.
