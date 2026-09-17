from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.auditor import (
    AuditFinding,
    EvidenceReference,
    approve_public_claim,
    evaluation_stability_audit,
    evidence_reference,
    feature_availability_audit,
    ordered_findings,
    release_decision,
    split_integrity_audit,
    suspicious_feature_audit,
    transformation_boundary_audit,
)

EVIDENCE = EvidenceReference(
    evidence_id="EV_TEST",
    path="assets/test.json",
    description="Test evidence.",
)


def test_finding_requires_evidence() -> None:
    with pytest.raises(
        ValueError,
        match="requires at least one evidence",
    ):
        AuditFinding(
            audit_id="A01",
            audit_family="FEATURE_AVAILABILITY",
            status="PASS",
            severity="INFO",
            affected_pipeline="C",
            summary="safe",
            required_correction="None.",
            evidence=(),
        )


def test_critical_finding_cannot_pass() -> None:
    with pytest.raises(
        ValueError,
        match="Critical violations cannot receive PASS",
    ):
        AuditFinding(
            audit_id="A01",
            audit_family="FEATURE_AVAILABILITY",
            status="PASS",
            severity="CRITICAL",
            affected_pipeline="bad",
            summary="bad",
            required_correction="fix",
            evidence=(EVIDENCE,),
            critical_violation=True,
        )


def test_unknown_availability_blocks() -> None:
    finding = feature_availability_audit(
        ("campaign",),
        {
            "campaign": "UNKNOWN",
        },
        EVIDENCE,
        pipeline="test",
    )

    assert finding.status == "BLOCK"
    assert finding.critical_violation is True


def test_safe_feature_availability_passes() -> None:
    finding = feature_availability_audit(
        (
            "age",
            "job",
        ),
        {
            "age": "PRE_DECISION",
            "job": "PRE_DECISION",
        },
        EVIDENCE,
        pipeline="C",
    )

    assert finding.status == "PASS"


def test_split_overlap_blocks() -> None:
    finding = split_integrity_audit(
        train_validation_overlap=0,
        train_test_overlap=2,
        validation_test_overlap=0,
        chronological_holdout=True,
        evidence=EVIDENCE,
        pipeline="bad",
    )

    assert finding.status == "BLOCK"


def test_non_chronological_split_warns_without_overlap() -> None:
    finding = split_integrity_audit(
        train_validation_overlap=0,
        train_test_overlap=0,
        validation_test_overlap=0,
        chronological_holdout=False,
        evidence=EVIDENCE,
        pipeline="B",
    )

    assert finding.status == "WARN"


def test_safe_split_passes() -> None:
    finding = split_integrity_audit(
        train_validation_overlap=0,
        train_test_overlap=0,
        validation_test_overlap=0,
        chronological_holdout=True,
        evidence=EVIDENCE,
        pipeline="C",
    )

    assert finding.status == "PASS"


def test_contaminated_supervised_transformation_blocks() -> None:
    finding = transformation_boundary_audit(
        fitted_on_training_only=False,
        supervised_transformation=True,
        evidence=EVIDENCE,
        pipeline="bad",
    )

    assert finding.status == "BLOCK"
    assert finding.critical_violation is True


def test_training_only_transformation_passes() -> None:
    finding = transformation_boundary_audit(
        fitted_on_training_only=True,
        supervised_transformation=False,
        evidence=EVIDENCE,
        pipeline="C",
    )

    assert finding.status == "PASS"


def test_duration_is_suspicious_and_blocks() -> None:
    finding = suspicious_feature_audit(
        (
            "age",
            "duration",
        ),
        EVIDENCE,
        pipeline="bad",
    )

    assert finding.status == "BLOCK"


def test_post_outcome_proxy_blocks() -> None:
    finding = suspicious_feature_audit(
        (
            "age",
            "post_outcome_confirmation_proxy",
        ),
        EVIDENCE,
        pipeline="bad",
    )

    assert finding.status == "BLOCK"


def test_safe_features_pass_suspicious_feature_audit() -> None:
    finding = suspicious_feature_audit(
        (
            "age",
            "job",
        ),
        EVIDENCE,
        pipeline="C",
    )

    assert finding.status == "PASS"


def test_temporal_random_reference_blocks_when_measured_block() -> None:
    finding = evaluation_stability_audit(
        uses_chronological_reference=False,
        temporal_result="BLOCK",
        temporal_roc_auc_gap=0.05,
        temporal_pr_auc_gap=0.03,
        evidence=EVIDENCE,
        pipeline="random",
    )

    assert finding.status == "BLOCK"


def test_temporal_random_reference_warns_when_measured_warn() -> None:
    finding = evaluation_stability_audit(
        uses_chronological_reference=False,
        temporal_result="WARN",
        temporal_roc_auc_gap=0.01,
        temporal_pr_auc_gap=0.01,
        evidence=EVIDENCE,
        pipeline="random",
    )

    assert finding.status == "WARN"


def test_chronological_reference_passes_stability() -> None:
    finding = evaluation_stability_audit(
        uses_chronological_reference=True,
        temporal_result="BLOCK",
        temporal_roc_auc_gap=0.05,
        temporal_pr_auc_gap=0.03,
        evidence=EVIDENCE,
        pipeline="C",
    )

    assert finding.status == "PASS"


def test_release_decision_block_warn_pass() -> None:
    block = suspicious_feature_audit(
        ("duration",),
        EVIDENCE,
        pipeline="bad",
    )

    warning = split_integrity_audit(
        train_validation_overlap=0,
        train_test_overlap=0,
        validation_test_overlap=0,
        chronological_holdout=False,
        evidence=EVIDENCE,
        pipeline="B",
    )

    passed = split_integrity_audit(
        train_validation_overlap=0,
        train_test_overlap=0,
        validation_test_overlap=0,
        chronological_holdout=True,
        evidence=EVIDENCE,
        pipeline="C",
    )

    assert release_decision((block,)).status == "BLOCK"

    assert release_decision((warning,)).status == "WARN"

    assert release_decision((passed,)).status == "PASS"


def test_deterministic_ordering() -> None:
    split = split_integrity_audit(
        train_validation_overlap=0,
        train_test_overlap=0,
        validation_test_overlap=0,
        chronological_holdout=True,
        evidence=EVIDENCE,
        pipeline="C",
    )

    features = feature_availability_audit(
        ("age",),
        {
            "age": "PRE_DECISION",
        },
        EVIDENCE,
        pipeline="C",
    )

    ordered = ordered_findings(
        (
            split,
            features,
        )
    )

    assert [finding.audit_family for finding in ordered] == [
        "FEATURE_AVAILABILITY",
        "SPLIT_INTEGRITY",
    ]


def test_public_claim_requires_evidence() -> None:
    assert (
        approve_public_claim(
            claim_id="CLAIM_1",
            evidence=(),
        )
        is False
    )

    assert (
        approve_public_claim(
            claim_id="CLAIM_1",
            evidence=(EVIDENCE,),
        )
        is True
    )

    assert (
        approve_public_claim(
            claim_id="CLAIM_1",
            evidence=(EVIDENCE,),
            preview_only=True,
        )
        is False
    )

    assert (
        approve_public_claim(
            claim_id="CLAIM_1",
            evidence=(EVIDENCE,),
            supported=False,
        )
        is False
    )


def test_evidence_path_required() -> None:
    with pytest.raises(
        ValueError,
        match="Evidence path is required",
    ):
        evidence_reference(
            "EV",
            "",
            "description",
        )
