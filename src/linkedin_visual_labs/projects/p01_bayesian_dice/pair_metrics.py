"""Canonical metrics, summaries, and validation for pair-dice inference."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    PAIR_CASE_IDS,
    DecisionState,
    DiceModelError,
    DiceProjectConfig,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pair_inference import (
    PAIR_HISTORY_COLUMNS,
    PairCaseInferenceResult,
    PairInferenceResult,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.simulation import (
    PairCaseSimulationResult,
    PairSimulationResult,
)

PAIR_VALIDATION_SCHEMA_VERSION = 1


class PairDiceMetricsError(DiceModelError):
    """Raised when canonical pair experiment metrics are invalid."""


@dataclass(frozen=True, slots=True)
class PairCaseSummary:
    """Headline and diagnostic metrics for one canonical pair case."""

    case_id: str
    label: str
    truth_loaded: bool
    expected_final_state: DecisionState
    roll_count: int
    seed: int
    first_fair_threshold_crossing: int | None
    first_loaded_threshold_crossing: int | None
    stable_decision_roll: int | None
    stable_decision_state: DecisionState | None
    final_decision_state: DecisionState
    final_posterior_loaded: float
    final_posterior_fair: float
    final_top_model: str

    def __post_init__(self) -> None:
        if self.case_id not in PAIR_CASE_IDS:
            raise PairDiceMetricsError(f"unknown pair case {self.case_id!r}")

        if not self.label.strip():
            raise PairDiceMetricsError("pair-case label must not be empty")

        if self.roll_count != 10_000:
            raise PairDiceMetricsError("canonical pair summary must use 10,000 rolls")

        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise PairDiceMetricsError("pair summary seed must be a non-negative integer")

        if not (
            math.isfinite(self.final_posterior_loaded) and 0.0 <= self.final_posterior_loaded <= 1.0
        ):
            raise PairDiceMetricsError("final_posterior_loaded must remain within [0, 1]")

        if not (
            math.isfinite(self.final_posterior_fair) and 0.0 <= self.final_posterior_fair <= 1.0
        ):
            raise PairDiceMetricsError("final_posterior_fair must remain within [0, 1]")

        if not math.isclose(
            self.final_posterior_loaded + self.final_posterior_fair,
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise PairDiceMetricsError("final loaded/fair posterior probabilities must sum to one")

        if self.stable_decision_roll is None:
            if self.stable_decision_state is not None:
                raise PairDiceMetricsError("stable state must be None when stable roll is None")
        else:
            if not (1 <= self.stable_decision_roll <= self.roll_count):
                raise PairDiceMetricsError("stable decision roll is outside canonical history")

            if self.stable_decision_state is not self.final_decision_state:
                raise PairDiceMetricsError("stable decision state must equal final decision state")

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible pair-case summary."""
        return {
            "case_id": self.case_id,
            "label": self.label,
            "truth_loaded": self.truth_loaded,
            "expected_final_state": (self.expected_final_state.value),
            "roll_count": self.roll_count,
            "seed": self.seed,
            "first_fair_threshold_crossing": (self.first_fair_threshold_crossing),
            "first_loaded_threshold_crossing": (self.first_loaded_threshold_crossing),
            "stable_decision_roll": (self.stable_decision_roll),
            "stable_decision_state": (
                None if self.stable_decision_state is None else self.stable_decision_state.value
            ),
            "final_decision_state": (self.final_decision_state.value),
            "final_posterior_loaded": (self.final_posterior_loaded),
            "final_posterior_fair": (self.final_posterior_fair),
            "final_top_model": self.final_top_model,
        }


@dataclass(frozen=True, slots=True)
class PairValidationCheck:
    """One deterministic validation assertion."""

    check_id: str
    passed: bool
    detail: str

    def __post_init__(self) -> None:
        if not self.check_id.strip():
            raise PairDiceMetricsError("validation check_id must not be empty")

        if not self.detail.strip():
            raise PairDiceMetricsError("validation detail must not be empty")

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible validation check."""
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class PairValidationReport:
    """Complete deterministic acceptance report for the pair experiment."""

    schema_version: int
    project_id: str
    roll_count_per_case: int
    total_observation_count: int
    headline_roll_metric: str
    checks: tuple[
        PairValidationCheck,
        ...,
    ]

    def __post_init__(self) -> None:
        if self.schema_version != PAIR_VALIDATION_SCHEMA_VERSION:
            raise PairDiceMetricsError("unexpected pair validation schema version")

        if self.project_id != "p01_bayesian_dice":
            raise PairDiceMetricsError("validation project_id must equal p01_bayesian_dice")

        if self.roll_count_per_case != 10_000:
            raise PairDiceMetricsError("validation must use 10,000 rolls per case")

        if self.total_observation_count != 60_000:
            raise PairDiceMetricsError("validation must cover 60,000 observations")

        if self.headline_roll_metric != "stable_decision_roll":
            raise PairDiceMetricsError("headline metric must be stable_decision_roll")

        if not self.checks:
            raise PairDiceMetricsError("validation report must contain checks")

        check_ids = tuple(check.check_id for check in self.checks)

        if len(check_ids) != len(set(check_ids)):
            raise PairDiceMetricsError("validation check IDs must be unique")

    @property
    def passed(self) -> bool:
        """Return True only when every deterministic check passes."""
        return all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible validation report."""
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "passed": self.passed,
            "roll_count_per_case": (self.roll_count_per_case),
            "total_observation_count": (self.total_observation_count),
            "headline_roll_metric": (self.headline_roll_metric),
            "checks": [check.as_dict() for check in self.checks],
            "failed_check_ids": [check.check_id for check in self.checks if not check.passed],
        }


