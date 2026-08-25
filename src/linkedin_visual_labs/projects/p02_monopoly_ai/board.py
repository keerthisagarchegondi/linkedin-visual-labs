"""Board construction from the frozen Project 3 contract."""

from __future__ import annotations

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
    """Build the immutable canonical board definition."""

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

    jail_indices = [space.index for space in spaces if space.space_type is SpaceType.JAIL]

    if jail_indices != [10]:
        raise ValueError("canonical board requires Jail at index 10")

    return BoardDefinition(
        spaces=tuple(spaces),
        jail_index=10,
    )
