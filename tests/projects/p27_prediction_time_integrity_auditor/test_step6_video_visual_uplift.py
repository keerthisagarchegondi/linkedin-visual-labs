from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import (
    video,
)


def assets_root() -> Path:
    return Path(__file__).resolve().parents[3] / "assets" / "p27_prediction_time_integrity_auditor"


def image_sha(
    image: Image.Image,
) -> str:
    return hashlib.sha256(image.tobytes()).hexdigest()


def test_uplift_scene_schedule_exact() -> None:
    assert video.UPLIFT_SCENE_SCHEDULE == (
        ("S1", 0.0, 4.5),
        ("S2", 4.5, 8.5),
        ("S3", 8.5, 12.5),
        ("S4", 12.5, 17.0),
        ("S5", 17.0, 21.0),
        ("S6", 21.0, 25.0),
        ("S7", 25.0, 29.5),
        ("S8", 29.5, 34.0),
        ("S9", 34.0, 40.0),
        ("S10", 40.0, 45.0),
    )

    total = sum(end - start for _scene_id, start, end in video.UPLIFT_SCENE_SCHEDULE)

    assert total == 45.0


def test_scene_boundary_resolution() -> None:
    assert video.uplift_scene_id_for_time(-100.0) == "S1"

    assert video.uplift_scene_id_for_time(0.0) == "S1"

    assert video.uplift_scene_id_for_time(4.499) == "S1"

    assert video.uplift_scene_id_for_time(4.5) == "S2"

    assert video.uplift_scene_id_for_time(8.5) == "S3"

    assert video.uplift_scene_id_for_time(12.5) == "S4"

    assert video.uplift_scene_id_for_time(17.0) == "S5"

    assert video.uplift_scene_id_for_time(21.0) == "S6"

    assert video.uplift_scene_id_for_time(25.0) == "S7"

    assert video.uplift_scene_id_for_time(29.5) == "S8"

    assert video.uplift_scene_id_for_time(34.0) == "S9"

    assert video.uplift_scene_id_for_time(40.0) == "S10"

    assert video.uplift_scene_id_for_time(1000.0) == "S10"


def test_all_ten_scene_midpoints_render() -> None:
    release, claims = video.load_video_evidence(assets_root())

    for scene_id, start, end in video.UPLIFT_SCENE_SCHEDULE:
        midpoint = (start + end) / 2.0

        assert video.uplift_scene_id_for_time(midpoint) == scene_id

        frame = video.render_frame(
            release,
            claims,
            midpoint,
        )

        assert frame.size == (
            1080,
            1350,
        )

        assert frame.mode == "RGB"

        assert frame.getbbox() is not None


def test_representative_uplift_frames_are_deterministic() -> None:
    release, claims = video.load_video_evidence(assets_root())

    for timestamp in (
        6.5,
        31.5,
        37.0,
        42.5,
    ):
        first = video.render_frame(
            release,
            claims,
            timestamp,
        )

        second = video.render_frame(
            release,
            claims,
            timestamp,
        )

        assert image_sha(first) == image_sha(second)


def test_keyframe_preview_contract_matches_frozen_export() -> None:
    assert video.KEYFRAME_TIMES == (
        2.25,
        6.5,
        10.5,
        14.75,
        19.0,
        23.0,
        27.25,
        31.75,
        37.0,
        42.5,
    )

    assert video.KEYFRAME_FILENAMES == (
        "scene_01_S1.png",
        "scene_02_S2.png",
        "scene_03_S3.png",
        "scene_04_S4.png",
        "scene_05_S5.png",
        "scene_06_S6.png",
        "scene_07_S7.png",
        "scene_08_S8.png",
        "scene_09_S9.png",
        "scene_10_S10.png",
    )
