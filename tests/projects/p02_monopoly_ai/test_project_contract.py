"""Project 3 Step 1 contract validation tests."""

from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(".")

CONFIG = ROOT / "configs/p02_monopoly_ai.yaml"

RULES = ROOT / "docs/projects/p02_monopoly_ai_rules.md"

STRATEGIES = ROOT / "docs/projects/p02_monopoly_ai_strategies.md"

STORYBOARD = ROOT / "docs/projects/p02_monopoly_ai_storyboard.md"


def _payload() -> dict[str, object]:
    value = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    assert isinstance(
        value,
        dict,
    )

    return value


def test_contract_files_exist() -> None:
    for path in (
        CONFIG,
        RULES,
        STRATEGIES,
        STORYBOARD,
    ):
        assert path.is_file()
        assert path.stat().st_size > 0


def test_board_has_exactly_40_unique_spaces() -> None:
    payload = _payload()

    board = payload["board"]
    assert isinstance(board, dict)

    spaces = board["spaces"]
    assert isinstance(spaces, list)

    assert len(spaces) == 40

    indices = [
        space["index"]
        for space in spaces
        if isinstance(
            space,
            dict,
        )
    ]

    assert indices == list(range(40))

    ids = [
        space["space_id"]
        for space in spaces
        if isinstance(
            space,
            dict,
        )
    ]

    assert len(ids) == len(set(ids))


def test_board_taxonomy_matches_contract() -> None:
    payload = _payload()

    board = payload["board"]
    assert isinstance(board, dict)

    spaces = board["spaces"]
    assert isinstance(spaces, list)

    actual = Counter(
        str(space["type"])
        for space in spaces
        if isinstance(
            space,
            dict,
        )
    )

    expected = payload["board_space_taxonomy"]

    assert isinstance(
        expected,
        dict,
    )

    assert dict(actual) == expected


def test_four_strategy_contracts_exist() -> None:
    payload = _payload()

    strategies = payload["strategies"]
    assert isinstance(
        strategies,
        dict,
    )

    policies = strategies["policies"]
    assert isinstance(
        policies,
        dict,
    )

    assert set(policies) == {
        "collector",
        "specialist",
        "cash_protector",
        "aggressive_builder",
    }


def test_strategy_reserves_are_distinct() -> None:
    payload = _payload()

    strategies = payload["strategies"]
    assert isinstance(
        strategies,
        dict,
    )

    policies = strategies["policies"]
    assert isinstance(
        policies,
        dict,
    )

    reserves = {
        key: value["desired_cash_reserve"]
        for key, value in policies.items()
        if isinstance(
            value,
            dict,
        )
    }

    assert (
        reserves["cash_protector"]
        > reserves["specialist"]
        > reserves["collector"]
        > reserves["aggressive_builder"]
    )


def test_canonical_seed_sequence_is_unique() -> None:
    payload = _payload()

    seed_contract = payload["seed_contract"]
    assert isinstance(
        seed_contract,
        dict,
    )

    tournament = payload["tournament_seed_contract"]
    assert isinstance(
        tournament,
        dict,
    )

    namespace = str(seed_contract["namespace"])

    master_seed = int(tournament["canonical_master_seed"])

    game_count = int(tournament["canonical_game_count"])

    seeds = set()

    for game_index in range(game_count):
        raw = f"{namespace}:{master_seed}:{game_index}"

        digest = hashlib.sha256(raw.encode("utf-8")).digest()

        seeds.add(
            int.from_bytes(
                digest[:8],
                byteorder="big",
                signed=False,
            )
        )

    assert len(seeds) == game_count


