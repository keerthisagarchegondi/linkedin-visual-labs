"""Deterministic simulation engines for Bayesian Dice Detective."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from linkedin_visual_labs.common.random_state import create_rng
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    FACE_COUNT,
    PAIR_CASE_COUNT,
    PAIR_CASE_IDS,
    PAIR_SUM_COUNT,
    PAIR_SUM_MAXIMUM,
    PAIR_SUM_MINIMUM,
    DiceModelError,
    DiceProjectConfig,
    PairExperimentDefinition,
    ProbabilityVector,
)

MIN_FACE = 1
MAX_FACE = FACE_COUNT

PAIR_SUM_VALUES = tuple(
    range(
        PAIR_SUM_MINIMUM,
        PAIR_SUM_MAXIMUM + 1,
    )
)

PAIR_SIMULATION_REQUIRED_FIELDS = (
    "project_id",
    "roll_count_per_case",
    "cases",
)

PAIR_CASE_SIMULATION_REQUIRED_FIELDS = (
    "case_id",
    "label",
    "seed",
    "die_1_type",
    "die_2_type",
    "die_1_probabilities",
    "die_2_probabilities",
    "sums",
    "final_sum_counts",
)

###############################################################################
# AUTHORITATIVE PAIR-DICE SIMULATION
###############################################################################


class PairDiceSimulationError(DiceModelError):
    """Raised when deterministic pair-dice simulation fails."""


@dataclass(frozen=True, slots=True)
class PairRoll:
    """One physical pair roll and its inference-facing sum."""

    roll_index: int
    die_1_face: int
    die_2_face: int
    observed_sum: int

    def __post_init__(self) -> None:
        if self.roll_index <= 0:
            raise PairDiceSimulationError("roll_index must be positive")

        if not MIN_FACE <= self.die_1_face <= MAX_FACE:
            raise PairDiceSimulationError("die_1_face must be between 1 and 6")

        if not MIN_FACE <= self.die_2_face <= MAX_FACE:
            raise PairDiceSimulationError("die_2_face must be between 1 and 6")

        expected_sum = self.die_1_face + self.die_2_face

        if self.observed_sum != expected_sum:
            raise PairDiceSimulationError("observed_sum must equal die_1_face + die_2_face")

        if not (PAIR_SUM_MINIMUM <= self.observed_sum <= PAIR_SUM_MAXIMUM):
            raise PairDiceSimulationError("observed_sum must be between 2 and 12")


@dataclass(frozen=True, slots=True)
class PairSumRecord:
    """One inference-facing sum with cumulative counts for sums 2 through 12."""

    roll_index: int
    observed_sum: int
    cumulative_sum_counts: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.roll_index <= 0:
            raise PairDiceSimulationError("roll_index must be positive")

        if not (PAIR_SUM_MINIMUM <= self.observed_sum <= PAIR_SUM_MAXIMUM):
            raise PairDiceSimulationError("observed_sum must be between 2 and 12")

        if len(self.cumulative_sum_counts) != PAIR_SUM_COUNT:
            raise PairDiceSimulationError("cumulative_sum_counts must contain eleven values")

        if not all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in self.cumulative_sum_counts
        ):
            raise PairDiceSimulationError("cumulative sum counts must be non-negative integers")

        if sum(self.cumulative_sum_counts) != self.roll_index:
            raise PairDiceSimulationError("cumulative sum counts must sum to roll_index")


@dataclass(frozen=True, slots=True)
class PairCaseSimulationResult:
    """Complete deterministic simulation for one canonical pair case."""

    case_id: str
    label: str
    seed: int
    die_1_type: str
    die_2_type: str
    die_1_probabilities: tuple[float, ...]
    die_2_probabilities: tuple[float, ...]
    truth_loaded: bool
    roll_count: int
    die_1_rolls: tuple[int, ...]
    die_2_rolls: tuple[int, ...]
    sums: tuple[int, ...]
    final_sum_counts: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.case_id not in PAIR_CASE_IDS:
            raise PairDiceSimulationError(f"unknown canonical pair case {self.case_id!r}")

        if not self.label.strip():
            raise PairDiceSimulationError("pair-case label must not be empty")

        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise PairDiceSimulationError("pair-case seed must be a non-negative integer")

        if self.roll_count <= 0:
            raise PairDiceSimulationError("roll_count must be positive")

        ProbabilityVector(self.die_1_probabilities)

        ProbabilityVector(self.die_2_probabilities)

        if len(self.die_1_rolls) != self.roll_count:
            raise PairDiceSimulationError("die_1_rolls length must equal roll_count")

        if len(self.die_2_rolls) != self.roll_count:
            raise PairDiceSimulationError("die_2_rolls length must equal roll_count")

        if len(self.sums) != self.roll_count:
            raise PairDiceSimulationError("sum sequence length must equal roll_count")

        if not all(MIN_FACE <= face <= MAX_FACE for face in self.die_1_rolls):
            raise PairDiceSimulationError("die_1_rolls contain invalid faces")

        if not all(MIN_FACE <= face <= MAX_FACE for face in self.die_2_rolls):
            raise PairDiceSimulationError("die_2_rolls contain invalid faces")

        if not all(PAIR_SUM_MINIMUM <= value <= PAIR_SUM_MAXIMUM for value in self.sums):
            raise PairDiceSimulationError("sum sequence contains values outside 2 through 12")

        expected_sums = tuple(
            first + second
            for first, second in zip(
                self.die_1_rolls,
                self.die_2_rolls,
                strict=True,
            )
        )

        if expected_sums != self.sums:
            raise PairDiceSimulationError("sum sequence does not match physical die outcomes")

        if len(self.final_sum_counts) != PAIR_SUM_COUNT:
            raise PairDiceSimulationError("final_sum_counts must contain eleven values")

        if sum(self.final_sum_counts) != self.roll_count:
            raise PairDiceSimulationError("final_sum_counts must sum to roll_count")

        if count_pair_sums(self.sums) != self.final_sum_counts:
            raise PairDiceSimulationError("final_sum_counts do not match generated sums")

    def as_dict(self) -> dict[str, object]:
        """Return canonical JSON-compatible pair-case simulation data."""
        return {
            "case_id": self.case_id,
            "label": self.label,
            "seed": self.seed,
            "die_1_type": self.die_1_type,
            "die_2_type": self.die_2_type,
            "die_1_probabilities": list(self.die_1_probabilities),
            "die_2_probabilities": list(self.die_2_probabilities),
            "truth_loaded": self.truth_loaded,
            "roll_count": self.roll_count,
            "die_1_rolls": list(self.die_1_rolls),
            "die_2_rolls": list(self.die_2_rolls),
            "sums": list(self.sums),
            "final_sum_counts": {
                str(observed_sum): count
                for observed_sum, count in zip(
                    PAIR_SUM_VALUES,
                    self.final_sum_counts,
                    strict=True,
                )
            },
        }


@dataclass(frozen=True, slots=True)
class PairSimulationResult:
    """Complete deterministic six-case pair experiment."""

    project_id: str
    roll_count_per_case: int
    cases: Mapping[
        str,
        PairCaseSimulationResult,
    ]

    def __post_init__(self) -> None:
        if self.project_id != "p01_bayesian_dice":
            raise PairDiceSimulationError("project_id must equal 'p01_bayesian_dice'")

        if self.roll_count_per_case != 10_000:
            raise PairDiceSimulationError(
                "canonical pair experiment must use 10,000 rolls per case"
            )

        if set(self.cases) != set(PAIR_CASE_IDS):
            raise PairDiceSimulationError("pair simulation must contain all six canonical cases")

        if len(self.cases) != PAIR_CASE_COUNT:
            raise PairDiceSimulationError("pair simulation must contain exactly six cases")

        for case_id in PAIR_CASE_IDS:
            result = self.cases[case_id]

            if result.case_id != case_id:
                raise PairDiceSimulationError("pair-case mapping key does not match result case_id")

            if result.roll_count != self.roll_count_per_case:
                raise PairDiceSimulationError("all pair cases must use the canonical roll count")

    @property
    def total_observation_count(self) -> int:
        """Return total inference-facing observed sums."""
        return sum(result.roll_count for result in self.cases.values())

    def case(
        self,
        case_id: str,
    ) -> PairCaseSimulationResult:
        """Return one canonical simulated pair case."""
        try:
            return self.cases[case_id]
        except KeyError as exc:
            allowed = ", ".join(PAIR_CASE_IDS)

            raise PairDiceSimulationError(
                f"unknown pair simulation case {case_id!r}; allowed: {allowed}"
            ) from exc

    def as_dict(self) -> dict[str, object]:
        """Return canonical JSON-compatible six-case payload."""
        return {
            "project_id": self.project_id,
            "roll_count_per_case": self.roll_count_per_case,
            "total_observation_count": (self.total_observation_count),
            "case_order": list(PAIR_CASE_IDS),
            "cases": {case_id: self.cases[case_id].as_dict() for case_id in PAIR_CASE_IDS},
        }


def validate_pair_roll_count(
    roll_count: object,
) -> int:
    """Validate one pair-experiment roll count."""
    if isinstance(roll_count, bool) or not isinstance(
        roll_count,
        int,
    ):
        raise PairDiceSimulationError("pair roll_count must be an integer")

    if roll_count <= 0:
        raise PairDiceSimulationError("pair roll_count must be positive")

    return roll_count


def validate_pair_sums(
    sums: Sequence[object],
) -> tuple[int, ...]:
    """Validate inference-facing pair sums."""
    validated: list[int] = []

    for value in sums:
        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                int,
            )
            or not (PAIR_SUM_MINIMUM <= value <= PAIR_SUM_MAXIMUM)
        ):
            raise PairDiceSimulationError("pair sums must contain only integers from 2 through 12")

        validated.append(value)

    return tuple(validated)


def count_pair_sums(
    sums: Sequence[int],
) -> tuple[int, ...]:
    """Count observed sums 2 through 12."""
    counts = [0 for _ in range(PAIR_SUM_COUNT)]

    for observed_sum in sums:
        if not (PAIR_SUM_MINIMUM <= observed_sum <= PAIR_SUM_MAXIMUM):
            raise PairDiceSimulationError("observed pair sum must be between 2 and 12")

        counts[observed_sum - PAIR_SUM_MINIMUM] += 1

    return tuple(counts)


def cumulative_pair_sum_records(
    sums: Sequence[int],
) -> tuple[
    PairSumRecord,
    ...,
]:
    """Create cumulative sum-count history for one pair sequence."""
    validated = validate_pair_sums(sums)

    counts = [0 for _ in range(PAIR_SUM_COUNT)]

    records: list[PairSumRecord] = []

    for roll_index, observed_sum in enumerate(
        validated,
        start=1,
    ):
        counts[observed_sum - PAIR_SUM_MINIMUM] += 1

        records.append(
            PairSumRecord(
                roll_index=roll_index,
                observed_sum=observed_sum,
                cumulative_sum_counts=tuple(counts),
            )
        )

    return tuple(records)


def _generate_faces(
    probabilities: ProbabilityVector,
    *,
    roll_count: int,
    rng: np.random.Generator,
) -> tuple[int, ...]:
    """Generate one physical die's face sequence from a supplied RNG."""
    faces = np.arange(
        MIN_FACE,
        MAX_FACE + 1,
        dtype=np.int64,
    )

    generated = rng.choice(
        faces,
        size=roll_count,
        replace=True,
        p=np.asarray(
            probabilities.values,
            dtype=float,
        ),
    )

    return tuple(int(value) for value in generated.tolist())


