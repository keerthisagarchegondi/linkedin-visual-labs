"""Canonical analytical board construction and validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    SpaceType,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    BoardDefinition,
    BoardSpace,
    PropertyDefinition,
)


def _require_mapping(
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


def _require_int(
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


def build_board(
    config: MonopolyConfig,
) -> BoardDefinition:
    """Build the immutable canonical analytical board."""

    groups = {group.group_id: group for group in config.property_groups}

    transit_rules = _require_mapping(
        config.raw.get("transit_rules"),
        name="transit_rules",
    )

    utility_rules = _require_mapping(
        config.raw.get("utility_rules"),
        name="utility_rules",
    )

    transit_price = _require_int(
        transit_rules.get("purchase_price"),
        name="transit_rules.purchase_price",
    )

    utility_price = _require_int(
        utility_rules.get("purchase_price"),
        name="utility_rules.purchase_price",
    )

    spaces: list[BoardSpace] = []

    for item in config.board_spaces:
        asset = None

        if item.space_type is SpaceType.PROPERTY:
            if item.group_id is None:
                raise ValueError(f"{item.space_id}: missing group")

            if item.price is None:
                raise ValueError(f"{item.space_id}: missing price")

            if item.base_rent is None:
                raise ValueError(f"{item.space_id}: missing rent")

            group = groups[item.group_id]

            asset = PropertyDefinition(
                asset_id=item.space_id,
                board_index=item.index,
                name=item.name,
                space_type=item.space_type,
                purchase_price=item.price,
                base_rent=item.base_rent,
                group_id=item.group_id,
                house_cost=group.house_cost,
            )

        elif item.space_type is SpaceType.TRANSIT:
            asset = PropertyDefinition(
                asset_id=item.space_id,
                board_index=item.index,
                name=item.name,
                space_type=item.space_type,
                purchase_price=transit_price,
            )

        elif item.space_type is SpaceType.UTILITY:
            asset = PropertyDefinition(
                asset_id=item.space_id,
                board_index=item.index,
                name=item.name,
                space_type=item.space_type,
                purchase_price=utility_price,
            )

        spaces.append(
            BoardSpace(
                index=item.index,
                space_id=item.space_id,
                name=item.name,
                space_type=item.space_type,
                asset=asset,
                amount=item.amount,
            )
        )

    board = BoardDefinition(
        spaces=tuple(spaces),
        jail_index=10,
    )

    validate_board_definition(
        board,
        config,
    )

    return board


def validate_board_definition(
    board: BoardDefinition,
    config: MonopolyConfig,
) -> None:
    """Validate the frozen Project 3 board topology."""

    if board.size != 40:
        raise ValueError("canonical board must contain 40 spaces")

    if tuple(space.index for space in board.spaces) != tuple(range(40)):
        raise ValueError("board indices must equal 0..39")

    if board.spaces[0].space_type is not SpaceType.GO:
        raise ValueError("space 0 must be GO")

    if board.spaces[10].space_type is not SpaceType.JAIL:
        raise ValueError("space 10 must be JAIL")

    if board.spaces[30].space_type is not SpaceType.GO_TO_JAIL:
        raise ValueError("space 30 must be GO_TO_JAIL")

    taxonomy = Counter(space.space_type.value for space in board.spaces)

    expected = {
        str(key): int(value)
        for key, value in (
            config.raw["board_space_taxonomy"].items()
            if isinstance(
                config.raw["board_space_taxonomy"],
                Mapping,
            )
            else ()
        )
    }

    if dict(taxonomy) != expected:
        raise ValueError("board taxonomy does not match contract")

    assets = [space.asset for space in board.spaces if space.asset is not None]

    if len(assets) != 28:
        raise ValueError("canonical board must contain 28 purchasable assets")

    asset_ids = [asset.asset_id for asset in assets]

    if len(asset_ids) != len(set(asset_ids)):
        raise ValueError("purchasable asset IDs must be unique")

    color_properties = [asset for asset in assets if asset.space_type is SpaceType.PROPERTY]

    if len(color_properties) != 22:
        raise ValueError("canonical board requires 22 color properties")

    actual_group_counts = Counter(asset.group_id for asset in color_properties)

    configured_group_counts = {
        group.group_id: group.property_count for group in config.property_groups
    }

    if dict(actual_group_counts) != configured_group_counts:
        raise ValueError("property-group membership does not match contract")
