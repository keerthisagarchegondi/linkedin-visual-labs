"""Typed domain models for Project 2 — Zombie Escape."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any, Self


class ZombieModelError(ValueError):
    """Base domain-model validation error."""


class ZombieConfigError(ZombieModelError):
    """Raised when the authoritative YAML contract is invalid."""


class CityId(StrEnum):
    """Canonical showcase-city identifiers."""

    PHOENIX = "phoenix"
    NEW_YORK = "new_york"
    CHICAGO = "chicago"


class MethodId(StrEnum):
    """Canonical headline planner identifiers."""

    DIJKSTRA = "dijkstra"
    ML = "ml"
    DL = "dl"


class TerrainType(StrEnum):
    """Supported deterministic city-grid terrain types."""

    BUILDING = "building"
    LOCAL_ROAD = "local_road"
    ARTERIAL = "arterial"
    SLOW_TERRAIN = "slow_terrain"
    OPEN_SPACE = "open_space"


class MovementRule(StrEnum):
    """Grid-neighbor movement contract."""

    FOUR_NEIGHBOR = "four_neighbor"


class RoutePlanner(StrEnum):
    """Supported route-planner identifiers."""

    DIJKSTRA = "dijkstra"
    ASTAR = "astar"


class RiskEstimator(StrEnum):
    """Supported risk-estimation strategies."""

    OBSERVED_VISIBLE_RISK = "observed_visible_risk"
    GRADIENT_BOOSTING = "gradient_boosting"
    CNN = "convolutional_neural_network"
    TRUE_HIDDEN_RISK = "true_hidden_risk"


class MethodCategory(StrEnum):
    """Headline-method categories."""

    DETERMINISTIC_BASELINE = "deterministic_baseline"
    CLASSICAL_MACHINE_LEARNING = "classical_machine_learning"
    DEEP_LEARNING = "deep_learning"


@dataclass(frozen=True, slots=True, order=True)
class GridPosition:
    """One logical cell position."""

    row: int
    column: int

    def __post_init__(self) -> None:
        if self.row < 0:
            raise ZombieModelError("GridPosition.row must be non-negative")

        if self.column < 0:
            raise ZombieModelError("GridPosition.column must be non-negative")


@dataclass(frozen=True, slots=True)
class PixelRegion:
    """One exact pixel-space rectangle."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0:
            raise ZombieModelError("PixelRegion coordinates must be non-negative")

        if self.width <= 0 or self.height <= 0:
            raise ZombieModelError("PixelRegion dimensions must be positive")

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


@dataclass(frozen=True, slots=True)
class GridDefinition:
    """Logical city-grid geometry."""

    rows: int
    columns: int
    movement: MovementRule
    allow_diagonal: bool
    step_distance: float

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.columns <= 0:
            raise ZombieModelError("Grid dimensions must be positive")

        if not isfinite(self.step_distance) or self.step_distance <= 0.0:
            raise ZombieModelError("Grid step_distance must be positive and finite")

        if self.movement is MovementRule.FOUR_NEIGHBOR and self.allow_diagonal:
            raise ZombieModelError("four_neighbor movement cannot allow diagonal movement")

    def contains(
        self,
        position: GridPosition,
    ) -> bool:
        """Return whether a position lies inside this grid."""
        return 0 <= position.row < self.rows and 0 <= position.column < self.columns


@dataclass(frozen=True, slots=True)
class RiskDefinition:
    """Risk-scale and planner-weight contract."""

    minimum: float
    maximum: float
    high_risk_threshold: float
    planner_risk_weight: float
    true_risk_visible_to_headline_methods: bool

    def __post_init__(self) -> None:
        values = (
            self.minimum,
            self.maximum,
            self.high_risk_threshold,
            self.planner_risk_weight,
        )

        if not all(isfinite(value) for value in values):
            raise ZombieModelError("Risk values must be finite")

        if self.minimum >= self.maximum:
            raise ZombieModelError("Risk minimum must be smaller than maximum")

        if not (self.minimum <= self.high_risk_threshold <= self.maximum):
            raise ZombieModelError("High-risk threshold must lie inside the risk range")

        if self.planner_risk_weight < 0.0:
            raise ZombieModelError("Planner risk weight must be non-negative")


@dataclass(frozen=True, slots=True)
class PlannerCostDefinition:
    """Common planner-objective contract."""

    formula: str
    same_formula_for_all_headline_methods: bool

    def __post_init__(self) -> None:
        if not self.formula.strip():
            raise ZombieModelError("Planner cost formula cannot be empty")


@dataclass(frozen=True, slots=True)
class TerrainDefinition:
    """Cost/traversability definition for one terrain type."""

    terrain_type: TerrainType
    traversable: bool
    speed_multiplier: float

    def __post_init__(self) -> None:
        if not isfinite(self.speed_multiplier) or self.speed_multiplier < 0.0:
            raise ZombieModelError("Terrain speed multiplier must be finite and non-negative")

        if self.traversable and self.speed_multiplier <= 0.0:
            raise ZombieModelError("Traversable terrain must have positive speed")

        if not self.traversable and self.speed_multiplier != 0.0:
            raise ZombieModelError("Impassable terrain must have zero speed")


@dataclass(frozen=True, slots=True)
class CityProfile:
    """Qualitative city-generation profile."""

    block_density: str
    intersection_density: str
    arterial_width: str
    choke_point_density: str
    hidden_risk_structure: str
    synthetic_barrier: str


@dataclass(frozen=True, slots=True)
class CityDefinition:
    """One deterministic showcase-city definition."""

    city_id: CityId
    display_name: str
    inspiration_only: bool
    seed: int
    start: GridPosition
    destination: GridPosition
    profile: CityProfile

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise ZombieModelError("City display_name cannot be empty")

        if self.seed < 0:
            raise ZombieModelError("City seed must be non-negative")

        if self.start == self.destination:
            raise ZombieModelError("City start and destination must differ")


@dataclass(frozen=True, slots=True)
class PlannerDefinition:
    """One headline planner definition."""

    method_id: MethodId
    display_name: str
    category: MethodCategory
    risk_estimator: RiskEstimator
    route_planner: RoutePlanner
    sees_true_hidden_risk: bool

    def __post_init__(self) -> None:
        if not self.display_name.strip():
            raise ZombieModelError("Planner display_name cannot be empty")


