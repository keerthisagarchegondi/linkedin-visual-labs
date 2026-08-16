"""Tests for deterministic random-state helpers."""

from __future__ import annotations

import numpy as np
import pytest

from linkedin_visual_labs.common.random_state import (
    MAX_SEED,
    create_namespaced_rng,
    create_rng,
    derive_seed,
    normalize_seed,
    seed_manifest_entry,
)
from linkedin_visual_labs.common.validation import ValidationError


def test_same_seed_produces_same_random_sequence() -> None:
    first = create_rng(12345).integers(
        1,
        7,
        size=100,
    )
    second = create_rng(12345).integers(
        1,
        7,
        size=100,
    )

    assert np.array_equal(first, second)


def test_different_seeds_produce_different_sequences() -> None:
    first = create_rng(12345).integers(
        1,
        7,
        size=100,
    )
    second = create_rng(54321).integers(
        1,
        7,
        size=100,
    )

    assert not np.array_equal(first, second)


def test_derived_seed_is_deterministic() -> None:
    first = derive_seed(100, "simulation")
    second = derive_seed(100, "simulation")

    assert first == second
    assert 0 <= first <= MAX_SEED


def test_namespaces_produce_different_child_seeds() -> None:
    simulation = derive_seed(100, "simulation")
    validation = derive_seed(100, "validation")

    assert simulation != validation


def test_namespaced_rng_is_deterministic() -> None:
    first = create_namespaced_rng(
        20260816,
        "p01_bayesian_dice",
    ).random(10)

    second = create_namespaced_rng(
        20260816,
        "p01_bayesian_dice",
    ).random(10)

    assert np.array_equal(first, second)


def test_seed_manifest_entry_is_machine_readable() -> None:
    assert seed_manifest_entry(
        42,
        namespace="simulation",
    ) == {
        "seed": 42,
        "namespace": "simulation",
    }


@pytest.mark.parametrize(
    "seed",
    [
        -1,
        MAX_SEED + 1,
        True,
        1.5,
        "123",
    ],
)
def test_normalize_seed_rejects_invalid_values(
    seed: object,
) -> None:
    with pytest.raises(ValidationError):
        normalize_seed(seed)
