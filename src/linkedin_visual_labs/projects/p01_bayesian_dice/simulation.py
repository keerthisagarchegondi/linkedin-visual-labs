"""Deterministic simulation engine for Bayesian Dice Detective."""

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
    DiceModelError,
    DiceProjectConfig,
    ProbabilityVector,
)

MIN_FACE = 1
MAX_FACE = FACE_COUNT

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
    """Raised when deterministic die simulation fails."""


@dataclass(frozen=True, slots=True)
class RollRecord:
    """One sequential die observation with cumulative face counts."""

    roll_index: int
    observed_face: int
    cumulative_counts: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.roll_index <= 0:
            raise DiceSimulationError("roll_index must be positive")

        if not MIN_FACE <= self.observed_face <= MAX_FACE:
            raise DiceSimulationError(f"observed_face must be between {MIN_FACE} and {MAX_FACE}")

        if len(self.cumulative_counts) != FACE_COUNT:
            raise DiceSimulationError(f"cumulative_counts must contain {FACE_COUNT} values")

        if not all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in self.cumulative_counts
        ):
            raise DiceSimulationError("cumulative counts must be non-negative integers")

        if sum(self.cumulative_counts) != self.roll_index:
            raise DiceSimulationError("cumulative counts must sum to roll_index")

    def as_dict(self) -> dict[str, int]:
        """Return one CSV/JSON-compatible sequential record."""
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
    """Complete deterministic roll sequence and generating metadata."""

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

        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise DiceSimulationError("seed must be a non-negative integer")

        if self.roll_count <= 0:
            raise DiceSimulationError("roll_count must be positive")

        ProbabilityVector(self.true_probabilities)

        if len(self.rolls) != self.roll_count:
            raise DiceSimulationError("number of rolls must equal roll_count")

        if not all(
            isinstance(face, int) and not isinstance(face, bool) and MIN_FACE <= face <= MAX_FACE
            for face in self.rolls
        ):
            raise DiceSimulationError("all rolls must be integers from 1 through 6")

        if len(self.final_counts) != FACE_COUNT:
            raise DiceSimulationError(f"final_counts must contain {FACE_COUNT} values")

        if not all(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0
            for value in self.final_counts
        ):
            raise DiceSimulationError("final counts must be non-negative integers")

        if sum(self.final_counts) != self.roll_count:
            raise DiceSimulationError("final counts must sum to roll_count")

        recomputed = count_faces(self.rolls)

        if recomputed != self.final_counts:
            raise DiceSimulationError("final_counts do not match generated rolls")

    def empirical_probabilities(self) -> tuple[float, ...]:
        """Return observed relative frequency for each face."""
        return tuple(count / self.roll_count for count in self.final_counts)

    def as_dict(self) -> dict[str, object]:
        """Return the canonical machine-readable simulation payload."""
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
    """Validate and return a positive simulation roll count."""
    if isinstance(roll_count, bool) or not isinstance(roll_count, int):
        raise DiceSimulationError("roll_count must be an integer")

    if roll_count <= 0:
        raise DiceSimulationError("roll_count must be positive")

    return roll_count


def validate_rolls(
    rolls: Sequence[object],
) -> tuple[int, ...]:
    """Validate an externally supplied roll sequence."""
    validated: list[int] = []

    for value in rolls:
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not MIN_FACE <= value <= MAX_FACE
        ):
            raise DiceSimulationError("rolls must contain only integers from 1 through 6")

        validated.append(value)

    return tuple(validated)


def count_faces(
    rolls: Sequence[int],
) -> tuple[int, ...]:
    """Count observations of faces 1 through 6."""
    counts = [0] * FACE_COUNT

    for face in rolls:
        if not MIN_FACE <= face <= MAX_FACE:
            raise DiceSimulationError(f"face must be between {MIN_FACE} and {MAX_FACE}")

        counts[face - 1] += 1

    return tuple(counts)


def generate_rolls(
    probabilities: ProbabilityVector,
    *,
    roll_count: int,
    seed: int,
) -> tuple[int, ...]:
    """Generate a deterministic sequence of die observations."""
    validated_roll_count = validate_roll_count(roll_count)

    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
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
    """Generate rolls from an exactly fair six-sided die."""
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
    """Generate rolls from a configured loaded die."""
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
) -> tuple[RollRecord, ...]:
    """Create cumulative-count records after every observed roll."""
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
    """Simulate one configured deterministic Project 1 scenario."""
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
    """Create a deterministic, JSON-compatible simulation summary."""
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
        "maximum_face_count": maximum_count,
    }


def write_simulation_json(
    result: SimulationResult,
    output_path: Path | str,
) -> Path:
    """Write the canonical simulation result atomically as JSON."""
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
    """Write sequential observations and cumulative counts as CSV."""
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
    """Return a compact human-readable simulation summary."""
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
    """Return the Step 1 simulation JSON schema's required fields."""
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
    """Validate required fields in a serialized simulation payload."""
    missing = [field for field in simulation_required_fields() if field not in payload]

    if missing:
        raise DiceSimulationError(
            "simulation payload missing required fields: " + ", ".join(missing)
        )
