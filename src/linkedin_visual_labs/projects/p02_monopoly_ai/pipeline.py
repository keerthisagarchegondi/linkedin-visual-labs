"""Project 3 scaffold pipeline.

Gameplay begins in Step 3. This module only validates that the typed
Step 2 domain layer can be assembled from the frozen contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai.board import (
    build_board,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    DEFAULT_CONFIG_PATH,
    load_config,
)


@dataclass(frozen=True, slots=True)
class ScaffoldReport:
    project_id: str
    board_spaces: int
    purchasable_assets: int
    strategy_count: int
    tournament_games: int


def validate_scaffold(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> ScaffoldReport:
    """Load contract and build immutable definitions."""

    config = load_config(config_path)

    board = build_board(config)

    purchasable = sum(1 for space in board.spaces if space.asset is not None)

    return ScaffoldReport(
        project_id=config.project_id,
        board_spaces=board.size,
        purchasable_assets=purchasable,
        strategy_count=len(config.strategies),
        tournament_games=config.tournament.game_count,
    )
