"""Evidence-linked prediction-time integrity auditor."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal

from .contracts import (
    blocked_feature_names,
    build_feature_contract,
)
from .models import AvailabilityClass

AuditStatus = Literal["PASS", "WARN", "BLOCK"]
Severity = Literal["INFO", "MEDIUM", "HIGH", "CRITICAL"]

AUDIT_ORDER: Final[tuple[str, ...]] = (
    "FEATURE_AVAILABILITY",
    "SPLIT_INTEGRITY",
    "TRANSFORMATION_BOUNDARY",
    "SUSPICIOUS_FEATURE",
    "EVALUATION_STABILITY",
)

STATUS_RANK: Final[dict[str, int]] = {
    "PASS": 0,
    "WARN": 1,
    "BLOCK": 2,
}


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    """One machine-readable evidence pointer."""

    evidence_id: str
    path: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AuditFinding:
    """One deterministic auditor finding."""

    audit_id: str
    audit_family: str
    status: AuditStatus
    severity: Severity
    affected_pipeline: str
    summary: str
    required_correction: str
    evidence: tuple[EvidenceReference, ...]
    critical_violation: bool = False

    def __post_init__(self) -> None:
        if not self.evidence:
            raise ValueError("Every audit finding requires at least one evidence reference.")

        if self.critical_violation and self.status == "PASS":
            raise ValueError("Critical violations cannot receive PASS.")

        if self.audit_family not in AUDIT_ORDER:
            raise ValueError(f"Unknown audit family: {self.audit_family}")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        return payload


@dataclass(frozen=True, slots=True)
class ReleaseDecision:
    """Release recommendation derived from findings."""

    status: AuditStatus
    recommendation: str
    blocking_finding_ids: tuple[str, ...]
    warning_finding_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evidence_reference(
    evidence_id: str,
    path: str,
    description: str,
) -> EvidenceReference:
    """Validate and create one evidence reference."""

    if not evidence_id.strip():
        raise ValueError("evidence_id is required.")

    if not path.strip():
        raise ValueError("Evidence path is required.")

    if not description.strip():
        raise ValueError("Evidence description is required.")

    return EvidenceReference(
        evidence_id=evidence_id,
        path=path,
        description=description,
    )


def feature_availability_audit(
    feature_names: tuple[str, ...],
    availability_by_feature: dict[str, str],
    evidence: EvidenceReference,
    *,
    pipeline: str,
) -> AuditFinding:
    """Audit whether every scoring feature is available at prediction time."""

    unknown = tuple(
        sorted(
            feature
            for feature in feature_names
            if availability_by_feature.get(feature)
            in {
                None,
                AvailabilityClass.UNKNOWN.value,
            }
        )
    )

    blocked = tuple(
        sorted(
            feature
            for feature in feature_names
            if availability_by_feature.get(feature)
            in {
                AvailabilityClass.DURING_ACTION.value,
                AvailabilityClass.POST_OUTCOME.value,
            }
        )
    )

    if unknown:
        return AuditFinding(
            audit_id="A01_FEATURE_AVAILABILITY",
            audit_family="FEATURE_AVAILABILITY",
            status="BLOCK",
            severity="CRITICAL",
            affected_pipeline=pipeline,
            summary=("Unknown feature availability blocks release: " + ", ".join(unknown)),
            required_correction=(
                "Document exact production-time semantics or remove unknown-availability features."
            ),
            evidence=(evidence,),
            critical_violation=True,
        )

    if blocked:
        return AuditFinding(
            audit_id="A01_FEATURE_AVAILABILITY",
            audit_family="FEATURE_AVAILABILITY",
            status="BLOCK",
            severity="CRITICAL",
            affected_pipeline=pipeline,
            summary=("Features unavailable at prediction time: " + ", ".join(blocked)),
            required_correction=("Remove DURING_ACTION and POST_OUTCOME features."),
            evidence=(evidence,),
            critical_violation=True,
        )

    return AuditFinding(
        audit_id="A01_FEATURE_AVAILABILITY",
        audit_family="FEATURE_AVAILABILITY",
        status="PASS",
        severity="INFO",
        affected_pipeline=pipeline,
        summary=("All scoring features have prediction-time-safe availability."),
        required_correction="None.",
        evidence=(evidence,),
    )


def split_integrity_audit(
    *,
    train_validation_overlap: int,
    train_test_overlap: int,
    validation_test_overlap: int,
    chronological_holdout: bool,
    evidence: EvidenceReference,
    pipeline: str,
) -> AuditFinding:
    """Audit split overlap and prospective ordering."""

    total_overlap = train_validation_overlap + train_test_overlap + validation_test_overlap

    if total_overlap > 0:
        return AuditFinding(
            audit_id="A02_SPLIT_INTEGRITY",
            audit_family="SPLIT_INTEGRITY",
            status="BLOCK",
            severity="CRITICAL",
            affected_pipeline=pipeline,
            summary=(f"Prohibited cross-partition overlap detected: {total_overlap}."),
            required_correction=("Rebuild partitions with zero prohibited row overlap."),
            evidence=(evidence,),
            critical_violation=True,
        )

    if not chronological_holdout:
        return AuditFinding(
            audit_id="A02_SPLIT_INTEGRITY",
            audit_family="SPLIT_INTEGRITY",
            status="WARN",
            severity="HIGH",
            affected_pipeline=pipeline,
            summary=("No overlap detected, but evaluation is not chronological."),
            required_correction=("Use chronological source-order holdout for deployability."),
            evidence=(evidence,),
        )

    return AuditFinding(
        audit_id="A02_SPLIT_INTEGRITY",
        audit_family="SPLIT_INTEGRITY",
        status="PASS",
        severity="INFO",
        affected_pipeline=pipeline,
        summary=("Chronological holdout has zero prohibited row overlap."),
        required_correction="None.",
        evidence=(evidence,),
    )


def transformation_boundary_audit(
    *,
    fitted_on_training_only: bool,
    supervised_transformation: bool,
    evidence: EvidenceReference,
    pipeline: str,
) -> AuditFinding:
    """Audit transformation fitting boundaries."""

    if supervised_transformation and not fitted_on_training_only:
        return AuditFinding(
            audit_id="A03_TRANSFORMATION_BOUNDARY",
            audit_family="TRANSFORMATION_BOUNDARY",
            status="BLOCK",
            severity="CRITICAL",
            affected_pipeline=pipeline,
            summary=("Supervised transformation used non-training targets."),
            required_correction=(
                "Split first and fit supervised transformations using training data only."
            ),
            evidence=(evidence,),
            critical_violation=True,
        )

    if not fitted_on_training_only:
        return AuditFinding(
            audit_id="A03_TRANSFORMATION_BOUNDARY",
            audit_family="TRANSFORMATION_BOUNDARY",
            status="BLOCK",
            severity="HIGH",
            affected_pipeline=pipeline,
            summary=("Preprocessing boundary is not training-only."),
            required_correction=("Fit preprocessing inside the training pipeline only."),
            evidence=(evidence,),
            critical_violation=True,
        )

    return AuditFinding(
        audit_id="A03_TRANSFORMATION_BOUNDARY",
        audit_family="TRANSFORMATION_BOUNDARY",
        status="PASS",
        severity="INFO",
        affected_pipeline=pipeline,
        summary=("Transformations are fitted on training data only."),
        required_correction="None.",
        evidence=(evidence,),
    )


def suspicious_feature_audit(
    feature_names: tuple[str, ...],
    evidence: EvidenceReference,
    *,
    pipeline: str,
) -> AuditFinding:
    """Audit blocked and obviously outcome-derived features."""

    blocked = set(blocked_feature_names())

    outcome_proxy = "post_outcome_confirmation_proxy"

    suspicious = tuple(
        sorted(
            feature for feature in feature_names if (feature in blocked or feature == outcome_proxy)
        )
    )

    if suspicious:
        return AuditFinding(
            audit_id="A04_SUSPICIOUS_FEATURE",
            audit_family="SUSPICIOUS_FEATURE",
            status="BLOCK",
            severity="CRITICAL",
            affected_pipeline=pipeline,
            summary=("Suspicious or prohibited features detected: " + ", ".join(suspicious)),
            required_correction=("Remove prohibited and outcome-derived features."),
            evidence=(evidence,),
            critical_violation=True,
        )

    return AuditFinding(
        audit_id="A04_SUSPICIOUS_FEATURE",
        audit_family="SUSPICIOUS_FEATURE",
        status="PASS",
        severity="INFO",
        affected_pipeline=pipeline,
        summary="No prohibited scoring features detected.",
        required_correction="None.",
        evidence=(evidence,),
    )


def evaluation_stability_audit(
    *,
    uses_chronological_reference: bool,
    temporal_result: str,
    temporal_roc_auc_gap: float,
    temporal_pr_auc_gap: float,
    evidence: EvidenceReference,
    pipeline: str,
) -> AuditFinding:
    """Audit whether release evidence uses the honest temporal reference."""

    if not uses_chronological_reference:
        status: AuditStatus = "BLOCK" if temporal_result == "BLOCK" else "WARN"

        return AuditFinding(
            audit_id="A05_EVALUATION_STABILITY",
            audit_family="EVALUATION_STABILITY",
            status=status,
            severity=("CRITICAL" if status == "BLOCK" else "HIGH"),
            affected_pipeline=pipeline,
            summary=(
                "Release evidence relies on random temporal mixing; "
                f"ROC-AUC gap={temporal_roc_auc_gap:.6f}, "
                f"PR-AUC gap={temporal_pr_auc_gap:.6f}."
            ),
            required_correction=("Use chronological evaluation as the release reference."),
            evidence=(evidence,),
            critical_violation=(status == "BLOCK"),
        )

    return AuditFinding(
        audit_id="A05_EVALUATION_STABILITY",
        audit_family="EVALUATION_STABILITY",
        status="PASS",
        severity="INFO",
        affected_pipeline=pipeline,
        summary=(
            "Release evidence uses the chronological reference; "
            "measured random-vs-temporal gaps are retained as evidence."
        ),
        required_correction="None.",
        evidence=(evidence,),
    )


def ordered_findings(
    findings: tuple[AuditFinding, ...],
) -> tuple[AuditFinding, ...]:
    """Return deterministic family/id ordering."""

    index = {name: position for position, name in enumerate(AUDIT_ORDER)}

    return tuple(
        sorted(
            findings,
            key=lambda finding: (
                index[finding.audit_family],
                finding.audit_id,
            ),
        )
    )


def release_decision(
    findings: tuple[AuditFinding, ...],
) -> ReleaseDecision:
    """Aggregate findings into deterministic release status."""

    if not findings:
        raise ValueError("At least one finding is required.")

    blockers = tuple(finding.audit_id for finding in findings if finding.status == "BLOCK")

    warnings = tuple(finding.audit_id for finding in findings if finding.status == "WARN")

    if blockers:
        return ReleaseDecision(
            status="BLOCK",
            recommendation=("Do not release until all blocking findings are corrected."),
            blocking_finding_ids=blockers,
            warning_finding_ids=warnings,
        )

    if warnings:
        return ReleaseDecision(
            status="WARN",
            recommendation=("Release requires explicit governance acceptance of warning findings."),
            blocking_finding_ids=(),
            warning_finding_ids=warnings,
        )

    return ReleaseDecision(
        status="PASS",
        recommendation=("Release gate passed for the audited evidence."),
        blocking_finding_ids=(),
        warning_finding_ids=(),
    )


def approve_public_claim(
    *,
    claim_id: str,
    evidence: tuple[EvidenceReference, ...],
    preview_only: bool = False,
    supported: bool = True,
) -> bool:
    """Evidence gate for public-facing claims."""

    if not claim_id.strip():
        raise ValueError("claim_id is required.")

    if not evidence:
        return False

    if preview_only:
        return False

    return supported


def _availability_map() -> dict[str, str]:
    contract = build_feature_contract()

    return {row.feature_name: row.availability_class.value for row in contract}


def _max_temporal_gap(
    temporal_case: dict[str, Any],
    metric: str,
) -> float:
    values = [float(model["metric_effect"][metric]) for model in temporal_case["model_results"]]

    return max(values)


def build_step4_audit(
    *,
    baseline: dict[str, Any],
    leakage_results: dict[str, Any],
) -> dict[str, Any]:
    """Build safe-pipeline and scenario reconciliation audit evidence."""

    cases = {row["case_id"]: row for row in leakage_results["cases"]}

    temporal = cases["S2_RANDOM_TEMPORAL_MIXING"]

    safe_features = tuple(baseline["pipelines"]["C_PREDICTION_TIME_SAFE"]["features"])

    chrono = baseline["splits"]["chronological"]

    feature_evidence = evidence_reference(
        "EV_FEATURE_CONTRACT",
        ("assets/p27_prediction_time_integrity_auditor/feature_availability_contract.json"),
        "Frozen feature-availability contract.",
    )

    split_evidence = evidence_reference(
        "EV_STEP2_SPLITS",
        ("assets/p27_prediction_time_integrity_auditor/split_manifest.json"),
        "Step 2 chronological split and overlap evidence.",
    )

    transformation_evidence = evidence_reference(
        "EV_STEP2_PIPELINE_C",
        ("assets/p27_prediction_time_integrity_auditor/baseline_results.json"),
        "Pipeline C train-only preprocessing evidence.",
    )

    scenario_evidence = evidence_reference(
        "EV_STEP3_CASES",
        ("assets/p27_prediction_time_integrity_auditor/leakage_case_results.json"),
        "Measured five-case leakage experiment evidence.",
    )

    safe_findings = ordered_findings(
        (
            feature_availability_audit(
                safe_features,
                _availability_map(),
                feature_evidence,
                pipeline="C_PREDICTION_TIME_SAFE",
            ),
            split_integrity_audit(
                train_validation_overlap=int(chrono["overlap_counts"]["train_validation"]),
                train_test_overlap=int(chrono["overlap_counts"]["train_test"]),
                validation_test_overlap=int(chrono["overlap_counts"]["validation_test"]),
                chronological_holdout=True,
                evidence=split_evidence,
                pipeline="C_PREDICTION_TIME_SAFE",
            ),
            transformation_boundary_audit(
                fitted_on_training_only=True,
                supervised_transformation=False,
                evidence=transformation_evidence,
                pipeline="C_PREDICTION_TIME_SAFE",
            ),
            suspicious_feature_audit(
                safe_features,
                feature_evidence,
                pipeline="C_PREDICTION_TIME_SAFE",
            ),
            evaluation_stability_audit(
                uses_chronological_reference=True,
                temporal_result=str(temporal["actual_auditor_result"]),
                temporal_roc_auc_gap=(
                    _max_temporal_gap(
                        temporal,
                        "roc_auc",
                    )
                ),
                temporal_pr_auc_gap=(
                    _max_temporal_gap(
                        temporal,
                        "pr_auc",
                    )
                ),
                evidence=scenario_evidence,
                pipeline="C_PREDICTION_TIME_SAFE",
            ),
        )
    )

    scenario_findings: tuple[AuditFinding, ...] = (
        suspicious_feature_audit(
            (
                *safe_features,
                "duration",
            ),
            scenario_evidence,
            pipeline="S1_CURRENT_CALL_DURATION",
        ),
        evaluation_stability_audit(
            uses_chronological_reference=False,
            temporal_result=str(temporal["actual_auditor_result"]),
            temporal_roc_auc_gap=(
                _max_temporal_gap(
                    temporal,
                    "roc_auc",
                )
            ),
            temporal_pr_auc_gap=(
                _max_temporal_gap(
                    temporal,
                    "pr_auc",
                )
            ),
            evidence=scenario_evidence,
            pipeline="S2_RANDOM_TEMPORAL_MIXING",
        ),
        transformation_boundary_audit(
            fitted_on_training_only=False,
            supervised_transformation=True,
            evidence=scenario_evidence,
            pipeline=("S3_GLOBAL_SUPERVISED_TRANSFORMATION"),
        ),
        split_integrity_audit(
            train_validation_overlap=0,
            train_test_overlap=int(
                cases["S4_DUPLICATE_OVERLAP"]["business_effect"]["detected_train_test_overlap"]
            ),
            validation_test_overlap=0,
            chronological_holdout=True,
            evidence=scenario_evidence,
            pipeline="S4_DUPLICATE_OVERLAP",
        ),
        suspicious_feature_audit(
            (
                *safe_features,
                "post_outcome_confirmation_proxy",
            ),
            scenario_evidence,
            pipeline=("S5_POST_OUTCOME_CONFIRMATION_PROXY"),
        ),
    )

    scenario_findings = tuple(
        sorted(
            scenario_findings,
            key=lambda finding: (
                finding.affected_pipeline,
                finding.audit_id,
            ),
        )
    )

    safe_release = release_decision(safe_findings)

    if safe_release.status != "PASS":
        raise RuntimeError("Prediction-time-safe Pipeline C failed Step 4 release gate.")

    if any(finding.status == "PASS" for finding in scenario_findings):
        raise RuntimeError("A defined Step 3 violation received a false PASS.")

    payload: dict[str, Any] = {
        "scope": "PROJECT7_STEP4_AUDITOR_RELEASE_GATE",
        "audit_families": list(AUDIT_ORDER),
        "safe_pipeline": {
            "pipeline_id": ("C_PREDICTION_TIME_SAFE"),
            "findings": [finding.to_dict() for finding in safe_findings],
            "release_decision": (safe_release.to_dict()),
        },
        "scenario_reconciliation": [finding.to_dict() for finding in scenario_findings],
        "public_claim_gate": {
            "evidence_required": True,
            "preview_only_blocked": True,
            "unsupported_blocked": True,
        },
        "source_fingerprints": {
            "step2_baseline": baseline["baseline_fingerprint_sha256"],
            "step3_cases": leakage_results["step3_fingerprint_sha256"],
        },
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    payload["step4_fingerprint_sha256"] = hashlib.sha256(canonical).hexdigest()

    return payload


def write_step4_evidence(
    payload: dict[str, Any],
    output_root: Path,
) -> tuple[Path, Path]:
    """Write Step 4 audit evidence and manifest."""

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    findings_path = output_root / "audit_findings.json"

    manifest_path = output_root / "audit_manifest.json"

    findings_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest = {
        "scope": payload["scope"],
        "audit_families": payload["audit_families"],
        "safe_release_status": payload["safe_pipeline"]["release_decision"]["status"],
        "source_fingerprints": payload["source_fingerprints"],
        "step4_fingerprint_sha256": payload["step4_fingerprint_sha256"],
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return (
        findings_path,
        manifest_path,
    )
