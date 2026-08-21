"""Deterministic routing and route evaluation for Zombie Escape.

The routing engine is deliberately estimator-agnostic. A planner receives an
explicit risk lookup and never decides whether that lookup represents visible
risk, an ML prediction, a CNN prediction, or simulator-only hidden truth.

This preserves the Project 2 scientific separation between:

* estimating danger; and
* optimizing a route over the estimated costs.
"""

from __future__ import annotations

import heapq
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from itertools import pairwise
from math import inf, isfinite

from linkedin_visual_labs.projects.p04_zombie_escape.city_generator import (
    GeneratedCity,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    GridPosition,
    MethodId,
    RouteMetrics,
    RoutePlanner,
    RouteResult,
    TerrainType,
    ZombieModelError,
    ZombieProjectConfig,
)

_NUMERIC_TOLERANCE = 1e-12

RiskLookup = Callable[
    [GridPosition],
    float,
]


class RoutePlanningError(ZombieModelError):
    """Raised when a valid route cannot be planned or evaluated."""


@dataclass(frozen=True, slots=True)
class PlannedPath:
    """Algorithm-level path result before headline-method evaluation."""

    planner: RoutePlanner
    start: GridPosition
    destination: GridPosition
    path: tuple[GridPosition, ...]
    objective_cost: float
    expanded_nodes: int

    def __post_init__(self) -> None:
        if not self.path:
            raise RoutePlanningError("PlannedPath cannot be empty")

        if self.path[0] != self.start:
            raise RoutePlanningError("PlannedPath must begin at start")

        if self.path[-1] != self.destination:
            raise RoutePlanningError("PlannedPath must end at destination")

        if not isfinite(self.objective_cost) or self.objective_cost < 0.0:
            raise RoutePlanningError("PlannedPath objective_cost must be finite and non-negative")

        if self.expanded_nodes <= 0:
            raise RoutePlanningError("PlannedPath expanded_nodes must be positive")


@dataclass(frozen=True, slots=True)
class RouteEvaluation:
    """True simulator-side metrics for one legal path.

    The path cost used for planning and the true evaluation metrics are kept
    separate intentionally.

    Distance, travel time, cumulative true risk, and high-risk crossings count
    entered cells/edges and therefore exclude the starting cell.
    """

    distance: float
    travel_time: float
    true_cumulative_risk: float
    maximum_local_true_risk: float
    high_risk_cells_crossed: int
    route_valid: bool
    start: GridPosition
    destination: GridPosition

    def __post_init__(self) -> None:
        numeric_values = (
            self.distance,
            self.travel_time,
            self.true_cumulative_risk,
            self.maximum_local_true_risk,
        )

        if any(not isfinite(value) or value < 0.0 for value in numeric_values):
            raise RoutePlanningError("RouteEvaluation metrics must be finite and non-negative")

        if self.high_risk_cells_crossed < 0:
            raise RoutePlanningError("high_risk_cells_crossed must be non-negative")

    def to_route_metrics(
        self,
        *,
        oracle_true_cumulative_risk: float,
    ) -> RouteMetrics:
        """Attach oracle regret and produce the shared RouteMetrics model."""
        if not isfinite(oracle_true_cumulative_risk) or oracle_true_cumulative_risk < 0.0:
            raise RoutePlanningError("Oracle true cumulative risk must be finite and non-negative")

        regret = max(
            0.0,
            self.true_cumulative_risk - oracle_true_cumulative_risk,
        )

        return RouteMetrics(
            distance=self.distance,
            travel_time=self.travel_time,
            true_cumulative_risk=self.true_cumulative_risk,
            maximum_local_true_risk=self.maximum_local_true_risk,
            high_risk_cells_crossed=self.high_risk_cells_crossed,
            oracle_risk_regret=regret,
        )


