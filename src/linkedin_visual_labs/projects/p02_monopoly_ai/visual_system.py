"""Project 3 polished cinematic visual system V4.

This module turns the frozen Project 3 simulation into original
property-board-native visuals.

No official Monopoly/Hasbro artwork, logos, board artwork, card
designs, fonts, banknotes, or playing tokens are reproduced.

All pieces, dice, icons, cash, buildings, cards, and HUD components
are deterministic original vector illustrations.
"""

from __future__ import annotations

import hashlib
import json
import math
import textwrap
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import yaml
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import (
    Circle,
    Ellipse,
    FancyArrowPatch,
    FancyBboxPatch,
    Polygon,
    Rectangle,
)

from linkedin_visual_labs.projects.p02_monopoly_ai.cinematic_storyboard import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    PREVIEW_MOMENTS,
)

FRAME_DPI = 100

DISCLAIMER = "Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro."


# =====================================================================
# 7.1-7.7 - VISUAL CONTRACT
# =====================================================================


@dataclass(frozen=True, slots=True)
class Theme:
    """Frozen V4 cinematic visual language."""

    background: str = "#07101D"
    background_alt: str = "#0B1727"

    board: str = "#E8E1CA"
    board_space: str = "#FFFDF5"
    board_text: str = "#111827"
    board_edge: str = "#18212F"

    panel: str = "#0C1829"
    panel_alt: str = "#13233A"
    panel_border: str = "#455A78"

    primary_text: str = "#F8FAFC"
    secondary_text: str = "#CFD8E6"

    danger: str = "#E53935"
    danger_dark: str = "#991B1B"
    warning: str = "#FFD166"
    positive: str = "#36D399"
    gold: str = "#FFD166"
    cyan: str = "#67E8F9"

    # Strategy identity appears as accents only.
    collector: str = "#0077B6"
    specialist: str = "#A61E69"
    cash_protector: str = "#047857"
    aggressive_builder: str = "#C65D00"

    # Metallic playing-piece palette.
    silver_dark: str = "#555E69"
    silver_mid: str = "#A7B0BA"
    silver_light: str = "#E8EDF2"
    silver_highlight: str = "#FFFFFF"

    font_family: str = "DejaVu Sans"


THEME = Theme()


STRATEGY_ORDER = (
    "collector",
    "specialist",
    "cash_protector",
    "aggressive_builder",
)


STRATEGY_NAMES = {
    "collector": "Collector",
    "specialist": "Specialist",
    "cash_protector": "Cash Protector",
    "aggressive_builder": "Aggressive Builder",
}


STRATEGY_COLORS = {
    "collector": THEME.collector,
    "specialist": THEME.specialist,
    "cash_protector": THEME.cash_protector,
    "aggressive_builder": THEME.aggressive_builder,
}


STRATEGY_PIECES = {
    "collector": "silver_sports_coupe",
    "specialist": "silver_yacht",
    "cash_protector": "silver_armored_vault",
    "aggressive_builder": "silver_construction_loader",
}


GROUP_COLORS = (
    "#6D28D9",
    "#1D4ED8",
    "#0369A1",
    "#0F766E",
    "#4D7C0F",
    "#CA8A04",
    "#C2410C",
    "#B91C1C",
)


FRAME_TITLES = {
    "01_hook_race": "THE RACE STARTS NOW",
    "02_hook_rent": "ONE LANDING. ONE HUGE RENT BILL.",
    "03_hook_liquidity": "WHO SURVIVES 10,000 GAMES?",
    "04_strategy_gameplay": "FOUR STRATEGIES. FOUR PERSONALITIES.",
    "05_purchase": "BUY OR HOLD CASH?",
    "06_build": "NOW THE BET GETS BIGGER",
    "07_survival": "SAME BOARD. VERY DIFFERENT SURVIVAL.",
    "08_scale": "ONE GAME IS A STORY.",
    "09_counter": "10,000 GAMES LATER...",
    "10_leaderboard": "WHO WON MOST OFTEN?",
    "11_risk_reward": "WIN RATE ISN'T THE WHOLE STORY",
    "12_result": "THE DATA GETS THE LAST WORD",
    "13_footer": "BUILT TO BE REPRODUCIBLE",
}


@dataclass(frozen=True, slots=True)
class BoardSpaceVisual:
    index: int
    label: str
    space_type: str
    group_color: str | None


@dataclass(frozen=True, slots=True)
class StrategyMetric:
    strategy_id: str
    win_rate: float
    bankruptcy_rate: float
    median_finishing_cash: float
    ci_lower: float
    ci_upper: float


@dataclass(frozen=True, slots=True)
class PreviewContext:
    master_seed: int
    game_count: int

    representative_game_index: int
    representative_game_seed: int

    headline_status: str
    numerical_leader: str | None
    headline_winner: str | None

    representative_rent_amount: int
    representative_purchase_amount: int

    strategies: tuple[
        StrategyMetric,
        ...,
    ]


# =====================================================================
# DATA LOADING
# =====================================================================


