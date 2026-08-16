"""Foundation smoke tests."""

from __future__ import annotations

import sys

from typer.testing import CliRunner

from linkedin_visual_labs import __version__
from linkedin_visual_labs.cli import app

runner = CliRunner()


def test_python_version_is_313() -> None:
    """The project must run on the Python 3.13 family."""
    assert sys.version_info[:2] == (3, 13)


def test_package_version() -> None:
    """The package exposes its initial semantic version."""
    assert __version__ == "0.1.0"


def test_cli_help() -> None:
    """The module CLI starts successfully."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "LinkedIn Visual Labs" in result.stdout


def test_cli_version() -> None:
    """The version command returns the package version."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout
