from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.freeze import (
    METRICS,
    SAMPLE_SIZE_GRID,
    crossover_intervals,
    independent_profile_expected_metrics,
    ordering_groups,
    ordering_text,
    pairwise_relation,
    profile_expected_metrics,
    profile_full_metrics,
    reconcile_source_reference_values,
)
from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.reference import (
    load_reference_protocol,
)


def test_ordering_groups_preserves_real_ties() -> None:
    groups = ordering_groups(
        {
            "A": 1.0,
            "B": 1.0 + 5e-13,
            "C": 0.5,
        }
    )

    assert groups == (
        (
            "A",
            "B",
        ),
        ("C",),
    )

    assert ordering_text(groups) == "A=B>C"


def test_ordering_groups_separates_values_outside_tolerance() -> None:
    groups = ordering_groups(
        {
            "A": 1.0,
            "B": 1.0 - 2e-12,
        }
    )

    assert groups == (
        ("A",),
        ("B",),
    )

    with pytest.raises(
        ValueError,
    ):
        ordering_groups(
            {
                "A": 1.0,
            },
            tolerance=-1.0,
        )


def test_pairwise_relation() -> None:
    assert (
        pairwise_relation(
            1.0,
            1.0,
        )
        == "tie"
    )

    assert (
        pairwise_relation(
            2.0,
            1.0,
        )
        == "first_above_second"
    )

    assert (
        pairwise_relation(
            1.0,
            2.0,
        )
        == "second_above_first"
    )


def test_full_and_sampled_metric_shapes() -> None:
    reference = load_reference_protocol()

    full = profile_full_metrics(
        reference.profiles,
        n_items=reference.n_items,
    )

    sampled = profile_expected_metrics(
        reference.profiles,
        n_items=reference.n_items,
        negative_draws=99,
    )

    assert set(full) == {
        "A",
        "B",
        "C",
    }

    for profile in full:
        assert set(full[profile]) == set(METRICS)

        assert set(sampled[profile]) == set(METRICS)


def test_independent_m99_recomputation_matches_primary() -> None:
    reference = load_reference_protocol()

    primary = profile_expected_metrics(
        reference.profiles,
        n_items=reference.n_items,
        negative_draws=99,
    )

    independent = independent_profile_expected_metrics(
        reference.profiles,
        n_items=reference.n_items,
        negative_draws=99,
    )

    for profile in primary:
        for metric in METRICS:
            assert primary[profile][metric] == pytest.approx(
                independent[profile][metric],
                abs=1e-12,
            )


def test_auc_is_negative_control_across_frozen_grid() -> None:
    reference = load_reference_protocol()

    full = profile_full_metrics(
        reference.profiles,
        n_items=reference.n_items,
    )

    for m in SAMPLE_SIZE_GRID:
        sampled = profile_expected_metrics(
            reference.profiles,
            n_items=reference.n_items,
            negative_draws=m,
        )

        for profile in full:
            assert sampled[profile]["auc"] == pytest.approx(
                full[profile]["auc"],
                abs=1e-12,
            )


def test_crossover_intervals_never_claim_exact_point() -> None:
    synthetic = {
        1: {
            "A": {metric: (1.0 if metric == "ap" else 0.0) for metric in METRICS},
            "B": {metric: (0.0) for metric in METRICS},
        },
        2: {
            "A": {metric: (0.0) for metric in METRICS},
            "B": {metric: (1.0 if metric == "ap" else 0.0) for metric in METRICS},
        },
    }

    intervals = crossover_intervals(synthetic)

    ap = [interval for interval in intervals if interval["metric"] == "ap"]

    assert len(ap) == 1

    assert ap[0]["lower_computed_m"] == 1

    assert ap[0]["upper_computed_m"] == 2

    assert ap[0]["exact_crossover_inferred"] is False


def test_source_rounding_reconciliation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.csv"

    path.write_text(
        "profile,metric,context,value\nA,AP,full,0.100\nA,AP,sampled,0.200\n",
        encoding="utf-8",
    )

    result = reconcile_source_reference_values(
        path,
        full_metrics={
            "A": {
                "ap": 0.1001,
            }
        },
        sampled_metrics={
            "A": {
                "ap": 0.2001,
            }
        },
    )

    assert result["status"] == "PASS"

    assert result["definition_changes"] is False

    reconciled = result["reconciled"]

    assert isinstance(
        reconciled,
        list,
    )

    assert all(row["status"] == "ROUNDING_MATCH" for row in reconciled)


def test_source_rounding_discrepancy_is_recorded(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.csv"

    path.write_text(
        "profile,metric,context,value\nA,AP,full,0.100\n",
        encoding="utf-8",
    )

    result = reconcile_source_reference_values(
        path,
        full_metrics={
            "A": {
                "ap": 0.5,
            }
        },
        sampled_metrics={
            "A": {
                "ap": 0.5,
            }
        },
    )

    rows = result["reconciled"]

    assert isinstance(
        rows,
        list,
    )

    assert rows[0]["status"] == "DISCREPANCY_RECORDED"

    assert rows[0]["definition_changed"] is False


def test_frozen_full_ap_and_sampled_ap_orderings_differ() -> None:
    reference = load_reference_protocol()

    full = profile_full_metrics(
        reference.profiles,
        n_items=reference.n_items,
    )

    sampled = profile_expected_metrics(
        reference.profiles,
        n_items=reference.n_items,
        negative_draws=99,
    )

    full_order = ordering_text(
        ordering_groups({profile: values["ap"] for profile, values in full.items()})
    )

    sampled_order = ordering_text(
        ordering_groups({profile: values["ap"] for profile, values in sampled.items()})
    )

    assert full_order != sampled_order
