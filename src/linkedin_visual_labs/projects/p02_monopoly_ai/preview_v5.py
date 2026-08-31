"""V5 cinematic preview laboratory for Project 3.

This module intentionally renders only thirteen art-direction stills.
It does not render the final 60-second video.
"""

from __future__ import annotations

import io
import math
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
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
    load_replay,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
    draw_board,
    load_board_spaces,
    load_preview_context,
)

WIDTH: Final = 1080
HEIGHT: Final = 1080
SCALE: Final = 2

RW: Final = WIDTH * SCALE
RH: Final = HEIGHT * SCALE

OUTPUT_DIRECTORY: Final = Path("outputs/p02_monopoly_ai/visual/v5_preview_lab")

CONTACT_SHEET: Final = OUTPUT_DIRECTORY / "v5_storyboard_contact_sheet.jpg"

PIECE_DIRECTORY: Final = Path("outputs/p02_monopoly_ai/visual/v6_3d_piece_assets")

VALIDATION_DIRECTORY: Final = Path("outputs/p02_monopoly_ai/validation")

CONFIG_PATH: Final = Path("configs/p02_monopoly_ai.yaml")


BACKGROUND = (
    5,
    10,
    18,
)

BACKGROUND_SOFT = (
    9,
    17,
    29,
)

WHITE = (
    248,
    250,
    252,
)

MUTED = (
    179,
    191,
    209,
)

CREAM = (
    244,
    239,
    224,
)

INK = (
    29,
    32,
    36,
)

GOLD = (
    250,
    204,
    21,
)

GREEN = (
    34,
    197,
    94,
)

RED = (
    248,
    70,
    70,
)

AMBER = (
    251,
    146,
    60,
)


# ---------------------------------------------------------------------
# Mandatory 1080x1080 social-video typography scale.
#
# These values are FINAL 1080-pixel-equivalent sizes. font() applies
# the internal 2x supersampling factor automatically.
# ---------------------------------------------------------------------

TYPE_HERO = 76
TYPE_DISPLAY = 58
TYPE_HEADLINE = 46
TYPE_SECTION = 34
TYPE_METRIC = 31
TYPE_LABEL = 24
TYPE_BODY = 19
TYPE_SMALL = 16
TYPE_FINE = 13

ACCENTS = {
    "collector": (
        68,
        180,
        255,
    ),
    "specialist": (
        206,
        103,
        255,
    ),
    "cash_protector": (
        61,
        220,
        164,
    ),
    "aggressive_builder": (
        255,
        151,
        61,
    ),
}

STRATEGY_ORDER = (
    "collector",
    "specialist",
    "cash_protector",
    "aggressive_builder",
)


@dataclass(frozen=True)
class StrategyMetric:
    strategy_id: str
    win_rate: float
    bankruptcy_rate: float
    median_finishing_cash: float
    ci_lower: float
    ci_upper: float


@dataclass(frozen=True)
class StoryBeat:
    label: str
    turn: TurnBeat


@dataclass(frozen=True)
class PreviewStoryPlan:
    dice_turn: TurnBeat
    move_turn: TurnBeat
    purchase_turn: TurnBeat
    build_turn: TurnBeat
    rent_turn: TurnBeat
    shock_turn: TurnBeat
    survival_turn: TurnBeat
    strategy_turns: tuple[
        TurnBeat,
        ...,
    ]
    narrative_beats: tuple[
        StoryBeat,
        ...,
    ]

    @property
    def narrative_turns(
        self,
    ) -> tuple[
        TurnBeat,
        ...,
    ]:
        return tuple(beat.turn for beat in self.narrative_beats)


@dataclass(frozen=True)
class PreviewRuntime:
    turns: tuple[TurnBeat, ...]
    story: PreviewStoryPlan
    metrics: tuple[StrategyMetric, ...]
    headline_winner: str | None


def s(
    value: float,
) -> int:
    return round(value * SCALE)


@lru_cache(maxsize=96)
def font(
    size: int,
    *,
    bold: bool = False,
) -> ImageFont.FreeTypeFont:
    """Load a real scalable font for deterministic social-video type.

    Never fall back to Pillow's tiny bitmap default because that would
    silently invalidate the V5 typography scale.
    """

    windows_regular = (
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    )

    windows_bold = (
        Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
    )

    linux_regular = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    )

    linux_bold = (
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    )

    candidates = (
        (
            *windows_bold,
            *linux_bold,
        )
        if bold
        else (
            *windows_regular,
            *linux_regular,
        )
    )

    requested_size = s(size)

    for candidate in candidates:
        if not candidate.is_file():
            continue

        try:
            loaded = ImageFont.truetype(
                str(candidate),
                requested_size,
            )

        except OSError:
            continue

        return loaded

    raise RuntimeError(
        "No scalable V5 font could be loaded. "
        f"bold={bold}, size={size}, "
        f"candidates={[str(path) for path in candidates]}"
    )


def ease(
    value: float,
) -> float:
    value = max(
        0.0,
        min(
            1.0,
            value,
        ),
    )

    return value * value * (3.0 - 2.0 * value)


def rgba_canvas() -> Image.Image:
    return Image.new(
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


def downsample(
    image: Image.Image,
) -> Image.Image:
    return image.convert("RGB").resize(
        (
            WIDTH,
            HEIGHT,
        ),
        Image.Resampling.LANCZOS,
    )


def paste_center(
    canvas: Image.Image,
    overlay: Image.Image,
    *,
    x: float,
    y: float,
) -> None:
    rgba = overlay if overlay.mode == "RGBA" else overlay.convert("RGBA")

    canvas.alpha_composite(
        rgba,
        (
            round(s(x) - rgba.width / 2),
            round(s(y) - rgba.height / 2),
        ),
    )


def centered_text(
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
        bold=bold,
    )

    box = draw.textbbox(
        (
            0,
            0,
        ),
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


def left_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    x: float,
    y: float,
    size: int,
    fill: tuple[int, int, int] = WHITE,
    bold: bool = True,
) -> None:
    draw.text(
        (
            s(x),
            s(y),
        ),
        text,
        font=font(
            size,
            bold=bold,
        ),
        fill=fill,
    )


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[
        float,
        float,
        float,
        float,
    ],
    *,
    radius: int = 20,
    fill: tuple[int, int, int] = BACKGROUND_SOFT,
    outline: tuple[int, int, int] = (
        64,
        79,
        101,
    ),
    width: int = 2,
) -> None:
    draw.rounded_rectangle(
        tuple(s(value) for value in box),
        radius=s(radius),
        fill=fill,
        outline=outline,
        width=s(width),
    )


def add_vignette(
    image: Image.Image,
    *,
    strength: int = 135,
) -> None:
    """Apply a smooth cinematic vignette with no visible contour bands."""

    if strength <= 0:
        return

    mask = Image.new(
        "L",
        (
            RW,
            RH,
        ),
        0,
    )

    pixels = mask.load()

    if pixels is None:
        raise RuntimeError("Could not allocate vignette mask.")

    center_x = RW / 2.0

    center_y = RH / 2.0

    radius_x = RW * 0.69

    radius_y = RH * 0.67

    for y in range(RH):
        normalized_y = (y - center_y) / radius_y

        normalized_y_squared = normalized_y * normalized_y

        for x in range(RW):
            normalized_x = (x - center_x) / radius_x

            distance = math.sqrt(normalized_x * normalized_x + normalized_y_squared)

            edge = max(
                0.0,
                min(
                    1.0,
                    (distance - 0.52) / 0.48,
                ),
            )

            alpha = round(strength * ease(edge))

            pixels[
                x,
                y,
            ] = alpha

    mask = mask.filter(ImageFilter.GaussianBlur(s(28)))

    darkness = Image.new(
        "RGBA",
        (
            RW,
            RH,
        ),
        (
            0,
            0,
            0,
            255,
        ),
    )

    darkness.putalpha(mask)

    image.alpha_composite(darkness)


