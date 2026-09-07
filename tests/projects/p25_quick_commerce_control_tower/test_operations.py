"""Independent labor arithmetic, solver constraints, provenance and actual-target isolation."""

from __future__ import annotations

import json
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from linkedin_visual_labs.cli import app
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import operations as o
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import optimization as lp
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    common_holdout,
    file_hash,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.evaluation import NO_CHAMPION
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.forecasting import MODEL_NAMES
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.inventory import (
    inventory_proxy,
    risk_status,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    build_pipeline_context,
)


@pytest.fixture(scope="module")
def config() -> CommerceConfig:
    return load_commerce_config()


@pytest.fixture(scope="module")
def inputs(daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    actual = common_holdout(daily).holdout[[*GRAIN, "demand"]]
    parts = []
    for model in MODEL_NAMES:
        p = actual.rename(columns={"demand": "actual_units"}).copy()
        p["model_name"] = model
        p["forecast_units"] = np.where(p["category"].eq("FOODS"), 3600.0, 1200.0)
        p["raw_forecast_units"] = p["forecast_units"]
        p["was_clipped"] = False
        p["model_status"] = "success"
        parts.append(p)
    champions = actual[["store_id", "category"]].drop_duplicates().copy()
    champions["champion_model"] = "mlp"
    champions["eligibility_status"] = "eligible"
    mask = champions["store_id"].eq("TX_3") & champions["category"].eq("FOODS")
    champions.loc[mask, "champion_model"] = None
    champions.loc[mask, "eligibility_status"] = NO_CHAMPION
    return pd.concat(parts, ignore_index=True), champions


def problem() -> lp.DayProblem:
    return lp.DayProblem(
        ("A", "B", "C"),
        (100.0, 100.0, 100.0),
        (10.0,) * 3,
        (20.0, 100.0, 100.0),
        (22.0,) * 3,
        (1.0, 2.0, 3.0),
        90.0,
        100.0,
        1e-7,
    )


def test_proportional_minima_saturation_redistribution() -> None:
    p = problem()
    a = lp.allocate_day(p, "proportional")
    assert a.status == "feasible"
    np.testing.assert_allclose(a.hours, [20, 35, 35])
    assert sum(a.hours) == pytest.approx(p.capacity)
    lp.validate_allocation(p, a)
    assert a == lp.allocate_day(p, "proportional")


def test_highs_priority_objective_and_tradeoff() -> None:
    p = problem()
    optimized, baseline = lp.allocate_day(p, "optimized"), lp.allocate_day(p, "proportional")
    lp.validate_allocation(p, optimized)
    np.testing.assert_allclose(optimized.hours, [10, 10, 70])
    assert optimized.objective is not None and baseline.objective is not None
    assert optimized.objective < baseline.objective
    assert optimized.hours[0] < baseline.hours[0]
    assert optimized.hours[2] > baseline.hours[2]
    np.testing.assert_allclose(optimized.hours, lp.allocate_day(p, "optimized").hours, atol=1e-7)


@pytest.mark.parametrize("method", ["proportional", "optimized"])
def test_infeasible_minima_no_relaxation(method: str) -> None:
    p = replace(problem(), capacity=29.0)
    result = lp.allocate_day(p, "proportional" if method == "proportional" else "optimized")
    assert result.status == "infeasible"
    assert result.hours == () and result.objective is None
    assert "minimum_total=30" in result.message and "network_capacity=29" in result.message


def test_capacity_unused_low_workload_and_minima() -> None:
    p = replace(problem(), required_hours=(0.0, 12.0, 14.0))
    for method in ("proportional", "optimized"):
        a = lp.allocate_day(p, "proportional" if method == "proportional" else "optimized")
        np.testing.assert_allclose(a.hours, [10, 12, 14])
        assert p.capacity - sum(a.hours) == pytest.approx(54)


def test_expensive_labor_can_leave_shortfall() -> None:
    p = replace(problem(), uncovered_penalty=1.0)
    a = lp.allocate_day(p, "optimized")
    np.testing.assert_allclose(a.hours, p.minimum_hours)
    assert sum(a.uncovered) > 0
    assert sum(a.hours) < p.capacity


def test_solver_failure_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        lp,
        "linprog",
        Mock(
            return_value=SimpleNamespace(
                success=False, status=4, message="intentional solver failure"
            )
        ),
    )
    a = lp.allocate_day(problem(), "optimized")
    assert a.status == "solver_failed" and not a.hours
    assert "intentional solver failure" in a.message


@pytest.mark.parametrize("defect", ["nan", "negative", "size", "priority"])
def test_invalid_solver_inputs(defect: str) -> None:
    p = problem()
    if defect == "nan":
        p = replace(p, required_hours=(float("nan"), 1, 1))
    if defect == "negative":
        p = replace(p, required_hours=(-1, 1, 1))
    if defect == "size":
        p = replace(p, required_hours=(1,))
    if defect == "priority":
        p = replace(p, priority_weight=(0, 1, 1))
    with pytest.raises(DataError):
        lp.allocate_day(p, "optimized")


