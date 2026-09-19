from __future__ import annotations

from pathlib import Path

from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.video import (
    KEYFRAME_TIMES,
    VIDEO_DURATION_SECONDS,
    VIDEO_FPS,
    VIDEO_FRAME_COUNT,
    VIDEO_HEIGHT,
    VIDEO_WIDTH,
    VideoContract,
    load_video_evidence,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.visualization import (
    FIGURE_FILES,
    render_all_figures,
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def assets_root() -> Path:
    return repository_root() / "assets" / "p27_prediction_time_integrity_auditor"


def test_video_contract_is_frozen() -> None:
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


def test_video_has_exactly_ten_keyframe_checkpoints() -> None:
    assert KEYFRAME_TIMES == (
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


def test_video_evidence_uses_frozen_step5_release() -> None:
    release, claims = load_video_evidence(assets_root())

    assert (
        release["step5_fingerprint_sha256"]
        == "7954203abe1cb0f5457c3658f2105cd16a0800528e81723ee970d259afe60ed0"
    )

    assert release["release_status"] == "PASS"

    assert claims["claim_count"] == 8


def test_all_required_research_figures_render(
    tmp_path: Path,
) -> None:
    temp_assets = tmp_path

    for name in (
        "release_data.json",
        "claim_register.json",
    ):
        (temp_assets / name).write_bytes((assets_root() / name).read_bytes())

    outputs = render_all_figures(temp_assets)

    assert len(outputs) == len(FIGURE_FILES)

    assert tuple(path.name for path in outputs) == FIGURE_FILES

    for path in outputs:
        assert path.is_file()
        assert path.stat().st_size > 10_000

        with Image.open(path) as image:
            assert image.width >= 800
            assert image.height >= 500
