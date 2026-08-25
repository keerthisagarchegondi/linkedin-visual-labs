"""CLI namespace for Project 3."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    DEFAULT_CONFIG_PATH,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.pipeline import (
    validate_scaffold,
)

app = typer.Typer(
    name="monopoly",
    help="Monopoly AI Landlord Arena",
    no_args_is_help=False,
)


@app.callback(
    invoke_without_command=True,
)
def main(
    ctx: typer.Context,
) -> None:
    """Monopoly AI Landlord Arena commands."""

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("contract")
def contract_command(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            help="Path to the Project 3 YAML contract.",
        ),
    ] = DEFAULT_CONFIG_PATH,
) -> None:
    """Validate and summarize the frozen Project 3 contract."""

    report = validate_scaffold(config)

    typer.echo(f"project_id={report.project_id}")
    typer.echo(f"board_spaces={report.board_spaces}")
    typer.echo(f"purchasable_assets={report.purchasable_assets}")
    typer.echo(f"strategies={report.strategy_count}")
    typer.echo(f"tournament_games={report.tournament_games}")
