from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.validation import (
    EXPECTED_CASE_IDS,
    baseline_metric_rows,
    build_claim_register,
    build_release_data,
    campaign_yield_overstatement_values,
    canonical_sha256,
    freeze_step5_release,
    independently_validate,
    independently_validate_frozen_release,
    leakage_inflation_rows,
    leakage_model_rows,
    normalize_cases,
    reconcile_metric_effects,
    temporal_gap,
)


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
        raise TypeError(f"{name} is not a JSON object.")

    return payload


def test_step3_cases_normalize_to_exact_five_ids() -> None:
    cases = normalize_cases(load("leakage_case_results.json"))

    assert tuple(cases) == EXPECTED_CASE_IDS


def test_baseline_contains_eight_evaluations() -> None:
    rows = baseline_metric_rows(load("baseline_results.json"))

    assert len(rows) == 8

    assert {str(row["model_id"]) for row in rows} == {
        "logistic_regression",
        "histogram_gradient_boosting",
    }


def test_leakage_table_contains_ten_model_case_rows() -> None:
    rows = leakage_model_rows(load("leakage_case_results.json"))

    assert len(rows) == 10


def test_every_reported_effect_reconciles_independently() -> None:
    rows = reconcile_metric_effects(load("leakage_case_results.json"))

    assert len(rows) == 60
    assert all(row.reconciled for row in rows)


def test_campaign_yield_overstatement_reconciles() -> None:
    values = campaign_yield_overstatement_values(load("leakage_case_results.json"))

    assert len(values) == 10


def test_temporal_gap_is_recomputed() -> None:
    step3 = load("leakage_case_results.json")

    assert (
        temporal_gap(
            step3,
            "roc_auc",
        )
        > 0
    )

    assert (
        temporal_gap(
            step3,
            "pr_auc",
        )
        > 0
    )


def test_leakage_inflation_direction_is_explicit() -> None:
    rows = leakage_inflation_rows(load("leakage_case_results.json"))

    assert rows

    assert {str(row["direction"]) for row in rows} == {
        "HIGHER_IS_BETTER",
        "LOWER_IS_BETTER",
    }


def test_independent_validation_passes_exact_sources() -> None:
    validation, reconciliation = independently_validate(
        load("baseline_results.json"),
        load("leakage_case_results.json"),
        load("audit_findings.json"),
    )

    assert validation.status == "PASS"
    assert validation.scenario_count == 5
    assert validation.model_result_count == 10
    assert validation.metric_effect_mismatch_count == 0
    assert validation.safe_release_status == "PASS"
    assert validation.no_false_pass is True
    assert validation.duplicate_train_test_overlap > 0
    assert reconciliation


def test_release_data_has_no_public_artifacts() -> None:
    release = build_release_data(
        load("baseline_results.json"),
        load("leakage_case_results.json"),
        load("audit_findings.json"),
    )

    assert release["release_status"] == "PASS"

    assert release["public_artifacts_generated"] is False

    assert release["step6_started"] is False


def test_claim_register_distinguishes_observed_and_injected() -> None:
    leakage = load("leakage_case_results.json")

    release = build_release_data(
        load("baseline_results.json"),
        leakage,
        load("audit_findings.json"),
    )

    claims = build_claim_register(
        release,
        leakage,
    )

    assert claims["claim_count"] == 8

    assert claims["preview_claims_approved"] is False

    assert claims["unsupported_claims_approved"] is False


def test_canonical_hash_is_order_independent() -> None:
    assert canonical_sha256(
        {
            "a": 1,
            "b": 2,
        }
    ) == canonical_sha256(
        {
            "b": 2,
            "a": 1,
        }
    )


def test_complete_freeze_and_revalidation(
    tmp_path: Path,
) -> None:
    for name in (
        "baseline_results.json",
        "leakage_case_results.json",
        "audit_findings.json",
        "audit_manifest.json",
    ):
        (tmp_path / name).write_bytes((assets_root() / name).read_bytes())

    result = freeze_step5_release(tmp_path)

    assert result["release_data"]["release_status"] == "PASS"

    validation = independently_validate_frozen_release(tmp_path)

    assert validation["status"] == "PASS"

    assert validation["metric_effect_mismatch_count"] == 0


def test_preview_contamination_is_blocked() -> None:
    from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.validation import (
        assert_no_preview_contamination,
    )

    with pytest.raises(
        RuntimeError,
        match="Preview",
    ):
        assert_no_preview_contamination(
            {
                "preview_metric": 1,
            }
        )
