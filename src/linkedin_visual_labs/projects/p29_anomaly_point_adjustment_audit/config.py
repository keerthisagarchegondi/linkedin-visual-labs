"""Typed, frozen Project 9 configuration and deterministic stream keys."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

PROJECT_ID = "p29_anomaly_point_adjustment_audit"
CONFIG_RESOURCE_NAME = f"{PROJECT_ID}.yaml"
UINT32_MAX = 2**32 - 1


def _plain_int(value: object, *, name: str, minimum: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain integer")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _probability(value: object, *, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be in [0, 1]")
    return result


@dataclass(frozen=True, slots=True)
class Project9Config:
    """Validated canonical design for Project 9; no simulation occurs here."""

    project_id: str
    experiment_version: int
    n_timestamps: int
    anomalous_timestamps: int
    prevalence: float
    event_lengths: tuple[int, ...]
    alert_probabilities: tuple[float, ...]
    primary_event_length: int
    primary_alert_probability: float
    initial_repetitions: int
    seed_namespace: str
    output_roots: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.project_id != PROJECT_ID:
            raise ValueError(f"project_id must be {PROJECT_ID!r}")
        _plain_int(self.experiment_version, name="experiment_version", minimum=1)
        n_timestamps = _plain_int(self.n_timestamps, name="n_timestamps", minimum=1)
        anomalous = _plain_int(self.anomalous_timestamps, name="anomalous_timestamps", minimum=1)
        if anomalous >= n_timestamps:
            raise ValueError("anomalous_timestamps must be < n_timestamps")
        prevalence = _probability(self.prevalence, name="prevalence")
        if abs(prevalence - anomalous / n_timestamps) > 1e-12:
            raise ValueError("prevalence must equal anomalous_timestamps / n_timestamps")
        if (
            not self.event_lengths
            or tuple(sorted(self.event_lengths)) != self.event_lengths
            or len(set(self.event_lengths)) != len(self.event_lengths)
        ):
            raise ValueError("event_lengths must be non-empty, sorted, and unique")
        for length in self.event_lengths:
            _plain_int(length, name="event length", minimum=1)
            if anomalous % length != 0:
                raise ValueError("every event length must divide anomalous_timestamps")
        if (
            not self.alert_probabilities
            or tuple(sorted(self.alert_probabilities)) != self.alert_probabilities
            or len(set(self.alert_probabilities)) != len(self.alert_probabilities)
        ):
            raise ValueError("alert_probabilities must be non-empty, sorted, and unique")
        for probability in self.alert_probabilities:
            _probability(probability, name="alert probability")
        if self.primary_event_length not in self.event_lengths:
            raise ValueError("primary_event_length must be in event_lengths")
        if self.primary_alert_probability not in self.alert_probabilities:
            raise ValueError("primary_alert_probability must be in alert_probabilities")
        _plain_int(self.initial_repetitions, name="initial_repetitions", minimum=1)
        if not self.seed_namespace or not self.output_roots:
            raise ValueError("seed_namespace and output_roots cannot be empty")

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> Project9Config:
        required = {
            "project_id",
            "experiment_version",
            "n_timestamps",
            "anomalous_timestamps",
            "prevalence",
            "event_lengths",
            "alert_probabilities",
            "primary_event_length",
            "primary_alert_probability",
            "initial_repetitions",
            "seed_namespace",
            "output_roots",
        }
        unknown, missing = set(value) - required, required - set(value)
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        if missing:
            raise ValueError(f"missing config keys: {sorted(missing)}")
        lengths, probabilities, roots = (
            value["event_lengths"],
            value["alert_probabilities"],
            value["output_roots"],
        )
        if (
            not isinstance(lengths, list)
            or not isinstance(probabilities, list)
            or not isinstance(roots, list)
            or not all(isinstance(root, str) for root in roots)
        ):
            raise TypeError("grids and output_roots must be lists of the required type")
        return cls(
            value["project_id"],
            value["experiment_version"],
            value["n_timestamps"],
            value["anomalous_timestamps"],
            value["prevalence"],
            tuple(lengths),
            tuple(float(x) for x in probabilities),
            value["primary_event_length"],
            float(value["primary_alert_probability"]),
            value["initial_repetitions"],
            value["seed_namespace"],
            tuple(roots),
        )


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


def default_config_path() -> Path:
    """Return the canonical repository config path for development workflows."""
    return repository_root() / "configs" / f"{PROJECT_ID}.yaml"


def load_config(path: Path) -> Project9Config:
    return _load_config_text(path.read_text(encoding="utf-8"))


def _load_config_text(text: str) -> Project9Config:
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise TypeError("Project 9 config must decode to a mapping")
    return Project9Config.from_mapping(raw)


def default_config_source() -> str:
    """Identify the stable source class used by :func:`load_default_config`."""
    return "REPOSITORY_CONFIG" if default_config_path().is_file() else "PACKAGE_RESOURCE"


def load_default_config() -> Project9Config:
    path = default_config_path()
    if path.is_file():
        return load_config(path)
    resource = resources.files(__package__).joinpath("resources", CONFIG_RESOURCE_NAME)
    return _load_config_text(resource.read_text(encoding="utf-8"))


def derive_seed(config: Project9Config, purpose: str, **identifiers: object) -> int:
    """Derive a restart-independent uint32 seed from canonical semantic identifiers."""
    if purpose not in {
        "semantic_fixture",
        "condition_simulation",
        "presentation",
        "runtime_pilot",
        "timeline_validation",
        "semantic_reference",
    }:
        raise ValueError("unsupported seed purpose")
    payload = {"namespace": config.seed_namespace, "purpose": purpose, "identifiers": identifiers}
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).digest()
    return int.from_bytes(digest[:4], byteorder="big") & UINT32_MAX
