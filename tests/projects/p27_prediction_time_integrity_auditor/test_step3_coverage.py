from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.leakage_cases import (
    ModelComparison,
    _direct_numeric_model,
    _target_mean_mapping,
    duplicate_injection_indices,
    temporal_audit_result,
    write_step3_evidence,
)


def comparison(
    roc_gap: float,
    pr_gap: float,
) -> ModelComparison:
    return ModelComparison(
        model_id="logistic_regression",
        leaked_metrics={},
        safe_metrics={},
        metric_effect={
            "roc_auc": roc_gap,
            "pr_auc": pr_gap,
        },
        campaign_yield_overstatement=0.0,
    )


def test_temporal_warn_policy() -> None:
    assert (
        temporal_audit_result(
            (
                comparison(
                    0.01,
                    0.01,
                ),
            )
        )
        == "WARN"
    )


@pytest.mark.parametrize(
    ("roc_gap", "pr_gap"),
    [
        (
            0.02,
            0.00,
        ),
        (
            0.00,
            0.02,
        ),
    ],
)
def test_temporal_block_policy(
    roc_gap: float,
    pr_gap: float,
) -> None:
    assert (
        temporal_audit_result(
            (
                comparison(
                    roc_gap,
                    pr_gap,
                ),
            )
        )
        == "BLOCK"
    )


@pytest.mark.parametrize(
    "fraction",
    [
        0.0,
        -0.1,
        1.1,
    ],
)
def test_duplicate_fraction_validation(
    fraction: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="fraction must be",
    ):
        duplicate_injection_indices(
            (
                1,
                2,
                3,
            ),
            fraction=fraction,
        )


def test_target_mean_mapping() -> None:
    mapping, fallback = _target_mean_mapping(
        [
            "a",
            "a",
            "b",
            "b",
        ],
        [
            0,
            1,
            1,
            1,
        ],
        (
            0,
            1,
            2,
            3,
        ),
    )

    assert mapping == {
        "a": 0.5,
        "b": 1.0,
    }

    assert fallback == pytest.approx(0.75)


def test_direct_numeric_models() -> None:
    assert _direct_numeric_model("logistic_regression") is not None

    assert _direct_numeric_model("histogram_gradient_boosting") is not None


def test_direct_numeric_model_rejects_unknown() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown model_id",
    ):
        _direct_numeric_model("unknown")


def test_write_step3_evidence(
    tmp_path: Path,
) -> None:
    payload = {
        "scope": "PROJECT7_STEP3_FIVE_LEAKAGE_CASES",
        "seed": 1729,
        "scenario_count": 5,
        "scenario_ids": [
            "a",
            "b",
            "c",
            "d",
            "e",
        ],
        "temporal_governance_policy": {
            "warn_default": True,
        },
        "duplicate_injection_fraction": 0.10,
        "cases": [],
        "step3_fingerprint_sha256": "abc123",
    }

    results, manifest = write_step3_evidence(
        payload,
        tmp_path,
    )

    assert results.is_file()
    assert manifest.is_file()
