"""Synthetic supervised-learning data for Zombie Escape."""

from __future__ import annotations

import random
from dataclasses import replace
from math import exp
from pathlib import Path

import pandas as pd

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
    HiddenRiskHotspot,
    ZombieZone,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    CityDefinition,
    CityId,
    GridCell,
    GridPosition,
    TerrainType,
    ZombieProjectConfig,
)

SAMPLES_PER_SYNTHETIC_CITY = 128

_SPLIT_ORDER = (
    "training",
    "validation",
    "benchmark",
)


def generate_synthetic_training_city(
    config: ZombieProjectConfig,
    *,
    seed: int,
    style: CityId,
) -> GeneratedCity:
    """Generate one non-showcase procedural city for supervised learning."""
    rng = random.Random(seed)

    grid = config.experiment.grid

    base_definition = config.city(style)

    definition = replace(
        base_definition,
        seed=seed,
        display_name=(f"Synthetic {style.value} {seed}"),
    )

    if style is CityId.PHOENIX:
        building_probability = 0.10
        base_terrain = TerrainType.OPEN_SPACE
        road_spacing = rng.choice((5, 6, 7))
        visible_zone_count = 4
        hidden_hotspot_count = 7
    elif style is CityId.NEW_YORK:
        building_probability = 0.42
        base_terrain = TerrainType.LOCAL_ROAD
        road_spacing = rng.choice((3, 4))
        visible_zone_count = 3
        hidden_hotspot_count = 4
    else:
        building_probability = 0.24
        base_terrain = TerrainType.LOCAL_ROAD
        road_spacing = rng.choice((4, 5))
        visible_zone_count = 4
        hidden_hotspot_count = 5

    terrain: dict[
        GridPosition,
        TerrainType,
    ] = {}

    arterial_offset = rng.randrange(road_spacing)

    local_offset = rng.randrange(road_spacing)

    for row in range(grid.rows):
        for column in range(grid.columns):
            position = GridPosition(
                row,
                column,
            )

            if (row - arterial_offset) % (road_spacing * 2) == 0 or (column - arterial_offset) % (
                road_spacing * 2
            ) == 0:
                terrain[position] = TerrainType.ARTERIAL
                continue

            if (row - local_offset) % road_spacing == 0 or (
                column - local_offset
            ) % road_spacing == 0:
                terrain[position] = TerrainType.LOCAL_ROAD
                continue

            if rng.random() < building_probability:
                terrain[position] = TerrainType.BUILDING
                continue

            if rng.random() < 0.12:
                terrain[position] = TerrainType.SLOW_TERRAIN
            else:
                terrain[position] = base_terrain

    _carve_training_corridor(
        terrain,
        definition,
    )

    barrier_cells: list[GridPosition] = []

    if style is CityId.CHICAGO:
        barrier_column = rng.randrange(
            14,
            22,
        )

        bridges = {
            rng.randrange(4, 10),
            rng.randrange(15, 22),
            rng.randrange(26, 33),
        }

        for row in range(grid.rows):
            position = GridPosition(
                row,
                barrier_column,
            )

            if row in bridges:
                terrain[position] = TerrainType.ARTERIAL
            else:
                terrain[position] = TerrainType.BUILDING
                barrier_cells.append(position)

        _carve_training_corridor(
            terrain,
            definition,
        )

    visible_zones = tuple(
        ZombieZone(
            center=GridPosition(
                rng.randrange(2, 34),
                rng.randrange(2, 34),
            ),
            radius=rng.uniform(3.0, 7.0),
            intensity=rng.uniform(0.25, 0.70),
        )
        for _ in range(visible_zone_count)
    )

    hidden_hotspots: list[HiddenRiskHotspot] = []

    for index in range(hidden_hotspot_count):
        if style is CityId.NEW_YORK and index > 0:
            anchor = hidden_hotspots[0].center

            center = GridPosition(
                min(
                    33,
                    max(
                        2,
                        anchor.row + rng.randint(-5, 5),
                    ),
                ),
                min(
                    33,
                    max(
                        2,
                        anchor.column + rng.randint(-5, 5),
                    ),
                ),
            )
        elif index < len(visible_zones) and rng.random() < 0.55:
            visible_center = visible_zones[index].center

            center = GridPosition(
                min(
                    33,
                    max(
                        2,
                        visible_center.row + rng.randint(-5, 5),
                    ),
                ),
                min(
                    33,
                    max(
                        2,
                        visible_center.column + rng.randint(-5, 5),
                    ),
                ),
            )
        else:
            center = GridPosition(
                rng.randrange(2, 34),
                rng.randrange(2, 34),
            )

        hidden_hotspots.append(
            HiddenRiskHotspot(
                center=center,
                radius=rng.uniform(
                    2.3,
                    5.2,
                ),
                intensity=rng.uniform(
                    0.30,
                    0.90,
                ),
            )
        )

    noise_rng = random.Random(seed + 97_003)

    cells: list[GridCell] = []

    for row in range(grid.rows):
        for column in range(grid.columns):
            position = GridPosition(
                row,
                column,
            )

            terrain_type = terrain[position]

            if terrain_type is TerrainType.BUILDING:
                observed = 0.0
                truth = 0.0
            else:
                observed = _risk_field(
                    position,
                    visible_zones,
                    base=0.02,
                )

                hidden = _risk_field(
                    position,
                    tuple(hidden_hotspots),
                    base=0.0,
                )

                truth = min(
                    1.0,
                    max(
                        0.0,
                        (0.04 + 0.50 * observed + 0.72 * hidden + noise_rng.random() * 0.06),
                    ),
                )

            cells.append(
                GridCell(
                    position=position,
                    terrain=terrain_type,
                    observed_risk=observed,
                    true_risk=truth,
                )
            )

    city = GeneratedCity(
        definition=definition,
        grid=grid,
        cells=tuple(cells),
        visible_zombie_zones=visible_zones,
        hidden_risk_hotspots=tuple(hidden_hotspots),
        synthetic_barrier_cells=tuple(barrier_cells),
    )

    if not city.has_start_destination_connectivity():
        raise RuntimeError(f"Synthetic training city disconnected: {seed}")

    return city


