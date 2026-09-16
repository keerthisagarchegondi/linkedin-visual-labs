from __future__ import annotations

import json
import subprocess
import sys

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.cli import (
    main,
)


def test_project_cli_environment_receipt(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["audit-environment"]) == 0

    receipt = json.loads(capsys.readouterr().out)

    assert receipt["status"] == "PASS"
    assert receipt["package_id"] == "p27_prediction_time_integrity_auditor"
    assert receipt["cli_namespace"] == "prediction-integrity"
    assert receipt["seed"] == 1729
    assert receipt["dataset_id"] == 222


def test_project_cli_show_config(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["show-config"]) == 0

    payload = json.loads(capsys.readouterr().out)

    assert payload["project_id"] == "p27_prediction_time_integrity_auditor"
    assert payload["seed"] == 1729
    assert payload["dataset_id"] == 222
    assert payload["preferred_file"] == "bank-additional-full.csv"
    assert payload["target"] == "y"
    assert payload["preserve_source_order"] is True

    assert payload["chronological_split"] == {
        "train": 0.70,
        "validation": 0.15,
        "test": 0.15,
    }

    assert payload["random_seed"] == 1729
    assert payload["random_stratify"] is True


def test_project_cli_without_command_prints_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([]) == 0

    output = capsys.readouterr().out

    assert "Prediction-Time Integrity Auditor" in output
    assert "audit-environment" in output
    assert "show-config" in output


def test_top_level_prediction_integrity_dispatch() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "linkedin_visual_labs",
            "prediction-integrity",
            "--help",
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "Prediction-Time Integrity Auditor" in result.stdout


def test_existing_top_level_help_still_works() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "linkedin_visual_labs",
            "--help",
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
