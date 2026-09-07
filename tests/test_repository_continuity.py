"""Tests for the repository continuity contract and CLI tools."""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "contracts" / "repository_continuity.json"
CONTINUITY_GATE = ROOT / "scripts" / "continuity_gate.py"
UPDATE_CONTINUITY = ROOT / "scripts" / "update_continuity.py"
BASELINE_COMMIT = "0557673c790dc900db7293586ce96931ede40c96"


def test_continuity_manifest_contract() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "1.0"
    assert payload["environment_roots"] == {
        "windows": r"D:\linkedin-visual-labs-git\linkedin-visual-labs"
    }
    assert payload["repository"] == {
        "default_branch": "main",
        "key": "keerthisagarchegondi/linkedin-visual-labs",
        "origin_url": ("https://github.com/keerthisagarchegondi/linkedin-visual-labs.git"),
    }
    assert payload["minimum_baseline"] == {
        "commit": BASELINE_COMMIT,
        "label": "Project 3 complete: Monopoly AI Landlord Arena",
    }

    checkpoint = payload["checkpoint"]
    required_checkpoint_fields = {
        "project_number",
        "project_id",
        "project_name",
        "phase",
        "step",
        "substep",
        "status",
        "label",
    }

    assert isinstance(checkpoint, dict)
    assert set(checkpoint) == required_checkpoint_fields
    assert isinstance(checkpoint["project_number"], int)
    assert checkpoint["project_number"] >= 0
    assert checkpoint["status"] in {"in_progress", "complete", "blocked"}

    for key in required_checkpoint_fields - {"project_number"}:
        assert isinstance(checkpoint[key], str)
        assert checkpoint[key].strip()


def test_continuity_gate_help_is_operational() -> None:
    completed = subprocess.run(
        (sys.executable, str(CONTINUITY_GATE), "--help"),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--expected-branch" in completed.stdout
    assert "--expected-fingerprint" in completed.stdout
    assert "--allow-no-upstream" in completed.stdout
    assert "--allow-dirty" in completed.stdout
    assert completed.stderr == ""


def test_update_continuity_help_is_operational() -> None:
    completed = subprocess.run(
        (sys.executable, str(UPDATE_CONTINUITY), "--help"),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "--project-number" in completed.stdout
    assert "--project-id" in completed.stdout
    assert "--expected-branch" in completed.stdout
    assert "--substep" in completed.stdout
    assert "--status" in completed.stdout
    assert completed.stderr == ""


def test_environment_root_uses_contract_and_preserves_codespaces() -> None:
    namespace = runpy.run_path(str(CONTINUITY_GATE))
    resolve = namespace["expected_environment_root"]
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert resolve(payload, platform="nt") == Path(payload["environment_roots"]["windows"])
    payload["environment_roots"]["windows"] = r"E:\explicit-test-checkout"
    assert resolve(payload, platform="nt") == Path(r"E:\explicit-test-checkout")
    assert resolve(payload, platform="posix") == Path("/workspaces/linkedin-visual-labs")
    assert not namespace["same_path"](ROOT, Path(r"D:\linkedin-visual-labs"))


@pytest.mark.parametrize(
    "roots", [None, {}, {"windows": "relative/path"}, {"windows": "D:relative"}]
)
def test_invalid_windows_checkout_contract_fails_closed(roots: object) -> None:
    namespace = runpy.run_path(str(CONTINUITY_GATE))
    with pytest.raises(namespace["ContinuityError"], match="absolute checkout path"):
        namespace["expected_environment_root"]({"environment_roots": roots}, platform="nt")
