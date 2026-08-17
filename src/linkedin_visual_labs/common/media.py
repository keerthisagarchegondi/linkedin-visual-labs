"""Media export validation and generation-manifest utilities."""

from __future__ import annotations

import json
import struct
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from matplotlib.figure import Figure

from linkedin_visual_labs.common.plotting import (
    DEFAULT_CANVAS,
    DEFAULT_THEME,
    CanvasSpec,
    VisualTheme,
)
from linkedin_visual_labs.common.validation import (
    ValidationError,
    ensure_json_serializable,
    require_non_negative_int,
    require_positive_int,
    validate_project_id,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class MediaValidationError(ValidationError):
    """Raised when generated media violates the shared specification."""


@dataclass(frozen=True, slots=True)
class ImageMetadata:
    """Validated raster-image metadata."""

    width_px: int
    height_px: int
    format: str = "PNG"


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    """Metadata extracted from the primary video stream."""

    width_px: int
    height_px: int
    frame_rate: float
    duration_seconds: float
    codec_name: str
    pixel_format: str


def save_figure_png(
    figure: Figure,
    output_path: Path | str,
    *,
    spec: CanvasSpec = DEFAULT_CANVAS,
    theme: VisualTheme = DEFAULT_THEME,
) -> ImageMetadata:
    """Save a Matplotlib figure as an exact-dimension PNG."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    figure.set_size_inches(
        *spec.figsize_inches,
        forward=True,
    )
    figure.set_dpi(spec.dpi)
    figure.set_facecolor(theme.background)

    figure.savefig(
        path,
        format="png",
        dpi=spec.dpi,
        facecolor=theme.background,
        edgecolor="none",
        transparent=False,
    )

    return validate_png_dimensions(
        path,
        expected_width=spec.width_px,
        expected_height=spec.height_px,
    )


def read_png_dimensions(
    path: Path | str,
) -> ImageMetadata:
    """Read PNG dimensions directly from the IHDR chunk."""
    image_path = Path(path)

    if not image_path.is_file():
        raise MediaValidationError(f"PNG file does not exist: {image_path}")

    with image_path.open("rb") as file:
        signature = file.read(8)

        if signature != PNG_SIGNATURE:
            raise MediaValidationError(f"file is not a valid PNG: {image_path}")

        ihdr_length_bytes = file.read(4)
        ihdr_type = file.read(4)

        if len(ihdr_length_bytes) != 4:
            raise MediaValidationError(f"PNG IHDR length is missing: {image_path}")

        if ihdr_type != b"IHDR":
            raise MediaValidationError(f"PNG IHDR chunk is missing: {image_path}")

        ihdr_length = struct.unpack(
            ">I",
            ihdr_length_bytes,
        )[0]

        if ihdr_length != 13:
            raise MediaValidationError(f"unexpected PNG IHDR size: {ihdr_length}")

        ihdr_data = file.read(13)

        if len(ihdr_data) != 13:
            raise MediaValidationError(f"PNG IHDR data is incomplete: {image_path}")

        width_px, height_px = struct.unpack(
            ">II",
            ihdr_data[:8],
        )

    return ImageMetadata(
        width_px=width_px,
        height_px=height_px,
    )


def validate_png_dimensions(
    path: Path | str,
    *,
    expected_width: int,
    expected_height: int,
) -> ImageMetadata:
    """Validate exact PNG dimensions."""
    width = require_positive_int(
        expected_width,
        name="expected_width",
    )

    height = require_positive_int(
        expected_height,
        name="expected_height",
    )

    metadata = read_png_dimensions(path)

    if metadata.width_px != width:
        raise MediaValidationError(
            f"PNG width mismatch: expected {width}, found {metadata.width_px}"
        )

    if metadata.height_px != height:
        raise MediaValidationError(
            f"PNG height mismatch: expected {height}, found {metadata.height_px}"
        )

    return metadata


def _parse_frame_rate(value: str) -> float:
    """Parse an ffprobe frame-rate fraction."""
    numerator_text, separator, denominator_text = value.partition("/")

    if not separator:
        try:
            return float(value)
        except ValueError as exc:
            raise MediaValidationError(f"invalid ffprobe frame rate: {value!r}") from exc

    try:
        numerator = float(numerator_text)
        denominator = float(denominator_text)
    except ValueError as exc:
        raise MediaValidationError(f"invalid ffprobe frame rate: {value!r}") from exc

    if denominator == 0:
        raise MediaValidationError("ffprobe returned a zero frame-rate denominator")

    return numerator / denominator


def probe_video(
    path: Path | str,
) -> VideoMetadata:
    """Extract primary-video metadata with ffprobe."""
    video_path = Path(path)

    if not video_path.is_file():
        raise MediaValidationError(f"video file does not exist: {video_path}")

    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        ("stream=width,height,avg_frame_rate,r_frame_rate,codec_name,pix_fmt:format=duration"),
        "-of",
        "json",
        str(video_path),
    ]

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise MediaValidationError("ffprobe executable was not found") from exc
    except subprocess.CalledProcessError as exc:
        raise MediaValidationError(
            f"ffprobe failed for {video_path}: {exc.stderr.strip()}"
        ) from exc

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise MediaValidationError("ffprobe returned invalid JSON") from exc

    streams = payload.get("streams")

    if not isinstance(streams, list) or not streams:
        raise MediaValidationError(f"ffprobe found no video stream: {video_path}")

    stream = streams[0]

    if not isinstance(stream, dict):
        raise MediaValidationError("ffprobe video-stream metadata is malformed")

    format_payload = payload.get("format", {})

    if not isinstance(format_payload, dict):
        raise MediaValidationError("ffprobe format metadata is malformed")

    frame_rate_text = str(stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "")

    try:
        width_px = int(stream["width"])
        height_px = int(stream["height"])
        duration_seconds = float(format_payload["duration"])
        codec_name = str(stream["codec_name"])
        pixel_format = str(stream["pix_fmt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MediaValidationError("ffprobe output is missing required video metadata") from exc

    frame_rate = _parse_frame_rate(frame_rate_text)

    return VideoMetadata(
        width_px=width_px,
        height_px=height_px,
        frame_rate=frame_rate,
        duration_seconds=duration_seconds,
        codec_name=codec_name,
        pixel_format=pixel_format,
    )


def validate_video_metadata(
    path: Path | str,
    *,
    expected_width: int,
    expected_height: int,
    expected_frame_rate: float,
    expected_codec: str = "h264",
    expected_pixel_format: str = "yuv420p",
    frame_rate_tolerance: float = 0.05,
    minimum_duration_seconds: float | None = None,
    maximum_duration_seconds: float | None = None,
) -> VideoMetadata:
    """Validate generated video metadata using ffprobe."""
    metadata = probe_video(path)

    if metadata.width_px != expected_width:
        raise MediaValidationError(
            f"video width mismatch: expected {expected_width}, found {metadata.width_px}"
        )

    if metadata.height_px != expected_height:
        raise MediaValidationError(
            f"video height mismatch: expected {expected_height}, found {metadata.height_px}"
        )

    if abs(metadata.frame_rate - expected_frame_rate) > (frame_rate_tolerance):
        raise MediaValidationError(
            f"video frame-rate mismatch: expected "
            f"{expected_frame_rate}, found {metadata.frame_rate}"
        )

    if metadata.codec_name != expected_codec:
        raise MediaValidationError(
            f"video codec mismatch: expected {expected_codec!r}, found {metadata.codec_name!r}"
        )

    if metadata.pixel_format != expected_pixel_format:
        raise MediaValidationError(
            f"video pixel format mismatch: expected "
            f"{expected_pixel_format!r}, "
            f"found {metadata.pixel_format!r}"
        )

    if (
        minimum_duration_seconds is not None
        and metadata.duration_seconds < minimum_duration_seconds
    ):
        raise MediaValidationError(
            f"video duration {metadata.duration_seconds:.3f}s "
            f"is shorter than {minimum_duration_seconds:.3f}s"
        )

    if (
        maximum_duration_seconds is not None
        and metadata.duration_seconds > maximum_duration_seconds
    ):
        raise MediaValidationError(
            f"video duration {metadata.duration_seconds:.3f}s "
            f"is longer than {maximum_duration_seconds:.3f}s"
        )

    return metadata


def current_git_commit(
    repository_root: Path | str,
) -> str | None:
    """Return the current Git commit hash when available."""
    root = Path(repository_root)

    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "rev-parse",
                "HEAD",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    commit = completed.stdout.strip()

    return commit or None


def build_generation_manifest(
    *,
    project_id: str,
    asset_name: str,
    configuration_path: Path | str,
    random_seed: int,
    width: int,
    height: int,
    repository_root: Path | str,
    metrics: Mapping[str, object] | None = None,
    frame_rate: float | None = None,
    duration_seconds: float | None = None,
    generation_timestamp: str | None = None,
    git_commit: str | None = None,
) -> dict[str, object]:
    """Build the shared machine-readable generation manifest."""
    canonical_project_id = validate_project_id(project_id)

    seed = require_non_negative_int(
        random_seed,
        name="random_seed",
    )

    manifest: dict[str, object] = {
        "project_id": canonical_project_id,
        "asset_name": asset_name,
        "generation_timestamp": (
            generation_timestamp
            if generation_timestamp is not None
            else datetime.now(UTC).isoformat()
        ),
        "git_commit": (
            git_commit if git_commit is not None else current_git_commit(repository_root)
        ),
        "configuration_path": Path(configuration_path).as_posix(),
        "random_seed": seed,
        "width": require_positive_int(
            width,
            name="width",
        ),
        "height": require_positive_int(
            height,
            name="height",
        ),
        "frame_rate": frame_rate,
        "duration_seconds": duration_seconds,
        "metrics": dict(metrics or {}),
    }

    ensure_json_serializable(
        manifest,
        name="generation manifest",
    )

    return manifest


def write_generation_manifest(
    manifest: Mapping[str, object],
    output_path: Path | str,
) -> Path:
    """Write a generation manifest atomically as formatted JSON."""
    ensure_json_serializable(
        dict(manifest),
        name="generation manifest",
    )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    temporary_path.write_text(
        json.dumps(
            dict(manifest),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)

    return path
