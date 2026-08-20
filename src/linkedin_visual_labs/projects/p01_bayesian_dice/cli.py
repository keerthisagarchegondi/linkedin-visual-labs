"""CLI registration for Bayesian Dice Detective."""

from __future__ import annotations

import typer

from linkedin_visual_labs.projects.p01_bayesian_dice.config import (
    DEFAULT_CONFIG_PATH,
)

app = typer.Typer(
    name="dice",
    help="Bayesian Dice Detective project commands.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def dice(
    ctx: typer.Context,
) -> None:
    """Can AI tell a loaded die from a fair die?"""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def default_config_path() -> str:
    """Return the repository-relative default Dice configuration path."""
    return DEFAULT_CONFIG_PATH.as_posix()
