"""CLI registration for Bayesian Dice Detective."""

from __future__ import annotations

import typer

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
