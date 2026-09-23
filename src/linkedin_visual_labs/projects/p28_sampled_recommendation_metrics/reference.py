"""Verified source-defined Project 8 inputs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import Project8Config, load_default_config


def _require_plain_rank(
    value: object,
    *,
    n_items: int,
) -> int:
    if type(value) is not int:
        raise TypeError("rank values must be plain integers")

    if not 1 <= value <= n_items:
        raise ValueError(f"rank must be in [1, {n_items}]")

    return value


@dataclass(frozen=True)
class ReferenceProtocol:
    n_items: int
    reference_negative_draws: int
    profiles: dict[str, tuple[int, ...]]

    def __post_init__(self) -> None:
        if type(self.n_items) is not int or self.n_items < 2:
            raise ValueError("n_items must be an integer >= 2")

        if type(self.reference_negative_draws) is not int or self.reference_negative_draws < 1:
            raise ValueError("reference_negative_draws must be an integer >= 1")

        if self.reference_negative_draws >= self.n_items:
            raise ValueError("reference_negative_draws must be < n_items")

        if set(self.profiles) != {"A", "B", "C"}:
            raise ValueError("profiles must be exactly A, B, and C")

        for label, ranks in self.profiles.items():
            if len(ranks) != 5:
                raise ValueError(f"profile {label} must contain exactly 5 ranks")

            for rank in ranks:
                _require_plain_rank(
                    rank,
                    n_items=self.n_items,
                )


def reference_ranks_path() -> Path:
    return (
        Path(__file__).resolve().parents[4]
        / "assets"
        / "p28_sampled_recommendation_metrics"
        / "reference_ranks.json"
    )


def load_reference_protocol(
    *,
    config: Project8Config | None = None,
) -> ReferenceProtocol:
    if config is None:
        config = load_default_config()

    raw: Any = json.loads(reference_ranks_path().read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise TypeError("reference rank asset must be a mapping")

    allowed = {
        "n_items",
        "reference_negative_draws",
        "profiles",
    }

    unknown = set(raw) - allowed
    missing = allowed - set(raw)

    if unknown:
        raise ValueError(f"unknown reference keys: {sorted(unknown)}")

    if missing:
        raise ValueError(f"missing reference keys: {sorted(missing)}")

    profile_raw = raw["profiles"]

    if not isinstance(profile_raw, dict):
        raise TypeError("profiles must be a mapping")

    profiles: dict[str, tuple[int, ...]] = {}

    for label, ranks in profile_raw.items():
        if not isinstance(label, str):
            raise TypeError("profile labels must be strings")

        if not isinstance(ranks, list):
            raise TypeError(f"profile {label} ranks must be a list")

        profiles[label] = tuple(ranks)

    protocol = ReferenceProtocol(
        n_items=raw["n_items"],
        reference_negative_draws=raw["reference_negative_draws"],
        profiles=profiles,
    )

    if protocol.n_items != config.n_items:
        raise ValueError("reference n_items disagrees with config")

    if protocol.reference_negative_draws != config.reference_negative_draws:
        raise ValueError("reference negative draws disagree with config")

    return protocol
