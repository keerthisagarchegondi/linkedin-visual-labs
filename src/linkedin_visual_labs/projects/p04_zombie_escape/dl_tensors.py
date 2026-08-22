"""Spatial tensor representation for Zombie Escape deep learning."""

from __future__ import annotations

import random
from dataclasses import dataclass

import torch
from torch import Tensor

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_data import (
    generate_synthetic_training_city,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    CityId,
    GridPosition,
    TerrainType,
    ZombieProjectConfig,
)

INPUT_CHANNELS = (
    "observed_risk",
    "terrain_building",
    "terrain_local_road",
    "terrain_arterial",
    "terrain_slow_terrain",
    "terrain_open_space",
    "row_norm",
    "column_norm",
)

INPUT_CHANNEL_COUNT = len(INPUT_CHANNELS)

TARGET_NAME = "true_risk"

FORBIDDEN_INPUT_CHANNELS = (
    "true_risk",
    "hidden_risk",
    "hidden_hotspot",
    "oracle_risk",
)


@dataclass(frozen=True, slots=True)
class CityTensor:
    """One complete city represented for dense CNN regression."""

    inputs: Tensor
    target: Tensor
    traversable_mask: Tensor

    def __post_init__(self) -> None:
        if self.inputs.ndim != 3:
            raise ValueError("CityTensor inputs must have shape [C, H, W]")

        if self.target.ndim != 3:
            raise ValueError("CityTensor target must have shape [1, H, W]")

        if self.traversable_mask.ndim != 3:
            raise ValueError("CityTensor mask must have shape [1, H, W]")

        if self.inputs.shape[0] != INPUT_CHANNEL_COUNT:
            raise ValueError("CityTensor input-channel count mismatch")

        if self.target.shape[0] != 1:
            raise ValueError("CityTensor target must have one channel")

        if self.traversable_mask.shape[0] != 1:
            raise ValueError("CityTensor traversable mask must have one channel")

        if (
            self.inputs.shape[1:] != self.target.shape[1:]
            or self.inputs.shape[1:] != self.traversable_mask.shape[1:]
        ):
            raise ValueError("CityTensor spatial dimensions must match")


def validate_dl_input_contract() -> None:
    """Ensure hidden simulator truth cannot enter the CNN input tensor."""
    lower_channels = {channel.lower() for channel in INPUT_CHANNELS}

    leaked = [
        forbidden for forbidden in FORBIDDEN_INPUT_CHANNELS if forbidden.lower() in lower_channels
    ]

    if leaked:
        raise RuntimeError("Hidden-risk DL input leakage detected: " + ", ".join(leaked))

    if TARGET_NAME in INPUT_CHANNELS:
        raise RuntimeError("true_risk target appears in CNN input channels")


def city_to_tensor(
    city: GeneratedCity,
) -> CityTensor:
    """Convert one complete city into observable inputs and hidden target."""
    validate_dl_input_contract()

    rows = city.grid.rows
    columns = city.grid.columns

    inputs = torch.zeros(
        (
            INPUT_CHANNEL_COUNT,
            rows,
            columns,
        ),
        dtype=torch.float32,
    )

    target = torch.zeros(
        (
            1,
            rows,
            columns,
        ),
        dtype=torch.float32,
    )

    traversable_mask = torch.zeros(
        (
            1,
            rows,
            columns,
        ),
        dtype=torch.float32,
    )

    row_denominator = max(
        1,
        rows - 1,
    )

    column_denominator = max(
        1,
        columns - 1,
    )

    terrain_channel = {
        TerrainType.BUILDING: 1,
        TerrainType.LOCAL_ROAD: 2,
        TerrainType.ARTERIAL: 3,
        TerrainType.SLOW_TERRAIN: 4,
        TerrainType.OPEN_SPACE: 5,
    }

    for cell in city.cells:
        row = cell.position.row
        column = cell.position.column

        inputs[
            0,
            row,
            column,
        ] = cell.observed_risk

        inputs[
            terrain_channel[cell.terrain],
            row,
            column,
        ] = 1.0

        inputs[
            6,
            row,
            column,
        ] = row / row_denominator

        inputs[
            7,
            row,
            column,
        ] = column / column_denominator

        target[
            0,
            row,
            column,
        ] = cell.true_risk

        if cell.terrain is not TerrainType.BUILDING:
            traversable_mask[
                0,
                row,
                column,
            ] = 1.0

    return CityTensor(
        inputs=inputs,
        target=target,
        traversable_mask=traversable_mask,
    )


def split_contract(
    config: ZombieProjectConfig,
    split: str,
) -> tuple[
    int,
    int,
]:
    """Return frozen city count and seed for one DL split."""
    if split == "training":
        return (
            config.training.synthetic_training_cities,
            config.training.seeds.training,
        )

    if split == "validation":
        return (
            config.training.synthetic_validation_cities,
            config.training.seeds.validation,
        )

    if split == "benchmark":
        return (
            config.training.synthetic_benchmark_cities,
            config.training.seeds.benchmark,
        )

    raise ValueError(f"Unknown DL split: {split}")


def synthetic_city_for_index(
    config: ZombieProjectConfig,
    *,
    split: str,
    city_index: int,
) -> GeneratedCity:
    """Recreate one deterministic synthetic city used by DL training."""
    count, base_seed = split_contract(
        config,
        split,
    )

    if not 0 <= city_index < count:
        raise IndexError(f"{split} city index outside frozen split: {city_index}")

    city_seed = base_seed + city_index * 10_007

    style = tuple(CityId)[city_index % len(CityId)]

    return generate_synthetic_training_city(
        config,
        seed=city_seed,
        style=style,
    )


def city_indices_for_epoch(
    *,
    count: int,
    seed: int,
    epoch: int,
    shuffle: bool,
) -> tuple[int, ...]:
    """Return deterministic city ordering for one training/evaluation epoch."""
    indices = list(range(count))

    if shuffle:
        rng = random.Random(seed + epoch * 1_000_003)

        rng.shuffle(indices)

    return tuple(indices)


def build_city_batch(
    config: ZombieProjectConfig,
    *,
    split: str,
    indices: tuple[int, ...],
) -> tuple[
    Tensor,
    Tensor,
    Tensor,
]:
    """Generate and stack one deterministic city batch."""
    tensors = [
        city_to_tensor(
            synthetic_city_for_index(
                config,
                split=split,
                city_index=index,
            )
        )
        for index in indices
    ]

    inputs = torch.stack([item.inputs for item in tensors])

    targets = torch.stack([item.target for item in tensors])

    masks = torch.stack([item.traversable_mask for item in tensors])

    return (
        inputs,
        targets,
        masks,
    )


def showcase_prediction_positions(
    city: GeneratedCity,
) -> tuple[
    GridPosition,
    ...,
]:
    """Return canonical traversable positions for dense prediction export."""
    return city.traversable_positions()