def _mapping(
    value: object,
    *,
    name: str,
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")

    return {str(key): item for key, item in value.items()}


def _sequence(
    value: object,
    *,
    name: str,
) -> Sequence[object]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")

    return value


def _string(
    value: object,
    *,
    name: str,
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")

    return value


def _optional_string(
    value: object,
    *,
    name: str,
) -> str | None:
    if value is None:
        return None

    return _string(
        value,
        name=name,
    )


def _integer(
    value: object,
    *,
    name: str,
) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")

    return value


def _number(
    value: object,
    *,
    name: str,
) -> float:
    if not isinstance(
        value,
        (int, float),
    ) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")

    result = float(value)

    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")

    return result


def _json(
    path: Path,
) -> Mapping[str, object]:
    return _mapping(
        json.loads(path.read_text(encoding="utf-8")),
        name=str(path),
    )


def _extract_event_amount(
    events: Sequence[object],
    *,
    event_keywords: tuple[str, ...],
    fallback: int,
) -> int:
    for raw_event in events:
        event = _mapping(
            raw_event,
            name="representative event",
        )

        raw_type = event.get("event_type")

        if not isinstance(
            raw_type,
            str,
        ):
            continue

        event_type = raw_type.upper()

        if not any(keyword in event_type for keyword in event_keywords):
            continue

        raw_amount = event.get("amount")

        if (
            isinstance(raw_amount, int)
            and not isinstance(
                raw_amount,
                bool,
            )
            and raw_amount > 0
        ):
            return raw_amount

    return fallback


def load_preview_context(
    *,
    validation_directory: Path,
) -> PreviewContext:
    """Read only validated Step 6 analytical outputs."""

    freeze = _json(validation_directory / "canonical_video_freeze.json")

    if freeze.get("validated_for_video") is not True:
        raise ValueError("Step 6 freeze is not validated")

    report = _json(validation_directory / "tournament_validation_report.json")

    statistics = _mapping(
        report.get("statistical_validation"),
        name="statistical_validation",
    )

    headline = _mapping(
        statistics.get("headline_rule"),
        name="headline_rule",
    )

    diagnostics_payload = _json(validation_directory / "strategy_diagnostic_summary.json")

    diagnostics = _mapping(
        diagnostics_payload.get("diagnostics"),
        name="diagnostics",
    )

    win_ranking = _sequence(
        statistics.get("win_rate_ranking"),
        name="win_rate_ranking",
    )

    bankruptcy_ranking = _sequence(
        statistics.get("bankruptcy_ranking"),
        name="bankruptcy_ranking",
    )

    confidence = _mapping(
        statistics.get("independent_confidence_intervals"),
        name="confidence_intervals",
    )

    win_rates: dict[str, float] = {}
    bankruptcy_rates: dict[str, float] = {}

    for raw_item in win_ranking:
        item = _mapping(
            raw_item,
            name="win ranking item",
        )

        strategy = _string(
            item.get("strategy_id"),
            name="strategy_id",
        )

        win_rates[strategy] = _number(
            item.get("win_rate"),
            name="win_rate",
        )

    for raw_item in bankruptcy_ranking:
        item = _mapping(
            raw_item,
            name="bankruptcy ranking item",
        )

        strategy = _string(
            item.get("strategy_id"),
            name="strategy_id",
        )

        bankruptcy_rates[strategy] = _number(
            item.get("bankruptcy_rate"),
            name="bankruptcy_rate",
        )

    metrics: list[StrategyMetric] = []

    for strategy in STRATEGY_ORDER:
        diagnostic = _mapping(
            diagnostics.get(strategy),
            name=(f"diagnostics.{strategy}"),
        )

        strategy_ci = _mapping(
            confidence.get(strategy),
            name=(f"confidence.{strategy}"),
        )

        win_ci = _mapping(
            strategy_ci.get("win_rate"),
            name=(f"{strategy}.win_rate"),
        )

        metrics.append(
            StrategyMetric(
                strategy_id=strategy,
                win_rate=(win_rates[strategy]),
                bankruptcy_rate=(bankruptcy_rates[strategy]),
                median_finishing_cash=(
                    _number(
                        diagnostic.get("median_finishing_cash"),
                        name="median_finishing_cash",
                    )
                ),
                ci_lower=_number(
                    win_ci.get("lower"),
                    name="ci.lower",
                ),
                ci_upper=_number(
                    win_ci.get("upper"),
                    name="ci.upper",
                ),
            )
        )

    source_artifacts = _mapping(
        freeze.get("source_artifacts"),
        name="source_artifacts",
    )

    representative_events_path = Path(
        _string(
            source_artifacts.get("representative_events"),
            name="representative_events",
        )
    )

    events_payload = _json(representative_events_path)

    events = _sequence(
        events_payload.get("events"),
        name="representative.events",
    )

    rent_amount = _extract_event_amount(
        events,
        event_keywords=("RENT",),
        fallback=420,
    )

    purchase_amount = _extract_event_amount(
        events,
        event_keywords=(
            "PURCHASE",
            "BUY",
        ),
        fallback=260,
    )

    return PreviewContext(
        master_seed=_integer(
            freeze.get("master_seed"),
            name="master_seed",
        ),
        game_count=_integer(
            freeze.get("game_count"),
            name="game_count",
        ),
        representative_game_index=(
            _integer(
                freeze.get("representative_game_index"),
                name="representative_game_index",
            )
        ),
        representative_game_seed=(
            _integer(
                freeze.get("representative_game_seed"),
                name="representative_game_seed",
            )
        ),
        headline_status=_string(
            headline.get("status"),
            name="headline.status",
        ),
        numerical_leader=(
            _optional_string(
                headline.get("numerical_leader"),
                name="numerical_leader",
            )
        ),
        headline_winner=(
            _optional_string(
                headline.get("headline_winner"),
                name="headline_winner",
            )
        ),
        representative_rent_amount=(rent_amount),
        representative_purchase_amount=(purchase_amount),
        strategies=tuple(metrics),
    )


# =====================================================================
# 7.3-7.6 - BOARD
# =====================================================================


def _discover_space_list(
    value: object,
) -> list[Mapping[str, object]] | None:
    if isinstance(value, list):
        if len(value) == 40 and all(isinstance(item, dict) for item in value):
            return [
                _mapping(
                    item,
                    name="board space",
                )
                for item in value
            ]

        for item in value:
            result = _discover_space_list(item)

            if result is not None:
                return result

    if isinstance(value, dict):
        for item in value.values():
            result = _discover_space_list(item)

            if result is not None:
                return result

    return None


def _infer_space_type(
    item: Mapping[str, object],
    label: str,
) -> str:
    explicit = item.get("space_type") or item.get("type") or item.get("category")

    text = ((str(explicit) if explicit is not None else "") + " " + label).lower()

    if any(
        token in text
        for token in (
            "go",
            "start",
        )
    ):
        return "start"

    if any(
        token in text
        for token in (
            "rail",
            "transit",
            "station",
        )
    ):
        return "transit"

    if any(
        token in text
        for token in (
            "jail",
            "detention",
            "holding",
        )
    ):
        return "jail"

    if any(
        token in text
        for token in (
            "chance",
            "community",
            "event",
            "card",
        )
    ):
        return "event"

    if any(
        token in text
        for token in (
            "utility",
            "electric",
            "water",
        )
    ):
        return "utility"

    if any(
        token in text
        for token in (
            "tax",
            "fee",
        )
    ):
        return "fee"

    if any(
        token in text
        for token in (
            "parking",
            "rest",
        )
    ):
        return "rest"

    if (
        item.get("group") is not None
        or item.get("group_id") is not None
        or item.get("property_group") is not None
    ):
        return "property"

    return "neutral"


def load_board_spaces(
    config_path: Path,
) -> tuple[BoardSpaceVisual, ...]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    discovered = _discover_space_list(raw)

    if discovered is None:
        raise ValueError("Could not discover 40-space board")

    result: list[BoardSpaceVisual] = []

    for index, item in enumerate(discovered):
        raw_label = (
            item.get("name") or item.get("label") or item.get("space_name") or item.get("id")
        )

        if raw_label is None:
            raise ValueError(f"space {index} has no label")

        label = str(raw_label).replace(
            "_",
            " ",
        )

        group_raw = item.get("group") or item.get("group_id") or item.get("property_group")

        group_color: str | None = None

        if group_raw is not None:
            stable_index = sum(ord(character) for character in str(group_raw)) % len(GROUP_COLORS)

            group_color = GROUP_COLORS[stable_index]

        result.append(
            BoardSpaceVisual(
                index=index,
                label=label,
                space_type=(
                    _infer_space_type(
                        item,
                        label,
                    )
                ),
                group_color=(group_color),
            )
        )

    return tuple(result)


def board_positions() -> tuple[
    tuple[float, float],
    ...,
]:
    left = 0.075
    right = 0.925
    bottom = 0.085
    top = 0.825

    positions: list[tuple[float, float]] = []

    for index in range(40):
        side = index // 10
        offset = index % 10
        fraction = offset / 10.0

        if side == 0:
            point = (
                left + (right - left) * fraction,
                bottom,
            )

        elif side == 1:
            point = (
                right,
                bottom + (top - bottom) * fraction,
            )

        elif side == 2:
            point = (
                right - (right - left) * fraction,
                top,
            )

        else:
            point = (
                left,
                top - (top - bottom) * fraction,
            )

        positions.append(point)

    result = tuple(positions)

    if len(set(result)) != 40:
        raise ValueError("board positions must be unique")

    return result


# =====================================================================
# TYPOGRAPHY / BASE CANVAS
# =====================================================================


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
    rotation: float = 0.0,
    outlined: bool = False,
    zorder: int = 50,
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
        rotation=rotation,
        transform=(axis.transAxes),
        zorder=zorder,
    )

    if outlined:
        artist.set_path_effects(
            [
                path_effects.withStroke(
                    linewidth=3.2,
                    foreground="#000000",
                ),
            ]
        )


def _fit_title_size(
    value: str,
) -> float:
    length = len(value)

    if length <= 22:
        return 42.0

    if length <= 29:
        return 37.0

    if length <= 36:
        return 32.0

    return 28.0


def _fit_subtitle_size(
    value: str,
) -> float:
    length = len(value)

    if length <= 48:
        return 21.0

    if length <= 62:
        return 18.5

    return 16.5


def _headline(
    axis: Axes,
    title: str,
    subtitle: str | None = None,
) -> None:
    """Auto-fit the entire headline; truncation is never allowed."""

    _text(
        axis,
        0.050,
        0.950,
        title,
        size=_fit_title_size(title),
        weight="bold",
        outlined=True,
        zorder=90,
    )

    if subtitle is not None:
        wrapped = textwrap.fill(
            subtitle,
            width=64,
        )

        _text(
            axis,
            0.050,
            0.899,
            wrapped,
            size=_fit_subtitle_size(subtitle),
            color=(THEME.secondary_text),
            weight="bold",
            outlined=True,
            zorder=90,
        )


def _panel(
    axis: Axes,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    facecolor: str | None = None,
    alpha: float = 0.98,
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
            facecolor=(facecolor if facecolor is not None else THEME.panel),
            edgecolor=(THEME.panel_border),
            linewidth=1.5,
            alpha=alpha,
            transform=(axis.transAxes),
            zorder=zorder,
        )
    )


def _shadow(
    axis: Axes,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    alpha: float = 0.38,
    zorder: int = 50,
) -> None:
    axis.add_patch(
        Ellipse(
            (
                x,
                y,
            ),
            width,
            height,
            facecolor="#000000",
            edgecolor="none",
            alpha=alpha,
            transform=(axis.transAxes),
            zorder=zorder,
        )
    )


# =====================================================================
# BOARD SPACE ICONS
# =====================================================================


def _wrap_board_label(
    label: str,
) -> str:
    return "\n".join(
        textwrap.wrap(
            label,
            width=10,
        )[:2]
    )


def _start_icon(
    axis: Axes,
    x: float,
    y: float,
) -> None:
    axis.add_patch(
        Circle(
            (
                x,
                y,
            ),
            0.014,
            facecolor="#DCFCE7",
            edgecolor="#15803D",
            linewidth=1.2,
            transform=(axis.transAxes),
            zorder=10,
        )
    )

    _text(
        axis,
        x,
        y,
        "▶",
        size=9,
        color="#166534",
        weight="bold",
        ha="center",
        zorder=11,
    )


