"""Project 3 Step 7 V4 cinematic visual regression tests."""

from __future__ import annotations

import ast
from pathlib import Path

import matplotlib.image as mpimg

from linkedin_visual_labs.projects.p02_monopoly_ai.cinematic_storyboard import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    PREVIEW_MOMENTS,
    STORY_SEGMENTS,
    validate_storyboard_contract,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
    DIE_PIPS,
    DISCLAIMER,
    FRAME_TITLES,
    STRATEGY_PIECES,
    THEME,
    board_positions,
    load_board_spaces,
)

CONFIG_PATH = Path("configs/p02_monopoly_ai.yaml")


def test_storyboard_contract() -> None:
    validate_storyboard_contract()


def test_sixty_second_contract() -> None:
    assert STORY_SEGMENTS[0].start_second == 0.0

    assert STORY_SEGMENTS[-1].end_second == 60.0


def test_first_fifteen_seconds_have_dense_keyframes() -> None:
    early = [moment for moment in PREVIEW_MOMENTS if moment.second <= 15.0]

    assert len(early) >= 5


def test_visual_contract_is_square_1080() -> None:
    assert FRAME_WIDTH == 1080
    assert FRAME_HEIGHT == 1080


def test_board_geometry_has_40_unique_positions() -> None:
    positions = board_positions()

    assert len(positions) == 40

    assert len(set(positions)) == 40


def test_canonical_board_has_40_labels() -> None:
    spaces = load_board_spaces(CONFIG_PATH)

    assert len(spaces) == 40

    assert all(space.label.strip() for space in spaces)


def test_original_non_property_icon_categories_exist() -> None:
    spaces = load_board_spaces(CONFIG_PATH)

    categories = {space.space_type for space in spaces}

    assert "property" in categories

    assert any(
        category in categories
        for category in (
            "start",
            "transit",
            "jail",
            "event",
            "utility",
            "fee",
            "rest",
        )
    )


def test_strategy_pieces_are_metallic_object_tokens() -> None:
    assert STRATEGY_PIECES == {
        "collector": "silver_sports_coupe",
        "specialist": "silver_yacht",
        "cash_protector": "silver_armored_vault",
        "aggressive_builder": "silver_construction_loader",
    }


def test_all_piece_bodies_share_silver_palette() -> None:
    assert THEME.silver_dark == "#555E69"
    assert THEME.silver_mid == "#A7B0BA"
    assert THEME.silver_light == "#E8EDF2"


def test_dice_use_pips_not_numeric_face_text() -> None:
    assert set(DIE_PIPS) == {
        1,
        2,
        3,
        4,
        5,
        6,
    }

    assert len(DIE_PIPS[6]) == 6


def test_frame_titles_are_complete_strings() -> None:
    assert FRAME_TITLES["03_hook_liquidity"] == "WHO SURVIVES 10,000 GAMES?"

    assert FRAME_TITLES["04_strategy_gameplay"] == "FOUR STRATEGIES. FOUR PERSONALITIES."

    assert FRAME_TITLES["11_risk_reward"] == "WIN RATE ISN'T THE WHOLE STORY"

    assert FRAME_TITLES["12_result"] == "THE DATA GETS THE LAST WORD"


def test_danger_language_is_red() -> None:
    assert THEME.danger == "#E53935"


def test_counter_is_cinematic_gold() -> None:
    assert THEME.gold == "#FFD166"


def test_typography_is_neutral() -> None:
    assert THEME.font_family == "DejaVu Sans"


def test_disclaimer_is_frozen() -> None:
    assert DISCLAIMER == (
        "Unofficial analytical simulation. Not affiliated with or endorsed by Hasbro."
    )


def test_visual_source_contains_no_runtime_python_hash_call() -> None:
    from linkedin_visual_labs.projects.p02_monopoly_ai import (
        visual_system,
    )

    source = Path(visual_system.__file__).read_text(encoding="utf-8")

    tree = ast.parse(source)

    calls = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(
                node,
                ast.Call,
            )
            and isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id == "hash"
        )
    ]

    assert not calls


def test_cash_component_prints_dollar_value() -> None:
    from linkedin_visual_labs.projects.p02_monopoly_ai import (
        visual_system,
    )

    source = Path(visual_system.__file__).read_text(encoding="utf-8")

    assert 'f"${amount:,}"' in source


def test_liquidity_warning_contains_exclamation() -> None:
    from linkedin_visual_labs.projects.p02_monopoly_ai import (
        visual_system,
    )

    source = Path(visual_system.__file__).read_text(encoding="utf-8")

    assert "draw_warning_badge" in source
    assert '"!"' in source


def test_no_official_visual_asset_references() -> None:
    from linkedin_visual_labs.projects.p02_monopoly_ai import (
        visual_system,
    )

    source = Path(visual_system.__file__).read_text(encoding="utf-8").lower()

    forbidden = (
        "rich uncle pennybags",
        "mr. monopoly",
        "monopoly logo",
        "monopoly font",
        "hasbro font",
        "official token",
        "official chance card",
        "official community chest",
    )

    for phrase in forbidden:
        assert phrase not in source


def test_generated_v4_preview_dimensions() -> None:
    root = Path("outputs/p02_monopoly_ai/visual/cinematic_preview_v4")

    if not root.is_dir():
        return

    for moment in PREVIEW_MOMENTS:
        path = root / (moment.key + ".png")

        assert path.is_file()

        image = mpimg.imread(path)

        assert image.shape[0] == FRAME_HEIGHT

        assert image.shape[1] == FRAME_WIDTH
