"""Production video pipeline for the pair-dice Bayesian experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg

from linkedin_visual_labs.projects.p01_bayesian_dice.config import (
    DEFAULT_CONFIG_PATH,
    load_dice_config,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    PAIR_CASE_IDS,
    DiceModelError,
    DiceProjectConfig,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pair_inference import (
    PairInferenceResult,
    infer_all_pair_cases,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pair_metrics import (
    build_pair_validation_report,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pair_visualization import (
    FRAME_HEIGHT_PX,
    FRAME_WIDTH_PX,
    build_pair_dashboard_frame,
    validate_pair_dashboard_frame,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pipeline import (
    build_pipeline_context,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.simulation import (
    simulate_all_pair_cases,
)

VIDEO_CODEC = "libx264"
VIDEO_PIXEL_FORMAT = "yuv420p"
VIDEO_CONTAINER = "mp4"
VIDEO_CRF = 16
VIDEO_PRESET = "medium"

VIDEO_MANIFEST_SCHEMA_VERSION = 1
DEFAULT_TARGET_DURATION_SECONDS = 45.0
DEFAULT_FRAME_RATE = 30

SCHEDULE_ROLL_MINIMUM = 1
SCHEDULE_ROLL_MAXIMUM = 10_000

MEDIA_DIMENSION_TOLERANCE_PX = 0
MEDIA_FRAME_RATE_TOLERANCE = 1.0e-6
MEDIA_DURATION_TOLERANCE_SECONDS = 0.20


class PairVideoError(DiceModelError):
    """Raised when Project 1 production video generation fails."""


@dataclass(frozen=True, slots=True)
class FrameSchedule:
    """Deterministic mapping from video frame to real Bayesian roll."""

    frame_rate: int
    frame_count: int
    target_duration_seconds: float
    roll_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.frame_rate <= 0:
            raise PairVideoError("frame_rate must be positive")

        if self.frame_count <= 0:
            raise PairVideoError("frame_count must be positive")

        if not math.isfinite(self.target_duration_seconds) or self.target_duration_seconds <= 0.0:
            raise PairVideoError("target_duration_seconds must be finite and positive")

        if len(self.roll_indices) != self.frame_count:
            raise PairVideoError("roll_indices length must equal frame_count")

        if self.roll_indices[0] != SCHEDULE_ROLL_MINIMUM:
            raise PairVideoError("frame schedule must begin at roll 1")

        if self.roll_indices[-1] != SCHEDULE_ROLL_MAXIMUM:
            raise PairVideoError("frame schedule must end at roll 10,000")

        if not all(
            SCHEDULE_ROLL_MINIMUM <= roll <= SCHEDULE_ROLL_MAXIMUM for roll in self.roll_indices
        ):
            raise PairVideoError("frame schedule contains roll outside 1..10,000")

        if any(second < first for first, second in pairwise(self.roll_indices)):
            raise PairVideoError("frame schedule must be monotonically non-decreasing")

    @property
    def actual_duration_seconds(
        self,
    ) -> float:
        """Return duration implied by exact frame count and frame rate."""
        return self.frame_count / self.frame_rate

    @property
    def unique_roll_count(
        self,
    ) -> int:
        """Return number of distinct real Bayesian states displayed."""
        return len(set(self.roll_indices))

    def as_dict(
        self,
    ) -> dict[str, object]:
        """Return JSON-compatible frame-schedule metadata."""
        return {
            "frame_rate": self.frame_rate,
            "frame_count": self.frame_count,
            "target_duration_seconds": (self.target_duration_seconds),
            "actual_duration_seconds": (self.actual_duration_seconds),
            "first_roll": self.roll_indices[0],
            "last_roll": self.roll_indices[-1],
            "unique_roll_count": (self.unique_roll_count),
            "roll_indices": list(self.roll_indices),
        }


@dataclass(frozen=True, slots=True)
class VideoProbe:
    """Subset of ffprobe metadata required for deterministic validation."""

    width: int
    height: int
    codec_name: str
    pixel_format: str
    frame_rate: float
    duration_seconds: float
    frame_count: int | None

    def as_dict(
        self,
    ) -> dict[str, object]:
        """Return JSON-compatible media metadata."""
        return {
            "width": self.width,
            "height": self.height,
            "codec_name": self.codec_name,
            "pixel_format": self.pixel_format,
            "frame_rate": self.frame_rate,
            "duration_seconds": (self.duration_seconds),
            "frame_count": self.frame_count,
        }


@dataclass(frozen=True, slots=True)
class VideoValidationCheck:
    """One automated final-video acceptance check."""

    check_id: str
    passed: bool
    detail: str

    def as_dict(
        self,
    ) -> dict[str, object]:
        """Return JSON-compatible media check."""
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class VideoValidationReport:
    """Automated final-video validation."""

    checks: tuple[
        VideoValidationCheck,
        ...,
    ]

    @property
    def passed(self) -> bool:
        """Return True only when every media check passes."""
        return all(check.passed for check in self.checks)

    def as_dict(
        self,
    ) -> dict[str, object]:
        """Return JSON-compatible validation result."""
        return {
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
            "failed_check_ids": [check.check_id for check in self.checks if not check.passed],
        }


@dataclass(frozen=True, slots=True)
class PairVideoResult:
    """Final encoded media plus reproducibility metadata."""

    video_path: Path
    manifest_path: Path
    schedule: FrameSchedule
    probe: VideoProbe
    validation: VideoValidationReport


def require_media_tools() -> None:
    """Require FFmpeg and ffprobe binaries."""
    missing = [
        name
        for name in (
            "ffmpeg",
            "ffprobe",
        )
        if shutil.which(name) is None
    ]

    if missing:
        raise PairVideoError("missing required media tools: " + ", ".join(missing))


def sha256_file(
    path: Path | str,
) -> str:
    """Return SHA-256 digest for one file."""
    target = Path(path)

    digest = hashlib.sha256()

    with target.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _schedule_weights(
    stable_rolls: Sequence[int],
) -> np.ndarray:
    """Build deterministic emphasis weights over real rolls 1..10,000."""
    rolls = np.arange(
        SCHEDULE_ROLL_MINIMUM,
        SCHEDULE_ROLL_MAXIMUM + 1,
        dtype=float,
    )

    # Slow the visual story substantially at the beginning.
    weights = 0.55 + 18.0 / np.sqrt(rolls)

    # Give a small amount of additional emphasis to each real stable decision.
    for stable_roll in stable_rolls:
        sigma = max(
            18.0,
            min(
                160.0,
                stable_roll * 0.08,
            ),
        )

        distance = rolls - float(stable_roll)

        weights += 2.5 * np.exp(-0.5 * (distance / sigma) ** 2)

    # Preserve enough representation of the long tail to 10,000.
    weights += 0.15 * (rolls / SCHEDULE_ROLL_MAXIMUM)

    return weights


def build_frame_schedule(
    inference: PairInferenceResult,
    *,
    frame_rate: int,
    target_duration_seconds: float,
) -> FrameSchedule:
    """Map video frames to monotonically increasing real inference records."""
    if frame_rate <= 0:
        raise PairVideoError("frame_rate must be positive")

    if not math.isfinite(target_duration_seconds) or target_duration_seconds <= 0.0:
        raise PairVideoError("target_duration_seconds must be finite and positive")

    frame_count = round(frame_rate * target_duration_seconds)

    if frame_count < 2:
        raise PairVideoError("video requires at least two frames")

    stable_rolls = tuple(
        result.stable_decision_roll
        for case_id in PAIR_CASE_IDS
        for result in (inference.case(case_id),)
        if result.stable_decision_roll is not None
    )

    if len(stable_rolls) != len(PAIR_CASE_IDS):
        raise PairVideoError("all six cases require a stable decision before video rendering")

    weights = _schedule_weights(stable_rolls)

    cumulative = np.cumsum(weights)

    cumulative /= cumulative[-1]

    targets = np.linspace(
        0.0,
        1.0,
        frame_count,
        dtype=float,
    )

    indices = np.searchsorted(
        cumulative,
        targets,
        side="left",
    )

    indices = np.clip(
        indices,
        0,
        SCHEDULE_ROLL_MAXIMUM - 1,
    )

    rolls = tuple(int(index + 1) for index in indices.tolist())

    mutable = list(rolls)

    mutable[0] = 1

    mutable[-1] = 10_000

    # Guarantee every canonical stable decision appears at least once by
    # replacing the closest monotonic frame location.
    for stable_roll in sorted(stable_rolls):
        closest_index = min(
            range(
                1,
                frame_count - 1,
            ),
            key=lambda index: abs(mutable[index] - stable_roll),
        )

        mutable[closest_index] = stable_roll

    mutable.sort()

    mutable[0] = 1

    mutable[-1] = 10_000

    result = FrameSchedule(
        frame_rate=frame_rate,
        frame_count=frame_count,
        target_duration_seconds=(target_duration_seconds),
        roll_indices=tuple(mutable),
    )

    missing_stable = [stable for stable in stable_rolls if stable not in result.roll_indices]

    if missing_stable:
        raise PairVideoError(
            "frame schedule omitted stable decisions: "
            + ", ".join(str(value) for value in missing_stable)
        )

    return result


def build_ffmpeg_command(
    output_path: Path | str,
    *,
    frame_rate: int,
) -> tuple[str, ...]:
    """Build canonical raw-RGB-to-H.264 FFmpeg command."""
    path = Path(output_path)

    return (
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        (f"{FRAME_WIDTH_PX}x{FRAME_HEIGHT_PX}"),
        "-framerate",
        str(frame_rate),
        "-i",
        "-",
        "-an",
        "-c:v",
        VIDEO_CODEC,
        "-preset",
        VIDEO_PRESET,
        "-tune",
        "animation",
        "-crf",
        str(VIDEO_CRF),
        "-pix_fmt",
        VIDEO_PIXEL_FORMAT,
        "-movflags",
        "+faststart",
        "-map_metadata",
        "-1",
        "-metadata",
        "creation_time=1970-01-01T00:00:00Z",
        str(path),
    )


def _draw_agg_canvas(
    canvas: FigureCanvasAgg,
) -> None:
    """Draw an Agg canvas despite Matplotlib's untyped stub surface."""
    canvas.draw()  # type: ignore[no-untyped-call]