def _transit_icon(
    axis: Axes,
    x: float,
    y: float,
) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (
                x - 0.014,
                y - 0.010,
            ),
            0.028,
            0.021,
            boxstyle="round,pad=0.002",
            facecolor="#CBD5E1",
            edgecolor="#334155",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=10,
        )
    )

    for offset in (
        -0.007,
        0.007,
    ):
        axis.add_patch(
            Circle(
                (
                    x + offset,
                    y - 0.012,
                ),
                0.0035,
                facecolor="#111827",
                transform=(axis.transAxes),
                zorder=11,
            )
        )

    axis.plot(
        (
            x - 0.008,
            x + 0.008,
        ),
        (
            y + 0.003,
            y + 0.003,
        ),
        color="#334155",
        linewidth=1.0,
        transform=(axis.transAxes),
        zorder=11,
    )


def _jail_icon(
    axis: Axes,
    x: float,
    y: float,
) -> None:
    axis.add_patch(
        Rectangle(
            (
                x - 0.014,
                y - 0.013,
            ),
            0.028,
            0.026,
            facecolor="#FEE2E2",
            edgecolor="#991B1B",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=10,
        )
    )

    for offset in (
        -0.008,
        0.0,
        0.008,
    ):
        axis.plot(
            (
                x + offset,
                x + offset,
            ),
            (
                y - 0.011,
                y + 0.011,
            ),
            color="#991B1B",
            linewidth=1.1,
            transform=(axis.transAxes),
            zorder=11,
        )


def _event_icon(
    axis: Axes,
    x: float,
    y: float,
) -> None:
    axis.add_patch(
        FancyBboxPatch(
            (
                x - 0.012,
                y - 0.014,
            ),
            0.024,
            0.028,
            boxstyle="round,pad=0.002",
            facecolor="#FFF7ED",
            edgecolor="#EA580C",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=10,
        )
    )

    _text(
        axis,
        x,
        y,
        "?",
        size=12,
        color="#C2410C",
        weight="bold",
        ha="center",
        zorder=11,
    )


def _utility_icon(
    axis: Axes,
    x: float,
    y: float,
) -> None:
    bolt = (
        (
            x - 0.004,
            y + 0.014,
        ),
        (
            x + 0.005,
            y + 0.003,
        ),
        (
            x,
            y + 0.003,
        ),
        (
            x + 0.004,
            y - 0.014,
        ),
        (
            x - 0.007,
            y - 0.001,
        ),
        (
            x - 0.002,
            y - 0.001,
        ),
    )

    axis.add_patch(
        Polygon(
            bolt,
            closed=True,
            facecolor="#FACC15",
            edgecolor="#A16207",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=10,
        )
    )


def _property_icon(
    axis: Axes,
    x: float,
    y: float,
    color: str | None,
) -> None:
    accent = color if color is not None else "#64748B"

    axis.add_patch(
        Rectangle(
            (
                x - 0.011,
                y - 0.010,
            ),
            0.022,
            0.018,
            facecolor="#F1F5F9",
            edgecolor="#334155",
            linewidth=0.7,
            transform=(axis.transAxes),
            zorder=10,
        )
    )

    axis.add_patch(
        Polygon(
            (
                (
                    x - 0.013,
                    y + 0.008,
                ),
                (
                    x,
                    y + 0.019,
                ),
                (
                    x + 0.013,
                    y + 0.008,
                ),
            ),
            closed=True,
            facecolor=accent,
            edgecolor="#334155",
            linewidth=0.7,
            transform=(axis.transAxes),
            zorder=11,
        )
    )


def _space_icon(
    axis: Axes,
    space: BoardSpaceVisual,
    x: float,
    y: float,
) -> None:
    if space.space_type == "start":
        _start_icon(
            axis,
            x,
            y,
        )

    elif space.space_type == "transit":
        _transit_icon(
            axis,
            x,
            y,
        )

    elif space.space_type == "jail":
        _jail_icon(
            axis,
            x,
            y,
        )

    elif space.space_type == "event":
        _event_icon(
            axis,
            x,
            y,
        )

    elif space.space_type == "utility":
        _utility_icon(
            axis,
            x,
            y,
        )

    elif space.space_type == "fee":
        _text(
            axis,
            x,
            y,
            "-$",
            size=11,
            color="#B91C1C",
            weight="bold",
            ha="center",
            zorder=11,
        )

    elif space.space_type == "rest":
        _text(
            axis,
            x,
            y,
            "P",
            size=12,
            color="#1D4ED8",
            weight="bold",
            ha="center",
            zorder=11,
        )

    elif space.space_type == "property":
        _property_icon(
            axis,
            x,
            y,
            space.group_color,
        )


def draw_board(
    axis: Axes,
    spaces: Sequence[BoardSpaceVisual],
    *,
    center_title: bool = True,
    opacity: float = 1.0,
) -> None:
    if len(spaces) != 40:
        raise ValueError("board requires forty spaces")

    axis.add_patch(
        Rectangle(
            (
                0.060,
                0.065,
            ),
            0.880,
            0.780,
            facecolor=(THEME.board),
            edgecolor=(THEME.board_edge),
            linewidth=4.0,
            alpha=opacity,
            transform=(axis.transAxes),
            zorder=2,
        )
    )

    positions = board_positions()

    for space, (
        x,
        y,
    ) in zip(
        spaces,
        positions,
        strict=True,
    ):
        width = 0.079
        height = 0.066

        axis.add_patch(
            FancyBboxPatch(
                (
                    x - width / 2.0,
                    y - height / 2.0,
                ),
                width,
                height,
                boxstyle=("round,pad=0.002,rounding_size=0.005"),
                facecolor=(THEME.board_space),
                edgecolor="#334155",
                linewidth=0.9,
                alpha=opacity,
                transform=(axis.transAxes),
                zorder=4,
            )
        )

        if space.group_color is not None:
            axis.add_patch(
                Rectangle(
                    (
                        x - width / 2.0,
                        y + height / 2.0 - 0.011,
                    ),
                    width,
                    0.011,
                    facecolor=(space.group_color),
                    edgecolor="none",
                    alpha=opacity,
                    transform=(axis.transAxes),
                    zorder=5,
                )
            )

        _space_icon(
            axis,
            space,
            x,
            y + 0.007,
        )

        axis.text(
            x,
            y - 0.020,
            _wrap_board_label(space.label),
            fontsize=5.6,
            color=(THEME.board_text),
            fontfamily=(THEME.font_family),
            fontweight="bold",
            ha="center",
            va="center",
            linespacing=0.9,
            alpha=opacity,
            transform=(axis.transAxes),
            zorder=12,
        )

    if center_title:
        _text(
            axis,
            0.500,
            0.530,
            "AI LANDLORD ARENA",
            size=30,
            color="#172033",
            weight="bold",
            ha="center",
            zorder=15,
        )

        _text(
            axis,
            0.500,
            0.488,
            "capital allocation under uncertainty",
            size=16,
            color="#475569",
            weight="bold",
            ha="center",
            zorder=15,
        )


# =====================================================================
# 7.8 — SILVER TOY-LIKE PIECES
# =====================================================================


def _metal_shadow(
    axis: Axes,
    x: float,
    y: float,
    width: float,
    scale: float,
) -> None:
    _shadow(
        axis,
        x=x + 0.003,
        y=y - 0.014 * scale,
        width=width,
        height=0.014 * scale,
        alpha=0.42,
        zorder=55,
    )


def _metal_highlight(
    axis: Axes,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    zorder: int = 67,
) -> None:
    axis.plot(
        (
            x1,
            x2,
        ),
        (
            y1,
            y2,
        ),
        color=(THEME.silver_highlight),
        linewidth=1.2,
        alpha=0.9,
        transform=(axis.transAxes),
        zorder=zorder,
    )


def _accent_badge(
    axis: Axes,
    x: float,
    y: float,
    strategy: str,
    *,
    scale: float,
) -> None:
    axis.add_patch(
        Circle(
            (
                x,
                y,
            ),
            0.0055 * scale,
            facecolor=(STRATEGY_COLORS[strategy]),
            edgecolor="#FFFFFF",
            linewidth=0.5,
            transform=(axis.transAxes),
            zorder=69,
        )
    )


