"""Measured exception components and deterministic, noncausal review narratives."""

from __future__ import annotations

import pandas as pd

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig


def exception_components(
    errors: pd.DataFrame,
    candidates: pd.DataFrame,
    champions: pd.DataFrame,
    spread: pd.DataFrame,
    config: CommerceConfig,
) -> pd.DataFrame:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.evaluation import (
        metric_summary,
    )

    network_volume = float(
        errors.drop_duplicates(["date", "store_id", "category"])["actual_units"].sum()
    )
    # Unit floor applies only to priority normalization, never to WAPE/bias denominators.
    normalizer = max(network_volume, 1.0)
    rows: list[dict[str, object]] = []
    for champion in champions.to_dict(orient="records"):
        store, category = champion["store_id"], champion["category"]
        selected_champion = pd.notna(champion["champion_model"])
        model = str(champion["champion_model"]) if selected_champion else "seasonal_naive"
        candidate = candidates.loc[
            candidates["store_id"].eq(store)
            & candidates["category"].eq(category)
            & candidates["model_name"].eq(model)
        ].iloc[0]
        selected = errors.loc[
            errors["store_id"].eq(store)
            & errors["category"].eq(category)
            & errors["model_name"].eq(model)
        ]
        event = metric_summary(selected.loc[selected["event_status"].eq("event")])
        ordinary = metric_summary(selected.loc[selected["event_status"].eq("ordinary")])
        event_sufficient = (
            int(event["observations"] or 0) >= config.diagnostics.minimum_subgroup_observations
            and int(ordinary["observations"] or 0)
            >= config.diagnostics.minimum_subgroup_observations
            and event["wape"] is not None
            and ordinary["wape"] is not None
        )
        difference = (
            float(event["wape"] or 0) - float(ordinary["wape"] or 0) if event_sufficient else None
        )
        disagreement = spread.loc[
            spread["store_id"].eq(store) & spread["category"].eq(category), "disagreement"
        ].iloc[0]
        volume = float(candidate["demand_volume"])
        share = volume / normalizer
        raw_bias = candidate["bias"]
        raw_under = candidate["underforecast_rate"]
        row = candidate.to_dict()
        row.update(
            champion_model=champion["champion_model"],
            eligibility_status=champion["eligibility_status"],
            subject="selected_champion" if selected_champion else "unassigned_baseline_review_only",
            classification="retrospective",
            period_start=str(selected["date"].min().date()),
            period_end=str(selected["date"].max().date()),
            disagreement=disagreement,
            volume_component=share,
            shortfall_component=float(candidate["shortfall_units"]) / normalizer,
            absolute_error_component=float(candidate["absolute_error"]) / normalizer,
            bias_component=share * abs(float(raw_bias)) if pd.notna(raw_bias) else 0.0,
            disagreement_component=share * float(disagreement) if pd.notna(disagreement) else 0.0,
            repeat_component=share * float(raw_under) if pd.notna(raw_under) else 0.0,
            priority_status="complete_evidence"
            if candidate["completeness"] == 1
            else "incomplete_evidence",
            event_observations=event["observations"],
            ordinary_observations=ordinary["observations"],
            event_wape=event["wape"],
            ordinary_wape=ordinary["wape"],
            event_wape_difference=difference,
            event_evidence_status="observed_association"
            if event_sufficient
            else "insufficient_evidence",
            ranking_basis=(
                "fixed weighted volume, unit shortfall/error, bias, "
                "disagreement, repeated underforecast"
            ),
        )
        rows.append({str(k): v for k, v in row.items()})
    return (
        pd.DataFrame(rows)
        .sort_values(["store_id", "category", "model_name"])
        .reset_index(drop=True)
    )


def narrate_exceptions(queue: pd.DataFrame, config: CommerceConfig) -> pd.DataFrame:
    """Each narrative names measured evidence, comparison coverage, risk, experiment and owner."""
    result = queue.copy()
    patterns: list[str] = []
    evidence: list[str] = []
    implications: list[str] = []
    experiments: list[str] = []
    for row in queue.to_dict(orient="records"):
        shortfall = float(row["shortfall_units"])
        excess = float(row["excess_units"])
        direction = "underforecast" if shortfall >= excess else "overforecast"
        count = int(row["under_count"] if direction == "underforecast" else row["over_count"])
        no_error = shortfall == 0 and excess == 0 and row["priority_status"] == "complete_evidence"
        patterns.append(
            f"No unit forecast error observed for {row['store_id']}/{row['category']} "
            f"with {row['model_name']} across {int(row['observations'])} valid days; "
            "review cross-model disagreement separately."
            if no_error
            else f"{row['model_name']} {direction} observed on "
            f"{count}/{int(row['observations'])} valid days "
            f"for {row['store_id']}/{row['category']} "
            f"({row['period_start']} to {row['period_end']})."
        )
        comparison = (
            f"Event WAPE {float(row['event_wape']):.4f} "
            f"versus ordinary {float(row['ordinary_wape']):.4f}; "
            f"difference {float(row['event_wape_difference']):+.4f}, an observed association."
            if row["event_evidence_status"] == "observed_association"
            else "Event versus ordinary comparison has insufficient evidence; no event attribution."
        )
        evidence.append(
            f"Actual units {float(row['demand_volume']):.1f}; "
            f"absolute error {float(row['absolute_error']):.1f}; "
            f"signed error {float(row['signed_error']):+.1f}; unit shortfall {shortfall:.1f}; "
            f"excess {excess:.1f}; valid/expected "
            f"{int(row['observations'])}/{int(row['expected_observations'])}. "
            f"Event n={int(row['event_observations'])}, "
            f"ordinary n={int(row['ordinary_observations'])}. "
            f"{comparison} Priority {float(row['priority_score']):.6f}: {row['ranking_basis']}."
        )
        implications.append(
            "Forecast comparison review only; no measured unit-error exposure for this subject."
            if no_error
            else "Possible under-allocation risk; review planning inputs before operational use."
            if direction == "underforecast"
            else "Possible overstaffing risk; review planning inputs before operational use."
        )
        experiments.append(
            "Data Science owner: compare challenger stability on a later untouched window; "
            "this is a proposed experiment, not evidence of a miss."
            if no_error
            else f"Data Science owner: test {row['model_name']} calendar enrichment "
            "on a later untouched window; "
            "Engineering owner: verify event schedules. This is a proposed experiment."
            if row["event_evidence_status"] == "observed_association"
            and row["event_wape_difference"] > 0
            else f"Data Science owner: test {row['model_name']} recalibration "
            "or store-category interactions "
            "on a later untouched window; Engineering owner: audit source completeness. "
            "This is a proposed experiment."
        )
    result["observed_pattern"] = patterns
    result["evidence"] = evidence
    result["operational_implication"] = implications
    result["recommended_experiment"] = experiments
    result["is_top_exception"] = result["priority_rank"].le(config.diagnostics.top_exceptions)
    return result
