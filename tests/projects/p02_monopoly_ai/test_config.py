"""Configuration loading tests."""

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    load_config,
)

CONFIG = Path("configs/p02_monopoly_ai.yaml")


def test_canonical_config_loads() -> None:
    config = load_config(CONFIG)

    assert config.project_id == "p02_monopoly_ai"
    assert config.simulation.board_size == 40
    assert config.simulation.starting_cash == 1500
    assert config.simulation.maximum_turns == 500

    assert len(config.property_groups) == 8

    assert len(config.board_spaces) == 40

    assert len(config.strategies) == 4

    assert config.tournament.game_count == 10000
    assert config.tournament.result_rows == 40000

    assert config.media.width == 1080
    assert config.media.height == 1080
    assert config.media.fps == 30
    assert config.media.frame_count == 1800


def test_missing_config_fails(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.yaml")


def test_invalid_root_fails(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.yaml"

    path.write_text(
        "- not\n- a\n- mapping\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="root must be a mapping",
    ):
        load_config(path)


def test_wrong_board_size_fails(
    tmp_path: Path,
) -> None:
    text = CONFIG.read_text(encoding="utf-8").replace(
        "board_size: 40",
        "board_size: 39",
        1,
    )

    path = tmp_path / "invalid_board.yaml"

    path.write_text(
        text,
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="board size",
    ):
        load_config(path)
