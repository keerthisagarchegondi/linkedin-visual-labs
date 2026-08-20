"""Tests for Project 1 production video orchestration."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path
from typing import cast

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice import (
    PAIR_CASE_IDS,
    DiceProjectConfig,
    PairInferenceResult,
    PairSimulationResult,
    infer_all_pair_cases,
    load_dice_config,
    simulate_all_pair_cases,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pair_video import (
    VIDEO_CODEC,
    VIDEO_PIXEL_FORMAT,
    FrameSchedule,
    VideoProbe,
    build_ffmpeg_command,
    build_frame_schedule,
    validate_video,
)

type CanonicalVideoExperiment = tuple[
    DiceProjectConfig,
    PairSimulationResult,
    PairInferenceResult,
]


@pytest.fixture(scope="module")
def canonical_video_experiment() -> CanonicalVideoExperiment:
    """Return one deterministic experiment for video tests."""
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


def test_frame_schedule_has_exact_canonical_frame_count(
    canonical_video_experiment: CanonicalVideoExperiment,
) -> None:
    config, _, inference = canonical_video_experiment

    schedule = build_frame_schedule(
        inference,
        frame_rate=(config.pair_experiment.video.frame_rate),
        target_duration_seconds=(config.pair_experiment.video.target_duration_seconds),
    )

    assert schedule.frame_rate == 30
    assert schedule.frame_count == 1_350

    assert schedule.actual_duration_seconds == pytest.approx(45.0)


def test_frame_schedule_starts_at_one_and_ends_at_10000(
    canonical_video_experiment: CanonicalVideoExperiment,
) -> None:
    config, _, inference = canonical_video_experiment

    schedule = build_frame_schedule(
        inference,
        frame_rate=(config.pair_experiment.video.frame_rate),
        target_duration_seconds=(config.pair_experiment.video.target_duration_seconds),
    )

    assert schedule.roll_indices[0] == 1

    assert schedule.roll_indices[-1] == 10_000


def test_frame_schedule_is_monotonic(
    canonical_video_experiment: CanonicalVideoExperiment,
) -> None:
    config, _, inference = canonical_video_experiment

    schedule = build_frame_schedule(
        inference,
        frame_rate=(config.pair_experiment.video.frame_rate),
        target_duration_seconds=(config.pair_experiment.video.target_duration_seconds),
    )

    assert all(second >= first for first, second in pairwise(schedule.roll_indices))


def test_frame_schedule_contains_all_stable_decisions(
    canonical_video_experiment: CanonicalVideoExperiment,
) -> None:
    config, _, inference = canonical_video_experiment

    schedule = build_frame_schedule(
        inference,
        frame_rate=(config.pair_experiment.video.frame_rate),
        target_duration_seconds=(config.pair_experiment.video.target_duration_seconds),
    )

    for case_id in PAIR_CASE_IDS:
        stable = inference.case(case_id).stable_decision_roll

        assert stable is not None

        assert stable in schedule.roll_indices


def test_frame_schedule_is_deterministic(
    canonical_video_experiment: CanonicalVideoExperiment,
) -> None:
    _, _, inference = canonical_video_experiment

    first = build_frame_schedule(
        inference,
        frame_rate=30,
        target_duration_seconds=45.0,
    )

    second = build_frame_schedule(
        inference,
        frame_rate=30,
        target_duration_seconds=45.0,
    )

    assert first == second


def test_frame_schedule_is_nonlinear(
    canonical_video_experiment: CanonicalVideoExperiment,
) -> None:
    _, _, inference = canonical_video_experiment

    schedule = build_frame_schedule(
        inference,
        frame_rate=30,
        target_duration_seconds=45.0,
    )

    midpoint_roll = schedule.roll_indices[schedule.frame_count // 2]

    assert midpoint_roll != 5_000


def test_ffmpeg_command_has_required_codec_and_pixel_format(
    tmp_path: Path,
) -> None:
    output = tmp_path / "video.mp4"

    command = build_ffmpeg_command(
        output,
        frame_rate=30,
    )

    assert command[0] == "ffmpeg"

    assert VIDEO_CODEC in command
    assert VIDEO_PIXEL_FORMAT in command
    assert "1080x1080" in command

    assert str(output) == command[-1]


def test_video_validation_accepts_canonical_probe() -> None:
    schedule = FrameSchedule(
        frame_rate=30,
        frame_count=1_350,
        target_duration_seconds=45.0,
        roll_indices=(
            1,
            *range(
                2,
                1_350,
            ),
            10_000,
        ),
    )

    probe = VideoProbe(
        width=1080,
        height=1080,
        codec_name="h264",
        pixel_format="yuv420p",
        frame_rate=30.0,
        duration_seconds=45.0,
        frame_count=1_350,
    )

    report = validate_video(
        probe,
        schedule,
    )

    assert report.passed is True

    payload = report.as_dict()

    failed_check_ids_raw = payload["failed_check_ids"]

    assert isinstance(
        failed_check_ids_raw,
        list,
    )

    failed_check_ids = cast(
        list[str],
        failed_check_ids_raw,
    )

    assert failed_check_ids == []


def test_video_validation_rejects_wrong_dimensions() -> None:
    schedule = FrameSchedule(
        frame_rate=30,
        frame_count=2,
        target_duration_seconds=(2 / 30),
        roll_indices=(
            1,
            10_000,
        ),
    )

    probe = VideoProbe(
        width=1920,
        height=1080,
        codec_name="h264",
        pixel_format="yuv420p",
        frame_rate=30.0,
        duration_seconds=(2 / 30),
        frame_count=2,
    )

    report = validate_video(
        probe,
        schedule,
    )

    assert report.passed is False

    payload = report.as_dict()

    failed_check_ids_raw = payload["failed_check_ids"]

    assert isinstance(
        failed_check_ids_raw,
        list,
    )

    failed_check_ids = cast(
        list[str],
        failed_check_ids_raw,
    )

    assert "media.width" in failed_check_ids
