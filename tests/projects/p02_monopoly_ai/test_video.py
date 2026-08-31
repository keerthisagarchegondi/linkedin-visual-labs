"""Tests for the Project 3 V4 cinematic tabletop renderer."""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai.video import (
    DURATION_SECONDS,
    FPS,
    FRAME_COUNT,
    HEIGHT,
    TIMELINE,
    WIDTH,
    load_runtime,
    ranking,
    segment,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_board import (
    PIPS,
    board_xy,
    moving_position,
    route,
)


def test_media_contract() -> None:
    assert WIDTH == 1080
    assert HEIGHT == 1080
    assert FPS == 30
    assert FRAME_COUNT == 1800
    assert DURATION_SECONDS == 60


def test_timeline_contract() -> None:
    assert TIMELINE[0].start == 0
    assert TIMELINE[-1].end == 1800

    for previous, current in pairwise(TIMELINE):
        assert previous.end == current.start


def test_conventional_dice_have_pips() -> None:
    assert set(PIPS) == {
        1,
        2,
        3,
        4,
        5,
        6,
    }

    assert len(PIPS[1]) == 1

    assert len(PIPS[6]) == 6


def test_board_positions_are_projected() -> None:
    positions = [board_xy(index) for index in range(40)]

    assert len(set(positions)) == 40


def test_route_wraps_start() -> None:
    assert route(
        38,
        2,
    ) == (
        38,
        39,
        0,
        1,
        2,
    )


def test_lift_carry_drop() -> None:
    start = moving_position(
        3,
        9,
        0.0,
    )

    middle = moving_position(
        3,
        9,
        0.5,
    )

    end = moving_position(
        3,
        9,
        1.0,
    )

    assert start[2] == 0.0
    assert middle[2] > 0.0
    assert abs(end[2]) < 1e-12


def test_runtime_uses_validated_metrics() -> None:
    runtime = load_runtime()

    assert len(runtime.metrics) == 4

    for metric in runtime.metrics:
        assert 0.0 <= metric.win_rate <= 1.0

        assert 0.0 <= metric.bankruptcy_rate <= 1.0

        assert 0.0 <= metric.ci_lower <= metric.ci_upper <= 1.0


def test_story_uses_real_turns() -> None:
    runtime = load_runtime()

    assert runtime.story.dice_turn.dice is not None

    assert runtime.story.move_turn.from_position != runtime.story.move_turn.to_position

    assert len(runtime.story.strategy_turns) == 4

    assert len(runtime.story.narrative_turns) >= 4


def test_ranking_matches_actual_maximum() -> None:
    runtime = load_runtime()

    rows = ranking(runtime)

    assert rows[0].win_rate == max(metric.win_rate for metric in runtime.metrics)


def test_segment_boundaries() -> None:
    cases = (
        (0, "opening"),
        (209, "opening"),
        (210, "strategies"),
        (419, "strategies"),
        (420, "gameplay"),
        (929, "gameplay"),
        (930, "scale"),
        (1169, "scale"),
        (1170, "leaderboard"),
        (1499, "leaderboard"),
        (1500, "risk"),
        (1649, "risk"),
        (1650, "result"),
        (1799, "result"),
    )

    for frame, expected in cases:
        item, progress = segment(frame)

        assert item.name == expected

        assert 0.0 <= progress < 1.0


def test_v4_sources_are_bom_free() -> None:
    paths = (
        Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/video.py"),
        Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/video_board.py"),
        Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/video_story.py"),
        Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/video_replay.py"),
    )

    for path in paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf")
