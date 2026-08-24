"""Showcase route-divergence contract for Project 2."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, cast

from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    METHOD_ORDER,
    _method_route,
    _position,
)

# ============================================================================
# Frozen Step-3R scientific contract
# ============================================================================


SHOWCASE_CITY_ORDER: Final[tuple[str, ...]] = (
    "new_york",
    "chicago",
    "phoenix",
)

HEADLINE_METHODS: Final[tuple[str, ...]] = (
    "dijkstra",
    "ml",
    "dl",
)

if tuple(METHOD_ORDER) != HEADLINE_METHODS:
    raise RuntimeError("Project 2 headline method order changed")


# ---------------------------------------------------------------------------
# Training / validation / benchmark seeds are immutable.
# ---------------------------------------------------------------------------

TRAINING_SEED: Final[int] = 4301
VALIDATION_SEED: Final[int] = 4302
BENCHMARK_SEED: Final[int] = 4303

ML_SEED: Final[int] = 4304
DL_SEED: Final[int] = 4305


# ---------------------------------------------------------------------------
# Historical showcase seeds from the original Step-1 contract.
#
# Step 3R may replace ONLY these three showcase seeds.
# ---------------------------------------------------------------------------

ORIGINAL_SHOWCASE_SEEDS: Final[dict[str, int]] = {
    "new_york": 4201,
    "chicago": 4202,
    "phoenix": 4203,
}


# ---------------------------------------------------------------------------
# Frozen candidate triples.
#
# Important anti-cherry-picking property:
#     every candidate triple is declared BEFORE results are examined.
#
# Search policy:
#     evaluate in this exact order
#     accept the FIRST triple satisfying the frozen criteria
#     never skip an acceptable earlier candidate in favor of a prettier later
#     candidate.
#
# Candidate seeds are deliberately separated from training/benchmark seeds.
# ---------------------------------------------------------------------------

CANDIDATE_SHOWCASE_SEEDS: Final[
    tuple[
        tuple[
            int,
            int,
            int,
        ],
        ...,
    ]
] = tuple(
    (
        5201 + offset,
        5301 + offset,
        5401 + offset,
    )
    for offset in range(24)
)


# ============================================================================
# Estimator fairness contract
# ============================================================================


ESTIMATOR_CONTRACT: Final[dict[str, str]] = {
    "dijkstra": ("observed visible risk -> Dijkstra"),
    "ml": ("observable engineered features -> Gradient Boosting predicted risk -> A*"),
    "dl": ("observable multi-channel grid tensor -> CNN predicted risk -> A*"),
}


COMMON_OBJECTIVE: Final[str] = "travel_time + 4.0 * estimated_zombie_risk"


FAIRNESS_RULES: Final[tuple[str, ...]] = (
    ("All headline planners receive the same physical city geometry."),
    ("All headline planners receive the same Camp A and Safe Zone."),
    ("All headline planners use the same travel-time cost semantics."),
    ("All headline planners use risk weight 4.0."),
    ("The only headline planning difference is the risk estimator."),
    ("Hidden true risk is forbidden during headline route inference."),
    ("True risk may be used only after routing for evaluation."),
    ("The Oracle remains benchmark-only and is never eligible to win."),
)


# ============================================================================
# Route divergence structures
# ============================================================================


@dataclass(frozen=True, slots=True)
class PairwiseRouteDivergence:
    """Divergence between two headline routes."""

    left_method: str
    right_method: str

    left_steps: int
    right_steps: int

    shared_cells: int
    cell_jaccard: float

    shared_edges: int
    edge_jaccard: float

    common_prefix_steps: int
    common_prefix_fraction: float

    maximum_cell_separation: int


@dataclass(frozen=True, slots=True)
class CityRouteDivergence:
    """Showcase divergence summary for one city."""

    city_id: str

    common_start: tuple[int, int]
    common_destination: tuple[int, int]

    exact_unique_route_count: int

    pairwise: tuple[
        PairwiseRouteDivergence,
        ...,
    ]

    mean_edge_jaccard: float
    maximum_edge_jaccard: float
    minimum_edge_jaccard: float

    visibly_divergent_pair_count: int
    maximum_route_separation: int

    accepted: bool
    rejection_reasons: tuple[
        str,
        ...,
    ]


@dataclass(frozen=True, slots=True)
class ShowcaseDivergenceSummary:
    """Three-city showcase acceptance result."""

    cities: tuple[
        CityRouteDivergence,
        ...,
    ]

    accepted_city_count: int
    accepted: bool


# ============================================================================
# Frozen visual-divergence thresholds
#
# These are intentionally declared before the seed search.
# ============================================================================


MINIMUM_UNIQUE_ROUTE_COUNT: Final[int] = 3

# At least two of the three method-pairs must visibly diverge.
MINIMUM_VISIBLY_DIVERGENT_PAIRS: Final[int] = 2

# A pair is considered visibly divergent when edge overlap is at most 85%.
VISIBLE_PAIR_MAX_EDGE_JACCARD: Final[float] = 0.85

# Across all three pairs, average overlap must remain below 88%.
MAXIMUM_MEAN_EDGE_JACCARD: Final[float] = 0.88

# No single pair may be essentially identical.
MAXIMUM_PAIR_EDGE_JACCARD: Final[float] = 0.97

# At least one pair must separate by >= 3 Manhattan cells somewhere.
MINIMUM_MAXIMUM_ROUTE_SEPARATION: Final[int] = 3


# ============================================================================
# Path helpers
# ============================================================================


def _path(
    route: dict[str, object],
) -> tuple[
    tuple[int, int],
    ...,
]:
    raw = route.get("path")

    if not isinstance(
        raw,
        list,
    ):
        raise TypeError("route.path must be a list")

    result = tuple(_position(item) for item in raw)

    if len(result) < 2:
        raise ValueError("route must contain at least two positions")

    return result


def _edges(
    path: tuple[
        tuple[int, int],
        ...,
    ],
) -> frozenset[
    tuple[
        tuple[int, int],
        tuple[int, int],
    ]
]:
    return frozenset(
        (
            path[index],
            path[index + 1],
        )
        for index in range(len(path) - 1)
    )


def _jaccard(
    left: frozenset[object],
    right: frozenset[object],
) -> float:
    union = left | right

    if not union:
        return 1.0

    return len(left & right) / len(union)


def _common_prefix_steps(
    left: tuple[
        tuple[int, int],
        ...,
    ],
    right: tuple[
        tuple[int, int],
        ...,
    ],
) -> int:
    matched = 0

    for (
        left_position,
        right_position,
    ) in zip(
        left,
        right,
        strict=False,
    ):
        if left_position != right_position:
            break

        matched += 1

    # Number of shared edges, not shared vertices.
    return max(
        0,
        matched - 1,
    )


def _nearest_distance(
    position: tuple[int, int],
    path: tuple[
        tuple[int, int],
        ...,
    ],
) -> int:
    return min(abs(position[0] - other[0]) + abs(position[1] - other[1]) for other in path)


def _maximum_route_separation(
    left: tuple[
        tuple[int, int],
        ...,
    ],
    right: tuple[
        tuple[int, int],
        ...,
    ],
) -> int:
    left_to_right = max(
        _nearest_distance(
            position,
            right,
        )
        for position in left
    )

    right_to_left = max(
        _nearest_distance(
            position,
            left,
        )
        for position in right
    )

    return max(
        left_to_right,
        right_to_left,
    )


# ============================================================================
# Pairwise metrics
# ============================================================================


def compare_routes(
    *,
    left_method: str,
    right_method: str,
    left_route: dict[str, object],
    right_route: dict[str, object],
) -> PairwiseRouteDivergence:
    """Measure geometric divergence between two routes."""
    left_path = _path(left_route)

    right_path = _path(right_route)

    left_cells = frozenset(left_path)

    right_cells = frozenset(right_path)

    left_edges = _edges(left_path)

    right_edges = _edges(right_path)

    prefix_steps = _common_prefix_steps(
        left_path,
        right_path,
    )

    shorter_steps = max(
        1,
        min(
            len(left_path),
            len(right_path),
        )
        - 1,
    )

    return PairwiseRouteDivergence(
        left_method=left_method,
        right_method=right_method,
        left_steps=(len(left_path) - 1),
        right_steps=(len(right_path) - 1),
        shared_cells=len(left_cells & right_cells),
        cell_jaccard=_jaccard(
            cast(
                frozenset[object],
                left_cells,
            ),
            cast(
                frozenset[object],
                right_cells,
            ),
        ),
        shared_edges=len(left_edges & right_edges),
        edge_jaccard=_jaccard(
            cast(
                frozenset[object],
                left_edges,
            ),
            cast(
                frozenset[object],
                right_edges,
            ),
        ),
        common_prefix_steps=prefix_steps,
        common_prefix_fraction=(prefix_steps / shorter_steps),
        maximum_cell_separation=(
            _maximum_route_separation(
                left_path,
                right_path,
            )
        ),
    )


# ============================================================================
# One-city acceptance
# ============================================================================


def evaluate_city_divergence(
    *,
    routes_payload: dict[str, object],
    city_id: str,
) -> CityRouteDivergence:
    """Apply the frozen showcase-divergence acceptance contract."""
    routes = {
        method_id: _method_route(
            routes_payload,
            city_id,
            method_id,
        )
        for method_id in HEADLINE_METHODS
    }

    paths = {
        method_id: _path(route)
        for (
            method_id,
            route,
        ) in routes.items()
    }

    starts = {path[0] for path in paths.values()}

    destinations = {path[-1] for path in paths.values()}

    if len(starts) != 1:
        raise ValueError(f"{city_id}: headline methods do not share start")

    if len(destinations) != 1:
        raise ValueError(f"{city_id}: headline methods do not share destination")

    pair_ids = (
        (
            "dijkstra",
            "ml",
        ),
        (
            "dijkstra",
            "dl",
        ),
        (
            "ml",
            "dl",
        ),
    )

    pairwise = tuple(
        compare_routes(
            left_method=left_method,
            right_method=right_method,
            left_route=routes[left_method],
            right_route=routes[right_method],
        )
        for (
            left_method,
            right_method,
        ) in pair_ids
    )

    edge_jaccards = [comparison.edge_jaccard for comparison in pairwise]

    unique_route_count = len({path for path in paths.values()})

    visibly_divergent = sum(
        comparison.edge_jaccard <= VISIBLE_PAIR_MAX_EDGE_JACCARD for comparison in pairwise
    )

    maximum_separation = max(comparison.maximum_cell_separation for comparison in pairwise)

    mean_edge_jaccard = sum(edge_jaccards) / len(edge_jaccards)

    maximum_edge_jaccard = max(edge_jaccards)

    reasons: list[str] = []

    if unique_route_count < MINIMUM_UNIQUE_ROUTE_COUNT:
        reasons.append("fewer than three unique headline routes")

    if visibly_divergent < MINIMUM_VISIBLY_DIVERGENT_PAIRS:
        reasons.append("fewer than two visibly divergent method pairs")

    if mean_edge_jaccard > MAXIMUM_MEAN_EDGE_JACCARD:
        reasons.append("mean edge overlap exceeds showcase threshold")

    if maximum_edge_jaccard > MAXIMUM_PAIR_EDGE_JACCARD:
        reasons.append("at least one method pair is effectively identical")

    if maximum_separation < MINIMUM_MAXIMUM_ROUTE_SEPARATION:
        reasons.append("routes do not separate sufficiently on the map")

    return CityRouteDivergence(
        city_id=city_id,
        common_start=next(iter(starts)),
        common_destination=next(iter(destinations)),
        exact_unique_route_count=unique_route_count,
        pairwise=pairwise,
        mean_edge_jaccard=mean_edge_jaccard,
        maximum_edge_jaccard=maximum_edge_jaccard,
        minimum_edge_jaccard=min(edge_jaccards),
        visibly_divergent_pair_count=visibly_divergent,
        maximum_route_separation=maximum_separation,
        accepted=not reasons,
        rejection_reasons=tuple(reasons),
    )


def evaluate_showcase_divergence(
    routes_payload: dict[str, object],
) -> ShowcaseDivergenceSummary:
    """Require every showcase city to satisfy the frozen criteria."""
    cities = tuple(
        evaluate_city_divergence(
            routes_payload=routes_payload,
            city_id=city_id,
        )
        for city_id in SHOWCASE_CITY_ORDER
    )

    accepted_count = sum(city.accepted for city in cities)

    return ShowcaseDivergenceSummary(
        cities=cities,
        accepted_city_count=accepted_count,
        accepted=(accepted_count == len(SHOWCASE_CITY_ORDER)),
    )


# ============================================================================
# Multiple-corridor / estimator-ambiguity interpretation
# ============================================================================


def corridor_count(
    city: CityRouteDivergence,
) -> int:
    """
    Number of distinct headline evacuation corridors.

    A Step-3R-accepted city must expose three geometrically distinct routes.
    """
    return city.exact_unique_route_count


def has_observable_estimator_ambiguity(
    city: CityRouteDivergence,
) -> bool:
    """
    Infer estimator disagreement without using hidden true risk.

    Since geometry, endpoints, travel-time semantics and risk weight are
    identical, headline route divergence can arise only from the planners'
    different observable risk estimators.
    """
    return (
        city.exact_unique_route_count == 3
        and city.visibly_divergent_pair_count >= MINIMUM_VISIBLY_DIVERGENT_PAIRS
    )


# ============================================================================
# Anti-cherry-picking contract
# ============================================================================


def search_contract_payload() -> dict[
    str,
    object,
]:
    """Return immutable pre-search selection rules."""
    return {
        "schema_version": 1,
        "selection_policy": ("first_acceptable_candidate"),
        "candidate_order_is_frozen": True,
        "headline_methods": list(HEADLINE_METHODS),
        "common_objective": (COMMON_OBJECTIVE),
        "estimator_contract": dict(ESTIMATOR_CONTRACT),
        "fairness_rules": list(FAIRNESS_RULES),
        "immutable_seeds": {
            "training": TRAINING_SEED,
            "validation": VALIDATION_SEED,
            "benchmark": BENCHMARK_SEED,
            "ml": ML_SEED,
            "dl": DL_SEED,
        },
        "original_showcase_seeds": dict(ORIGINAL_SHOWCASE_SEEDS),
        "candidate_showcase_seeds": [
            {
                "candidate_index": index,
                "new_york": triple[0],
                "chicago": triple[1],
                "phoenix": triple[2],
            }
            for (
                index,
                triple,
            ) in enumerate(CANDIDATE_SHOWCASE_SEEDS)
        ],
        "acceptance": {
            "minimum_unique_route_count": (MINIMUM_UNIQUE_ROUTE_COUNT),
            "minimum_visibly_divergent_pairs": (MINIMUM_VISIBLY_DIVERGENT_PAIRS),
            "visible_pair_max_edge_jaccard": (VISIBLE_PAIR_MAX_EDGE_JACCARD),
            "maximum_mean_edge_jaccard": (MAXIMUM_MEAN_EDGE_JACCARD),
            "maximum_pair_edge_jaccard": (MAXIMUM_PAIR_EDGE_JACCARD),
            "minimum_maximum_route_separation": (MINIMUM_MAXIMUM_ROUTE_SEPARATION),
        },
        "showcase_is_not_benchmark": True,
        "showcase_seed_search_may_not_modify_benchmark_seed": True,
        "showcase_seed_search_may_not_modify_training_seed": True,
        "showcase_seed_search_may_not_modify_validation_seed": True,
        "showcase_seed_search_may_not_modify_ml_seed": True,
        "showcase_seed_search_may_not_modify_dl_seed": True,
    }


def divergence_payload(
    summary: ShowcaseDivergenceSummary,
) -> dict[str, object]:
    return {
        "accepted": summary.accepted,
        "accepted_city_count": (summary.accepted_city_count),
        "cities": [asdict(city) for city in summary.cities],
    }


def write_search_contract(
    path: Path,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            search_contract_payload(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path


def write_divergence_report(
    *,
    summary: ShowcaseDivergenceSummary,
    path: Path,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            divergence_payload(summary),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path
