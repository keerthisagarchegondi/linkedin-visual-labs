"""Analytical sampled-rank expectations for Project 8."""

from __future__ import annotations

import math
from collections.abc import Callable

from .metrics import (
    auc_at_rank,
    average_precision_at_rank,
    ndcg_at_rank,
    recall_at_k,
    validate_n_items,
    validate_rank,
)

SampledRankMetric = Callable[[int, int], float]


def validate_negative_draws(
    negative_draws: object,
) -> int:
    """Validate the number of sampled irrelevant-item draws."""
    if type(negative_draws) is not int:
        raise TypeError("negative_draws must be a plain integer")

    if negative_draws < 1:
        raise ValueError("negative_draws must be >= 1")

    return negative_draws


def irrelevant_outrank_probability(
    rank: int,
    *,
    n_items: int,
) -> float:
    """Probability that a uniform irrelevant draw outranks the positive."""
    validated_n = validate_n_items(n_items)

    validated_rank = validate_rank(
        rank,
        n_items=validated_n,
    )

    return (validated_rank - 1) / (validated_n - 1)


def binomial_pmf(
    *,
    negative_draws: int,
    p: float,
) -> tuple[float, ...]:
    """Return P(X=x) for X~Binomial(m,p) using stable log-space evaluation."""
    m = validate_negative_draws(negative_draws)

    if isinstance(p, bool) or not isinstance(
        p,
        (int, float),
    ):
        raise TypeError("p must be a real number")

    p_float = float(p)

    if not math.isfinite(p_float):
        raise ValueError("p must be finite")

    if not 0.0 <= p_float <= 1.0:
        raise ValueError("p must be in [0, 1]")

    if p_float == 0.0:
        return (
            1.0,
            *([0.0] * m),
        )

    if p_float == 1.0:
        return (
            *([0.0] * m),
            1.0,
        )

    log_p = math.log(p_float)

    log_q = math.log1p(-p_float)

    log_m_factorial = math.lgamma(m + 1)

    probabilities: list[float] = []

    for x in range(m + 1):
        log_probability = (
            log_m_factorial
            - math.lgamma(x + 1)
            - math.lgamma(m - x + 1)
            + x * log_p
            + (m - x) * log_q
        )

        probabilities.append(math.exp(log_probability))

    raw_total = math.fsum(probabilities)

    if not math.isfinite(raw_total) or raw_total <= 0.0:
        raise ValueError("binomial PMF has invalid total mass")

    normalized = [probability / raw_total for probability in probabilities]

    residual = 1.0 - math.fsum(normalized)

    if residual != 0.0:
        mode_index = max(
            range(len(normalized)),
            key=normalized.__getitem__,
        )

        corrected = normalized[mode_index] + residual

        if not math.isfinite(corrected) or corrected < 0.0:
            raise ValueError("binomial PMF normalization failed")

        normalized[mode_index] = corrected

    return tuple(normalized)


def probability_mass_sum(
    probabilities: tuple[float, ...],
) -> float:
    """Accurately sum a PMF."""
    if not probabilities:
        raise ValueError("probabilities cannot be empty")

    for probability in probabilities:
        if not math.isfinite(probability):
            raise ValueError("probabilities must be finite")

        if probability < 0.0:
            raise ValueError("probabilities cannot be negative")

    return math.fsum(probabilities)


def validate_probability_mass(
    probabilities: tuple[float, ...],
    *,
    absolute_tolerance: float = 1e-12,
) -> float:
    """Validate that a PMF sums to one within tolerance."""
    if not math.isfinite(absolute_tolerance) or absolute_tolerance <= 0.0:
        raise ValueError("absolute_tolerance must be finite and > 0")

    total = probability_mass_sum(probabilities)

    if not math.isclose(
        total,
        1.0,
        rel_tol=0.0,
        abs_tol=absolute_tolerance,
    ):
        raise ValueError(f"binomial probability mass does not sum to one: {total:.17g}")

    return total


def sampled_rank_distribution(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
) -> tuple[tuple[int, float], ...]:
    """Return the sampled-rank distribution R=1+X."""
    m = validate_negative_draws(negative_draws)

    p = irrelevant_outrank_probability(
        rank,
        n_items=n_items,
    )

    probabilities = binomial_pmf(
        negative_draws=m,
        p=p,
    )

    validate_probability_mass(probabilities)

    return tuple(
        (
            x + 1,
            probability,
        )
        for x, probability in enumerate(probabilities)
    )