@lru_cache(maxsize=1)
@lru_cache(maxsize=1)
def board_image() -> Image.Image:
    """Render and normalize the original Project 3 board.

    The reusable board contains:
    - no baked-in cinematic dark matte
    - no repeated center-board stripe artifact
    - all original perimeter spaces
    """

    spaces = load_board_spaces(CONFIG_PATH)

    figure = plt.figure(
        figsize=(
            14,
            14,
        ),
        dpi=150,
        facecolor=(
            0.035,
            0.055,
            0.08,
        ),
    )

    axis = figure.add_axes(
        (
            0,
            0,
            1,
            1,
        )
    )

    axis.set_xlim(
        0,
        1,
    )

    axis.set_ylim(
        0,
        1,
    )

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
        dpi=150,
        bbox_inches=None,
        pad_inches=0,
    )

    plt.close(figure)

    buffer.seek(0)

    with Image.open(buffer) as image:
        raw = image.convert("RGBA")

    # -------------------------------------------------------------
    # Detect the light board bounds without Image.load().
    # Pillow's PixelAccess typing is intentionally avoided because
    # it is wider than the guaranteed RGB tuple needed here.
    # -------------------------------------------------------------

    rgb = raw.convert("RGB")

    width, height = rgb.size

    light_points: list[tuple[int, int]] = []

    for y in range(
        0,
        height,
        4,
    ):
        for x in range(
            0,
            width,
            4,
        ):
            pixel = rgb.getpixel(
                (
                    x,
                    y,
                )
            )

            if not isinstance(
                pixel,
                tuple,
            ):
                raise RuntimeError("Expected RGB tuple while detecting board bounds.")

            if len(pixel) < 3:
                raise RuntimeError("RGB pixel contains fewer than three channels.")

            red = float(pixel[0])

            green = float(pixel[1])

            blue = float(pixel[2])

            brightness = (red + green + blue) / 3.0

            if brightness > 80.0:
                light_points.append(
                    (
                        x,
                        y,
                    )
                )

    if not light_points:
        raise RuntimeError("Could not detect canonical board bounds.")

    minimum_x = min(point[0] for point in light_points)

    maximum_x = max(point[0] for point in light_points)

    minimum_y = min(point[1] for point in light_points)

    maximum_y = max(point[1] for point in light_points)

    padding_x = round(width * 0.012)

    padding_y = round(height * 0.012)

    minimum_x = max(
        0,
        minimum_x - padding_x,
    )

    maximum_x = min(
        width,
        maximum_x + padding_x,
    )

    minimum_y = max(
        0,
        minimum_y - padding_y,
    )

    maximum_y = min(
        height,
        maximum_y + padding_y,
    )

    board = raw.crop(
        (
            minimum_x,
            minimum_y,
            maximum_x,
            maximum_y,
        )
    )

    # -------------------------------------------------------------
    # Flatten only the intentionally empty board center.
    # -------------------------------------------------------------

    board_width, board_height = board.size

    center_left = round(board_width * 0.145)

    center_top = round(board_height * 0.145)

    center_right = round(board_width * 0.855)

    center_bottom = round(board_height * 0.855)

    sample_points = (
        (
            0.45,
            0.45,
        ),
        (
            0.50,
            0.45,
        ),
        (
            0.55,
            0.45,
        ),
        (
            0.45,
            0.50,
        ),
        (
            0.50,
            0.50,
        ),
        (
            0.55,
            0.50,
        ),
        (
            0.45,
            0.55,
        ),
        (
            0.50,
            0.55,
        ),
        (
            0.55,
            0.55,
        ),
    )

    colors: list[
        tuple[
            int,
            int,
            int,
            int,
        ]
    ] = []

    for (
        x_fraction,
        y_fraction,
    ) in sample_points:
        pixel = board.getpixel(
            (
                round(board_width * x_fraction),
                round(board_height * y_fraction),
            )
        )

        if (
            not isinstance(
                pixel,
                tuple,
            )
            or len(pixel) < 4
        ):
            raise RuntimeError("Expected RGBA tuple while sampling board center.")

        colors.append(
            (
                int(pixel[0]),
                int(pixel[1]),
                int(pixel[2]),
                int(pixel[3]),
            )
        )

    red_values = sorted(color[0] for color in colors)

    green_values = sorted(color[1] for color in colors)

    blue_values = sorted(color[2] for color in colors)

    alpha_values = sorted(color[3] for color in colors)

    middle = len(colors) // 2

    center_color = (
        red_values[middle],
        green_values[middle],
        blue_values[middle],
        alpha_values[middle],
    )

    draw = ImageDraw.Draw(board)

    draw.rectangle(
        (
            center_left,
            center_top,
            center_right,
            center_bottom,
        ),
        fill=center_color,
    )

    # -------------------------------------------------------------
    # Normalize onto a transparent square. Cinematic backgrounds
    # belong to individual scenes, not the reusable board asset.
    # -------------------------------------------------------------

    normalized_size = max(
        board_width,
        board_height,
    )

    normalized = Image.new(
        "RGBA",
        (
            normalized_size,
            normalized_size,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    normalized.alpha_composite(
        board,
        (
            (normalized_size - board_width) // 2,
            (normalized_size - board_height) // 2,
        ),
    )

    return normalized


@lru_cache(maxsize=1)
def canonical_board_content_box() -> tuple[
    float,
    float,
    float,
    float,
]:
    """Return the actual visible-board rectangle in normalized coordinates."""

    image = board_image()

    alpha = image.getchannel("A")

    box = alpha.getbbox()

    if box is None:
        raise RuntimeError("Canonical board has no visible alpha bounds.")

    left, top, right, bottom = box

    width, height = image.size

    if right <= left or bottom <= top:
        raise RuntimeError(f"Invalid canonical board alpha bounds: {box}")

    return (
        left / width,
        top / height,
        right / width,
        bottom / height,
    )


def canonical_board_normalized_point(
    index: int,
) -> tuple[
    float,
    float,
]:
    """Return the visual center of one canonical playable board space.

    The 40-space perimeter is derived geometrically from the normalized
    board bounds rather than inheriting legacy plotting coordinates.
    """

    board_index = index % 40

    (
        content_left,
        content_top,
        content_right,
        content_bottom,
    ) = canonical_board_content_box()

    content_width = content_right - content_left

    content_height = content_bottom - content_top

    # Corner tiles are slightly larger than ordinary edge spaces.
    # These inset values place pieces near the visual center of the
    # actual corner tiles.
    corner_x = content_width * 0.050

    corner_y = content_height * 0.050

    left_x = content_left + corner_x

    right_x = content_right - corner_x

    top_y = content_top + corner_y

    bottom_y = content_bottom - corner_y

    if board_index == 0:
        return (
            left_x,
            bottom_y,
        )

    if board_index == 10:
        return (
            right_x,
            bottom_y,
        )

    if board_index == 20:
        return (
            right_x,
            top_y,
        )

    if board_index == 30:
        return (
            left_x,
            top_y,
        )

    # Ordinary spaces occupy the span between the two corner centers.
    # Nine spaces divide that span into ten equal center-to-center
    # intervals.
    horizontal_step = (right_x - left_x) / 10.0

    vertical_step = (bottom_y - top_y) / 10.0

    if 1 <= board_index <= 9:
        return (
            left_x + horizontal_step * board_index,
            bottom_y,
        )

    if 11 <= board_index <= 19:
        offset = board_index - 10

        return (
            right_x,
            bottom_y - vertical_step * offset,
        )

    if 21 <= board_index <= 29:
        offset = board_index - 20

        return (
            right_x - horizontal_step * offset,
            top_y,
        )

    if 31 <= board_index <= 39:
        offset = board_index - 30

        return (
            left_x,
            top_y + vertical_step * offset,
        )

    raise RuntimeError(f"Unsupported board index: {board_index}")


def canonical_board_pixel_point(
    index: int,
    *,
    width: int,
    height: int,
) -> tuple[
    float,
    float,
]:
    normalized_x, normalized_y = canonical_board_normalized_point(index)

    return (
        normalized_x * width,
        normalized_y * height,
    )


def board_point(
    index: int,
    *,
    left: float,
    top: float,
    size: float,
) -> tuple[
    float,
    float,
]:
    """Map board-space index into a rendered square board stage."""

    normalized_x, normalized_y = canonical_board_normalized_point(index)

    return (
        left + normalized_x * size,
        top + normalized_y * size,
    )


@lru_cache(maxsize=128)
def piece_asset(
    strategy: str,
    size: int,
) -> Image.Image:
    path = PIECE_DIRECTORY / (PIECE_NAMES[strategy] + ".png")

    with Image.open(path) as image:
        return image.convert("RGBA").resize(
            (
                s(size),
                s(size),
            ),
            Image.Resampling.LANCZOS,
        )


def grounded_piece(
    canvas: Image.Image,
    *,
    strategy: str,
    x: float,
    y: float,
    size: int,
    shadow_scale: float = 1.0,
) -> None:
    shadow = Image.new(
        "RGBA",
        (
            s(size * 1.5),
            s(size * 0.7),
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
            s(size * 0.18),
            s(size * 0.30),
            s(size * 1.32),
            s(size * 0.58),
        ),
        fill=(
            0,
            0,
            0,
            round(130 * shadow_scale),
        ),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(s(6)))

    paste_center(
        canvas,
        shadow,
        x=x,
        y=y + size * 0.36,
    )

    paste_center(
        canvas,
        piece_asset(
            strategy,
            size,
        ),
        x=x,
        y=y,
    )


PIPS = {
    1: (
        (
            0.50,
            0.50,
        ),
    ),
    2: (
        (
            0.28,
            0.28,
        ),
        (
            0.72,
            0.72,
        ),
    ),
    3: (
        (
            0.28,
            0.28,
        ),
        (
            0.50,
            0.50,
        ),
        (
            0.72,
            0.72,
        ),
    ),
    4: (
        (
            0.28,
            0.28,
        ),
        (
            0.72,
            0.28,
        ),
        (
            0.28,
            0.72,
        ),
        (
            0.72,
            0.72,
        ),
    ),
    5: (
        (
            0.28,
            0.28,
        ),
        (
            0.72,
            0.28,
        ),
        (
            0.50,
            0.50,
        ),
        (
            0.28,
            0.72,
        ),
        (
            0.72,
            0.72,
        ),
    ),
    6: (
        (
            0.28,
            0.23,
        ),
        (
            0.72,
            0.23,
        ),
        (
            0.28,
            0.50,
        ),
        (
            0.72,
            0.50,
        ),
        (
            0.28,
            0.77,
        ),
        (
            0.72,
            0.77,
        ),
    ),
}


def die_asset(
    value: int,
    *,
    size: int,
    rotation: float,
) -> Image.Image:
    pixels = s(size)

    image = Image.new(
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

    draw = ImageDraw.Draw(image)

    margin = s(7)

    draw.rounded_rectangle(
        (
            margin,
            margin,
            pixels - margin,
            pixels - margin,
        ),
        radius=s(18),
        fill=(
            244,
            240,
            229,
            255,
        ),
        outline=(
            153,
            148,
            138,
            255,
        ),
        width=s(3),
    )

    draw.line(
        (
            s(size * 0.14),
            s(size * 0.84),
            s(size * 0.86),
            s(size * 0.84),
        ),
        fill=(
            118,
            114,
            107,
            220,
        ),
        width=s(4),
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
                22,
                24,
                27,
                255,
            ),
        )

    return image.rotate(
        rotation,
        resample=Image.Resampling.BICUBIC,
        expand=True,
    )


def physical_card(
    *,
    header: str,
    headline: str,
    body: str,
    accent: tuple[int, int, int],
    width: int = 390,
    height: int = 270,
) -> Image.Image:
    image = Image.new(
        "RGBA",
        (
            s(width),
            s(height),
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
        image.size,
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
            s(16),
            s(17),
            s(width - 8),
            s(height - 7),
        ),
        radius=s(14),
        fill=(
            0,
            0,
            0,
            130,
        ),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(s(9)))

    image.alpha_composite(shadow)

    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (
            s(5),
            s(5),
            s(width - 18),
            s(height - 20),
        ),
        radius=s(12),
        fill=(
            *CREAM,
            255,
        ),
        outline=(
            87,
            81,
            71,
            255,
        ),
        width=s(2),
    )

    draw.rounded_rectangle(
        (
            s(18),
            s(18),
            s(width - 31),
            s(72),
        ),
        radius=s(6),
        fill=(
            *accent,
            255,
        ),
    )

    def local_center(
        text: str,
        *,
        y: int,
        size: int,
        fill: tuple[int, int, int],
    ) -> None:
        active_font = font(
            size,
            bold=True,
        )

        box = draw.textbbox(
            (
                0,
                0,
            ),
            text,
            font=active_font,
        )

        text_width = box[2] - box[0]

        draw.text(
            (
                (s(width) - text_width) / 2,
                s(y),
            ),
            text,
            font=active_font,
            fill=fill,
        )

    local_center(
        header,
        y=34,
        size=16,
        fill=WHITE,
    )

    local_center(
        headline,
        y=105,
        size=28,
        fill=INK,
    )

    local_center(
        body,
        y=173,
        size=17,
        fill=(
            66,
            68,
            69,
        ),
    )

    return image


def render_board_stage(
    *,
    state: GameState,
    active: str | None = None,
    board_left: float = 65,
    board_top: float = 85,
    board_size: float = 950,
    blur: float = 0.0,
    dim: float = 0.0,
) -> Image.Image:
    canvas = rgba_canvas()

    board = board_image().resize(
        (
            s(board_size),
            s(board_size),
        ),
        Image.Resampling.LANCZOS,
    )

    if blur > 0:
        board = board.filter(ImageFilter.GaussianBlur(s(blur)))

    canvas.alpha_composite(
        board,
        (
            s(board_left),
            s(board_top),
        ),
    )

    if dim > 0:
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
                round(255 * dim),
            ),
        )

        canvas.alpha_composite(overlay)

    offsets = {
        "collector": (
            -12,
            -10,
        ),
        "specialist": (
            12,
            -10,
        ),
        "cash_protector": (
            -12,
            11,
        ),
        "aggressive_builder": (
            12,
            11,
        ),
    }

    for strategy in STRATEGY_ORDER:
        if strategy in state.bankrupt:
            continue

        position = state.positions[strategy]

        x, y = board_point(
            position,
            left=board_left,
            top=board_top,
            size=board_size,
        )

        offset_x, offset_y = offsets[strategy]

        grounded_piece(
            canvas,
            strategy=strategy,
            x=x + offset_x,
            y=y + offset_y,
            size=(78 if strategy == active else 58),
        )

    return canvas


def draw_title_band(
    canvas: Image.Image,
    *,
    kicker: str,
    headline: str,
    subline: str = "",
    accent: tuple[int, int, int] = GOLD,
) -> None:
    draw = ImageDraw.Draw(canvas)

    draw.rectangle(
        (
            0,
            0,
            RW,
            s(118),
        ),
        fill=(
            2,
            7,
            14,
            236,
        ),
    )

    left_text(
        draw,
        kicker,
        x=38,
        y=24,
        size=15,
        fill=accent,
    )

    left_text(
        draw,
        headline,
        x=38,
        y=50,
        size=34,
        fill=WHITE,
    )

    if subline:
        left_text(
            draw,
            subline,
            x=40,
            y=93,
            size=13,
            fill=MUTED,
            bold=False,
        )


