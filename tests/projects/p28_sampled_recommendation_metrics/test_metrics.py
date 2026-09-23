from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.metrics import (
    auc_at_rank,
    average_precision_at_rank,
    average_rank_metric,
    average_values,
    ndcg_at_rank,
    recall_at_k,
    validate_n_items,
    validate_rank,
)


def test_validate_rank_accepts_one_based_boundaries() -> None:
    assert validate_rank(1, n_items=10) == 1
    assert validate_rank(10, n_items=10) == 10


@pytest.mark.parametrize(
    "rank",
    [0, -1, 11],
)
def test_validate_rank_rejects_out_of_range(
    rank: int,
) -> None:
    with pytest.raises(ValueError):
        validate_rank(
            rank,
            n_items=10,
        )


@pytest.mark.parametrize(
    "rank",
    [True, 1.0, "1"],
)
def test_validate_rank_rejects_non_plain_integer(
    rank: object,
) -> None:
    with pytest.raises(TypeError):
        validate_rank(
            rank,
            n_items=10,
        )


@pytest.mark.parametrize(
    "n_items",
    [True, 2.0, "10"],
)
def test_validate_n_items_rejects_non_integer(
    n_items: object,
) -> None:
    with pytest.raises(TypeError):
        validate_n_items(n_items)


def test_validate_n_items_rejects_too_small() -> None:
    with pytest.raises(ValueError):
        validate_n_items(1)


def test_ap_equals_reciprocal_rank_single_positive() -> None:
    assert average_precision_at_rank(
        4,
        n_items=10,
    ) == pytest.approx(0.25)


def test_untruncated_ndcg_definition() -> None:
    assert ndcg_at_rank(
        3,
        n_items=10,
    ) == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("rank", "expected"),
    [
        (1, 1.0),
        (10, 1.0),
        (11, 0.0),
    ],
)
def test_recall_at_10(
    rank: int,
    expected: float,
) -> None:
    assert (
        recall_at_k(
            rank,
            n_items=20,
            k=10,
        )
        == expected
    )


def test_recall_rejects_invalid_k() -> None:
    with pytest.raises(ValueError):
        recall_at_k(
            1,
            n_items=10,
            k=0,
        )

    with pytest.raises(TypeError):
        recall_at_k(
            1,
            n_items=10,
            k=True,
        )


def test_auc_best_and_worst_rank() -> None:
    assert auc_at_rank(
        1,
        n_items=10,
    ) == pytest.approx(1.0)

    assert auc_at_rank(
        10,
        n_items=10,
    ) == pytest.approx(0.0)


def test_average_values_uses_arithmetic_mean() -> None:
    assert average_values([0.1, 0.2, 0.3]) == pytest.approx(0.2)


def test_average_values_rejects_empty_or_nonfinite() -> None:
    with pytest.raises(ValueError):
        average_values([])

    with pytest.raises(ValueError):
        average_values([1.0, math.inf])


def test_average_rank_metric_averages_instance_metrics() -> None:
    result = average_rank_metric(
        [1, 2, 4, 5, 10],
        metric=lambda rank: 1.0 / rank,
        n_items=10,
    )

    assert result == pytest.approx((1.0 + 0.5 + 0.25 + 0.2 + 0.1) / 5.0)


def test_average_rank_metric_rejects_empty() -> None:
    with pytest.raises(ValueError):
        average_rank_metric(
            [],
            metric=lambda rank: float(rank),
            n_items=10,
        )
