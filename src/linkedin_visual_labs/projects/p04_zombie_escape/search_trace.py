"""Deterministic real-search tracing for Project 2 Step 10R.

This module does not alter the production routing engine.

Instead, it deterministically re-executes the frozen Dijkstra/A* searches,
records their search state, and requires the resulting final path to match
the canonical path persisted by the production routing pipeline.
"""

from __future__ import annotations

import hashlib
import heapq
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Literal, cast

from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    CITY_ORDER,
    METHOD_ORDER,
    _cell_position,
    _cells,
    _city_payload,
    _method_route,
    _observed_risk,
    _position,
    _terrain_name,
    load_visual_payloads,
)

Position = tuple[int, int]

TraceMethod = Literal[
    "dijkstra",
    "ml",
    "dl",
]

EdgeClassification = Literal[
    "explored_active",
    "explored_rejected",
    "final_route",
    "blocked",
]


GRID_SIZE: Final[int] = 36

RISK_WEIGHT: Final[float] = 4.0

TERRAIN_SPEEDS: Final[dict[str, float]] = {
    "local": 1.00,
    "arterial": 1.35,
    "slow": 0.70,
    "open": 0.85,
}

FASTEST_SPEED: Final[float] = max(TERRAIN_SPEEDS.values())

MINIMUM_TRAVEL_TIME_PER_STEP: Final[float] = 1.0 / FASTEST_SPEED


METHOD_ALGORITHMS: Final[dict[str, str]] = {
    "dijkstra": "dijkstra",
    "ml": "astar",
    "dl": "astar",
}


RISK_SOURCES: Final[dict[str, str]] = {
    "dijkstra": "observed_risk",
    "ml": "ml_predicted_risk",
    "dl": "dl_predicted_risk",
}


# ============================================================================
# Typed trace records
# ============================================================================


@dataclass(
    frozen=True,
    slots=True,
)
class SearchExpansion:
    """One settled/popped search node."""

    step: int
    position: Position

    g_cost: float
    h_cost: float
    f_cost: float

    frontier_size_after_pop: int


@dataclass(
    frozen=True,
    slots=True,
)
class SearchTreeEdge:
    """A predecessor edge created by a successful relaxation."""

    parent: Position
    child: Position

    discovery_step: int

    g_cost: float
    h_cost: float
    f_cost: float

    classification: EdgeClassification


@dataclass(
    frozen=True,
    slots=True,
)
class BlockedEdge:
    """An attempted cardinal transition into an impassable cell."""

    parent: Position
    blocked: Position

    expansion_step: int

    classification: EdgeClassification = "blocked"


@dataclass(
    frozen=True,
    slots=True,
)
class PlannerSearchTrace:
    """Complete deterministic trace for one planner/city pair."""

    city_id: str
    method_id: str

    algorithm: str
    risk_source: str

    start: Position
    destination: Position

    expansions: tuple[SearchExpansion, ...]

    tree_edges: tuple[SearchTreeEdge, ...]

    blocked_edges: tuple[BlockedEdge, ...]

    final_path: tuple[Position, ...]

    expanded_node_count: int
    discovered_tree_edge_count: int
    blocked_edge_count: int

    route_objective: float

    canonical_route_match: bool


@dataclass(
    frozen=True,
    slots=True,
)
class SearchTraceBundle:
    """All 3 cities x 3 headline methods."""

    schema_version: int

    traces: tuple[PlannerSearchTrace, ...]


# ============================================================================
# City-grid normalization
# ============================================================================


def _terrain_kind(
    raw: str,
) -> str:
    value = raw.lower()

    if "building" in value:
        return "building"

    if "arterial" in value:
        return "arterial"

    if "local" in value or "road" in value:
        return "local"

    if "slow" in value:
        return "slow"

    return "open"


def _speed(
    terrain: str,
) -> float:
    if terrain == "building":
        return 0.0

    return TERRAIN_SPEEDS[terrain]