def _silver_car(
    axis: Axes,
    x: float,
    y: float,
    strategy: str,
    scale: float,
) -> None:
    width = 0.054 * scale
    height = 0.027 * scale

    _metal_shadow(
        axis,
        x,
        y,
        width * 1.1,
        scale,
    )

    lower_body = (
        (
            x - width * 0.52,
            y - height * 0.20,
        ),
        (
            x - width * 0.36,
            y + height * 0.15,
        ),
        (
            x + width * 0.32,
            y + height * 0.15,
        ),
        (
            x + width * 0.52,
            y - height * 0.08,
        ),
        (
            x + width * 0.35,
            y - height * 0.36,
        ),
        (
            x - width * 0.40,
            y - height * 0.36,
        ),
    )

    axis.add_patch(
        Polygon(
            lower_body,
            closed=True,
            facecolor=(THEME.silver_mid),
            edgecolor="#F8FAFC",
            linewidth=1.1,
            transform=(axis.transAxes),
            zorder=61,
        )
    )

    roof = (
        (
            x - width * 0.22,
            y + height * 0.14,
        ),
        (
            x - width * 0.08,
            y + height * 0.55,
        ),
        (
            x + width * 0.18,
            y + height * 0.50,
        ),
        (
            x + width * 0.30,
            y + height * 0.14,
        ),
    )

    axis.add_patch(
        Polygon(
            roof,
            closed=True,
            facecolor=(THEME.silver_light),
            edgecolor="#FFFFFF",
            linewidth=0.9,
            transform=(axis.transAxes),
            zorder=63,
        )
    )

    windshield = (
        (
            x - width * 0.075,
            y + height * 0.49,
        ),
        (
            x + width * 0.15,
            y + height * 0.45,
        ),
        (
            x + width * 0.24,
            y + height * 0.18,
        ),
        (
            x - width * 0.15,
            y + height * 0.18,
        ),
    )

    axis.add_patch(
        Polygon(
            windshield,
            closed=True,
            facecolor="#BFE7F5",
            edgecolor="#FFFFFF",
            linewidth=0.6,
            transform=(axis.transAxes),
            zorder=64,
        )
    )

    for wheel_x in (
        x - width * 0.31,
        x + width * 0.31,
    ):
        axis.add_patch(
            Circle(
                (
                    wheel_x,
                    y - height * 0.34,
                ),
                0.0075 * scale,
                facecolor="#111827",
                edgecolor=(THEME.silver_light),
                linewidth=0.9,
                transform=(axis.transAxes),
                zorder=65,
            )
        )

    _metal_highlight(
        axis,
        x - width * 0.33,
        y + height * 0.06,
        x + width * 0.31,
        y + height * 0.06,
    )

    _accent_badge(
        axis,
        x,
        y - 0.002 * scale,
        strategy,
        scale=scale,
    )


def _silver_yacht(
    axis: Axes,
    x: float,
    y: float,
    strategy: str,
    scale: float,
) -> None:
    width = 0.058 * scale

    _metal_shadow(
        axis,
        x,
        y,
        width,
        scale,
    )

    hull = (
        (
            x - 0.031 * scale,
            y,
        ),
        (
            x + 0.033 * scale,
            y,
        ),
        (
            x + 0.021 * scale,
            y - 0.019 * scale,
        ),
        (
            x - 0.022 * scale,
            y - 0.019 * scale,
        ),
    )

    axis.add_patch(
        Polygon(
            hull,
            closed=True,
            facecolor=(THEME.silver_mid),
            edgecolor="#FFFFFF",
            linewidth=1.1,
            transform=(axis.transAxes),
            zorder=61,
        )
    )

    axis.add_patch(
        Polygon(
            (
                (
                    x - 0.019 * scale,
                    y,
                ),
                (
                    x + 0.026 * scale,
                    y,
                ),
                (
                    x + 0.018 * scale,
                    y + 0.007 * scale,
                ),
                (
                    x - 0.014 * scale,
                    y + 0.007 * scale,
                ),
            ),
            closed=True,
            facecolor=(THEME.silver_light),
            edgecolor="#FFFFFF",
            linewidth=0.7,
            transform=(axis.transAxes),
            zorder=62,
        )
    )

    axis.plot(
        (
            x,
            x,
        ),
        (
            y + 0.005 * scale,
            y + 0.047 * scale,
        ),
        color=(THEME.silver_light),
        linewidth=2.0,
        transform=(axis.transAxes),
        zorder=63,
    )

    sail = (
        (
            x + 0.002 * scale,
            y + 0.043 * scale,
        ),
        (
            x + 0.002 * scale,
            y + 0.009 * scale,
        ),
        (
            x + 0.025 * scale,
            y + 0.013 * scale,
        ),
    )

    axis.add_patch(
        Polygon(
            sail,
            closed=True,
            facecolor="#F8FAFC",
            edgecolor=(THEME.silver_dark),
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=64,
        )
    )

    _metal_highlight(
        axis,
        x - 0.024 * scale,
        y - 0.004 * scale,
        x + 0.022 * scale,
        y - 0.004 * scale,
    )

    _accent_badge(
        axis,
        x,
        y - 0.010 * scale,
        strategy,
        scale=scale,
    )


def _silver_vault(
    axis: Axes,
    x: float,
    y: float,
    strategy: str,
    scale: float,
) -> None:
    width = 0.046 * scale
    height = 0.040 * scale

    _metal_shadow(
        axis,
        x,
        y,
        width,
        scale,
    )

    # Right side gives the safe depth.
    axis.add_patch(
        Polygon(
            (
                (
                    x + width / 2,
                    y - height / 2,
                ),
                (
                    x + width / 2 + 0.009 * scale,
                    y - height / 2 + 0.007 * scale,
                ),
                (
                    x + width / 2 + 0.009 * scale,
                    y + height / 2 + 0.007 * scale,
                ),
                (
                    x + width / 2,
                    y + height / 2,
                ),
            ),
            closed=True,
            facecolor=(THEME.silver_dark),
            edgecolor="#FFFFFF",
            linewidth=0.7,
            transform=(axis.transAxes),
            zorder=60,
        )
    )

    axis.add_patch(
        FancyBboxPatch(
            (
                x - width / 2,
                y - height / 2,
            ),
            width,
            height,
            boxstyle=("round,pad=0.003,rounding_size=0.004"),
            facecolor=(THEME.silver_mid),
            edgecolor="#FFFFFF",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=61,
        )
    )

    axis.add_patch(
        Circle(
            (
                x,
                y,
            ),
            0.011 * scale,
            facecolor=(THEME.silver_dark),
            edgecolor="#FFFFFF",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=63,
        )
    )

    for angle in (
        0,
        45,
        90,
        135,
    ):
        radians = math.radians(angle)

        axis.plot(
            (
                x - math.cos(radians) * 0.009 * scale,
                x + math.cos(radians) * 0.009 * scale,
            ),
            (
                y - math.sin(radians) * 0.009 * scale,
                y + math.sin(radians) * 0.009 * scale,
            ),
            color="#FFFFFF",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=64,
        )

    _metal_highlight(
        axis,
        x - width * 0.35,
        y + height * 0.31,
        x + width * 0.24,
        y + height * 0.31,
    )

    _accent_badge(
        axis,
        x,
        y - 0.027 * scale,
        strategy,
        scale=scale,
    )


def _silver_loader(
    axis: Axes,
    x: float,
    y: float,
    strategy: str,
    scale: float,
) -> None:
    _metal_shadow(
        axis,
        x,
        y,
        0.065 * scale,
        scale,
    )

    body_x = x - 0.023 * scale
    body_y = y - 0.012 * scale

    axis.add_patch(
        Rectangle(
            (
                body_x,
                body_y,
            ),
            0.043 * scale,
            0.026 * scale,
            facecolor=(THEME.silver_mid),
            edgecolor="#FFFFFF",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=61,
        )
    )

    axis.add_patch(
        Polygon(
            (
                (
                    x + 0.020 * scale,
                    y - 0.009 * scale,
                ),
                (
                    x + 0.030 * scale,
                    y - 0.003 * scale,
                ),
                (
                    x + 0.030 * scale,
                    y + 0.017 * scale,
                ),
                (
                    x + 0.020 * scale,
                    y + 0.012 * scale,
                ),
            ),
            closed=True,
            facecolor=(THEME.silver_dark),
            edgecolor="#FFFFFF",
            linewidth=0.7,
            transform=(axis.transAxes),
            zorder=60,
        )
    )

    axis.add_patch(
        Rectangle(
            (
                x - 0.010 * scale,
                y + 0.014 * scale,
            ),
            0.021 * scale,
            0.021 * scale,
            facecolor="#D6F0FA",
            edgecolor="#FFFFFF",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=63,
        )
    )

    arm = (
        (
            x + 0.018 * scale,
            y + 0.008 * scale,
        ),
        (
            x + 0.044 * scale,
            y + 0.023 * scale,
        ),
        (
            x + 0.048 * scale,
            y + 0.015 * scale,
        ),
        (
            x + 0.022 * scale,
            y,
        ),
    )

    axis.add_patch(
        Polygon(
            arm,
            closed=True,
            facecolor=(THEME.silver_light),
            edgecolor="#FFFFFF",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=64,
        )
    )

    bucket = (
        (
            x + 0.044 * scale,
            y + 0.021 * scale,
        ),
        (
            x + 0.064 * scale,
            y + 0.018 * scale,
        ),
        (
            x + 0.058 * scale,
            y - 0.004 * scale,
        ),
        (
            x + 0.047 * scale,
            y + 0.002 * scale,
        ),
    )

    axis.add_patch(
        Polygon(
            bucket,
            closed=True,
            facecolor=(THEME.silver_dark),
            edgecolor="#FFFFFF",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=65,
        )
    )

    for wheel_x in (
        x - 0.014 * scale,
        x + 0.014 * scale,
    ):
        axis.add_patch(
            Circle(
                (
                    wheel_x,
                    y - 0.014 * scale,
                ),
                0.008 * scale,
                facecolor="#111827",
                edgecolor=(THEME.silver_light),
                linewidth=0.8,
                transform=(axis.transAxes),
                zorder=66,
            )
        )

    _metal_highlight(
        axis,
        x - 0.019 * scale,
        y + 0.009 * scale,
        x + 0.015 * scale,
        y + 0.009 * scale,
    )

    _accent_badge(
        axis,
        x,
        y - 0.026 * scale,
        strategy,
        scale=scale,
    )


