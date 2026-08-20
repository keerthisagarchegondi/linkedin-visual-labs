"""Tests for revised pair-of-dice configuration and domain models."""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    PAIR_CASE_IDS,
    DecisionState,
    DiceModelError,
    build_pipeline_context,
    load_dice_config,
)


def test_pair_experiment_is_authoritative() -> None:
    config = load_dice_config()

    pair = config.pair_experiment

    assert pair.authoritative is True
    assert pair.roll_count_per_case == 10_000
    assert pair.total_observation_count == 60_000


def test_pair_experiment_contains_three_die_types() -> None:
    config = load_dice_config()

    assert set(config.pair_experiment.die_types) == {
        "unloaded",
        "partially_loaded",
        "fully_loaded",
    }


def test_pair_experiment_contains_six_cases() -> None:
    config = load_dice_config()

    assert tuple(config.pair_experiment.pair_order) == PAIR_CASE_IDS

    assert set(config.pair_experiment.pair_cases) == set(PAIR_CASE_IDS)


def test_pair_case_accessor() -> None:
    config = load_dice_config()

    case = config.pair_case("UF")

    assert case.case_id == "UF"
    assert case.die_1_type == "unloaded"
    assert case.die_2_type == "fully_loaded"
    assert case.truth_loaded is True
    assert case.seed == 1103


def test_die_type_accessor() -> None:
    config = load_dice_config()

    die = config.die_type("partially_loaded")

    assert die.short_id == "P"
    assert die.probabilities.values[-1] == pytest.approx(0.25)


def test_pair_inference_observes_sums_only() -> None:
    config = load_dice_config()

    observation = config.pair_experiment.observation

    assert observation.observation_type == "pair_sum"
    assert observation.minimum == 2
    assert observation.maximum == 12
    assert observation.individual_faces_visible_to_inference is False


def test_pair_model_prior_is_neutral_loaded_vs_fair() -> None:
    config = load_dice_config()

    priors = config.pair_experiment.model_priors

    assert priors.prior_fair_probability == pytest.approx(0.50)

    assert priors.prior_loaded_probability == pytest.approx(0.50)


def test_pair_decision_classifies_three_states() -> None:
    config = load_dice_config()

    decision = config.pair_experiment.decision

    assert decision.classify(0.01) is DecisionState.FAIR

    assert decision.classify(0.50) is DecisionState.UNCERTAIN

    assert decision.classify(0.99) is DecisionState.LOADED


def test_pair_decision_uses_stable_headline_metric() -> None:
    config = load_dice_config()

    decision = config.pair_experiment.decision

    assert decision.headline_roll_metric == "stable_decision_roll"

    assert decision.require_same_final_state_through_end is True

    assert decision.use_first_threshold_crossing_as_headline is False


def test_pair_video_contract_is_square() -> None:
    config = load_dice_config()

    video = config.pair_experiment.video

    assert video.width_px == 1080
    assert video.height_px == 1080
    assert video.aspect_ratio == "1:1"

    assert video.heading.height_px == 40
    assert video.middle_grid.height_px == 1000
    assert video.result_strip.height_px == 40

    assert video.panel_width_px == 360
    assert video.panel_height_px == 500

    assert video.result_cell_width_px == 180


def test_pair_video_contains_six_unique_panel_cells() -> None:
    config = load_dice_config()

    placements = config.pair_experiment.video.panel_placements

    assert len(placements) == 6

    assert {placement.case_id for placement in placements} == set(PAIR_CASE_IDS)

    assert (
        len(
            {
                (
                    placement.row,
                    placement.column,
                )
                for placement in placements
            }
        )
        == 6
    )


def test_pair_output_contract_matches_revised_paths() -> None:
    config = load_dice_config()

    outputs = config.pair_experiment.outputs

    assert outputs.simulation == Path("outputs/p01_bayesian_dice/data/pair_simulation.json")

    assert outputs.history == Path("outputs/p01_bayesian_dice/data/pair_case_histories.csv")

    assert outputs.summary == Path("outputs/p01_bayesian_dice/data/pair_case_summary.json")

    assert outputs.validation == Path("outputs/p01_bayesian_dice/data/pair_validation.json")

    assert outputs.video == Path(
        "outputs/p01_bayesian_dice/video/how_many_rolls_loaded_dice_pair.mp4"
    )


def test_pipeline_resolves_pair_outputs_safely() -> None:
    context = build_pipeline_context()

    outputs = context.pair_output_files()

    assert set(outputs) == {
        "simulation",
        "history",
        "summary",
        "validation",
        "preview_directory",
        "video",
        "manifest",
    }

    pair_root = (context.repository_root / "outputs" / "p01_bayesian_dice").resolve()

    assert all(path == pair_root or pair_root in path.parents for path in outputs.values())


def test_unknown_pair_case_is_rejected() -> None:
    config = load_dice_config()

    with pytest.raises(
        DiceModelError,
        match="unknown pair case",
    ):
        config.pair_case("XX")


def test_unknown_die_type_is_rejected() -> None:
    config = load_dice_config()

    with pytest.raises(
        DiceModelError,
        match="unknown die type",
    ):
        config.die_type("mystery")


def test_legacy_compatibility_remains_available_temporarily() -> None:
    config = load_dice_config()

    assert config.roll_count == 180
    assert config.showcase_scenario == "clearly_loaded"

    assert set(config.scenarios) == {
        "fair",
        "mildly_loaded",
        "clearly_loaded",
    }