@dataclass(frozen=True, slots=True)
class PlannerCostEngine:
    """Common planner objective used by every headline method.

    Edge cost:

        travel_time_to_enter_destination_cell
        + risk_weight * estimated_risk(destination_cell)

    The starting cell contributes no edge cost because no movement has occurred.
    """

    step_distance: float
    risk_weight: float
    speed_multipliers: Mapping[
        TerrainType,
        float,
    ]

    def __post_init__(self) -> None:
        if not isfinite(self.step_distance) or self.step_distance <= 0.0:
            raise RoutePlanningError("step_distance must be positive and finite")

        if not isfinite(self.risk_weight) or self.risk_weight < 0.0:
            raise RoutePlanningError("risk_weight must be finite and non-negative")

        if set(self.speed_multipliers) != set(TerrainType):
            raise RoutePlanningError("speed_multipliers must contain every TerrainType")

        for terrain, speed in self.speed_multipliers.items():
            if not isfinite(speed):
                raise RoutePlanningError(f"Non-finite speed for terrain {terrain.value}")

            if terrain is TerrainType.BUILDING:
                if speed != 0.0:
                    raise RoutePlanningError("Building speed must be zero")
            elif speed <= 0.0:
                raise RoutePlanningError(
                    f"Traversable terrain {terrain.value} must have positive speed"
                )

    @classmethod
    def from_config(
        cls,
        config: ZombieProjectConfig,
    ) -> PlannerCostEngine:
        """Build the shared objective directly from authoritative config."""
        return cls(
            step_distance=(config.experiment.grid.step_distance),
            risk_weight=(config.experiment.risk.planner_risk_weight),
            speed_multipliers={
                item.terrain_type: item.speed_multiplier for item in config.experiment.terrain
            },
        )

    @property
    def maximum_traversable_speed(
        self,
    ) -> float:
        """Return the fastest traversable terrain multiplier."""
        return max(
            speed
            for terrain, speed in self.speed_multipliers.items()
            if terrain is not TerrainType.BUILDING
        )

    def travel_time_to_enter(
        self,
        city: GeneratedCity,
        position: GridPosition,
    ) -> float:
        """Return travel time for one cardinal step into a cell."""
        cell = city.cell(position)

        if cell.terrain is TerrainType.BUILDING:
            raise RoutePlanningError("Cannot compute entry travel time for a building")

        speed = self.speed_multipliers[cell.terrain]

        if speed <= 0.0:
            raise RoutePlanningError("Traversable cell has non-positive speed")

        return self.step_distance / speed

    def edge_cost(
        self,
        city: GeneratedCity,
        destination: GridPosition,
        risk_lookup: RiskLookup,
    ) -> float:
        """Return common planner cost for entering one adjacent cell."""
        risk = _validated_risk(
            risk_lookup(destination),
            destination,
        )

        return (
            self.travel_time_to_enter(
                city,
                destination,
            )
            + self.risk_weight * risk
        )

    def path_objective_cost(
        self,
        city: GeneratedCity,
        path: tuple[GridPosition, ...],
        risk_lookup: RiskLookup,
    ) -> float:
        """Compute exact common objective for an existing legal path."""
        validate_path_legality(
            city,
            path,
        )

        return sum(
            self.edge_cost(
                city,
                destination,
                risk_lookup,
            )
            for destination in path[1:]
        )

    def heuristic_time_lower_bound(
        self,
        position: GridPosition,
        destination: GridPosition,
    ) -> float:
        """Admissible A* heuristic using only minimum possible travel time.

        Zombie risk is non-negative, so excluding risk from the heuristic
        cannot overestimate the true remaining common-objective cost.
        """
        manhattan_steps = abs(destination.row - position.row) + abs(
            destination.column - position.column
        )

        return manhattan_steps * self.step_distance / self.maximum_traversable_speed


def observed_risk_lookup(
    city: GeneratedCity,
) -> RiskLookup:
    """Return the visible-risk estimator used by the Dijkstra baseline."""

    def lookup(
        position: GridPosition,
    ) -> float:
        return city.cell(position).observed_risk

    return lookup


