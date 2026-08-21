"""Deterministic synthetic city generation for Zombie Escape.

This module owns synthetic city construction, terrain layout, visible zombie
risk, hidden true-risk fields, and grid-connectivity validation.

Routing algorithms intentionally do not live here. Dijkstra, A*, and Oracle
routing begin in Revised Step 4.
"""

from __future__ import annotations

import random
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from math import exp, isfinite

from linkedin_visual_labs.projects.p04_zombie_escape.grid import (
    four_neighbors,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    CityDefinition,
    CityId,
    GridCell,
    GridDefinition,
    GridPosition,
    TerrainDefinition,
    TerrainType,
    ZombieModelError,
    ZombieProjectConfig,
)

_RISK_EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class ZombieZone:
    """One observable zombie-risk zone."""

    center: GridPosition
    radius: float
    intensity: float

    def __post_init__(self) -> None:
        if self.radius <= 0.0 or not isfinite(self.radius):
            raise ZombieModelError("ZombieZone radius must be positive and finite")

        if not isfinite(self.intensity) or not 0.0 <= self.intensity <= 1.0:
            raise ZombieModelError("ZombieZone intensity must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class HiddenRiskHotspot:
    """One simulator-only hidden-risk hotspot."""

    center: GridPosition
    radius: float
    intensity: float

    def __post_init__(self) -> None:
        if self.radius <= 0.0 or not isfinite(self.radius):
            raise ZombieModelError("HiddenRiskHotspot radius must be positive and finite")

        if not isfinite(self.intensity) or not 0.0 <= self.intensity <= 1.0:
            raise ZombieModelError("HiddenRiskHotspot intensity must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class GeneratedCity:
    """Complete deterministic simulator representation for one city."""

    definition: CityDefinition
    grid: GridDefinition
    cells: tuple[GridCell, ...]
    visible_zombie_zones: tuple[ZombieZone, ...]
    hidden_risk_hotspots: tuple[HiddenRiskHotspot, ...]
    synthetic_barrier_cells: tuple[GridPosition, ...]

    def __post_init__(self) -> None:
        expected = self.grid.rows * self.grid.columns

        if len(self.cells) != expected:
            raise ZombieModelError(f"Generated city must contain exactly {expected} grid cells")

        positions = {cell.position for cell in self.cells}

        if len(positions) != expected:
            raise ZombieModelError("Generated city contains duplicate grid positions")

        for row in range(self.grid.rows):
            for column in range(self.grid.columns):
                position = GridPosition(
                    row=row,
                    column=column,
                )

                if position not in positions:
                    raise ZombieModelError(f"Generated city is missing grid position {position}")

        if not self.is_traversable(self.definition.start):
            raise ZombieModelError("City start must be traversable")

        if not self.is_traversable(self.definition.destination):
            raise ZombieModelError("City destination must be traversable")

    @property
    def city_id(self) -> CityId:
        """Return the canonical city identifier."""
        return self.definition.city_id

    def cell(
        self,
        position: GridPosition,
    ) -> GridCell:
        """Return the cell at one grid position in O(1) row-major order."""
        if not self.grid.contains(position):
            raise ZombieModelError("Requested city cell lies outside the grid")

        index = position.row * self.grid.columns + position.column

        cell = self.cells[index]

        if cell.position != position:
            raise ZombieModelError("Generated city cell ordering invariant violated")

        return cell

    def is_traversable(
        self,
        position: GridPosition,
    ) -> bool:
        """Return whether the cell can be entered by a route."""
        return self.cell(position).terrain is not TerrainType.BUILDING

    def traversable_neighbors(
        self,
        position: GridPosition,
    ) -> tuple[GridPosition, ...]:
        """Return deterministic traversable cardinal neighbors."""
        return tuple(
            neighbor
            for neighbor in four_neighbors(
                self.grid,
                position,
            )
            if self.is_traversable(neighbor)
        )

    def traversable_positions(
        self,
    ) -> tuple[GridPosition, ...]:
        """Return all traversable positions in deterministic row-major order."""
        return tuple(
            cell.position for cell in self.cells if cell.terrain is not TerrainType.BUILDING
        )

    def terrain_count(
        self,
        terrain: TerrainType,
    ) -> int:
        """Count cells of a particular terrain type."""
        return sum(1 for cell in self.cells if cell.terrain is terrain)

    def has_start_destination_connectivity(
        self,
    ) -> bool:
        """Check reachability without selecting an optimal route.

        This is a grid-validity invariant, not a route-planning algorithm.
        """
        start = self.definition.start
        destination = self.definition.destination

        frontier: deque[GridPosition] = deque((start,))

        visited = {start}

        while frontier:
            current = frontier.popleft()

            if current == destination:
                return True

            for neighbor in self.traversable_neighbors(current):
                if neighbor in visited:
                    continue

                visited.add(neighbor)

                frontier.append(neighbor)

        return False


def terrain_is_traversable(
    terrain: TerrainType,
) -> bool:
    """Return the fixed traversability semantics for a terrain value."""
    return terrain is not TerrainType.BUILDING


def terrain_speed_multiplier(
    config: ZombieProjectConfig,
    terrain: TerrainType,
) -> float:
    """Return the authoritative speed multiplier for one terrain type."""
    definition = config.experiment.terrain_definition(terrain)

    return definition.speed_multiplier


def validate_terrain_contract(
    definitions: Iterable[TerrainDefinition],
) -> None:
    """Validate that all five terrain types exist exactly once."""
    definitions_tuple = tuple(definitions)

    actual = {item.terrain_type for item in definitions_tuple}

    if actual != set(TerrainType):
        raise ZombieModelError("Terrain contract must define every TerrainType exactly once")

    if len(definitions_tuple) != len(TerrainType):
        raise ZombieModelError("Terrain contract contains duplicate terrain definitions")


def generate_all_cities(
    config: ZombieProjectConfig,
) -> tuple[GeneratedCity, ...]:
    """Generate all three showcase cities in canonical config order."""
    validate_terrain_contract(config.experiment.terrain)

    result = tuple(
        generate_city(
            config,
            city,
        )
        for city in config.cities
    )

    if tuple(city.city_id for city in result) != (
        CityId.PHOENIX,
        CityId.NEW_YORK,
        CityId.CHICAGO,
    ):
        raise ZombieModelError("Generated city order must remain Phoenix, New York, Chicago")

    return result


def generate_city(
    config: ZombieProjectConfig,
    city: CityDefinition | CityId | str,
) -> GeneratedCity:
    """Generate one deterministic showcase city."""
    definition = (
        city
        if isinstance(
            city,
            CityDefinition,
        )
        else config.city(CityId(city))
    )

    if definition.city_id is CityId.PHOENIX:
        return _generate_phoenix(
            config,
            definition,
        )

    if definition.city_id is CityId.NEW_YORK:
        return _generate_new_york(
            config,
            definition,
        )

    if definition.city_id is CityId.CHICAGO:
        return _generate_chicago(
            config,
            definition,
        )

    raise ZombieModelError(f"Unsupported city: {definition.city_id}")


def _generate_phoenix(
    config: ZombieProjectConfig,
    definition: CityDefinition,
) -> GeneratedCity:
    grid = config.experiment.grid

    terrain = _base_terrain(
        grid,
        TerrainType.OPEN_SPACE,
    )

    arterial_rows = {
        5,
        11,
        17,
        23,
        29,
        34,
    }

    arterial_columns = {
        4,
        10,
        16,
        22,
        28,
        33,
    }

    for row in range(grid.rows):
        for column in range(grid.columns):
            position = GridPosition(
                row,
                column,
            )

            if row in arterial_rows or column in arterial_columns:
                terrain[position] = TerrainType.ARTERIAL

                continue

            if row % 6 in {
                1,
                2,
            } and column % 6 in {
                1,
                2,
            }:
                terrain[position] = TerrainType.BUILDING

                continue

            if (row + column) % 11 == 0:
                terrain[position] = TerrainType.SLOW_TERRAIN

                continue

            if row % 3 == 0 or column % 3 == 0:
                terrain[position] = TerrainType.LOCAL_ROAD

    _carve_manhattan_corridor(
        terrain,
        definition.start,
        definition.destination,
        TerrainType.ARTERIAL,
    )

    visible_zones = _make_visible_zones(
        definition,
        count=4,
        radius_range=(
            4.5,
            7.5,
        ),
        intensity_range=(
            0.30,
            0.58,
        ),
        salt=101,
    )

    hidden_hotspots = _make_hidden_hotspots(
        definition,
        count=7,
        radius_range=(
            3.0,
            5.5,
        ),
        intensity_range=(
            0.28,
            0.52,
        ),
        salt=201,
    )

    return _finalize_city(
        config=config,
        definition=definition,
        terrain=terrain,
        visible_zones=visible_zones,
        hidden_hotspots=hidden_hotspots,
        synthetic_barrier_cells=(),
        noise_amplitude=0.055,
    )


def _generate_new_york(
    config: ZombieProjectConfig,
    definition: CityDefinition,
) -> GeneratedCity:
    grid = config.experiment.grid

    terrain = _base_terrain(
        grid,
        TerrainType.LOCAL_ROAD,
    )

    road_rows = {
        2,
        5,
        8,
        11,
        14,
        17,
        20,
        23,
        26,
        29,
        32,
        35,
    }

    road_columns = {
        2,
        5,
        8,
        11,
        14,
        17,
        20,
        23,
        26,
        29,
        32,
        35,
    }

    arterial_rows = {
        8,
        17,
        26,
    }

    arterial_columns = {
        5,
        14,
        23,
        32,
    }

    for row in range(grid.rows):
        for column in range(grid.columns):
            position = GridPosition(
                row,
                column,
            )

            if row in arterial_rows or column in arterial_columns:
                terrain[position] = TerrainType.ARTERIAL

                continue

            if row in road_rows or column in road_columns:
                terrain[position] = TerrainType.LOCAL_ROAD

                continue

            terrain[position] = TerrainType.BUILDING

    _carve_manhattan_corridor(
        terrain,
        definition.start,
        definition.destination,
        TerrainType.LOCAL_ROAD,
    )

    visible_zones = _make_visible_zones(
        definition,
        count=3,
        radius_range=(
            3.0,
            5.0,
        ),
        intensity_range=(
            0.40,
            0.68,
        ),
        salt=102,
    )

    hidden_hotspots = _make_hidden_hotspots(
        definition,
        count=4,
        radius_range=(
            2.4,
            4.0,
        ),
        intensity_range=(
            0.58,
            0.92,
        ),
        salt=202,
    )

    return _finalize_city(
        config=config,
        definition=definition,
        terrain=terrain,
        visible_zones=visible_zones,
        hidden_hotspots=hidden_hotspots,
        synthetic_barrier_cells=(),
        noise_amplitude=0.035,
    )


def _generate_chicago(
    config: ZombieProjectConfig,
    definition: CityDefinition,
) -> GeneratedCity:
    grid = config.experiment.grid

    terrain = _base_terrain(
        grid,
        TerrainType.LOCAL_ROAD,
    )

    arterial_rows = {
        6,
        12,
        18,
        24,
        30,
    }

    arterial_columns = {
        5,
        11,
        24,
        30,
    }

    for row in range(grid.rows):
        for column in range(grid.columns):
            position = GridPosition(
                row,
                column,
            )

            if row in arterial_rows or column in arterial_columns:
                terrain[position] = TerrainType.ARTERIAL

                continue

            if row % 5 in {
                1,
                2,
            } and column % 5 in {
                2,
                3,
            }:
                terrain[position] = TerrainType.BUILDING

                continue

            if (row + 2 * column) % 17 == 0:
                terrain[position] = TerrainType.SLOW_TERRAIN

    barrier_columns = (
        17,
        18,
    )

    bridge_rows = {
        6,
        18,
        30,
    }

    barrier_cells: list[GridPosition] = []

    for row in range(grid.rows):
        for column in barrier_columns:
            position = GridPosition(
                row,
                column,
            )

            if row in bridge_rows:
                terrain[position] = TerrainType.ARTERIAL
            else:
                terrain[position] = TerrainType.BUILDING

                barrier_cells.append(position)

    _carve_chicago_bridge_corridor(
        terrain,
        definition,
        bridge_row=18,
    )

    visible_zones = _make_visible_zones(
        definition,
        count=4,
        radius_range=(
            3.5,
            5.5,
        ),
        intensity_range=(
            0.36,
            0.64,
        ),
        salt=103,
    )

    hidden_hotspots = _make_hidden_hotspots(
        definition,
        count=5,
        radius_range=(
            2.8,
            4.4,
        ),
        intensity_range=(
            0.46,
            0.78,
        ),
        salt=203,
    )

    return _finalize_city(
        config=config,
        definition=definition,
        terrain=terrain,
        visible_zones=visible_zones,
        hidden_hotspots=hidden_hotspots,
        synthetic_barrier_cells=tuple(barrier_cells),
        noise_amplitude=0.045,
    )


def _base_terrain(
    grid: GridDefinition,
    default: TerrainType,
) -> dict[GridPosition, TerrainType]:
    return {
        GridPosition(
            row=row,
            column=column,
        ): default
        for row in range(grid.rows)
        for column in range(grid.columns)
    }


def _carve_manhattan_corridor(
    terrain: dict[GridPosition, TerrainType],
    start: GridPosition,
    destination: GridPosition,
    terrain_type: TerrainType,
) -> None:
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
        ] = terrain_type

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
        ] = terrain_type


