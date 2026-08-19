"""Square six-panel visualization framework for Bayesian Dice Detective."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.text import Text

from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    PAIR_CASE_IDS,
    DecisionState,
    DiceModelError,
    PairExperimentDefinition,
    PixelRegion,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pair_inference import (
    PairInferenceRecord,
    PairInferenceResult,
)

FRAME_WIDTH_PX = 1080
FRAME_HEIGHT_PX = 1080
FRAME_DPI = 100

PANEL_BACKGROUND = "#111827"
CANVAS_BACKGROUND = "#090D14"
GRID_COLOR = "#374151"
TEXT_COLOR = "#F9FAFB"
MUTED_TEXT_COLOR = "#9CA3AF"
FAIR_COLOR = "#4ADE80"
UNCERTAIN_COLOR = "#FBBF24"
LOADED_COLOR = "#FB7185"
GAUGE_BACKGROUND = "#273244"
COUNT_BAR_COLOR = "#60A5FA"
TRAJECTORY_COLOR = "#C084FC"
RESULT_BACKGROUND = "#0F172A"

TEXT_BOUND_TOLERANCE_PX = 1.5
AXES_BOUND_TOLERANCE_PX = 1.5


class PairVisualizationError(DiceModelError):
    """Raised when the pair visualization contract is violated."""


@dataclass(frozen=True, slots=True)
class PixelBounds:
    """One region in display coordinates with origin at bottom-left."""

    left: float
    bottom: float
    right: float
    top: float

    def __post_init__(self) -> None:
        if not (
            math.isfinite(self.left)
            and math.isfinite(self.bottom)
            and math.isfinite(self.right)
            and math.isfinite(self.top)
        ):
            raise PairVisualizationError("pixel bounds must be finite")

        if self.right <= self.left:
            raise PairVisualizationError("pixel bounds must have positive width")

        if self.top <= self.bottom:
            raise PairVisualizationError("pixel bounds must have positive height")

    @property
    def width(self) -> float:
        """Return bounds width."""
        return self.right - self.left

    @property
    def height(self) -> float:
        """Return bounds height."""
        return self.top - self.bottom


@dataclass(frozen=True, slots=True)
class TrackedText:
    """Text artist paired with its allowed region and overlap group."""

    name: str
    artist: Text
    allowed_bounds: PixelBounds
    overlap_group: str | None = None


@dataclass(frozen=True, slots=True)
class TrackedAxes:
    """Axes paired with the exact region it must occupy."""

    name: str
    axes: Axes
    expected_bounds: PixelBounds


@dataclass(frozen=True, slots=True)
class FrameValidationIssue:
    """One deterministic frame-layout failure."""

    check_id: str
    detail: str


@dataclass(frozen=True, slots=True)
class FrameValidationReport:
    """Automated geometry and text-layout validation result."""

    roll_index: int
    issues: tuple[
        FrameValidationIssue,
        ...,
    ]

    @property
    def passed(self) -> bool:
        """Return True when no validation issue exists."""
        return not self.issues


@dataclass(frozen=True, slots=True)
class PairDashboardFrame:
    """Rendered in-memory frame and validation metadata."""

    figure: Figure
    roll_index: int
    tracked_text: tuple[
        TrackedText,
        ...,
    ]
    tracked_axes: tuple[
        TrackedAxes,
        ...,
    ]


@dataclass(frozen=True, slots=True)
class PairFrameRenderResult:
    """Saved preview frame and its automated validation report."""

    path: Path
    roll_index: int
    validation: FrameValidationReport


def pixel_region_to_display_bounds(
    region: PixelRegion,
) -> PixelBounds:
    """Convert top-left contract coordinates into Matplotlib display coordinates."""
    return PixelBounds(
        left=float(region.x_px),
        bottom=float(FRAME_HEIGHT_PX - region.y_px - region.height_px),
        right=float(region.x_px + region.width_px),
        top=float(FRAME_HEIGHT_PX - region.y_px),
    )


def pixel_bounds_to_figure_rect(
    bounds: PixelBounds,
) -> tuple[
    float,
    float,
    float,
    float,
]:
    """Convert display-pixel bounds to normalized figure coordinates."""
    return (
        bounds.left / FRAME_WIDTH_PX,
        bounds.bottom / FRAME_HEIGHT_PX,
        bounds.width / FRAME_WIDTH_PX,
        bounds.height / FRAME_HEIGHT_PX,
    )


def panel_region(
    experiment: PairExperimentDefinition,
    case_id: str,
) -> PixelRegion:
    """Return the exact 360x500 top-left pixel region for one case panel."""
    placement = next(
        (item for item in experiment.video.panel_placements if item.case_id == case_id),
        None,
    )

    if placement is None:
        raise PairVisualizationError(f"missing panel placement for {case_id}")

    return PixelRegion(
        x_px=(
            experiment.video.middle_grid.x_px + placement.column * experiment.video.panel_width_px
        ),
        y_px=(experiment.video.middle_grid.y_px + placement.row * experiment.video.panel_height_px),
        width_px=(experiment.video.panel_width_px),
        height_px=(experiment.video.panel_height_px),
    )


def result_cell_region(
    experiment: PairExperimentDefinition,
    index: int,
) -> PixelRegion:
    """Return one exact 180x40 result-strip cell."""
    if not (0 <= index < len(PAIR_CASE_IDS)):
        raise PairVisualizationError("result cell index is outside 0..5")

    return PixelRegion(
        x_px=(experiment.video.result_strip.x_px + index * experiment.video.result_cell_width_px),
        y_px=(experiment.video.result_strip.y_px),
        width_px=(experiment.video.result_cell_width_px),
        height_px=(experiment.video.result_strip.height_px),
    )


def synchronized_pair_records(
    inference: PairInferenceResult,
    roll_index: int,
) -> dict[
    str,
    PairInferenceRecord,
]:
    """Return the same one-based inference roll from all six cases."""
    if not (1 <= roll_index <= 10_000):
        raise PairVisualizationError("display roll_index must be between 1 and 10,000")

    records = {
        case_id: inference.case(case_id).records[roll_index - 1] for case_id in PAIR_CASE_IDS
    }

    if {record.roll_index for record in records.values()} != {roll_index}:
        raise PairVisualizationError("six pair panels are not synchronized")

    return records


def preview_roll_indices(
    inference: PairInferenceResult,
) -> tuple[int, ...]:
    """Return deterministic preview rolls including every stable decision."""
    rolls: set[int] = {
        1,
        10,
        100,
        1_000,
        10_000,
    }

    for case_id in PAIR_CASE_IDS:
        stable = inference.case(case_id).stable_decision_roll

        if stable is not None:
            rolls.add(stable)

    return tuple(sorted(rolls))


def _decision_color(
    state: DecisionState,
) -> str:
    if state is DecisionState.FAIR:
        return FAIR_COLOR

    if state is DecisionState.LOADED:
        return LOADED_COLOR

    return UNCERTAIN_COLOR


def _trajectory_records(
    records: Sequence[PairInferenceRecord],
    *,
    maximum_points: int = 240,
) -> tuple[
    PairInferenceRecord,
    ...,
]:
    """Sample only real Bayesian states without interpolating posterior values."""
    if not records:
        raise PairVisualizationError("trajectory requires at least one record")

    if len(records) <= maximum_points:
        return tuple(records)

    last_index = len(records) - 1

    indices = {round(index * last_index / (maximum_points - 1)) for index in range(maximum_points)}

    indices.add(last_index)

    return tuple(records[index] for index in sorted(indices))


def _configure_axes(
    axes: Axes,
    *,
    facecolor: str,
) -> None:
    """Apply deterministic panel-level styling."""
    axes.set_xlim(
        0.0,
        1.0,
    )

    axes.set_ylim(
        0.0,
        1.0,
    )

    axes.set_xticks([])

    axes.set_yticks([])

    axes.set_facecolor(facecolor)

    for spine in axes.spines.values():
        spine.set_edgecolor(GRID_COLOR)

        spine.set_linewidth(0.8)


def _add_panel_text(
    axes: Axes,
    *,
    text: str,
    x: float,
    y: float,
    fontsize: float,
    weight: str = "normal",
    color: str = TEXT_COLOR,
    horizontal_alignment: str = "left",
) -> Text:
    return axes.text(
        x,
        y,
        text,
        transform=axes.transAxes,
        ha=horizontal_alignment,
        va="center",
        fontsize=fontsize,
        fontweight=weight,
        color=color,
        clip_on=True,
    )


def _render_pair_panel(
    axes: Axes,
    *,
    case_id: str,
    record: PairInferenceRecord,
    inference: PairInferenceResult,
    allowed_bounds: PixelBounds,
) -> tuple[
    TrackedText,
    ...,
]:
    """Render one reusable analytical case panel."""
    _configure_axes(
        axes,
        facecolor=PANEL_BACKGROUND,
    )

    case_result = inference.case(case_id)

    tracked: list[TrackedText] = []

    title = _add_panel_text(
        axes,
        text=case_id,
        x=0.04,
        y=0.955,
        fontsize=10.0,
        weight="bold",
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.title",
            artist=title,
            allowed_bounds=allowed_bounds,
            overlap_group=f"{case_id}.top",
        )
    )

    status = _add_panel_text(
        axes,
        text=(f"Roll {record.roll_index:,}   P(load) {record.posterior_loaded:.3f}"),
        x=0.04,
        y=0.910,
        fontsize=6.5,
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.status",
            artist=status,
            allowed_bounds=allowed_bounds,
            overlap_group=f"{case_id}.top",
        )
    )

    decision = _add_panel_text(
        axes,
        text=record.decision_state.value,
        x=0.96,
        y=0.955,
        fontsize=7.0,
        weight="bold",
        color=_decision_color(record.decision_state),
        horizontal_alignment="right",
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.decision",
            artist=decision,
            allowed_bounds=allowed_bounds,
            overlap_group=f"{case_id}.top",
        )
    )

    gauge_label = _add_panel_text(
        axes,
        text="LOADED POSTERIOR",
        x=0.04,
        y=0.835,
        fontsize=5.0,
        color=MUTED_TEXT_COLOR,
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.gauge_label",
            artist=gauge_label,
            allowed_bounds=allowed_bounds,
        )
    )

    axes.add_patch(
        Rectangle(
            (
                0.04,
                0.775,
            ),
            0.92,
            0.035,
            facecolor=GAUGE_BACKGROUND,
            edgecolor=GRID_COLOR,
            linewidth=0.5,
        )
    )

    axes.add_patch(
        Rectangle(
            (
                0.04,
                0.775,
            ),
            0.92 * record.posterior_loaded,
            0.035,
            facecolor=_decision_color(record.decision_state),
            edgecolor="none",
        )
    )

    counts_label = _add_panel_text(
        axes,
        text="CUMULATIVE SUM COUNTS",
        x=0.04,
        y=0.720,
        fontsize=5.0,
        color=MUTED_TEXT_COLOR,
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.counts_label",
            artist=counts_label,
            allowed_bounds=allowed_bounds,
        )
    )

    maximum_count = max(record.cumulative_sum_counts)

    count_ceiling = max(
        maximum_count,
        1,
    )

    count_area_bottom = 0.385
    count_area_height = 0.275

    bar_width = 0.057
    gap = 0.024
    start_x = 0.057

    for index, count in enumerate(record.cumulative_sum_counts):
        x = start_x + index * (bar_width + gap)

        bar_height = count_area_height * count / count_ceiling

        axes.add_patch(
            Rectangle(
                (
                    x,
                    count_area_bottom,
                ),
                bar_width,
                bar_height,
                facecolor=COUNT_BAR_COLOR,
                edgecolor="none",
            )
        )

        sum_label = _add_panel_text(
            axes,
            text=str(index + 2),
            x=(x + bar_width / 2.0),
            y=0.358,
            fontsize=4.0,
            color=MUTED_TEXT_COLOR,
            horizontal_alignment="center",
        )

        tracked.append(
            TrackedText(
                name=(f"{case_id}.sum_label_{index + 2}"),
                artist=sum_label,
                allowed_bounds=allowed_bounds,
            )
        )

    trajectory_label = _add_panel_text(
        axes,
        text="P(LOAD) TRAJECTORY",
        x=0.04,
        y=0.310,
        fontsize=5.0,
        color=MUTED_TEXT_COLOR,
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.trajectory_label",
            artist=trajectory_label,
            allowed_bounds=allowed_bounds,
        )
    )

    trajectory = _trajectory_records(case_result.records[: record.roll_index])

    x_values: tuple[float, ...]

    if len(trajectory) == 1:
        x_values = (0.04,)
    else:
        first_roll = trajectory[0].roll_index

        last_roll = trajectory[-1].roll_index

        denominator = max(
            last_roll - first_roll,
            1,
        )

        x_values = tuple(
            0.04 + 0.92 * (item.roll_index - first_roll) / denominator for item in trajectory
        )

    y_values = tuple(0.075 + 0.190 * item.posterior_loaded for item in trajectory)

    axes.plot(
        x_values,
        y_values,
        linewidth=1.2,
        color=TRAJECTORY_COLOR,
        clip_on=True,
    )

    axes.plot(
        (
            0.04,
            0.96,
        ),
        (
            0.075 + 0.190 * 0.05,
            0.075 + 0.190 * 0.05,
        ),
        linewidth=0.45,
        linestyle="--",
        color=FAIR_COLOR,
        alpha=0.7,
    )

    axes.plot(
        (
            0.04,
            0.96,
        ),
        (
            0.075 + 0.190 * 0.95,
            0.075 + 0.190 * 0.95,
        ),
        linewidth=0.45,
        linestyle="--",
        color=LOADED_COLOR,
        alpha=0.7,
    )

    stable = case_result.stable_decision_roll

    stable_text = _add_panel_text(
        axes,
        text=("Stable: " + ("—" if stable is None else f"{stable:,}")),
        x=0.96,
        y=0.310,
        fontsize=5.0,
        color=MUTED_TEXT_COLOR,
        horizontal_alignment="right",
    )

    tracked.append(
        TrackedText(
            name=f"{case_id}.stable",
            artist=stable_text,
            allowed_bounds=allowed_bounds,
        )
    )

    return tuple(tracked)


def _render_heading(
    axes: Axes,
    *,
    experiment: PairExperimentDefinition,
    allowed_bounds: PixelBounds,
) -> tuple[
    TrackedText,
    ...,
]:
    _configure_axes(
        axes,
        facecolor=CANVAS_BACKGROUND,
    )

    title = axes.text(
        0.012,
        0.5,
        experiment.viewer_question,
        transform=axes.transAxes,
        ha="left",
        va="center",
        fontsize=10.5,
        fontweight="bold",
        color=TEXT_COLOR,
        clip_on=True,
    )

    footer = axes.text(
        0.988,
        0.5,
        experiment.video.technical_footer,
        transform=axes.transAxes,
        ha="right",
        va="center",
        fontsize=4.7,
        color=MUTED_TEXT_COLOR,
        clip_on=True,
    )

    return (
        TrackedText(
            name="heading.title",
            artist=title,
            allowed_bounds=allowed_bounds,
            overlap_group="heading",
        ),
        TrackedText(
            name="heading.footer",
            artist=footer,
            allowed_bounds=allowed_bounds,
            overlap_group="heading",
        ),
    )


def _render_result_strip(
    axes: Axes,
    *,
    experiment: PairExperimentDefinition,
    inference: PairInferenceResult,
) -> tuple[
    TrackedText,
    ...,
]:
    _configure_axes(
        axes,
        facecolor=RESULT_BACKGROUND,
    )

    tracked: list[TrackedText] = []

    for index, case_id in enumerate(PAIR_CASE_IDS):
        cell = result_cell_region(
            experiment,
            index,
        )

        cell_bounds = pixel_region_to_display_bounds(cell)

        x_start = index / len(PAIR_CASE_IDS)

        cell_width = 1.0 / len(PAIR_CASE_IDS)

        if index > 0:
            axes.plot(
                (
                    x_start,
                    x_start,
                ),
                (
                    0.0,
                    1.0,
                ),
                transform=axes.transAxes,
                color=GRID_COLOR,
                linewidth=0.6,
            )

        result = inference.case(case_id)

        stable = result.stable_decision_roll

        stable_label = "—" if stable is None else f"{stable:,}"

        label = f"{case_id} · R{stable_label} · P{result.final_posterior_loaded:.3f}"

        text = axes.text(
            (x_start + cell_width / 2.0),
            0.5,
            label,
            transform=axes.transAxes,
            ha="center",
            va="center",
            fontsize=5.2,
            fontweight="bold",
            color=_decision_color(result.final_decision_state),
            clip_on=True,
        )

        tracked.append(
            TrackedText(
                name=f"result.{case_id}",
                artist=text,
                allowed_bounds=cell_bounds,
                overlap_group="results",
            )
        )

    return tuple(tracked)


def build_pair_dashboard_frame(
    experiment: PairExperimentDefinition,
    inference: PairInferenceResult,
    *,
    roll_index: int,
) -> PairDashboardFrame:
    """Build one exact 1080x1080 synchronized analytical frame."""
    synchronized_pair_records(
        inference,
        roll_index,
    )

    figure = Figure(
        figsize=(
            FRAME_WIDTH_PX / FRAME_DPI,
            FRAME_HEIGHT_PX / FRAME_DPI,
        ),
        dpi=FRAME_DPI,
        facecolor=CANVAS_BACKGROUND,
    )

    FigureCanvasAgg(figure)

    tracked_text: list[TrackedText] = []

    tracked_axes: list[TrackedAxes] = []

    heading_bounds = pixel_region_to_display_bounds(experiment.video.heading)

    heading_axes = figure.add_axes(pixel_bounds_to_figure_rect(heading_bounds))

    tracked_axes.append(
        TrackedAxes(
            name="heading",
            axes=heading_axes,
            expected_bounds=heading_bounds,
        )
    )

    tracked_text.extend(
        _render_heading(
            heading_axes,
            experiment=experiment,
            allowed_bounds=heading_bounds,
        )
    )

    records = synchronized_pair_records(
        inference,
        roll_index,
    )

    for case_id in PAIR_CASE_IDS:
        region = panel_region(
            experiment,
            case_id,
        )

        bounds = pixel_region_to_display_bounds(region)

        axes = figure.add_axes(pixel_bounds_to_figure_rect(bounds))

        tracked_axes.append(
            TrackedAxes(
                name=f"panel.{case_id}",
                axes=axes,
                expected_bounds=bounds,
            )
        )

        tracked_text.extend(
            _render_pair_panel(
                axes,
                case_id=case_id,
                record=records[case_id],
                inference=inference,
                allowed_bounds=bounds,
            )
        )

    result_bounds = pixel_region_to_display_bounds(experiment.video.result_strip)

    result_axes = figure.add_axes(pixel_bounds_to_figure_rect(result_bounds))

    tracked_axes.append(
        TrackedAxes(
            name="result_strip",
            axes=result_axes,
            expected_bounds=result_bounds,
        )
    )

    tracked_text.extend(
        _render_result_strip(
            result_axes,
            experiment=experiment,
            inference=inference,
        )
    )

    return PairDashboardFrame(
        figure=figure,
        roll_index=roll_index,
        tracked_text=tuple(tracked_text),
        tracked_axes=tuple(tracked_axes),
    )


def _artist_bounds(
    text: Text,
) -> PixelBounds:
    bbox = text.get_window_extent()

    return PixelBounds(
        left=float(bbox.x0),
        bottom=float(bbox.y0),
        right=float(bbox.x1),
        top=float(bbox.y1),
    )


def _axes_bounds(
    axes: Axes,
) -> PixelBounds:
    bbox = axes.get_window_extent()

    return PixelBounds(
        left=float(bbox.x0),
        bottom=float(bbox.y0),
        right=float(bbox.x1),
        top=float(bbox.y1),
    )


def _contains(
    outer: PixelBounds,
    inner: PixelBounds,
    *,
    tolerance: float,
) -> bool:
    return (
        inner.left >= outer.left - tolerance
        and inner.right <= outer.right + tolerance
        and inner.bottom >= outer.bottom - tolerance
        and inner.top <= outer.top + tolerance
    )


def _bounds_match(
    expected: PixelBounds,
    actual: PixelBounds,
    *,
    tolerance: float,
) -> bool:
    return all(
        abs(first - second) <= tolerance
        for first, second in (
            (
                expected.left,
                actual.left,
            ),
            (
                expected.bottom,
                actual.bottom,
            ),
            (
                expected.right,
                actual.right,
            ),
            (
                expected.top,
                actual.top,
            ),
        )
    )


def _overlap_area(
    first: PixelBounds,
    second: PixelBounds,
) -> float:
    width = max(
        0.0,
        min(
            first.right,
            second.right,
        )
        - max(
            first.left,
            second.left,
        ),
    )

    height = max(
        0.0,
        min(
            first.top,
            second.top,
        )
        - max(
            first.bottom,
            second.bottom,
        ),
    )

    return width * height


def validate_pair_dashboard_frame(
    frame: PairDashboardFrame,
) -> FrameValidationReport:
    """Validate exact geometry, clipping, and selected text-overlap constraints."""
    canvas = frame.figure.canvas

    canvas.draw()

    issues: list[FrameValidationIssue] = []

    width, height = canvas.get_width_height()

    if (
        width,
        height,
    ) != (
        FRAME_WIDTH_PX,
        FRAME_HEIGHT_PX,
    ):
        issues.append(
            FrameValidationIssue(
                check_id="canvas.dimensions",
                detail=(f"expected 1080x1080, found {width}x{height}"),
            )
        )

    for tracked_axes in frame.tracked_axes:
        actual = _axes_bounds(tracked_axes.axes)

        if not _bounds_match(
            tracked_axes.expected_bounds,
            actual,
            tolerance=AXES_BOUND_TOLERANCE_PX,
        ):
            issues.append(
                FrameValidationIssue(
                    check_id=(f"axes.{tracked_axes.name}.geometry"),
                    detail=(f"{tracked_axes.name} axes do not match contract bounds"),
                )
            )

    text_bounds: dict[
        str,
        PixelBounds,
    ] = {}

    for tracked_text in frame.tracked_text:
        actual = _artist_bounds(tracked_text.artist)

        text_bounds[tracked_text.name] = actual

        if not _contains(
            tracked_text.allowed_bounds,
            actual,
            tolerance=TEXT_BOUND_TOLERANCE_PX,
        ):
            issues.append(
                FrameValidationIssue(
                    check_id=(f"text.{tracked_text.name}.bounds"),
                    detail=(f"{tracked_text.name} text escapes its assigned region"),
                )
            )

    groups: dict[
        str,
        list[TrackedText],
    ] = {}

    for tracked_text in frame.tracked_text:
        if tracked_text.overlap_group is None:
            continue

        groups.setdefault(
            tracked_text.overlap_group,
            [],
        ).append(tracked_text)

    for group_name, members in groups.items():
        for first_index, first in enumerate(members):
            for second in members[first_index + 1 :]:
                overlap = _overlap_area(
                    text_bounds[first.name],
                    text_bounds[second.name],
                )

                if overlap > 0.25:
                    issues.append(
                        FrameValidationIssue(
                            check_id=(f"text_overlap.{group_name}.{first.name}.{second.name}"),
                            detail=(f"{first.name} and {second.name} overlap by {overlap:.2f} px²"),
                        )
                    )

    return FrameValidationReport(
        roll_index=frame.roll_index,
        issues=tuple(issues),
    )


def render_pair_dashboard_frame(
    experiment: PairExperimentDefinition,
    inference: PairInferenceResult,
    *,
    roll_index: int,
    output_path: Path | str,
) -> PairFrameRenderResult:
    """Render, validate, and save one synchronized dashboard preview frame."""
    frame = build_pair_dashboard_frame(
        experiment,
        inference,
        roll_index=roll_index,
    )

    validation = validate_pair_dashboard_frame(frame)

    if not validation.passed:
        details = "; ".join((f"{issue.check_id}: {issue.detail}") for issue in validation.issues)

        raise PairVisualizationError("frame validation failed: " + details)

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.figure.savefig(
        path,
        dpi=FRAME_DPI,
        facecolor=(frame.figure.get_facecolor()),
        edgecolor="none",
    )

    frame.figure.clear()

    return PairFrameRenderResult(
        path=path,
        roll_index=roll_index,
        validation=validation,
    )
