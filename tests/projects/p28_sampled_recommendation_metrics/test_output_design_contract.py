from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DOCS = ROOT / "docs" / "projects" / "p28_sampled_recommendation_metrics"

FROZEN = ROOT / "assets" / "p28_sampled_recommendation_metrics" / "frozen"


def _contract() -> dict[str, object]:
    return json.loads((DOCS / "OUTPUT_DESIGN_CONTRACT.json").read_text(encoding="utf-8"))


def _release() -> dict[str, object]:
    return json.loads((FROZEN / "release_data.json").read_text(encoding="utf-8"))


def test_step5_is_user_approved_and_frozen() -> None:
    contract = _contract()

    assert contract["status"] == "FROZEN"

    assert contract["results_frozen"] is True

    assert contract["output_design_frozen"] is True

    approval = contract["approval"]

    assert isinstance(
        approval,
        dict,
    )

    assert approval["required"] is True

    assert approval["approved"] is True


def test_primary_ap_orderings_come_from_release_data() -> None:
    contract = _contract()
    release = _release()

    evidence = contract["evidence_summary"]

    assert isinstance(
        evidence,
        dict,
    )

    full = release["full_catalog"]

    sampled = release["sampled_m99"]

    assert isinstance(
        full,
        dict,
    )

    assert isinstance(
        sampled,
        dict,
    )

    full_orderings = full["orderings"]

    sampled_orderings = sampled["orderings"]

    assert isinstance(
        full_orderings,
        dict,
    )

    assert isinstance(
        sampled_orderings,
        dict,
    )

    assert evidence["full_ap_ordering"] == full_orderings["ap"]["text"]

    assert evidence["sampled_ap_ordering_m99"] == sampled_orderings["ap"]["text"]


def test_static_figure_count_is_three() -> None:
    contract = _contract()

    figures = contract["static_figures"]

    assert isinstance(
        figures,
        dict,
    )

    assert figures["count"] == 3

    assert set(key for key in figures if key.startswith("figure_")) == {
        "figure_1",
        "figure_2",
        "figure_3",
    }


def test_dashboard_uses_frozen_m_only() -> None:
    contract = _contract()

    dashboard = contract["dashboard"]

    assert isinstance(
        dashboard,
        dict,
    )

    allowed = dashboard["allowed_interactivity"]

    prohibited = dashboard["prohibited_interactivity"]

    assert "selection among frozen m values only" in allowed

    assert "arbitrary user-entered m" in prohibited

    assert "interpolation between m values" in prohibited


def test_video_contract() -> None:
    contract = _contract()

    video = contract["video"]

    assert isinstance(
        video,
        dict,
    )

    assert video["target_duration_seconds"] == 45

    assert video["scene_count"] == 6

    assert video["aspect_ratio"] == "16:9"

    assert video["resolution"] == "1920x1080"

    assert video["frame_rate_fps"] == 30

    storyboard = video["storyboard"]

    assert isinstance(
        storyboard,
        list,
    )

    assert len(storyboard) == 6


def test_required_public_limitation_exists() -> None:
    contract = _contract()

    limitations = contract["limitations"]

    assert isinstance(
        limitations,
        dict,
    )

    text = limitations["required_public_language"]

    assert isinstance(
        text,
        str,
    )

    assert "toy example" in text

    assert "does not estimate" in text

    assert "production recommender systems" in text


def test_auc_is_explicit_negative_control() -> None:
    contract = _contract()

    metrics = contract["metric_emphasis"]

    assert isinstance(
        metrics,
        dict,
    )

    assert metrics["negative_control_metric"] == "AUC"


def test_exact_crossover_claim_is_prohibited() -> None:
    contract = _contract()

    terminology = contract["terminology"]

    assert isinstance(
        terminology,
        dict,
    )

    avoid = terminology["prohibited_or_avoid"]

    assert "exact crossover threshold" in avoid


def test_attribution_names_krichene_and_rendle() -> None:
    contract = _contract()

    attribution = contract["attribution"]

    assert isinstance(
        attribution,
        dict,
    )

    language = attribution["required_language"]

    assert "Krichene & Rendle" in language
