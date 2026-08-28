"""Project 3 CLI scaffold tests."""

from typer.testing import CliRunner

from linkedin_visual_labs.projects.p02_monopoly_ai.cli import (
    app,
)

runner = CliRunner()


def test_monopoly_help() -> None:
    result = runner.invoke(
        app,
        [
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Monopoly AI Landlord Arena" in result.stdout


def test_contract_command() -> None:
    result = runner.invoke(
        app,
        [
            "contract",
        ],
    )

    assert result.exit_code == 0

    assert "board_spaces=40" in result.stdout
    assert "purchasable_assets=28" in result.stdout
    assert "strategies=4" in result.stdout
    assert "tournament_games=10000" in result.stdout
