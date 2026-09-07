"""Tests for the final Project 3 V5 motion renderer."""

from __future__ import annotations

import hashlib

import pytest

from linkedin_visual_labs.projects.p02_monopoly_ai import video_motion
from linkedin_visual_labs.projects.p02_monopoly_ai.video_timeline import (
    load_timeline,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_v5 import (
    load_video_context,
    render_frame,
)


def test_v5_final_timeline_contract() -> None:
    timeline = load_timeline()

    assert timeline.fps == 30
    assert timeline.duration_seconds == 60.0
    assert timeline.frame_count == 1800
    assert len(timeline.scenes) == 13

    assert timeline.scenes[0].start_frame == 0

    assert timeline.scenes[-1].end_frame_exclusive == 1800


@pytest.mark.parametrize(
    (
        "frame_index",
        "scene_id",
    ),
    (
        (
            0,
            "cold_open_dice",
        ),
        (
            29,
            "cold_open_dice",
        ),
        (
            30,
            "cold_open_move",
        ),
        (
            59,
            "cold_open_move",
        ),
        (
            60,
            "cold_open_purchase",
        ),
        (
            209,
            "cold_open_question",
        ),
        (
            210,
            "strategies",
        ),
        (
            419,
            "strategies",
        ),
        (
            420,
            "representative_game",
        ),
        (
            929,
            "representative_game",
        ),
        (
            930,
            "scale_10000",
        ),
        (
            1170,
            "leaderboard",
        ),
        (
            1500,
            "risk_reward",
        ),
        (
            1650,
            "result",
        ),
        (
            1799,
            "result",
        ),
    ),
)
def test_v5_frame_router_boundaries(
    frame_index: int,
    scene_id: str,
) -> None:
    timeline = load_timeline()

    assert timeline.scene_for_frame(frame_index).scene_id == scene_id


def test_v5_motion_primitives_are_bounded() -> None:
    for value in (
        -10.0,
        -1.0,
        0.0,
        0.25,
        0.5,
        0.75,
        1.0,
        2.0,
        10.0,
    ):
        assert 0.0 <= video_motion.clamp01(value) <= 1.0

        assert 0.0 <= video_motion.ease_in_out_cubic(value) <= 1.0

        assert 0.0 <= video_motion.ease_out_cubic(value) <= 1.0


@pytest.mark.monopoly_release_artifacts
@pytest.mark.parametrize(
    "frame_index",
    (
        0,
        15,
        29,
        30,
        45,
        59,
        420,
        500,
        929,
        930,
        1170,
        1499,
        1500,
        1649,
        1650,
        1799,
    ),
)
def test_v5_rendered_key_frames_are_1080_square(
    frame_index: int,
) -> None:
    context = load_video_context()

    image = render_frame(
        context,
        frame_index,
    )

    assert image.size == (
        1080,
        1080,
    )

    assert image.mode == "RGB"


@pytest.mark.monopoly_release_artifacts
def test_v5_frame_render_is_deterministic() -> None:
    context = load_video_context()

    first = render_frame(
        context,
        500,
    )

    second = render_frame(
        context,
        500,
    )

    first_digest = hashlib.sha256(first.tobytes()).hexdigest()

    second_digest = hashlib.sha256(second.tobytes()).hexdigest()

    assert first_digest == second_digest
