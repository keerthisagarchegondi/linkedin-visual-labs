"""Semantic turn replay for the Project 3 playable video."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

STRATEGIES = (
    "collector",
    "specialist",
    "cash_protector",
    "aggressive_builder",
)

DISPLAY_NAMES = {
    "collector": "Collector",
    "specialist": "Specialist",
    "cash_protector": "Cash Protector",
    "aggressive_builder": "Aggressive Builder",
}


@dataclass(frozen=True)
class SemanticEvent:
    index: int
    kind: str
    strategy_id: str | None
    turn_number: int | None
    from_position: int | None
    to_position: int | None
    die_1: int | None
    die_2: int | None
    amount: float | None
    cash_after: float | None
    space_index: int | None
    property_name: str | None
    houses_after: int | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class GameState:
    positions: dict[str, int]
    cash: dict[str, float]
    ownership: dict[int, str]
    houses: dict[int, int]
    bankrupt: frozenset[str]


@dataclass(frozen=True)
class TurnBeat:
    index: int
    turn_number: int
    strategy_id: str
    events: tuple[SemanticEvent, ...]
    state_before: GameState
    state_after: GameState
    dice: tuple[int, int] | None
    from_position: int
    to_position: int
    primary_action: str
    amount: float | None
    property_name: str | None
    passes_start: bool
    bankrupts: bool


@dataclass
class MutableState:
    positions: dict[str, int] = field(
        default_factory=lambda: {strategy: 0 for strategy in STRATEGIES}
    )

    cash: dict[str, float] = field(
        default_factory=lambda: {strategy: 1500.0 for strategy in STRATEGIES}
    )

    ownership: dict[int, str] = field(default_factory=dict)

    houses: dict[int, int] = field(default_factory=dict)

    bankrupt: set[str] = field(default_factory=set)


def freeze(
    state: MutableState,
) -> GameState:
    return GameState(
        positions=dict(state.positions),
        cash=dict(state.cash),
        ownership=dict(state.ownership),
        houses=dict(state.houses),
        bankrupt=frozenset(state.bankrupt),
    )


def walk(
    value: Any,
) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key), nested
            yield from walk(nested)

    elif isinstance(value, list):
        for nested in value:
            yield from walk(nested)


def first(
    value: Any,
    names: tuple[str, ...],
) -> Any | None:
    wanted = {name.lower() for name in names}

    for key, nested in walk(value):
        if key.lower() in wanted:
            return nested

    return None


def integer(
    value: Any,
) -> int | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float) and value.is_integer():
        return round(value)

    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None

    return None


def number(
    value: Any,
) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip().replace("$", "").replace(",", "")

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def normalize_name(
    value: Any,
) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def strategy_from_value(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = normalize_name(value)

    aliases = {
        "collector": "collector",
        "specialist": "specialist",
        "cash_protector": "cash_protector",
        "cashprotector": "cash_protector",
        "aggressive_builder": "aggressive_builder",
        "aggressivebuilder": "aggressive_builder",
    }

    if normalized in aliases:
        return aliases[normalized]

    for strategy in STRATEGIES:
        if strategy in normalized:
            return strategy

    return None


def build_player_map(
    representative_game: Any,
) -> dict[str, str]:
    mapping: dict[str, str] = {}

    for key, value in walk(representative_game):
        if key.lower() not in {
            "players",
            "seats",
            "strategies",
        }:
            continue

        if not isinstance(value, list):
            continue

        for index, item in enumerate(value):
            strategy = strategy_from_value(item)

            if strategy is None and isinstance(item, dict):
                strategy = strategy_from_value(
                    first(
                        item,
                        (
                            "strategy_id",
                            "strategy",
                            "player_strategy",
                            "agent",
                            "policy",
                        ),
                    )
                )

            if strategy is not None:
                mapping[str(index)] = strategy

                if isinstance(item, dict):
                    identity = first(
                        item,
                        (
                            "player_id",
                            "player_index",
                            "seat",
                            "seat_index",
                            "id",
                        ),
                    )

                    if identity is not None:
                        mapping[str(identity)] = strategy

    return mapping


def resolve_strategy(
    event: dict[str, Any],
    player_map: dict[str, str],
) -> str | None:
    direct = strategy_from_value(
        first(
            event,
            (
                "strategy_id",
                "strategy",
                "player_strategy",
                "actor_strategy",
                "agent",
                "policy",
            ),
        )
    )

    if direct is not None:
        return direct

    identity = first(
        event,
        (
            "player_id",
            "player_index",
            "seat",
            "seat_index",
            "actor_id",
            "actor",
            "owner_id",
            "payer_id",
        ),
    )

    if identity is not None:
        mapped = player_map.get(str(identity))

        if mapped is not None:
            return mapped

        direct = strategy_from_value(identity)

        if direct is not None:
            return direct

    return None


def classify(
    event: dict[str, Any],
) -> str:
    raw = first(
        event,
        (
            "event_type",
            "type",
            "event",
            "kind",
            "action",
            "name",
        ),
    )

    text = normalize_name(raw or "event")

    if "turn_start" in text:
        return "TURN_START"

    if "turn_end" in text:
        return "TURN_END"

    if "dice" in text and "roll" in text:
        return "DICE_ROLL"

    if text in {
        "roll",
        "dice",
    }:
        return "DICE_ROLL"

    if "bankrupt" in text:
        return "BANKRUPTCY"

    if "purchase_decision" in text:
        return "PURCHASE_DECISION"

    if "purchased" in text or text in {
        "purchase",
        "asset_purchase",
    }:
        return "PURCHASE"

    if "build" in text or "house" in text or "develop" in text:
        return "BUILD"

    if "monopoly" in text or "group_complete" in text:
        return "GROUP_COMPLETE"

    if "rent" in text:
        return "RENT"

    if "cash_transfer" in text or "payment" in text:
        return "CASH_TRANSFER"

    if "pass_go" in text or "passed_go" in text or "pass_start" in text:
        return "PASS_START"

    if text == "move" or "movement" in text:
        return "MOVE"

    if "event_draw" in text or "chance" in text or "community" in text:
        return "EVENT_DRAW"

    return "OTHER"


def extract_events(
    payload: Any,
) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]

    if isinstance(payload, dict):
        for key in (
            "events",
            "event_log",
            "records",
            "items",
        ):
            value = payload.get(key)

            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, dict)]

    raise RuntimeError("Representative event list not found.")


def normalize_events(
    payload: Any,
    representative_game: Any,
) -> tuple[SemanticEvent, ...]:
    player_map = build_player_map(representative_game)

    events = []

    for index, raw in enumerate(extract_events(payload)):
        dice = first(
            raw,
            (
                "dice",
                "dice_values",
                "roll",
            ),
        )

        die_1 = integer(
            first(
                raw,
                (
                    "die_1",
                    "die1",
                    "dice_1",
                    "first_die",
                ),
            )
        )

        die_2 = integer(
            first(
                raw,
                (
                    "die_2",
                    "die2",
                    "dice_2",
                    "second_die",
                ),
            )
        )

        if isinstance(dice, list) and len(dice) >= 2:
            die_1 = die_1 if die_1 is not None else integer(dice[0])

            die_2 = die_2 if die_2 is not None else integer(dice[1])

        from_position = integer(
            first(
                raw,
                (
                    "from_position",
                    "position_before",
                    "old_position",
                    "start_position",
                    "previous_position",
                    "from_space",
                ),
            )
        )

        to_position = integer(
            first(
                raw,
                (
                    "to_position",
                    "position_after",
                    "new_position",
                    "end_position",
                    "board_position",
                    "to_space",
                ),
            )
        )

        kind = classify(raw)

        space_index = integer(
            first(
                raw,
                (
                    "space_index",
                    "property_index",
                    "asset_index",
                    "board_index",
                    "space",
                ),
            )
        )

        if space_index is None and kind in {
            "PURCHASE",
            "BUILD",
            "RENT",
        }:
            space_index = to_position

        property_value = first(
            raw,
            (
                "property_name",
                "space_name",
                "asset_name",
            ),
        )

        events.append(
            SemanticEvent(
                index=index,
                kind=kind,
                strategy_id=resolve_strategy(
                    raw,
                    player_map,
                ),
                turn_number=integer(
                    first(
                        raw,
                        (
                            "turn_number",
                            "turn_index",
                            "turn",
                            "scheduled_turn",
                        ),
                    )
                ),
                from_position=from_position,
                to_position=to_position,
                die_1=die_1,
                die_2=die_2,
                amount=number(
                    first(
                        raw,
                        (
                            "amount",
                            "rent_amount",
                            "purchase_price",
                            "price",
                            "payment",
                            "cash_delta",
                        ),
                    )
                ),
                cash_after=number(
                    first(
                        raw,
                        (
                            "cash_after",
                            "cash_balance",
                            "balance_after",
                            "player_cash",
                        ),
                    )
                ),
                space_index=space_index,
                property_name=(str(property_value) if property_value is not None else None),
                houses_after=integer(
                    first(
                        raw,
                        (
                            "houses_after",
                            "house_count",
                            "houses",
                            "development_level",
                        ),
                    )
                ),
                raw=raw,
            )
        )

    return tuple(events)


def apply_event(
    state: MutableState,
    event: SemanticEvent,
) -> None:
    strategy = event.strategy_id

    if (
        strategy is not None
        and event.to_position is not None
        and event.kind
        in {
            "MOVE",
            "PASS_START",
        }
    ):
        state.positions[strategy] = event.to_position % 40

    if strategy is not None and event.cash_after is not None:
        state.cash[strategy] = event.cash_after

    if strategy is not None and event.kind == "PURCHASE" and event.space_index is not None:
        state.ownership[event.space_index] = strategy

    if event.kind == "BUILD" and event.space_index is not None:
        previous = state.houses.get(
            event.space_index,
            0,
        )

        state.houses[event.space_index] = (
            event.houses_after if event.houses_after is not None else previous + 1
        )

    if strategy is not None and event.kind == "BANKRUPTCY":
        state.bankrupt.add(strategy)


def build_turns(
    events: tuple[SemanticEvent, ...],
) -> tuple[TurnBeat, ...]:
    grouped: list[list[SemanticEvent]] = []

    current: list[SemanticEvent] = []

    current_turn = None

    for event in events:
        starts_new = bool(current) and (
            event.kind == "TURN_START"
            or (
                current_turn is not None
                and event.turn_number is not None
                and event.turn_number != current_turn
            )
        )

        if starts_new:
            grouped.append(current)
            current = []

        current.append(event)

        if event.turn_number is not None:
            current_turn = event.turn_number

        if event.kind == "TURN_END":
            grouped.append(current)
            current = []
            current_turn = None

    if current:
        grouped.append(current)

    state = MutableState()

    turns: list[TurnBeat] = []

    previous_strategy = None

    for group_index, group in enumerate(grouped):
        strategy = next(
            (event.strategy_id for event in group if event.strategy_id is not None),
            previous_strategy,
        )

        if strategy is None:
            continue

        previous_strategy = strategy

        normalized = tuple(
            event
            if event.strategy_id is not None
            else replace(
                event,
                strategy_id=strategy,
            )
            for event in group
        )

        before = freeze(state)

        for event in normalized:
            apply_event(
                state,
                event,
            )

        after = freeze(state)

        dice_event = next(
            (
                event
                for event in normalized
                if (
                    event.kind == "DICE_ROLL"
                    and event.die_1 is not None
                    and event.die_2 is not None
                )
            ),
            None,
        )

        move_event = next(
            (
                event
                for event in normalized
                if (
                    event.kind == "MOVE"
                    and event.from_position is not None
                    and event.to_position is not None
                )
            ),
            None,
        )

        priority = (
            "BANKRUPTCY",
            "BUILD",
            "GROUP_COMPLETE",
            "RENT",
            "PURCHASE",
            "EVENT_DRAW",
            "PASS_START",
            "CASH_TRANSFER",
            "PURCHASE_DECISION",
            "MOVE",
        )

        action = next(
            (kind for kind in priority if any(event.kind == kind for event in normalized)),
            "TURN",
        )

        action_event = next(
            (event for event in normalized if event.kind == action),
            normalized[-1],
        )

        turn_number = next(
            (event.turn_number for event in normalized if event.turn_number is not None),
            group_index + 1,
        )

        turns.append(
            TurnBeat(
                index=len(turns),
                turn_number=turn_number,
                strategy_id=strategy,
                events=normalized,
                state_before=before,
                state_after=after,
                dice=(
                    (
                        dice_event.die_1,
                        dice_event.die_2,
                    )
                    if (
                        dice_event is not None
                        and dice_event.die_1 is not None
                        and dice_event.die_2 is not None
                    )
                    else None
                ),
                from_position=(
                    move_event.from_position
                    if (move_event is not None and move_event.from_position is not None)
                    else before.positions[strategy]
                ),
                to_position=(
                    move_event.to_position
                    if (move_event is not None and move_event.to_position is not None)
                    else after.positions[strategy]
                ),
                primary_action=action,
                amount=action_event.amount,
                property_name=action_event.property_name,
                passes_start=any(event.kind == "PASS_START" for event in normalized),
                bankrupts=any(event.kind == "BANKRUPTCY" for event in normalized),
            )
        )

    if not turns:
        raise RuntimeError("No semantic turns were constructed.")

    return tuple(turns)


def select_highlights(
    turns: tuple[TurnBeat, ...],
    count: int = 6,
) -> tuple[TurnBeat, ...]:
    priority = {
        "BANKRUPTCY": 100,
        "BUILD": 90,
        "GROUP_COMPLETE": 85,
        "RENT": 80,
        "PURCHASE": 70,
        "EVENT_DRAW": 60,
        "PASS_START": 50,
        "CASH_TRANSFER": 40,
        "MOVE": 20,
        "TURN": 0,
    }

    candidates = sorted(
        range(len(turns)),
        key=lambda index: (
            -priority.get(
                turns[index].primary_action,
                0,
            ),
            index,
        ),
    )

    selected = sorted(candidates[:count])

    return tuple(turns[index] for index in selected)


def load_replay() -> tuple[
    tuple[SemanticEvent, ...],
    tuple[TurnBeat, ...],
    tuple[TurnBeat, ...],
]:
    root = Path("outputs/p02_monopoly_ai")

    manifest = json.loads(
        (root / "step8_input_manifest.json").read_text(
            encoding="utf-8",
        )
    )

    representative_game = json.loads(
        Path(manifest["representative_game"]).read_text(
            encoding="utf-8",
        )
    )

    payload = json.loads(
        Path(manifest["representative_events"]).read_text(
            encoding="utf-8",
        )
    )

    events = normalize_events(
        payload,
        representative_game,
    )

    turns = build_turns(events)

    return (
        events,
        turns,
        select_highlights(turns),
    )