PURCHASE_ACTIONS = frozenset(
    {
        "PURCHASE",
        "BUY",
        "BUY_PROPERTY",
        "PROPERTY_PURCHASE",
        "ACQUIRE",
        "ACQUIRE_PROPERTY",
    }
)

BUILD_ACTIONS = frozenset(
    {
        "BUILD",
        "BUILD_HOUSE",
        "HOUSE_BUILD",
        "DEVELOP",
        "DEVELOP_PROPERTY",
    }
)

RENT_ACTIONS = frozenset(
    {
        "RENT",
        "PAY_RENT",
        "RENT_PAYMENT",
        "COLLECT_RENT",
    }
)

GROUP_ACTIONS = frozenset(
    {
        "GROUP_COMPLETE",
        "COMPLETE_GROUP",
        "COLOR_GROUP_COMPLETE",
        "MONOPOLY_COMPLETE",
    }
)

BANKRUPTCY_ACTIONS = frozenset(
    {
        "BANKRUPTCY",
        "BANKRUPT",
        "PLAYER_BANKRUPT",
    }
)


def semantic_raw_value(
    event: object,
    key: str,
) -> object | None:
    """Read one field from a raw replay event."""

    raw = getattr(
        event,
        "raw",
        None,
    )

    if not isinstance(
        raw,
        dict,
    ):
        return None

    return raw.get(key)


