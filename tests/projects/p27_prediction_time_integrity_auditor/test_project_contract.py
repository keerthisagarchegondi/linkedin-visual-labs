from __future__ import annotations

import json
import subprocess

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


def test_step1_raw_source_is_local_ignored_and_untracked() -> None:
    root = repository_root()

    raw_root = root / "data" / "p27_prediction_time_integrity_auditor" / "raw"

    archive = raw_root / "bank+marketing.zip"
    csv_path = raw_root / "bank-additional-full.csv"

    assert raw_root.is_dir()
    assert archive.is_file()
    assert csv_path.is_file()

    for path in (archive, csv_path):
        ignored = subprocess.run(
            [
                "git",
                "check-ignore",
                "-q",
                "--",
                str(path),
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )

        assert ignored.returncode == 0

    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "--",
            "data/p27_prediction_time_integrity_auditor",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )

    assert tracked.returncode == 0
    assert tracked.stdout.strip() == ""


def test_step1_module_boundary_is_exact() -> None:
    root = repository_root()

    package_root = (
        root / "src" / "linkedin_visual_labs" / "projects" / "p27_prediction_time_integrity_auditor"
    )

    required_step1_modules = {
        "__init__.py",
        "cli.py",
        "config.py",
        "contracts.py",
        "data.py",
        "models.py",
    }

    existing = {path.name for path in package_root.glob("*.py")}

    assert required_step1_modules <= existing

    forbidden_step2_plus_modules = {
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

    assert existing.isdisjoint(forbidden_step2_plus_modules)
