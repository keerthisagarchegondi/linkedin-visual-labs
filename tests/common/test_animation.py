"""Tests for Matplotlib animation and FFmpeg export."""

from __future__ import annotations

from pathlib import Path

import pytest
from matplotlib.animation import FuncAnimation
from matplotlib.artist import Artist

from linkedin_visual_labs.common.animation import (
    AnimationExportSettings,
    export_matplotlib_animation,
)
from linkedin_visual_labs.common.media import (
    MediaValidationError,
    probe_video,
    validate_video_metadata,
)
from linkedin_visual_labs.common.plotting import (
    CanvasSpec,
    create_canvas,
)


def test_matplotlib_animation_exports_valid_h264_mp4(
    tmp_path: Path,
) -> None:
    canvas = CanvasSpec(
        width_px=320,
        height_px=400,
        dpi=100,
        safe_margin_px=20,
    )

    settings = AnimationExportSettings(
        frame_rate=10,
        bitrate_kbps=1_000,
    )

    figure, axes = create_canvas(
        spec=canvas,
    )

    axes.set_xlim(0, 4)
    axes.set_ylim(0, 4)

    (line,) = axes.plot(
        [],
        [],
    )

    def update(
        frame: int,
    ) -> tuple[Artist, ...]:
        line.set_data(
            [0, frame],
            [0, frame],
        )

        return (line,)

    animation = FuncAnimation(
        figure,
        update,
        frames=4,
        interval=100,
        blit=False,
    )

    output = tmp_path / "animation.mp4"

    metadata = export_matplotlib_animation(
        animation,
        figure,
        output,
        canvas=canvas,
        settings=settings,
    )

    assert output.is_file()
    assert metadata is not None
    assert metadata.width_px == 320
    assert metadata.height_px == 400
    assert metadata.frame_rate == pytest.approx(
        10.0,
        abs=0.05,
    )
    assert metadata.codec_name == "h264"
    assert metadata.pixel_format == "yuv420p"
    assert metadata.duration_seconds > 0


def test_probe_video_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        MediaValidationError,
        match="does not exist",
    ):
        probe_video(tmp_path / "missing.mp4")


def test_video_validation_rejects_wrong_dimensions(
    tmp_path: Path,
) -> None:
    canvas = CanvasSpec(
        width_px=320,
        height_px=400,
        dpi=100,
        safe_margin_px=20,
    )

    settings = AnimationExportSettings(
        frame_rate=10,
        bitrate_kbps=1_000,
    )

    figure, axes = create_canvas(
        spec=canvas,
    )

    (point,) = axes.plot(
        [],
        [],
        marker="o",
    )

    axes.set_xlim(0, 1)
    axes.set_ylim(0, 1)

    def update(
        frame: int,
    ) -> tuple[Artist, ...]:
        value = frame / 2

        point.set_data(
            [value],
            [value],
        )

        return (point,)

    animation = FuncAnimation(
        figure,
        update,
        frames=3,
        interval=100,
        blit=False,
    )

    output = tmp_path / "video.mp4"

    export_matplotlib_animation(
        animation,
        figure,
        output,
        canvas=canvas,
        settings=settings,
    )

    with pytest.raises(
        MediaValidationError,
        match="width mismatch",
    ):
        validate_video_metadata(
            output,
            expected_width=1080,
            expected_height=400,
            expected_frame_rate=10.0,
        )
