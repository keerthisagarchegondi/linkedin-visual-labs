from __future__ import annotations

import json

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.config import (
    repository_root,
)


def test_step2_baseline_artifacts_are_complete() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    baseline = json.loads((root / "baseline_results.json").read_text(encoding="utf-8"))

    split_manifest = json.loads((root / "split_manifest.json").read_text(encoding="utf-8"))

    assert baseline["scope"] == "PROJECT7_STEP2_BASELINE_ONLY"

    assert baseline["seed"] == 1729

    assert baseline["models"] == [
        "logistic_regression",
        "histogram_gradient_boosting",
    ]

    assert len(baseline["evaluations"]) == 8

    chronological = baseline["splits"]["chronological"]

    assert chronological["overlap_counts"] == {
        "train_test": 0,
        "train_validation": 0,
        "validation_test": 0,
    }

    assert split_manifest["baseline_fingerprint_sha256"] == baseline["baseline_fingerprint_sha256"]


def test_step2_pipeline_contracts_are_preserved() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    baseline = json.loads((root / "baseline_results.json").read_text(encoding="utf-8"))

    pipeline_b = baseline["pipelines"]["B_PARTIALLY_CORRECTED"]

    pipeline_c = baseline["pipelines"]["C_PREDICTION_TIME_SAFE"]

    assert "duration" not in pipeline_b["features"]

    assert "campaign" in pipeline_b["features"]

    assert "duration" not in pipeline_c["features"]

    assert "campaign" not in pipeline_c["features"]

    assert pipeline_c["fully_prediction_time_safe"] is True