def _buffer_rgba(
    canvas: FigureCanvasAgg,
) -> Any:
    """Return Agg RGBA buffer despite Matplotlib's untyped stub surface."""
    return canvas.buffer_rgba()  # type: ignore[no-untyped-call]


def _figure_rgb_bytes(
    inference: PairInferenceResult,
    config: DiceProjectConfig,
    *,
    roll_index: int,
    validate_layout: bool,
) -> bytes:
    """Render one synchronized real-state frame as RGB24 bytes."""
    frame = build_pair_dashboard_frame(
        config.pair_experiment,
        inference,
        roll_index=roll_index,
    )

    canvas = frame.figure.canvas

    if not isinstance(
        canvas,
        FigureCanvasAgg,
    ):
        raise PairVideoError("pair dashboard requires FigureCanvasAgg")

    _draw_agg_canvas(canvas)

    if validate_layout:
        report = validate_pair_dashboard_frame(frame)

        if not report.passed:
            details = "; ".join(f"{issue.check_id}: {issue.detail}" for issue in report.issues)

            frame.figure.clear()

            raise PairVideoError(f"layout validation failed at roll {roll_index}: {details}")

    rgba_flat = np.frombuffer(
        _buffer_rgba(canvas),
        dtype=np.uint8,
    )

    expected_size = FRAME_HEIGHT_PX * FRAME_WIDTH_PX * 4

    if rgba_flat.size != expected_size:
        frame.figure.clear()

        raise PairVideoError(
            "rendered frame has unexpected RGBA element count "
            f"{rgba_flat.size}; expected {expected_size}"
        )

    rgba = rgba_flat.reshape(
        (
            FRAME_HEIGHT_PX,
            FRAME_WIDTH_PX,
            4,
        )
    )

    rgb = np.ascontiguousarray(
        rgba[
            :,
            :,
            :3,
        ]
    )

    result = rgb.tobytes()

    frame.figure.clear()

    return result