def semantic_event_type(
    event: object,
) -> str:
    value = semantic_raw_value(
        event,
        "event_type",
    )

    if not isinstance(
        value,
        str,
    ):
        return ""

    return (
        value.strip()
        .upper()
        .replace(
            "-",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )


def turn_events_of_type(
    turn: TurnBeat,
    event_type: str,
) -> tuple[
    object,
    ...,
]:
    expected = event_type.upper()

    return tuple(event for event in turn.events if semantic_event_type(event) == expected)


@lru_cache(maxsize=1)
def replay_asset_index_map() -> dict[
    str,
    int,
]:
    """Derive canonical asset locations from ASSET_PURCHASED only.

    Purchase events identify both an asset_id and the actual purchased
    landing square. RENT_DUE positions are intentionally excluded
    because event-driven movement can make turn.to_position differ from
    the canonical property square.
    """

    _, turns, _ = load_replay()

    observations: dict[
        str,
        set[int],
    ] = {}

    for turn in turns:
        for event in turn.events:
            if semantic_event_type(event) != "ASSET_PURCHASED":
                continue

            asset_id = semantic_raw_value(
                event,
                "asset_id",
            )

            if not isinstance(
                asset_id,
                str,
            ):
                raise RuntimeError("ASSET_PURCHASED event lacks string asset_id.")

            positions = observations.setdefault(
                asset_id,
                set(),
            )

            positions.add(turn.to_position % 40)

    if not observations:
        raise RuntimeError("No ASSET_PURCHASED evidence exists for asset-to-board mapping.")

    conflicts = {
        asset_id: positions for asset_id, positions in observations.items() if len(positions) != 1
    }

    if conflicts:
        raise RuntimeError(f"Conflicting purchase-derived asset mappings: {conflicts}")

    return {asset_id: next(iter(positions)) for asset_id, positions in observations.items()}


def semantic_event_asset_id(
    event: object,
) -> str:
    value = semantic_raw_value(
        event,
        "asset_id",
    )

    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise RuntimeError(
            f"{semantic_event_type(event)} event does not contain a usable asset_id."
        )

    return value.strip()


def semantic_event_space_index(
    turn: TurnBeat,
    event: object,
) -> int:
    """Resolve an event's actual canonical board-space index."""

    del turn

    asset_id = semantic_event_asset_id(event)

    mapping = replay_asset_index_map()

    if asset_id not in mapping:
        raise RuntimeError(f"No purchase-derived canonical mapping for asset_id={asset_id!r}.")

    return mapping[asset_id]


def semantic_event_property_name(
    turn: TurnBeat,
    event: object,
) -> str:
    index = semantic_event_space_index(
        turn,
        event,
    )

    return board_space_names()[index]


def actual_purchase_events(
    turn: TurnBeat,
) -> tuple[
    object,
    ...,
]:
    return turn_events_of_type(
        turn,
        "ASSET_PURCHASED",
    )


def actual_build_events(
    turn: TurnBeat,
) -> tuple[
    object,
    ...,
]:
    """Return only genuine HOUSE_BUILT events."""

    events = []

    for event in turn_events_of_type(
        turn,
        "HOUSE_BUILT",
    ):
        amount = getattr(
            event,
            "amount",
            None,
        )

        if not isinstance(
            amount,
            (int, float),
        ):
            continue

        if amount <= 0:
            continue

        events.append(event)

    return tuple(events)


def actual_rent_events(
    turn: TurnBeat,
) -> tuple[
    object,
    ...,
]:
    return turn_events_of_type(
        turn,
        "RENT_DUE",
    )


def actual_bankruptcy_events(
    turn: TurnBeat,
) -> tuple[
    object,
    ...,
]:
    return turn_events_of_type(
        turn,
        "BANKRUPTCY",
    )


def normalized_action(
    turn: TurnBeat,
) -> str:
    return (
        str(turn.primary_action)
        .strip()
        .upper()
        .replace(
            "-",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )


@lru_cache(maxsize=1)
@lru_cache(maxsize=1)
def board_space_names() -> tuple[
    str,
    ...,
]:
    """Return the canonical display names of all 40 typed board spaces."""

    spaces = load_board_spaces(CONFIG_PATH)

    names: list[str] = []

    for index, space in enumerate(spaces):
        candidate = getattr(
            space,
            "name",
            None,
        )

        if (
            isinstance(
                candidate,
                str,
            )
            and candidate.strip()
        ):
            names.append(candidate.strip())

            continue

        candidate = getattr(
            space,
            "label",
            None,
        )

        if (
            isinstance(
                candidate,
                str,
            )
            and candidate.strip()
        ):
            names.append(candidate.strip())

            continue

        candidate = getattr(
            space,
            "display_name",
            None,
        )

        if (
            isinstance(
                candidate,
                str,
            )
            and candidate.strip()
        ):
            names.append(candidate.strip())

            continue

        raise RuntimeError(
            "Canonical board space has no resolvable display name: "
            f"index={index}, type={type(space).__name__}"
        )

    if len(names) != 40:
        raise RuntimeError(f"Expected exactly 40 canonical board-space names; found {len(names)}")

    return tuple(names)


def resolved_property_label(
    turn: TurnBeat,
) -> str:
    explicit = (turn.property_name or "").strip()

    if explicit and explicit.upper() != "BOARD PROPERTY":
        return explicit

    index = turn_space_index(turn)

    return board_space_names()[index]


def purchase_event(
    turn: TurnBeat,
) -> object:
    events = actual_purchase_events(turn)

    if not events:
        raise RuntimeError("Selected purchase turn contains no ASSET_PURCHASED event.")

    return events[0]


def build_event(
    turn: TurnBeat,
) -> object:
    events = actual_build_events(turn)

    if not events:
        raise RuntimeError("Selected build turn contains no HOUSE_BUILT event.")

    # If multiple properties are developed in one turn, use the first
    # actual paid build deterministically for the canonical close-up.
    return events[0]


def rent_event(
    turn: TurnBeat,
) -> object:
    events = actual_rent_events(turn)

    if not events:
        raise RuntimeError("Selected rent turn contains no RENT_DUE event.")

    return events[0]


def purchase_space_index(
    turn: TurnBeat,
) -> int:
    return semantic_event_space_index(
        turn,
        purchase_event(turn),
    )


def build_space_index(
    turn: TurnBeat,
) -> int:
    return semantic_event_space_index(
        turn,
        build_event(turn),
    )


def rent_space_index(
    turn: TurnBeat,
) -> int:
    return semantic_event_space_index(
        turn,
        rent_event(turn),
    )


def purchase_property_name(
    turn: TurnBeat,
) -> str:
    return semantic_event_property_name(
        turn,
        purchase_event(turn),
    )


def build_property_name(
    turn: TurnBeat,
) -> str:
    return semantic_event_property_name(
        turn,
        build_event(turn),
    )


def rent_property_name(
    turn: TurnBeat,
) -> str:
    return semantic_event_property_name(
        turn,
        rent_event(turn),
    )


def property_label(
    turn: TurnBeat,
) -> str:
    """Return a real board-space name; never fabricate BOARD PROPERTY."""

    return resolved_property_label(turn)


def turn_position(
    turns: tuple[
        TurnBeat,
        ...,
    ],
    target: TurnBeat,
) -> int:
    for index, turn in enumerate(turns):
        if turn is target:
            return index

    raise RuntimeError("Selected story turn is not present in the representative-game replay.")


def exact_action_turn(
    turns: tuple[
        TurnBeat,
        ...,
    ],
    actions: frozenset[str],
    *,
    start_index: int = 0,
    end_index: int | None = None,
    require_property: bool = False,
) -> TurnBeat | None:
    stop = len(turns) if end_index is None else end_index

    for turn in turns[start_index:stop]:
        if normalized_action(turn) not in actions:
            continue

        if require_property:
            label = resolved_property_label(turn)

            if not label or label.upper().startswith("SPACE "):
                continue

        return turn

    return None


def largest_cash_loss_turn(
    turns: tuple[
        TurnBeat,
        ...,
    ],
    *,
    start_index: int,
    excluded: tuple[
        TurnBeat,
        ...,
    ] = (),
) -> TurnBeat:
    excluded_ids = {id(turn) for turn in excluded}

    candidates: list[
        tuple[
            float,
            int,
            TurnBeat,
        ]
    ] = []

    for index in range(
        start_index,
        len(turns),
    ):
        turn = turns[index]

        if id(turn) in excluded_ids:
            continue

        strategy = turn.strategy_id

        before = turn.state_before.cash[strategy]

        after = turn.state_after.cash[strategy]

        loss = before - after

        if loss <= 0:
            continue

        candidates.append(
            (
                float(loss),
                -index,
                turn,
            )
        )

    if not candidates:
        raise RuntimeError(
            "Representative game contains no real cash-loss turn after the rent sequence."
        )

    return max(
        candidates,
        key=lambda item: (
            item[0],
            item[1],
        ),
    )[2]


def first_movement_turn(
    turns: tuple[
        TurnBeat,
        ...,
    ],
) -> TurnBeat:
    for turn in turns:
        if turn.from_position != turn.to_position:
            return turn

    raise RuntimeError("Representative game contains no movement turn.")


def first_dice_turn(
    turns: tuple[
        TurnBeat,
        ...,
    ],
) -> TurnBeat:
    for turn in turns:
        if turn.dice is not None:
            return turn

    raise RuntimeError("Representative game contains no dice turn.")


def strategy_preview_turns(
    turns: tuple[
        TurnBeat,
        ...,
    ],
) -> tuple[
    TurnBeat,
    ...,
]:
    selected: list[TurnBeat] = []

    for strategy in STRATEGY_ORDER:
        match = next(
            (turn for turn in turns if turn.strategy_id == strategy),
            None,
        )

        if match is None:
            raise RuntimeError(f"Representative game contains no turn for strategy {strategy}.")

        selected.append(match)

    return tuple(selected)


def build_truthful_story_plan(
    turns: tuple[
        TurnBeat,
        ...,
    ],
) -> PreviewStoryPlan:
    """Select six chronological cinematic beats from real SemanticEvents."""

    purchase_candidates = [
        (
            index,
            turn,
        )
        for index, turn in enumerate(turns)
        if actual_purchase_events(turn)
    ]

    build_candidates = [
        (
            index,
            turn,
        )
        for index, turn in enumerate(turns)
        if actual_build_events(turn)
    ]

    rent_candidates = [
        (
            index,
            turn,
        )
        for index, turn in enumerate(turns)
        if actual_rent_events(turn)
    ]

    bankruptcy_candidates = [
        (
            index,
            turn,
        )
        for index, turn in enumerate(turns)
        if actual_bankruptcy_events(turn)
    ]

    if not purchase_candidates:
        raise RuntimeError("Representative game contains no ASSET_PURCHASED event.")

    if not build_candidates:
        raise RuntimeError("Representative game contains no HOUSE_BUILT event.")

    if not rent_candidates:
        raise RuntimeError("Representative game contains no RENT_DUE event.")

    if not bankruptcy_candidates:
        raise RuntimeError("Representative game contains no BANKRUPTCY event.")

    # Work backwards from the first bankruptcy for which a complete
    # real chronological story can be established.
    selected: (
        tuple[
            TurnBeat,
            TurnBeat,
            TurnBeat,
            TurnBeat,
            TurnBeat,
            TurnBeat,
        ]
        | None
    ) = None

    for bankruptcy_index, bankruptcy_turn in bankruptcy_candidates:
        rents_before = [
            (
                index,
                turn,
            )
            for index, turn in rent_candidates
            if index < bankruptcy_index
        ]

        if not rents_before:
            continue

        # Prefer the latest meaningful rent before bankruptcy.
        for rent_index, rent_turn in reversed(rents_before):
            builds_before = [
                (
                    index,
                    turn,
                )
                for index, turn in build_candidates
                if index < rent_index
            ]

            if not builds_before:
                continue

            for build_index, build_turn in reversed(builds_before):
                purchases_before = [
                    (
                        index,
                        turn,
                    )
                    for index, turn in purchase_candidates
                    if index < build_index
                ]

                if len(purchases_before) < 2:
                    continue

                purchase_index, purchase_turn = purchases_before[-2]

                progress_index, progress_turn = purchases_before[-1]

                # Pick the largest real active-player loss after rent
                # but before bankruptcy as the cash-shock beat.
                shock_candidates: list[
                    tuple[
                        float,
                        int,
                        TurnBeat,
                    ]
                ] = []

                for index in range(
                    rent_index + 1,
                    bankruptcy_index,
                ):
                    turn = turns[index]

                    strategy = turn.strategy_id

                    before = turn.state_before.cash[strategy]

                    after = turn.state_after.cash[strategy]

                    loss = before - after

                    if loss <= 0:
                        continue

                    shock_candidates.append(
                        (
                            float(loss),
                            index,
                            turn,
                        )
                    )

                if not shock_candidates:
                    continue

                _, shock_index, shock_turn = max(
                    shock_candidates,
                    key=lambda item: (
                        item[0],
                        -item[1],
                    ),
                )

                if not (
                    purchase_index
                    < progress_index
                    < build_index
                    < rent_index
                    < shock_index
                    < bankruptcy_index
                ):
                    continue

                selected = (
                    purchase_turn,
                    progress_turn,
                    build_turn,
                    rent_turn,
                    shock_turn,
                    bankruptcy_turn,
                )

                break

            if selected is not None:
                break

        if selected is not None:
            break

    if selected is None:
        raise RuntimeError(
            "Representative game contains semantic events, "
            "but no complete chronological "
            "purchase -> progress -> build -> rent -> "
            "cash shock -> bankruptcy sequence."
        )

    (
        purchase,
        progress,
        build,
        rent,
        shock,
        bankruptcy,
    ) = selected

    return PreviewStoryPlan(
        dice_turn=first_dice_turn(turns),
        move_turn=first_movement_turn(turns),
        purchase_turn=purchase,
        build_turn=build,
        rent_turn=rent,
        shock_turn=shock,
        survival_turn=bankruptcy,
        strategy_turns=strategy_preview_turns(turns),
        narrative_beats=(
            StoryBeat(
                label="ACQUIRE",
                turn=purchase,
            ),
            StoryBeat(
                label="EXPAND",
                turn=progress,
            ),
            StoryBeat(
                label="BUILD",
                turn=build,
            ),
            StoryBeat(
                label="RENT",
                turn=rent,
            ),
            StoryBeat(
                label="CASH SHOCK",
                turn=shock,
            ),
            StoryBeat(
                label="BANKRUPTCY",
                turn=bankruptcy,
            ),
        ),
    )


def load_runtime() -> PreviewRuntime:
    _, turns, _ = load_replay()

    context = load_preview_context(validation_directory=(VALIDATION_DIRECTORY))

    metrics = tuple(
        StrategyMetric(
            strategy_id=metric.strategy_id,
            win_rate=metric.win_rate,
            bankruptcy_rate=(metric.bankruptcy_rate),
            median_finishing_cash=(metric.median_finishing_cash),
            ci_lower=metric.ci_lower,
            ci_upper=metric.ci_upper,
        )
        for metric in context.strategies
    )

    if len(metrics) != 4:
        raise RuntimeError("Expected four validated strategy metrics.")

    winner = getattr(
        context,
        "headline_winner",
        None,
    )

    story = build_truthful_story_plan(turns)

    runtime = PreviewRuntime(
        turns=turns,
        story=story,
        metrics=metrics,
        headline_winner=(str(winner) if winner is not None else None),
    )

    validate_preview_semantics(runtime)

    return runtime


def validate_preview_semantics(
    runtime: PreviewRuntime,
) -> None:
    """Fail closed unless every cinematic beat is supported by replay truth."""

    purchase = runtime.story.purchase_turn
    build = runtime.story.build_turn
    rent = runtime.story.rent_turn
    bankruptcy = runtime.story.survival_turn

    if not actual_purchase_events(purchase):
        raise RuntimeError("Purchase preview lacks ASSET_PURCHASED.")

    if not actual_build_events(build):
        raise RuntimeError("Build preview lacks HOUSE_BUILT.")

    if not actual_rent_events(rent):
        raise RuntimeError("Rent preview lacks RENT_DUE.")

    if not actual_bankruptcy_events(bankruptcy):
        raise RuntimeError("Final story beat lacks BANKRUPTCY.")

    # All selected assets must resolve to canonical board coordinates.
    for label, index, name in (
        (
            "purchase",
            purchase_space_index(purchase),
            purchase_property_name(purchase),
        ),
        (
            "build",
            build_space_index(build),
            build_property_name(build),
        ),
        (
            "rent",
            rent_space_index(rent),
            rent_property_name(rent),
        ),
    ):
        if not (0 <= index < 40):
            raise RuntimeError(f"V5 {label} space index invalid: {index}")

        if not name.strip():
            raise RuntimeError(f"V5 {label} property name is empty.")

    beats = runtime.story.narrative_beats

    if tuple(beat.label for beat in beats) != (
        "ACQUIRE",
        "EXPAND",
        "BUILD",
        "RENT",
        "CASH SHOCK",
        "BANKRUPTCY",
    ):
        raise RuntimeError("V5 narrative labels do not match frozen semantic sequence.")

    indexes = [
        turn_position(
            runtime.turns,
            beat.turn,
        )
        for beat in beats
    ]

    if indexes != sorted(indexes):
        raise RuntimeError(f"V5 narrative is not chronological: {indexes}")

    if len(set(indexes)) != 6:
        raise RuntimeError(f"V5 narrative reuses turns: {indexes}")

    shock = runtime.story.shock_turn

    strategy = shock.strategy_id

    if shock.state_after.cash[strategy] >= shock.state_before.cash[strategy]:
        raise RuntimeError("CASH SHOCK does not contain a real cash decline.")

    if runtime.story.dice_turn.dice is None:
        raise RuntimeError("Dice shot lacks a real dice roll.")

    if runtime.story.move_turn.from_position == runtime.story.move_turn.to_position:
        raise RuntimeError("Movement shot contains no real movement.")


def ranking(
    runtime: PreviewRuntime,
) -> tuple[
    StrategyMetric,
    ...,
]:
    return tuple(
        sorted(
            runtime.metrics,
            key=lambda metric: (
                -metric.win_rate,
                metric.strategy_id,
            ),
        )
    )


def cash_delta(
    turn: TurnBeat,
) -> float:
    strategy = turn.strategy_id

    return turn.state_after.cash[strategy] - turn.state_before.cash[strategy]


# =====================================================================
# 01 — DICE HIT
# =====================================================================


def turn_space_index(
    turn: TurnBeat,
) -> int:
    """Resolve the most relevant real board-space index for a turn."""

    for event in reversed(turn.events):
        if event.space_index is not None:
            return event.space_index % 40

        if event.to_position is not None:
            return event.to_position % 40

    return turn.to_position % 40


def board_zoom_crop_box(
    *,
    focus_space: int,
    zoom: float,
    vertical_bias: float,
) -> tuple[
    float,
    float,
    float,
    float,
]:
    """Return the source-pixel crop used for a board close-up."""

    if zoom <= 1.0:
        raise ValueError("board_zoom requires zoom > 1.0")

    base = board_image()

    base_width, base_height = base.size

    focus_x, focus_y = canonical_board_pixel_point(
        focus_space,
        width=base_width,
        height=base_height,
    )

    crop_width = base_width / zoom

    crop_height = base_height / zoom

    left = max(
        0.0,
        min(
            base_width - crop_width,
            focus_x - crop_width / 2.0,
        ),
    )

    top = max(
        0.0,
        min(
            base_height - crop_height,
            focus_y - crop_height / 2.0 + vertical_bias * crop_height,
        ),
    )

    return (
        left,
        top,
        left + crop_width,
        top + crop_height,
    )


def board_zoom_project(
    *,
    focus_space: int,
    target_space: int,
    zoom: float,
    vertical_bias: float,
) -> tuple[
    float,
    float,
]:
    """Project a real board-space coordinate into final 1080 scene space."""

    base = board_image()

    base_width, base_height = base.size

    source_x, source_y = canonical_board_pixel_point(
        target_space,
        width=base_width,
        height=base_height,
    )

    (
        crop_left,
        crop_top,
        crop_right,
        crop_bottom,
    ) = board_zoom_crop_box(
        focus_space=focus_space,
        zoom=zoom,
        vertical_bias=vertical_bias,
    )

    crop_width = crop_right - crop_left

    crop_height = crop_bottom - crop_top

    projected_x = (source_x - crop_left) / crop_width * WIDTH

    projected_y = (source_y - crop_top) / crop_height * HEIGHT

    return (
        projected_x,
        projected_y,
    )


def board_zoom(
    *,
    state: GameState,
    focus_space: int,
    active: str | None,
    zoom: float = 2.15,
    vertical_bias: float = 0.0,
    dim: float = 0.0,
    blur: float = 0.0,
) -> Image.Image:
    """Create a cinematic close-up centered on an actual board space."""

    del state
    del active

    base = board_image().convert("RGBA")

    (
        crop_left,
        crop_top,
        crop_right,
        crop_bottom,
    ) = board_zoom_crop_box(
        focus_space=focus_space,
        zoom=zoom,
        vertical_bias=vertical_bias,
    )

    crop = base.crop(
        (
            round(crop_left),
            round(crop_top),
            round(crop_right),
            round(crop_bottom),
        )
    ).resize(
        (
            RW,
            RH,
        ),
        Image.Resampling.LANCZOS,
    )

    if blur > 0:
        crop = crop.filter(ImageFilter.GaussianBlur(s(blur)))

    canvas = rgba_canvas()

    canvas.alpha_composite(crop)

    if dim > 0:
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
                round(255 * dim),
            ),
        )

        canvas.alpha_composite(overlay)

    return canvas


