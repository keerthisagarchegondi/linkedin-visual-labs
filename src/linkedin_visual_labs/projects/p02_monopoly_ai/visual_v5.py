"""Project 3 Step 7 V5 cinematic compositor.

V5 keeps the validated board/data contract from visual_system.py but
replaces pseudo-3D vector tokens with genuine deterministic 3D-rendered
sprites and introduces stricter responsive layout geometry.
"""

from __future__ import annotations

import hashlib
import json
import math
import textwrap
from functools import lru_cache
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy.typing as npt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.offsetbox import (
    AnnotationBbox,
    OffsetImage,
)
from matplotlib.patches import (
    FancyArrowPatch,
    FancyBboxPatch,
    Rectangle,
)

from linkedin_visual_labs.projects.p02_monopoly_ai.cinematic_storyboard import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    PREVIEW_MOMENTS,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.piece_assets_3d import (
    PIECE_NAMES,
    ensure_piece_assets,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
    DISCLAIMER,
    FRAME_DPI,
    GROUP_COLORS,
    THEME,
    BoardSpaceVisual,
    PreviewContext,
    StrategyMetric,
    board_positions,
    draw_board,
    draw_cash,
    draw_dice,
    draw_houses,
    draw_owner,
    draw_warning_badge,
)

# The intentionally odd BOARD import above must never execute; it is
# removed below by deterministic source cleanup before this module runs.


ASSET_DIRECTORY = Path("outputs/p02_monopoly_ai/visual/v6_3d_piece_assets")


@lru_cache(maxsize=16)
def _read_sprite(
    path: str,
) -> npt.NDArray[Any]:
    return mpimg.imread(path)


def _figure() -> tuple[
    Figure,
    Axes,
]:
    figure = plt.figure(
        figsize=(
            FRAME_WIDTH / FRAME_DPI,
            FRAME_HEIGHT / FRAME_DPI,
        ),
        dpi=FRAME_DPI,
        facecolor=(THEME.background),
    )

    axis = figure.add_axes(
        (
            0.0,
            0.0,
            1.0,
            1.0,
        )
    )

    axis.set_xlim(
        0.0,
        1.0,
    )

    axis.set_ylim(
        0.0,
        1.0,
    )

    axis.axis("off")

    return (
        figure,
        axis,
    )


def _text(
    axis: Axes,
    x: float,
    y: float,
    value: str,
    *,
    size: float,
    color: str | None = None,
    weight: str = "normal",
    ha: str = "left",
    outlined: bool = False,
    zorder: int = 100,
) -> None:
    artist = axis.text(
        x,
        y,
        value,
        fontsize=size,
        color=(color if color is not None else THEME.primary_text),
        fontfamily=(THEME.font_family),
        fontweight=weight,
        ha=ha,
        va="center",
        transform=(axis.transAxes),
        zorder=zorder,
    )

    if outlined:
        artist.set_path_effects(
            [
                path_effects.withStroke(
                    linewidth=3.0,
                    foreground="#000000",
                )
            ]
        )


def _panel(
    axis: Axes,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    zorder: int = 35,
) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (
                x,
                y,
            ),
            width,
            height,
            boxstyle=("round,pad=0.012,rounding_size=0.018"),
            facecolor="#091526",
            edgecolor="#405675",
            linewidth=1.5,
            transform=(axis.transAxes),
            zorder=zorder,
        )
    )


def _title_size(
    value: str,
) -> float:
    if len(value) <= 22:
        return 39.0

    if len(value) <= 30:
        return 34.0

    if len(value) <= 38:
        return 29.0

    return 26.0


def _headline(
    axis: Axes,
    title: str,
    subtitle: str,
) -> None:
    """Centered full-width headline contract."""

    _text(
        axis,
        0.50,
        0.952,
        title,
        size=_title_size(title),
        weight="bold",
        ha="center",
        outlined=True,
        zorder=120,
    )

    wrapped = textwrap.fill(
        subtitle,
        width=64,
    )

    subtitle_size = 18.0 if len(subtitle) <= 65 else 16.0

    _text(
        axis,
        0.50,
        0.900,
        wrapped,
        size=subtitle_size,
        color="#D4DCE8",
        weight="bold",
        ha="center",
        outlined=True,
        zorder=120,
    )


