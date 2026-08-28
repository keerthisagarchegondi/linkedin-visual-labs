"""Step 7 V5 true-3D visual-system tests."""

from __future__ import annotations

from pathlib import Path

import matplotlib.image as mpimg

from linkedin_visual_labs.projects.p02_monopoly_ai.piece_assets_3d import (
    PIECE_NAMES,
    render_all_piece_assets,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.visual_v5 import (
    pickup_position,
)


def test_piece_contract_is_true_3d_asset_contract() -> None:
    assert PIECE_NAMES == {
        "collector": "silver_sports_coupe",
        "specialist": "silver_yacht",
        "cash_protector": "silver_armored_vault",
        "aggressive_builder": "silver_construction_loader",
    }


def test_piece_pickup_starts_on_source() -> None:
    start = (
        0.2,
        0.3,
    )

    end = (
        0.8,
        0.7,
    )

    x, y, lift = pickup_position(
        start,
        end,
        0.0,
    )

    assert x == start[0]

    assert y == start[1]

    assert lift == 0.0


def test_piece_pickup_lifts_during_motion() -> None:
    _, _, lift = pickup_position(
        (
            0.2,
            0.3,
        ),
        (
            0.8,
            0.7,
        ),
        0.5,
    )

    assert lift > 0.0


def test_piece_pickup_lands_on_destination() -> None:
    start = (
        0.2,
        0.3,
    )

    end = (
        0.8,
        0.7,
    )

    x, y, lift = pickup_position(
        start,
        end,
        1.0,
    )

    assert abs(x - end[0]) < 1e-12

    assert abs(y - end[1]) < 1e-12

    assert abs(lift) < 1e-12


def test_3d_piece_assets_are_transparent_rgba(
    tmp_path: Path,
) -> None:
    assets = render_all_piece_assets(
        tmp_path,
        show_progress=False,
    )

    assert len(assets) == 4

    for path in assets.values():
        image = mpimg.imread(path)

        assert image.ndim == 3

        assert image.shape[2] == 4


def test_all_four_piece_assets_are_nonempty(
    tmp_path: Path,
) -> None:
    assets = render_all_piece_assets(
        tmp_path,
        show_progress=False,
    )

    for path in assets.values():
        assert path.stat().st_size > 0


def test_final_visual_contract_source_markers() -> None:
    """Freeze the revised Step 7 V6 visual requirements."""

    from pathlib import Path

    source = Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/visual_v5.py").read_text(
        encoding="utf-8"
    )

    assert '"95% WILSON CI"' in source

    assert '"95% WILSON CONFIDENCE INTERVAL"' not in source

    assert '"Aggressive\\nBuilder"' in source

    assert "for row in range(5)" in source

    assert "for column in range(5)" in source

    assert "math.exp(" in source


def test_piece_pipeline_has_no_runtime_blender() -> None:
    from pathlib import Path

    source = Path("src/linkedin_visual_labs/projects/p02_monopoly_ai/piece_assets_3d.py").read_text(
        encoding="utf-8"
    )

    forbidden = (
        "import bpy",
        "mathutils",
        "mplot3d",
        "subprocess.run",
        "BLENDER_EXECUTABLE",
        "BLENDER_SCRIPT",
    )

    for marker in forbidden:
        assert marker not in source


def test_fluent_piece_manifest_exists() -> None:
    import json
    from pathlib import Path

    path = Path("assets/p02_monopoly_ai/fluent_3d_manifest.json")

    assert path.is_file()

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["source"] == ("microsoft/fluentui-emoji")

    assert payload["source_style"] == "3D"

    assert payload["license"] == "MIT"

    assert set(payload["assets"]) == {
        "collector",
        "specialist",
        "cash_protector",
        "aggressive_builder",
    }


def test_final_piece_art_license_bundle() -> None:
    import json
    from pathlib import Path

    root = Path("assets/p02_monopoly_ai")

    manifest_path = root / "fluent_3d_manifest.json"

    contract_path = root / "piece_visual_contract.json"

    notice_path = root / "fluent_3d" / "NOTICE.md"

    license_path = root / "fluent_3d" / "MICROSOFT_FLUENT_EMOJI_LICENSE.txt"

    for artifact in (
        manifest_path,
        contract_path,
        notice_path,
        license_path,
    ):
        assert artifact.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["source"] == "microsoft/fluentui-emoji"

    assert manifest["source_style"] == "3D"

    assert manifest["license"] == "MIT"

    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["source_family"] == "microsoft/fluentui-emoji"

    assert contract["source_license"] == "MIT"

    assert contract["runtime_3d_renderer"] is None

    assert "Microsoft Fluent Emoji" in notice_path.read_text(encoding="utf-8")

    assert "MIT License" in license_path.read_text(encoding="utf-8")


def test_v6_canonical_board_geometry_contract() -> None:
    from pathlib import Path

    from linkedin_visual_labs.projects.p02_monopoly_ai.visual_system import (
        board_positions,
        load_board_spaces,
    )

    spaces = load_board_spaces(Path("configs/p02_monopoly_ai.yaml"))

    positions = board_positions()

    assert len(spaces) == 40
    assert len(positions) == 40

    assert all(space.label.strip() for space in spaces)

    normalized_positions = {
        (
            round(float(x), 12),
            round(float(y), 12),
        )
        for x, y in positions
    }

    assert len(normalized_positions) == 40