def _city_tables(
    city: dict[str, object],
) -> tuple[
    dict[
        Position,
        str,
    ],
    dict[
        Position,
        float,
    ],
]:
    terrain: dict[Position, str] = {}

    observed_risk: dict[Position, float] = {}

    for cell in _cells(city):
        position = _cell_position(cell)

        terrain[position] = _terrain_kind(_terrain_name(cell))

        observed_risk[position] = float(_observed_risk(cell))

    return (
        terrain,
        observed_risk,
    )


def _is_in_bounds(
    position: Position,
) -> bool:
    return 0 <= position[0] < GRID_SIZE and 0 <= position[1] < GRID_SIZE


def _cardinal_positions(
    position: Position,
) -> tuple[
    Position,
    Position,
    Position,
    Position,
]:
    row, column = position

    # Frozen deterministic neighbor order.
    #
    # The final canonical-route equality gate below prevents us from
    # silently accepting a tie-breaking order that disagrees with the
    # production route engine.
    return (
        (
            row - 1,
            column,
        ),
        (
            row,
            column - 1,
        ),
        (
            row,
            column + 1,
        ),
        (
            row + 1,
            column,
        ),
    )


# ============================================================================
# Predicted-risk payload extraction
# ============================================================================


def _float_value(
    value: object,
) -> float | None:
    """Return one finite numeric risk value."""
    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        result = float(value)

        if math.isfinite(result):
            return result

    return None


RISK_VALUE_KEYS: Final[tuple[str, ...]] = (
    "predicted_risk",
    "prediction",
    "risk",
    "risk_score",
    "zombie_risk",
    "value",
    "score",
    "predicted",
)


def _integer_coordinate(
    value: object,
) -> int | None:
    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        stripped = value.strip()

        if stripped.lstrip("-").isdigit():
            return int(stripped)

    return None


def _position_from_mapping(
    value: dict[object, object],
) -> Position | None:
    """Extract row/column from common serialized cell shapes."""
    row_keys = (
        "row",
        "r",
        "y",
    )

    column_keys = (
        "column",
        "col",
        "c",
        "x",
    )

    row: int | None = None
    column: int | None = None

    normalized = {
        str(key).lower(): child
        for (
            key,
            child,
        ) in value.items()
    }

    for key in row_keys:
        if key not in normalized:
            continue

        row = _integer_coordinate(normalized[key])

        if row is not None:
            break

    for key in column_keys:
        if key not in normalized:
            continue

        column = _integer_coordinate(normalized[key])

        if column is not None:
            break

    if row is not None and column is not None:
        direct_position: Position = (
            row,
            column,
        )

        if _is_in_bounds(direct_position):
            return direct_position

    for nested_key in (
        "position",
        "coordinate",
        "coordinates",
        "cell",
        "location",
    ):
        nested = normalized.get(nested_key)

        if not isinstance(
            nested,
            dict,
        ):
            continue

        nested_position = _position_from_mapping(
            cast(
                dict[object, object],
                nested,
            )
        )

        if nested_position is not None:
            return nested_position

    return None


def _risk_from_mapping(
    value: dict[object, object],
) -> float | None:
    """Extract a numeric prediction from a serialized cell record."""
    normalized = {
        str(key).lower(): child
        for (
            key,
            child,
        ) in value.items()
    }

    for key in RISK_VALUE_KEYS:
        if key not in normalized:
            continue

        child = normalized[key]

        numeric = _float_value(child)

        if numeric is not None:
            return numeric

        if isinstance(
            child,
            dict,
        ):
            nested = _risk_from_mapping(
                cast(
                    dict[object, object],
                    child,
                )
            )

            if nested is not None:
                return nested

    return None


