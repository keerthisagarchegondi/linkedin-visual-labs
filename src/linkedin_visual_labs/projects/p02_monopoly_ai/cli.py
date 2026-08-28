"""CLI namespace for Project 3."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    DEFAULT_CONFIG_PATH,
    load_config,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.pipeline import (
    validate_scaffold,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.tournament import (
    TournamentRunConfig,
    run_tournament,
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


@app.command("tournament")
def tournament_command(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            help="Path to the Project 3 YAML contract.",
        ),
    ] = DEFAULT_CONFIG_PATH,
    games: Annotated[
        int | None,
        typer.Option(
            "--games",
            min=1,
            help=("Override game count. Defaults to canonical config."),
        ),
    ] = None,
    master_seed: Annotated[
        int | None,
        typer.Option(
            "--master-seed",
            min=0,
            help=("Override master seed. Defaults to canonical config."),
        ),
    ] = None,
    output_directory: Annotated[
        Path,
        typer.Option(
            "--output-directory",
            help="Tournament artifact directory.",
        ),
    ] = Path("outputs/p02_monopoly_ai/data"),
    progress: Annotated[
        bool,
        typer.Option(
            "--progress/--no-progress",
            help="Show interactive tournament progress.",
        ),
    ] = True,
    progress_every: Annotated[
        int,
        typer.Option(
            "--progress-every",
            min=1,
            help="Print progress every N games.",
        ),
    ] = 100,
) -> None:
    """Run a deterministic bounded tournament."""

    project_config = load_config(config)

    game_count = games if games is not None else project_config.tournament.game_count

    seed = master_seed if master_seed is not None else project_config.tournament.master_seed

    artifacts = run_tournament(
        config=project_config,
        run_config=TournamentRunConfig(
            game_count=game_count,
            master_seed=seed,
            output_directory=output_directory,
            show_progress=progress,
            progress_every=progress_every,
        ),
    )

    typer.echo(f"games={game_count}")

    typer.echo(f"master_seed={seed}")

    typer.echo(f"results_csv={artifacts.results_csv}")

    typer.echo(f"summary_json={artifacts.summary_json}")

    typer.echo(f"representative_json={artifacts.representative_json}")

    typer.echo(f"representative_events_json={artifacts.representative_events_json}")