def draw_piece(
    axis: Axes,
    strategy_id: str,
    position: tuple[
        float,
        float,
    ],
    *,
    scale: float = 1.0,
) -> None:
    """Render metallic silver toy-like strategy piece."""

    x, y = position

    if strategy_id == "collector":
        _silver_car(
            axis,
            x,
            y,
            strategy_id,
            scale,
        )

    elif strategy_id == "specialist":
        _silver_yacht(
            axis,
            x,
            y,
            strategy_id,
            scale,
        )

    elif strategy_id == "cash_protector":
        _silver_vault(
            axis,
            x,
            y,
            strategy_id,
            scale,
        )

    else:
        _silver_loader(
            axis,
            x,
            y,
            strategy_id,
            scale,
        )


# =====================================================================
# 7.9 — PSEUDO-3D DICE WITH PIPS
# =====================================================================


DIE_PIPS = {
    1: (
        (
            0.5,
            0.5,
        ),
    ),
    2: (
        (
            0.28,
            0.72,
        ),
        (
            0.72,
            0.28,
        ),
    ),
    3: (
        (
            0.28,
            0.72,
        ),
        (
            0.5,
            0.5,
        ),
        (
            0.72,
            0.28,
        ),
    ),
    4: (
        (
            0.28,
            0.72,
        ),
        (
            0.72,
            0.72,
        ),
        (
            0.28,
            0.28,
        ),
        (
            0.72,
            0.28,
        ),
    ),
    5: (
        (
            0.28,
            0.72,
        ),
        (
            0.72,
            0.72,
        ),
        (
            0.5,
            0.5,
        ),
        (
            0.28,
            0.28,
        ),
        (
            0.72,
            0.28,
        ),
    ),
    6: (
        (
            0.28,
            0.72,
        ),
        (
            0.72,
            0.72,
        ),
        (
            0.28,
            0.5,
        ),
        (
            0.72,
            0.5,
        ),
        (
            0.28,
            0.28,
        ),
        (
            0.72,
            0.28,
        ),
    ),
}


def _die(
    axis: Axes,
    *,
    x: float,
    y: float,
    value: int,
    size: float = 0.072,
) -> None:
    if value not in DIE_PIPS:
        raise ValueError("die value must be 1..6")

    depth = size * 0.12

    _shadow(
        axis,
        x=x + size / 2,
        y=y - depth,
        width=size * 1.18,
        height=size * 0.25,
        zorder=55,
    )

    # Right side.
    axis.add_patch(
        Polygon(
            (
                (
                    x + size,
                    y,
                ),
                (
                    x + size + depth,
                    y + depth,
                ),
                (
                    x + size + depth,
                    y + size + depth,
                ),
                (
                    x + size,
                    y + size,
                ),
            ),
            closed=True,
            facecolor="#BFC8D2",
            edgecolor="#111827",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=57,
        )
    )

    # Top depth face.
    axis.add_patch(
        Polygon(
            (
                (
                    x,
                    y + size,
                ),
                (
                    x + depth,
                    y + size + depth,
                ),
                (
                    x + size + depth,
                    y + size + depth,
                ),
                (
                    x + size,
                    y + size,
                ),
            ),
            closed=True,
            facecolor="#FFFFFF",
            edgecolor="#111827",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=58,
        )
    )

    axis.add_patch(
        FancyBboxPatch(
            (
                x,
                y,
            ),
            size,
            size,
            boxstyle=("round,pad=0.004,rounding_size=0.010"),
            facecolor="#F8FAFC",
            edgecolor="#111827",
            linewidth=1.7,
            transform=(axis.transAxes),
            zorder=60,
        )
    )

    for px, py in DIE_PIPS[value]:
        axis.add_patch(
            Circle(
                (
                    x + px * size,
                    y + py * size,
                ),
                size * 0.065,
                facecolor="#111827",
                edgecolor="none",
                transform=(axis.transAxes),
                zorder=62,
            )
        )


def draw_dice(
    axis: Axes,
    *,
    first: int,
    second: int,
) -> None:
    _die(
        axis,
        x=0.414,
        y=0.585,
        value=first,
    )

    _die(
        axis,
        x=0.515,
        y=0.585,
        value=second,
    )


# =====================================================================
# 7.10-7.20 - GAMEPLAY HUD COMPONENTS
# =====================================================================


def draw_cash(
    axis: Axes,
    *,
    x: float,
    y: float,
    amount: int,
    label: str,
) -> None:
    """Always foreground cash with visible dollar value."""

    _shadow(
        axis,
        x=x + 0.066,
        y=y - 0.008,
        width=0.145,
        height=0.020,
        zorder=68,
    )

    for index in range(3):
        offset = index * 0.007

        axis.add_patch(
            FancyBboxPatch(
                (
                    x + offset,
                    y + offset,
                ),
                0.132,
                0.058,
                boxstyle=("round,pad=0.004,rounding_size=0.006"),
                facecolor="#D0F5D9",
                edgecolor="#14532D",
                linewidth=1.0,
                transform=(axis.transAxes),
                zorder=70 + index,
            )
        )

    _text(
        axis,
        x + 0.073,
        y + 0.043,
        f"${amount:,}",
        size=19,
        color="#14532D",
        weight="bold",
        ha="center",
        zorder=76,
    )

    _text(
        axis,
        x + 0.073,
        y + 0.021,
        label,
        size=8.5,
        color="#166534",
        weight="bold",
        ha="center",
        zorder=76,
    )


def draw_event_card(
    axis: Axes,
    *,
    x: float,
    y: float,
    title: str,
    body: str,
) -> None:
    _panel(
        axis,
        x=x,
        y=y,
        width=0.230,
        height=0.145,
        facecolor="#FFF7ED",
        zorder=43,
    )

    _text(
        axis,
        x + 0.115,
        y + 0.103,
        title,
        size=17,
        color="#9A3412",
        weight="bold",
        ha="center",
        zorder=47,
    )

    _text(
        axis,
        x + 0.115,
        y + 0.052,
        body,
        size=13,
        color="#7C2D12",
        weight="bold",
        ha="center",
        zorder=47,
    )


def draw_owner(
    axis: Axes,
    *,
    space_index: int,
    strategy_id: str,
) -> None:
    x, y = board_positions()[space_index]

    color = STRATEGY_COLORS[strategy_id]

    axis.plot(
        (
            x - 0.017,
            x - 0.017,
        ),
        (
            y + 0.028,
            y + 0.061,
        ),
        color="#334155",
        linewidth=1.1,
        transform=(axis.transAxes),
        zorder=17,
    )

    axis.add_patch(
        Polygon(
            (
                (
                    x - 0.016,
                    y + 0.058,
                ),
                (
                    x + 0.020,
                    y + 0.048,
                ),
                (
                    x - 0.016,
                    y + 0.038,
                ),
            ),
            closed=True,
            facecolor=color,
            edgecolor="#FFFFFF",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=18,
        )
    )


