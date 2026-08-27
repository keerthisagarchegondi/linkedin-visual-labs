"""Independent Step 6 validation tests."""

from __future__ import annotations

import math
from pathlib import Path

from linkedin_visual_labs.projects.p02_monopoly_ai.validation import (
    independent_exact_binomial_two_sided,
    independent_holm_adjust,
    independent_wilson_interval,
)


def test_independent_wilson_contains_observed_rate() -> None:
    low, high = independent_wilson_interval(
        2500,
        10000,
    )

    assert low < 0.25 < high


def test_independent_wilson_is_symmetric_near_half() -> None:
    first = independent_wilson_interval(
        450,
        1000,
    )

    second = independent_wilson_interval(
        550,
        1000,
    )

    assert math.isclose(
        first[0],
        1.0 - second[1],
        abs_tol=1e-12,
    )

    assert math.isclose(
        first[1],
        1.0 - second[0],
        abs_tol=1e-12,
    )


def test_independent_exact_binomial_is_symmetric() -> None:
    first = independent_exact_binomial_two_sided(
        450,
        1000,
    )

    second = independent_exact_binomial_two_sided(
        550,
        1000,
    )

    assert math.isclose(
        first,
        second,
        abs_tol=1e-15,
    )


def test_exact_binomial_half_is_one() -> None:
    assert math.isclose(
        independent_exact_binomial_two_sided(
            500,
            1000,
        ),
        1.0,
        abs_tol=1e-15,
    )


def test_holm_adjusted_values_are_not_below_raw() -> None:
    raw = {
        "a": 0.001,
        "b": 0.01,
        "c": 0.05,
        "d": 0.2,
        "e": 0.5,
        "f": 0.9,
    }

    adjusted = independent_holm_adjust(raw)

    assert set(adjusted) == set(raw)

    for key, raw_value in raw.items():
        assert adjusted[key] >= raw_value

        assert 0.0 <= adjusted[key] <= 1.0


def test_holm_adjustment_is_monotone_in_sorted_order() -> None:
    raw = {
        "a": 0.001,
        "b": 0.008,
        "c": 0.02,
        "d": 0.15,
        "e": 0.4,
        "f": 0.8,
    }

    adjusted = independent_holm_adjust(raw)

    ordered = sorted(
        raw,
        key=raw.__getitem__,
    )

    values = [adjusted[key] for key in ordered]

    assert values == sorted(values)


def test_seat_outcome_limits_are_diagnostic_not_hard_failures() -> None:
    """Seat outcome spread must not itself invalidate a balanced experiment."""

    from linkedin_visual_labs.projects.p02_monopoly_ai import (
        validation,
    )

    source = Path(validation.__file__).read_text(encoding="utf-8")

    assert "overall seat win-rate spread exceeds frozen fairness threshold" not in source

    assert "seat win-rate spread exceeds frozen threshold" not in source

    assert '"overall_seat_win_advantage_flag"' in source

    assert '"strategy_seat_win_advantage_flags"' in source

    assert '"seat_survival_bias_flag"' in source


def test_seat_fairness_report_declares_assignment_balance_as_hard_gate() -> None:
    """The report must distinguish randomization fairness from outcomes."""

    from linkedin_visual_labs.projects.p02_monopoly_ai import (
        validation,
    )

    source = Path(validation.__file__).read_text(encoding="utf-8")

    assert '"assignment_balance_is_hard_gate": True' in source

    assert '"outcome_seat_effect_is_diagnostic": True' in source


def test_post_bankruptcy_turn_end_is_bookkeeping_not_action() -> None:
    """TURN_END may close the same turn in which bankruptcy occurred."""

    from linkedin_visual_labs.projects.p02_monopoly_ai.validation import (
        validate_representative_events,
    )

    payload: dict[str, object] = {
        "events": [
            {
                "event_index": 0,
                "event_type": "TURN_START",
                "player_id": "player_1",
                "turn_number": 12,
            },
            {
                "event_index": 1,
                "event_type": "BANKRUPTCY",
                "player_id": "player_1",
                "turn_number": 12,
            },
            {
                "event_index": 2,
                "event_type": "TURN_END",
                "player_id": "player_1",
                "turn_number": 12,
            },
            {
                "event_index": 3,
                "event_type": "GAME_END",
                "player_id": None,
                "turn_number": 12,
            },
        ]
    }

    result = validate_representative_events(payload)

    assert result["bankrupt_players_stop_acting"] is True

    assert result["post_bankruptcy_bookkeeping_events"] == 1


def test_post_bankruptcy_new_gameplay_action_is_rejected() -> None:
    """A bankrupt player cannot begin or perform later gameplay."""

    import pytest

    from linkedin_visual_labs.projects.p02_monopoly_ai.validation import (
        validate_representative_events,
    )

    payload: dict[str, object] = {
        "events": [
            {
                "event_index": 0,
                "event_type": "BANKRUPTCY",
                "player_id": "player_1",
                "turn_number": 12,
            },
            {
                "event_index": 1,
                "event_type": "TURN_START",
                "player_id": "player_1",
                "turn_number": 13,
            },
        ]
    }

    with pytest.raises(
        ValueError,
        match="bankrupt player acted after bankruptcy",
    ):
        validate_representative_events(payload)


def test_exact_binomial_supports_canonical_10000_game_scale() -> None:
    """Canonical pairwise tests must not overflow at n=10,000."""

    value = independent_exact_binomial_two_sided(
        5000,
        10000,
    )

    assert math.isclose(
        value,
        1.0,
        abs_tol=1e-15,
    )


def test_exact_binomial_canonical_scale_is_symmetric() -> None:
    """Exact p-values remain symmetric around n/2."""

    lower = independent_exact_binomial_two_sided(
        4700,
        10000,
    )

    upper = independent_exact_binomial_two_sided(
        5300,
        10000,
    )

    assert math.isclose(
        lower,
        upper,
        rel_tol=1e-12,
        abs_tol=1e-15,
    )

    assert 0.0 <= lower <= 1.0