@dataclass(frozen=True, slots=True)
class OracleDefinition:
    """Perfect-information benchmark definition."""

    enabled: bool
    headline_contestant: bool
    display_name: str
    risk_estimator: RiskEstimator
    route_planner: RoutePlanner
    purpose: str


@dataclass(frozen=True, slots=True)
class TrainingSeeds:
    """Deterministic dataset/model-training seeds."""

    training: int
    validation: int
    benchmark: int
    ml_model: int
    dl_model: int

    def __post_init__(self) -> None:
        values = (
            self.training,
            self.validation,
            self.benchmark,
            self.ml_model,
            self.dl_model,
        )

        if any(value < 0 for value in values):
            raise ZombieModelError("Training seeds must be non-negative")

        if len(set(values)) != len(values):
            raise ZombieModelError("Training seeds must be distinct")


@dataclass(frozen=True, slots=True)
class TrainingDefinition:
    """Synthetic training/validation/benchmark contract."""

    synthetic_training_cities: int
    synthetic_validation_cities: int
    synthetic_benchmark_cities: int
    showcase_cities_excluded_from_training: bool
    seeds: TrainingSeeds
    classical_ml_model_family: str
    deep_learning_model_family: str

    def __post_init__(self) -> None:
        counts = (
            self.synthetic_training_cities,
            self.synthetic_validation_cities,
            self.synthetic_benchmark_cities,
        )

        if any(count <= 0 for count in counts):
            raise ZombieModelError("Synthetic dataset counts must be positive")


