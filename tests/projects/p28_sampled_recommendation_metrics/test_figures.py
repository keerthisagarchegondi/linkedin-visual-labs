from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.figures import (
    figure_payloads,
    load_inputs,
    profile_colors,
)

ROOT = Path(__file__).resolve().parents[3]


def test_step6_uses_frozen_inputs() -> None:
    release, validation, contract = load_inputs(ROOT)

    assert release["results_frozen"] is True

    assert contract["status"] == "FROZEN"

    assert contract["output_design_frozen"] is True

    assert validation["auc_negative_control"]["status"] == "PASS"


def test_figure_1_uses_actual_ap_reversal() -> None:
    release, validation, _ = load_inputs(ROOT)

    payload = figure_payloads(
        release,
        validation,
    )["figure_1"]

    assert payload["full_ordering"] == "C>B>A"

    assert payload["sampled_ordering"] == "A>B>C"

    assert payload["full_ap"]["A"] == 0.01

    assert payload["sampled_ap_m99"]["A"] > payload["sampled_ap_m99"]["B"]


def test_figure_2_uses_only_frozen_grid() -> None:
    release, validation, _ = load_inputs(ROOT)

    payload = figure_payloads(
        release,
        validation,
    )["figure_2"]

    assert payload["grid"] == [
        1,
        2,
        5,
        10,
        20,
        50,
        99,
        200,
        500,
        1000,
        5000,
        9999,
    ]

    assert set(payload["metrics"]) == {
        "ap",
        "ndcg",
        "recall_at_10",
    }

    assert all(
        interval["exact_crossover_inferred"] is False for interval in payload["crossover_intervals"]
    )


def test_figure_3_auc_is_negative_control() -> None:
    release, validation, _ = load_inputs(ROOT)

    payload = figure_payloads(
        release,
        validation,
    )["figure_3"]

    assert payload["full_auc_ordering"] == "A>C>B"

    assert payload["sampled_auc_ordering"] == "A>C>B"

    assert payload["source_mc_all_accepted"] is True

    assert payload["high_precision_all_accepted"] is True

    for profile in (
        "A",
        "B",
        "C",
    ):
        expected = payload["full_auc"][profile]

        assert all(value == expected for value in payload["auc"][profile])


def test_profile_colors_come_from_frozen_contract() -> None:
    _, _, contract = load_inputs(ROOT)

    colors = profile_colors(contract)

    assert colors == {
        "A": "#0072B2",
        "B": "#D55E00",
        "C": "#009E73",
    }
