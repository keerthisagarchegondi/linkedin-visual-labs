"""Typed Project 7 scaffold models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AvailabilityClass(StrEnum):
    """Prediction-time feature availability classes."""

    PRE_DECISION = "PRE_DECISION"
    KNOWN_AT_DECISION = "KNOWN_AT_DECISION"
    DURING_ACTION = "DURING_ACTION"
    POST_OUTCOME = "POST_OUTCOME"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class SplitConfig:
    """Frozen split proportions."""

    train: float
    validation: float
    test: float

    def validate(self) -> None:
        """Validate split proportions."""

        values = (
            self.train,
            self.validation,
            self.test,
        )

        if any(value <= 0.0 for value in values):
            raise ValueError("All split proportions must be positive.")

        if abs(sum(values) - 1.0) > 1e-12:
            raise ValueError("Split proportions must sum to 1.0.")


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Minimal frozen Project 7 configuration."""

    project_id: str
    seed: int
    contract_version: str
    dataset_id: int
    preferred_file: str
    target: str
    preserve_source_order: bool
    chronological_split: SplitConfig
    random_seed: int
    random_stratify: bool
