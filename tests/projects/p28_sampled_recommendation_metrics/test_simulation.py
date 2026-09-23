from __future__ import annotations

import math
import random

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.simulation import (
    METRIC_NAMES,
    analytical_profile_ap_closed_form,
    analytical_profile_expectations,
    build_profile_stream_key,
    construct_rng,
    derive_stream_seed,
    monte_carlo_acceptance_threshold,
    monte_carlo_agrees,
    run_monte_carlo_protocol,
    sample_outranking_count,
    sampled_rank_from_count,
    simulate_profile,
    simulate_profile_repetitions,
    summarize_repetitions,
    validate_repetitions,
)

RANKS_A = (
    100,
    100,
    100,
    100,
    100,
)


def test_validate_repetitions() -> None:
    assert validate_repetitions(2) == 2

    with pytest.raises(
        TypeError,
    ):
        validate_repetitions(True)

    with pytest.raises(
        ValueError,
    ):
        validate_repetitions(1)


def test_stream_seed_is_stable_and_keyed() -> None:
    first = derive_stream_seed(
        root_seed=20260923,
        stream_key="profile=A|N=10000|m=99|R=1000",
    )

    second = derive_stream_seed(
        root_seed=20260923,
        stream_key="profile=A|N=10000|m=99|R=1000",
    )

    other = derive_stream_seed(
        root_seed=20260923,
        stream_key="profile=B|N=10000|m=99|R=1000",
    )

    assert first == second
    assert first != other


@pytest.mark.parametrize(
    ("root_seed", "stream_key", "error"),
    [
        (
            True,
            "x",
            TypeError,
        ),
        (
            -1,
            "x",
            ValueError,
        ),
        (
            1,
            "",
            ValueError,
        ),
        (
            1,
            " x",
            ValueError,
        ),
    ],
)
def test_stream_seed_rejects_invalid_inputs(
    root_seed: object,
    stream_key: str,
    error: type[Exception],
) -> None:
    with pytest.raises(
        error,
    ):
        derive_stream_seed(
            root_seed=root_seed,  # type: ignore[arg-type]
            stream_key=stream_key,
        )


def test_construct_rng_replays_identically() -> None:
    rng_a, seed_a = construct_rng(
        root_seed=20260923,
        stream_key="deterministic",
    )

    rng_b, seed_b = construct_rng(
        root_seed=20260923,
        stream_key="deterministic",
    )

    assert seed_a == seed_b

    assert [rng_a.random() for _ in range(10)] == [rng_b.random() for _ in range(10)]


def test_profile_stream_key_is_stable() -> None:
    assert build_profile_stream_key(
        profile_label="A",
        n_items=10_000,
        negative_draws=99,
        repetitions=1_000,
    ) == ("profile=A|N=10000|m=99|R=1000")

    with pytest.raises(
        ValueError,
    ):
        build_profile_stream_key(
            profile_label=" A",
            n_items=10_000,
            negative_draws=99,
            repetitions=1_000,
        )


def test_sample_outranking_count_boundaries() -> None:
    rng = random.Random(123)

    assert (
        sample_outranking_count(
            rng=rng,
            negative_draws=9,
            p=0.0,
        )
        == 0
    )

    assert (
        sample_outranking_count(
            rng=rng,
            negative_draws=9,
            p=1.0,
        )
        == 9
    )


@pytest.mark.parametrize(
    ("p", "error"),
    [
        (
            True,
            TypeError,
        ),
        (
            math.inf,
            ValueError,
        ),
        (
            -0.1,
            ValueError,
        ),
        (
            1.1,
            ValueError,
        ),
    ],
)
def test_sample_outranking_count_rejects_invalid_probability(
    p: object,
    error: type[Exception],
) -> None:
    with pytest.raises(
        error,
    ):
        sample_outranking_count(
            rng=random.Random(1),
            negative_draws=4,
            p=p,  # type: ignore[arg-type]
        )


def test_sample_count_is_deterministic() -> None:
    rng_a = random.Random(321)

    rng_b = random.Random(321)

    a = [
        sample_outranking_count(
            rng=rng_a,
            negative_draws=12,
            p=0.3,
        )
        for _ in range(20)
    ]

    b = [
        sample_outranking_count(
            rng=rng_b,
            negative_draws=12,
            p=0.3,
        )
        for _ in range(20)
    ]

    assert a == b


