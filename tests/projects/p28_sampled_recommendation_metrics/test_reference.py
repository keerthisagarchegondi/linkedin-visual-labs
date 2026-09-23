from __future__ import annotations

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.reference import (
    ReferenceProtocol,
    load_reference_protocol,
)


def test_verified_reference_profiles() -> None:
    protocol = load_reference_protocol()

    assert protocol.profiles == {
        "A": (100, 100, 100, 100, 100),
        "B": (40, 40, 8437, 9266, 4482),
        "C": (212, 2, 743, 5342, 1548),
    }


def test_rejects_rank_zero() -> None:
    with pytest.raises(ValueError):
        ReferenceProtocol(
            n_items=10_000,
            reference_negative_draws=99,
            profiles={
                "A": (0, 100, 100, 100, 100),
                "B": (40, 40, 8437, 9266, 4482),
                "C": (212, 2, 743, 5342, 1548),
            },
        )


def test_rejects_boolean_rank() -> None:
    with pytest.raises(TypeError):
        ReferenceProtocol(
            n_items=10_000,
            reference_negative_draws=99,
            profiles={
                "A": (True, 100, 100, 100, 100),
                "B": (40, 40, 8437, 9266, 4482),
                "C": (212, 2, 743, 5342, 1548),
            },
        )
