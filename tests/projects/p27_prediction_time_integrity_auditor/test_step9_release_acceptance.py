from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import (
    release_acceptance as release,
)


def test_source_and_split_contracts() -> None:
    source = release.validate_source()
    split = release.validate_split()

    assert source["release_status"] == "PASS"
    assert source["step5_fingerprint"] == release.EXPECTED_STEP5_FINGERPRINT

    assert float(split["temporal_roc_auc_gap"]) > 0.0


def test_five_cases_and_models() -> None:
    cases = release.validate_leakage_cases()
    models = release.validate_models()

    assert cases["scenario_count"] == 5
    assert cases["model_result_count"] == 10

    assert set(models["models"]) == release.EXPECTED_MODELS


def test_reconciliation_auditor_claims() -> None:
    reconciliation = release.validate_metric_reconciliation()

    auditor = release.validate_auditor()
    claims = release.validate_claim_register()

    assert reconciliation["reconciled_effects"] == 60
    assert reconciliation["mismatches"] == 0
    assert reconciliation["duplicate_overlap"] == 618

    assert auditor["safe_release"] == "PASS"
    assert auditor["no_false_pass"] is True

    assert claims["approved_claim_count"] == 8


def test_figures_dashboard_and_manuscript() -> None:
    figures = release.validate_figures()
    dashboard = release.validate_dashboard()
    manuscript = release.validate_manuscript()
    metadata = release.validate_publication_metadata()

    assert figures["figure_count"] == 7
    assert dashboard["tab_count"] == 6
    assert manuscript["traceability_rows"] == 8
    assert metadata["external_publication"] == "LOCKED"


def test_publication_scans() -> None:
    placeholders = release.placeholder_scan()
    preview = release.preview_number_scan()
    reconciliation = release.claim_evidence_reconciliation()

    assert placeholders["placeholder_matches"] == 0
    assert preview["preview_number_matches"] == 0
    assert reconciliation["approved_claims"] == 8
    assert reconciliation["mismatches"] == 0


def test_release_zip_exists_after_run_all() -> None:
    manifest = release.RELEASE / "step9_release_manifest.json"

    receipt = release.RELEASE / "run_all_receipt.json"

    assert isinstance(
        manifest,
        Path,
    )

    assert manifest.is_file()
    assert receipt.is_file()

    verification = release.verify_release()

    assert verification["zip_size_bytes"] > 0
    assert len(verification["zip_sha256"]) == 64
