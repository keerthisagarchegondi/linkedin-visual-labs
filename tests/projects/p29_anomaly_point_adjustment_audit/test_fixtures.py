from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.fixtures import (
    fixture_from_mapping,
    load_fixtures,
)


def test_fixture_file_has_required_semantic_cases() -> None:
    fixtures = load_fixtures()
    assert len({fixture.fixture_id for fixture in fixtures}) == len(fixtures)
    assert {
        "all_normal",
        "event_first",
        "event_last",
        "two_separated_events",
        "final_timestamp_hit",
        "no_alert",
        "all_anomalous",
    } <= {fixture.fixture_id for fixture in fixtures}


def test_mismatched_prediction_length_fails() -> None:
    with pytest.raises(ValueError, match="same length"):
        fixture_from_mapping(
            {
                "fixture_id": "bad",
                "purpose": "bad",
                "labels": [0, 1],
                "raw_predictions": [0],
                "expected_intervals": [[1, 2]],
            }
        )
