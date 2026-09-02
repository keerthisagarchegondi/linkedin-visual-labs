"""Project 4 frozen-contract tests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROJECT_ID = "p25_retail_media_audience_decision"


def load_contract() -> dict[str, object]:
    """Load the frozen Project 4 contract."""

    path = ROOT / "assets" / PROJECT_ID / "project_contract.json"

    value = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert isinstance(
        value,
        dict,
    )

    return value


def test_project_contract_identity_and_visual_reference() -> None:
    """Project identity and visual reference must not drift."""

    contract = load_contract()

    assert contract["project_number"] == 4
    assert contract["project_id"] == PROJECT_ID
    assert contract["project_name"] == "Retail Media Audience Decision Studio"
    assert contract["cli_namespace"] == "retail-media"
    assert contract["feature_branch"] == "project/p25-retail-media-audience-decision"

    reference = contract["visual_reference"]

    assert isinstance(
        reference,
        dict,
    )

    assert reference["width_px"] == 1536
    assert reference["height_px"] == 1024
    assert reference["sha256"] == "abe93962fc863ec9d21ef3574d7152b7759718b21c30e27cd160136dfb2360e3"


def test_evidence_classes_are_separate() -> None:
    """Four public evidence classes may not become one fake graph."""

    contract = load_contract()

    policy = contract["evidence_policy"]

    assert isinstance(
        policy,
        dict,
    )

    assert policy["cross_dataset_customer_identity_join_allowed"] is False
    assert policy["fabricated_cross_dataset_identity_allowed"] is False
    assert policy["attribution_is_not_incrementality"] is True

    sources = contract["sources"]

    assert isinstance(
        sources,
        list,
    )

    source_ids = {
        source["source_id"]
        for source in sources
        if isinstance(
            source,
            dict,
        )
    }

    assert source_ids == {
        "dunnhumby_complete_journey",
        "hillstrom",
        "criteo_attribution",
        "retailrocket",
        "synthetic_attribution_fixture",
    }


def test_mock_dashboard_semantics_cannot_be_hard_coded() -> None:
    """Mock art direction cannot authorize unsupported claims."""

    contract = load_contract()

    semantics = contract["metric_semantics"]

    assert isinstance(
        semantics,
        dict,
    )

    assert semantics["literal_ad_spend_supported"] is False
    assert semantics["literal_roas_supported"] is False
    assert semantics["criteo_cost_label"] == "Media Cost Index"