def _carve_chicago_bridge_corridor(
    terrain: dict[GridPosition, TerrainType],
    definition: CityDefinition,
    *,
    bridge_row: int,
) -> None:
    start = definition.start
    destination = definition.destination

    row_step = 1 if bridge_row >= start.row else -1

    for row in range(
        start.row,
        bridge_row + row_step,
        row_step,
    ):
        terrain[
            GridPosition(
                row,
                start.column,
            )
        ] = TerrainType.LOCAL_ROAD

    left_column = min(
        start.column,
        destination.column,
    )

    right_column = max(
        start.column,
        destination.column,
    )

    for column in range(
        left_column,
        right_column + 1,
    ):
        terrain[
            GridPosition(
                bridge_row,
                column,
            )
        ] = TerrainType.ARTERIAL

    row_step = 1 if destination.row >= bridge_row else -1

    for row in range(
        bridge_row,
        destination.row + row_step,
        row_step,
    ):
        terrain[
            GridPosition(
                row,
                destination.column,
            )
        ] = TerrainType.LOCAL_ROAD


def _make_visible_zones(
    definition: CityDefinition,
    *,
    count: int,
    radius_range: tuple[float, float],
    intensity_range: tuple[float, float],
    salt: int,
) -> tuple[ZombieZone, ...]:
    rng = random.Random(definition.seed + salt)

    zones: list[ZombieZone] = []

    for _ in range(count):
        center = GridPosition(
            row=rng.randrange(
                3,
                33,
            ),
            column=rng.randrange(
                3,
                33,
            ),
        )

        zones.append(
            ZombieZone(
                center=center,
                radius=rng.uniform(*radius_range),
                intensity=rng.uniform(*intensity_range),
            )
        )

    return tuple(zones)


