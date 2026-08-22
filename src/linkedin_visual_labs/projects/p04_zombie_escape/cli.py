"""CLI for Project 2 — Zombie Escape."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

import typer

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    generate_all_cities,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_pipeline import (
    run_dl_pipeline,
    solve_all_routes_from_persisted_predictions,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_pipeline import (
    run_ml_pipeline,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    CityId,
    MethodId,
)
from linkedin_visual_labs.projects.p04_zombie_escape.pipeline import (
    build_pipeline_context,
)
from linkedin_visual_labs.projects.p04_zombie_escape.serialization import (
    write_generated_cities,
)

CLI_HELP = "Dynamic Zombie Escape Planner — Dijkstra vs ML vs Deep Learning"

app = typer.Typer(
    name="zombie",
    help=CLI_HELP,
    invoke_without_command=True,
    no_args_is_help=False,
)

_FUTURE_COMMANDS = (
    "evaluate",
    "render-previews",
    "render-video",
    "validate",
    "run-all",
)


@app.callback()
def zombie_callback(
    ctx: typer.Context,
) -> None:
    """Show Project 2 help when no zombie subcommand is supplied."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _doctor_payload() -> dict[str, object]:
    """Return the typed Project 2 contract summary."""
    context = build_pipeline_context()

    config = context.configuration

    return {
        "project_id": config.project.project_id,
        "authoritative": config.project.authoritative,
        "cities": [city.value for city in CityId],
        "methods": [method.value for method in MethodId],
        "grid": {
            "rows": config.experiment.grid.rows,
            "columns": config.experiment.grid.columns,
            "movement": (config.experiment.grid.movement.value),
        },
        "video": {
            "width_px": config.video.width_px,
            "height_px": config.video.height_px,
            "frame_rate": config.video.frame_rate,
            "duration_seconds": (config.video.duration_seconds),
            "frame_count": config.video.frame_count,
        },
        "output_root": str(config.outputs.root),
    }


@app.command("doctor")
def doctor_command() -> None:
    """Validate and summarize the typed Project 2 contract."""
    typer.echo(
        json.dumps(
            _doctor_payload(),
            indent=2,
            sort_keys=True,
        )
    )


@app.command("generate-cities")
def generate_cities_command() -> None:
    """Generate deterministic showcase cities."""
    context = build_pipeline_context()

    output = write_generated_cities(
        context,
        generate_all_cities(context.configuration),
    )

    typer.echo(str(output))


@app.command("train-ml")
def train_ml_command() -> None:
    """Run the deterministic classical ML risk pipeline."""
    result = run_ml_pipeline(build_pipeline_context())

    typer.echo(
        json.dumps(
            {
                "training_dataset": str(result.training_dataset_path),
                "model": str(result.model_path),
                "metadata": str(result.metadata_path),
                "predicted_risk_maps": str(result.predicted_risk_maps_path),
                "routes": str(result.routes_path),
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("train-dl")
def train_dl_command() -> None:
    """Train deterministic CNN, predict risk, and generate DL routes."""
    result = run_dl_pipeline(build_pipeline_context())

    typer.echo(
        json.dumps(
            {
                "checkpoint": str(result.checkpoint_path),
                "metadata": str(result.metadata_path),
                "predicted_risk_maps": str(result.predicted_risk_maps_path),
                "routes": str(result.routes_path),
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("solve-routes")
def solve_routes_command() -> None:
    """Rebuild all headline routes from persisted prediction maps."""
    output = solve_all_routes_from_persisted_predictions(build_pipeline_context())

    typer.echo(str(output))


def _reserved_command(
    command: str,
) -> None:
    """Fail clearly for a command reserved for a later Project 2 step."""
    raise typer.BadParameter(
        f"{command!r} is reserved and will be implemented in a later Project 2 step"
    )


@app.command("evaluate")
def evaluate_command() -> None:
    """Reserved for Revised Step 7."""
    _reserved_command("evaluate")


@app.command("render-previews")
def render_previews_command() -> None:
    """Reserved for Revised Step 8."""
    _reserved_command("render-previews")


@app.command("render-video")
def render_video_command() -> None:
    """Reserved for Revised Step 9."""
    _reserved_command("render-video")


@app.command("validate")
def validate_command() -> None:
    """Reserved for later Project 2 validation."""
    _reserved_command("validate")


@app.command("run-all")
def run_all_command() -> None:
    """Reserved for final Project 2 pipeline integration."""
    _reserved_command("run-all")


def build_parser() -> argparse.ArgumentParser:
    """Build the programmatic Project 2 argument parser."""
    parser = argparse.ArgumentParser(
        prog="zombie",
        description=CLI_HELP,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    for command in (
        "doctor",
        "generate-cities",
        "train-ml",
        "train-dl",
        "solve-routes",
        *_FUTURE_COMMANDS,
    ):
        subparsers.add_parser(command)

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run Project 2 programmatically."""
    parser = build_parser()

    args = parser.parse_args(argv)

    if args.command == "doctor":
        print(
            json.dumps(
                _doctor_payload(),
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    if args.command == "generate-cities":
        context = build_pipeline_context()

        print(
            write_generated_cities(
                context,
                generate_all_cities(context.configuration),
            )
        )

        return 0

    if args.command == "train-ml":
        ml_result = run_ml_pipeline(build_pipeline_context())

        print(ml_result.metadata_path)

        return 0

    if args.command == "train-dl":
        dl_result = run_dl_pipeline(build_pipeline_context())

        print(dl_result.metadata_path)

        return 0

    if args.command == "solve-routes":
        print(solve_all_routes_from_persisted_predictions(build_pipeline_context()))

        return 0

    if args.command in _FUTURE_COMMANDS:
        parser.error(
            f"{args.command!r} is reserved and will be implemented in a later Project 2 step"
        )

    parser.error(f"unsupported command: {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
