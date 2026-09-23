from __future__ import annotations

import itertools
from collections import Counter

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.sampling import (
    expected_sampled_ap_pmf,
    sampled_rank_distribution,
)


def _enumerated_sampled_rank_distribution(
    *,
    rank: int,
    n_items: int,
    negative_draws: int,
) -> dict[int, float]:
    # Explicitly enumerate irrelevant-item rank positions.
    irrelevant_positions = tuple(
        value
        for value in range(
            1,
            n_items + 1,
        )
        if value != rank
    )

    total = len(irrelevant_positions) ** negative_draws

    counts: Counter[int] = Counter()

    for draw_tuple in itertools.product(
        irrelevant_positions,
        repeat=negative_draws,
    ):
        outranking_count = sum(sampled_position < rank for sampled_position in draw_tuple)

        sampled_rank = 1 + outranking_count

        counts[sampled_rank] += 1

    return {sampled_rank: count / total for sampled_rank, count in counts.items()}


@pytest.mark.parametrize(
    ("rank", "n_items", "m"),
    [
        (1, 4, 2),
        (2, 4, 2),
        (3, 4, 2),
        (4, 4, 2),
        (2, 5, 3),
    ],
)
def test_binomial_distribution_matches_exact_enumeration(
    rank: int,
    n_items: int,
    m: int,
) -> None:
    enumerated = _enumerated_sampled_rank_distribution(
        rank=rank,
        n_items=n_items,
        negative_draws=m,
    )

    analytical = dict(
        sampled_rank_distribution(
            rank,
            n_items=n_items,
            negative_draws=m,
        )
    )

    all_ranks = set(enumerated) | set(analytical)

    for sampled_rank in all_ranks:
        assert analytical.get(
            sampled_rank,
            0.0,
        ) == pytest.approx(
            enumerated.get(
                sampled_rank,
                0.0,
            ),
            abs=1e-14,
        )


def test_expected_ap_matches_exact_enumeration() -> None:
    rank = 3
    n_items = 5
    m = 3

    enumerated = _enumerated_sampled_rank_distribution(
        rank=rank,
        n_items=n_items,
        negative_draws=m,
    )

    exact_expected_ap = sum(
        probability * (1.0 / sampled_rank) for sampled_rank, probability in enumerated.items()
    )

    analytical = expected_sampled_ap_pmf(
        rank,
        n_items=n_items,
        negative_draws=m,
    )

    assert analytical == pytest.approx(
        exact_expected_ap,
        abs=1e-14,
    )
