"""Load and validate the frozen Project 7 configuration."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from .models import ProjectConfig, SplitConfig

PACKAGE_ID = "p27_prediction_time_integrity_auditor"
EXPECTED_SEED = 1729
EXPECTED_DATASET_ID = 222


def repository_root() -> Path:
    """Resolve the repository root from this source file."""

    current = Path(__file__).resolve()

    for parent in current.parents:
        if (parent / "pyproject.toml").is_file():
            return parent

    raise RuntimeError("Unable to locate repository root from Project 7 package.")


def default_config_path() -> Path:
    """Return the frozen Project 7 config path."""

    return repository_root() / "configs" / f"{PACKAGE_ID}.yaml"


def _mapping(
    value: object,
    *,
    name: str,
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be an object.")

    return cast(
        Mapping[str, object],
        value,
    )


def _string(
    mapping: Mapping[str, object],
    key: str,
) -> str:
    value = mapping.get(key)

    if not isinstance(value, str) or not value:
        raise TypeError(f"{key} must be a non-empty string.")

    return value


def _integer(
    mapping: Mapping[str, object],
    key: str,
) -> int:
    value = mapping.get(key)

    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{key} must be an integer.")

    return value


def _boolean(
    mapping: Mapping[str, object],
    key: str,
) -> bool:
    value = mapping.get(key)

    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a boolean.")

    return value


def _number(
    mapping: Mapping[str, object],
    key: str,
) -> float:
    value = mapping.get(key)

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{key} must be numeric.")

    return float(value)


def load_config(
    path: Path | None = None,
) -> ProjectConfig:
    """Load the JSON-form YAML 1.2 Project 7 configuration."""

    selected = default_config_path() if path is None else path

    raw_object = cast(
        object,
        json.loads(selected.read_text(encoding="utf-8")),
    )

    root = _mapping(
        raw_object,
        name="config",
    )

    project = _mapping(
        root.get("project"),
        name="project",
    )

    data = _mapping(
        root.get("data"),
        name="data",
    )

    splits = _mapping(
        root.get("splits"),
        name="splits",
    )

    chronological = _mapping(
        splits.get("chronological"),
        name="splits.chronological",
    )

    random_comparison = _mapping(
        splits.get("random_comparison"),
        name="splits.random_comparison",
    )

    split_config = SplitConfig(
        train=_number(
            chronological,
            "train",
        ),
        validation=_number(
            chronological,
            "validation",
        ),
        test=_number(
            chronological,
            "test",
        ),
    )

    split_config.validate()

    config = ProjectConfig(
        project_id=_string(
            project,
            "id",
        ),
        seed=_integer(
            project,
            "seed",
        ),
        contract_version=_string(
            project,
            "contract_version",
        ),
        dataset_id=_integer(
            data,
            "dataset_id",
        ),
        preferred_file=_string(
            data,
            "preferred_file",
        ),
        target=_string(
            data,
            "target",
        ),
        preserve_source_order=_boolean(
            data,
            "preserve_source_order",
        ),
        chronological_split=split_config,
        random_seed=_integer(
            random_comparison,
            "seed",
        ),
        random_stratify=_boolean(
            random_comparison,
            "stratify",
        ),
    )

    if config.project_id != PACKAGE_ID:
        raise ValueError(f"Unexpected project id: {config.project_id}")

    if config.seed != EXPECTED_SEED:
        raise ValueError(f"Unexpected project seed: {config.seed}")

    if config.random_seed != EXPECTED_SEED:
        raise ValueError(f"Unexpected random split seed: {config.random_seed}")

    if config.dataset_id != EXPECTED_DATASET_ID:
        raise ValueError(f"Unexpected dataset id: {config.dataset_id}")

    if not config.preserve_source_order:
        raise ValueError("Project 7 must preserve source order.")

    return config
