"""CLI registration for Dynamic Zombie Escape Planner."""

from __future__ import annotations

import typer

app = typer.Typer(
    name="zombie",
    help="Dynamic Zombie Escape Planner project commands.",
    invoke_without_command=True,
    no_args_is_help=False,
)


@app.callback()
def zombie(
    ctx: typer.Context,
) -> None:
    """Shortest, safest, fastest—choose your route."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
