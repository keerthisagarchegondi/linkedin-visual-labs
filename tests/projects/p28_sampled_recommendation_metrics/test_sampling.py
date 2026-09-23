from __future__ import annotations

import math

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.metrics import (
    auc_at_rank,
)
from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.sampling import (
    binomial_pmf,
    expected_sampled_ap_closed_form,
    expected_sampled_ap_pmf,
    expected_sampled_auc_identity,
    expected_sampled_auc_pmf,
    expected_sampled_ndcg,
    expected_sampled_recall_at_k,
    full_auc_identity_value,
    irrelevant_outrank_probability,
    probability_mass_sum,
    sampled_auc_from_outranking_count,
    sampled_rank_distribution,
    validate_negative_draws,
    validate_probability_mass,
)


@pytest.mark.parametrize(
    "value",
    [True, 1.0, "1"],
)
def test_negative_draws_rejects_non_integer(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        validate_negative_draws(value)


def test_negative_draws_rejects_zero() -> None:
    with pytest.raises(ValueError):
        validate_negative_draws(0)


def test_outrank_probability_best_and_worst_rank() -> None:
    assert (
        irrelevant_outrank_probability(
            1,
            n_items=10,
        )
        == 0.0
    )

    assert (
        irrelevant_outrank_probability(
            10,
            n_items=10,
        )
        == 1.0
    )


def test_binomial_pmf_explicit_p_zero_branch() -> None:
    assert binomial_pmf(
        negative_draws=3,
        p=0.0,
    ) == (
        1.0,
        0.0,
        0.0,
        0.0,
    )


def test_binomial_pmf_explicit_p_one_branch() -> None:
    assert binomial_pmf(
        negative_draws=3,
        p=1.0,
    ) == (
        0.0,
        0.0,
        0.0,
        1.0,
    )


@pytest.mark.parametrize(
    "p",
    [True, "0.5", math.inf, -0.1, 1.1],
)
def test_binomial_pmf_rejects_invalid_probability(
    p: object,
) -> None:
    error = TypeError if isinstance(p, (bool, str)) else ValueError

    with pytest.raises(error):
        binomial_pmf(
            negative_draws=3,
            p=p,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("m", "p"),
    [
        (1, 0.25),
        (5, 0.4),
        (99, 0.009900990099009901),
        (9999, 0.5),
        (9999, 0.9999),
    ],
)
def test_binomial_probability_mass_sums_to_one(
    m: int,
    p: float,
) -> None:
    probabilities = binomial_pmf(
        negative_draws=m,
        p=p,
    )

    total = validate_probability_mass(
        probabilities,
        absolute_tolerance=1e-10,
    )

    assert total == pytest.approx(
        1.0,
        abs=1e-10,
    )


def test_probability_mass_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        probability_mass_sum(())

    with pytest.raises(ValueError):
        probability_mass_sum((0.5, -0.5, 1.0))

    with pytest.raises(ValueError):
        probability_mass_sum((0.5, math.inf))

    with pytest.raises(ValueError):
        validate_probability_mass(
            (0.25, 0.25),
        )

    with pytest.raises(ValueError):
        validate_probability_mass(
            (1.0,),
            absolute_tolerance=0.0,
        )


def test_best_rank_sampled_distribution_is_deterministic() -> None:
    assert sampled_rank_distribution(
        1,
        n_items=10_000,
        negative_draws=99,
    ) == (
        (1, 1.0),
        *tuple(
            (rank, 0.0)
            for rank in range(
                2,
                101,
            )
        ),
    )


def test_worst_rank_sampled_distribution_is_deterministic() -> None:
    distribution = sampled_rank_distribution(
        10,
        n_items=10,
        negative_draws=4,
    )

    assert distribution[-1] == (
        5,
        1.0,
    )

    assert sum(probability for _, probability in distribution[:-1]) == 0.0


def test_hand_check_m_equals_one_ap() -> None:
    # If m=1, sampled rank is 1 with probability 1-p
    # and 2 with probability p.
    rank = 4
    n_items = 10
    p = (rank - 1) / (n_items - 1)

    expected = (1.0 - p) * 1.0 + p * 0.5

    assert expected_sampled_ap_pmf(
        rank,
        n_items=n_items,
        negative_draws=1,
    ) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("rank", "n_items", "m"),
    [
        (1, 10_000, 99),
        (2, 10_000, 99),
        (100, 10_000, 99),
        (8437, 10_000, 99),
        (10_000, 10_000, 99),
        (5342, 10_000, 500),
        (1548, 10_000, 9999),
    ],
)
def test_expected_ap_pmf_matches_closed_form(
    rank: int,
    n_items: int,
    m: int,
) -> None:
    via_pmf = expected_sampled_ap_pmf(
        rank,
        n_items=n_items,
        negative_draws=m,
    )

    closed_form = expected_sampled_ap_closed_form(
        rank,
        n_items=n_items,
        negative_draws=m,
    )

    assert via_pmf == pytest.approx(
        closed_form,
        rel=1e-11,
        abs=1e-12,
    )


