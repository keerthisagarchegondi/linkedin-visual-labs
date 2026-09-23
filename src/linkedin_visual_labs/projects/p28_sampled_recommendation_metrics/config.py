"""Typed Project 8 configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _require_plain_int(
    value: object,
    *,
    name: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain integer")

    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")

    return value


@dataclass(frozen=True)
class Project8Config:
    n_items: int
    reference_negative_draws: int
    source_protocol_repetitions: int
    validation_repetitions: int
    root_seed: int
    sensitivity_grid_negative_draws: tuple[int, ...]

    def __post_init__(self) -> None:
        n_items = _require_plain_int(
            self.n_items,
            name="n_items",
            minimum=2,
        )

        m = _require_plain_int(
            self.reference_negative_draws,
            name="reference_negative_draws",
            minimum=1,
        )

        _require_plain_int(
            self.source_protocol_repetitions,
            name="source_protocol_repetitions",
            minimum=1,
        )

        _require_plain_int(
            self.validation_repetitions,
            name="validation_repetitions",
            minimum=1,
        )

        _require_plain_int(
            self.root_seed,
            name="root_seed",
            minimum=0,
        )

        if not self.sensitivity_grid_negative_draws:
            raise ValueError("sensitivity grid cannot be empty")

        previous = 0

        for value in self.sensitivity_grid_negative_draws:
            current = _require_plain_int(
                value,
                name="sensitivity grid value",
                minimum=1,
            )

            if current <= previous:
                raise ValueError("sensitivity grid must be strictly increasing")

            previous = current

        if m >= n_items:
            raise ValueError("reference negative draws must be < n_items")

    @classmethod
    def from_mapping(
        cls,
        value: dict[str, Any],
    ) -> Project8Config:
        required = {
            "n_items",
            "reference_negative_draws",
            "source_protocol_repetitions",
            "validation_repetitions",
            "root_seed",
            "sensitivity_grid_negative_draws",
        }

        unknown = set(value) - required
        missing = required - set(value)

        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")

        if missing:
            raise ValueError(f"missing config keys: {sorted(missing)}")

        grid = value["sensitivity_grid_negative_draws"]

        if not isinstance(grid, list):
            raise TypeError("sensitivity_grid_negative_draws must be a list")

        return cls(
            n_items=value["n_items"],
            reference_negative_draws=(value["reference_negative_draws"]),
            source_protocol_repetitions=(value["source_protocol_repetitions"]),
            validation_repetitions=(value["validation_repetitions"]),
            root_seed=value["root_seed"],
            sensitivity_grid_negative_draws=tuple(grid),
        )


def default_config_path() -> Path:
    return (
        Path(__file__).resolve().parents[4] / "configs" / "p28_sampled_recommendation_metrics.yaml"
    )


def load_config(path: Path) -> Project8Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise TypeError("Project 8 config must decode to a mapping")

    return Project8Config.from_mapping(raw)


def load_default_config() -> Project8Config:
    return load_config(default_config_path())
