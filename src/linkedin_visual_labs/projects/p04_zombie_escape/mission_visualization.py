"""Mission-map visualization Version 2.1 for Project 2."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

from PIL import Image, ImageColor, ImageDraw, ImageFont

from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    CANVAS_SIZE,
    CITY_LABELS,
    CITY_ORDER,
    METHOD_LABELS,
    METHOD_ORDER,
    _cell_position,
    _cells,
    _city_payload,
    _evaluation_city_payload,
    _method_route,
    _observed_risk,
    _position,
    _terrain_name,
    load_visual_payloads,
)

RouteOverlay = Literal[
    "none",
    "final",
]


@dataclass(frozen=True, slots=True)
class MissionBox:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return self.x1 - self.x0

    @property
    def height(self) -> int:
        return self.y1 - self.y0

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height


@dataclass(frozen=True, slots=True)
class MissionTextPlacement:
    label: str
    box: MissionBox


@dataclass(frozen=True, slots=True)
class MissionPreviewArtifacts:
    opening_board: Path
    city_frames: tuple[Path, ...]
    final_summary: Path


# ============================================================================
# Exact 1080 x 1080 city-frame geometry
# ============================================================================

HEADING_HEIGHT: Final[int] = 45
METHOD_LAYER_HEIGHT: Final[int] = 330
RESULT_HEIGHT: Final[int] = 45

HEADING_BOX: Final[MissionBox] = MissionBox(
    0,
    0,
    1080,
    45,
)

METHOD_LAYER_BOXES: Final[dict[str, MissionBox]] = {
    "dijkstra": MissionBox(
        0,
        45,
        1080,
        375,
    ),
    "ml": MissionBox(
        0,
        375,
        1080,
        705,
    ),
    "dl": MissionBox(
        0,
        705,
        1080,
        1035,
    ),
}

RESULT_BOX: Final[MissionBox] = MissionBox(
    0,
    1035,
    1080,
    1080,
)

METHOD_LABEL_WIDTH: Final[int] = 170
METHOD_MAP_GAP: Final[int] = 10

FULL_MAP_MIN_ASPECT: Final[float] = 2.50
MINI_MAP_MIN_ASPECT: Final[float] = 1.85


def method_map_box(
    method_id: str,
) -> MissionBox:
    layer = METHOD_LAYER_BOXES[method_id]

    return MissionBox(
        METHOD_LABEL_WIDTH,
        layer.y0 + METHOD_MAP_GAP,
        CANVAS_SIZE - 10,
        layer.y1 - METHOD_MAP_GAP,
    )


# ============================================================================
# Opening board
# ============================================================================

OPENING_CARD_WIDTH: Final[int] = 318
OPENING_CARD_HEIGHT: Final[int] = 256

OPENING_START_X: Final[int] = 45
OPENING_START_Y: Final[int] = 170

OPENING_GAP_X: Final[int] = 18
OPENING_GAP_Y: Final[int] = 17


def opening_card_boxes() -> tuple[
    MissionBox,
    ...,
]:
    boxes: list[MissionBox] = []

    for row in range(3):
        for column in range(3):
            x0 = OPENING_START_X + column * (OPENING_CARD_WIDTH + OPENING_GAP_X)

            y0 = OPENING_START_Y + row * (OPENING_CARD_HEIGHT + OPENING_GAP_Y)

            boxes.append(
                MissionBox(
                    x0,
                    y0,
                    x0 + OPENING_CARD_WIDTH,
                    y0 + OPENING_CARD_HEIGHT,
                )
            )

    return tuple(boxes)


def opening_map_box(
    card: MissionBox,
) -> MissionBox:
    return MissionBox(
        card.x0 + 9,
        card.y0 + 45,
        card.x1 - 9,
        card.y0 + 195,
    )


# ============================================================================
# Final summary
# ============================================================================

FINAL_CARD_WIDTH: Final[int] = 310
FINAL_CARD_HEIGHT: Final[int] = 250

FINAL_START_X: Final[int] = 50
FINAL_CARD_Y: Final[int] = 300
FINAL_GAP_X: Final[int] = 25


def final_card_boxes() -> tuple[
    MissionBox,
    ...,
]:
    return tuple(
        MissionBox(
            (FINAL_START_X + index * (FINAL_CARD_WIDTH + FINAL_GAP_X)),
            FINAL_CARD_Y,
            (FINAL_START_X + index * (FINAL_CARD_WIDTH + FINAL_GAP_X) + FINAL_CARD_WIDTH),
            FINAL_CARD_Y + FINAL_CARD_HEIGHT,
        )
        for index in range(3)
    )


def final_map_box(
    card: MissionBox,
) -> MissionBox:
    return MissionBox(
        card.x0 + 10,
        card.y0 + 49,
        card.x1 - 10,
        card.y0 + 194,
    )


# ============================================================================
# Visual language
# ============================================================================

BACKGROUND: Final[str] = "#07101c"

PANEL: Final[str] = "#0e1928"
PANEL_ALT: Final[str] = "#111f31"
BORDER: Final[str] = "#30435c"

TEXT: Final[str] = "#f4f7fb"
TEXT_SECONDARY: Final[str] = "#a9b7c9"
TEXT_MUTED: Final[str] = "#71849c"

BUILDING: Final[str] = "#263447"
BUILDING_EDGE: Final[str] = "#34475e"

OPEN_LAND: Final[str] = "#17372f"
ROUGH_LAND: Final[str] = "#403728"

LOCAL_ROAD: Final[str] = "#68788c"
ARTERIAL_ROAD: Final[str] = "#96a6b8"
ROAD_CENTER: Final[str] = "#c6cdd6"

ZOMBIE_SKIN: Final[str] = "#8fd17a"
ZOMBIE_DARK: Final[str] = "#294a31"
ZOMBIE_DANGER: Final[str] = "#ff4a3d"

START_COLOR: Final[str] = "#f6b84b"
SAFE_COLOR: Final[str] = "#4ee39a"

EXPLORED_COLOR: Final[str] = "#d8dee8"
REJECTED_COLOR: Final[str] = "#ff453a"
FINAL_ROUTE_COLOR: Final[str] = "#4ee58a"

METHOD_COLORS: Final[dict[str, str]] = {
    "dijkstra": "#51a7ff",
    "ml": "#f2b64b",
    "dl": "#d06bff",
}


# ============================================================================
# Fair mission identity
# ============================================================================

MISSION_ENDPOINTS: Final[
    dict[
        str,
        tuple[
            tuple[int, int],
            tuple[int, int],
        ],
    ]
] = {
    "new_york": (
        (
            33,
            2,
        ),
        (
            2,
            33,
        ),
    ),
    "chicago": (
        (
            32,
            3,
        ),
        (
            3,
            32,
        ),
    ),
    "phoenix": (
        (
            31,
            4,
        ),
        (
            4,
            31,
        ),
    ),
}


# ============================================================================
# Distributed zombie-swarm contract
#
# Each city is divided into a 3 x 3 sector grid.
# A city can have at most one swarm center in a sector.
#
# This is intentionally stronger than the old ">= 3 quadrants" rule.
# ============================================================================

SWARM_COUNTS: Final[dict[str, int]] = {
    "new_york": 7,
    "chicago": 6,
    "phoenix": 5,
}

SWARM_SEEDS: Final[dict[str, int]] = {
    "new_york": 8101,
    "chicago": 8102,
    "phoenix": 8103,
}

SWARM_SECTOR_PLAN: Final[
    dict[
        str,
        tuple[
            tuple[int, int],
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
            0,
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
            0,
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

SECTOR_SIZE: Final[int] = 12

SWARM_ENDPOINT_CLEARANCE: Final[int] = 4
SWARM_MIN_DISTANCE: Final[int] = 4

SWARM_MIN_ROW_SPAN: Final[int] = 18
SWARM_MIN_COLUMN_SPAN: Final[int] = 18


# ============================================================================
# Fonts / helpers
# ============================================================================


def _font(
    size: int,
    *,
    bold: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
        if bold
        else ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")
        if bold
        else ("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )

    for candidate in candidates:
        candidate_path = Path(candidate)

        if candidate_path.is_file():
            return ImageFont.truetype(
                str(candidate_path),
                size=size,
            )

    return ImageFont.load_default()


def _new_canvas() -> Image.Image:
    return Image.new(
        "RGB",
        (
            CANVAS_SIZE,
            CANVAS_SIZE,
        ),
        BACKGROUND,
    )


def _rgba(
    color: str,
    alpha: int,
) -> tuple[
    int,
    int,
    int,
    int,
]:
    rgb = ImageColor.getrgb(color)

    return (
        int(rgb[0]),
        int(rgb[1]),
        int(rgb[2]),
        alpha,
    )


def _draw_text(
    draw: ImageDraw.ImageDraw,
    placements: list[MissionTextPlacement],
    *,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    anchor: str = "la",
    track: bool = True,
) -> MissionBox:
    raw_box = draw.textbbox(
        xy,
        text,
        font=font,
        anchor=anchor,
    )

    box = MissionBox(
        round(raw_box[0]),
        round(raw_box[1]),
        round(raw_box[2]),
        round(raw_box[3]),
    )

    draw.text(
        xy,
        text,
        font=font,
        fill=fill,
        anchor=anchor,
    )

    if track:
        placements.append(
            MissionTextPlacement(
                label=text,
                box=box,
            )
        )

    return box


# ============================================================================
# Contract validation
# ============================================================================


def validate_frame_geometry() -> None:
    if CANVAS_SIZE != 1080:
        raise ValueError("canvas must remain 1080 x 1080")

    total = HEADING_HEIGHT + METHOD_LAYER_HEIGHT * 3 + RESULT_HEIGHT

    if total != 1080:
        raise ValueError("45/330/330/330/45 geometry invalid")

    expected = {
        "dijkstra": (
            45,
            375,
        ),
        "ml": (
            375,
            705,
        ),
        "dl": (
            705,
            1035,
        ),
    }

    for (
        method_id,
        (
            y0,
            y1,
        ),
    ) in expected.items():
        layer = METHOD_LAYER_BOXES[method_id]

        if layer.y0 != y0 or layer.y1 != y1 or layer.height != METHOD_LAYER_HEIGHT:
            raise ValueError(f"{method_id}: invalid layer")

        if method_map_box(method_id).aspect_ratio < FULL_MAP_MIN_ASPECT:
            raise ValueError(f"{method_id}: map not horizontal")

    if RESULT_BOX.height != 45:
        raise ValueError("result strip must remain 45px")

    opening_cards = opening_card_boxes()

    if len(opening_cards) != 9:
        raise ValueError("opening board must have 9 cards")

    for card in opening_cards:
        if opening_map_box(card).aspect_ratio < MINI_MAP_MIN_ASPECT:
            raise ValueError("opening map not horizontal")

    final_cards = final_card_boxes()

    if len(final_cards) != 3:
        raise ValueError("final summary must have 3 cards")

    for card in final_cards:
        if final_map_box(card).aspect_ratio < MINI_MAP_MIN_ASPECT:
            raise ValueError("final map not horizontal")


def validate_text_placements(
    placements: list[MissionTextPlacement],
) -> None:
    for index, left in enumerate(placements):
        for right in placements[index + 1 :]:
            width = max(
                0,
                min(
                    left.box.x1,
                    right.box.x1,
                )
                - max(
                    left.box.x0,
                    right.box.x0,
                ),
            )

            height = max(
                0,
                min(
                    left.box.y1,
                    right.box.y1,
                )
                - max(
                    left.box.y0,
                    right.box.y0,
                ),
            )

            intersection = width * height

            if intersection == 0:
                continue

            left_area = left.box.width * left.box.height

            right_area = right.box.width * right.box.height

            smaller = min(
                left_area,
                right_area,
            )

            if smaller > 0 and intersection / smaller > 0.35:
                raise ValueError(f"tracked text overlap: {left.label!r} vs {right.label!r}")


def _validate_route_overlay(
    route_overlay: RouteOverlay,
) -> None:
    if route_overlay not in {
        "none",
        "final",
    }:
        raise ValueError("route overlay must be none or final")


# ============================================================================
# Grid coordinate helpers
# ============================================================================


def _cell_center(
    row: int,
    column: int,
    viewport: MissionBox,
) -> tuple[int, int]:
    return (
        round(viewport.x0 + (column + 0.5) * viewport.width / 36.0),
        round(viewport.y0 + (row + 0.5) * viewport.height / 36.0),
    )


def _cell_box(
    row: int,
    column: int,
    viewport: MissionBox,
    *,
    inset: float = 0.0,
) -> tuple[
    int,
    int,
    int,
    int,
]:
    cell_width = viewport.width / 36.0

    cell_height = viewport.height / 36.0

    return (
        round(viewport.x0 + column * cell_width + inset),
        round(viewport.y0 + row * cell_height + inset),
        round(viewport.x0 + (column + 1) * cell_width - inset),
        round(viewport.y0 + (row + 1) * cell_height - inset),
    )


def _terrain_kind(
    raw: str,
) -> str:
    value = raw.lower()

    if "building" in value:
        return "building"

    if "arterial" in value:
        return "arterial"

    if "road" in value or "local" in value:
        return "local"

    if "slow" in value:
        return "rough"

    return "open"


# ============================================================================
# Sector-aware swarm distribution
# ============================================================================


def swarm_sector(
    row: int,
    column: int,
) -> tuple[int, int]:
    return (
        min(
            2,
            row // SECTOR_SIZE,
        ),
        min(
            2,
            column // SECTOR_SIZE,
        ),
    )


def _sector_anchor(
    sector: tuple[int, int],
) -> tuple[float, float]:
    sector_row, sector_column = sector

    return (
        sector_row * SECTOR_SIZE + (SECTOR_SIZE - 1) / 2.0,
        sector_column * SECTOR_SIZE + (SECTOR_SIZE - 1) / 2.0,
    )


def _endpoint_clear(
    *,
    row: int,
    column: int,
    city_id: str,
) -> bool:
    start, destination = MISSION_ENDPOINTS[city_id]

    for endpoint in (
        start,
        destination,
    ):
        distance = abs(row - endpoint[0]) + abs(column - endpoint[1])

        if distance < SWARM_ENDPOINT_CLEARANCE:
            return False

    return True


def _minimum_distance_to_selected(
    *,
    row: int,
    column: int,
    selected: list[
        tuple[
            int,
            int,
            float,
        ]
    ],
) -> int:
    if not selected:
        return 72

    return min(
        abs(row - selected_row) + abs(column - selected_column)
        for (
            selected_row,
            selected_column,
            _risk,
        ) in selected
    )


def select_zombie_hotspots(
    city: dict[str, object],
    *,
    city_id: str,
) -> tuple[
    tuple[
        int,
        int,
        float,
    ],
    ...,
]:
    """
    Select one deterministic swarm center per planned 3x3 city sector.

    Geography is primary, observed risk is secondary.
    """
    target_sectors = SWARM_SECTOR_PLAN[city_id]

    if len(target_sectors) != SWARM_COUNTS[city_id]:
        raise ValueError(f"{city_id}: swarm plan/count mismatch")

    rng = random.Random(SWARM_SEEDS[city_id])

    candidates_by_sector: dict[
        tuple[int, int],
        list[
            tuple[
                float,
                int,
                int,
                float,
            ]
        ],
    ] = {sector: [] for sector in target_sectors}

    for cell in _cells(city):
        if _terrain_kind(_terrain_name(cell)) == "building":
            continue

        row, column = _cell_position(cell)

        sector = swarm_sector(
            row,
            column,
        )

        if sector not in (candidates_by_sector):
            continue

        if not _endpoint_clear(
            row=row,
            column=column,
            city_id=city_id,
        ):
            continue

        risk = float(_observed_risk(cell))

        anchor_row, anchor_column = _sector_anchor(sector)

        anchor_distance = abs(row - anchor_row) + abs(column - anchor_column)

        anchor_score = max(
            0.0,
            1.0 - anchor_distance / 12.0,
        )

        jitter = rng.random()

        # Geography matters as much as risk.
        # This prevents a city's high-risk region
        # from visually swallowing all swarm pockets.
        base_score = risk * 0.45 + anchor_score * 0.45 + jitter * 0.10

        candidates_by_sector[sector].append(
            (
                base_score,
                row,
                column,
                risk,
            )
        )

    for sector in target_sectors:
        if not (candidates_by_sector[sector]):
            raise ValueError(f"{city_id}: no candidates for sector {sector}")

        candidates_by_sector[sector].sort(
            key=lambda candidate: (
                -candidate[0],
                candidate[1],
                candidate[2],
            )
        )

    selected: list[
        tuple[
            int,
            int,
            float,
        ]
    ] = []

    distance_passes = (
        8,
        6,
        SWARM_MIN_DISTANCE,
    )

    for sector in target_sectors:
        selected_candidate: (
            tuple[
                int,
                int,
                float,
            ]
            | None
        ) = None

        candidates = candidates_by_sector[sector]

        for minimum_distance in distance_passes:
            eligible: list[
                tuple[
                    float,
                    int,
                    int,
                    float,
                    int,
                ]
            ] = []

            for (
                base_score,
                row,
                column,
                risk,
            ) in candidates:
                separation = _minimum_distance_to_selected(
                    row=row,
                    column=column,
                    selected=selected,
                )

                if separation < minimum_distance:
                    continue

                spread_score = min(
                    1.0,
                    separation / 24.0,
                )

                final_score = base_score * 0.80 + spread_score * 0.20

                eligible.append(
                    (
                        final_score,
                        row,
                        column,
                        risk,
                        separation,
                    )
                )

            if not eligible:
                continue

            eligible.sort(
                key=lambda candidate: (
                    -candidate[0],
                    -candidate[4],
                    candidate[1],
                    candidate[2],
                )
            )

            (
                _score,
                row,
                column,
                risk,
                _separation,
            ) = eligible[0]

            selected_candidate = (
                row,
                column,
                float(risk),
            )

            break

        if selected_candidate is None:
            raise ValueError(
                f"{city_id}: unable to place "
                f"sector {sector} with "
                f"minimum distance "
                f"{SWARM_MIN_DISTANCE}"
            )

        selected.append(selected_candidate)

    result = tuple(selected)

    validate_swarm_distribution(
        result,
        city_id=city_id,
    )

    return result


def minimum_swarm_distance(
    hotspots: tuple[
        tuple[
            int,
            int,
            float,
        ],
        ...,
    ],
) -> int:
    if len(hotspots) < 2:
        return 72

    distances: list[int] = []

    for index, (
        row_a,
        column_a,
        _risk_a,
    ) in enumerate(hotspots):
        for (
            row_b,
            column_b,
            _risk_b,
        ) in hotspots[index + 1 :]:
            distances.append(abs(row_a - row_b) + abs(column_a - column_b))

    return min(distances)


def swarm_spans(
    hotspots: tuple[
        tuple[
            int,
            int,
            float,
        ],
        ...,
    ],
) -> tuple[int, int]:
    rows = [
        row
        for (
            row,
            _column,
            _risk,
        ) in hotspots
    ]

    columns = [
        column
        for (
            _row,
            column,
            _risk,
        ) in hotspots
    ]

    return (
        max(rows) - min(rows),
        max(columns) - min(columns),
    )


def validate_swarm_distribution(
    hotspots: tuple[
        tuple[
            int,
            int,
            float,
        ],
        ...,
    ],
    *,
    city_id: str,
) -> None:
    if len(hotspots) != SWARM_COUNTS[city_id]:
        raise ValueError(f"{city_id}: wrong swarm count")

    coordinates = {
        (
            row,
            column,
        )
        for (
            row,
            column,
            _risk,
        ) in hotspots
    }

    if len(coordinates) != len(hotspots):
        raise ValueError(f"{city_id}: duplicate swarm centers")

    sectors = {
        swarm_sector(
            row,
            column,
        )
        for (
            row,
            column,
            _risk,
        ) in hotspots
    }

    if len(sectors) != len(hotspots):
        raise ValueError(f"{city_id}: multiple swarms collapsed into one sector")

    planned = set(SWARM_SECTOR_PLAN[city_id])

    if sectors != planned:
        raise ValueError(f"{city_id}: swarm sectors do not match frozen plan")

    minimum_distance = minimum_swarm_distance(hotspots)

    if minimum_distance < SWARM_MIN_DISTANCE:
        raise ValueError(f"{city_id}: swarm centers too close together")

    row_span, column_span = swarm_spans(hotspots)

    if row_span < SWARM_MIN_ROW_SPAN:
        raise ValueError(f"{city_id}: swarm row span too narrow")

    if column_span < SWARM_MIN_COLUMN_SPAN:
        raise ValueError(f"{city_id}: swarm column span too narrow")


# ============================================================================
# Map drawing
# ============================================================================


def _draw_background_texture(
    draw: ImageDraw.ImageDraw,
    viewport: MissionBox,
) -> None:
    draw.rounded_rectangle(
        (
            viewport.x0,
            viewport.y0,
            viewport.x1,
            viewport.y1,
        ),
        radius=10,
        fill=PANEL,
        outline=BORDER,
        width=2,
    )

    for offset in range(
        -viewport.height,
        viewport.width,
        44,
    ):
        draw.line(
            (
                viewport.x0 + offset,
                viewport.y1,
                viewport.x0 + offset + viewport.height,
                viewport.y0,
            ),
            fill="#132135",
            width=1,
        )


def _draw_land(
    draw: ImageDraw.ImageDraw,
    city: dict[str, object],
    viewport: MissionBox,
) -> None:
    for cell in _cells(city):
        row, column = _cell_position(cell)

        terrain = _terrain_kind(_terrain_name(cell))

        box = _cell_box(
            row,
            column,
            viewport,
            inset=0.7,
        )

        if terrain == "building":
            draw.rounded_rectangle(
                box,
                radius=2,
                fill=BUILDING,
                outline=BUILDING_EDGE,
                width=1,
            )

        elif terrain == "rough":
            draw.rectangle(
                box,
                fill=ROUGH_LAND,
            )

        elif terrain == "open":
            draw.rectangle(
                box,
                fill=OPEN_LAND,
            )


def _road_cells(
    city: dict[str, object],
) -> tuple[
    set[tuple[int, int]],
    set[tuple[int, int]],
]:
    roads: set[tuple[int, int]] = set()

    arterial: set[tuple[int, int]] = set()

    for cell in _cells(city):
        row, column = _cell_position(cell)

        terrain = _terrain_kind(_terrain_name(cell))

        if terrain in {
            "local",
            "arterial",
        }:
            roads.add(
                (
                    row,
                    column,
                )
            )

        if terrain == "arterial":
            arterial.add(
                (
                    row,
                    column,
                )
            )

    return (
        roads,
        arterial,
    )


def _draw_roads(
    draw: ImageDraw.ImageDraw,
    city: dict[str, object],
    viewport: MissionBox,
) -> None:
    roads, arterial = _road_cells(city)

    for row, column in roads:
        here = _cell_center(
            row,
            column,
            viewport,
        )

        for neighbor in (
            (
                row + 1,
                column,
            ),
            (
                row,
                column + 1,
            ),
        ):
            if neighbor not in roads:
                continue

            there = _cell_center(
                neighbor[0],
                neighbor[1],
                viewport,
            )

            is_arterial = (
                row,
                column,
            ) in arterial or neighbor in arterial

            draw.line(
                (
                    here,
                    there,
                ),
                fill=(ARTERIAL_ROAD if is_arterial else LOCAL_ROAD),
                width=(8 if is_arterial else 5),
            )

            draw.line(
                (
                    here,
                    there,
                ),
                fill=ROAD_CENTER,
                width=1,
            )


def _draw_risk_haze(
    image: Image.Image,
    city: dict[str, object],
    viewport: MissionBox,
) -> None:
    overlay = Image.new(
        "RGBA",
        image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(
        overlay,
        "RGBA",
    )

    radius_x = max(
        14,
        round(viewport.width / 36.0 * 1.7),
    )

    radius_y = max(
        9,
        round(viewport.height / 36.0 * 1.9),
    )

    for cell in _cells(city):
        risk = float(_observed_risk(cell))

        if risk < 0.72:
            continue

        row, column = _cell_position(cell)

        x, y = _cell_center(
            row,
            column,
            viewport,
        )

        alpha = min(
            45,
            round(10 + risk * 34),
        )

        draw.ellipse(
            (
                x - radius_x,
                y - radius_y,
                x + radius_x,
                y + radius_y,
            ),
            fill=_rgba(
                ZOMBIE_DANGER,
                alpha,
            ),
        )

    composed = Image.alpha_composite(
        image.convert("RGBA"),
        overlay,
    ).convert("RGB")

    image.paste(composed)


# ============================================================================
# Zombie icons
# ============================================================================


def _draw_zombie_icon(
    draw: ImageDraw.ImageDraw,
    *,
    center: tuple[int, int],
    scale: float,
) -> None:
    x, y = center

    radius = max(
        3,
        round(6 * scale),
    )

    halo = max(
        6,
        round(11 * scale),
    )

    draw.ellipse(
        (
            x - halo,
            y - halo,
            x + halo,
            y + halo,
        ),
        fill=_rgba(
            ZOMBIE_DANGER,
            38,
        ),
    )

    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius,
        ),
        fill=ZOMBIE_SKIN,
        outline=ZOMBIE_DARK,
        width=1,
    )

    eye_dx = max(
        1,
        round(2.0 * scale),
    )

    for eye_x in (
        x - eye_dx,
        x + eye_dx,
    ):
        draw.ellipse(
            (
                eye_x - 1,
                y - 2,
                eye_x + 1,
                y,
            ),
            fill="#101812",
        )


def _swarm_icon_count(
    risk: float,
) -> int:
    if risk >= 0.82:
        return 5

    if risk >= 0.65:
        return 4

    if risk >= 0.40:
        return 3

    return 2


def _draw_swarms(
    draw: ImageDraw.ImageDraw,
    *,
    city_id: str,
    city: dict[str, object],
    viewport: MissionBox,
    compact: bool,
) -> None:
    scale = 0.44 if compact else 0.68

    offsets = (
        (
            0,
            0,
        ),
        (
            -13,
            7,
        ),
        (
            13,
            7,
        ),
        (
            -8,
            -11,
        ),
        (
            10,
            -11,
        ),
    )

    for (
        row,
        column,
        risk,
    ) in select_zombie_hotspots(
        city,
        city_id=city_id,
    ):
        center_x, center_y = _cell_center(
            row,
            column,
            viewport,
        )

        for (
            offset_x,
            offset_y,
        ) in offsets[: _swarm_icon_count(risk)]:
            _draw_zombie_icon(
                draw,
                center=(
                    center_x + round(offset_x * scale),
                    center_y + round(offset_y * scale),
                ),
                scale=scale,
            )


# ============================================================================
# Routes + mission markers
# ============================================================================


def _route_points(
    route: dict[str, object],
    viewport: MissionBox,
) -> tuple[
    tuple[int, int],
    ...,
]:
    raw_path = route.get("path")

    if not isinstance(
        raw_path,
        list,
    ):
        raise TypeError("route.path must be a list")

    return tuple(
        _cell_center(
            *_position(raw),
            viewport,
        )
        for raw in raw_path
    )


def _draw_final_route(
    draw: ImageDraw.ImageDraw,
    *,
    route: dict[str, object],
    viewport: MissionBox,
) -> None:
    points = _route_points(
        route,
        viewport,
    )

    if len(points) < 2:
        return

    draw.line(
        points,
        fill=_rgba(
            FINAL_ROUTE_COLOR,
            80,
        ),
        width=10,
        joint="curve",
    )

    draw.line(
        points,
        fill=FINAL_ROUTE_COLOR,
        width=5,
        joint="curve",
    )


def _draw_marker(
    draw: ImageDraw.ImageDraw,
    *,
    row: int,
    column: int,
    viewport: MissionBox,
    label: str,
    color: str,
    compact: bool,
) -> None:
    x, y = _cell_center(
        row,
        column,
        viewport,
    )

    radius = 5 if compact else 8

    draw.ellipse(
        (
            x - radius,
            y - radius,
            x + radius,
            y + radius,
        ),
        fill=color,
        outline=TEXT,
        width=1,
    )

    if compact:
        return

    font = _font(
        10,
        bold=True,
    )

    raw = draw.textbbox(
        (
            x + 11,
            y - 5,
        ),
        label,
        font=font,
        anchor="la",
    )

    draw.rounded_rectangle(
        (
            raw[0] - 4,
            raw[1] - 3,
            raw[2] + 4,
            raw[3] + 3,
        ),
        radius=4,
        fill=BACKGROUND,
        outline=color,
        width=1,
    )

    draw.text(
        (
            x + 11,
            y - 5,
        ),
        label,
        font=font,
        fill=TEXT,
        anchor="la",
    )


def _draw_mission_map(
    image: Image.Image,
    *,
    city_id: str,
    city: dict[str, object],
    viewport: MissionBox,
    compact: bool,
    route_overlay: RouteOverlay = "none",
    route: dict[str, object] | None = None,
) -> None:
    """
    Render a mission map.

    route_overlay="none":
        animation-safe base map

    route_overlay="final":
        post-search green chosen route
    """
    _validate_route_overlay(route_overlay)

    if route_overlay == "final" and route is None:
        raise ValueError("final route overlay requires route")

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    _draw_background_texture(
        draw,
        viewport,
    )

    _draw_land(
        draw,
        city,
        viewport,
    )

    _draw_roads(
        draw,
        city,
        viewport,
    )

    _draw_risk_haze(
        image,
        city,
        viewport,
    )

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    _draw_swarms(
        draw,
        city_id=city_id,
        city=city,
        viewport=viewport,
        compact=compact,
    )

    if route_overlay == "final":
        assert route is not None

        _draw_final_route(
            draw,
            route=route,
            viewport=viewport,
        )

    start, destination = MISSION_ENDPOINTS[city_id]

    _draw_marker(
        draw,
        row=start[0],
        column=start[1],
        viewport=viewport,
        label="CAMP A",
        color=START_COLOR,
        compact=compact,
    )

    _draw_marker(
        draw,
        row=destination[0],
        column=destination[1],
        viewport=viewport,
        label="SAFE ZONE",
        color=SAFE_COLOR,
        compact=compact,
    )


# ============================================================================
# Evaluation helpers
# ============================================================================


def _method_metrics(
    evaluation_city: dict[str, object],
    method_id: str,
) -> dict[str, object]:
    methods = evaluation_city.get("methods")

    if not isinstance(
        methods,
        dict,
    ):
        raise TypeError("evaluation methods missing")

    raw = methods.get(method_id)

    if not isinstance(
        raw,
        dict,
    ):
        raise KeyError(method_id)

    return cast(
        dict[str, object],
        raw,
    )


# ============================================================================
# Algorithm layer
# ============================================================================


def _draw_algorithm_layer(
    image: Image.Image,
    placements: list[MissionTextPlacement],
    *,
    city_id: str,
    city: dict[str, object],
    method_id: str,
    winner: bool,
    route_overlay: RouteOverlay,
    route: dict[str, object] | None,
) -> None:
    layer = METHOD_LAYER_BOXES[method_id]

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    draw.rectangle(
        (
            layer.x0,
            layer.y0,
            layer.x1,
            layer.y1,
        ),
        fill=PANEL_ALT,
    )

    draw.line(
        (
            0,
            layer.y0,
            CANVAS_SIZE,
            layer.y0,
        ),
        fill=BORDER,
        width=1,
    )

    method_color = (
        FINAL_ROUTE_COLOR if (winner and route_overlay == "final") else METHOD_COLORS[method_id]
    )

    _draw_text(
        draw,
        placements,
        xy=(
            14,
            layer.y0 + 45,
        ),
        text=METHOD_LABELS[method_id],
        font=_font(
            18,
            bold=True,
        ),
        fill=method_color,
    )

    _draw_text(
        draw,
        placements,
        xy=(
            14,
            layer.y0 + 79,
        ),
        text=(CITY_LABELS[city_id] + " Downtown"),
        font=_font(12),
        fill=TEXT_SECONDARY,
    )

    _draw_text(
        draw,
        placements,
        xy=(
            14,
            layer.y0 + 126,
        ),
        text="SEARCH",
        font=_font(
            10,
            bold=True,
        ),
        fill=TEXT_MUTED,
    )

    _draw_text(
        draw,
        placements,
        xy=(
            14,
            layer.y0 + 149,
        ),
        text=("search tree\nappears here\nin Step 10R"),
        font=_font(9),
        fill=TEXT_SECONDARY,
    )

    _draw_mission_map(
        image,
        city_id=city_id,
        city=city,
        viewport=method_map_box(method_id),
        compact=False,
        route_overlay=route_overlay,
        route=route,
    )


# ============================================================================
# Opening board — deliberately route-free
# ============================================================================


def render_opening_board(
    *,
    cities_payload: dict[str, object],
    routes_payload: dict[str, object],
    evaluation_payload: dict[str, object],
    output_path: Path,
) -> Path:
    del routes_payload

    validate_frame_geometry()

    image = _new_canvas()

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    placements: list[MissionTextPlacement] = []

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            46,
        ),
        text="WHO ESCAPES BEST?",
        font=_font(
            34,
            bold=True,
        ),
        fill=TEXT,
        anchor="ma",
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            99,
        ),
        text=("Dijkstra vs ML + A* vs Deep Learning + A*"),
        font=_font(17),
        fill=TEXT_SECONDARY,
        anchor="ma",
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            133,
        ),
        text=("Same city. Same Camp A. Same Safe Zone. Different perception of danger."),
        font=_font(13),
        fill=TEXT_MUTED,
        anchor="ma",
    )

    cards = opening_card_boxes()

    card_index = 0

    for city_id in CITY_ORDER:
        city = _city_payload(
            cities_payload,
            city_id,
        )

        evaluation_city = _evaluation_city_payload(
            evaluation_payload,
            city_id,
        )

        winner = cast(
            str,
            evaluation_city["winner_method"],
        )

        for method_id in METHOD_ORDER:
            card = cards[card_index]

            card_index += 1

            draw.rounded_rectangle(
                (
                    card.x0,
                    card.y0,
                    card.x1,
                    card.y1,
                ),
                radius=12,
                fill=PANEL_ALT,
                outline=BORDER,
                width=1,
            )

            _draw_text(
                draw,
                placements,
                xy=(
                    card.x0 + 10,
                    card.y0 + 11,
                ),
                text=CITY_LABELS[city_id],
                font=_font(
                    12,
                    bold=True,
                ),
                fill=TEXT,
            )

            _draw_text(
                draw,
                placements,
                xy=(
                    card.x1 - 10,
                    card.y0 + 11,
                ),
                text=METHOD_LABELS[method_id],
                font=_font(
                    10,
                    bold=True,
                ),
                fill=METHOD_COLORS[method_id],
                anchor="ra",
            )

            # No green route here.
            _draw_mission_map(
                image,
                city_id=city_id,
                city=city,
                viewport=opening_map_box(card),
                compact=True,
                route_overlay="none",
            )

            suffix = "WINNER REVEALED LATER" if method_id == winner else "MISSION READY"

            _draw_text(
                draw,
                placements,
                xy=(
                    card.x0 + 10,
                    card.y1 - 30,
                ),
                text=suffix,
                font=_font(
                    8,
                    bold=True,
                ),
                fill=TEXT_SECONDARY,
            )

    validate_text_placements(placements)

    return _save(
        image,
        output_path,
    )


# ============================================================================
# City comparison frame
#
# Default is deliberately route-free.
# ============================================================================


def render_city_frame(
    *,
    city_id: str,
    cities_payload: dict[str, object],
    routes_payload: dict[str, object],
    evaluation_payload: dict[str, object],
    output_path: Path,
    route_overlay: RouteOverlay = "none",
) -> Path:
    validate_frame_geometry()

    _validate_route_overlay(route_overlay)

    if city_id not in CITY_ORDER:
        raise KeyError(city_id)

    image = _new_canvas()

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    placements: list[MissionTextPlacement] = []

    city = _city_payload(
        cities_payload,
        city_id,
    )

    evaluation_city = _evaluation_city_payload(
        evaluation_payload,
        city_id,
    )

    winner = cast(
        str,
        evaluation_city["winner_method"],
    )

    draw.rectangle(
        (
            HEADING_BOX.x0,
            HEADING_BOX.y0,
            HEADING_BOX.x1,
            HEADING_BOX.y1,
        ),
        fill=BACKGROUND,
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            23,
        ),
        text=("DIJKSTRA vs ML vs DL — " + CITY_LABELS[city_id].upper() + " DOWNTOWN"),
        font=_font(
            20,
            bold=True,
        ),
        fill=TEXT,
        anchor="mm",
    )

    for method_id in METHOD_ORDER:
        route = (
            _method_route(
                routes_payload,
                city_id,
                method_id,
            )
            if route_overlay == "final"
            else None
        )

        _draw_algorithm_layer(
            image,
            placements,
            city_id=city_id,
            city=city,
            method_id=method_id,
            winner=(method_id == winner),
            route_overlay=route_overlay,
            route=route,
        )

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    draw.rectangle(
        (
            RESULT_BOX.x0,
            RESULT_BOX.y0,
            RESULT_BOX.x1,
            RESULT_BOX.y1,
        ),
        fill=("#0b2c23" if route_overlay == "final" else "#151f2d"),
    )

    if route_overlay == "none":
        result_text = "MISSION ACTIVE — SEARCH RESULTS HIDDEN UNTIL EXPLORATION COMPLETES"

        result_color = TEXT_SECONDARY

    else:
        metrics = _method_metrics(
            evaluation_city,
            winner,
        )

        travel = float(
            cast(
                float,
                metrics["travel_time"],
            )
        )

        risk = float(
            cast(
                float,
                metrics["true_cumulative_risk"],
            )
        )

        objective = float(
            cast(
                float,
                metrics["realized_objective"],
            )
        )

        result_text = (
            "CITY WINNER: "
            + METHOD_LABELS[winner]
            + f"   |   TIME {travel:.1f}"
            + f"   |   TRUE RISK {risk:.2f}"
            + f"   |   SCORE {objective:.2f}"
        )

        result_color = FINAL_ROUTE_COLOR

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            1058,
        ),
        text=result_text,
        font=_font(
            13,
            bold=True,
        ),
        fill=result_color,
        anchor="mm",
    )

    validate_text_placements(placements)

    return _save(
        image,
        output_path,
    )


# ============================================================================
# Final summary
#
# This occurs after all search sequences, so final green routes are allowed.
# ============================================================================


def render_final_summary(
    *,
    cities_payload: dict[str, object],
    routes_payload: dict[str, object],
    evaluation_payload: dict[str, object],
    output_path: Path,
) -> Path:
    validate_frame_geometry()

    image = _new_canvas()

    draw = ImageDraw.Draw(
        image,
        "RGBA",
    )

    placements: list[MissionTextPlacement] = []

    overall = evaluation_payload.get("overall")

    if not isinstance(
        overall,
        dict,
    ):
        raise TypeError("overall evaluation missing")

    overall_winner = overall.get("winner_method")

    if not isinstance(
        overall_winner,
        str,
    ):
        raise TypeError("overall winner missing")

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            65,
        ),
        text="MISSION COMPLETE",
        font=_font(
            28,
            bold=True,
        ),
        fill=TEXT_SECONDARY,
        anchor="ma",
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            120,
        ),
        text=(METHOD_LABELS[overall_winner] + " WINS OVERALL"),
        font=_font(
            34,
            bold=True,
        ),
        fill=FINAL_ROUTE_COLOR,
        anchor="ma",
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            172,
        ),
        text=("Best realized travel-time / zombie-risk tradeoff across all three missions"),
        font=_font(14),
        fill=TEXT_SECONDARY,
        anchor="ma",
    )

    cards = final_card_boxes()

    for index, city_id in enumerate(CITY_ORDER):
        card = cards[index]

        evaluation_city = _evaluation_city_payload(
            evaluation_payload,
            city_id,
        )

        city_winner = cast(
            str,
            evaluation_city["winner_method"],
        )

        city = _city_payload(
            cities_payload,
            city_id,
        )

        route = _method_route(
            routes_payload,
            city_id,
            city_winner,
        )

        draw.rounded_rectangle(
            (
                card.x0,
                card.y0,
                card.x1,
                card.y1,
            ),
            radius=14,
            fill=PANEL_ALT,
            outline=BORDER,
            width=2,
        )

        _draw_text(
            draw,
            placements,
            xy=(
                card.x0 + 12,
                card.y0 + 13,
            ),
            text=CITY_LABELS[city_id],
            font=_font(
                14,
                bold=True,
            ),
            fill=TEXT,
        )

        _draw_text(
            draw,
            placements,
            xy=(
                card.x1 - 12,
                card.y0 + 13,
            ),
            text=METHOD_LABELS[city_winner],
            font=_font(
                11,
                bold=True,
            ),
            fill=FINAL_ROUTE_COLOR,
            anchor="ra",
        )

        _draw_mission_map(
            image,
            city_id=city_id,
            city=city,
            viewport=final_map_box(card),
            compact=True,
            route_overlay="final",
            route=route,
        )

        _draw_text(
            draw,
            placements,
            xy=(
                card.x0 + 12,
                card.y1 - 31,
            ),
            text="SAFE ZONE REACHED",
            font=_font(
                10,
                bold=True,
            ),
            fill=SAFE_COLOR,
        )

    summary_box = MissionBox(
        145,
        650,
        935,
        865,
    )

    draw.rounded_rectangle(
        (
            summary_box.x0,
            summary_box.y0,
            summary_box.x1,
            summary_box.y1,
        ),
        radius=20,
        fill=PANEL_ALT,
        outline=FINAL_ROUTE_COLOR,
        width=3,
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            695,
        ),
        text="WHY IT WON",
        font=_font(
            17,
            bold=True,
        ),
        fill=TEXT_MUTED,
        anchor="ma",
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            754,
        ),
        text=("The winning planner best balanced travel time against true zombie exposure."),
        font=_font(
            16,
            bold=True,
        ),
        fill=TEXT,
        anchor="ma",
    )

    _draw_text(
        draw,
        placements,
        xy=(
            540,
            810,
        ),
        text=("Winner is computed from evaluation outputs — never hardcoded."),
        font=_font(13),
        fill=TEXT_SECONDARY,
        anchor="ma",
    )

    validate_text_placements(placements)

    return _save(
        image,
        output_path,
    )


# ============================================================================
# Five canonical Step 8R previews
# ============================================================================


def render_preview_frames(
    *,
    data_directory: Path,
    output_directory: Path,
) -> MissionPreviewArtifacts:
    (
        cities,
        _predictions,
        routes,
        evaluation,
    ) = load_visual_payloads(data_directory)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    opening = output_directory / "opening_board.png"

    render_opening_board(
        cities_payload=cities,
        routes_payload=routes,
        evaluation_payload=evaluation,
        output_path=opening,
    )

    city_paths: list[Path] = []

    for city_id in CITY_ORDER:
        output = output_directory / f"city_{city_id}.png"

        # Base city previews intentionally contain NO green final route.
        render_city_frame(
            city_id=city_id,
            cities_payload=cities,
            routes_payload=routes,
            evaluation_payload=evaluation,
            output_path=output,
            route_overlay="none",
        )

        city_paths.append(output)

    final_summary = output_directory / "final_summary.png"

    render_final_summary(
        cities_payload=cities,
        routes_payload=routes,
        evaluation_payload=evaluation,
        output_path=final_summary,
    )

    return MissionPreviewArtifacts(
        opening_board=opening,
        city_frames=tuple(city_paths),
        final_summary=final_summary,
    )


def _save(
    image: Image.Image,
    path: Path,
) -> Path:
    if image.size != (
        CANVAS_SIZE,
        CANVAS_SIZE,
    ):
        raise ValueError("preview must remain 1080 x 1080")

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(
        path,
        format="PNG",
        optimize=False,
    )

    return path


# ============================================================================
# Machine-readable contract used by later Step 10R / 9R
# ============================================================================


def mission_contract_payload() -> dict[
    str,
    object,
]:
    return {
        "schema_version": 3,
        "canvas": {
            "width": 1080,
            "height": 1080,
        },
        "city_frame": {
            "heading_height": (HEADING_HEIGHT),
            "method_layer_height": (METHOD_LAYER_HEIGHT),
            "result_height": (RESULT_HEIGHT),
            "method_order": list(METHOD_ORDER),
        },
        "base_city_frame": {
            "route_overlay": "none",
            "camp_a_visible": True,
            "safe_zone_visible": True,
            "search_tree_visible": False,
        },
        "final_reveal": {
            "route_overlay": "final",
            "route_source": ("computed routes.json"),
            "route_is_hardcoded": False,
        },
        "swarms": {
            "counts": dict(SWARM_COUNTS),
            "seeds": dict(SWARM_SEEDS),
            "sector_grid": [
                3,
                3,
            ],
            "sector_plan": {
                city_id: [list(sector) for sector in sectors]
                for (
                    city_id,
                    sectors,
                ) in (SWARM_SECTOR_PLAN.items())
            },
            "one_center_per_sector": True,
            "minimum_manhattan_distance": (SWARM_MIN_DISTANCE),
            "minimum_row_span": (SWARM_MIN_ROW_SPAN),
            "minimum_column_span": (SWARM_MIN_COLUMN_SPAN),
        },
        "search_animation": {
            "provided_by": ("Step 10R and Step 9R"),
            "fake_search_tree_allowed": False,
            "explored_active": (EXPLORED_COLOR),
            "explored_rejected": (REJECTED_COLOR),
            "final_route": (FINAL_ROUTE_COLOR),
            "final_route_initially_visible": False,
        },
    }


def write_mission_contract(
    path: Path,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            mission_contract_payload(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return path
