from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import validation


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def assets_root() -> Path:
    return repository_root() / "assets" / "p27_prediction_time_integrity_auditor"


def load(
    name: str,
) -> dict[str, Any]:
    payload: object = json.loads((assets_root() / name).read_text(encoding="utf-8"))

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(name)

    return payload


def test_normalize_cases_rejects_non_list() -> None:
    with pytest.raises(
        RuntimeError,
        match="must be a list",
    ):
        validation.normalize_cases(
            {
                "cases": {},
            }
        )


def test_normalize_cases_rejects_wrong_count() -> None:
    with pytest.raises(
        RuntimeError,
        match="Expected 5",
    ):
        validation.normalize_cases(
            {
                "cases": [],
            }
        )


def test_normalize_cases_rejects_non_object_case() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0] = "bad"

    with pytest.raises(
        RuntimeError,
        match="must be an object",
    ):
        validation.normalize_cases(broken)


def test_normalize_cases_rejects_missing_case_id() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0].pop("case_id")

    with pytest.raises(
        RuntimeError,
        match="missing case_id",
    ):
        validation.normalize_cases(broken)


def test_normalize_cases_rejects_duplicate_id() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][1]["case_id"] = broken["cases"][0]["case_id"]

    with pytest.raises(
        RuntimeError,
        match="Duplicate case_id",
    ):
        validation.normalize_cases(broken)


def test_normalize_cases_rejects_order_drift() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0], broken["cases"][1] = (
        broken["cases"][1],
        broken["cases"][0],
    )

    with pytest.raises(
        RuntimeError,
        match="scenario order drift",
    ):
        validation.normalize_cases(broken)


def test_baseline_metric_rows_rejects_missing_evaluations() -> None:
    with pytest.raises(
        RuntimeError,
        match="evaluations missing",
    ):
        validation.baseline_metric_rows({})


def test_baseline_metric_rows_rejects_wrong_count() -> None:
    baseline = load("baseline_results.json")

    broken = copy.deepcopy(baseline)

    broken["evaluations"] = broken["evaluations"][:-1]

    with pytest.raises(
        RuntimeError,
        match="Expected 8",
    ):
        validation.baseline_metric_rows(broken)


def test_baseline_metric_rows_rejects_non_object() -> None:
    baseline = load("baseline_results.json")

    broken = copy.deepcopy(baseline)

    broken["evaluations"][0] = "bad"

    with pytest.raises(
        RuntimeError,
        match="must be an object",
    ):
        validation.baseline_metric_rows(broken)


def test_baseline_metric_rows_rejects_missing_metrics() -> None:
    baseline = load("baseline_results.json")

    broken = copy.deepcopy(baseline)

    broken["evaluations"][0]["metrics"] = None

    with pytest.raises(
        RuntimeError,
        match="metrics missing",
    ):
        validation.baseline_metric_rows(broken)


def test_leakage_rows_reject_wrong_model_result_count() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0]["model_results"] = []

    with pytest.raises(
        RuntimeError,
        match="expected two model_results",
    ):
        validation.leakage_model_rows(broken)


def test_leakage_rows_reject_bad_model_result() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0]["model_results"][0] = "bad"

    with pytest.raises(
        RuntimeError,
        match="invalid model result",
    ):
        validation.leakage_model_rows(broken)


def test_leakage_rows_reject_unknown_model() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0]["model_results"][0]["model_id"] = "other"

    with pytest.raises(
        RuntimeError,
        match="Unexpected model_id",
    ):
        validation.leakage_model_rows(broken)


@pytest.mark.parametrize(
    (
        "field",
        "match",
    ),
    (
        (
            "safe_metrics",
            "safe_metrics missing",
        ),
        (
            "leaked_metrics",
            "leaked_metrics missing",
        ),
        (
            "metric_effect",
            "metric_effect missing",
        ),
    ),
)
def test_leakage_rows_reject_missing_model_sections(
    field: str,
    match: str,
) -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    broken["cases"][0]["model_results"][0][field] = None

    with pytest.raises(
        RuntimeError,
        match=match,
    ):
        validation.leakage_model_rows(broken)


def test_unknown_leakage_inflation_direction_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="No leakage-inflation direction",
    ):
        validation.leakage_inflation_value(
            "unknown",
            1.0,
            2.0,
        )


def test_duplicate_overlap_requires_business_effect() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    for case in broken["cases"]:
        if case["case_id"] == "S4_DUPLICATE_OVERLAP":
            case["business_effect"] = None

    with pytest.raises(
        RuntimeError,
        match="business_effect missing",
    ):
        validation.duplicate_overlap(broken)


def test_duplicate_overlap_requires_overlap_value() -> None:
    step3 = load("leakage_case_results.json")

    broken = copy.deepcopy(step3)

    for case in broken["cases"]:
        if case["case_id"] == "S4_DUPLICATE_OVERLAP":
            case["business_effect"]["detected_train_test_overlap"] = None

    with pytest.raises(
        RuntimeError,
        match="detected_train_test_overlap missing",
    ):
        validation.duplicate_overlap(broken)