def large_metric_pair(
    canvas: Image.Image,
    *,
    before: float,
    after: float,
    label_before: str,
    label_after: str,
    accent: tuple[int, int, int],
    y: float,
) -> None:
    draw = ImageDraw.Draw(canvas)

    rounded_panel(
        draw,
        (
            100,
            y,
            980,
            y + 200,
        ),
        radius=28,
        fill=(
            5,
            14,
            25,
        ),
    )

    centered_text(
        draw,
        f"${before:,.0f}",
        center_x=300,
        y=y + 43,
        size=TYPE_DISPLAY,
        fill=WHITE,
    )

    centered_text(
        draw,
        "→",
        center_x=540,
        y=y + 48,
        size=TYPE_DISPLAY,
        fill=accent,
    )

    centered_text(
        draw,
        f"${after:,.0f}",
        center_x=780,
        y=y + 43,
        size=TYPE_DISPLAY,
        fill=accent,
    )

    centered_text(
        draw,
        label_before,
        center_x=300,
        y=y + 130,
        size=TYPE_SMALL,
        fill=MUTED,
    )

    centered_text(
        draw,
        label_after,
        center_x=780,
        y=y + 130,
        size=TYPE_SMALL,
        fill=MUTED,
    )


def hero_header(
    canvas: Image.Image,
    *,
    kicker: str,
    headline: str,
    subline: str = "",
    accent: tuple[int, int, int] = GOLD,
) -> None:
    draw = ImageDraw.Draw(canvas)

    draw.rectangle(
        (
            0,
            0,
            RW,
            s(145),
        ),
        fill=(
            2,
            7,
            14,
            242,
        ),
    )

    left_text(
        draw,
        kicker,
        x=42,
        y=22,
        size=TYPE_SMALL,
        fill=accent,
    )

    left_text(
        draw,
        headline,
        x=42,
        y=52,
        size=TYPE_SECTION,
        fill=WHITE,
    )

    if subline:
        left_text(
            draw,
            subline,
            x=44,
            y=105,
            size=TYPE_SMALL,
            fill=MUTED,
            bold=False,
        )


def render_01_dice_hit(
    runtime: PreviewRuntime,
) -> Image.Image:
    turn = runtime.story.dice_turn

    canvas = render_board_stage(
        state=turn.state_before,
        active=None,
        board_left=-120,
        board_top=150,
        board_size=1320,
        blur=2.0,
        dim=0.30,
    )

    hero_header(
        canvas,
        kicker="0:00  •  COLD OPEN",
        headline="THE DICE HIT.",
        subline="Four autonomous landlords. One board.",
        accent=GOLD,
    )

    dice = (
        turn.dice
        if turn.dice is not None
        else (
            4,
            3,
        )
    )

    die_one = die_asset(
        dice[0],
        size=300,
        rotation=-15,
    )

    die_two = die_asset(
        dice[1],
        size=300,
        rotation=12,
    )

    for x, y in (
        (
            395,
            560,
        ),
        (
            690,
            575,
        ),
    ):
        shadow = Image.new(
            "RGBA",
            (
                s(330),
                s(120),
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
                s(25),
                s(30),
                s(305),
                s(100),
            ),
            fill=(
                0,
                0,
                0,
                165,
            ),
        )

        shadow = shadow.filter(ImageFilter.GaussianBlur(s(12)))

        paste_center(
            canvas,
            shadow,
            x=x,
            y=y + 165,
        )

    paste_center(
        canvas,
        die_one,
        x=395,
        y=575,
    )

    paste_center(
        canvas,
        die_two,
        x=690,
        y=590,
    )

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "LET THE RACE BEGIN.",
        center_x=540,
        y=900,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    add_vignette(
        canvas,
        strength=95,
    )

    return downsample(canvas)


# =====================================================================
# 02 — PIECE RACE
# =====================================================================


def movement_route_indices(
    turn: TurnBeat,
) -> tuple[
    int,
    ...,
]:
    """Return the real clockwise board-space path of one movement turn."""

    start = turn.from_position % 40

    end = turn.to_position % 40

    distance = (end - start) % 40

    if distance == 0:
        raise RuntimeError("Movement route has zero board-space distance.")

    return tuple((start + offset) % 40 for offset in range(distance + 1))


def board_crop_for_spaces(
    indices: tuple[
        int,
        ...,
    ],
    *,
    minimum_fraction: float = 0.38,
    padding_fraction: float = 0.10,
) -> tuple[
    float,
    float,
    float,
    float,
]:
    """Return a square canonical-board crop containing selected spaces."""

    if not indices:
        raise ValueError("board_crop_for_spaces() requires at least one board space.")

    base = board_image()

    width, height = base.size

    points = [
        canonical_board_pixel_point(
            index,
            width=width,
            height=height,
        )
        for index in indices
    ]

    minimum_x = min(point[0] for point in points)

    maximum_x = max(point[0] for point in points)

    minimum_y = min(point[1] for point in points)

    maximum_y = max(point[1] for point in points)

    span_x = maximum_x - minimum_x

    span_y = maximum_y - minimum_y

    minimum_side = (
        min(
            width,
            height,
        )
        * minimum_fraction
    )

    content_side = max(
        span_x,
        span_y,
        minimum_side,
    )

    side = min(
        min(
            width,
            height,
        ),
        content_side * (1.0 + padding_fraction * 2.0),
    )

    center_x = (minimum_x + maximum_x) / 2.0

    center_y = (minimum_y + maximum_y) / 2.0

    left = max(
        0.0,
        min(
            width - side,
            center_x - side / 2.0,
        ),
    )

    top = max(
        0.0,
        min(
            height - side,
            center_y - side / 2.0,
        ),
    )

    return (
        left,
        top,
        left + side,
        top + side,
    )


def project_board_space_to_crop(
    index: int,
    crop_box: tuple[
        float,
        float,
        float,
        float,
    ],
) -> tuple[
    float,
    float,
]:
    """Project one canonical board space into final 1080 scene coordinates."""

    base = board_image()

    width, height = base.size

    source_x, source_y = canonical_board_pixel_point(
        index,
        width=width,
        height=height,
    )

    (
        left,
        top,
        right,
        bottom,
    ) = crop_box

    crop_width = right - left

    crop_height = bottom - top

    if crop_width <= 0 or crop_height <= 0:
        raise RuntimeError(f"Invalid board crop: {crop_box}")

    return (
        (source_x - left) / crop_width * WIDTH,
        (source_y - top) / crop_height * HEIGHT,
    )


def render_board_crop(
    crop_box: tuple[
        float,
        float,
        float,
        float,
    ],
    *,
    dim: float = 0.06,
) -> Image.Image:
    """Render one canonical-board crop onto the supersampled V5 canvas."""

    base = board_image().convert("RGBA")

    (
        left,
        top,
        right,
        bottom,
    ) = crop_box

    crop = base.crop(
        (
            round(left),
            round(top),
            round(right),
            round(bottom),
        )
    ).resize(
        (
            RW,
            RH,
        ),
        Image.Resampling.LANCZOS,
    )

    canvas = rgba_canvas()

    canvas.alpha_composite(crop)

    if dim > 0:
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
                round(255 * dim),
            ),
        )

        canvas.alpha_composite(overlay)

    return canvas


