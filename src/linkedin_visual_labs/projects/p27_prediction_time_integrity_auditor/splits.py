"""Deterministic split integrity utilities for Project 7."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass

from sklearn.model_selection import train_test_split

from .data import LoadedDataset


@dataclass(frozen=True, slots=True)
class SplitIndices:
    """One deterministic train/validation/test split."""

    train: tuple[int, ...]
    validation: tuple[int, ...]
    test: tuple[int, ...]

    def all_indices(self) -> tuple[int, ...]:
        return self.train + self.validation + self.test


def chronological_split(
    row_count: int,
    *,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> SplitIndices:
    """Split source order without shuffling."""

    if row_count < 3:
        raise ValueError("At least three rows are required.")

    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be in (0, 1).")

    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be in (0, 1).")

    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train + validation fractions must be < 1.")

    train_end = int(row_count * train_fraction)

    validation_count = int(row_count * validation_fraction)

    validation_end = train_end + validation_count

    train = tuple(range(0, train_end))

    validation = tuple(range(train_end, validation_end))

    test = tuple(range(validation_end, row_count))

    if not train or not validation or not test:
        raise ValueError("Chronological split produced an empty partition.")

    return SplitIndices(
        train=train,
        validation=validation,
        test=test,
    )


def random_comparison_split(
    targets: Sequence[int],
    *,
    seed: int = 1729,
) -> SplitIndices:
    """Create deterministic stratified 70/15/15 comparison split."""

    indices = list(range(len(targets)))

    train, remainder = train_test_split(
        indices,
        test_size=0.30,
        random_state=seed,
        stratify=list(targets),
    )

    remainder_targets = [targets[index] for index in remainder]

    validation, test = train_test_split(
        remainder,
        test_size=0.50,
        random_state=seed,
        stratify=remainder_targets,
    )

    return SplitIndices(
        train=tuple(sorted(train)),
        validation=tuple(sorted(validation)),
        test=tuple(sorted(test)),
    )


def row_fingerprint(
    row: dict[str, str],
) -> str:
    """Stable SHA-256 over one canonical source row."""

    payload = json.dumps(
        row,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def dataset_fingerprints(
    dataset: LoadedDataset,
) -> tuple[str, ...]:
    """Fingerprint every source row in preserved order."""

    return tuple(row_fingerprint(row) for row in dataset.rows)


def overlap_counts(
    fingerprints: Sequence[str],
    split: SplitIndices,
) -> dict[str, int]:
    """Calculate independent exact-row overlap counts."""

    train = {fingerprints[index] for index in split.train}

    validation = {fingerprints[index] for index in split.validation}

    test = {fingerprints[index] for index in split.test}

    return {
        "train_validation": len(train & validation),
        "train_test": len(train & test),
        "validation_test": len(validation & test),
    }


def validate_partition_integrity(
    row_count: int,
    split: SplitIndices,
) -> None:
    """Ensure each source row belongs to exactly one partition."""

    combined = split.all_indices()

    if len(combined) != row_count:
        raise ValueError("Split does not contain every source row.")

    if len(set(combined)) != row_count:
        raise ValueError("Split contains duplicate row indices.")

    if set(combined) != set(range(row_count)):
        raise ValueError("Split indices do not match source row domain.")


def validate_chronological_order(
    split: SplitIndices,
) -> None:
    """Prove train < validation < test in source order."""

    if max(split.train) >= min(split.validation):
        raise ValueError("Training period overlaps validation period.")

    if max(split.validation) >= min(split.test):
        raise ValueError("Validation period overlaps test period.")


def prevalence(
    targets: Sequence[int],
    indices: Sequence[int],
) -> float:
    """Binary target prevalence for one partition."""

    if not indices:
        raise ValueError("Cannot calculate prevalence for empty partition.")

    return sum(targets[index] for index in indices) / len(indices)


def split_summary(
    targets: Sequence[int],
    fingerprints: Sequence[str],
    split: SplitIndices,
    *,
    policy: str,
    seed: int | None,
) -> dict[str, object]:
    """Build reproducibility evidence for one split."""

    validate_partition_integrity(
        len(targets),
        split,
    )

    overlaps = overlap_counts(
        fingerprints,
        split,
    )

    return {
        "policy": policy,
        "seed": seed,
        "counts": {
            "train": len(split.train),
            "validation": len(split.validation),
            "test": len(split.test),
        },
        "source_order_ranges": {
            "train": [
                min(split.train),
                max(split.train),
            ],
            "validation": [
                min(split.validation),
                max(split.validation),
            ],
            "test": [
                min(split.test),
                max(split.test),
            ],
        },
        "target_prevalence": {
            "train": prevalence(
                targets,
                split.train,
            ),
            "validation": prevalence(
                targets,
                split.validation,
            ),
            "test": prevalence(
                targets,
                split.test,
            ),
        },
        "overlap_counts": overlaps,
    }