def test_sampled_rank_from_count() -> None:
    assert (
        sampled_rank_from_count(
            0,
            negative_draws=9,
        )
        == 1
    )

    assert (
        sampled_rank_from_count(
            9,
            negative_draws=9,
        )
        == 10
    )

    with pytest.raises(
        TypeError,
    ):
        sampled_rank_from_count(
            True,
            negative_draws=9,
        )

    with pytest.raises(
        ValueError,
    ):
        sampled_rank_from_count(
            10,
            negative_draws=9,
        )


def test_repetition_statistics_are_distinct_quantities() -> None:
    summary = summarize_repetitions(
        (
            1.0,
            2.0,
            3.0,
        )
    )

    assert summary.mean == pytest.approx(2.0)

    assert summary.standard_deviation == pytest.approx(1.0)

    assert summary.standard_error == pytest.approx(1.0 / math.sqrt(3.0))

    assert summary.standard_error != summary.standard_deviation


def test_repetition_statistics_reject_nonfinite() -> None:
    with pytest.raises(
        ValueError,
    ):
        summarize_repetitions(
            (
                1.0,
                math.inf,
            )
        )


def test_profile_simulation_replays_exactly() -> None:
    first = simulate_profile(
        profile_label="A",
        ranks=RANKS_A,
        n_items=10_000,
        negative_draws=9,
        repetitions=20,
        root_seed=20260923,
    )

    second = simulate_profile(
        profile_label="A",
        ranks=RANKS_A,
        n_items=10_000,
        negative_draws=9,
        repetitions=20,
        root_seed=20260923,
    )

    assert first == second

    assert set(first.metrics) == set(METRIC_NAMES)


def test_profile_requires_five_instances() -> None:
    with pytest.raises(
        ValueError,
    ):
        simulate_profile_repetitions(
            profile_label="A",
            ranks=(
                1,
                2,
            ),
            n_items=10,
            negative_draws=2,
            repetitions=5,
            root_seed=1,
        )


def test_analytical_profile_requires_five_instances() -> None:
    with pytest.raises(
        ValueError,
    ):
        analytical_profile_expectations(
            ranks=(
                1,
                2,
            ),
            n_items=10,
            negative_draws=2,
        )

    with pytest.raises(
        ValueError,
    ):
        analytical_profile_ap_closed_form(
            ranks=(
                1,
                2,
            ),
            n_items=10,
            negative_draws=2,
        )


def test_ap_pmf_and_closed_form_profile_expectations_match() -> None:
    analytical = analytical_profile_expectations(
        ranks=RANKS_A,
        n_items=10_000,
        negative_draws=99,
    )

    closed_form = analytical_profile_ap_closed_form(
        ranks=RANKS_A,
        n_items=10_000,
        negative_draws=99,
    )

    assert analytical["ap"] == pytest.approx(
        closed_form,
        rel=1e-11,
        abs=1e-12,
    )


def test_acceptance_threshold_uses_five_se_or_floor() -> None:
    assert monte_carlo_acceptance_threshold(
        standard_error=0.0,
    ) == pytest.approx(1e-3)

    assert monte_carlo_acceptance_threshold(
        standard_error=0.01,
    ) == pytest.approx(0.05)

    with pytest.raises(
        ValueError,
    ):
        monte_carlo_acceptance_threshold(
            standard_error=-1.0,
        )


def test_monte_carlo_agreement_rule() -> None:
    assert monte_carlo_agrees(
        monte_carlo_mean=1.0005,
        analytical_expectation=1.0,
        standard_error=0.0,
    )

    assert not monte_carlo_agrees(
        monte_carlo_mean=1.002,
        analytical_expectation=1.0,
        standard_error=0.0,
    )

    with pytest.raises(
        ValueError,
    ):
        monte_carlo_agrees(
            monte_carlo_mean=math.inf,
            analytical_expectation=1.0,
            standard_error=0.1,
        )

    with pytest.raises(
        ValueError,
    ):
        monte_carlo_agrees(
            monte_carlo_mean=1.0,
            analytical_expectation=math.inf,
            standard_error=0.1,
        )


def test_protocol_uses_independent_profile_streams() -> None:
    profiles = {
        "A": RANKS_A,
        "B": (
            40,
            40,
            8437,
            9266,
            4482,
        ),
    }

    result = run_monte_carlo_protocol(
        profiles=profiles,
        n_items=10_000,
        negative_draws=9,
        repetitions=5,
        root_seed=20260923,
    )

    assert result["A"].stream_seed != result["B"].stream_seed

    with pytest.raises(
        ValueError,
    ):
        run_monte_carlo_protocol(
            profiles={},
            n_items=10_000,
            negative_draws=9,
            repetitions=5,
            root_seed=20260923,
        )
