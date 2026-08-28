"""Cinematic storyboard contract for Project 3."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

FRAME_WIDTH = 1080
FRAME_HEIGHT = 1080

VIDEO_SECONDS = 60
VIDEO_FPS = 30
VIDEO_FRAMES = VIDEO_SECONDS * VIDEO_FPS


@dataclass(
    frozen=True,
    slots=True,
)
class StorySegment:
    """Frozen narrative segment."""

    key: str
    start_second: float
    end_second: float
    objective: str
    visual_hook: str


STORY_SEGMENTS = (
    StorySegment(
        key="opening",
        start_second=0.0,
        end_second=7.0,
        objective=("Create immediate curiosity through active gameplay."),
        visual_hook=("dice → movement → purchase → build → rent → liquidity shock"),
    ),
    StorySegment(
        key="strategy_intro",
        start_second=7.0,
        end_second=14.0,
        objective=("Introduce four strategy personalities while gameplay continues."),
        visual_hook=("four pieces + reserve gauges + different purchase behavior"),
    ),
    StorySegment(
        key="representative_game",
        start_second=14.0,
        end_second=31.0,
        objective=("Tell one representative capital-allocation mini-story."),
        visual_hook=("purchase → ownership → development → rent → survival pressure"),
    ),
    StorySegment(
        key="scale",
        start_second=31.0,
        end_second=39.0,
        objective=("Transform one game into statistical evidence."),
        visual_hook=("single board zooms into many simulations → 10,000 counter"),
    ),
    StorySegment(
        key="leaderboard",
        start_second=39.0,
        end_second=50.0,
        objective=("Reveal relative performance without prematurely declaring a winner."),
        visual_hook=("bars race into place + confidence intervals"),
    ),
    StorySegment(
        key="risk_reward",
        start_second=50.0,
        end_second=55.0,
        objective=("Show why raw win rate is not the whole story."),
        visual_hook=("win rate vs bankruptcy vs median cash"),
    ),
    StorySegment(
        key="summary",
        start_second=55.0,
        end_second=60.0,
        objective=("Deliver statistically defensible conclusion and technical proof."),
        visual_hook=("winner/tie interpretation + seed + game count + disclaimer"),
    ),
)


@dataclass(
    frozen=True,
    slots=True,
)
class PreviewMoment:
    """One representative storyboard keyframe."""

    key: str
    second: float
    meaning: str


PREVIEW_MOMENTS = (
    PreviewMoment(
        key="01_hook_race",
        second=0.0,
        meaning="Dice launch four strategies into an active board.",
    ),
    PreviewMoment(
        key="02_hook_rent",
        second=3.0,
        meaning="Large rent payment creates immediate conflict.",
    ),
    PreviewMoment(
        key="03_hook_liquidity",
        second=6.0,
        meaning="Liquidity collapses and the central question appears.",
    ),
    PreviewMoment(
        key="04_strategy_gameplay",
        second=10.0,
        meaning="Four strategy identities appear during play.",
    ),
    PreviewMoment(
        key="05_purchase",
        second=15.0,
        meaning="Representative-game property purchase.",
    ),
    PreviewMoment(
        key="06_build",
        second=22.0,
        meaning="Ownership develops into higher rent exposure.",
    ),
    PreviewMoment(
        key="07_survival",
        second=28.0,
        meaning="Bankruptcy and liquidity protection diverge.",
    ),
    PreviewMoment(
        key="08_scale",
        second=34.0,
        meaning="Single-game story expands into Monte Carlo evidence.",
    ),
    PreviewMoment(
        key="09_counter",
        second=38.0,
        meaning="Tournament reaches 10,000 games.",
    ),
    PreviewMoment(
        key="10_leaderboard",
        second=44.0,
        meaning="Win-rate ranking and uncertainty appear.",
    ),
    PreviewMoment(
        key="11_risk_reward",
        second=52.0,
        meaning="Risk/reward metrics contextualize win rate.",
    ),
    PreviewMoment(
        key="12_result",
        second=57.0,
        meaning="Statistically supported conclusion revealed.",
    ),
    PreviewMoment(
        key="13_footer",
        second=59.5,
        meaning="Technical proof and disclaimer.",
    ),
)


def validate_storyboard_contract() -> None:
    """Validate contiguous 60-second narrative contract."""

    assert len(STORY_SEGMENTS) == 7

    assert STORY_SEGMENTS[0].start_second == 0.0

    assert STORY_SEGMENTS[-1].end_second == 60.0

    for first, second in pairwise(STORY_SEGMENTS):
        assert first.end_second == second.start_second

    assert len(PREVIEW_MOMENTS) == 13

    assert sum(moment.second <= 15.0 for moment in PREVIEW_MOMENTS) >= 5