def true_risk_lookup(
    city: GeneratedCity,
) -> RiskLookup:
    """Return simulator-only hidden truth for explicit Oracle use."""

    def lookup(
        position: GridPosition,
    ) -> float:
        return city.cell(position).true_risk

    return lookup


def mapping_risk_lookup(
    risk_by_position: Mapping[
        GridPosition,
        float,
    ],
) -> RiskLookup:
    """Adapt a complete predicted-risk mapping to the planner interface."""

    def lookup(
        position: GridPosition,
    ) -> float:
        try:
            return risk_by_position[position]
        except KeyError as exc:
            raise RoutePlanningError(f"Estimated-risk map is missing position {position}") from exc

    return lookup


def dijkstra_shortest_path(
    city: GeneratedCity,
    *,
    cost_engine: PlannerCostEngine,
    risk_lookup: RiskLookup,
    start: GridPosition | None = None,
    destination: GridPosition | None = None,
) -> PlannedPath:
    """Find the exact minimum common-objective path using Dijkstra."""
    resolved_start, resolved_destination = _resolve_endpoints(
        city,
        start=start,
        destination=destination,
    )

    return _best_first_search(
        city,
        cost_engine=cost_engine,
        risk_lookup=risk_lookup,
        start=resolved_start,
        destination=resolved_destination,
        planner=RoutePlanner.DIJKSTRA,
        use_heuristic=False,
    )


def astar_shortest_path(
    city: GeneratedCity,
    *,
    cost_engine: PlannerCostEngine,
    risk_lookup: RiskLookup,
    start: GridPosition | None = None,
    destination: GridPosition | None = None,
) -> PlannedPath:
    """Find the exact minimum common-objective path using admissible A*."""
    resolved_start, resolved_destination = _resolve_endpoints(
        city,
        start=start,
        destination=destination,
    )

    return _best_first_search(
        city,
        cost_engine=cost_engine,
        risk_lookup=risk_lookup,
        start=resolved_start,
        destination=resolved_destination,
        planner=RoutePlanner.ASTAR,
        use_heuristic=True,
    )


def observed_dijkstra_route(
    city: GeneratedCity,
    *,
    cost_engine: PlannerCostEngine,
) -> PlannedPath:
    """Run the headline Dijkstra baseline using observed visible risk."""
    return dijkstra_shortest_path(
        city,
        cost_engine=cost_engine,
        risk_lookup=observed_risk_lookup(city),
    )


def oracle_astar_route(
    city: GeneratedCity,
    *,
    cost_engine: PlannerCostEngine,
) -> PlannedPath:
    """Run simulator-only perfect-information Oracle routing."""
    return astar_shortest_path(
        city,
        cost_engine=cost_engine,
        risk_lookup=true_risk_lookup(city),
    )


def validate_path_legality(
    city: GeneratedCity,
    path: tuple[GridPosition, ...],
    *,
    expected_start: GridPosition | None = None,
    expected_destination: GridPosition | None = None,
) -> None:
    """Require a path to be bounded, traversable, cardinal, and endpoint-safe."""
    if not path:
        raise RoutePlanningError("Route path cannot be empty")

    start = city.definition.start if expected_start is None else expected_start

    destination = (
        city.definition.destination if expected_destination is None else expected_destination
    )

    if path[0] != start:
        raise RoutePlanningError("Route path does not begin at expected start")

    if path[-1] != destination:
        raise RoutePlanningError("Route path does not end at expected destination")

    for position in path:
        if not city.grid.contains(position):
            raise RoutePlanningError(f"Route contains out-of-bounds position {position}")

        if not city.is_traversable(position):
            raise RoutePlanningError(f"Route crosses impassable cell {position}")

    for first, second in pairwise(path):
        row_delta = abs(first.row - second.row)

        column_delta = abs(first.column - second.column)

        if row_delta + column_delta != 1:
            raise RoutePlanningError(
                f"Route contains a non-cardinal or non-adjacent move: {first} -> {second}"
            )


