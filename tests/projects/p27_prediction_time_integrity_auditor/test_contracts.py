from __future__ import annotations

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.contracts import (
    EXPECTED_INPUT_COLUMNS,
    blocked_feature_names,
    build_feature_contract,
    deployment_feature_names,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.models import (
    AvailabilityClass,
)


def test_feature_contract_is_complete_and_ordered() -> None:
    records = build_feature_contract()

    assert tuple(record.feature_name for record in records) == EXPECTED_INPUT_COLUMNS

    assert len(records) == 20
    assert len({record.feature_name for record in records}) == 20


def test_duration_is_during_action_and_blocked() -> None:
    by_name = {record.feature_name: record for record in build_feature_contract()}

    duration = by_name["duration"]

    assert duration.availability_class is AvailabilityClass.DURING_ACTION
    assert duration.available_at_prediction is False
    assert duration.deployment_allowed is False


def test_campaign_is_unknown_and_blocked() -> None:
    by_name = {record.feature_name: record for record in build_feature_contract()}

    campaign = by_name["campaign"]

    assert campaign.availability_class is AvailabilityClass.UNKNOWN
    assert campaign.available_at_prediction is False
    assert campaign.deployment_allowed is False


def test_only_frozen_blocked_features_are_excluded() -> None:
    assert blocked_feature_names() == (
        "duration",
        "campaign",
    )

    expected_safe = tuple(
        name for name in EXPECTED_INPUT_COLUMNS if name not in {"duration", "campaign"}
    )

    assert deployment_feature_names() == expected_safe


def test_all_records_have_required_evidence_fields() -> None:
    for record in build_feature_contract():
        payload = record.to_dict()

        assert payload["feature_name"]
        assert payload["business_definition"]
        assert payload["source_column"]
        assert payload["availability_class"]
        assert isinstance(
            payload["available_at_prediction"],
            bool,
        )
        assert isinstance(
            payload["deployment_allowed"],
            bool,
        )
        assert payload["reason"]
        assert payload["owner"]
        assert payload["evidence"]
        assert payload["version"] == "1.0.0"
