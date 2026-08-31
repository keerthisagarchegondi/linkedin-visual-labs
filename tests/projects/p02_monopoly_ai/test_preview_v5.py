"""Tests for Project 3 V5 cinematic preview laboratory."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai import preview_v5
from linkedin_visual_labs.projects.p02_monopoly_ai.preview_v5 import (
    HEIGHT,
    PIPS,
    PREVIEW_RENDERERS,
    TYPE_BODY,
    TYPE_DISPLAY,
    TYPE_HEADLINE,
    TYPE_HERO,
    TYPE_LABEL,
    TYPE_SMALL,
    WIDTH,
    load_runtime,
    ranking,
)


def test_v5_preview_contract() -> None:
    assert WIDTH == 1080
    assert HEIGHT == 1080

    assert tuple(PREVIEW_RENDERERS) == (
        "01_dice_hit",
        "02_piece_race",
        "03_property_purchase",
        "04_house_build",
        "05_rent_hit",
        "06_cash_crash",
        "07_survival_question",
        "08_strategy_personalities",
        "09_gameplay_story",
        "10_scale_10000",
        "11_leaderboard_ci",
        "12_risk_reward",
        "13_result",
    )


def test_v5_uses_conventional_dice_pips() -> None:
    assert set(PIPS) == {
        1,
        2,
        3,
        4,
        5,
        6,
    }

    for value in range(
        1,
        7,
    ):
        assert len(PIPS[value]) == value


def test_v5_runtime_is_real_and_validated() -> None:
    runtime = load_runtime()

    assert runtime.turns
    assert runtime.story.dice_turn.dice is not None

    assert len(runtime.metrics) == 4

    for metric in runtime.metrics:
        assert 0.0 <= metric.win_rate <= 1.0

        assert 0.0 <= metric.bankruptcy_rate <= 1.0

        assert 0.0 <= metric.ci_lower <= metric.ci_upper <= 1.0


def test_v5_ranking_uses_actual_metrics() -> None:
    runtime = load_runtime()

    rows = ranking(runtime)

    assert rows[0].win_rate == max(metric.win_rate for metric in runtime.metrics)


def test_v5_source_is_bom_free() -> None:
    path = Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/preview_v5.py")

    assert not path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_v5_typography_floor() -> None:
    assert TYPE_HERO >= 70
    assert TYPE_DISPLAY >= 54
    assert TYPE_HEADLINE >= 42
    assert TYPE_LABEL >= 22
    assert TYPE_BODY >= 18
    assert TYPE_SMALL >= 15


def test_v5_has_exactly_thirteen_renderers() -> None:
    assert len(PREVIEW_RENDERERS) == 13


def test_v5_replay_asset_mapping_is_purchase_derived_and_unique() -> None:
    mapping = preview_v5.replay_asset_index_map()

    assert mapping

    assert len(mapping) == len(set(mapping))

    assert all(0 <= index < 40 for index in mapping.values())


def test_v5_selected_action_shots_use_real_semantic_events() -> None:
    runtime = preview_v5.load_runtime()

    purchase = runtime.story.purchase_turn
    build = runtime.story.build_turn
    rent = runtime.story.rent_turn
    bankruptcy = runtime.story.survival_turn

    assert preview_v5.actual_purchase_events(purchase)

    assert preview_v5.actual_build_events(build)

    assert preview_v5.actual_rent_events(rent)

    assert preview_v5.actual_bankruptcy_events(bankruptcy)


def test_v5_build_event_is_house_built_not_build_decision() -> None:
    runtime = preview_v5.load_runtime()

    event = preview_v5.build_event(runtime.story.build_turn)

    assert preview_v5.semantic_event_type(event) == "HOUSE_BUILT"

    amount = getattr(
        event,
        "amount",
        None,
    )

    assert isinstance(
        amount,
        (int, float),
    )

    assert amount > 0

    houses_after = getattr(
        event,
        "houses_after",
        None,
    )

    assert isinstance(
        houses_after,
        int,
    )

    assert houses_after >= 1


def test_v5_action_shots_resolve_real_named_properties() -> None:
    runtime = preview_v5.load_runtime()

    cases = (
        (
            preview_v5.purchase_space_index(runtime.story.purchase_turn),
            preview_v5.purchase_property_name(runtime.story.purchase_turn),
        ),
        (
            preview_v5.build_space_index(runtime.story.build_turn),
            preview_v5.build_property_name(runtime.story.build_turn),
        ),
        (
            preview_v5.rent_space_index(runtime.story.rent_turn),
            preview_v5.rent_property_name(runtime.story.rent_turn),
        ),
    )

    for index, name in cases:
        assert 0 <= index < 40

        assert name
        assert name != "BOARD PROPERTY"
        assert not name.startswith("SPACE ")


def test_v5_frozen_story_sequence_is_strictly_chronological() -> None:
    runtime = preview_v5.load_runtime()

    beats = runtime.story.narrative_beats

    assert tuple(beat.label for beat in beats) == (
        "ACQUIRE",
        "EXPAND",
        "BUILD",
        "RENT",
        "CASH SHOCK",
        "BANKRUPTCY",
    )

    indexes = [
        preview_v5.turn_position(
            runtime.turns,
            beat.turn,
        )
        for beat in beats
    ]

    assert indexes == sorted(indexes)

    assert len(set(indexes)) == 6


def test_v5_selected_semantic_contract_matches_representative_game() -> None:
    runtime = preview_v5.load_runtime()

    assert preview_v5.purchase_property_name(runtime.story.purchase_turn) == "Gold Avenue"

    assert preview_v5.build_property_name(runtime.story.build_turn) == "Skyline Drive"

    assert preview_v5.rent_property_name(runtime.story.rent_turn) == "Emerald Avenue"


def test_v5_piece_race_route_projects_inside_frame() -> None:
    runtime = preview_v5.load_runtime()

    turn = runtime.story.move_turn

    route = preview_v5.movement_route_indices(turn)

    crop = preview_v5.board_crop_for_spaces(
        route,
        minimum_fraction=0.42,
        padding_fraction=0.14,
    )

    points = [
        preview_v5.project_board_space_to_crop(
            index,
            crop,
        )
        for index in route
    ]

    assert len(points) >= 2

    assert all(
        -1.0 <= x <= preview_v5.WIDTH + 1.0 and -1.0 <= y <= preview_v5.HEIGHT + 1.0
        for x, y in points
    )


def test_v5_house_overlay_property_is_skyline_drive() -> None:
    runtime = preview_v5.load_runtime()

    turn = runtime.story.build_turn

    assert preview_v5.build_property_name(turn) == "Skyline Drive"

    assert preview_v5.semantic_event_type(preview_v5.build_event(turn)) == "HOUSE_BUILT"


def test_v5_story_display_details_match_event_specific_truth() -> None:
    runtime = preview_v5.load_runtime()

    beats = runtime.story.narrative_beats

    assert tuple(beat.label for beat in beats) == (
        "ACQUIRE",
        "EXPAND",
        "BUILD",
        "RENT",
        "CASH SHOCK",
        "BANKRUPTCY",
    )

    details = tuple(preview_v5.story_beat_detail(beat) for beat in beats)

    assert details[0] == "Gold Avenue"
    assert details[1] == "Skyline Tower"
    assert details[2] == "Skyline Drive"
    assert details[3] == "Emerald Avenue"
    assert details[4] == "$707 -> $659"
    assert details[5] == "RENT BANKRUPTCY"


def test_v5_story_build_detail_uses_house_asset_not_turn_landing() -> None:
    runtime = preview_v5.load_runtime()

    build_beat = runtime.story.narrative_beats[2]

    assert build_beat.label == "BUILD"

    assert preview_v5.story_beat_detail(build_beat) == preview_v5.build_property_name(
        build_beat.turn
    )

    assert (
        preview_v5.story_beat_detail(build_beat)
        != preview_v5.board_space_names()[build_beat.turn.to_position % 40]
    )


def test_v5_story_rent_detail_uses_rent_asset_not_generic_turn_label() -> None:
    runtime = preview_v5.load_runtime()

    rent_beat = runtime.story.narrative_beats[3]

    assert rent_beat.label == "RENT"

    assert preview_v5.story_beat_detail(rent_beat) == "Emerald Avenue"
