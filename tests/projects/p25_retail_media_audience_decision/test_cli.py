"""Project 4 CLI registration tests."""

from __future__ import annotations

from typer.testing import CliRunner

from linkedin_visual_labs.cli import app

runner = CliRunner()


def test_root_cli_registers_retail_media_namespace() -> None:
    """The shared root CLI must expose Project 4."""

    result = runner.invoke(
        app,
        ["--help"],
    )

    assert result.exit_code == 0
    assert "retail-media" in result.stdout


def test_retail_media_help_lists_frozen_commands() -> None:
    """Project 4 must expose every frozen stage command."""

    result = runner.invoke(
        app,
        [
            "retail-media",
            "--help",
        ],
    )

    assert result.exit_code == 0

    for command in (
        "fetch-data",
        "validate-data",
        "build-features",
        "segment",
        "train-uplift",
        "measure",
        "build-funnel",
        "attribute",
        "recommend",
        "build-dashboard",
        "validate-outputs",
        "run-all",
    ):
        assert command in result.stdout