def generate_training_dataset(
    config: ZombieProjectConfig,
) -> pd.DataFrame:
    """Generate all frozen train/validation/benchmark city splits."""
    frames = []

    split_contract = (
        (
            "training",
            (config.training.synthetic_training_cities),
            config.training.seeds.training,
        ),
        (
            "validation",
            (config.training.synthetic_validation_cities),
            config.training.seeds.validation,
        ),
        (
            "benchmark",
            (config.training.synthetic_benchmark_cities),
            config.training.seeds.benchmark,
        ),
    )

    for split, count, base_seed in split_contract:
        frames.append(
            _generate_split(
                config,
                split=split,
                count=count,
                base_seed=base_seed,
            )
        )

    dataset = pd.concat(
        frames,
        ignore_index=True,
    )

    return dataset


def write_training_dataset(
    dataset: pd.DataFrame,
    path: Path,
) -> None:
    """Write deterministic supervised dataset to Parquet."""
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset.to_parquet(
        path,
        index=False,
        engine="pyarrow",
    )


def _generate_split(
    config: ZombieProjectConfig,
    *,
    split: str,
    count: int,
    base_seed: int,
) -> pd.DataFrame:
    from linkedin_visual_labs.projects.p04_zombie_escape.ml_features import (
        training_rows_for_city,
    )

    if split not in _SPLIT_ORDER:
        raise ValueError(f"Unknown split: {split}")

    records: list[dict[str, object]] = []

    for city_index in range(count):
        city_seed = base_seed + city_index * 10_007

        style = tuple(CityId)[city_index % len(CityId)]

        city = generate_synthetic_training_city(
            config,
            seed=city_seed,
            style=style,
        )

        records.extend(
            training_rows_for_city(
                city,
                split=split,
                synthetic_city_index=city_index,
                sample_seed=(city_seed + 1_003),
                sample_size=(SAMPLES_PER_SYNTHETIC_CITY),
            )
        )

    return pd.DataFrame.from_records(records)


def _carve_training_corridor(
    terrain: dict[
        GridPosition,
        TerrainType,
    ],
    definition: CityDefinition,
) -> None:
    start = definition.start
    destination = definition.destination

    row_step = 1 if destination.row >= start.row else -1

    for row in range(
        start.row,
        destination.row + row_step,
        row_step,
    ):
        terrain[
            GridPosition(
                row,
                start.column,
            )
        ] = TerrainType.LOCAL_ROAD

    column_step = 1 if destination.column >= start.column else -1

    for column in range(
        start.column,
        destination.column + column_step,
        column_step,
    ):
        terrain[
            GridPosition(
                destination.row,
                column,
            )
        ] = TerrainType.LOCAL_ROAD

    terrain[start] = TerrainType.ARTERIAL
    terrain[destination] = TerrainType.ARTERIAL


def _risk_field(
    position: GridPosition,
    zones: tuple[
        ZombieZone | HiddenRiskHotspot,
        ...,
    ],
    *,
    base: float,
) -> float:
    value = base

    for zone in zones:
        row_delta = position.row - zone.center.row

        column_delta = position.column - zone.center.column

        distance_squared = row_delta * row_delta + column_delta * column_delta

        variance = zone.radius * zone.radius

        value += zone.intensity * exp(-distance_squared / (2.0 * variance))

    return min(
        1.0,
        max(
            0.0,
            value,
        ),
    )
