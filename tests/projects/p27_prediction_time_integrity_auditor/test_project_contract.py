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


def test_raw_source_remains_ignored_and_untracked() -> None:
    root = repository_root()

    raw_root = root / "data" / "p27_prediction_time_integrity_auditor" / "raw"

    for path in (
        raw_root / "bank+marketing.zip",
        raw_root / "bank-additional-full.csv",
    ):
        assert path.is_file()

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


def test_step2_module_boundary_is_exact() -> None:
    root = repository_root()

    package_root = (
        root / "src" / "linkedin_visual_labs" / "projects" / "p27_prediction_time_integrity_auditor"
    )

    required = {
        "__init__.py",
        "cli.py",
        "config.py",
        "contracts.py",
        "data.py",
        "metrics.py",
        "modeling.py",
        "models.py",
        "preprocessing.py",
        "splits.py",
    }

    existing = {path.name for path in package_root.glob("*.py")}

    assert required <= existing

    forbidden_step3_plus = {
        "leakage_cases.py",
        "auditor.py",
        "business_impact.py",
        "validation.py",
        "visualization.py",
        "video.py",
        "dashboard.py",
        "publication.py",
        "pipeline.py",
    }

    assert existing.isdisjoint(forbidden_step3_plus)
