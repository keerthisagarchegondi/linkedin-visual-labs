"""Typed domain models for Bayesian Dice Detective."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from linkedin_visual_labs.common.validation import ValidationError

FACE_COUNT = 6
PAIR_SUM_MINIMUM = 2
PAIR_SUM_MAXIMUM = 12
PAIR_SUM_COUNT = 11
PAIR_CASE_COUNT = 6

PROBABILITY_SUM_TOLERANCE = 1.0e-12

PAIR_CASE_IDS = (
    "UU",
    "UP",
    "UF",
    "PP",
    "PF",
    "FF",
)

DIE_TYPE_IDS = (
    "unloaded",
    "partially_loaded",
    "fully_loaded",
)


class DiceModelError(ValidationError):
    """Raised when a Bayesian Dice domain model is invalid."""


class DecisionState(StrEnum):
    """Bayesian loaded/fair decision state."""

    FAIR = "FAIR"
    UNCERTAIN = "UNCERTAIN"
    LOADED = "LOADED"


@dataclass(frozen=True, slots=True)
class ProbabilityVector:
    """Validated six-face probability vector."""

    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != FACE_COUNT:
            raise DiceModelError(f"probability vector must contain exactly {FACE_COUNT} values")

        if not all(math.isfinite(value) and value >= 0.0 for value in self.values):
            raise DiceModelError("probabilities must be finite and non-negative")

        total = math.fsum(self.values)

        if not math.isclose(
            total,
            1.0,
            rel_tol=0.0,
            abs_tol=PROBABILITY_SUM_TOLERANCE,
        ):
            raise DiceModelError(
                f"probabilities must sum to one within tolerance; found {total:.17f}"
            )

    @classmethod
    def from_sequence(
        cls,
        values: Sequence[object],
    ) -> ProbabilityVector:
        """Construct a probability vector from numeric input."""
        converted: list[float] = []

        for value in values:
            if isinstance(value, bool) or not isinstance(
                value,
                (int, float),
            ):
                raise DiceModelError("probabilities must contain only numeric values")

            converted.append(float(value))

        return cls(tuple(converted))

    def as_tuple(self) -> tuple[float, ...]:
        """Return immutable probability values."""
        return self.values

    def as_list(self) -> list[float]:
        """Return JSON-compatible probability values."""
        return list(self.values)


###############################################################################
# REVISED PAIR-OF-DICE DOMAIN MODELS
###############################################################################


@dataclass(frozen=True, slots=True)
class PairObservationDefinition:
    """Observed-data contract for pair-of-dice inference."""

    observation_type: str
    minimum: int
    maximum: int
    individual_faces_visible_to_inference: bool

    def __post_init__(self) -> None:
        if self.observation_type != "pair_sum":
            raise DiceModelError("pair observation type must equal 'pair_sum'")

        if self.minimum != PAIR_SUM_MINIMUM:
            raise DiceModelError(f"pair-sum minimum must equal {PAIR_SUM_MINIMUM}")

        if self.maximum != PAIR_SUM_MAXIMUM:
            raise DiceModelError(f"pair-sum maximum must equal {PAIR_SUM_MAXIMUM}")

        if self.individual_faces_visible_to_inference:
            raise DiceModelError("revised pair inference must observe sums only")


@dataclass(frozen=True, slots=True)
class DieTypeDefinition:
    """One canonical six-sided die type."""

    type_id: str
    short_id: str
    label: str
    probabilities: ProbabilityVector

    def __post_init__(self) -> None:
        if self.type_id not in DIE_TYPE_IDS:
            raise DiceModelError(f"unknown die type {self.type_id!r}")

        if self.short_id not in {
            "U",
            "P",
            "F",
        }:
            raise DiceModelError("die short_id must be U, P, or F")

        if not self.label.strip():
            raise DiceModelError("die label must not be empty")


@dataclass(frozen=True, slots=True)
class PairCaseDefinition:
    """One canonical unordered pair-of-dice experiment."""

    case_id: str
    label: str
    die_1_type: str
    die_2_type: str
    truth_loaded: bool
    seed: int

    def __post_init__(self) -> None:
        if self.case_id not in PAIR_CASE_IDS:
            raise DiceModelError(f"unknown pair case {self.case_id!r}")

        if not self.label.strip():
            raise DiceModelError("pair-case label must not be empty")

        if self.die_1_type not in DIE_TYPE_IDS:
            raise DiceModelError(f"unknown die_1_type {self.die_1_type!r}")

        if self.die_2_type not in DIE_TYPE_IDS:
            raise DiceModelError(f"unknown die_2_type {self.die_2_type!r}")

        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise DiceModelError("pair-case seed must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class PairModelPriorDefinition:
    """Prior probability over the six exact pair hypotheses."""

    values: Mapping[str, float]

    def __post_init__(self) -> None:
        if set(self.values) != set(PAIR_CASE_IDS):
            raise DiceModelError(
                "pair model priors must contain exactly UU, UP, UF, PP, PF, and FF"
            )

        if not all(math.isfinite(value) and 0.0 < value < 1.0 for value in self.values.values()):
            raise DiceModelError("pair model priors must be finite and strictly between 0 and 1")

        total = math.fsum(self.values.values())

        if not math.isclose(
            total,
            1.0,
            rel_tol=0.0,
            abs_tol=PROBABILITY_SUM_TOLERANCE,
        ):
            raise DiceModelError(f"pair model priors must sum to one; found {total:.17f}")

    @property
    def prior_fair_probability(self) -> float:
        """Return prior probability of the completely fair UU model."""
        return self.values["UU"]

    @property
    def prior_loaded_probability(self) -> float:
        """Return prior probability that at least one die is loaded."""
        return 1.0 - self.prior_fair_probability


@dataclass(frozen=True, slots=True)
class PairDecisionDefinition:
    """Decision and headline-result contract for pair inference."""

    fair_threshold: float
    loaded_threshold: float
    headline_roll_metric: str
    require_same_final_state_through_end: bool
    use_first_threshold_crossing_as_headline: bool

    def __post_init__(self) -> None:
        if not (math.isfinite(self.fair_threshold) and math.isfinite(self.loaded_threshold)):
            raise DiceModelError("pair decision thresholds must be finite")

        if not (0.0 <= self.fair_threshold < self.loaded_threshold <= 1.0):
            raise DiceModelError("pair decision thresholds must satisfy 0 <= fair < loaded <= 1")

        if self.headline_roll_metric != "stable_decision_roll":
            raise DiceModelError("pair headline roll metric must be stable_decision_roll")

        if not self.require_same_final_state_through_end:
            raise DiceModelError("stable decisions must remain in the final state through the end")

        if self.use_first_threshold_crossing_as_headline:
            raise DiceModelError("first threshold crossing must not be used as headline metric")

    def classify(
        self,
        posterior_loaded: float,
    ) -> DecisionState:
        """Classify one loaded posterior probability."""
        if not (math.isfinite(posterior_loaded) and 0.0 <= posterior_loaded <= 1.0):
            raise DiceModelError("posterior_loaded must remain within [0, 1]")

        if posterior_loaded <= self.fair_threshold:
            return DecisionState.FAIR

        if posterior_loaded >= self.loaded_threshold:
            return DecisionState.LOADED

        return DecisionState.UNCERTAIN


@dataclass(frozen=True, slots=True)
class PairOutputContract:
    """Repository-relative canonical pair-experiment outputs."""

    simulation: Path
    history: Path
    summary: Path
    validation: Path
    preview_directory: Path
    video: Path
    manifest: Path

    def as_mapping(self) -> Mapping[str, Path]:
        """Return pair output names and repository-relative paths."""
        return {
            "simulation": self.simulation,
            "history": self.history,
            "summary": self.summary,
            "validation": self.validation,
            "preview_directory": self.preview_directory,
            "video": self.video,
            "manifest": self.manifest,
        }


@dataclass(frozen=True, slots=True)
class PixelRegion:
    """One validated rectangular pixel region."""

    x_px: int
    y_px: int
    width_px: int
    height_px: int

    def __post_init__(self) -> None:
        if self.x_px < 0 or self.y_px < 0:
            raise DiceModelError("pixel-region coordinates must be non-negative")

        if self.width_px <= 0 or self.height_px <= 0:
            raise DiceModelError("pixel-region dimensions must be positive")

    @property
    def right_px(self) -> int:
        """Return exclusive right edge."""
        return self.x_px + self.width_px

    @property
    def bottom_px(self) -> int:
        """Return exclusive bottom edge."""
        return self.y_px + self.height_px


@dataclass(frozen=True, slots=True)
class PairPanelPlacement:
    """Grid placement for one pair-case analytical panel."""

    case_id: str
    row: int
    column: int

    def __post_init__(self) -> None:
        if self.case_id not in PAIR_CASE_IDS:
            raise DiceModelError(f"unknown panel case {self.case_id!r}")

        if self.row not in {
            0,
            1,
        }:
            raise DiceModelError("panel row must be 0 or 1")

        if self.column not in {
            0,
            1,
            2,
        }:
            raise DiceModelError("panel column must be 0, 1, or 2")


@dataclass(frozen=True, slots=True)
class PairVideoContract:
    """Square six-panel video-layout contract."""

    width_px: int
    height_px: int
    aspect_ratio: str
    frame_rate: int
    target_duration_seconds: float
    heading: PixelRegion
    heading_text: str
    middle_grid: PixelRegion
    columns: int
    rows: int
    panel_width_px: int
    panel_height_px: int
    panel_placements: tuple[
        PairPanelPlacement,
        ...,
    ]
    result_strip: PixelRegion
    result_cell_count: int
    result_cell_width_px: int
    technical_footer: str
    auto_fit_typography: bool
    enforce_region_bounds: bool
    allow_text_clipping: bool
    allow_artist_overlap: bool

    def __post_init__(self) -> None:
        if (
            self.width_px,
            self.height_px,
        ) != (
            1080,
            1080,
        ):
            raise DiceModelError("revised pair video must be exactly 1080x1080")

        if self.aspect_ratio != "1:1":
            raise DiceModelError("revised pair video aspect_ratio must be 1:1")

        if self.frame_rate <= 0:
            raise DiceModelError("video frame_rate must be positive")

        if not math.isfinite(self.target_duration_seconds) or self.target_duration_seconds <= 0.0:
            raise DiceModelError("target video duration must be finite and positive")

        if not self.heading_text.strip():
            raise DiceModelError("heading text must not be empty")

        if (
            self.heading.height_px + self.middle_grid.height_px + self.result_strip.height_px
        ) != self.height_px:
            raise DiceModelError(
                "heading, grid, and result-strip heights must fill the 1080px canvas"
            )

        if self.columns != 3 or self.rows != 2:
            raise DiceModelError("pair analytical grid must be 3 columns by 2 rows")

        if (self.panel_width_px * self.columns) != self.middle_grid.width_px:
            raise DiceModelError("panel widths must exactly fill the middle grid")

        if (self.panel_height_px * self.rows) != self.middle_grid.height_px:
            raise DiceModelError("panel heights must exactly fill the middle grid")

        if len(self.panel_placements) != PAIR_CASE_COUNT:
            raise DiceModelError("video must contain six panel placements")

        if {placement.case_id for placement in self.panel_placements} != set(PAIR_CASE_IDS):
            raise DiceModelError("video panel placements must contain all six cases")

        occupied_cells = {
            (
                placement.row,
                placement.column,
            )
            for placement in self.panel_placements
        }

        if len(occupied_cells) != PAIR_CASE_COUNT:
            raise DiceModelError("video panel placements must occupy unique grid cells")

        if self.result_cell_count != PAIR_CASE_COUNT:
            raise DiceModelError("results strip must contain six cells")

        if (self.result_cell_width_px * self.result_cell_count) != self.result_strip.width_px:
            raise DiceModelError("result cells must exactly fill the results strip")

        if not self.auto_fit_typography:
            raise DiceModelError("pair video must enable automatic typography fitting")

        if not self.enforce_region_bounds:
            raise DiceModelError("pair video must enforce artist region bounds")

        if self.allow_text_clipping:
            raise DiceModelError("pair video must not allow text clipping")

        if self.allow_artist_overlap:
            raise DiceModelError("pair video must not allow unintended artist overlap")


@dataclass(frozen=True, slots=True)
class PairExperimentDefinition:
    """Complete authoritative pair-of-dice experiment contract."""

    authoritative: bool
    viewer_question: str
    observation: PairObservationDefinition
    roll_count_per_case: int
    die_types: Mapping[
        str,
        DieTypeDefinition,
    ]
    pair_cases: Mapping[
        str,
        PairCaseDefinition,
    ]
    pair_order: tuple[str, ...]
    model_priors: PairModelPriorDefinition
    loaded_probability_definition: str
    derive_sum_pmf_by_convolution: bool
    hard_code_sum_pmf: bool
    decision: PairDecisionDefinition
    outputs: PairOutputContract
    video: PairVideoContract

    def __post_init__(self) -> None:
        if not self.authoritative:
            raise DiceModelError("pair experiment must be authoritative")

        if not self.viewer_question.strip():
            raise DiceModelError("pair viewer question must not be empty")

        if self.roll_count_per_case != 10_000:
            raise DiceModelError("canonical pair experiment must use 10,000 rolls per case")

        if set(self.die_types) != set(DIE_TYPE_IDS):
            raise DiceModelError(
                "pair experiment must contain exactly "
                "unloaded, partially_loaded, and fully_loaded die types"
            )

        if set(self.pair_cases) != set(PAIR_CASE_IDS):
            raise DiceModelError("pair experiment must contain exactly six canonical pair cases")

        if self.pair_order != PAIR_CASE_IDS:
            raise DiceModelError("pair_order must equal UU, UP, UF, PP, PF, FF")

        if len({case.seed for case in self.pair_cases.values()}) != PAIR_CASE_COUNT:
            raise DiceModelError("canonical pair-case seeds must be unique")

        normalized_pairs: set[tuple[str, str]] = set()

        for case in self.pair_cases.values():
            normalized_values = sorted(
                (
                    case.die_1_type,
                    case.die_2_type,
                )
            )

            normalized = (
                normalized_values[0],
                normalized_values[1],
            )

            if normalized in normalized_pairs:
                raise DiceModelError(f"duplicate unordered pair definition {normalized}")

            normalized_pairs.add(normalized)

        if len(normalized_pairs) != PAIR_CASE_COUNT:
            raise DiceModelError("pair experiment must contain six unique unordered pairs")

        if self.loaded_probability_definition != ("1 - posterior(M_UU)"):
            raise DiceModelError("loaded probability definition must equal '1 - posterior(M_UU)'")

        if not self.derive_sum_pmf_by_convolution:
            raise DiceModelError("pair sum PMFs must be derived by convolution")

        if self.hard_code_sum_pmf:
            raise DiceModelError("pair sum PMFs must not be hard-coded")

    @property
    def total_observation_count(self) -> int:
        """Return total canonical observed pair sums."""
        return self.roll_count_per_case * len(self.pair_cases)

    def die_type(
        self,
        type_id: str,
    ) -> DieTypeDefinition:
        """Return one configured die type."""
        try:
            return self.die_types[type_id]
        except KeyError as exc:
            allowed = ", ".join(sorted(self.die_types))

            raise DiceModelError(f"unknown die type {type_id!r}; allowed: {allowed}") from exc

    def pair_case(
        self,
        case_id: str,
    ) -> PairCaseDefinition:
        """Return one configured canonical pair case."""
        try:
            return self.pair_cases[case_id]
        except KeyError as exc:
            allowed = ", ".join(self.pair_order)

            raise DiceModelError(f"unknown pair case {case_id!r}; allowed: {allowed}") from exc


###############################################################################
# TEMPORARY LEGACY SINGLE-DIE DOMAIN MODELS
#
# These remain until Revised Steps 3-5 replace simulation/inference/metrics.
###############################################################################


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    """Legacy deterministic single-die generating scenario."""

    scenario_id: str
    label: str
    probabilities: ProbabilityVector
    seed: int

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise DiceModelError("scenario_id must not be empty")

        if not self.label.strip():
            raise DiceModelError("scenario label must not be empty")

        if isinstance(self.seed, bool) or self.seed < 0:
            raise DiceModelError("scenario seed must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class BayesianModelDefinition:
    """Legacy Bayesian single-die model configuration."""

    fair_probabilities: ProbabilityVector
    dirichlet_alpha: tuple[float, ...]
    prior_loaded_probability: float

    def __post_init__(self) -> None:
        if len(self.dirichlet_alpha) != FACE_COUNT:
            raise DiceModelError(f"Dirichlet prior must contain {FACE_COUNT} values")

        if not all(math.isfinite(value) and value > 0.0 for value in self.dirichlet_alpha):
            raise DiceModelError("Dirichlet alpha values must be finite and positive")

        if not (
            math.isfinite(self.prior_loaded_probability)
            and 0.0 < self.prior_loaded_probability < 1.0
        ):
            raise DiceModelError("prior_loaded_probability must be strictly between 0 and 1")


@dataclass(frozen=True, slots=True)
class DecisionThresholds:
    """Legacy single-die posterior decision thresholds."""

    fair_threshold: float
    loaded_threshold: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.fair_threshold) and math.isfinite(self.loaded_threshold)):
            raise DiceModelError("decision thresholds must be finite")

        if not (0.0 <= self.fair_threshold < self.loaded_threshold <= 1.0):
            raise DiceModelError("decision thresholds must satisfy 0 <= fair < loaded <= 1")

    def classify(
        self,
        posterior_loaded: float,
    ) -> DecisionState:
        """Classify one legacy loaded-model posterior."""
        if not (math.isfinite(posterior_loaded) and 0.0 <= posterior_loaded <= 1.0):
            raise DiceModelError("posterior_loaded must be finite and within [0, 1]")

        if posterior_loaded <= self.fair_threshold:
            return DecisionState.FAIR

        if posterior_loaded >= self.loaded_threshold:
            return DecisionState.LOADED

        return DecisionState.UNCERTAIN


@dataclass(frozen=True, slots=True)
class CalibrationDefinition:
    """Legacy repeated-simulation validation contract."""

    repetitions_per_scenario: int
    master_seed: int
    posterior_bucket_count: int
    prior_sensitivity: tuple[float, ...]
    primary_loaded_scenario: str

    def __post_init__(self) -> None:
        if self.repetitions_per_scenario <= 0:
            raise DiceModelError("repetitions_per_scenario must be positive")

        if self.master_seed < 0:
            raise DiceModelError("calibration master_seed must be non-negative")

        if self.posterior_bucket_count <= 0:
            raise DiceModelError("posterior_bucket_count must be positive")

        if not self.prior_sensitivity:
            raise DiceModelError("prior_sensitivity must not be empty")

        if not all(math.isfinite(value) and 0.0 < value < 1.0 for value in self.prior_sensitivity):
            raise DiceModelError("prior sensitivity values must be strictly between 0 and 1")

        if not self.primary_loaded_scenario.strip():
            raise DiceModelError("primary_loaded_scenario must not be empty")


@dataclass(frozen=True, slots=True)
class OutputContract:
    """Legacy repository-relative Project 1 output files."""

    simulation: Path
    posterior_history: Path
    validation: Path
    video: Path
    manifest: Path

    def as_mapping(self) -> Mapping[str, Path]:
        """Return legacy output paths."""
        return {
            "simulation": self.simulation,
            "posterior_history": self.posterior_history,
            "validation": self.validation,
            "video": self.video,
            "manifest": self.manifest,
        }


@dataclass(frozen=True, slots=True)
class VideoContract:
    """Legacy single-die video contract."""

    width_px: int
    height_px: int
    frame_rate: int
    target_duration_seconds: float
    opening_hook: str
    technical_footer: str

    def __post_init__(self) -> None:
        if self.width_px <= 0 or self.height_px <= 0:
            raise DiceModelError("video dimensions must be positive")

        if self.frame_rate <= 0:
            raise DiceModelError("video frame_rate must be positive")

        if not math.isfinite(self.target_duration_seconds) or self.target_duration_seconds <= 0.0:
            raise DiceModelError("target_duration_seconds must be finite and positive")

        if not self.opening_hook.strip():
            raise DiceModelError("opening_hook must not be empty")

        if not self.technical_footer.strip():
            raise DiceModelError("technical_footer must not be empty")


@dataclass(frozen=True, slots=True)
class DiceProjectConfig:
    """Complete transitional Project 1 configuration."""

    project_id: str
    name: str
    hook: str
    technical_description: str

    pair_experiment: PairExperimentDefinition

    model: BayesianModelDefinition
    decision: DecisionThresholds
    roll_count: int
    scenarios: Mapping[
        str,
        ScenarioDefinition,
    ]
    showcase_scenario: str
    calibration: CalibrationDefinition
    outputs: OutputContract
    video: VideoContract

    configuration_path: Path

    def __post_init__(self) -> None:
        if self.project_id != "p01_bayesian_dice":
            raise DiceModelError("project_id must equal 'p01_bayesian_dice'")

        if not self.name.strip():
            raise DiceModelError("project name must not be empty")

        if not self.hook.strip():
            raise DiceModelError("project hook must not be empty")

        if not self.technical_description.strip():
            raise DiceModelError("technical_description must not be empty")

        if self.roll_count <= 0:
            raise DiceModelError("legacy roll_count must be positive")

        required_scenarios = {
            "fair",
            "mildly_loaded",
            "clearly_loaded",
        }

        if set(self.scenarios) != required_scenarios:
            raise DiceModelError(
                "legacy scenarios must contain exactly fair, mildly_loaded, and clearly_loaded"
            )

        if self.showcase_scenario not in self.scenarios:
            raise DiceModelError("legacy showcase_scenario must reference a configured scenario")

        if self.calibration.primary_loaded_scenario not in self.scenarios:
            raise DiceModelError(
                "legacy primary_loaded_scenario must reference a configured scenario"
            )

    def scenario(
        self,
        scenario_id: str,
    ) -> ScenarioDefinition:
        """Return one legacy configured single-die scenario."""
        try:
            return self.scenarios[scenario_id]
        except KeyError as exc:
            allowed = ", ".join(sorted(self.scenarios))

            raise DiceModelError(f"unknown scenario {scenario_id!r}; allowed: {allowed}") from exc

    def pair_case(
        self,
        case_id: str,
    ) -> PairCaseDefinition:
        """Return one authoritative pair-case definition."""
        return self.pair_experiment.pair_case(case_id)

    def die_type(
        self,
        type_id: str,
    ) -> DieTypeDefinition:
        """Return one authoritative die-type definition."""
        return self.pair_experiment.die_type(type_id)
