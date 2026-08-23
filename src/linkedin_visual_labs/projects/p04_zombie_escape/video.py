"""Project 2 Revised Step 9R — deterministic 60-second comparison animation.

The animation is a presentation layer only.

Authoritative inputs:
- cities.json
- routes.json
- search_traces.json
- route_comparison.csv
- overall_comparison.csv

The renderer never recomputes routing or evaluation results.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Final

from PIL import Image, ImageDraw, ImageFont

from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    _cell_position,
    _cells,
    _city_payload,
    _method_route,
    _observed_risk,
    _position,
    _terrain_name,
    load_visual_payloads,
)

# ============================================================================
# 9R.1 — Frozen global schedule
# ============================================================================

WIDTH: Final[int] = 1080
HEIGHT: Final[int] = 1080

FPS: Final[int] = 30
DURATION_SECONDS: Final[float] = 60.0
FRAME_COUNT: Final[int] = int(FPS * DURATION_SECONDS)

OPENING_START: Final[float] = 0.0
OPENING_END: Final[float] = 8.0

NEW_YORK_START: Final[float] = 8.0
NEW_YORK_END: Final[float] = 23.0

CHICAGO_START: Final[float] = 23.0
CHICAGO_END: Final[float] = 38.0

PHOENIX_START: Final[float] = 38.0
PHOENIX_END: Final[float] = 53.0

SUMMARY_START: Final[float] = 53.0
SUMMARY_END: Final[float] = 60.0

CITY_DURATION: Final[float] = 15.0

CITY_SCHEDULE: Final[
    tuple[
        tuple[
            str,
            float,
            float,
        ],
        ...,
    ]
] = (
    (
        "new_york",
        NEW_YORK_START,
        NEW_YORK_END,
    ),
    (
        "chicago",
        CHICAGO_START,
        CHICAGO_END,
    ),
    (
        "phoenix",
        PHOENIX_START,
        PHOENIX_END,
    ),
)


# ============================================================================
# 9R.2 — Frozen 45 / 330 / 330 / 330 / 45 geometry
# ============================================================================

HEADING_HEIGHT: Final[int] = 45
DIJKSTRA_HEIGHT: Final[int] = 330
ML_HEIGHT: Final[int] = 330
DL_HEIGHT: Final[int] = 330
RESULT_HEIGHT: Final[int] = 45

DIJKSTRA_TOP: Final[int] = HEADING_HEIGHT
ML_TOP: Final[int] = DIJKSTRA_TOP + DIJKSTRA_HEIGHT
DL_TOP: Final[int] = ML_TOP + ML_HEIGHT
RESULT_TOP: Final[int] = DL_TOP + DL_HEIGHT

assert HEADING_HEIGHT + DIJKSTRA_HEIGHT + ML_HEIGHT + DL_HEIGHT + RESULT_HEIGHT == HEIGHT

METHOD_GEOMETRY: Final[
    dict[
        str,
        tuple[
            int,
            int,
        ],
    ]
] = {
    "dijkstra": (
        DIJKSTRA_TOP,
        DIJKSTRA_HEIGHT,
    ),
    "ml": (
        ML_TOP,
        ML_HEIGHT,
    ),
    "dl": (
        DL_TOP,
        DL_HEIGHT,
    ),
}


# ============================================================================
# City-local 15-second animation schedule
# ============================================================================

CITY_BASE_END: Final[float] = 1.5
CITY_SEARCH_END: Final[float] = 9.0
CITY_COMPLETE_TREE_END: Final[float] = 11.0
CITY_REJECT_FADE_END: Final[float] = 12.5
CITY_FINAL_ROUTE_END: Final[float] = 14.0
CITY_RESULT_END: Final[float] = 15.0


# ============================================================================
# Visual contract
#
# Colors are centralized here for this one animation asset rather than being
# scattered across drawing functions.
# ============================================================================

BACKGROUND: Final[tuple[int, int, int]] = (
    10,
    13,
    18,
)

PANEL_BACKGROUND: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    17,
    22,
    29,
)

PANEL_BORDER: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    60,
    69,
    80,
)

ROAD: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    63,
    69,
    77,
)

ARTERIAL: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    85,
    93,
    104,
)

SLOW: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    52,
    59,
    51,
)

OPEN_TERRAIN: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    38,
    47,
    42,
)

BUILDING: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    25,
    29,
    35,
)

BUILDING_EDGE: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    45,
    50,
    59,
)

TEXT: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    239,
    243,
    248,
)

MUTED_TEXT: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    156,
    165,
    177,
)

ACTIVE_SEARCH: Final[
    tuple[
        int,
        int,
        int,
        int,
    ]
] = (
    90,
    207,
    255,
    205,
)

FRONTIER: Final[
    tuple[
        int,
        int,
        int,
        int,
    ]
] = (
    250,
    216,
    92,
    235,
)

REJECTED: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    245,
    75,
    75,
)

FINAL_ROUTE: Final[
    tuple[
        int,
        int,
        int,
        int,
    ]
] = (
    72,
    255,
    116,
    255,
)

BLOCKED_MARK: Final[
    tuple[
        int,
        int,
        int,
        int,
    ]
] = (
    132,
    94,
    94,
    150,
)

RISK_RED: Final[
    tuple[
        int,
        int,
        int,
        int,
    ]
] = (
    255,
    72,
    72,
    80,
)

START_COLOR: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    108,
    188,
    255,
)

DESTINATION_COLOR: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    255,
    222,
    80,
)

ZOMBIE_BODY: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    136,
    202,
    104,
)

ZOMBIE_EYE: Final[
    tuple[
        int,
        int,
        int,
    ]
] = (
    20,
    28,
    20,
)


CITY_LABELS: Final[
    dict[
        str,
        str,
    ]
] = {
    "new_york": ("NEW YORK"),
    "chicago": ("CHICAGO"),
    "phoenix": ("PHOENIX"),
}

METHOD_LABELS: Final[
    dict[
        str,
        str,
    ]
] = {
    "dijkstra": ("DIJKSTRA · observed risk"),
    "ml": ("ML + A* · predicted risk"),
    "dl": ("CNN + A* · predicted risk"),
}

METHOD_SHORT_LABELS: Final[
    dict[
        str,
        str,
    ]
] = {
    "dijkstra": ("DIJKSTRA"),
    "ml": ("ML + A*"),
    "dl": ("CNN + A*"),
}


# ============================================================================
# Typed data contracts
# ============================================================================

Position = tuple[
    int,
    int,
]


@dataclass(
    frozen=True,
    slots=True,
)
class TraceEdge:
    """One persisted Step-10R predecessor-tree edge."""

    parent: Position
    child: Position

    parent_expansion_step: int

    classification: str


@dataclass(
    frozen=True,
    slots=True,
)
class BlockedTraceEdge:
    """One real attempted transition into an impassable cell."""

    parent: Position
    child: Position

    expansion_step: int


@dataclass(
    frozen=True,
    slots=True,
)
class TraceView:
    """Typed presentation view over one Step-10R trace."""

    city_id: str
    method_id: str

    expansions: tuple[
        Position,
        ...,
    ]

    tree_edges: tuple[
        TraceEdge,
        ...,
    ]

    blocked_edges: tuple[
        BlockedTraceEdge,
        ...,
    ]

    final_path: tuple[
        Position,
        ...,
    ]


@dataclass(
    frozen=True,
    slots=True,
)
class CityResult:
    """Current Step-7R result for one showcase city."""

    city_id: str
    winner_method: str

    realized_objective: str | None


@dataclass(
    frozen=True,
    slots=True,
)
class VideoFrameState:
    """Semantic animation state at one global video time."""

    section: str
    city_id: str | None

    city_local_seconds: float | None

    search_progress: float
    rejected_alpha: float
    final_route_progress: float

    result_visible: bool


@dataclass(
    slots=True,
)
class VideoAssets:
    """Loaded, deterministic inputs and cached city panel backgrounds."""

    data_directory: Path

    cities: dict[str, object]

    routes: dict[str, object]

    traces: dict[
        tuple[
            str,
            str,
        ],
        TraceView,
    ]

    city_results: dict[
        str,
        CityResult,
    ]

    overall_winner: str

    panel_bases: dict[
        tuple[
            str,
            str,
        ],
        Image.Image,
    ]


@dataclass(
    frozen=True,
    slots=True,
)
class VideoRenderResult:
    """Canonical video-render result."""

    video_path: Path
    manifest_path: Path

    width: int
    height: int
    fps: int
    frame_count: int

    duration_seconds: float


@dataclass(
    frozen=True,
    slots=True,
)
class VideoValidation:
    """ffprobe validation result."""

    width: int
    height: int

    codec: str
    pixel_format: str

    fps: float
    duration_seconds: float

    frame_count: int


# ============================================================================
# Basic utilities
# ============================================================================


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


def _progress(
    value: float,
    start: float,
    end: float,
) -> float:
    if end <= start:
        raise ValueError("invalid progress interval")

    return _clamp((value - start) / (end - start))


def _truthy(
    value: str,
) -> bool:
    return value.strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def _read_json(
    path: Path,
) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(f"{path} must contain a JSON object")

    return value


def _read_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def _pick_column(
    columns: list[str],
    candidates: tuple[
        str,
        ...,
    ],
) -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise ValueError(f"required column missing; candidates={candidates}; actual={columns}")


def _font(
    size: int,
    *,
    bold: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold
            else ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        ),
    )

    for name in names:
        try:
            return ImageFont.truetype(
                name,
                size=size,
            )
        except OSError:
            continue

    return ImageFont.load_default()


# ============================================================================
# Trace loading
# ============================================================================


def _trace_position(
    value: object,
) -> Position:
    """
    Decode one Step-10R serialized position.

    search_traces.json canonically serializes positions as:
        [row, column]

    Mapping form is also accepted so this presentation adapter remains
    compatible with the existing visualization position contract.
    """
    if (
        isinstance(
            value,
            list,
        )
        and len(value) == 2
    ):
        row = value[0]

        column = value[1]

        if (
            isinstance(
                row,
                int,
            )
            and not isinstance(
                row,
                bool,
            )
            and isinstance(
                column,
                int,
            )
            and not isinstance(
                column,
                bool,
            )
        ):
            return (
                row,
                column,
            )

    if isinstance(
        value,
        dict,
    ):
        return _position(value)

    raise TypeError(
        "serialized trace position must be [row, column] or {'row': ..., 'column': ...}"
    )


def _load_traces(
    path: Path,
) -> dict[
    tuple[
        str,
        str,
    ],
    TraceView,
]:
    payload = _read_json(path)

    raw_traces = payload.get("traces")

    if not isinstance(
        raw_traces,
        list,
    ):
        raise ValueError("search_traces.json must contain traces list")

    result: dict[
        tuple[
            str,
            str,
        ],
        TraceView,
    ] = {}

    for raw_trace in raw_traces:
        if not isinstance(
            raw_trace,
            dict,
        ):
            raise ValueError("trace entry must be mapping")

        city_id = raw_trace.get("city_id")

        method_id = raw_trace.get("method_id")

        if not isinstance(
            city_id,
            str,
        ):
            raise ValueError("trace city_id must be string")

        if not isinstance(
            method_id,
            str,
        ):
            raise ValueError("trace method_id must be string")

        raw_expansions = raw_trace.get("expansions")

        raw_tree_edges = raw_trace.get("tree_edges")

        raw_blocked = raw_trace.get("blocked_edges")

        raw_final_path = raw_trace.get("final_path")

        if not isinstance(
            raw_expansions,
            list,
        ):
            raise ValueError("trace expansions must be list")

        if not isinstance(
            raw_tree_edges,
            list,
        ):
            raise ValueError("trace tree_edges must be list")

        if not isinstance(
            raw_blocked,
            list,
        ):
            raise ValueError("trace blocked_edges must be list")

        if not isinstance(
            raw_final_path,
            list,
        ):
            raise ValueError("trace final_path must be list")

        expansions: list[Position] = []

        expansion_index: dict[Position, int] = {}

        for index, raw in enumerate(raw_expansions):
            if not isinstance(
                raw,
                dict,
            ):
                raise ValueError("expansion must be mapping")

            position = _trace_position(raw.get("position"))

            expansions.append(position)

            expansion_index[position] = index

        tree_edges: list[TraceEdge] = []

        for raw in raw_tree_edges:
            if not isinstance(
                raw,
                dict,
            ):
                raise ValueError("tree edge must be mapping")

            parent = _trace_position(raw.get("parent"))

            child = _trace_position(raw.get("child"))

            classification = raw.get("classification")

            if not isinstance(
                classification,
                str,
            ):
                raise ValueError("tree edge classification must be string")

            if parent not in (expansion_index):
                raise ValueError("tree edge parent was never expanded")

            tree_edges.append(
                TraceEdge(
                    parent=parent,
                    child=child,
                    parent_expansion_step=(expansion_index[parent]),
                    classification=classification,
                )
            )

        blocked_edges: list[BlockedTraceEdge] = []

        for raw in raw_blocked:
            if not isinstance(
                raw,
                dict,
            ):
                raise ValueError("blocked edge must be mapping")

            raw_step = raw.get("expansion_step")

            if not isinstance(
                raw_step,
                int,
            ):
                raise ValueError("blocked expansion_step must be integer")

            blocked_edges.append(
                BlockedTraceEdge(
                    parent=_trace_position(raw.get("parent")),
                    child=_trace_position(raw.get("blocked")),
                    expansion_step=raw_step,
                )
            )

        final_path = tuple(_trace_position(value) for value in raw_final_path)

        result[
            (
                city_id,
                method_id,
            )
        ] = TraceView(
            city_id=city_id,
            method_id=method_id,
            expansions=tuple(expansions),
            tree_edges=tuple(tree_edges),
            blocked_edges=tuple(blocked_edges),
            final_path=final_path,
        )

    expected = {
        (
            city_id,
            method_id,
        )
        for city_id in (
            "new_york",
            "chicago",
            "phoenix",
        )
        for method_id in (
            "dijkstra",
            "ml",
            "dl",
        )
    }

    if set(result) != expected:
        raise ValueError("Step-10R trace set does not contain exactly 3 cities x 3 methods")

    return result


# ============================================================================
# Step-7R result loading
# ============================================================================


def _load_results(
    data_directory: Path,
) -> tuple[
    dict[str, CityResult],
    str,
]:
    (
        route_columns,
        route_rows,
    ) = _read_csv(data_directory / "route_comparison.csv")

    (
        overall_columns,
        overall_rows,
    ) = _read_csv(data_directory / "overall_comparison.csv")

    city_column = _pick_column(
        route_columns,
        (
            "city_id",
            "city",
        ),
    )

    method_column = _pick_column(
        route_columns,
        (
            "method_id",
            "method",
            "planner",
        ),
    )

    city_winner_column = _pick_column(
        route_columns,
        (
            "is_city_winner",
            "city_winner",
            "winner",
            "is_winner",
        ),
    )

    objective_column: str | None = None

    for candidate in (
        "realized_objective",
        "objective",
        "realized_cost",
    ):
        if candidate in (route_columns):
            objective_column = candidate

            break

    results: dict[str, CityResult] = {}

    for city_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        winners = [
            row
            for row in route_rows
            if (
                row[city_column] == city_id
                and row[method_column]
                in {
                    "dijkstra",
                    "ml",
                    "dl",
                }
                and _truthy(row[city_winner_column])
            )
        ]

        if len(winners) != 1:
            raise ValueError(f"{city_id}: expected exactly one headline winner")

        winner = winners[0]

        objective = winner.get(objective_column) if (objective_column is not None) else None

        results[city_id] = CityResult(
            city_id=city_id,
            winner_method=winner[method_column],
            realized_objective=(objective if objective else None),
        )

    overall_method_column = _pick_column(
        overall_columns,
        (
            "method_id",
            "method",
            "planner",
        ),
    )

    overall_winner_column = _pick_column(
        overall_columns,
        (
            "is_overall_winner",
            "overall_winner",
            "winner",
            "is_winner",
        ),
    )

    overall_winners = [
        row
        for row in overall_rows
        if (
            row[overall_method_column]
            in {
                "dijkstra",
                "ml",
                "dl",
            }
            and _truthy(row[overall_winner_column])
        )
    ]

    if len(overall_winners) != 1:
        raise ValueError("expected exactly one overall headline winner")

    return (
        results,
        overall_winners[0][overall_method_column],
    )


# ============================================================================
# 9R.1 animation-state contract
# ============================================================================


def frame_state_at(
    seconds: float,
) -> VideoFrameState:
    if seconds < 0.0 or seconds >= DURATION_SECONDS:
        raise ValueError("video time must satisfy 0 <= seconds < 60")

    if seconds < OPENING_END:
        return VideoFrameState(
            section="opening",
            city_id=None,
            city_local_seconds=None,
            search_progress=0.0,
            rejected_alpha=1.0,
            final_route_progress=0.0,
            result_visible=False,
        )

    if seconds >= SUMMARY_START:
        return VideoFrameState(
            section="summary",
            city_id=None,
            city_local_seconds=None,
            search_progress=1.0,
            rejected_alpha=0.1,
            final_route_progress=1.0,
            result_visible=True,
        )

    for (
        city_id,
        start,
        end,
    ) in CITY_SCHEDULE:
        if start <= seconds < end:
            local = seconds - start

            search_progress = (
                0.0
                if local < CITY_BASE_END
                else _progress(
                    local,
                    CITY_BASE_END,
                    CITY_SEARCH_END,
                )
            )

            if local < CITY_COMPLETE_TREE_END:
                rejected_alpha = 1.0

            elif local < CITY_REJECT_FADE_END:
                fade = _progress(
                    local,
                    CITY_COMPLETE_TREE_END,
                    CITY_REJECT_FADE_END,
                )

                rejected_alpha = 1.0 - (0.9 * fade)

            else:
                rejected_alpha = 0.1

            final_route_progress = (
                0.0
                if local < CITY_REJECT_FADE_END
                else _progress(
                    local,
                    CITY_REJECT_FADE_END,
                    CITY_FINAL_ROUTE_END,
                )
            )

            return VideoFrameState(
                section="city",
                city_id=city_id,
                city_local_seconds=local,
                search_progress=search_progress,
                rejected_alpha=rejected_alpha,
                final_route_progress=(final_route_progress),
                result_visible=(local >= CITY_FINAL_ROUTE_END),
            )

    raise RuntimeError("video schedule contains a gap")


# ============================================================================
# Real frontier/search-tree derivation from Step 10R
# ============================================================================


def expansion_cutoff(
    trace: TraceView,
    search_progress: float,
) -> int:
    if not trace.expansions:
        raise ValueError("trace has no expansions")

    progress = _clamp(search_progress)

    return min(
        len(trace.expansions) - 1,
        math.floor(progress * (len(trace.expansions) - 1)),
    )


def visible_search_edges(
    trace: TraceView,
    *,
    cutoff: int,
) -> tuple[
    TraceEdge,
    ...,
]:
    return tuple(edge for edge in (trace.tree_edges) if (edge.parent_expansion_step <= cutoff))


def visible_blocked_edges(
    trace: TraceView,
    *,
    cutoff: int,
) -> tuple[
    BlockedTraceEdge,
    ...,
]:
    return tuple(edge for edge in (trace.blocked_edges) if (edge.expansion_step <= cutoff))


def frontier_positions(
    trace: TraceView,
    *,
    cutoff: int,
) -> tuple[
    Position,
    ...,
]:
    """
    Derive the persisted predecessor-tree frontier.

    A child is a visible frontier tip when its final predecessor has already
    been expanded but the child itself has not yet been expanded at cutoff.

    This uses only Step-10R persisted trace state.
    """
    expansion_step = {
        position: index
        for (
            index,
            position,
        ) in enumerate(trace.expansions)
    }

    visible = visible_search_edges(
        trace,
        cutoff=cutoff,
    )

    candidates = {
        edge.child
        for edge in visible
        if (
            expansion_step.get(
                edge.child,
                len(trace.expansions) + 1,
            )
            > cutoff
        )
    }

    return tuple(sorted(candidates))


# ============================================================================
# 9R.5 — deterministic distributed zombie swarms
# ============================================================================

SWARM_SECTORS: Final[
    dict[
        str,
        tuple[
            tuple[
                int,
                int,
            ],
            ...,
        ],
    ]
] = {
    "new_york": (
        (
            0,
            0,
        ),
        (
            0,
            1,
        ),
        (
            0,
            2,
        ),
        (
            1,
            1,
        ),
        (
            2,
            0,
        ),
        (
            2,
            1,
        ),
        (
            2,
            2,
        ),
    ),
    "chicago": (
        (
            0,
            0,
        ),
        (
            0,
            2,
        ),
        (
            1,
            1,
        ),
        (
            1,
            2,
        ),
        (
            2,
            0,
        ),
        (
            2,
            2,
        ),
    ),
    "phoenix": (
        (
            0,
            0,
        ),
        (
            0,
            2,
        ),
        (
            1,
            1,
        ),
        (
            2,
            0,
        ),
        (
            2,
            2,
        ),
    ),
}


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


def _traversable_positions(
    city: dict[str, object],
) -> frozenset[Position]:
    return frozenset(
        _cell_position(cell)
        for cell in _cells(city)
        if (_terrain_kind(_terrain_name(cell)) != "building")
    )


def swarm_centers(
    city_id: str,
    city: dict[str, object],
) -> tuple[
    Position,
    ...,
]:
    sectors = SWARM_SECTORS[city_id]

    traversable = _traversable_positions(city)

    result: list[Position] = []

    for (
        sector_row,
        sector_column,
    ) in sectors:
        target = (
            (sector_row * 12) + 6,
            (sector_column * 12) + 6,
        )

        candidates = sorted(
            traversable,
            key=lambda position: (
                abs(position[0] - target[0]) + abs(position[1] - target[1]),
                position,
            ),
        )

        chosen = next(
            (candidate for candidate in candidates if candidate not in result),
            None,
        )

        if chosen is None:
            raise ValueError(f"unable to place swarm for {city_id}")

        result.append(chosen)

    return tuple(result)


# ============================================================================
# Coordinate transforms
# ============================================================================

MAP_LEFT: Final[int] = 118
MAP_RIGHT: Final[int] = 1060

MAP_TOP_MARGIN: Final[int] = 48
MAP_BOTTOM_MARGIN: Final[int] = 16


def _panel_point(
    position: Position,
    *,
    panel_top: int,
    panel_height: int,
) -> tuple[
    float,
    float,
]:
    row, column = position

    map_width = MAP_RIGHT - MAP_LEFT

    map_height = panel_height - MAP_TOP_MARGIN - MAP_BOTTOM_MARGIN

    x = MAP_LEFT + (column / 35.0) * map_width

    y = panel_top + MAP_TOP_MARGIN + (row / 35.0) * map_height

    return (
        x,
        y,
    )


# ============================================================================
# Base city rendering
# ============================================================================


def _terrain_color(
    terrain: str,
) -> tuple[
    int,
    int,
    int,
]:
    if terrain == "building":
        return BUILDING

    if terrain == "arterial":
        return ARTERIAL

    if terrain == "slow":
        return SLOW

    if terrain == "local":
        return ROAD

    return OPEN_TERRAIN


def _draw_zombie(
    draw: ImageDraw.ImageDraw,
    center: tuple[
        float,
        float,
    ],
    *,
    phase: float,
    index: int,
) -> None:
    x, y = center

    jitter_x = math.sin(phase * 2.1 + index * 1.7) * 3.0

    jitter_y = math.cos(phase * 1.8 + index * 2.3) * 2.0

    x += jitter_x
    y += jitter_y

    radius = 7

    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius,
        ),
        fill=ZOMBIE_BODY,
    )

    draw.ellipse(
        (
            x - 3.5,
            y - 2.5,
            x - 1.0,
            y,
        ),
        fill=ZOMBIE_EYE,
    )

    draw.ellipse(
        (
            x + 1.0,
            y - 2.5,
            x + 3.5,
            y,
        ),
        fill=ZOMBIE_EYE,
    )


def _build_panel_base(
    *,
    city_id: str,
    method_id: str,
    city: dict[str, object],
) -> Image.Image:
    _panel_top, panel_height = METHOD_GEOMETRY[method_id]

    image = Image.new(
        "RGB",
        (
            WIDTH,
            panel_height,
        ),
        PANEL_BACKGROUND,
    )

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    local_panel_top = 0

    draw.rectangle(
        (
            0,
            0,
            WIDTH - 1,
            panel_height - 1,
        ),
        outline=PANEL_BORDER,
        width=1,
    )

    label_font = _font(
        23,
        bold=True,
    )

    draw.text(
        (
            18,
            10,
        ),
        METHOD_LABELS[method_id],
        fill=TEXT,
        font=label_font,
    )

    for cell in _cells(city):
        position = _cell_position(cell)

        terrain = _terrain_kind(_terrain_name(cell))

        observed = float(_observed_risk(cell))

        x, y = _panel_point(
            position,
            panel_top=local_panel_top,
            panel_height=panel_height,
        )

        cell_width = (MAP_RIGHT - MAP_LEFT) / 35.0

        cell_height = (panel_height - MAP_TOP_MARGIN - MAP_BOTTOM_MARGIN) / 35.0

        left = x - (cell_width * 0.47)

        top = y - (cell_height * 0.47)

        right = x + (cell_width * 0.47)

        bottom = y + (cell_height * 0.47)

        draw.rectangle(
            (
                left,
                top,
                right,
                bottom,
            ),
            fill=_terrain_color(terrain),
            outline=(BUILDING_EDGE if terrain == "building" else None),
        )

        if terrain != "building" and observed >= 0.65:
            radius = 3.5 + (
                4.5
                * min(
                    1.0,
                    observed,
                )
            )

            draw.ellipse(
                (
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                ),
                fill=RISK_RED,
            )

    route = (
        _method_route(
            {
                "cities": [],
            },
            city_id,
            method_id,
        )
        if False
        else None
    )

    del route

    return image


# ============================================================================
# Asset loading
# ============================================================================


def load_video_assets(
    data_directory: Path,
) -> VideoAssets:
    (
        cities,
        _predictions,
        routes,
        _evaluation,
    ) = load_visual_payloads(data_directory)

    traces = _load_traces(data_directory / "search_traces.json")

    (
        city_results,
        overall_winner,
    ) = _load_results(data_directory)

    panel_bases: dict[
        tuple[
            str,
            str,
        ],
        Image.Image,
    ] = {}

    for (
        city_id,
        _start,
        _end,
    ) in CITY_SCHEDULE:
        city = _city_payload(
            cities,
            city_id,
        )

        for method_id in (
            "dijkstra",
            "ml",
            "dl",
        ):
            panel_bases[
                (
                    city_id,
                    method_id,
                )
            ] = _build_panel_base(
                city_id=city_id,
                method_id=method_id,
                city=city,
            )

    return VideoAssets(
        data_directory=data_directory,
        cities=cities,
        routes=routes,
        traces=traces,
        city_results=city_results,
        overall_winner=overall_winner,
        panel_bases=panel_bases,
    )


# ============================================================================
# Drawing helpers
# ============================================================================


def _draw_line_between(
    draw: ImageDraw.ImageDraw,
    left: Position,
    right: Position,
    *,
    panel_top: int,
    panel_height: int,
    fill: tuple[
        int,
        int,
        int,
        int,
    ],
    width: int,
) -> None:
    draw.line(
        (
            _panel_point(
                left,
                panel_top=panel_top,
                panel_height=panel_height,
            ),
            _panel_point(
                right,
                panel_top=panel_top,
                panel_height=panel_height,
            ),
        ),
        fill=fill,
        width=width,
    )


def _draw_endpoints(
    draw: ImageDraw.ImageDraw,
    trace: TraceView,
    *,
    panel_top: int,
    panel_height: int,
) -> None:
    start = _panel_point(
        trace.final_path[0],
        panel_top=panel_top,
        panel_height=panel_height,
    )

    destination = _panel_point(
        trace.final_path[-1],
        panel_top=panel_top,
        panel_height=panel_height,
    )

    radius = 9

    draw.ellipse(
        (
            start[0] - radius,
            start[1] - radius,
            start[0] + radius,
            start[1] + radius,
        ),
        fill=START_COLOR,
        outline=TEXT,
        width=2,
    )

    draw.rectangle(
        (
            destination[0] - radius,
            destination[1] - radius,
            destination[0] + radius,
            destination[1] + radius,
        ),
        fill=DESTINATION_COLOR,
        outline=TEXT,
        width=2,
    )


def _draw_swarms(
    draw: ImageDraw.ImageDraw,
    *,
    city_id: str,
    city: dict[str, object],
    panel_top: int,
    panel_height: int,
    seconds: float,
) -> None:
    centers = swarm_centers(
        city_id,
        city,
    )

    for swarm_index, center in enumerate(centers):
        base = _panel_point(
            center,
            panel_top=panel_top,
            panel_height=panel_height,
        )

        for zombie_index in range(4):
            angle = (2.0 * math.pi * zombie_index / 4.0) + (seconds * 0.35)

            spread = 11.0 + (2.0 * (swarm_index % 3))

            _draw_zombie(
                draw,
                (
                    base[0] + (math.cos(angle) * spread),
                    base[1] + (math.sin(angle) * spread),
                ),
                phase=seconds,
                index=(swarm_index * 4 + zombie_index),
            )


def _draw_blocked_mark(
    draw: ImageDraw.ImageDraw,
    edge: BlockedTraceEdge,
    *,
    panel_top: int,
    panel_height: int,
) -> None:
    x, y = _panel_point(
        edge.child,
        panel_top=panel_top,
        panel_height=panel_height,
    )

    size = 4.5

    draw.line(
        (
            (
                x - size,
                y - size,
            ),
            (
                x + size,
                y + size,
            ),
        ),
        fill=BLOCKED_MARK,
        width=2,
    )

    draw.line(
        (
            (
                x - size,
                y + size,
            ),
            (
                x + size,
                y - size,
            ),
        ),
        fill=BLOCKED_MARK,
        width=2,
    )


def _draw_frontier(
    draw: ImageDraw.ImageDraw,
    trace: TraceView,
    *,
    cutoff: int,
    panel_top: int,
    panel_height: int,
) -> None:
    for position in frontier_positions(
        trace,
        cutoff=cutoff,
    ):
        x, y = _panel_point(
            position,
            panel_top=panel_top,
            panel_height=panel_height,
        )

        radius = 5.5

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            ),
            outline=FRONTIER,
            width=2,
        )


def _draw_active_tree(
    draw: ImageDraw.ImageDraw,
    trace: TraceView,
    *,
    cutoff: int,
    panel_top: int,
    panel_height: int,
) -> None:
    for tree_edge in visible_search_edges(
        trace,
        cutoff=cutoff,
    ):
        _draw_line_between(
            draw,
            tree_edge.parent,
            tree_edge.child,
            panel_top=panel_top,
            panel_height=panel_height,
            fill=ACTIVE_SEARCH,
            width=3,
        )

    for blocked_edge in visible_blocked_edges(
        trace,
        cutoff=cutoff,
    ):
        _draw_blocked_mark(
            draw,
            blocked_edge,
            panel_top=panel_top,
            panel_height=panel_height,
        )

    _draw_frontier(
        draw,
        trace,
        cutoff=cutoff,
        panel_top=panel_top,
        panel_height=panel_height,
    )


def _draw_complete_tree(
    draw: ImageDraw.ImageDraw,
    trace: TraceView,
    *,
    panel_top: int,
    panel_height: int,
    rejected_alpha: float,
    final_route_progress: float,
) -> None:
    alpha = round(
        255
        * _clamp(
            rejected_alpha,
            0.1,
            1.0,
        )
    )

    for tree_edge in trace.tree_edges:
        if tree_edge.classification == "explored_rejected":
            color = (
                REJECTED[0],
                REJECTED[1],
                REJECTED[2],
                alpha,
            )

        else:
            color = ACTIVE_SEARCH

        _draw_line_between(
            draw,
            tree_edge.parent,
            tree_edge.child,
            panel_top=panel_top,
            panel_height=panel_height,
            fill=color,
            width=(2 if tree_edge.classification == "explored_rejected" else 3),
        )

    for blocked_edge in trace.blocked_edges:
        _draw_blocked_mark(
            draw,
            blocked_edge,
            panel_top=panel_top,
            panel_height=panel_height,
        )

    if final_route_progress <= 0.0:
        return

    edge_count = len(trace.final_path) - 1

    visible_count = min(
        edge_count,
        math.ceil(edge_count * _clamp(final_route_progress)),
    )

    for index in range(visible_count):
        _draw_line_between(
            draw,
            trace.final_path[index],
            trace.final_path[index + 1],
            panel_top=panel_top,
            panel_height=panel_height,
            fill=FINAL_ROUTE,
            width=7,
        )


# ============================================================================
# City frame
# ============================================================================


def _render_city_frame(
    assets: VideoAssets,
    *,
    city_id: str,
    local_seconds: float,
    global_seconds: float,
) -> Image.Image:
    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    title_font = _font(
        24,
        bold=True,
    )

    small_font = _font(
        18,
    )

    draw.text(
        (
            18,
            8,
        ),
        (CITY_LABELS[city_id] + " · SAME MISSION · THREE PLANNERS"),
        fill=TEXT,
        font=title_font,
    )

    state = frame_state_at(global_seconds)

    city = _city_payload(
        assets.cities,
        city_id,
    )

    for method_id in (
        "dijkstra",
        "ml",
        "dl",
    ):
        panel_top, panel_height = METHOD_GEOMETRY[method_id]

        base = assets.panel_bases[
            (
                city_id,
                method_id,
            )
        ]

        image.paste(
            base,
            (
                0,
                panel_top,
            ),
        )

        draw = ImageDraw.Draw(
            image,
            "RGBA",
        )

        trace = assets.traces[
            (
                city_id,
                method_id,
            )
        ]

        _draw_swarms(
            draw,
            city_id=city_id,
            city=city,
            panel_top=panel_top,
            panel_height=panel_height,
            seconds=local_seconds,
        )

        if local_seconds < CITY_BASE_END:
            pass

        elif local_seconds < CITY_SEARCH_END:
            cutoff = expansion_cutoff(
                trace,
                state.search_progress,
            )

            _draw_active_tree(
                draw,
                trace,
                cutoff=cutoff,
                panel_top=panel_top,
                panel_height=panel_height,
            )

        elif local_seconds < CITY_COMPLETE_TREE_END:
            _draw_complete_tree(
                draw,
                trace,
                panel_top=panel_top,
                panel_height=panel_height,
                rejected_alpha=1.0,
                final_route_progress=0.0,
            )

        else:
            _draw_complete_tree(
                draw,
                trace,
                panel_top=panel_top,
                panel_height=panel_height,
                rejected_alpha=(state.rejected_alpha),
                final_route_progress=(state.final_route_progress),
            )

        _draw_endpoints(
            draw,
            trace,
            panel_top=panel_top,
            panel_height=panel_height,
        )

        if CITY_BASE_END <= local_seconds < CITY_SEARCH_END:
            cutoff = expansion_cutoff(
                trace,
                state.search_progress,
            )

            count = cutoff + 1

            frontier_count = len(
                frontier_positions(
                    trace,
                    cutoff=cutoff,
                )
            )

            draw.text(
                (
                    830,
                    panel_top + 12,
                ),
                (f"expanded {count}  frontier {frontier_count}"),
                fill=MUTED_TEXT,
                font=small_font,
            )

    # Result bar remains intentionally empty until t=14.0 city-local.
    draw.rectangle(
        (
            0,
            RESULT_TOP,
            WIDTH,
            HEIGHT,
        ),
        fill=(
            13,
            17,
            23,
            255,
        ),
    )

    if state.result_visible:
        result = assets.city_results[city_id]

        winner_label = METHOD_SHORT_LABELS[result.winner_method]

        text = f"{CITY_LABELS[city_id]} WINNER · {winner_label}"

        if result.realized_objective is not None:
            text += " · realized objective " + result.realized_objective

        draw.text(
            (
                18,
                RESULT_TOP + 9,
            ),
            text,
            fill=FINAL_ROUTE[:3],
            font=_font(
                20,
                bold=True,
            ),
        )

    return image


# ============================================================================
# 9R.9 — 8-second opening
# ============================================================================


def _render_opening(
    assets: VideoAssets,
    *,
    seconds: float,
) -> Image.Image:
    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    title = _font(
        58,
        bold=True,
    )

    subtitle = _font(
        30,
        bold=True,
    )

    body = _font(
        23,
    )

    if seconds < 2.2:
        draw.text(
            (
                70,
                250,
            ),
            "DIJKSTRA vs ML vs DEEP LEARNING",
            fill=TEXT,
            font=title,
        )

        draw.text(
            (
                70,
                335,
            ),
            "Who actually finds the best escape route?",
            fill=DESTINATION_COLOR,
            font=subtitle,
        )

    elif seconds < 5.2:
        draw.text(
            (
                70,
                190,
            ),
            "SAME CITY.",
            fill=TEXT,
            font=title,
        )

        draw.text(
            (
                70,
                280,
            ),
            "SAME START.",
            fill=TEXT,
            font=title,
        )

        draw.text(
            (
                70,
                370,
            ),
            "SAME SAFE ZONE.",
            fill=TEXT,
            font=title,
        )

        draw.text(
            (
                70,
                495,
            ),
            ("Only the danger estimator changes."),
            fill=MUTED_TEXT,
            font=subtitle,
        )

    else:
        y = 230

        for method_id in (
            "dijkstra",
            "ml",
            "dl",
        ):
            draw.rounded_rectangle(
                (
                    80,
                    y,
                    1000,
                    y + 135,
                ),
                radius=24,
                fill=PANEL_BACKGROUND,
                outline=PANEL_BORDER,
                width=2,
            )

            draw.text(
                (
                    110,
                    y + 24,
                ),
                METHOD_SHORT_LABELS[method_id],
                fill=TEXT,
                font=subtitle,
            )

            explanation = {
                "dijkstra": ("Observed visible risk · Dijkstra"),
                "ml": ("Engineered-feature risk · A*"),
                "dl": ("CNN dense risk surface · A*"),
            }[method_id]

            draw.text(
                (
                    110,
                    y + 75,
                ),
                explanation,
                fill=MUTED_TEXT,
                font=body,
            )

            y += 165

        draw.text(
            (
                80,
                765,
            ),
            ("Watch the real search trees grow."),
            fill=DESTINATION_COLOR,
            font=subtitle,
        )

    draw.text(
        (
            70,
            1000,
        ),
        ("Frozen showcase · predeclared divergence contract"),
        fill=MUTED_TEXT,
        font=body,
    )

    return image


# ============================================================================
# 9R.10 — 7-second overall summary
# ============================================================================


def _render_summary(
    assets: VideoAssets,
    *,
    seconds: float,
) -> Image.Image:
    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BACKGROUND,
    )

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    title = _font(
        48,
        bold=True,
    )

    subtitle = _font(
        28,
        bold=True,
    )

    body = _font(
        23,
    )

    draw.text(
        (
            70,
            100,
        ),
        "THREE CITIES. ONE OVERALL WINNER.",
        fill=TEXT,
        font=title,
    )

    reveal = _progress(
        seconds,
        0.0,
        4.0,
    )

    city_order = (
        "new_york",
        "chicago",
        "phoenix",
    )

    y = 260

    visible_city_count = min(
        3,
        math.ceil(reveal * 3),
    )

    for index, city_id in enumerate(city_order):
        if index >= visible_city_count:
            break

        result = assets.city_results[city_id]

        draw.rounded_rectangle(
            (
                90,
                y,
                990,
                y + 120,
            ),
            radius=20,
            fill=PANEL_BACKGROUND,
            outline=PANEL_BORDER,
            width=2,
        )

        draw.text(
            (
                120,
                y + 22,
            ),
            CITY_LABELS[city_id],
            fill=TEXT,
            font=subtitle,
        )

        draw.text(
            (
                610,
                y + 24,
            ),
            METHOD_SHORT_LABELS[result.winner_method],
            fill=FINAL_ROUTE[:3],
            font=subtitle,
        )

        y += 150

    if seconds >= 4.0:
        draw.text(
            (
                90,
                760,
            ),
            "OVERALL",
            fill=MUTED_TEXT,
            font=body,
        )

        draw.text(
            (
                90,
                805,
            ),
            METHOD_SHORT_LABELS[assets.overall_winner],
            fill=FINAL_ROUTE[:3],
            font=_font(
                62,
                bold=True,
            ),
        )

        draw.text(
            (
                90,
                900,
            ),
            ("Winner based on realized objective across the frozen showcase."),
            fill=TEXT,
            font=body,
        )

    draw.text(
        (
            90,
            1010,
        ),
        ("Dijkstra · Gradient Boosting + A* · CNN + A*"),
        fill=MUTED_TEXT,
        font=body,
    )

    return image


# ============================================================================
# Public frame renderer
# ============================================================================


def render_video_frame(
    assets: VideoAssets,
    *,
    frame_index: int,
) -> Image.Image:
    if not (0 <= frame_index < FRAME_COUNT):
        raise ValueError("frame index out of bounds")

    seconds = frame_index / FPS

    state = frame_state_at(seconds)

    if state.section == "opening":
        return _render_opening(
            assets,
            seconds=seconds,
        )

    if state.section == "summary":
        return _render_summary(
            assets,
            seconds=(seconds - SUMMARY_START),
        )

    if state.city_id is None or state.city_local_seconds is None:
        raise RuntimeError("city frame missing city state")

    return _render_city_frame(
        assets,
        city_id=state.city_id,
        local_seconds=(state.city_local_seconds),
        global_seconds=seconds,
    )


# ============================================================================
# 9R.11 — representative frames
# ============================================================================

REPRESENTATIVE_TIMES: Final[
    tuple[
        tuple[
            str,
            float,
        ],
        ...,
    ]
] = (
    (
        "opening_hook",
        1.0,
    ),
    (
        "opening_methods",
        6.5,
    ),
    (
        "ny_base",
        8.75,
    ),
    (
        "ny_search",
        14.0,
    ),
    (
        "ny_complete_tree",
        18.0,
    ),
    (
        "ny_rejected",
        20.0,
    ),
    (
        "ny_final_route",
        21.5,
    ),
    (
        "ny_result",
        22.5,
    ),
    (
        "overall_summary",
        58.0,
    ),
)


def render_representative_frames(
    *,
    data_directory: Path,
    output_directory: Path,
) -> tuple[
    Path,
    ...,
]:
    assets = load_video_assets(data_directory)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs: list[Path] = []

    for label, seconds in REPRESENTATIVE_TIMES:
        frame_index = min(
            FRAME_COUNT - 1,
            round(seconds * FPS),
        )

        image = render_video_frame(
            assets,
            frame_index=frame_index,
        )

        path = output_directory / (label + ".png")

        image.save(
            path,
            format="PNG",
        )

        outputs.append(path)

    return tuple(outputs)


# ============================================================================
# 9R.13 — FFmpeg raw-frame assembly
# ============================================================================


def ffmpeg_command(
    output_path: Path,
) -> tuple[
    str,
    ...,
]:
    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg is None:
        raise FileNotFoundError("ffmpeg is not available")

    return (
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s:v",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-r",
        str(FPS),
        str(output_path),
    )


def _git_hash() -> str | None:
    completed = subprocess.run(
        (
            "git",
            "rev-parse",
            "HEAD",
        ),
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        return None

    value = completed.stdout.strip()

    return value if value else None


def _write_manifest(
    *,
    path: Path,
    video_path: Path,
    assets: VideoAssets,
) -> None:
    payload = {
        "project_id": ("p04_zombie_escape"),
        "asset_name": ("dijkstra_vs_ml_vs_dl_60s"),
        "generation_timestamp_utc": (datetime.now(UTC).isoformat()),
        "git_commit_hash": (_git_hash()),
        "configuration_path": ("configs/p04_zombie_escape.yaml"),
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "duration_seconds": (DURATION_SECONDS),
        "frame_count": (FRAME_COUNT),
        "video_path": str(video_path),
        "city_schedule": [
            {
                "city_id": (city_id),
                "start": start,
                "end": end,
            }
            for (
                city_id,
                start,
                end,
            ) in CITY_SCHEDULE
        ],
        "city_winners": {
            city_id: (result.winner_method)
            for (
                city_id,
                result,
            ) in (assets.city_results.items())
        },
        "overall_winner": (assets.overall_winner),
        "search_trace_source": ("outputs/p04_zombie_escape/data/search_traces.json"),
        "winner_source": (
            "outputs/p04_zombie_escape/data/route_comparison.csv + overall_comparison.csv"
        ),
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def render_canonical_video(
    *,
    data_directory: Path = Path("outputs/p04_zombie_escape/data"),
    video_path: Path = Path("outputs/p04_zombie_escape/video/dijkstra_vs_ml_vs_dl_60s.mp4"),
    manifest_path: Path = Path("outputs/p04_zombie_escape/manifests/dijkstra_vs_ml_vs_dl_60s.json"),
) -> VideoRenderResult:
    assets = load_video_assets(data_directory)

    video_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = ffmpeg_command(video_path)

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
    )

    if process.stdin is None:
        raise RuntimeError("unable to open ffmpeg stdin")

    try:
        for frame_index in range(FRAME_COUNT):
            image = render_video_frame(
                assets,
                frame_index=frame_index,
            )

            if image.mode != "RGB":
                image = image.convert("RGB")

            process.stdin.write(image.tobytes())

    except BaseException:
        process.stdin.close()

        process.terminate()

        process.wait()

        raise

    process.stdin.close()

    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(f"ffmpeg video encoding failed with exit code {return_code}")

    _write_manifest(
        path=manifest_path,
        video_path=video_path,
        assets=assets,
    )

    return VideoRenderResult(
        video_path=video_path,
        manifest_path=manifest_path,
        width=WIDTH,
        height=HEIGHT,
        fps=FPS,
        frame_count=FRAME_COUNT,
        duration_seconds=(DURATION_SECONDS),
    )


# ============================================================================
# 9R.15 — ffprobe validation
# ============================================================================


def _parse_rate(
    value: str,
) -> float:
    return float(Fraction(value))


def probe_video(
    path: Path,
) -> VideoValidation:
    ffprobe = shutil.which("ffprobe")

    if ffprobe is None:
        raise FileNotFoundError("ffprobe is not available")

    completed = subprocess.run(
        (
            ffprobe,
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            (
                "stream=codec_name,pix_fmt,width,height,"
                "avg_frame_rate,nb_read_frames:"
                "format=duration"
            ),
            "-of",
            "json",
            str(path),
        ),
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError("ffprobe payload must be mapping")

    streams = payload.get("streams")

    format_payload = payload.get("format")

    if (
        not isinstance(
            streams,
            list,
        )
        or len(streams) != 1
    ):
        raise ValueError("expected one video stream")

    if not isinstance(
        format_payload,
        dict,
    ):
        raise ValueError("ffprobe format payload missing")

    stream = streams[0]

    if not isinstance(
        stream,
        dict,
    ):
        raise ValueError("ffprobe stream must be mapping")

    width = stream.get("width")

    height = stream.get("height")

    codec = stream.get("codec_name")

    pixel_format = stream.get("pix_fmt")

    rate = stream.get("avg_frame_rate")

    frame_count = stream.get("nb_read_frames")

    duration = format_payload.get("duration")

    if not isinstance(
        width,
        int,
    ):
        raise ValueError("ffprobe width missing")

    if not isinstance(
        height,
        int,
    ):
        raise ValueError("ffprobe height missing")

    if not isinstance(
        codec,
        str,
    ):
        raise ValueError("ffprobe codec missing")

    if not isinstance(
        pixel_format,
        str,
    ):
        raise ValueError("ffprobe pixel format missing")

    if not isinstance(
        rate,
        str,
    ):
        raise ValueError("ffprobe rate missing")

    if not isinstance(
        frame_count,
        str,
    ):
        raise ValueError("ffprobe frame count missing")

    if not isinstance(
        duration,
        str,
    ):
        raise ValueError("ffprobe duration missing")

    return VideoValidation(
        width=width,
        height=height,
        codec=codec,
        pixel_format=pixel_format,
        fps=_parse_rate(rate),
        duration_seconds=float(duration),
        frame_count=int(frame_count),
    )


def validate_canonical_video(
    path: Path,
) -> VideoValidation:
    result = probe_video(path)

    if result.width != WIDTH:
        raise ValueError(f"width={result.width}, expected={WIDTH}")

    if result.height != HEIGHT:
        raise ValueError(f"height={result.height}, expected={HEIGHT}")

    if result.codec != "h264":
        raise ValueError(f"codec={result.codec}, expected=h264")

    if result.pixel_format != "yuv420p":
        raise ValueError(f"pixel format={result.pixel_format}, expected=yuv420p")

    if not math.isclose(
        result.fps,
        float(FPS),
        rel_tol=0.0,
        abs_tol=0.001,
    ):
        raise ValueError(f"fps={result.fps}, expected={FPS}")

    if result.frame_count != FRAME_COUNT:
        raise ValueError(f"frame_count={result.frame_count}, expected={FRAME_COUNT}")

    if not math.isclose(
        result.duration_seconds,
        DURATION_SECONDS,
        rel_tol=0.0,
        abs_tol=0.05,
    ):
        raise ValueError(f"duration={result.duration_seconds}, expected={DURATION_SECONDS}")

    return result


def main() -> None:
    result = render_canonical_video()

    validation = validate_canonical_video(result.video_path)

    print(result.video_path)

    print(f"duration={validation.duration_seconds:.3f}")

    print(f"dimensions={validation.width}x{validation.height}")

    print(f"fps={validation.fps:.3f}")

    print(f"frames={validation.frame_count}")

    print(f"codec={validation.codec}")

    print(f"pix_fmt={validation.pixel_format}")


if __name__ == "__main__":
    main()
