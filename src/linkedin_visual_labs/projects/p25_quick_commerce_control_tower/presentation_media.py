"Packaged FFmpeg streaming and full-decode validation for Project 5."

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import imageio_ffmpeg  # type: ignore[import-untyped]
import numpy as np
from PIL import Image

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
    HEIGHT,
    WIDTH,
    motion_frame,
    scene_canvas,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    Evidence,
    sha256,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    VIDEO_TITLES,
    Scene,
)

FPS = 30


def packaged_ffmpeg() -> tuple[Path, str]:
    "Resolve the installed imageio-ffmpeg binary directly; ignore PATH/env overrides."
    binaries = Path(imageio_ffmpeg.__file__).resolve().parent / "binaries"
    candidates = sorted(
        p for p in binaries.glob("ffmpeg-*") if p.is_file() and p.suffix in ("", ".exe")
    )
    if len(candidates) != 1:
        raise ValueError(f"Expected one packaged FFmpeg executable in {binaries}")
    executable = candidates[0]
    result = subprocess.run(
        [str(executable), "-version"], check=True, capture_output=True, text=True
    )
    return executable, result.stdout.splitlines()[0]


def encode_video(e: Evidence, scenes: tuple[Scene, ...], name: str, path: Path) -> None:
    executable, _ = packaged_ffmpeg()
    path.parent.mkdir(parents=True, exist_ok=True)
    log = path.with_suffix(".encode.log")
    command = [
        str(executable),
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "pipe:0",
        "-an",
        "-metadata",
        f"title={VIDEO_TITLES[name]}",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "19",
        "-threads",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(path),
    ]
    with (
        log.open("wb") as errors,
        subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=errors
        ) as process,
    ):
        assert process.stdin is not None
        try:
            for i, scene in enumerate(scenes):
                canvas = scene_canvas(e, scene, i, name)
                for frame in range(scene.seconds * FPS):
                    image = motion_frame(canvas, e, scene, frame / (scene.seconds * FPS))
                    # Deterministic progress indicator outside all text regions.
                    from PIL import ImageDraw

                    draw = ImageDraw.Draw(image)
                    draw.rectangle(
                        (
                            40,
                            1320,
                            40
                            + int(
                                1000
                                * (sum(s.seconds for s in scenes[:i]) + frame / FPS)
                                / sum(s.seconds for s in scenes)
                            ),
                            1326,
                        ),
                        fill="#008b8d",
                    )
                    process.stdin.write(image.tobytes())
        finally:
            process.stdin.close()
        if process.wait() != 0:
            raise ValueError("FFmpeg encode failed: " + log.read_text(encoding="utf-8"))


def validate_video(path: Path, *, expected_frames: int = 900) -> dict[str, Any]:
    "Parse input metadata and decode every frame with the same explicit executable."
    executable, version = packaged_ffmpeg()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("Missing or empty video")
    result = subprocess.run(
        [
            str(executable),
            "-v",
            "info",
            "-xerror",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-progress",
            "pipe:1",
            "-nostats",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    header = result.stderr.split("Stream mapping:")[0]
    match = re.search(
        ("Video: (\\w+).*?\\b(yuv\\d+p)\\b.*?\\b(\\d{3,5})x(\\d{3,5})\\b.*?([\\d.]+) fps"), header
    )
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", header)
    frames = re.findall(r"^frame=(\d+)", result.stdout, re.MULTILINE)
    if match is None or duration is None or not frames:
        raise ValueError("Missing encoded video metadata")
    codec, pixel, width, height, fps = match.groups()
    seconds = int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3])
    if (
        (codec, pixel, int(width), int(height), float(fps))
        != ("h264", "yuv420p", WIDTH, HEIGHT, float(FPS))
        or int(frames[-1]) != expected_frames
        or abs(seconds - expected_frames / FPS) > 0.05
    ):
        raise ValueError("Video metadata/frame-count mismatch")
    return dict(
        width=int(width),
        height=int(height),
        fps=float(fps),
        codec=codec,
        pixel_format=pixel,
        duration_seconds=seconds,
        frame_count=int(frames[-1]),
        full_decode=True,
        ffmpeg_executable=str(executable),
        ffmpeg_version=version,
        ffmpeg_sha256=sha256(executable),
    )


def validate_scene_pixels(
    e: Evidence, scenes: tuple[Scene, ...], name: str, path: Path
) -> list[float]:
    "Compare actual decoded midpoint canvases; catches absent/wrong scene content."
    executable, _ = packaged_ffmpeg()
    errors: list[float] = []
    elapsed = 0
    for i, scene in enumerate(scenes):
        result = subprocess.run(
            [
                str(executable),
                "-v",
                "error",
                "-ss",
                str(elapsed + scene.seconds / 2),
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "pipe:1",
            ],
            capture_output=True,
            check=True,
        )
        decoded = Image.frombytes("RGB", (WIDTH, HEIGHT), result.stdout)
        expected = motion_frame(scene_canvas(e, scene, i, name), e, scene, 0.5)
        # Exclude only the animated progress strip; include all text/captions.
        a = np.asarray(decoded)[:1310].astype(float)
        b = np.asarray(expected)[:1310].astype(float)
        error = float(np.abs(a - b).mean())
        if error > 3.0:
            raise ValueError(f"Decoded scene content differs: {name}/{i}: {error}")
        errors.append(error)
        elapsed += scene.seconds
    return errors
