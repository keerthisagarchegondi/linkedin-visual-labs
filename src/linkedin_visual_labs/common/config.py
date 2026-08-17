"""Shared YAML configuration loading."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml

from linkedin_visual_labs.common.validation import (
    ValidationError,
    require_keys,
    require_mapping,
)


class ConfigurationError(ValidationError):
    """Raised when configuration loading or validation fails."""


def _normalize_mapping(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Copy a string-keyed mapping into an ordinary dictionary."""
    return dict(value)


def load_yaml_config(
    path: Path | str,
    *,
    required_keys: Sequence[str] = (),
) -> dict[str, Any]:
    """Load and validate a YAML configuration file."""
    config_path = Path(path)

    if not config_path.is_file():
        raise ConfigurationError(f"configuration file does not exist: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML configuration: {config_path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"could not read configuration: {config_path}") from exc

    if raw is None:
        raw = {}

    try:
        mapping = require_mapping(
            raw,
            name=f"configuration {config_path}",
        )
        require_keys(
            mapping,
            required_keys,
            name=f"configuration {config_path}",
        )
    except ValidationError as exc:
        raise ConfigurationError(str(exc)) from exc

    return _normalize_mapping(mapping)
