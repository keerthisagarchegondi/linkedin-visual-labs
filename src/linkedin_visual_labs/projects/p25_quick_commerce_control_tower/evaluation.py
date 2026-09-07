"""Frozen-forecast metrics, independent SQL reconciliation, and retrospective governance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from linkedin_visual_labs.common.media import write_generation_manifest
from linkedin_visual_labs.common.paths import ensure_path_within
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    GRAIN,
    DataError,
    common_holdout,
    file_hash,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.forecasting import (
    MODEL_NAMES,
    PREDICTION_COLUMNS,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext

NO_CHAMPION = "No eligible champion—review required"
SERIES = ["store_id", "category"]
KEYS = [*GRAIN, "model_name"]
Metric = float | int | str | None
LEVELS = (
    "network",
    "store",
    "category",
    "store_category",
    "day_of_week",
    "event",
    "snap",
    "horizon",
)


@dataclass(frozen=True)
class EvaluationResult:
    tables: dict[str, pd.DataFrame]


def metric_summary(frame: pd.DataFrame) -> dict[str, Metric]:
    """Independent Python sums; null ratios retain explicit coverage/denominator status."""
    valid = frame.loc[frame["valid"]]
    count, expected = len(valid), len(frame)
    actual = float(valid["actual_units"].sum())
    forecast = float(valid["forecast_units"].sum())
    errors = valid["forecast_units"] - valid["actual_units"]
    absolute = float(errors.abs().sum())
    signed = float(errors.sum())
    raw = frame.loc[frame["raw_finite"], "raw_forecast_units"]
    clipped = int(raw.lt(0).sum())
    return {
        "expected_observations": expected,
        "observations": count,
        "demand_volume": float(frame["actual_units"].sum()),
        "actual_units": actual,
        "forecast_units": forecast,
        "absolute_error": absolute,
        "signed_error": signed,
        "shortfall_units": float((-errors).clip(lower=0).sum()),
        "excess_units": float(errors.clip(lower=0).sum()),
        "under_count": int(errors.lt(0).sum()),
        "over_count": int(errors.gt(0).sum()),
        "finite_raw_count": len(raw),
        "clipping_count": clipped,
        "wape": absolute / actual if actual else None,
        "mae": absolute / count if count else None,
        "bias": signed / actual if actual else None,
        "underforecast_rate": float(errors.lt(0).mean()) if count else None,
        "overforecast_rate": float(errors.gt(0).mean()) if count else None,
        "completeness": count / expected if expected else None,
        "clipping_rate": clipped / len(raw) if len(raw) else None,
        "metric_status": (
            "undefined_empty"
            if not count
            else "undefined_zero_demand"
            if not actual
            else "partial_coverage"
            if count < expected
            else "defined"
        ),
    }


def normalize_predictions(
    predictions: pd.DataFrame,
    daily: pd.DataFrame,
    *,
    strict_grid: bool = True,
) -> pd.DataFrame:
    """Preserve invalid/missing candidates as expected rows; never silently improve coverage."""
    if not set(PREDICTION_COLUMNS).issubset(predictions.columns):
        raise DataError("canonical prediction schema missing required fields")
    split = common_holdout(daily)
    expected = split.holdout.merge(pd.DataFrame({"model_name": MODEL_NAMES}), how="cross")
    if predictions[KEYS].isna().any().any():
        raise DataError("null canonical prediction keys")
    if strict_grid and (
        len(predictions) != 2240
        or predictions.duplicated(KEYS).any()
        or not pd.MultiIndex.from_frame(predictions[KEYS])
        .sort_values()
        .equals(pd.MultiIndex.from_frame(expected[KEYS]).sort_values())
    ):
        raise DataError("canonical predictions must contain exactly 2240 unique expected keys")
    supplied = predictions.copy()
    supplied["input_rows"] = supplied.groupby(KEYS)["model_name"].transform("size")
    supplied["series_input_rows"] = supplied.groupby([*SERIES, "model_name"])["date"].transform(
        "size"
    )
    supplied = supplied.drop_duplicates(KEYS, keep="first")
    joined = expected.merge(supplied, on=KEYS, how="left", validate="one_to_one")
    joined["actual_matches"] = joined["actual_units"].eq(joined["demand"])
    # Prepared demand is authoritative even when a candidate carries a corrupt actual column.
    joined["actual_units"] = joined["demand"].astype(float)
    numeric = joined[["forecast_units", "raw_forecast_units"]].to_numpy(dtype=float)
    finite = np.isfinite(numeric).all(axis=1)
    joined["raw_finite"] = np.isfinite(numeric[:, 1]) & joined["input_rows"].eq(1)
    joined["postprocessing_valid"] = joined["forecast_units"].eq(
        joined["raw_forecast_units"].clip(lower=0)
    ) & joined["was_clipped"].eq(joined["raw_forecast_units"].lt(0))
    joined["valid"] = (
        finite
        & joined["input_rows"].eq(1)
        & joined["actual_matches"]
        & joined["forecast_units"].ge(0)
        & joined["postprocessing_valid"]
        & joined["model_status"].isin(["success", "warning"])
    )
    joined["event_status"] = np.where(
        joined["event_name_1"].fillna("").ne("") | joined["event_name_2"].fillna("").ne(""),
        "event",
        "ordinary",
    )
    joined["snap_status"] = np.where(joined["snap"].eq(1), "active", "inactive")
    joined["horizon"] = (joined["date"] - split.origin).dt.days
    return joined.sort_values(KEYS).reset_index(drop=True)


def level_values(frame: pd.DataFrame, level: str) -> pd.Series[str]:
    if level == "network":
        return pd.Series("ALL", index=frame.index)
    if level == "store_category":
        return frame["store_id"].astype(str) + "/" + frame["category"].astype(str)
    column = {
        "store": "store_id",
        "day_of_week": "weekday",
        "event": "event_status",
        "snap": "snap_status",
    }.get(level, level)
    return frame[column].astype(str)


def scorecard_grid(errors: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for level in LEVELS:
        dimensions = sorted(level_values(errors, level).unique())
        if level == "event":
            dimensions = ["event", "ordinary"]
        if level == "snap":
            dimensions = ["active", "inactive"]
        rows.extend(
            {"level": level, "dimension": str(d), "model_name": m}
            for d in dimensions
            for m in MODEL_NAMES
        )
    return pd.DataFrame(rows)


def python_scorecards(errors: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Metric]] = []
    for entry in grid.to_dict(orient="records"):
        selected = errors.loc[
            level_values(errors, str(entry["level"])).eq(str(entry["dimension"]))
            & errors["model_name"].eq(str(entry["model_name"]))
        ]
        rows.append({**{str(k): v for k, v in entry.items()}, **metric_summary(selected)})
    return (
        pd.DataFrame(rows).sort_values(["level", "dimension", "model_name"]).reset_index(drop=True)
    )


def candidate_eligibility(
    errors: pd.DataFrame,
    config: CommerceConfig,
    *,
    deterministic_validated: bool,
) -> pd.DataFrame:
    rows: list[dict[str, Metric]] = []
    for (store, category, model), group in errors.groupby([*SERIES, "model_name"], sort=True):
        metrics = metric_summary(group)
        reasons: list[str] = []
        if not group["input_rows"].eq(1).all() or not group["series_input_rows"].eq(28).all():
            reasons.append("missing_duplicate_or_extra_predictions")
        if len(group) != 28 or group["date"].nunique() != 28 or metrics["completeness"] != 1:
            reasons.append("incomplete_or_invalid_predictions")
        if not group["postprocessing_valid"].all():
            reasons.append("postprocessing_contract_failed")
        if not group["actual_matches"].all():
            reasons.append("actual_demand_mismatch")
        bias = metrics["bias"]
        if bias is None or abs(float(bias)) > config.governance.absolute_bias_guardrail:
            reasons.append("undefined_or_excessive_bias")
        if not deterministic_validated:
            reasons.append("deterministic_validation_not_passed")
        rows.append(
            {
                "store_id": str(store),
                "category": str(category),
                "model_name": str(model),
                **metrics,
                "eligible": not reasons,
                "rejection_reasons": "|".join(reasons),
                "tie_rank": MODEL_NAMES.index(str(model)),
                "deterministic_validated": deterministic_validated,
            }
        )
    return pd.DataFrame(rows)


def disagreement(errors: pd.DataFrame, daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    training = common_holdout(daily).training
    scales = training.groupby(SERIES)["demand"].mean().rename("training_mean")
    rows: list[dict[str, Metric | pd.Timestamp]] = []
    for (date, store, category), group in errors.groupby(GRAIN, sort=True):
        valid = group.loc[group["valid"], "forecast_units"]
        mean = float(scales.to_dict()[(store, category)])
        scale = max(mean, 1.0)
        count = len(valid)
        rows.append(
            {
                "date": pd.Timestamp(str(date)),
                "store_id": str(store),
                "category": str(category),
                "model_count": count,
                "training_mean": mean,
                "training_scale": scale,
                "disagreement": float(valid.max() - valid.min()) / scale if count >= 2 else None,
                "coverage_status": "complete"
                if count == 4
                else "partial"
                if count >= 2
                else "insufficient_model_coverage",
            }
        )
    dates = pd.DataFrame(rows)
    summary = dates.groupby(SERIES, as_index=False).agg(
        disagreement=("disagreement", "mean"),
        maximum_disagreement=("disagreement", "max"),
        dates_with_disagreement=("disagreement", "count"),
        minimum_model_count=("model_count", "min"),
        training_scale=("training_scale", "first"),
    )
    summary["coverage_status"] = np.where(
        summary["minimum_model_count"].eq(4), "complete", "partial"
    )
    return dates, summary


def select_champions(
    candidates: pd.DataFrame, spread: pd.DataFrame, threshold: float
) -> pd.DataFrame:
    rows: list[dict[str, Metric]] = []
    for (store, category), group in candidates.groupby(SERIES, sort=True):
        baseline = group.loc[group["model_name"].eq("seasonal_naive")].iloc[0]
        eligible = group.loc[group["eligible"]].sort_values(["wape", "tie_rank"])
        row: dict[str, Metric] = {
            "store_id": str(store),
            "category": str(category),
            "classification": "retrospective",
            "champion_model": None,
            "eligibility_status": NO_CHAMPION,
            "wape": None,
            "mae": None,
            "bias": None,
            "completeness": None,
            "clipping_rate": None,
            "seasonal_naive_wape": baseline["wape"],
            "baseline_bias": baseline["bias"],
            "improvement_vs_seasonal_naive": None,
            "improvement_percentage_points": None,
            "relative_improvement": None,
            "improvement_status": "undefined_no_champion",
        }
        if not eligible.empty:
            winner = eligible.iloc[0]
            row.update(
                {
                    key: winner[key]
                    for key in ("wape", "mae", "bias", "completeness", "clipping_rate")
                }
            )
            row.update(champion_model=str(winner["model_name"]), eligibility_status="eligible")
            if baseline["completeness"] == 1 and pd.notna(baseline["wape"]):
                delta = float(baseline["wape"] - winner["wape"])
                row.update(
                    improvement_vs_seasonal_naive=delta,
                    improvement_percentage_points=100 * delta,
                    relative_improvement=delta / float(baseline["wape"])
                    if baseline["wape"]
                    else None,
                    improvement_status="defined" if baseline["wape"] else "undefined_zero_baseline",
                )
            else:
                row["improvement_status"] = "undefined_incomplete_baseline"
        rows.append(row)
    champions = pd.DataFrame(rows).merge(spread, on=SERIES, validate="one_to_one")
    champions["champion_model"] = champions["champion_model"].astype("string")
    champions["review_flag"] = champions["disagreement"].gt(threshold)
    champions["review_threshold"] = threshold
    return champions.sort_values(SERIES).reset_index(drop=True)


def reconcile(python: pd.DataFrame, sql: pd.DataFrame) -> None:
    keys = ["level", "dimension", "model_name"]
    left = python.sort_values(keys).reset_index(drop=True)
    right = sql.sort_values(keys).reset_index(drop=True)
    if not left[keys].equals(right[keys]) or not left["metric_status"].equals(
        right["metric_status"]
    ):
        raise DataError("SQL/Python scorecard keys or statuses disagree")
    columns = [c for c in left if c not in [*keys, "metric_status"]]
    try:
        np.testing.assert_allclose(
            left[columns].to_numpy(dtype=float),
            right[columns].to_numpy(dtype=float),
            rtol=1e-10,
            atol=1e-8,
            equal_nan=True,
        )
    except AssertionError as exc:
        raise DataError("SQL/Python metric drift") from exc


def evaluate_predictions(
    predictions: pd.DataFrame,
    daily: pd.DataFrame,
    config: CommerceConfig,
    sql_directory: Path,
    *,
    deterministic_validated: bool,
) -> EvaluationResult:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.diagnostics import (
        exception_components,
        narrate_exceptions,
    )

    normalized = normalize_predictions(predictions, daily)
    tables: dict[str, pd.DataFrame] = {}
    with duckdb.connect() as connection:
        connection.execute("SET threads=1")
        connection.register(
            "diagnostics_settings",
            pd.DataFrame(
                [
                    {
                        "minimum_subgroup_observations": (
                            config.diagnostics.minimum_subgroup_observations
                        )
                    }
                ]
            ),
        )

        def query(name: str) -> pd.DataFrame:
            frame = connection.execute((sql_directory / f"{name}.sql").read_text()).df()
            connection.register(name, frame)
            tables[name] = frame
            return frame

        connection.register("normalized_predictions", normalized)
        errors = query("prediction_errors")
        grid = scorecard_grid(errors)
        connection.register("scorecard_grid", grid)
        rollup = query("metric_rollup")
        reconcile(python_scorecards(errors, grid), rollup)
        candidates = candidate_eligibility(
            errors, config, deterministic_validated=deterministic_validated
        )
        dates, spread = disagreement(errors, daily)
        champions = select_champions(
            candidates, spread, config.diagnostics.disagreement_review_threshold
        )
        tables.update(
            candidate_eligibility=candidates,
            model_disagreement=dates,
            disagreement_summary=spread,
            champions=champions,
        )
        connection.register("candidate_eligibility", candidates)
        connection.register("champions", champions)
        for name in (
            "network_scorecard",
            "store_category_scorecard",
            "event_analysis",
            "snap_analysis",
            "day_of_week_analysis",
            "under_over_rankings",
            "high_volume_exceptions",
            "champion_map",
            "champion_counts",
        ):
            query(name)
        expected_counts = champions["champion_model"].dropna().value_counts().sort_index()
        actual_counts = (
            tables["champion_counts"].set_index("model_name")["champion_count"].sort_index()
        )
        if expected_counts.to_dict() != actual_counts.to_dict():
            raise DataError("SQL/Python champion count drift")
        components = exception_components(errors, candidates, champions, spread, config)
        connection.register("exception_components", components)
        connection.register(
            "exception_weights", pd.DataFrame([config.diagnostics.weights.model_dump()])
        )
        queue = query("dri_exception_queue")
        tables["dri_exception_queue"] = narrate_exceptions(queue, config)
    for level in ("store", "category", "horizon"):
        tables[f"{level}_scorecard"] = rollup.loc[rollup["level"].eq(level)].reset_index(drop=True)
    network = tables["network_scorecard"].copy()
    eligibility = candidates.groupby("model_name")["eligible"].all()
    network["globally_eligible"] = network["model_name"].map(eligibility)
    ranked = (
        network.loc[network["globally_eligible"]]
        .assign(tie_rank=lambda f: f["model_name"].map({m: i for i, m in enumerate(MODEL_NAMES)}))
        .sort_values(["wape", "tie_rank"])
    )
    network["global_winner"] = (
        network["model_name"].eq(str(ranked.iloc[0]["model_name"])) if len(ranked) else False
    )
    network["global_selection_status"] = (
        "available" if len(ranked) else "No globally eligible model"
    )
    tables["network_scorecard"] = network
    counts = champions["champion_model"].value_counts().reindex(MODEL_NAMES, fill_value=0)
    tables["champion_distribution"] = pd.DataFrame(
        {
            "model_name": [*MODEL_NAMES, "unassigned"],
            "series_count": [*counts.tolist(), int(champions["champion_model"].isna().sum())],
            "classification": "retrospective",
        }
    )
    selected = errors.merge(champions[[*SERIES, "champion_model"]], on=SERIES)
    portfolio = selected.loc[selected["model_name"].eq(selected["champion_model"])]
    baseline = errors.loc[errors["model_name"].eq("seasonal_naive")].merge(
        champions.loc[champions["champion_model"].notna(), SERIES],
        on=SERIES,
    )
    tables["local_champion_portfolio"] = pd.DataFrame(
        [
            {
                "portfolio": "local_champions",
                "classification": "retrospective",
                "covered_series": len(champions.dropna(subset=["champion_model"])),
                "total_series": 20,
                **metric_summary(portfolio),
            },
            {
                "portfolio": "seasonal_naive_same_coverage",
                "classification": "retrospective",
                "covered_series": len(champions.dropna(subset=["champion_model"])),
                "total_series": 20,
                **metric_summary(baseline),
            },
        ]
    )
    return EvaluationResult(tables)


def run_evaluation(context: PipelineContext, validation_record: Path | str) -> Path:
    """Use frozen real artifacts and hash-bound prior deterministic evidence; never refit."""
    prediction_path = context.resolve_output_path("data/predictions.parquet")
    daily_path = context.resolve_output_path("data/demand_daily.parquet")
    metadata = json.loads(prediction_path.with_suffix(".metadata.json").read_text())
    proof_path = ensure_path_within(
        context.paths.repository_root / validation_record, context.paths.repository_root
    )
    proof = json.loads(proof_path.read_text())
    prediction_hash, daily_hash = file_hash(prediction_path), file_hash(daily_path)
    if (
        metadata.get("complete") is not True
        or metadata.get("classification") != "public_real_m5"
        or metadata.get("predictions_sha256") != prediction_hash
        or metadata.get("source_sha256") != daily_hash
        or metadata.get("configuration") != context.configuration.model_dump(mode="json")
    ):
        raise DataError("frozen real forecast manifest/hash validation failed")
    if (
        proof.get("predictions_sha256") != prediction_hash
        or proof.get("prepared_sha256") != daily_hash
        or proof.get("real_mutation_rerun") != "PASS"
        or proof.get("max_raw_difference") != 0
        or proof.get("configuration") != context.configuration.model_dump(mode="json")
    ):
        raise DataError("hash-bound Step 3 deterministic validation proof missing or failed")
    predictions, daily = pd.read_parquet(prediction_path), pd.read_parquet(daily_path)
    if not daily["data_classification"].eq("public_real_m5").all():
        raise DataError("real prepared classification mismatch")
    sql_directory = context.paths.repository_root / context.configuration.paths.sql
    result = evaluate_predictions(
        predictions, daily, context.configuration, sql_directory, deterministic_validated=True
    )
    repeated = evaluate_predictions(
        predictions.sample(frac=1, random_state=47),
        daily,
        context.configuration,
        sql_directory,
        deterministic_validated=True,
    )
    for name, table in result.tables.items():
        try:
            pd.testing.assert_frame_equal(table, repeated.tables[name], rtol=1e-10, atol=1e-8)
        except AssertionError as exc:
            raise DataError(f"deterministic evaluation rerun failed: {name}") from exc
    hashes: dict[str, str] = {}
    for name, table in result.tables.items():
        output = context.resolve_output_path(f"data/{name}.csv")
        temporary = output.with_suffix(".csv.part")
        try:
            table.to_csv(temporary, index=False, float_format="%.12g", lineterminator="\n")
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        hashes[name] = file_hash(output)
    manifest = context.resolve_output_path("data/evaluation.metadata.json")
    write_generation_manifest(
        {
            "classification": "measured_historical_backtest",
            "local_selection": "retrospective",
            "predictions_sha256": prediction_hash,
            "prepared_sha256": daily_hash,
            "deterministic_proof_sha256": file_hash(proof_path),
            "configuration": context.configuration.model_dump(mode="json"),
            "sql_sha256": {p.name: file_hash(p) for p in sorted(sql_directory.glob("*.sql"))},
            "sql_python_reconciliation": "PASS",
            "deterministic_evaluation_rerun": "PASS",
            "tolerance": {"rtol": 1e-10, "atol": 1e-8},
            "artifact_sha256": hashes,
            "prediction_rows": len(predictions),
            "no_champion_count": int(result.tables["champions"]["champion_model"].isna().sum()),
        },
        manifest,
    )
    return manifest
