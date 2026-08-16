"""Shared validation utilities for LinkedIn Visual Labs."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

PROJECT_ID_PATTERN = re.compile(r"^p\d{2}_[a-z0-9]+(?:_[a-z0-9]+)*$")


class ValidationError(ValueError):
    """Raised when shared project validation fails."""


def validate_project_id(project_id: str) -> str:
    """Validate and return a canonical repository project identifier."""
    if not isinstance(project_id, str):
        raise ValidationError("project_id must be a string")

    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise ValidationError(
            "project_id must match 'pNN_lowercase_words', for example 'p01_bayesian_dice'"
        )

    return project_id


def require_mapping(
    value: object,
    *,
    name: str,
) -> Mapping[str, Any]:
    """Require a mapping with string keys."""
    if not isinstance(value, Mapping):
        raise ValidationError(f"{name} must be a mapping")

    invalid_keys = [key for key in value if not isinstance(key, str)]

    if invalid_keys:
        raise ValidationError(f"{name} must contain only string keys")

    return value


def require_keys(
    mapping: Mapping[str, Any],
    required_keys: Sequence[str],
    *,
    name: str,
) -> None:
    """Require keys to exist in a mapping."""
    missing = [key for key in required_keys if key not in mapping]

    if missing:
        joined = ", ".join(sorted(missing))
        raise ValidationError(f"{name} is missing required keys: {joined}")


def require_non_empty_string(
    value: object,
    *,
    name: str,
) -> str:
    """Require a non-empty string."""
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")

    normalized = value.strip()

    if not normalized:
        raise ValidationError(f"{name} must not be empty")

    return normalized


def require_non_negative_int(
    value: object,
    *,
    name: str,
) -> int:
    """Require a non-negative integer while rejecting booleans."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer")

    if value < 0:
        raise ValidationError(f"{name} must be non-negative")

    return value


def require_positive_int(
    value: object,
    *,
    name: str,
) -> int:
    """Require a strictly positive integer while rejecting booleans."""
    result = require_non_negative_int(
        value,
        name=name,
    )

    if result == 0:
        raise ValidationError(f"{name} must be greater than zero")

    return result


def require_probability(
    value: object,
    *,
    name: str,
) -> float:
    """Require a probability in the inclusive interval [0, 1]."""
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ValidationError(f"{name} must be numeric")

    result = float(value)

    if not 0.0 <= result <= 1.0:
        raise ValidationError(f"{name} must be between 0 and 1 inclusive")

    return result


def ensure_json_serializable[T](
    value: T,
    *,
    name: str = "value",
) -> T:
    """Require a value to be serializable by the standard JSON encoder."""
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must be JSON serializable") from exc

    return value