def _matrix_risk_map(
    value: object,
) -> dict[Position, float] | None:
    """Recognize a conventional 36 x 36 nested numeric matrix."""
    if not isinstance(
        value,
        list,
    ):
        return None

    if len(value) != GRID_SIZE:
        return None

    result: dict[Position, float] = {}

    for row, raw_row in enumerate(value):
        if not isinstance(
            raw_row,
            list,
        ):
            return None

        if len(raw_row) != GRID_SIZE:
            return None

        for column, raw_value in enumerate(raw_row):
            risk = _float_value(raw_value)

            if risk is None:
                return None

            result[
                (
                    row,
                    column,
                )
            ] = risk

    return result


def _flat_numeric_risk_map(
    value: object,
) -> dict[Position, float] | None:
    """Recognize a flattened 1296-element numeric grid."""
    if not isinstance(
        value,
        list,
    ):
        return None

    if len(value) != (GRID_SIZE * GRID_SIZE):
        return None

    numbers: list[float] = []

    for child in value:
        risk = _float_value(child)

        if risk is None:
            return None

        numbers.append(risk)

    return {
        (
            index // GRID_SIZE,
            index % GRID_SIZE,
        ): risk
        for (
            index,
            risk,
        ) in enumerate(numbers)
    }


def _cell_list_risk_map(
    value: object,
) -> dict[Position, float] | None:
    """
    Recognize a list of cell records.

    Examples supported:
        {"row": 2, "column": 5, "predicted_risk": 0.4}

        {
            "position": {"row": 2, "column": 5},
            "prediction": 0.4,
        }
    """
    if not isinstance(
        value,
        list,
    ):
        return None

    if not value:
        return None

    result: dict[Position, float] = {}

    for item in value:
        if not isinstance(
            item,
            dict,
        ):
            return None

        mapping = cast(
            dict[object, object],
            item,
        )

        position = _position_from_mapping(mapping)

        risk = _risk_from_mapping(mapping)

        if position is None or risk is None:
            return None

        result[position] = risk

    if not result:
        return None

    return result


def _row_mapping_risk_map(
    value: object,
) -> dict[Position, float] | None:
    """
    Recognize dictionary-based grids.

    Supported examples:

        {
            "0": [0.1, 0.2, ...],
            ...
            "35": [...]
        }

    or:

        {
            "0": {
                "0": 0.1,
                "1": 0.2,
                ...
            },
            ...
        }
    """
    if not isinstance(
        value,
        dict,
    ):
        return None

    normalized_rows: dict[int, object] = {}

    for (
        raw_row,
        raw_value,
    ) in value.items():
        parsed_row = _integer_coordinate(raw_row)

        if parsed_row is None:
            return None

        normalized_rows[parsed_row] = raw_value

    if set(normalized_rows) != set(range(GRID_SIZE)):
        return None

    result: dict[Position, float] = {}

    for row_index in range(GRID_SIZE):
        raw_row_value = normalized_rows[row_index]

        if isinstance(
            raw_row_value,
            list,
        ):
            if len(raw_row_value) != GRID_SIZE:
                return None

            for (
                column_index,
                raw_risk,
            ) in enumerate(raw_row_value):
                risk = _float_value(raw_risk)

                if risk is None:
                    return None

                result[
                    (
                        row_index,
                        column_index,
                    )
                ] = risk

            continue

        if isinstance(
            raw_row_value,
            dict,
        ):
            normalized_columns: dict[int, object] = {}

            for (
                raw_column,
                raw_risk,
            ) in raw_row_value.items():
                parsed_column = _integer_coordinate(raw_column)

                if parsed_column is None:
                    return None

                normalized_columns[parsed_column] = raw_risk

            if set(normalized_columns) != set(range(GRID_SIZE)):
                return None

            for column_index in range(GRID_SIZE):
                risk = _float_value(normalized_columns[column_index])

                if risk is None:
                    return None

                result[
                    (
                        row_index,
                        column_index,
                    )
                ] = risk

            continue

        return None

    return result