@dataclass(frozen=True, slots=True)
class WinnerRule:
    """Deterministic winner-selection rule."""

    metric_order: tuple[str, ...]
    final_deterministic_tiebreak: tuple[MethodId, ...]
    numeric_tolerance: float | None = None

    def __post_init__(self) -> None:
        if not self.metric_order:
            raise ZombieModelError("Winner metric order cannot be empty")

        if set(self.final_deterministic_tiebreak) != set(MethodId):
            raise ZombieModelError(
                "Winner tie-break must contain all headline methods exactly once"
            )

        if self.numeric_tolerance is not None and (
            not isfinite(self.numeric_tolerance) or self.numeric_tolerance < 0.0
        ):
            raise ZombieModelError("Winner numeric tolerance must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class EvaluationDefinition:
    """Route-evaluation and winner-selection contract."""

    reported_route_metrics: tuple[str, ...]
    per_city_winner: WinnerRule
    overall_winner: WinnerRule

    def __post_init__(self) -> None:
        if not self.reported_route_metrics:
            raise ZombieModelError("Route metric list cannot be empty")

        if len(set(self.reported_route_metrics)) != len(self.reported_route_metrics):
            raise ZombieModelError("Route metrics must be unique")


@dataclass(frozen=True, slots=True)
class EncoderDefinition:
    """Production FFmpeg encoder contract."""

    codec: str
    pixel_format: str
    crf: int
    preset: str
    tune: str
    faststart: bool

    def __post_init__(self) -> None:
        if self.crf < 0:
            raise ZombieModelError("Encoder CRF must be non-negative")


@dataclass(frozen=True, slots=True)
class TypographyDefinition:
    """Minimum viewer-facing typography sizes."""

    main_heading: float
    major_title: float
    primary_metric: float
    secondary_metric: float
    technical_footer: float

    def __post_init__(self) -> None:
        values = (
            self.main_heading,
            self.major_title,
            self.primary_metric,
            self.secondary_metric,
            self.technical_footer,
        )

        if any((not isfinite(value) or value <= 0.0) for value in values):
            raise ZombieModelError("Minimum font sizes must be positive and finite")


@dataclass(frozen=True, slots=True)
class VisualQualityDefinition:
    """Automated visual-quality contract."""

    enforce_region_bounds: bool
    allow_text_clipping: bool
    allow_unintended_text_overlap: bool
    auto_fit_typography: bool
    minimum_font_sizes_pt: TypographyDefinition
    minimum_route_stroke_px: int
    minimum_frontier_stroke_px: int

    def __post_init__(self) -> None:
        if self.minimum_route_stroke_px <= 0:
            raise ZombieModelError("Route stroke must be positive")

        if self.minimum_frontier_stroke_px <= 0:
            raise ZombieModelError("Frontier stroke must be positive")


@dataclass(frozen=True, slots=True)
class OverviewGridDefinition:
    """Opening 3 x 3 comparison-grid geometry."""

    rows: int
    columns: int
    cell_width: int
    cell_height: int
    row_order: tuple[CityId, ...]
    column_order: tuple[MethodId, ...]


@dataclass(frozen=True, slots=True)
class OverviewSceneDefinition:
    """Opening video-scene contract."""

    start_second: float
    duration_seconds: float
    frame_count: int
    heading: PixelRegion
    content: PixelRegion
    grid: OverviewGridDefinition


@dataclass(frozen=True, slots=True)
class MethodLayerDefinition:
    """One full-width city-method layer."""

    x: int
    y: int
    width: int
    height: int

    @property
    def region(self) -> PixelRegion:
        return PixelRegion(
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
        )


@dataclass(frozen=True, slots=True)
class LayerInternalGeometry:
    """Map/metric-rail partition within a city-method layer."""

    map_width: int
    metric_width: int
    height: int

    def __post_init__(self) -> None:
        if self.map_width <= 0 or self.metric_width <= 0 or self.height <= 0:
            raise ZombieModelError("Layer internal geometry must be positive")


@dataclass(frozen=True, slots=True)
class CitySceneDefinition:
    """One 15-second city-comparison scene."""

    scene_id: CityId
    start_second: float
    duration_seconds: float
    frame_count: int
    city: CityId
    heading: PixelRegion
    dijkstra_layer: MethodLayerDefinition
    ml_layer: MethodLayerDefinition
    dl_layer: MethodLayerDefinition
    layer_internal_geometry: LayerInternalGeometry
    result: PixelRegion


@dataclass(frozen=True, slots=True)
class SummarySceneDefinition:
    """Final ten-second comparison scene."""

    start_second: float
    duration_seconds: float
    frame_count: int
    heading: PixelRegion
    comparison: PixelRegion
    takeaway: PixelRegion


@dataclass(frozen=True, slots=True)
class VideoDefinition:
    """Complete deterministic production-video contract."""

    width_px: int
    height_px: int
    aspect_ratio: str
    frame_rate: int
    duration_seconds: float
    frame_count: int
    dpi: int
    encoder: EncoderDefinition
    visual_quality: VisualQualityDefinition
    overview: OverviewSceneDefinition
    new_york: CitySceneDefinition
    chicago: CitySceneDefinition
    phoenix: CitySceneDefinition
    summary: SummarySceneDefinition
    scene_order: tuple[str, ...]
    technical_footer: str

    def __post_init__(self) -> None:
        if self.width_px <= 0 or self.height_px <= 0:
            raise ZombieModelError("Video dimensions must be positive")

        if self.frame_rate <= 0:
            raise ZombieModelError("Video frame rate must be positive")

        if self.duration_seconds <= 0.0:
            raise ZombieModelError("Video duration must be positive")

        if self.frame_count <= 0:
            raise ZombieModelError("Video frame count must be positive")

        expected_frames = int(self.duration_seconds * self.frame_rate)

        if self.frame_count != expected_frames:
            raise ZombieModelError("Video frame_count does not match duration x frame_rate")

        if self.dpi <= 0:
            raise ZombieModelError("Video DPI must be positive")


@dataclass(frozen=True, slots=True)
class DataOutputPaths:
    cities: Path
    training_dataset: Path
    predicted_risk_maps: Path
    routes: Path
    evaluation_summary: Path


@dataclass(frozen=True, slots=True)
class ModelOutputPaths:
    ml: Path
    dl: Path


@dataclass(frozen=True, slots=True)
class OutputDefinition:
    """Canonical runtime-artifact paths."""

    root: Path
    data: DataOutputPaths
    models: ModelOutputPaths
    previews_directory: Path
    thumbnail: Path
    final_video: Path
    final_manifest: Path


@dataclass(frozen=True, slots=True)
class AcceptanceDefinition:
    """Step-1 release invariants propagated into typed configuration."""

    require_three_showcase_cities: bool
    require_three_headline_methods: bool
    require_distinct_city_profiles: bool
    require_hidden_true_risk: bool
    require_same_planner_cost_formula: bool
    require_showcase_exclusion_from_training: bool
    require_all_routes_valid: bool
    require_oracle_regret: bool
    require_computed_winner: bool
    prohibit_hardcoded_winner: bool
    require_exact_1080_square_video: bool
    require_exact_1800_frames: bool
    require_exact_60_seconds: bool
    require_30_fps: bool
    require_h264: bool
    require_yuv420p: bool
    require_visual_geometry_validation: bool
    require_text_overlap_validation: bool
    require_generated_outputs_untracked: bool


@dataclass(frozen=True, slots=True)
class GridCell:
    """Future city-generator output for one typed grid cell."""

    position: GridPosition
    terrain: TerrainType
    observed_risk: float
    true_risk: float

    def __post_init__(self) -> None:
        for name, value in (
            (
                "observed_risk",
                self.observed_risk,
            ),
            (
                "true_risk",
                self.true_risk,
            ),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ZombieModelError(f"{name} must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class RouteMetrics:
    """Typed route-evaluation result."""

    distance: float
    travel_time: float
    true_cumulative_risk: float
    maximum_local_true_risk: float
    high_risk_cells_crossed: int
    oracle_risk_regret: float

    def __post_init__(self) -> None:
        if any(
            (not isfinite(value) or value < 0.0)
            for value in (
                self.distance,
                self.travel_time,
                self.true_cumulative_risk,
                self.maximum_local_true_risk,
                self.oracle_risk_regret,
            )
        ):
            raise ZombieModelError("Route metrics must be finite and non-negative")

        if self.high_risk_cells_crossed < 0:
            raise ZombieModelError("High-risk cell count must be non-negative")


@dataclass(frozen=True, slots=True)
class RouteResult:
    """Future solver output independent of implementation algorithm."""

    city_id: CityId
    method_id: MethodId
    start: GridPosition
    destination: GridPosition
    path: tuple[GridPosition, ...]
    route_valid: bool
    metrics: RouteMetrics

    def __post_init__(self) -> None:
        if not self.path:
            raise ZombieModelError("Route path cannot be empty")

        if self.path[0] != self.start:
            raise ZombieModelError("Route path must start at start")

        if self.path[-1] != self.destination:
            raise ZombieModelError("Route path must end at destination")


@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    """Human-facing project identity."""

    project_id: str
    name: str
    authoritative: bool
    viewer_question: str
    headline: str
    supporting_message: str


@dataclass(frozen=True, slots=True)
class ExperimentDefinition:
    """Scientific experiment core."""

    city_representation: str
    geographic_replica: bool
    deterministic: bool
    grid: GridDefinition
    risk: RiskDefinition
    planner_cost: PlannerCostDefinition
    terrain: tuple[TerrainDefinition, ...]

    def terrain_definition(
        self,
        terrain_type: TerrainType,
    ) -> TerrainDefinition:
        for item in self.terrain:
            if item.terrain_type is terrain_type:
                return item

        raise ZombieModelError(f"Missing terrain definition: {terrain_type}")


@dataclass(frozen=True, slots=True)
class ZombieProjectConfig:
    """Complete typed Project 2 configuration."""

    project: ProjectMetadata
    experiment: ExperimentDefinition
    cities: tuple[CityDefinition, ...]
    methods: tuple[PlannerDefinition, ...]
    oracle: OracleDefinition
    training: TrainingDefinition
    evaluation: EvaluationDefinition
    video: VideoDefinition
    outputs: OutputDefinition
    acceptance: AcceptanceDefinition

    def __post_init__(self) -> None:
        if len(self.cities) != 3:
            raise ZombieConfigError("Exactly three showcase cities are required")

        if {city.city_id for city in self.cities} != set(CityId):
            raise ZombieConfigError("Showcase cities must be Phoenix, New York, and Chicago")

        if len({city.seed for city in self.cities}) != 3:
            raise ZombieConfigError("Showcase city seeds must be distinct")

        if len(self.methods) != 3:
            raise ZombieConfigError("Exactly three headline methods are required")

        if {method.method_id for method in self.methods} != set(MethodId):
            raise ZombieConfigError("Headline methods must be Dijkstra, ML, and DL")

        if any(method.sees_true_hidden_risk for method in self.methods):
            raise ZombieConfigError("Headline methods cannot see true hidden risk")

        for city in self.cities:
            if not self.experiment.grid.contains(city.start):
                raise ZombieConfigError(f"{city.city_id} start lies outside the grid")

            if not self.experiment.grid.contains(city.destination):
                raise ZombieConfigError(f"{city.city_id} destination lies outside the grid")

        self._validate_scientific_contract()
        self._validate_video_contract()
        self._validate_output_contract()

    def _validate_scientific_contract(self) -> None:
        if self.experiment.risk.true_risk_visible_to_headline_methods:
            raise ZombieConfigError("True hidden risk cannot be visible to headline methods")

        if not (self.experiment.planner_cost.same_formula_for_all_headline_methods):
            raise ZombieConfigError("Headline methods must share one planner-cost formula")

        if self.oracle.headline_contestant:
            raise ZombieConfigError("Oracle cannot be a headline contestant")

        if self.oracle.risk_estimator is not RiskEstimator.TRUE_HIDDEN_RISK:
            raise ZombieConfigError("Oracle must use true hidden risk")

        if not (self.training.showcase_cities_excluded_from_training):
            raise ZombieConfigError("Showcase cities must remain excluded from training")

        if not self.acceptance.require_computed_winner:
            raise ZombieConfigError("Winner must be computed")

        if not self.acceptance.prohibit_hardcoded_winner:
            raise ZombieConfigError("Hard-coded winner must remain prohibited")

    def _validate_video_contract(self) -> None:
        if (
            self.video.width_px,
            self.video.height_px,
            self.video.frame_rate,
            self.video.duration_seconds,
            self.video.frame_count,
        ) != (
            1080,
            1080,
            30,
            60.0,
            1800,
        ):
            raise ZombieConfigError(
                "Canonical video must be 1080x1080, 30 fps, 60 sec, 1800 frames"
            )

        scenes = (
            self.video.overview,
            self.video.new_york,
            self.video.chicago,
            self.video.phoenix,
            self.video.summary,
        )

        if sum(scene.frame_count for scene in scenes) != self.video.frame_count:
            raise ZombieConfigError("Scene frame counts must total video frame count")

        if sum(scene.duration_seconds for scene in scenes) != self.video.duration_seconds:
            raise ZombieConfigError("Scene durations must total video duration")

        overview = self.video.overview

        if (overview.heading.height + overview.content.height) != self.video.height_px:
            raise ZombieConfigError("Overview regions must fill the canvas height")

        if (overview.grid.columns * overview.grid.cell_width) != self.video.width_px:
            raise ZombieConfigError("Overview grid must fill canvas width")

        if (overview.grid.rows * overview.grid.cell_height) != overview.content.height:
            raise ZombieConfigError("Overview grid must fill overview content height")

        for scene in (
            self.video.new_york,
            self.video.chicago,
            self.video.phoenix,
        ):
            if (
                scene.heading.height
                + scene.dijkstra_layer.height
                + scene.ml_layer.height
                + scene.dl_layer.height
                + scene.result.height
            ) != self.video.height_px:
                raise ZombieConfigError(f"{scene.city} scene must fill canvas height")

            if (
                scene.layer_internal_geometry.map_width + scene.layer_internal_geometry.metric_width
            ) != self.video.width_px:
                raise ZombieConfigError(f"{scene.city} layer must fill canvas width")

        if (
            self.video.summary.heading.height
            + self.video.summary.comparison.height
            + self.video.summary.takeaway.height
        ) != self.video.height_px:
            raise ZombieConfigError("Summary regions must fill canvas height")

    def _validate_output_contract(self) -> None:
        root = self.outputs.root

        if root != Path("outputs/p04_zombie_escape"):
            raise ZombieConfigError("Project 2 output root must be outputs/p04_zombie_escape")

        all_paths = (
            self.outputs.data.cities,
            self.outputs.data.training_dataset,
            self.outputs.data.predicted_risk_maps,
            self.outputs.data.routes,
            self.outputs.data.evaluation_summary,
            self.outputs.models.ml,
            self.outputs.models.dl,
            self.outputs.previews_directory,
            self.outputs.thumbnail,
            self.outputs.final_video,
            self.outputs.final_manifest,
        )

        for output_path in all_paths:
            try:
                output_path.relative_to(root)
            except ValueError as exc:
                raise ZombieConfigError(
                    f"Output path escapes Project 2 root: {output_path}"
                ) from exc

    def city(
        self,
        city_id: CityId | str,
    ) -> CityDefinition:
        requested = CityId(city_id)

        for city in self.cities:
            if city.city_id is requested:
                return city

        raise ZombieConfigError(f"Unknown city: {city_id}")

    def method(
        self,
        method_id: MethodId | str,
    ) -> PlannerDefinition:
        requested = MethodId(method_id)

        for method in self.methods:
            if method.method_id is requested:
                return method

        raise ZombieConfigError(f"Unknown method: {method_id}")

    @classmethod
    def from_mapping(
        cls,
        raw: Mapping[str, Any],
    ) -> Self:
        """Construct the complete typed contract from parsed YAML."""
        parser = _ConfigParser(raw)

        return cls(
            project=parser.project(),
            experiment=parser.experiment(),
            cities=parser.cities(),
            methods=parser.methods(),
            oracle=parser.oracle(),
            training=parser.training(),
            evaluation=parser.evaluation(),
            video=parser.video(),
            outputs=parser.outputs(),
            acceptance=parser.acceptance(),
        )


class _ConfigParser:
    """Small strict parser for the frozen Step-1 YAML schema."""

    def __init__(
        self,
        raw: Mapping[str, Any],
    ) -> None:
        self._raw = raw

    def project(self) -> ProjectMetadata:
        item = _mapping(
            self._raw.get("project"),
            "project",
        )

        return ProjectMetadata(
            project_id=_string(
                item.get("id"),
                "project.id",
            ),
            name=_string(
                item.get("name"),
                "project.name",
            ),
            authoritative=_boolean(
                item.get("authoritative"),
                "project.authoritative",
            ),
            viewer_question=_string(
                item.get("viewer_question"),
                "project.viewer_question",
            ),
            headline=_string(
                item.get("headline"),
                "project.headline",
            ),
            supporting_message=_string(
                item.get("supporting_message"),
                "project.supporting_message",
            ),
        )

    def experiment(self) -> ExperimentDefinition:
        item = _mapping(
            self._raw.get("experiment"),
            "experiment",
        )

        grid_raw = _mapping(
            item.get("grid"),
            "experiment.grid",
        )

        risk_raw = _mapping(
            item.get("risk"),
            "experiment.risk",
        )

        planner_raw = _mapping(
            item.get("planner_cost"),
            "experiment.planner_cost",
        )

        terrain_raw = _mapping(
            item.get("terrain"),
            "experiment.terrain",
        )

        terrain: list[TerrainDefinition] = []

        for terrain_type in TerrainType:
            definition = _mapping(
                terrain_raw.get(terrain_type.value),
                (f"experiment.terrain.{terrain_type.value}"),
            )

            terrain.append(
                TerrainDefinition(
                    terrain_type=terrain_type,
                    traversable=_boolean(
                        definition.get("traversable"),
                        (f"experiment.terrain.{terrain_type.value}.traversable"),
                    ),
                    speed_multiplier=_number(
                        definition.get("speed_multiplier"),
                        (f"experiment.terrain.{terrain_type.value}.speed_multiplier"),
                    ),
                )
            )

        return ExperimentDefinition(
            city_representation=_string(
                item.get("city_representation"),
                "experiment.city_representation",
            ),
            geographic_replica=_boolean(
                item.get("geographic_replica"),
                "experiment.geographic_replica",
            ),
            deterministic=_boolean(
                item.get("deterministic"),
                "experiment.deterministic",
            ),
            grid=GridDefinition(
                rows=_integer(
                    grid_raw.get("rows"),
                    "experiment.grid.rows",
                ),
                columns=_integer(
                    grid_raw.get("columns"),
                    "experiment.grid.columns",
                ),
                movement=_enum(
                    MovementRule,
                    grid_raw.get("movement"),
                    "experiment.grid.movement",
                ),
                allow_diagonal=_boolean(
                    grid_raw.get("allow_diagonal"),
                    "experiment.grid.allow_diagonal",
                ),
                step_distance=_number(
                    grid_raw.get("step_distance"),
                    "experiment.grid.step_distance",
                ),
            ),
            risk=RiskDefinition(
                minimum=_number(
                    risk_raw.get("minimum"),
                    "experiment.risk.minimum",
                ),
                maximum=_number(
                    risk_raw.get("maximum"),
                    "experiment.risk.maximum",
                ),
                high_risk_threshold=_number(
                    risk_raw.get("high_risk_threshold"),
                    "experiment.risk.high_risk_threshold",
                ),
                planner_risk_weight=_number(
                    risk_raw.get("planner_risk_weight"),
                    "experiment.risk.planner_risk_weight",
                ),
                true_risk_visible_to_headline_methods=_boolean(
                    risk_raw.get("true_risk_visible_to_headline_methods"),
                    ("experiment.risk.true_risk_visible_to_headline_methods"),
                ),
            ),
            planner_cost=PlannerCostDefinition(
                formula=_string(
                    planner_raw.get("formula"),
                    "experiment.planner_cost.formula",
                ),
                same_formula_for_all_headline_methods=_boolean(
                    planner_raw.get("same_formula_for_all_headline_methods"),
                    ("experiment.planner_cost.same_formula_for_all_headline_methods"),
                ),
            ),
            terrain=tuple(terrain),
        )

    def cities(self) -> tuple[CityDefinition, ...]:
        raw = _mapping(
            self._raw.get("cities"),
            "cities",
        )

        result: list[CityDefinition] = []

        for city_id in CityId:
            item = _mapping(
                raw.get(city_id.value),
                f"cities.{city_id.value}",
            )

            profile = _mapping(
                item.get("profile"),
                f"cities.{city_id.value}.profile",
            )

            result.append(
                CityDefinition(
                    city_id=city_id,
                    display_name=_string(
                        item.get("display_name"),
                        f"cities.{city_id.value}.display_name",
                    ),
                    inspiration_only=_boolean(
                        item.get("inspiration_only"),
                        f"cities.{city_id.value}.inspiration_only",
                    ),
                    seed=_integer(
                        item.get("seed"),
                        f"cities.{city_id.value}.seed",
                    ),
                    start=_position(
                        item.get("start"),
                        f"cities.{city_id.value}.start",
                    ),
                    destination=_position(
                        item.get("destination"),
                        f"cities.{city_id.value}.destination",
                    ),
                    profile=CityProfile(
                        block_density=_string(
                            profile.get("block_density"),
                            f"cities.{city_id.value}.profile.block_density",
                        ),
                        intersection_density=_string(
                            profile.get("intersection_density"),
                            (f"cities.{city_id.value}.profile.intersection_density"),
                        ),
                        arterial_width=_string(
                            profile.get("arterial_width"),
                            f"cities.{city_id.value}.profile.arterial_width",
                        ),
                        choke_point_density=_string(
                            profile.get("choke_point_density"),
                            (f"cities.{city_id.value}.profile.choke_point_density"),
                        ),
                        hidden_risk_structure=_string(
                            profile.get("hidden_risk_structure"),
                            (f"cities.{city_id.value}.profile.hidden_risk_structure"),
                        ),
                        synthetic_barrier=_string(
                            profile.get("synthetic_barrier"),
                            (f"cities.{city_id.value}.profile.synthetic_barrier"),
                        ),
                    ),
                )
            )

        return tuple(result)

    def methods(self) -> tuple[PlannerDefinition, ...]:
        raw = _mapping(
            self._raw.get("methods"),
            "methods",
        )

        result: list[PlannerDefinition] = []

        for method_id in MethodId:
            item = _mapping(
                raw.get(method_id.value),
                f"methods.{method_id.value}",
            )

            result.append(
                PlannerDefinition(
                    method_id=method_id,
                    display_name=_string(
                        item.get("display_name"),
                        f"methods.{method_id.value}.display_name",
                    ),
                    category=_enum(
                        MethodCategory,
                        item.get("category"),
                        f"methods.{method_id.value}.category",
                    ),
                    risk_estimator=_enum(
                        RiskEstimator,
                        item.get("risk_estimator"),
                        f"methods.{method_id.value}.risk_estimator",
                    ),
                    route_planner=_enum(
                        RoutePlanner,
                        item.get("route_planner"),
                        f"methods.{method_id.value}.route_planner",
                    ),
                    sees_true_hidden_risk=_boolean(
                        item.get("sees_true_hidden_risk"),
                        f"methods.{method_id.value}.sees_true_hidden_risk",
                    ),
                )
            )

        return tuple(result)

    def oracle(self) -> OracleDefinition:
        item = _mapping(
            self._raw.get("oracle"),
            "oracle",
        )

        return OracleDefinition(
            enabled=_boolean(
                item.get("enabled"),
                "oracle.enabled",
            ),
            headline_contestant=_boolean(
                item.get("headline_contestant"),
                "oracle.headline_contestant",
            ),
            display_name=_string(
                item.get("display_name"),
                "oracle.display_name",
            ),
            risk_estimator=_enum(
                RiskEstimator,
                item.get("risk_estimator"),
                "oracle.risk_estimator",
            ),
            route_planner=_enum(
                RoutePlanner,
                item.get("route_planner"),
                "oracle.route_planner",
            ),
            purpose=_string(
                item.get("purpose"),
                "oracle.purpose",
            ),
        )

    def training(self) -> TrainingDefinition:
        item = _mapping(
            self._raw.get("training"),
            "training",
        )

        seeds = _mapping(
            item.get("seeds"),
            "training.seeds",
        )

        classical = _mapping(
            item.get("classical_ml"),
            "training.classical_ml",
        )

        deep = _mapping(
            item.get("deep_learning"),
            "training.deep_learning",
        )

        return TrainingDefinition(
            synthetic_training_cities=_integer(
                item.get("synthetic_training_cities"),
                "training.synthetic_training_cities",
            ),
            synthetic_validation_cities=_integer(
                item.get("synthetic_validation_cities"),
                "training.synthetic_validation_cities",
            ),
            synthetic_benchmark_cities=_integer(
                item.get("synthetic_benchmark_cities"),
                "training.synthetic_benchmark_cities",
            ),
            showcase_cities_excluded_from_training=_boolean(
                item.get("showcase_cities_excluded_from_training"),
                "training.showcase_cities_excluded_from_training",
            ),
            seeds=TrainingSeeds(
                training=_integer(
                    seeds.get("training"),
                    "training.seeds.training",
                ),
                validation=_integer(
                    seeds.get("validation"),
                    "training.seeds.validation",
                ),
                benchmark=_integer(
                    seeds.get("benchmark"),
                    "training.seeds.benchmark",
                ),
                ml_model=_integer(
                    seeds.get("ml_model"),
                    "training.seeds.ml_model",
                ),
                dl_model=_integer(
                    seeds.get("dl_model"),
                    "training.seeds.dl_model",
                ),
            ),
            classical_ml_model_family=_string(
                classical.get("model_family"),
                "training.classical_ml.model_family",
            ),
            deep_learning_model_family=_string(
                deep.get("model_family"),
                "training.deep_learning.model_family",
            ),
        )

    def evaluation(self) -> EvaluationDefinition:
        item = _mapping(
            self._raw.get("evaluation"),
            "evaluation",
        )

        per_city = _mapping(
            item.get("per_city_winner"),
            "evaluation.per_city_winner",
        )

        overall = _mapping(
            item.get("overall_winner"),
            "evaluation.overall_winner",
        )

        return EvaluationDefinition(
            reported_route_metrics=_string_tuple(
                item.get("reported_route_metrics"),
                "evaluation.reported_route_metrics",
            ),
            per_city_winner=WinnerRule(
                metric_order=_string_tuple(
                    per_city.get("lexicographic_order"),
                    "evaluation.per_city_winner.lexicographic_order",
                ),
                final_deterministic_tiebreak=_method_tuple(
                    per_city.get("final_deterministic_tiebreak"),
                    ("evaluation.per_city_winner.final_deterministic_tiebreak"),
                ),
                numeric_tolerance=_number(
                    per_city.get("numeric_tolerance"),
                    "evaluation.per_city_winner.numeric_tolerance",
                ),
            ),
            overall_winner=WinnerRule(
                metric_order=_string_tuple(
                    overall.get("order"),
                    "evaluation.overall_winner.order",
                ),
                final_deterministic_tiebreak=_method_tuple(
                    overall.get("final_deterministic_tiebreak"),
                    ("evaluation.overall_winner.final_deterministic_tiebreak"),
                ),
            ),
        )

    def video(self) -> VideoDefinition:
        item = _mapping(
            self._raw.get("video"),
            "video",
        )

        encoder_raw = _mapping(
            item.get("encoder"),
            "video.encoder",
        )

        quality_raw = _mapping(
            item.get("visual_quality"),
            "video.visual_quality",
        )

        fonts_raw = _mapping(
            quality_raw.get("minimum_font_sizes_pt"),
            "video.visual_quality.minimum_font_sizes_pt",
        )

        scenes = _mapping(
            item.get("scenes"),
            "video.scenes",
        )

        return VideoDefinition(
            width_px=_integer(
                item.get("width_px"),
                "video.width_px",
            ),
            height_px=_integer(
                item.get("height_px"),
                "video.height_px",
            ),
            aspect_ratio=_string(
                item.get("aspect_ratio"),
                "video.aspect_ratio",
            ),
            frame_rate=_integer(
                item.get("frame_rate"),
                "video.frame_rate",
            ),
            duration_seconds=_number(
                item.get("duration_seconds"),
                "video.duration_seconds",
            ),
            frame_count=_integer(
                item.get("frame_count"),
                "video.frame_count",
            ),
            dpi=_integer(
                item.get("dpi"),
                "video.dpi",
            ),
            encoder=EncoderDefinition(
                codec=_string(
                    encoder_raw.get("codec"),
                    "video.encoder.codec",
                ),
                pixel_format=_string(
                    encoder_raw.get("pixel_format"),
                    "video.encoder.pixel_format",
                ),
                crf=_integer(
                    encoder_raw.get("crf"),
                    "video.encoder.crf",
                ),
                preset=_string(
                    encoder_raw.get("preset"),
                    "video.encoder.preset",
                ),
                tune=_string(
                    encoder_raw.get("tune"),
                    "video.encoder.tune",
                ),
                faststart=_boolean(
                    encoder_raw.get("faststart"),
                    "video.encoder.faststart",
                ),
            ),
            visual_quality=VisualQualityDefinition(
                enforce_region_bounds=_boolean(
                    quality_raw.get("enforce_region_bounds"),
                    "video.visual_quality.enforce_region_bounds",
                ),
                allow_text_clipping=_boolean(
                    quality_raw.get("allow_text_clipping"),
                    "video.visual_quality.allow_text_clipping",
                ),
                allow_unintended_text_overlap=_boolean(
                    quality_raw.get("allow_unintended_text_overlap"),
                    ("video.visual_quality.allow_unintended_text_overlap"),
                ),
                auto_fit_typography=_boolean(
                    quality_raw.get("auto_fit_typography"),
                    "video.visual_quality.auto_fit_typography",
                ),
                minimum_font_sizes_pt=TypographyDefinition(
                    main_heading=_number(
                        fonts_raw.get("main_heading"),
                        ("video.visual_quality.minimum_font_sizes_pt.main_heading"),
                    ),
                    major_title=_number(
                        fonts_raw.get("major_title"),
                        ("video.visual_quality.minimum_font_sizes_pt.major_title"),
                    ),
                    primary_metric=_number(
                        fonts_raw.get("primary_metric"),
                        ("video.visual_quality.minimum_font_sizes_pt.primary_metric"),
                    ),
                    secondary_metric=_number(
                        fonts_raw.get("secondary_metric"),
                        ("video.visual_quality.minimum_font_sizes_pt.secondary_metric"),
                    ),
                    technical_footer=_number(
                        fonts_raw.get("technical_footer"),
                        ("video.visual_quality.minimum_font_sizes_pt.technical_footer"),
                    ),
                ),
                minimum_route_stroke_px=_integer(
                    quality_raw.get("minimum_route_stroke_px"),
                    "video.visual_quality.minimum_route_stroke_px",
                ),
                minimum_frontier_stroke_px=_integer(
                    quality_raw.get("minimum_frontier_stroke_px"),
                    "video.visual_quality.minimum_frontier_stroke_px",
                ),
            ),
            overview=_overview_scene(scenes.get("overview")),
            new_york=_city_scene(
                CityId.NEW_YORK,
                scenes.get("new_york"),
            ),
            chicago=_city_scene(
                CityId.CHICAGO,
                scenes.get("chicago"),
            ),
            phoenix=_city_scene(
                CityId.PHOENIX,
                scenes.get("phoenix"),
            ),
            summary=_summary_scene(scenes.get("summary")),
            scene_order=_string_tuple(
                item.get("scene_order"),
                "video.scene_order",
            ),
            technical_footer=_string(
                item.get("technical_footer"),
                "video.technical_footer",
            ),
        )

    def outputs(self) -> OutputDefinition:
        item = _mapping(
            self._raw.get("outputs"),
            "outputs",
        )

        data = _mapping(
            item.get("data"),
            "outputs.data",
        )

        models = _mapping(
            item.get("models"),
            "outputs.models",
        )

        previews = _mapping(
            item.get("previews"),
            "outputs.previews",
        )

        images = _mapping(
            item.get("images"),
            "outputs.images",
        )

        video = _mapping(
            item.get("video"),
            "outputs.video",
        )

        manifests = _mapping(
            item.get("manifests"),
            "outputs.manifests",
        )

        return OutputDefinition(
            root=Path(
                _string(
                    item.get("root"),
                    "outputs.root",
                )
            ),
            data=DataOutputPaths(
                cities=Path(
                    _string(
                        data.get("cities"),
                        "outputs.data.cities",
                    )
                ),
                training_dataset=Path(
                    _string(
                        data.get("training_dataset"),
                        "outputs.data.training_dataset",
                    )
                ),
                predicted_risk_maps=Path(
                    _string(
                        data.get("predicted_risk_maps"),
                        "outputs.data.predicted_risk_maps",
                    )
                ),
                routes=Path(
                    _string(
                        data.get("routes"),
                        "outputs.data.routes",
                    )
                ),
                evaluation_summary=Path(
                    _string(
                        data.get("evaluation_summary"),
                        "outputs.data.evaluation_summary",
                    )
                ),
            ),
            models=ModelOutputPaths(
                ml=Path(
                    _string(
                        models.get("ml"),
                        "outputs.models.ml",
                    )
                ),
                dl=Path(
                    _string(
                        models.get("dl"),
                        "outputs.models.dl",
                    )
                ),
            ),
            previews_directory=Path(
                _string(
                    previews.get("directory"),
                    "outputs.previews.directory",
                )
            ),
            thumbnail=Path(
                _string(
                    images.get("thumbnail"),
                    "outputs.images.thumbnail",
                )
            ),
            final_video=Path(
                _string(
                    video.get("final"),
                    "outputs.video.final",
                )
            ),
            final_manifest=Path(
                _string(
                    manifests.get("final"),
                    "outputs.manifests.final",
                )
            ),
        )

    def acceptance(self) -> AcceptanceDefinition:
        item = _mapping(
            self._raw.get("acceptance"),
            "acceptance",
        )

        names = (
            "require_three_showcase_cities",
            "require_three_headline_methods",
            "require_distinct_city_profiles",
            "require_hidden_true_risk",
            "require_same_planner_cost_formula",
            "require_showcase_exclusion_from_training",
            "require_all_routes_valid",
            "require_oracle_regret",
            "require_computed_winner",
            "prohibit_hardcoded_winner",
            "require_exact_1080_square_video",
            "require_exact_1800_frames",
            "require_exact_60_seconds",
            "require_30_fps",
            "require_h264",
            "require_yuv420p",
            "require_visual_geometry_validation",
            "require_text_overlap_validation",
            "require_generated_outputs_untracked",
        )

        values = {
            name: _boolean(
                item.get(name),
                f"acceptance.{name}",
            )
            for name in names
        }

        return AcceptanceDefinition(**values)


def _mapping(
    value: object,
    location: str,
) -> Mapping[str, Any]:
    if not isinstance(
        value,
        Mapping,
    ):
        raise ZombieConfigError(f"{location} must be a mapping")

    result: dict[
        str,
        Any,
    ] = {}

    for key, item in value.items():
        if not isinstance(
            key,
            str,
        ):
            raise ZombieConfigError(f"{location} keys must be strings")

        result[key] = item

    return result


def _string(
    value: object,
    location: str,
) -> str:
    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise ZombieConfigError(f"{location} must be a non-empty string")

    return value


def _boolean(
    value: object,
    location: str,
) -> bool:
    if not isinstance(
        value,
        bool,
    ):
        raise ZombieConfigError(f"{location} must be a boolean")

    return value


def _integer(
    value: object,
    location: str,
) -> int:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        int,
    ):
        raise ZombieConfigError(f"{location} must be an integer")

    return value


def _number(
    value: object,
    location: str,
) -> float:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        raise ZombieConfigError(f"{location} must be numeric")

    result = float(value)

    if not isfinite(result):
        raise ZombieConfigError(f"{location} must be finite")

    return result


def _enum[EnumT: StrEnum](
    enum_type: type[EnumT],
    value: object,
    location: str,
) -> EnumT:
    raw = _string(
        value,
        location,
    )

    try:
        return enum_type(raw)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_type)

        raise ZombieConfigError(f"{location} must be one of: {allowed}") from exc


def _sequence(
    value: object,
    location: str,
) -> Sequence[object]:
    if isinstance(
        value,
        (
            str,
            bytes,
        ),
    ) or not isinstance(
        value,
        Sequence,
    ):
        raise ZombieConfigError(f"{location} must be a sequence")

    return value


def _string_tuple(
    value: object,
    location: str,
) -> tuple[str, ...]:
    items = _sequence(
        value,
        location,
    )

    return tuple(
        _string(
            item,
            f"{location}[{index}]",
        )
        for index, item in enumerate(items)
    )


def _method_tuple(
    value: object,
    location: str,
) -> tuple[MethodId, ...]:
    items = _sequence(
        value,
        location,
    )

    return tuple(
        _enum(
            MethodId,
            item,
            f"{location}[{index}]",
        )
        for index, item in enumerate(items)
    )


def _position(
    value: object,
    location: str,
) -> GridPosition:
    item = _mapping(
        value,
        location,
    )

    return GridPosition(
        row=_integer(
            item.get("row"),
            f"{location}.row",
        ),
        column=_integer(
            item.get("column"),
            f"{location}.column",
        ),
    )


def _region(
    value: object,
    location: str,
) -> PixelRegion:
    item = _mapping(
        value,
        location,
    )

    return PixelRegion(
        x=_integer(
            item.get("x"),
            f"{location}.x",
        ),
        y=_integer(
            item.get("y"),
            f"{location}.y",
        ),
        width=_integer(
            item.get("width"),
            f"{location}.width",
        ),
        height=_integer(
            item.get("height"),
            f"{location}.height",
        ),
    )


def _overview_scene(
    value: object,
) -> OverviewSceneDefinition:
    item = _mapping(
        value,
        "video.scenes.overview",
    )

    grid_raw = _mapping(
        item.get("grid"),
        "video.scenes.overview.grid",
    )

    row_order = tuple(
        _enum(
            CityId,
            entry,
            (f"video.scenes.overview.grid.row_order[{index}]"),
        )
        for index, entry in enumerate(
            _sequence(
                grid_raw.get("row_order"),
                "video.scenes.overview.grid.row_order",
            )
        )
    )

    column_order = _method_tuple(
        grid_raw.get("column_order"),
        "video.scenes.overview.grid.column_order",
    )

    return OverviewSceneDefinition(
        start_second=_number(
            item.get("start_second"),
            "video.scenes.overview.start_second",
        ),
        duration_seconds=_number(
            item.get("duration_seconds"),
            "video.scenes.overview.duration_seconds",
        ),
        frame_count=_integer(
            item.get("frame_count"),
            "video.scenes.overview.frame_count",
        ),
        heading=_region(
            item.get("heading"),
            "video.scenes.overview.heading",
        ),
        content=_region(
            item.get("content"),
            "video.scenes.overview.content",
        ),
        grid=OverviewGridDefinition(
            rows=_integer(
                grid_raw.get("rows"),
                "video.scenes.overview.grid.rows",
            ),
            columns=_integer(
                grid_raw.get("columns"),
                "video.scenes.overview.grid.columns",
            ),
            cell_width=_integer(
                grid_raw.get("cell_width"),
                "video.scenes.overview.grid.cell_width",
            ),
            cell_height=_integer(
                grid_raw.get("cell_height"),
                "video.scenes.overview.grid.cell_height",
            ),
            row_order=row_order,
            column_order=column_order,
        ),
    )


def _city_scene(
    scene_id: CityId,
    value: object,
) -> CitySceneDefinition:
    location = f"video.scenes.{scene_id.value}"

    item = _mapping(
        value,
        location,
    )

    layers = _mapping(
        item.get("layers"),
        f"{location}.layers",
    )

    internal = _mapping(
        item.get("layer_internal_geometry"),
        f"{location}.layer_internal_geometry",
    )

    return CitySceneDefinition(
        scene_id=scene_id,
        start_second=_number(
            item.get("start_second"),
            f"{location}.start_second",
        ),
        duration_seconds=_number(
            item.get("duration_seconds"),
            f"{location}.duration_seconds",
        ),
        frame_count=_integer(
            item.get("frame_count"),
            f"{location}.frame_count",
        ),
        city=_enum(
            CityId,
            item.get("city"),
            f"{location}.city",
        ),
        heading=_region(
            item.get("heading"),
            f"{location}.heading",
        ),
        dijkstra_layer=_layer(
            layers.get("dijkstra"),
            f"{location}.layers.dijkstra",
        ),
        ml_layer=_layer(
            layers.get("ml"),
            f"{location}.layers.ml",
        ),
        dl_layer=_layer(
            layers.get("dl"),
            f"{location}.layers.dl",
        ),
        layer_internal_geometry=LayerInternalGeometry(
            map_width=_integer(
                internal.get("map_width"),
                f"{location}.layer_internal_geometry.map_width",
            ),
            metric_width=_integer(
                internal.get("metric_width"),
                f"{location}.layer_internal_geometry.metric_width",
            ),
            height=_integer(
                internal.get("height"),
                f"{location}.layer_internal_geometry.height",
            ),
        ),
        result=_region(
            item.get("result"),
            f"{location}.result",
        ),
    )


def _layer(
    value: object,
    location: str,
) -> MethodLayerDefinition:
    region = _region(
        value,
        location,
    )

    return MethodLayerDefinition(
        x=region.x,
        y=region.y,
        width=region.width,
        height=region.height,
    )


def _summary_scene(
    value: object,
) -> SummarySceneDefinition:
    location = "video.scenes.summary"

    item = _mapping(
        value,
        location,
    )

    return SummarySceneDefinition(
        start_second=_number(
            item.get("start_second"),
            f"{location}.start_second",
        ),
        duration_seconds=_number(
            item.get("duration_seconds"),
            f"{location}.duration_seconds",
        ),
        frame_count=_integer(
            item.get("frame_count"),
            f"{location}.frame_count",
        ),
        heading=_region(
            item.get("heading"),
            f"{location}.heading",
        ),
        comparison=_region(
            item.get("comparison"),
            f"{location}.comparison",
        ),
        takeaway=_region(
            item.get("takeaway"),
            f"{location}.takeaway",
        ),
    )