def _make_hidden_hotspots(
    definition: CityDefinition,
    *,
    count: int,
    radius_range: tuple[float, float],
    intensity_range: tuple[float, float],
    salt: int,
) -> tuple[HiddenRiskHotspot, ...]:
    rng = random.Random(definition.seed + salt)

    hotspots: list[HiddenRiskHotspot] = []

    if definition.city_id is CityId.NEW_YORK:
        anchor_row = rng.randrange(
            10,
            25,
        )

        anchor_column = rng.randrange(
            10,
            25,
        )

        for _ in range(count):
            row = min(
                32,
                max(
                    3,
                    anchor_row
                    + rng.randint(
                        -5,
                        5,
                    ),
                ),
            )

            column = min(
                32,
                max(
                    3,
                    anchor_column
                    + rng.randint(
                        -5,
                        5,
                    ),
                ),
            )

            hotspots.append(
                HiddenRiskHotspot(
                    center=GridPosition(
                        row,
                        column,
                    ),
                    radius=rng.uniform(*radius_range),
                    intensity=rng.uniform(*intensity_range),
                )
            )

        return tuple(hotspots)

    for _ in range(count):
        hotspots.append(
            HiddenRiskHotspot(
                center=GridPosition(
                    row=rng.randrange(
                        3,
                        33,
                    ),
                    column=rng.randrange(
                        3,
                        33,
                    ),
                ),
                radius=rng.uniform(*radius_range),
                intensity=rng.uniform(*intensity_range),
            )
        )

    return tuple(hotspots)


