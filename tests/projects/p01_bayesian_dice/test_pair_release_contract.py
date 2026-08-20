"""Release-contract tests for the authoritative Project 1 pair experiment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    PAIR_CASE_IDS,
    case_display_label,
    load_dice_config,
)

EXPECTED_CASE_LABELS = {
    "UU": "Unloaded - Unloaded",
    "UP": "Unloaded - Partially Loaded",
    "UF": "Unloaded - Fully Loaded",
    "PP": "Partially Loaded - Partially Loaded",
    "PF": "Partially Loaded - Fully Loaded",
    "FF": "Fully Loaded - Fully Loaded",
}


def test_release_contract_has_six_canonical_cases() -> None:
    assert tuple(EXPECTED_CASE_LABELS) == PAIR_CASE_IDS


def test_release_contract_has_descriptive_viewer_labels() -> None:
    for case_id in PAIR_CASE_IDS:
        assert EXPECTED_CASE_LABELS[case_id] == case_display_label(case_id)


def test_release_contract_uses_authoritative_pair_experiment() -> None:
    config = load_dice_config()

    experiment = config.pair_experiment

    assert experiment.authoritative is True
    assert experiment.roll_count_per_case == 10_000


def test_pair_video_schedule_cli_is_warning_free_and_valid() -> None:
    command = (
        sys.executable,
        "-m",
        ("linkedin_visual_labs.projects.p01_bayesian_dice.pair_video"),
        "schedule",
    )

    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stderr == ""

    payload = json.loads(completed.stdout)

    assert payload["frame_rate"] == 30

    assert payload["frame_count"] == 1_350

    assert payload["first_roll"] == 1

    assert payload["last_roll"] == 10_000

    assert len(payload["roll_indices"]) == 1_350


def test_project_documentation_exists() -> None:
    path = Path("docs/projects/p01_bayesian_dice.md")

    assert path.is_file()

    text = path.read_text(encoding="utf-8")

    assert "How many rolls before knowing whether a pair of dice is loaded?" in text

    assert "Stable Roll" in text
    assert "60,000 observed pair sums" in text
    assert "1080 x 1080" in text
