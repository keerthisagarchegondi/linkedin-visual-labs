"""Independent Monte Carlo validation engine for Project 8."""

from __future__ import annotations

import hashlib
import math
import random
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .metrics import (
    average_precision_at_rank,
    ndcg_at_rank,
    recall_at_k,
    validate_n_items,
    validate_rank,
)
from .sampling import (
    expected_sampled_ap_closed_form,
    expected_sampled_ap_pmf,
    expected_sampled_auc_identity,
    expected_sampled_ndcg,
    expected_sampled_recall_at_k,
    irrelevant_outrank_probability,
    sampled_auc_from_outranking_count,
    validate_negative_draws,
)

METRIC_NAMES = (
    "ap",
    "ndcg",
    "recall_at_10",
    "auc",
)


@dataclass(frozen=True)
class MonteCarloSummary:
    """Summary across repetition-level five-instance means."""

    mean: float
    standard_deviation: float
    standard_error: float
    repetitions: int


@dataclass(frozen=True)
class MonteCarloProfileResult:
    """Monte Carlo result for one five-instance model profile."""

    profile_label: str
    stream_key: str
    stream_seed: int
    repetitions: int
    metrics: dict[str, MonteCarloSummary]


def validate_repetitions(
    repetitions: object,
) -> int:
    """Validate Monte Carlo repetition count."""
    if type(repetitions) is not int:
        raise TypeError("repetitions must be a plain integer")

    if repetitions < 2:
        raise ValueError("repetitions must be >= 2")

    return repetitions


def derive_stream_seed(
    *,
    root_seed: int,
    stream_key: str,
) -> int:
    """Derive a stable RNG seed without Python's randomized hash()."""
    if type(root_seed) is not int:
        raise TypeError("root_seed must be a plain integer")

    if root_seed < 0:
        raise ValueError("root_seed must be >= 0")

    if (
        not isinstance(
            stream_key,
            str,
        )
        or not stream_key
        or stream_key.strip() != stream_key
    ):
        raise ValueError("stream_key must be a non-empty stripped string")

    payload = (f"project8|{root_seed}|{stream_key}").encode()

    digest = hashlib.sha256(payload).digest()

    return int.from_bytes(
        digest[:16],
        byteorder="big",
        signed=False,
    )


def construct_rng(
    *,
    root_seed: int,
    stream_key: str,
) -> tuple[random.Random, int]:
    """Construct an isolated deterministic MT19937 stream."""
    seed = derive_stream_seed(
        root_seed=root_seed,
        stream_key=stream_key,
    )

    return (
        random.Random(seed),
        seed,
    )


def build_profile_stream_key(
    *,
    profile_label: str,
    n_items: int,
    negative_draws: int,
    repetitions: int,
) -> str:
    """Build the immutable experiment stream key."""
    if (
        not isinstance(
            profile_label,
            str,
        )
        or not profile_label
        or profile_label.strip() != profile_label
    ):
        raise ValueError("profile_label must be a non-empty stripped string")

    validated_n = validate_n_items(n_items)

    validated_m = validate_negative_draws(negative_draws)

    validated_repetitions = validate_repetitions(repetitions)

    return f"profile={profile_label}|N={validated_n}|m={validated_m}|R={validated_repetitions}"


def sample_outranking_count(
    *,
    rng: random.Random,
    negative_draws: int,
    p: float,
) -> int:
    """Generate X by explicit Bernoulli sampling, independent of PMF code."""
    m = validate_negative_draws(negative_draws)

    if isinstance(
        p,
        bool,
    ) or not isinstance(
        p,
        (int, float),
    ):
        raise TypeError("p must be a real number")

    probability = float(p)

    if not math.isfinite(probability):
        raise ValueError("p must be finite")

    if not 0.0 <= probability <= 1.0:
        raise ValueError("p must be in [0, 1]")

    if probability == 0.0:
        return 0

    if probability == 1.0:
        return m

    return sum(rng.random() < probability for _ in range(m))


