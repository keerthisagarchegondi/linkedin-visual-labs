"""Deterministic Project 3 game engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Protocol

from linkedin_visual_labs.projects.p02_monopoly_ai.board import (
    build_board,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    EventType,
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
    GameResult,
    GameState,
    PlayerState,
    PropertyDefinition,
    PropertyState,
    PurchaseDecision,
    TurnEvent,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.randomness import (
    RandomStreams,
    deterministic_tie_rank,
)


class EngineInvariantError(RuntimeError):
    """Raised when game state violates an engine invariant."""


class DecisionValidationError(RuntimeError):
    """Raised when a decision provider requests an illegal action."""


@dataclass(frozen=True, slots=True)
class PlayerView:
    player_id: str
    strategy_id: StrategyId
    seat_index: int
    cash: int
    position: int
    owned_asset_ids: tuple[str, ...]
    bankrupt: bool


@dataclass(frozen=True, slots=True)
class PropertyView:
    asset_id: str
    owner_id: str | None
    house_count: int


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """Read-only policy context."""

    turn_number: int
    player: PlayerView
    properties: Mapping[str, PropertyView]


class DecisionProvider(Protocol):
    """Interface used by Step 4 strategy policies."""

    def purchase_decision(
        self,
        *,
        context: DecisionContext,
        space: BoardSpace,
        asset: PropertyDefinition,
    ) -> PurchaseDecision:
        """Return BUY or PASS."""

    def build_decisions(
        self,
        *,
        context: DecisionContext,
        board: BoardDefinition,
    ) -> tuple[BuildDecision, ...]:
        """Return zero or more BUILD/HOLD_CASH decisions."""


class PassiveDecisionProvider:
    """Deterministic engine-only provider used for smoke simulations."""

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
            action=StrategyAction.PASS,
            reason_code="engine_passive_provider",
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
                reason_code="engine_passive_provider",
            ),
        )


@dataclass(frozen=True, slots=True)
class TurnSnapshot:
    turn_number: int
    active_player_index: int
    player_cash: tuple[
        tuple[str, int],
        ...,
    ]
    player_positions: tuple[
        tuple[str, int],
        ...,
    ]
    ownership: tuple[
        tuple[
            str,
            str | None,
            int,
        ],
        ...,
    ]


@dataclass(frozen=True, slots=True)
class SimulationResult:
    result: GameResult
    final_state: GameState
    events: tuple[TurnEvent, ...]
    snapshots: tuple[TurnSnapshot, ...]


@dataclass(frozen=True, slots=True)
class EventCard:
    event_id: str
    action: str
    target_space: int | None = None
    spaces: int | None = None
    amount: int | None = None


def _mapping(
    value: object,
    *,
    name: str,
) -> Mapping[object, object]:
    if not isinstance(
        value,
        Mapping,
    ):
        raise ValueError(f"{name} must be a mapping")

    return value


def _sequence(
    value: object,
    *,
    name: str,
) -> Sequence[object]:
    if not isinstance(
        value,
        Sequence,
    ) or isinstance(
        value,
        (
            str,
            bytes,
        ),
    ):
        raise ValueError(f"{name} must be a sequence")

    return value


def _integer(
    value: object,
    *,
    name: str,
) -> int:
    if not isinstance(
        value,
        int,
    ) or isinstance(
        value,
        bool,
    ):
        raise ValueError(f"{name} must be an integer")

    return value


def _text(
    value: object,
    *,
    name: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise ValueError(f"{name} must be a string")

    return value


class GameEngine:
    """Own all legal Project 3 game-state mutations."""

    def __init__(
        self,
        *,
        config: MonopolyConfig,
        game_index: int,
        game_seed: int,
        seat_assignment: tuple[
            StrategyId,
            StrategyId,
            StrategyId,
            StrategyId,
        ],
        decision_provider: DecisionProvider,
    ) -> None:
        if len(set(seat_assignment)) != 4:
            raise ValueError("seat assignment must contain four distinct strategies")

        self.config = config
        self.board = build_board(config)
        self.game_index = game_index
        self.game_seed = game_seed
        self.decision_provider = decision_provider
        self.random = RandomStreams(game_seed)

        self.events: list[TurnEvent] = []
        self.snapshots: list[TurnSnapshot] = []

        self.bankruptcy_event_indices: dict[
            str,
            int,
        ] = {}

        players = {
            f"player_{seat}": PlayerState(
                player_id=f"player_{seat}",
                strategy_id=strategy_id,
                seat_index=seat,
                cash=config.simulation.starting_cash,
            )
            for seat, strategy_id in enumerate(seat_assignment)
        }

        properties = {
            space.asset.asset_id: PropertyState(asset_id=space.asset.asset_id)
            for space in self.board.spaces
            if space.asset is not None
        }

        self.state = GameState(
            game_id=f"game_{game_index:05d}",
            game_index=game_index,
            game_seed=game_seed,
            phase=GamePhase.ACTIVE,
            turn_number=0,
            active_player_index=0,
            players=players,
            properties=properties,
        )

        self.asset_definitions = {
            space.asset.asset_id: space.asset
            for space in self.board.spaces
            if space.asset is not None
        }

        self.group_assets = self._group_assets()

        (
            self.chance_deck,
            self.community_deck,
        ) = self._build_event_decks()

        self.chance_index = 0
        self.community_index = 0

        self._emit(
            EventType.GAME_SETUP,
            metadata={
                "game_seed": game_seed,
                "seat_assignment": [strategy.value for strategy in seat_assignment],
            },
        )

        self.validate_invariants()

    def _group_assets(
        self,
    ) -> dict[
        PropertyGroupId,
        tuple[str, ...],
    ]:
        result: dict[
            PropertyGroupId,
            list[str],
        ] = {}

        for asset in self.asset_definitions.values():
            if asset.group_id is None:
                continue

            result.setdefault(
                asset.group_id,
                [],
            ).append(asset.asset_id)

        return {group_id: tuple(asset_ids) for group_id, asset_ids in result.items()}

    def _build_event_decks(
        self,
    ) -> tuple[
        list[EventCard],
        list[EventCard],
    ]:
        rules = _mapping(
            self.config.raw.get("event_rules"),
            name="event_rules",
        )

        def parse(
            key: str,
        ) -> list[EventCard]:
            raw_cards = _sequence(
                rules.get(key),
                name=f"event_rules.{key}",
            )

            cards: list[EventCard] = []

            for raw in raw_cards:
                item = _mapping(
                    raw,
                    name=f"{key} card",
                )

                target = item.get("target_space")
                spaces = item.get("spaces")
                amount = item.get("amount")

                cards.append(
                    EventCard(
                        event_id=_text(
                            item.get("event_id"),
                            name="event_id",
                        ),
                        action=_text(
                            item.get("action"),
                            name="action",
                        ),
                        target_space=(
                            _integer(
                                target,
                                name="target_space",
                            )
                            if target is not None
                            else None
                        ),
                        spaces=(
                            _integer(
                                spaces,
                                name="spaces",
                            )
                            if spaces is not None
                            else None
                        ),
                        amount=(
                            _integer(
                                amount,
                                name="amount",
                            )
                            if amount is not None
                            else None
                        ),
                    )
                )

            return cards

        chance = parse("chance")
        community = parse("community")

        self.random.chance.shuffle(chance)
        self.random.community.shuffle(community)

        return (
            chance,
            community,
        )

    def _emit(
        self,
        event_type: EventType,
        *,
        player: PlayerState | None = None,
        position_before: int | None = None,
        position_after: int | None = None,
        cash_before: int | None = None,
        cash_after: int | None = None,
        asset_id: str | None = None,
        counterparty_player_id: str | None = None,
        amount: int | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> None:
        event = TurnEvent(
            game_id=self.state.game_id,
            event_index=self.state.event_index,
            turn_number=self.state.turn_number,
            event_type=event_type,
            player_id=(player.player_id if player is not None else None),
            strategy_id=(player.strategy_id if player is not None else None),
            seat_index=(player.seat_index if player is not None else None),
            position_before=position_before,
            position_after=position_after,
            cash_before=cash_before,
            cash_after=cash_after,
            asset_id=asset_id,
            counterparty_player_id=counterparty_player_id,
            amount=amount,
            metadata=(metadata if metadata is not None else {}),
        )

        self.events.append(event)

        self.state.event_index += 1

    def _context(
        self,
        player: PlayerState,
    ) -> DecisionContext:
        return DecisionContext(
            turn_number=self.state.turn_number,
            player=PlayerView(
                player_id=player.player_id,
                strategy_id=player.strategy_id,
                seat_index=player.seat_index,
                cash=player.cash,
                position=player.position,
                owned_asset_ids=tuple(player.owned_asset_ids),
                bankrupt=player.bankrupt,
            ),
            properties=MappingProxyType(
                {
                    asset_id: PropertyView(
                        asset_id=asset_id,
                        owner_id=state.owner_id,
                        house_count=state.house_count,
                    )
                    for asset_id, state in self.state.properties.items()
                }
            ),
        )

    def _snapshot(self) -> None:
        self.snapshots.append(
            TurnSnapshot(
                turn_number=self.state.turn_number,
                active_player_index=self.state.active_player_index,
                player_cash=tuple(
                    sorted(
                        (
                            player_id,
                            player.cash,
                        )
                        for player_id, player in self.state.players.items()
                    )
                ),
                player_positions=tuple(
                    sorted(
                        (
                            player_id,
                            player.position,
                        )
                        for player_id, player in self.state.players.items()
                    )
                ),
                ownership=tuple(
                    sorted(
                        (
                            asset_id,
                            state.owner_id,
                            state.house_count,
                        )
                        for asset_id, state in self.state.properties.items()
                    )
                ),
            )
        )

    def _active_players(
        self,
    ) -> list[PlayerState]:
        return [player for player in self.state.players.values() if not player.bankrupt]

    def _next_active_seat(
        self,
        after_seat: int,
    ) -> int:
        for offset in range(
            1,
            5,
        ):
            seat = (after_seat + offset) % 4

            player = self.state.players[f"player_{seat}"]

            if not player.bankrupt:
                return seat

        return after_seat

    def _move(
        self,
        player: PlayerState,
        steps: int,
        *,
        collect_go: bool = True,
    ) -> None:
        before = player.position

        raw_position = before + steps

        passed_go = collect_go and steps > 0 and raw_position >= self.board.size

        player.position = raw_position % self.board.size

        self._emit(
            EventType.MOVE,
            player=player,
            position_before=before,
            position_after=player.position,
            metadata={
                "steps": steps,
            },
        )

        if passed_go:
            self._award_go(player)

    def _move_to(
        self,
        player: PlayerState,
        target: int,
        *,
        collect_go_if_target_go: bool,
    ) -> None:
        before = player.position

        player.position = target

        self._emit(
            EventType.MOVE,
            player=player,
            position_before=before,
            position_after=target,
            metadata={
                "direct_move": True,
            },
        )

        if target == 0 and collect_go_if_target_go:
            self._award_go(player)

    def _award_go(
        self,
        player: PlayerState,
    ) -> None:
        before = player.cash

        player.cash += self.config.simulation.go_salary

        self._observe_cash(player)

        self._emit(
            EventType.PASS_GO,
            player=player,
            cash_before=before,
            cash_after=player.cash,
            amount=self.config.simulation.go_salary,
        )

    def _observe_cash(
        self,
        player: PlayerState,
    ) -> None:
        if player.minimum_cash_observed is None or player.cash < player.minimum_cash_observed:
            player.minimum_cash_observed = player.cash

    def _owns_complete_group(
        self,
        player_id: str,
        group_id: PropertyGroupId,
    ) -> bool:
        asset_ids = self.group_assets[group_id]

        return all(self.state.properties[asset_id].owner_id == player_id for asset_id in asset_ids)

    def _asset_rent(
        self,
        asset: PropertyDefinition,
        *,
        dice_total: int,
    ) -> int:
        state = self.state.properties[asset.asset_id]

        if state.owner_id is None:
            return 0

        if asset.space_type is SpaceType.PROPERTY:
            if asset.group_id is None:
                raise EngineInvariantError("color property missing group")

            multipliers_raw = _mapping(
                self.config.raw["rent_rules"],
                name="rent_rules",
            )

            house_multipliers = _mapping(
                multipliers_raw.get("house_multipliers"),
                name="house_multipliers",
            )

            if state.house_count > 0:
                multiplier = _integer(
                    house_multipliers.get(state.house_count),
                    name="house multiplier",
                )

                return asset.base_rent * multiplier

            owner = state.owner_id

            if self._owns_complete_group(
                owner,
                asset.group_id,
            ):
                complete_multiplier = _integer(
                    multipliers_raw.get("complete_group_unimproved_multiplier"),
                    name="complete group multiplier",
                )

                return asset.base_rent * complete_multiplier

            return asset.base_rent

        if asset.space_type is SpaceType.TRANSIT:
            owner = state.owner_id

            owned_count = sum(
                1
                for candidate in self.asset_definitions.values()
                if (
                    candidate.space_type is SpaceType.TRANSIT
                    and self.state.properties[candidate.asset_id].owner_id == owner
                )
            )

            rules = _mapping(
                self.config.raw["transit_rules"],
                name="transit_rules",
            )

            rents = _mapping(
                rules.get("rent_by_transit_count"),
                name="rent_by_transit_count",
            )

            return _integer(
                rents.get(owned_count),
                name="transit rent",
            )

        if asset.space_type is SpaceType.UTILITY:
            owner = state.owner_id

            owned_count = sum(
                1
                for candidate in self.asset_definitions.values()
                if (
                    candidate.space_type is SpaceType.UTILITY
                    and self.state.properties[candidate.asset_id].owner_id == owner
                )
            )

            rules = _mapping(
                self.config.raw["utility_rules"],
                name="utility_rules",
            )

            multipliers = _mapping(
                rules.get("rent_multiplier_by_utility_count"),
                name="utility multipliers",
            )

            multiplier = _integer(
                multipliers.get(owned_count),
                name="utility multiplier",
            )

            return dice_total * multiplier

        raise EngineInvariantError("unsupported asset type")

    def _transfer_required_payment(
        self,
        *,
        payer: PlayerState,
        amount: int,
        creditor: PlayerState | None,
        reason: str,
    ) -> None:
        if amount < 0:
            raise ValueError("required payment cannot be negative")

        before = payer.cash

        payment = min(
            payer.cash,
            amount,
        )

        payer.cash -= payment

        if creditor is not None:
            creditor.cash += payment

            if reason == "rent":
                payer.total_rent_paid += payment
                creditor.total_rent_collected += payment

                self._observe_cash(creditor)

        self._observe_cash(payer)

        self._emit(
            EventType.CASH_TRANSFER,
            player=payer,
            cash_before=before,
            cash_after=payer.cash,
            counterparty_player_id=(creditor.player_id if creditor is not None else None),
            amount=payment,
            metadata={
                "reason": reason,
                "required_amount": amount,
                "shortfall": (amount - payment),
            },
        )

        if payment < amount:
            self._bankrupt(
                payer,
                creditor=creditor,
                reason=reason,
            )

    def _bankrupt(
        self,
        player: PlayerState,
        *,
        creditor: PlayerState | None,
        reason: str,
    ) -> None:
        if player.bankrupt:
            return

        player.bankrupt = True
        player.bankruptcy_turn = self.state.turn_number

        event_index = self.state.event_index

        self.bankruptcy_event_indices[player.player_id] = event_index

        self._emit(
            EventType.BANKRUPTCY,
            player=player,
            metadata={
                "reason": reason,
                "creditor": (creditor.player_id if creditor is not None else None),
            },
        )

        owned = tuple(player.owned_asset_ids)

        for asset_id in owned:
            state = self.state.properties[asset_id]

            if creditor is None:
                state.owner_id = None
                state.house_count = 0

            else:
                state.owner_id = creditor.player_id

                if asset_id not in creditor.owned_asset_ids:
                    creditor.owned_asset_ids.append(asset_id)

            self._emit(
                EventType.ASSET_TRANSFER,
                player=player,
                asset_id=asset_id,
                counterparty_player_id=(creditor.player_id if creditor is not None else None),
            )

        player.owned_asset_ids.clear()

    def _purchase(
        self,
        player: PlayerState,
        asset: PropertyDefinition,
    ) -> None:
        state = self.state.properties[asset.asset_id]

        if state.owner_id is not None:
            raise DecisionValidationError("cannot buy owned asset")

        if player.bankrupt:
            raise DecisionValidationError("bankrupt player cannot buy")

        if player.cash < asset.purchase_price:
            raise DecisionValidationError("player cannot afford asset")

        before = player.cash

        player.cash -= asset.purchase_price

        self._observe_cash(player)

        state.owner_id = player.player_id

        player.owned_asset_ids.append(asset.asset_id)

        self._emit(
            EventType.ASSET_PURCHASED,
            player=player,
            cash_before=before,
            cash_after=player.cash,
            asset_id=asset.asset_id,
            amount=asset.purchase_price,
        )

    def _build_house(
        self,
        player: PlayerState,
        property_id: str,
    ) -> None:
        if property_id not in self.asset_definitions:
            raise DecisionValidationError("unknown build property")

        asset = self.asset_definitions[property_id]

        if asset.space_type is not SpaceType.PROPERTY:
            raise DecisionValidationError("houses require color property")

        state = self.state.properties[property_id]

        if state.owner_id != player.player_id:
            raise DecisionValidationError("player does not own property")

        if asset.group_id is None:
            raise EngineInvariantError("color property missing group")

        if not self._owns_complete_group(
            player.player_id,
            asset.group_id,
        ):
            raise DecisionValidationError("complete group required")

        if state.house_count >= 4:
            raise DecisionValidationError("maximum house count reached")

        if asset.house_cost is None:
            raise EngineInvariantError("house cost missing")

        if player.cash < asset.house_cost:
            raise DecisionValidationError("player cannot afford house")

        group_states = [
            self.state.properties[asset_id] for asset_id in self.group_assets[asset.group_id]
        ]

        prospective = [
            (candidate.house_count + (1 if candidate.asset_id == property_id else 0))
            for candidate in group_states
        ]

        if max(prospective) - min(prospective) > 1:
            raise DecisionValidationError("build violates even-development rule")

        before = player.cash

        player.cash -= asset.house_cost

        self._observe_cash(player)

        state.house_count += 1

        self._emit(
            EventType.HOUSE_BUILT,
            player=player,
            cash_before=before,
            cash_after=player.cash,
            asset_id=property_id,
            amount=asset.house_cost,
            metadata={
                "house_count": state.house_count,
            },
        )

    def _enter_jail(
        self,
        player: PlayerState,
    ) -> None:
        before = player.position

        player.position = self.board.jail_index

        player.jail.turns_remaining = 1

        self._emit(
            EventType.MOVE,
            player=player,
            position_before=before,
            position_after=player.position,
            metadata={
                "sent_to_jail": True,
            },
        )

    def _draw_event(
        self,
        space_type: SpaceType,
    ) -> EventCard:
        if space_type is SpaceType.CHANCE:
            card = self.chance_deck[self.chance_index % len(self.chance_deck)]

            self.chance_index += 1

            return card

        if space_type is SpaceType.COMMUNITY:
            card = self.community_deck[self.community_index % len(self.community_deck)]

            self.community_index += 1

            return card

        raise ValueError("event draw requires Chance or Community")

    def _apply_event(
        self,
        player: PlayerState,
        card: EventCard,
        *,
        dice_total: int,
    ) -> None:
        self._emit(
            EventType.EVENT_DRAW,
            player=player,
            metadata={
                "event_id": card.event_id,
                "action": card.action,
            },
        )

        if card.action == "MOVE_TO":
            if card.target_space is None:
                raise EngineInvariantError("MOVE_TO event missing target")

            self._move_to(
                player,
                card.target_space,
                collect_go_if_target_go=True,
            )

            if not player.bankrupt:
                self._resolve_landing(
                    player,
                    dice_total=dice_total,
                    allow_event_draw=False,
                )

            return

        if card.action == "MOVE_RELATIVE":
            if card.spaces is None:
                raise EngineInvariantError("MOVE_RELATIVE event missing spaces")

            self._move(
                player,
                card.spaces,
                collect_go=(card.spaces > 0),
            )

            if not player.bankrupt:
                self._resolve_landing(
                    player,
                    dice_total=dice_total,
                    allow_event_draw=False,
                )

            return

        if card.action == "GO_TO_JAIL":
            self._enter_jail(player)
            return

        if card.action == "CASH":
            if card.amount is None:
                raise EngineInvariantError("CASH event missing amount")

            if card.amount >= 0:
                before = player.cash

                player.cash += card.amount

                self._observe_cash(player)

                self._emit(
                    EventType.CASH_TRANSFER,
                    player=player,
                    cash_before=before,
                    cash_after=player.cash,
                    amount=card.amount,
                    metadata={
                        "reason": "event",
                    },
                )

            else:
                self._transfer_required_payment(
                    payer=player,
                    amount=abs(card.amount),
                    creditor=None,
                    reason="event",
                )

            return

        raise EngineInvariantError(f"unsupported event action: {card.action}")

    def _resolve_landing(
        self,
        player: PlayerState,
        *,
        dice_total: int,
        allow_event_draw: bool = True,
    ) -> None:
        space = self.board.spaces[player.position]

        if space.space_type in {
            SpaceType.GO,
            SpaceType.JAIL,
            SpaceType.FREE_REST,
        }:
            return

        if space.space_type is SpaceType.GO_TO_JAIL:
            self._enter_jail(player)
            return

        if space.space_type is SpaceType.TAX:
            if space.amount is None:
                raise EngineInvariantError("tax space missing amount")

            self._transfer_required_payment(
                payer=player,
                amount=space.amount,
                creditor=None,
                reason="tax",
            )
            return

        if space.space_type in {
            SpaceType.CHANCE,
            SpaceType.COMMUNITY,
        }:
            if allow_event_draw:
                self._apply_event(
                    player,
                    self._draw_event(space.space_type),
                    dice_total=dice_total,
                )

            return

        asset = space.asset

        if asset is None:
            raise EngineInvariantError("purchasable space missing asset")

        property_state = self.state.properties[asset.asset_id]

        if property_state.owner_id is None:
            decision = self.decision_provider.purchase_decision(
                context=self._context(player),
                space=space,
                asset=asset,
            )

            self._emit(
                EventType.PURCHASE_DECISION,
                player=player,
                asset_id=asset.asset_id,
                metadata={
                    "action": decision.action.value,
                    "reason_code": decision.reason_code,
                },
            )

            if decision.action is StrategyAction.BUY:
                if decision.asset_id != asset.asset_id:
                    raise DecisionValidationError("BUY must target landed asset")

                self._purchase(
                    player,
                    asset,
                )

            elif decision.action is not StrategyAction.PASS:
                raise DecisionValidationError("invalid purchase-phase decision")

            return

        if property_state.owner_id == player.player_id:
            return

        owner = self.state.players[property_state.owner_id]

        if owner.bankrupt:
            raise EngineInvariantError("bankrupt player cannot own asset")

        rent = self._asset_rent(
            asset,
            dice_total=dice_total,
        )

        self._emit(
            EventType.RENT_DUE,
            player=player,
            asset_id=asset.asset_id,
            counterparty_player_id=owner.player_id,
            amount=rent,
        )

        self._transfer_required_payment(
            payer=player,
            amount=rent,
            creditor=owner,
            reason="rent",
        )

    def _development_phase(
        self,
        player: PlayerState,
    ) -> None:
        decisions = self.decision_provider.build_decisions(
            context=self._context(player),
            board=self.board,
        )

        for decision in decisions:
            self._emit(
                EventType.BUILD_DECISION,
                player=player,
                asset_id=decision.property_id,
                metadata={
                    "action": decision.action.value,
                    "reason_code": decision.reason_code,
                },
            )

            if decision.action is StrategyAction.HOLD_CASH:
                if decision.property_id is not None:
                    raise DecisionValidationError("HOLD_CASH cannot target property")

                continue

            if decision.action is not StrategyAction.BUILD:
                raise DecisionValidationError("invalid development-phase decision")

            if decision.property_id is None:
                raise DecisionValidationError("BUILD requires property_id")

            self._build_house(
                player,
                decision.property_id,
            )

    def _execute_turn(
        self,
        player: PlayerState,
    ) -> None:
        self._emit(
            EventType.TURN_START,
            player=player,
        )

        if player.jail.is_jailed:
            player.jail.turns_remaining -= 1

            self._emit(
                EventType.JAIL_SKIP,
                player=player,
                metadata={
                    "turns_remaining": player.jail.turns_remaining,
                },
            )

            self._emit(
                EventType.TURN_END,
                player=player,
            )

            return

        roll = self.random.dice.roll()

        self._emit(
            EventType.DICE_ROLL,
            player=player,
            metadata={
                "die_1": roll.die_1,
                "die_2": roll.die_2,
                "total": roll.total,
                "doubles": roll.is_doubles,
            },
        )

        self._move(
            player,
            roll.total,
        )

        if not player.bankrupt:
            self._resolve_landing(
                player,
                dice_total=roll.total,
            )

        if not player.bankrupt:
            self._development_phase(player)

        self._emit(
            EventType.TURN_END,
            player=player,
        )

    def terminal_net_worth(
        self,
        player: PlayerState,
    ) -> int:
        value = player.cash

        for asset_id in player.owned_asset_ids:
            definition = self.asset_definitions[asset_id]

            state = self.state.properties[asset_id]

            value += definition.purchase_price

            if definition.house_cost is not None:
                value += state.house_count * definition.house_cost

        return value

    def _completed_group_count(
        self,
        player_id: str,
    ) -> int:
        return sum(
            1
            for group_id in self.group_assets
            if self._owns_complete_group(
                player_id,
                group_id,
            )
        )

    def _owned_asset_count(
        self,
        player_id: str,
    ) -> int:
        return sum(1 for state in self.state.properties.values() if state.owner_id == player_id)

    def _active_ranking(
        self,
    ) -> list[PlayerState]:
        active = self._active_players()

        return sorted(
            active,
            key=lambda player: (
                -self.terminal_net_worth(player),
                -player.cash,
                -player.total_rent_collected,
                -self._completed_group_count(player.player_id),
                -self._owned_asset_count(player.player_id),
                deterministic_tie_rank(
                    self.random.tie_break_seed,
                    player.player_id,
                ),
            ),
        )

    def _bankrupt_ranking(
        self,
    ) -> list[PlayerState]:
        bankrupt = [player for player in self.state.players.values() if player.bankrupt]

        return sorted(
            bankrupt,
            key=lambda player: (
                -(player.bankruptcy_turn if player.bankruptcy_turn is not None else -1),
                -self.bankruptcy_event_indices.get(
                    player.player_id,
                    -1,
                ),
                deterministic_tie_rank(
                    self.random.tie_break_seed,
                    player.player_id,
                ),
            ),
        )

    def _finish_game(
        self,
        phase: GamePhase,
    ) -> GameResult:
        self.state.phase = phase

        active = self._active_ranking()
        bankrupt = self._bankrupt_ranking()

        ranking = active + bankrupt

        if not ranking:
            raise EngineInvariantError("game has no ranked players")

        finishing_positions = {player.player_id: index + 1 for index, player in enumerate(ranking)}

        winner = ranking[0]

        self._emit(
            EventType.GAME_END,
            player=winner,
            metadata={
                "termination_reason": phase.value,
                "finishing_positions": finishing_positions,
            },
        )

        return GameResult(
            game_id=self.state.game_id,
            game_index=self.state.game_index,
            game_seed=self.state.game_seed,
            winner_player_id=winner.player_id,
            winner_strategy_id=winner.strategy_id,
            turns_played=self.state.turn_number,
            termination_reason=phase,
            finishing_positions=finishing_positions,
        )

    def validate_invariants(
        self,
    ) -> None:
        owners_seen: dict[
            str,
            str,
        ] = {}

        for asset_id, state in self.state.properties.items():
            if not 0 <= state.house_count <= 4:
                raise EngineInvariantError(f"{asset_id}: illegal house count")

            if state.owner_id is None:
                if state.house_count != 0:
                    raise EngineInvariantError(f"{asset_id}: unowned asset has houses")

                continue

            if state.owner_id not in self.state.players:
                raise EngineInvariantError(f"{asset_id}: unknown owner")

            owner = self.state.players[state.owner_id]

            if owner.bankrupt:
                raise EngineInvariantError(f"{asset_id}: bankrupt owner")

            if asset_id not in owner.owned_asset_ids:
                raise EngineInvariantError(f"{asset_id}: ownership lists disagree")

            owners_seen[asset_id] = state.owner_id

        for player in self.state.players.values():
            if len(player.owned_asset_ids) != len(set(player.owned_asset_ids)):
                raise EngineInvariantError(f"{player.player_id}: duplicate asset")

            for asset_id in player.owned_asset_ids:
                if asset_id not in self.state.properties:
                    raise EngineInvariantError(f"{player.player_id}: unknown asset")

                if self.state.properties[asset_id].owner_id != player.player_id:
                    raise EngineInvariantError(f"{player.player_id}: ownership mismatch")

            if player.bankrupt and player.owned_asset_ids:
                raise EngineInvariantError(f"{player.player_id}: bankrupt player retains assets")

        event_indices = [event.event_index for event in self.events]

        if event_indices != list(range(len(event_indices))):
            raise EngineInvariantError("event indices are not contiguous")

    def simulate(
        self,
    ) -> SimulationResult:
        """Run one complete headless deterministic game."""

        maximum_turns = self.config.simulation.maximum_turns

        while True:
            active = self._active_players()

            if len(active) == 1:
                result = self._finish_game(GamePhase.TERMINATED_BANKRUPTCY)

                break

            if self.state.turn_number >= maximum_turns:
                result = self._finish_game(GamePhase.TERMINATED_TURN_LIMIT)

                break

            seat = self.state.active_player_index

            player = self.state.players[f"player_{seat}"]

            if player.bankrupt:
                self.state.active_player_index = self._next_active_seat(seat)

                continue

            self.state.turn_number += 1

            self._execute_turn(player)

            self.validate_invariants()

            self._snapshot()

            self.state.active_player_index = self._next_active_seat(seat)

        self.validate_invariants()

        return SimulationResult(
            result=result,
            final_state=self.state,
            events=tuple(self.events),
            snapshots=tuple(self.snapshots),
        )


def simulate_game(
    *,
    config: MonopolyConfig,
    game_index: int,
    game_seed: int,
    seat_assignment: tuple[
        StrategyId,
        StrategyId,
        StrategyId,
        StrategyId,
    ],
    decision_provider: DecisionProvider | None = None,
) -> SimulationResult:
    """Convenience function for one deterministic headless game."""

    provider = decision_provider if decision_provider is not None else PassiveDecisionProvider()

    engine = GameEngine(
        config=config,
        game_index=game_index,
        game_seed=game_seed,
        seat_assignment=seat_assignment,
        decision_provider=provider,
    )

    return engine.simulate()
