"""Deterministic Project 3 engine tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
    load_config,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    EventType,
    GamePhase,
    StrategyAction,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.engine import (
    DecisionContext,
    DecisionValidationError,
    simulate_game,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    BoardDefinition,
    BoardSpace,
    BuildDecision,
    PropertyDefinition,
    PurchaseDecision,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.randomness import (
    DiceRoller,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.serialization import (
    dumps,
)

CONFIG = Path("configs/p02_monopoly_ai.yaml")

SEATS = (
    StrategyId.COLLECTOR,
    StrategyId.SPECIALIST,
    StrategyId.CASH_PROTECTOR,
    StrategyId.AGGRESSIVE_BUILDER,
)


def _config() -> MonopolyConfig:
    return load_config(CONFIG)


@dataclass(slots=True)
class BuyEverythingProvider:
    """Engine-test provider, not a canonical strategy."""

    build: bool = False

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        del space

        if context.player.cash >= asset.purchase_price:
            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code="test_buy",
                asset_id=asset.asset_id,
            )

        return PurchaseDecision(
            action=StrategyAction.PASS,
            reason_code="cannot_afford",
        )

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        del context
        del board

        return (
            BuildDecision(
                action=StrategyAction.HOLD_CASH,
                reason_code="test_hold",
            ),
        )


def test_dice_same_seed_is_reproducible() -> None:
    first = DiceRoller(123)

    second = DiceRoller(123)

    assert [first.roll() for _ in range(20)] == [second.roll() for _ in range(20)]


def test_dice_different_seed_diverges() -> None:
    first = DiceRoller(123)

    second = DiceRoller(124)

    assert [first.roll() for _ in range(20)] != [second.roll() for _ in range(20)]


def test_passive_game_always_terminates() -> None:
    result = simulate_game(
        config=_config(),
        game_index=0,
        game_seed=100,
        seat_assignment=SEATS,
    )

    assert result.result.turns_played == 500

    assert result.result.termination_reason is GamePhase.TERMINATED_TURN_LIMIT


def test_same_seed_reproduces_entire_game() -> None:
    first = simulate_game(
        config=_config(),
        game_index=3,
        game_seed=999,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    second = simulate_game(
        config=_config(),
        game_index=3,
        game_seed=999,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    assert dumps(first.result) == dumps(second.result)

    assert dumps(first.final_state) == dumps(second.final_state)

    assert dumps(first.events) == dumps(second.events)

    assert dumps(first.snapshots) == dumps(second.snapshots)


def test_different_seed_changes_event_trace() -> None:
    first = simulate_game(
        config=_config(),
        game_index=1,
        game_seed=111,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    second = simulate_game(
        config=_config(),
        game_index=2,
        game_seed=222,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    dice_first = [
        event.metadata for event in first.events if event.event_type is EventType.DICE_ROLL
    ]

    dice_second = [
        event.metadata for event in second.events if event.event_type is EventType.DICE_ROLL
    ]

    assert dice_first != dice_second


def test_event_indices_are_contiguous() -> None:
    result = simulate_game(
        config=_config(),
        game_index=1,
        game_seed=321,
        seat_assignment=SEATS,
    )

    assert [event.event_index for event in result.events] == list(range(len(result.events)))


def test_all_finishing_positions_are_unique() -> None:
    result = simulate_game(
        config=_config(),
        game_index=0,
        game_seed=44,
        seat_assignment=SEATS,
    )

    positions = sorted(result.result.finishing_positions.values())

    assert positions == [
        1,
        2,
        3,
        4,
    ]


def test_buy_provider_creates_unique_ownership() -> None:
    result = simulate_game(
        config=_config(),
        game_index=5,
        game_seed=98765,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    owners = {}

    for asset_id, state in result.final_state.properties.items():
        if state.owner_id is None:
            continue

        assert asset_id not in owners

        owners[asset_id] = state.owner_id


def test_house_counts_are_always_legal() -> None:
    result = simulate_game(
        config=_config(),
        game_index=8,
        game_seed=8123,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    assert all(
        0 <= property_state.house_count <= 4
        for property_state in result.final_state.properties.values()
    )


def test_bankrupt_players_do_not_retain_assets() -> None:
    result = simulate_game(
        config=_config(),
        game_index=9,
        game_seed=9123,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    for player in result.final_state.players.values():
        if player.bankrupt:
            assert not player.owned_asset_ids


def test_game_state_is_serializable() -> None:
    result = simulate_game(
        config=_config(),
        game_index=10,
        game_seed=10123,
        seat_assignment=SEATS,
        decision_provider=BuyEverythingProvider(),
    )

    text = dumps(result.final_state)

    assert '"game_id"' in text
    assert '"players"' in text
    assert '"properties"' in text


def test_winner_resolution_is_deterministic() -> None:
    winners = {
        simulate_game(
            config=_config(),
            game_index=0,
            game_seed=777,
            seat_assignment=SEATS,
        ).result.winner_player_id
        for _ in range(5)
    }

    assert len(winners) == 1


def test_engine_rejects_wrong_purchase_target() -> None:
    class InvalidProvider:
        def purchase_decision(
            self,
            *,
            context: DecisionContext,
            space: BoardSpace,
            asset: PropertyDefinition,
        ) -> PurchaseDecision:
            del context
            del space
            del asset

            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code="wrong_target",
                asset_id="NOT_THE_LANDED_ASSET",
            )

        def build_decisions(
            self,
            *,
            context: DecisionContext,
            board: BoardDefinition,
        ) -> tuple[BuildDecision, ...]:
            del context
            del board

            return ()

    with pytest.raises(DecisionValidationError):
        simulate_game(
            config=_config(),
            game_index=11,
            game_seed=10,
            seat_assignment=SEATS,
            decision_provider=InvalidProvider(),
        )
