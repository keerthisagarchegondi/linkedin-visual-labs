"""Domain-model construction and mutability tests."""

from dataclasses import FrozenInstanceError

import pytest

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    GamePhase,
    PropertyGroupId,
    SpaceType,
    StrategyAction,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    BoardDefinition,
    BoardSpace,
    BuildDecision,
    GameState,
    PlayerState,
    PropertyDefinition,
    PropertyState,
    PurchaseDecision,
)


def test_purchase_decision_rejects_build() -> None:
    with pytest.raises(
        ValueError,
        match="BUY or PASS",
    ):
        PurchaseDecision(
            action=StrategyAction.BUILD,
            reason_code="invalid",
        )


def test_buy_requires_asset() -> None:
    with pytest.raises(
        ValueError,
        match="asset_id",
    ):
        PurchaseDecision(
            action=StrategyAction.BUY,
            reason_code="missing",
        )


def test_build_requires_property() -> None:
    with pytest.raises(
        ValueError,
        match="property_id",
    ):
        BuildDecision(
            action=StrategyAction.BUILD,
            reason_code="missing",
        )


def test_property_state_rejects_illegal_house_count() -> None:
    with pytest.raises(
        ValueError,
        match="exceed four",
    ):
        PropertyState(
            asset_id="P01",
            house_count=5,
        )


def test_immutable_definition_cannot_mutate() -> None:
    asset = PropertyDefinition(
        asset_id="P01",
        board_index=1,
        name="Harbor Lane",
        space_type=SpaceType.PROPERTY,
        purchase_price=80,
        base_rent=8,
        group_id=PropertyGroupId("G1"),
        house_cost=50,
    )

    space = BoardSpace(
        index=0,
        space_id="JAIL",
        name="Jail",
        space_type=SpaceType.JAIL,
    )

    board = BoardDefinition(
        spaces=(space,),
        jail_index=0,
    )

    with pytest.raises(FrozenInstanceError):
        board.jail_index = 1  # type: ignore[misc]

    assert asset.purchase_price == 80


def test_game_state_is_explicitly_mutable() -> None:
    player = PlayerState(
        player_id="p0",
        strategy_id=StrategyId.COLLECTOR,
        seat_index=0,
        cash=1500,
    )

    state = GameState(
        game_id="g0",
        game_index=0,
        game_seed=42,
        phase=GamePhase.SETUP,
        turn_number=0,
        active_player_index=0,
        players={
            "p0": player,
        },
        properties={},
    )

    state.turn_number = 1
    state.players["p0"].cash = 1400

    assert state.turn_number == 1
    assert state.players["p0"].cash == 1400
