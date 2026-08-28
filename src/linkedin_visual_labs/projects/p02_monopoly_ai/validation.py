"""Independent statistical and fairness validation for Project 3.

This module validates canonical Step 5 artifacts without changing
simulation rules, strategy behavior, seeds, or representative-game
selection.

For full reproducibility validation it can rerun the complete canonical
tournament into a separate validation directory and compare artifact
bytes/hashes against the frozen Step 5 outputs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    MonopolyConfig,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    GamePhase,
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.randomness import (
    derive_game_seed,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.tournament import (
    TournamentRunConfig,
    run_tournament,
)

WIN_RATE_SUM_TOLERANCE = 1e-12
OVERALL_SEAT_WIN_SPREAD_LIMIT = 0.05
WITHIN_STRATEGY_SEAT_WIN_SPREAD_LIMIT = 0.10

# Step 1 did not freeze a bankruptcy-by-seat hard threshold.
# Step 6 therefore uses this only as an explicit diagnostic threshold,
# not as a historical Step 1 contract assertion.
BANKRUPTCY_SEAT_DIAGNOSTIC_LIMIT = 0.10

Z_95 = 1.959963984540054


@dataclass(frozen=True, slots=True)
class ValidationPaths:
    """Canonical artifact locations."""

    data_directory: Path
    validation_directory: Path

    @property
    def results_csv(self) -> Path:
        return self.data_directory / "tournament_results.csv"

    @property
    def summary_json(self) -> Path:
        return self.data_directory / "tournament_summary.json"

    @property
    def representative_json(
        self,
    ) -> Path:
        return self.data_directory / "representative_game.json"

    @property
    def representative_events_json(
        self,
    ) -> Path:
        return self.data_directory / "representative_game_events.json"


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    """Typed subset of one tournament strategy-game row."""

    game_id: str
    game_index: int
    game_seed: int
    strategy_id: StrategyId
    seat_index: int
    finishing_position: int
    won: bool
    bankrupt: bool
    bankruptcy_turn: int | None
    finishing_cash: int
    terminal_net_worth: int
    houses_built_total: int
    houses_owned_at_finish: int
    total_rent_paid: int
    total_rent_collected: int
    net_rent: int
    minimum_cash_observed: int
    turns_played: int
    termination_reason: GamePhase


def _require_mapping(
    value: object,
    *,
    name: str,
) -> Mapping[str, object]:
    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(f"{name} must be an object")

    result: dict[str, object] = {}

    for key, item in value.items():
        if not isinstance(
            key,
            str,
        ):
            raise ValueError(f"{name} keys must be strings")

        result[key] = item

    return result


def _require_sequence(
    value: object,
    *,
    name: str,
) -> Sequence[object]:
    if not isinstance(
        value,
        list,
    ):
        raise ValueError(f"{name} must be a list")

    return value


def _require_str(
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


def _require_number(
    value: object,
    *,
    name: str,
) -> float:
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


def _parse_csv_int(
    row: Mapping[str, str],
    key: str,
) -> int:
    try:
        return int(row[key])
    except (
        KeyError,
        ValueError,
    ) as exc:
        raise ValueError(f"invalid integer CSV field: {key}") from exc


def _parse_optional_csv_int(
    row: Mapping[str, str],
    key: str,
) -> int | None:
    try:
        value = row[key]
    except KeyError as exc:
        raise ValueError(f"missing CSV field: {key}") from exc

    if value == "":
        return None

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"invalid optional integer CSV field: {key}") from exc


def _parse_csv_bool(
    row: Mapping[str, str],
    key: str,
) -> bool:
    value = _parse_csv_int(
        row,
        key,
    )

    if value not in {
        0,
        1,
    }:
        raise ValueError(f"{key} must be 0 or 1")

    return bool(value)


def _load_json(
    path: Path,
) -> Mapping[str, object]:
    raw = json.loads(path.read_text(encoding="utf-8"))

    return _require_mapping(
        raw,
        name=str(path),
    )


def load_records(
    path: Path,
) -> tuple[
    ValidationRecord,
    ...,
]:
    """Load canonical tournament CSV into a typed validation view."""

    records: list[ValidationRecord] = []

    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        for raw_row in reader:
            row = {
                str(key): str(value)
                for key, value in raw_row.items()
                if key is not None and value is not None
            }

            records.append(
                ValidationRecord(
                    game_id=row["game_id"],
                    game_index=_parse_csv_int(
                        row,
                        "game_index",
                    ),
                    game_seed=_parse_csv_int(
                        row,
                        "game_seed",
                    ),
                    strategy_id=StrategyId(row["strategy_id"]),
                    seat_index=_parse_csv_int(
                        row,
                        "seat_index",
                    ),
                    finishing_position=(
                        _parse_csv_int(
                            row,
                            "finishing_position",
                        )
                    ),
                    won=_parse_csv_bool(
                        row,
                        "won",
                    ),
                    bankrupt=_parse_csv_bool(
                        row,
                        "bankrupt",
                    ),
                    bankruptcy_turn=(
                        _parse_optional_csv_int(
                            row,
                            "bankruptcy_turn",
                        )
                    ),
                    finishing_cash=(
                        _parse_csv_int(
                            row,
                            "finishing_cash",
                        )
                    ),
                    terminal_net_worth=(
                        _parse_csv_int(
                            row,
                            "terminal_net_worth",
                        )
                    ),
                    houses_built_total=(
                        _parse_csv_int(
                            row,
                            "houses_built_total",
                        )
                    ),
                    houses_owned_at_finish=(
                        _parse_csv_int(
                            row,
                            "houses_owned_at_finish",
                        )
                    ),
                    total_rent_paid=(
                        _parse_csv_int(
                            row,
                            "total_rent_paid",
                        )
                    ),
                    total_rent_collected=(
                        _parse_csv_int(
                            row,
                            "total_rent_collected",
                        )
                    ),
                    net_rent=_parse_csv_int(
                        row,
                        "net_rent",
                    ),
                    minimum_cash_observed=(
                        _parse_csv_int(
                            row,
                            "minimum_cash_observed",
                        )
                    ),
                    turns_played=(
                        _parse_csv_int(
                            row,
                            "turns_played",
                        )
                    ),
                    termination_reason=GamePhase(row["termination_reason"]),
                )
            )

    return tuple(records)


def independent_wilson_interval(
    successes: int,
    total: int,
    *,
    z: float = Z_95,
) -> tuple[
    float,
    float,
]:
    """Independent Wilson interval implementation for cross-checking."""

    if total <= 0:
        raise ValueError("total must be positive")

    if not 0 <= successes <= total:
        raise ValueError("invalid successes")

    rate = successes / total

    z_squared = z * z

    denominator = 1.0 + (z_squared / total)

    adjusted_center = rate + (z_squared / (2.0 * total))

    adjusted_radius = z * math.sqrt(
        (rate * (1.0 - rate) / total) + (z_squared / (4.0 * total * total))
    )

    return (
        (adjusted_center - adjusted_radius) / denominator,
        (adjusted_center + adjusted_radius) / denominator,
    )


def independent_exact_binomial_two_sided(
    successes: int,
    total: int,
) -> float:
    """Compute an exact two-sided Binomial(total, 0.5) p-value.

    Under p=0.5 every outcome shares denominator 2**total:

        P(X=k) = C(total, k) / 2**total

    Probability ordering is therefore identical to ordering the
    integer binomial coefficients. Keeping the computation in Python
    arbitrary-precision integers until the final division avoids
    overflow for the canonical 10,000-game tournament.
    """

    if total < 0:
        raise ValueError("total cannot be negative")

    if not (0 <= successes <= total):
        raise ValueError("invalid successes")

    if total == 0:
        return 1.0

    observed_coefficient = math.comb(
        total,
        successes,
    )

    qualifying_numerator = 0

    # Start with C(total, 0).
    coefficient = 1

    for count in range(total + 1):
        if coefficient <= observed_coefficient:
            qualifying_numerator += coefficient

        if count < total:
            coefficient = coefficient * (total - count) // (count + 1)

    denominator: int = 1 << total

    probability = qualifying_numerator / denominator

    return min(
        1.0,
        probability,
    )


def independent_holm_adjust(
    p_values: Mapping[
        str,
        float,
    ],
) -> dict[
    str,
    float,
]:
    """Independent Holm family-wise correction."""

    ordered = sorted(
        p_values.items(),
        key=lambda pair: (
            pair[1],
            pair[0],
        ),
    )

    count = len(ordered)

    result: dict[
        str,
        float,
    ] = {}

    running_max = 0.0

    for index, (
        key,
        p_value,
    ) in enumerate(ordered):
        adjusted = min(
            1.0,
            (count - index) * p_value,
        )

        running_max = max(
            running_max,
            adjusted,
        )

        result[key] = running_max

    return result


def _sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def _write_json_atomic(
    path: Path,
    payload: object,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(
            payload,
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


def _game_groups(
    records: Sequence[ValidationRecord],
) -> dict[
    int,
    tuple[
        ValidationRecord,
        ...,
    ],
]:
    grouped: dict[
        int,
        list[ValidationRecord],
    ] = defaultdict(list)

    for record in records:
        grouped[record.game_index].append(record)

    return {game_index: tuple(game_records) for game_index, game_records in grouped.items()}


def validate_core_tournament(
    *,
    records: tuple[
        ValidationRecord,
        ...,
    ],
    summary: Mapping[
        str,
        object,
    ],
    config: MonopolyConfig,
) -> dict[
    str,
    object,
]:
    """Validate Steps 6.1-6.10 and 6.23-6.24."""

    canonical_games = config.tournament.game_count

    expected_rows = canonical_games * 4

    if len(records) != expected_rows:
        raise ValueError(f"canonical tournament must contain {expected_rows} strategy-game rows")

    grouped = _game_groups(records)

    if len(grouped) != canonical_games:
        raise ValueError(f"canonical tournament must contain {canonical_games} games")

    if set(grouped) != set(range(canonical_games)):
        raise ValueError("game indices must equal 0..9999")

    game_ids = {game_records[0].game_id for game_records in grouped.values()}

    if len(game_ids) != canonical_games:
        raise ValueError("game IDs are not unique")

    seeds = {game_records[0].game_seed for game_records in grouped.values()}

    if len(seeds) != canonical_games:
        raise ValueError("game seeds are not unique")

    valid_terminations = {
        GamePhase.TERMINATED_BANKRUPTCY,
        GamePhase.TERMINATED_TURN_LIMIT,
    }

    for game_index, game_records in grouped.items():
        if len(game_records) != 4:
            raise ValueError(f"game {game_index} must have four records")

        if {record.game_id for record in game_records} != {game_records[0].game_id}:
            raise ValueError(f"game {game_index} has inconsistent game_id")

        if {record.game_seed for record in game_records} != {game_records[0].game_seed}:
            raise ValueError(f"game {game_index} has inconsistent seed")

        if {record.strategy_id for record in game_records} != set(StrategyId):
            raise ValueError(f"game {game_index} has invalid strategy participation")

        seats = sorted(record.seat_index for record in game_records)

        if seats != [
            0,
            1,
            2,
            3,
        ]:
            raise ValueError(f"game {game_index} has invalid seats")

        winners = [record for record in game_records if record.won]

        if len(winners) != 1:
            raise ValueError(f"game {game_index} must have one winner")

        if winners[0].strategy_id not in StrategyId:
            raise ValueError(f"game {game_index} has illegal winner strategy")

        positions = sorted(record.finishing_position for record in game_records)

        if positions != [
            1,
            2,
            3,
            4,
        ]:
            raise ValueError(f"game {game_index} has invalid positions")

        termination_values = {record.termination_reason for record in game_records}

        if len(termination_values) != 1:
            raise ValueError(f"game {game_index} has inconsistent termination")

        termination = next(iter(termination_values))

        if termination not in valid_terminations:
            raise ValueError(f"game {game_index} did not resolve")

        turns_values = {record.turns_played for record in game_records}

        if len(turns_values) != 1:
            raise ValueError(f"game {game_index} has inconsistent turns")

        turns = next(iter(turns_values))

        if not (1 <= turns <= config.simulation.maximum_turns):
            raise ValueError(f"game {game_index} has illegal turn count")

        if (
            termination is GamePhase.TERMINATED_TURN_LIMIT
            and turns != config.simulation.maximum_turns
        ):
            raise ValueError(
                f"game {game_index}: turn-limit termination without maximum turn count"
            )

    strategy_counts = Counter(record.strategy_id for record in records)

    if set(strategy_counts.values()) != {canonical_games}:
        raise ValueError("strategy participation imbalance")

    seat_counts = Counter(
        (
            record.strategy_id,
            record.seat_index,
        )
        for record in records
    )

    expected_per_seat = canonical_games // 4

    if set(seat_counts.values()) != {expected_per_seat}:
        raise ValueError("strategy-seat cross-tab is not exactly balanced")

    summary_game_count = _require_int(
        summary.get("game_count"),
        name="summary.game_count",
    )

    if summary_game_count != canonical_games:
        raise ValueError("summary game count mismatch")

    summary_rows = _require_int(
        summary.get("result_rows"),
        name="summary.result_rows",
    )

    if summary_rows != expected_rows:
        raise ValueError("summary result-row count mismatch")

    return {
        "game_count": canonical_games,
        "strategy_game_rows": expected_rows,
        "unique_game_ids": len(game_ids),
        "unique_game_seeds": len(seeds),
        "one_winner_per_game": True,
        "legal_winner_strategy": True,
        "all_games_resolved": True,
        "turn_counts_valid": True,
        "turn_limit_rules_valid": True,
        "strategy_participation": {
            strategy.value: (strategy_counts[strategy]) for strategy in StrategyId
        },
        "strategy_seat_counts": {
            strategy.value: {
                str(seat): seat_counts[
                    (
                        strategy,
                        seat,
                    )
                ]
                for seat in range(4)
            }
            for strategy in StrategyId
        },
    }


def compute_seat_fairness(
    records: tuple[
        ValidationRecord,
        ...,
    ],
) -> dict[
    str,
    object,
]:
    """Compute Steps 6.11-6.14 seat-effect diagnostics.

    Exact strategy-seat allocation balance is validated separately by
    validate_core_tournament() and remains a hard fairness invariant.

    Observed outcome differences by seat are diagnostics rather than
    hard failures because every strategy receives identical exposure
    to every seat in the canonical tournament.
    """

    seat_games = Counter(record.seat_index for record in records)

    seat_wins = Counter(record.seat_index for record in records if record.won)

    seat_bankruptcies = Counter(record.seat_index for record in records if record.bankrupt)

    expected_seats = {
        0,
        1,
        2,
        3,
    }

    if set(seat_games) != expected_seats:
        raise ValueError("tournament must contain seats 0, 1, 2, and 3")

    if any(seat_games[seat] <= 0 for seat in expected_seats):
        raise ValueError("every seat must contain tournament observations")

    # ========================================================
    # 6.11 — OVERALL WIN RATE BY SEAT
    # ========================================================

    overall_win_rate_by_seat = {seat: (seat_wins[seat] / seat_games[seat]) for seat in range(4)}

    overall_win_spread = max(overall_win_rate_by_seat.values()) - min(
        overall_win_rate_by_seat.values()
    )

    # ========================================================
    # 6.13 — OVERALL BANKRUPTCY RATE BY SEAT
    # ========================================================

    overall_bankruptcy_rate_by_seat = {
        seat: (seat_bankruptcies[seat] / seat_games[seat]) for seat in range(4)
    }

    overall_bankruptcy_spread = max(overall_bankruptcy_rate_by_seat.values()) - min(
        overall_bankruptcy_rate_by_seat.values()
    )

    # ========================================================
    # WITHIN-STRATEGY SEAT EFFECTS
    # ========================================================

    strategy_win_rate_by_seat: dict[
        str,
        dict[
            str,
            float,
        ],
    ] = {}

    strategy_bankruptcy_rate_by_seat: dict[
        str,
        dict[
            str,
            float,
        ],
    ] = {}

    strategy_win_spreads: dict[
        str,
        float,
    ] = {}

    strategy_bankruptcy_spreads: dict[
        str,
        float,
    ] = {}

    for strategy in StrategyId:
        subset = [record for record in records if record.strategy_id is strategy]

        if not subset:
            raise ValueError(f"{strategy.value}: no tournament records")

        games_by_seat = Counter(record.seat_index for record in subset)

        if set(games_by_seat) != expected_seats:
            raise ValueError(f"{strategy.value}: missing seat observations")

        if any(games_by_seat[seat] <= 0 for seat in expected_seats):
            raise ValueError(f"{strategy.value}: empty seat observation")

        wins_by_seat = Counter(record.seat_index for record in subset if record.won)

        bankruptcies_by_seat = Counter(record.seat_index for record in subset if record.bankrupt)

        win_rates = {seat: (wins_by_seat[seat] / games_by_seat[seat]) for seat in range(4)}

        bankruptcy_rates = {
            seat: (bankruptcies_by_seat[seat] / games_by_seat[seat]) for seat in range(4)
        }

        win_spread = max(win_rates.values()) - min(win_rates.values())

        bankruptcy_spread = max(bankruptcy_rates.values()) - min(bankruptcy_rates.values())

        strategy_win_rate_by_seat[strategy.value] = {
            str(seat): rate for seat, rate in win_rates.items()
        }

        strategy_bankruptcy_rate_by_seat[strategy.value] = {
            str(seat): rate for seat, rate in bankruptcy_rates.items()
        }

        strategy_win_spreads[strategy.value] = win_spread

        strategy_bankruptcy_spreads[strategy.value] = bankruptcy_spread

    # ========================================================
    # 6.12 — SEAT-ADVANTAGE DIAGNOSTICS
    #
    # These limits flag practically notable effects.
    # They are NOT tournament validity thresholds.
    # ========================================================

    overall_seat_win_advantage_flag = overall_win_spread > OVERALL_SEAT_WIN_SPREAD_LIMIT

    strategy_seat_win_advantage_flags = {
        strategy: (spread > WITHIN_STRATEGY_SEAT_WIN_SPREAD_LIMIT)
        for strategy, spread in (strategy_win_spreads.items())
    }

    # ========================================================
    # 6.14 — SURVIVAL-BIAS DIAGNOSTICS
    # ========================================================

    maximum_bankruptcy_spread = max(strategy_bankruptcy_spreads.values())

    seat_survival_bias_flag = maximum_bankruptcy_spread > BANKRUPTCY_SEAT_DIAGNOSTIC_LIMIT

    return {
        "overall_win_rate_by_seat": {
            str(seat): rate for seat, rate in (overall_win_rate_by_seat.items())
        },
        "overall_win_rate_spread": (overall_win_spread),
        "overall_win_rate_spread_diagnostic_limit": (OVERALL_SEAT_WIN_SPREAD_LIMIT),
        "overall_seat_win_advantage_flag": (overall_seat_win_advantage_flag),
        "strategy_win_rate_by_seat": (strategy_win_rate_by_seat),
        "strategy_win_rate_spread": (strategy_win_spreads),
        "within_strategy_win_spread_diagnostic_limit": (WITHIN_STRATEGY_SEAT_WIN_SPREAD_LIMIT),
        "strategy_seat_win_advantage_flags": (strategy_seat_win_advantage_flags),
        "overall_bankruptcy_rate_by_seat": {
            str(seat): rate for seat, rate in (overall_bankruptcy_rate_by_seat.items())
        },
        "overall_bankruptcy_rate_spread": (overall_bankruptcy_spread),
        "strategy_bankruptcy_rate_by_seat": (strategy_bankruptcy_rate_by_seat),
        "strategy_bankruptcy_rate_spread": (strategy_bankruptcy_spreads),
        "bankruptcy_seat_diagnostic_limit": (BANKRUPTCY_SEAT_DIAGNOSTIC_LIMIT),
        "maximum_bankruptcy_seat_spread": (maximum_bankruptcy_spread),
        "seat_survival_bias_flag": (seat_survival_bias_flag),
        "interpretation": {
            "assignment_balance_is_hard_gate": True,
            "outcome_seat_effect_is_diagnostic": True,
            "seat_effect_does_not_bias_strategy_comparison_when_cross_tab_balanced": True,
        },
    }


def validate_record_economics(
    records: tuple[
        ValidationRecord,
        ...,
    ],
) -> dict[
    str,
    object,
]:
    """Validate persisted economic invariants available at CSV grain."""

    for record in records:
        if record.houses_built_total < 0:
            raise ValueError("negative houses_built_total")

        if record.houses_owned_at_finish < 0:
            raise ValueError("negative houses_owned_at_finish")

        if record.net_rent != (record.total_rent_collected - record.total_rent_paid):
            raise ValueError("net-rent accounting inconsistency")

        if record.total_rent_paid < 0 or record.total_rent_collected < 0:
            raise ValueError("negative rent accounting")

        if record.bankrupt and record.finishing_cash != 0:
            raise ValueError("bankrupt player must finish with zero cash")

        if record.bankrupt and record.bankruptcy_turn is None:
            raise ValueError("bankrupt player missing bankruptcy turn")

        if not record.bankrupt and record.bankruptcy_turn is not None:
            raise ValueError("non-bankrupt player has bankruptcy turn")

    grouped = _game_groups(records)

    rent_conservation_failures: list[int] = []

    for game_index, game_records in grouped.items():
        paid = sum(record.total_rent_paid for record in game_records)

        collected = sum(record.total_rent_collected for record in game_records)

        if paid != collected:
            rent_conservation_failures.append(game_index)

    if rent_conservation_failures:
        raise ValueError(
            "rent conservation failed for games: "
            + ", ".join(str(value) for value in rent_conservation_failures[:10])
        )

    return {
        "negative_house_counts": 0,
        "negative_rent_amounts": 0,
        "net_rent_consistent": True,
        "bankruptcy_cash_rule_valid": True,
        "bankruptcy_turn_fields_valid": True,
        "rent_transfer_conservation_valid": True,
        "note": (
            "Property-level unique ownership and per-action "
            "post-bankruptcy inactivity are engine-state invariants. "
            "They are revalidated during the full deterministic replay."
        ),
    }


def validate_representative_events(
    events_payload: Mapping[
        str,
        object,
    ],
) -> dict[
    str,
    object,
]:
    """Cross-check logged transfers and post-bankruptcy behavior.

    BANKRUPTCY can occur during an already-running scheduled turn.
    TURN_END is therefore legitimate bookkeeping after bankruptcy.

    Asset transfer and game-end events may also follow bankruptcy.
    A new TURN_START or any ordinary gameplay action by the bankrupt
    player remains illegal.
    """

    events = _require_sequence(
        events_payload.get("events"),
        name="representative.events",
    )

    bankrupt_at: dict[
        str,
        int,
    ] = {}

    bankruptcy_turn: dict[
        str,
        int | None,
    ] = {}

    permitted_after_bankruptcy = {
        "ASSET_TRANSFER",
        "TURN_END",
        "GAME_END",
    }

    cash_transfer_count = 0
    post_bankruptcy_bookkeeping_count = 0

    previous_event_index = -1

    for raw_event in events:
        event = _require_mapping(
            raw_event,
            name="representative event",
        )

        event_index = _require_int(
            event.get("event_index"),
            name="event.event_index",
        )

        if event_index != previous_event_index + 1:
            raise ValueError("representative event indices not contiguous")

        previous_event_index = event_index

        event_type = _require_str(
            event.get("event_type"),
            name="event.event_type",
        )

        player_raw = event.get("player_id")

        player_id = (
            _require_str(
                player_raw,
                name="event.player_id",
            )
            if player_raw is not None
            else None
        )

        turn_raw = event.get("turn_number")

        turn_number = (
            _require_int(
                turn_raw,
                name="event.turn_number",
            )
            if turn_raw is not None
            else None
        )

        # ----------------------------------------------------
        # Post-bankruptcy behavior
        # ----------------------------------------------------

        if (
            player_id is not None
            and player_id in bankrupt_at
            and event_index > bankrupt_at[player_id]
        ):
            if event_type not in permitted_after_bankruptcy:
                raise ValueError(
                    f"bankrupt player acted after bankruptcy: {player_id} event={event_type}"
                )

            if event_type == "TURN_END":
                bankrupt_turn = bankruptcy_turn[player_id]

                # TURN_END may only close the turn in which
                # bankruptcy occurred. It cannot represent a
                # later scheduled turn.
                if (
                    bankrupt_turn is not None
                    and turn_number is not None
                    and turn_number != bankrupt_turn
                ):
                    raise ValueError(
                        "bankrupt player received TURN_END "
                        "for a later turn: "
                        f"{player_id} "
                        f"bankruptcy_turn={bankrupt_turn} "
                        f"turn_end={turn_number}"
                    )

            post_bankruptcy_bookkeeping_count += 1

        # ----------------------------------------------------
        # Cash-transfer logging
        # ----------------------------------------------------

        if event_type == "CASH_TRANSFER":
            cash_transfer_count += 1

            amount_raw = event.get("amount")

            if amount_raw is None:
                raise ValueError("CASH_TRANSFER missing amount")

            amount = _require_int(
                amount_raw,
                name="event.amount",
            )

            if amount < 0:
                raise ValueError("negative logged cash transfer")

        # ----------------------------------------------------
        # Bankruptcy registration
        # ----------------------------------------------------

        if event_type == "BANKRUPTCY" and player_id is not None:
            if player_id in bankrupt_at:
                raise ValueError(f"player logged bankruptcy more than once: {player_id}")

            bankrupt_at[player_id] = event_index

            bankruptcy_turn[player_id] = turn_number

    return {
        "event_count": len(events),
        "cash_transfer_count": (cash_transfer_count),
        "cash_transfers_nonnegative": True,
        "bankrupt_players_stop_acting": True,
        "post_bankruptcy_bookkeeping_events": (post_bankruptcy_bookkeeping_count),
        "permitted_post_bankruptcy_event_types": sorted(permitted_after_bankruptcy),
        "event_indices_contiguous": True,
    }


def validate_statistical_summary(
    *,
    records: tuple[
        ValidationRecord,
        ...,
    ],
    summary: Mapping[
        str,
        object,
    ],
) -> dict[
    str,
    object,
]:
    """Validate Steps 6.7 and 6.25-6.34."""

    strategy_summary_raw = _require_sequence(
        summary.get("strategy_summary"),
        name="summary.strategy_summary",
    )

    strategy_summary: dict[
        StrategyId,
        Mapping[str, object],
    ] = {}

    for raw_item in strategy_summary_raw:
        item = _require_mapping(
            raw_item,
            name="strategy summary item",
        )

        strategy = StrategyId(
            _require_str(
                item.get("strategy_id"),
                name="strategy_id",
            )
        )

        strategy_summary[strategy] = item

    if set(strategy_summary) != set(StrategyId):
        raise ValueError("summary strategy set invalid")

    calculated_win_rates: dict[
        StrategyId,
        float,
    ] = {}

    calculated_bankruptcy_rates: dict[
        StrategyId,
        float,
    ] = {}

    finishing_cash_medians: dict[
        StrategyId,
        float,
    ] = {}

    position_distributions: dict[
        StrategyId,
        dict[int, int],
    ] = {}

    independent_intervals: dict[
        str,
        dict[str, object],
    ] = {}

    for strategy in StrategyId:
        subset = [record for record in records if record.strategy_id is strategy]

        total = len(subset)

        wins = sum(record.won for record in subset)

        bankruptcies = sum(record.bankrupt for record in subset)

        win_rate = wins / total

        bankruptcy_rate = bankruptcies / total

        calculated_win_rates[strategy] = win_rate

        calculated_bankruptcy_rates[strategy] = bankruptcy_rate

        finishing_cash_medians[strategy] = float(median(record.finishing_cash for record in subset))

        positions = Counter(record.finishing_position for record in subset)

        position_distributions[strategy] = {
            position: positions[position]
            for position in range(
                1,
                5,
            )
        }

        item = strategy_summary[strategy]

        summary_win_rate = _require_number(
            item.get("win_rate"),
            name=f"{strategy.value}.win_rate",
        )

        summary_bankruptcy_rate = _require_number(
            item.get("bankruptcy_rate"),
            name=(f"{strategy.value}.bankruptcy_rate"),
        )

        summary_median_cash = _require_number(
            item.get("median_finishing_cash"),
            name=(f"{strategy.value}.median_finishing_cash"),
        )

        if not math.isclose(
            summary_win_rate,
            win_rate,
            abs_tol=1e-15,
        ):
            raise ValueError(f"{strategy.value}: win rate mismatch")

        if not math.isclose(
            summary_bankruptcy_rate,
            bankruptcy_rate,
            abs_tol=1e-15,
        ):
            raise ValueError(f"{strategy.value}: bankruptcy rate mismatch")

        if not math.isclose(
            summary_median_cash,
            finishing_cash_medians[strategy],
            abs_tol=1e-12,
        ):
            raise ValueError(f"{strategy.value}: median cash mismatch")

        independent_win_ci = independent_wilson_interval(
            int(wins),
            total,
        )

        independent_bankruptcy_ci = independent_wilson_interval(
            int(bankruptcies),
            total,
        )

        win_ci = _require_mapping(
            item.get("win_rate_ci95"),
            name="win_rate_ci95",
        )

        bankruptcy_ci = _require_mapping(
            item.get("bankruptcy_rate_ci95"),
            name="bankruptcy_rate_ci95",
        )

        for reported, calculated, label in (
            (
                _require_number(
                    win_ci.get("lower"),
                    name="win_ci.lower",
                ),
                independent_win_ci[0],
                "win lower",
            ),
            (
                _require_number(
                    win_ci.get("upper"),
                    name="win_ci.upper",
                ),
                independent_win_ci[1],
                "win upper",
            ),
            (
                _require_number(
                    bankruptcy_ci.get("lower"),
                    name="bankruptcy_ci.lower",
                ),
                independent_bankruptcy_ci[0],
                "bankruptcy lower",
            ),
            (
                _require_number(
                    bankruptcy_ci.get("upper"),
                    name="bankruptcy_ci.upper",
                ),
                independent_bankruptcy_ci[1],
                "bankruptcy upper",
            ),
        ):
            if not math.isclose(
                reported,
                calculated,
                abs_tol=1e-12,
            ):
                raise ValueError(f"{strategy.value}: CI mismatch {label}")

        independent_intervals[strategy.value] = {
            "win_rate": {
                "lower": (independent_win_ci[0]),
                "upper": (independent_win_ci[1]),
            },
            "bankruptcy_rate": {
                "lower": (independent_bankruptcy_ci[0]),
                "upper": (independent_bankruptcy_ci[1]),
            },
        }

    win_rate_sum = sum(calculated_win_rates.values())

    if not math.isclose(
        win_rate_sum,
        1.0,
        abs_tol=WIN_RATE_SUM_TOLERANCE,
    ):
        raise ValueError("strategy win rates do not sum to one")

    pairwise_raw = _require_sequence(
        summary.get("pairwise"),
        name="summary.pairwise",
    )

    if len(pairwise_raw) != 6:
        raise ValueError("exactly six pairwise comparisons required")

    independent_raw_p: dict[
        str,
        float,
    ] = {}

    independent_pairwise: dict[
        str,
        dict[str, object],
    ] = {}

    grouped = _game_groups(records)

    for raw_item in pairwise_raw:
        item = _require_mapping(
            raw_item,
            name="pairwise item",
        )

        comparison_id = _require_str(
            item.get("comparison_id"),
            name="comparison_id",
        )

        strategy_a = StrategyId(
            _require_str(
                item.get("strategy_a"),
                name="strategy_a",
            )
        )

        strategy_b = StrategyId(
            _require_str(
                item.get("strategy_b"),
                name="strategy_b",
            )
        )

        a_above = 0

        for game_records in grouped.values():
            by_strategy = {record.strategy_id: record for record in game_records}

            if (
                by_strategy[strategy_a].finishing_position
                < by_strategy[strategy_b].finishing_position
            ):
                a_above += 1

        p_value = independent_exact_binomial_two_sided(
            a_above,
            len(grouped),
        )

        independent_raw_p[comparison_id] = p_value

        independent_pairwise[comparison_id] = {
            "strategy_a": (strategy_a.value),
            "strategy_b": (strategy_b.value),
            "a_finishes_above_b": (a_above),
            "head_to_head_rate": (a_above / len(grouped)),
            "exact_binomial_p_value": (p_value),
        }

        reported_count = _require_int(
            item.get("strategy_a_finishes_above_b"),
            name="pairwise count",
        )

        if reported_count != a_above:
            raise ValueError(f"{comparison_id}: head-to-head count mismatch")

        reported_p = _require_number(
            item.get("exact_binomial_p_value"),
            name="pairwise p-value",
        )

        if not math.isclose(
            reported_p,
            p_value,
            abs_tol=1e-12,
        ):
            raise ValueError(f"{comparison_id}: exact binomial mismatch")

    adjusted = independent_holm_adjust(independent_raw_p)

    for raw_item in pairwise_raw:
        item = _require_mapping(
            raw_item,
            name="pairwise item",
        )

        comparison_id = _require_str(
            item.get("comparison_id"),
            name="comparison_id",
        )

        reported_adjusted = _require_number(
            item.get("holm_adjusted_p_value"),
            name="holm p-value",
        )

        if not math.isclose(
            reported_adjusted,
            adjusted[comparison_id],
            abs_tol=1e-12,
        ):
            raise ValueError(f"{comparison_id}: Holm correction mismatch")

        independent_pairwise[comparison_id]["holm_adjusted_p_value"] = adjusted[comparison_id]

    win_ranking = sorted(
        StrategyId,
        key=lambda strategy: (
            -calculated_win_rates[strategy],
            strategy.value,
        ),
    )

    bankruptcy_ranking = sorted(
        StrategyId,
        key=lambda strategy: (
            calculated_bankruptcy_rates[strategy],
            strategy.value,
        ),
    )

    median_cash_ranking = sorted(
        StrategyId,
        key=lambda strategy: (
            -finishing_cash_medians[strategy],
            strategy.value,
        ),
    )

    unique_numerical_leader = len(win_ranking) >= 2 and not math.isclose(
        calculated_win_rates[win_ranking[0]],
        calculated_win_rates[win_ranking[1]],
        abs_tol=1e-15,
    )

    numerical_leader = win_ranking[0] if unique_numerical_leader else None

    statistically_supported_against_all = True

    materially_overlapping_rivals: list[str] = []

    if numerical_leader is not None:
        leader_ci = independent_intervals[numerical_leader.value]["win_rate"]

        leader_lower = _require_number(
            _require_mapping(
                leader_ci,
                name="leader CI",
            ).get("lower"),
            name="leader CI lower",
        )

        leader_upper = _require_number(
            _require_mapping(
                leader_ci,
                name="leader CI",
            ).get("upper"),
            name="leader CI upper",
        )

        for rival in StrategyId:
            if rival is numerical_leader:
                continue

            rival_ci = _require_mapping(
                independent_intervals[rival.value]["win_rate"],
                name="rival CI",
            )

            rival_lower = _require_number(
                rival_ci.get("lower"),
                name="rival lower",
            )

            rival_upper = _require_number(
                rival_ci.get("upper"),
                name="rival upper",
            )

            intervals_overlap = not (leader_lower > rival_upper or rival_lower > leader_upper)

            if intervals_overlap:
                materially_overlapping_rivals.append(rival.value)

            pair_item = next(
                _require_mapping(
                    raw_item,
                    name="pairwise item",
                )
                for raw_item in pairwise_raw
                if {
                    _require_str(
                        _require_mapping(
                            raw_item,
                            name="pairwise item",
                        ).get("strategy_a"),
                        name="strategy_a",
                    ),
                    _require_str(
                        _require_mapping(
                            raw_item,
                            name="pairwise item",
                        ).get("strategy_b"),
                        name="strategy_b",
                    ),
                }
                == {
                    numerical_leader.value,
                    rival.value,
                }
            )

            adjusted_p = _require_number(
                pair_item.get("holm_adjusted_p_value"),
                name="pairwise adjusted p",
            )

            strategy_a_value = _require_str(
                pair_item.get("strategy_a"),
                name="strategy_a",
            )

            h2h_rate_a = _require_number(
                pair_item.get("strategy_a_head_to_head_rate"),
                name="pairwise H2H rate",
            )

            leader_h2h_rate = (
                h2h_rate_a if strategy_a_value == numerical_leader.value else (1.0 - h2h_rate_a)
            )

            if not (adjusted_p < 0.05 and leader_h2h_rate > 0.5):
                statistically_supported_against_all = False

    else:
        statistically_supported_against_all = False

    # Headline rule:
    #
    # 1. A unique numerical leader must exist.
    # 2. It must have Holm-adjusted pairwise evidence against every rival.
    # 3. If Wilson intervals overlap, that overlap is explicitly disclosed.
    #
    # We therefore never turn a numerical edge into an unsupported
    # categorical "winner".
    headline_status: str

    if numerical_leader is not None and statistically_supported_against_all:
        headline_status = "statistically_supported_winner"
    elif numerical_leader is not None:
        headline_status = "numerical_leader_statistical_tie"
    else:
        headline_status = "statistical_tie"

    headline_winner = (
        numerical_leader.value
        if (numerical_leader is not None and statistically_supported_against_all)
        else None
    )

    return {
        "win_rate_sum": (win_rate_sum),
        "win_rate_sum_tolerance": (WIN_RATE_SUM_TOLERANCE),
        "independent_confidence_intervals": (independent_intervals),
        "independent_pairwise": (independent_pairwise),
        "win_rate_ranking": [
            {
                "rank": index + 1,
                "strategy_id": (strategy.value),
                "win_rate": (calculated_win_rates[strategy]),
            }
            for index, strategy in enumerate(win_ranking)
        ],
        "bankruptcy_ranking": [
            {
                "rank": index + 1,
                "strategy_id": (strategy.value),
                "bankruptcy_rate": (calculated_bankruptcy_rates[strategy]),
            }
            for index, strategy in enumerate(bankruptcy_ranking)
        ],
        "median_cash_ranking": [
            {
                "rank": index + 1,
                "strategy_id": (strategy.value),
                "median_finishing_cash": (finishing_cash_medians[strategy]),
            }
            for index, strategy in enumerate(median_cash_ranking)
        ],
        "position_distribution": {
            strategy.value: {
                str(position): position_distributions[strategy][position]
                for position in range(
                    1,
                    5,
                )
            }
            for strategy in StrategyId
        },
        "first_place_distribution": {
            strategy.value: (position_distributions[strategy][1]) for strategy in StrategyId
        },
        "last_place_distribution": {
            strategy.value: (position_distributions[strategy][4]) for strategy in StrategyId
        },
        "headline_rule": {
            "status": (headline_status),
            "numerical_leader": (numerical_leader.value if numerical_leader is not None else None),
            "headline_winner": (headline_winner),
            "requires_unique_numerical_leader": True,
            "requires_holm_pairwise_support_against_all_rivals": True,
            "materially_overlapping_wilson_ci_rivals": (materially_overlapping_rivals),
            "false_winner_prevention_active": True,
        },
    }


def validate_seed_contract(
    *,
    config: MonopolyConfig,
    records: tuple[
        ValidationRecord,
        ...,
    ],
) -> dict[
    str,
    object,
]:
    """Validate master-seed expansion and different-seed divergence."""

    grouped = _game_groups(records)

    master_seed = config.tournament.master_seed

    for game_index, game_records in grouped.items():
        expected_seed = derive_game_seed(
            master_seed,
            game_index,
        )

        if game_records[0].game_seed != expected_seed:
            raise ValueError(f"game {game_index}: derived seed mismatch")

    alternate_master_seed = master_seed + 1

    canonical_probe = tuple(
        derive_game_seed(
            master_seed,
            index,
        )
        for index in range(64)
    )

    alternate_probe = tuple(
        derive_game_seed(
            alternate_master_seed,
            index,
        )
        for index in range(64)
    )

    if canonical_probe == alternate_probe:
        raise ValueError("different master seed did not change game seeds")

    return {
        "master_seed": (master_seed),
        "all_game_seeds_match_master_seed_expansion": True,
        "alternate_master_seed": (alternate_master_seed),
        "different_master_seed_changes_seed_sequence": True,
        "probe_games": 64,
    }


def full_replay_hash_validation(
    *,
    config: MonopolyConfig,
    canonical_paths: ValidationPaths,
    replay_directory: Path,
    show_progress: bool,
    progress_every: int,
) -> dict[
    str,
    object,
]:
    """Rerun all 10,000 games and require byte-identical artifacts."""

    artifacts = run_tournament(
        config=config,
        run_config=TournamentRunConfig(
            game_count=(config.tournament.game_count),
            master_seed=(config.tournament.master_seed),
            output_directory=(replay_directory),
            show_progress=(show_progress),
            progress_every=(progress_every),
        ),
    )

    comparisons = (
        (
            "tournament_results.csv",
            canonical_paths.results_csv,
            artifacts.results_csv,
        ),
        (
            "tournament_summary.json",
            canonical_paths.summary_json,
            artifacts.summary_json,
        ),
        (
            "representative_game.json",
            canonical_paths.representative_json,
            artifacts.representative_json,
        ),
        (
            "representative_game_events.json",
            canonical_paths.representative_events_json,
            artifacts.representative_events_json,
        ),
    )

    hashes: dict[
        str,
        dict[str, object],
    ] = {}

    for (
        name,
        canonical,
        replay,
    ) in comparisons:
        canonical_hash = _sha256(canonical)

        replay_hash = _sha256(replay)

        identical = canonical.read_bytes() == replay.read_bytes()

        if not identical:
            raise ValueError(f"full replay mismatch: {name}")

        hashes[name] = {
            "canonical_sha256": (canonical_hash),
            "replay_sha256": (replay_hash),
            "byte_identical": True,
        }

    return {
        "full_replay_game_count": (config.tournament.game_count),
        "master_seed": (config.tournament.master_seed),
        "artifacts": hashes,
        "canonical_tournament_reproducible": True,
        "engine_invariants_reexecuted_for_every_game": True,
    }


def _strategy_diagnostics(
    records: tuple[
        ValidationRecord,
        ...,
    ],
) -> dict[
    str,
    object,
]:
    result: dict[
        str,
        object,
    ] = {}

    for strategy in StrategyId:
        subset = [record for record in records if record.strategy_id is strategy]

        positions = Counter(record.finishing_position for record in subset)

        result[strategy.value] = {
            "games": len(subset),
            "wins": sum(record.won for record in subset),
            "bankruptcies": sum(record.bankrupt for record in subset),
            "median_finishing_cash": float(median(record.finishing_cash for record in subset)),
            "median_terminal_net_worth": float(
                median(record.terminal_net_worth for record in subset)
            ),
            "mean_minimum_cash": (
                sum(record.minimum_cash_observed for record in subset) / len(subset)
            ),
            "first_place_count": positions[1],
            "last_place_count": positions[4],
        }

    return result


def run_canonical_validation(
    *,
    config: MonopolyConfig,
    paths: ValidationPaths,
    full_replay: bool,
    replay_directory: Path,
    show_progress: bool = True,
    progress_every: int = 100,
) -> dict[
    str,
    Path,
]:
    """Run complete Step 6 validation and write the four reports."""

    def stage(
        message: str,
    ) -> None:
        if show_progress:
            print(
                message,
                flush=True,
            )

    stage("\n[LOAD] loading canonical Step 5 artifacts...")

    for required in (
        paths.results_csv,
        paths.summary_json,
        paths.representative_json,
        paths.representative_events_json,
    ):
        if not required.is_file():
            raise FileNotFoundError(required)

    records = load_records(paths.results_csv)

    summary = _load_json(paths.summary_json)

    representative = _load_json(paths.representative_json)

    representative_events = _load_json(paths.representative_events_json)

    stage(f"[LOAD] loaded {len(records):,} strategy-game records")

    stage("[SCHEMA] validating games, IDs, seeds, winners, participation, turns...")

    core = validate_core_tournament(
        records=records,
        summary=summary,
        config=config,
    )

    stage("[FAIRNESS] calculating strategy-seat cross-tabs...")

    fairness = compute_seat_fairness(records)

    stage("[ECONOMICS] validating persisted economic invariants...")

    economics = validate_record_economics(records)

    stage("[EVENTS] validating representative cash transfers and bankruptcy inactivity...")

    event_validation = validate_representative_events(representative_events)

    stage("[SEEDS] validating master-seed expansion...")

    seed_validation = validate_seed_contract(
        config=config,
        records=records,
    )

    stage("[STATISTICS] independently recomputing Wilson intervals...")

    stage(
        "[STATISTICS] independently recomputing six exact-binomial comparisons + Holm correction..."
    )

    statistics = validate_statistical_summary(
        records=records,
        summary=summary,
    )

    replay: dict[
        str,
        object,
    ]

    if full_replay:
        stage("[REPRODUCIBILITY] rerunning canonical 10,000-game tournament...")

        replay = full_replay_hash_validation(
            config=config,
            canonical_paths=paths,
            replay_directory=(replay_directory),
            show_progress=(show_progress),
            progress_every=(progress_every),
        )

        stage("[REPRODUCIBILITY] canonical outputs are byte-identical")

    else:
        replay = {
            "full_replay_executed": False,
            "canonical_tournament_reproducible": None,
        }

    stage("[DIAGNOSTICS] building strategy diagnostic summary...")

    diagnostics = _strategy_diagnostics(records)

    canonical_hashes = {
        "tournament_results_sha256": (_sha256(paths.results_csv)),
        "tournament_summary_sha256": (_sha256(paths.summary_json)),
        "representative_game_sha256": (_sha256(paths.representative_json)),
        "representative_events_sha256": (_sha256(paths.representative_events_json)),
    }

    headline_rule = _require_mapping(
        statistics["headline_rule"],
        name="headline_rule",
    )

    stage("[REPORT] writing tournament validation report...")

    validation_report = {
        "schema_version": "1.0",
        "project_id": (config.project_id),
        "master_seed": (config.tournament.master_seed),
        "canonical_game_count": (config.tournament.game_count),
        "core_validation": (core),
        "economic_validation": (economics),
        "event_validation": (event_validation),
        "seed_validation": (seed_validation),
        "statistical_validation": (statistics),
        "reproducibility_validation": (replay),
        "canonical_hashes": (canonical_hashes),
        "completion": {
            "tournament_reproducible": (
                replay.get("canonical_tournament_reproducible") is True if full_replay else None
            ),
            "seats_balanced": True,
            "no_impossible_persisted_states": True,
            "metrics_internally_consistent": True,
            "statistical_calculations_verified": True,
            "winner_logic_data_driven": True,
        },
    }

    validation_report_path = paths.validation_directory / "tournament_validation_report.json"

    _write_json_atomic(
        validation_report_path,
        validation_report,
    )

    stage("[REPORT] writing fairness summary...")

    fairness_path = paths.validation_directory / "fairness_summary.json"

    _write_json_atomic(
        fairness_path,
        {
            "schema_version": "1.0",
            "project_id": (config.project_id),
            "master_seed": (config.tournament.master_seed),
            "fairness": fairness,
            "strategy_seat_counts": (core["strategy_seat_counts"]),
        },
    )

    stage("[REPORT] writing strategy diagnostic summary...")

    diagnostics_path = paths.validation_directory / "strategy_diagnostic_summary.json"

    _write_json_atomic(
        diagnostics_path,
        {
            "schema_version": "1.0",
            "project_id": (config.project_id),
            "diagnostics": (diagnostics),
            "rankings": {
                "win_rate": (statistics["win_rate_ranking"]),
                "bankruptcy": (statistics["bankruptcy_ranking"]),
                "median_cash": (statistics["median_cash_ranking"]),
            },
            "headline_rule": (headline_rule),
        },
    )

    stage("[FREEZE] freezing validated canonical inputs for video...")

    freeze_path = paths.validation_directory / "canonical_video_freeze.json"

    representative_game_index = _require_int(
        representative.get("game_index"),
        name="representative.game_index",
    )

    representative_game_seed = _require_int(
        representative.get("game_seed"),
        name="representative.game_seed",
    )

    freeze_payload = {
        "schema_version": "1.0",
        "project_id": (config.project_id),
        "master_seed": (config.tournament.master_seed),
        "game_count": (config.tournament.game_count),
        "source_artifacts": {
            "tournament_results": str(paths.results_csv),
            "tournament_summary": str(paths.summary_json),
            "representative_game": str(paths.representative_json),
            "representative_events": str(paths.representative_events_json),
        },
        "source_hashes": (canonical_hashes),
        "headline_rule": (headline_rule),
        "representative_game_index": (representative_game_index),
        "representative_game_seed": (representative_game_seed),
        "winner_used_for_representative_selection": False,
        "seat_used_for_representative_selection": False,
        "validated_for_video": (
            (replay.get("canonical_tournament_reproducible") is True) if full_replay else False
        ),
    }

    _write_json_atomic(
        freeze_path,
        freeze_payload,
    )

    stage("[COMPLETE] Step 6 statistical/fairness validation finished")

    return {
        "validation_report": (validation_report_path),
        "fairness_summary": (fairness_path),
        "strategy_diagnostics": (diagnostics_path),
        "video_freeze": (freeze_path),
    }