def _coordinate_key(
    value: object,
) -> Position | None:
    """
    Recognize simple serialized coordinate keys.

    Examples:
        "2,5"
        "(2,5)"
        "2:5"
        "2|5"
    """
    if not isinstance(
        value,
        str,
    ):
        return None

    cleaned = (
        value.strip()
        .replace(
            "(",
            "",
        )
        .replace(
            ")",
            "",
        )
        .replace(
            "[",
            "",
        )
        .replace(
            "]",
            "",
        )
    )

    for separator in (
        ",",
        ":",
        "|",
        "/",
    ):
        if separator not in cleaned:
            continue

        parts = [part.strip() for part in cleaned.split(separator)]

        if len(parts) != 2:
            continue

        row = _integer_coordinate(parts[0])

        column = _integer_coordinate(parts[1])

        if row is None or column is None:
            continue

        position = (
            row,
            column,
        )

        if _is_in_bounds(position):
            return position

    return None


def _coordinate_mapping_risk_map(
    value: object,
) -> dict[Position, float] | None:
    """
    Recognize mappings such as:

        {
            "0,0": 0.1,
            "0,1": 0.2,
            ...
        }
    """
    if not isinstance(
        value,
        dict,
    ):
        return None

    if not value:
        return None

    result: dict[Position, float] = {}

    for (
        raw_key,
        raw_value,
    ) in value.items():
        position = _coordinate_key(raw_key)

        if position is None:
            return None

        risk = _float_value(raw_value)

        if risk is None and isinstance(
            raw_value,
            dict,
        ):
            risk = _risk_from_mapping(
                cast(
                    dict[object, object],
                    raw_value,
                )
            )

        if risk is None:
            return None

        result[position] = risk

    return result


def _recursive_risk_maps(
    value: object,
    *,
    path: tuple[str, ...] = (),
) -> list[
    tuple[
        tuple[str, ...],
        dict[Position, float],
    ]
]:
    """
    Recursively discover recognized risk-map encodings.

    Recognition stops at the first valid map at a branch so that a
    cell-list map is not duplicated by recursively inspecting each cell.
    """
    parsers = (
        _matrix_risk_map,
        _flat_numeric_risk_map,
        _cell_list_risk_map,
        _row_mapping_risk_map,
        _coordinate_mapping_risk_map,
    )

    for parser in parsers:
        risk_map = parser(value)

        if risk_map is None:
            continue

        return [
            (
                path,
                risk_map,
            )
        ]

    found: list[
        tuple[
            tuple[str, ...],
            dict[Position, float],
        ]
    ] = []

    if isinstance(
        value,
        dict,
    ):
        for (
            key,
            child,
        ) in value.items():
            found.extend(
                _recursive_risk_maps(
                    child,
                    path=(
                        *path,
                        str(key),
                    ),
                )
            )

    elif isinstance(
        value,
        list,
    ):
        for (
            index,
            child,
        ) in enumerate(value):
            found.extend(
                _recursive_risk_maps(
                    child,
                    path=(
                        *path,
                        str(index),
                    ),
                )
            )

    return found


def _method_path_tokens(
    method_id: str,
) -> tuple[
    str,
    ...,
]:
    if method_id == "ml":
        return (
            "ml",
            "machine_learning",
            "machine-learning",
            "gradient_boosting",
            "gradient-boosting",
            "histgradient",
            "hist_gradient",
        )

    if method_id == "dl":
        return (
            "dl",
            "deep_learning",
            "deep-learning",
            "cnn",
            "conv",
            "convolution",
        )

    return (method_id,)


def _path_token_match(
    path: tuple[str, ...],
    token: str,
) -> bool:
    normalized_parts = [part.lower() for part in path]

    normalized_token = token.lower()

    return any((part == normalized_token or normalized_token in part) for part in normalized_parts)


