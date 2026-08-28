"""Deterministic Monte Carlo tournament for Project 3."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from statistics import mean, median

from linkedin_visual_labs.projects.p02_monopoly_ai.board import (
    build_board,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    EventType,
    GamePhase,
    PropertyGroupId,
    SpaceType,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.engine import (
    SimulationResult,
    simulate_game,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.models import (
    PropertyDefinition,
    TournamentGameRecord,
    TurnEvent,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.progress import (
    TournamentProgressReporter,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.randomness import (
    derive_game_seed,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.serialization import (
    to_primitive,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.strategies import (
    build_strategy_registry,
)


def _require_number(
    value: object,
    *,
    name: str,
) -> float:
    """Return a finite numeric value after explicit narrowing."""

    if not isinstance(
        value,
        (int, float),
    ) or isinstance(
        value,
        bool,
    ):
        raise ValueError(f"{name} must be numeric")

    result = float(value)

    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")

    return result


CANONICAL_SEAT_CYCLE: tuple[
    tuple[
        StrategyId,
        StrategyId,
        StrategyId,
        StrategyId,
    ],
    ...,
] = (
    (
        StrategyId.COLLECTOR,
        StrategyId.SPECIALIST,
        StrategyId.CASH_PROTECTOR,
        StrategyId.AGGRESSIVE_BUILDER,
    ),
    (
        StrategyId.SPECIALIST,
        StrategyId.CASH_PROTECTOR,
        StrategyId.AGGRESSIVE_BUILDER,
        StrategyId.COLLECTOR,
    ),
    (
        StrategyId.CASH_PROTECTOR,
        StrategyId.AGGRESSIVE_BUILDER,
        StrategyId.COLLECTOR,
        StrategyId.SPECIALIST,
    ),
    (
        StrategyId.AGGRESSIVE_BUILDER,
        StrategyId.COLLECTOR,
        StrategyId.SPECIALIST,
        StrategyId.CASH_PROTECTOR,
    ),
    (
        StrategyId.COLLECTOR,
        StrategyId.AGGRESSIVE_BUILDER,
        StrategyId.CASH_PROTECTOR,
        StrategyId.SPECIALIST,
    ),
    (
        StrategyId.AGGRESSIVE_BUILDER,
        StrategyId.CASH_PROTECTOR,
        StrategyId.SPECIALIST,
        StrategyId.COLLECTOR,
    ),
    (
        StrategyId.CASH_PROTECTOR,
        StrategyId.SPECIALIST,
        StrategyId.COLLECTOR,
        StrategyId.AGGRESSIVE_BUILDER,
    ),
    (
        StrategyId.SPECIALIST,
        StrategyId.COLLECTOR,
        StrategyId.AGGRESSIVE_BUILDER,
        StrategyId.CASH_PROTECTOR,
    ),
)


@dataclass(frozen=True, slots=True)
class TournamentRunConfig:
    """Execution configuration for one tournament invocation."""

    game_count: int
    master_seed: int
    output_directory: Path

    # Interactive reporting only.
    # These fields never participate in simulation determinism.
    show_progress: bool = False
    progress_every: int = 100

    def __post_init__(self) -> None:
        if self.game_count <= 0:
            raise ValueError("game_count must be positive")

        if self.master_seed < 0:
            raise ValueError("master_seed cannot be negative")

        if self.progress_every <= 0:
            raise ValueError("progress_every must be positive")


@dataclass(frozen=True, slots=True)
class TournamentGameSpec:
    """Immutable specification for one tournament game."""

    game_index: int
    game_seed: int
    seat_assignment: tuple[
        StrategyId,
        StrategyId,
        StrategyId,
        StrategyId,
    ]


@dataclass(frozen=True, slots=True)
class TournamentArtifacts:
    """Paths produced by one tournament run."""

    results_csv: Path
    summary_json: Path
    representative_json: Path
    representative_events_json: Path


def seat_assignment_for_game(
    game_index: int,
) -> tuple[
    StrategyId,
    StrategyId,
    StrategyId,
    StrategyId,
]:
    """Return canonical deterministic seat assignment."""

    if game_index < 0:
        raise ValueError("game_index cannot be negative")

    return CANONICAL_SEAT_CYCLE[game_index % len(CANONICAL_SEAT_CYCLE)]


def tournament_game_specs(
    *,
    game_count: int,
    master_seed: int,
) -> Iterable[TournamentGameSpec]:
    """Yield deterministic game specifications lazily."""

    for game_index in range(game_count):
        yield TournamentGameSpec(
            game_index=game_index,
            game_seed=derive_game_seed(
                master_seed,
                game_index,
            ),
            seat_assignment=(seat_assignment_for_game(game_index)),
        )


def validate_seat_balance(
    *,
    game_count: int,
) -> dict[
    StrategyId,
    dict[int, int],
]:
    """Validate deterministic strategy-by-seat balance."""

    if game_count <= 0:
        raise ValueError("game_count must be positive")

    counts: dict[
        StrategyId,
        dict[int, int],
    ] = {strategy_id: {seat: 0 for seat in range(4)} for strategy_id in StrategyId}

    for game_index in range(game_count):
        assignment = seat_assignment_for_game(game_index)

        if set(assignment) != set(StrategyId):
            raise ValueError("seat assignment must contain each strategy exactly once")

        for seat_index, strategy_id in enumerate(assignment):
            counts[strategy_id][seat_index] += 1

    # Every strategy participates exactly once in every game.
    for strategy_id in StrategyId:
        total = sum(counts[strategy_id].values())

        if total != game_count:
            raise ValueError("strategy game count mismatch")

    # For arbitrary game counts, the deterministic cycle may be
    # incomplete. No strategy-seat cell may differ from another
    # by more than one appearance.
    values = [count for seat_counts in counts.values() for count in seat_counts.values()]

    if max(values) - min(values) > 1:
        raise ValueError("seat schedule is not balanced")

    # Any complete eight-game cycle is perfectly balanced:
    #
    #   each strategy plays game_count games total
    #   spread over four seats
    #   => game_count / 4 appearances per seat.
    if game_count % len(CANONICAL_SEAT_CYCLE) == 0:
        expected_per_seat = game_count // 4

        for strategy_id in StrategyId:
            for seat in range(4):
                actual = counts[strategy_id][seat]

                if actual != expected_per_seat:
                    raise ValueError(
                        "exact seat balance mismatch: "
                        f"{strategy_id.value} "
                        f"seat={seat} "
                        f"actual={actual} "
                        f"expected={expected_per_seat}"
                    )

    return counts


def _asset_maps(
    config: MonopolyConfig,
) -> tuple[
    dict[str, PropertyDefinition],
    dict[
        PropertyGroupId,
        tuple[str, ...],
    ],
]:
    board = build_board(config)

    asset_definitions = {
        space.asset.asset_id: space.asset for space in board.spaces if space.asset is not None
    }

    groups: dict[
        PropertyGroupId,
        list[str],
    ] = defaultdict(list)

    for asset in asset_definitions.values():
        if asset.group_id is not None:
            groups[asset.group_id].append(asset.asset_id)

    return (
        asset_definitions,
        {group_id: tuple(asset_ids) for group_id, asset_ids in groups.items()},
    )


def _strategy_reserves(
    config: MonopolyConfig,
) -> dict[
    StrategyId,
    int,
]:
    return {strategy.strategy_id: (strategy.desired_cash_reserve) for strategy in config.strategies}


def _terminal_net_worth(
    *,
    config: MonopolyConfig,
    result: SimulationResult,
    player_id: str,
) -> int:
    board = build_board(config)

    definitions = {
        space.asset.asset_id: space.asset for space in board.spaces if space.asset is not None
    }

    player = result.final_state.players[player_id]

    value = player.cash

    for asset_id in player.owned_asset_ids:
        definition = definitions[asset_id]

        property_state = result.final_state.properties[asset_id]

        value += definition.purchase_price

        if definition.house_cost is not None:
            value += property_state.house_count * definition.house_cost

    return value


def _group_completion_metrics(
    *,
    config: MonopolyConfig,
    events: tuple[
        TurnEvent,
        ...,
    ],
) -> tuple[
    dict[str, int],
    dict[str, int | None],
]:
    """Replay ownership-changing events to detect group completion."""

    board = build_board(config)

    group_assets: dict[
        PropertyGroupId,
        tuple[str, ...],
    ] = {}

    intermediate: dict[
        PropertyGroupId,
        list[str],
    ] = defaultdict(list)

    for space in board.spaces:
        if space.asset is None or space.asset.group_id is None:
            continue

        intermediate[space.asset.group_id].append(space.asset.asset_id)

    group_assets = {group_id: tuple(assets) for group_id, assets in intermediate.items()}

    owners: dict[
        str,
        str | None,
    ] = {space.asset.asset_id: None for space in board.spaces if space.asset is not None}

    completed: dict[
        str,
        set[PropertyGroupId],
    ] = defaultdict(set)

    first_completion: dict[
        str,
        int,
    ] = {}

    def detect(
        player_id: str,
        turn_number: int,
    ) -> None:
        for group_id, asset_ids in group_assets.items():
            if group_id in completed[player_id]:
                continue

            if all(owners[asset_id] == player_id for asset_id in asset_ids):
                completed[player_id].add(group_id)

                first_completion.setdefault(
                    player_id,
                    turn_number,
                )

    for event in events:
        if (
            event.event_type is EventType.ASSET_PURCHASED
            and event.asset_id is not None
            and event.player_id is not None
        ):
            owners[event.asset_id] = event.player_id

            detect(
                event.player_id,
                event.turn_number,
            )

        elif event.event_type is EventType.ASSET_TRANSFER and event.asset_id is not None:
            owners[event.asset_id] = event.counterparty_player_id

            if event.counterparty_player_id is not None:
                detect(
                    event.counterparty_player_id,
                    event.turn_number,
                )

    player_ids = {event.player_id for event in events if event.player_id is not None}

    return (
        {player_id: len(completed[player_id]) for player_id in player_ids},
        {player_id: first_completion.get(player_id) for player_id in player_ids},
    )


def records_from_simulation(
    *,
    config: MonopolyConfig,
    simulation: SimulationResult,
) -> tuple[
    TournamentGameRecord,
    ...,
]:
    """Convert one complete simulation into four canonical records."""

    board = build_board(config)

    definitions = {
        space.asset.asset_id: space.asset for space in board.spaces if space.asset is not None
    }

    reserves = _strategy_reserves(config)

    groups: dict[
        PropertyGroupId,
        tuple[str, ...],
    ] = {}

    group_lists: dict[
        PropertyGroupId,
        list[str],
    ] = defaultdict(list)

    for definition in definitions.values():
        if definition.group_id is not None:
            group_lists[definition.group_id].append(definition.asset_id)

    groups = {group_id: tuple(asset_ids) for group_id, asset_ids in group_lists.items()}

    purchases: Counter[str] = Counter()

    color_purchases: Counter[str] = Counter()

    transit_purchases: Counter[str] = Counter()

    utility_purchases: Counter[str] = Counter()

    houses_built: Counter[str] = Counter()

    first_house_turn: dict[
        str,
        int,
    ] = {}

    for event in simulation.events:
        if event.player_id is None:
            continue

        if event.event_type is EventType.ASSET_PURCHASED and event.asset_id is not None:
            purchases[event.player_id] += 1

            definition = definitions[event.asset_id]

            if definition.space_type is SpaceType.PROPERTY:
                color_purchases[event.player_id] += 1

            elif definition.space_type is SpaceType.TRANSIT:
                transit_purchases[event.player_id] += 1

            elif definition.space_type is SpaceType.UTILITY:
                utility_purchases[event.player_id] += 1

        elif event.event_type is EventType.HOUSE_BUILT:
            houses_built[event.player_id] += 1

            first_house_turn.setdefault(
                event.player_id,
                event.turn_number,
            )

    (
        groups_completed,
        first_group_turn,
    ) = _group_completion_metrics(
        config=config,
        events=simulation.events,
    )

    records: list[TournamentGameRecord] = []

    for player_id, player in sorted(
        simulation.final_state.players.items(),
        key=lambda pair: pair[1].seat_index,
    ):
        owned_assets = tuple(player.owned_asset_ids)

        complete_at_finish = sum(
            1
            for asset_ids in groups.values()
            if all(
                simulation.final_state.properties[asset_id].owner_id == player_id
                for asset_id in asset_ids
            )
        )

        houses_at_finish = sum(
            simulation.final_state.properties[asset_id].house_count for asset_id in owned_assets
        )

        own_turn_cash = [
            dict(snapshot.player_cash)[player_id]
            for snapshot in simulation.snapshots
            if (snapshot.active_player_index == player.seat_index)
        ]

        if not own_turn_cash:
            own_turn_cash = [player.cash]

        desired_reserve = reserves[player.strategy_id]

        record = TournamentGameRecord(
            game_id=(simulation.result.game_id),
            game_index=(simulation.result.game_index),
            game_seed=(simulation.result.game_seed),
            strategy_id=player.strategy_id,
            seat_index=player.seat_index,
            finishing_position=(simulation.result.finishing_positions[player_id]),
            won=(simulation.result.winner_player_id == player_id),
            bankrupt=player.bankrupt,
            bankruptcy_turn=(player.bankruptcy_turn),
            finishing_cash=(0 if player.bankrupt else player.cash),
            terminal_net_worth=(
                _terminal_net_worth(
                    config=config,
                    result=simulation,
                    player_id=player_id,
                )
            ),
            assets_acquired_total=(purchases[player_id]),
            color_properties_acquired=(color_purchases[player_id]),
            transit_assets_acquired=(transit_purchases[player_id]),
            utility_assets_acquired=(utility_purchases[player_id]),
            assets_owned_at_finish=len(owned_assets),
            groups_completed_during_game=(
                groups_completed.get(
                    player_id,
                    0,
                )
            ),
            groups_owned_complete_at_finish=(complete_at_finish),
            first_group_completion_turn=(first_group_turn.get(player_id)),
            houses_built_total=(houses_built[player_id]),
            houses_owned_at_finish=(houses_at_finish),
            first_house_build_turn=(first_house_turn.get(player_id)),
            total_rent_paid=(player.total_rent_paid),
            total_rent_collected=(player.total_rent_collected),
            net_rent=(player.total_rent_collected - player.total_rent_paid),
            minimum_cash_observed=(
                player.minimum_cash_observed
                if player.minimum_cash_observed is not None
                else player.cash
            ),
            median_end_of_turn_cash=float(median(own_turn_cash)),
            mean_end_of_turn_cash=float(mean(own_turn_cash)),
            turns_below_strategy_desired_reserve=sum(
                1 for cash in own_turn_cash if cash < desired_reserve
            ),
            turns_played=(simulation.result.turns_played),
            termination_reason=(simulation.result.termination_reason),
        )

        records.append(record)

    if len(records) != 4:
        raise ValueError("one game must generate four strategy records")

    return tuple(records)


def _record_to_csv_row(
    record: TournamentGameRecord,
) -> dict[
    str,
    object,
]:
    row = asdict(record)

    row["strategy_id"] = record.strategy_id.value

    row["termination_reason"] = record.termination_reason.value

    row["won"] = int(record.won)

    row["bankrupt"] = int(record.bankrupt)

    return row


def csv_fieldnames() -> tuple[
    str,
    ...,
]:
    return tuple(field.name for field in fields(TournamentGameRecord))


def wilson_interval(
    successes: int,
    total: int,
    *,
    z: float = 1.959963984540054,
) -> tuple[
    float,
    float,
]:
    """Wilson score 95% confidence interval."""

    if total <= 0:
        raise ValueError("total must be positive")

    p_hat = successes / total

    denominator = 1.0 + (z * z / total)

    center = p_hat + (z * z / (2.0 * total))

    margin = z * math.sqrt((p_hat * (1.0 - p_hat) / total) + (z * z / (4.0 * total * total)))

    return (
        (center - margin) / denominator,
        (center + margin) / denominator,
    )


def exact_binomial_two_sided(
    successes: int,
    total: int,
) -> float:
    """Exact two-sided binomial test for p=0.5."""

    if not 0 <= successes <= total:
        raise ValueError("invalid successes")

    tail = min(
        successes,
        total - successes,
    )

    log_two = math.log(2.0)

    probability = sum(
        math.exp(
            math.lgamma(total + 1)
            - math.lgamma(index + 1)
            - math.lgamma(total - index + 1)
            - (total * log_two)
        )
        for index in range(tail + 1)
    )

    return min(
        1.0,
        2.0 * probability,
    )


def holm_adjust(
    p_values: Mapping[
        str,
        float,
    ],
) -> dict[
    str,
    float,
]:
    """Holm family-wise multiplicity correction."""

    ordered = sorted(
        p_values.items(),
        key=lambda pair: (
            pair[1],
            pair[0],
        ),
    )

    total = len(ordered)

    adjusted: dict[
        str,
        float,
    ] = {}

    previous = 0.0

    for rank, (
        key,
        p_value,
    ) in enumerate(ordered):
        candidate = min(
            1.0,
            (total - rank) * p_value,
        )

        candidate = max(
            candidate,
            previous,
        )

        adjusted[key] = candidate

        previous = candidate

    return adjusted


def _pairwise_summary(
    records: tuple[
        TournamentGameRecord,
        ...,
    ],
) -> list[dict[str, object]]:
    by_game: dict[
        int,
        dict[
            StrategyId,
            TournamentGameRecord,
        ],
    ] = defaultdict(dict)

    for record in records:
        by_game[record.game_index][record.strategy_id] = record

    strategies = tuple(StrategyId)

    raw: list[dict[str, object]] = []

    p_values: dict[
        str,
        float,
    ] = {}

    for left_index in range(len(strategies)):
        for right_index in range(
            left_index + 1,
            len(strategies),
        ):
            left = strategies[left_index]

            right = strategies[right_index]

            left_above = sum(
                1
                for game in by_game.values()
                if (game[left].finishing_position < game[right].finishing_position)
            )

            total = len(by_game)

            key = f"{left.value}__vs__{right.value}"

            p_value = exact_binomial_two_sided(
                left_above,
                total,
            )

            p_values[key] = p_value

            raw.append(
                {
                    "comparison_id": key,
                    "strategy_a": left.value,
                    "strategy_b": right.value,
                    "games": total,
                    "strategy_a_finishes_above_b": (left_above),
                    "strategy_a_head_to_head_rate": (left_above / total),
                    "exact_binomial_p_value": (p_value),
                }
            )

    adjusted = holm_adjust(p_values)

    for item in raw:
        key = str(item["comparison_id"])

        adjusted_p = adjusted[key]

        item["holm_adjusted_p_value"] = adjusted_p

        item["statistically_supported_advantage"] = adjusted_p < 0.05

    if len(raw) != 6:
        raise ValueError("exactly six pairwise comparisons required")

    return raw


def _strategy_summary(
    records: tuple[
        TournamentGameRecord,
        ...,
    ],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []

    for strategy_id in StrategyId:
        subset = [record for record in records if record.strategy_id is strategy_id]

        total = len(subset)

        wins = sum(record.won for record in subset)

        bankruptcies = sum(record.bankrupt for record in subset)

        win_low, win_high = wilson_interval(
            int(wins),
            total,
        )

        (
            bankruptcy_low,
            bankruptcy_high,
        ) = wilson_interval(
            int(bankruptcies),
            total,
        )

        position_counts = Counter(record.finishing_position for record in subset)

        result.append(
            {
                "strategy_id": (strategy_id.value),
                "games": total,
                "wins": int(wins),
                "win_rate": (wins / total),
                "win_rate_ci95": {
                    "lower": win_low,
                    "upper": win_high,
                    "method": "wilson",
                },
                "bankruptcies": int(bankruptcies),
                "bankruptcy_rate": (bankruptcies / total),
                "bankruptcy_rate_ci95": {
                    "lower": (bankruptcy_low),
                    "upper": (bankruptcy_high),
                    "method": "wilson",
                },
                "median_finishing_cash": float(median(record.finishing_cash for record in subset)),
                "mean_terminal_net_worth": float(
                    mean(record.terminal_net_worth for record in subset)
                ),
                "finishing_position_distribution": {
                    str(position): {
                        "count": (position_counts[position]),
                        "rate": (position_counts[position] / total),
                    }
                    for position in range(
                        1,
                        5,
                    )
                },
                "mean_assets_acquired": float(
                    mean(record.assets_acquired_total for record in subset)
                ),
                "mean_groups_completed": float(
                    mean(record.groups_completed_during_game for record in subset)
                ),
                "mean_houses_built": float(mean(record.houses_built_total for record in subset)),
                "mean_rent_paid": float(mean(record.total_rent_paid for record in subset)),
                "mean_rent_collected": float(
                    mean(record.total_rent_collected for record in subset)
                ),
                "mean_minimum_cash": float(mean(record.minimum_cash_observed for record in subset)),
                "mean_turns_below_desired_reserve": float(
                    mean(record.turns_below_strategy_desired_reserve for record in subset)
                ),
            }
        )

    return result


def _median_absolute_deviation(
    values: list[float],
) -> float:
    center = float(median(values))

    deviation = float(median(abs(value - center) for value in values))

    scaled = 1.4826 * deviation

    return scaled if scaled > 0.0 else 1.0


def representative_game_index(
    records: tuple[
        TournamentGameRecord,
        ...,
    ],
) -> tuple[
    int,
    dict[str, object],
]:
    """Select representative game without winner/seat information."""

    grouped: dict[
        int,
        list[TournamentGameRecord],
    ] = defaultdict(list)

    for record in records:
        grouped[record.game_index].append(record)

    features: dict[
        int,
        dict[str, float],
    ] = {}

    eligible: list[int] = []

    for game_index, game_records in grouped.items():
        game_features = {
            "turns": float(max(record.turns_played for record in game_records)),
            "purchases": float(sum(record.assets_acquired_total for record in game_records)),
            "houses": float(sum(record.houses_built_total for record in game_records)),
            "rent": float(sum(record.total_rent_paid for record in game_records)),
            "bankruptcies": float(sum(record.bankrupt for record in game_records)),
        }

        features[game_index] = game_features

        has_group = any(record.groups_completed_during_game > 0 for record in game_records)

        has_reserve_breach = any(
            record.turns_below_strategy_desired_reserve > 0 for record in game_records
        )

        if (
            game_features["purchases"] > 0
            and game_features["rent"] > 0
            and has_group
            and game_features["houses"] > 0
            and has_reserve_breach
        ):
            eligible.append(game_index)

    if not eligible:
        raise ValueError(
            "no representative-game candidate satisfies the frozen eligibility contract"
        )

    feature_names = (
        "turns",
        "purchases",
        "houses",
        "rent",
        "bankruptcies",
    )

    medians = {
        name: float(median(features[game_index][name] for game_index in grouped))
        for name in feature_names
    }

    scales = {
        name: _median_absolute_deviation([features[game_index][name] for game_index in grouped])
        for name in feature_names
    }

    scores = {
        game_index: sum(
            abs(features[game_index][name] - medians[name]) / scales[name] for name in feature_names
        )
        for game_index in eligible
    }

    selected = min(
        eligible,
        key=lambda game_index: (
            scores[game_index],
            game_index,
        ),
    )

    return (
        selected,
        {
            "method": ("minimum_sum_absolute_standardized_distance"),
            "eligibility": {
                "purchase": True,
                "rent": True,
                "group_completion": True,
                "house_build": True,
                "reserve_breach": True,
            },
            "features_used": list(feature_names),
            "winner_used_for_selection": False,
            "seat_used_for_selection": False,
            "median": medians,
            "scaled_mad": scales,
            "selected_features": (features[selected]),
            "selected_distance": (scores[selected]),
        },
    )


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def _write_json_atomic(
    path: Path,
    payload: object,
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(
            to_primitive(payload),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    os.replace(
        temporary,
        path,
    )


def _rerun_representative_game(
    *,
    config: MonopolyConfig,
    master_seed: int,
    game_index: int,
) -> SimulationResult:
    return simulate_game(
        config=config,
        game_index=game_index,
        game_seed=derive_game_seed(
            master_seed,
            game_index,
        ),
        seat_assignment=(seat_assignment_for_game(game_index)),
        decision_provider=(build_strategy_registry(config)),
    )


def validate_tournament_records(
    *,
    records: tuple[
        TournamentGameRecord,
        ...,
    ],
    game_count: int,
) -> None:
    """Validate row-level canonical tournament invariants."""

    if len(records) != (game_count * 4):
        raise ValueError("tournament row count mismatch")

    by_game: dict[
        int,
        list[TournamentGameRecord],
    ] = defaultdict(list)

    for record in records:
        by_game[record.game_index].append(record)

    if len(by_game) != game_count:
        raise ValueError("game count mismatch")

    for game_index, game_records in by_game.items():
        if len(game_records) != 4:
            raise ValueError(f"game {game_index} does not have four rows")

        if sum(record.won for record in game_records) != 1:
            raise ValueError(f"game {game_index} does not have exactly one winner")

        positions = sorted(record.finishing_position for record in game_records)

        if positions != [
            1,
            2,
            3,
            4,
        ]:
            raise ValueError(f"game {game_index} has invalid positions")

        if {record.strategy_id for record in game_records} != set(StrategyId):
            raise ValueError(f"game {game_index} missing strategy")


def validate_summary(
    summary: Mapping[
        str,
        object,
    ],
    *,
    game_count: int,
) -> None:
    """Validate required summary structure."""

    required = {
        "schema_version",
        "project_id",
        "master_seed",
        "game_count",
        "result_rows",
        "strategy_order",
        "headline",
        "strategy_summary",
        "pairwise",
        "fairness",
        "game_length",
        "representative",
        "validation",
        "hashes",
    }

    missing = required - set(summary)

    if missing:
        raise ValueError("summary missing keys: " + ", ".join(sorted(missing)))

    if summary["game_count"] != game_count:
        raise ValueError("summary game_count mismatch")


def run_tournament(
    *,
    config: MonopolyConfig,
    run_config: TournamentRunConfig,
) -> TournamentArtifacts:
    """Run one bounded sequential deterministic tournament."""

    output_directory = run_config.output_directory

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    progress = (
        TournamentProgressReporter(
            total_games=run_config.game_count,
            master_seed=run_config.master_seed,
            output_directory=str(output_directory),
            progress_every=(run_config.progress_every),
        )
        if run_config.show_progress
        else None
    )

    if progress is not None:
        progress.start()

    results_path = output_directory / "tournament_results.csv"

    summary_path = output_directory / "tournament_summary.json"

    representative_path = output_directory / "representative_game.json"

    representative_events_path = output_directory / "representative_game_events.json"

    temporary_csv = results_path.with_suffix(".csv.tmp")

    records: list[TournamentGameRecord] = []

    fieldnames = list(csv_fieldnames())

    # One immutable registry can safely serve all games because
    # policies contain configuration only and receive all game state
    # through immutable DecisionContext values.
    registry = build_strategy_registry(config)

    with temporary_csv.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )

        writer.writeheader()

        for spec in tournament_game_specs(
            game_count=(run_config.game_count),
            master_seed=(run_config.master_seed),
        ):
            simulation = simulate_game(
                config=config,
                game_index=spec.game_index,
                game_seed=spec.game_seed,
                seat_assignment=(spec.seat_assignment),
                decision_provider=registry,
            )

            game_records = records_from_simulation(
                config=config,
                simulation=simulation,
            )

            for record in game_records:
                writer.writerow(_record_to_csv_row(record))

                records.append(record)

            if progress is not None:
                bankrupt_strategies = tuple(
                    record.strategy_id for record in game_records if record.bankrupt
                )

                progress.record_game(
                    completed_games=(spec.game_index + 1),
                    winner=(simulation.result.winner_strategy_id),
                    bankrupt_strategies=(bankrupt_strategies),
                    last_game_index=(spec.game_index),
                    last_termination_reason=(simulation.result.termination_reason.value),
                    rows_written=len(records),
                )

    os.replace(
        temporary_csv,
        results_path,
    )

    frozen_records = tuple(records)

    if progress is not None:
        progress.stage("[VALIDATION] validating tournament records...")

    validate_tournament_records(
        records=frozen_records,
        game_count=(run_config.game_count),
    )

    if progress is not None:
        progress.stage("[FAIRNESS] validating seat balance...")

    seat_balance = validate_seat_balance(game_count=(run_config.game_count))

    if progress is not None:
        progress.stage("[AGGREGATION] calculating strategy metrics...")

    strategy_summary = _strategy_summary(frozen_records)

    if progress is not None:
        progress.stage("[STATISTICS] calculating pairwise comparisons...")

    pairwise = _pairwise_summary(frozen_records)

    if progress is not None:
        progress.stage("[REPRESENTATIVE] selecting representative game...")

    representative_index, (representative_selection) = representative_game_index(frozen_records)

    if progress is not None:
        progress.stage("[REPRESENTATIVE] rerunning selected game...")

    representative_simulation = _rerun_representative_game(
        config=config,
        master_seed=(run_config.master_seed),
        game_index=(representative_index),
    )

    representative_records = records_from_simulation(
        config=config,
        simulation=(representative_simulation),
    )

    representative_payload = {
        "schema_version": "1.0",
        "project_id": (config.project_id),
        "master_seed": (run_config.master_seed),
        "game_index": (representative_index),
        "game_seed": (
            derive_game_seed(
                run_config.master_seed,
                representative_index,
            )
        ),
        "selection": (representative_selection),
        "seat_assignment": [
            strategy.value for strategy in (seat_assignment_for_game(representative_index))
        ],
        "winner_strategy_id": (representative_simulation.result.winner_strategy_id.value),
        "turns_played": (representative_simulation.result.turns_played),
        "termination_reason": (representative_simulation.result.termination_reason.value),
        "records": [to_primitive(record) for record in representative_records],
    }

    representative_events_payload = {
        "schema_version": "1.0",
        "project_id": (config.project_id),
        "game_index": (representative_index),
        "game_seed": (
            derive_game_seed(
                run_config.master_seed,
                representative_index,
            )
        ),
        "events": [to_primitive(event) for event in (representative_simulation.events)],
    }

    _write_json_atomic(
        representative_path,
        representative_payload,
    )

    _write_json_atomic(
        representative_events_path,
        representative_events_payload,
    )

    win_rates: dict[
        str,
        float,
    ] = {}

    for item in strategy_summary:
        strategy_value = item.get("strategy_id")

        if not isinstance(
            strategy_value,
            str,
        ):
            raise ValueError("strategy summary strategy_id must be a string")

        win_rates[strategy_value] = _require_number(
            item.get("win_rate"),
            name=(f"strategy_summary.{strategy_value}.win_rate"),
        )

    highest_win_rate = max(win_rates.values())

    headline_leaders = sorted(
        strategy_id
        for strategy_id, rate in (win_rates.items())
        if math.isclose(
            rate,
            highest_win_rate,
            abs_tol=1e-15,
        )
    )

    game_lengths = [record.turns_played for record in frozen_records[::4]]

    if progress is not None:
        progress.stage("[HASH] calculating deterministic artifact hashes...")

    results_hash = _sha256_file(results_path)

    representative_hash = _sha256_file(representative_path)

    events_hash = _sha256_file(representative_events_path)

    reproducibility_hash = hashlib.sha256(
        (results_hash + representative_hash + events_hash).encode("utf-8")
    ).hexdigest()

    win_rate_sum = sum(win_rates.values())

    summary: dict[
        str,
        object,
    ] = {
        "schema_version": "1.0",
        "project_id": (config.project_id),
        "master_seed": (run_config.master_seed),
        "game_count": (run_config.game_count),
        "result_rows": len(frozen_records),
        "strategy_order": [strategy.value for strategy in StrategyId],
        "headline": {
            "metric": "tournament_win_rate",
            "highest_win_rate": (highest_win_rate),
            "numerical_leaders": (headline_leaders),
        },
        "strategy_summary": (strategy_summary),
        "pairwise": pairwise,
        "fairness": {
            "seat_counts": {
                strategy_id.value: {str(seat): count for seat, count in (seat_counts.items())}
                for (
                    strategy_id,
                    seat_counts,
                ) in seat_balance.items()
            },
            "win_rate_sum": (win_rate_sum),
            "win_rate_sum_target": 1.0,
            "win_rate_sum_tolerance": (1e-12),
        },
        "game_length": {
            "mean_turns": float(mean(game_lengths)),
            "median_turns": float(median(game_lengths)),
            "turn_limit_resolutions": sum(
                1
                for record in frozen_records[::4]
                if (record.termination_reason is GamePhase.TERMINATED_TURN_LIMIT)
            ),
        },
        "representative": {
            "game_index": (representative_index),
            "game_seed": (
                derive_game_seed(
                    run_config.master_seed,
                    representative_index,
                )
            ),
            "selection": (representative_selection),
        },
        "validation": {
            "exactly_one_winner_per_game": True,
            "four_rows_per_game": True,
            "unique_finishing_positions": True,
            "four_strategies_per_game": True,
            "sequential_bounded_execution": True,
            "rendering_enabled": False,
            "bulk_game_event_logs_persisted": False,
            "representative_event_log_persisted": True,
        },
        "hashes": {
            "tournament_results_sha256": (results_hash),
            "representative_game_sha256": (representative_hash),
            "representative_events_sha256": (events_hash),
            "reproducibility_sha256": (reproducibility_hash),
        },
    }

    if not math.isclose(
        win_rate_sum,
        1.0,
        abs_tol=1e-12,
    ):
        raise ValueError("strategy win rates do not sum to one")

    validate_summary(
        summary,
        game_count=(run_config.game_count),
    )

    _write_json_atomic(
        summary_path,
        summary,
    )

    if progress is not None:
        progress.complete()

    return TournamentArtifacts(
        results_csv=results_path,
        summary_json=summary_path,
        representative_json=(representative_path),
        representative_events_json=(representative_events_path),
    )