def render_pair_video(
    config: DiceProjectConfig,
    inference: PairInferenceResult,
    schedule: FrameSchedule,
    output_path: Path | str,
) -> Path:
    """Stream synchronized 1080x1080 RGB frames directly into FFmpeg."""
    require_media_tools()

    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(f"{path.stem}.tmp{path.suffix}")

    temporary_path.unlink(missing_ok=True)

    command = build_ffmpeg_command(
        temporary_path,
        frame_rate=(schedule.frame_rate),
    )

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    if process.stdin is None:
        raise PairVideoError("FFmpeg stdin pipe was not created")

    # Re-run the expensive layout validation only when the displayed roll
    # changes to a known structural checkpoint. Step 6 already validated the
    # canonical preview set exhaustively at artist level.
    validation_rolls = {
        1,
        10,
        100,
        1_000,
        10_000,
    }

    validation_rolls.update(
        result.stable_decision_roll
        for case_id in PAIR_CASE_IDS
        for result in (inference.case(case_id),)
        if result.stable_decision_roll is not None
    )

    try:
        for frame_number, roll_index in enumerate(
            schedule.roll_indices,
            start=1,
        ):
            frame_bytes = _figure_rgb_bytes(
                inference,
                config,
                roll_index=roll_index,
                validate_layout=(roll_index in validation_rolls),
            )

            process.stdin.write(frame_bytes)

            if frame_number == 1 or frame_number % 150 == 0 or frame_number == schedule.frame_count:
                print(f"FRAME {frame_number:>4}/{schedule.frame_count} ROLL {roll_index:>5}")

        process.stdin.close()

        return_code = process.wait()

        stderr_bytes = process.stderr.read() if process.stderr is not None else b""

        stderr_text = stderr_bytes.decode(
            "utf-8",
            errors="replace",
        )

        if return_code != 0:
            raise PairVideoError("FFmpeg encoding failed: " + stderr_text.strip())

    except BaseException:
        if process.stdin is not None:
            with suppress(BrokenPipeError):
                process.stdin.close()

        process.kill()
        process.wait()

        temporary_path.unlink(missing_ok=True)

        raise

    if not temporary_path.is_file():
        raise PairVideoError("FFmpeg completed without producing output")

    temporary_path.replace(path)

    return path


