from __future__ import annotations

import json

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.config import (
    repository_root,
)


def test_project_contract_remains_frozen() -> None:
    root = repository_root()

    contract_path = (
        root / "assets" / "p27_prediction_time_integrity_auditor" / "project_contract.json"
    )

    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["contract_status"] == "FROZEN_BEFORE_EXPERIMENT"

    identity = contract["project_identity"]

    assert identity["package_id"] == "p27_prediction_time_integrity_auditor"

    assert identity["branch"] == "project/p27-prediction-time-integrity-auditor"

    assert identity["cli_namespace"] == "prediction-integrity"

    assert contract["reproducibility"]["seed"] == 1729

    assert len(contract["leakage_cases"]) == 5
    assert len(contract["model_contract"]["models"]) == 2

    by_name = {
        item["feature_name"]: item
        for item in contract["prediction_time_feature_contract"]["features"]
    }

    assert by_name["duration"]["availability_class"] == "DURING_ACTION"
    assert by_name["duration"]["deployment_allowed"] is False

    assert by_name["campaign"]["availability_class"] == "UNKNOWN"
    assert by_name["campaign"]["deployment_allowed"] is False


def test_no_benchmark_data_has_been_added() -> None:
    root = repository_root()

    raw_root = root / "data" / "p27_prediction_time_integrity_auditor"

    assert not raw_root.exists()


def test_no_step1_analytics_modules_exist_yet() -> None:
    root = repository_root()

    package_root = (
        root / "src" / "linkedin_visual_labs" / "projects" / "p27_prediction_time_integrity_auditor"
    )

    forbidden = {
        "data.py",
        "splits.py",
        "preprocessing.py",
        "leakage_cases.py",
        "modeling.py",
        "metrics.py",
        "auditor.py",
        "business_impact.py",
        "validation.py",
        "visualization.py",
        "video.py",
        "dashboard.py",
        "publication.py",
        "pipeline.py",
    }

    existing = {path.name for path in package_root.glob("*.py")}

    assert existing.isdisjoint(forbidden)
