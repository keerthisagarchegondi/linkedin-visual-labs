"""Typed domain models for Project 3.

Immutable definitions and decisions are frozen dataclasses.
Live simulation state is intentionally mutable and will be owned by
the game engine in Step 3.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    EventType,
    GamePhase,
    PropertyGroupId,
    SpaceType,
    StrategyAction,
    StrategyId,
)


@dataclass(frozen=True, slots=True)
class PropertyDefinition:
    """Immutable definition of one purchasable board asset."""

    asset_id: str
    board_index: int
    name: str
    space_type: SpaceType
    purchase_price: int
    base_rent: int = 0
    group_id: PropertyGroupId | None = None
    house_cost: int | None = None

    def __post_init__(self) -> None:
        if self.space_type not in {
            SpaceType.PROPERTY,
            SpaceType.TRANSIT,
            SpaceType.UTILITY,
        }:
            raise ValueError("PropertyDefinition requires a purchasable space type")

        if self.purchase_price <= 0:
            raise ValueError("purchase_price must be positive")

        if self.base_rent < 0:
            raise ValueError("base_rent cannot be negative")

        if self.space_type is SpaceType.PROPERTY and self.group_id is None:
            raise ValueError("color property requires group_id")


@dataclass(frozen=True, slots=True)
class BoardSpace:
    """Immutable board-space definition."""

    index: int
    space_id: str
    name: str
    space_type: SpaceType
    asset: PropertyDefinition | None = None
    amount: int | None = None

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("board-space index cannot be negative")

        purchasable = self.space_type in {
            SpaceType.PROPERTY,
            SpaceType.TRANSIT,
            SpaceType.UTILITY,
        }

        if purchasable != (self.asset is not None):
            raise ValueError("purchasable spaces require exactly one asset definition")


@dataclass(frozen=True, slots=True)
class BoardDefinition:
    """Immutable canonical circular board."""

    spaces: tuple[BoardSpace, ...]
    jail_index: int

    def __post_init__(self) -> None:
        if not self.spaces:
            raise ValueError("board must contain spaces")

        indices = tuple(space.index for space in self.spaces)

        if indices != tuple(range(len(self.spaces))):
            raise ValueError("board indices must be contiguous from zero")

        identifiers = [space.space_id for space in self.spaces]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError("board space IDs must be unique")

        if not (0 <= self.jail_index < len(self.spaces)):
            raise ValueError("jail index outside board")

        if self.spaces[self.jail_index].space_type is not SpaceType.JAIL:
            raise ValueError("jail_index must identify JAIL space")

    @property
    def size(self) -> int:
        return len(self.spaces)


@dataclass(slots=True)
class JailState:
    """Mutable jail status owned by the game engine."""

    turns_remaining: int = 0

    @property
    def is_jailed(self) -> bool:
        return self.turns_remaining > 0


@dataclass(slots=True)
class PropertyState:
    """Mutable ownership/development state."""

    asset_id: str
    owner_id: str | None = None
    house_count: int = 0

    def __post_init__(self) -> None:
        if self.house_count < 0:
            raise ValueError("house_count cannot be negative")

        if self.house_count > 4:
            raise ValueError("house_count cannot exceed four")


@dataclass(slots=True)
class PlayerState:
    """Mutable player state owned by the game engine."""

    player_id: str
    strategy_id: StrategyId
    seat_index: int
    cash: int
    position: int = 0
    owned_asset_ids: list[str] = field(default_factory=list)
    jail: JailState = field(default_factory=JailState)
    bankrupt: bool = False
    bankruptcy_turn: int | None = None
    total_rent_paid: int = 0
    total_rent_collected: int = 0
    minimum_cash_observed: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.seat_index <= 3:
            raise ValueError("seat_index must be between 0 and 3")

        if self.position < 0:
            raise ValueError("position cannot be negative")

        if self.minimum_cash_observed is None:
            self.minimum_cash_observed = self.cash


@dataclass(slots=True)
class GameState:
    """Explicitly mutable state for one game."""

    game_id: str
    game_index: int
    game_seed: int
    phase: GamePhase
    turn_number: int
    active_player_index: int
    players: dict[str, PlayerState]
    properties: dict[str, PropertyState]
    event_index: int = 0

    def __post_init__(self) -> None:
        if self.game_index < 0:
            raise ValueError("game_index cannot be negative")

        if self.game_seed < 0:
            raise ValueError("game_seed cannot be negative")

        if self.turn_number < 0:
            raise ValueError("turn_number cannot be negative")

        if self.event_index < 0:
            raise ValueError("event_index cannot be negative")


@dataclass(frozen=True, slots=True)
class PurchaseDecision:
    """Immutable strategy purchase decision."""

    action: StrategyAction
    reason_code: str
    asset_id: str | None = None

    def __post_init__(self) -> None:
        if self.action not in {
            StrategyAction.BUY,
            StrategyAction.PASS,
        }:
            raise ValueError("purchase decision must be BUY or PASS")

        if self.action is StrategyAction.BUY and self.asset_id is None:
            raise ValueError("BUY requires asset_id")


@dataclass(frozen=True, slots=True)
class BuildDecision:
    """Immutable strategy development decision."""

    action: StrategyAction
    reason_code: str
    property_id: str | None = None

    def __post_init__(self) -> None:
        if self.action not in {
            StrategyAction.BUILD,
            StrategyAction.HOLD_CASH,
        }:
            raise ValueError("build decision must be BUILD or HOLD_CASH")

        if self.action is StrategyAction.BUILD and self.property_id is None:
            raise ValueError("BUILD requires property_id")


@dataclass(frozen=True, slots=True)
class TurnEvent:
    """Immutable replay event."""

    game_id: str
    event_index: int
    turn_number: int
    event_type: EventType
    player_id: str | None = None
    strategy_id: StrategyId | None = None
    seat_index: int | None = None
    position_before: int | None = None
    position_after: int | None = None
    cash_before: int | None = None
    cash_after: int | None = None
    asset_id: str | None = None
    counterparty_player_id: str | None = None
    amount: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GameResult:
    """Immutable completed-game summary."""

    game_id: str
    game_index: int
    game_seed: int
    winner_player_id: str
    winner_strategy_id: StrategyId
    turns_played: int
    termination_reason: GamePhase
    finishing_positions: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class TournamentGameRecord:
    """One strategy-game row in tournament_results.csv."""

    game_id: str
    game_index: int
    game_seed: int
    strategy_id: StrategyId
    seat_index: int
    finishing_position: int
    won: bool
    bankrupt: bool
    bankruptcy_turn: int | None
    finishing_cash: int
    terminal_net_worth: int
    assets_acquired_total: int
    color_properties_acquired: int
    transit_assets_acquired: int
    utility_assets_acquired: int
    assets_owned_at_finish: int
    groups_completed_during_game: int
    groups_owned_complete_at_finish: int
    first_group_completion_turn: int | None
    houses_built_total: int
    houses_owned_at_finish: int
    first_house_build_turn: int | None
    total_rent_paid: int
    total_rent_collected: int
    net_rent: int
    minimum_cash_observed: int
    median_end_of_turn_cash: float
    mean_end_of_turn_cash: float
    turns_below_strategy_desired_reserve: int
    turns_played: int
    termination_reason: GamePhase


@dataclass(frozen=True, slots=True)
class TournamentSummary:
    """Typed scaffold for the later aggregated tournament result."""

    schema_version: str
    project_id: str
    master_seed: int
    game_count: int
    strategy_order: tuple[StrategyId, ...]
    headline_result: Mapping[str, object]
    strategy_summary: tuple[Mapping[str, object], ...]
    pairwise_comparisons: tuple[Mapping[str, object], ...]
    fairness: Mapping[str, object]
    game_length: Mapping[str, object]
    representative_game: Mapping[str, object]
    validation: Mapping[str, object]
    artifact_hashes: Mapping[str, str]