def generate_pair_rolls(
    die_1_probabilities: ProbabilityVector,
    die_2_probabilities: ProbabilityVector,
    *,
    roll_count: int,
    seed: int,
) -> tuple[
    PairRoll,
    ...,
]:
    """Generate deterministic physical outcomes for one die pair."""
    validated_roll_count = validate_pair_roll_count(roll_count)

    if (
        isinstance(seed, bool)
        or not isinstance(
            seed,
            int,
        )
        or seed < 0
    ):
        raise PairDiceSimulationError("pair seed must be a non-negative integer")

    rng = create_rng(seed)

    die_1_rolls = _generate_faces(
        die_1_probabilities,
        roll_count=validated_roll_count,
        rng=rng,
    )

    die_2_rolls = _generate_faces(
        die_2_probabilities,
        roll_count=validated_roll_count,
        rng=rng,
    )

    return tuple(
        PairRoll(
            roll_index=roll_index,
            die_1_face=first,
            die_2_face=second,
            observed_sum=(first + second),
        )
        for roll_index, (
            first,
            second,
        ) in enumerate(
            zip(
                die_1_rolls,
                die_2_rolls,
                strict=True,
            ),
            start=1,
        )
    )


def simulate_pair_case(
    experiment: PairExperimentDefinition,
    case_id: str,
) -> PairCaseSimulationResult:
    """Simulate one canonical 10,000-roll pair case."""
    case = experiment.pair_case(case_id)

    die_1 = experiment.die_type(case.die_1_type)

    die_2 = experiment.die_type(case.die_2_type)

    rolls = generate_pair_rolls(
        die_1.probabilities,
        die_2.probabilities,
        roll_count=(experiment.roll_count_per_case),
        seed=case.seed,
    )

    die_1_rolls = tuple(roll.die_1_face for roll in rolls)

    die_2_rolls = tuple(roll.die_2_face for roll in rolls)

    sums = tuple(roll.observed_sum for roll in rolls)

    return PairCaseSimulationResult(
        case_id=case.case_id,
        label=case.label,
        seed=case.seed,
        die_1_type=case.die_1_type,
        die_2_type=case.die_2_type,
        die_1_probabilities=(die_1.probabilities.values),
        die_2_probabilities=(die_2.probabilities.values),
        truth_loaded=case.truth_loaded,
        roll_count=(experiment.roll_count_per_case),
        die_1_rolls=die_1_rolls,
        die_2_rolls=die_2_rolls,
        sums=sums,
        final_sum_counts=count_pair_sums(sums),
    )


