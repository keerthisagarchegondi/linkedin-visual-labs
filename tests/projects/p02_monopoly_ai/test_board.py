"""Immutable board-construction tests."""

from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai.board import (
    build_board,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    load_config,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    SpaceType,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    BoardDefinition,
)


def _board() -> BoardDefinition:
    return build_board(load_config(Path("configs/p02_monopoly_ai.yaml")))


def test_board_has_exactly_40_spaces() -> None:
    board = _board()

    assert board.size == 40

    assert [space.index for space in board.spaces] == list(range(40))


def test_board_has_exactly_28_purchasable_assets() -> None:
    board = _board()

    assets = [space.asset for space in board.spaces if space.asset is not None]

    assert len(assets) == 28


def test_board_has_jail_at_index_10() -> None:
    board = _board()

    assert board.jail_index == 10

    assert board.spaces[10].space_type is SpaceType.JAIL


def test_color_properties_have_groups_and_house_costs() -> None:
    board = _board()

    properties = [
        space.asset
        for space in board.spaces
        if (space.asset is not None and space.asset.space_type is SpaceType.PROPERTY)
    ]

    assert len(properties) == 22

    assert all(property_.group_id is not None for property_ in properties)

    assert all(property_.house_cost is not None for property_ in properties)
