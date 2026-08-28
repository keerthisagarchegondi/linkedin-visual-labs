"""Deterministic JSON serialization for Project 3."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    GamePhase,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    GameState,
    JailState,
    PlayerState,
    PropertyState,
)


def _require_int(
    value: object,
    *,
    name: str,
) -> int:
    """Return an integer after explicit runtime narrowing."""

    if not isinstance(
        value,
        int,
    ) or isinstance(
        value,
        bool,
    ):
        raise ValueError(f"{name} must be an integer")

    return value


def _require_bool(
    value: object,
    *,
    name: str,
) -> bool:
    """Return a boolean after explicit runtime narrowing."""

    if not isinstance(
        value,
        bool,
    ):
        raise ValueError(f"{name} must be a boolean")

    return value


def _require_str(
    value: object,
    *,
    name: str,
) -> str:
    """Return a string after explicit runtime narrowing."""

    if not isinstance(
        value,
        str,
    ):
        raise ValueError(f"{name} must be a string")

    return value


def to_primitive(
    value: object,
) -> object:
    """Convert supported domain objects to JSON-compatible values."""

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if is_dataclass(value):
        return {
            field_.name: to_primitive(
                getattr(
                    value,
                    field_.name,
                )
            )
            for field_ in fields(value)
        }

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): to_primitive(item)
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(pair[0]),
            )
        }

    if isinstance(
        value,
        (tuple, list),
    ):
        return [to_primitive(item) for item in value]

    if (
        isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        )
        or value is None
    ):
        return value

    raise TypeError(f"unsupported serialization type: {type(value)!r}")


def dumps(
    value: object,
) -> str:
    """Serialize deterministically."""

    return json.dumps(
        to_primitive(value),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
    )


def game_state_from_dict(
    payload: Mapping[str, object],
) -> GameState:
    """Deserialize the mutable game-state scaffold."""

    players_raw = payload.get("players")

    properties_raw = payload.get("properties")

    if not isinstance(
        players_raw,
        Mapping,
    ):
        raise ValueError("players must be a mapping")

    if not isinstance(
        properties_raw,
        Mapping,
    ):
        raise ValueError("properties must be a mapping")

    players: dict[
        str,
        PlayerState,
    ] = {}

    for player_key, raw in players_raw.items():
        if not isinstance(
            raw,
            Mapping,
        ):
            raise ValueError("player payload must be a mapping")

        jail_raw = raw.get("jail")

        if not isinstance(
            jail_raw,
            Mapping,
        ):
            raise ValueError("jail payload must be a mapping")

        owned = raw.get("owned_asset_ids")

        if not isinstance(
            owned,
            list,
        ):
            raise ValueError("owned_asset_ids must be a list")

        owned_asset_ids: list[str] = []

        for index, item in enumerate(owned):
            owned_asset_ids.append(
                _require_str(
                    item,
                    name=(f"owned_asset_ids[{index}]"),
                )
            )

        bankruptcy_value = raw.get("bankruptcy_turn")

        player_id = _require_str(
            raw.get("player_id"),
            name="player_id",
        )

        players[str(player_key)] = PlayerState(
            player_id=player_id,
            strategy_id=StrategyId(
                _require_str(
                    raw.get("strategy_id"),
                    name="strategy_id",
                )
            ),
            seat_index=_require_int(
                raw.get("seat_index"),
                name="seat_index",
            ),
            cash=_require_int(
                raw.get("cash"),
                name="cash",
            ),
            position=_require_int(
                raw.get("position"),
                name="position",
            ),
            owned_asset_ids=owned_asset_ids,
            jail=JailState(
                turns_remaining=_require_int(
                    jail_raw.get("turns_remaining"),
                    name="jail.turns_remaining",
                )
            ),
            bankrupt=_require_bool(
                raw.get("bankrupt"),
                name="bankrupt",
            ),
            bankruptcy_turn=(
                _require_int(
                    bankruptcy_value,
                    name="bankruptcy_turn",
                )
                if bankruptcy_value is not None
                else None
            ),
            total_rent_paid=_require_int(
                raw.get("total_rent_paid"),
                name="total_rent_paid",
            ),
            total_rent_collected=_require_int(
                raw.get("total_rent_collected"),
                name="total_rent_collected",
            ),
            minimum_cash_observed=_require_int(
                raw.get("minimum_cash_observed"),
                name="minimum_cash_observed",
            ),
        )

    properties: dict[
        str,
        PropertyState,
    ] = {}

    for asset_key, raw in properties_raw.items():
        if not isinstance(
            raw,
            Mapping,
        ):
            raise ValueError("property payload must be a mapping")

        owner = raw.get("owner_id")

        properties[str(asset_key)] = PropertyState(
            asset_id=_require_str(
                raw.get("asset_id"),
                name="asset_id",
            ),
            owner_id=(
                _require_str(
                    owner,
                    name="owner_id",
                )
                if owner is not None
                else None
            ),
            house_count=_require_int(
                raw.get("house_count"),
                name="house_count",
            ),
        )

    return GameState(
        game_id=_require_str(
            payload.get("game_id"),
            name="game_id",
        ),
        game_index=_require_int(
            payload.get("game_index"),
            name="game_index",
        ),
        game_seed=_require_int(
            payload.get("game_seed"),
            name="game_seed",
        ),
        phase=GamePhase(
            _require_str(
                payload.get("phase"),
                name="phase",
            )
        ),
        turn_number=_require_int(
            payload.get("turn_number"),
            name="turn_number",
        ),
        active_player_index=_require_int(
            payload.get("active_player_index"),
            name="active_player_index",
        ),
        players=players,
        properties=properties,
        event_index=_require_int(
            payload.get("event_index"),
            name="event_index",
        ),
    )


def loads_game_state(
    text: str,
) -> GameState:
    """Deserialize GameState from deterministic JSON."""

    raw = json.loads(text)

    if not isinstance(
        raw,
        dict,
    ):
        raise ValueError("game state JSON must contain an object")

    return game_state_from_dict(raw)
