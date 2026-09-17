from __future__ import annotations

import json

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.config import (
    repository_root,
)


def test_step4_audit_artifacts_exist_and_reconcile() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    findings = json.loads((root / "audit_findings.json").read_text(encoding="utf-8"))

    manifest = json.loads((root / "audit_manifest.json").read_text(encoding="utf-8"))

    assert findings["scope"] == "PROJECT7_STEP4_AUDITOR_RELEASE_GATE"

    assert findings["audit_families"] == [
        "FEATURE_AVAILABILITY",
        "SPLIT_INTEGRITY",
        "TRANSFORMATION_BOUNDARY",
        "SUSPICIOUS_FEATURE",
        "EVALUATION_STABILITY",
    ]

    assert findings["safe_pipeline"]["release_decision"]["status"] == "PASS"

    assert len(findings["safe_pipeline"]["findings"]) == 5

    assert len(findings["scenario_reconciliation"]) == 5

    assert all(finding["status"] != "PASS" for finding in findings["scenario_reconciliation"])

    assert manifest["step4_fingerprint_sha256"] == findings["step4_fingerprint_sha256"]


def test_step4_preserves_step2_and_step3_fingerprints() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    findings = json.loads((root / "audit_findings.json").read_text(encoding="utf-8"))

    assert findings["source_fingerprints"]["step2_baseline"] == (
        "87d57e0824657a5984a867ee3456b5a999e2bbac516f3b772b94a0e47a014abf"
    )

    assert findings["source_fingerprints"]["step3_cases"] == (
        "99bfafda40ff9404cddbcc48b454708f2bc9efe3e8742b174471d3a6d6f2da84"
    )
