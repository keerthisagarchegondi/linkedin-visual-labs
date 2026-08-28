"""Project 3 strategy-policy tests."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest

from linkedin_visual_labs.projects.p02_monopoly_ai.board import (
    build_board,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
    load_config,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    StrategyAction,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.engine import (
    DecisionContext,
    DecisionValidationError,
    GameEngine,
    PlayerView,
    PropertyView,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    BoardDefinition,
    BoardSpace,
    BuildDecision,
    PropertyDefinition,
    PurchaseDecision,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.strategies import (
    AggressiveBuilderPolicy,
    CashProtectorPolicy,
    CollectorPolicy,
    SpecialistPolicy,
    StrategyRegistryProvider,
    build_strategy_registry,
)

CONFIG = Path("configs/p02_monopoly_ai.yaml")


def _config() -> MonopolyConfig:
    return load_config(CONFIG)


def _registry() -> StrategyRegistryProvider:
    return build_strategy_registry(_config())


def _board() -> BoardDefinition:
    return build_board(_config())


def _context(
    *,
    strategy_id: StrategyId,
    cash: int,
    owned: tuple[str, ...] = (),
    ownership: Mapping[
        str,
        str | None,
    ]
    | None = None,
    houses: Mapping[
        str,
        int,
    ]
    | None = None,
) -> DecisionContext:
    board = _board()

    owner_values = ownership if ownership is not None else {}

    house_values = houses if houses is not None else {}

    properties = {
        space.asset.asset_id: PropertyView(
            asset_id=space.asset.asset_id,
            owner_id=owner_values.get(space.asset.asset_id),
            house_count=house_values.get(
                space.asset.asset_id,
                0,
            ),
        )
        for space in board.spaces
        if space.asset is not None
    }

    return DecisionContext(
        turn_number=50,
        player=PlayerView(
            player_id="player_0",
            strategy_id=strategy_id,
            seat_index=0,
            cash=cash,
            position=0,
            owned_asset_ids=owned,
            bankrupt=False,
        ),
        properties=MappingProxyType(properties),
    )


def _asset(
    asset_id: str,
) -> tuple[
    BoardSpace,
    PropertyDefinition,
]:
    board = _board()

    for space in board.spaces:
        if space.asset is not None and space.asset.asset_id == asset_id:
            return (
                space,
                space.asset,
            )

    raise AssertionError(f"unknown test asset: {asset_id}")


def test_registry_loads_four_independent_policies() -> None:
    registry = _registry()

    assert isinstance(
        registry.policy_for(StrategyId.COLLECTOR),
        CollectorPolicy,
    )

    assert isinstance(
        registry.policy_for(StrategyId.SPECIALIST),
        SpecialistPolicy,
    )

    assert isinstance(
        registry.policy_for(StrategyId.CASH_PROTECTOR),
        CashProtectorPolicy,
    )

    assert isinstance(
        registry.policy_for(StrategyId.AGGRESSIVE_BUILDER),
        AggressiveBuilderPolicy,
    )


def test_collector_buys_broadly() -> None:
    registry = _registry()

    policy = registry.policy_for(StrategyId.COLLECTOR)

    context = _context(
        strategy_id=StrategyId.COLLECTOR,
        cash=1500,
    )

    decisions = []

    for asset_id in (
        "P01",
        "P08",
        "T01",
        "U01",
    ):
        space, asset = _asset(asset_id)

        decisions.append(
            policy.purchase_decision(
                context=context,
                space=space,
                asset=asset,
            )
        )

    assert all(decision.action is StrategyAction.BUY for decision in decisions)


def test_specialist_prioritizes_selected_group() -> None:
    registry = _registry()

    policy = registry.policy_for(StrategyId.SPECIALIST)

    assert isinstance(
        policy,
        SpecialistPolicy,
    )

    context = _context(
        strategy_id=StrategyId.SPECIALIST,
        cash=900,
    )

    _, preferred = _asset("P09")

    _, low_priority = _asset("P21")

    preferred_score = policy.purchase_priority_score(
        context=context,
        asset=preferred,
    )

    low_score = policy.purchase_priority_score(
        context=context,
        asset=low_priority,
    )

    assert preferred_score > low_score


def test_specialist_passes_low_priority_when_capital_is_constrained() -> None:
    registry = _registry()

    policy = registry.policy_for(StrategyId.SPECIALIST)

    context = _context(
        strategy_id=StrategyId.SPECIALIST,
        cash=900,
    )

    space, asset = _asset("P21")

    decision = policy.purchase_decision(
        context=context,
        space=space,
        asset=asset,
    )

    assert decision.action is StrategyAction.PASS


def test_cash_protector_respects_large_reserve() -> None:
    registry = _registry()

    policy = registry.policy_for(StrategyId.CASH_PROTECTOR)

    context = _context(
        strategy_id=StrategyId.CASH_PROTECTOR,
        cash=1000,
    )

    space, asset = _asset("P17")

    decision = policy.purchase_decision(
        context=context,
        space=space,
        asset=asset,
    )

    assert decision.action is StrategyAction.PASS


def test_aggressive_builder_accepts_lower_liquidity() -> None:
    registry = _registry()

    aggressive = registry.policy_for(StrategyId.AGGRESSIVE_BUILDER)

    cash_protector = registry.policy_for(StrategyId.CASH_PROTECTOR)

    aggressive_context = _context(
        strategy_id=StrategyId.AGGRESSIVE_BUILDER,
        cash=600,
    )

    cash_context = _context(
        strategy_id=StrategyId.CASH_PROTECTOR,
        cash=600,
    )

    space, asset = _asset("P11")

    aggressive_decision = aggressive.purchase_decision(
        context=aggressive_context,
        space=space,
        asset=asset,
    )

    cash_decision = cash_protector.purchase_decision(
        context=cash_context,
        space=space,
        asset=asset,
    )

    assert aggressive_decision.action is StrategyAction.BUY

    assert cash_decision.action is StrategyAction.PASS


def test_aggressive_builder_develops_more_than_collector() -> None:
    registry = _registry()

    ownership = {
        "P01": "player_0",
        "P02": "player_0",
    }

    houses = {
        "P01": 0,
        "P02": 0,
    }

    collector_context = _context(
        strategy_id=StrategyId.COLLECTOR,
        cash=2000,
        owned=(
            "P01",
            "P02",
        ),
        ownership=ownership,
        houses=houses,
    )

    aggressive_context = _context(
        strategy_id=StrategyId.AGGRESSIVE_BUILDER,
        cash=2000,
        owned=(
            "P01",
            "P02",
        ),
        ownership=ownership,
        houses=houses,
    )

    board = _board()

    collector = registry.policy_for(StrategyId.COLLECTOR)

    aggressive = registry.policy_for(StrategyId.AGGRESSIVE_BUILDER)

    collector_builds = [
        decision
        for decision in collector.build_decisions(
            context=collector_context,
            board=board,
        )
        if decision.action is StrategyAction.BUILD
    ]

    aggressive_builds = [
        decision
        for decision in aggressive.build_decisions(
            context=aggressive_context,
            board=board,
        )
        if decision.action is StrategyAction.BUILD
    ]

    assert len(collector_builds) == 1

    assert len(aggressive_builds) == 4


def test_policy_context_is_runtime_read_only() -> None:
    context = _context(
        strategy_id=StrategyId.COLLECTOR,
        cash=1500,
    )

    with pytest.raises(TypeError):
        context.properties["P01"] = PropertyView(  # type: ignore[index]
            asset_id="P01",
            owner_id="attacker",
            house_count=4,
        )


def test_policy_player_view_is_immutable() -> None:
    context = _context(
        strategy_id=StrategyId.COLLECTOR,
        cash=1500,
    )

    with pytest.raises(AttributeError):
        context.player.cash = 0  # type: ignore[misc]


def test_same_input_returns_same_purchase_decision() -> None:
    registry = _registry()

    policy = registry.policy_for(StrategyId.SPECIALIST)

    context = _context(
        strategy_id=StrategyId.SPECIALIST,
        cash=1500,
    )

    space, asset = _asset("P09")

    first = policy.purchase_decision(
        context=context,
        space=space,
        asset=asset,
    )

    second = policy.purchase_decision(
        context=context,
        space=space,
        asset=asset,
    )

    assert first == second


def test_engine_rejects_unaffordable_buy() -> None:
    class IllegalBuyProvider:
        def purchase_decision(
            self,
            *,
            context: DecisionContext,
            space: BoardSpace,
            asset: PropertyDefinition,
        ) -> PurchaseDecision:
            del context
            del space

            return PurchaseDecision(
                action=StrategyAction.BUY,
                reason_code="illegal",
                asset_id=asset.asset_id,
            )

        def build_decisions(
            self,
            *,
            context: DecisionContext,
            board: object,
        ) -> tuple[BuildDecision, ...]:
            del context
            del board

            return ()

    config = _config()

    engine = GameEngine(
        config=config,
        game_index=0,
        game_seed=42,
        seat_assignment=(
            StrategyId.COLLECTOR,
            StrategyId.SPECIALIST,
            StrategyId.CASH_PROTECTOR,
            StrategyId.AGGRESSIVE_BUILDER,
        ),
        decision_provider=IllegalBuyProvider(),
    )

    player = engine.state.players["player_0"]

    player.cash = 1

    asset = engine.asset_definitions["P01"]

    with pytest.raises(
        DecisionValidationError,
        match="cannot afford",
    ):
        engine._purchase(
            player,
            asset,
        )


def test_engine_rejects_illegal_build() -> None:
    config = _config()

    engine = GameEngine(
        config=config,
        game_index=0,
        game_seed=42,
        seat_assignment=(
            StrategyId.COLLECTOR,
            StrategyId.SPECIALIST,
            StrategyId.CASH_PROTECTOR,
            StrategyId.AGGRESSIVE_BUILDER,
        ),
        decision_provider=_registry(),
    )

    player = engine.state.players["player_0"]

    player.cash = 5000

    with pytest.raises(
        DecisionValidationError,
        match="does not own",
    ):
        engine._build_house(
            player,
            "P01",
        )