def render_02_piece_race(
    runtime: PreviewRuntime,
) -> Image.Image:
    turn = runtime.story.move_turn

    route = movement_route_indices(turn)

    crop_box = board_crop_for_spaces(
        route,
        minimum_fraction=0.42,
        padding_fraction=0.14,
    )

    canvas = render_board_crop(
        crop_box,
        dim=0.09,
    )

    hero_header(
        canvas,
        kicker="0:01  •  MOVEMENT",
        headline="THE PIECES RACE.",
        subline=(DISPLAY_NAMES[turn.strategy_id] + " follows the real representative-game path."),
        accent=ACCENTS[turn.strategy_id],
    )

    draw = ImageDraw.Draw(canvas)

    projected = [
        project_board_space_to_crop(
            index,
            crop_box,
        )
        for index in route
    ]

    if len(projected) < 2:
        raise RuntimeError("Piece Race requires at least two projected route points.")

    route_points = tuple(
        (
            s(x),
            s(y),
        )
        for x, y in projected
    )

    # Wide dark under-stroke makes the route legible over property art.
    draw.line(
        route_points,
        fill=(
            4,
            10,
            18,
        ),
        width=s(16),
        joint="curve",
    )

    draw.line(
        route_points,
        fill=ACCENTS[turn.strategy_id],
        width=s(8),
        joint="curve",
    )

    for x, y in projected[1:-1]:
        draw.ellipse(
            (
                s(x - 6),
                s(y - 6),
                s(x + 6),
                s(y + 6),
            ),
            fill=ACCENTS[turn.strategy_id],
            outline=WHITE,
            width=s(2),
        )

    start_x, start_y = projected[0]

    end_x, end_y = projected[-1]

    draw.ellipse(
        (
            s(start_x - 14),
            s(start_y - 14),
            s(start_x + 14),
            s(start_y + 14),
        ),
        fill=(
            5,
            10,
            18,
        ),
        outline=WHITE,
        width=s(4),
    )

    draw.ellipse(
        (
            s(end_x - 18),
            s(end_y - 18),
            s(end_x + 18),
            s(end_y + 18),
        ),
        fill=GOLD,
        outline=WHITE,
        width=s(3),
    )

    grounded_piece(
        canvas,
        strategy=turn.strategy_id,
        x=end_x,
        y=end_y - 48,
        size=190,
        shadow_scale=1.2,
    )

    rounded_panel(
        draw,
        (
            265,
            830,
            815,
            1000,
        ),
        radius=24,
        fill=(
            4,
            12,
            22,
        ),
        outline=ACCENTS[turn.strategy_id],
        width=2,
    )

    centered_text(
        draw,
        DISPLAY_NAMES[turn.strategy_id].upper(),
        center_x=540,
        y=850,
        size=TYPE_LABEL,
        fill=ACCENTS[turn.strategy_id],
    )

    centered_text(
        draw,
        (f"MOVES {len(route) - 1} SPACE" + ("S" if len(route) - 1 != 1 else "")),
        center_x=540,
        y=895,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    centered_text(
        draw,
        (
            board_space_names()[turn.from_position % 40]
            + "  ->  "
            + board_space_names()[turn.to_position % 40]
        ),
        center_x=540,
        y=958,
        size=TYPE_SMALL,
        fill=MUTED,
        bold=False,
    )

    return downsample(canvas)


# =====================================================================
# 03 — PROPERTY PURCHASE
# =====================================================================


def render_03_property_purchase(
    runtime: PreviewRuntime,
) -> Image.Image:
    turn = runtime.story.purchase_turn

    event = purchase_event(turn)

    strategy = turn.strategy_id

    space = purchase_space_index(turn)

    property_name = purchase_property_name(turn)

    amount_value = getattr(
        event,
        "amount",
        None,
    )

    amount = (
        float(amount_value)
        if isinstance(
            amount_value,
            (int, float),
        )
        else 0.0
    )

    canvas = board_zoom(
        state=turn.state_after,
        focus_space=space,
        active=strategy,
        zoom=1.75,
        vertical_bias=-0.05,
        dim=0.10,
    )

    hero_header(
        canvas,
        kicker="0:02  •  ACQUISITION",
        headline="PROPERTY CHANGES HANDS.",
        subline=(property_name + " becomes part of the persistent game state."),
        accent=ACCENTS[strategy],
    )

    grounded_piece(
        canvas,
        strategy=strategy,
        x=285,
        y=650,
        size=195,
        shadow_scale=1.2,
    )

    card = physical_card(
        header=property_name.upper(),
        headline="ACQUIRED",
        body=(DISPLAY_NAMES[strategy] + (f"  •  ${amount:,.0f}" if amount > 0 else "")),
        accent=ACCENTS[strategy],
        width=470,
        height=310,
    )

    paste_center(
        canvas,
        card,
        x=765,
        y=600,
    )

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        property_name.upper(),
        center_x=540,
        y=915,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    return downsample(canvas)


# =====================================================================
# 04 — HOUSE BUILD
# =====================================================================


def draw_physical_house(
    canvas: Image.Image,
    *,
    x: float,
    y: float,
    size: float = 95,
) -> None:
    """Draw a dimensional house anchored to a canonical property."""

    shadow = Image.new(
        "RGBA",
        (
            s(size * 1.55),
            s(size * 0.70),
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
            s(size * 0.10),
            s(size * 0.25),
            s(size * 1.45),
            s(size * 0.59),
        ),
        fill=(
            0,
            0,
            0,
            150,
        ),
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(s(7)))

    paste_center(
        canvas,
        shadow,
        x=x,
        y=y + size * 0.50,
    )

    draw = ImageDraw.Draw(canvas)

    half_width = size * 0.52

    roof_height = size * 0.42

    wall_height = size * 0.52

    draw.polygon(
        (
            (
                s(x - half_width),
                s(y),
            ),
            (
                s(x),
                s(y - roof_height),
            ),
            (
                s(x + half_width),
                s(y),
            ),
        ),
        fill=(
            31,
            177,
            92,
        ),
        outline=(
            238,
            255,
            244,
        ),
    )

    draw.rounded_rectangle(
        (
            s(x - half_width * 0.82),
            s(y),
            s(x + half_width * 0.82),
            s(y + wall_height),
        ),
        radius=s(5),
        fill=(
            34,
            197,
            94,
        ),
        outline=(
            238,
            255,
            244,
        ),
        width=s(2),
    )

    draw.rectangle(
        (
            s(x - size * 0.10),
            s(y + size * 0.22),
            s(x + size * 0.10),
            s(y + wall_height),
        ),
        fill=(
            17,
            108,
            57,
        ),
    )


def property_scene_offset(
    space: int,
    *,
    shift: float = 170.0,
) -> tuple[
    float,
    float,
]:
    """Shift an edge-property close-up inward for overlay-safe framing."""

    index = space % 40

    if 31 <= index <= 39:
        return (
            shift,
            0.0,
        )

    if 11 <= index <= 19:
        return (
            -shift,
            0.0,
        )

    if 21 <= index <= 29:
        return (
            0.0,
            shift,
        )

    if 1 <= index <= 9:
        return (
            0.0,
            -shift,
        )

    return (
        0.0,
        0.0,
    )


def translate_scene(
    image: Image.Image,
    *,
    offset_x: float,
    offset_y: float,
) -> Image.Image:
    """Translate a supersampled scene while preserving the V5 background."""

    translated = rgba_canvas()

    translated.paste(
        image,
        (
            s(offset_x),
            s(offset_y),
        ),
        image,
    )

    return translated


def render_04_house_build(
    runtime: PreviewRuntime,
) -> Image.Image:
    turn = runtime.story.build_turn

    event = build_event(turn)

    if semantic_event_type(event) != "HOUSE_BUILT":
        raise RuntimeError("House Build renderer received a non-HOUSE_BUILT event.")

    space = build_space_index(turn)

    property_name = build_property_name(turn)

    amount_value = getattr(
        event,
        "amount",
        None,
    )

    amount = (
        float(amount_value)
        if isinstance(
            amount_value,
            (int, float),
        )
        else 0.0
    )

    house_count_value = getattr(
        event,
        "houses_after",
        None,
    )

    house_count = (
        int(house_count_value)
        if isinstance(
            house_count_value,
            int,
        )
        and house_count_value > 0
        else 1
    )

    zoom = 1.70
    vertical_bias = -0.03

    base_scene = board_zoom(
        state=turn.state_after,
        focus_space=space,
        active=turn.strategy_id,
        zoom=zoom,
        vertical_bias=vertical_bias,
        dim=0.08,
    )

    offset_x, offset_y = property_scene_offset(
        space,
        shift=185.0,
    )

    canvas = translate_scene(
        base_scene,
        offset_x=offset_x,
        offset_y=offset_y,
    )

    hero_header(
        canvas,
        kicker="0:03  •  DEVELOPMENT",
        headline="A HOUSE GOES UP.",
        subline=(property_name + " changes on the actual board."),
        accent=ACCENTS[turn.strategy_id],
    )

    projected_x, projected_y = board_zoom_project(
        focus_space=space,
        target_space=space,
        zoom=zoom,
        vertical_bias=vertical_bias,
    )

    property_x = projected_x + offset_x

    property_y = projected_y + offset_y

    # Property overlays must remain inside a mobile-safe visual region.
    property_x = max(
        210.0,
        min(
            870.0,
            property_x,
        ),
    )

    property_y = max(
        260.0,
        min(
            720.0,
            property_y,
        ),
    )

    displayed_houses = min(
        house_count,
        4,
    )

    spacing = 72.0

    start_x = property_x - spacing * (displayed_houses - 1) / 2.0

    for index in range(displayed_houses):
        draw_physical_house(
            canvas,
            x=start_x + spacing * index,
            y=property_y - 20,
            size=92,
        )

    piece_x = max(
        150.0,
        min(
            930.0,
            property_x + 210.0,
        ),
    )

    piece_y = max(
        300.0,
        min(
            770.0,
            property_y + 120.0,
        ),
    )

    grounded_piece(
        canvas,
        strategy=turn.strategy_id,
        x=piece_x,
        y=piece_y,
        size=150,
    )

    draw = ImageDraw.Draw(canvas)

    rounded_panel(
        draw,
        (
            245,
            815,
            835,
            990,
        ),
        radius=24,
        fill=(
            4,
            12,
            22,
        ),
        outline=GREEN,
        width=2,
    )

    centered_text(
        draw,
        property_name.upper(),
        center_x=540,
        y=840,
        size=TYPE_LABEL,
        fill=MUTED,
    )

    centered_text(
        draw,
        (f"HOUSE {house_count} BUILT" if house_count > 1 else "HOUSE BUILT"),
        center_x=540,
        y=885,
        size=TYPE_HEADLINE,
        fill=GREEN,
    )

    centered_text(
        draw,
        (f"${amount:,.0f} DEVELOPMENT COST" if amount > 0 else "DEVELOPMENT"),
        center_x=540,
        y=950,
        size=TYPE_SMALL,
        fill=WHITE,
    )

    return downsample(canvas)


# =====================================================================
# 05 — RENT HIT
# =====================================================================


def render_05_rent_hit(
    runtime: PreviewRuntime,
) -> Image.Image:
    turn = runtime.story.rent_turn

    event = rent_event(turn)

    space = rent_space_index(turn)

    property_name = rent_property_name(turn)

    amount_value = getattr(
        event,
        "amount",
        None,
    )

    amount = (
        float(amount_value)
        if isinstance(
            amount_value,
            (int, float),
        )
        else abs(cash_delta(turn))
    )

    canvas = board_zoom(
        state=turn.state_after,
        focus_space=space,
        active=turn.strategy_id,
        zoom=1.75,
        dim=0.32,
        blur=1.0,
    )

    hero_header(
        canvas,
        kicker="0:04  •  RENT",
        headline="THEN THE RENT HITS.",
        subline=(property_name + " turns one landing into a liquidity event."),
        accent=RED,
    )

    draw = ImageDraw.Draw(canvas)

    rounded_panel(
        draw,
        (
            280,
            250,
            800,
            570,
        ),
        radius=30,
        fill=(
            247,
            242,
            228,
        ),
        outline=RED,
        width=3,
    )

    centered_text(
        draw,
        "RENT DUE",
        center_x=540,
        y=295,
        size=TYPE_LABEL,
        fill=RED,
    )

    centered_text(
        draw,
        f"${amount:,.0f}",
        center_x=540,
        y=350,
        size=TYPE_HERO,
        fill=INK,
    )

    centered_text(
        draw,
        property_name,
        center_x=540,
        y=465,
        size=TYPE_BODY,
        fill=INK,
    )

    large_metric_pair(
        canvas,
        before=turn.state_before.cash[turn.strategy_id],
        after=turn.state_after.cash[turn.strategy_id],
        label_before="CASH BEFORE",
        label_after="CASH AFTER",
        accent=RED,
        y=675,
    )

    return downsample(canvas)


# =====================================================================
# 06 — CASH CRASH
# =====================================================================


def render_06_cash_crash(
    runtime: PreviewRuntime,
) -> Image.Image:
    turn = runtime.story.shock_turn

    strategy = turn.strategy_id

    canvas = render_board_stage(
        state=turn.state_after,
        active=None,
        board_left=-100,
        board_top=100,
        board_size=1280,
        blur=3.2,
        dim=0.58,
    )

    hero_header(
        canvas,
        kicker="0:05  •  LIQUIDITY",
        headline="CASH COLLAPSES.",
        subline="Expansion only works while the strategy can survive.",
        accent=RED,
    )

    grounded_piece(
        canvas,
        strategy=strategy,
        x=245,
        y=585,
        size=255,
        shadow_scale=1.2,
    )

    draw = ImageDraw.Draw(canvas)

    rounded_panel(
        draw,
        (
            440,
            220,
            1000,
            885,
        ),
        radius=35,
        fill=(
            5,
            14,
            25,
        ),
        outline=RED,
        width=3,
    )

    centered_text(
        draw,
        DISPLAY_NAMES[strategy].upper(),
        center_x=720,
        y=280,
        size=TYPE_LABEL,
        fill=ACCENTS[strategy],
    )

    centered_text(
        draw,
        f"${turn.state_before.cash[strategy]:,.0f}",
        center_x=720,
        y=370,
        size=TYPE_DISPLAY,
        fill=WHITE,
    )

    centered_text(
        draw,
        "↓",
        center_x=720,
        y=460,
        size=TYPE_DISPLAY,
        fill=RED,
    )

    centered_text(
        draw,
        f"${turn.state_after.cash[strategy]:,.0f}",
        center_x=720,
        y=550,
        size=TYPE_HERO,
        fill=RED,
    )

    centered_text(
        draw,
        "LIQUIDITY CRITICAL",
        center_x=720,
        y=680,
        size=TYPE_LABEL,
        fill=RED,
    )

    bar_left = 520
    bar_right = 920
    bar_y = 760

    draw.rounded_rectangle(
        (
            s(bar_left),
            s(bar_y),
            s(bar_right),
            s(bar_y + 38),
        ),
        radius=s(10),
        fill=(
            46,
            58,
            73,
        ),
    )

    before = max(
        turn.state_before.cash[strategy],
        1,
    )

    after = max(
        turn.state_after.cash[strategy],
        0,
    )

    fraction = max(
        0.015,
        min(
            1.0,
            after / before,
        ),
    )

    draw.rounded_rectangle(
        (
            s(bar_left),
            s(bar_y),
            s(bar_left + (bar_right - bar_left) * fraction),
            s(bar_y + 38),
        ),
        radius=s(10),
        fill=RED,
    )

    return downsample(canvas)


# =====================================================================
# 07 — SURVIVAL QUESTION
# =====================================================================


def render_07_survival_question(
    runtime: PreviewRuntime,
) -> Image.Image:
    del runtime

    canvas = rgba_canvas()

    draw = ImageDraw.Draw(canvas)

    x_positions = (
        225,
        430,
        650,
        855,
    )

    sizes = (
        165,
        180,
        180,
        175,
    )

    for strategy, x, size in zip(
        STRATEGY_ORDER,
        x_positions,
        sizes,
        strict=True,
    ):
        grounded_piece(
            canvas,
            strategy=strategy,
            x=x,
            y=295,
            size=size,
            shadow_scale=1.1,
        )

    centered_text(
        draw,
        "WHICH AI LANDLORD",
        center_x=540,
        y=500,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    centered_text(
        draw,
        "SURVIVES",
        center_x=540,
        y=570,
        size=TYPE_HERO,
        fill=GOLD,
    )

    centered_text(
        draw,
        "10,000 GAMES?",
        center_x=540,
        y=675,
        size=TYPE_DISPLAY,
        fill=WHITE,
    )

    draw.line(
        (
            s(260),
            s(790),
            s(820),
            s(790),
        ),
        fill=(
            69,
            84,
            105,
        ),
        width=s(2),
    )

    centered_text(
        draw,
        "SAME CASH  •  SAME BOARD  •  DIFFERENT RULES",
        center_x=540,
        y=825,
        size=TYPE_BODY,
        fill=MUTED,
        bold=False,
    )

    return downsample(canvas)


# =====================================================================
# 08 — STRATEGY PERSONALITIES
# =====================================================================


def render_08_strategy_personalities(
    runtime: PreviewRuntime,
) -> Image.Image:
    del runtime

    canvas = rgba_canvas()

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "FOUR STRATEGIES.",
        center_x=540,
        y=40,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    centered_text(
        draw,
        "FOUR DIFFERENT WAYS TO PLAY THE SAME BOARD.",
        center_x=540,
        y=95,
        size=TYPE_BODY,
        fill=MUTED,
        bold=False,
    )

    name_lines = {
        "collector": ("COLLECTOR",),
        "specialist": ("SPECIALIST",),
        "cash_protector": (
            "CASH",
            "PROTECTOR",
        ),
        "aggressive_builder": (
            "AGGRESSIVE",
            "BUILDER",
        ),
    }

    tagline_lines = {
        "collector": ("BUY BROADLY",),
        "specialist": (
            "COMPLETE",
            "GROUPS",
        ),
        "cash_protector": ("HOLD RESERVES",),
        "aggressive_builder": ("BUILD FAST",),
    }

    descriptions = {
        "collector": "More properties. More options.",
        "specialist": "Concentrate before expanding.",
        "cash_protector": "Liquidity before growth.",
        "aggressive_builder": "Convert control into houses.",
    }

    for index, strategy in enumerate(STRATEGY_ORDER):
        left = 35 + index * 257

        right = left + 235

        center = left + 117

        rounded_panel(
            draw,
            (
                left,
                170,
                right,
                925,
            ),
            radius=24,
            fill=(
                7,
                17,
                29,
            ),
            outline=ACCENTS[strategy],
            width=3,
        )

        grounded_piece(
            canvas,
            strategy=strategy,
            x=center,
            y=330,
            size=175,
        )

        names = name_lines[strategy]

        name_start_y = 478 if len(names) == 2 else 500

        for line_index, line in enumerate(names):
            centered_text(
                draw,
                line,
                center_x=center,
                y=(name_start_y + line_index * 31),
                size=20,
                fill=ACCENTS[strategy],
            )

        taglines = tagline_lines[strategy]

        tagline_start_y = 580 if len(taglines) == 2 else 596

        for line_index, line in enumerate(taglines):
            centered_text(
                draw,
                line,
                center_x=center,
                y=(tagline_start_y + line_index * 31),
                size=20,
                fill=WHITE,
            )

        centered_text(
            draw,
            descriptions[strategy],
            center_x=center,
            y=670,
            size=13,
            fill=MUTED,
            bold=False,
        )

        if strategy == "collector":
            for marker in range(4):
                draw.ellipse(
                    (
                        s(left + 65 + marker * 34),
                        s(760),
                        s(left + 82 + marker * 34),
                        s(777),
                    ),
                    fill=ACCENTS[strategy],
                )

        elif strategy == "specialist":
            for marker in range(3):
                draw.rectangle(
                    (
                        s(left + 70 + marker * 38),
                        s(748),
                        s(left + 98 + marker * 38),
                        s(780),
                    ),
                    fill=ACCENTS[strategy],
                )

        elif strategy == "cash_protector":
            draw.rounded_rectangle(
                (
                    s(left + 50),
                    s(748),
                    s(right - 50),
                    s(782),
                ),
                radius=s(8),
                fill=(
                    42,
                    55,
                    69,
                ),
            )

            draw.rounded_rectangle(
                (
                    s(left + 50),
                    s(748),
                    s(left + 165),
                    s(782),
                ),
                radius=s(8),
                fill=ACCENTS[strategy],
            )

        else:
            for marker in range(3):
                marker_x = left + 72 + marker * 43

                draw.polygon(
                    (
                        (
                            s(marker_x - 15),
                            s(770),
                        ),
                        (
                            s(marker_x),
                            s(748),
                        ),
                        (
                            s(marker_x + 15),
                            s(770),
                        ),
                        (
                            s(marker_x + 15),
                            s(790),
                        ),
                        (
                            s(marker_x - 15),
                            s(790),
                        ),
                    ),
                    fill=GREEN,
                )

    return downsample(canvas)


# =====================================================================
# 09 — REPRESENTATIVE GAME MINI-STORY
# =====================================================================


def story_beat_detail(
    beat: StoryBeat,
) -> str:
    """Return the truthful display detail for one cinematic story beat."""

    turn = beat.turn

    if beat.label in {
        "ACQUIRE",
        "EXPAND",
    }:
        return purchase_property_name(turn)

    if beat.label == "BUILD":
        return build_property_name(turn)

    if beat.label == "RENT":
        return rent_property_name(turn)

    if beat.label == "CASH SHOCK":
        strategy = turn.strategy_id

        before = turn.state_before.cash[strategy]

        after = turn.state_after.cash[strategy]

        return f"${before:,.0f} -> ${after:,.0f}"

    if beat.label == "BANKRUPTCY":
        if not actual_bankruptcy_events(turn):
            raise RuntimeError("BANKRUPTCY story beat lacks BANKRUPTCY event.")

        return "RENT BANKRUPTCY"

    raise RuntimeError(f"Unsupported story beat label: {beat.label}")


def render_09_gameplay_story(
    runtime: PreviewRuntime,
) -> Image.Image:
    canvas = rgba_canvas()

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "ONE REPRESENTATIVE GAME.",
        center_x=540,
        y=35,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    centered_text(
        draw,
        "SIX REAL EVENTS. ONE CHRONOLOGICAL STATE.",
        center_x=540,
        y=94,
        size=TYPE_BODY,
        fill=GOLD,
    )

    beats = runtime.story.narrative_beats

    if len(beats) != 6:
        raise RuntimeError("Gameplay Story requires exactly six truthful beats.")

    positions = (
        (
            45,
            185,
        ),
        (
            375,
            185,
        ),
        (
            705,
            185,
        ),
        (
            45,
            565,
        ),
        (
            375,
            565,
        ),
        (
            705,
            565,
        ),
    )

    for sequence, (
        beat,
        (
            left,
            top,
        ),
    ) in enumerate(
        zip(
            beats,
            positions,
            strict=True,
        ),
        start=1,
    ):
        turn = beat.turn

        rounded_panel(
            draw,
            (
                left,
                top,
                left + 285,
                top + 300,
            ),
            radius=22,
            fill=(
                8,
                18,
                31,
            ),
            outline=ACCENTS[turn.strategy_id],
            width=2,
        )

        left_text(
            draw,
            str(sequence),
            x=left + 27,
            y=top + 20,
            size=TYPE_SMALL,
            fill=MUTED,
        )

        grounded_piece(
            canvas,
            strategy=turn.strategy_id,
            x=left + 143,
            y=top + 105,
            size=110,
        )

        centered_text(
            draw,
            beat.label,
            center_x=left + 143,
            y=top + 184,
            size=TYPE_LABEL,
            fill=GOLD,
        )

        centered_text(
            draw,
            DISPLAY_NAMES[turn.strategy_id],
            center_x=left + 143,
            y=top + 230,
            size=TYPE_SMALL,
            fill=ACCENTS[turn.strategy_id],
        )

        centered_text(
            draw,
            story_beat_detail(beat),
            center_x=left + 143,
            y=top + 262,
            size=TYPE_FINE,
            fill=MUTED,
            bold=False,
        )

    draw.line(
        (
            s(110),
            s(535),
            s(970),
            s(535),
        ),
        fill=(
            66,
            82,
            104,
        ),
        width=s(2),
    )

    return downsample(canvas)


# =====================================================================
# 10 — SCALE TO 10,000
# =====================================================================


def render_10_scale_10000(
    runtime: PreviewRuntime,
) -> Image.Image:
    del runtime

    canvas = rgba_canvas()

    board = board_image().convert("RGB")

    tile = board.resize(
        (
            s(172),
            s(172),
        ),
        Image.Resampling.LANCZOS,
    ).convert("RGBA")

    for row in range(5):
        for column in range(5):
            x = 68 + column * 190

            y = 145 + row * 178

            canvas.alpha_composite(
                tile,
                (
                    s(x),
                    s(y),
                ),
            )

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
            120,
        ),
    )

    canvas.alpha_composite(overlay)

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "ONE GAME IS A STORY.",
        center_x=540,
        y=36,
        size=TYPE_SECTION,
        fill=WHITE,
    )

    rounded_panel(
        draw,
        (
            225,
            330,
            855,
            760,
        ),
        radius=34,
        fill=(
            3,
            10,
            18,
        ),
        outline=GOLD,
        width=3,
    )

    centered_text(
        draw,
        "SIMULATIONS",
        center_x=540,
        y=390,
        size=TYPE_LABEL,
        fill=MUTED,
    )

    centered_text(
        draw,
        "10,000",
        center_x=540,
        y=455,
        size=TYPE_HERO,
        fill=GOLD,
    )

    centered_text(
        draw,
        "FULL GAMES",
        center_x=540,
        y=585,
        size=TYPE_SECTION,
        fill=WHITE,
    )

    centered_text(
        draw,
        "10,000 GAMES ARE EVIDENCE.",
        center_x=540,
        y=680,
        size=TYPE_BODY,
        fill=MUTED,
    )

    return downsample(canvas)


