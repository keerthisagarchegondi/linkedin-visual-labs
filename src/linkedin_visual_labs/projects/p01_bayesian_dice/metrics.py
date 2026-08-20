"""Deterministic calibration and validation for Bayesian Dice Detective."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.common.config import load_yaml_config
from linkedin_visual_labs.common.random_state import derive_seed
from linkedin_visual_labs.projects.p01_bayesian_dice.inference import (
    log_marginal_likelihood_h0,
    log_marginal_likelihood_h1,
    posterior_loaded_probability,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    BayesianModelDefinition,
    DiceModelError,
    DiceProjectConfig,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.simulation import (
    generate_rolls,
)


class DiceCalibrationError(DiceModelError):
    """Raised when calibration or validation cannot be completed."""


@dataclass(frozen=True, slots=True)
class CalibrationObservation:
    """One deterministic calibration simulation result."""

    scenario_id: str
    repetition_index: int
    seed: int
    truth_loaded: bool
    detected_loaded: bool
    detection_roll: int | None
    final_posterior_loaded: float

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise DiceCalibrationError("scenario_id must not be empty")

        if self.repetition_index < 0:
            raise DiceCalibrationError("repetition_index must be non-negative")

        if self.seed < 0:
            raise DiceCalibrationError("seed must be non-negative")

        if self.detection_roll is not None and self.detection_roll <= 0:
            raise DiceCalibrationError("detection_roll must be positive when present")

        if not (
            math.isfinite(self.final_posterior_loaded) and 0.0 <= self.final_posterior_loaded <= 1.0
        ):
            raise DiceCalibrationError("final_posterior_loaded must be finite and within [0, 1]")


@dataclass(frozen=True, slots=True)
class ScenarioCalibrationMetrics:
    """Aggregate metrics for one generating scenario."""

    scenario_id: str
    repetitions: int
    detection_count: int
    detection_rate: float
    miss_rate: float
    average_detection_roll: float | None
    mean_final_posterior_loaded: float

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible scenario metrics."""
        return {
            "scenario_id": self.scenario_id,
            "repetitions": self.repetitions,
            "detection_count": self.detection_count,
            "detection_rate": self.detection_rate,
            "miss_rate": self.miss_rate,
            "average_detection_roll": (self.average_detection_roll),
            "mean_final_posterior_loaded": (self.mean_final_posterior_loaded),
        }


