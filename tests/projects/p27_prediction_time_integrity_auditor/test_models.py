from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.models import (
    AvailabilityClass,
    SplitConfig,
)


def test_availability_classes_are_frozen() -> None:
    assert {item.value for item in AvailabilityClass} == {
        "PRE_DECISION",
        "KNOWN_AT_DECISION",
        "DURING_ACTION",
        "POST_OUTCOME",
        "UNKNOWN",
    }


def test_split_config_accepts_frozen_ratios() -> None:
    split = SplitConfig(
        train=0.70,
        validation=0.15,
        test=0.15,
    )

    split.validate()


def test_split_config_rejects_nonpositive_value() -> None:
    split = SplitConfig(
        train=0.0,
        validation=0.50,
        test=0.50,
    )

    with pytest.raises(
        ValueError,
        match="must be positive",
    ):
        split.validate()


def test_split_config_rejects_invalid_total() -> None:
    split = SplitConfig(
        train=0.70,
        validation=0.20,
        test=0.20,
    )

    with pytest.raises(
        ValueError,
        match=r"sum to 1\.0",
    ):
        split.validate()
