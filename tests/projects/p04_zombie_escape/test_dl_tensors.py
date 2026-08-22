"""Deep-learning tensor contract tests for Project 2."""

from __future__ import annotations

import torch

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityId,
    GridCell,
    generate_city,
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_tensors import (
    INPUT_CHANNEL_COUNT,
    INPUT_CHANNELS,
    TARGET_NAME,
    city_to_tensor,
    validate_dl_input_contract,
)


def test_true_risk_is_not_a_cnn_input_channel() -> None:
    validate_dl_input_contract()

    assert TARGET_NAME == "true_risk"
    assert TARGET_NAME not in INPUT_CHANNELS
    assert INPUT_CHANNEL_COUNT == 8


def test_showcase_tensor_has_exact_shape() -> None:
    city = generate_city(
        load_zombie_config(),
        CityId.PHOENIX,
    )

    tensor = city_to_tensor(city)

    assert tensor.inputs.shape == (
        8,
        36,
        36,
    )

    assert tensor.target.shape == (
        1,
        36,
        36,
    )

    assert tensor.traversable_mask.shape == (
        1,
        36,
        36,
    )


def test_cnn_input_channels_are_observable_only() -> None:
    assert INPUT_CHANNELS == (
        "observed_risk",
        "terrain_building",
        "terrain_local_road",
        "terrain_arterial",
        "terrain_slow_terrain",
        "terrain_open_space",
        "row_norm",
        "column_norm",
    )


def test_hidden_truth_mutation_does_not_change_cnn_input() -> None:
    city = generate_city(
        load_zombie_config(),
        CityId.NEW_YORK,
    )

    original = city_to_tensor(city)

    mutated = GeneratedCity(
        definition=city.definition,
        grid=city.grid,
        cells=tuple(
            GridCell(
                position=cell.position,
                terrain=cell.terrain,
                observed_risk=cell.observed_risk,
                true_risk=(1.0 - cell.true_risk),
            )
            for cell in city.cells
        ),
        visible_zombie_zones=(city.visible_zombie_zones),
        hidden_risk_hotspots=(city.hidden_risk_hotspots),
        synthetic_barrier_cells=(city.synthetic_barrier_cells),
    )

    changed = city_to_tensor(mutated)

    assert torch.equal(
        original.inputs,
        changed.inputs,
    )

    assert not torch.equal(
        original.target,
        changed.target,
    )


def test_building_cells_are_masked_out() -> None:
    city = generate_city(
        load_zombie_config(),
        CityId.CHICAGO,
    )

    tensor = city_to_tensor(city)

    for cell in city.cells:
        mask_value = float(
            tensor.traversable_mask[
                0,
                cell.position.row,
                cell.position.column,
            ].item()
        )

        expected = float(city.is_traversable(cell.position))

        assert mask_value == expected


def test_tensor_conversion_is_exactly_deterministic() -> None:
    city = generate_city(
        load_zombie_config(),
        CityId.PHOENIX,
    )

    first = city_to_tensor(city)

    second = city_to_tensor(city)

    assert torch.equal(
        first.inputs,
        second.inputs,
    )

    assert torch.equal(
        first.target,
        second.target,
    )

    assert torch.equal(
        first.traversable_mask,
        second.traversable_mask,
    )