def _finalize_city(
    *,
    config: ZombieProjectConfig,
    definition: CityDefinition,
    terrain: dict[GridPosition, TerrainType],
    visible_zones: tuple[ZombieZone, ...],
    hidden_hotspots: tuple[HiddenRiskHotspot, ...],
    synthetic_barrier_cells: tuple[GridPosition, ...],
    noise_amplitude: float,
) -> GeneratedCity:
    grid = config.experiment.grid

    terrain[definition.start] = TerrainType.ARTERIAL

    terrain[definition.destination] = TerrainType.ARTERIAL

    noise_rng = random.Random(definition.seed + 901)

    cells: list[GridCell] = []

    for row in range(grid.rows):
        for column in range(grid.columns):
            position = GridPosition(
                row,
                column,
            )

            terrain_type = terrain[position]

            observed_risk = _visible_risk(
                position,
                visible_zones,
            )

            hidden_component = _hidden_risk(
                position,
                hidden_hotspots,
            )

            deterministic_noise = noise_rng.random() * noise_amplitude

            true_risk = _clamp_risk(
                0.04 + 0.55 * observed_risk + hidden_component + deterministic_noise
            )

            if terrain_type is TerrainType.BUILDING:
                observed_risk = 0.0
                true_risk = 0.0

            cells.append(
                GridCell(
                    position=position,
                    terrain=terrain_type,
                    observed_risk=observed_risk,
                    true_risk=true_risk,
                )
            )

    city = GeneratedCity(
        definition=definition,
        grid=grid,
        cells=tuple(cells),
        visible_zombie_zones=visible_zones,
        hidden_risk_hotspots=hidden_hotspots,
        synthetic_barrier_cells=synthetic_barrier_cells,
    )

    if not city.has_start_destination_connectivity():
        raise ZombieModelError(f"{definition.city_id} start and destination are disconnected")

    return city