def test_operational_provenance_and_conversion(
    inputs: tuple[pd.DataFrame, pd.DataFrame], config: CommerceConfig
) -> None:
    p, c = inputs
    original = c.copy(deep=True)
    demand = o.operational_demand(p, c)
    assert "actual_units" not in demand.planning
    assert {field.name for field in fields(lp.DayProblem)}.isdisjoint(
        {"actual_units", "actual_required_hours"}
    )
    assert len(demand.planning) == 560
    contingency = demand.planning.loc[demand.planning["contingency_used"]]
    assert len(contingency) == 28
    assert contingency["forecast_role"].eq("contingency_forecast").all()
    assert contingency["champion_status"].eq("no_eligible_champion").all()
    assert contingency["forecast_source_model"].eq("seasonal_naive").all()
    pd.testing.assert_frame_equal(c, original)
    w = o.workload(demand.planning, config, config.scenarios[0])
    assert w.loc[w["category"].eq("FOODS"), "required_hours"].eq(40).all()
    assert w.loc[w["category"].eq("HOUSEHOLD"), "required_hours"].eq(20).all()
    assert w.groupby(["date", "store_id"])["required_hours"].sum().eq(60).all()
    with pytest.raises(DataError, match="actual demand"):
        o.workload(demand.planning.assign(actual_units=1), config, config.scenarios[0])


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_productivity_config_rejection(config: CommerceConfig, bad: float) -> None:
    settings = config.model_dump()
    settings["labor"]["productivity_units_per_hour"]["FOODS"] = bad
    with pytest.raises(ValidationError):
        CommerceConfig.model_validate(settings)


def test_productivity_missing_category(config: CommerceConfig) -> None:
    settings = config.model_dump()
    del settings["labor"]["productivity_units_per_hour"]["FOODS"]
    with pytest.raises(ValidationError):
        CommerceConfig.model_validate(settings)


def test_invalid_contingency_rejected(inputs: tuple[pd.DataFrame, pd.DataFrame]) -> None:
    p, c = inputs
    p = p.copy()
    mask = (
        p["store_id"].eq("TX_3") & p["category"].eq("FOODS") & p["model_name"].eq("seasonal_naive")
    )
    p.loc[mask, "forecast_units"] = float("nan")
    with pytest.raises(DataError, match="incomplete or invalid"):
        o.operational_demand(p, c)


def test_scenarios_conservation_and_actual_mutation(
    inputs: tuple[pd.DataFrame, pd.DataFrame], config: CommerceConfig
) -> None:
    p, c = inputs
    first = o.run_operations_tables(p, c, config).tables
    changed = p.copy()
    changed["actual_units"] += 1000000
    second = o.run_operations_tables(
        changed.sample(frac=1, random_state=2), c.sample(frac=1, random_state=3), config
    ).tables
    for name in first:
        if name not in ("operational_demand", "retrospective_labor", "retrospective_summary"):
            pd.testing.assert_frame_equal(first[name], second[name], rtol=1e-10, atol=1e-7)
    assert (
        second["retrospective_labor"]["actual_required_hours"].sum()
        > first["retrospective_labor"]["actual_required_hours"].sum()
    )
    allocation = first["labor_allocations"]
    assert len(allocation) == 3 * 2 * 28 * 10
    assert allocation.groupby(["scenario", "allocation_method", "date"]).size().eq(10).all()
    assert (
        allocation.groupby(["scenario", "allocation_method", "date"])["allocated_hours"]
        .sum()
        .le(480 + 1e-7)
        .all()
    )
    assert allocation["allocated_hours"].between(16 - 1e-7, 96 + 1e-7).all()
    summary = first["scenario_summary"]
    assert set(summary.scenario) == {"Base", "+15% demand", "-10% productivity"}
    np.testing.assert_allclose(summary.allocated_hours + summary.unused_capacity, 13440)
    base = float(summary.loc[summary.scenario.eq("Base"), "required_hours"].iloc[0])
    np.testing.assert_allclose(
        summary.loc[summary.scenario.eq("+15% demand"), "required_hours"], base * 1.15
    )
    np.testing.assert_allclose(
        summary.loc[summary.scenario.eq("-10% productivity"), "required_hours"], base / 0.9
    )
    for method in ("proportional", "optimized"):
        group = summary.loc[summary.allocation_method.eq(method)].set_index("scenario")
        assert float(group["uncovered_hours"].loc["+15% demand"]) > float(
            group["uncovered_hours"].loc["Base"]
        )
    objectives = summary.pivot(index="scenario", columns="allocation_method", values="objective")
    assert (objectives.optimized <= objectives.proportional + 1e-6).all()


