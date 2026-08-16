"""Deterministic random-state helpers."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass

import numpy as np
from numpy.random import Generator

from linkedin_visual_labs.common.validation import (
    ValidationError,
    require_non_negative_int,
)

MAX_SEED = (2**63) - 1


@dataclass(frozen=True, slots=True)
class SeedRecord:
    """Machine-readable random-seed metadata."""

    seed: int
    namespace: str | None = None

    def as_manifest_dict(self) -> dict[str, int | str | None]:
        """Return seed metadata suitable for inclusion in a manifest."""
        return asdict(self)


def normalize_seed(seed: object) -> int:
    """Validate a deterministic NumPy-compatible project seed."""
    result = require_non_negative_int(seed, name="seed")

    if result > MAX_SEED:
        raise ValidationError(f"seed must be less than or equal to {MAX_SEED}")

    return result


def create_rng(seed: object) -> Generator:
    """Create a deterministic NumPy random-number generator."""
    return np.random.default_rng(normalize_seed(seed))


def derive_seed(
    master_seed: object,
    namespace: str,
) -> int:
    """Derive a deterministic child seed from a master seed and namespace."""
    normalized_master_seed = normalize_seed(master_seed)

    if not isinstance(namespace, str) or not namespace.strip():
        raise ValidationError("namespace must be a non-empty string")

    payload = f"{normalized_master_seed}:{namespace}".encode()

    digest = hashlib.blake2b(
        payload,
        digest_size=8,
        person=b"LVL-SEED",
    ).digest()

    derived = int.from_bytes(
        digest,
        byteorder="big",
        signed=False,
    )

    return derived % (MAX_SEED + 1)


def create_namespaced_rng(
    master_seed: object,
    namespace: str,
) -> Generator:
    """Create a deterministic RNG derived from a master seed."""
    return create_rng(
        derive_seed(
            master_seed,
            namespace,
        )
    )


def seed_manifest_entry(
    seed: object,
    *,
    namespace: str | None = None,
) -> dict[str, int | str | None]:
    """Create JSON-compatible seed metadata for output manifests."""
    normalized_seed = normalize_seed(seed)

    if namespace is not None and (not isinstance(namespace, str) or not namespace.strip()):
        raise ValidationError("namespace must be a non-empty string when provided")

    return SeedRecord(
        seed=normalized_seed,
        namespace=namespace,
    ).as_manifest_dict()
