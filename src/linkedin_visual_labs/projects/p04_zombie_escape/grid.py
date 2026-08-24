"""Grid-domain primitives for Project 2 — Zombie Escape.

Deterministic city generation begins in Revised Step 3. This module only
provides typed geometry operations required by the Step-2 domain layer.
"""

from __future__ import annotations

from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    GridDefinition,
    GridPosition,
    ZombieModelError,
)


def validate_grid_position(
    grid: GridDefinition,
    position: GridPosition,
) -> None:
    """Require one logical position to lie inside the configured grid."""
    if not grid.contains(position):
        raise ZombieModelError(
            "Grid position lies outside configured grid: "
            f"row={position.row}, column={position.column}"
        )


def four_neighbors(
    grid: GridDefinition,
    position: GridPosition,
) -> tuple[GridPosition, ...]:
    """Return deterministic four-neighbor positions in canonical order.

    Canonical order is:
    up, right, down, left.

    Out-of-bounds positions are omitted.
    """
    validate_grid_position(
        grid,
        position,
    )

    candidates = (
        (
            position.row - 1,
            position.column,
        ),
        (
            position.row,
            position.column + 1,
        ),
        (
            position.row + 1,
            position.column,
        ),
        (
            position.row,
            position.column - 1,
        ),
    )

    result: list[GridPosition] = []

    for row, column in candidates:
        if 0 <= row < grid.rows and 0 <= column < grid.columns:
            result.append(
                GridPosition(
                    row=row,
                    column=column,
                )
            )

    return tuple(result)


def are_adjacent(
    first: GridPosition,
    second: GridPosition,
) -> bool:
    """Return whether two cells share one cardinal edge."""
    return abs(first.row - second.row) + abs(first.column - second.column) == 1