def test_inventory_seed_labels_arithmetic(
    inputs: tuple[pd.DataFrame, pd.DataFrame], config: CommerceConfig
) -> None:
    planning = o.operational_demand(*inputs).planning
    a = inventory_proxy(planning, config.inventory, config.seed)
    b = inventory_proxy(planning.sample(frac=1, random_state=7), config.inventory, config.seed)
    pd.testing.assert_frame_equal(a, b)
    assert len(a) == 560 and a.synthetic.all() and a.illustrative.all()
    np.testing.assert_allclose(a.days_of_cover, a.synthetic_on_hand_units / a.forecast_daily_mean)
    assert a.generation_days_multiplier.between(0, 7).all()
    assert not a.synthetic_on_hand_units.equals(
        inventory_proxy(planning, config.inventory, 48).synthetic_on_hand_units
    )
    assert a.window_days.min() == 1 and a.window_days.max() == 7


@pytest.mark.parametrize(
    "cover,expected",
    [(0, "Expedite"), (1, "Reorder"), (2, "Monitor"), (4, "Healthy"), (None, "Healthy")],
)
def test_inventory_thresholds(config: CommerceConfig, cover: float | None, expected: str) -> None:
    assert risk_status(cover, config.inventory) == expected


def test_inventory_zero_low_and_missing(
    inputs: tuple[pd.DataFrame, pd.DataFrame], config: CommerceConfig
) -> None:
    planning = o.operational_demand(*inputs).planning
    zero = inventory_proxy(planning.assign(forecast_units=0.0), config.inventory, config.seed)
    assert zero.days_of_cover.isna().all() and zero.synthetic_on_hand_units.eq(0).all()
    assert zero.cover_status.eq("undefined_zero_demand").all()
    low = inventory_proxy(planning.assign(forecast_units=0.001), config.inventory, config.seed)
    assert low.cover_status.eq("low_forecast_demand").all()
    assert np.isfinite(low.days_of_cover).all()
    with pytest.raises(DataError):
        inventory_proxy(planning.iloc[1:], config.inventory, config.seed)


def test_verified_artifacts_cli(
    tmp_path: Path, inputs: tuple[pd.DataFrame, pd.DataFrame], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = build_pipeline_context()
    context = replace(original, paths=replace(original.paths, output_root=tmp_path))
    p = context.resolve_output_path("data/predictions.parquet")
    p.parent.mkdir()
    c = p.with_name("champions.csv")
    inputs[0].to_parquet(p, index=False)
    inputs[1].to_csv(c, index=False)
    metadata = p.with_name("evaluation.metadata.json")
    metadata.write_text(
        json.dumps(
            {
                "predictions_sha256": file_hash(p),
                "artifact_sha256": {"champions": file_hash(c)},
                "sql_python_reconciliation": "PASS",
                "deterministic_evaluation_rerun": "PASS",
            }
        ),
        encoding="utf-8",
    )
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import cli

    monkeypatch.setattr(cli, "build_pipeline_context", lambda *_: context)
    result = CliRunner().invoke(app, ["commerce", "optimize"])
    assert result.exit_code == 0, result.output
    manifest = json.loads(p.with_name("operations.metadata.json").read_text(encoding="utf-8"))
    assert manifest["contingency_rows"] == 28 and manifest["actuals_used_for_allocation"] is False
    assert manifest["complete"] is True
    c.write_text("corrupt", encoding="utf-8")
    assert CliRunner().invoke(app, ["commerce", "optimize"]).exit_code == 1


def test_scenario_failure_evidence(
    inputs: tuple[pd.DataFrame, pd.DataFrame],
    config: CommerceConfig,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lp,
        "linprog",
        Mock(return_value=SimpleNamespace(success=False, status=4, message="deliberate failure")),
    )
    tables = o.run_operations_tables(*inputs, config).tables
    assert tables["labor_allocations"]["allocation_method"].eq("proportional").all()
    failed = tables["scenario_summary"].loc[
        tables["scenario_summary"]["allocation_method"].eq("optimized")
    ]
    assert failed["feasibility"].eq("solver_failed").all()
    assert failed["allocated_hours"].isna().all()
    assert tables["labor_tradeoffs"].empty


def test_scenario_infeasible_constraint_evidence(
    inputs: tuple[pd.DataFrame, pd.DataFrame],
    config: CommerceConfig,
) -> None:
    # The public YAML validator rejects this first; exercise the solver's defensive gate too.
    altered = config.model_copy(
        update={"labor": config.labor.model_copy(update={"daily_network_hours": 100.0})}
    )
    tables = o.run_operations_tables(*inputs, altered).tables
    assert tables["scenario_summary"]["feasibility"].eq("infeasible").all()
    assert tables["solver_status"]["minimum_total_hours"].eq(160).all()
    assert tables["solver_status"]["network_capacity"].eq(100).all()
    assert tables["labor_allocations"].empty
