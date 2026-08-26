"""Interactive progress reporting for Project 3.

Progress reporting is deliberately separated from simulation logic.

It may print wall-clock timing, throughput, ETA, and cumulative
diagnostics, but none of those values participate in deterministic
simulation state or generated analytical artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from linkedin_visual_labs.projects.p02_monopoly_ai.constants import (
    StrategyId,
)


def _format_duration(
    seconds: float,
) -> str:
    """Format a duration as HH:MM:SS."""

    seconds = max(
        0.0,
        seconds,
    )

    total_seconds = round(seconds)

    hours, remainder = divmod(
        total_seconds,
        3600,
    )

    minutes, remaining_seconds = divmod(
        remainder,
        60,
    )

    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"


@dataclass(slots=True)
class TournamentProgressReporter:
    """Human-readable bounded tournament progress reporter."""

    total_games: int
    master_seed: int
    output_directory: str
    progress_every: int

    started_at: float = field(default_factory=perf_counter)

    wins: dict[
        StrategyId,
        int,
    ] = field(default_factory=lambda: {strategy_id: 0 for strategy_id in StrategyId})

    bankruptcies: dict[
        StrategyId,
        int,
    ] = field(default_factory=lambda: {strategy_id: 0 for strategy_id in StrategyId})

    def __post_init__(
        self,
    ) -> None:
        if self.total_games <= 0:
            raise ValueError("total_games must be positive")

        if self.progress_every <= 0:
            raise ValueError("progress_every must be positive")

    def start(
        self,
    ) -> None:
        """Print tournament header."""

        print(
            "\n============================================================",
            flush=True,
        )

        print(
            "PROJECT 3 — MONOPOLY AI TOURNAMENT",
            flush=True,
        )

        print(
            "============================================================",
            flush=True,
        )

        print(
            "\n[TOURNAMENT] starting",
            flush=True,
        )

        print(
            f"  games             : {self.total_games:,}",
            flush=True,
        )

        print(
            f"  master seed       : {self.master_seed:,}",
            flush=True,
        )

        print(
            f"  output            : {self.output_directory}",
            flush=True,
        )

        print(
            f"  progress interval : {self.progress_every:,} games",
            flush=True,
        )

        print(
            "\n[SIMULATION] running games...",
            flush=True,
        )

    def record_game(
        self,
        *,
        completed_games: int,
        winner: StrategyId,
        bankrupt_strategies: tuple[
            StrategyId,
            ...,
        ],
        last_game_index: int,
        last_termination_reason: str,
        rows_written: int,
    ) -> None:
        """Update counters and print at the requested cadence."""

        self.wins[winner] += 1

        for strategy_id in bankrupt_strategies:
            self.bankruptcies[strategy_id] += 1

        should_print = (
            completed_games == 1
            or completed_games % self.progress_every == 0
            or completed_games == self.total_games
        )

        if not should_print:
            return

        elapsed = perf_counter() - self.started_at

        games_per_second = completed_games / elapsed if elapsed > 0.0 else 0.0

        remaining_games = self.total_games - completed_games

        eta_seconds = remaining_games / games_per_second if games_per_second > 0.0 else 0.0

        percentage = 100.0 * completed_games / self.total_games

        print(
            f"\n[SIMULATION] {completed_games:,}/{self.total_games:,} ({percentage:5.1f}%)",
            flush=True,
        )

        print(
            f"  elapsed           : {_format_duration(elapsed)}",
            flush=True,
        )

        print(
            f"  throughput        : {games_per_second:.2f} games/sec",
            flush=True,
        )

        print(
            f"  ETA               : {_format_duration(eta_seconds)}",
            flush=True,
        )

        print(
            f"  rows written      : {rows_written:,}",
            flush=True,
        )

        print(
            f"  last game         : {last_game_index:,}",
            flush=True,
        )

        print(
            f"  last winner       : {winner.value}",
            flush=True,
        )

        print(
            f"  termination       : {last_termination_reason}",
            flush=True,
        )

        print(
            "\n  cumulative wins",
            flush=True,
        )

        for strategy_id in StrategyId:
            print(
                f"    {strategy_id.value:<20} {self.wins[strategy_id]:>6,}",
                flush=True,
            )

        print(
            "\n  cumulative bankruptcies",
            flush=True,
        )

        for strategy_id in StrategyId:
            print(
                f"    {strategy_id.value:<20} {self.bankruptcies[strategy_id]:>6,}",
                flush=True,
            )

    def stage(
        self,
        message: str,
    ) -> None:
        """Print one major tournament processing stage."""

        elapsed = perf_counter() - self.started_at

        print(
            f"\n{message} [elapsed={_format_duration(elapsed)}]",
            flush=True,
        )

    def complete(
        self,
    ) -> None:
        """Print completion summary."""

        elapsed = perf_counter() - self.started_at

        throughput = self.total_games / elapsed if elapsed > 0.0 else 0.0

        print(
            "\n============================================================",
            flush=True,
        )

        print(
            "[COMPLETE] tournament finished",
            flush=True,
        )

        print(
            f"  games             : {self.total_games:,}",
            flush=True,
        )

        print(
            f"  elapsed           : {_format_duration(elapsed)}",
            flush=True,
        )

        print(
            f"  average throughput: {throughput:.2f} games/sec",
            flush=True,
        )

        print(
            "============================================================",
            flush=True,
        )