def test_safe_release_requires_safe_pipeline() -> None:
    with pytest.raises(
        RuntimeError,
        match="safe_pipeline missing",
    ):
        validation.safe_release_status({})


def test_safe_release_requires_release_decision() -> None:
    with pytest.raises(
        RuntimeError,
        match="release_decision missing",
    ):
        validation.safe_release_status(
            {
                "safe_pipeline": {},
            }
        )


def test_no_false_pass_requires_five_findings() -> None:
    with pytest.raises(
        RuntimeError,
        match="five scenario",
    ):
        validation.no_false_pass(
            {
                "scenario_reconciliation": [],
            }
        )


@pytest.mark.parametrize(
    (
        "source",
        "expected",
    ),
    (
        (
            "baseline",
            "Step 2 baseline fingerprint drift",
        ),
        (
            "step3",
            "Step 3 fingerprint drift",
        ),
        (
            "step4",
            "Step 4 fingerprint drift",
        ),
    ),
)
def test_source_fingerprint_drift_is_blocked(
    source: str,
    expected: str,
) -> None:
    baseline = load("baseline_results.json")

    step3 = load("leakage_case_results.json")

    step4 = load("audit_findings.json")

    if source == "baseline":
        baseline["baseline_fingerprint_sha256"] = "bad"

    elif source == "step3":
        step3["step3_fingerprint_sha256"] = "bad"

    else:
        step4["step4_fingerprint_sha256"] = "bad"

    with pytest.raises(
        RuntimeError,
        match=expected,
    ):
        validation.validate_source_fingerprints(
            baseline,
            step3,
            step4,
        )


def test_build_release_blocks_failed_independent_validation() -> None:
    baseline = load("baseline_results.json")

    step3 = load("leakage_case_results.json")

    step4 = load("audit_findings.json")

    broken = copy.deepcopy(step4)

    broken["safe_pipeline"]["release_decision"]["status"] = "BLOCK"

    with pytest.raises(
        RuntimeError,
        match="blocked release",
    ):
        validation.build_release_data(
            baseline,
            step3,
            broken,
        )


def test_claim_register_blocks_s1_label_drift() -> None:
    baseline = load("baseline_results.json")

    step3 = load("leakage_case_results.json")

    step4 = load("audit_findings.json")

    release = validation.build_release_data(
        baseline,
        step3,
        step4,
    )

    broken = copy.deepcopy(step3)

    broken["cases"][0]["observed_or_injected"] = "INJECTED"

    with pytest.raises(
        RuntimeError,
        match="S1 observed/injected label drift",
    ):
        validation.build_claim_register(
            release,
            broken,
        )


def test_claim_register_blocks_injected_label_drift() -> None:
    baseline = load("baseline_results.json")

    step3 = load("leakage_case_results.json")

    step4 = load("audit_findings.json")

    release = validation.build_release_data(
        baseline,
        step3,
        step4,
    )

    broken = copy.deepcopy(step3)

    for case in broken["cases"]:
        if case["case_id"] == "S3_GLOBAL_SUPERVISED_TRANSFORMATION":
            case["observed_or_injected"] = "OBSERVED"

    with pytest.raises(
        RuntimeError,
        match="not labeled as injected",
    ):
        validation.build_claim_register(
            release,
            broken,
        )


def test_write_csv_rejects_empty_rows(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        RuntimeError,
        match="Refusing empty result table",
    ):
        validation.write_csv(
            tmp_path / "empty.csv",
            [],
        )


def test_frozen_release_blocks_validation_drift(
    tmp_path: Path,
) -> None:
    for name in (
        "baseline_results.json",
        "leakage_case_results.json",
        "audit_findings.json",
        "audit_manifest.json",
    ):
        (tmp_path / name).write_bytes((assets_root() / name).read_bytes())

    validation.freeze_step5_release(tmp_path)

    release_path = tmp_path / "release_data.json"

    release = json.loads(release_path.read_text(encoding="utf-8"))

    release["independent_validation"]["scenario_count"] = 999

    release_path.write_text(
        json.dumps(
            release,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="Frozen validation does not reconcile",
    ):
        validation.independently_validate_frozen_release(tmp_path)


def test_frozen_release_blocks_reconciliation_drift(
    tmp_path: Path,
) -> None:
    for name in (
        "baseline_results.json",
        "leakage_case_results.json",
        "audit_findings.json",
        "audit_manifest.json",
    ):
        (tmp_path / name).write_bytes((assets_root() / name).read_bytes())

    validation.freeze_step5_release(tmp_path)

    release_path = tmp_path / "release_data.json"

    release = json.loads(release_path.read_text(encoding="utf-8"))

    release["metric_effect_reconciliation"] = []

    release_path.write_text(
        json.dumps(
            release,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="metric reconciliation",
    ):
        validation.independently_validate_frozen_release(tmp_path)