def simulate_all_pair_cases(
    config: DiceProjectConfig,
) -> PairSimulationResult:
    """Simulate all six canonical pair cases deterministically."""
    experiment = config.pair_experiment

    cases = {
        case_id: simulate_pair_case(
            experiment,
            case_id,
        )
        for case_id in experiment.pair_order
    }

    return PairSimulationResult(
        project_id=config.project_id,
        roll_count_per_case=(experiment.roll_count_per_case),
        cases=cases,
    )


def pair_case_summary_line(
    result: PairCaseSimulationResult,
) -> str:
    """Return a compact human-readable simulation summary."""
    return (
        f"{result.case_id} | "
        f"{result.die_1_type}+{result.die_2_type} | "
        f"seed={result.seed} | "
        f"rolls={result.roll_count} | "
        f"sum2={result.final_sum_counts[0]} | "
        f"sum7={result.final_sum_counts[5]} | "
        f"sum12={result.final_sum_counts[10]}"
    )


def write_pair_simulation_json(
    result: PairSimulationResult,
    output_path: Path | str,
) -> Path:
    """Write the authoritative pair simulation atomically."""
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    temporary_path.write_text(
        json.dumps(
            result.as_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)

    return path


def validate_pair_simulation_payload(
    payload: Mapping[str, object],
) -> None:
    """Validate required top-level pair-simulation fields."""
    missing = [field for field in PAIR_SIMULATION_REQUIRED_FIELDS if field not in payload]

    if missing:
        raise PairDiceSimulationError(
            "pair simulation payload missing required fields: " + ", ".join(missing)
        )

    cases = payload["cases"]

    if not isinstance(
        cases,
        Mapping,
    ):
        raise PairDiceSimulationError("pair simulation cases must be a mapping")

    if set(cases) != set(PAIR_CASE_IDS):
        raise PairDiceSimulationError("pair simulation payload must contain all six cases")

    for case_id, raw_case in cases.items():
        if not isinstance(
            raw_case,
            Mapping,
        ):
            raise PairDiceSimulationError(f"pair simulation case {case_id} must be a mapping")

        missing_case_fields = [
            field for field in PAIR_CASE_SIMULATION_REQUIRED_FIELDS if field not in raw_case
        ]

        if missing_case_fields:
            raise PairDiceSimulationError(
                f"pair simulation case {case_id} missing fields: " + ", ".join(missing_case_fields)
            )


###############################################################################
# TEMPORARY LEGACY SINGLE-DIE SIMULATION COMPATIBILITY
#
# Revised Step 4 replaces inference.py and Revised Step 5 replaces metrics.py.
###############################################################################

ROLL_HISTORY_COLUMNS = (
    "roll_index",
    "observed_face",
    "count_1",
    "count_2",
    "count_3",
    "count_4",
    "count_5",
    "count_6",
)


class DiceSimulationError(DiceModelError):
    """Raised when legacy deterministic single-die simulation fails."""


@dataclass(frozen=True, slots=True)
class RollRecord:
    """One legacy sequential die observation."""

    roll_index: int
    observed_face: int
    cumulative_counts: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.roll_index <= 0:
            raise DiceSimulationError("roll_index must be positive")

        if not MIN_FACE <= self.observed_face <= MAX_FACE:
            raise DiceSimulationError("observed_face must be between 1 and 6")

        if len(self.cumulative_counts) != FACE_COUNT:
            raise DiceSimulationError("cumulative_counts must contain six values")

        if sum(self.cumulative_counts) != self.roll_index:
            raise DiceSimulationError("cumulative counts must sum to roll_index")

    def as_dict(self) -> dict[str, int]:
        """Return legacy CSV-compatible sequential record."""
        return {
            "roll_index": self.roll_index,
            "observed_face": self.observed_face,
            "count_1": self.cumulative_counts[0],
            "count_2": self.cumulative_counts[1],
            "count_3": self.cumulative_counts[2],
            "count_4": self.cumulative_counts[3],
            "count_5": self.cumulative_counts[4],
            "count_6": self.cumulative_counts[5],
        }


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Legacy deterministic single-die simulation result."""

    project_id: str
    scenario_id: str
    scenario_label: str
    seed: int
    roll_count: int
    true_probabilities: tuple[float, ...]
    rolls: tuple[int, ...]
    final_counts: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.project_id != "p01_bayesian_dice":
            raise DiceSimulationError("project_id must equal 'p01_bayesian_dice'")

        if not self.scenario_id.strip():
            raise DiceSimulationError("scenario_id must not be empty")

        if not self.scenario_label.strip():
            raise DiceSimulationError("scenario_label must not be empty")

        if self.roll_count <= 0:
            raise DiceSimulationError("roll_count must be positive")

        ProbabilityVector(self.true_probabilities)

        if len(self.rolls) != self.roll_count:
            raise DiceSimulationError("number of rolls must equal roll_count")

        if len(self.final_counts) != FACE_COUNT:
            raise DiceSimulationError("final_counts must contain six values")

        if sum(self.final_counts) != self.roll_count:
            raise DiceSimulationError("final_counts must sum to roll_count")

        if count_faces(self.rolls) != self.final_counts:
            raise DiceSimulationError("final_counts do not match generated rolls")

    def empirical_probabilities(self) -> tuple[float, ...]:
        """Return legacy empirical face probabilities."""
        return tuple(count / self.roll_count for count in self.final_counts)

    def as_dict(self) -> dict[str, object]:
        """Return legacy JSON-compatible simulation payload."""
        return {
            "project_id": self.project_id,
            "scenario_id": self.scenario_id,
            "scenario_label": self.scenario_label,
            "seed": self.seed,
            "roll_count": self.roll_count,
            "true_probabilities": list(self.true_probabilities),
            "rolls": list(self.rolls),
            "final_counts": list(self.final_counts),
            "summary": summarize_simulation(self),
        }


def validate_roll_count(
    roll_count: object,
) -> int:
    """Validate legacy single-die roll count."""
    if isinstance(roll_count, bool) or not isinstance(
        roll_count,
        int,
    ):
        raise DiceSimulationError("roll_count must be an integer")

    if roll_count <= 0:
        raise DiceSimulationError("roll_count must be positive")

    return roll_count


def validate_rolls(
    rolls: Sequence[object],
) -> tuple[int, ...]:
    """Validate legacy face observations."""
    validated: list[int] = []

    for value in rolls:
        if (
            isinstance(value, bool)
            or not isinstance(
                value,
                int,
            )
            or not MIN_FACE <= value <= MAX_FACE
        ):
            raise DiceSimulationError("rolls must contain only integers from 1 through 6")

        validated.append(value)

    return tuple(validated)


def count_faces(
    rolls: Sequence[int],
) -> tuple[int, ...]:
    """Count legacy face observations."""
    counts = [0] * FACE_COUNT

    for face in rolls:
        if not MIN_FACE <= face <= MAX_FACE:
            raise DiceSimulationError("face must be between 1 and 6")

        counts[face - 1] += 1

    return tuple(counts)


def generate_rolls(
    probabilities: ProbabilityVector,
    *,
    roll_count: int,
    seed: int,
) -> tuple[int, ...]:
    """Generate deterministic legacy single-die observations."""
    validated_roll_count = validate_roll_count(roll_count)

    if (
        isinstance(seed, bool)
        or not isinstance(
            seed,
            int,
        )
        or seed < 0
    ):
        raise DiceSimulationError("seed must be a non-negative integer")

    rng = create_rng(seed)

    faces = np.arange(
        MIN_FACE,
        MAX_FACE + 1,
        dtype=np.int64,
    )

    generated = rng.choice(
        faces,
        size=validated_roll_count,
        replace=True,
        p=np.asarray(
            probabilities.values,
            dtype=float,
        ),
    )

    return tuple(int(value) for value in generated.tolist())


def generate_fair_rolls(
    *,
    roll_count: int,
    seed: int,
) -> tuple[int, ...]:
    """Generate legacy fair-die observations."""
    probabilities = ProbabilityVector.from_sequence([1.0 / FACE_COUNT] * FACE_COUNT)

    return generate_rolls(
        probabilities,
        roll_count=roll_count,
        seed=seed,
    )


def generate_loaded_rolls(
    probabilities: ProbabilityVector,
    *,
    roll_count: int,
    seed: int,
) -> tuple[int, ...]:
    """Generate legacy loaded-die observations."""
    uniform = tuple([1.0 / FACE_COUNT] * FACE_COUNT)

    if all(
        math.isclose(
            actual,
            expected,
            rel_tol=0.0,
            abs_tol=1.0e-12,
        )
        for actual, expected in zip(
            probabilities.values,
            uniform,
            strict=True,
        )
    ):
        raise DiceSimulationError("loaded-die generator requires a non-uniform probability vector")

    return generate_rolls(
        probabilities,
        roll_count=roll_count,
        seed=seed,
    )


def cumulative_roll_records(
    rolls: Sequence[int],
) -> tuple[
    RollRecord,
    ...,
]:
    """Create legacy cumulative face-count records."""
    validated_rolls = validate_rolls(rolls)

    counts = [0] * FACE_COUNT

    records: list[RollRecord] = []

    for roll_index, face in enumerate(
        validated_rolls,
        start=1,
    ):
        counts[face - 1] += 1

        records.append(
            RollRecord(
                roll_index=roll_index,
                observed_face=face,
                cumulative_counts=tuple(counts),
            )
        )

    return tuple(records)


def simulate_scenario(
    config: DiceProjectConfig,
    scenario_id: str | None = None,
) -> SimulationResult:
    """Simulate one temporary legacy single-die scenario."""
    selected_id = config.showcase_scenario if scenario_id is None else scenario_id

    scenario = config.scenario(selected_id)

    rolls = generate_rolls(
        scenario.probabilities,
        roll_count=config.roll_count,
        seed=scenario.seed,
    )

    counts = count_faces(rolls)

    return SimulationResult(
        project_id=config.project_id,
        scenario_id=scenario.scenario_id,
        scenario_label=scenario.label,
        seed=scenario.seed,
        roll_count=config.roll_count,
        true_probabilities=(scenario.probabilities.as_tuple()),
        rolls=rolls,
        final_counts=counts,
    )


def summarize_simulation(
    result: SimulationResult,
) -> dict[str, object]:
    """Create legacy deterministic simulation summary."""
    empirical = result.empirical_probabilities()

    maximum_count = max(result.final_counts)

    most_observed_faces = [
        index
        for index, count in enumerate(
            result.final_counts,
            start=1,
        )
        if count == maximum_count
    ]

    return {
        "face_counts": {
            str(face): count
            for face, count in enumerate(
                result.final_counts,
                start=1,
            )
        },
        "empirical_probabilities": [float(value) for value in empirical],
        "most_observed_faces": (most_observed_faces),
        "maximum_face_count": (maximum_count),
    }


def write_simulation_json(
    result: SimulationResult,
    output_path: Path | str,
) -> Path:
    """Write legacy single-die simulation JSON."""
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    temporary_path.write_text(
        json.dumps(
            result.as_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)

    return path


def write_roll_history_csv(
    result: SimulationResult,
    output_path: Path | str,
) -> Path:
    """Write legacy sequential observations and face counts."""
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    records = cumulative_roll_records(result.rolls)

    with temporary_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(ROLL_HISTORY_COLUMNS),
        )

        writer.writeheader()

        for record in records:
            writer.writerow(record.as_dict())

    temporary_path.replace(path)

    return path


def simulation_summary_line(
    result: SimulationResult,
) -> str:
    """Return compact legacy simulation summary."""
    counts = ", ".join(
        f"{face}:{count}"
        for face, count in enumerate(
            result.final_counts,
            start=1,
        )
    )

    return (
        f"{result.scenario_id} | seed={result.seed} | rolls={result.roll_count} | counts=[{counts}]"
    )


def simulation_required_fields() -> tuple[str, ...]:
    """Return legacy simulation JSON required fields."""
    return (
        "project_id",
        "scenario_id",
        "scenario_label",
        "seed",
        "roll_count",
        "true_probabilities",
        "rolls",
        "final_counts",
    )


def validate_simulation_payload(
    payload: Mapping[str, object],
) -> None:
    """Validate required fields in legacy simulation payload."""
    missing = [field for field in simulation_required_fields() if field not in payload]

    if missing:
        raise DiceSimulationError(
            "simulation payload missing required fields: " + ", ".join(missing)
        )
