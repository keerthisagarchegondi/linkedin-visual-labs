"""Accelerated real-source montage with causal, evolving observation overlays."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from itertools import pairwise
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter

from . import render_v2 as base
from .block2 import write_json
from .detection import checksum
from .presentation import KEYFRAMES
from .presentation_v2 import SCENES, STATUS, TOKENS, extract_tokens, scene_index, validate_first15
from .presentation_v3 import BUILD, COLORS, history_at, playback_contract, source_time, trail_alpha
from .video import probe

ENTRY_EXIT_LINE_WIDTH = 3
ENTRY_EXIT_GLOW_WIDTH = 8
ENTRY_EXIT_GLOW_ALPHA = 58
ENTRY_EXIT_ARROW_WIDTH = 4
ENTRY_EXIT_ARROW_SIZE = 14
ENTRY_EXIT_LABEL_SIZE = 22
ENTRY_EXIT_LABEL_OUTLINE = (10, 12, 20, 220)
ENTRY_EXIT_LABEL_OFFSET = (0, -30)
ENTRY_EXIT_CROSSING_HALO_WIDTH = 6
ENTRY_EXIT_CROSSING_PULSE_BASE = 7
ENTRY_EXIT_CROSSING_PULSE_RATE = 5.0
ENTRY_EXIT_CROSSING_PULSE_MAX_WIDTH = 5
ENTRY_EXIT_CROSSING_LABEL_SIZE = 22
ENTRY_EXIT_CROSSING_LABEL_OFFSET = 8


@contextmanager
def palette() -> Iterator[None]:
    """Reuse layout primitives with scoped colors; preserve historical API defaults."""
    previous = dict(TOKENS)
    TOKENS.update(COLORS)
    try:
        yield
    finally:
        TOKENS.clear()
        TOKENS.update(previous)


def _draw_glow_line(
    draw: ImageDraw.ImageDraw,
    layer: Image.Image,
    start: tuple[int, int],
    end: tuple[int, int],
    token: str,
) -> None:
    glow = Image.new("RGBA", layer.size)
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.line(
        (start, end), fill=base.rgb(token, ENTRY_EXIT_GLOW_ALPHA), width=ENTRY_EXIT_GLOW_WIDTH
    )
    glow = glow.filter(ImageFilter.GaussianBlur(1.8))
    layer.alpha_composite(glow)
    draw.line((start, end), fill=base.rgb(token, 230), width=ENTRY_EXIT_LINE_WIDTH)


def _draw_direction_arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    token: str,
) -> None:
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    wings = [
        (
            round(end[0] - ENTRY_EXIT_ARROW_SIZE * math.cos(angle + v)),
            round(end[1] - ENTRY_EXIT_ARROW_SIZE * math.sin(angle + v)),
        )
        for v in (-0.5, 0.5)
    ]
    draw.line((start, end), fill=base.rgb(token, 240), width=ENTRY_EXIT_ARROW_WIDTH)
    draw.line((wings[0], end, wings[1]), fill=base.rgb(token, 240), width=ENTRY_EXIT_ARROW_WIDTH)


class DynamicRenderer(base.Renderer):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.cache = root / ".cache/p05_traffic_operations_early_warning/block4cc"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.display_time = 0.0
        self.samples: list[dict[str, Any]] = []
        self.latest: dict[str, Any] = {}

    def manifest(self) -> dict[str, Any]:
        return {
            "build": BUILD,
            "PUBLICATION_STATUS": STATUS,
            "source_pixels": True,
            "final_artifact_release_approved": False,
            **playback_contract(),
            "tokens_sha256": checksum(self.preview / "project6_visual_tokens_v3.json"),
            "contract_sha256": checksum(self.preview / "project6_presentation_contract_v3.json"),
            "presentation_metrics_sha256": checksum(self.output / "data/presentation_metrics.json"),
        }

    def prepare(self) -> None:
        sampled = extract_tokens(
            list((self.root / "reference/project6/previews/linkedin_video_frames").glob("*.png"))
        )
        write_json(
            self.preview / "project6_visual_tokens_v3.json",
            {
                "build": BUILD,
                "tokens": COLORS,
                "sampled_originals": sampled["originals"],
                "direct_samples": {
                    "violet": "#835CF6 (4630 exact original pixels)",
                    "emerald": "#2BA668",
                    "warning": "#E04F4F",
                    "watch": "#F2A93B",
                },
                "adaptations": "Deep indigo #30205F, muted violet #62439A, magenta #EC4899, "
                "gold #F4CC63 and near-white #F4F7FA provide distinct semantic roles. "
                "They are curated extensions, not falsely claimed exact original samples.",
                "deprecated": "DEPRECATED_VISUAL_STYLE: light-blue contours/boxes plus permanent "
                "orange vehicle dots; original source PNGs themselves remain untouched.",
                "density_gradient": [
                    COLORS[k] for k in ("density_low", "density_mid", "density_high")
                ],
                "PUBLICATION_STATUS": STATUS,
            },
        )
        write_json(
            self.preview / "project6_presentation_contract_v3.json",
            {
                **playback_contract(),
                "canonical_kpis": self.kpis,
                "story": SCENES,
                "causality": "All field/trail observations are at or before displayed source time.",
                "static_map": "Only deliberate static summary uses full [1200,1800) history.",
                "claim_limit": "No queue absence or measured false-escalation reduction claim.",
            },
        )
        old = self.preview / "project6_visual_tokens_v2.json"
        value = json.loads(old.read_text(encoding="utf-8"))
        value["current_style_status"] = "DEPRECATED_VISUAL_STYLE"
        value["superseded_by"] = "project6_visual_tokens_v3.json"
        write_json(old, value)

    def scene_pixels(
        self, raw: Image.Image, t: float, index: int, *, include_trails: bool = True
    ) -> Image.Image:
        # Static summary calls this with its explicit final source timestamp.
        history = history_at(self.tracks, t, 45)
        if index == 10:
            history = self.tracks[
                (self.tracks.source_timestamp >= 1200) & (self.tracks.source_timestamp < 1800)
            ]
        layer, evidence = base.density_layer(history)
        field_hash = hashlib.sha256(layer.tobytes()).hexdigest()
        trail = Image.new("RGBA", (1080, 1080))
        draw = ImageDraw.Draw(trail)
        paths = history_at(self.tracks, t, 60) if include_trails else self.tracks.iloc[:0]
        segments = 0
        for _, group in paths.groupby("track_id"):
            for a, b in pairwise(base.observations(group)):
                if 0 < b.source_timestamp - a.source_timestamp <= 1:
                    age = t - b.source_timestamp
                    draw.line(
                        (
                            base.point(a.reference_x, a.reference_y),
                            base.point(b.reference_x, b.reference_y),
                        ),
                        fill=base.rgb(
                            "trajectory_primary" if age < 15 else "trajectory_secondary",
                            trail_alpha(age),
                        ),
                        width=3 if age < 15 else 2,
                    )
                    segments += 1
        trail_hash = hashlib.sha256(trail.tobytes()).hexdigest()
        layer.alpha_composite(trail)
        draw = ImageDraw.Draw(layer)
        for name in ("roi", "queue_zone"):
            pts = [base.point(p["x"] * 1280, p["y"] * 720) for p in self.geometry[name]["points"]]
            draw.line([*pts, pts[0]], fill=base.rgb("zone_outline", 165), width=2)
        for name, token in (("entry", "entry_color"), ("exit", "exit_color")):
            line = self.geometry[name]
            a = base.point(line["start"]["x"] * 1280, line["start"]["y"] * 720)
            b = base.point(line["end"]["x"] * 1280, line["end"]["y"] * 720)
            _draw_glow_line(draw, layer, a, b, token)
            _draw_direction_arrow(draw, a, b, token)
            draw.text(
                (
                    max(15, min(a[0], 950)) + ENTRY_EXIT_LABEL_OFFSET[0],
                    a[1] + ENTRY_EXIT_LABEL_OFFSET[1],
                ),
                name.upper(),
                font=base.font(ENTRY_EXIT_LABEL_SIZE, True),
                fill=base.rgb(token),
                stroke_width=2,
                stroke_fill=ENTRY_EXIT_LABEL_OUTLINE,
            )
        active = (
            history_at(self.tracks, t, 0.4)
            .sort_values("source_timestamp")
            .groupby("track_id")
            .tail(1)
        )
        for row in base.observations(active):
            a, b = base.point(row.x1, row.y1), base.point(row.x2, row.y2)
            draw.rectangle((*a, *b), outline=base.rgb("box_default", 235), width=1)
            # Small neutral corner marker, no permanently illuminated vehicle node.
            draw.line(
                ((a[0], a[1] + 7), a, (a[0] + 7, a[1])), fill=base.rgb("box_default"), width=2
            )
        events = self.crossings[
            (self.crossings.source_timestamp <= t) & (self.crossings.source_timestamp > t - 3)
        ]
        pulse_ids = []
        for event in base.observations(events):
            observation = self.tracks[self.tracks.detection_id == event.detection_id]
            if observation.empty:
                continue
            row = base.observations(observation)[0]
            x, y = base.point(row.reference_x, row.reference_y)
            age = t - event.source_timestamp
            radius = round(ENTRY_EXIT_CROSSING_PULSE_BASE + age * ENTRY_EXIT_CROSSING_PULSE_RATE)
            token = "entry_color" if event.event_type == "ENTRY" else "exit_color"
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                outline=base.rgb(token, round(240 * (1 - age / 3))),
                width=ENTRY_EXIT_CROSSING_PULSE_MAX_WIDTH,
            )
            halo = Image.new("RGBA", layer.size)
            halo_draw = ImageDraw.Draw(halo)
            halo_draw.ellipse(
                (
                    x - radius - ENTRY_EXIT_CROSSING_HALO_WIDTH,
                    y - radius - ENTRY_EXIT_CROSSING_HALO_WIDTH,
                    x + radius + ENTRY_EXIT_CROSSING_HALO_WIDTH,
                    y + radius + ENTRY_EXIT_CROSSING_HALO_WIDTH,
                ),
                outline=base.rgb(token, 110),
                width=ENTRY_EXIT_CROSSING_PULSE_MAX_WIDTH * 3,
            )
            layer.alpha_composite(halo.filter(ImageFilter.GaussianBlur(2.0)))
            draw.text(
                (x + 10, y - ENTRY_EXIT_CROSSING_LABEL_OFFSET - 18),
                "+1",
                font=base.font(ENTRY_EXIT_CROSSING_LABEL_SIZE, True),
                fill=base.rgb(token),
                stroke_width=2,
                stroke_fill=ENTRY_EXIT_LABEL_OUTLINE,
            )
            pulse_ids.append(event.event_id)
        source = (
            raw.convert("RGB")
            .crop((560, 0, 1280, 720))
            .resize((1080, 1080), Image.Resampling.LANCZOS)
        )
        self.latest = {
            "source_timestamp": t,
            "scene": index,
            "field_hash": field_hash,
            "trail_hash": trail_hash,
            "active_ids": [int(i) for i in active.track_id],
            "trailing_ids": [int(i) for i in paths.track_id.unique()],
            "maximum_observation_time": None
            if history.empty
            else float(history.source_timestamp.max()),
            "history_start_exclusive": t - 45,
            "trail_segments": segments,
            "pulses": pulse_ids,
            "density": evidence,
            "source_hash": hashlib.sha256(raw.tobytes()).hexdigest(),
        }
        return Image.alpha_composite(source.convert("RGBA"), layer).convert("RGB")

    def frame(
        self, raw: Image.Image, seconds: float, *, source_timestamp: float | None = None
    ) -> Image.Image:
        self.display_time = seconds
        t = source_time(seconds) if source_timestamp is None else source_timestamp
        image = super().frame(raw, seconds, source_timestamp=t)
        # A smaller tag distinguishes accelerated montage time from fixed KPI time.
        base.text(image, (30, 204), "ACCELERATED SOURCE TIME / ANALYTICS KEEP ORIGINAL TIME", 17)
        index = scene_index(seconds)
        if index == 0:
            base.panel(image, (20, 1090, 1060, 1185))
            base.text(image, (38, 1116), "CAMERA → FLOW → WARNING → VALIDATE", 30, bold=True)
        if index == 4:
            # Hero has almost no opaque UI. Restore source pixels under the inherited KPI strip.
            clean = self.scene_pixels(raw, t, index)
            image.paste(clean.crop((0, 880, 1080, 1080)), (0, 1010))
        if index in (2, 6):
            state = "NORMAL" if t < 1383 else ("WATCH" if t < 1440 else "WARNING")
            base.panel(image, (20, 230, 1060, 292))
            base.text(
                image,
                (38, 248),
                f"SOURCE STATE: {state}  /  NORMAL → WATCH → WARNING",
                23,
                "warning_active" if state == "WARNING" else "warning_watch",
                True,
            )
        return image

    def kpi_strip(self, im: Image.Image) -> None:
        base.panel(im, (20, 1035, 1060, 1190))
        base.text(
            im, (35, 1044), "FIXED 24:00 SNAPSHOT / NUMERIC WINDOW (23:00,24:00]", 20, bold=True
        )
        count = min(5, 1 + int(max(0, self.display_time - 4) / 0.75))
        for i, (label, value, detail) in enumerate(self.kpis[:count]):
            x = 32 + i * 207
            base.text(im, (x, 1086), label, 14, "text_secondary", True, 198)
            base.text(
                im, (x, 1114), value, 25, "warning_active" if i == 0 else "text_primary", True, 198
            )
            base.text(im, (x, 1152), detail, 13, width=198)

    def charts(self, im: Image.Image) -> None:
        super().charts(im)
        t = source_time(self.display_time)
        draw = ImageDraw.Draw(im)
        for i in range(4):
            x = round(40 + i * 253 + (t - 1380) / 270 * 225)
            draw.line(((x, 990), (x, 1148)), fill=base.rgb("warning_active"), width=2)

    def encode(self, *, proof: bool) -> None:
        duration = 25 if proof else 45
        name = "project6_motion_proof_00_25s.mp4" if proof else "project6_linkedin_master.mp4"
        target = self.output / "videos" / name
        partial = target.with_suffix(".partial.mp4")
        command = [
            self.ffmpeg,
            "-y",
            "-v",
            "error",
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
            "20" if proof else "18",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(partial),
        ]
        self.commands.append(command)
        transcripts: dict[int, list[str]] = {}
        samples = []
        keydir = self.output / "images/video_keyframes"
        with (self.cache / ("proof_encode.log" if proof else "encode.log")).open("wb") as log:
            encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
            if encoder.stdin is None:
                raise ValueError("Encoder pipe unavailable")
            try:
                for index, scene in enumerate(SCENES):
                    if scene[0] >= duration:
                        break
                    numbers = list(
                        range(round(scene[0] * 30), round(min(scene[1], duration) * 30), 2)
                    )
                    times = [source_time(n / 30) for n in numbers]
                    indices = sorted({round((t - times[0]) * 10) for t in times})
                    select = "+".join(f"eq(n\\,{i})" for i in indices)
                    cmd = [
                        self.ffmpeg,
                        "-v",
                        "error",
                        "-ss",
                        str(times[0]),
                        "-i",
                        str(self.source),
                        "-t",
                        str(times[-1] - times[0] + 0.1),
                        "-vf",
                        f"select={select}",
                        "-fps_mode",
                        "passthrough",
                        "-f",
                        "rawvideo",
                        "-pix_fmt",
                        "rgb24",
                        "pipe:1",
                    ]
                    self.commands.append(cmd)
                    decoder = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=log)
                    if decoder.stdout is None:
                        raise ValueError("Decoder pipe unavailable")
                    previous_time = -1.0
                    raw = Image.new("RGB", (1280, 720))
                    for number, t in zip(numbers, times, strict=True):
                        if t != previous_time:
                            data = decoder.stdout.read(1280 * 720 * 3)
                            if len(data) != 1280 * 720 * 3:
                                raise ValueError(f"Incomplete accelerated source frame at {t}")
                            raw = Image.frombytes("RGB", (1280, 720), data)
                            previous_time = t
                        image = self.frame(raw, number / 30)
                        if index < 3:
                            transcripts[index] = image.info["transcript"]
                        encoder.stdin.write(image.tobytes() * 2)
                        if number % 30 == 0:
                            samples.append({"display_time": number / 30, **self.latest})
                            if proof:
                                image.save(self.cache / f"proof_{number // 30:02d}.png")
                        if not proof:
                            for n in (number, number + 1):
                                if n in KEYFRAMES:
                                    i = KEYFRAMES.index(n)
                                    image.save(
                                        keydir / f"{i + 1:02d}_video_{round(n / 30):02d}s.png"
                                    )
                    decoder.stdout.close()
                    if decoder.wait(timeout=30):
                        raise ValueError("Accelerated decoder failed")
                    print(f"{'Proof' if proof else 'Final'} scene {index + 1} rendered", flush=True)
            finally:
                encoder.stdin.close()
                if encoder.wait(timeout=120):
                    raise ValueError("Accelerated encoder failed")
        if proof:
            # The ordinary final-video probe correctly rejects25s, so decode proof separately.
            decode = subprocess.run(
                [self.ffmpeg, "-v", "error", "-i", str(partial), "-f", "null", "-"],
                capture_output=True,
                check=True,
            )
            (self.cache / "proof_decode.log").write_bytes(decode.stderr)
        else:
            metadata = probe(self.ffmpeg, partial, self.cache / "master_decode.log")
        partial.replace(target)
        story = validate_first15(transcripts)
        if story["automated_status"] != "PASS":
            raise ValueError("Rendered first15 contract failed")
        story["build"] = BUILD
        if proof:
            write_json(self.cache / "motion_samples.json", {"samples": samples, "story": story})
            validate_motion(samples, self.output / "manifests/motion_validation.json", target)
            return
        web = target.with_name("project6_linkedin_web.mp4")
        command = [
            self.ffmpeg,
            "-y",
            "-v",
            "error",
            "-i",
            str(target),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "24",
            "-threads",
            "2",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(web),
        ]
        self.commands.append(command)
        subprocess.run(command, check=True, capture_output=True)
        web_meta = probe(self.ffmpeg, web, self.cache / "web_decode.log")
        keys = sorted(keydir.glob("[0-9][0-9]_video_*.png"))
        for i, number in enumerate(KEYFRAMES):
            subprocess.run(
                [
                    self.ffmpeg,
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    str(number / 30),
                    "-i",
                    str(web),
                    "-frames:v",
                    "1",
                    str(keydir / f"decoded_{i + 1:02d}.png"),
                ],
                check=True,
                capture_output=True,
            )
        Image.open(keys[2]).save(self.output / "images/project6_thumbnail.png")
        base.contact(keys, self.output / "images/video_keyframe_contact_sheet.png", 5)
        write_json(
            self.output / "manifests/video_manifest.json",
            {
                **self.manifest(),
                "master": metadata,
                "web": web_meta,
                "outputs": base.artifacts([target, web]),
                "keyframes": base.artifacts(keys),
                "commands": self.commands,
                "motion_samples": samples,
                "motion_validation_sha256": checksum(
                    self.output / "manifests/motion_validation.json"
                ),
            },
        )
        write_json(self.output / "manifests/first_15_seconds_story_validation.json", story)
        write_json(self.preview / "first_15_seconds_story_validation.json", story)


def validate_motion(samples: list[dict[str, Any]], path: Path, proof: Path) -> None:
    results = []
    for index in sorted({r["scene"] for r in samples}):
        rows = [r for r in samples if r["scene"] == index]
        source = len({r["source_hash"] for r in rows}) > 1
        field = len({r["field_hash"] for r in rows}) > 1
        trail = len({r["trail_hash"] for r in rows}) > 1
        clock = rows[-1]["source_timestamp"] - rows[0]["source_timestamp"] >= 6 * (
            rows[-1]["display_time"] - rows[0]["display_time"]
        )
        lifecycle = len({tuple(r["active_ids"]) for r in rows}) > 1
        assert all(
            r["maximum_observation_time"] is None
            or r["maximum_observation_time"] <= r["source_timestamp"]
            for r in rows
        )
        results.append(
            {
                "scene": index,
                "SOURCE_MOTION": source,
                "CONTOUR_EVOLUTION": field,
                "TRAJECTORY_EVOLUTION": trail,
                "TIME_ADVANCEMENT": clock,
                "TRACK_LIFECYCLE": lifecycle,
                "NO_STATIC_OVERLAY_FAILURE": field and trail,
            }
        )
    checks = {
        key: "PASS" if all(row[key] for row in results) else "FAIL"
        for key in results[0]
        if key != "scene"
    }
    write_json(
        path,
        {
            "build": BUILD,
            "checks": checks,
            "scenes": results,
            "proof_sha256": checksum(proof),
            "analytics_timebase": "ORIGINAL_SOURCE_TIME",
            "presentation_playback": "ACCELERATED_FOR_VISUALIZATION",
        },
    )
    if "FAIL" in checks.values():
        raise ValueError(f"Motion proof failed: {checks}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "proof", "final"))
    args = parser.parse_args()
    renderer = DynamicRenderer(Path.cwd())
    if args.mode == "prepare":
        renderer.prepare()
        return
    with palette():
        if args.mode == "proof":
            renderer.encode(proof=True)
        else:
            motion = json.loads((renderer.output / "manifests/motion_validation.json").read_text())
            if any(v != "PASS" for v in motion["checks"].values()):
                raise ValueError("Motion gate not passed")
            renderer.encode(proof=False)


if __name__ == "__main__":
    main()