def _parse_fraction(
    value: str,
) -> float:
    """Parse FFprobe rational numeric value."""
    if "/" not in value:
        return float(value)

    numerator_text, denominator_text = value.split(
        "/",
        maxsplit=1,
    )

    numerator = float(numerator_text)

    denominator = float(denominator_text)

    if denominator == 0.0:
        raise PairVideoError(f"invalid FFprobe fraction {value!r}")

    return numerator / denominator


def probe_video(
    path: Path | str,
) -> VideoProbe:
    """Read canonical media properties using ffprobe."""
    require_media_tools()

    target = Path(path)

    command = (
        "ffprobe",
        "-v",
        "error",
        "-count_frames",
        "-select_streams",
        "v:0",
        "-show_entries",
        ("stream=width,height,codec_name,pix_fmt,avg_frame_rate,nb_read_frames:format=duration"),
        "-of",
        "json",
        str(target),
    )

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        raise PairVideoError("ffprobe failed: " + completed.stderr.strip())

    payload = json.loads(completed.stdout)

    streams = payload.get("streams")

    if (
        not isinstance(
            streams,
            list,
        )
        or len(streams) != 1
    ):
        raise PairVideoError("ffprobe did not return exactly one selected video stream")

    stream = streams[0]

    format_payload = payload.get("format")

    if not isinstance(
        stream,
        Mapping,
    ) or not isinstance(
        format_payload,
        Mapping,
    ):
        raise PairVideoError("ffprobe returned malformed JSON")

    frame_count_raw = stream.get("nb_read_frames")

    frame_count = (
        None
        if frame_count_raw
        in (
            None,
            "N/A",
        )
        else int(str(frame_count_raw))
    )

    return VideoProbe(
        width=int(stream["width"]),
        height=int(stream["height"]),
        codec_name=str(stream["codec_name"]),
        pixel_format=str(stream["pix_fmt"]),
        frame_rate=_parse_fraction(str(stream["avg_frame_rate"])),
        duration_seconds=float(format_payload["duration"]),
        frame_count=frame_count,
    )


