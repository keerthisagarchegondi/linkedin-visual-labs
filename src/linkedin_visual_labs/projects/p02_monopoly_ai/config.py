"""Typed configuration loading for Project 3."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import yaml

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    PropertyGroupId,
    SpaceType,
    StrategyId,
)

DEFAULT_CONFIG_PATH = Path("configs/p02_monopoly_ai.yaml")


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    board_size: int
    starting_cash: int
    go_salary: int
    dice_count: int
    die_sides: int
    maximum_turns: int


@dataclass(frozen=True, slots=True)
class PropertyGroupConfig:
    group_id: PropertyGroupId
    label: str
    property_count: int
    house_cost: int


@dataclass(frozen=True, slots=True)
class BoardSpaceConfig:
    index: int
    space_id: str
    name: str
    space_type: SpaceType
    group_id: PropertyGroupId | None = None
    price: int | None = None
    base_rent: int | None = None
    amount: int | None = None


@dataclass(frozen=True, slots=True)
class StrategyPolicyConfig:
    strategy_id: StrategyId
    label: str
    desired_cash_reserve: int
    development_cash_reserve: int
    maximum_builds_per_turn: int


@dataclass(frozen=True, slots=True)
class TournamentConfig:
    game_count: int
    master_seed: int
    result_rows: int
    players_per_game: int


@dataclass(frozen=True, slots=True)
class MediaConfig:
    width: int
    height: int
    fps: int
    duration_seconds: float
    frame_count: int
    codec: str
    pixel_format: str


@dataclass(frozen=True, slots=True)
class MonopolyConfig:
    project_id: str
    viewer_question: str
    disclaimer: str
    simulation: SimulationConfig
    property_groups: tuple[PropertyGroupConfig, ...]
    board_spaces: tuple[BoardSpaceConfig, ...]
    strategies: tuple[StrategyPolicyConfig, ...]
    tournament: TournamentConfig
    media: MediaConfig
    raw: Mapping[str, object]


def _require_mapping(
    value: object,
    *,
    name: str,
) -> dict[str, object]:
    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(f"{name} must be a mapping")

    return {str(key): item for key, item in value.items()}


def _require_list(
    value: object,
    *,
    name: str,
) -> list[object]:
    if not isinstance(
        value,
        list,
    ):
        raise ValueError(f"{name} must be a list")

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


def load_config(
    path: Path = DEFAULT_CONFIG_PATH,
) -> MonopolyConfig:
    """Load and validate the frozen Project 3 YAML contract."""

    if not path.is_file():
        raise FileNotFoundError(f"Project 3 config missing: {path}")

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))

    raw = _require_mapping(
        loaded,
        name="root",
    )

    project = _require_mapping(
        raw.get("project"),
        name="project",
    )

    simulation_raw = _require_mapping(
        raw.get("simulation"),
        name="simulation",
    )

    simulation = SimulationConfig(
        board_size=_integer(
            simulation_raw.get("board_size"),
            name="simulation.board_size",
        ),
        starting_cash=_integer(
            simulation_raw.get("starting_cash"),
            name="simulation.starting_cash",
        ),
        go_salary=_integer(
            simulation_raw.get("go_salary"),
            name="simulation.go_salary",
        ),
        dice_count=_integer(
            simulation_raw.get("dice_count"),
            name="simulation.dice_count",
        ),
        die_sides=_integer(
            simulation_raw.get("die_sides"),
            name="simulation.die_sides",
        ),
        maximum_turns=_integer(
            simulation_raw.get("maximum_turns"),
            name="simulation.maximum_turns",
        ),
    )

    group_items = _require_list(
        raw.get("property_groups"),
        name="property_groups",
    )

    groups: list[PropertyGroupConfig] = []

    for index, item in enumerate(group_items):
        group = _require_mapping(
            item,
            name=f"property_groups[{index}]",
        )

        groups.append(
            PropertyGroupConfig(
                group_id=PropertyGroupId(
                    _text(
                        group.get("group_id"),
                        name="group_id",
                    )
                ),
                label=_text(
                    group.get("label"),
                    name="label",
                ),
                property_count=_integer(
                    group.get("property_count"),
                    name="property_count",
                ),
                house_cost=_integer(
                    group.get("house_cost"),
                    name="house_cost",
                ),
            )
        )

    board_raw = _require_mapping(
        raw.get("board"),
        name="board",
    )

    space_items = _require_list(
        board_raw.get("spaces"),
        name="board.spaces",
    )

    board_spaces: list[BoardSpaceConfig] = []

    for item in space_items:
        space = _require_mapping(
            item,
            name="board space",
        )

        group_value = space.get("group_id")

        price_value = space.get("price")

        rent_value = space.get("base_rent")

        amount_value = space.get("amount")

        board_spaces.append(
            BoardSpaceConfig(
                index=_integer(
                    space.get("index"),
                    name="space.index",
                ),
                space_id=_text(
                    space.get("space_id"),
                    name="space.space_id",
                ),
                name=_text(
                    space.get("name"),
                    name="space.name",
                ),
                space_type=SpaceType(
                    _text(
                        space.get("type"),
                        name="space.type",
                    )
                ),
                group_id=(
                    PropertyGroupId(
                        _text(
                            group_value,
                            name="space.group_id",
                        )
                    )
                    if group_value is not None
                    else None
                ),
                price=(
                    _integer(
                        price_value,
                        name="space.price",
                    )
                    if price_value is not None
                    else None
                ),
                base_rent=(
                    _integer(
                        rent_value,
                        name="space.base_rent",
                    )
                    if rent_value is not None
                    else None
                ),
                amount=(
                    _integer(
                        amount_value,
                        name="space.amount",
                    )
                    if amount_value is not None
                    else None
                ),
            )
        )

    strategies_raw = _require_mapping(
        raw.get("strategies"),
        name="strategies",
    )

    order = _require_list(
        strategies_raw.get("canonical_order"),
        name="strategies.canonical_order",
    )

    policies = _require_mapping(
        strategies_raw.get("policies"),
        name="strategies.policies",
    )

    strategies: list[StrategyPolicyConfig] = []

    for strategy_value in order:
        strategy_id = StrategyId(
            _text(
                strategy_value,
                name="strategy ID",
            )
        )

        policy = _require_mapping(
            policies.get(strategy_id.value),
            name=f"policy {strategy_id.value}",
        )

        development = _require_mapping(
            policy.get("development"),
            name="strategy.development",
        )

        strategies.append(
            StrategyPolicyConfig(
                strategy_id=strategy_id,
                label=_text(
                    policy.get("label"),
                    name="strategy.label",
                ),
                desired_cash_reserve=_integer(
                    policy.get("desired_cash_reserve"),
                    name="desired_cash_reserve",
                ),
                development_cash_reserve=_integer(
                    policy.get("development_cash_reserve"),
                    name="development_cash_reserve",
                ),
                maximum_builds_per_turn=_integer(
                    development.get("maximum_builds_per_turn"),
                    name="maximum_builds_per_turn",
                ),
            )
        )

    tournament_raw = _require_mapping(
        raw.get("tournament_contract"),
        name="tournament_contract",
    )

    tournament = TournamentConfig(
        game_count=_integer(
            tournament_raw.get("canonical_game_count"),
            name="canonical_game_count",
        ),
        master_seed=_integer(
            tournament_raw.get("canonical_master_seed"),
            name="canonical_master_seed",
        ),
        result_rows=_integer(
            tournament_raw.get("canonical_result_rows"),
            name="canonical_result_rows",
        ),
        players_per_game=_integer(
            tournament_raw.get("players_per_game"),
            name="players_per_game",
        ),
    )

    media_raw = _require_mapping(
        raw.get("media_contract"),
        name="media_contract",
    )

    duration_value = media_raw.get("duration_seconds")

    if not isinstance(
        duration_value,
        (int, float),
    ) or isinstance(
        duration_value,
        bool,
    ):
        raise ValueError("media duration must be numeric")

    media = MediaConfig(
        width=_integer(
            media_raw.get("width"),
            name="media.width",
        ),
        height=_integer(
            media_raw.get("height"),
            name="media.height",
        ),
        fps=_integer(
            media_raw.get("fps"),
            name="media.fps",
        ),
        duration_seconds=float(duration_value),
        frame_count=_integer(
            media_raw.get("frame_count"),
            name="media.frame_count",
        ),
        codec=_text(
            media_raw.get("codec"),
            name="media.codec",
        ),
        pixel_format=_text(
            media_raw.get("pixel_format"),
            name="media.pixel_format",
        ),
    )

    config = MonopolyConfig(
        project_id=_text(
            project.get("project_id"),
            name="project.project_id",
        ),
        viewer_question=_text(
            project.get("viewer_question"),
            name="project.viewer_question",
        ),
        disclaimer=_text(
            project.get("disclaimer"),
            name="project.disclaimer",
        ),
        simulation=simulation,
        property_groups=tuple(groups),
        board_spaces=tuple(board_spaces),
        strategies=tuple(strategies),
        tournament=tournament,
        media=media,
        raw=raw,
    )

    validate_config(config)

    return config


def validate_config(
    config: MonopolyConfig,
) -> None:
    """Validate invariants already frozen in Step 1."""

    if config.project_id != "p02_monopoly_ai":
        raise ValueError("unexpected Project 3 project_id")

    if config.simulation.board_size != 40:
        raise ValueError("canonical board size must equal 40")

    if len(config.board_spaces) != config.simulation.board_size:
        raise ValueError("board-space count does not match board_size")

    if tuple(space.index for space in config.board_spaces) != tuple(range(40)):
        raise ValueError("board indices must equal 0..39")

    ids = [space.space_id for space in config.board_spaces]

    if len(ids) != len(set(ids)):
        raise ValueError("duplicate board space_id")

    if len(config.property_groups) != 8:
        raise ValueError("canonical game requires eight property groups")

    if len(config.strategies) != 4:
        raise ValueError("canonical game requires four strategies")

    if config.tournament.game_count != 10000:
        raise ValueError("canonical tournament requires 10,000 games")

    if config.tournament.result_rows != 40000:
        raise ValueError("canonical tournament requires 40,000 result rows")

    if config.media.frame_count != (config.media.fps * int(config.media.duration_seconds)):
        raise ValueError("media frame count does not match FPS x duration")
