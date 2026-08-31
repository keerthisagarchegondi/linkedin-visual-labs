"""V4 cinematic 60-second Project 3 video."""

from __future__ import annotations

import hashlib
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import (
    Image,
    ImageDraw,
)

from linkedin_visual_labs.projects.p02_monopoly_ai.video_board import (
    ACCENTS,
    BACKGROUND,
    GOLD,
    MUTED,
    WHITE,
    font,
    paste_center,
    piece_asset,
    render_turn,
    text_center,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_board import (
    HEIGHT as BOARD_HEIGHT,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_board import (
    WIDTH as BOARD_WIDTH,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_replay import (
    DISPLAY_NAMES,
    TurnBeat,
    load_replay,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_story import (
    StoryPlan,
    build_story_plan,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
    load_preview_context,
)

WIDTH = BOARD_WIDTH
HEIGHT = BOARD_HEIGHT

FPS = 30
FRAME_COUNT = 1800
DURATION_SECONDS = 60

ROOT = Path("outputs/p02_monopoly_ai")

VIDEO_ROOT = ROOT / "video_v4"

FRAME_ROOT = VIDEO_ROOT / "frames"

PREVIEW_ROOT = VIDEO_ROOT / "representative_frames"

CANONICAL_ROOT = VIDEO_ROOT / "canonical"

CANONICAL_MP4 = CANONICAL_ROOT / "p02_monopoly_ai_60s_v4.mp4"


@dataclass(frozen=True)
class Segment:
    name: str
    start: int
    end: int


TIMELINE = (
    Segment(
        "opening",
        0,
        210,
    ),
    Segment(
        "strategies",
        210,
        420,
    ),
    Segment(
        "gameplay",
        420,
        930,
    ),
    Segment(
        "scale",
        930,
        1170,
    ),
    Segment(
        "leaderboard",
        1170,
        1500,
    ),
    Segment(
        "risk",
        1500,
        1650,
    ),
    Segment(
        "result",
        1650,
        1800,
    ),
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
class Runtime:
    turns: tuple[
        TurnBeat,
        ...,
    ]
    story: StoryPlan
    metrics: tuple[
        StrategyMetric,
        ...,
    ]
    headline_winner: str | None


def load_runtime() -> Runtime:
    _, turns, _ = load_replay()

    context = load_preview_context(validation_directory=(ROOT / "validation"))

    if context.game_count != 10_000:
        raise RuntimeError("Expected validated 10,000-game context.")

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

    raw_winner = getattr(
        context,
        "headline_winner",
        None,
    )

    return Runtime(
        turns=turns,
        story=build_story_plan(turns),
        metrics=metrics,
        headline_winner=(str(raw_winner) if raw_winner is not None else None),
    )


def ranking(
    runtime: Runtime,
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


def segment(
    frame: int,
) -> tuple[
    Segment,
    float,
]:
    for item in TIMELINE:
        if item.start <= frame < item.end:
            return (
                item,
                (frame - item.start) / (item.end - item.start),
            )

    raise ValueError(frame)


def render_opening(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    story = runtime.story

    second = min(
        6,
        int(progress * 7),
    )

    local = progress * 7 - second

    if second == 0:
        return render_turn(
            story.dice_turn,
            local * 0.19,
            headline="THE DICE HIT.",
            subline=("Four autonomous landlords. One deterministic board."),
            show_card=False,
        )

    if second == 1:
        return render_turn(
            story.move_turn,
            (0.18 + local * 0.49),
            headline="THE RACE BEGINS.",
            subline=("Pieces travel square by square."),
            show_card=False,
        )

    if second == 2:
        return render_turn(
            story.purchase_turn,
            (0.69 + local * 0.31),
            headline="PROPERTY CHANGES HANDS.",
            subline=("Ownership remains visible after the card disappears."),
        )

    if second == 3:
        return render_turn(
            story.build_turn,
            (0.69 + local * 0.31),
            headline="A HOUSE GOES UP.",
            subline=("Development changes the board."),
        )

    if second == 4:
        return render_turn(
            story.rent_turn,
            (0.69 + local * 0.31),
            headline="THEN THE RENT HITS.",
            subline=("Cash transfers change the next decision."),
        )

    if second == 5:
        return render_turn(
            story.shock_turn,
            (0.74 + local * 0.26),
            headline="CASH CAN COLLAPSE FAST.",
            subline=("Liquidity matters as much as expansion."),
        )

    return render_turn(
        story.survival_turn,
        1.0,
        headline="",
        show_question=True,
    )


STRATEGY_COPY = {
    "collector": (
        "COLLECTOR — BUY BROADLY",
        "Keeps acquiring when opportunities appear.",
    ),
    "specialist": (
        "SPECIALIST — COMPLETE GROUPS",
        "Concentrates capital around controlled sets.",
    ),
    "cash_protector": (
        "CASH PROTECTOR — HOLD RESERVES",
        "Preserves liquidity before expansion.",
    ),
    "aggressive_builder": (
        "AGGRESSIVE BUILDER — BUILD FAST",
        "Turns control into development quickly.",
    ),
}


def render_strategies(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    turns = runtime.story.strategy_turns

    scaled = progress * 4

    index = min(
        3,
        math.floor(scaled),
    )

    local = scaled - index

    turn = turns[index]

    headline, subline = STRATEGY_COPY[turn.strategy_id]

    return render_turn(
        turn,
        (0.10 + local * 0.70),
        headline=headline,
        subline=subline,
        show_card=False,
    )


def render_gameplay(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    turns = runtime.story.narrative_turns

    scaled = progress * len(turns)

    index = min(
        len(turns) - 1,
        math.floor(scaled),
    )

    local = scaled - index

    turn = turns[index]

    headline = {
        "PURCHASE": "ACQUISITION",
        "GROUP_COMPLETE": "GROUP COMPLETE",
        "BUILD": "CAPITAL → DEVELOPMENT",
        "RENT": "RENT PRESSURE",
        "BANKRUPTCY": "SURVIVAL TEST",
        "PASS_START": "LIQUIDITY RESET",
    }.get(
        turn.primary_action,
        ("TURN " + str(turn.turn_number)),
    )

    return render_turn(
        turn,
        local,
        headline=headline,
        subline=(
            DISPLAY_NAMES[turn.strategy_id]
            + " • "
            + turn.primary_action.replace(
                "_",
                " ",
            ).title()
        ),
    )


def dark_canvas() -> Image.Image:
    return Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BACKGROUND,
    )


def render_scale(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    base = render_turn(
        runtime.story.narrative_turns[-1],
        1.0,
        headline="REPRESENTATIVE GAME",
        show_card=False,
    )

    canvas = dark_canvas()

    draw = ImageDraw.Draw(canvas)

    text_center(
        draw,
        "ONE GAME IS A STORY.",
        center_x=540,
        y=45,
        size=34,
        fill=WHITE,
    )

    text_center(
        draw,
        "10,000 games are evidence.",
        center_x=540,
        y=91,
        size=16,
        fill=MUTED,
        bold=False,
    )

    if progress < 0.20:
        grid = 1
    elif progress < 0.42:
        grid = 2
    elif progress < 0.65:
        grid = 3
    else:
        grid = 5

    available = 850
    gap = 7

    size = (available - gap * (grid - 1)) // grid

    mini = base.resize(
        (
            size,
            size,
        ),
        Image.Resampling.LANCZOS,
    )

    total = size * grid + gap * (grid - 1)

    left = (WIDTH - total) // 2

    top = 137

    for row in range(grid):
        for column in range(grid):
            canvas.paste(
                mini,
                (
                    left + column * (size + gap),
                    top + row * (size + gap),
                ),
            )

    count = round(10_000 * (progress**1.7))

    if progress > 0.96:
        count = 10_000

    draw.rectangle(
        (
            322,
            888,
            758,
            1024,
        ),
        fill=(
            4,
            10,
            18,
        ),
        outline=(
            67,
            79,
            97,
        ),
        width=2,
    )

    text_center(
        draw,
        "SIMULATIONS RUNNING",
        center_x=540,
        y=910,
        size=14,
        fill=MUTED,
    )

    text_center(
        draw,
        f"{count:,}",
        center_x=540,
        y=944,
        size=47,
        fill=GOLD,
    )

    return canvas


def density_points(
    *,
    mean: float,
    low: float,
    high: float,
    left: float,
    right: float,
    baseline: float,
    height: float,
    scale_low: float,
    scale_high: float,
) -> list[
    tuple[
        float,
        float,
    ]
]:
    sigma = max(
        (high - low) / 3.92,
        1e-5,
    )

    result = []

    for index in range(101):
        value = scale_low + (scale_high - scale_low) * index / 100

        x = left + (value - scale_low) / (scale_high - scale_low) * (right - left)

        density = math.exp(-0.5 * ((value - mean) / sigma) ** 2)

        y = baseline - density * height

        result.append(
            (
                x,
                y,
            )
        )

    return result


def render_leaderboard(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    canvas = dark_canvas()

    draw = ImageDraw.Draw(canvas)

    text_center(
        draw,
        "WHO WON MOST OFTEN?",
        center_x=540,
        y=52,
        size=38,
    )

    text_center(
        draw,
        "WIN RATE WITH 95% WILSON CONFIDENCE INTERVAL",
        center_x=540,
        y=105,
        size=14,
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

    chart_left = 430.0
    chart_right = 900.0

    for index, metric in enumerate(rows):
        row_progress = max(
            0.0,
            min(
                1.0,
                (progress - index * 0.10) / 0.52,
            ),
        )

        y = 275 + index * 168

        paste_center(
            canvas.convert("RGBA"),
            piece_asset(
                metric.strategy_id,
                68,
            ),
            122,
            y,
        )

        draw.text(
            (
                165,
                y - 23,
            ),
            DISPLAY_NAMES[metric.strategy_id],
            font=font(
                21,
                True,
            ),
            fill=ACCENTS[metric.strategy_id],
        )

        draw.text(
            (
                165,
                y + 17,
            ),
            f"{metric.win_rate:.1%}",
            font=font(
                25,
                True,
            ),
            fill=WHITE,
        )

        baseline = y + 39

        points = density_points(
            mean=metric.win_rate,
            low=metric.ci_lower,
            high=metric.ci_upper,
            left=chart_left,
            right=chart_right,
            baseline=baseline,
            height=55,
            scale_low=scale_low,
            scale_high=scale_high,
        )

        visible_count = max(
            2,
            round(len(points) * row_progress),
        )

        draw.line(
            points[:visible_count],
            fill=ACCENTS[metric.strategy_id],
            width=3,
        )

        def x_value(
            value: float,
            *,
            minimum: float = scale_low,
            maximum: float = scale_high,
            left: float = chart_left,
            right: float = chart_right,
        ) -> float:
            return left + (value - minimum) / (maximum - minimum) * (right - left)

        center = x_value(metric.win_rate)

        low = x_value(metric.ci_lower)

        high = x_value(metric.ci_upper)

        animated_low = center + (low - center) * row_progress

        animated_high = center + (high - center) * row_progress

        draw.line(
            (
                animated_low,
                baseline + 17,
                animated_high,
                baseline + 17,
            ),
            fill=WHITE,
            width=3,
        )

        draw.line(
            (
                animated_low,
                baseline + 10,
                animated_low,
                baseline + 24,
            ),
            fill=WHITE,
            width=2,
        )

        draw.line(
            (
                animated_high,
                baseline + 10,
                animated_high,
                baseline + 24,
            ),
            fill=WHITE,
            width=2,
        )

        draw.line(
            (
                center,
                baseline - 53,
                center,
                baseline + 24,
            ),
            fill=(*ACCENTS[metric.strategy_id],),
            width=2,
        )

    text_center(
        draw,
        "Curves are decorative uncertainty profiles; endpoints are the Wilson interval.",
        center_x=540,
        y=1001,
        size=12,
        fill=MUTED,
        bold=False,
    )

    return canvas


def render_risk(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    canvas = dark_canvas()

    draw = ImageDraw.Draw(canvas)

    text_center(
        draw,
        "RISK / REWARD SNAPSHOT",
        center_x=540,
        y=56,
        size=36,
    )

    text_center(
        draw,
        "Winning • Bankruptcy • Cash remaining",
        center_x=540,
        y=108,
        size=15,
        fill=MUTED,
        bold=False,
    )

    rows = ranking(runtime)

    headers = (
        (
            "WIN RATE",
            430,
        ),
        (
            "BANKRUPTCY",
            655,
        ),
        (
            "MEDIAN CASH",
            875,
        ),
    )

    for title, x in headers:
        text_center(
            draw,
            title,
            center_x=x,
            y=190,
            size=13,
            fill=MUTED,
        )

    for index, metric in enumerate(rows):
        y = 300 + index * 155

        paste_center(
            canvas.convert("RGBA"),
            piece_asset(
                metric.strategy_id,
                62,
            ),
            100,
            y,
        )

        draw.text(
            (
                143,
                y - 15,
            ),
            DISPLAY_NAMES[metric.strategy_id],
            font=font(
                18,
                True,
            ),
            fill=ACCENTS[metric.strategy_id],
        )

        win_width = 150 * metric.win_rate / max(item.win_rate for item in rows) * progress

        bankruptcy_width = (
            150 * metric.bankruptcy_rate / max(item.bankruptcy_rate for item in rows) * progress
        )

        cash_width = (
            150
            * metric.median_finishing_cash
            / max(item.median_finishing_cash for item in rows)
            * progress
        )

        for left, width in (
            (
                355,
                win_width,
            ),
            (
                580,
                bankruptcy_width,
            ),
            (
                800,
                cash_width,
            ),
        ):
            draw.rounded_rectangle(
                (
                    left,
                    y - 13,
                    left + width,
                    y + 17,
                ),
                radius=6,
                fill=ACCENTS[metric.strategy_id],
            )

        draw.text(
            (
                510,
                y - 13,
            ),
            f"{metric.win_rate:.1%}",
            font=font(
                14,
                True,
            ),
            fill=WHITE,
        )

        draw.text(
            (
                735,
                y - 13,
            ),
            f"{metric.bankruptcy_rate:.1%}",
            font=font(
                14,
                True,
            ),
            fill=WHITE,
        )

        draw.text(
            (
                958,
                y - 13,
            ),
            f"${metric.median_finishing_cash:,.0f}",
            font=font(
                14,
                True,
            ),
            fill=WHITE,
            anchor="ra",
        )

    return canvas


def render_result(
    runtime: Runtime,
    progress: float,
) -> Image.Image:
    canvas = dark_canvas()

    draw = ImageDraw.Draw(canvas)

    leader = ranking(runtime)[0]

    winner = runtime.headline_winner or leader.strategy_id

    if progress < 0.64:
        text_center(
            draw,
            "THE RESULT",
            center_x=540,
            y=76,
            size=28,
            fill=MUTED,
        )

        rgba = canvas.convert("RGBA")

        paste_center(
            rgba,
            piece_asset(
                winner,
                235,
            ),
            540,
            375,
        )

        canvas = rgba.convert("RGB")

        draw = ImageDraw.Draw(canvas)

        if runtime.headline_winner is None:
            headline = "NO SINGLE STATISTICALLY SUPPORTED WINNER"

            detail = "Numerical leader: " + DISPLAY_NAMES[leader.strategy_id]

        else:
            headline = DISPLAY_NAMES[winner].upper() + " WINS MOST OFTEN"

            detail = "Statistically supported headline result"

        text_center(
            draw,
            headline,
            center_x=540,
            y=565,
            size=34,
            fill=GOLD,
        )

        text_center(
            draw,
            detail,
            center_x=540,
            y=626,
            size=17,
            fill=WHITE,
        )

        text_center(
            draw,
            "10,000 games • balanced seats • 95% Wilson CI",
            center_x=540,
            y=718,
            size=15,
            fill=MUTED,
            bold=False,
        )

    else:
        text_center(
            draw,
            "TECHNICAL PROOF",
            center_x=540,
            y=80,
            size=29,
            fill=WHITE,
        )

        proof_lines = (
            "10,000 deterministic games",
            "Master seed 73,031",
            "Balanced 2,500 games / strategy-seat",
            "Wilson CI + exact binomial + Holm correction",
        )

        for index, line in enumerate(proof_lines):
            y = 270 + index * 115

            draw.rounded_rectangle(
                (
                    160,
                    y - 25,
                    920,
                    y + 50,
                ),
                radius=16,
                fill=(
                    9,
                    20,
                    34,
                ),
                outline=(
                    58,
                    72,
                    92,
                ),
                width=2,
            )

            text_center(
                draw,
                line,
                center_x=540,
                y=y - 3,
                size=18,
                fill=WHITE,
            )

        text_center(
            draw,
            ("Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro."),
            center_x=540,
            y=997,
            size=12,
            fill=MUTED,
            bold=False,
        )

    return canvas


def render_frame(
    frame: int,
    runtime: Runtime,
) -> Image.Image:
    item, progress = segment(frame)

    if item.name == "opening":
        return render_opening(
            runtime,
            progress,
        )

    if item.name == "strategies":
        return render_strategies(
            runtime,
            progress,
        )

    if item.name == "gameplay":
        return render_gameplay(
            runtime,
            progress,
        )

    if item.name == "scale":
        return render_scale(
            runtime,
            progress,
        )

    if item.name == "leaderboard":
        return render_leaderboard(
            runtime,
            progress,
        )

    if item.name == "risk":
        return render_risk(
            runtime,
            progress,
        )

    return render_result(
        runtime,
        progress,
    )


def sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def render_frames() -> None:
    if FRAME_ROOT.exists():
        shutil.rmtree(FRAME_ROOT)

    FRAME_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    runtime = load_runtime()

    for frame in range(FRAME_COUNT):
        if frame % FPS == 0:
            print(
                f"[FRAME] {frame:04d}/1799 t={frame / FPS:05.1f}s",
                flush=True,
            )

        render_frame(
            frame,
            runtime,
        ).save(
            FRAME_ROOT / f"frame_{frame:04d}.png",
            compress_level=1,
        )


def encode() -> Path:
    CANONICAL_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-framerate",
            "30",
            "-start_number",
            "0",
            "-i",
            str(FRAME_ROOT / "frame_%04d.png"),
            "-frames:v",
            "1800",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "30",
            "-movflags",
            "+faststart",
            str(CANONICAL_MP4),
        ],
        check=True,
    )

    return CANONICAL_MP4
