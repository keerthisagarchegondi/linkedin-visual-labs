"""Project 3 Step 8 video contract tests."""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path

from PIL import Image

from linkedin_visual_labs.projects.p02_monopoly_ai.video import (
    DURATION_SECONDS,
    FPS,
    FRAME_COUNT,
    HEIGHT,
    REPRESENTATIVE_FRAME_INDICES,
    TIMELINE,
    VIDEO_MANIFEST,
    WIDTH,
    frame_state,
    headline_winner,
    load_runtime_inputs,
    numerical_leader,
    takeaway_sentence,
)


def test_media_contract() -> None:
    assert WIDTH == 1080
    assert HEIGHT == 1080
    assert FPS == 30
    assert DURATION_SECONDS == 60
    assert FRAME_COUNT == 1800


def test_timeline_is_exactly_1800_frames() -> None:
    assert TIMELINE[0].start_frame == 0
    assert TIMELINE[-1].end_frame == 1800

    assert sum(segment.frame_count for segment in TIMELINE) == 1800


def test_timeline_segments_are_contiguous() -> None:
    for previous, current in pairwise(TIMELINE):
        assert previous.end_frame == current.start_frame


def test_every_frame_has_state() -> None:
    for frame_index in (
        0,
        209,
        210,
        419,
        420,
        929,
        930,
        1169,
        1170,
        1499,
        1500,
        1649,
        1650,
        1799,
    ):
        state = frame_state(frame_index)

        assert 0.0 <= state.segment_progress <= 1.0


def test_representative_frame_contract() -> None:
    assert len(REPRESENTATIVE_FRAME_INDICES) == 13

    assert all(0 <= frame < FRAME_COUNT for frame in REPRESENTATIVE_FRAME_INDICES)


def test_runtime_inputs_use_real_event_log() -> None:
    inputs = load_runtime_inputs()

    assert len(inputs.replay.events) > 0

    assert len(inputs.replay.snapshots) == len(inputs.replay.events)

    assert inputs.context.game_count == 10_000


def test_winner_is_data_driven() -> None:
    inputs = load_runtime_inputs()

    expected = getattr(
        inputs.context,
        "headline_winner",
        None,
    )

    assert headline_winner(inputs.context) == expected


def test_numerical_leader_matches_max_win_rate() -> None:
    inputs = load_runtime_inputs()

    leader = numerical_leader(inputs.context)

    expected = max(
        inputs.context.strategies,
        key=lambda metric: (
            metric.win_rate,
            metric.strategy_id,
        ),
    )

    assert leader.strategy_id == expected.strategy_id

    assert leader.win_rate == expected.win_rate


def test_takeaway_is_generated_from_context() -> None:
    inputs = load_runtime_inputs()

    value = takeaway_sentence(inputs.context)

    assert value.strip()

    assert len(value) > 30


def test_representative_frames_when_present() -> None:
    root = Path("outputs/p02_monopoly_ai/video/representative_frames")

    if not root.is_dir():
        return

    frames = sorted(root.glob("frame_*.png"))

    assert len(frames) == 13

    for path in frames:
        with Image.open(path) as image:
            assert image.size == (
                1080,
                1080,
            )


def test_video_manifest_when_present() -> None:
    if not VIDEO_MANIFEST.is_file():
        return

    payload = json.loads(VIDEO_MANIFEST.read_text(encoding="utf-8"))

    assert payload["width"] == 1080

    assert payload["height"] == 1080

    assert payload["fps"] == 30

    assert payload["frame_count"] == 1800

    assert payload["duration_seconds"] == 60

    assert payload["game_count"] == 10_000
