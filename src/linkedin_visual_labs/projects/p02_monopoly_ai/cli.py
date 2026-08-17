"""CLI registration for Monopoly AI Landlord Arena."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="monopoly",
    help="Monopoly AI Landlord Arena project commands.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def monopoly(
    ctx: typer.Context,
) -> None:
    """Four landlord strategies. 10,000 games. Which one survives?"""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
