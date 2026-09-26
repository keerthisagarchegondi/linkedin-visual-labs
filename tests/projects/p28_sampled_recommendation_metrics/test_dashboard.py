from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.dashboard import (
    build_html,
    dashboard_payload,
    load_dashboard_inputs,
)

ROOT = Path(__file__).resolve().parents[3]


def _payload() -> dict:
    return dashboard_payload(load_dashboard_inputs(ROOT))


def test_step7_inputs_are_frozen() -> None:
    inputs = load_dashboard_inputs(ROOT)

    assert inputs["release"]["results_frozen"] is True

    assert inputs["contract"]["status"] == "FROZEN"

    assert inputs["contract"]["output_design_frozen"] is True

    assert inputs["figure_manifest"]["status"] == "PASS"


def test_dashboard_preserves_central_scientific_result() -> None:
    payload = _payload()

    assert payload["full"]["orderings"]["ap"] == "C>B>A"

    assert payload["sampled_m99"]["orderings"]["ap"] == "A>B>C"

    assert payload["full"]["orderings"]["auc"] == "A>C>B"


def test_dashboard_uses_frozen_sample_grid() -> None:
    payload = _payload()

    assert payload["meta"]["grid"] == [
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


def test_dashboard_is_self_contained() -> None:
    document = build_html(_payload())

    lower = document.lower()

    assert "<script src=" not in lower
    assert "<link " not in lower
    assert "<img " not in lower
    assert "background-image:" not in lower

    assert 'id="frozen-data"' in document

    assert "window.__P28_DASHBOARD_READY__ = true" in document


def test_dashboard_has_frozen_sections() -> None:
    document = build_html(_payload())

    for label in (
        "Overview",
        "Sensitivity",
        "Validation",
        "Methods &amp; Evidence",
    ):
        assert label in document


def test_dashboard_has_preview_prohibition_provenance() -> None:
    payload = _payload()

    assert payload["provenance"]["preview_images_used"] is False

    assert payload["provenance"]["definition_changes_performed"] is False

    assert payload["provenance"]["exact_crossover_inference_performed"] is False

    assert payload["provenance"]["seed_searching_performed"] is False
