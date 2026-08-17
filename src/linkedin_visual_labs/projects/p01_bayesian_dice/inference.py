"""Sequential Bayesian model comparison for Bayesian Dice Detective."""

from __future__ import annotations

import csv
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    FACE_COUNT,
    BayesianModelDefinition,
    DecisionState,
    DecisionThresholds,
    DiceModelError,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.simulation import (
    SimulationResult,
    cumulative_roll_records,
)

POSTERIOR_HISTORY_COLUMNS = (
    "roll_index",
    "observed_face",
    "count_1",
    "count_2",
    "count_3",
    "count_4",
    "count_5",
    "count_6",
    "log_marginal_h0",
    "log_marginal_h1",
    "log_bayes_factor_h1_h0",
    "posterior_loaded",
    "posterior_fair",
    "predictive_face_1",
    "predictive_face_2",
    "predictive_face_3",
    "predictive_face_4",
    "predictive_face_5",
    "predictive_face_6",
    "decision_state",
)


class DiceInferenceError(DiceModelError):
    """Raised when Bayesian inference cannot be evaluated safely."""


@dataclass(frozen=True, slots=True)
class InferenceRecord:
    """One sequential Bayesian update after an observed roll."""

    roll_index: int
    observed_face: int
    cumulative_counts: tuple[int, ...]
    log_marginal_h0: float
    log_marginal_h1: float
    log_bayes_factor_h1_h0: float
    posterior_loaded: float
    posterior_fair: float
    predictive_probabilities: tuple[float, ...]
    decision_state: DecisionState

    def __post_init__(self) -> None:
        if self.roll_index <= 0:
            raise DiceInferenceError("roll_index must be positive")

        if len(self.cumulative_counts) != FACE_COUNT:
            raise DiceInferenceError("cumulative_counts must contain six values")

        if len(self.predictive_probabilities) != FACE_COUNT:
            raise DiceInferenceError("predictive probabilities must contain six values")

        finite_values = (
            self.log_marginal_h0,
            self.log_marginal_h1,
            self.log_bayes_factor_h1_h0,
            self.posterior_loaded,
            self.posterior_fair,
            *self.predictive_probabilities,
        )

        if not all(math.isfinite(value) for value in finite_values):
            raise DiceInferenceError("inference record contains non-finite numeric values")

        if not 0.0 <= self.posterior_loaded <= 1.0:
            raise DiceInferenceError("posterior_loaded must remain within [0, 1]")

        if not 0.0 <= self.posterior_fair <= 1.0:
            raise DiceInferenceError("posterior_fair must remain within [0, 1]")

        if not math.isclose(
            self.posterior_loaded + self.posterior_fair,
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise DiceInferenceError("posterior model probabilities must sum to one")

        if not all(0.0 <= probability <= 1.0 for probability in self.predictive_probabilities):
            raise DiceInferenceError("predictive probabilities must remain within [0, 1]")

        if not math.isclose(
            math.fsum(self.predictive_probabilities),
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise DiceInferenceError("predictive probabilities must sum to one")

    def as_dict(self) -> dict[str, int | float | str]:
        """Return the canonical posterior-history row."""
        return {
            "roll_index": self.roll_index,
            "observed_face": self.observed_face,
            "count_1": self.cumulative_counts[0],
            "count_2": self.cumulative_counts[1],
            "count_3": self.cumulative_counts[2],
            "count_4": self.cumulative_counts[3],
            "count_5": self.cumulative_counts[4],
            "count_6": self.cumulative_counts[5],
            "log_marginal_h0": self.log_marginal_h0,
            "log_marginal_h1": self.log_marginal_h1,
            "log_bayes_factor_h1_h0": self.log_bayes_factor_h1_h0,
            "posterior_loaded": self.posterior_loaded,
            "posterior_fair": self.posterior_fair,
            "predictive_face_1": self.predictive_probabilities[0],
            "predictive_face_2": self.predictive_probabilities[1],
            "predictive_face_3": self.predictive_probabilities[2],
            "predictive_face_4": self.predictive_probabilities[3],
            "predictive_face_5": self.predictive_probabilities[4],
            "predictive_face_6": self.predictive_probabilities[5],
            "decision_state": self.decision_state.value,
        }


@dataclass(frozen=True, slots=True)
class InferenceResult:
    """Complete sequential Bayesian inference result."""

    records: tuple[InferenceRecord, ...]
    first_loaded_detection_roll: int | None
    final_decision_state: DecisionState
    final_posterior_loaded: float

    def __post_init__(self) -> None:
        if not self.records:
            raise DiceInferenceError("inference result must contain at least one record")

        if self.first_loaded_detection_roll is not None and not (
            1 <= self.first_loaded_detection_roll <= len(self.records)
        ):
            raise DiceInferenceError("first_loaded_detection_roll is outside record range")

        final = self.records[-1]

        if final.decision_state is not self.final_decision_state:
            raise DiceInferenceError("final_decision_state does not match final record")

        if not math.isclose(
            final.posterior_loaded,
            self.final_posterior_loaded,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ):
            raise DiceInferenceError("final_posterior_loaded does not match final record")


def _validate_counts(
    counts: Sequence[int],
) -> tuple[int, ...]:
    """Validate a six-face cumulative count vector."""
    if len(counts) != FACE_COUNT:
        raise DiceInferenceError("counts must contain six values")

    validated: list[int] = []

    for value in counts:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise DiceInferenceError("counts must contain non-negative integers")

        validated.append(value)

    return tuple(validated)


def log_marginal_likelihood_h0(
    counts: Sequence[int],
    fair_probabilities: Sequence[float],
) -> float:
    """Calculate ordered-sequence log likelihood under H0."""
    validated_counts = _validate_counts(counts)

    if len(fair_probabilities) != FACE_COUNT:
        raise DiceInferenceError("fair probabilities must contain six values")

    total = 0.0

    for count, probability in zip(
        validated_counts,
        fair_probabilities,
        strict=True,
    ):
        if not math.isfinite(probability) or probability <= 0.0 or probability > 1.0:
            raise DiceInferenceError("H0 probabilities must be finite and strictly positive")

        total += count * math.log(probability)

    if not math.isfinite(total):
        raise DiceInferenceError("H0 log marginal likelihood is non-finite")

    return total


def log_marginal_likelihood_h1(
    counts: Sequence[int],
    dirichlet_alpha: Sequence[float],
) -> float:
    """Calculate integrated ordered-sequence likelihood under H1."""
    validated_counts = _validate_counts(counts)

    if len(dirichlet_alpha) != FACE_COUNT:
        raise DiceInferenceError("Dirichlet alpha must contain six values")

    alpha = tuple(float(value) for value in dirichlet_alpha)

    if not all(math.isfinite(value) and value > 0.0 for value in alpha):
        raise DiceInferenceError("Dirichlet alpha must be finite and positive")

    alpha_total = math.fsum(alpha)
    observation_count = sum(validated_counts)

    result = math.lgamma(alpha_total) - math.lgamma(alpha_total + observation_count)

    for alpha_i, count_i in zip(
        alpha,
        validated_counts,
        strict=True,
    ):
        result += math.lgamma(alpha_i + count_i) - math.lgamma(alpha_i)

    if not math.isfinite(result):
        raise DiceInferenceError("H1 log marginal likelihood is non-finite")

    return result


def posterior_predictive_probabilities(
    counts: Sequence[int],
    dirichlet_alpha: Sequence[float],
) -> tuple[float, ...]:
    """Calculate H1 posterior predictive face probabilities."""
    validated_counts = _validate_counts(counts)

    if len(dirichlet_alpha) != FACE_COUNT:
        raise DiceInferenceError("Dirichlet alpha must contain six values")

    alpha = tuple(float(value) for value in dirichlet_alpha)

    if not all(math.isfinite(value) and value > 0.0 for value in alpha):
        raise DiceInferenceError("Dirichlet alpha must be finite and positive")

    denominator = math.fsum(alpha) + sum(validated_counts)

    probabilities = tuple(
        (alpha_i + count_i) / denominator
        for alpha_i, count_i in zip(
            alpha,
            validated_counts,
            strict=True,
        )
    )

    if not math.isclose(
        math.fsum(probabilities),
        1.0,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ):
        raise DiceInferenceError("posterior predictive probabilities do not sum to one")

    return probabilities


def _logsumexp_two(
    first: float,
    second: float,
) -> float:
    """Stable two-value log-sum-exp."""
    maximum = max(
        first,
        second,
    )

    return maximum + math.log(math.exp(first - maximum) + math.exp(second - maximum))


def posterior_loaded_probability(
    *,
    log_marginal_h0: float,
    log_marginal_h1: float,
    prior_loaded_probability: float,
) -> float:
    """Calculate stable posterior loaded-model probability."""
    if not (math.isfinite(log_marginal_h0) and math.isfinite(log_marginal_h1)):
        raise DiceInferenceError("log marginal likelihoods must be finite")

    if not (math.isfinite(prior_loaded_probability) and 0.0 < prior_loaded_probability < 1.0):
        raise DiceInferenceError("prior_loaded_probability must be strictly between 0 and 1")

    prior_fair_probability = 1.0 - prior_loaded_probability

    log_weight_loaded = math.log(prior_loaded_probability) + log_marginal_h1

    log_weight_fair = math.log(prior_fair_probability) + log_marginal_h0

    normalization = _logsumexp_two(
        log_weight_loaded,
        log_weight_fair,
    )

    posterior = math.exp(log_weight_loaded - normalization)

    if not (math.isfinite(posterior) and 0.0 <= posterior <= 1.0):
        raise DiceInferenceError("posterior loaded probability is invalid")

    return posterior


def infer_counts(
    counts: Sequence[int],
    *,
    model: BayesianModelDefinition,
    thresholds: DecisionThresholds,
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    tuple[float, ...],
    DecisionState,
]:
    """Evaluate both hypotheses and classification for one count vector."""
    log_h0 = log_marginal_likelihood_h0(
        counts,
        model.fair_probabilities.values,
    )

    log_h1 = log_marginal_likelihood_h1(
        counts,
        model.dirichlet_alpha,
    )

    log_bayes_factor = log_h1 - log_h0

    posterior_loaded = posterior_loaded_probability(
        log_marginal_h0=log_h0,
        log_marginal_h1=log_h1,
        prior_loaded_probability=(model.prior_loaded_probability),
    )

    posterior_fair = 1.0 - posterior_loaded

    predictive = posterior_predictive_probabilities(
        counts,
        model.dirichlet_alpha,
    )

    decision_state = thresholds.classify(posterior_loaded)

    return (
        log_h0,
        log_h1,
        log_bayes_factor,
        posterior_loaded,
        posterior_fair,
        predictive,
        decision_state,
    )


def sequential_inference(
    simulation: SimulationResult,
    *,
    model: BayesianModelDefinition,
    thresholds: DecisionThresholds,
) -> InferenceResult:
    """Calculate Bayesian evidence after every simulated observation."""
    roll_records = cumulative_roll_records(simulation.rolls)

    inference_records: list[InferenceRecord] = []
    first_loaded_detection_roll: int | None = None

    for roll_record in roll_records:
        (
            log_h0,
            log_h1,
            log_bayes_factor,
            posterior_loaded,
            posterior_fair,
            predictive,
            decision_state,
        ) = infer_counts(
            roll_record.cumulative_counts,
            model=model,
            thresholds=thresholds,
        )

        if first_loaded_detection_roll is None and decision_state is DecisionState.LOADED:
            first_loaded_detection_roll = roll_record.roll_index

        inference_records.append(
            InferenceRecord(
                roll_index=roll_record.roll_index,
                observed_face=roll_record.observed_face,
                cumulative_counts=(roll_record.cumulative_counts),
                log_marginal_h0=log_h0,
                log_marginal_h1=log_h1,
                log_bayes_factor_h1_h0=(log_bayes_factor),
                posterior_loaded=posterior_loaded,
                posterior_fair=posterior_fair,
                predictive_probabilities=predictive,
                decision_state=decision_state,
            )
        )

    final_record = inference_records[-1]

    return InferenceResult(
        records=tuple(inference_records),
        first_loaded_detection_roll=(first_loaded_detection_roll),
        final_decision_state=(final_record.decision_state),
        final_posterior_loaded=(final_record.posterior_loaded),
    )


def write_posterior_history_csv(
    inference: InferenceResult,
    output_path: Path | str,
) -> Path:
    """Write canonical sequential Bayesian history atomically."""
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    with temporary_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(POSTERIOR_HISTORY_COLUMNS),
        )

        writer.writeheader()

        for record in inference.records:
            writer.writerow(record.as_dict())

    temporary_path.replace(path)

    return path