def compute_route_evaluation(
    city: GeneratedCity,
    path: tuple[GridPosition, ...],
    *,
    cost_engine: PlannerCostEngine,
) -> RouteEvaluation:
    """Evaluate one route against simulator-only true risk."""
    validate_path_legality(
        city,
        path,
    )

    entered = path[1:]

    distance = len(entered) * cost_engine.step_distance

    travel_time = sum(
        cost_engine.travel_time_to_enter(
            city,
            position,
        )
        for position in entered
    )

    true_cumulative_risk = sum(city.cell(position).true_risk for position in entered)

    maximum_local_true_risk = max(
        (city.cell(position).true_risk for position in entered),
        default=0.0,
    )

    high_risk_threshold = _infer_high_risk_threshold(city)

    high_risk_cells_crossed = sum(
        1 for position in entered if (city.cell(position).true_risk >= high_risk_threshold)
    )

    return RouteEvaluation(
        distance=distance,
        travel_time=travel_time,
        true_cumulative_risk=true_cumulative_risk,
        maximum_local_true_risk=maximum_local_true_risk,
        high_risk_cells_crossed=high_risk_cells_crossed,
        route_valid=True,
        start=path[0],
        destination=path[-1],
    )


def compute_route_evaluation_with_threshold(
    city: GeneratedCity,
    path: tuple[GridPosition, ...],
    *,
    cost_engine: PlannerCostEngine,
    high_risk_threshold: float,
) -> RouteEvaluation:
    """Evaluate a route with the authoritative explicit high-risk threshold."""
    if not isfinite(high_risk_threshold) or not 0.0 <= high_risk_threshold <= 1.0:
        raise RoutePlanningError("high_risk_threshold must lie in [0, 1]")

    validate_path_legality(
        city,
        path,
    )

    entered = path[1:]

    return RouteEvaluation(
        distance=(len(entered) * cost_engine.step_distance),
        travel_time=sum(
            cost_engine.travel_time_to_enter(
                city,
                position,
            )
            for position in entered
        ),
        true_cumulative_risk=sum(city.cell(position).true_risk for position in entered),
        maximum_local_true_risk=max(
            (city.cell(position).true_risk for position in entered),
            default=0.0,
        ),
        high_risk_cells_crossed=sum(
            1 for position in entered if (city.cell(position).true_risk >= high_risk_threshold)
        ),
        route_valid=True,
        start=path[0],
        destination=path[-1],
    )


def build_headline_route_result(
    city: GeneratedCity,
    *,
    method_id: MethodId,
    planned_path: PlannedPath,
    cost_engine: PlannerCostEngine,
    high_risk_threshold: float,
    oracle_true_cumulative_risk: float,
) -> RouteResult:
    """Build the shared headline RouteResult after Oracle comparison."""
    evaluation = compute_route_evaluation_with_threshold(
        city,
        planned_path.path,
        cost_engine=cost_engine,
        high_risk_threshold=high_risk_threshold,
    )

    return RouteResult(
        city_id=city.city_id,
        method_id=method_id,
        start=planned_path.start,
        destination=planned_path.destination,
        path=planned_path.path,
        route_valid=evaluation.route_valid,
        metrics=evaluation.to_route_metrics(
            oracle_true_cumulative_risk=(oracle_true_cumulative_risk)
        ),
    )