def sampled_rank_from_count(
    outranking_count: int,
    *,
    negative_draws: int,
) -> int:
    """Convert X to sampled rank R=1+X."""
    m = validate_negative_draws(negative_draws)

    if type(outranking_count) is not int:
        raise TypeError("outranking_count must be a plain integer")

    if not 0 <= outranking_count <= m:
        raise ValueError(f"outranking_count must be in [0, {m}]")

    return outranking_count + 1


def simulate_profile_repetitions(
    *,
    profile_label: str,
    ranks: Sequence[int],
    n_items: int,
    negative_draws: int,
    repetitions: int,
    root_seed: int,
) -> tuple[
    dict[str, tuple[float, ...]],
    str,
    int,
]:
    """Return metric values for every repetition of one model profile."""
    validated_n = validate_n_items(n_items)

    m = validate_negative_draws(negative_draws)

    r_count = validate_repetitions(repetitions)

    validated_ranks = tuple(
        validate_rank(
            rank,
            n_items=validated_n,
        )
        for rank in ranks
    )

    if len(validated_ranks) != 5:
        raise ValueError("profile must contain exactly five ranks")

    stream_key = build_profile_stream_key(
        profile_label=profile_label,
        n_items=validated_n,
        negative_draws=m,
        repetitions=r_count,
    )

    rng, seed = construct_rng(
        root_seed=root_seed,
        stream_key=stream_key,
    )

    sampled_candidate_count = m + 1

    values: dict[str, list[float]] = {metric: [] for metric in METRIC_NAMES}

    probabilities = tuple(
        irrelevant_outrank_probability(
            rank,
            n_items=validated_n,
        )
        for rank in validated_ranks
    )

    for _ in range(r_count):
        ap_values: list[float] = []
        ndcg_values: list[float] = []
        recall_values: list[float] = []
        auc_values: list[float] = []

        for p in probabilities:
            count = sample_outranking_count(
                rng=rng,
                negative_draws=m,
                p=p,
            )

            sampled_rank = sampled_rank_from_count(
                count,
                negative_draws=m,
            )

            ap_values.append(
                average_precision_at_rank(
                    sampled_rank,
                    n_items=sampled_candidate_count,
                )
            )

            ndcg_values.append(
                ndcg_at_rank(
                    sampled_rank,
                    n_items=sampled_candidate_count,
                )
            )

            recall_values.append(
                recall_at_k(
                    sampled_rank,
                    n_items=sampled_candidate_count,
                    k=10,
                )
            )

            auc_values.append(
                sampled_auc_from_outranking_count(
                    count,
                    negative_draws=m,
                )
            )

        values["ap"].append(math.fsum(ap_values) / 5.0)

        values["ndcg"].append(math.fsum(ndcg_values) / 5.0)

        values["recall_at_10"].append(math.fsum(recall_values) / 5.0)

        values["auc"].append(math.fsum(auc_values) / 5.0)

    return (
        {metric: tuple(metric_values) for metric, metric_values in values.items()},
        stream_key,
        seed,
    )


def summarize_repetitions(
    values: Sequence[float],
) -> MonteCarloSummary:
    """Compute mean, sample SD, and Monte Carlo standard error."""
    materialized = tuple(float(value) for value in values)

    repetitions = validate_repetitions(len(materialized))

    if not all(math.isfinite(value) for value in materialized):
        raise ValueError("Monte Carlo repetition values must be finite")

    mean = statistics.fmean(materialized)

    standard_deviation = statistics.stdev(materialized)

    standard_error = standard_deviation / math.sqrt(repetitions)

    return MonteCarloSummary(
        mean=mean,
        standard_deviation=standard_deviation,
        standard_error=standard_error,
        repetitions=repetitions,
    )


def simulate_profile(
    *,
    profile_label: str,
    ranks: Sequence[int],
    n_items: int,
    negative_draws: int,
    repetitions: int,
    root_seed: int,
) -> MonteCarloProfileResult:
    """Simulate and summarize one five-instance model profile."""
    values, stream_key, seed = simulate_profile_repetitions(
        profile_label=profile_label,
        ranks=ranks,
        n_items=n_items,
        negative_draws=negative_draws,
        repetitions=repetitions,
        root_seed=root_seed,
    )

    return MonteCarloProfileResult(
        profile_label=profile_label,
        stream_key=stream_key,
        stream_seed=seed,
        repetitions=repetitions,
        metrics={
            metric: summarize_repetitions(metric_values) for metric, metric_values in values.items()
        },
    )


