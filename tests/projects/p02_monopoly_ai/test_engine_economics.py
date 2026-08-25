"""Direct economic invariant tests for the Project 3 engine."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    load_config,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.engine import (
    GameEngine,
    PassiveDecisionProvider,
)

CONFIG = Path("configs/p02_monopoly_ai.yaml")

SEATS = (
    StrategyId.COLLECTOR,
    StrategyId.SPECIALIST,
    StrategyId.CASH_PROTECTOR,
    StrategyId.AGGRESSIVE_BUILDER,
)


def _engine() -> GameEngine:
    return GameEngine(
        config=load_config(CONFIG),
        game_index=0,
        game_seed=12345,
        seat_assignment=SEATS,
        decision_provider=PassiveDecisionProvider(),
    )


def test_go_award_is_exactly_200() -> None:
    engine = _engine()

    player = engine.state.players["player_0"]

    player.position = 39
    player.cash = 1000

    engine._move(
        player,
        2,
    )

    assert player.position == 1
    assert player.cash == 1200


def test_base_rent_moves_cash_tenant_to_owner() -> None:
    engine = _engine()

    owner = engine.state.players["player_0"]

    tenant = engine.state.players["player_1"]

    asset = engine.asset_definitions["P01"]

    state = engine.state.properties["P01"]

    state.owner_id = owner.player_id

    owner.owned_asset_ids.append("P01")

    owner.cash = 1000
    tenant.cash = 1000

    rent = engine._asset_rent(
        asset,
        dice_total=7,
    )

    assert rent == asset.base_rent

    engine._transfer_required_payment(
        payer=tenant,
        amount=rent,
        creditor=owner,
        reason="rent",
    )

    assert tenant.cash == (1000 - rent)

    assert owner.cash == (1000 + rent)

    assert tenant.total_rent_paid == rent

    assert owner.total_rent_collected == rent


def test_complete_group_doubles_unimproved_rent() -> None:
    engine = _engine()

    owner = engine.state.players["player_0"]

    for asset_id in (
        "P01",
        "P02",
    ):
        engine.state.properties[asset_id].owner_id = owner.player_id

        owner.owned_asset_ids.append(asset_id)

    asset = engine.asset_definitions["P01"]

    assert engine._asset_rent(
        asset,
        dice_total=7,
    ) == (asset.base_rent * 2)


def test_house_multiplier_applies() -> None:
    engine = _engine()

    owner = engine.state.players["player_0"]

    for asset_id in (
        "P01",
        "P02",
    ):
        engine.state.properties[asset_id].owner_id = owner.player_id

        owner.owned_asset_ids.append(asset_id)

    engine.state.properties["P01"].house_count = 1

    asset = engine.asset_definitions["P01"]

    assert engine._asset_rent(
        asset,
        dice_total=7,
    ) == (asset.base_rent * 5)


def test_insufficient_rent_causes_bankruptcy_and_transfer() -> None:
    engine = _engine()

    creditor = engine.state.players["player_0"]

    payer = engine.state.players["player_1"]

    engine.state.properties["P01"].owner_id = payer.player_id

    payer.owned_asset_ids.append("P01")

    payer.cash = 5

    engine._transfer_required_payment(
        payer=payer,
        amount=50,
        creditor=creditor,
        reason="rent",
    )

    assert payer.bankrupt is True
    assert payer.cash == 0

    assert not payer.owned_asset_ids

    assert engine.state.properties["P01"].owner_id == creditor.player_id

    assert "P01" in creditor.owned_asset_ids


def test_bank_bankruptcy_releases_assets_and_houses() -> None:
    engine = _engine()

    player = engine.state.players["player_0"]

    engine.state.properties["P01"].owner_id = player.player_id

    engine.state.properties["P01"].house_count = 2

    player.owned_asset_ids.append("P01")

    player.cash = 1

    engine._transfer_required_payment(
        payer=player,
        amount=100,
        creditor=None,
        reason="tax",
    )

    assert player.bankrupt

    property_state = engine.state.properties["P01"]

    assert property_state.owner_id is None
    assert property_state.house_count == 0


def test_jail_entry_and_deterministic_exit() -> None:
    engine = _engine()

    player = engine.state.players["player_0"]

    engine._enter_jail(player)

    assert player.position == 10
    assert player.jail.turns_remaining == 1

    engine._execute_turn(player)

    assert player.jail.turns_remaining == 0


def test_even_development_prevents_unbalanced_build() -> None:
    engine = _engine()

    player = engine.state.players["player_0"]

    for asset_id in (
        "P01",
        "P02",
    ):
        engine.state.properties[asset_id].owner_id = player.player_id

        player.owned_asset_ids.append(asset_id)

    player.cash = 5000

    engine._build_house(
        player,
        "P01",
    )

    assert engine.state.properties["P01"].house_count == 1