def expected_state_for_truth(
    truth_loaded: bool,
) -> DecisionState:
    """Return expected terminal classification for generating truth."""
    return DecisionState.LOADED if truth_loaded else DecisionState.FAIR


def build_pair_case_summary(
    simulation: PairCaseSimulationResult,
    inference: PairCaseInferenceResult,
) -> PairCaseSummary:
    """Build canonical metrics for one pair case."""
    if simulation.case_id != inference.case_id:
        raise PairDiceMetricsError("simulation and inference case IDs do not match")

    return PairCaseSummary(
        case_id=simulation.case_id,
        label=simulation.label,
        truth_loaded=simulation.truth_loaded,
        expected_final_state=expected_state_for_truth(simulation.truth_loaded),
        roll_count=simulation.roll_count,
        seed=simulation.seed,
        first_fair_threshold_crossing=(inference.first_fair_threshold_crossing),
        first_loaded_threshold_crossing=(inference.first_loaded_threshold_crossing),
        stable_decision_roll=(inference.stable_decision_roll),
        stable_decision_state=(inference.stable_decision_state),
        final_decision_state=(inference.final_decision_state),
        final_posterior_loaded=(inference.final_posterior_loaded),
        final_posterior_fair=(inference.final_posterior_fair),
        final_top_model=(inference.final_top_model),
    )


def build_pair_case_summaries(
    simulation: PairSimulationResult,
    inference: PairInferenceResult,
) -> dict[
    str,
    PairCaseSummary,
]:
    """Build canonical summaries for all six pair cases."""
    return {
        case_id: build_pair_case_summary(
            simulation.case(case_id),
            inference.case(case_id),
        )
        for case_id in PAIR_CASE_IDS
    }


def pair_summary_payload(
    config: DiceProjectConfig,
    simulation: PairSimulationResult,
    inference: PairInferenceResult,
) -> dict[str, object]:
    """Build the canonical six-case summary payload."""
    summaries = build_pair_case_summaries(
        simulation,
        inference,
    )

    return {
        "project_id": config.project_id,
        "viewer_question": (config.pair_experiment.viewer_question),
        "observation_type": (config.pair_experiment.observation.observation_type),
        "roll_count_per_case": (config.pair_experiment.roll_count_per_case),
        "total_observation_count": (simulation.total_observation_count),
        "case_order": list(PAIR_CASE_IDS),
        "loaded_probability_definition": (config.pair_experiment.loaded_probability_definition),
        "fair_threshold": (config.pair_experiment.decision.fair_threshold),
        "loaded_threshold": (config.pair_experiment.decision.loaded_threshold),
        "headline_roll_metric": (config.pair_experiment.decision.headline_roll_metric),
        "cases": {case_id: summaries[case_id].as_dict() for case_id in PAIR_CASE_IDS},
    }


def _stable_suffix_is_valid(
    result: PairCaseInferenceResult,
) -> bool:
    stable_roll = result.stable_decision_roll

    if stable_roll is None:
        return False

    stable_index = stable_roll - 1

    final_state = result.final_decision_state

    return all(record.decision_state is final_state for record in result.records[stable_index:])


def _stable_roll_is_earliest(
    result: PairCaseInferenceResult,
) -> bool:
    stable_roll = result.stable_decision_roll

    if stable_roll is None:
        return False

    stable_index = stable_roll - 1

    if stable_index == 0:
        return True

    return result.records[stable_index - 1].decision_state is not result.final_decision_state