def expected_sampled_rank_metric(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
    metric: SampledRankMetric,
) -> float:
    """Expected sampled metric via explicit binomial PMF summation."""
    distribution = sampled_rank_distribution(
        rank,
        n_items=n_items,
        negative_draws=negative_draws,
    )

    sampled_candidate_count = validate_negative_draws(negative_draws) + 1

    return math.fsum(
        probability
        * metric(
            sampled_rank,
            sampled_candidate_count,
        )
        for sampled_rank, probability in distribution
    )


def expected_sampled_ap_pmf(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
) -> float:
    """Expected sampled AP via PMF summation."""
    return expected_sampled_rank_metric(
        rank,
        n_items=n_items,
        negative_draws=negative_draws,
        metric=lambda sampled_rank, candidate_count: average_precision_at_rank(
            sampled_rank,
            n_items=candidate_count,
        ),
    )


def expected_sampled_ap_closed_form(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
) -> float:
    """Independent closed-form E[1/(1+X)] for X~Binomial(m,p)."""
    m = validate_negative_draws(negative_draws)

    p = irrelevant_outrank_probability(
        rank,
        n_items=n_items,
    )

    if p == 0.0:
        return 1.0

    if p == 1.0:
        return 1.0 / (m + 1)

    exponent = (m + 1) * math.log1p(-p)

    numerator = -math.expm1(exponent)

    denominator = (m + 1) * p

    return numerator / denominator


def expected_sampled_ndcg(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
) -> float:
    """Expected untruncated sampled NDCG."""
    return expected_sampled_rank_metric(
        rank,
        n_items=n_items,
        negative_draws=negative_draws,
        metric=lambda sampled_rank, candidate_count: ndcg_at_rank(
            sampled_rank,
            n_items=candidate_count,
        ),
    )


def expected_sampled_recall_at_k(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
    k: int,
) -> float:
    """Expected sampled Recall@k."""
    m = validate_negative_draws(negative_draws)

    if type(k) is not int:
        raise TypeError("k must be a plain integer")

    if k < 1:
        raise ValueError("k must be >= 1")

    sampled_candidate_count = m + 1

    if k >= sampled_candidate_count:
        return 1.0

    return expected_sampled_rank_metric(
        rank,
        n_items=n_items,
        negative_draws=m,
        metric=lambda sampled_rank, candidate_count: recall_at_k(
            sampled_rank,
            n_items=candidate_count,
            k=k,
        ),
    )


def sampled_auc_from_outranking_count(
    outranking_count: int,
    *,
    negative_draws: int,
) -> float:
    """Sampled AUC for X outranking sampled negatives: 1-X/m."""
    m = validate_negative_draws(negative_draws)

    if type(outranking_count) is not int:
        raise TypeError("outranking_count must be a plain integer")

    if not 0 <= outranking_count <= m:
        raise ValueError(f"outranking_count must be in [0, {m}]")

    return 1.0 - (outranking_count / m)


def expected_sampled_auc_pmf(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
) -> float:
    """Expected sampled AUC through direct PMF summation."""
    m = validate_negative_draws(negative_draws)

    p = irrelevant_outrank_probability(
        rank,
        n_items=n_items,
    )

    probabilities = binomial_pmf(
        negative_draws=m,
        p=p,
    )

    validate_probability_mass(probabilities)

    return math.fsum(
        probability
        * sampled_auc_from_outranking_count(
            x,
            negative_draws=m,
        )
        for x, probability in enumerate(probabilities)
    )


def expected_sampled_auc_identity(
    rank: int,
    *,
    n_items: int,
    negative_draws: int,
) -> float:
    """Analytical identity E[sampled AUC]=1-p=full-catalog AUC."""
    validate_negative_draws(negative_draws)

    p = irrelevant_outrank_probability(
        rank,
        n_items=n_items,
    )

    return 1.0 - p


def full_auc_identity_value(
    rank: int,
    *,
    n_items: int,
) -> float:
    """Independent full-catalog comparator for the AUC identity."""
    return auc_at_rank(
        rank,
        n_items=n_items,
    )
