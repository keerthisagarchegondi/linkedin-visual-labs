"Commerce configuration, data preparation, and four-model forecasting commands."

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from linkedin_visual_labs.common.validation import ValidationError
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    DEFAULT_CONFIG_PATH,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    acquire_data,
    prepare_data,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    build_pipeline_context,
)

app = typer.Typer(
    name="commerce",
    help=(
        "Quick-Commerce Forecast Model Arena & Network Optimizer — evidenc"
        "e, operations and final media."
    ),
    invoke_without_command=True,
)


@app.command(name="run-all")
def run_all_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
) -> None:
    """Run the real M5 pipeline, fresh leakage proof, operations, media and validation."""
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.release import run_all

    try:
        path = run_all(build_pipeline_context(config))
    except (ValidationError, OSError, ValueError, KeyError, AssertionError) as exc:
        typer.echo(f"Release pipeline failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"PUBLIC REAL M5; complete pipeline validated: {path}")


@app.command(name="optimize")
def optimize_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
) -> None:
    "Run illustrative labor scenarios and synthetic inventory evidence; no rendering."
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.operations import (
        run_operations,
    )

    try:
        output = run_operations(build_pipeline_context(config))
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Operations failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"ILLUSTRATIVE LABOR; SYNTHETIC INVENTORY; RETROSPECTIVE SELECTION: {output}")


@app.callback()
def commerce_callback(ctx: typer.Context) -> None:
    """Show help without starting analytics or creating outputs."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command()
def doctor(
    config: Annotated[
        Path, typer.Option("--config", help="Repository-local YAML configuration.")
    ] = (DEFAULT_CONFIG_PATH),
) -> None:
    "Validate and display settings; no ingestion, fitting, or rendering."
    try:
        context = build_pipeline_context(config)
    except (ValidationError, OSError) as exc:
        typer.echo(f"Configuration validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(context.configuration.model_dump(mode="json"), indent=2, sort_keys=True))


@app.command(name="acquire-data")
def acquire_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    local_directory: Annotated[Path | None, typer.Option("--local-directory")] = None,
) -> None:
    "Download or verify the two pinned real M5 files; optional verified offline local input."
    try:
        records = acquire_data(build_pipeline_context(config), local_directory)
    except (ValidationError, OSError) as exc:
        typer.echo(f"Real-data acquisition failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for record in records:
        typer.echo(f"Verified {record.filename}: sha256={record.sha256} bytes={record.size_bytes}")


@app.command(name="prepare-data")
def prepare_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    fixture: Annotated[
        bool, typer.Option("--fixture", help="Explicit synthetic test-only mode.")
    ] = False,
) -> None:
    "Aggregate the verified real cache, or isolate test-only fixture output."
    try:
        output = prepare_data(build_pipeline_context(config), fixture=fixture)
    except (ValidationError, OSError) as exc:
        typer.echo(f"Data preparation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{'SYNTHETIC TEST ONLY' if fixture else 'PUBLIC REAL M5'}: {output}")


@app.command(name="evaluate")
def evaluate_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    validation_record: Annotated[Path, typer.Option("--validation-record")] = Path(
        "outputs/p25_quick_commerce_control_tower/manifests/forecast_validation.json"
    ),
) -> None:
    "Evaluate frozen real predictions and publish retrospective governance evidence."
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.evaluation import (
        run_evaluation,
    )

    try:
        output = run_evaluation(build_pipeline_context(config), validation_record)
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Evaluation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"MEASURED BACKTEST; LOCAL SELECTION RETROSPECTIVE: {output}")


@app.command(name="forecast")
def forecast_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    fixture: Annotated[
        bool, typer.Option("--fixture", help="Explicit synthetic test-only mode.")
    ] = False,
) -> None:
    "Fit the four fixed methods against prepared data; no champion selection."
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.forecasting import (
        run_forecast,
    )

    try:
        output = run_forecast(build_pipeline_context(config), fixture=fixture)
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Forecasting failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"{'SYNTHETIC TEST ONLY' if fixture else 'PUBLIC REAL M5'}: {output}")


@app.command(name="render")
def render_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
) -> None:
    "Render verified real evidence into the final PNG, HTML and captioned videos."
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.rendering import (
        render_outputs,
    )

    try:
        path = render_outputs(build_pipeline_context(config))
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Rendering failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Verified final artifacts: {path}")


@app.command(name="validate")
def validate_command(
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
) -> None:
    "Fully decode final videos and reconcile rendered evidence without refitting."
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.rendering import (
        validate_outputs,
    )

    try:
        result = validate_outputs(build_pipeline_context(config))
    except (ValidationError, OSError, ValueError, KeyError) as exc:
        typer.echo(f"Output validation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2))
