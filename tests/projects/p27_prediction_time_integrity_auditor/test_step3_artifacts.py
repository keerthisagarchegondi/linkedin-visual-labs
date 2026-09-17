from __future__ import annotations

import json

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.config import (
    repository_root,
)


def test_step3_artifacts_are_exact() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    results = json.loads((root / "leakage_case_results.json").read_text(encoding="utf-8"))

    manifest = json.loads((root / "leakage_case_manifest.json").read_text(encoding="utf-8"))

    assert results["scope"] == "PROJECT7_STEP3_FIVE_LEAKAGE_CASES"

    assert results["scenario_count"] == 5

    assert len(results["cases"]) == 5

    assert manifest["step3_fingerprint_sha256"] == results["step3_fingerprint_sha256"]


def test_evidence_classes_are_frozen() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    results = json.loads((root / "leakage_case_results.json").read_text(encoding="utf-8"))

    cases = results["cases"]

    assert cases[0]["evidence_class"] == "OBSERVED_DATASET_CONDITION"

    assert cases[1]["evidence_class"] == "EVALUATION_DESIGN_EXPERIMENT"

    assert all(row["evidence_class"] == "CONTROLLED_INJECTION" for row in cases[2:])


def test_safe_step2_baseline_is_unchanged() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    baseline = json.loads((root / "baseline_results.json").read_text(encoding="utf-8"))

    assert (
        baseline["baseline_fingerprint_sha256"]
        == "87d57e0824657a5984a867ee3456b5a999e2bbac516f3b772b94a0e47a014abf"
    )
