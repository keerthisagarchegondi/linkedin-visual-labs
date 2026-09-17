from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.splits import (
    SplitIndices,
    chronological_split,
    overlap_counts,
    random_comparison_split,
    validate_chronological_order,
    validate_partition_integrity,
)


def test_chronological_split_is_70_15_15_and_ordered() -> None:
    split = chronological_split(100)

    assert len(split.train) == 70
    assert len(split.validation) == 15
    assert len(split.test) == 15

    validate_partition_integrity(
        100,
        split,
    )

    validate_chronological_order(split)

    assert max(split.train) < min(split.validation)
    assert max(split.validation) < min(split.test)


def test_random_comparison_is_deterministic_and_disjoint() -> None:
    targets = [index % 2 for index in range(100)]

    first = random_comparison_split(targets)

    second = random_comparison_split(targets)

    assert first == second

    validate_partition_integrity(
        100,
        first,
    )

    fingerprints = [f"row-{index}" for index in range(100)]

    assert overlap_counts(
        fingerprints,
        first,
    ) == {
        "train_validation": 0,
        "train_test": 0,
        "validation_test": 0,
    }


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (
            2,
            "At least three rows",
        ),
    ],
)
def test_chronological_split_rejects_invalid_rows(
    rows: int,
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        chronological_split(rows)


def test_partition_integrity_rejects_duplicate_indices() -> None:
    split = SplitIndices(
        train=(0, 1),
        validation=(2,),
        test=(2,),
    )

    with pytest.raises(
        ValueError,
    ):
        validate_partition_integrity(
            4,
            split,
        )
