from __future__ import annotations

from pathlib import Path

from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import (
    video,
)


def assets_root() -> Path:
    return Path(__file__).resolve().parents[3] / "assets" / "p27_prediction_time_integrity_auditor"


def test_keyframes_map_one_to_one_to_frozen_scenes() -> None:
    expected_ids = (
        "S1",
        "S2",
        "S3",
        "S4",
        "S5",
        "S6",
        "S7",
        "S8",
        "S9",
        "S10",
    )

    assert len(video.KEYFRAME_TIMES) == 10
    assert len(video.KEYFRAME_FILENAMES) == 10

    for (
        expected_scene,
        timestamp,
        filename,
    ) in zip(
        expected_ids,
        video.KEYFRAME_TIMES,
        video.KEYFRAME_FILENAMES,
        strict=True,
    ):
        assert video.uplift_scene_id_for_time(timestamp) == expected_scene

        assert filename == (f"scene_{int(expected_scene[1:]):02d}_{expected_scene}.png")


def test_rendered_preview_contract() -> None:
    root = assets_root()

    keyframes = root / "video" / "keyframes"

    assert keyframes.is_dir()

    actual = tuple(path.name for path in sorted(keyframes.glob("*.png")))

    assert actual == tuple(sorted(video.KEYFRAME_FILENAMES))

    for filename in video.KEYFRAME_FILENAMES:
        path = keyframes / filename

        assert path.stat().st_size > 20_000

        with Image.open(path) as image:
            assert image.size == (
                1080,
                1350,
            )

            assert image.mode == "RGB"


def test_contact_sheet_matches_frozen_export_geometry() -> None:
    path = assets_root() / "video" / "project7_prediction_time_integrity_contact_sheet.png"

    assert path.is_file()
    assert path.stat().st_size > 20_000

    with Image.open(path) as image:
        assert image.size == (
            1020,
            510,
        )

        assert image.mode == "RGB"
