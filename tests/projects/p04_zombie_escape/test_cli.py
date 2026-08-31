"""CLI scaffold tests for Project 2."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
from typer import Typer

from linkedin_visual_labs.projects.p04_zombie_escape.cli import (
    CLI_HELP,
    app,
    main,
)


def test_project_cli_exposes_shared_typer_app() -> None:
    assert isinstance(
        app,
        Typer,
    )


def test_project_cli_preserves_repository_help_identity() -> None:
    assert "Dynamic Zombie Escape Planner" in CLI_HELP

    assert "Dijkstra vs ML vs Deep Learning" in CLI_HELP


def test_programmatic_doctor_returns_typed_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(("doctor",)) == 0

    captured = capsys.readouterr()

    assert captured.err == ""

    payload = json.loads(captured.out)

    assert payload["project_id"] == "p04_zombie_escape"

    assert payload["authoritative"] is True

    assert payload["cities"] == [
        "phoenix",
        "new_york",
        "chicago",
    ]

    assert payload["methods"] == [
        "dijkstra",
        "ml",
        "dl",
    ]

    assert payload["grid"] == {
        "columns": 36,
        "movement": "four_neighbor",
        "rows": 36,
    }

    assert payload["video"] == {
        "duration_seconds": 60.0,
        "frame_count": 1_800,
        "frame_rate": 30,
        "height_px": 1080,
        "width_px": 1080,
    }


def test_repository_cli_can_execute_zombie_doctor() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "linkedin_visual_labs",
            "zombie",
            "doctor",
        ),
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stderr == ""

    payload = json.loads(completed.stdout)

    assert payload["project_id"] == "p04_zombie_escape"

    assert payload["authoritative"] is True

    assert payload["cities"] == [
        "phoenix",
        "new_york",
        "chicago",
    ]

    assert payload["methods"] == [
        "dijkstra",
        "ml",
        "dl",
    ]

    assert payload["video"]["frame_count"] == 1_800


def test_repository_cli_exposes_zombie_namespace() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "linkedin_visual_labs",
            "--help",
        ),
        check=True,
        capture_output=True,
        text=True,
    )

    combined = completed.stdout + completed.stderr

    assert "zombie" in combined.lower()


def test_zombie_without_subcommand_shows_help_successfully() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "linkedin_visual_labs",
            "zombie",
        ),
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0

    combined = completed.stdout + completed.stderr

    assert "Dynamic Zombie Escape Planner" in combined

    assert "doctor" in combined


def test_generate_cities_command_is_operational() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-m",
            "linkedin_visual_labs",
            "zombie",
            "generate-cities",
        ),
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stderr == ""

    normalized_stdout = completed.stdout.replace("\\", "/")
    assert "outputs/p04_zombie_escape/data/cities.json" in normalized_stdout
