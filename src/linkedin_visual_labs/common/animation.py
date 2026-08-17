"""Shared Matplotlib animation and FFmpeg export utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from matplotlib.animation import Animation, FFMpegWriter
from matplotlib.figure import Figure

from linkedin_visual_labs.common.media import (
    VideoMetadata,
    validate_video_metadata,
)
from linkedin_visual_labs.common.plotting import (
    DEFAULT_CANVAS,
    CanvasSpec,
)
from linkedin_visual_labs.common.validation import (
    ValidationError,
    require_positive_int,
)


@dataclass(frozen=True, slots=True)
class AnimationExportSettings:
    """Repository-wide FFmpeg export settings."""

    frame_rate: int = 30
    codec: str = "libx264"
    pixel_format: str = "yuv420p"
    bitrate_kbps: int = 4_000

    def __post_init__(self) -> None:
        require_positive_int(
            self.frame_rate,
            name="frame_rate",
        )

        require_positive_int(
            self.bitrate_kbps,
            name="bitrate_kbps",
        )

        if not self.codec.strip():
            raise ValidationError("animation codec must not be empty")

        if not self.pixel_format.strip():
            raise ValidationError("animation pixel_format must not be empty")


DEFAULT_ANIMATION_SETTINGS = AnimationExportSettings()


def export_matplotlib_animation(
    animation: Animation,
    figure: Figure,
    output_path: Path | str,
    *,
    canvas: CanvasSpec = DEFAULT_CANVAS,
    settings: AnimationExportSettings = DEFAULT_ANIMATION_SETTINGS,
    validate: bool = True,
) -> VideoMetadata | None:
    """Export a Matplotlib animation to H.264 MP4 through FFmpeg."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure.set_size_inches(
        *canvas.figsize_inches,
        forward=True,
    )
    figure.set_dpi(canvas.dpi)

    writer = FFMpegWriter(
        fps=settings.frame_rate,
        codec=settings.codec,
        bitrate=settings.bitrate_kbps,
        extra_args=[
            "-pix_fmt",
            settings.pixel_format,
            "-movflags",
            "+faststart",
        ],
    )

    animation.save(
        str(path),
        writer=writer,
        dpi=canvas.dpi,
    )

    if not validate:
        return None

    return validate_video_metadata(
        path,
        expected_width=canvas.width_px,
        expected_height=canvas.height_px,
        expected_frame_rate=float(settings.frame_rate),
        expected_codec="h264",
        expected_pixel_format=settings.pixel_format,
    )
