"""Exercise the real top-level commerce registration and configuration command."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from linkedin_visual_labs.cli import app

runner = CliRunner()


def test_commerce_registration() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "commerce" in result.stdout


def test_commerce_help() -> None:
    for args in (["commerce", "--help"], ["commerce"]):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        assert "Quick-Commerce" in result.stdout
        assert "doctor" in result.stdout
        assert "run-all" in result.stdout


def test_commerce_doctor() -> None:
    result = runner.invoke(app, ["commerce", "doctor"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["project_id"] == "p25_quick_commerce_control_tower"
    assert payload["data"]["holdout_days"] == 28
    assert payload["labor"]["classification"] == "illustrative"


def test_commerce_invalid_config() -> None:
    result = runner.invoke(app, ["commerce", "doctor", "--config", "missing.yaml"])
    assert result.exit_code == 1
    assert "Configuration validation failed" in result.output


def test_run_all_invalid_configuration_fails() -> None:
    result = runner.invoke(app, ["commerce", "run-all", "--config", "missing.yaml"])
    assert result.exit_code == 1
    assert "Release pipeline failed" in result.output
