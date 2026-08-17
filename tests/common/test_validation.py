"""Tests for shared validation helpers."""

from __future__ import annotations

import pytest

from linkedin_visual_labs.common.validation import (
    ValidationError,
    ensure_json_serializable,
    require_keys,
    require_positive_int,
    require_probability,
    validate_project_id,
)


def test_validate_project_id_accepts_catalog_ids() -> None:
    assert validate_project_id("p01_bayesian_dice") == "p01_bayesian_dice"
    assert validate_project_id("p04_zombie_escape") == "p04_zombie_escape"
    assert validate_project_id("p02_monopoly_ai") == "p02_monopoly_ai"


@pytest.mark.parametrize(
    "project_id",
    [
        "",
        "P01_bayesian_dice",
        "p1_bayesian_dice",
        "p01-Bayesian",
        "../p01_bayesian_dice",
        "p01_bayesian dice",
    ],
)
def test_validate_project_id_rejects_invalid_values(
    project_id: str,
) -> None:
    with pytest.raises(ValidationError):
        validate_project_id(project_id)


def test_require_keys_reports_missing_keys() -> None:
    with pytest.raises(
        ValidationError,
        match="missing required keys: seed",
    ):
        require_keys(
            {"project_id": "p01_bayesian_dice"},
            ["project_id", "seed"],
            name="config",
        )


def test_require_positive_int_rejects_zero() -> None:
    with pytest.raises(ValidationError):
        require_positive_int(0, name="rolls")


def test_require_probability_validates_bounds() -> None:
    assert require_probability(0.0, name="probability") == 0.0
    assert require_probability(1.0, name="probability") == 1.0

    with pytest.raises(ValidationError):
        require_probability(1.01, name="probability")


def test_ensure_json_serializable_rejects_set() -> None:
    with pytest.raises(ValidationError):
        ensure_json_serializable(
            {"bad": {1, 2, 3}},
            name="manifest",
        )
