"""CLI for Retail Media Audience Decision Studio."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.pipeline import (
    fetch_sources,
    validate_cached_sources,
)

app = typer.Typer(
    name="retail-media",
    help="Build and validate the Retail Media Audience Decision Studio.",
    no_args_is_help=True,
)

console = Console()


def _repository_root() -> Path:
    """Resolve the repository root from this package."""

    candidate = Path.cwd().resolve()

    for path in (
        candidate,
        *candidate.parents,
    ):
        if (path / "pyproject.toml").is_file() and (path / "src" / "linkedin_visual_labs").is_dir():
            return path

    raise RuntimeError("Could not locate linkedin-visual-labs repository root.")


@app.command("fetch-data")
def fetch_data(
    source: str = typer.Option(
        "all",
        "--source",
        help=("Source to fetch: all, hillstrom, dunnhumby, criteo, or retailrocket."),
    ),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Require existing raw caches; never use the network.",
    ),
    criteo_max_rows: int = typer.Option(
        2_000_000,
        "--criteo-max-rows",
        min=1,
        help="Deterministic upper bound for normalized Criteo rows.",
    ),
) -> None:
    """Fetch and normalize one or all governed evidence sources."""

    results = fetch_sources(
        repository_root=_repository_root(),
        source=source,
        offline=offline,
        criteo_max_rows=criteo_max_rows,
    )

    table = Table(title="Project 4 Source Ingestion")

    table.add_column("Source")
    table.add_column("Evidence class")
    table.add_column("Rows", justify="right")
    table.add_column("Result")

    for result in results:
        table.add_row(
            result.source_id.value,
            result.evidence_class.value,
            f"{result.row_count:,}",
            "PASS",
        )

    console.print(table)
    console.print("FETCH_DATA=PASS")


@app.command("validate-data")
def validate_data() -> None:
    """Independently validate all four normalized evidence sources."""

    counts = validate_cached_sources(repository_root=_repository_root())

    table = Table(title="Project 4 Independent Source Validation")

    table.add_column("Source")
    table.add_column("Rows", justify="right")
    table.add_column("Result")

    for source, count in counts.items():
        table.add_row(
            source,
            f"{count:,}",
            "PASS",
        )

    console.print(table)
    console.print("NO_FALSE_IDENTITY_JOINS=PASS")
    console.print("SOURCE_PROVENANCE=PASS")
    console.print("VALIDATE_DATA=PASS")


@app.command("build-features")
def build_features() -> None:
    """Build retail customer features and true RFM."""

    console.print("build-features: implementation begins in Project 4 — Step 3.")


@app.command("segment")
def segment() -> None:
    """Build ML segments and governed audiences."""

    console.print("segment: implementation begins in Project 4 — Step 4.")


@app.command("train-uplift")
def train_uplift() -> None:
    """Train and evaluate uplift models."""

    console.print("train-uplift: implementation begins in Project 4 — Step 5.")


@app.command("measure")
def measure() -> None:
    """Measure randomized treatment incrementality."""

    console.print("measure: implementation begins in Project 4 — Step 5.")


@app.command("build-funnel")
def build_funnel() -> None:
    """Build the behavioral conversion funnel."""

    console.print("build-funnel: implementation begins in Project 4 — Step 6.")


@app.command("attribute")
def attribute() -> None:
    """Run the five governed attribution methods."""

    console.print("attribute: implementation begins in Project 4 — Step 7.")


@app.command("recommend")
def recommend() -> None:
    """Build governed activation recommendations."""

    console.print("recommend: implementation begins in Project 4 — Step 8.")


@app.command("build-dashboard")
def build_dashboard() -> None:
    """Build the canonical dashboard."""

    console.print("build-dashboard: implementation begins in Project 4 — Step 9.")


@app.command("validate-outputs")
def validate_outputs() -> None:
    """Validate completed Project 4 outputs."""

    console.print("validate-outputs: implementation begins in Project 4 — Step 10.")


@app.command("run-all")
def run_all() -> None:
    """Run the completed Project 4 pipeline."""

    console.print("run-all: implementation begins in Project 4 — Step 10.")
