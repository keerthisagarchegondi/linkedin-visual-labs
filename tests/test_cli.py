"""Tests for the top-level LinkedIn Visual Labs CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from linkedin_visual_labs.cli import app

runner = CliRunner()


def test_top_level_help_lists_shared_commands() -> None:
    result = runner.invoke(
        app,
        ["--help"],
    )

    assert result.exit_code == 0
    assert "doctor" in result.stdout
    assert "version" in result.stdout
    assert "dice" in result.stdout
    assert "zombie" in result.stdout
    assert "monopoly" in result.stdout


def test_version_command() -> None:
    result = runner.invoke(
        app,
        ["version"],
    )

    assert result.exit_code == 0
    assert "linkedin-visual-labs" in result.stdout
    assert "0.1.0" in result.stdout


def test_dice_help_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "dice",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Bayesian Dice Detective" in result.stdout


def test_zombie_help_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "zombie",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Dynamic Zombie Escape Planner" in result.stdout


def test_monopoly_help_is_registered() -> None:
    result = runner.invoke(
        app,
        [
            "monopoly",
            "--help",
        ],
    )

    assert result.exit_code == 0
    assert "Monopoly AI Landlord Arena" in result.stdout


def test_dice_without_command_shows_help() -> None:
    result = runner.invoke(
        app,
        ["dice"],
    )

    assert result.exit_code == 0
    assert "Bayesian Dice Detective" in result.stdout


def test_zombie_without_command_shows_help() -> None:
    result = runner.invoke(
        app,
        ["zombie"],
    )

    assert result.exit_code == 0
    assert "Dynamic Zombie Escape Planner" in result.stdout


def test_monopoly_without_command_shows_help() -> None:
    result = runner.invoke(
        app,
        ["monopoly"],
    )

    assert result.exit_code == 0
    assert "Monopoly AI Landlord Arena" in result.stdout


def test_unknown_command_fails() -> None:
    result = runner.invoke(
        app,
        ["not-a-project"],
    )

    assert result.exit_code != 0
