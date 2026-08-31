"""Deterministic cinematic story planning for Project 3 video."""

from __future__ import annotations

from dataclasses import dataclass

from linkedin_visual_labs.projects.p02_monopoly_ai.video_replay import (
    STRATEGIES,
    TurnBeat,
)


@dataclass(frozen=True)
class StoryPlan:
    dice_turn: TurnBeat
    move_turn: TurnBeat
    purchase_turn: TurnBeat
    build_turn: TurnBeat
    rent_turn: TurnBeat
    shock_turn: TurnBeat
    survival_turn: TurnBeat
    strategy_turns: tuple[TurnBeat, ...]
    narrative_turns: tuple[TurnBeat, ...]


ACTION_SCORE = {
    "BANKRUPTCY": 120,
    "BUILD": 110,
    "GROUP_COMPLETE": 105,
    "RENT": 100,
    "PURCHASE": 90,
    "PASS_START": 65,
    "EVENT_DRAW": 55,
    "CASH_TRANSFER": 50,
    "MOVE": 30,
    "TURN": 10,
}


def cash_change(
    turn: TurnBeat,
) -> float:
    strategy = turn.strategy_id

    before = turn.state_before.cash[strategy]

    after = turn.state_after.cash[strategy]

    return after - before


def interesting(
    turn: TurnBeat,
) -> bool:
    return turn.dice is not None and turn.from_position != turn.to_position


def first_matching(
    turns: tuple[TurnBeat, ...],
    action: str,
) -> TurnBeat | None:
    return next(
        (turn for turn in turns if turn.primary_action == action),
        None,
    )


def best_action_turn(
    turns: tuple[TurnBeat, ...],
    action: str,
) -> TurnBeat:
    exact = first_matching(
        turns,
        action,
    )

    if exact is not None:
        return exact

    candidates = [turn for turn in turns if interesting(turn)]

    if not candidates:
        raise RuntimeError("Representative game has no animated turns.")

    return max(
        candidates,
        key=lambda turn: (
            ACTION_SCORE.get(
                turn.primary_action,
                0,
            ),
            -turn.index,
        ),
    )


def most_negative_cash_turn(
    turns: tuple[TurnBeat, ...],
) -> TurnBeat:
    candidates = [turn for turn in turns if interesting(turn)]

    if not candidates:
        raise RuntimeError("No turns available for cash-shock selection.")

    return min(
        candidates,
        key=lambda turn: (
            cash_change(turn),
            turn.index,
        ),
    )


def strategy_intro_turns(
    turns: tuple[TurnBeat, ...],
) -> tuple[TurnBeat, ...]:
    selected: list[TurnBeat] = []

    for strategy in STRATEGIES:
        candidate = next(
            (turn for turn in turns if (turn.strategy_id == strategy and interesting(turn))),
            None,
        )

        if candidate is None:
            candidate = next(
                (turn for turn in turns if turn.strategy_id == strategy),
                None,
            )

        if candidate is None:
            raise RuntimeError(f"No representative turn for {strategy}")

        selected.append(candidate)

    return tuple(selected)


def narrative_sequence(
    turns: tuple[TurnBeat, ...],
    *,
    count: int = 6,
) -> tuple[TurnBeat, ...]:
    candidates = [turn for turn in turns if interesting(turn)]

    if len(candidates) < count:
        raise RuntimeError("Not enough real representative turns for cinematic mini-story.")

    # Choose one strong event from chronological windows rather
    # than six unrelated global maxima. This preserves the feeling
    # of watching one evolving match.
    result: list[TurnBeat] = []

    window_size = max(
        1,
        len(candidates) // count,
    )

    for index in range(count):
        start = index * window_size

        end = (
            len(candidates)
            if index == count - 1
            else min(
                len(candidates),
                (index + 1) * window_size,
            )
        )

        window = candidates[start:end]

        if not window:
            continue

        chosen = max(
            window,
            key=lambda turn: (
                ACTION_SCORE.get(
                    turn.primary_action,
                    0,
                ),
                -turn.index,
            ),
        )

        result.append(chosen)

    result = sorted(
        {turn.index: turn for turn in result}.values(),
        key=lambda turn: turn.index,
    )

    if len(result) < 4:
        raise RuntimeError("Narrative selection collapsed to fewer than four distinct turns.")

    return tuple(result)


def build_story_plan(
    turns: tuple[TurnBeat, ...],
) -> StoryPlan:
    animated = tuple(turn for turn in turns if interesting(turn))

    if not animated:
        raise RuntimeError("Representative game contains no dice + movement turns.")

    dice_turn = animated[0]

    purchase = best_action_turn(
        turns,
        "PURCHASE",
    )

    build = best_action_turn(
        turns,
        "BUILD",
    )

    rent = best_action_turn(
        turns,
        "RENT",
    )

    shock = most_negative_cash_turn(turns)

    bankruptcy = first_matching(
        turns,
        "BANKRUPTCY",
    )

    survival = bankruptcy if bankruptcy is not None else shock

    return StoryPlan(
        dice_turn=dice_turn,
        move_turn=dice_turn,
        purchase_turn=purchase,
        build_turn=build,
        rent_turn=rent,
        shock_turn=shock,
        survival_turn=survival,
        strategy_turns=(strategy_intro_turns(turns)),
        narrative_turns=(narrative_sequence(turns)),
    )