# =====================================================================
# 11 — LEADERBOARD + WILSON CI
# =====================================================================


def normal_profile(
    *,
    mean: float,
    low: float,
    high: float,
    chart_left: float,
    chart_right: float,
    baseline: float,
    height: float,
    scale_low: float,
    scale_high: float,
) -> tuple[
    tuple[
        float,
        float,
    ],
    ...,
]:
    sigma = max(
        (high - low) / 3.92,
        1e-6,
    )

    points = []

    for index in range(121):
        value = scale_low + (scale_high - scale_low) * index / 120

        x = chart_left + (value - scale_low) / (scale_high - scale_low) * (chart_right - chart_left)

        density = math.exp(-0.5 * ((value - mean) / sigma) ** 2)

        y = baseline - density * height

        points.append(
            (
                x,
                y,
            )
        )

    return tuple(points)


def render_11_leaderboard_ci(
    runtime: PreviewRuntime,
) -> Image.Image:
    canvas = rgba_canvas()

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "WHO WON MOST OFTEN?",
        center_x=540,
        y=34,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    centered_text(
        draw,
        "ACTUAL WIN RATE  •  95% WILSON CONFIDENCE INTERVAL",
        center_x=540,
        y=92,
        size=TYPE_SMALL,
        fill=MUTED,
    )

    rows = ranking(runtime)

    scale_low = max(
        0.0,
        min(metric.ci_lower for metric in rows) - 0.03,
    )

    scale_high = min(
        1.0,
        max(metric.ci_upper for metric in rows) + 0.03,
    )

    chart_left = 390.0
    chart_right = 965.0

    row_centers = (
        260,
        455,
        650,
        845,
    )

    denominator = scale_high - scale_low

    def x_axis(
        value: float,
        *,
        minimum: float = scale_low,
        span: float = denominator,
        left: float = chart_left,
        right: float = chart_right,
    ) -> float:
        return left + (value - minimum) / span * (right - left)

    for metric, row_center in zip(
        rows,
        row_centers,
        strict=True,
    ):
        grounded_piece(
            canvas,
            strategy=metric.strategy_id,
            x=90,
            y=row_center,
            size=82,
        )

        left_text(
            draw,
            DISPLAY_NAMES[metric.strategy_id],
            x=145,
            y=row_center - 40,
            size=TYPE_LABEL,
            fill=ACCENTS[metric.strategy_id],
        )

        left_text(
            draw,
            f"{metric.win_rate:.1%}",
            x=145,
            y=row_center + 4,
            size=TYPE_METRIC,
            fill=WHITE,
        )

        center = x_axis(metric.win_rate)

        low = x_axis(metric.ci_lower)

        high = x_axis(metric.ci_upper)

        # Decorative curve uses a minimum visible width so very tight
        # confidence intervals still read well on mobile. Statistical
        # whisker positions below remain exact.
        decorative_sigma = max(
            (high - low) / 3.92,
            34.0,
        )

        baseline = row_center + 30

        points = []

        for index in range(121):
            x = chart_left + (chart_right - chart_left) * index / 120

            density = math.exp(-0.5 * ((x - center) / decorative_sigma) ** 2)

            y = baseline - density * 65

            points.append(
                (
                    s(x),
                    s(y),
                )
            )

        draw.line(
            tuple(points),
            fill=ACCENTS[metric.strategy_id],
            width=s(4),
        )

        draw.line(
            (
                s(low),
                s(baseline + 18),
                s(high),
                s(baseline + 18),
            ),
            fill=WHITE,
            width=s(4),
        )

        for value in (
            low,
            high,
        ):
            draw.line(
                (
                    s(value),
                    s(baseline + 5),
                    s(value),
                    s(baseline + 31),
                ),
                fill=WHITE,
                width=s(3),
            )

        draw.ellipse(
            (
                s(center - 8),
                s(baseline + 10),
                s(center + 8),
                s(baseline + 26),
            ),
            fill=GOLD,
        )

    axis_y = 980

    draw.line(
        (
            s(chart_left),
            s(axis_y),
            s(chart_right),
            s(axis_y),
        ),
        fill=(
            75,
            91,
            112,
        ),
        width=s(2),
    )

    for value in (
        scale_low,
        (scale_low + scale_high) / 2,
        scale_high,
    ):
        x = x_axis(value)

        draw.line(
            (
                s(x),
                s(axis_y - 6),
                s(x),
                s(axis_y + 6),
            ),
            fill=MUTED,
            width=s(2),
        )

        centered_text(
            draw,
            f"{value:.0%}",
            center_x=x,
            y=997,
            size=TYPE_FINE,
            fill=MUTED,
            bold=False,
        )

    return downsample(canvas)


