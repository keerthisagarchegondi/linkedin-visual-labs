from __future__ import annotations

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.data import (
    LoadedDataset,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.modeling import (
    MODEL_NAMES,
    build_model_pipeline,
    run_baselines,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.preprocessing import (
    pipeline_c_features,
)


def _synthetic_dataset(
    rows: int = 80,
) -> LoadedDataset:
    records: list[dict[str, str]] = []

    jobs = [
        "admin.",
        "technician",
        "services",
    ]

    for index in range(rows):
        positive = index % 5 == 0 or index % 7 == 0

        records.append(
            {
                "age": str(25 + index % 35),
                "job": jobs[index % len(jobs)],
                "marital": ("single" if index % 2 else "married"),
                "education": "university.degree",
                "default": "no",
                "housing": ("yes" if index % 3 else "no"),
                "loan": "no",
                "contact": "cellular",
                "month": ("may" if index < rows // 2 else "jun"),
                "day_of_week": ("mon" if index % 2 else "tue"),
                "duration": str(60 + index),
                "campaign": str(1 + index % 3),
                "pdays": "999",
                "previous": str(index % 2),
                "poutcome": "nonexistent",
                "emp.var.rate": "1.1",
                "cons.price.idx": "93.9",
                "cons.conf.idx": "-36.4",
                "euribor3m": str(3.0 + index / 100),
                "nr.employed": "5191.0",
                "y": ("yes" if positive else "no"),
            }
        )

    return LoadedDataset(
        rows=tuple(records),
        source_order=tuple(range(rows)),
    )


def test_both_frozen_models_build() -> None:
    features = pipeline_c_features()

    for model_id in MODEL_NAMES:
        pipeline = build_model_pipeline(
            model_id,
            features,
        )

        assert pipeline.named_steps["preprocessor"] is not None

        assert pipeline.named_steps["model"] is not None


def test_step2_baseline_is_deterministic_on_synthetic_data() -> None:
    dataset = _synthetic_dataset()

    first = run_baselines(dataset)

    second = run_baselines(dataset)

    assert first["baseline_fingerprint_sha256"] == second["baseline_fingerprint_sha256"]

    evaluations = first["evaluations"]

    assert isinstance(
        evaluations,
        list,
    )

    assert len(evaluations) == 8

    pipeline_c = first["pipelines"]["C_PREDICTION_TIME_SAFE"]

    assert isinstance(
        pipeline_c,
        dict,
    )

    features = pipeline_c["features"]

    assert isinstance(
        features,
        list,
    )

    assert "duration" not in features
    assert "campaign" not in features
