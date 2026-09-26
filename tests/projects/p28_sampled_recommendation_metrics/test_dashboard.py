from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.dashboard import (
    SCREENSHOT_ROUTES,
    build_html,
    dashboard_payload,
    load_dashboard_inputs,
)

ROOT = Path(__file__).resolve().parents[3]


def _payload() -> dict:
    return dashboard_payload(load_dashboard_inputs(ROOT))


def _document() -> str:
    return build_html(_payload())


def test_step7_inputs_are_frozen() -> None:
    inputs = load_dashboard_inputs(ROOT)

    assert inputs["release"]["results_frozen"] is True

    assert inputs["contract"]["output_design_frozen"] is True


def test_scientific_contract_preserved() -> None:
    payload = _payload()

    assert payload["full"]["orderings"]["ap"] == "C>B>A"

    assert payload["sampled_m99"]["orderings"]["ap"] == "A>B>C"

    assert payload["full"]["orderings"]["auc"] == "A>C>B"


def test_frozen_sample_grid_preserved() -> None:
    assert _payload()["meta"]["grid"] == [
        1,
        2,
        5,
        10,
        20,
        50,
        99,
        200,
        500,
        1000,
        5000,
        9999,
    ]


def test_self_contained() -> None:
    document = _document()

    lower = document.lower()

    assert "<script src=" not in lower
    assert "<link " not in lower
    assert "<img " not in lower
    assert "background-image:" not in lower


def test_approved_primary_navigation() -> None:
    document = _document()

    assert SCREENSHOT_ROUTES == (
        "overview",
        "ap-reversal",
        "sample-size-sweep",
        "validation",
    )

    for label in (
        "Overview",
        "AP reversal",
        "Sample-size sweep",
        "Validation",
    ):
        assert f'data-contract-tab="{label}"' in document

    assert 'data-route="sensitivity"' not in document

    assert 'data-route="methods-evidence"' not in document


def test_approved_overview_three_panel_contract() -> None:
    document = _document()

    assert 'data-preview-contract="approved-overview-three-panel-v1"' in document

    for panel in (
        'data-overview-panel="ap-reversal"',
        'data-overview-panel="sample-size-sweep"',
        'data-overview-panel="validation"',
    ):
        assert panel in document


def test_overview_kpis_and_insight() -> None:
    document = _document()

    assert document.count('class="kpi ') == 4

    assert 'class="insight-strip"' in document


def test_overview_contains_three_evidence_blocks() -> None:
    document = _document()

    for marker in (
        'id="overview-full-ap"',
        'id="overview-sampled-ap"',
        'id="overview-ap-sweep"',
        'id="overview-validation-body"',
    ):
        assert marker in document


def test_methods_evidence_retained_inside_validation() -> None:
    document = _document()

    assert "Methods &amp; Evidence" in document

    assert 'data-contract-tab="Methods' not in document


def test_preview_prohibition_provenance() -> None:
    payload = _payload()

    provenance = payload["provenance"]

    assert provenance["preview_images_used"] is False

    assert provenance["definition_changes_performed"] is False

    assert provenance["exact_crossover_inference_performed"] is False

    assert provenance["seed_searching_performed"] is False
