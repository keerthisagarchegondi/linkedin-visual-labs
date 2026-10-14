from __future__ import annotations

import json

import pytest
from _pytest.capture import CaptureFixture

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.cli import main


@pytest.mark.parametrize("command", ["audit-environment", "validate-inputs", "show-contract"])
def test_step_one_cli_commands(command: str, capsys: CaptureFixture[str]) -> None:
    assert main([command]) == 0
    assert json.loads(capsys.readouterr().out)["project_id"] == "p29_anomaly_point_adjustment_audit"
