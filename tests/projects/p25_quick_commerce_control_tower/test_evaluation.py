"""Independent arithmetic, adversarial governance, and offline SQL reconciliation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from linkedin_visual_labs.cli import app
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import evaluation as e
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    common_holdout,
    file_hash,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.forecasting import MODEL_NAMES
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    build_pipeline_context,
)


@pytest.fixture(scope="module")
def config() -> CommerceConfig:
    return load_commerce_config()


@pytest.fixture(scope="module")
def sql_directory() -> Path:
    return build_pipeline_context().paths.repository_root / "sql/p25_quick_commerce_control_tower"


@pytest.fixture(scope="module")
def predictions(daily: pd.DataFrame) -> pd.DataFrame:
    """Test-only hypothetical methods, independent of the fitted forecasting implementation."""
    actual = common_holdout(daily).holdout[[*GRAIN, "demand"]]
    parts = []
    for index, model in enumerate(MODEL_NAMES):
        frame = actual.rename(columns={"demand": "actual_units"}).copy()
        frame["model_name"] = model
        frame["forecast_units"] = frame["actual_units"] * (1 + index * 0.01)
        frame["raw_forecast_units"] = frame["forecast_units"]
        frame["was_clipped"] = False
        frame["model_status"] = "success"
        parts.append(frame)
    return pd.concat(parts, ignore_index=True)


def arithmetic(actual: list[float], forecast: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "actual_units": actual,
            "forecast_units": forecast,
            "raw_forecast_units": forecast,
            "valid": [True] * len(actual),
            "raw_finite": [True] * len(actual),
        }
    )


def test_hand_calculated_metrics() -> None:
    result = e.metric_summary(arithmetic([10, 20, 30], [8, 25, 30]))
    assert result["wape"] == pytest.approx(7 / 60)
    assert result["mae"] == pytest.approx(7 / 3)
    assert result["bias"] == pytest.approx(3 / 60)
    assert result["underforecast_rate"] == pytest.approx(1 / 3)
    assert result["overforecast_rate"] == pytest.approx(1 / 3)
    assert result["under_count"] == result["over_count"] == 1
    assert result["shortfall_units"] == 2
    assert result["excess_units"] == 5
    assert result["completeness"] == 1


def test_undefined_metrics() -> None:
    zero = e.metric_summary(arithmetic([0, 0], [1, 0]))
    assert zero["wape"] is None and zero["bias"] is None
    assert zero["mae"] == 0.5
    assert zero["metric_status"] == "undefined_zero_demand"
    empty = e.metric_summary(arithmetic([], []))
    assert empty["observations"] == 0
    assert empty["wape"] is None and empty["mae"] is None
    assert empty["completeness"] is None and empty["clipping_rate"] is None
    assert empty["metric_status"] == "undefined_empty"


def test_pooled_network_not_average_of_ratios() -> None:
    first, second = arithmetic([1], [2]), arithmetic([99], [99])
    pooled = e.metric_summary(pd.concat([first, second]))
    assert pooled["wape"] == pytest.approx(0.01)
    assert (
        float(e.metric_summary(first)["wape"] or 0) + float(e.metric_summary(second)["wape"] or 0)
    ) / 2 == 0.5


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "duplicate",
        "nan",
        "inf",
        "negative",
        "bias",
        "clipping",
        "actual",
        "failed_status",
        "extra",
    ],
)
def test_bad_candidate_cannot_win(
    defect: str, daily: pd.DataFrame, predictions: pd.DataFrame, config: CommerceConfig
) -> None:
    frame = predictions.copy()
    subject = (
        frame["model_name"].eq("seasonal_naive")
        & frame["store_id"].eq("CA_1")
        & frame["category"].eq("FOODS")
    )
    index = frame.index[subject][0]
    if defect == "missing":
        frame = frame.drop(index)
    elif defect == "duplicate":
        frame = pd.concat([frame, frame.loc[[index]]], ignore_index=True)
    elif defect == "extra":
        extra = frame.loc[[index]].copy()
        extra["date"] = pd.Timestamp("2099-01-01")
        frame = pd.concat([frame, extra], ignore_index=True)
    elif defect == "bias":
        frame.loc[subject, ["forecast_units", "raw_forecast_units"]] *= 2
    elif defect == "clipping":
        frame.loc[index, "was_clipped"] = True
    elif defect == "actual":
        frame.loc[index, "actual_units"] = 999
    elif defect == "failed_status":
        frame.loc[index, "model_status"] = "failed"
    else:
        value = {"nan": np.nan, "inf": np.inf, "negative": -10}[defect]
        frame.loc[index, "forecast_units"] = value
        frame.loc[index, "raw_forecast_units"] = value
    errors = e.normalize_predictions(frame, daily, strict_grid=False)
    candidates = e.candidate_eligibility(errors, config, deterministic_validated=True)
    bad = candidates.loc[
        candidates["model_name"].eq("seasonal_naive")
        & candidates["store_id"].eq("CA_1")
        & candidates["category"].eq("FOODS")
    ].iloc[0]
    assert not bad["eligible"] and bad["rejection_reasons"]
    _, spread = e.disagreement(errors, daily)
    champions = e.select_champions(candidates, spread, 0.5)
    assert (
        champions.loc[
            champions["store_id"].eq("CA_1") & champions["category"].eq("FOODS"), "champion_model"
        ].iloc[0]
        == "holt_winters"
    )


def test_no_champion_without_determinism(
    daily: pd.DataFrame, predictions: pd.DataFrame, config: CommerceConfig
) -> None:
    errors = e.normalize_predictions(predictions, daily)
    candidates = e.candidate_eligibility(errors, config, deterministic_validated=False)
    _, spread = e.disagreement(errors, daily)
    champions = e.select_champions(candidates, spread, 0.5)
    assert len(champions) == 20
    assert champions["champion_model"].isna().all()
    assert champions["eligibility_status"].eq(e.NO_CHAMPION).all()


def test_ties_baseline_and_lowest_eligible(
    daily: pd.DataFrame, predictions: pd.DataFrame, config: CommerceConfig
) -> None:
    tied = predictions.copy()
    tied["forecast_units"] = tied["actual_units"]
    tied["raw_forecast_units"] = tied["actual_units"]
    errors = e.normalize_predictions(tied, daily)
    candidates = e.candidate_eligibility(errors, config, deterministic_validated=True)
    _, spread = e.disagreement(errors, daily)
    champions = e.select_champions(candidates.sample(frac=1, random_state=12), spread, 0.5)
    assert champions["champion_model"].eq("seasonal_naive").all()
    assert champions["improvement_vs_seasonal_naive"].eq(0).all()
    assert champions["relative_improvement"].isna().all()
    assert not champions.duplicated(e.SERIES).any()
    candidates.loc[candidates["model_name"].eq("seasonal_naive"), "eligible"] = False
    champions = e.select_champions(candidates, spread, 0.5)
    assert champions["champion_model"].eq("holt_winters").all()


def test_disagreement_training_normalization(
    daily: pd.DataFrame, predictions: pd.DataFrame
) -> None:
    tied = predictions.copy()
    tied["forecast_units"] = 10.0
    tied["raw_forecast_units"] = 10.0
    dates, _ = e.disagreement(e.normalize_predictions(tied, daily), daily)
    assert dates["disagreement"].eq(0).all()
    tied.loc[tied["model_name"].eq("mlp"), ["forecast_units", "raw_forecast_units"]] = 20.0
    dates, spread = e.disagreement(e.normalize_predictions(tied, daily), daily)
    np.testing.assert_allclose(dates["disagreement"], 10 / dates["training_scale"])
    assert spread["disagreement"].gt(0).all()
    changed = daily.copy()
    changed.loc[changed["date"] > common_holdout(daily).origin, "demand"] += 1000
    tied["actual_units"] += 1000
    other, _ = e.disagreement(e.normalize_predictions(tied, changed), changed)
    pd.testing.assert_frame_equal(dates, other)


def test_sql_python_and_exception_determinism(
    daily: pd.DataFrame, predictions: pd.DataFrame, config: CommerceConfig, sql_directory: Path
) -> None:
    first = e.evaluate_predictions(
        predictions, daily, config, sql_directory, deterministic_validated=True
    )
    second = e.evaluate_predictions(
        predictions.sample(frac=1, random_state=123),
        daily,
        config,
        sql_directory,
        deterministic_validated=True,
    )
    for name in first.tables:
        pd.testing.assert_frame_equal(
            first.tables[name], second.tables[name], rtol=1e-10, atol=1e-8
        )
    assert len(first.tables["champions"]) == 20
    assert first.tables["champion_counts"]["champion_count"].sum() == 20
    assert first.tables["local_champion_portfolio"]["classification"].eq("retrospective").all()
    queue = first.tables["dri_exception_queue"]
    for column in (
        "observed_pattern",
        "evidence",
        "operational_implication",
        "recommended_experiment",
    ):
        assert queue[column].str.len().gt(20).all()
    assert queue["evidence"].str.contains("Actual units").all()
    assert queue["evidence"].str.contains("n=").all()
    assert queue["priority_score"].is_monotonic_decreasing
    assert queue["observed_pattern"].str.contains("No unit forecast error").all()
    assert queue["operational_implication"].str.contains("no measured unit-error exposure").all()


def test_empty_event_sql(
    daily: pd.DataFrame, predictions: pd.DataFrame, config: CommerceConfig, sql_directory: Path
) -> None:
    altered = daily.copy()
    altered[["event_name_1", "event_name_2", "event_type_1", "event_type_2"]] = ""
    tables = e.evaluate_predictions(
        predictions, altered, config, sql_directory, deterministic_validated=True
    ).tables
    event = tables["event_analysis"].loc[tables["event_analysis"]["dimension"].eq("event")]
    assert event["observations"].eq(0).all()
    assert event["wape"].isna().all()
    assert event["metric_status"].eq("undefined_empty").all()


def test_material_miss_priority(
    daily: pd.DataFrame, predictions: pd.DataFrame, config: CommerceConfig, sql_directory: Path
) -> None:
    altered = daily.copy()
    altered.loc[altered["store_id"].eq("CA_1"), "demand"] = 10000.0
    altered.loc[altered["store_id"].eq("WI_3"), "demand"] = 1.0
    holdout = common_holdout(altered).holdout[[*GRAIN, "demand"]]
    p = (
        predictions.drop(columns="actual_units")
        .merge(holdout, on=GRAIN)
        .rename(columns={"demand": "actual_units"})
    )
    p["forecast_units"] = p["actual_units"] * 0.95
    p.loc[p["store_id"].eq("WI_3"), "forecast_units"] = 0.0
    p["raw_forecast_units"] = p["forecast_units"]
    result = e.evaluate_predictions(p, altered, config, sql_directory, deterministic_validated=True)
    queue = result.tables["dri_exception_queue"]
    high = queue.loc[queue["store_id"].eq("CA_1"), "priority_score"].min()
    low = queue.loc[queue["store_id"].eq("WI_3"), "priority_score"].max()
    assert high > low


def test_reconciliation_rejects_drift(daily: pd.DataFrame, predictions: pd.DataFrame) -> None:
    errors = e.normalize_predictions(predictions, daily)
    python = e.python_scorecards(errors, e.scorecard_grid(errors))
    altered = python.copy()
    altered.loc[0, "wape"] = 100
    with pytest.raises(DataError, match="drift"):
        e.reconcile(python, altered)


def test_strict_grid_rejects_missing(daily: pd.DataFrame, predictions: pd.DataFrame) -> None:
    with pytest.raises(DataError, match="2240"):
        e.normalize_predictions(predictions.iloc[1:], daily)


def test_valid_clipping_and_review_threshold(
    daily: pd.DataFrame,
    predictions: pd.DataFrame,
    config: CommerceConfig,
) -> None:
    p = predictions.copy()
    index = p.index[p["actual_units"].eq(0) & p["model_name"].eq("seasonal_naive")][0]
    p.loc[index, "raw_forecast_units"] = -5.0
    p.loc[index, "was_clipped"] = True
    errors = e.normalize_predictions(p, daily)
    candidates = e.candidate_eligibility(errors, config, deterministic_validated=True)
    assert candidates["eligible"].all()
    assert candidates["clipping_count"].sum() == 1
    assert candidates["clipping_rate"].max() == pytest.approx(1 / 28)
    _, spread = e.disagreement(errors, daily)
    assert e.select_champions(candidates, spread, 1e-9)["review_flag"].all()
    assert not e.select_champions(candidates, spread, 100)["review_flag"].any()


def test_invalid_row_sql_coverage(
    daily: pd.DataFrame,
    predictions: pd.DataFrame,
    config: CommerceConfig,
    sql_directory: Path,
) -> None:
    p = predictions.copy()
    p.loc[0, "forecast_units"] = float("nan")
    tables = e.evaluate_predictions(
        p, daily, config, sql_directory, deterministic_validated=True
    ).tables
    baseline = (
        tables["network_scorecard"]
        .loc[tables["network_scorecard"]["model_name"].eq("seasonal_naive")]
        .iloc[0]
    )
    assert baseline["observations"] == 559
    assert baseline["completeness"] == pytest.approx(559 / 560)
    assert baseline["metric_status"] == "partial_coverage"
    assert not baseline["globally_eligible"]


def test_config_bounds(config: CommerceConfig) -> None:
    settings = config.model_dump()
    settings["diagnostics"]["weights"] = {name: 0.0 for name in settings["diagnostics"]["weights"]}
    with pytest.raises(ValidationError, match="positive total"):
        CommerceConfig.model_validate(settings)


def test_all_unassigned_sql(
    daily: pd.DataFrame,
    predictions: pd.DataFrame,
    config: CommerceConfig,
    sql_directory: Path,
) -> None:
    tables = e.evaluate_predictions(
        predictions, daily, config, sql_directory, deterministic_validated=False
    ).tables
    assert tables["champions"]["eligibility_status"].eq(e.NO_CHAMPION).all()
    assert tables["champion_counts"].empty
    assert not tables["network_scorecard"]["global_winner"].any()
    assert tables["dri_exception_queue"]["subject"].eq("unassigned_baseline_review_only").all()
    assert tables["local_champion_portfolio"]["observations"].eq(0).all()
    assert tables["local_champion_portfolio"]["wape"].isna().all()


def test_real_artifact_runner_and_cli(
    tmp_path: Path, daily: pd.DataFrame, predictions: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = build_pipeline_context()
    context = replace(original, paths=replace(original.paths, output_root=tmp_path))
    data_path = context.resolve_output_path("data/demand_daily.parquet")
    data_path.parent.mkdir()
    # Local runner contract test only: these files remain isolated under pytest's temp directory.
    daily.assign(data_classification="public_real_m5").to_parquet(data_path, index=False)
    p = data_path.with_name("predictions.parquet")
    predictions.to_parquet(p, index=False)
    p.with_suffix(".metadata.json").write_text(
        json.dumps(
            {
                "complete": True,
                "classification": "public_real_m5",
                "predictions_sha256": file_hash(p),
                "source_sha256": file_hash(data_path),
                "configuration": context.configuration.model_dump(mode="json"),
            }
        )
    )
    proof = tmp_path / "proof.json"
    proof.write_text(
        json.dumps(
            {
                "predictions_sha256": file_hash(p),
                "prepared_sha256": file_hash(data_path),
                "real_mutation_rerun": "PASS",
                "max_raw_difference": 0,
                "configuration": context.configuration.model_dump(mode="json"),
            }
        )
    )
    output = e.run_evaluation(context, proof)
    manifest = json.loads(output.read_text())
    assert manifest["sql_python_reconciliation"] == "PASS"
    assert manifest["deterministic_evaluation_rerun"] == "PASS"
    assert (output.parent / "champions.csv").exists()
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import cli

    monkeypatch.setattr(cli, "build_pipeline_context", lambda *_: context)
    response = CliRunner().invoke(app, ["commerce", "evaluate", "--validation-record", str(proof)])
    assert response.exit_code == 0, response.output
    for path in (proof, p.with_suffix(".metadata.json")):
        original_text = path.read_text()
        tampered = json.loads(original_text)
        tampered["configuration"]["seed"] += 1
        path.write_text(json.dumps(tampered))
        with pytest.raises(DataError, match="validation"):
            e.run_evaluation(context, proof)
        path.write_text(original_text)
    proof.write_text("{}")
    response = CliRunner().invoke(app, ["commerce", "evaluate", "--validation-record", str(proof)])
    assert response.exit_code == 1
