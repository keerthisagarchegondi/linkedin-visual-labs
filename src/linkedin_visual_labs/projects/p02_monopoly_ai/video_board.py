"""V4 cinematic tabletop renderer for Project 3."""

from __future__ import annotations

import io
import math
from functools import lru_cache
from pathlib import Path
from typing import Final

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from PIL import (
    Image,
    ImageDraw,
    ImageFilter,
    ImageFont,
)

from linkedin_visual_labs.projects.p02_monopoly_ai.piece_assets_3d import (
    PIECE_NAMES,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_replay import (
    DISPLAY_NAMES,
    GameState,
    TurnBeat,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
    board_positions,
    draw_board,
    load_board_spaces,
)

WIDTH: Final = 1080
HEIGHT: Final = 1080

SCALE: Final = 2
RW: Final = WIDTH * SCALE
RH: Final = HEIGHT * SCALE


BACKGROUND = (4, 9, 16)
WHITE = (248, 250, 252)
CREAM = (245, 240, 226)
INK = (28, 31, 35)
MUTED = (178, 191, 210)
GOLD = (250, 204, 21)
GREEN = (34, 197, 94)
RED = (248, 70, 70)
AMBER = (251, 146, 60)

ACCENTS = {
    "collector": (71, 181, 255),
    "specialist": (211, 116, 255),
    "cash_protector": (63, 220, 167),
    "aggressive_builder": (255, 156, 66),
}

STRATEGY_ORDER = (
    "collector",
    "specialist",
    "cash_protector",
    "aggressive_builder",
)

PIECE_ROOT = Path("outputs/p02_monopoly_ai/visual/v6_3d_piece_assets")


# Source board fills its image completely.
SOURCE_SIZE = 1000

# Cinematic perspective quad at render resolution.
# Large enough that the board dominates the frame.
BOARD_QUAD = np.array(
    [
        [112 * SCALE, 210 * SCALE],
        [968 * SCALE, 210 * SCALE],
        [1055 * SCALE, 860 * SCALE],
        [25 * SCALE, 860 * SCALE],
    ],
    dtype=np.float64,
)


def s(value: float) -> int:
    return round(value * SCALE)


@lru_cache(maxsize=64)
def font(
    size: int,
    bold: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        (
            "DejaVuSans-Bold.ttf",
            "Arial Bold.ttf",
        )
        if bold
        else (
            "DejaVuSans.ttf",
            "Arial.ttf",
        )
    )

    for candidate in candidates:
        try:
            return ImageFont.truetype(
                candidate,
                s(size),
            )
        except OSError:
            continue

    return ImageFont.load_default()


def ease(value: float) -> float:
    value = max(
        0.0,
        min(
            1.0,
            value,
        ),
    )

    return value * value * (3.0 - 2.0 * value)


def text_center(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    center_x: float,
    y: float,
    size: int,
    fill: tuple[int, int, int] = WHITE,
    bold: bool = True,
) -> None:
    active_font = font(
        size,
        bold,
    )

    box = draw.textbbox(
        (0, 0),
        text,
        font=active_font,
    )

    width = box[2] - box[0]

    draw.text(
        (
            s(center_x) - width / 2,
            s(y),
        ),
        text,
        font=active_font,
        fill=fill,
    )


@lru_cache(maxsize=1)
def source_board() -> Image.Image:
    spaces = load_board_spaces(Path("configs/p02_monopoly_ai.yaml"))

    figure = plt.figure(
        figsize=(10, 10),
        dpi=100,
        facecolor=(0.025, 0.045, 0.07),
    )

    axis = figure.add_axes((0, 0, 1, 1))

    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")

    draw_board(
        axis,
        spaces,
        center_title=False,
    )

    buffer = io.BytesIO()

    figure.savefig(
        buffer,
        format="png",
        dpi=100,
        bbox_inches=None,
        pad_inches=0,
    )

    plt.close(figure)

    buffer.seek(0)

    with Image.open(buffer) as image:
        result = image.convert("RGBA").resize(
            (
                SOURCE_SIZE,
                SOURCE_SIZE,
            ),
            Image.Resampling.LANCZOS,
        )

    return result


def homography(
    source: np.ndarray,
    destination: np.ndarray,
) -> np.ndarray:
    rows = []
    values = []

    for (
        (x, y),
        (u, v),
    ) in zip(
        source,
        destination,
        strict=True,
    ):
        rows.append(
            [
                x,
                y,
                1,
                0,
                0,
                0,
                -u * x,
                -u * y,
            ]
        )

        values.append(u)

        rows.append(
            [
                0,
                0,
                0,
                x,
                y,
                1,
                -v * x,
                -v * y,
            ]
        )

        values.append(v)

    coefficients = np.linalg.solve(
        np.asarray(
            rows,
            dtype=np.float64,
        ),
        np.asarray(
            values,
            dtype=np.float64,
        ),
    )

    return np.array(
        [
            [
                coefficients[0],
                coefficients[1],
                coefficients[2],
            ],
            [
                coefficients[3],
                coefficients[4],
                coefficients[5],
            ],
            [
                coefficients[6],
                coefficients[7],
                1.0,
            ],
        ],
        dtype=np.float64,
    )


SOURCE_CORNERS = np.array(
    [
        [0, 0],
        [SOURCE_SIZE - 1, 0],
        [
            SOURCE_SIZE - 1,
            SOURCE_SIZE - 1,
        ],
        [0, SOURCE_SIZE - 1],
    ],
    dtype=np.float64,
)

SOURCE_TO_SCREEN = homography(
    SOURCE_CORNERS,
    BOARD_QUAD,
)

SCREEN_TO_SOURCE = np.linalg.inv(SOURCE_TO_SCREEN)


def transform_point(
    x: float,
    y: float,
) -> tuple[float, float]:
    vector = np.array(
        [
            x,
            y,
            1.0,
        ],
        dtype=np.float64,
    )

    transformed = SOURCE_TO_SCREEN @ vector

    transformed /= transformed[2]

    return (
        float(transformed[0]),
        float(transformed[1]),
    )


def perspective_coefficients() -> tuple[float, ...]:
    matrix = SCREEN_TO_SOURCE

    matrix = matrix / matrix[2, 2]

    return (
        float(matrix[0, 0]),
        float(matrix[0, 1]),
        float(matrix[0, 2]),
        float(matrix[1, 0]),
        float(matrix[1, 1]),
        float(matrix[1, 2]),
        float(matrix[2, 0]),
        float(matrix[2, 1]),
    )


@lru_cache(maxsize=1)
def tabletop_board() -> Image.Image:
    board = source_board()

    warped = board.transform(
        (
            RW,
            RH,
        ),
        Image.Transform.PERSPECTIVE,
        perspective_coefficients(),
        resample=Image.Resampling.BICUBIC,
    )

    # Ground shadow under the table.
    alpha = warped.getchannel("A")

    shadow = Image.new(
        "RGBA",
        (
            RW,
            RH,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    shadow_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=s(15)))

    shadow.putalpha(shadow_alpha.point(lambda value: round(value * 0.42)))

    shifted = Image.new(
        "RGBA",
        (
            RW,
            RH,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    shifted.alpha_composite(
        shadow,
        (
            s(0),
            s(20),
        ),
    )

    shifted.alpha_composite(warped)

    return shifted


@lru_cache(maxsize=128)
def piece_asset(
    strategy: str,
    size: int,
) -> Image.Image:
    path = PIECE_ROOT / (PIECE_NAMES[strategy] + ".png")

    with Image.open(path) as image:
        return image.convert("RGBA").resize(
            (
                s(size),
                s(size),
            ),
            Image.Resampling.LANCZOS,
        )


def paste_center(
    canvas: Image.Image,
    source: Image.Image,
    x: float,
    y: float,
) -> None:
    overlay = source if source.mode == "RGBA" else source.convert("RGBA")

    canvas.alpha_composite(
        overlay,
        (
            round(x - overlay.width / 2),
            round(y - overlay.height / 2),
        ),
    )


def board_xy(
    index: int,
) -> tuple[float, float]:
    x, y = board_positions()[index % 40]

    source_x = x * SOURCE_SIZE

    source_y = (1.0 - y) * SOURCE_SIZE

    return transform_point(
        source_x,
        source_y,
    )


def route(
    start: int,
    end: int,
) -> tuple[int, ...]:
    start %= 40
    end %= 40

    distance = (end - start) % 40

    return tuple((start + offset) % 40 for offset in range(distance + 1))


def moving_position(
    start: int,
    end: int,
    progress: float,
) -> tuple[
    float,
    float,
    float,
]:
    locations = tuple(
        board_xy(index)
        for index in route(
            start,
            end,
        )
    )

    progress = max(
        0.0,
        min(
            1.0,
            progress,
        ),
    )

    if len(locations) == 1:
        x, y = locations[0]
        return x, y, 0.0

    lift_height = s(46)

    if progress < 0.10:
        travel = 0.0
        lift = lift_height * ease(progress / 0.10)

    elif progress > 0.90:
        travel = 1.0
        lift = lift_height * (1.0 - ease((progress - 0.90) / 0.10))

    else:
        travel = (progress - 0.10) / 0.80

        lift = float(lift_height)

    scaled = travel * (len(locations) - 1)

    segment = min(
        len(locations) - 2,
        math.floor(scaled),
    )

    local = ease(scaled - segment)

    first = locations[segment]

    second = locations[segment + 1]

    x = first[0] + (second[0] - first[0]) * local

    y = first[1] + (second[1] - first[1]) * local - lift

    return (
        x,
        y,
        lift,
    )


PIPS = {
    1: ((0.50, 0.50),),
    2: (
        (0.28, 0.28),
        (0.72, 0.72),
    ),
    3: (
        (0.28, 0.28),
        (0.50, 0.50),
        (0.72, 0.72),
    ),
    4: (
        (0.28, 0.28),
        (0.72, 0.28),
        (0.28, 0.72),
        (0.72, 0.72),
    ),
    5: (
        (0.28, 0.28),
        (0.72, 0.28),
        (0.50, 0.50),
        (0.28, 0.72),
        (0.72, 0.72),
    ),
    6: (
        (0.28, 0.24),
        (0.72, 0.24),
        (0.28, 0.50),
        (0.72, 0.50),
        (0.28, 0.76),
        (0.72, 0.76),
    ),
}


def die_face(
    value: int,
    *,
    size: int,
    rotation: float = 0.0,
) -> Image.Image:
    pixels = s(size)

    tile = Image.new(
        "RGBA",
        (
            pixels,
            pixels,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(tile)

    margin = s(5)

    draw.rounded_rectangle(
        (
            margin,
            margin,
            pixels - margin,
            pixels - margin,
        ),
        radius=s(11),
        fill=(
            244,
            240,
            229,
            255,
        ),
        outline=(
            170,
            163,
            147,
            255,
        ),
        width=s(2),
    )

    # subtle lower-right depth edge
    draw.line(
        (
            s(size * 0.18),
            s(size * 0.86),
            s(size * 0.82),
            s(size * 0.86),
        ),
        fill=(
            135,
            129,
            117,
            210,
        ),
        width=s(3),
    )

    radius = s(size * 0.065)

    for x_fraction, y_fraction in PIPS[value]:
        x = round(pixels * x_fraction)

        y = round(pixels * y_fraction)

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            ),
            fill=(
                24,
                26,
                29,
                255,
            ),
        )

    if abs(rotation) > 0.001:
        tile = tile.rotate(
            rotation,
            resample=Image.Resampling.BICUBIC,
            expand=True,
        )

    return tile


def draw_dice(
    image: Image.Image,
    dice: tuple[int, int],
    progress: float,
) -> None:
    progress = ease(progress)

    positions = (
        (
            s(462),
            s(500),
        ),
        (
            s(605),
            s(508),
        ),
    )

    rotations = (
        (18 * (1.0 - progress)),
        (-16 * (1.0 - progress)),
    )

    for value, position, rotation in zip(
        dice,
        positions,
        rotations,
        strict=True,
    ):
        shadow = Image.new(
            "RGBA",
            (
                s(118),
                s(118),
            ),
            (
                0,
                0,
                0,
                0,
            ),
        )

        shadow_draw = ImageDraw.Draw(shadow)

        shadow_draw.ellipse(
            (
                s(14),
                s(75),
                s(104),
                s(105),
            ),
            fill=(
                0,
                0,
                0,
                95,
            ),
        )

        shadow = shadow.filter(ImageFilter.GaussianBlur(s(5)))

        paste_center(
            image,
            shadow,
            position[0],
            position[1] + s(14),
        )

        die = die_face(
            value,
            size=88,
            rotation=rotation,
        )

        paste_center(
            image,
            die,
            position[0],
            position[1] - s(20 * (1.0 - progress)),
        )


def draw_status_rail(
    image: Image.Image,
    state: GameState,
    active: str,
) -> None:
    draw = ImageDraw.Draw(image)

    left = s(48)
    top = s(896)
    right = s(1032)
    bottom = s(978)

    draw.rounded_rectangle(
        (
            left,
            top,
            right,
            bottom,
        ),
        radius=s(16),
        fill=(
            6,
            14,
            25,
            235,
        ),
        outline=(
            77,
            91,
            113,
            255,
        ),
        width=s(1),
    )

    slot_width = s(238)

    for index, strategy in enumerate(STRATEGY_ORDER):
        slot_left = s(62) + index * slot_width

        accent = ACCENTS[strategy]

        if strategy == active:
            draw.rounded_rectangle(
                (
                    slot_left,
                    s(908),
                    slot_left + s(222),
                    s(966),
                ),
                radius=s(10),
                fill=(
                    *accent,
                    32,
                ),
                outline=(
                    *accent,
                    255,
                ),
                width=s(2),
            )

        paste_center(
            image,
            piece_asset(
                strategy,
                (42 if strategy == active else 36),
            ),
            slot_left + s(27),
            s(938),
        )

        draw.text(
            (
                slot_left + s(52),
                s(913),
            ),
            DISPLAY_NAMES[strategy],
            font=font(
                12,
                True,
            ),
            fill=(accent if strategy == active else WHITE),
        )

        cash = state.cash[strategy]

        draw.text(
            (
                slot_left + s(52),
                s(938),
            ),
            f"${cash:,.0f}",
            font=font(
                18,
                True,
            ),
            fill=(RED if cash < 200 else (AMBER if cash < 450 else WHITE)),
        )


def draw_grounded_piece(
    image: Image.Image,
    *,
    strategy: str,
    x: float,
    y: float,
    size: int,
    lift: float = 0.0,
) -> None:
    shadow_width = s(34 + lift / SCALE * 0.10)

    shadow_height = s(10)

    shadow_layer = Image.new(
        "RGBA",
        (
            RW,
            RH,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(shadow_layer)

    draw.ellipse(
        (
            x - shadow_width,
            y + s(20),
            x + shadow_width,
            y + s(20) + shadow_height,
        ),
        fill=(
            0,
            0,
            0,
            125,
        ),
    )

    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(s(4)))

    image.alpha_composite(shadow_layer)

    paste_center(
        image,
        piece_asset(
            strategy,
            size,
        ),
        x,
        y,
    )


def draw_state(
    image: Image.Image,
    state: GameState,
    *,
    active: str,
    move_from: int,
    move_to: int,
    movement: float,
) -> None:
    draw = ImageDraw.Draw(image)

    for space, strategy in state.ownership.items():
        x, y = board_xy(space)

        radius = s(7)

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            ),
            fill=ACCENTS[strategy],
            outline=WHITE,
            width=s(1),
        )

    for space, count in state.houses.items():
        if count <= 0:
            continue

        x, y = board_xy(space)

        count = min(
            4,
            count,
        )

        for index in range(count):
            hx = x + s((index - (count - 1) / 2) * 10)

            hy = y + s(13)

            draw.polygon(
                (
                    (
                        hx - s(5),
                        hy,
                    ),
                    (
                        hx,
                        hy - s(5),
                    ),
                    (
                        hx + s(5),
                        hy,
                    ),
                    (
                        hx + s(5),
                        hy + s(8),
                    ),
                    (
                        hx - s(5),
                        hy + s(8),
                    ),
                ),
                fill=GREEN,
                outline=WHITE,
            )

    offsets = {
        "collector": (-11, -8),
        "specialist": (11, -8),
        "cash_protector": (-11, 9),
        "aggressive_builder": (11, 9),
    }

    for strategy in STRATEGY_ORDER:
        if strategy in state.bankrupt:
            continue

        if strategy == active:
            x, y, lift = moving_position(
                move_from,
                move_to,
                movement,
            )

            size = 68 + round((lift / SCALE) * 0.16)

        else:
            x, y = board_xy(state.positions[strategy])

            ox, oy = offsets[strategy]

            x += s(ox)
            y += s(oy)

            lift = 0.0
            size = 52

        draw_grounded_piece(
            image,
            strategy=strategy,
            x=x,
            y=y,
            size=size,
            lift=lift,
        )


def physical_card(
    image: Image.Image,
    *,
    title: str,
    primary: str,
    secondary: str,
    accent: tuple[int, int, int],
    progress: float,
) -> None:
    progress = ease(progress)

    width = s(326 * progress)

    if width < s(10):
        return

    full_width = s(326)
    full_height = s(184)

    card = Image.new(
        "RGBA",
        (
            full_width,
            full_height,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    shadow = Image.new(
        "RGBA",
        card.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    shadow_draw = ImageDraw.Draw(shadow)

    shadow_draw.rounded_rectangle(
        (
            s(12),
            s(12),
            full_width - s(8),
            full_height - s(4),
        ),
        radius=s(10),
        fill=(
            0,
            0,
            0,
            125,
        ),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(s(7)))

    card.alpha_composite(shadow)

    draw = ImageDraw.Draw(card)

    draw.rounded_rectangle(
        (
            s(4),
            s(4),
            full_width - s(14),
            full_height - s(14),
        ),
        radius=s(8),
        fill=(
            *CREAM,
            255,
        ),
        outline=(
            95,
            89,
            78,
            255,
        ),
        width=s(2),
    )

    draw.rectangle(
        (
            s(15),
            s(15),
            full_width - s(25),
            s(55),
        ),
        fill=(
            *accent,
            255,
        ),
    )

    local_draw = draw

    def local_center(
        text: str,
        y: int,
        size: int,
        color: tuple[int, int, int],
    ) -> None:
        active_font = font(
            size,
            True,
        )

        box = local_draw.textbbox(
            (0, 0),
            text,
            font=active_font,
        )

        local_draw.text(
            (
                (full_width - (box[2] - box[0])) / 2,
                s(y),
            ),
            text,
            font=active_font,
            fill=color,
        )

    local_center(
        title,
        23,
        14,
        WHITE,
    )

    local_center(
        primary,
        78,
        24,
        INK,
    )

    local_center(
        secondary,
        127,
        15,
        (
            62,
            67,
            73,
        ),
    )

    cropped = card.crop(
        (
            (full_width - width) // 2,
            0,
            (full_width + width) // 2,
            full_height,
        )
    )

    paste_center(
        image,
        cropped,
        s(540),
        s(530),
    )


def action_text(
    turn: TurnBeat,
) -> tuple[
    str,
    str,
    str,
]:
    strategy = DISPLAY_NAMES[turn.strategy_id]

    property_name = turn.property_name or "Board Space"

    if turn.primary_action == "PURCHASE":
        return (
            property_name.upper(),
            "PROPERTY ACQUIRED",
            strategy,
        )

    if turn.primary_action == "BUILD":
        return (
            property_name.upper(),
            "HOUSE BUILT",
            strategy,
        )

    if turn.primary_action == "RENT":
        amount = f"${abs(turn.amount):,.0f}" if turn.amount is not None else "RENT"

        return (
            "RENT DUE",
            amount,
            strategy,
        )

    if turn.primary_action == "GROUP_COMPLETE":
        return (
            "GROUP COMPLETE",
            property_name,
            strategy,
        )

    if turn.primary_action == "BANKRUPTCY":
        return (
            "LIQUIDITY CRISIS",
            "BANKRUPTCY",
            strategy,
        )

    before = turn.state_before.cash[turn.strategy_id]

    after = turn.state_after.cash[turn.strategy_id]

    delta = after - before

    return (
        turn.primary_action.replace(
            "_",
            " ",
        ),
        (f"{delta:+,.0f} CASH" if abs(delta) >= 1 else strategy),
        property_name,
    )


def draw_caption(
    image: Image.Image,
    headline: str,
    *,
    subline: str = "",
    accent: tuple[int, int, int] = WHITE,
) -> None:
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (
            0,
            s(986),
            RW,
            RH,
        ),
        fill=(
            3,
            9,
            17,
            255,
        ),
    )

    text_center(
        draw,
        headline,
        center_x=540,
        y=996,
        size=24,
        fill=accent,
    )

    if subline:
        text_center(
            draw,
            subline,
            center_x=540,
            y=1031,
            size=13,
            fill=MUTED,
            bold=False,
        )


def apply_vignette(
    image: Image.Image,
) -> None:
    overlay = Image.new(
        "RGBA",
        (
            RW,
            RH,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(overlay)

    for index in range(22):
        alpha = round(index / 21 * 4)

        inset = s(index * 6)

        draw.rectangle(
            (
                inset,
                inset,
                RW - inset,
                RH - inset,
            ),
            outline=(
                0,
                0,
                0,
                alpha,
            ),
            width=s(7),
        )

    image.alpha_composite(overlay)


def render_turn(
    turn: TurnBeat,
    progress: float,
    *,
    headline: str,
    subline: str = "",
    show_card: bool = True,
    show_question: bool = False,
) -> Image.Image:
    progress = max(
        0.0,
        min(
            1.0,
            progress,
        ),
    )

    image = Image.new(
        "RGBA",
        (
            RW,
            RH,
        ),
        (
            *BACKGROUND,
            255,
        ),
    )

    image.alpha_composite(tabletop_board())

    dice_end = 0.20
    move_start = 0.18
    move_end = 0.67
    action_start = 0.68

    state = turn.state_before if progress < move_end else turn.state_after

    movement = (
        0.0
        if progress <= move_start
        else (
            1.0 if progress >= move_end else ease((progress - move_start) / (move_end - move_start))
        )
    )

    draw_state(
        image,
        state,
        active=turn.strategy_id,
        move_from=turn.from_position,
        move_to=turn.to_position,
        movement=movement,
    )

    if turn.dice is not None and progress <= dice_end:
        draw_dice(
            image,
            turn.dice,
            min(
                1.0,
                progress / dice_end,
            ),
        )

    if show_card and progress >= action_start:
        title, primary, secondary = action_text(turn)

        physical_card(
            image,
            title=title,
            primary=primary,
            secondary=secondary,
            accent=ACCENTS[turn.strategy_id],
            progress=((progress - action_start) / (1.0 - action_start)),
        )

    draw_status_rail(
        image,
        state,
        turn.strategy_id,
    )

    if show_question:
        draw_caption(
            image,
            "WHICH AI LANDLORD SURVIVES 10,000 GAMES?",
            subline=("Same starting cash. Different investment rules."),
            accent=GOLD,
        )

    else:
        draw_caption(
            image,
            headline,
            subline=subline,
            accent=ACCENTS[turn.strategy_id],
        )

    apply_vignette(image)

    return image.convert("RGB").resize(
        (
            WIDTH,
            HEIGHT,
        ),
        Image.Resampling.LANCZOS,
    )
