"""Enums and identifier types for Project 3."""

from __future__ import annotations

from enum import StrEnum
from typing import NewType

PropertyGroupId = NewType(
    "PropertyGroupId",
    str,
)


class SpaceType(StrEnum):
    """Canonical board-space taxonomy."""

    GO = "GO"
    PROPERTY = "PROPERTY"
    TRANSIT = "TRANSIT"
    UTILITY = "UTILITY"
    CHANCE = "CHANCE"
    COMMUNITY = "COMMUNITY"
    TAX = "TAX"
    JAIL = "JAIL"
    FREE_REST = "FREE_REST"
    GO_TO_JAIL = "GO_TO_JAIL"


class StrategyId(StrEnum):
    """Canonical autonomous strategy identifiers."""

    COLLECTOR = "collector"
    SPECIALIST = "specialist"
    CASH_PROTECTOR = "cash_protector"
    AGGRESSIVE_BUILDER = "aggressive_builder"


class StrategyAction(StrEnum):
    """Legal strategy decision actions."""

    BUY = "BUY"
    PASS = "PASS"
    BUILD = "BUILD"
    HOLD_CASH = "HOLD_CASH"


class GamePhase(StrEnum):
    """Canonical game lifecycle phases."""

    SETUP = "SETUP"
    ACTIVE = "ACTIVE"
    TERMINATED_BANKRUPTCY = "TERMINATED_BANKRUPTCY"
    TERMINATED_TURN_LIMIT = "TERMINATED_TURN_LIMIT"


class EventType(StrEnum):
    """Canonical replayable event types."""

    GAME_SETUP = "GAME_SETUP"
    TURN_START = "TURN_START"
    JAIL_SKIP = "JAIL_SKIP"
    DICE_ROLL = "DICE_ROLL"
    MOVE = "MOVE"
    PASS_GO = "PASS_GO"
    EVENT_DRAW = "EVENT_DRAW"
    CASH_TRANSFER = "CASH_TRANSFER"
    PURCHASE_DECISION = "PURCHASE_DECISION"
    ASSET_PURCHASED = "ASSET_PURCHASED"
    BUILD_DECISION = "BUILD_DECISION"
    HOUSE_BUILT = "HOUSE_BUILT"
    RENT_DUE = "RENT_DUE"
    BANKRUPTCY = "BANKRUPTCY"
    ASSET_TRANSFER = "ASSET_TRANSFER"
    TURN_END = "TURN_END"
    GAME_END = "GAME_END"
