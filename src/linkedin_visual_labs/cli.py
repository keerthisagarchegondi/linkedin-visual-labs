"""Command-line interface for LinkedIn Visual Labs."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from linkedin_visual_labs import __version__

app = typer.Typer(
    add_completion=False,
    help="Build and run LinkedIn Visual Labs experiments.",
    no_args_is_help=True,
)
console = Console()


def _repository_root() -> Path:
    """Return the repository root for the editable src-layout installation."""
    return Path(__file__).resolve().parents[2]


@app.command()
def version() -> None:
    """Display the package version."""
    console.print(f"linkedin-visual-labs {__version__}")


@app.command()
def doctor() -> None:
    """Verify the shared Codespaces development environment."""
    repository_root = _repository_root()
    ffmpeg_path = shutil.which("ffmpeg")
    git_path = shutil.which("git")

    python_is_supported = sys.version_info[:2] == (3, 13)
    virtual_environment_is_active = Path(sys.prefix).name == ".venv"
    pyproject_exists = (repository_root / "pyproject.toml").is_file()

    checks: list[tuple[str, str, bool]] = [
        (
            "Python",
            sys.version.split()[0],
            python_is_supported,
        ),
        (
            "Python executable",
            sys.executable,
            virtual_environment_is_active,
        ),
        (
            "Repository root",
            str(repository_root),
            pyproject_exists,
        ),
        (
            "Git",
            git_path or "not found",
            git_path is not None,
        ),
        (
            "FFmpeg",
            ffmpeg_path or "not found",
            ffmpeg_path is not None,
        ),
    ]

    table = Table(title="LinkedIn Visual Labs Environment Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Detected value")
    table.add_column("Result")

    failed = False

    for name, detected_value, passed in checks:
        result = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        table.add_row(name, detected_value, result)
        failed = failed or not passed

    console.print(table)

    if failed:
        raise typer.Exit(code=1)

    console.print("[bold green]Environment is ready.[/bold green]")


if __name__ == "__main__":
    app()