def test_closed_form_explicit_p_zero_and_one() -> None:
    assert (
        expected_sampled_ap_closed_form(
            1,
            n_items=100,
            negative_draws=9,
        )
        == 1.0
    )

    assert expected_sampled_ap_closed_form(
        100,
        n_items=100,
        negative_draws=9,
    ) == pytest.approx(0.1)


def test_expected_sampled_ndcg_best_and_worst() -> None:
    assert expected_sampled_ndcg(
        1,
        n_items=100,
        negative_draws=9,
    ) == pytest.approx(1.0)

    assert expected_sampled_ndcg(
        100,
        n_items=100,
        negative_draws=9,
    ) == pytest.approx(1.0 / math.log2(11))


def test_expected_sampled_recall_trivial_k_boundary() -> None:
    assert (
        expected_sampled_recall_at_k(
            50,
            n_items=100,
            negative_draws=9,
            k=10,
        )
        == 1.0
    )


def test_expected_sampled_recall_nontrivial() -> None:
    # m=1 and k=1 means recall iff X=0.
    rank = 4
    n_items = 10

    p = (rank - 1) / (n_items - 1)

    assert expected_sampled_recall_at_k(
        rank,
        n_items=n_items,
        negative_draws=1,
        k=1,
    ) == pytest.approx(1.0 - p)


@pytest.mark.parametrize(
    ("rank", "n_items", "m"),
    [
        (1, 10_000, 99),
        (40, 10_000, 99),
        (100, 10_000, 99),
        (4482, 10_000, 99),
        (9266, 10_000, 500),
        (10_000, 10_000, 9999),
    ],
)
def test_expected_sampled_auc_equals_full_auc(
    rank: int,
    n_items: int,
    m: int,
) -> None:
    via_pmf = expected_sampled_auc_pmf(
        rank,
        n_items=n_items,
        negative_draws=m,
    )

    identity = expected_sampled_auc_identity(
        rank,
        n_items=n_items,
        negative_draws=m,
    )

    full_auc = auc_at_rank(
        rank,
        n_items=n_items,
    )

    independent_full = full_auc_identity_value(
        rank,
        n_items=n_items,
    )

    assert via_pmf == pytest.approx(
        identity,
        rel=1e-11,
        abs=1e-12,
    )

    assert identity == pytest.approx(
        full_auc,
        abs=1e-15,
    )

    assert identity == pytest.approx(
        independent_full,
        abs=1e-15,
    )


@pytest.mark.parametrize(
    ("x", "m", "expected"),
    [
        (0, 4, 1.0),
        (1, 4, 0.75),
        (4, 4, 0.0),
    ],
)
def test_sampled_auc_definition(
    x: int,
    m: int,
    expected: float,
) -> None:
    assert sampled_auc_from_outranking_count(
        x,
        negative_draws=m,
    ) == pytest.approx(expected)


def test_sampled_auc_rejects_invalid_count() -> None:
    with pytest.raises(ValueError):
        sampled_auc_from_outranking_count(
            5,
            negative_draws=4,
        )

    with pytest.raises(TypeError):
        sampled_auc_from_outranking_count(
            True,
            negative_draws=4,
        )