def _select_predicted_risk(
    predictions: dict[str, object],
    *,
    city_id: str,
    method_id: str,
) -> dict[Position, float]:
    """
    Read one prediction map from the frozen Step-5/Step-6 artifact.

    Canonical serialization:

        ML:
            predictions["cities"][city_id]

        DL:
            predictions["dl"]["cities"][city_id]

    The recursive map parser is used only to decode the serialized map
    shape. It is not used to guess which method/city owns the map.
    """
    if method_id == "ml":
        raw_cities = predictions.get("cities")

        if not isinstance(
            raw_cities,
            dict,
        ):
            raise ValueError("ML prediction namespace predictions['cities'] is missing")

        if city_id not in raw_cities:
            raise ValueError(f"ML prediction map missing for city={city_id!r}")

        raw_map = raw_cities[city_id]

        namespace = "cities/" + city_id

    elif method_id == "dl":
        raw_dl = predictions.get("dl")

        if not isinstance(
            raw_dl,
            dict,
        ):
            raise ValueError("DL prediction namespace predictions['dl'] is missing")

        raw_cities = raw_dl.get("cities")

        if not isinstance(
            raw_cities,
            dict,
        ):
            raise ValueError("DL prediction namespace predictions['dl']['cities'] is missing")

        if city_id not in raw_cities:
            raise ValueError(f"DL prediction map missing for city={city_id!r}")

        raw_map = raw_cities[city_id]

        namespace = "dl/cities/" + city_id

    else:
        raise ValueError(f"predicted-risk lookup supports only ml/dl; got {method_id!r}")

    recognized = _recursive_risk_maps(
        raw_map,
        path=tuple(namespace.split("/")),
    )

    if not recognized:
        raise ValueError(
            f"{method_id.upper()} prediction map "
            f"for {city_id!r} uses an unsupported "
            "serialization shape"
        )

    exact_namespace_maps = [
        risk_map
        for (
            candidate_path,
            risk_map,
        ) in recognized
        if candidate_path == tuple(namespace.split("/"))
    ]

    if len(exact_namespace_maps) == 1:
        selected = exact_namespace_maps[0]

    elif len(recognized) == 1:
        selected = recognized[0][1]

    else:
        descriptions = [
            ("/".join(candidate_path) or "$") + f" [cells={len(risk_map)}]"
            for (
                candidate_path,
                risk_map,
            ) in recognized
        ]

        raise ValueError(f"ambiguous serialized risk map inside {namespace!r}: {descriptions}")

    if not selected:
        raise ValueError(f"{namespace}: prediction map is empty")

    for position, risk in selected.items():
        if not _is_in_bounds(position):
            raise ValueError(f"{namespace}: out-of-bounds prediction cell {position}")

        if not math.isfinite(risk):
            raise ValueError(f"{namespace}: non-finite risk at {position}")

    return selected


# ============================================================================
# Cost / heuristic
# ============================================================================


def _travel_time(
    destination: Position,
    terrain: dict[Position, str],
) -> float:
    speed = _speed(terrain[destination])

    if speed <= 0:
        raise ValueError("travel-time requested for building")

    return 1.0 / speed


def _step_cost(
    destination: Position,
    *,
    terrain: dict[Position, str],
    risk: dict[Position, float],
) -> float:
    return (
        _travel_time(
            destination,
            terrain,
        )
        + RISK_WEIGHT * risk[destination]
    )


def _heuristic(
    position: Position,
    destination: Position,
    *,
    algorithm: str,
) -> float:
    if algorithm == "dijkstra":
        return 0.0

    if algorithm != "astar":
        raise ValueError(f"unsupported algorithm: {algorithm}")

    manhattan = abs(position[0] - destination[0]) + abs(position[1] - destination[1])

    return manhattan * MINIMUM_TRAVEL_TIME_PER_STEP


# ============================================================================
# Real traced graph search
# ============================================================================


def _reconstruct(
    parents: dict[Position, Position],
    *,
    start: Position,
    destination: Position,
) -> tuple[Position, ...]:
    if destination == start:
        return (start,)

    if destination not in parents:
        raise ValueError("destination was not reached")

    reversed_path = [destination]

    current = destination

    while current != start:
        current = parents[current]

        reversed_path.append(current)

    reversed_path.reverse()

    return tuple(reversed_path)


