"""Project 2 Revised Step 9R video regression tests."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape.video import (
    CITY_SCHEDULE,
    DIJKSTRA_HEIGHT,
    DL_HEIGHT,
    DURATION_SECONDS,
    FPS,
    FRAME_COUNT,
    HEADING_HEIGHT,
    HEIGHT,
    METHOD_GEOMETRY,
    ML_HEIGHT,
    RESULT_HEIGHT,
    SWARM_SECTORS,
    WIDTH,
    expansion_cutoff,
    ffmpeg_command,
    frame_state_at,
    frontier_positions,
    load_video_assets,
    render_video_frame,
    swarm_centers,
    visible_search_edges,
)
from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    _city_payload,
)

DATA = Path("tests/fixtures/p04_zombie_escape/data")


def test_schedule_is_exactly_sixty_seconds() -> None:
    assert DURATION_SECONDS == 60.0
    assert FPS == 30
    assert FRAME_COUNT == 1800

    assert CITY_SCHEDULE == (
        (
            "new_york",
            8.0,
            23.0,
        ),
        (
            "chicago",
            23.0,
            38.0,
        ),
        (
            "phoenix",
            38.0,
            53.0,
        ),
    )


def test_city_geometry_is_exactly_1080_pixels() -> None:
    assert WIDTH == 1080
    assert HEIGHT == 1080

    assert HEADING_HEIGHT == 45
    assert DIJKSTRA_HEIGHT == 330
    assert ML_HEIGHT == 330
    assert DL_HEIGHT == 330
    assert RESULT_HEIGHT == 45

    assert HEADING_HEIGHT + DIJKSTRA_HEIGHT + ML_HEIGHT + DL_HEIGHT + RESULT_HEIGHT == HEIGHT

    assert METHOD_GEOMETRY["dijkstra"] == (
        45,
        330,
    )

    assert METHOD_GEOMETRY["ml"] == (
        375,
        330,
    )

    assert METHOD_GEOMETRY["dl"] == (
        705,
        330,
    )


def test_city_animation_phase_boundaries() -> None:
    base = frame_state_at(8.5)

    search = frame_state_at(12.0)

    complete = frame_state_at(18.0)

    rejected = frame_state_at(20.0)

    final_route = frame_state_at(21.25)

    result = frame_state_at(22.5)

    assert base.search_progress == 0.0

    assert 0.0 < search.search_progress < 1.0

    assert complete.search_progress == 1.0

    assert 0.1 < rejected.rejected_alpha < 1.0

    assert 0.0 < final_route.final_route_progress < 1.0

    assert result.final_route_progress == 1.0

    assert result.result_visible is True


def test_no_final_route_before_reveal_window() -> None:
    for seconds in (
        8.0,
        9.0,
        12.0,
        17.0,
        19.0,
        20.49,
    ):
        assert frame_state_at(seconds).final_route_progress == 0.0


def test_current_traces_cover_all_nine_city_method_pairs() -> None:
    assets = load_video_assets(DATA)

    assert len(assets.traces) == 9


def test_search_tree_growth_is_monotonic() -> None:
    assets = load_video_assets(DATA)

    for trace in assets.traces.values():
        early = visible_search_edges(
            trace,
            cutoff=expansion_cutoff(
                trace,
                0.25,
            ),
        )

        middle = visible_search_edges(
            trace,
            cutoff=expansion_cutoff(
                trace,
                0.50,
            ),
        )

        final = visible_search_edges(
            trace,
            cutoff=expansion_cutoff(
                trace,
                1.0,
            ),
        )

        assert len(early) <= len(middle) <= len(final)

        assert len(final) == len(trace.tree_edges)


def test_frontier_positions_come_from_trace_tree() -> None:
    assets = load_video_assets(DATA)

    for trace in assets.traces.values():
        cutoff = expansion_cutoff(
            trace,
            0.5,
        )

        frontier = frontier_positions(
            trace,
            cutoff=cutoff,
        )

        tree_children = {
            edge.child
            for edge in visible_search_edges(
                trace,
                cutoff=cutoff,
            )
        }

        assert set(frontier) <= tree_children


def test_swarm_contract_is_7_6_5() -> None:
    assets = load_video_assets(DATA)

    expected = {
        "new_york": 7,
        "chicago": 6,
        "phoenix": 5,
    }

    for city_id, count in expected.items():
        city = _city_payload(
            assets.cities,
            city_id,
        )

        centers = swarm_centers(
            city_id,
            city,
        )

        assert len(centers) == count

        assert len(SWARM_SECTORS[city_id]) == count


def test_current_city_and_overall_winners_are_data_driven() -> None:
    assets = load_video_assets(DATA)

    assert set(assets.city_results) == {
        "new_york",
        "chicago",
        "phoenix",
    }

    for result in assets.city_results.values():
        assert result.winner_method in {
            "dijkstra",
            "ml",
            "dl",
        }

    assert assets.overall_winner in {
        "dijkstra",
        "ml",
        "dl",
    }


def test_representative_frame_is_deterministic() -> None:
    assets = load_video_assets(DATA)

    frame_index = round(14.0 * FPS)

    first = render_video_frame(
        assets,
        frame_index=frame_index,
    )

    second = render_video_frame(
        assets,
        frame_index=frame_index,
    )

    assert first.size == (
        1080,
        1080,
    )

    assert second.size == (
        1080,
        1080,
    )

    assert first.tobytes() == second.tobytes()


def test_ffmpeg_contract_is_h264_yuv420p_30fps() -> None:
    command = ffmpeg_command(Path("dummy.mp4"))

    assert "libx264" in command
    assert "yuv420p" in command
    assert "rgb24" in command
    assert str(FPS) in command
