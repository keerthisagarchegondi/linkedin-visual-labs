"""Synthetic contract oracles; no source processing or runtime decisions."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning import models as m


def evidence() -> dict[str, object]:
    return {
        "evidence_id": "synthetic-review",
        "path": f"{m.OUTPUT}/manifests/fixture.json",
        "sha256": "a" * 64,
        "review": "APPROVED",
    }


def approved_candidate() -> dict[str, Any]:
    """Authored synthetic metadata; no real approval or media bytes."""
    return {
        "source_id": "fixture",
        "source_name": "Synthetic metadata only",
        "owner": "Fixture owner",
        "acquisition_method": "Fixture",
        "license_or_ownership_basis": "Synthetic ownership",
        "private_evidence": evidence(),
        "permitted_use": dict.fromkeys(
            ("analysis", "derivatives", "excerpts", "image", "video", "report"), "YES"
        ),
        "attribution_requirement": "Synthetic attribution",
        "raw_file_path": f"{m.RAW}/fixture.mp4",
        "checksum_sha256": "b" * 64,
        "duration_seconds": 1800.0,
        "width": 640,
        "height": 480,
        "codec": "fixture",
        "average_frame_rate": 30.0,
        "variable_frame_rate": "NO",
        "timestamp_characteristics": "Synthetic PTS declaration",
        "timing_review": "APPROVED",
        "camera_continuity": "APPROVED",
        "scene_cuts": "NO",
        "camera_motion": "NO",
        "episode_review": "APPROVED",
        "quality_review": "APPROVED",
        "privacy_treatment": "Synthetic aggregate-only treatment",
        "privacy_review": "APPROVED",
        "status": "SOURCE_APPROVED",
        "reviewer_decision": "APPROVED",
        "evidence": [evidence()],
    }


def frozen_queue() -> dict[str, Any]:
    return {
        "status": "FROZEN",
        "cadence_seconds": 1.0,
        "composition": "ALL",
        "persistence": {"mode": "CONSECUTIVE_WINDOWS", "window_count": 2},
        "unavailable_data": "BLOCK_EVALUATION",
        "review_evidence": evidence(),
        "predicates": [
            {
                "signal": "QUEUE_COUNT",
                "unit": "VEHICLES",
                "comparator": "GE",
                "threshold": 2.0,
                "rationale": "Synthetic test threshold only",
                "evidence": evidence(),
            }
        ],
    }


def test_enum_vocabularies_and_result_declarations() -> None:
    assert {x.value for x in m.SourceStatus} == {
        "SOURCE_PENDING",
        "SOURCE_APPROVED",
        "SOURCE_REVIEW_REQUIRED",
        "SOURCE_REJECTED_LICENSE",
        "SOURCE_REJECTED_DURATION",
        "SOURCE_REJECTED_CAMERA",
        "SOURCE_REJECTED_EPISODE",
        "SOURCE_REJECTED_QUALITY",
    }
    assert len(m.ResultClassification) == 8
    assert len(m.ClaimClassification) == 6
    assert len(m.ActionType) == 6
    assert tuple(x.value for x in m.WarningState) == ("NORMAL", "WATCH", "WARNING", "CRITICAL")
    result = m.ResultContract()
    assert result.positive == "POSITIVE_EARLY_WARNING"
    assert result.zero == "WARNING_AT_VISIBLE_ONSET"
    assert result.negative == "LATE_WARNING"
    assert result.formula == "visible_queue_timestamp - warning_timestamp"
    assert result.missing_onset_lead_time is None and result.clamp_negative is False
    assert result.precedence[0] == "INSUFFICIENT_SOURCE_EPISODE"
    with pytest.raises(ValidationError):
        m.ResultContract.model_validate({"precedence": list(reversed(result.precedence))})


def test_candidate_complete_synthetic_approval_and_no_maximum() -> None:
    payload = approved_candidate()
    assert m.SourceCandidate.model_validate(payload).status == m.SourceStatus.SOURCE_APPROVED
    payload["duration_seconds"] = 3600.0
    assert m.SourceCandidate.model_validate(payload).duration_seconds == 3600


@pytest.mark.parametrize(
    "field",
    [
        "owner",
        "license_or_ownership_basis",
        "private_evidence",
        "attribution_requirement",
        "raw_file_path",
        "checksum_sha256",
        "duration_seconds",
        "width",
        "height",
        "codec",
        "timestamp_characteristics",
        "privacy_treatment",
    ],
)
def test_approval_requires_complete_metadata(field: str) -> None:
    payload = approved_candidate()
    payload[field] = None
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)


@pytest.mark.parametrize(
    "field",
    [
        "timing_review",
        "camera_continuity",
        "episode_review",
        "quality_review",
        "privacy_review",
        "reviewer_decision",
    ],
)
def test_unknown_review_never_approves(field: str) -> None:
    payload = approved_candidate()
    payload[field] = "UNKNOWN"
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)


@pytest.mark.parametrize(
    "right", ["analysis", "derivatives", "excerpts", "image", "video", "report"]
)
def test_every_required_right(right: str) -> None:
    payload = approved_candidate()
    payload["permitted_use"][right] = "UNKNOWN"
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("duration_seconds", 0),
        ("duration_seconds", -1),
        ("duration_seconds", True),
        ("duration_seconds", float("nan")),
        ("duration_seconds", float("inf")),
        ("duration_seconds", "1800"),
        ("average_frame_rate", 0),
        ("average_frame_rate", -1),
        ("average_frame_rate", True),
        ("average_frame_rate", float("inf")),
        ("width", 0),
        ("height", -1),
        ("width", True),
        ("height", 1.2),
        ("status", "APPROVED"),
    ],
)
def test_source_strictness(field: str, value: object) -> None:
    payload = approved_candidate()
    payload[field] = value
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)


def test_source_review_states_duration_and_location() -> None:
    assert m.SourceConfig().candidate is None
    with pytest.raises(ValidationError):
        m.SourceConfig(status=m.SourceStatus.SOURCE_PENDING)
    payload = approved_candidate()
    payload["duration_seconds"] = 720.0
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)
    payload["short_episode_justification"] = "Synthetic complete episode"
    assert m.SourceCandidate.model_validate(payload).duration_seconds == 720
    payload["duration_seconds"] = 719.0
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)
    payload["status"] = "SOURCE_REVIEW_REQUIRED"
    assert m.SourceCandidate.model_validate(payload).duration_seconds == 719
    payload["location_wording"] = "A specific location"
    with pytest.raises(ValidationError):
        m.SourceCandidate.model_validate(payload)


@pytest.mark.parametrize(
    "path",
    [
        "../escape.mp4",
        "/tmp/foreign.mp4",
        "D:/linkedin-visual-labs/x",
        "Z:/foreign/file",
        "//server/share/file",
        f"{m.RAW}/../../other/file",
        "data/raw/p02_monopoly_ai/source.mp4",
        f"{m.RAW}/..\\file",
    ],
)
def test_source_path_rejection(path: str) -> None:
    with pytest.raises(ValidationError):
        m.SourceCandidate(source_id="fixture", source_name="fixture", raw_file_path=path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("throughput_window_seconds", 0),
        ("throughput_window_seconds", 301),
        ("imbalance_window_seconds", 299),
        ("minimum_completed_samples", 0),
        ("minimum_completed_samples", True),
        ("minimum_coverage", 1.1),
        ("percentile_range", [90, 10]),
        ("percentile_range", [10, 101]),
        ("low_motion_threshold", float("nan")),
        ("low_motion_duration_seconds", -1),
    ],
)
def test_metric_invalid_variants(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        m.MetricsConfig.model_validate({field: value})


def test_metric_semantics_and_frozen_completeness() -> None:
    config = m.MetricsConfig(percentile_range=(10.0, 90.0), minimum_completed_samples=3)
    assert config.throughput_window_seconds == config.imbalance_window_seconds == 300
    assert config.dwell == "COMPLETED_EXIT_ASSIGNED_ORIGINAL_SECONDS"
    assert config.missing_samples == "UNAVAILABLE"
    assert config.missing_evaluation == "BREAK_PERSISTENCE"
    assert config.zero_baseline_delta == "UNAVAILABLE"
    with pytest.raises(ValidationError):
        m.MetricsConfig(review=m.RuleStatus.FROZEN)


@pytest.mark.parametrize(
    "field",
    ["cadence_seconds", "composition", "persistence", "unavailable_data", "review_evidence"],
)
def test_frozen_rule_requires_complete_evidence(field: str) -> None:
    payload = frozen_queue()
    payload[field] = None
    with pytest.raises(ValidationError):
        m.QueueOutcomeConfig.model_validate(payload)


def test_rule_status_duplicates_and_disjoint_signals() -> None:
    assert not m.QueueOutcomeConfig().executable
    assert not m.WarningConfig().executable
    payload = frozen_queue()
    assert m.QueueOutcomeConfig.model_validate(payload).executable
    with pytest.raises(ValidationError):
        m.WarningConfig.model_validate(payload)
    payload["predicates"] *= 2
    for order in (payload["predicates"], list(reversed(payload["predicates"]))):
        with pytest.raises(ValidationError):
            m.QueueOutcomeConfig.model_validate({**payload, "predicates": order})


@pytest.mark.parametrize("signal", ["QUEUE_COUNT", "QUEUE_OUTCOME", "queue_count", "density"])
def test_warning_signal_alias_and_outcome_rejection(signal: str) -> None:
    with pytest.raises(ValidationError):
        m.WarningPredicate.model_validate(
            {"signal": signal, "unit": "VEHICLES", "comparator": "GE"}
        )


def test_warning_freeze_requires_rationale_transitions_and_provenance() -> None:
    payload = frozen_queue()
    payload["predicates"][0]["signal"] = "DENSITY_LEVEL"
    with pytest.raises(ValidationError):
        m.WarningConfig.model_validate(payload)
    payload["leading_rationale"] = "Synthetic leading deterioration rationale"
    payload["transitions"] = {
        "reset_persistence": {"mode": "DURATION", "duration_seconds": 2.0},
        "hysteresis": 1.0,
    }
    assert m.WarningConfig.model_validate(payload).executable
    payload["predicates"][0]["evidence"] = None
    with pytest.raises(ValidationError):
        m.WarningConfig.model_validate(payload)
    with pytest.raises(ValidationError):
        m.WarningConfig.model_validate({"depends_on_queue_outcome": True})


@pytest.mark.parametrize("unit", ["MPH", "FEET", "METERS", "VEHICLES_PER_LANE_MILE"])
def test_physical_units_need_calibration(unit: str) -> None:
    with pytest.raises(ValidationError):
        m.CalibrationConfig.model_validate({"units": [unit]})
    with pytest.raises(ValidationError):
        m.CalibrationConfig.model_validate({"status": "PHYSICAL_CALIBRATED", "units": [unit]})
    calibrated = {
        "status": "PHYSICAL_CALIBRATED",
        "units": [unit],
        "source_id": "fixture",
        "geometry_id": "fixture-geometry",
        "method": "synthetic",
        "evidence": evidence(),
    }
    assert (
        m.CalibrationConfig.model_validate(calibrated).status
        == m.CalibrationStatus.PHYSICAL_CALIBRATED
    )


@pytest.mark.parametrize("availability", ["DISABLED", "UNSUPPORTED"])
def test_unavailable_action_not_eligible(availability: str) -> None:
    with pytest.raises(ValidationError):
        m.ActionConfig.model_validate(
            {
                "action": "OPEN_OVERFLOW_CAPACITY",
                "availability": availability,
                "eligible": True,
                "conditional_wording": "Consider opening overflow capacity",
                "context_evidence": evidence(),
            }
        )


def test_enabled_action_and_no_action() -> None:
    assert m.RecommendationsConfig().no_enabled_action == "NO_ACTION_WITH_REASON"
    with pytest.raises(ValidationError):
        m.ActionConfig(action=m.ActionType.MONITOR, availability=m.Availability.ENABLED)
    assert m.ActionConfig(
        action=m.ActionType.MONITOR,
        availability=m.Availability.ENABLED,
        eligible=True,
        conditional_wording="Consider monitoring",
        context_evidence=m.EvidenceReference.model_validate(evidence()),
    ).eligible


def claim() -> dict[str, Any]:
    return {
        "claim_id": "synthetic",
        "claim_text": "Synthetic configured assumption",
        "classification": "CONFIGURED_ASSUMPTION",
        "evidence": [evidence()],
        "calculation": "Synthetic policy",
        "caveat": "Synthetic, not real evidence",
        "reviewer_status": "APPROVED",
        "approved_for_publication": True,
        "last_validated_step": 1,
        "approved_evidence_hashes": ["a" * 64],
    }


@pytest.mark.parametrize("classification", ["PREVIEW_ONLY", "UNSUPPORTED"])
def test_preview_and_unsupported_never_publish(classification: str) -> None:
    with pytest.raises(ValidationError):
        m.ClaimRecord.model_validate({**claim(), "classification": classification})


@pytest.mark.parametrize(
    "field",
    [
        "evidence",
        "calculation",
        "caveat",
        "reviewer_status",
        "last_validated_step",
        "approved_evidence_hashes",
    ],
)
def test_publication_requires_evidence_review_and_caveat(field: str) -> None:
    payload = claim()
    del payload[field]
    with pytest.raises(ValidationError):
        m.ClaimRecord.model_validate(payload)


def test_claim_hash_binding_and_planned_evidence() -> None:
    assert m.ClaimRecord.model_validate(claim()).approved_for_publication
    payload = deepcopy(claim())
    payload["evidence"][0]["sha256"] = "b" * 64
    with pytest.raises(ValidationError):
        m.ClaimRecord.model_validate(payload)
    payload["evidence"][0]["review"] = "REVIEW_REQUIRED"
    with pytest.raises(ValidationError):
        m.ClaimRecord.model_validate(payload)


@pytest.mark.parametrize(
    "field",
    [
        "face_recognition",
        "facial_identity",
        "plate_ocr",
        "driver_identity",
        "persistent_vehicle_identity",
        "cross_camera_identity",
        "external_vehicle_lookup",
        "enforcement_citations",
    ],
)
def test_privacy_cannot_enable_prohibited_features(field: str) -> None:
    with pytest.raises(ValidationError):
        m.PrivacyConfig.model_validate({field: True})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("width", 1920),
        ("height", 1080),
        ("width", True),
        ("fps", 0),
        ("fps", 60),
        ("aspect", "16:9"),
        ("duration_seconds", 43.9),
        ("duration_seconds", 46.6),
        ("frame_count", 1319),
        ("frame_count", 1396),
        ("frame_count", True),
        ("keyframe_seconds", [5, 0, 10]),
        ("closing_selector", "45_SECONDS"),
    ],
)
def test_invalid_video_contract(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        m.VideoOutput.model_validate({field: value})


@pytest.mark.parametrize(("duration", "frames"), [(44.0, 1320), (45.0, 1350), (46.5, 1395)])
def test_frame_bounds_and_closing_selector(duration: float, frames: int) -> None:
    model = m.VideoOutput(duration_seconds=duration, frame_count=frames)
    assert model.closing_selector == "LAST_FRAME"
    assert model.closing_time_formula == "(frame_count - 1) / 30"
    assert (frames - 1) / model.fps < duration


def test_static_interval_tabs_and_original_time() -> None:
    assert (m.StaticOutput().width, m.StaticOutput().height) == (1080, 1350)
    with pytest.raises(ValidationError):
        m.StaticOutput(width=1350)
    with pytest.raises(ValidationError):
        m.SourceInterval(start_seconds=0, end_seconds=599)
    assert m.SourceInterval(start_seconds=30, end_seconds=630).end_seconds == 630
    with pytest.raises(ValidationError):
        m.OutputConfig(report_tabs=("Dashboard", "Video", "Method", "About", "Results"))
    with pytest.raises(ValidationError):
        m.AnalysisConfig.model_validate({"clock": "PLAYBACK_TIME"})
    with pytest.raises(ValidationError):
        m.AnalysisConfig.model_validate({"sampling_rescales_time": True})
