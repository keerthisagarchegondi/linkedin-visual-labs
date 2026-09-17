from __future__ import annotations

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.data import (
    LoadedDataset,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.leakage_cases import (
    DUPLICATE_INJECTION_FRACTION,
    SCENARIO_IDS,
    duplicate_injection_indices,
    run_leakage_cases,
    scenario_catalog,
)


def synthetic_dataset(
    rows: int = 100,
) -> LoadedDataset:
    records: list[dict[str, str]] = []

    jobs = (
        "admin.",
        "technician",
        "services",
        "management",
    )

    for index in range(rows):
        positive = index % 5 == 0 or index % 11 == 0

        records.append(
            {
                "age": str(24 + index % 40),
                "job": jobs[index % len(jobs)],
                "marital": ("single" if index % 2 else "married"),
                "education": "university.degree",
                "default": "no",
                "housing": ("yes" if index % 3 else "no"),
                "loan": "no",
                "contact": "cellular",
                "month": ("may" if index < rows // 2 else "jun"),
                "day_of_week": ("mon" if index % 2 else "tue"),
                "duration": str((500 if positive else 75) + index % 20),
                "campaign": str(1 + index % 4),
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


def test_catalog_is_exactly_five_cases() -> None:
    catalog = scenario_catalog()

    assert len(catalog) == 5

    assert tuple(row["case_id"] for row in catalog) == SCENARIO_IDS

    assert catalog[0]["evidence_class"] == "OBSERVED_DATASET_CONDITION"

    assert catalog[1]["evidence_class"] == "EVALUATION_DESIGN_EXPERIMENT"

    assert all(row["evidence_class"] == "CONTROLLED_INJECTION" for row in catalog[2:])


def test_duplicate_injection_is_deterministic() -> None:
    indices = tuple(
        range(
            100,
            120,
        )
    )

    first = duplicate_injection_indices(indices)

    second = duplicate_injection_indices(indices)

    assert first == second
    assert first == (
        100,
        101,
    )

    assert DUPLICATE_INJECTION_FRACTION == 0.10


def test_five_cases_are_deterministic() -> None:
    dataset = synthetic_dataset()

    first = run_leakage_cases(dataset)

    second = run_leakage_cases(dataset)

    assert first["step3_fingerprint_sha256"] == second["step3_fingerprint_sha256"]

    assert first["scenario_count"] == 5

    assert first["scenario_ids"] == list(SCENARIO_IDS)


def test_case_labels_and_results() -> None:
    payload = run_leakage_cases(synthetic_dataset())

    by_id = {row["case_id"]: row for row in payload["cases"]}

    assert by_id["S1_CURRENT_CALL_DURATION"]["observed_or_injected"] == "OBSERVED"

    assert by_id["S1_CURRENT_CALL_DURATION"]["actual_auditor_result"] == "BLOCK"

    assert by_id["S2_RANDOM_TEMPORAL_MIXING"]["actual_auditor_result"] in {
        "WARN",
        "BLOCK",
    }

    for case_id in (
        "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
        "S4_DUPLICATE_OVERLAP",
        "S5_POST_OUTCOME_CONFIRMATION_PROXY",
    ):
        assert by_id[case_id]["observed_or_injected"] == "CONTROLLED_INJECTION"

        assert by_id[case_id]["actual_auditor_result"] == "BLOCK"


def test_duplicate_case_has_overlap_proof() -> None:
    payload = run_leakage_cases(synthetic_dataset())

    duplicate = next(row for row in payload["cases"] if row["case_id"] == "S4_DUPLICATE_OVERLAP")

    assert duplicate["business_effect"]["detected_train_test_overlap"] > 0


def test_every_case_has_frozen_schema() -> None:
    payload = run_leakage_cases(synthetic_dataset())

    required = {
        "case_id",
        "name",
        "evidence_class",
        "setup",
        "expected_auditor_result",
        "actual_auditor_result",
        "violation",
        "metric_effect",
        "business_effect",
        "caveat",
        "required_correction",
        "observed_or_injected",
        "model_results",
    }

    for row in payload["cases"]:
        assert required <= set(row)

        assert len(row["model_results"]) == 2
