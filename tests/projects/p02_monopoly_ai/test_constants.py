"""Enum contract tests."""

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    EventType,
    GamePhase,
    SpaceType,
    StrategyAction,
    StrategyId,
)


def test_space_types_are_complete() -> None:
    assert {item.value for item in SpaceType} == {
        "GO",
        "PROPERTY",
        "TRANSIT",
        "UTILITY",
        "CHANCE",
        "COMMUNITY",
        "TAX",
        "JAIL",
        "FREE_REST",
        "GO_TO_JAIL",
    }


def test_strategy_ids_are_complete() -> None:
    assert {item.value for item in StrategyId} == {
        "collector",
        "specialist",
        "cash_protector",
        "aggressive_builder",
    }


def test_strategy_actions_are_complete() -> None:
    assert {item.value for item in StrategyAction} == {
        "BUY",
        "PASS",
        "BUILD",
        "HOLD_CASH",
    }


def test_game_phases_are_complete() -> None:
    assert {item.value for item in GamePhase} == {
        "SETUP",
        "ACTIVE",
        "TERMINATED_BANKRUPTCY",
        "TERMINATED_TURN_LIMIT",
    }


def test_event_types_cover_replay_contract() -> None:
    assert EventType.DICE_ROLL.value == "DICE_ROLL"
    assert EventType.ASSET_PURCHASED.value == "ASSET_PURCHASED"
    assert EventType.HOUSE_BUILT.value == "HOUSE_BUILT"
    assert EventType.BANKRUPTCY.value == "BANKRUPTCY"