def validate_video(
    probe: VideoProbe,
    schedule: FrameSchedule,
) -> VideoValidationReport:
    """Validate final media against the authoritative contract."""
    checks = (
        VideoValidationCheck(
            check_id="media.width",
            passed=(abs(probe.width - FRAME_WIDTH_PX) <= MEDIA_DIMENSION_TOLERANCE_PX),
            detail=(f"expected width {FRAME_WIDTH_PX}; found {probe.width}"),
        ),
        VideoValidationCheck(
            check_id="media.height",
            passed=(abs(probe.height - FRAME_HEIGHT_PX) <= MEDIA_DIMENSION_TOLERANCE_PX),
            detail=(f"expected height {FRAME_HEIGHT_PX}; found {probe.height}"),
        ),
        VideoValidationCheck(
            check_id="media.codec",
            passed=(probe.codec_name == "h264"),
            detail=(f"expected codec h264; found {probe.codec_name}"),
        ),
        VideoValidationCheck(
            check_id="media.pixel_format",
            passed=(probe.pixel_format == VIDEO_PIXEL_FORMAT),
            detail=(f"expected pixel format {VIDEO_PIXEL_FORMAT}; found {probe.pixel_format}"),
        ),
        VideoValidationCheck(
            check_id="media.frame_rate",
            passed=(abs(probe.frame_rate - schedule.frame_rate) <= MEDIA_FRAME_RATE_TOLERANCE),
            detail=(f"expected frame rate {schedule.frame_rate}; found {probe.frame_rate}"),
        ),
        VideoValidationCheck(
            check_id="media.duration",
            passed=(
                abs(probe.duration_seconds - schedule.actual_duration_seconds)
                <= MEDIA_DURATION_TOLERANCE_SECONDS
            ),
            detail=(
                f"expected duration approximately "
                f"{schedule.actual_duration_seconds:.3f}; "
                f"found {probe.duration_seconds:.3f}"
            ),
        ),
        VideoValidationCheck(
            check_id="media.frame_count",
            passed=(probe.frame_count is None or probe.frame_count == schedule.frame_count),
            detail=(f"expected frame count {schedule.frame_count}; found {probe.frame_count}"),
        ),
    )

    return VideoValidationReport(checks=checks)