def test_seat_rotation_is_exactly_balanced() -> None:
    payload = _payload()

    strategies = payload["strategies"]
    assert isinstance(
        strategies,
        dict,
    )

    order = strategies["canonical_order"]
    assignments = strategies["seat_rotation"]["assignments"]

    assert isinstance(order, list)
    assert isinstance(assignments, list)

    counts: Counter[tuple[str, int]] = Counter()

    for game_index in range(10000):
        assignment = assignments[game_index % 8]

        assert isinstance(
            assignment,
            list,
        )

        for seat, strategy_id in enumerate(assignment):
            counts[
                (
                    str(strategy_id),
                    seat,
                )
            ] += 1

    for strategy_id in order:
        for seat in range(4):
            assert (
                counts[
                    (
                        str(strategy_id),
                        seat,
                    )
                ]
                == 2500
            )


def test_pairwise_contract_has_six_pairs() -> None:
    payload = _payload()

    contract = payload["pairwise_comparison_contract"]

    assert isinstance(
        contract,
        dict,
    )

    pairs = contract["canonical_pairs"]

    assert isinstance(
        pairs,
        list,
    )

    assert len(pairs) == 6

    assert contract["inferential_test"]["multiple_comparison_correction"] == "Holm"


def test_tournament_contract_is_10000_games() -> None:
    payload = _payload()

    tournament = payload["tournament_contract"]

    assert isinstance(
        tournament,
        dict,
    )

    assert tournament["canonical_game_count"] == 10000

    assert tournament["canonical_result_rows"] == 40000


def test_representative_game_cannot_use_winner_identity() -> None:
    payload = _payload()

    contract = payload["representative_game_selection"]

    assert isinstance(
        contract,
        dict,
    )

    assert contract["manual_selection_forbidden"] is True

    assert contract["winner_identity_used_in_selection"] is False

    assert contract["seat_identity_used_in_selection"] is False


def test_result_csv_schema_is_40000_rows() -> None:
    payload = _payload()

    schema = payload["tournament_results_csv_schema"]

    assert isinstance(
        schema,
        dict,
    )

    assert schema["canonical_rows"] == 40000

    assert schema["grain"] == "one row per strategy per game"


def test_media_contract_is_exact() -> None:
    payload = _payload()

    media = payload["media_contract"]

    assert isinstance(
        media,
        dict,
    )

    assert media["width"] == 1080
    assert media["height"] == 1080
    assert media["fps"] == 30
    assert media["duration_seconds"] == 60.0
    assert media["frame_count"] == 1800
    assert media["codec"] == "h264"
    assert media["pixel_format"] == "yuv420p"


def test_storyboard_covers_exactly_60_seconds() -> None:
    payload = _payload()

    storyboard = payload["video_storyboard"]

    assert isinstance(
        storyboard,
        dict,
    )

    order = (
        "opening",
        "strategy_introduction",
        "representative_game",
        "scale_up",
        "leaderboard",
        "risk_reward",
        "winner_summary",
    )

    previous_end = 0.0

    for name in order:
        section = storyboard[name]

        assert isinstance(
            section,
            dict,
        )

        start = float(section["start_second"])

        end = float(section["end_second"])

        assert start == previous_end
        assert end > start

        previous_end = end

    assert previous_end == 60.0


def test_video_result_traceability_is_strict() -> None:
    payload = _payload()

    contract = payload["video_traceability_contract"]

    assert isinstance(
        contract,
        dict,
    )

    assert contract["hardcoded_winner_forbidden"] is True

    assert contract["hardcoded_result_metrics_forbidden"] is True

    assert contract["displayed_numeric_value_must_match_source"] is True

    assert contract["representative_game_event_must_match_log"] is True


def test_rules_document_has_sections_1_1_through_1_68() -> None:
    text = RULES.read_text(encoding="utf-8")

    for number in range(
        1,
        69,
    ):
        marker = f"## 1.{number} "

        assert text.count(marker) == 1


def test_required_disclaimer_is_present() -> None:
    disclaimer = "Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro."

    def normalize_whitespace(
        text: str,
    ) -> str:
        return " ".join(text.split())

    normalized_disclaimer = normalize_whitespace(disclaimer)

    assert normalized_disclaimer in normalize_whitespace(RULES.read_text(encoding="utf-8"))

    assert normalized_disclaimer in normalize_whitespace(STORYBOARD.read_text(encoding="utf-8"))
