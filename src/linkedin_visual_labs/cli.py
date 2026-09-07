"""Top-level command-line interface for LinkedIn Visual Labs."""

from __future__ import annotations

import shutil
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from linkedin_visual_labs.projects import (
    commerce_app,
    dice_app,
    monopoly_app,
    zombie_app,
)

PACKAGE_DISTRIBUTION_NAME = "linkedin-visual-labs"

app = typer.Typer(
    name="linkedin-visual-labs",
    help="Build and run LinkedIn Visual Labs experiments.",
    no_args_is_help=True,
)

console = Console()

app.add_typer(commerce_app, name="commerce")

app.add_typer(
    dice_app,
    name="dice",
)

app.add_typer(
    zombie_app,
    name="zombie",
)

app.add_typer(
    monopoly_app,
    name="monopoly",
)


def package_version() -> str:
    """Return the installed package version."""
    try:
        return version(PACKAGE_DISTRIBUTION_NAME)
    except PackageNotFoundError:
        return "unknown"


def _find_repository_root(
    start: Path | None = None,
) -> Path | None:
    """Find the repository root using project markers."""
    current = (Path.cwd() if start is None else start).resolve()

    if current.is_file():
        current = current.parent

    for candidate in (
        current,
        *current.parents,
    ):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "linkedin_visual_labs"
        ).is_dir():
            return candidate

    return None


@app.command(name="version")
def version_command() -> None:
    """Display the package version."""
    console.print(f"{PACKAGE_DISTRIBUTION_NAME} {package_version()}")


@app.command()
def doctor() -> None:
    """Verify the shared Codespaces development environment."""
    repository_root = _find_repository_root()

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    expected_venv = repository_root / ".venv" if repository_root is not None else None

    git_path = shutil.which("git")
    ffmpeg_path = shutil.which("ffmpeg")

    python_ok = sys.version_info[:2] == (3, 13)

    executable_ok = (
        expected_venv is not None and Path(sys.prefix).resolve() == expected_venv.resolve()
    )

    repository_ok = repository_root is not None
    git_ok = git_path is not None
    ffmpeg_ok = ffmpeg_path is not None

    checks = [
        (
            "Python",
            python_version,
            python_ok,
        ),
        (
            "Python executable",
            (
                str(expected_venv / "bin" / "python")
                if expected_venv is not None
                else str(Path(sys.executable))
            ),
            executable_ok,
        ),
        (
            "Repository root",
            (str(repository_root) if repository_root is not None else "not found"),
            repository_ok,
        ),
        (
            "Git",
            git_path or "not found",
            git_ok,
        ),
        (
            "FFmpeg",
            ffmpeg_path or "not found",
            ffmpeg_ok,
        ),
    ]

    table = Table(title="LinkedIn Visual Labs Environment Doctor")

    table.add_column("Check")
    table.add_column("Detected value")
    table.add_column("Result")

    for check_name, detected, passed in checks:
        table.add_row(
            check_name,
            detected,
            "PASS" if passed else "FAIL",
        )

    console.print(table)

    if all(passed for _, _, passed in checks):
        console.print("Environment is ready.")
        return

    console.print("Environment verification failed.")

    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