# =====================================================================
# 12 — RISK / REWARD
# =====================================================================


def render_12_risk_reward(
    runtime: PreviewRuntime,
) -> Image.Image:
    canvas = rgba_canvas()

    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "RISK / REWARD",
        center_x=540,
        y=34,
        size=TYPE_HEADLINE,
        fill=WHITE,
    )

    centered_text(
        draw,
        "WIN RATE  •  BANKRUPTCY  •  MEDIAN CASH",
        center_x=540,
        y=91,
        size=TYPE_SMALL,
        fill=MUTED,
    )

    rows = ranking(runtime)

    column_centers = (
        460,
        705,
        925,
    )

    for title, center in zip(
        (
            "WIN RATE",
            "BANKRUPTCY",
            "MEDIAN CASH",
        ),
        column_centers,
        strict=True,
    ):
        centered_text(
            draw,
            title,
            center_x=center,
            y=175,
            size=TYPE_SMALL,
            fill=MUTED,
        )

    maximum_win = max(metric.win_rate for metric in rows)

    maximum_bankruptcy = max(metric.bankruptcy_rate for metric in rows)

    maximum_cash = max(
        1.0,
        max(metric.median_finishing_cash for metric in rows),
    )

    row_centers = (
        300,
        490,
        680,
        870,
    )

    for metric, y in zip(
        rows,
        row_centers,
        strict=True,
    ):
        grounded_piece(
            canvas,
            strategy=metric.strategy_id,
            x=85,
            y=y,
            size=80,
        )

        left_text(
            draw,
            DISPLAY_NAMES[metric.strategy_id],
            x=145,
            y=y - 32,
            size=TYPE_LABEL,
            fill=ACCENTS[metric.strategy_id],
        )

        specs = (
            (
                350,
                metric.win_rate / maximum_win,
                f"{metric.win_rate:.1%}",
            ),
            (
                595,
                metric.bankruptcy_rate / maximum_bankruptcy,
                f"{metric.bankruptcy_rate:.1%}",
            ),
            (
                815,
                metric.median_finishing_cash / maximum_cash,
                f"${metric.median_finishing_cash:,.0f}",
            ),
        )

        for left, fraction, value in specs:
            right = left + 145

            draw.rounded_rectangle(
                (
                    s(left),
                    s(y - 20),
                    s(right),
                    s(y + 24),
                ),
                radius=s(9),
                fill=(
                    34,
                    48,
                    65,
                ),
            )

            width = max(
                3.0,
                145 * fraction,
            )

            draw.rounded_rectangle(
                (
                    s(left),
                    s(y - 20),
                    s(left + width),
                    s(y + 24),
                ),
                radius=s(9),
                fill=ACCENTS[metric.strategy_id],
            )

            centered_text(
                draw,
                value,
                center_x=left + 72,
                y=y + 46,
                size=TYPE_SMALL,
                fill=WHITE,
            )

    return downsample(canvas)


# =====================================================================
# 13 — RESULT
# =====================================================================


def render_13_result(
    runtime: PreviewRuntime,
) -> Image.Image:
    canvas = rgba_canvas()

    draw = ImageDraw.Draw(canvas)

    leader = ranking(runtime)[0]

    winner = runtime.headline_winner or leader.strategy_id

    centered_text(
        draw,
        "THE RESULT",
        center_x=540,
        y=42,
        size=TYPE_SECTION,
        fill=MUTED,
    )

    grounded_piece(
        canvas,
        strategy=winner,
        x=270,
        y=475,
        size=300,
        shadow_scale=1.2,
    )

    result_center_x = 745

    if runtime.headline_winner is None:
        line_one = "NO SINGLE"
        line_two = "SUPPORTED WINNER"

        metric_text = "NUMERICAL LEADER: " + DISPLAY_NAMES[leader.strategy_id].upper()

        metric_size = TYPE_SECTION

    else:
        line_one = DISPLAY_NAMES[winner].upper()

        line_two = "WINS MOST OFTEN"

        metric_text = f"{leader.win_rate:.1%}"

        metric_size = TYPE_HERO

    centered_text(
        draw,
        line_one,
        center_x=result_center_x,
        y=250,
        size=TYPE_HEADLINE,
        fill=ACCENTS[winner],
    )

    # Dynamically fit the long result headline inside a 500px safe area.
    result_line_size = TYPE_HEADLINE

    while result_line_size > 30:
        active_font = font(
            result_line_size,
            bold=True,
        )

        box = draw.textbbox(
            (
                0,
                0,
            ),
            line_two,
            font=active_font,
        )

        width = (box[2] - box[0]) / SCALE

        if width <= 500:
            break

        result_line_size -= 1

    centered_text(
        draw,
        line_two,
        center_x=result_center_x,
        y=320,
        size=result_line_size,
        fill=GOLD,
    )

    centered_text(
        draw,
        metric_text,
        center_x=result_center_x,
        y=410,
        size=metric_size,
        fill=WHITE,
    )

    centered_text(
        draw,
        "10,000-GAME SIMULATION",
        center_x=result_center_x,
        y=535,
        size=TYPE_LABEL,
        fill=MUTED,
    )

    rounded_panel(
        draw,
        (
            450,
            625,
            995,
            920,
        ),
        radius=26,
        fill=(
            8,
            18,
            31,
        ),
    )

    proof = (
        "10,000 deterministic games",
        "Balanced strategy-seat assignments",
        "95% Wilson confidence intervals",
        "Exact binomial + Holm correction",
    )

    for index, line in enumerate(proof):
        y = 670 + index * 58

        left_text(
            draw,
            "✓",
            x=495,
            y=y,
            size=TYPE_BODY,
            fill=GREEN,
        )

        left_text(
            draw,
            line,
            x=540,
            y=y,
            size=TYPE_BODY,
            fill=WHITE,
        )

    centered_text(
        draw,
        ("Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro."),
        center_x=540,
        y=1017,
        size=TYPE_FINE,
        fill=MUTED,
        bold=False,
    )

    return downsample(canvas)


PREVIEW_RENDERERS = {
    "01_dice_hit": render_01_dice_hit,
    "02_piece_race": render_02_piece_race,
    "03_property_purchase": render_03_property_purchase,
    "04_house_build": render_04_house_build,
    "05_rent_hit": render_05_rent_hit,
    "06_cash_crash": render_06_cash_crash,
    "07_survival_question": render_07_survival_question,
    "08_strategy_personalities": render_08_strategy_personalities,
    "09_gameplay_story": render_09_gameplay_story,
    "10_scale_10000": render_10_scale_10000,
    "11_leaderboard_ci": render_11_leaderboard_ci,
    "12_risk_reward": render_12_risk_reward,
    "13_result": render_13_result,
}


def render_preview_set(
    *,
    output_directory: Path = OUTPUT_DIRECTORY,
    show_progress: bool = True,
) -> dict[
    str,
    Path,
]:
    if output_directory.exists():
        shutil.rmtree(output_directory)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    runtime = load_runtime()

    outputs = {}

    for index, (
        key,
        renderer,
    ) in enumerate(
        PREVIEW_RENDERERS.items(),
        start=1,
    ):
        if show_progress:
            print(
                f"[V5 PREVIEW] {index:02d}/13 {key}",
                flush=True,
            )

        image = renderer(runtime)

        if image.size != (
            WIDTH,
            HEIGHT,
        ):
            raise RuntimeError(f"{key}: invalid image size {image.size}")

        path = output_directory / f"{key}.png"

        image.save(
            path,
            format="PNG",
            compress_level=4,
        )

        outputs[key] = path

    return outputs