def _best_first_search(
    city: GeneratedCity,
    *,
    cost_engine: PlannerCostEngine,
    risk_lookup: RiskLookup,
    start: GridPosition,
    destination: GridPosition,
    planner: RoutePlanner,
    use_heuristic: bool,
) -> PlannedPath:
    """Shared deterministic Dijkstra/A* implementation."""
    best_cost: dict[
        GridPosition,
        float,
    ] = {
        start: 0.0,
    }

    came_from: dict[
        GridPosition,
        GridPosition,
    ] = {}

    start_priority = (
        cost_engine.heuristic_time_lower_bound(
            start,
            destination,
        )
        if use_heuristic
        else 0.0
    )

    frontier: list[
        tuple[
            float,
            float,
            int,
            int,
            GridPosition,
        ]
    ] = [
        (
            start_priority,
            0.0,
            start.row,
            start.column,
            start,
        )
    ]

    expanded_nodes = 0

    while frontier:
        (
            _priority,
            queued_cost,
            _row,
            _column,
            current,
        ) = heapq.heappop(frontier)

        known_cost = best_cost.get(
            current,
            inf,
        )

        if queued_cost > known_cost + _NUMERIC_TOLERANCE:
            continue

        expanded_nodes += 1

        if current == destination:
            path = _reconstruct_path(
                came_from,
                start=start,
                destination=destination,
            )

            exact_cost = cost_engine.path_objective_cost(
                city,
                path,
                risk_lookup,
            )

            return PlannedPath(
                planner=planner,
                start=start,
                destination=destination,
                path=path,
                objective_cost=exact_cost,
                expanded_nodes=expanded_nodes,
            )

        for neighbor in city.traversable_neighbors(current):
            candidate_cost = known_cost + cost_engine.edge_cost(
                city,
                neighbor,
                risk_lookup,
            )

            previous_cost = best_cost.get(
                neighbor,
                inf,
            )

            if not _strictly_better(
                candidate_cost,
                previous_cost,
            ):
                continue

            best_cost[neighbor] = candidate_cost

            came_from[neighbor] = current

            heuristic = (
                cost_engine.heuristic_time_lower_bound(
                    neighbor,
                    destination,
                )
                if use_heuristic
                else 0.0
            )

            priority = candidate_cost + heuristic

            heapq.heappush(
                frontier,
                (
                    priority,
                    candidate_cost,
                    neighbor.row,
                    neighbor.column,
                    neighbor,
                ),
            )

    raise RoutePlanningError(f"No legal route exists from {start} to {destination}")


def _strictly_better(
    candidate: float,
    previous: float,
) -> bool:
    """Deterministic relaxation rule.

    Equal-cost alternatives never replace the first canonical predecessor.
    This, together with canonical neighbor order and row/column heap keys,
    produces deterministic exact routes.
    """
    return candidate < previous - _NUMERIC_TOLERANCE


def _reconstruct_path(
    came_from: Mapping[
        GridPosition,
        GridPosition,
    ],
    *,
    start: GridPosition,
    destination: GridPosition,
) -> tuple[GridPosition, ...]:
    current = destination

    reversed_path = [current]

    while current != start:
        try:
            current = came_from[current]
        except KeyError as exc:
            raise RoutePlanningError("Route predecessor chain is incomplete") from exc

        reversed_path.append(current)

    reversed_path.reverse()

    return tuple(reversed_path)


def _resolve_endpoints(
    city: GeneratedCity,
    *,
    start: GridPosition | None,
    destination: GridPosition | None,
) -> tuple[
    GridPosition,
    GridPosition,
]:
    resolved_start = city.definition.start if start is None else start

    resolved_destination = city.definition.destination if destination is None else destination

    for label, position in (
        (
            "start",
            resolved_start,
        ),
        (
            "destination",
            resolved_destination,
        ),
    ):
        if not city.grid.contains(position):
            raise RoutePlanningError(f"Route {label} lies outside city grid")

        if not city.is_traversable(position):
            raise RoutePlanningError(f"Route {label} is not traversable")

    return (
        resolved_start,
        resolved_destination,
    )


def _validated_risk(
    value: float,
    position: GridPosition,
) -> float:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise RoutePlanningError(
            f"Estimated risk must lie in [0, 1] at {position}; received {value!r}"
        )

    return value


def _infer_high_risk_threshold(
    city: GeneratedCity,
) -> float:
    """Deprecated-safe internal fallback.

    The authoritative Project 2 threshold is supplied explicitly through
    compute_route_evaluation_with_threshold(). This fallback exists only for
    low-level standalone evaluation and uses the frozen Step 1 value.
    """
    del city

    return 0.65
