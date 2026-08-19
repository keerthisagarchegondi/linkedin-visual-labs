"""Tests for the square six-panel pair-dice visualization framework."""

from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg
import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    FRAME_HEIGHT_PX,
    FRAME_WIDTH_PX,
    PAIR_CASE_IDS,
    DiceProjectConfig,
    PairInferenceResult,
    PairSimulationResult,
    build_pair_dashboard_frame,
    infer_all_pair_cases,
    load_dice_config,
    panel_region,
    pixel_region_to_display_bounds,
    preview_roll_indices,
    render_pair_dashboard_frame,
    result_cell_region,
    simulate_all_pair_cases,
    synchronized_pair_records,
    validate_pair_dashboard_frame,
)

type CanonicalVisualizationExperiment = tuple[
    DiceProjectConfig,
    PairSimulationResult,
    PairInferenceResult,
]


@pytest.fixture(scope="module")
def canonical_visualization_experiment() -> CanonicalVisualizationExperiment:
    """Return one shared deterministic experiment for rendering tests."""
    config = load_dice_config()

    simulation = simulate_all_pair_cases(config)

    inference = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    return (
        config,
        simulation,
        inference,
    )


def test_panel_regions_match_exact_3x2_geometry(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
) -> None:
    config, _, _ = canonical_visualization_experiment

    expected = {
        "UU": (
            0,
            40,
        ),
        "UP": (
            360,
            40,
        ),
        "UF": (
            720,
            40,
        ),
        "PP": (
            0,
            540,
        ),
        "PF": (
            360,
            540,
        ),
        "FF": (
            720,
            540,
        ),
    }

    for case_id in PAIR_CASE_IDS:
        region = panel_region(
            config.pair_experiment,
            case_id,
        )

        assert (
            region.x_px,
            region.y_px,
        ) == expected[case_id]

        assert (
            region.width_px,
            region.height_px,
        ) == (
            360,
            500,
        )


def test_result_cells_are_exactly_180x40(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
) -> None:
    config, _, _ = canonical_visualization_experiment

    for index, _ in enumerate(PAIR_CASE_IDS):
        region = result_cell_region(
            config.pair_experiment,
            index,
        )

        assert region.x_px == (index * 180)

        assert region.y_px == 1040

        assert (
            region.width_px,
            region.height_px,
        ) == (
            180,
            40,
        )


def test_top_left_region_conversion_is_exact(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
) -> None:
    config, _, _ = canonical_visualization_experiment

    heading = pixel_region_to_display_bounds(config.pair_experiment.video.heading)

    assert heading.left == 0.0
    assert heading.right == 1080.0
    assert heading.bottom == 1040.0
    assert heading.top == 1080.0


def test_synchronized_records_use_same_roll_for_all_cases(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
) -> None:
    _, _, inference = canonical_visualization_experiment

    records = synchronized_pair_records(
        inference,
        1_234,
    )

    assert set(records) == set(PAIR_CASE_IDS)

    assert {record.roll_index for record in records.values()} == {1_234}


def test_preview_rolls_include_start_end_and_all_stable_decisions(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
) -> None:
    _, _, inference = canonical_visualization_experiment

    rolls = preview_roll_indices(inference)

    assert 1 in rolls
    assert 10_000 in rolls

    for case_id in PAIR_CASE_IDS:
        stable = inference.case(case_id).stable_decision_roll

        assert stable is not None
        assert stable in rolls


@pytest.mark.parametrize(
    "roll_index",
    (
        1,
        100,
        10_000,
    ),
)
def test_dashboard_frame_passes_geometry_validation(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
    roll_index: int,
) -> None:
    config, _, inference = canonical_visualization_experiment

    frame = build_pair_dashboard_frame(
        config.pair_experiment,
        inference,
        roll_index=roll_index,
    )

    report = validate_pair_dashboard_frame(frame)

    frame.figure.clear()

    assert report.passed is True
    assert report.issues == ()


def test_rendered_preview_is_exactly_1080x1080(
    canonical_visualization_experiment: (CanonicalVisualizationExperiment),
    tmp_path: Path,
) -> None:
    config, _, inference = canonical_visualization_experiment

    path = tmp_path / "preview.png"

    result = render_pair_dashboard_frame(
        config.pair_experiment,
        inference,
        roll_index=10_000,
        output_path=path,
    )

    assert result.validation.passed is True
    assert path.is_file()

    image = mpimg.imread(path)

    assert image.shape[0] == FRAME_HEIGHT_PX

    assert image.shape[1] == FRAME_WIDTH_PX
