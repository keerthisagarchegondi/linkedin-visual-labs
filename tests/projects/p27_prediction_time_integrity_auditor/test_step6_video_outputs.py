from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.video import (
    CLAIM_IDS_USED,
    KEYFRAME_FILENAMES,
    KEYFRAME_TIMES,
    STEP5_FINGERPRINT,
    VIDEO_DURATION_SECONDS,
    VIDEO_FPS,
    VIDEO_FRAME_COUNT,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    VideoContract,
    load_video_evidence,
    render_frame,
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def assets_root() -> Path:
    return repository_root() / "assets" / "p27_prediction_time_integrity_auditor"


def load_json(
    path: Path,
) -> dict[str, Any]:
    payload: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        payload,
        dict,
    ):
        raise TypeError(path.name)

    return payload


def test_video_contract_exact() -> None:
    contract = VideoContract()

    assert contract.width == 1080
    assert contract.height == 1350
    assert contract.fps == 30
    assert contract.duration_seconds == 45.0
    assert contract.frame_count == 1350

    assert VIDEO_WIDTH == 1080
    assert VIDEO_HEIGHT == 1350
    assert VIDEO_FPS == 30
    assert VIDEO_DURATION_SECONDS == 45.0
    assert VIDEO_FRAME_COUNT == 1350


def test_keyframe_contract_exact() -> None:
    assert len(KEYFRAME_TIMES) == 10

    assert len(KEYFRAME_FILENAMES) == 10

    assert KEYFRAME_TIMES[0] == 0.0

    assert KEYFRAME_TIMES[-1] == 44.8


def test_renderer_produces_correct_canvas() -> None:
    release, claims = load_video_evidence(assets_root())

    for timestamp in (
        0.0,
        6.0,
        12.0,
        18.0,
        23.0,
        28.0,
        33.0,
        38.0,
        43.0,
    ):
        frame = render_frame(
            release,
            claims,
            timestamp,
        )

        assert frame.size == (
            1080,
            1350,
        )

        assert frame.mode == "RGB"


def test_video_manifest_and_outputs() -> None:
    assets = assets_root()

    manifest = load_json(assets / "video" / "video_manifest.json")

    assert manifest["scope"] == "PROJECT7_STEP6_VIDEO"

    assert manifest["contract"]["width"] == 1080

    assert manifest["contract"]["height"] == 1350

    assert manifest["contract"]["fps"] == 30

    assert manifest["keyframe_count"] == 10

    assert manifest["claim_ids"] == list(CLAIM_IDS_USED)

    assert manifest["release_data"]["step5_fingerprint_sha256"] == STEP5_FINGERPRINT

    assert manifest["muted_comprehension"] is True

    assert manifest["evidence_policy"]["business_logic_recomputed"] is False

    assert manifest["evidence_policy"]["preview_metrics_used"] is False

    for name in (
        "project7_prediction_time_integrity.mp4",
        "project7_prediction_time_integrity_web.mp4",
        "project7_video_thumbnail.png",
        "video_manifest.json",
    ):
        path = assets / "video" / name

        assert path.is_file()
        assert path.stat().st_size > 0

    primary = manifest["primary_video"]

    assert primary["width"] == 1080

    assert primary["height"] == 1350

    assert primary["codec"] == "h264"

    assert primary["pixel_format"] == "yuv420p"

    assert abs(float(primary["frame_rate"]) - 30.0) < 0.01

    assert 44.0 <= float(primary["duration_seconds"]) <= 46.5


def test_ten_keyframes_and_contact_sheet() -> None:
    assets = assets_root()

    keyframes = assets / "video_keyframes"

    actual = tuple(path.name for path in sorted(keyframes.glob("*.png")))

    assert actual == tuple(sorted(KEYFRAME_FILENAMES))

    for name in KEYFRAME_FILENAMES:
        path = keyframes / name

        with Image.open(path) as image:
            assert image.size == (
                1080,
                1350,
            )

    sheet = assets / "images" / "video_keyframe_contact_sheet.png"

    assert sheet.is_file()
    assert sheet.stat().st_size > 10_000

    with Image.open(sheet) as image:
        assert image.width == 648
        assert image.height == 2025
