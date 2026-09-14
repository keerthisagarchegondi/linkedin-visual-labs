"""Bounded RGB streaming to package-owned CPU FFmpeg; no source video decoding."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from .block2 import write_json
from .design_system import HERO_BOX, OVERLAY_BOXES, VIDEO_REFERENCES
from .evidence import artifact
from .presentation import KEYFRAMES, Presentation, captions
from .runtime import resolve_packaged_ffmpeg
from .visualization import contact_sheet, frame, static_image


def validate_video_metadata(metadata: dict[str, Any]) -> None:
    expected = {
        "width": 1080,
        "height": 1350,
        "fps": 30.0,
        "codec": "h264",
        "pixel_format": "yuv420p",
        "frames": 1350,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Video technical contract failed")
    if not 44 <= metadata["duration"] <= 46.5:
        raise ValueError("Video duration failed")


def probe(executable: str, path: Path, log: Path) -> dict[str, Any]:
    command = [
        executable,
        "-v",
        "info",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-f",
        "null",
        "-",
        "-progress",
        "pipe:1",
        "-nostats",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    log.write_text(result.stderr + "\n" + result.stdout, encoding="utf-8")
    stream = next(line for line in result.stderr.splitlines() if "Video:" in line)
    dimensions = re.search(r"\b(\d{3,4})x(\d{3,4})\b", stream)
    fps = re.search(r"([\d.]+) fps", stream)
    frames = re.findall(r"^frame=(\d+)$", result.stdout, re.MULTILINE)
    duration = re.search(r"Duration: (\d+):(\d+):([\d.]+)", result.stderr)
    if dimensions is None or fps is None or not frames or duration is None:
        raise ValueError("Incomplete packaged FFmpeg probe")
    value = {
        "width": int(dimensions[1]),
        "height": int(dimensions[2]),
        "fps": float(fps[1]),
        "codec": "h264" if "Video: h264" in stream else "unknown",
        "pixel_format": "yuv420p" if "yuv420p" in stream else "unknown",
        "frames": int(frames[-1]),
        "duration": int(duration[1]) * 3600 + int(duration[2]) * 60 + float(duration[3]),
        "full_decode": "PASS",
    }
    validate_video_metadata(value)
    return value


def render_static(p: Presentation) -> dict[str, Any]:
    images = p.output / "images"
    images.mkdir(parents=True, exist_ok=True)
    im = static_image(p)
    path = images / "trajectory_map.png"
    im.save(path)
    im.resize((432, 540)).save(images / "trajectory_map_thumbnail.png")
    manifest = {
        "schema_version": "1.0",
        "title": "Ten minutes of traffic in one frame",
        "dimensions": list(im.size),
        "source_interval": [1200, 1800],
        "source_pixels": False,
        "physical_calibration": False,
        "gap_policy": "Never connect observations separated by more than one second",
        "journey_styling": "Retrospective full-episode completion; not online identity",
        "counts_scope": "Full episode 0-1800s, not static interval",
        "inputs": p.index,
        "outputs": [
            artifact(p.root, path),
            artifact(p.root, images / "trajectory_map_thumbnail.png"),
        ],
    }
    write_json(p.output / "manifests/trajectory_map_manifest.json", manifest)
    return manifest


def render_video(p: Presentation) -> dict[str, Any]:
    tool = resolve_packaged_ffmpeg()
    if tool.executable is None:
        raise ValueError("Package-owned FFmpeg unavailable")
    videos = p.output / "videos"
    images = p.output / "images"
    keydir = images / "video_keyframes"
    logs = p.root / ".cache/p05_traffic_operations_early_warning/block4a-p6"
    for folder in (videos, keydir, logs):
        folder.mkdir(parents=True, exist_ok=True)
    master = videos / "project6_linkedin_master.mp4"
    partial = videos / "project6_linkedin_master.partial.mp4"
    command = [
        tool.executable,
        "-y",
        "-v",
        "warning",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        "1080x1350",
        "-r",
        "30",
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-threads",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-map_metadata",
        "-1",
        str(partial),
    ]
    keys: list[Path] = []
    with (logs / "encode.log").open("wb") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log, stdout=log)
        if process.stdin is None:
            raise ValueError("No encoder pipe")
        try:
            for number in range(1350):
                im = frame(p, number)
                process.stdin.write(im.tobytes())
                if number in KEYFRAMES:
                    key = keydir / f"{len(keys) + 1:02d}_video_{round(number / 30):02d}s.png"
                    im.save(key)
                    keys.append(key)
                if number % 150 == 0:
                    print(f"Encoded {number}/1350 frames", flush=True)
        finally:
            process.stdin.close()
            returncode = process.wait(timeout=120)
        if returncode:
            raise ValueError("Encoder failed; partial artifact retained for diagnosis")
    master_meta = probe(tool.executable, partial, logs / "master_decode.log")
    partial.replace(master)
    web = videos / "project6_linkedin_web.mp4"
    web_partial = videos / "project6_linkedin_web.partial.mp4"
    transcode = [
        tool.executable,
        "-y",
        "-v",
        "error",
        "-i",
        str(master),
        "-an",
        "-c:v",
        "libx264",
        "-crf",
        "24",
        "-preset",
        "fast",
        "-threads",
        "2",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-map_metadata",
        "-1",
        str(web_partial),
    ]
    subprocess.run(transcode, check=True, capture_output=True)
    web_meta = probe(tool.executable, web_partial, logs / "web_decode.log")
    web_partial.replace(web)
    frame(p, 300).save(images / "project6_thumbnail.png")
    contact_sheet(keys, images / "video_keyframe_contact_sheet.png", 5)
    # Extract actual decoded keyframes to verify the encoded scene boundaries, too.
    for index, number in enumerate(KEYFRAMES):
        decoded = keydir / f"decoded_{index + 1:02d}.png"
        subprocess.run(
            [
                tool.executable,
                "-y",
                "-v",
                "error",
                "-i",
                str(web),
                "-vf",
                f"select=eq(n\\,{number})",
                "-frames:v",
                "1",
                str(decoded),
            ],
            check=True,
            capture_output=True,
        )
    manifest = {
        "schema_version": "1.0",
        "master": master_meta,
        "web": web_meta,
        "source_pixels": False,
        "analytical_clock": "ORIGINAL_SOURCE_SECONDS",
        "presentation_clock": "45 seconds; geometry replay 1200-1800; no analytical rescaling",
        "ffmpeg": tool.model_dump(mode="json"),
        "encoder_command": command,
        "transcode_command": transcode,
        "inputs": p.index,
        "scenes": [
            {
                "start": i * 5 if i < 9 else 44,
                "end": (i + 1) * 5 if i < 8 else (44 if i == 8 else 45),
                "eyebrow": v[0],
                "title": v[1],
                "caption": v[2],
                "reference": VIDEO_REFERENCES[i],
                "hero_box": HERO_BOX,
                "overlay_box": OVERLAY_BOXES[i],
            }
            for i, v in enumerate(captions(p))
        ],
        "keyframes": [
            {"frame": n, "time": n / 30, **artifact(p.root, path)}
            for n, path in zip(KEYFRAMES, keys, strict=True)
        ],
        "outputs": [artifact(p.root, master), artifact(p.root, web)],
        "final_release_approved": False,
    }
    write_json(p.output / "manifests/video_manifest.json", manifest)
    return manifest
