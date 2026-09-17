from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import (
    cli as cli_module,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.metrics import (
    evaluate_probabilities,
    expected_calibration_error,
    practical_calibration_parameters,
    top_decile_metrics,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.modeling import (
    build_model_pipeline,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.preprocessing import (
    pipeline_c_features,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.splits import (
    SplitIndices,
    chronological_split,
    validate_chronological_order,
    validate_partition_integrity,
)


def test_chronological_split_rejects_invalid_fractions() -> None:
    with pytest.raises(
        ValueError,
        match="train_fraction",
    ):
        chronological_split(
            100,
            train_fraction=0.0,
        )

    with pytest.raises(
        ValueError,
        match="validation_fraction",
    ):
        chronological_split(
            100,
            validation_fraction=0.0,
        )

    with pytest.raises(
        ValueError,
        match=r"Train \+ validation",
    ):
        chronological_split(
            100,
            train_fraction=0.90,
            validation_fraction=0.20,
        )

    with pytest.raises(
        ValueError,
        match="empty partition",
    ):
        chronological_split(
            3,
            train_fraction=0.01,
            validation_fraction=0.01,
        )


def test_partition_validation_rejects_missing_domain() -> None:
    split = SplitIndices(
        train=(0,),
        validation=(1,),
        test=(3,),
    )

    with pytest.raises(
        ValueError,
        match="source row domain",
    ):
        validate_partition_integrity(
            3,
            split,
        )


def test_chronological_order_rejects_train_validation_overlap() -> None:
    split = SplitIndices(
        train=(0, 2),
        validation=(2, 3),
        test=(4,),
    )

    with pytest.raises(
        ValueError,
        match="Training period overlaps",
    ):
        validate_chronological_order(split)


def test_chronological_order_rejects_validation_test_overlap() -> None:
    split = SplitIndices(
        train=(0,),
        validation=(1, 3),
        test=(3, 4),
    )

    with pytest.raises(
        ValueError,
        match="Validation period overlaps",
    ):
        validate_chronological_order(split)


def test_ece_rejects_shape_mismatch_and_empty() -> None:
    with pytest.raises(
        ValueError,
        match="equal shape",
    ):
        expected_calibration_error(
            [0, 1],
            [0.1],
        )

    with pytest.raises(
        ValueError,
        match="empty prediction set",
    ):
        expected_calibration_error(
            [],
            [],
        )


def test_top_decile_zero_prevalence_has_zero_lift() -> None:
    response_rate, lift, per_1000 = top_decile_metrics(
        [0] * 10,
        [
            0.90,
            0.80,
            0.70,
            0.60,
            0.50,
            0.40,
            0.30,
            0.20,
            0.10,
            0.00,
        ],
    )

    assert response_rate == 0.0
    assert lift == 0.0
    assert per_1000 == 0.0


def test_calibration_parameters_single_class_returns_nan() -> None:
    intercept, slope = practical_calibration_parameters(
        [0, 0, 0],
        [0.1, 0.2, 0.3],
    )

    assert str(intercept) == "nan"
    assert str(slope) == "nan"


def test_evaluate_probabilities_rejects_shape_mismatch_and_empty() -> None:
    with pytest.raises(
        ValueError,
        match="equal shape",
    ):
        evaluate_probabilities(
            [0, 1],
            [0.2],
        )

    with pytest.raises(
        ValueError,
        match="empty prediction set",
    ):
        evaluate_probabilities(
            [],
            [],
        )


def test_model_factory_rejects_unknown_model() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown model_id",
    ):
        build_model_pipeline(
            "not-a-model",
            pipeline_c_features(),
        )


def test_step2_evidence_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli_module,
        "repository_root",
        lambda: tmp_path,
    )

    payload: dict[str, Any] = {
        "seed": 1729,
        "splits": {
            "chronological": {
                "policy": "test",
            }
        },
        "baseline_fingerprint_sha256": "abc123",
    }

    results_path, split_path = cli_module._write_step2_payload(payload)

    assert results_path.is_file()
    assert split_path.is_file()

    results = json.loads(results_path.read_text(encoding="utf-8"))

    split = json.loads(split_path.read_text(encoding="utf-8"))

    assert results["baseline_fingerprint_sha256"] == "abc123"

    assert split["baseline_fingerprint_sha256"] == "abc123"

    assert split["seed"] == 1729


def test_cli_run_step2_baseline_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake_dataset = object()

    payload: dict[str, Any] = {
        "seed": 1729,
        "splits": {},
        "evaluations": [],
        "baseline_fingerprint_sha256": "fixture-fingerprint",
    }

    monkeypatch.setattr(
        cli_module,
        "load_official_dataset",
        lambda *, acquire=False: fake_dataset,
    )

    monkeypatch.setattr(
        cli_module,
        "run_baselines",
        lambda dataset: payload,
    )

    results_path = tmp_path / "baseline_results.json"

    split_path = tmp_path / "split_manifest.json"

    monkeypatch.setattr(
        cli_module,
        "_write_step2_payload",
        lambda generated: (
            results_path,
            split_path,
        ),
    )

    result = cli_module.main(
        [
            "run-step2-baseline",
        ]
    )

    assert result == 0

    output = json.loads(capsys.readouterr().out)

    assert output["status"] == "PASS"

    assert output["baseline_fingerprint_sha256"] == "fixture-fingerprint"

    assert output["evaluation_count"] == 0
