"""Observable ML features for Zombie Escape risk prediction."""

from __future__ import annotations

import random
from math import sqrt

import pandas as pd

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    GridPosition,
    TerrainType,
)

FEATURE_COLUMNS = (
    "row_norm",
    "column_norm",
    "edge_distance_norm",
    "speed_multiplier",
    "observed_risk",
    "neighbor_observed_mean",
    "neighbor_observed_max",
    "neighbor_observed_min",
    "neighbor_observed_std",
    "traversable_neighbor_fraction",
    "local_building_fraction",
    "local_arterial_fraction",
    "terrain_local_road",
    "terrain_arterial",
    "terrain_slow_terrain",
    "terrain_open_space",
)

LABEL_COLUMN = "true_risk"

FORBIDDEN_INFERENCE_COLUMNS = (
    "true_risk",
    "hidden_risk",
    "hidden_hotspot",
    "oracle_risk",
)


def observable_features(
    city: GeneratedCity,
    position: GridPosition,
) -> dict[str, float]:
    """Extract features available to headline methods at inference time."""
    cell = city.cell(position)

    if cell.terrain is TerrainType.BUILDING:
        raise ValueError("ML features are defined only for traversable cells")

    neighbors = city.traversable_neighbors(position)

    neighbor_risks = [city.cell(neighbor).observed_risk for neighbor in neighbors]

    if neighbor_risks:
        mean_risk = sum(neighbor_risks) / len(neighbor_risks)

        maximum = max(neighbor_risks)

        minimum = min(neighbor_risks)

        variance = sum((risk - mean_risk) ** 2 for risk in neighbor_risks) / len(neighbor_risks)

        standard_deviation = sqrt(variance)
    else:
        mean_risk = cell.observed_risk
        maximum = cell.observed_risk
        minimum = cell.observed_risk
        standard_deviation = 0.0

    local_positions = []

    for row in range(
        max(
            0,
            position.row - 1,
        ),
        min(
            city.grid.rows,
            position.row + 2,
        ),
    ):
        for column in range(
            max(
                0,
                position.column - 1,
            ),
            min(
                city.grid.columns,
                position.column + 2,
            ),
        ):
            local_positions.append(
                GridPosition(
                    row,
                    column,
                )
            )

    local_cells = [city.cell(item) for item in local_positions]

    local_building_fraction = sum(
        1 for item in local_cells if (item.terrain is TerrainType.BUILDING)
    ) / len(local_cells)

    local_arterial_fraction = sum(
        1 for item in local_cells if (item.terrain is TerrainType.ARTERIAL)
    ) / len(local_cells)

    speed = {
        TerrainType.LOCAL_ROAD: 1.0,
        TerrainType.ARTERIAL: 1.35,
        TerrainType.SLOW_TERRAIN: 0.70,
        TerrainType.OPEN_SPACE: 0.85,
    }[cell.terrain]

    row_denominator = max(
        1,
        city.grid.rows - 1,
    )

    column_denominator = max(
        1,
        city.grid.columns - 1,
    )

    edge_distance = min(
        position.row,
        position.column,
        (city.grid.rows - 1 - position.row),
        (city.grid.columns - 1 - position.column),
    )

    edge_denominator = max(
        1.0,
        min(
            city.grid.rows,
            city.grid.columns,
        )
        / 2.0,
    )

    return {
        "row_norm": (position.row / row_denominator),
        "column_norm": (position.column / column_denominator),
        "edge_distance_norm": (edge_distance / edge_denominator),
        "speed_multiplier": speed,
        "observed_risk": (cell.observed_risk),
        "neighbor_observed_mean": mean_risk,
        "neighbor_observed_max": maximum,
        "neighbor_observed_min": minimum,
        "neighbor_observed_std": standard_deviation,
        "traversable_neighbor_fraction": (len(neighbors) / 4.0),
        "local_building_fraction": (local_building_fraction),
        "local_arterial_fraction": (local_arterial_fraction),
        "terrain_local_road": float(cell.terrain is TerrainType.LOCAL_ROAD),
        "terrain_arterial": float(cell.terrain is TerrainType.ARTERIAL),
        "terrain_slow_terrain": float(cell.terrain is TerrainType.SLOW_TERRAIN),
        "terrain_open_space": float(cell.terrain is TerrainType.OPEN_SPACE),
    }


def training_rows_for_city(
    city: GeneratedCity,
    *,
    split: str,
    synthetic_city_index: int,
    sample_seed: int,
    sample_size: int,
) -> list[dict[str, object]]:
    """Sample deterministic traversable cells with true-risk labels."""
    positions = list(city.traversable_positions())

    rng = random.Random(sample_seed)

    selected = rng.sample(
        positions,
        min(
            sample_size,
            len(positions),
        ),
    )

    selected.sort()

    records = []

    for position in selected:
        features = observable_features(
            city,
            position,
        )

        record: dict[
            str,
            object,
        ] = {
            "split": split,
            "synthetic_city_index": (synthetic_city_index),
            "synthetic_seed": (city.definition.seed),
            "style": (city.city_id.value),
            "row": position.row,
            "column": position.column,
            **features,
            LABEL_COLUMN: (city.cell(position).true_risk),
        }

        records.append(record)

    return records


def showcase_feature_frame(
    city: GeneratedCity,
) -> tuple[
    pd.DataFrame,
    tuple[GridPosition, ...],
]:
    """Build an inference frame for every traversable showcase cell."""
    positions = city.traversable_positions()

    rows = [
        observable_features(
            city,
            position,
        )
        for position in positions
    ]

    frame = pd.DataFrame(
        rows,
        columns=list(FEATURE_COLUMNS),
    )

    return (
        frame,
        positions,
    )


def validate_no_feature_leakage() -> None:
    """Hard fail if hidden truth becomes an inference feature."""
    lower_features = {column.lower() for column in FEATURE_COLUMNS}

    leaked = [
        forbidden
        for forbidden in FORBIDDEN_INFERENCE_COLUMNS
        if forbidden.lower() in lower_features
    ]

    if leaked:
        raise RuntimeError("Hidden-risk leakage detected: " + ", ".join(leaked))

    if LABEL_COLUMN in FEATURE_COLUMNS:
        raise RuntimeError("true_risk label is present in FEATURE_COLUMNS")
