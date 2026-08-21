"""Grid-geometry scaffold tests for Project 2."""

from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p04_zombie_escape import (
    GridDefinition,
    GridPosition,
    MovementRule,
    ZombieModelError,
    are_adjacent,
    four_neighbors,
)


@pytest.fixture
def grid() -> GridDefinition:
    return GridDefinition(
        rows=3,
        columns=3,
        movement=MovementRule.FOUR_NEIGHBOR,
        allow_diagonal=False,
        step_distance=1.0,
    )


def test_center_neighbors_use_canonical_order(
    grid: GridDefinition,
) -> None:
    assert four_neighbors(
        grid,
        GridPosition(
            1,
            1,
        ),
    ) == (
        GridPosition(
            0,
            1,
        ),
        GridPosition(
            1,
            2,
        ),
        GridPosition(
            2,
            1,
        ),
        GridPosition(
            1,
            0,
        ),
    )


def test_corner_neighbors_are_bounded(
    grid: GridDefinition,
) -> None:
    assert four_neighbors(
        grid,
        GridPosition(
            0,
            0,
        ),
    ) == (
        GridPosition(
            0,
            1,
        ),
        GridPosition(
            1,
            0,
        ),
    )


def test_out_of_bounds_origin_is_rejected(
    grid: GridDefinition,
) -> None:
    with pytest.raises(
        ZombieModelError,
        match="outside",
    ):
        four_neighbors(
            grid,
            GridPosition(
                4,
                4,
            ),
        )


def test_adjacency_is_cardinal_only() -> None:
    origin = GridPosition(
        2,
        2,
    )

    assert are_adjacent(
        origin,
        GridPosition(
            2,
            3,
        ),
    )

    assert not are_adjacent(
        origin,
        GridPosition(
            3,
            3,
        ),
    )