def _json_payload(
    path: Path,
) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(
    payload: Mapping[str, object],
    path: Path,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(f"{path.suffix}.tmp")

    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary_path.replace(path)

    return path


def build_video_manifest(
    config: DiceProjectConfig,
    inference: PairInferenceResult,
    *,
    schedule: FrameSchedule,
    video_path: Path,
    probe: VideoProbe,
    media_validation: VideoValidationReport,
    data_paths: Mapping[str, Path],
) -> dict[str, object]:
    """Build final Project 1 video manifest."""
    cases: dict[
        str,
        object,
    ] = {}

    for case_id in PAIR_CASE_IDS:
        result = inference.case(case_id)

        cases[case_id] = {
            "final_decision_state": (result.final_decision_state.value),
            "final_posterior_loaded": (result.final_posterior_loaded),
            "final_top_model": (result.final_top_model),
            "first_fair_threshold_crossing": (result.first_fair_threshold_crossing),
            "first_loaded_threshold_crossing": (result.first_loaded_threshold_crossing),
            "stable_decision_roll": (result.stable_decision_roll),
        }

    input_hashes = {key: sha256_file(path) for key, path in data_paths.items()}

    return {
        "schema_version": (VIDEO_MANIFEST_SCHEMA_VERSION),
        "project_id": config.project_id,
        "viewer_question": (config.pair_experiment.viewer_question),
        "observation_type": (config.pair_experiment.observation.observation_type),
        "loaded_probability_definition": (config.pair_experiment.loaded_probability_definition),
        "headline_roll_metric": (config.pair_experiment.decision.headline_roll_metric),
        "frame_schedule": (schedule.as_dict()),
        "video": {
            "path": str(video_path),
            "sha256": sha256_file(video_path),
            "probe": probe.as_dict(),
            "validation": (media_validation.as_dict()),
            "encoder": {
                "codec": VIDEO_CODEC,
                "pixel_format": (VIDEO_PIXEL_FORMAT),
                "crf": VIDEO_CRF,
                "preset": VIDEO_PRESET,
            },
        },
        "canonical_input_sha256": (input_hashes),
        "cases": cases,
    }


def run_pair_video_pipeline(
    configuration_path: Path | str = DEFAULT_CONFIG_PATH,
) -> PairVideoResult:
    """Execute the complete validated production video pipeline."""
    require_media_tools()

    context = build_pipeline_context(configuration_path)

    config = context.configuration

    simulation = simulate_all_pair_cases(config)

    inference = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    statistical_validation = build_pair_validation_report(
        config,
        simulation,
        inference,
    )

    if not statistical_validation.passed:
        failed = [check.check_id for check in statistical_validation.checks if not check.passed]

        raise PairVideoError("statistical validation failed: " + ", ".join(failed))

    frame_rate = config.pair_experiment.video.frame_rate

    target_duration = config.pair_experiment.video.target_duration_seconds

    schedule = build_frame_schedule(
        inference,
        frame_rate=frame_rate,
        target_duration_seconds=(target_duration),
    )

    outputs = context.pair_output_files()

    video_path = render_pair_video(
        config,
        inference,
        schedule,
        outputs["video"],
    )

    probe = probe_video(video_path)

    media_validation = validate_video(
        probe,
        schedule,
    )

    if not media_validation.passed:
        failed = [check.check_id for check in media_validation.checks if not check.passed]

        raise PairVideoError("final video validation failed: " + ", ".join(failed))

    data_paths = {
        "pair_simulation": (outputs["simulation"]),
        "pair_case_histories": (outputs["history"]),
        "pair_case_summary": (outputs["summary"]),
        "pair_validation": (outputs["validation"]),
    }

    missing_inputs = [name for name, path in data_paths.items() if not path.is_file()]

    if missing_inputs:
        raise PairVideoError("canonical Step 5 artifacts missing: " + ", ".join(missing_inputs))

    manifest_payload = build_video_manifest(
        config,
        inference,
        schedule=schedule,
        video_path=video_path,
        probe=probe,
        media_validation=media_validation,
        data_paths=data_paths,
    )

    manifest_path = _write_json(
        manifest_payload,
        outputs["manifest"],
    )

    return PairVideoResult(
        video_path=video_path,
        manifest_path=manifest_path,
        schedule=schedule,
        probe=probe,
        validation=media_validation,
    )


def _schedule_command(
    configuration_path: Path,
) -> int:
    config = load_dice_config(configuration_path)

    simulation = simulate_all_pair_cases(config)

    inference = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    schedule = build_frame_schedule(
        inference,
        frame_rate=(config.pair_experiment.video.frame_rate),
        target_duration_seconds=(config.pair_experiment.video.target_duration_seconds),
    )

    print(
        json.dumps(
            schedule.as_dict(),
            indent=2,
            sort_keys=True,
        )
    )

    return 0


def _render_command(
    configuration_path: Path,
) -> int:
    result = run_pair_video_pipeline(configuration_path)

    print()
    print("=" * 80)
    print("PROJECT 1 — FINAL PAIR-DICE VIDEO")
    print("=" * 80)

    print(f"Video:    {result.video_path}")

    print(f"Manifest: {result.manifest_path}")

    print(f"Frames:   {result.schedule.frame_count}")

    print(f"FPS:      {result.schedule.frame_rate}")

    print(f"Duration: {result.probe.duration_seconds:.3f}s")

    print(f"Codec:    {result.probe.codec_name}")

    print(f"Pix fmt:  {result.probe.pixel_format}")

    print(f"Media validation: {'PASS' if result.validation.passed else 'FAIL'}")

    return 0 if result.validation.passed else 1


def _validate_command(
    configuration_path: Path,
) -> int:
    context = build_pipeline_context(configuration_path)

    config = context.configuration

    simulation = simulate_all_pair_cases(config)

    inference = infer_all_pair_cases(
        config.pair_experiment,
        simulation,
    )

    schedule = build_frame_schedule(
        inference,
        frame_rate=(config.pair_experiment.video.frame_rate),
        target_duration_seconds=(config.pair_experiment.video.target_duration_seconds),
    )

    video_path = context.pair_output_files()["video"]

    if not video_path.is_file():
        raise PairVideoError(f"final video missing: {video_path}")

    probe = probe_video(video_path)

    report = validate_video(
        probe,
        schedule,
    )

    print(
        json.dumps(
            {
                "probe": probe.as_dict(),
                "validation": report.as_dict(),
            },
            indent=2,
            sort_keys=True,
        )
    )

    return 0 if report.passed else 1


def build_argument_parser() -> argparse.ArgumentParser:
    """Build standalone Project 1 video CLI."""
    parser = argparse.ArgumentParser(
        prog=("python -m linkedin_visual_labs.projects.p01_bayesian_dice.pair_video"),
        description=("Render and validate the Bayesian pair-dice video."),
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=("Path to the Project 1 YAML configuration."),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "schedule",
        help=("Print the deterministic nonlinear frame schedule."),
    )

    subparsers.add_parser(
        "render",
        help=("Render MP4, validate it, and write the manifest."),
    )

    subparsers.add_parser(
        "validate",
        help=("Validate an already-rendered canonical MP4."),
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Standalone command-line entry point."""
    parser = build_argument_parser()

    args = parser.parse_args(argv)

    configuration_path = Path(args.config)

    try:
        if args.command == "schedule":
            return _schedule_command(configuration_path)

        if args.command == "render":
            return _render_command(configuration_path)

        if args.command == "validate":
            return _validate_command(configuration_path)

    except (
        OSError,
        PairVideoError,
        subprocess.SubprocessError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        parser.error(str(exc))

    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