def draw_piece_3d(
    axis: Axes,
    strategy_id: str,
    position: tuple[
        float,
        float,
    ],
    *,
    zoom: float = 0.16,
    zorder: int = 75,
) -> None:
    """Composite actual 3D-rendered transparent piece sprite."""

    paths = ensure_piece_assets(ASSET_DIRECTORY)

    image = _read_sprite(str(paths[strategy_id]))

    image_box = OffsetImage(
        image,
        zoom=zoom,
    )

    annotation = AnnotationBbox(
        image_box,
        position,
        xycoords="axes fraction",
        frameon=False,
        pad=0.0,
        box_alignment=(
            0.5,
            0.5,
        ),
        zorder=zorder,
    )

    axis.add_artist(annotation)


def pickup_position(
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
    """Lift, carry and place a physical game piece.

    0.00-0.20:
        piece rises vertically from its current board space.

    0.20-0.80:
        piece travels above the board.

    0.80-1.00:
        piece lowers onto the destination.
    """

    progress = min(
        1.0,
        max(
            0.0,
            progress,
        ),
    )

    maximum_lift = 0.090

    if progress < 0.20:
        travel = 0.0

        lift = maximum_lift * (progress / 0.20)

    elif progress <= 0.80:
        travel = (progress - 0.20) / 0.60

        lift = maximum_lift

    else:
        travel = 1.0

        lift = maximum_lift * (1.0 - (progress - 0.80) / 0.20)

    smooth_travel = travel * travel * (3.0 - 2.0 * travel)

    x = start[0] + (end[0] - start[0]) * smooth_travel

    y = start[1] + (end[1] - start[1]) * smooth_travel

    return (
        x,
        y + lift,
        lift,
    )


def _liquidity_hud(
    axis: Axes,
    *,
    strategy: str,
    fraction: float,
) -> None:
    """Aligned three-column liquidity HUD."""

    _panel(
        axis,
        x=0.175,
        y=0.155,
        width=0.650,
        height=0.170,
    )

    draw_piece_3d(
        axis,
        strategy,
        (
            0.265,
            0.237,
        ),
        zoom=0.150,
        zorder=80,
    )

    _text(
        axis,
        0.345,
        0.267,
        (strategy.replace("_", " ").title() + " — LIQUIDITY"),
        size=17,
        weight="bold",
        zorder=82,
    )

    bar_x = 0.345
    bar_y = 0.205
    bar_width = 0.360

    axis.add_patch(
        Rectangle(
            (
                bar_x,
                bar_y,
            ),
            bar_width,
            0.030,
            facecolor="#263449",
            edgecolor="#475569",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=45,
        )
    )

    color = (
        THEME.danger if fraction < 0.25 else (THEME.warning if fraction < 0.45 else THEME.positive)
    )

    axis.add_patch(
        Rectangle(
            (
                bar_x,
                bar_y,
            ),
            bar_width * fraction,
            0.030,
            facecolor=color,
            edgecolor="none",
            transform=(axis.transAxes),
            zorder=46,
        )
    )

    _text(
        axis,
        0.720,
        0.220,
        f"{fraction:.0%}",
        size=17,
        color=color,
        weight="bold",
        ha="right",
        zorder=82,
    )

    if fraction < 0.25:
        draw_warning_badge(
            axis,
            x=0.765,
            y=0.223,
            scale=0.60,
        )


def _strategy_grid(
    axis: Axes,
) -> None:
    """V4-style strategy composition with generous margins."""

    _panel(
        axis,
        x=0.105,
        y=0.135,
        width=0.790,
        height=0.285,
    )

    entries = (
        (
            "collector",
            "Collector",
        ),
        (
            "specialist",
            "Specialist",
        ),
        (
            "cash_protector",
            "Cash Protector",
        ),
        (
            "aggressive_builder",
            "Aggressive\nBuilder",
        ),
    )

    for index, (
        strategy,
        label,
    ) in enumerate(entries):
        column = index % 2
        row = index // 2

        piece_x = 0.190 + column * 0.405

        row_y = 0.338 - row * 0.125

        draw_piece_3d(
            axis,
            strategy,
            (
                piece_x,
                row_y,
            ),
            zoom=0.145,
            zorder=80,
        )

        _text(
            axis,
            piece_x + 0.090,
            row_y,
            label,
            size=16,
            color=(THEME.primary_text),
            weight="bold",
            zorder=84,
        )


def _rent_hud(
    axis: Axes,
    context: PreviewContext,
) -> None:
    """Foreground rent panel below board center."""

    _panel(
        axis,
        x=0.170,
        y=0.145,
        width=0.660,
        height=0.205,
    )

    axis.add_patch(
        FancyArrowPatch(
            (
                0.380,
                0.242,
            ),
            (
                0.620,
                0.242,
            ),
            arrowstyle="-|>",
            mutation_scale=24,
            linewidth=3.5,
            color=(THEME.warning),
            transform=(axis.transAxes),
            zorder=55,
        )
    )

    draw_piece_3d(
        axis,
        "collector",
        (
            0.285,
            0.240,
        ),
        zoom=0.150,
        zorder=80,
    )

    draw_piece_3d(
        axis,
        "specialist",
        (
            0.715,
            0.240,
        ),
        zoom=0.150,
        zorder=80,
    )

    draw_cash(
        axis,
        x=0.432,
        y=0.263,
        amount=(context.representative_rent_amount),
        label="RENT",
    )

    _text(
        axis,
        0.285,
        0.175,
        "Collector",
        size=13,
        weight="bold",
        ha="center",
        zorder=84,
    )

    _text(
        axis,
        0.715,
        0.175,
        "Specialist",
        size=13,
        weight="bold",
        ha="center",
        zorder=84,
    )


def _purchase_hud(
    axis: Axes,
    context: PreviewContext,
    board_spaces: tuple[
        BoardSpaceVisual,
        ...,
    ],
) -> None:
    """Spacious three-column purchase card."""

    property_index = 14

    _panel(
        axis,
        x=0.145,
        y=0.140,
        width=0.710,
        height=0.230,
    )

    draw_piece_3d(
        axis,
        "collector",
        (
            0.240,
            0.255,
        ),
        zoom=0.155,
        zorder=80,
    )

    _text(
        axis,
        0.350,
        0.300,
        "PROPERTY ACQUIRED",
        size=20,
        weight="bold",
        zorder=84,
    )

    property_name = board_spaces[property_index].label

    _text(
        axis,
        0.350,
        0.255,
        property_name,
        size=16,
        color=(THEME.cyan),
        weight="bold",
        zorder=84,
    )

    draw_cash(
        axis,
        x=0.615,
        y=0.205,
        amount=(context.representative_purchase_amount),
        label="PURCHASE",
    )


def _bankruptcy_hud(
    axis: Axes,
) -> None:
    _panel(
        axis,
        x=0.285,
        y=0.345,
        width=0.430,
        height=0.210,
    )

    _text(
        axis,
        0.500,
        0.510,
        "AGGRESSIVE BUILDER",
        size=20,
        color=(THEME.primary_text),
        weight="bold",
        ha="center",
        zorder=84,
    )

    _text(
        axis,
        0.500,
        0.470,
        "BANKRUPT",
        size=24,
        color=(THEME.danger),
        weight="bold",
        ha="center",
        zorder=84,
    )

    draw_piece_3d(
        axis,
        "aggressive_builder",
        (
            0.500,
            0.400,
        ),
        zoom=0.155,
        zorder=80,
    )


def _tiny_board(
    axis: Axes,
    *,
    x: float,
    y: float,
    size: float,
    ranking: tuple[
        StrategyMetric,
        ...,
    ],
) -> None:
    """Miniature 40-space game board, not a beige placeholder."""

    axis.add_patch(
        Rectangle(
            (
                x,
                y,
            ),
            size,
            size,
            facecolor="#E8E1CA",
            edgecolor="#4B5563",
            linewidth=0.7,
            transform=(axis.transAxes),
            zorder=25,
        )
    )

    tile = size * 0.090

    inner_left = x
    inner_bottom = y

    for index in range(40):
        side = index // 10
        offset = index % 10

        fraction = offset / 10.0

        if side == 0:
            tx = inner_left + size * fraction

            ty = inner_bottom

        elif side == 1:
            tx = inner_left + size - tile

            ty = inner_bottom + size * fraction

        elif side == 2:
            tx = inner_left + size - tile - size * fraction

            ty = inner_bottom + size - tile

        else:
            tx = inner_left

            ty = inner_bottom + size - tile - size * fraction

        color = GROUP_COLORS[(index // 5) % len(GROUP_COLORS)]

        axis.add_patch(
            Rectangle(
                (
                    tx,
                    ty,
                ),
                tile,
                tile,
                facecolor="#FFFDF5",
                edgecolor="#64748B",
                linewidth=0.18,
                transform=(axis.transAxes),
                zorder=27,
            )
        )

        axis.add_patch(
            Rectangle(
                (
                    tx,
                    ty + tile * 0.72,
                ),
                tile,
                tile * 0.28,
                facecolor=color,
                edgecolor="none",
                transform=(axis.transAxes),
                zorder=28,
            )
        )

    # Four pieces shown in canonical winning order.
    for index, metric in enumerate(ranking):
        px = x + size * (0.26 + index * 0.16)

        py = y + size * 0.50

        draw_piece_3d(
            axis,
            metric.strategy_id,
            (
                px,
                py,
            ),
            zoom=0.018,
            zorder=40,
        )


def _leaderboard(
    axis: Axes,
    context: PreviewContext,
) -> None:
    """V4 composition with graphical uncertainty glyph."""

    _panel(
        axis,
        x=0.050,
        y=0.150,
        width=0.900,
        height=0.675,
    )

    _text(
        axis,
        0.190,
        0.765,
        "STRATEGY",
        size=15,
        color="#D4DCE8",
        weight="bold",
    )

    _text(
        axis,
        0.645,
        0.765,
        "95% WILSON CI",
        size=16,
        color="#D4DCE8",
        weight="bold",
        ha="center",
    )

    _text(
        axis,
        0.895,
        0.765,
        "WIN RATE",
        size=15,
        color="#D4DCE8",
        weight="bold",
        ha="right",
    )

    ranking = tuple(
        sorted(
            context.strategies,
            key=lambda metric: (
                -metric.win_rate,
                metric.strategy_id,
            ),
        )
    )

    domain_left = 0.490
    domain_width = 0.310
    maximum_rate = 0.50

    for index, metric in enumerate(ranking):
        y = 0.665 - index * 0.125

        draw_piece_3d(
            axis,
            metric.strategy_id,
            (
                0.125,
                y,
            ),
            zoom=0.125,
            zorder=80,
        )

        _text(
            axis,
            0.220,
            y,
            (f"#{index + 1}  " + metric.strategy_id.replace("_", " ").title()),
            size=17,
            weight="bold",
        )

        low = domain_left + domain_width * metric.ci_lower / maximum_rate

        high = domain_left + domain_width * metric.ci_upper / maximum_rate

        center = domain_left + domain_width * metric.win_rate / maximum_rate

        sigma = max(
            (high - low) / 3.92,
            0.008,
        )

        xs = [domain_left + domain_width * step / 100.0 for step in range(101)]

        density = [math.exp(-0.5 * ((x - center) / sigma) ** 2) for x in xs]

        maximum_density = max(density)

        ys = [y - 0.020 + (value / maximum_density) * 0.042 for value in density]

        axis.plot(
            xs,
            ys,
            color="#BFC8D4",
            linewidth=2.0,
            transform=(axis.transAxes),
            zorder=54,
        )

        axis.plot(
            (
                low,
                high,
            ),
            (
                y - 0.023,
                y - 0.023,
            ),
            color="#F8FAFC",
            linewidth=3.0,
            transform=(axis.transAxes),
            zorder=55,
        )

        for bound in (
            low,
            high,
        ):
            axis.plot(
                (
                    bound,
                    bound,
                ),
                (
                    y - 0.032,
                    y - 0.014,
                ),
                color="#F8FAFC",
                linewidth=1.5,
                transform=(axis.transAxes),
                zorder=56,
            )

        axis.scatter(
            (center,),
            (y - 0.023,),
            s=72,
            facecolor=(THEME.gold if index == 0 else "#F8FAFC"),
            edgecolor="#334155",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=57,
        )

        _text(
            axis,
            0.895,
            y,
            f"{metric.win_rate:.1%}",
            size=22,
            color=(THEME.gold if index == 0 else THEME.primary_text),
            weight="bold",
            ha="right",
        )


def _risk_reward(
    axis: Axes,
    context: PreviewContext,
) -> None:
    _panel(
        axis,
        x=0.045,
        y=0.155,
        width=0.910,
        height=0.670,
    )

    columns = (
        (
            0.195,
            "STRATEGY",
        ),
        (
            0.500,
            "WIN",
        ),
        (
            0.670,
            "BANKRUPT",
        ),
        (
            0.860,
            "MEDIAN CASH",
        ),
    )

    for x, title in columns:
        _text(
            axis,
            x,
            0.765,
            title,
            size=15,
            color="#D4DCE8",
            weight="bold",
            ha=("left" if title == "STRATEGY" else "center"),
            zorder=84,
        )

    for index, metric in enumerate(context.strategies):
        y = 0.665 - index * 0.125

        draw_piece_3d(
            axis,
            metric.strategy_id,
            (
                0.120,
                y,
            ),
            zoom=0.155,
            zorder=80,
        )

        _text(
            axis,
            0.205,
            y,
            metric.strategy_id.replace("_", " ").title(),
            size=17,
            weight="bold",
            zorder=84,
        )

        _text(
            axis,
            0.500,
            y,
            f"{metric.win_rate:.1%}",
            size=20,
            weight="bold",
            ha="center",
            zorder=84,
        )

        _text(
            axis,
            0.670,
            y,
            f"{metric.bankruptcy_rate:.1%}",
            size=20,
            color=(THEME.danger),
            weight="bold",
            ha="center",
            zorder=84,
        )

        _text(
            axis,
            0.860,
            y,
            (f"${metric.median_finishing_cash:,.0f}"),
            size=20,
            color=(THEME.gold),
            weight="bold",
            ha="center",
            zorder=84,
        )


def _footer(
    axis: Axes,
) -> None:
    _text(
        axis,
        0.500,
        0.022,
        DISCLAIMER,
        size=12.5,
        color="#D4DCE8",
        weight="bold",
        ha="center",
        outlined=True,
        zorder=120,
    )


def _save(
    figure: Figure,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        path,
        dpi=FRAME_DPI,
        facecolor=(THEME.background),
        format="png",
    )

    plt.close(figure)


def render_preview_frame(
    *,
    frame_key: str,
    context: PreviewContext,
    board_spaces: tuple[
        BoardSpaceVisual,
        ...,
    ],
    path: Path,
) -> None:
    figure, axis = _figure()

    gameplay = {
        "01_hook_race",
        "02_hook_rent",
        "03_hook_liquidity",
        "04_strategy_gameplay",
        "05_purchase",
        "06_build",
        "07_survival",
    }

    if frame_key in gameplay:
        draw_board(
            axis,
            board_spaces,
            center_title=(
                frame_key
                in {
                    "01_hook_race",
                    "02_hook_rent",
                    "05_purchase",
                }
            ),
        )

    if frame_key == "01_hook_race":
        _headline(
            axis,
            "THE RACE STARTS NOW",
            ("Four AI landlords. Same board. Different instincts."),
        )

        draw_dice(
            axis,
            first=6,
            second=5,
        )

        positions = board_positions()

        for strategy, index in zip(
            (
                "collector",
                "specialist",
                "cash_protector",
                "aggressive_builder",
            ),
            (
                4,
                7,
                10,
                13,
            ),
            strict=True,
        ):
            draw_piece_3d(
                axis,
                strategy,
                positions[index],
                zoom=0.140,
            )

    elif frame_key == "02_hook_rent":
        _headline(
            axis,
            "ONE LANDING. ONE HUGE RENT BILL.",
            ("Capital moves fast when someone else owns the square."),
        )

        draw_owner(
            axis,
            space_index=16,
            strategy_id="specialist",
        )

        draw_houses(
            axis,
            space_index=16,
            count=3,
        )

        _rent_hud(
            axis,
            context,
        )

    elif frame_key == "03_hook_liquidity":
        _headline(
            axis,
            "WHO SURVIVES 10,000 GAMES?",
            ("Aggressive Builder owns assets, but its cash reserve is disappearing."),
        )

        draw_warning_badge(
            axis,
            x=0.500,
            y=0.470,
            scale=1.10,
        )

        _text(
            axis,
            0.500,
            0.390,
            "CASH RESERVE COLLAPSING",
            size=24,
            color=(THEME.danger),
            weight="bold",
            ha="center",
            outlined=True,
        )

        _liquidity_hud(
            axis,
            strategy="aggressive_builder",
            fraction=0.12,
        )

    elif frame_key == "04_strategy_gameplay":
        _headline(
            axis,
            "FOUR STRATEGIES. FOUR PERSONALITIES.",
            ("Four deterministic policies deploy the same starting capital."),
        )

        positions = board_positions()

        for strategy, index in zip(
            (
                "collector",
                "specialist",
                "cash_protector",
                "aggressive_builder",
            ),
            (
                3,
                11,
                21,
                31,
            ),
            strict=True,
        ):
            draw_piece_3d(
                axis,
                strategy,
                positions[index],
                zoom=0.135,
            )

        _strategy_grid(axis)

    elif frame_key == "05_purchase":
        _headline(
            axis,
            "BUY OR HOLD CASH?",
            ("Every purchase shifts the balance between assets and liquidity."),
        )

        draw_owner(
            axis,
            space_index=14,
            strategy_id="collector",
        )

        _purchase_hud(
            axis,
            context,
            board_spaces,
        )

    elif frame_key == "06_build":
        _headline(
            axis,
            "NOW THE BET GETS BIGGER",
            ("Aggressive Builder commits more capital to development."),
        )

        draw_owner(
            axis,
            space_index=25,
            strategy_id="aggressive_builder",
        )

        draw_houses(
            axis,
            space_index=25,
            count=4,
        )

        _text(
            axis,
            0.500,
            0.395,
            ("Aggressive Builder • " + board_spaces[25].label),
            size=19,
            weight="bold",
            ha="center",
            outlined=True,
        )

        _liquidity_hud(
            axis,
            strategy="aggressive_builder",
            fraction=0.31,
        )

    elif frame_key == "07_survival":
        _headline(
            axis,
            "SAME BOARD. VERY DIFFERENT SURVIVAL.",
            ("Aggressive Builder runs out of cash. Cash Protector stays liquid."),
        )

        _bankruptcy_hud(axis)

        _liquidity_hud(
            axis,
            strategy="cash_protector",
            fraction=0.78,
        )

    elif frame_key == "08_scale":
        _headline(
            axis,
            "ONE GAME IS A STORY.",
            "10,000 games are evidence.",
        )

        ranking = tuple(
            sorted(
                context.strategies,
                key=lambda metric: (
                    -metric.win_rate,
                    metric.strategy_id,
                ),
            )
        )

        board_size = 0.142

        for row in range(5):
            for column in range(5):
                _tiny_board(
                    axis,
                    x=(0.105 + column * 0.165),
                    y=(0.175 + row * 0.130),
                    size=board_size,
                    ranking=ranking,
                )

        _text(
            axis,
            0.500,
            0.130,
            ("25 visible boards → zoom-out continues toward all 10,000 simulations"),
            size=15,
            color="#D4DCE8",
            weight="bold",
            ha="center",
        )

    elif frame_key == "09_counter":
        _headline(
            axis,
            "10,000 GAMES LATER...",
            ("Balanced seats. Frozen rules. Deterministic seeds."),
        )

        _panel(
            axis,
            x=0.175,
            y=0.270,
            width=0.650,
            height=0.370,
        )

        _text(
            axis,
            0.500,
            0.490,
            f"{context.game_count:,}",
            size=100,
            color=(THEME.gold),
            weight="bold",
            ha="center",
            outlined=True,
        )

        _text(
            axis,
            0.500,
            0.365,
            "COMPLETED GAMES",
            size=23,
            color="#D4DCE8",
            weight="bold",
            ha="center",
        )

    elif frame_key == "10_leaderboard":
        _headline(
            axis,
            "WHO WON MOST OFTEN?",
            ("Win rate with independently verified 95% Wilson confidence intervals."),
        )

        _leaderboard(
            axis,
            context,
        )

    elif frame_key == "11_risk_reward":
        _headline(
            axis,
            "WIN RATE ISN'T THE WHOLE STORY",
            "Winning without looking at risk can mislead.",
        )

        _risk_reward(
            axis,
            context,
        )

    elif frame_key == "12_result":
        _headline(
            axis,
            "THE DATA GETS THE LAST WORD",
            ("Numerical ranking and statistical evidence are not the same thing."),
        )

        _panel(
            axis,
            x=0.135,
            y=0.230,
            width=0.730,
            height=0.455,
        )

        winner = (
            context.headline_winner
            if context.headline_winner is not None
            else context.numerical_leader
        )

        if winner is not None:
            draw_piece_3d(
                axis,
                winner,
                (
                    0.500,
                    0.455,
                ),
                zoom=0.180,
                zorder=80,
            )

        if context.headline_winner is not None:
            _text(
                axis,
                0.500,
                0.600,
                context.headline_winner.replace("_", " ").upper(),
                size=28,
                weight="bold",
                ha="center",
            )

            _text(
                axis,
                0.500,
                0.320,
                "STATISTICALLY SUPPORTED WINNER",
                size=20,
                color=(THEME.gold),
                weight="bold",
                ha="center",
            )

        else:
            _text(
                axis,
                0.500,
                0.600,
                "NO SINGLE SUPPORTED WINNER",
                size=27,
                color=(THEME.gold),
                weight="bold",
                ha="center",
            )

            _text(
                axis,
                0.500,
                0.320,
                ("The numerical leader did not clear the full statistical winner rule."),
                size=16,
                color="#D4DCE8",
                weight="bold",
                ha="center",
            )

    elif frame_key == "13_footer":
        _headline(
            axis,
            "BUILT TO BE REPRODUCIBLE",
            ("Every result comes from the frozen and independently validated tournament."),
        )

        # Three headline KPI cards.
        cards = (
            (
                "GAMES",
                f"{context.game_count:,}",
            ),
            (
                "MASTER SEED",
                f"{context.master_seed:,}",
            ),
            (
                "SEAT BALANCE",
                "2,500 EACH",
            ),
        )

        for index, (
            title,
            value,
        ) in enumerate(cards):
            x = 0.080 + index * 0.300

            _panel(
                axis,
                x=x,
                y=0.555,
                width=0.250,
                height=0.170,
            )

            _text(
                axis,
                x + 0.125,
                0.670,
                title,
                size=14,
                color=(THEME.cyan),
                weight="bold",
                ha="center",
            )

            _text(
                axis,
                x + 0.125,
                0.610,
                value,
                size=24,
                color=(THEME.primary_text),
                weight="bold",
                ha="center",
            )

        _panel(
            axis,
            x=0.080,
            y=0.205,
            width=0.850,
            height=0.280,
        )

        methods = (
            "Rule-based autonomous strategy agents",
            "Wilson 95% confidence intervals",
            "Exact binomial pairwise comparisons",
            "Holm multiple-testing correction",
        )

        for index, method in enumerate(methods):
            y = 0.425 - index * 0.060

            _text(
                axis,
                0.145,
                y,
                "✓",
                size=17,
                color=(THEME.positive),
                weight="bold",
            )

            _text(
                axis,
                0.190,
                y,
                method,
                size=18,
                weight="bold",
            )

    else:
        raise ValueError(f"unknown V5 frame: {frame_key}")

    _footer(axis)

    _save(
        figure,
        path,
    )


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


def render_preview_frame_set(
    *,
    context: PreviewContext,
    board_spaces: tuple[
        BoardSpaceVisual,
        ...,
    ],
    output_directory: Path,
    show_progress: bool = True,
) -> dict[
    str,
    str,
]:
    ensure_piece_assets(ASSET_DIRECTORY)

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    hashes: dict[
        str,
        str,
    ] = {}

    total = len(PREVIEW_MOMENTS)

    for index, moment in enumerate(
        PREVIEW_MOMENTS,
        start=1,
    ):
        if show_progress:
            print(
                f"[RENDER] "
                f"{index}/{total} "
                f"({100.0 * index / total:5.1f}%) "
                f"t={moment.second:>4.1f}s "
                f"{moment.key}",
                flush=True,
            )

        output = output_directory / (moment.key + ".png")

        render_preview_frame(
            frame_key=(moment.key),
            context=context,
            board_spaces=board_spaces,
            path=output,
        )

        hashes[moment.key] = sha256_file(output)

    manifest = {
        "schema_version": "6.0",
        "frame_count": len(PREVIEW_MOMENTS),
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "piece_renderer": "fluent-emoji-3d-metallic-sprite",
        "piece_assets": PIECE_NAMES,
        "movement_contract": ("lift-travel-drop"),
        "moments": [
            {
                "key": moment.key,
                "second": moment.second,
                "meaning": moment.meaning,
                "sha256": hashes[moment.key],
            }
            for moment in PREVIEW_MOMENTS
        ],
    }

    (output_directory / "preview_frame_manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return hashes
