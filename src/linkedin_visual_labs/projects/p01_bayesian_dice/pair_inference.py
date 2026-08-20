"""Six-model Bayesian pair-sum inference for Bayesian Dice Detective."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    PAIR_CASE_COUNT,
    PAIR_CASE_IDS,
    PAIR_SUM_COUNT,
    PAIR_SUM_MAXIMUM,
    PAIR_SUM_MINIMUM,
    DecisionState,
    DiceModelError,
    PairExperimentDefinition,
    ProbabilityVector,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.simulation import (
    PairCaseSimulationResult,
    PairSimulationResult,
)

PAIR_MODEL_IDS = PAIR_CASE_IDS

PAIR_HISTORY_COLUMNS = (
    "case_id",
    "roll_index",
    "observed_sum",
    "count_sum_2",
    "count_sum_3",
    "count_sum_4",
    "count_sum_5",
    "count_sum_6",
    "count_sum_7",
    "count_sum_8",
    "count_sum_9",
    "count_sum_10",
    "count_sum_11",
    "count_sum_12",
    "log_likelihood_UU",
    "log_likelihood_UP",
    "log_likelihood_UF",
    "log_likelihood_PP",
    "log_likelihood_PF",
    "log_likelihood_FF",
    "posterior_UU",
    "posterior_UP",
    "posterior_UF",
    "posterior_PP",
    "posterior_PF",
    "posterior_FF",
    "posterior_loaded",
    "posterior_fair",
    "top_model",
    "decision_state",
)


class PairDiceInferenceError(DiceModelError):
    """Raised when pair-sum Bayesian inference is invalid."""


@dataclass(frozen=True, slots=True)
class PairModelPMF:
    """Exact probability distribution over pair sums 2 through 12."""

    model_id: str
    probabilities: tuple[float, ...]

    def __post_init__(self) -> None:
        if self.model_id not in PAIR_MODEL_IDS:
            raise PairDiceInferenceError(f"unknown pair model {self.model_id!r}")

        if len(self.probabilities) != PAIR_SUM_COUNT:
            raise PairDiceInferenceError("pair-model PMF must contain eleven probabilities")

        if not all(math.isfinite(value) and value > 0.0 for value in self.probabilities):
            raise PairDiceInferenceError("pair-model PMF probabilities must be finite and positive")

        if not math.isclose(
            math.fsum(self.probabilities),
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise PairDiceInferenceError("pair-model PMF must sum to one")

    def probability(
        self,
        observed_sum: int,
    ) -> float:
        """Return probability of one observed pair sum."""
        if not (PAIR_SUM_MINIMUM <= observed_sum <= PAIR_SUM_MAXIMUM):
            raise PairDiceInferenceError("observed_sum must be between 2 and 12")

        return self.probabilities[observed_sum - PAIR_SUM_MINIMUM]


@dataclass(frozen=True, slots=True)
class PairInferenceRecord:
    """One sequential six-model Bayesian update."""

    case_id: str
    roll_index: int
    observed_sum: int
    cumulative_sum_counts: tuple[int, ...]
    log_likelihoods: tuple[float, ...]
    model_posteriors: tuple[float, ...]
    posterior_loaded: float
    posterior_fair: float
    top_model: str
    decision_state: DecisionState

    def __post_init__(self) -> None:
        if self.case_id not in PAIR_CASE_IDS:
            raise PairDiceInferenceError(f"unknown case_id {self.case_id!r}")

        if self.roll_index <= 0:
            raise PairDiceInferenceError("roll_index must be positive")

        if not (PAIR_SUM_MINIMUM <= self.observed_sum <= PAIR_SUM_MAXIMUM):
            raise PairDiceInferenceError("observed_sum must be between 2 and 12")

        if len(self.cumulative_sum_counts) != PAIR_SUM_COUNT:
            raise PairDiceInferenceError("cumulative_sum_counts must contain eleven values")

        if sum(self.cumulative_sum_counts) != self.roll_index:
            raise PairDiceInferenceError("cumulative sum counts must sum to roll_index")

        if len(self.log_likelihoods) != PAIR_CASE_COUNT:
            raise PairDiceInferenceError("log_likelihoods must contain six values")

        if len(self.model_posteriors) != PAIR_CASE_COUNT:
            raise PairDiceInferenceError("model_posteriors must contain six values")

        if not all(math.isfinite(value) for value in self.log_likelihoods):
            raise PairDiceInferenceError("log likelihoods must remain finite")

        if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in self.model_posteriors):
            raise PairDiceInferenceError("model posteriors must remain within [0, 1]")

        if not math.isclose(
            math.fsum(self.model_posteriors),
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise PairDiceInferenceError("six model posteriors must sum to one")

        if not (math.isfinite(self.posterior_loaded) and 0.0 <= self.posterior_loaded <= 1.0):
            raise PairDiceInferenceError("posterior_loaded must remain within [0, 1]")

        if not (math.isfinite(self.posterior_fair) and 0.0 <= self.posterior_fair <= 1.0):
            raise PairDiceInferenceError("posterior_fair must remain within [0, 1]")

        if not math.isclose(
            self.posterior_loaded + self.posterior_fair,
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise PairDiceInferenceError("posterior loaded and fair probabilities must sum to one")

        if not math.isclose(
            self.posterior_fair,
            self.model_posteriors[0],
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise PairDiceInferenceError("posterior_fair must equal posterior(M_UU)")

        if self.top_model not in PAIR_MODEL_IDS:
            raise PairDiceInferenceError(f"unknown top_model {self.top_model!r}")

    def posterior_for(
        self,
        model_id: str,
    ) -> float:
        """Return posterior probability for one exact pair model."""
        try:
            index = PAIR_MODEL_IDS.index(model_id)
        except ValueError as exc:
            raise PairDiceInferenceError(f"unknown pair model {model_id!r}") from exc

        return self.model_posteriors[index]

    def log_likelihood_for(
        self,
        model_id: str,
    ) -> float:
        """Return cumulative log likelihood for one exact pair model."""
        try:
            index = PAIR_MODEL_IDS.index(model_id)
        except ValueError as exc:
            raise PairDiceInferenceError(f"unknown pair model {model_id!r}") from exc

        return self.log_likelihoods[index]

    def as_dict(
        self,
    ) -> dict[str, int | float | str]:
        """Return the canonical pair-history row."""
        values: dict[
            str,
            int | float | str,
        ] = {
            "case_id": self.case_id,
            "roll_index": self.roll_index,
            "observed_sum": self.observed_sum,
        }

        for observed_sum, count in zip(
            range(
                PAIR_SUM_MINIMUM,
                PAIR_SUM_MAXIMUM + 1,
            ),
            self.cumulative_sum_counts,
            strict=True,
        ):
            values[f"count_sum_{observed_sum}"] = count

        for model_id, log_likelihood in zip(
            PAIR_MODEL_IDS,
            self.log_likelihoods,
            strict=True,
        ):
            values[f"log_likelihood_{model_id}"] = log_likelihood

        for model_id, posterior in zip(
            PAIR_MODEL_IDS,
            self.model_posteriors,
            strict=True,
        ):
            values[f"posterior_{model_id}"] = posterior

        values["posterior_loaded"] = self.posterior_loaded

        values["posterior_fair"] = self.posterior_fair

        values["top_model"] = self.top_model

        values["decision_state"] = self.decision_state.value

        return values


@dataclass(frozen=True, slots=True)
class PairCaseInferenceResult:
    """Complete 10,000-roll inference trajectory for one pair case."""

    case_id: str
    records: tuple[
        PairInferenceRecord,
        ...,
    ]
    first_fair_threshold_crossing: int | None
    first_loaded_threshold_crossing: int | None
    stable_decision_roll: int | None
    stable_decision_state: DecisionState | None
    final_posterior_loaded: float
    final_posterior_fair: float
    final_top_model: str
    final_decision_state: DecisionState

    def __post_init__(self) -> None:
        if self.case_id not in PAIR_CASE_IDS:
            raise PairDiceInferenceError(f"unknown case_id {self.case_id!r}")

        if not self.records:
            raise PairDiceInferenceError("pair inference result must contain records")

        if any(record.case_id != self.case_id for record in self.records):
            raise PairDiceInferenceError("pair inference records contain mismatched case IDs")

        final = self.records[-1]

        if not math.isclose(
            final.posterior_loaded,
            self.final_posterior_loaded,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ):
            raise PairDiceInferenceError("final_posterior_loaded does not match final record")

        if not math.isclose(
            final.posterior_fair,
            self.final_posterior_fair,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ):
            raise PairDiceInferenceError("final_posterior_fair does not match final record")

        if final.top_model != self.final_top_model:
            raise PairDiceInferenceError("final_top_model does not match final record")

        if final.decision_state is not self.final_decision_state:
            raise PairDiceInferenceError("final_decision_state does not match final record")

        if self.stable_decision_roll is None:
            if self.stable_decision_state is not None:
                raise PairDiceInferenceError("stable decision state must be None when roll is None")
        else:
            if not (1 <= self.stable_decision_roll <= len(self.records)):
                raise PairDiceInferenceError("stable_decision_roll is outside trajectory")

            if self.stable_decision_state is not self.final_decision_state:
                raise PairDiceInferenceError("stable decision state must equal final state")


@dataclass(frozen=True, slots=True)
class PairInferenceResult:
    """Complete six-case Bayesian pair experiment."""

    cases: Mapping[
        str,
        PairCaseInferenceResult,
    ]

    def __post_init__(self) -> None:
        if set(self.cases) != set(PAIR_CASE_IDS):
            raise PairDiceInferenceError("pair inference result must contain all six cases")

    @property
    def total_record_count(
        self,
    ) -> int:
        """Return total sequential inference records."""
        return sum(len(result.records) for result in self.cases.values())

    def case(
        self,
        case_id: str,
    ) -> PairCaseInferenceResult:
        """Return inference result for one canonical pair case."""
        try:
            return self.cases[case_id]
        except KeyError as exc:
            allowed = ", ".join(PAIR_CASE_IDS)

            raise PairDiceInferenceError(
                f"unknown inference case {case_id!r}; allowed: {allowed}"
            ) from exc


def derive_pair_sum_pmf(
    first: ProbabilityVector,
    second: ProbabilityVector,
) -> tuple[float, ...]:
    """Convolve two six-face probability vectors into sums 2 through 12."""
    probabilities = [0.0 for _ in range(PAIR_SUM_COUNT)]

    for first_face, first_probability in enumerate(
        first.values,
        start=1,
    ):
        for second_face, second_probability in enumerate(
            second.values,
            start=1,
        ):
            observed_sum = first_face + second_face

            probabilities[observed_sum - PAIR_SUM_MINIMUM] += first_probability * second_probability

    result = tuple(probabilities)

    if not math.isclose(
        math.fsum(result),
        1.0,
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ):
        raise PairDiceInferenceError("derived pair-sum PMF does not sum to one")

    return result


def derive_pair_model_pmfs(
    experiment: PairExperimentDefinition,
) -> dict[
    str,
    PairModelPMF,
]:
    """Derive exact sum PMFs for all six Bayesian pair models."""
    pmfs: dict[
        str,
        PairModelPMF,
    ] = {}

    for model_id in PAIR_MODEL_IDS:
        case = experiment.pair_case(model_id)

        first = experiment.die_type(case.die_1_type)

        second = experiment.die_type(case.die_2_type)

        pmfs[model_id] = PairModelPMF(
            model_id=model_id,
            probabilities=derive_pair_sum_pmf(
                first.probabilities,
                second.probabilities,
            ),
        )

    if len({pmf.probabilities for pmf in pmfs.values()}) != PAIR_CASE_COUNT:
        raise PairDiceInferenceError("all six exact pair models must have distinct sum PMFs")

    return pmfs


def logsumexp(
    values: Sequence[float],
) -> float:
    """Calculate numerically stable log-sum-exp."""
    if not values:
        raise PairDiceInferenceError("logsumexp requires at least one value")

    if not all(math.isfinite(value) for value in values):
        raise PairDiceInferenceError("logsumexp values must be finite")

    maximum = max(values)

    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def normalize_model_posteriors(
    log_likelihoods: Sequence[float],
    model_priors: Mapping[str, float],
) -> tuple[float, ...]:
    """Normalize six exact-model posterior probabilities in log space."""
    if len(log_likelihoods) != PAIR_CASE_COUNT:
        raise PairDiceInferenceError("log_likelihoods must contain six values")

    if set(model_priors) != set(PAIR_MODEL_IDS):
        raise PairDiceInferenceError("model_priors must contain all six exact models")

    if not all(math.isfinite(value) for value in log_likelihoods):
        raise PairDiceInferenceError("log_likelihoods must be finite")

    if not all(
        math.isfinite(model_priors[model_id]) and model_priors[model_id] > 0.0
        for model_id in PAIR_MODEL_IDS
    ):
        raise PairDiceInferenceError("model priors must be finite and strictly positive")

    log_weights = tuple(
        math.log(model_priors[model_id]) + log_likelihood
        for model_id, log_likelihood in zip(
            PAIR_MODEL_IDS,
            log_likelihoods,
            strict=True,
        )
    )

    normalization = logsumexp(log_weights)

    unnormalized_posterior = tuple(
        math.exp(log_weight - normalization) for log_weight in log_weights
    )

    posterior_total = math.fsum(unnormalized_posterior)

    if not (math.isfinite(posterior_total) and posterior_total > 0.0):
        raise PairDiceInferenceError("posterior normalization total is invalid")

    posterior = tuple(value / posterior_total for value in unnormalized_posterior)

    if not all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in posterior):
        raise PairDiceInferenceError("normalized model posteriors must remain within [0, 1]")

    posterior_sum = math.fsum(posterior)

    if not math.isclose(
        posterior_sum,
        1.0,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    ):
        raise PairDiceInferenceError("normalized model posterior does not sum to one")

    return posterior


def find_first_state_roll(
    states: Sequence[DecisionState],
    target: DecisionState,
) -> int | None:
    """Return first one-based roll at which a target state occurs."""
    for roll_index, state in enumerate(
        states,
        start=1,
    ):
        if state is target:
            return roll_index

    return None


def find_stable_decision_roll(
    states: Sequence[DecisionState],
) -> int | None:
    """Return earliest roll of the final permanent FAIR or LOADED state."""
    if not states:
        raise PairDiceInferenceError("decision-state history must not be empty")

    final_state = states[-1]

    if final_state is DecisionState.UNCERTAIN:
        return None

    stable_index = len(states) - 1

    while stable_index > 0 and states[stable_index - 1] is final_state:
        stable_index -= 1

    return stable_index + 1


def infer_pair_case(
    experiment: PairExperimentDefinition,
    simulation: PairCaseSimulationResult,
) -> PairCaseInferenceResult:
    """Run sequential six-model inference for one 10,000-roll pair case."""
    pmfs = derive_pair_model_pmfs(experiment)

    log_probabilities = {
        model_id: tuple(math.log(probability) for probability in pmfs[model_id].probabilities)
        for model_id in PAIR_MODEL_IDS
    }

    log_likelihoods = [0.0 for _ in range(PAIR_CASE_COUNT)]

    sum_counts = [0 for _ in range(PAIR_SUM_COUNT)]

    records: list[PairInferenceRecord] = []

    states: list[DecisionState] = []

    first_fair_crossing: int | None = None
    first_loaded_crossing: int | None = None

    for roll_index, observed_sum in enumerate(
        simulation.sums,
        start=1,
    ):
        sum_index = observed_sum - PAIR_SUM_MINIMUM

        sum_counts[sum_index] += 1

        for model_index, model_id in enumerate(PAIR_MODEL_IDS):
            log_likelihoods[model_index] += log_probabilities[model_id][sum_index]

        model_posteriors = normalize_model_posteriors(
            log_likelihoods,
            experiment.model_priors.values,
        )

        posterior_fair = model_posteriors[0]

        posterior_loaded = 1.0 - posterior_fair

        decision_state = experiment.decision.classify(posterior_loaded)

        if first_fair_crossing is None and decision_state is DecisionState.FAIR:
            first_fair_crossing = roll_index

        if first_loaded_crossing is None and decision_state is DecisionState.LOADED:
            first_loaded_crossing = roll_index

        top_index = max(
            range(PAIR_CASE_COUNT),
            key=model_posteriors.__getitem__,
        )

        top_model = PAIR_MODEL_IDS[top_index]

        record = PairInferenceRecord(
            case_id=simulation.case_id,
            roll_index=roll_index,
            observed_sum=observed_sum,
            cumulative_sum_counts=tuple(sum_counts),
            log_likelihoods=tuple(log_likelihoods),
            model_posteriors=(model_posteriors),
            posterior_loaded=(posterior_loaded),
            posterior_fair=(posterior_fair),
            top_model=top_model,
            decision_state=(decision_state),
        )

        records.append(record)

        states.append(decision_state)

    stable_roll = find_stable_decision_roll(states)

    final_record = records[-1]

    stable_state = None if stable_roll is None else final_record.decision_state

    return PairCaseInferenceResult(
        case_id=simulation.case_id,
        records=tuple(records),
        first_fair_threshold_crossing=(first_fair_crossing),
        first_loaded_threshold_crossing=(first_loaded_crossing),
        stable_decision_roll=(stable_roll),
        stable_decision_state=(stable_state),
        final_posterior_loaded=(final_record.posterior_loaded),
        final_posterior_fair=(final_record.posterior_fair),
        final_top_model=(final_record.top_model),
        final_decision_state=(final_record.decision_state),
    )


def infer_all_pair_cases(
    experiment: PairExperimentDefinition,
    simulation: PairSimulationResult,
) -> PairInferenceResult:
    """Run authoritative six-model inference across all six cases."""
    results = {
        case_id: infer_pair_case(
            experiment,
            simulation.case(case_id),
        )
        for case_id in PAIR_MODEL_IDS
    }

    return PairInferenceResult(cases=results)