def analytical_profile_expectations(
    *,
    ranks: Sequence[int],
    n_items: int,
    negative_draws: int,
) -> dict[str, float]:
    """Compute analytical expectations independently from simulation."""
    validated_n = validate_n_items(n_items)

    m = validate_negative_draws(negative_draws)

    validated_ranks = tuple(
        validate_rank(
            rank,
            n_items=validated_n,
        )
        for rank in ranks
    )

    if len(validated_ranks) != 5:
        raise ValueError("profile must contain exactly five ranks")

    return {
        "ap": math.fsum(
            expected_sampled_ap_pmf(
                rank,
                n_items=validated_n,
                negative_draws=m,
            )
            for rank in validated_ranks
        )
        / 5.0,
        "ndcg": math.fsum(
            expected_sampled_ndcg(
                rank,
                n_items=validated_n,
                negative_draws=m,
            )
            for rank in validated_ranks
        )
        / 5.0,
        "recall_at_10": math.fsum(
            expected_sampled_recall_at_k(
                rank,
                n_items=validated_n,
                negative_draws=m,
                k=10,
            )
            for rank in validated_ranks
        )
        / 5.0,
        "auc": math.fsum(
            expected_sampled_auc_identity(
                rank,
                n_items=validated_n,
                negative_draws=m,
            )
            for rank in validated_ranks
        )
        / 5.0,
    }


def analytical_profile_ap_closed_form(
    *,
    ranks: Sequence[int],
    n_items: int,
    negative_draws: int,
) -> float:
    """Independent profile AP expectation via the Step-2 closed form."""
    validated_n = validate_n_items(n_items)

    m = validate_negative_draws(negative_draws)

    validated_ranks = tuple(
        validate_rank(
            rank,
            n_items=validated_n,
        )
        for rank in ranks
    )

    if len(validated_ranks) != 5:
        raise ValueError("profile must contain exactly five ranks")

    return (
        math.fsum(
            expected_sampled_ap_closed_form(
                rank,
                n_items=validated_n,
                negative_draws=m,
            )
            for rank in validated_ranks
        )
        / 5.0
    )


def monte_carlo_acceptance_threshold(
    *,
    standard_error: float,
) -> float:
    """Frozen Step-0 Monte Carlo validation threshold."""
    if not math.isfinite(standard_error) or standard_error < 0.0:
        raise ValueError("standard_error must be finite and >= 0")

    return max(
        5.0 * standard_error,
        1e-3,
    )


def monte_carlo_agrees(
    *,
    monte_carlo_mean: float,
    analytical_expectation: float,
    standard_error: float,
) -> bool:
    """Check the preregistered Monte Carlo acceptance criterion."""
    if not math.isfinite(monte_carlo_mean):
        raise ValueError("monte_carlo_mean must be finite")

    if not math.isfinite(analytical_expectation):
        raise ValueError("analytical_expectation must be finite")

    threshold = monte_carlo_acceptance_threshold(
        standard_error=standard_error,
    )

    return abs(monte_carlo_mean - analytical_expectation) <= threshold


def run_monte_carlo_protocol(
    *,
    profiles: Mapping[str, Sequence[int]],
    n_items: int,
    negative_draws: int,
    repetitions: int,
    root_seed: int,
) -> dict[str, MonteCarloProfileResult]:
    """Run one preregistered repetition-count experiment."""
    if not profiles:
        raise ValueError("profiles cannot be empty")

    return {
        profile_label: simulate_profile(
            profile_label=profile_label,
            ranks=ranks,
            n_items=n_items,
            negative_draws=negative_draws,
            repetitions=repetitions,
            root_seed=root_seed,
        )
        for profile_label, ranks in sorted(profiles.items())
    }