def draw_houses(
    axis: Axes,
    *,
    space_index: int,
    count: int,
) -> None:
    x, y = board_positions()[space_index]

    for index in range(count):
        hx = x - 0.026 + index * 0.014

        axis.add_patch(
            Rectangle(
                (
                    hx,
                    y + 0.031,
                ),
                0.011,
                0.011,
                facecolor="#15803D",
                edgecolor="#FFFFFF",
                linewidth=0.4,
                transform=(axis.transAxes),
                zorder=18,
            )
        )

        axis.add_patch(
            Polygon(
                (
                    (
                        hx - 0.001,
                        y + 0.042,
                    ),
                    (
                        hx + 0.0055,
                        y + 0.049,
                    ),
                    (
                        hx + 0.012,
                        y + 0.042,
                    ),
                ),
                closed=True,
                facecolor="#166534",
                edgecolor="#FFFFFF",
                linewidth=0.3,
                transform=(axis.transAxes),
                zorder=19,
            )
        )


def draw_warning_badge(
    axis: Axes,
    *,
    x: float,
    y: float,
    scale: float = 1.0,
) -> None:
    radius = 0.038 * scale

    axis.add_patch(
        Polygon(
            (
                (
                    x,
                    y + radius,
                ),
                (
                    x + radius * 0.88,
                    y - radius * 0.75,
                ),
                (
                    x - radius * 0.88,
                    y - radius * 0.75,
                ),
            ),
            closed=True,
            facecolor=(THEME.warning),
            edgecolor="#92400E",
            linewidth=1.8,
            transform=(axis.transAxes),
            zorder=82,
        )
    )

    _text(
        axis,
        x,
        y - 0.003,
        "!",
        size=22 * scale,
        color="#7C2D12",
        weight="bold",
        ha="center",
        zorder=83,
    )


def draw_liquidity(
    axis: Axes,
    *,
    strategy: str,
    fraction: float,
    y: float = 0.185,
) -> None:
    """Liquidity HUD lives below board-center content."""

    fraction = min(
        1.0,
        max(
            0.0,
            fraction,
        ),
    )

    _panel(
        axis,
        x=0.245,
        y=y,
        width=0.510,
        height=0.140,
        facecolor="#091526",
        zorder=38,
    )

    draw_piece(
        axis,
        strategy,
        (
            0.305,
            y + 0.069,
        ),
        scale=1.08,
    )

    _text(
        axis,
        0.360,
        y + 0.101,
        (STRATEGY_NAMES[strategy] + " — LIQUIDITY"),
        size=16,
        color=(THEME.secondary_text),
        weight="bold",
        zorder=44,
    )

    axis.add_patch(
        Rectangle(
            (
                0.360,
                y + 0.048,
            ),
            0.285,
            0.027,
            facecolor="#263449",
            edgecolor="#475569",
            linewidth=0.8,
            transform=(axis.transAxes),
            zorder=43,
        )
    )

    color = (
        THEME.danger if fraction < 0.25 else (THEME.warning if fraction < 0.45 else THEME.positive)
    )

    axis.add_patch(
        Rectangle(
            (
                0.360,
                y + 0.048,
            ),
            0.285 * fraction,
            0.027,
            facecolor=color,
            edgecolor="none",
            transform=(axis.transAxes),
            zorder=44,
        )
    )

    _text(
        axis,
        0.655,
        y + 0.061,
        f"{fraction:.0%}",
        size=16,
        color=color,
        weight="bold",
        ha="right",
        zorder=45,
    )

    if fraction < 0.25:
        draw_warning_badge(
            axis,
            x=0.705,
            y=y + 0.066,
            scale=0.63,
        )


def draw_movement(
    axis: Axes,
    *,
    start_index: int,
    end_index: int,
    strategy_id: str,
) -> None:
    start = board_positions()[start_index]

    end = board_positions()[end_index]

    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=17,
            linewidth=2.6,
            linestyle=(
                (
                    0,
                    (
                        3,
                        2,
                    ),
                )
            ),
            color=(STRATEGY_COLORS[strategy_id]),
            alpha=0.72,
            connectionstyle="arc3,rad=0.10",
            transform=(axis.transAxes),
            zorder=45,
        )
    )


def draw_rent_transfer(
    axis: Axes,
    *,
    payer: str,
    owner: str,
    amount: int,
) -> None:
    """Rent HUD sits below center; pieces/cash remain foreground."""

    _panel(
        axis,
        x=0.235,
        y=0.175,
        width=0.530,
        height=0.190,
        facecolor="#091526",
        zorder=36,
    )

    axis.add_patch(
        FancyArrowPatch(
            (
                0.390,
                0.255,
            ),
            (
                0.610,
                0.255,
            ),
            arrowstyle="-|>",
            mutation_scale=25,
            linewidth=4.0,
            color=(THEME.warning),
            connectionstyle=("arc3,rad=-0.16"),
            transform=(axis.transAxes),
            zorder=48,
        )
    )

    # Foreground pieces.
    draw_piece(
        axis,
        payer,
        (
            0.330,
            0.255,
        ),
        scale=1.30,
    )

    draw_piece(
        axis,
        owner,
        (
            0.670,
            0.255,
        ),
        scale=1.30,
    )

    # Foreground money above arrow/panel.
    draw_cash(
        axis,
        x=0.432,
        y=0.282,
        amount=amount,
        label="RENT",
    )

    _text(
        axis,
        0.330,
        0.205,
        STRATEGY_NAMES[payer],
        size=13,
        color=(THEME.primary_text),
        weight="bold",
        ha="center",
        zorder=77,
    )

    _text(
        axis,
        0.670,
        0.205,
        STRATEGY_NAMES[owner],
        size=13,
        color=(THEME.primary_text),
        weight="bold",
        ha="center",
        zorder=77,
    )


def draw_bankruptcy(
    axis: Axes,
    strategy: str,
) -> None:
    """Compact bankruptcy HUD."""

    _panel(
        axis,
        x=0.365,
        y=0.355,
        width=0.270,
        height=0.185,
        facecolor="#260D12",
        zorder=38,
    )

    _text(
        axis,
        0.500,
        0.505,
        (STRATEGY_NAMES[strategy] + " BANKRUPT"),
        size=24,
        color=(THEME.danger),
        weight="bold",
        ha="center",
        outlined=True,
        zorder=80,
    )

    draw_piece(
        axis,
        strategy,
        (
            0.500,
            0.425,
        ),
        scale=1.55,
    )

    axis.plot(
        (
            0.467,
            0.533,
        ),
        (
            0.390,
            0.459,
        ),
        color=(THEME.danger),
        linewidth=4.0,
        transform=(axis.transAxes),
        zorder=82,
    )

    axis.plot(
        (
            0.467,
            0.533,
        ),
        (
            0.459,
            0.390,
        ),
        color=(THEME.danger),
        linewidth=4.0,
        transform=(axis.transAxes),
        zorder=82,
    )


# =====================================================================
# 7.23-7.25 - RESULT VISUALS
# =====================================================================


def draw_confidence_interval(
    axis: Axes,
    *,
    metric: StrategyMetric,
    y: float,
) -> None:
    left = 0.470
    width = 0.300
    maximum_rate = 0.50

    lower = left + width * metric.ci_lower / maximum_rate

    upper = left + width * metric.ci_upper / maximum_rate

    center = left + width * metric.win_rate / maximum_rate

    color = STRATEGY_COLORS[metric.strategy_id]

    axis.plot(
        (
            lower,
            upper,
        ),
        (
            y,
            y,
        ),
        color=color,
        linewidth=4.0,
        transform=(axis.transAxes),
        zorder=54,
    )

    for x in (
        lower,
        upper,
    ):
        axis.plot(
            (
                x,
                x,
            ),
            (
                y - 0.010,
                y + 0.010,
            ),
            color=color,
            linewidth=2.0,
            transform=(axis.transAxes),
            zorder=54,
        )

    axis.scatter(
        (center,),
        (y,),
        s=100,
        facecolor=(THEME.silver_light),
        edgecolor=color,
        linewidth=2.0,
        transform=(axis.transAxes),
        zorder=55,
    )


def _ranking(
    context: PreviewContext,
) -> tuple[
    StrategyMetric,
    ...,
]:
    return tuple(
        sorted(
            context.strategies,
            key=lambda metric: (
                -metric.win_rate,
                metric.strategy_id,
            ),
        )
    )


