"""Illustrative forecast-driven labor scenarios and separately joined retrospective evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from linkedin_visual_labs.common.media import write_generation_manifest
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    file_hash,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.evaluation import (
    NO_CHAMPION,
    SERIES,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.forecasting import MODEL_NAMES
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.inventory import inventory_proxy
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import (
    CommerceConfig,
    ScenarioConfig,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.optimization import (
    DayProblem,
    allocate_day,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext


@dataclass(frozen=True)
class OperationalDemand:
    planning: pd.DataFrame
    actuals: pd.DataFrame


@dataclass(frozen=True)
class OperationsResult:
    tables: dict[str, pd.DataFrame]


def operational_demand(predictions: pd.DataFrame, champions: pd.DataFrame) -> OperationalDemand:
    if (
        len(champions) != 20
        or champions.duplicated(SERIES).any()
        or champions[SERIES].isna().any().any()
    ):
        raise DataError("operational governance must contain exactly 20 unique series")
    if len(predictions) != 2240 or predictions.duplicated([*GRAIN, "model_name"]).any():
        raise DataError("operational source must be the complete canonical forecast grid")
    parts: list[pd.DataFrame] = []
    for row in champions.to_dict(orient="records"):
        contingency = pd.isna(row["champion_model"])
        status = row["eligibility_status"]
        if (contingency and status != NO_CHAMPION) or (not contingency and status != "eligible"):
            raise DataError("inconsistent champion identity/status")
        model = "seasonal_naive" if contingency else str(row["champion_model"])
        if model not in MODEL_NAMES:
            raise DataError("unknown operational forecast model")
        selected = (
            predictions.loc[
                predictions["store_id"].eq(row["store_id"])
                & predictions["category"].eq(row["category"])
                & predictions["model_name"].eq(model)
            ]
            .sort_values("date")
            .copy()
        )
        if (
            len(selected) != 28
            or selected["date"].nunique() != 28
            or not np.isfinite(
                selected[["raw_forecast_units", "forecast_units", "actual_units"]].to_numpy(
                    dtype=float
                )
            ).all()
            or selected[["forecast_units", "actual_units"]].lt(0).any().any()
            or not selected["forecast_units"].eq(selected["raw_forecast_units"].clip(lower=0)).all()
            or not selected["was_clipped"].eq(selected["raw_forecast_units"].lt(0)).all()
            or not selected["model_status"].isin(["success", "warning"]).all()
        ):
            raise DataError("selected champion/contingency forecast is incomplete or invalid")
        selected["forecast_source_model"] = model
        selected["champion_status"] = "no_eligible_champion" if contingency else "eligible_champion"
        selected["forecast_role"] = "contingency_forecast" if contingency else "champion_forecast"
        selected["contingency_used"] = contingency
        selected["selection_classification"] = "retrospective"
        parts.append(selected)
    frame = pd.concat(parts, ignore_index=True).sort_values(GRAIN).reset_index(drop=True)
    if frame["date"].nunique() != 28 or not frame.groupby("date").size().eq(20).all():
        raise DataError("operational inputs must share 28 common planning dates")
    dates = pd.Series(sorted(frame["date"].unique()))
    if not dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise DataError("planning dates must be continuous")
    columns = [
        *GRAIN,
        "forecast_source_model",
        "champion_status",
        "forecast_units",
        "contingency_used",
        "forecast_role",
        "selection_classification",
    ]
    return OperationalDemand(frame[columns], frame[[*GRAIN, "actual_units"]])


def workload(
    planning: pd.DataFrame, config: CommerceConfig, scenario: ScenarioConfig
) -> pd.DataFrame:
    if "actual_units" in planning.columns:
        raise DataError("actual demand is forbidden in planning workload inputs")
    frame = planning.copy()
    frame["scenario"] = scenario.name
    frame["scenario_forecast_units"] = frame["forecast_units"] * scenario.demand_multiplier
    frame["productivity_units_per_hour"] = (
        frame["category"].map(config.labor.productivity_units_per_hour)
        * scenario.productivity_multiplier
    )
    if (
        frame["productivity_units_per_hour"].isna().any()
        or frame["productivity_units_per_hour"].le(0).any()
        or not np.isfinite(frame["productivity_units_per_hour"]).all()
    ):
        raise DataError("positive illustrative productivity required for every category")
    frame["required_hours"] = (
        frame["scenario_forecast_units"] / frame["productivity_units_per_hour"]
    )
    frame["assumption_classification"] = "illustrative"
    return frame


def plan_scenarios(planning: pd.DataFrame, config: CommerceConfig) -> dict[str, pd.DataFrame]:
    """All decisions finish here before any actuals can enter the retrospective layer."""
    allocations: list[dict[str, object]] = []
    statuses: list[dict[str, object]] = []
    workloads: list[pd.DataFrame] = []
    labor = config.labor
    for scenario in config.scenarios:
        category_hours = workload(planning, config, scenario)
        workloads.append(category_hours)
        store_days = category_hours.groupby(["date", "store_id"], as_index=False).agg(
            required_hours=("required_hours", "sum"),
            contingency_categories=("contingency_used", "sum"),
        )
        for date, day in store_days.groupby("date", sort=True):
            day = day.sort_values("store_id")
            stores = tuple(str(x) for x in day["store_id"])
            if len(stores) != 10 or set(stores) != set(labor.store_priority_weights):
                raise DataError("labor planning requires all 10 configured stores per date")
            problem = DayProblem(
                stores,
                tuple(day["required_hours"].astype(float)),
                (labor.minimum_staffing * labor.shift_hours,) * 10,
                (labor.maximum_staffing * labor.shift_hours,) * 10,
                (labor.cost_per_hour,) * 10,
                tuple(
                    {str(k): v for k, v in labor.store_priority_weights.items()}[s] for s in stores
                ),
                labor.daily_network_hours,
                labor.uncovered_hour_penalty,
                labor.solver_tolerance,
            )
            baseline = allocate_day(problem, "proportional")
            optimized = allocate_day(problem, "optimized")
            if (
                baseline.objective is not None
                and optimized.objective is not None
                and optimized.objective
                > baseline.objective + labor.solver_tolerance * max(1.0, abs(baseline.objective))
            ):
                raise DataError(
                    "optimized objective is worse than the feasible proportional objective"
                )
            for solution in (baseline, optimized):
                statuses.append(
                    {
                        "scenario": scenario.name,
                        "date": date,
                        "allocation_method": solution.method,
                        "feasibility": solution.status,
                        "message": solution.message,
                        "minimum_total_hours": sum(problem.minimum_hours),
                        "network_capacity": problem.capacity,
                        "objective": solution.objective,
                        "fallback_used": False,
                    }
                )
                if solution.status != "feasible":
                    continue
                for index, row in enumerate(day.to_dict(orient="records")):
                    h, u = solution.hours[index], solution.uncovered[index]
                    priority = problem.priority_weight[index]
                    allocations.append(
                        {
                            **{str(k): v for k, v in row.items()},
                            "scenario": scenario.name,
                            "allocation_method": solution.method,
                            "allocated_hours": h,
                            "uncovered_hours": u,
                            "priority_weight": priority,
                            "weighted_uncovered_hours": priority * u,
                            "labor_cost": labor.cost_per_hour * h,
                            "uncovered_penalty_cost": labor.uncovered_hour_penalty * priority * u,
                            "minimum_hours": problem.minimum_hours[index],
                            "maximum_hours": problem.maximum_hours[index],
                            "network_capacity": problem.capacity,
                            "critical_store_day": u > labor.critical_uncovered_hours,
                            "critical_threshold_hours": labor.critical_uncovered_hours,
                            "at_minimum": abs(h - problem.minimum_hours[index])
                            <= labor.solver_tolerance,
                            "at_maximum": abs(h - problem.maximum_hours[index])
                            <= labor.solver_tolerance,
                            "constrained_store_day": u > labor.solver_tolerance,
                            "assumption_classification": "illustrative",
                            "forecast_selection_classification": "retrospective",
                        }
                    )
    return {
        "category_workload": pd.concat(workloads, ignore_index=True),
        "labor_allocations": pd.DataFrame(allocations),
        "solver_status": pd.DataFrame(statuses),
    }


def summarize_labor(tables: dict[str, pd.DataFrame], config: CommerceConfig) -> None:
    allocations = tables["labor_allocations"]
    statuses = tables["solver_status"]
    trades: list[pd.DataFrame] = []
    summaries: list[dict[str, object]] = []
    tolerance = config.labor.solver_tolerance
    for scenario in config.scenarios:
        for method in ("proportional", "optimized"):
            status = statuses.loc[
                statuses["scenario"].eq(scenario.name) & statuses["allocation_method"].eq(method)
            ]
            feasible = status["feasibility"].eq("feasible").all()
            summary: dict[str, object] = {
                "scenario": scenario.name,
                "allocation_method": method,
                "feasibility": "feasible"
                if feasible
                else "infeasible"
                if status["feasibility"].eq("infeasible").any()
                else "solver_failed",
                "planning_dates": len(status),
                "network_capacity_per_day": config.labor.daily_network_hours,
                "total_capacity": len(status) * config.labor.daily_network_hours,
                "assumption_classification": "illustrative",
                "selection_classification": "retrospective",
            }
            metric_names = [
                "required_hours",
                "allocated_hours",
                "unused_capacity",
                "labor_cost",
                "uncovered_hours",
                "weighted_uncovered_hours",
                "critical_store_days",
                "stores_at_minimum",
                "stores_at_maximum",
                "store_days_at_minimum",
                "store_days_at_maximum",
                "constrained_stores",
                "constrained_store_days",
                "objective",
            ]
            summary.update({name: None for name in metric_names})
            if feasible:
                rows = allocations.loc[
                    allocations["scenario"].eq(scenario.name)
                    & allocations["allocation_method"].eq(method)
                ]
                for name in (
                    "required_hours",
                    "allocated_hours",
                    "labor_cost",
                    "uncovered_hours",
                    "weighted_uncovered_hours",
                ):
                    summary[name] = float(rows[name].sum())
                summary.update(
                    unused_capacity=len(status) * config.labor.daily_network_hours
                    - float(rows["allocated_hours"].sum()),
                    critical_store_days=int(rows["critical_store_day"].sum()),
                    stores_at_minimum=rows.loc[rows["at_minimum"], "store_id"].nunique(),
                    stores_at_maximum=rows.loc[rows["at_maximum"], "store_id"].nunique(),
                    store_days_at_minimum=int(rows["at_minimum"].sum()),
                    store_days_at_maximum=int(rows["at_maximum"].sum()),
                    constrained_stores=rows.loc[
                        rows["constrained_store_day"], "store_id"
                    ].nunique(),
                    constrained_store_days=int(rows["constrained_store_day"].sum()),
                    objective=float(
                        rows["labor_cost"].sum() + rows["uncovered_penalty_cost"].sum()
                    ),
                )
            summaries.append(summary)
        if allocations.empty:
            continue
        rows = allocations.loc[allocations["scenario"].eq(scenario.name)]
        a = rows.loc[rows["allocation_method"].eq("proportional")]
        b = rows.loc[rows["allocation_method"].eq("optimized")]
        keys = ["scenario", "date", "store_id"]
        columns = [
            *keys,
            "allocated_hours",
            "uncovered_hours",
            "weighted_uncovered_hours",
            "priority_weight",
        ]
        pair = a[columns].merge(
            b[columns], on=keys, suffixes=("_proportional", "_optimized"), validate="one_to_one"
        )
        pair = pair.rename(
            columns={
                "allocated_hours_proportional": "proportional_hours",
                "allocated_hours_optimized": "optimized_hours",
                "uncovered_hours_proportional": "proportional_uncovered",
                "uncovered_hours_optimized": "optimized_uncovered",
            }
        )
        pair["hours_delta"] = pair["optimized_hours"] - pair["proportional_hours"]
        pair["uncovered_delta"] = pair["optimized_uncovered"] - pair["proportional_uncovered"]
        pair["weighted_uncovered_delta"] = (
            pair["weighted_uncovered_hours_optimized"]
            - pair["weighted_uncovered_hours_proportional"]
        )
        pair["gained_hours"], pair["lost_hours"] = (
            pair["hours_delta"].gt(tolerance),
            pair["hours_delta"].lt(-tolerance),
        )
        pair["shortage_improved"], pair["shortage_worsened"] = (
            pair["uncovered_delta"].lt(-tolerance),
            pair["uncovered_delta"].gt(tolerance),
        )
        pair["shortage_unchanged"] = pair["uncovered_delta"].abs().le(tolerance)
        pair["assumption_classification"] = "illustrative"
        trades.append(pair)
    tables["scenario_summary"] = pd.DataFrame(summaries)
    tables["labor_tradeoffs"] = pd.concat(trades, ignore_index=True) if trades else pd.DataFrame()
    comparisons: list[dict[str, object]] = []
    for scenario in config.scenarios:
        trade = tables["labor_tradeoffs"]
        if trade.empty:
            continue
        subset = trade.loc[trade["scenario"].eq(scenario.name)]
        record: dict[str, object] = {"scenario": scenario.name, "compared_store_days": len(subset)}
        for flag in (
            "gained_hours",
            "lost_hours",
            "shortage_improved",
            "shortage_worsened",
            "shortage_unchanged",
        ):
            record[f"{flag}_store_days"] = int(subset[flag].sum())
            record[f"{flag}_stores"] = subset.loc[subset[flag], "store_id"].nunique()
        comparisons.append(record)
    tables["tradeoff_summary"] = pd.DataFrame(comparisons)


def retrospective_evidence(
    allocations: pd.DataFrame, actuals: pd.DataFrame, config: CommerceConfig
) -> pd.DataFrame:
    if allocations.empty:
        return pd.DataFrame()
    parts = []
    for scenario in config.scenarios:
        actual = actuals.copy()
        actual["actual_required_hours"] = actual["actual_units"] / (
            actual["category"].map(config.labor.productivity_units_per_hour)
            * scenario.productivity_multiplier
        )
        store_actual = actual.groupby(["date", "store_id"], as_index=False)[
            "actual_required_hours"
        ].sum()
        joined = allocations.loc[allocations["scenario"].eq(scenario.name)].merge(
            store_actual, on=["date", "store_id"], validate="many_to_one"
        )
        joined["actual_uncovered_hours"] = (
            joined["actual_required_hours"] - joined["allocated_hours"]
        ).clip(lower=0)
        joined["actual_weighted_uncovered_hours"] = (
            joined["actual_uncovered_hours"] * joined["priority_weight"]
        )
        joined["actual_critical_store_day"] = joined["actual_uncovered_hours"].gt(
            config.labor.critical_uncovered_hours
        )
        joined["evidence_classification"] = "retrospective_backtest_with_illustrative_productivity"
        parts.append(joined)
    return pd.concat(parts, ignore_index=True)


def run_operations_tables(
    predictions: pd.DataFrame, champions: pd.DataFrame, config: CommerceConfig
) -> OperationsResult:
    demand = operational_demand(predictions, champions)
    tables = plan_scenarios(demand.planning, config)
    summarize_labor(tables, config)
    tables["operational_demand"] = demand.planning.merge(
        demand.actuals, on=GRAIN, validate="one_to_one"
    )
    tables["retrospective_labor"] = retrospective_evidence(
        tables["labor_allocations"], demand.actuals, config
    )
    retrospective = tables["retrospective_labor"]
    tables["retrospective_summary"] = (
        retrospective.groupby(["scenario", "allocation_method"], as_index=False)
        .agg(
            actual_required_hours=("actual_required_hours", "sum"),
            allocated_hours=("allocated_hours", "sum"),
            actual_uncovered_hours=("actual_uncovered_hours", "sum"),
            actual_weighted_uncovered_hours=("actual_weighted_uncovered_hours", "sum"),
            actual_critical_store_days=("actual_critical_store_day", "sum"),
        )
        .assign(evidence_classification="retrospective_backtest_with_illustrative_productivity")
        if not retrospective.empty
        else pd.DataFrame()
    )
    tables["inventory_proxy"] = inventory_proxy(demand.planning, config.inventory, config.seed)
    for name, frame in tables.items():
        keys = [
            key
            for key in ("scenario", "allocation_method", "date", "store_id", "category")
            if key in frame
        ]
        if keys:
            tables[name] = frame.sort_values(keys).reset_index(drop=True)
    return OperationsResult(tables)


def run_operations(context: PipelineContext) -> Path:
    prediction_path = context.resolve_output_path("data/predictions.parquet")
    champion_path = context.resolve_output_path("data/champions.csv")
    evaluation_path = context.resolve_output_path("data/evaluation.metadata.json")
    metadata = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if (
        metadata.get("predictions_sha256") != file_hash(prediction_path)
        or metadata.get("artifact_sha256", {}).get("champions") != file_hash(champion_path)
        or metadata.get("sql_python_reconciliation") != "PASS"
        or metadata.get("deterministic_evaluation_rerun") != "PASS"
    ):
        raise DataError("verified frozen Step 4 evidence is required for operations")
    predictions, champions = pd.read_parquet(prediction_path), pd.read_csv(champion_path)
    result = run_operations_tables(predictions, champions, context.configuration)
    repeated = run_operations_tables(
        predictions.sample(frac=1, random_state=context.configuration.seed),
        champions.sample(frac=1, random_state=context.configuration.seed),
        context.configuration,
    )
    for name in result.tables:
        try:
            pd.testing.assert_frame_equal(
                result.tables[name],
                repeated.tables[name],
                rtol=1e-10,
                atol=context.configuration.labor.solver_tolerance,
            )
        except AssertionError as exc:
            raise DataError(f"operations deterministic rerun failed: {name}") from exc
    hashes = {}
    for name, table in result.tables.items():
        path = context.resolve_output_path(f"data/{name}.csv")
        temporary = path.with_suffix(".csv.part")
        try:
            table.to_csv(temporary, index=False, float_format="%.12g", lineterminator="\n")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        hashes[name] = file_hash(path)
    success = result.tables["solver_status"]["feasibility"].eq("feasible").all()
    output = context.resolve_output_path("data/operations.metadata.json")
    write_generation_manifest(
        {
            "complete": bool(success),
            "classification": "illustrative",
            "forecast_selection": "retrospective",
            "configuration": context.configuration.model_dump(mode="json"),
            "predictions_sha256": file_hash(prediction_path),
            "champions_sha256": file_hash(champion_path),
            "evaluation_sha256": file_hash(evaluation_path),
            "artifact_sha256": hashes,
            "deterministic_rerun": "PASS",
            "actuals_used_for_allocation": False,
            "inventory_classification": "synthetic_illustrative",
            "planning_rows": 560,
            "contingency_rows": int(result.tables["operational_demand"]["contingency_used"].sum()),
            "solver": (
                "scipy.optimize.linprog(method=highs); stable store order; "
                "no objective perturbation"
            ),
        },
        output,
    )
    if not success:
        raise DataError(
            f"incomplete/infeasible scenario evidence recorded at {output}; "
            "no fabricated optimizer fallback"
        )
    return output
