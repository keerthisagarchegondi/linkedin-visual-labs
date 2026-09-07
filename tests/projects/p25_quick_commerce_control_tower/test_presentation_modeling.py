"""Modeling transparency, evidence sensitivity and constructive, honest presentation."""

from __future__ import annotations

import copy

import pytest

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_decisions as decisions,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_modeling as modeling,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_charts import (
    chart_specs,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    Evidence,
    validate_story,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_html import (
    report_html,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    storyboards,
)

from .test_presentation import evidence as evidence
from .test_presentation import png_bytes


@pytest.mark.parametrize(
    "term",
    [
        "Target / dependent variable",
        "date \u00d7 store \u00d7 category",
        "Features / independent variables",
        "lag 28, lag 35, lag 42, lag 49 and lag 56",
        "7-day and 14-day",
        "t\u221228",
        "state-specific SNAP",
        "Data preparation",
        "ordered d_N",
        "duplicate-grain",
        "rejected, not imputed",
        "Empty event labels",
        "DuckDB",
        "checksum",
        "deterministic caching",
        "all 560 holdout",
        "Raw demand → aggregate",
        "training data only",
        "no scaling",
        "no feature\nstandardization",
        "numeric inputs pass through",
        "dense one-hot",
        "StandardScaler",
        "target is also standardized",
        "128, 64, 32",
        "Level 1",
        "MAE",
        "Level 2",
        "absolute\nbias ≤ 10%",
        "deterministic validation",
        "lowest WAPE",
        "untouched period",
    ],
)
def test_modeling_transparency_is_in_arena(evidence: Evidence, term: str) -> None:
    doc = report_html(evidence, png_bytes(evidence))
    arena = doc.split('id="panel-arena"')[1].split('id="panel-champion"')[0]
    assert term in arena
    assert '<details class="modeling-transparency">' in arena


def test_importance_uses_measured_ranking_signed_values_and_uncertainty(evidence: Evidence) -> None:
    spec = chart_specs(evidence)["hgb_importance"]
    trace = spec["data"][0]
    assert trace["x"] == ["weekday", "lag_28", "lag_35"]
    assert trace["y"] == [8.0, 4.0, -0.5]
    assert trace["error_y"]["array"] == [0.25] * 3
    assert "weekday ranks first" in spec["meaning"]
    assert "not causality" in spec["meaning"] and "not held-out importance" in spec["meaning"]
    assert "Retrospective model interpretation" in spec["title"]
    evidence.tables["hist_gradient_boosting_importance"][0]["mean_mae_increase"] = 12.5
    changed = chart_specs(evidence)["hgb_importance"]
    assert changed["data"][0]["x"][0] == "lag_28"
    assert changed["data"][0]["y"][0] == 12.5
    assert "lag_28 ranks first" in changed["meaning"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_rows", 560),
        ("repeats", 1),
        ("classification", "holdout"),
        ("sample_policy", "random"),
    ],
)
def test_importance_rejects_changed_interpretation_scope(
    evidence: Evidence,
    field: str,
    value: str | int,
) -> None:
    evidence.tables["hist_gradient_boosting_importance"][0][field] = value
    with pytest.raises(ValueError, match="provenance"):
        modeling.importance_rows(evidence)


def test_diagnostics_form_an_action_backlog(evidence: Evidence) -> None:
    doc = report_html(evidence, png_bytes(evidence))
    assert "Why diagnose forecast error?" in doc and "action backlog" in doc
    assert "Forecast error → prioritize → investigate → form hypothesis" in doc
    assert "test experiment → recalibrate/retrain" in doc
    for store in ("WI_2", "CA_1", "TX_3"):
        assert store + " / FOODS" in decisions.diagnostic_actions(evidence)


def test_validation_discloses_success_limitation_and_calibration(evidence: Evidence) -> None:
    text = decisions.impact(evidence)
    for term in (
        "YES — constraint performance",
        "YES — capacity redistribution",
        "2 → 1",
        "NOT YET",
        "70.00 → 80.00",
        "worsened",
        "functioning as designed",
        "calibration",
        "not a causal",
    ):
        assert term in text
    changed = copy.deepcopy(evidence)
    changed.tables["scenario_summary"][0]["feasibility"] = "infeasible"
    with pytest.raises(ValueError, match="Constraint success"):
        validate_story(changed)


def test_governance_integrated_once_and_production_inputs_complete(evidence: Evidence) -> None:
    doc = report_html(evidence, png_bytes(evidence))
    governance = doc.split('id="panel-governance"')[1].split("<script")[0]
    assert governance.count('class="overview-grid operating-system"') == 1
    for label in ("MONITOR", "REVIEW", "EXPERIMENT", "DEPLOY / ESCALATE"):
        assert governance.count("<h3>" + label + "</h3>") == 1
    assert "Level 1" not in governance
    assert "end-to-end forecasting operating loop" in governance
    for term in (
        "service importance",
        "SLA cost",
        "productivity variation",
        "shift structure",
        "local staffing rules",
        "Labor availability",
        "service-level targets",
        "event-specific",
        "Inventory availability",
        "replenishment timing",
        "Forecast uncertainty",
        "operational economics",
    ):
        assert term in modeling.production_inputs(optimizer=True)


def test_videos_learn_without_hiding_negative_evidence(evidence: Evidence) -> None:
    boards = storyboards(evidence)
    arena, labor = boards.values()
    assert "Different stores favor different approaches" in arena[3].title
    assert "No model qualified everywhere" in arena[3].caption
    assert "no eligible champion" in arena[4].caption
    assert arena[-1].caption == "Review the exceptions. Improve the features. Re-test."
    assert "70.00 → 80.00" in str(labor[3].items)
    assert "2 → 1" in str(labor[3].items)
    assert "coverage worsened under equal priorities" in labor[4].caption
    assert "richer business inputs" in labor[4].caption
    assert "inventory / replenishment" in labor[5].caption
    for scenes in boards.values():
        assert sum(s.seconds for s in scenes) == 30
        assert all("failed" not in (s.caption + s.title).lower() for s in scenes)