def _leaderboard(
    axis: Axes,
    context: PreviewContext,
) -> None:
    _panel(
        axis,
        x=0.060,
        y=0.185,
        width=0.880,
        height=0.640,
        facecolor="#091526",
        zorder=35,
    )

    _text(
        axis,
        0.175,
        0.765,
        "STRATEGY",
        size=14,
        color=(THEME.secondary_text),
        weight="bold",
        zorder=50,
    )

    _text(
        axis,
        0.620,
        0.765,
        "95% WILSON CI",
        size=14,
        color=(THEME.secondary_text),
        weight="bold",
        ha="center",
        zorder=50,
    )

    _text(
        axis,
        0.880,
        0.765,
        "WIN RATE",
        size=14,
        color=(THEME.secondary_text),
        weight="bold",
        ha="right",
        zorder=50,
    )

    for index, metric in enumerate(_ranking(context)):
        y = 0.675 - index * 0.125

        # Subtle strategy accent rail.
        axis.add_patch(
            Rectangle(
                (
                    0.080,
                    y - 0.044,
                ),
                0.008,
                0.080,
                facecolor=(STRATEGY_COLORS[metric.strategy_id]),
                edgecolor="none",
                transform=(axis.transAxes),
                zorder=42,
            )
        )

        draw_piece(
            axis,
            metric.strategy_id,
            (
                0.125,
                y,
            ),
            scale=0.93,
        )

        _text(
            axis,
            0.180,
            y,
            (f"#{index + 1}  {STRATEGY_NAMES[metric.strategy_id]}"),
            size=19,
            color=(THEME.primary_text),
            weight="bold",
            zorder=65,
        )

        draw_confidence_interval(
            axis,
            metric=metric,
            y=y,
        )

        _text(
            axis,
            0.880,
            y,
            f"{metric.win_rate:.1%}",
            size=24,
            color=(THEME.gold if index == 0 else THEME.primary_text),
            weight="bold",
            ha="right",
            zorder=65,
        )


def _risk_reward_panel(
    axis: Axes,
    context: PreviewContext,
) -> None:
    _panel(
        axis,
        x=0.055,
        y=0.175,
        width=0.890,
        height=0.650,
        facecolor="#091526",
        zorder=35,
    )

    _text(
        axis,
        0.175,
        0.760,
        "STRATEGY",
        size=14,
        color=(THEME.secondary_text),
        weight="bold",
        zorder=50,
    )

    _text(
        axis,
        0.480,
        0.760,
        "WIN",
        size=14,
        color=(THEME.cyan),
        weight="bold",
        ha="center",
        zorder=50,
    )

    _text(
        axis,
        0.650,
        0.760,
        "BANKRUPT",
        size=14,
        color=(THEME.danger),
        weight="bold",
        ha="center",
        zorder=50,
    )

    _text(
        axis,
        0.845,
        0.760,
        "MEDIAN CASH",
        size=14,
        color=(THEME.gold),
        weight="bold",
        ha="center",
        zorder=50,
    )

    for index, metric in enumerate(context.strategies):
        y = 0.670 - index * 0.125

        axis.add_patch(
            Rectangle(
                (
                    0.075,
                    y - 0.045,
                ),
                0.008,
                0.082,
                facecolor=(STRATEGY_COLORS[metric.strategy_id]),
                edgecolor="none",
                transform=(axis.transAxes),
                zorder=42,
            )
        )

        draw_piece(
            axis,
            metric.strategy_id,
            (
                0.120,
                y,
            ),
            scale=0.90,
        )

        _text(
            axis,
            0.172,
            y,
            STRATEGY_NAMES[metric.strategy_id],
            size=18,
            color=(THEME.primary_text),
            weight="bold",
            zorder=65,
        )

        _text(
            axis,
            0.480,
            y,
            f"{metric.win_rate:.1%}",
            size=21,
            color=(THEME.primary_text),
            weight="bold",
            ha="center",
            zorder=65,
        )

        _text(
            axis,
            0.650,
            y,
            f"{metric.bankruptcy_rate:.1%}",
            size=21,
            color=(THEME.danger),
            weight="bold",
            ha="center",
            zorder=65,
        )

        _text(
            axis,
            0.845,
            y,
            (f"${metric.median_finishing_cash:,.0f}"),
            size=21,
            color=(THEME.gold),
            weight="bold",
            ha="center",
            zorder=65,
        )


# =====================================================================
# SCALE MINI-BOARDS
# =====================================================================


def _mini_board(
    axis: Axes,
    *,
    x: float,
    y: float,
    width: float,
    ranking: Sequence[StrategyMetric],
) -> None:
    """Actual mini game-board motif used during zoom-out."""

    height = width

    axis.add_patch(
        Rectangle(
            (
                x,
                y,
            ),
            width,
            height,
            facecolor="#DDD5BC",
            edgecolor="#64748B",
            linewidth=1.0,
            transform=(axis.transAxes),
            zorder=28,
        )
    )

    inset = width * 0.20

    axis.add_patch(
        Rectangle(
            (
                x + inset,
                y + inset,
            ),
            width - 2 * inset,
            height - 2 * inset,
            facecolor="#F1EBD8",
            edgecolor="#94A3B8",
            linewidth=0.6,
            transform=(axis.transAxes),
            zorder=29,
        )
    )

    strip = width * 0.055

    for index, color in enumerate(GROUP_COLORS):
        fraction = index / len(GROUP_COLORS)

        axis.add_patch(
            Rectangle(
                (
                    x + fraction * width,
                    y + height - strip,
                ),
                width / len(GROUP_COLORS),
                strip,
                facecolor=color,
                edgecolor="none",
                transform=(axis.transAxes),
                zorder=30,
            )
        )

    # Winning order is visibly encoded left to right.
    for index, metric in enumerate(ranking):
        px = x + width * (0.24 + index * 0.175)

        py = y + height * 0.50

        draw_piece(
            axis,
            metric.strategy_id,
            (
                px,
                py,
            ),
            scale=0.27,
        )


# =====================================================================
# FRAME RENDERERS
# =====================================================================


