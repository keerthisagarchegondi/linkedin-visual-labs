"""Centralized plotting theme and reusable visual components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text

from linkedin_visual_labs.common.validation import (
    ValidationError,
    require_probability,
)

CANVAS_WIDTH_PX = 1080
CANVAS_HEIGHT_PX = 1350
CANVAS_DPI = 100
SAFE_MARGIN_PX = 60

LineStyle = Literal[
    "-",
    "solid",
    "--",
    "dashed",
    "-.",
    "dashdot",
    ":",
    "dotted",
    "",
    "none",
    " ",
    "None",
]

LegendLocation = Literal[
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
    "best",
]


@dataclass(frozen=True, slots=True)
class CanvasSpec:
    """Pixel and safe-area contract for a rendered visual."""

    width_px: int = CANVAS_WIDTH_PX
    height_px: int = CANVAS_HEIGHT_PX
    dpi: int = CANVAS_DPI
    safe_margin_px: int = SAFE_MARGIN_PX

    def __post_init__(self) -> None:
        if self.width_px <= 0:
            raise ValidationError("canvas width_px must be positive")

        if self.height_px <= 0:
            raise ValidationError("canvas height_px must be positive")

        if self.dpi <= 0:
            raise ValidationError("canvas dpi must be positive")

        if self.safe_margin_px < 0:
            raise ValidationError("canvas safe_margin_px must be non-negative")

        if (2 * self.safe_margin_px) >= self.width_px:
            raise ValidationError("horizontal safe margins consume the entire canvas")

        if (2 * self.safe_margin_px) >= self.height_px:
            raise ValidationError("vertical safe margins consume the entire canvas")

    @property
    def figsize_inches(self) -> tuple[float, float]:
        """Return Matplotlib figure dimensions in inches."""
        return (
            self.width_px / self.dpi,
            self.height_px / self.dpi,
        )

    @property
    def left_fraction(self) -> float:
        """Safe left edge in figure-normalized coordinates."""
        return self.safe_margin_px / self.width_px

    @property
    def right_fraction(self) -> float:
        """Safe right edge in figure-normalized coordinates."""
        return 1.0 - self.left_fraction

    @property
    def bottom_fraction(self) -> float:
        """Safe bottom edge in figure-normalized coordinates."""
        return self.safe_margin_px / self.height_px

    @property
    def top_fraction(self) -> float:
        """Safe top edge in figure-normalized coordinates."""
        return 1.0 - self.bottom_fraction


@dataclass(frozen=True, slots=True)
class VisualTheme:
    """Repository-wide visual identity."""

    background: str = "#0B1020"
    surface: str = "#151C30"
    surface_alt: str = "#1D2740"

    text_primary: str = "#F4F7FB"
    text_secondary: str = "#AEBBD0"
    text_muted: str = "#7D8CA7"

    grid: str = "#33405A"

    accent_primary: str = "#5CC8FF"
    accent_secondary: str = "#A78BFA"

    success: str = "#61D095"
    warning: str = "#F6C85F"
    danger: str = "#FF6B6B"

    route_shortest: str = "#5CC8FF"
    route_fastest: str = "#F6C85F"
    route_safest: str = "#61D095"

    categorical_1: str = "#5CC8FF"
    categorical_2: str = "#A78BFA"
    categorical_3: str = "#F6C85F"
    categorical_4: str = "#61D095"
    categorical_5: str = "#FF8A65"
    categorical_6: str = "#F06292"

    font_family: str = "DejaVu Sans"

    headline_size: int = 44
    subtitle_size: int = 26
    body_size: int = 22
    metric_value_size: int = 34
    metric_label_size: int = 18
    footer_size: int = 16


@dataclass(frozen=True, slots=True)
class RouteStyle:
    """Visual specification for one route objective."""

    key: str
    label: str
    color: str
    linestyle: LineStyle
    linewidth: float


@dataclass(frozen=True, slots=True)
class MetricCardArtists:
    """Artists created for one metric card."""

    label: Text
    value: Text


@dataclass(frozen=True, slots=True)
class ProgressGaugeArtists:
    """Artists created for one progress gauge."""

    background: Rectangle
    fill: Rectangle
    label: Text


DEFAULT_CANVAS = CanvasSpec()
DEFAULT_THEME = VisualTheme()


def route_style(
    objective: str,
    *,
    theme: VisualTheme = DEFAULT_THEME,
) -> RouteStyle:
    """Return centralized styling for a route objective."""
    styles = {
        "shortest": RouteStyle(
            key="shortest",
            label="Shortest",
            color=theme.route_shortest,
            linestyle="-",
            linewidth=5.0,
        ),
        "fastest": RouteStyle(
            key="fastest",
            label="Fastest",
            color=theme.route_fastest,
            linestyle="--",
            linewidth=5.0,
        ),
        "safest": RouteStyle(
            key="safest",
            label="Safest",
            color=theme.route_safest,
            linestyle="-.",
            linewidth=5.0,
        ),
    }

    try:
        return styles[objective]
    except KeyError as exc:
        allowed = ", ".join(styles)
        raise ValidationError(
            f"unsupported route objective {objective!r}; allowed: {allowed}"
        ) from exc


def categorical_colors(
    *,
    theme: VisualTheme = DEFAULT_THEME,
) -> tuple[str, ...]:
    """Return the centralized categorical palette."""
    return (
        theme.categorical_1,
        theme.categorical_2,
        theme.categorical_3,
        theme.categorical_4,
        theme.categorical_5,
        theme.categorical_6,
    )


def create_canvas(
    *,
    spec: CanvasSpec = DEFAULT_CANVAS,
    theme: VisualTheme = DEFAULT_THEME,
) -> tuple[Figure, Axes]:
    """Create one headless Matplotlib canvas using repository defaults."""
    figure = Figure(
        figsize=spec.figsize_inches,
        dpi=spec.dpi,
        facecolor=theme.background,
    )

    FigureCanvasAgg(figure)

    width_fraction = spec.right_fraction - spec.left_fraction
    height_fraction = spec.top_fraction - spec.bottom_fraction

    rect = (
        spec.left_fraction,
        spec.bottom_fraction,
        width_fraction,
        height_fraction,
    )

    axes = figure.add_axes(rect)

    axes.set_facecolor(theme.background)

    for spine in axes.spines.values():
        spine.set_color(theme.grid)

    axes.tick_params(
        colors=theme.text_secondary,
        labelsize=theme.footer_size,
    )

    axes.xaxis.label.set_color(theme.text_secondary)
    axes.yaxis.label.set_color(theme.text_secondary)
    axes.title.set_color(theme.text_primary)

    return figure, axes


def add_title_block(
    axes: Axes,
    headline: str,
    *,
    subtitle: str | None = None,
    theme: VisualTheme = DEFAULT_THEME,
) -> tuple[Text, Text | None]:
    """Add consistently styled headline and optional subtitle."""
    headline_artist = axes.text(
        0.0,
        1.0,
        headline,
        transform=axes.transAxes,
        ha="left",
        va="top",
        color=theme.text_primary,
        fontsize=theme.headline_size,
        fontfamily=theme.font_family,
        fontweight="bold",
    )

    subtitle_artist: Text | None = None

    if subtitle is not None:
        subtitle_artist = axes.text(
            0.0,
            0.945,
            subtitle,
            transform=axes.transAxes,
            ha="left",
            va="top",
            color=theme.text_secondary,
            fontsize=theme.subtitle_size,
            fontfamily=theme.font_family,
        )

    return headline_artist, subtitle_artist


def add_metric_card(
    axes: Axes,
    *,
    x: float,
    y: float,
    label: str,
    value: str,
    theme: VisualTheme = DEFAULT_THEME,
) -> MetricCardArtists:
    """Draw a reusable compact metric card in axes coordinates."""
    value_artist = axes.text(
        x,
        y,
        value,
        transform=axes.transAxes,
        ha="left",
        va="top",
        color=theme.text_primary,
        fontsize=theme.metric_value_size,
        fontfamily=theme.font_family,
        fontweight="bold",
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": theme.surface,
            "edgecolor": theme.grid,
            "linewidth": 1.5,
        },
    )

    label_artist = axes.text(
        x,
        y - 0.065,
        label,
        transform=axes.transAxes,
        ha="left",
        va="top",
        color=theme.text_secondary,
        fontsize=theme.metric_label_size,
        fontfamily=theme.font_family,
    )

    return MetricCardArtists(
        label=label_artist,
        value=value_artist,
    )


def add_progress_gauge(
    axes: Axes,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    progress: float,
    label: str,
    theme: VisualTheme = DEFAULT_THEME,
) -> ProgressGaugeArtists:
    """Draw a normalized progress gauge in axes coordinates."""
    normalized = require_probability(
        progress,
        name="progress",
    )

    background = Rectangle(
        (x, y),
        width,
        height,
        transform=axes.transAxes,
        facecolor=theme.surface_alt,
        edgecolor=theme.grid,
        linewidth=1.0,
        clip_on=False,
    )

    fill = Rectangle(
        (x, y),
        width * normalized,
        height,
        transform=axes.transAxes,
        facecolor=theme.accent_primary,
        edgecolor="none",
        clip_on=False,
    )

    axes.add_patch(background)
    axes.add_patch(fill)

    label_artist = axes.text(
        x,
        y + height + 0.012,
        label,
        transform=axes.transAxes,
        ha="left",
        va="bottom",
        color=theme.text_secondary,
        fontsize=theme.metric_label_size,
        fontfamily=theme.font_family,
    )

    return ProgressGaugeArtists(
        background=background,
        fill=fill,
        label=label_artist,
    )


def add_route_legend(
    axes: Axes,
    *,
    location: LegendLocation = "upper right",
    theme: VisualTheme = DEFAULT_THEME,
) -> Legend:
    """Add a centralized Shortest/Fastest/Safest route legend."""
    handles: list[Line2D] = []
    labels: list[str] = []

    for objective in (
        "shortest",
        "fastest",
        "safest",
    ):
        style = route_style(
            objective,
            theme=theme,
        )

        handles.append(
            Line2D(
                [0],
                [0],
                color=style.color,
                linestyle=style.linestyle,
                linewidth=style.linewidth,
            )
        )

        labels.append(style.label)

    legend: Legend = axes.legend(
        handles,
        labels,
        loc=location,
        frameon=True,
        facecolor=theme.surface,
        edgecolor=theme.grid,
        fontsize=theme.metric_label_size,
    )

    for text in legend.get_texts():
        text.set_color(theme.text_primary)

    return legend
