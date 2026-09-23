"""Deterministic rank metrics for Project 8."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable

RankMetric = Callable[[int], float]


def validate_n_items(n_items: object) -> int:
    """Validate the full candidate-space size."""
    if type(n_items) is not int:
        raise TypeError("n_items must be a plain integer")

    if n_items < 2:
        raise ValueError("n_items must be >= 2")

    return n_items


def validate_rank(
    rank: object,
    *,
    n_items: int,
) -> int:
    """Validate a one-based rank within the candidate space."""
    validated_n = validate_n_items(n_items)

    if type(rank) is not int:
        raise TypeError("rank must be a plain integer")

    if not 1 <= rank <= validated_n:
        raise ValueError(f"rank must be in [1, {validated_n}]")

    return rank


def average_values(
    values: Iterable[float],
) -> float:
    """Return the arithmetic mean of a non-empty finite sequence."""
    materialized = tuple(values)

    if not materialized:
        raise ValueError("cannot average an empty sequence")

    for value in materialized:
        if not math.isfinite(value):
            raise ValueError("metric values must be finite")

    return math.fsum(materialized) / len(materialized)


def average_rank_metric(
    ranks: Iterable[int],
    *,
    metric: RankMetric,
    n_items: int,
) -> float:
    """Apply a rank metric per instance then average arithmetically."""
    validated_ranks = tuple(
        validate_rank(
            rank,
            n_items=n_items,
        )
        for rank in ranks
    )

    if not validated_ranks:
        raise ValueError("ranks cannot be empty")

    return average_values(metric(rank) for rank in validated_ranks)


def average_precision_at_rank(
    rank: int,
    *,
    n_items: int,
) -> float:
    """Single-positive AP.

    With exactly one relevant item, AP equals reciprocal rank: 1 / r.
    """
    validated_rank = validate_rank(
        rank,
        n_items=n_items,
    )

    return 1.0 / validated_rank


def ndcg_at_rank(
    rank: int,
    *,
    n_items: int,
) -> float:
    """Untruncated single-positive NDCG: 1 / log2(r + 1)."""
    validated_rank = validate_rank(
        rank,
        n_items=n_items,
    )

    return 1.0 / math.log2(validated_rank + 1)


def recall_at_k(
    rank: int,
    *,
    n_items: int,
    k: int,
) -> float:
    """Single-positive Recall@k."""
    validated_rank = validate_rank(
        rank,
        n_items=n_items,
    )

    if type(k) is not int:
        raise TypeError("k must be a plain integer")

    if k < 1:
        raise ValueError("k must be >= 1")

    return float(validated_rank <= k)


def auc_at_rank(
    rank: int,
    *,
    n_items: int,
) -> float:
    """Single-positive full-catalog AUC."""
    validated_n = validate_n_items(n_items)

    validated_rank = validate_rank(
        rank,
        n_items=validated_n,
    )

    return (validated_n - validated_rank) / (validated_n - 1)
