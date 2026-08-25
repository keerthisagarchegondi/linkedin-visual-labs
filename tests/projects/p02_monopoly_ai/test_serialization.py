"""Deterministic serialization tests."""

import json

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    GamePhase,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    GameState,
    PlayerState,
    PropertyState,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.serialization import (
    dumps,
    loads_game_state,
)


def _state() -> GameState:
    player = PlayerState(
        player_id="p0",
        strategy_id=StrategyId.COLLECTOR,
        seat_index=0,
        cash=1500,
    )

    property_state = PropertyState(
        asset_id="P01",
    )

    return GameState(
        game_id="game-0",
        game_index=0,
        game_seed=123456,
        phase=GamePhase.ACTIVE,
        turn_number=4,
        active_player_index=0,
        players={
            "p0": player,
        },
        properties={
            "P01": property_state,
        },
        event_index=9,
    )


def test_serialization_is_deterministic() -> None:
    state = _state()

    first = dumps(state)

    second = dumps(state)

    assert first == second

    parsed = json.loads(first)

    assert parsed["game_id"] == "game-0"


def test_game_state_round_trip() -> None:
    original = _state()

    serialized = dumps(original)

    restored = loads_game_state(serialized)

    assert dumps(restored) == serialized

    assert restored.phase is GamePhase.ACTIVE

    assert restored.players["p0"].strategy_id is StrategyId.COLLECTOR


def test_serialization_sorts_mapping_keys() -> None:
    state = _state()

    state.properties["A"] = PropertyState(asset_id="A")

    text = dumps(state)

    assert text.index('"A"') < text.index('"P01"')
