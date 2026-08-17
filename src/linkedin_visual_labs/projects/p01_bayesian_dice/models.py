"""Typed domain models for Bayesian Dice Detective."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from linkedin_visual_labs.common.validation import ValidationError

FACE_COUNT = 6
PROBABILITY_SUM_TOLERANCE = 1.0e-12


class DiceModelError(ValidationError):
    """Raised when a Bayesian Dice domain model is invalid."""


class DecisionState(StrEnum):
    """Sequential Bayesian decision state."""

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
        """Return the immutable probability tuple."""
        return self.values

    def as_list(self) -> list[float]:
        """Return a JSON-compatible probability list."""
        return list(self.values)


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    """Deterministic generating scenario."""

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
    """Bayesian model-comparison configuration."""

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
    """Posterior thresholds for FAIR/UNCERTAIN/LOADED states."""

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
        """Classify one loaded-model posterior probability."""
        if not (math.isfinite(posterior_loaded) and 0.0 <= posterior_loaded <= 1.0):
            raise DiceModelError("posterior_loaded must be finite and within [0, 1]")

        if posterior_loaded <= self.fair_threshold:
            return DecisionState.FAIR

        if posterior_loaded >= self.loaded_threshold:
            return DecisionState.LOADED

        return DecisionState.UNCERTAIN


@dataclass(frozen=True, slots=True)
class CalibrationDefinition:
    """Automated repeated-simulation validation contract."""

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
    """Repository-relative canonical Project 1 output files."""

    simulation: Path
    posterior_history: Path
    validation: Path
    video: Path
    manifest: Path

    def as_mapping(self) -> Mapping[str, Path]:
        """Return output names and repository-relative paths."""
        return {
            "simulation": self.simulation,
            "posterior_history": self.posterior_history,
            "validation": self.validation,
            "video": self.video,
            "manifest": self.manifest,
        }


@dataclass(frozen=True, slots=True)
class VideoContract:
    """Initial Bayesian Dice video-output contract."""

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
    """Complete typed Project 1 configuration."""

    project_id: str
    name: str
    hook: str
    technical_description: str
    model: BayesianModelDefinition
    decision: DecisionThresholds
    roll_count: int
    scenarios: Mapping[str, ScenarioDefinition]
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
            raise DiceModelError("roll_count must be positive")

        required_scenarios = {
            "fair",
            "mildly_loaded",
            "clearly_loaded",
        }

        if set(self.scenarios) != required_scenarios:
            raise DiceModelError(
                "scenarios must contain exactly fair, mildly_loaded, and clearly_loaded"
            )

        if self.showcase_scenario not in self.scenarios:
            raise DiceModelError("showcase_scenario must reference a configured scenario")

        if self.calibration.primary_loaded_scenario not in self.scenarios:
            raise DiceModelError("primary_loaded_scenario must reference a configured scenario")

    def scenario(
        self,
        scenario_id: str,
    ) -> ScenarioDefinition:
        """Return one configured scenario by identifier."""
        try:
            return self.scenarios[scenario_id]
        except KeyError as exc:
            allowed = ", ".join(sorted(self.scenarios))
            raise DiceModelError(f"unknown scenario {scenario_id!r}; allowed: {allowed}") from exc
