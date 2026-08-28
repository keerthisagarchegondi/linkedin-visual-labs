"""Tournament orchestration tests."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai.config import (
    load_config,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    StrategyId,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.randomness import (
    derive_game_seed,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.tournament import (
    CANONICAL_SEAT_CYCLE,
    TournamentRunConfig,
    exact_binomial_two_sided,
    holm_adjust,
    run_tournament,
    seat_assignment_for_game,
    tournament_game_specs,
    validate_seat_balance,
    wilson_interval,
)

CONFIG = Path("configs/p02_monopoly_ai.yaml")


def test_game_seed_is_deterministic() -> None:
    first = [
        derive_game_seed(
            73031,
            index,
        )
        for index in range(100)
    ]

    second = [
        derive_game_seed(
            73031,
            index,
        )
        for index in range(100)
    ]

    assert first == second

    assert len(set(first)) == 100


def test_seat_cycle_has_exactly_eight_rows() -> None:
    assert len(CANONICAL_SEAT_CYCLE) == 8


def test_every_seat_cycle_row_contains_four_strategies() -> None:
    for assignment in CANONICAL_SEAT_CYCLE:
        assert set(assignment) == set(StrategyId)


def test_10000_games_are_exactly_seat_balanced() -> None:
    counts = validate_seat_balance(game_count=10000)

    for strategy_id in StrategyId:
        assert sum(counts[strategy_id].values()) == 10000

        assert set(counts[strategy_id].values()) == {2500}


def test_game_specs_are_lazy_and_deterministic() -> None:
    specs = list(
        tournament_game_specs(
            game_count=8,
            master_seed=73031,
        )
    )

    assert len(specs) == 8

    for index, spec in enumerate(specs):
        assert spec.game_index == index

        assert spec.game_seed == (
            derive_game_seed(
                73031,
                index,
            )
        )

        assert spec.seat_assignment == (seat_assignment_for_game(index))


def test_wilson_interval_contains_observed_rate() -> None:
    low, high = wilson_interval(
        2500,
        10000,
    )

    assert low < 0.25 < high


def test_exact_binomial_is_symmetric() -> None:
    assert exact_binomial_two_sided(
        450,
        1000,
    ) == exact_binomial_two_sided(
        550,
        1000,
    )


def test_holm_adjustment_is_not_smaller_than_raw() -> None:
    raw = {
        "a": 0.001,
        "b": 0.01,
        "c": 0.2,
    }

    adjusted = holm_adjust(raw)

    for key in raw:
        assert adjusted[key] >= raw[key]


def test_small_tournament_writes_consistent_artifacts(
    tmp_path: Path,
) -> None:
    config = load_config(CONFIG)

    artifacts = run_tournament(
        config=config,
        run_config=TournamentRunConfig(
            game_count=16,
            master_seed=73031,
            output_directory=tmp_path,
        ),
    )

    assert artifacts.results_csv.is_file()
    assert artifacts.summary_json.is_file()
    assert artifacts.representative_json.is_file()
    assert artifacts.representative_events_json.is_file()

    with artifacts.results_csv.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 64

    assert len({row["game_index"] for row in rows}) == 16

    summary = json.loads(artifacts.summary_json.read_text(encoding="utf-8"))

    assert summary["game_count"] == 16

    assert summary["result_rows"] == 64

    assert len(summary["strategy_summary"]) == 4

    assert len(summary["pairwise"]) == 6

    assert summary["representative"]["selection"]["winner_used_for_selection"] is False

    assert summary["representative"]["selection"]["seat_used_for_selection"] is False


def test_repeated_small_tournament_is_byte_deterministic(
    tmp_path: Path,
) -> None:
    config = load_config(CONFIG)

    first_dir = tmp_path / "first"

    second_dir = tmp_path / "second"

    first = run_tournament(
        config=config,
        run_config=TournamentRunConfig(
            game_count=16,
            master_seed=73031,
            output_directory=first_dir,
        ),
    )

    second = run_tournament(
        config=config,
        run_config=TournamentRunConfig(
            game_count=16,
            master_seed=73031,
            output_directory=second_dir,
        ),
    )

    assert first.results_csv.read_bytes() == second.results_csv.read_bytes()

    assert first.summary_json.read_bytes() == second.summary_json.read_bytes()

    assert first.representative_json.read_bytes() == second.representative_json.read_bytes()

    assert (
        first.representative_events_json.read_bytes()
        == second.representative_events_json.read_bytes()
    )