def _visible_risk(
    position: GridPosition,
    zones: tuple[ZombieZone, ...],
) -> float:
    value = 0.02

    for zone in zones:
        value += _gaussian_field(
            position,
            center=zone.center,
            radius=zone.radius,
            intensity=zone.intensity,
        )

    return _clamp_risk(value)


def _hidden_risk(
    position: GridPosition,
    hotspots: tuple[HiddenRiskHotspot, ...],
) -> float:
    value = 0.0

    for hotspot in hotspots:
        value += _gaussian_field(
            position,
            center=hotspot.center,
            radius=hotspot.radius,
            intensity=hotspot.intensity,
        )

    return _clamp_risk(value)


def _gaussian_field(
    position: GridPosition,
    *,
    center: GridPosition,
    radius: float,
    intensity: float,
) -> float:
    row_delta = position.row - center.row

    column_delta = position.column - center.column

    distance_squared = row_delta * row_delta + column_delta * column_delta

    variance = radius * radius

    return intensity * exp(-distance_squared / (2.0 * variance))


def _clamp_risk(
    value: float,
) -> float:
    if not isfinite(value):
        raise ZombieModelError("Risk field produced a non-finite value")

    if value <= _RISK_EPSILON:
        return 0.0

    return min(
        1.0,
        max(
            0.0,
            value,
        ),
    )