def _path_edges(
    path: tuple[Position, ...],
) -> frozenset[
    tuple[
        Position,
        Position,
    ]
]:
    return frozenset(
        (
            path[index],
            path[index + 1],
        )
        for index in range(len(path) - 1)
    )


def _trace_search(
    *,
    city_id: str,
    method_id: TraceMethod,
    city: dict[str, object],
    risk: dict[Position, float],
    canonical_route: dict[str, object],
) -> PlannerSearchTrace:
    terrain, _observed = _city_tables(city)

    missing_risk = sorted(
        position
        for (
            position,
            terrain_kind,
        ) in terrain.items()
        if (terrain_kind != "building" and position not in risk)
    )

    if missing_risk:
        raise ValueError(
            f"{city_id}/{method_id}: predicted-risk map "
            f"is missing {len(missing_risk)} traversable cells; "
            f"first_missing={missing_risk[:10]}"
        )

    canonical_path = tuple(
        _position(value)
        for value in cast(
            list[object],
            canonical_route["path"],
        )
    )

    if len(canonical_path) < 2:
        raise ValueError(f"{city_id}/{method_id}: canonical path too short")

    start = canonical_path[0]

    destination = canonical_path[-1]

    algorithm = METHOD_ALGORITHMS[method_id]

    g_score: dict[Position, float] = {start: 0.0}

    parents: dict[Position, Position] = {}

    discovered_step: dict[Position, int] = {}

    expansion_step: dict[Position, int] = {}

    tree_edge_values: dict[
        Position,
        tuple[
            Position,
            int,
            float,
            float,
            float,
        ],
    ] = {}

    blocked: list[BlockedEdge] = []

    blocked_seen: set[
        tuple[
            Position,
            Position,
        ]
    ] = set()

    expansions: list[SearchExpansion] = []

    start_h = _heuristic(
        start,
        destination,
        algorithm=algorithm,
    )

    # Queue key:
    #
    # (f, g, row, column)
    #
    # This keeps search deterministic. The canonical route-match gate below
    # ensures this tie-breaking remains synchronized with production routing.
    frontier: list[
        tuple[
            float,
            float,
            int,
            int,
        ]
    ] = [
        (
            start_h,
            0.0,
            start[0],
            start[1],
        )
    ]

    settled: set[Position] = set()

    while frontier:
        (
            popped_f,
            popped_g,
            row,
            column,
        ) = heapq.heappop(frontier)

        current = (
            row,
            column,
        )

        current_best = g_score.get(current)

        if current_best is None:
            continue

        if not math.isclose(
            popped_g,
            current_best,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            continue

        if current in settled:
            continue

        settled.add(current)

        step = len(expansions)

        expansion_step[current] = step

        current_h = _heuristic(
            current,
            destination,
            algorithm=algorithm,
        )

        expansions.append(
            SearchExpansion(
                step=step,
                position=current,
                g_cost=current_best,
                h_cost=current_h,
                f_cost=popped_f,
                frontier_size_after_pop=len(frontier),
            )
        )

        if current == destination:
            break

        for candidate in _cardinal_positions(current):
            if not _is_in_bounds(candidate):
                continue

            candidate_terrain = terrain.get(candidate)

            if candidate_terrain is None or candidate_terrain == "building":
                blocked_key = (
                    current,
                    candidate,
                )

                if blocked_key not in blocked_seen:
                    blocked_seen.add(blocked_key)

                    blocked.append(
                        BlockedEdge(
                            parent=current,
                            blocked=candidate,
                            expansion_step=step,
                        )
                    )

                continue

            tentative_g = current_best + _step_cost(
                candidate,
                terrain=terrain,
                risk=risk,
            )

            previous_g = g_score.get(candidate)

            improves = previous_g is None or tentative_g < (previous_g - 1e-12)

            if not improves:
                continue

            g_score[candidate] = tentative_g

            parents[candidate] = current

            child_h = _heuristic(
                candidate,
                destination,
                algorithm=algorithm,
            )

            child_f = tentative_g + child_h

            discovery_index = len(discovered_step)

            discovered_step[candidate] = discovery_index

            tree_edge_values[candidate] = (
                current,
                discovery_index,
                tentative_g,
                child_h,
                child_f,
            )

            heapq.heappush(
                frontier,
                (
                    child_f,
                    tentative_g,
                    candidate[0],
                    candidate[1],
                ),
            )

    traced_path = _reconstruct(
        parents,
        start=start,
        destination=destination,
    )

    canonical_match = traced_path == canonical_path

    if not canonical_match:
        raise ValueError(
            f"{city_id}/{method_id}: "
            "instrumented search path does not "
            "match canonical routes.json path"
        )

    final_edges = _path_edges(traced_path)

    tree_edges: list[SearchTreeEdge] = []

    for child, (
        parent,
        discovery_index,
        edge_g,
        edge_h,
        edge_f,
    ) in sorted(
        tree_edge_values.items(),
        key=lambda item: (
            item[1][1],
            item[0],
        ),
    ):
        edge = (
            parent,
            child,
        )

        classification: EdgeClassification = (
            "final_route" if edge in final_edges else "explored_rejected"
        )

        tree_edges.append(
            SearchTreeEdge(
                parent=parent,
                child=child,
                discovery_step=discovery_index,
                g_cost=edge_g,
                h_cost=edge_h,
                f_cost=edge_f,
                classification=classification,
            )
        )

    return PlannerSearchTrace(
        city_id=city_id,
        method_id=method_id,
        algorithm=algorithm,
        risk_source=RISK_SOURCES[method_id],
        start=start,
        destination=destination,
        expansions=tuple(expansions),
        tree_edges=tuple(tree_edges),
        blocked_edges=tuple(blocked),
        final_path=traced_path,
        expanded_node_count=len(expansions),
        discovered_tree_edge_count=len(tree_edges),
        blocked_edge_count=len(blocked),
        route_objective=g_score[destination],
        canonical_route_match=True,
    )


# ============================================================================
# Public Step-10R tracer
# ============================================================================


def build_search_traces(
    *,
    cities_payload: dict[str, object],
    predictions_payload: dict[str, object],
    routes_payload: dict[str, object],
) -> SearchTraceBundle:
    traces: list[PlannerSearchTrace] = []

    for city_id in CITY_ORDER:
        city = _city_payload(
            cities_payload,
            city_id,
        )

        (
            _terrain,
            observed_risk,
        ) = _city_tables(city)

        for method_id in METHOD_ORDER:
            if method_id not in {
                "dijkstra",
                "ml",
                "dl",
            }:
                raise ValueError(f"unexpected headline method: {method_id}")

            typed_method = cast(
                TraceMethod,
                method_id,
            )

            if typed_method == "dijkstra":
                risk = observed_risk

            else:
                risk = _select_predicted_risk(
                    predictions_payload,
                    city_id=city_id,
                    method_id=typed_method,
                )

            canonical_route = _method_route(
                routes_payload,
                city_id,
                typed_method,
            )

            traces.append(
                _trace_search(
                    city_id=city_id,
                    method_id=typed_method,
                    city=city,
                    risk=risk,
                    canonical_route=canonical_route,
                )
            )

    return SearchTraceBundle(
        schema_version=1,
        traces=tuple(traces),
    )


# ============================================================================
# Validation
# ============================================================================


def _is_cardinal_edge(
    left: Position,
    right: Position,
) -> bool:
    return abs(left[0] - right[0]) + abs(left[1] - right[1]) == 1


def validate_trace_bundle(
    bundle: SearchTraceBundle,
    *,
    cities_payload: dict[str, object],
) -> None:
    expected_pairs = {
        (
            city_id,
            method_id,
        )
        for city_id in CITY_ORDER
        for method_id in METHOD_ORDER
    }

    actual_pairs = {
        (
            trace.city_id,
            trace.method_id,
        )
        for trace in bundle.traces
    }

    if actual_pairs != expected_pairs:
        raise ValueError("search trace does not contain exactly 3 cities x 3 methods")

    for trace in bundle.traces:
        city = _city_payload(
            cities_payload,
            trace.city_id,
        )

        terrain, _risk = _city_tables(city)

        if not trace.canonical_route_match:
            raise ValueError(f"{trace.city_id}/{trace.method_id}: canonical route mismatch")

        if not trace.expansions:
            raise ValueError("trace contains no expansions")

        if trace.expansions[0].position != trace.start:
            raise ValueError("first expansion must be start")

        if trace.expansions[-1].position != trace.destination:
            raise ValueError("last expansion must be destination")

        expanded_positions = [item.position for item in trace.expansions]

        if len(expanded_positions) != len(set(expanded_positions)):
            raise ValueError("node expanded more than once")

        for index, expansion in enumerate(trace.expansions):
            if expansion.step != index:
                raise ValueError("expansion steps are not contiguous")

            if terrain[expansion.position] == "building":
                raise ValueError("expanded a building")

        final_edges = _path_edges(trace.final_path)

        tree_edges = {
            (
                edge.parent,
                edge.child,
            )
            for edge in trace.tree_edges
        }

        if not (final_edges <= tree_edges):
            raise ValueError("final route is not contained in search tree")

        for edge in trace.tree_edges:
            if not _is_cardinal_edge(
                edge.parent,
                edge.child,
            ):
                raise ValueError("non-cardinal tree edge")

            if terrain[edge.parent] == "building" or terrain[edge.child] == "building":
                raise ValueError("tree edge crosses building")

            raw_edge = (
                edge.parent,
                edge.child,
            )

            expected_classification: EdgeClassification = (
                "final_route" if raw_edge in final_edges else "explored_rejected"
            )

            if edge.classification != expected_classification:
                raise ValueError("tree-edge classification mismatch")

        for blocked in trace.blocked_edges:
            if not _is_cardinal_edge(
                blocked.parent,
                blocked.blocked,
            ):
                raise ValueError("non-cardinal blocked edge")

            if terrain.get(blocked.blocked) != "building":
                raise ValueError("blocked edge does not terminate at a building")

            if blocked.classification != "blocked":
                raise ValueError("blocked classification mismatch")


# ============================================================================
# Serialization
# ============================================================================


def trace_payload(
    bundle: SearchTraceBundle,
) -> dict[str, object]:
    return {
        "schema_version": (bundle.schema_version),
        "classification_contract": {
            "explored_active": (
                "tree edge while the search is still being animated before final-path reveal"
            ),
            "explored_rejected": (
                "real predecessor-tree edge explored "
                "by the planner but not used by the "
                "final chosen route"
            ),
            "final_route": ("predecessor-tree edge belonging to the canonical final route"),
            "blocked": ("attempted in-bounds cardinal edge whose destination is impassable"),
        },
        "traces": [asdict(trace) for trace in bundle.traces],
    }


def write_search_traces(
    *,
    bundle: SearchTraceBundle,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            trace_payload(bundle),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path


def build_validate_write_search_traces(
    *,
    data_directory: Path,
    output_path: Path,
) -> Path:
    (
        cities,
        predictions,
        routes,
        _evaluation,
    ) = load_visual_payloads(data_directory)

    bundle = build_search_traces(
        cities_payload=cities,
        predictions_payload=predictions,
        routes_payload=routes,
    )

    validate_trace_bundle(
        bundle,
        cities_payload=cities,
    )

    return write_search_traces(
        bundle=bundle,
        output_path=output_path,
    )


def deterministic_trace_digest(
    bundle: SearchTraceBundle,
) -> str:
    canonical = json.dumps(
        trace_payload(bundle),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()