@dataclass(frozen=True, slots=True)
class PosteriorCalibrationBucket:
    """One final-posterior calibration bucket."""

    bucket_index: int
    lower_bound: float
    upper_bound: float
    observation_count: int
    mean_predicted_loaded_probability: float | None
    empirical_loaded_frequency: float | None

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible bucket metrics."""
        return {
            "bucket_index": self.bucket_index,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "observation_count": self.observation_count,
            "mean_predicted_loaded_probability": (self.mean_predicted_loaded_probability),
            "empirical_loaded_frequency": (self.empirical_loaded_frequency),
        }


@dataclass(frozen=True, slots=True)
class CalibrationAcceptanceTargets:
    """Machine-readable acceptance thresholds from the YAML contract."""

    maximum_false_positive_rate: float
    minimum_clearly_loaded_true_positive_rate: float
    maximum_clearly_loaded_miss_rate: float
    maximum_clearly_loaded_average_detection_roll: float


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    """Complete deterministic Project 1 validation report."""

    project_id: str
    repetitions_per_scenario: int
    master_seed: int
    false_positive_rate: float
    clearly_loaded_true_positive_rate: float
    clearly_loaded_miss_rate: float
    clearly_loaded_average_detection_roll: float | None
    mildly_loaded_detection_rate: float
    scenario_metrics: dict[str, ScenarioCalibrationMetrics]
    posterior_calibration_buckets: tuple[
        PosteriorCalibrationBucket,
        ...,
    ]
    prior_sensitivity: tuple[dict[str, object], ...]
    acceptance_checks: dict[str, bool]
    acceptance_passed: bool
    calibration_method: str

    def as_dict(self) -> dict[str, object]:
        """Return the canonical machine-readable validation payload."""
        return {
            "project_id": self.project_id,
            "repetitions_per_scenario": (self.repetitions_per_scenario),
            "master_seed": self.master_seed,
            "false_positive_rate": self.false_positive_rate,
            "clearly_loaded_true_positive_rate": (self.clearly_loaded_true_positive_rate),
            "clearly_loaded_miss_rate": (self.clearly_loaded_miss_rate),
            "clearly_loaded_average_detection_roll": (self.clearly_loaded_average_detection_roll),
            "mildly_loaded_detection_rate": (self.mildly_loaded_detection_rate),
            "scenario_metrics": {
                scenario_id: metrics.as_dict()
                for scenario_id, metrics in self.scenario_metrics.items()
            },
            "posterior_calibration_buckets": [
                bucket.as_dict() for bucket in self.posterior_calibration_buckets
            ],
            "prior_sensitivity": list(self.prior_sensitivity),
            "acceptance_checks": dict(self.acceptance_checks),
            "acceptance_passed": self.acceptance_passed,
            "calibration_method": self.calibration_method,
        }


def calibration_seed(
    config: DiceProjectConfig,
    scenario_id: str,
    repetition_index: int,
) -> int:
    """Derive one deterministic child seed for calibration."""
    if repetition_index < 0:
        raise DiceCalibrationError("repetition_index must be non-negative")

    namespace = f"{config.project_id}.calibration.{scenario_id}.{repetition_index}"

    return derive_seed(
        config.calibration.master_seed,
        namespace,
    )


def _model_with_prior(
    model: BayesianModelDefinition,
    prior_loaded_probability: float,
) -> BayesianModelDefinition:
    """Clone the Bayesian model while changing only model prior odds."""
    return BayesianModelDefinition(
        fair_probabilities=model.fair_probabilities,
        dirichlet_alpha=model.dirichlet_alpha,
        prior_loaded_probability=prior_loaded_probability,
    )


def _evaluate_roll_sequence(
    rolls: tuple[int, ...],
    *,
    model: BayesianModelDefinition,
    loaded_threshold: float,
) -> tuple[int | None, float]:
    """Evaluate threshold crossing without constructing full history."""
    counts = [0] * 6
    first_detection_roll: int | None = None
    posterior_loaded = model.prior_loaded_probability

    for roll_index, face in enumerate(
        rolls,
        start=1,
    ):
        counts[face - 1] += 1

        log_h0 = log_marginal_likelihood_h0(
            counts,
            model.fair_probabilities.values,
        )

        log_h1 = log_marginal_likelihood_h1(
            counts,
            model.dirichlet_alpha,
        )

        posterior_loaded = posterior_loaded_probability(
            log_marginal_h0=log_h0,
            log_marginal_h1=log_h1,
            prior_loaded_probability=(model.prior_loaded_probability),
        )

        if first_detection_roll is None and posterior_loaded >= loaded_threshold:
            first_detection_roll = roll_index

    return (
        first_detection_roll,
        posterior_loaded,
    )


def evaluate_calibration_observation(
    config: DiceProjectConfig,
    scenario_id: str,
    repetition_index: int,
    *,
    prior_loaded_probability: float | None = None,
) -> CalibrationObservation:
    """Run one deterministic calibration simulation."""
    scenario = config.scenario(scenario_id)

    seed = calibration_seed(
        config,
        scenario_id,
        repetition_index,
    )

    model = (
        config.model
        if prior_loaded_probability is None
        else _model_with_prior(
            config.model,
            prior_loaded_probability,
        )
    )

    rolls = generate_rolls(
        scenario.probabilities,
        roll_count=config.roll_count,
        seed=seed,
    )

    (
        detection_roll,
        final_posterior_loaded,
    ) = _evaluate_roll_sequence(
        rolls,
        model=model,
        loaded_threshold=(config.decision.loaded_threshold),
    )

    return CalibrationObservation(
        scenario_id=scenario_id,
        repetition_index=repetition_index,
        seed=seed,
        truth_loaded=scenario_id != "fair",
        detected_loaded=detection_roll is not None,
        detection_roll=detection_roll,
        final_posterior_loaded=(final_posterior_loaded),
    )


def summarize_scenario_observations(
    scenario_id: str,
    observations: tuple[
        CalibrationObservation,
        ...,
    ],
) -> ScenarioCalibrationMetrics:
    """Aggregate deterministic calibration observations."""
    if not observations:
        raise DiceCalibrationError("scenario observations must not be empty")

    if any(observation.scenario_id != scenario_id for observation in observations):
        raise DiceCalibrationError("scenario observation identifiers do not match")

    repetitions = len(observations)

    detected = [observation for observation in observations if observation.detected_loaded]

    detection_count = len(detected)

    detection_rate = detection_count / repetitions

    miss_rate = 1.0 - detection_rate

    detection_rolls = [
        observation.detection_roll
        for observation in detected
        if observation.detection_roll is not None
    ]

    average_detection_roll = (
        math.fsum(float(value) for value in detection_rolls) / len(detection_rolls)
        if detection_rolls
        else None
    )

    mean_final_posterior_loaded = (
        math.fsum(observation.final_posterior_loaded for observation in observations) / repetitions
    )

    return ScenarioCalibrationMetrics(
        scenario_id=scenario_id,
        repetitions=repetitions,
        detection_count=detection_count,
        detection_rate=detection_rate,
        miss_rate=miss_rate,
        average_detection_roll=(average_detection_roll),
        mean_final_posterior_loaded=(mean_final_posterior_loaded),
    )


def build_posterior_calibration_buckets(
    observations: tuple[
        CalibrationObservation,
        ...,
    ],
    *,
    bucket_count: int,
) -> tuple[
    PosteriorCalibrationBucket,
    ...,
]:
    """Bucket final posterior probabilities against generating truth."""
    if bucket_count <= 0:
        raise DiceCalibrationError("bucket_count must be positive")

    if not observations:
        raise DiceCalibrationError("calibration observations must not be empty")

    grouped: list[list[CalibrationObservation]] = [[] for _ in range(bucket_count)]

    for observation in observations:
        raw_index = int(observation.final_posterior_loaded * bucket_count)

        bucket_index = min(
            raw_index,
            bucket_count - 1,
        )

        grouped[bucket_index].append(observation)

    buckets: list[PosteriorCalibrationBucket] = []

    for bucket_index, bucket_observations in enumerate(grouped):
        lower_bound = bucket_index / bucket_count

        upper_bound = (bucket_index + 1) / bucket_count

        if bucket_observations:
            count = len(bucket_observations)

            mean_prediction = (
                math.fsum(observation.final_posterior_loaded for observation in bucket_observations)
                / count
            )

            empirical_loaded = (
                sum(1 for observation in bucket_observations if observation.truth_loaded) / count
            )
        else:
            count = 0
            mean_prediction = None
            empirical_loaded = None

        buckets.append(
            PosteriorCalibrationBucket(
                bucket_index=bucket_index,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                observation_count=count,
                mean_predicted_loaded_probability=(mean_prediction),
                empirical_loaded_frequency=(empirical_loaded),
            )
        )

    return tuple(buckets)


def load_calibration_acceptance_targets(
    config: DiceProjectConfig,
) -> CalibrationAcceptanceTargets:
    """Load Step 1 calibration acceptance thresholds from YAML."""
    raw = load_yaml_config(
        config.configuration_path,
        required_keys=("acceptance",),
    )

    acceptance = raw["acceptance"]

    if not isinstance(
        acceptance,
        dict,
    ):
        raise DiceCalibrationError("acceptance must be a mapping")

    calibration = acceptance.get("calibration")

    if not isinstance(
        calibration,
        dict,
    ):
        raise DiceCalibrationError("acceptance.calibration must be a mapping")

    required = (
        "maximum_false_positive_rate",
        "minimum_clearly_loaded_true_positive_rate",
        "maximum_clearly_loaded_miss_rate",
        "maximum_clearly_loaded_average_detection_roll",
    )

    missing = [key for key in required if key not in calibration]

    if missing:
        raise DiceCalibrationError("acceptance.calibration missing fields: " + ", ".join(missing))

    values = {key: float(calibration[key]) for key in required}

    if not all(math.isfinite(value) for value in values.values()):
        raise DiceCalibrationError("acceptance targets must be finite")

    return CalibrationAcceptanceTargets(
        maximum_false_positive_rate=values["maximum_false_positive_rate"],
        minimum_clearly_loaded_true_positive_rate=values[
            "minimum_clearly_loaded_true_positive_rate"
        ],
        maximum_clearly_loaded_miss_rate=values["maximum_clearly_loaded_miss_rate"],
        maximum_clearly_loaded_average_detection_roll=values[
            "maximum_clearly_loaded_average_detection_roll"
        ],
    )


def evaluate_acceptance(
    *,
    false_positive_rate: float,
    clearly_loaded_true_positive_rate: float,
    clearly_loaded_miss_rate: float,
    clearly_loaded_average_detection_roll: float | None,
    targets: CalibrationAcceptanceTargets,
) -> dict[str, bool]:
    """Evaluate the configured machine-readable calibration gates."""
    return {
        "false_positive_rate": (false_positive_rate <= targets.maximum_false_positive_rate),
        "clearly_loaded_true_positive_rate": (
            clearly_loaded_true_positive_rate >= targets.minimum_clearly_loaded_true_positive_rate
        ),
        "clearly_loaded_miss_rate": (
            clearly_loaded_miss_rate <= targets.maximum_clearly_loaded_miss_rate
        ),
        "clearly_loaded_average_detection_roll": (
            clearly_loaded_average_detection_roll is not None
            and clearly_loaded_average_detection_roll
            <= targets.maximum_clearly_loaded_average_detection_roll
        ),
    }


def _run_scenario_calibration(
    config: DiceProjectConfig,
    scenario_id: str,
    *,
    repetitions: int,
    prior_loaded_probability: float | None = None,
) -> tuple[
    CalibrationObservation,
    ...,
]:
    """Run deterministic repeated simulations for one scenario."""
    if repetitions <= 0:
        raise DiceCalibrationError("repetitions must be positive")

    return tuple(
        evaluate_calibration_observation(
            config,
            scenario_id,
            repetition_index,
            prior_loaded_probability=(prior_loaded_probability),
        )
        for repetition_index in range(repetitions)
    )


def _run_prior_sensitivity(
    config: DiceProjectConfig,
    *,
    repetitions: int,
) -> tuple[
    dict[str, object],
    ...,
]:
    """Repeat scenario calibration across configured model priors."""
    results: list[dict[str, object]] = []

    for prior_loaded_probability in config.calibration.prior_sensitivity:
        scenario_metrics: dict[
            str,
            ScenarioCalibrationMetrics,
        ] = {}

        for scenario_id in (
            "fair",
            "mildly_loaded",
            "clearly_loaded",
        ):
            observations = _run_scenario_calibration(
                config,
                scenario_id,
                repetitions=repetitions,
                prior_loaded_probability=(prior_loaded_probability),
            )

            scenario_metrics[scenario_id] = summarize_scenario_observations(
                scenario_id,
                observations,
            )

        results.append(
            {
                "prior_loaded_probability": (prior_loaded_probability),
                "false_positive_rate": (scenario_metrics["fair"].detection_rate),
                "mildly_loaded_detection_rate": (scenario_metrics["mildly_loaded"].detection_rate),
                "clearly_loaded_true_positive_rate": (
                    scenario_metrics["clearly_loaded"].detection_rate
                ),
                "clearly_loaded_miss_rate": (scenario_metrics["clearly_loaded"].miss_rate),
                "clearly_loaded_average_detection_roll": (
                    scenario_metrics["clearly_loaded"].average_detection_roll
                ),
            }
        )

    return tuple(results)


def run_calibration(
    config: DiceProjectConfig,
    *,
    repetitions_per_scenario: int | None = None,
    include_prior_sensitivity: bool = True,
) -> CalibrationReport:
    """Run complete deterministic Project 1 calibration."""
    repetitions = (
        config.calibration.repetitions_per_scenario
        if repetitions_per_scenario is None
        else repetitions_per_scenario
    )

    if repetitions <= 0:
        raise DiceCalibrationError("repetitions_per_scenario must be positive")

    observations_by_scenario: dict[
        str,
        tuple[
            CalibrationObservation,
            ...,
        ],
    ] = {}

    scenario_metrics: dict[
        str,
        ScenarioCalibrationMetrics,
    ] = {}

    all_observations: list[CalibrationObservation] = []

    for scenario_id in (
        "fair",
        "mildly_loaded",
        "clearly_loaded",
    ):
        observations = _run_scenario_calibration(
            config,
            scenario_id,
            repetitions=repetitions,
        )

        observations_by_scenario[scenario_id] = observations

        scenario_metrics[scenario_id] = summarize_scenario_observations(
            scenario_id,
            observations,
        )

        all_observations.extend(observations)

    fair_metrics = scenario_metrics["fair"]

    mild_metrics = scenario_metrics["mildly_loaded"]

    clear_metrics = scenario_metrics["clearly_loaded"]

    calibration_buckets = build_posterior_calibration_buckets(
        tuple(all_observations),
        bucket_count=(config.calibration.posterior_bucket_count),
    )

    prior_sensitivity = (
        _run_prior_sensitivity(
            config,
            repetitions=repetitions,
        )
        if include_prior_sensitivity
        else ()
    )

    targets = load_calibration_acceptance_targets(config)

    acceptance_checks = evaluate_acceptance(
        false_positive_rate=(fair_metrics.detection_rate),
        clearly_loaded_true_positive_rate=(clear_metrics.detection_rate),
        clearly_loaded_miss_rate=(clear_metrics.miss_rate),
        clearly_loaded_average_detection_roll=(clear_metrics.average_detection_roll),
        targets=targets,
    )

    return CalibrationReport(
        project_id=config.project_id,
        repetitions_per_scenario=repetitions,
        master_seed=config.calibration.master_seed,
        false_positive_rate=(fair_metrics.detection_rate),
        clearly_loaded_true_positive_rate=(clear_metrics.detection_rate),
        clearly_loaded_miss_rate=(clear_metrics.miss_rate),
        clearly_loaded_average_detection_roll=(clear_metrics.average_detection_roll),
        mildly_loaded_detection_rate=(mild_metrics.detection_rate),
        scenario_metrics=scenario_metrics,
        posterior_calibration_buckets=(calibration_buckets),
        prior_sensitivity=prior_sensitivity,
        acceptance_checks=acceptance_checks,
        acceptance_passed=all(acceptance_checks.values()),
        calibration_method=(
            "Final posterior probability from each deterministic "
            "simulation is bucketed against generating truth; "
            "threshold metrics use first sequential crossing of "
            "the configured loaded threshold."
        ),
    )


def write_validation_json(
    report: CalibrationReport,
    output_path: Path | str,
) -> Path:
    """Write the canonical machine-readable validation report atomically."""
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    temporary_path.write_text(
        json.dumps(
            report.as_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)

    return path