def _all_posterior_records_are_valid(
    result: PairCaseInferenceResult,
) -> bool:
    return all(
        math.isclose(
            math.fsum(record.model_posteriors),
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        and math.isclose(
            record.posterior_loaded,
            1.0 - record.posterior_for("UU"),
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        and math.isclose(
            record.posterior_loaded + record.posterior_fair,
            1.0,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        for record in result.records
    )


def build_pair_validation_report(
    config: DiceProjectConfig,
    simulation: PairSimulationResult,
    inference: PairInferenceResult,
) -> PairValidationReport:
    """Validate the complete canonical pair experiment deterministically."""
    checks: list[PairValidationCheck] = []

    def add_check(
        check_id: str,
        passed: bool,
        detail: str,
    ) -> None:
        checks.append(
            PairValidationCheck(
                check_id=check_id,
                passed=passed,
                detail=detail,
            )
        )

    experiment = config.pair_experiment

    add_check(
        "experiment.authoritative",
        experiment.authoritative,
        "Pair experiment is the authoritative Project 1 contract.",
    )

    add_check(
        "experiment.case_count",
        len(simulation.cases) == 6 and len(inference.cases) == 6,
        "Simulation and inference each contain six canonical pair cases.",
    )

    add_check(
        "experiment.roll_count_per_case",
        simulation.roll_count_per_case == 10_000,
        "Every canonical pair case uses 10,000 rolls.",
    )

    add_check(
        "experiment.total_observations",
        simulation.total_observation_count == 60_000 and inference.total_record_count == 60_000,
        "Simulation and inference each cover exactly 60,000 observations.",
    )

    add_check(
        "experiment.headline_metric",
        (experiment.decision.headline_roll_metric) == "stable_decision_roll"
        and not (experiment.decision.use_first_threshold_crossing_as_headline),
        "Stable decision roll is the headline metric; first crossings are diagnostic.",
    )

    add_check(
        "experiment.sum_only_inference",
        (experiment.observation.observation_type) == "pair_sum"
        and not (experiment.observation.individual_faces_visible_to_inference),
        "Inference contract exposes pair sums only, never individual die faces.",
    )

    for case_id in PAIR_CASE_IDS:
        simulation_case = simulation.case(case_id)

        inference_case = inference.case(case_id)

        expected_state = expected_state_for_truth(simulation_case.truth_loaded)

        add_check(
            f"case.{case_id}.record_count",
            len(inference_case.records) == 10_000 and len(simulation_case.sums) == 10_000,
            f"{case_id} contains 10,000 simulated sums and 10,000 inference records.",
        )

        add_check(
            f"case.{case_id}.observation_identity",
            all(
                record.observed_sum == observed_sum
                for record, observed_sum in zip(
                    inference_case.records,
                    simulation_case.sums,
                    strict=True,
                )
            ),
            f"{case_id} inference observations exactly match simulated pair sums.",
        )

        add_check(
            f"case.{case_id}.truth_alignment",
            (inference_case.final_decision_state) is expected_state,
            (
                f"{case_id} final state "
                f"{inference_case.final_decision_state.value} "
                f"matches expected {expected_state.value}."
            ),
        )

        add_check(
            f"case.{case_id}.stable_decision_exists",
            (inference_case.stable_decision_roll) is not None,
            f"{case_id} obtains a stable decision by roll 10,000.",
        )

        add_check(
            f"case.{case_id}.stable_suffix",
            _stable_suffix_is_valid(inference_case),
            f"{case_id} remains in its final state from stable_decision_roll through roll 10,000.",
        )

        add_check(
            f"case.{case_id}.stable_roll_earliest",
            _stable_roll_is_earliest(inference_case),
            f"{case_id} stable_decision_roll is the earliest permanent final-state roll.",
        )

        add_check(
            f"case.{case_id}.posterior_integrity",
            _all_posterior_records_are_valid(inference_case),
            f"{case_id} posterior vectors normalize and satisfy P(load)=1-P(UU) throughout.",
        )

        add_check(
            f"case.{case_id}.final_threshold",
            (
                inference_case.final_posterior_loaded <= experiment.decision.fair_threshold
                if expected_state is DecisionState.FAIR
                else inference_case.final_posterior_loaded >= experiment.decision.loaded_threshold
            ),
            f"{case_id} final P(load) satisfies its expected decision threshold.",
        )

        add_check(
            f"case.{case_id}.sum_count_integrity",
            (inference_case.records[-1].cumulative_sum_counts) == simulation_case.final_sum_counts,
            f"{case_id} final inference sum counts match the simulation counts.",
        )

    return PairValidationReport(
        schema_version=(PAIR_VALIDATION_SCHEMA_VERSION),
        project_id=config.project_id,
        roll_count_per_case=(experiment.roll_count_per_case),
        total_observation_count=(simulation.total_observation_count),
        headline_roll_metric=(experiment.decision.headline_roll_metric),
        checks=tuple(checks),
    )


def write_pair_case_histories_csv(
    inference: PairInferenceResult,
    output_path: Path | str,
) -> Path:
    """Write all 60,000 sequential inference records deterministically."""
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
            fieldnames=list(PAIR_HISTORY_COLUMNS),
            extrasaction="raise",
        )

        writer.writeheader()

        for case_id in PAIR_CASE_IDS:
            result = inference.case(case_id)

            for record in result.records:
                writer.writerow(record.as_dict())

    temporary_path.replace(path)

    return path


def _write_json(
    payload: Mapping[str, object],
    output_path: Path | str,
) -> Path:
    """Write one deterministic JSON payload atomically."""
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)

    return path


def write_pair_case_summary_json(
    config: DiceProjectConfig,
    simulation: PairSimulationResult,
    inference: PairInferenceResult,
    output_path: Path | str,
) -> Path:
    """Write canonical six-case headline and diagnostic metrics."""
    return _write_json(
        pair_summary_payload(
            config,
            simulation,
            inference,
        ),
        output_path,
    )


def write_pair_validation_json(
    report: PairValidationReport,
    output_path: Path | str,
) -> Path:
    """Write deterministic pair-experiment acceptance evidence."""
    return _write_json(
        report.as_dict(),
        output_path,
    )
