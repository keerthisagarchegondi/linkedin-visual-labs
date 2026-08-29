"""Project 3 — Step 8 — deterministic 60-second video renderer.

The video is entirely derived from frozen Project 3 artifacts:

- canonical simulation configuration
- representative-game event log
- validated tournament summary
- accepted V6 visual system
- accepted metallic rendered-3D strategy sprites

The renderer creates exactly:

    1080 x 1080
    30 FPS
    1,800 frames
    60 seconds

The PNG sequence is encoded by FFmpeg as H.264/yuv420p.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

import numpy as np
from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFont,
)

from linkedin_visual_labs.projects.p02_monopoly_ai.piece_assets_3d import (
    PIECE_NAMES,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
    board_positions,
    load_board_spaces,
    load_preview_context,
)

# ============================================================================
# 8.1 — GLOBAL MEDIA CONTRACT
# ============================================================================

WIDTH: Final = 1080
HEIGHT: Final = 1080
FPS: Final = 30
DURATION_SECONDS: Final = 60
FRAME_COUNT: Final = FPS * DURATION_SECONDS

VIDEO_CODEC: Final = "h264"
PIXEL_FORMAT: Final = "yuv420p"

MASTER_SEED: Final = 73031


PROJECT_ROOT: Final = Path("outputs/p02_monopoly_ai")

DATA_ROOT: Final = PROJECT_ROOT / "data"

VALIDATION_ROOT: Final = PROJECT_ROOT / "validation"

VISUAL_ROOT: Final = PROJECT_ROOT / "visual"

V6_PREVIEW_ROOT: Final = VISUAL_ROOT / "cinematic_preview_v6"

V6_PIECE_ROOT: Final = VISUAL_ROOT / "v6_3d_piece_assets"

VIDEO_ROOT: Final = PROJECT_ROOT / "video"

FRAME_ROOT: Final = VIDEO_ROOT / "frames"

REPRESENTATIVE_FRAME_ROOT: Final = VIDEO_ROOT / "representative_frames"

CANONICAL_VIDEO_ROOT: Final = VIDEO_ROOT / "canonical"

CANONICAL_MP4: Final = CANONICAL_VIDEO_ROOT / "p02_monopoly_ai_60s.mp4"

VIDEO_MANIFEST: Final = VIDEO_ROOT / "video_manifest.json"


TOURNAMENT_SUMMARY_PATH: Final = DATA_ROOT / "tournament_summary.json"

REPRESENTATIVE_GAME_PATH: Final = DATA_ROOT / "representative_game.json"

REPRESENTATIVE_EVENTS_PATH: Final = DATA_ROOT / "representative_game_events.json"


STRATEGIES: Final = (
    "collector",
    "specialist",
    "cash_protector",
    "aggressive_builder",
)


DISPLAY_NAMES: Final = {
    "collector": "Collector",
    "specialist": "Specialist",
    "cash_protector": "Cash Protector",
    "aggressive_builder": "Aggressive Builder",
}


ACCENTS: Final = {
    "collector": (0, 119, 182),
    "specialist": (166, 30, 105),
    "cash_protector": (4, 120, 87),
    "aggressive_builder": (198, 93, 0),
}


BACKGROUND: Final = (
    7,
    16,
    29,
)

PANEL: Final = (
    9,
    21,
    38,
)

WHITE: Final = (
    248,
    250,
    252,
)

MUTED: Final = (
    203,
    213,
    225,
)

GOLD: Final = (
    255,
    209,
    102,
)

DANGER: Final = (
    229,
    57,
    53,
)

POSITIVE: Final = (
    22,
    163,
    74,
)

WARNING: Final = (
    250,
    204,
    21,
)


# ============================================================================
# 8.1 — TIMELINE
# ============================================================================


@dataclass(frozen=True)
class TimelineSegment:
    key: str
    start_second: float
    end_second: float

    @property
    def start_frame(self) -> int:
        return round(self.start_second * FPS)

    @property
    def end_frame(self) -> int:
        return round(self.end_second * FPS)

    @property
    def frame_count(self) -> int:
        return self.end_frame - self.start_frame


TIMELINE: Final = (
    TimelineSegment(
        "opening_hook",
        0.0,
        7.0,
    ),
    TimelineSegment(
        "strategy_introduction",
        7.0,
        14.0,
    ),
    TimelineSegment(
        "representative_game",
        14.0,
        31.0,
    ),
    TimelineSegment(
        "simulation_scale",
        31.0,
        39.0,
    ),
    TimelineSegment(
        "leaderboard",
        39.0,
        50.0,
    ),
    TimelineSegment(
        "risk_reward",
        50.0,
        55.0,
    ),
    TimelineSegment(
        "winner_reveal",
        55.0,
        60.0,
    ),
)


REPRESENTATIVE_FRAME_INDICES: Final = (
    0,
    90,
    180,
    300,
    450,
    660,
    840,
    1020,
    1140,
    1320,
    1560,
    1710,
    1785,
)


# ============================================================================
# 8.2 — FRAME-STATE MODEL
# ============================================================================


@dataclass(frozen=True)
class FrameState:
    frame_index: int
    second: float
    segment_key: str
    segment_progress: float


@dataclass(frozen=True)
class ReplayEvent:
    index: int
    raw_type: str
    strategy_id: str | None
    from_position: int | None
    to_position: int | None
    die_1: int | None
    die_2: int | None
    cash_after: float | None
    amount: float | None
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class ReplaySnapshot:
    event_index: int
    positions: Mapping[str, int]
    cash: Mapping[str, float]


@dataclass(frozen=True)
class ReplayModel:
    events: tuple[ReplayEvent, ...]
    snapshots: tuple[ReplaySnapshot, ...]


@dataclass(frozen=True)
class RuntimeInputs:
    context: Any
    board_positions_xy: tuple[
        tuple[
            float,
            float,
        ],
        ...,
    ]
    replay: ReplayModel
    representative_game: Mapping[str, Any]
    tournament_summary: Mapping[str, Any]


# ============================================================================
# HELPERS
# ============================================================================


def _progress(
    frame_index: int,
    segment: TimelineSegment,
) -> float:
    denominator = max(
        1,
        segment.frame_count,
    )

    return min(
        1.0,
        max(
            0.0,
            (frame_index - segment.start_frame) / denominator,
        ),
    )


def frame_state(
    frame_index: int,
) -> FrameState:
    if not (0 <= frame_index < FRAME_COUNT):
        raise ValueError(f"invalid frame index: {frame_index}")

    second = frame_index / FPS

    for segment in TIMELINE:
        if segment.start_frame <= frame_index < segment.end_frame:
            return FrameState(
                frame_index=frame_index,
                second=second,
                segment_key=segment.key,
                segment_progress=_progress(
                    frame_index,
                    segment,
                ),
            )

    raise RuntimeError(f"frame {frame_index} has no timeline segment")


def _font(
    size: int,
    *,
    bold: bool = False,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Arial Bold.ttf" if bold else "Arial.ttf",
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


def _centered_text(
    draw: ImageDraw.ImageDraw,
    *,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int] = (
        0,
        0,
        0,
    ),
) -> None:
    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=font,
        stroke_width=stroke_width,
    )

    width = bbox[2] - bbox[0]

    draw.text(
        (
            (WIDTH - width) // 2,
            y,
        ),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )


def _rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[
        int,
        int,
        int,
        int,
    ],
    *,
    fill: tuple[int, int, int, int] = (
        9,
        21,
        38,
        235,
    ),
    outline: tuple[int, int, int, int] = (
        64,
        86,
        117,
        255,
    ),
    radius: int = 22,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def _ease(
    value: float,
) -> float:
    value = min(
        1.0,
        max(
            0.0,
            value,
        ),
    )

    return value * value * (3.0 - 2.0 * value)


def _blend(
    first: Image.Image,
    second: Image.Image,
    amount: float,
) -> Image.Image:
    return Image.blend(
        first.convert("RGBA"),
        second.convert("RGBA"),
        min(
            1.0,
            max(
                0.0,
                amount,
            ),
        ),
    )


@lru_cache(maxsize=64)
def _image(
    raw_path: str,
) -> Image.Image:
    path = Path(raw_path)

    with Image.open(path) as handle:
        return handle.convert("RGBA").copy()


def _preview(
    name: str,
) -> Image.Image:
    path = V6_PREVIEW_ROOT / f"{name}.png"

    if not path.is_file():
        raise FileNotFoundError(path)

    return _image(str(path)).copy()


def _piece_image(
    strategy: str,
    *,
    size: int,
) -> Image.Image:
    asset_name = PIECE_NAMES[strategy]

    path = V6_PIECE_ROOT / f"{asset_name}.png"

    image = _image(str(path))

    return image.resize(
        (
            size,
            size,
        ),
        Image.Resampling.LANCZOS,
    )


def _paste_centered(
    destination: Image.Image,
    source: Image.Image,
    *,
    x: float,
    y: float,
) -> None:
    left = round(x - source.width / 2)

    top = round(y - source.height / 2)

    destination.alpha_composite(
        source,
        (
            left,
            top,
        ),
    )


def _board_pixel(
    position_index: int,
    positions: Sequence[
        tuple[
            float,
            float,
        ]
    ],
) -> tuple[
    float,
    float,
]:
    index = position_index % len(positions)

    x_norm, y_norm = positions[index]

    return (
        x_norm * WIDTH,
        (1.0 - y_norm) * HEIGHT,
    )


def _walk_mapping(
    value: Any,
) -> Iterable[
    tuple[
        str,
        Any,
    ]
]:
    if isinstance(
        value,
        Mapping,
    ):
        for key, nested in value.items():
            yield (
                str(key),
                nested,
            )

            yield from _walk_mapping(nested)

    elif isinstance(
        value,
        Sequence,
    ) and not isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        for nested in value:
            yield from _walk_mapping(nested)


def _first_value(
    value: Any,
    candidate_keys: Sequence[str],
) -> Any | None:
    candidates = {candidate.lower() for candidate in candidate_keys}

    for key, nested in _walk_mapping(value):
        if key.lower() in candidates:
            return nested

    return None


def _as_int(
    value: Any,
) -> int | None:
    if isinstance(
        value,
        bool,
    ):
        return None

    if isinstance(
        value,
        (
            int,
            np.integer,
        ),
    ):
        return int(value)

    if (
        isinstance(
            value,
            float,
        )
        and value.is_integer()
    ):
        return int(value)

    if isinstance(
        value,
        str,
    ):
        try:
            return int(value.strip())
        except ValueError:
            return None

    return None


def _as_float(
    value: Any,
) -> float | None:
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
            np.number,
        ),
    ):
        return float(value)

    if isinstance(
        value,
        str,
    ):
        cleaned = (
            value.strip()
            .replace(
                "$",
                "",
            )
            .replace(
                ",",
                "",
            )
        )

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def _strategy_from_value(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).lower()

    normalized = text.replace(
        " ",
        "_",
    ).replace(
        "-",
        "_",
    )

    for strategy in STRATEGIES:
        if strategy in normalized or DISPLAY_NAMES[strategy].lower() in text:
            return strategy

    return None


def _event_type(
    raw: Mapping[str, Any],
) -> str:
    value = _first_value(
        raw,
        (
            "event_type",
            "type",
            "event",
            "kind",
            "action",
            "name",
        ),
    )

    if value is None:
        return "event"

    return str(value).strip()


def _strategy(
    raw: Mapping[str, Any],
) -> str | None:
    value = _first_value(
        raw,
        (
            "strategy_id",
            "strategy",
            "player_strategy",
            "player",
            "player_id",
            "actor",
            "owner",
        ),
    )

    return _strategy_from_value(value)


def _position_value(
    raw: Mapping[str, Any],
    *,
    before: bool,
) -> int | None:
    keys = (
        (
            "from_position",
            "old_position",
            "position_before",
            "start_position",
            "previous_position",
        )
        if before
        else (
            "to_position",
            "new_position",
            "position_after",
            "end_position",
            "position",
            "board_position",
        )
    )

    return _as_int(
        _first_value(
            raw,
            keys,
        )
    )


def _die_value(
    raw: Mapping[str, Any],
    index: int,
) -> int | None:
    keys = (
        (
            "die_1",
            "die1",
            "dice_1",
            "dice1",
            "first_die",
        )
        if index == 1
        else (
            "die_2",
            "die2",
            "dice_2",
            "dice2",
            "second_die",
        )
    )

    value = _as_int(
        _first_value(
            raw,
            keys,
        )
    )

    if value is not None and 1 <= value <= 6:
        return value

    return None


def _cash_value(
    raw: Mapping[str, Any],
) -> float | None:
    return _as_float(
        _first_value(
            raw,
            (
                "cash_after",
                "cash_balance",
                "player_cash",
                "cash",
                "balance_after",
                "balance",
            ),
        )
    )


def _amount_value(
    raw: Mapping[str, Any],
) -> float | None:
    return _as_float(
        _first_value(
            raw,
            (
                "amount",
                "rent_amount",
                "purchase_price",
                "price",
                "payment",
                "cash_delta",
            ),
        )
    )


def _extract_raw_events(
    payload: Any,
) -> list[Mapping[str, Any]]:
    if isinstance(
        payload,
        list,
    ):
        return [
            item
            for item in payload
            if isinstance(
                item,
                Mapping,
            )
        ]

    if isinstance(
        payload,
        Mapping,
    ):
        for key in (
            "events",
            "event_log",
            "records",
            "items",
        ):
            nested = payload.get(key)

            if isinstance(
                nested,
                list,
            ):
                return [
                    item
                    for item in nested
                    if isinstance(
                        item,
                        Mapping,
                    )
                ]

    raise ValueError("representative_game_events.json does not contain an event list")


def _normalize_replay(
    payload: Any,
) -> ReplayModel:
    raw_events = _extract_raw_events(payload)

    events: list[ReplayEvent] = []

    positions: dict[
        str,
        int,
    ] = {strategy: 0 for strategy in STRATEGIES}

    cash: dict[
        str,
        float,
    ] = {strategy: 1500.0 for strategy in STRATEGIES}

    snapshots: list[ReplaySnapshot] = []

    for index, raw in enumerate(raw_events):
        strategy_id = _strategy(raw)

        from_position = _position_value(
            raw,
            before=True,
        )

        to_position = _position_value(
            raw,
            before=False,
        )

        cash_after = _cash_value(raw)

        event = ReplayEvent(
            index=index,
            raw_type=_event_type(raw),
            strategy_id=strategy_id,
            from_position=from_position,
            to_position=to_position,
            die_1=_die_value(
                raw,
                1,
            ),
            die_2=_die_value(
                raw,
                2,
            ),
            cash_after=cash_after,
            amount=_amount_value(raw),
            raw=raw,
        )

        events.append(event)

        if strategy_id is not None:
            if to_position is not None:
                positions[strategy_id] = to_position % 40

            if cash_after is not None:
                cash[strategy_id] = cash_after

        snapshots.append(
            ReplaySnapshot(
                event_index=index,
                positions=dict(positions),
                cash=dict(cash),
            )
        )

    if not events:
        raise ValueError("representative-game event log is empty")

    return ReplayModel(
        events=tuple(events),
        snapshots=tuple(snapshots),
    )


def load_runtime_inputs() -> RuntimeInputs:
    for path in (
        TOURNAMENT_SUMMARY_PATH,
        REPRESENTATIVE_GAME_PATH,
        REPRESENTATIVE_EVENTS_PATH,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    context = load_preview_context(validation_directory=VALIDATION_ROOT)

    # Explicitly load canonical board config so Step 8 remains
    # tied to the frozen board definition.
    load_board_spaces(Path("configs/p02_monopoly_ai.yaml"))

    positions = tuple(
        (
            float(x),
            float(y),
        )
        for x, y in board_positions()
    )

    with REPRESENTATIVE_EVENTS_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        replay = _normalize_replay(json.load(handle))

    with REPRESENTATIVE_GAME_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        representative_game = json.load(handle)

    with TOURNAMENT_SUMMARY_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:
        tournament_summary = json.load(handle)

    if not isinstance(
        representative_game,
        Mapping,
    ):
        raise ValueError("representative_game.json must contain an object")

    if not isinstance(
        tournament_summary,
        Mapping,
    ):
        raise ValueError("tournament_summary.json must contain an object")

    return RuntimeInputs(
        context=context,
        board_positions_xy=positions,
        replay=replay,
        representative_game=representative_game,
        tournament_summary=tournament_summary,
    )


# ============================================================================
# STATIC BOARD BACKPLATE
# ============================================================================


def _clean_board_backplate() -> Image.Image:
    """Create a clean board by suppressing accepted keyframe overlays.

    We use the accepted hook board and remove only the center/lower overlay
    region using a darkened board-compatible treatment. This keeps Step 8
    tightly coupled to the approved Step 7 board visual language without
    rebuilding that visual system.
    """

    image = _preview("01_hook_race")

    # Mild blur/contrast reduction creates a gameplay canvas while preserving
    # the canonical board perimeter.
    image = ImageEnhance.Contrast(image).enhance(0.92)

    return image


# ============================================================================
# DICE
# ============================================================================


DIE_PIPS: Final = {
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
            0.24,
        ),
        (
            0.72,
            0.24,
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
            0.76,
        ),
        (
            0.72,
            0.76,
        ),
    ),
}


def _die(
    value: int,
    *,
    size: int = 104,
    angle: float = 0.0,
) -> Image.Image:
    canvas_size = int(size * 1.45)

    image = Image.new(
        "RGBA",
        (
            canvas_size,
            canvas_size,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    draw = ImageDraw.Draw(image)

    offset = (canvas_size - size) // 2

    shadow = (
        offset + 9,
        offset + 12,
        offset + size + 9,
        offset + size + 12,
    )

    draw.rounded_rectangle(
        shadow,
        radius=19,
        fill=(
            0,
            0,
            0,
            110,
        ),
    )

    face = (
        offset,
        offset,
        offset + size,
        offset + size,
    )

    draw.rounded_rectangle(
        face,
        radius=19,
        fill=(
            247,
            249,
            252,
            255,
        ),
        outline=(
            107,
            114,
            128,
            255,
        ),
        width=3,
    )

    radius = max(
        5,
        int(size * 0.065),
    )

    for x_fraction, y_fraction in DIE_PIPS[value]:
        x = offset + int(x_fraction * size)

        y = offset + int(y_fraction * size)

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius,
            ),
            fill=(
                23,
                30,
                42,
                255,
            ),
        )

    return image.rotate(
        angle,
        resample=Image.Resampling.BICUBIC,
        expand=False,
    )


# ============================================================================
# 8.14 — TOKEN LIFT / CARRY / DROP
# ============================================================================


def _lift_carry_drop(
    start: tuple[
        float,
        float,
    ],
    end: tuple[
        float,
        float,
    ],
    progress: float,
) -> tuple[
    float,
    float,
    float,
]:
    progress = min(
        1.0,
        max(
            0.0,
            progress,
        ),
    )

    maximum_lift = 82.0

    if progress < 0.20:
        travel = 0.0
        lift = maximum_lift * progress / 0.20

    elif progress <= 0.80:
        travel = (progress - 0.20) / 0.60

        lift = maximum_lift

    else:
        travel = 1.0
        lift = maximum_lift * (1.0 - (progress - 0.80) / 0.20)

    travel = _ease(travel)

    x = start[0] + (end[0] - start[0]) * travel

    y = start[1] + (end[1] - start[1]) * travel

    return (
        x,
        y - lift,
        lift,
    )


# ============================================================================
# DATA-DRIVEN RESULT HELPERS
# ============================================================================


def ranking(
    context: Any,
) -> tuple[Any, ...]:
    return tuple(
        sorted(
            context.strategies,
            key=lambda metric: (
                -metric.win_rate,
                metric.strategy_id,
            ),
        )
    )


def numerical_leader(
    context: Any,
) -> Any:
    return ranking(context)[0]


def lowest_bankruptcy(
    context: Any,
) -> Any:
    return min(
        context.strategies,
        key=lambda metric: (
            metric.bankruptcy_rate,
            metric.strategy_id,
        ),
    )


def highest_median_cash(
    context: Any,
) -> Any:
    return max(
        context.strategies,
        key=lambda metric: (
            metric.median_finishing_cash,
            metric.strategy_id,
        ),
    )


def headline_winner(
    context: Any,
) -> str | None:
    value = getattr(
        context,
        "headline_winner",
        None,
    )

    if value is None:
        return None

    return str(value)


def takeaway_sentence(
    context: Any,
) -> str:
    supported = headline_winner(context)

    leader = numerical_leader(context)

    safest = lowest_bankruptcy(context)

    cash_leader = highest_median_cash(context)

    if supported is None:
        return (
            f"{DISPLAY_NAMES[leader.strategy_id]} finished with the "
            f"highest numerical win rate, but the statistical winner "
            f"rule did not support a single definitive champion."
        )

    if supported == safest.strategy_id == cash_leader.strategy_id:
        return (
            f"{DISPLAY_NAMES[supported]} won most often while also "
            f"finishing with the strongest liquidity profile."
        )

    if supported == safest.strategy_id:
        return (
            f"{DISPLAY_NAMES[supported]} paired the supported win-rate "
            f"advantage with the lowest bankruptcy rate."
        )

    if supported == cash_leader.strategy_id:
        return (
            f"{DISPLAY_NAMES[supported]} paired the supported win-rate "
            f"advantage with the highest median finishing cash."
        )

    return (
        f"{DISPLAY_NAMES[supported]} won the statistical comparison, "
        f"but the safest and richest finishing profiles belonged to "
        f"different strategies."
    )


# ============================================================================
# SEGMENT RENDERERS
# ============================================================================


def _opening_hook(
    state: FrameState,
) -> Image.Image:
    second = state.second

    if second < 3.0:
        amount = second / 3.0

        image = _blend(
            _preview("01_hook_race"),
            _preview("02_hook_rent"),
            amount * 0.22,
        )

        # Dice motion gives the first seconds continuous kinetic energy.
        phase = second * 5.4

        die_1 = _die(
            6,
            size=112,
            angle=(math.sin(phase) * 14.0),
        )

        die_2 = _die(
            5,
            size=112,
            angle=(math.cos(phase) * 14.0),
        )

        bounce = abs(math.sin(phase)) * 22

        _paste_centered(
            image,
            die_1,
            x=445,
            y=535 - bounce,
        )

        _paste_centered(
            image,
            die_2,
            x=595,
            y=535 - bounce * 0.75,
        )

    elif second < 6.0:
        amount = (second - 3.0) / 3.0

        image = _blend(
            _preview("02_hook_rent"),
            _preview("03_hook_liquidity"),
            _ease(amount),
        )

    else:
        amount = second - 6.0

        image = _preview("03_hook_liquidity")

        if int(amount * 4) % 2 == 0:
            overlay = Image.new(
                "RGBA",
                image.size,
                (
                    229,
                    57,
                    53,
                    18,
                ),
            )

            image = Image.alpha_composite(
                image,
                overlay,
            )

    draw = ImageDraw.Draw(image)

    _rounded_panel(
        draw,
        (
            280,
            790,
            800,
            862,
        ),
        fill=(
            9,
            21,
            38,
            225,
        ),
    )

    _centered_text(
        draw,
        y=805,
        text="4 STRATEGIES · 10,000 GAMES",
        font=_font(
            30,
            bold=True,
        ),
        fill=GOLD,
    )

    return image


def _strategy_intro(
    state: FrameState,
) -> Image.Image:
    image = _preview("04_strategy_gameplay")

    progress = state.segment_progress

    draw = ImageDraw.Draw(image)

    entries = (
        (
            "collector",
            "BUY BROADLY",
        ),
        (
            "specialist",
            "SPECIALIZE",
        ),
        (
            "cash_protector",
            "PROTECT LIQUIDITY",
        ),
        (
            "aggressive_builder",
            "BUILD FAST",
        ),
    )

    reveal_count = min(
        4,
        int(progress * 4.7) + 1,
    )

    y_positions = (
        560,
        650,
        740,
        830,
    )

    for index, (
        strategy,
        subtitle,
    ) in enumerate(entries):
        if index >= reveal_count:
            continue

        local = min(
            1.0,
            max(
                0.0,
                progress * 4.0 - index,
            ),
        )

        local = _ease(local)

        x = int(-360 + 450 * local)

        y = y_positions[index]

        piece = _piece_image(
            strategy,
            size=110,
        )

        _paste_centered(
            image,
            piece,
            x=x + 100,
            y=y,
        )

        draw.text(
            (
                x + 165,
                y - 26,
            ),
            DISPLAY_NAMES[strategy],
            font=_font(
                23,
                bold=True,
            ),
            fill=WHITE,
        )

        draw.text(
            (
                x + 165,
                y + 5,
            ),
            subtitle,
            font=_font(
                17,
                bold=True,
            ),
            fill=ACCENTS[strategy],
        )

    return image


def _event_display(
    event_type: str,
) -> str:
    text = (
        event_type.replace(
            "_",
            " ",
        )
        .replace(
            "-",
            " ",
        )
        .strip()
    )

    return text.upper() if text else "GAME EVENT"


def _event_badge(
    event: ReplayEvent,
) -> (
    tuple[
        str,
        tuple[
            int,
            int,
            int,
        ],
    ]
    | None
):
    lowered = event.raw_type.lower()

    if "bankrupt" in lowered:
        return (
            "BANKRUPTCY",
            DANGER,
        )

    if "rent" in lowered:
        return (
            "RENT TRANSFER",
            WARNING,
        )

    if "purchase" in lowered or "buy" in lowered or "acquire" in lowered:
        return (
            "PROPERTY ACQUIRED",
            GOLD,
        )

    if "house" in lowered or "build" in lowered or "develop" in lowered:
        return (
            "DEVELOPMENT",
            POSITIVE,
        )

    if "monopoly" in lowered or "group_complete" in lowered or "group complete" in lowered:
        return (
            "GROUP COMPLETED",
            GOLD,
        )

    if "go" in lowered and "pass" in lowered:
        return (
            "PASSED START · +$200",
            POSITIVE,
        )

    return None


def _representative_game(
    state: FrameState,
    inputs: RuntimeInputs,
) -> Image.Image:
    image = _clean_board_backplate().copy()

    replay = inputs.replay

    progress = state.segment_progress

    event_float = progress * (len(replay.events) - 1)

    event_index = min(
        len(replay.events) - 1,
        int(event_float),
    )

    event_fraction = event_float - event_index

    event = replay.events[event_index]

    snapshot = replay.snapshots[event_index]

    draw = ImageDraw.Draw(image)

    # Top replay title.
    _rounded_panel(
        draw,
        (
            100,
            42,
            980,
            132,
        ),
    )

    _centered_text(
        draw,
        y=58,
        text="REAL REPRESENTATIVE GAME",
        font=_font(
            28,
            bold=True,
        ),
        fill=WHITE,
    )

    _centered_text(
        draw,
        y=95,
        text=(f"Event {event_index + 1:,} of {len(replay.events):,}"),
        font=_font(
            16,
            bold=True,
        ),
        fill=MUTED,
    )

    # All four current token positions.
    for strategy in STRATEGIES:
        board_index = snapshot.positions.get(
            strategy,
            0,
        )

        x, y = _board_pixel(
            board_index,
            inputs.board_positions_xy,
        )

        size = 132

        if strategy == event.strategy_id:
            size = 156

        piece = _piece_image(
            strategy,
            size=size,
        )

        # Current mover gets actual lift/carry/drop animation.
        if (
            strategy == event.strategy_id
            and event.from_position is not None
            and event.to_position is not None
            and event.from_position != event.to_position
        ):
            start = _board_pixel(
                event.from_position,
                inputs.board_positions_xy,
            )

            end = _board_pixel(
                event.to_position,
                inputs.board_positions_xy,
            )

            x, y, lift = _lift_carry_drop(
                start,
                end,
                event_fraction,
            )

            # Tiny scale-up during lift makes the piece appear physically
            # closer to the camera.
            lifted_size = int(size * (1.0 + lift / 820.0))

            piece = _piece_image(
                strategy,
                size=lifted_size,
            )

        _paste_centered(
            image,
            piece,
            x=x,
            y=y,
        )

    # Dice.
    if event.die_1 is not None and event.die_2 is not None:
        roll_phase = event_fraction * math.pi * 3.0

        die_1 = _die(
            event.die_1,
            size=88,
            angle=(math.sin(roll_phase) * 11),
        )

        die_2 = _die(
            event.die_2,
            size=88,
            angle=(math.cos(roll_phase) * 11),
        )

        _paste_centered(
            image,
            die_1,
            x=465,
            y=450,
        )

        _paste_centered(
            image,
            die_2,
            x=580,
            y=450,
        )

    # Event HUD.
    _rounded_panel(
        draw,
        (
            110,
            760,
            970,
            1005,
        ),
    )

    actor = DISPLAY_NAMES[event.strategy_id] if event.strategy_id is not None else "GAME"

    draw.text(
        (
            150,
            795,
        ),
        actor,
        font=_font(
            26,
            bold=True,
        ),
        fill=(ACCENTS[event.strategy_id] if event.strategy_id is not None else WHITE),
    )

    draw.text(
        (
            150,
            838,
        ),
        _event_display(event.raw_type)[:56],
        font=_font(
            20,
            bold=True,
        ),
        fill=WHITE,
    )

    badge = _event_badge(event)

    if badge is not None:
        label, color = badge

        draw.rounded_rectangle(
            (
                620,
                785,
                925,
                837,
            ),
            radius=16,
            fill=(
                color[0],
                color[1],
                color[2],
                230,
            ),
        )

        bbox = draw.textbbox(
            (
                0,
                0,
            ),
            label,
            font=_font(
                16,
                bold=True,
            ),
        )

        width = bbox[2] - bbox[0]

        draw.text(
            (
                772 - width / 2,
                801,
            ),
            label,
            font=_font(
                16,
                bold=True,
            ),
            fill=(
                10,
                15,
                22,
            ),
        )

    # 8.21 — actual cash balances.
    x_positions = (
        155,
        365,
        575,
        785,
    )

    for strategy, x in zip(
        STRATEGIES,
        x_positions,
        strict=True,
    ):
        balance = snapshot.cash.get(
            strategy,
            1500.0,
        )

        color = DANGER if balance < 200 else (WARNING if balance < 400 else WHITE)

        draw.text(
            (
                x,
                915,
            ),
            DISPLAY_NAMES[strategy],
            font=_font(
                13,
                bold=True,
            ),
            fill=MUTED,
        )

        draw.text(
            (
                x,
                940,
            ),
            f"${balance:,.0f}",
            font=_font(
                21,
                bold=True,
            ),
            fill=color,
        )

        # 8.22 — liquidity warning.
        if balance < 250:
            draw.ellipse(
                (
                    x + 117,
                    936,
                    x + 147,
                    966,
                ),
                fill=WARNING,
            )

            draw.text(
                (
                    x + 127,
                    938,
                ),
                "!",
                font=_font(
                    18,
                    bold=True,
                ),
                fill=(
                    15,
                    20,
                    28,
                ),
            )

    return image


def _simulation_scale(
    state: FrameState,
) -> Image.Image:
    progress = state.segment_progress

    if progress < 0.58:
        image = _preview("08_scale")
    else:
        local = (progress - 0.58) / 0.42

        image = _blend(
            _preview("08_scale"),
            _preview("09_counter"),
            _ease(local),
        )

    draw = ImageDraw.Draw(image)

    # Exponential-feeling counter acceleration.
    scaled = _ease(progress) ** 1.65

    games = min(
        10_000,
        round(10_000 * scaled),
    )

    if progress > 0.92:
        games = 10_000

    _rounded_panel(
        draw,
        (
            305,
            780,
            775,
            935,
        ),
        fill=(
            7,
            16,
            29,
            238,
        ),
    )

    _centered_text(
        draw,
        y=802,
        text=f"{games:,}",
        font=_font(
            62,
            bold=True,
        ),
        fill=GOLD,
        stroke_width=2,
    )

    _centered_text(
        draw,
        y=875,
        text="GAMES",
        font=_font(
            21,
            bold=True,
        ),
        fill=MUTED,
    )

    if progress > 0.58:
        _centered_text(
            draw,
            y=956,
            text=("One game is a story. 10,000 games are evidence."),
            font=_font(
                20,
                bold=True,
            ),
            fill=WHITE,
        )

    return image


def _leaderboard(
    state: FrameState,
    inputs: RuntimeInputs,
) -> Image.Image:
    image = _preview("10_leaderboard")

    progress = state.segment_progress

    ranking_rows = ranking(inputs.context)

    draw = ImageDraw.Draw(image)

    # Dark masks progressively uncover rows to create convergence.
    row_tops = (
        340,
        470,
        600,
        730,
    )

    reveal = min(
        4,
        int(progress * 4.7) + 1,
    )

    for index, top in enumerate(row_tops):
        if index < reveal:
            continue

        draw.rectangle(
            (
                55,
                top,
                1025,
                top + 118,
            ),
            fill=(
                7,
                16,
                29,
                235,
            ),
        )

    # At the end explicitly reinforce actual values.
    if progress > 0.72:
        leader = ranking_rows[0]

        _rounded_panel(
            draw,
            (
                260,
                865,
                820,
                955,
            ),
            fill=(
                9,
                21,
                38,
                242,
            ),
        )

        _centered_text(
            draw,
            y=884,
            text=(
                f"NUMERICAL LEADER · {DISPLAY_NAMES[leader.strategy_id]} · {leader.win_rate:.1%}"
            ),
            font=_font(
                20,
                bold=True,
            ),
            fill=GOLD,
        )

    return image


def _risk_reward(
    state: FrameState,
    inputs: RuntimeInputs,
) -> Image.Image:
    image = _preview("11_risk_reward")

    draw = ImageDraw.Draw(image)

    safest = lowest_bankruptcy(inputs.context)

    richest = highest_median_cash(inputs.context)

    progress = state.segment_progress

    if progress > 0.18:
        _rounded_panel(
            draw,
            (
                95,
                825,
                505,
                965,
            ),
        )

        draw.text(
            (
                125,
                850,
            ),
            "LOWEST BANKRUPTCY",
            font=_font(
                16,
                bold=True,
            ),
            fill=MUTED,
        )

        draw.text(
            (
                125,
                890,
            ),
            DISPLAY_NAMES[safest.strategy_id],
            font=_font(
                24,
                bold=True,
            ),
            fill=ACCENTS[safest.strategy_id],
        )

        draw.text(
            (
                125,
                925,
            ),
            f"{safest.bankruptcy_rate:.1%}",
            font=_font(
                23,
                bold=True,
            ),
            fill=WHITE,
        )

    if progress > 0.48:
        _rounded_panel(
            draw,
            (
                575,
                825,
                985,
                965,
            ),
        )

        draw.text(
            (
                605,
                850,
            ),
            "HIGHEST MEDIAN CASH",
            font=_font(
                16,
                bold=True,
            ),
            fill=MUTED,
        )

        draw.text(
            (
                605,
                890,
            ),
            DISPLAY_NAMES[richest.strategy_id],
            font=_font(
                24,
                bold=True,
            ),
            fill=ACCENTS[richest.strategy_id],
        )

        draw.text(
            (
                605,
                925,
            ),
            (f"${richest.median_finishing_cash:,.0f}"),
            font=_font(
                23,
                bold=True,
            ),
            fill=GOLD,
        )

    return image


def _winner_reveal(
    state: FrameState,
    inputs: RuntimeInputs,
) -> Image.Image:
    progress = state.segment_progress

    image = _blend(
        _preview("12_result"),
        _preview("13_footer"),
        _ease(
            max(
                0.0,
                (progress - 0.66) / 0.34,
            )
        ),
    )

    draw = ImageDraw.Draw(image)

    supported = headline_winner(inputs.context)

    leader = numerical_leader(inputs.context)

    if progress < 0.66:
        if supported is None:
            title = "NO SINGLE STATISTICALLY SUPPORTED WINNER"

            subtitle = (
                f"Numerical leader: {DISPLAY_NAMES[leader.strategy_id]} ({leader.win_rate:.1%})"
            )

            piece_strategy = leader.strategy_id

        else:
            title = DISPLAY_NAMES[supported].upper()

            winner_metric = next(
                metric for metric in inputs.context.strategies if metric.strategy_id == supported
            )

            subtitle = f"Supported winner · {winner_metric.win_rate:.1%} win rate"

            piece_strategy = supported

        # Large accepted metallic token.
        piece = _piece_image(
            piece_strategy,
            size=260,
        )

        _paste_centered(
            image,
            piece,
            x=540,
            y=585,
        )

        _rounded_panel(
            draw,
            (
                120,
                790,
                960,
                975,
            ),
        )

        _centered_text(
            draw,
            y=815,
            text=title,
            font=_font(
                28,
                bold=True,
            ),
            fill=GOLD,
            stroke_width=1,
        )

        _centered_text(
            draw,
            y=861,
            text=subtitle,
            font=_font(
                19,
                bold=True,
            ),
            fill=WHITE,
        )

        takeaway = takeaway_sentence(inputs.context)

        # Wrap deterministic takeaway.
        words = takeaway.split()

        lines: list[str] = []
        current = ""

        for word in words:
            candidate = word if not current else (current + " " + word)

            if len(candidate) <= 67:
                current = candidate
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        for index, line in enumerate(lines[:2]):
            _centered_text(
                draw,
                y=905 + index * 27,
                text=line,
                font=_font(
                    15,
                    bold=True,
                ),
                fill=MUTED,
            )

    return image


# ============================================================================
# 8.3-8.43 - COMPLETE FRAME RENDERER
# ============================================================================


def render_frame(
    frame_index: int,
    inputs: RuntimeInputs,
) -> Image.Image:
    state = frame_state(frame_index)

    if state.segment_key == "opening_hook":
        image = _opening_hook(state)

    elif state.segment_key == "strategy_introduction":
        image = _strategy_intro(state)

    elif state.segment_key == "representative_game":
        image = _representative_game(
            state,
            inputs,
        )

    elif state.segment_key == "simulation_scale":
        image = _simulation_scale(state)

    elif state.segment_key == "leaderboard":
        image = _leaderboard(
            state,
            inputs,
        )

    elif state.segment_key == "risk_reward":
        image = _risk_reward(
            state,
            inputs,
        )

    elif state.segment_key == "winner_reveal":
        image = _winner_reveal(
            state,
            inputs,
        )

    else:
        raise RuntimeError(state.segment_key)

    if image.size != (
        WIDTH,
        HEIGHT,
    ):
        image = image.resize(
            (
                WIDTH,
                HEIGHT,
            ),
            Image.Resampling.LANCZOS,
        )

    return image.convert("RGB")


# ============================================================================
# 8.44-8.45 - REPRESENTATIVE FRAMES / HASHES
# ============================================================================


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def render_representative_frames(
    *,
    clean: bool = True,
) -> dict[
    int,
    str,
]:
    if clean and REPRESENTATIVE_FRAME_ROOT.exists():
        shutil.rmtree(REPRESENTATIVE_FRAME_ROOT)

    REPRESENTATIVE_FRAME_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    inputs = load_runtime_inputs()

    hashes: dict[
        int,
        str,
    ] = {}

    total = len(REPRESENTATIVE_FRAME_INDICES)

    for index, frame_index in enumerate(
        REPRESENTATIVE_FRAME_INDICES,
        start=1,
    ):
        print(
            f"[KEYFRAME] {index}/{total} frame={frame_index:04d} t={frame_index / FPS:05.2f}s",
            flush=True,
        )

        image = render_frame(
            frame_index,
            inputs,
        )

        path = REPRESENTATIVE_FRAME_ROOT / f"frame_{frame_index:04d}.png"

        image.save(
            path,
            format="PNG",
            compress_level=4,
        )

        hashes[frame_index] = sha256_file(path)

    manifest = {
        "schema_version": "1.0",
        "frame_count": len(hashes),
        "frames": [
            {
                "frame_index": frame_index,
                "second": (frame_index / FPS),
                "sha256": digest,
            }
            for frame_index, digest in hashes.items()
        ],
    }

    (REPRESENTATIVE_FRAME_ROOT / "representative_frame_manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return hashes


# ============================================================================
# 8.46 — 1,800-FRAME PIPELINE
# ============================================================================


def render_all_frames(
    *,
    clean: bool = True,
) -> None:
    if clean and FRAME_ROOT.exists():
        shutil.rmtree(FRAME_ROOT)

    FRAME_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    inputs = load_runtime_inputs()

    for frame_index in range(FRAME_COUNT):
        if frame_index % FPS == 0:
            print(
                f"[FRAME] "
                f"{frame_index + 1:04d}/{FRAME_COUNT} "
                f"({100.0 * frame_index / FRAME_COUNT:5.1f}%) "
                f"t={frame_index / FPS:05.1f}s",
                flush=True,
            )

        image = render_frame(
            frame_index,
            inputs,
        )

        path = FRAME_ROOT / f"frame_{frame_index:04d}.png"

        image.save(
            path,
            format="PNG",
            compress_level=1,
        )

    print(
        f"[FRAME] {FRAME_COUNT}/{FRAME_COUNT} (100.0%) t={DURATION_SECONDS:.1f}s",
        flush=True,
    )


# ============================================================================
# 8.47 — FFMPEG
# ============================================================================


def encode_video() -> Path:
    CANONICAL_VIDEO_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    if CANONICAL_MP4.exists():
        CANONICAL_MP4.unlink()

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-framerate",
        str(FPS),
        "-start_number",
        "0",
        "-i",
        str(FRAME_ROOT / "frame_%04d.png"),
        "-frames:v",
        str(FRAME_COUNT),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        PIXEL_FORMAT,
        "-r",
        str(FPS),
        "-movflags",
        "+faststart",
        str(CANONICAL_MP4),
    ]

    print(
        "[FFMPEG] encoding canonical MP4",
        flush=True,
    )

    subprocess.run(
        command,
        check=True,
    )

    if not CANONICAL_MP4.is_file():
        raise RuntimeError("FFmpeg did not create canonical MP4")

    return CANONICAL_MP4


# ============================================================================
# 8.48-8.54 - FFPROBE
# ============================================================================


def probe_video(
    path: Path = CANONICAL_MP4,
) -> Mapping[str, Any]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-count_frames",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]

    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)

    if not isinstance(
        payload,
        Mapping,
    ):
        raise ValueError("invalid ffprobe payload")

    return payload


def _video_stream(
    probe: Mapping[str, Any],
) -> Mapping[str, Any]:
    streams = probe.get("streams")

    if not isinstance(
        streams,
        list,
    ):
        raise ValueError("ffprobe streams missing")

    for stream in streams:
        if (
            isinstance(
                stream,
                Mapping,
            )
            and stream.get("codec_type") == "video"
        ):
            return stream

    raise ValueError("video stream missing")


def validate_video_probe(
    probe: Mapping[str, Any],
) -> None:
    stream = _video_stream(probe)

    assert int(stream["width"]) == WIDTH

    assert int(stream["height"]) == HEIGHT

    assert stream["codec_name"] == VIDEO_CODEC

    assert stream["pix_fmt"] == PIXEL_FORMAT

    rate = str(
        stream.get(
            "avg_frame_rate",
            "",
        )
    )

    numerator, denominator = rate.split("/")

    fps = float(numerator) / float(denominator)

    assert abs(fps - FPS) < 1e-9

    frame_count_raw = stream.get("nb_read_frames") or stream.get("nb_frames")

    assert frame_count_raw is not None

    assert int(frame_count_raw) == FRAME_COUNT

    format_payload = probe.get("format")

    if not isinstance(
        format_payload,
        Mapping,
    ):
        raise ValueError("ffprobe format missing")

    duration = float(format_payload["duration"])

    assert abs(duration - DURATION_SECONDS) <= 0.001


# ============================================================================
# 8.55-8.58 - VIDEO MANIFEST
# ============================================================================


def _artifact_hashes() -> dict[
    str,
    str,
]:
    paths = (
        TOURNAMENT_SUMMARY_PATH,
        REPRESENTATIVE_GAME_PATH,
        REPRESENTATIVE_EVENTS_PATH,
        VALIDATION_ROOT / "canonical_video_freeze.json",
        VALIDATION_ROOT / "visual_v6_freeze.json",
    )

    result: dict[
        str,
        str,
    ] = {}

    for path in paths:
        if path.is_file():
            result[str(path)] = sha256_file(path)

    return result


def build_video_manifest(
    probe: Mapping[str, Any],
) -> Mapping[str, Any]:
    inputs = load_runtime_inputs()

    stream = _video_stream(probe)

    leader = numerical_leader(inputs.context)

    supported = headline_winner(inputs.context)

    safest = lowest_bankruptcy(inputs.context)

    richest = highest_median_cash(inputs.context)

    strategy_metrics = {
        metric.strategy_id: {
            "win_rate": metric.win_rate,
            "bankruptcy_rate": metric.bankruptcy_rate,
            "median_finishing_cash": (metric.median_finishing_cash),
            "ci_lower": metric.ci_lower,
            "ci_upper": metric.ci_upper,
        }
        for metric in inputs.context.strategies
    }

    manifest: dict[
        str,
        Any,
    ] = {
        "schema_version": "1.0",
        "project": "p02_monopoly_ai",
        "width": WIDTH,
        "height": HEIGHT,
        "fps": FPS,
        "frame_count": FRAME_COUNT,
        "duration_seconds": DURATION_SECONDS,
        "codec": stream["codec_name"],
        "pixel_format": stream["pix_fmt"],
        "master_seed": MASTER_SEED,
        "game_count": inputs.context.game_count,
        "representative_game_event_count": len(inputs.replay.events),
        "numerical_leader": (leader.strategy_id),
        "headline_winner": supported,
        "lowest_bankruptcy_strategy": (safest.strategy_id),
        "highest_median_cash_strategy": (richest.strategy_id),
        "takeaway": takeaway_sentence(inputs.context),
        "strategy_metrics": strategy_metrics,
        "source_artifacts": _artifact_hashes(),
        "video_sha256": sha256_file(CANONICAL_MP4),
    }

    VIDEO_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    VIDEO_MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return manifest


def validate_manifest(
    manifest: Mapping[str, Any],
) -> None:
    inputs = load_runtime_inputs()

    assert manifest["width"] == WIDTH

    assert manifest["height"] == HEIGHT

    assert manifest["fps"] == FPS

    assert manifest["frame_count"] == FRAME_COUNT

    assert manifest["duration_seconds"] == DURATION_SECONDS

    assert manifest["game_count"] == inputs.context.game_count

    assert manifest["game_count"] == 10_000

    assert manifest["headline_winner"] == headline_winner(inputs.context)

    expected_metrics = {
        metric.strategy_id: {
            "win_rate": metric.win_rate,
            "bankruptcy_rate": metric.bankruptcy_rate,
            "median_finishing_cash": (metric.median_finishing_cash),
            "ci_lower": metric.ci_lower,
            "ci_upper": metric.ci_upper,
        }
        for metric in inputs.context.strategies
    }

    assert manifest["strategy_metrics"] == expected_metrics


# ============================================================================
# 8.60 — ACCEPTANCE
# ============================================================================


def acceptance_gate() -> None:
    assert len(TIMELINE) == 7

    assert TIMELINE[0].start_frame == 0

    assert TIMELINE[-1].end_frame == FRAME_COUNT

    assert sum(segment.frame_count for segment in TIMELINE) == FRAME_COUNT

    frame_files = sorted(FRAME_ROOT.glob("frame_*.png"))

    assert len(frame_files) == FRAME_COUNT

    assert CANONICAL_MP4.is_file()

    probe = probe_video(CANONICAL_MP4)

    validate_video_probe(probe)

    manifest = build_video_manifest(probe)

    validate_manifest(manifest)