def _footer(
    axis: Axes,
) -> None:
    _text(
        axis,
        0.500,
        0.023,
        DISCLAIMER,
        size=13,
        color="#D8E0EC",
        weight="bold",
        ha="center",
        outlined=True,
        zorder=95,
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


def _strategy_legend(
    axis: Axes,
) -> None:
    """Large lower HUD with no text overflow."""

    _panel(
        axis,
        x=0.165,
        y=0.165,
        width=0.670,
        height=0.220,
        facecolor="#091526",
        zorder=34,
    )

    for index, strategy in enumerate(STRATEGY_ORDER):
        column = index % 2
        row = index // 2

        x = 0.235 + column * 0.340

        y = 0.315 - row * 0.090

        draw_piece(
            axis,
            strategy,
            (
                x,
                y,
            ),
            scale=0.88,
        )

        _text(
            axis,
            x + 0.055,
            y,
            STRATEGY_NAMES[strategy],
            size=16,
            color=(THEME.primary_text),
            weight="bold",
            zorder=66,
        )

        axis.add_patch(
            Rectangle(
                (
                    x + 0.047,
                    y - 0.025,
                ),
                0.175,
                0.004,
                facecolor=(STRATEGY_COLORS[strategy]),
                edgecolor="none",
                transform=(axis.transAxes),
                zorder=64,
            )
        )


def render_preview_frame(
    *,
    frame_key: str,
    context: PreviewContext,
    board_spaces: Sequence[BoardSpaceVisual],
    path: Path,
) -> None:
    figure, axis = _figure()

    gameplay_frames = {
        "01_hook_race",
        "02_hook_rent",
        "03_hook_liquidity",
        "04_strategy_gameplay",
        "05_purchase",
        "06_build",
        "07_survival",
    }

    if frame_key in gameplay_frames:
        center_title = frame_key not in {
            "03_hook_liquidity",
            "04_strategy_gameplay",
            "06_build",
            "07_survival",
        }

        draw_board(
            axis,
            board_spaces,
            center_title=center_title,
        )

    if frame_key == "01_hook_race":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Four AI landlords. Same board. Different instincts."),
        )

        draw_dice(
            axis,
            first=6,
            second=5,
        )

        positions = board_positions()

        for strategy, index in zip(
            STRATEGY_ORDER,
            (
                4,
                7,
                10,
                13,
            ),
            strict=True,
        ):
            draw_movement(
                axis,
                start_index=max(
                    0,
                    index - 2,
                ),
                end_index=index,
                strategy_id=strategy,
            )

            draw_piece(
                axis,
                strategy,
                positions[index],
                scale=1.10,
            )

    elif frame_key == "02_hook_rent":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
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

        draw_rent_transfer(
            axis,
            payer="collector",
            owner="specialist",
            amount=(context.representative_rent_amount),
        )

    elif frame_key == "03_hook_liquidity":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Aggressive Builder owns assets—but the cash reserve is disappearing."),
        )

        draw_warning_badge(
            axis,
            x=0.500,
            y=0.500,
            scale=1.15,
        )

        _text(
            axis,
            0.500,
            0.430,
            "AGGRESSIVE BUILDER",
            size=20,
            color=(THEME.primary_text),
            weight="bold",
            ha="center",
            outlined=True,
            zorder=84,
        )

        _text(
            axis,
            0.500,
            0.390,
            "CASH RESERVE COLLAPSING",
            size=25,
            color=(THEME.danger),
            weight="bold",
            ha="center",
            outlined=True,
            zorder=84,
        )

        draw_liquidity(
            axis,
            strategy=("aggressive_builder"),
            fraction=0.12,
            y=0.175,
        )

    elif frame_key == "04_strategy_gameplay":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Four deterministic personalities deploy the same starting capital."),
        )

        positions = board_positions()

        for strategy, index in zip(
            STRATEGY_ORDER,
            (
                3,
                11,
                21,
                31,
            ),
            strict=True,
        ):
            draw_piece(
                axis,
                strategy,
                positions[index],
                scale=1.08,
            )

        _strategy_legend(axis)

    elif frame_key == "05_purchase":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Every purchase shifts the balance between assets and liquidity."),
        )

        property_index = 14

        draw_owner(
            axis,
            space_index=property_index,
            strategy_id="collector",
        )

        _panel(
            axis,
            x=0.285,
            y=0.170,
            width=0.430,
            height=0.200,
            facecolor="#091526",
            zorder=36,
        )

        draw_piece(
            axis,
            "collector",
            (
                0.350,
                0.270,
            ),
            scale=1.20,
        )

        _text(
            axis,
            0.415,
            0.320,
            "PROPERTY ACQUIRED",
            size=21,
            color=(THEME.primary_text),
            weight="bold",
            zorder=66,
        )

        _text(
            axis,
            0.415,
            0.282,
            board_spaces[property_index].label,
            size=17,
            color=(THEME.cyan),
            weight="bold",
            zorder=66,
        )

        draw_cash(
            axis,
            x=0.465,
            y=0.205,
            amount=(context.representative_purchase_amount),
            label="PURCHASE",
        )

    elif frame_key == "06_build":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Aggressive Builder commits more capital to development."),
        )

        property_index = 25

        draw_owner(
            axis,
            space_index=property_index,
            strategy_id=("aggressive_builder"),
        )

        draw_houses(
            axis,
            space_index=property_index,
            count=4,
        )

        _text(
            axis,
            0.500,
            0.415,
            ("AGGRESSIVE BUILDER • " + board_spaces[property_index].label),
            size=20,
            color=(THEME.primary_text),
            weight="bold",
            ha="center",
            outlined=True,
            zorder=78,
        )

        _text(
            axis,
            0.500,
            0.375,
            "4 DEVELOPMENTS ADDED",
            size=24,
            color=(THEME.gold),
            weight="bold",
            ha="center",
            outlined=True,
            zorder=78,
        )

        draw_liquidity(
            axis,
            strategy=("aggressive_builder"),
            fraction=0.31,
            y=0.175,
        )

    elif frame_key == "07_survival":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Aggressive Builder burns through cash. Cash Protector stays liquid."),
        )

        draw_bankruptcy(
            axis,
            "aggressive_builder",
        )

        draw_liquidity(
            axis,
            strategy="cash_protector",
            fraction=0.78,
            y=0.165,
        )

    elif frame_key == "08_scale":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            "10,000 games are evidence.",
        )

        ranking = _ranking(context)

        for row in range(3):
            for column in range(3):
                _mini_board(
                    axis,
                    x=(0.135 + column * 0.255),
                    y=(0.225 + row * 0.205),
                    width=0.190,
                    ranking=ranking,
                )

        _text(
            axis,
            0.500,
            0.170,
            ("Each board repeats the same four strategies • ordered here by win rate"),
            size=16,
            color=(THEME.secondary_text),
            weight="bold",
            ha="center",
            zorder=85,
        )

    elif frame_key == "09_counter":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Balanced seats. Frozen rules. Deterministic seeds."),
        )

        _panel(
            axis,
            x=0.175,
            y=0.270,
            width=0.650,
            height=0.370,
            facecolor="#091526",
            zorder=36,
        )

        _text(
            axis,
            0.500,
            0.490,
            f"{context.game_count:,}",
            size=102,
            color=(THEME.gold),
            weight="bold",
            ha="center",
            outlined=True,
            zorder=75,
        )

        _text(
            axis,
            0.500,
            0.365,
            "COMPLETED GAMES",
            size=23,
            color=(THEME.secondary_text),
            weight="bold",
            ha="center",
            zorder=75,
        )

    elif frame_key == "10_leaderboard":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Win rate with independently verified 95% Wilson intervals."),
        )

        _leaderboard(
            axis,
            context,
        )

    elif frame_key == "11_risk_reward":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            "Win rate alone hides the risk.",
        )

        _risk_reward_panel(
            axis,
            context,
        )

    elif frame_key == "12_result":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Numerical ranking and statistical evidence are not the same thing."),
        )

        _panel(
            axis,
            x=0.130,
            y=0.235,
            width=0.740,
            height=0.455,
            facecolor="#091526",
            zorder=36,
        )

        if context.headline_winner is not None:
            winner = context.headline_winner

            _text(
                axis,
                0.500,
                0.610,
                STRATEGY_NAMES[winner].upper(),
                size=34,
                color=(THEME.primary_text),
                weight="bold",
                ha="center",
                zorder=75,
            )

            axis.add_patch(
                Rectangle(
                    (
                        0.355,
                        0.576,
                    ),
                    0.290,
                    0.006,
                    facecolor=(STRATEGY_COLORS[winner]),
                    edgecolor="none",
                    transform=(axis.transAxes),
                    zorder=70,
                )
            )

            draw_piece(
                axis,
                winner,
                (
                    0.500,
                    0.475,
                ),
                scale=2.30,
            )

            _text(
                axis,
                0.500,
                0.335,
                "STATISTICALLY SUPPORTED WINNER",
                size=21,
                color=(THEME.gold),
                weight="bold",
                ha="center",
                zorder=75,
            )

        else:
            leader = context.numerical_leader if context.numerical_leader is not None else "none"

            _text(
                axis,
                0.500,
                0.575,
                "NO SINGLE SUPPORTED WINNER",
                size=29,
                color=(THEME.gold),
                weight="bold",
                ha="center",
                zorder=75,
            )

            if leader in STRATEGY_NAMES:
                draw_piece(
                    axis,
                    leader,
                    (
                        0.500,
                        0.455,
                    ),
                    scale=1.85,
                )

            _text(
                axis,
                0.500,
                0.350,
                (
                    "Numerical leader: "
                    + STRATEGY_NAMES.get(
                        leader,
                        leader,
                    )
                ),
                size=19,
                color=(THEME.primary_text),
                weight="bold",
                ha="center",
                zorder=75,
            )

            _text(
                axis,
                0.500,
                0.300,
                ("The evidence did not support a stronger categorical claim."),
                size=16,
                color=(THEME.secondary_text),
                weight="bold",
                ha="center",
                zorder=75,
            )

    elif frame_key == "13_footer":
        _headline(
            axis,
            FRAME_TITLES[frame_key],
            ("Every number shown here comes from the frozen Step 6 run."),
        )

        _panel(
            axis,
            x=0.090,
            y=0.190,
            width=0.820,
            height=0.610,
            facecolor="#091526",
            zorder=36,
        )

        entries = (
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
                "2,500 / strategy / seat",
            ),
            (
                "AGENTS",
                "deterministic rule-based policies",
            ),
            (
                "UNCERTAINTY",
                "Wilson 95% confidence intervals",
            ),
            (
                "PAIRWISE",
                "exact binomial + Holm correction",
            ),
        )

        for index, (
            label,
            value,
        ) in enumerate(entries):
            y = 0.705 - index * 0.081

            _text(
                axis,
                0.170,
                y,
                label,
                size=15,
                color=(THEME.cyan),
                weight="bold",
                zorder=68,
            )

            _text(
                axis,
                0.415,
                y,
                value,
                size=19,
                color=(THEME.primary_text),
                weight="bold",
                zorder=68,
            )

    else:
        raise ValueError(f"unknown frame key: {frame_key}")

    _footer(axis)

    _save(
        figure,
        path,
    )


# =====================================================================
# 7.43-7.44 - FRAME GENERATION / HASHING
# =====================================================================


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def render_preview_frame_set(
    *,
    context: PreviewContext,
    board_spaces: Sequence[BoardSpaceVisual],
    output_directory: Path,
    show_progress: bool = True,
) -> dict[str, str]:
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

        output_path = output_directory / (moment.key + ".png")

        render_preview_frame(
            frame_key=(moment.key),
            context=context,
            board_spaces=board_spaces,
            path=output_path,
        )

        hashes[moment.key] = sha256_file(output_path)

    manifest = {
        "schema_version": "4.0",
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "frame_count": total,
        "piece_designs": (STRATEGY_PIECES),
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

    if show_progress:
        print(
            "[RENDER] V4 preview set complete",
            flush=True,
        )

    return hashes
