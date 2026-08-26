"""Deterministic random streams for Project 3."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass

NAMESPACE = "p02-monopoly-ai"


def derive_seed(
    base_seed: int,
    stream_label: str,
) -> int:
    """Derive one deterministic unsigned 64-bit stream seed."""

    raw = f"{NAMESPACE}:{base_seed}:{stream_label}"

    digest = hashlib.sha256(raw.encode("utf-8")).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )


@dataclass(frozen=True, slots=True)
class DiceRoll:
    """Result of two six-sided dice."""

    die_1: int
    die_2: int

    def __post_init__(self) -> None:
        for value in (
            self.die_1,
            self.die_2,
        ):
            if not 1 <= value <= 6:
                raise ValueError("each die must be between 1 and 6")

    @property
    def total(self) -> int:
        return self.die_1 + self.die_2

    @property
    def is_doubles(self) -> bool:
        return self.die_1 == self.die_2


class DiceRoller:
    """Deterministic two-die roller."""

    def __init__(
        self,
        game_seed: int,
    ) -> None:
        self._rng = random.Random(
            derive_seed(
                game_seed,
                "dice",
            )
        )

    def roll(self) -> DiceRoll:
        return DiceRoll(
            die_1=self._rng.randint(
                1,
                6,
            ),
            die_2=self._rng.randint(
                1,
                6,
            ),
        )


class RandomStreams:
    """Independent deterministic random streams for one game."""

    def __init__(
        self,
        game_seed: int,
    ) -> None:
        self.dice = DiceRoller(game_seed)

        self.chance = random.Random(
            derive_seed(
                game_seed,
                "chance",
            )
        )

        self.community = random.Random(
            derive_seed(
                game_seed,
                "community",
            )
        )

        self.tie_break_seed = derive_seed(
            game_seed,
            "tie_break",
        )


def deterministic_tie_rank(
    tie_seed: int,
    player_id: str,
) -> int:
    """Return deterministic player-specific final tie rank."""

    raw = f"{NAMESPACE}:{tie_seed}:{player_id}"

    digest = hashlib.sha256(raw.encode("utf-8")).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )


def derive_game_seed(
    master_seed: int,
    game_index: int,
) -> int:
    """Derive the canonical deterministic seed for one tournament game."""

    if game_index < 0:
        raise ValueError("game_index cannot be negative")

    raw = f"{NAMESPACE}:{master_seed}:{game_index}"

    digest = hashlib.sha256(raw.encode("utf-8")).digest()

    return int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )
