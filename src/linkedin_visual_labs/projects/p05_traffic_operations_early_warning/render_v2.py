"""Internal source-footage renderer for Sub-step 4.C.B; frozen analytics only."""

from __future__ import annotations

import argparse
import importlib
import json
import math
import subprocess
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .block2 import write_json
from .detection import checksum
from .presentation import KEYFRAMES, load_presentation
from .presentation_v2 import (
    BUILD,
    NAMES,
    SCENES,
    STATUS,
    STYLE,
    TOKENS,
    canonical_metrics,
    extract_tokens,
    scene_index,
    validate_first15,
)
from .runtime import resolve_packaged_ffmpeg
from .video import probe


def observations(frame: pd.DataFrame) -> list[Any]:
    return list(frame.itertuples())


def rgb(token: str, alpha: int = 255) -> tuple[int, int, int, int]:
    color = TOKENS[token]
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), alpha


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    from matplotlib import get_data_path

    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(Path(get_data_path()) / "fonts/ttf" / name), size)


def text(
    im: Image.Image,
    xy: tuple[int, int],
    value: str,
    size: int = 24,
    token: str = "text_primary",
    bold: bool = False,
    width: int = 1020,
) -> None:
    im.info.setdefault("transcript", []).append(value)
    draw = ImageDraw.Draw(im)
    words = value.split()
    line = ""
    y = xy[1]
    for word in [*words, ""]:
        candidate = (line + " " + word).strip()
        if (draw.textlength(candidate, font=font(size, bold)) > width or not word) and line:
            draw.text((xy[0], y), line, font=font(size, bold), fill=rgb(token))
            y += round(size * 1.3)
            line = word
        else:
            line = candidate
    if y > im.height:
        raise ValueError(f"Text overflow: {value}")


def panel(im: Image.Image, box: tuple[int, int, int, int]) -> None:
    layer = Image.new("RGBA", im.size)
    ImageDraw.Draw(layer).rounded_rectangle(
        box,
        radius=10,
        fill=rgb("panel_fill", STYLE["panel_alpha"]),
        outline=rgb("panel_border", 150),
        width=1,
    )
    im.paste(Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB"))


def point(x: float, y: float) -> tuple[int, int]:
    return round((x - 560) * 1.5), round(y * 1.5)


def arrow(draw: ImageDraw.ImageDraw, a: tuple[int, int], b: tuple[int, int]) -> None:
    angle = math.atan2(b[1] - a[1], b[0] - a[0])
    wings = [
        (round(b[0] - 8 * math.cos(angle + v)), round(b[1] - 8 * math.sin(angle + v)))
        for v in (-0.5, 0.5)
    ]
    draw.line((a, b), fill=rgb("entry_color", 210), width=2)
    draw.line((wings[0], b, wings[1]), fill=rgb("entry_color", 210), width=2)


def density_layer(history: pd.DataFrame) -> tuple[Image.Image, dict[str, Any]]:
    """Observation-weighted concentration, explicitly not an occupancy metric."""
    from matplotlib.figure import Figure

    gaussian_filter = importlib.import_module("scipy.ndimage").gaussian_filter

    hist, _, _ = np.histogram2d(
        history.reference_y, history.reference_x, bins=(72, 128), range=((0, 720), (0, 1280))
    )
    smooth = gaussian_filter(hist, sigma=1.2, truncate=2, mode="constant")
    norm = np.log1p(smooth) / max(float(np.log1p(smooth.max())), 1e-10)
    colors = np.array([rgb(k)[:3] for k in ("density_low", "density_mid", "density_high")])
    pixels = np.zeros((72, 128, 4), dtype=np.uint8)
    for channel in range(3):
        pixels[:, :, channel] = np.interp(norm, [0, 0.55, 1], colors[:, channel])
    pixels[:, :, 3] = np.where(norm > 0.1, norm * STYLE["density_fill_alpha_max"], 0)
    fill = Image.fromarray(pixels).resize((1280, 720), Image.Resampling.BILINEAR)
    layer = fill.crop((560, 0, 1280, 720)).resize((1080, 1080), Image.Resampling.BILINEAR)
    lines = Image.new("RGBA", layer.size)
    draw = ImageDraw.Draw(lines)
    fig = Figure()
    contour = fig.subplots().contour(
        np.arange(128) * 10 + 5,
        np.arange(72) * 10 + 5,
        norm,
        levels=[0.25, 0.45, 0.65, 0.85],
        colors=[TOKENS["density_mid"]],
    )
    paths = 0
    for i, segments in enumerate(contour.allsegs):
        color = ("density_low", "density_mid", "density_mid", "density_high")[i]
        for segment in segments:
            if len(segment) > 2:
                draw.line(
                    [point(float(x), float(y)) for x, y in segment],
                    fill=rgb(color, STYLE["contour_alpha"][i]),
                    width=3,
                )
                paths += 1
    halo = lines.filter(ImageFilter.GaussianBlur(STYLE["glow_radius"]))
    halo.putalpha(halo.getchannel("A").point(lambda a: round(a * 0.45)))
    layer.alpha_composite(halo)
    layer.alpha_composite(lines)
    vectors: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for _, group in history.groupby("track_id"):
        rows: list[Any] = list(group.itertuples())
        for a, b in pairwise(rows):
            dx, dy = b.reference_x - a.reference_x, b.reference_y - a.reference_y
            length = math.hypot(dx, dy)
            if 0 < b.source_timestamp - a.source_timestamp <= 1 and length > 0:
                cell = int(b.reference_x // 60), int(b.reference_y // 40)
                vectors.setdefault(cell, []).append((dx / length, dy / length))
    draw = ImageDraw.Draw(layer)
    arrows = 0
    for (cx, cy), directions in vectors.items():
        vx, vy = np.mean(directions, axis=0)
        length = math.hypot(vx, vy)
        if len(directions) >= 8 and length >= 0.4:
            x, y = cx * 60 + 30, cy * 40 + 20
            arrow(draw, point(x, y), point(x + 20 * vx / length, y + 20 * vy / length))
            arrows += 1
    return layer, {
        "classification": "TRAJECTORY_DENSITY_VISUALIZATION",
        "observations": len(history),
        "track_ids": int(history.track_id.nunique()),
        "histogram_sum": float(hist.sum()),
        "contour_paths": paths,
        "direction_arrows": arrows,
        "weighting": "one vote per accepted observation",
        "not_physical_density_or_speed": True,
        "smoothing_sigma_bins": 1.2,
        "contour_levels": [0.25, 0.45, 0.65, 0.85],
    }


class Renderer:
    """Streaming source decoding; no model loading, inference or analytic evaluation."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.p = load_presentation(self.root)
        self.output = self.p.output
        self.preview = root / "reference/project6/revised_previews_v2"
        self.cache = root / ".cache/p05_traffic_operations_early_warning/block4cb"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.audit = json.loads((self.output / "data/presentation_metrics.json").read_text())
        self.kpis = canonical_metrics(self.audit)
        tracks = pd.read_parquet(self.output / "data/tracks.parquet")
        bad = set(tracks.loc[tracks.relative_movement_per_second > 0.15, "track_id"])
        self.tracks = tracks[
            tracks.confirmed_at_observation
            & tracks.confirmed
            & tracks.roi_eligible
            & ~tracks.track_id.isin(bad)
        ].sort_values(["track_id", "source_timestamp"])
        self.crossings = pd.read_parquet(self.output / "data/crossing_events.parquet")
        self.geometry = json.loads((self.output / "manifests/calibration.json").read_text())
        self.source = root / "data/raw/p05_traffic_operations_early_warning/Dataset_A/cam_3.mp4"
        tool = resolve_packaged_ffmpeg()
        if tool.executable is None:
            raise ValueError("Packaged FFmpeg unavailable")
        self.ffmpeg = tool.executable
        self.layers: dict[int, Image.Image] = {}
        self.layer_evidence: dict[str, Any] = {}
        self.commands: list[list[str]] = []

    def manifest(self) -> dict[str, Any]:
        return {
            "build": BUILD,
            "PUBLICATION_STATUS": STATUS,
            "source_pixels": True,
            "final_artifact_release_approved": False,
            "tokens_sha256": checksum(self.preview / "project6_visual_tokens_v2.json"),
            "contract_sha256": checksum(self.preview / "project6_presentation_contract_v2.json"),
            "presentation_metrics_sha256": checksum(self.output / "data/presentation_metrics.json"),
            "analytical_clock": "ORIGINAL_SOURCE_SECONDS",
        }

    def prepare(self) -> None:
        for folder in (self.preview / "linkedin_video_frames", self.preview / "portfolio_tabs"):
            folder.mkdir(parents=True, exist_ok=True)
        tokens = extract_tokens(
            list((self.root / "reference/project6/previews/linkedin_video_frames").glob("*.png"))
        )
        write_json(self.preview / "project6_visual_tokens_v2.json", tokens)
        write_json(
            self.preview / "project6_presentation_contract_v2.json",
            {
                "build": BUILD,
                "PUBLICATION_STATUS": STATUS,
                "scenes": SCENES,
                "canonical_kpis": self.kpis,
                "kpi_window": "(1380,1440] original seconds",
                "numeric_source": "presentation_metrics.json fixed_window_comparisons[1]",
                "kpi_context": "Fixed 24:00 snapshot, not live readings on every edited frame",
                "source_map": "Each scene plays 1x from its recorded source start, "
                "with explicit cuts. "
                "Native 10fps repeated to 30fps; no optical interpolation. All "
                "source time retained.",
                "box_sampling": "Most recent accepted observation no older than 0.4 "
                "source seconds; "
                "no invented prediction; sparse sampling may cause brief positional lag.",
                "density": "History [1200,scene source start], held constant within each scene; "
                "no future observations. Static map uses [1200,1800).",
                "claim_limit": "Queue not confirmed means configured rule not "
                "satisfied; not physical "
                "queue absence, classifier accuracy or measured reduction of false escalation.",
            },
        )
        for i, scene in enumerate(SCENES):
            history = self.tracks[self.tracks.source_timestamp.between(1200, scene[2])]
            self.layers[i], self.layer_evidence[str(i)] = density_layer(history)

    def scene_pixels(
        self, raw: Image.Image, t: float, index: int, *, include_trails: bool = True
    ) -> Image.Image:
        im = (
            raw.convert("RGB")
            .crop((560, 0, 1280, 720))
            .resize((1080, 1080), Image.Resampling.LANCZOS)
        )
        layer = self.layers[index].copy()
        draw = ImageDraw.Draw(layer)
        history = self.tracks[
            (self.tracks.source_timestamp > max(1200, t - 240))
            & (self.tracks.source_timestamp <= t)
        ]
        if not include_trails:
            history = history.iloc[:0]
        for _, group in history.groupby("track_id"):
            rows: list[Any] = list(group.itertuples())
            for a, b in pairwise(rows):
                if not 0 < b.source_timestamp - a.source_timestamp <= 1:
                    continue
                age = t - b.source_timestamp
                recent = age <= 15
                alpha = round(245 - age * 7) if recent else round(115 - age / 240 * 93)
                color = "trajectory_primary" if recent else "trajectory_secondary"
                draw.line(
                    (point(a.reference_x, a.reference_y), point(b.reference_x, b.reference_y)),
                    fill=rgb(color, max(22, alpha)),
                    width=3 if recent else 2,
                )
        for name, token in (("roi", "zone_outline"), ("queue_zone", "warning_watch")):
            pts = [point(p["x"] * 1280, p["y"] * 720) for p in self.geometry[name]["points"]]
            draw.line([*pts, pts[0]], fill=rgb(token, 190), width=2)
        for name, token in (("entry", "entry_color"), ("exit", "exit_color")):
            line = self.geometry[name]
            a = point(line["start"]["x"] * 1280, line["start"]["y"] * 720)
            b = point(line["end"]["x"] * 1280, line["end"]["y"] * 720)
            draw.line((a, b), fill=rgb(token, 240), width=4)
            draw.text(
                (max(15, min(a[0], 950)), a[1] - 28),
                name.upper(),
                font=font(20, True),
                fill=rgb(token),
            )
        current = self.tracks[
            (self.tracks.source_timestamp <= t) & (self.tracks.source_timestamp > t - 0.4)
        ]
        current = current.sort_values("source_timestamp").groupby("track_id").tail(1)
        for row in observations(current.sort_values("confidence", ascending=False).head(7)):
            a, b = point(row.x1, row.y1), point(row.x2, row.y2)
            draw.rectangle((*a, *b), outline=rgb("box_default", 230), width=2)
            for x, y, sx, sy in (
                (a[0], a[1], 1, 1),
                (b[0], a[1], -1, 1),
                (a[0], b[1], 1, -1),
                (b[0], b[1], -1, -1),
            ):
                draw.line(
                    ((x, y + sy * 10), (x, y), (x + sx * 10, y)), fill=rgb("box_default"), width=4
                )
            px, py = point(row.reference_x, row.reference_y)
            draw.ellipse((px - 3, py - 3, px + 3, py + 3), fill=rgb("box_highlight"))
        events = self.crossings[
            (self.crossings.source_timestamp <= t) & (self.crossings.source_timestamp > t - 2)
        ]
        for event in observations(events):
            obs = self.tracks[self.tracks.detection_id == event.detection_id]
            if obs.empty:
                continue
            row = cast(Any, obs.iloc[0])
            x, y = point(float(row.reference_x), float(row.reference_y))
            radius = round(5 + (t - event.source_timestamp) * 10)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                outline=rgb("entry_color" if event.event_type == "ENTRY" else "exit_color", 180),
                width=2,
            )
        return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")

    def frame(
        self, raw: Image.Image, seconds: float, *, source_timestamp: float | None = None
    ) -> Image.Image:
        index = scene_index(seconds)
        scene = SCENES[index]
        source_time = (
            scene[2] + seconds - scene[0] if source_timestamp is None else source_timestamp
        )
        im = Image.new("RGB", (1080, 1350), TOKENS["background_primary"])
        im.paste(self.scene_pixels(raw, source_time, index), (0, 130))
        text(
            im,
            (28, 12),
            "PROJECT 6  /  RECORDED TRAFFIC-CAMERA ANALYSIS",
            18,
            "text_secondary",
            True,
        )
        text(im, (28, 48), scene[3], 32, "warning_active", True)
        panel(im, (20, 145, 1058, 198))
        stamp = f"{int(source_time) // 60:02d}:{source_time % 60:04.1f}"
        text(im, (36, 160), f"cam_3  •  SOURCE {stamp}  •  CLIP-LOCAL ANONYMOUS TRACKS", 20)
        if index == 1:
            panel(im, (20, 216, 1060, 272))
            text(im, (38, 229), scene[4], 25, "trajectory_primary", True)
            self.kpi_strip(im)
        elif index in (2, 7):
            panel(im, (20, 880, 523, 1080))
            panel(im, (537, 880, 1060, 1080))
            text(im, (40, 903), "TRAFFIC WARNING", 22, "warning_active", True, 460)
            text(im, (40, 943), "QUALIFIED  /  24:00", 31, "warning_active", True, 460)
            text(im, (40, 998), "Original source time", 20, width=450)
            text(im, (557, 903), "CONGESTION / QUEUE", 22, bold=True, width=460)
            text(im, (557, 943), "NOT CONFIRMED", 29, bold=True, width=470)
            text(im, (557, 995), "Independent sustained-queue rule", 19, width=470)
            panel(im, (20, 1090, 1060, 1190))
            text(
                im,
                (38, 1102),
                "Withhold a congestion claim; consider REVIEW / MONITOR",
                25,
                bold=True,
            )
            text(im, (38, 1150), "Configured check, not proof of physical queue absence.", 20)
        elif index == 3:
            panel(im, (20, 1080, 1060, 1190))
            text(im, (38, 1095), "178 confirmed track IDs  /  65 completed journeys", 28, bold=True)
            text(
                im,
                (38, 1144),
                "Full 30-minute processing counts; not a physical vehicle census.",
                21,
            )
        elif index == 4:
            self.kpi_strip(im)
        elif index == 5:
            self.charts(im)
        elif index == 6:
            panel(im, (20, 1040, 1060, 1190))
            text(im, (38, 1054), scene[4], 26, bold=True)
            text(
                im,
                (38, 1138),
                "297s latched WARNING includes hysteresis; not continuous qualification.",
                19,
            )
        elif index >= 8:
            panel(im, (20, 1035, 1060, 1190))
            text(im, (38, 1054), "Consider REVIEW / MONITOR", 33, "warning_active", True)
            text(im, (38, 1110), "CAMERA → FLOW → WARNING → VALIDATE → ACT", 25, bold=True)
            text(
                im, (38, 1154), "Design objective: avoid false escalation. Impact not measured.", 19
            )
        text(im, (28, 1222), scene[4], 23, width=1020)
        text(
            im,
            (28, 1317),
            "INTERNAL REVIEW  /  PUBLICATION: PENDING SOURCE PERMISSION",
            17,
            "warning_active",
            True,
        )
        return im

    def kpi_strip(self, im: Image.Image) -> None:
        panel(im, (20, 1035, 1060, 1190))
        text(im, (35, 1044), "FIXED 24:00 SNAPSHOT  /  NUMERIC WINDOW (23:00,24:00]", 20, bold=True)
        for i, (label, value, detail) in enumerate(self.kpis):
            x = 32 + i * 207
            text(im, (x, 1086), label, 14, "text_secondary", True, 198)
            text(
                im, (x, 1114), value, 25, "warning_active" if i == 0 else "text_primary", True, 198
            )
            text(im, (x, 1152), detail, 13, width=198)

    def charts(self, im: Image.Image) -> None:
        panel(im, (20, 900, 1060, 1190))
        text(im, (35, 913), "FROZEN 60s ROLLING METRICS  /  SOURCE 23:00-27:30", 20, bold=True)
        fields = ("density_window_mean", "inflow_outflow_imbalance", "throughput", "movement_index")
        data = self.p.metrics
        time_column = "timestamp"
        data = data[data[time_column].between(1380, 1650)]
        draw = ImageDraw.Draw(im)
        for i, (field, label) in enumerate(
            zip(fields, ("Occupancy", "Entry-exit", "Throughput", "Rel. movement"), strict=True)
        ):
            x = 40 + i * 253
            text(im, (x, 950), label, 19, width=235)
            values = data[[time_column, field]].dropna()
            low, high = float(values[field].min()), float(values[field].max())
            points = [
                (
                    round(x + (r[time_column] - 1380) / 270 * 225),
                    round(1145 - (r[field] - low) / max(high - low, 1e-9) * 130),
                )
                for _, r in values.iterrows()
            ]
            if len(points) > 1:
                draw.line(points, fill=rgb("trajectory_primary"), width=3)
            text(im, (x, 1160), f"{low:.4g}-{high:.4g}  /  scaled axis", 14, width=240)

    def decode(self, start: float, duration: float) -> subprocess.Popen[bytes]:
        command = [
            self.ffmpeg,
            "-v",
            "error",
            "-ss",
            str(start),
            "-i",
            str(self.source),
            "-t",
            str(duration),
            "-an",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ]
        self.commands.append(command)
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def raw_frame(self, start: float) -> Image.Image:
        process = self.decode(start, 0.1)
        data, _ = process.communicate(timeout=30)
        if process.returncode or len(data) < 1280 * 720 * 3:
            raise ValueError("Source decode failed")
        return Image.frombytes("RGB", (1280, 720), data[: 1280 * 720 * 3])

    def previews(self) -> None:
        paths = []
        for i, number in enumerate(KEYFRAMES):
            # Preview the same repeated native frame as the 30fps production encode.
            t = (number // 3) / 10
            scene = SCENES[scene_index(t)]
            raw = self.raw_frame(scene[2] + t - scene[0])
            path = self.preview / "linkedin_video_frames" / (NAMES[i] + ".png")
            self.frame(raw, t).save(path)
            paths.append(path)
        contact(paths, self.preview / "project6_revised_v2_video_contact_sheet.png", 5)
        write_json(
            self.preview / "preview_manifest.json",
            {
                **self.manifest(),
                "frames": artifacts(paths),
                "layers": self.layer_evidence,
                "review_status": "REVIEW_REQUIRED",
                "source_sha256": checksum(self.source),
            },
        )

    def static(self) -> None:
        history = self.tracks[
            (self.tracks.source_timestamp >= 1200) & (self.tracks.source_timestamp < 1800)
        ]
        self.layers[10], evidence = density_layer(history)
        raw = self.raw_frame(1799.9)
        scene = self.scene_pixels(raw, 1799.9, 10, include_trails=False)
        # Full continuous ten-minute paths supplement the recent 240-second trails.
        layer = Image.new("RGBA", scene.size)
        draw = ImageDraw.Draw(layer)
        for _, group in history.groupby("track_id"):
            rows: list[Any] = list(group.itertuples())
            for a, b in pairwise(rows):
                if 0 < b.source_timestamp - a.source_timestamp <= 1:
                    draw.line(
                        (point(a.reference_x, a.reference_y), point(b.reference_x, b.reference_y)),
                        fill=rgb("trajectory_secondary", 100),
                        width=2,
                    )
        scene = Image.alpha_composite(scene.convert("RGBA"), layer).convert("RGB")
        im = Image.new("RGB", (1080, 1350), TOKENS["background_primary"])
        im.paste(scene, (0, 130))
        text(im, (28, 20), "Ten minutes of traffic in one frame.", 36, "warning_active", True)
        text(
            im, (28, 79), "Continuous source interval [20:00,30:00) / anonymous observed paths", 23
        )
        text(
            im,
            (28, 1220),
            f"{history.track_id.nunique()} eligible track IDs in this interval. "
            "Contours show observation concentration.",
            24,
        )
        text(
            im,
            (28, 1280),
            "Image-plane direction only; no physical speed or congestion-hotspot claim.",
            20,
        )
        text(
            im,
            (28, 1320),
            "INTERNAL REVIEW / PUBLICATION: PENDING SOURCE PERMISSION",
            17,
            "warning_active",
            True,
        )
        path = self.output / "images/trajectory_map.png"
        im.save(path)
        thumbnail = path.with_name("trajectory_map_thumbnail.png")
        im.resize((540, 675), Image.Resampling.LANCZOS).save(thumbnail)
        write_json(
            self.output / "manifests/trajectory_map_manifest.json",
            {
                **self.manifest(),
                "source_interval": [1200, 1800],
                "density": evidence,
                "outputs": artifacts([path, thumbnail]),
                "source_background_timestamp": 1799.9,
            },
        )

    def video(self) -> None:
        master = self.output / "videos/project6_linkedin_master.mp4"
        partial = master.with_name("project6_linkedin_master.partial.mp4")
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
        self.commands.append(command)
        keydir = self.output / "images/video_keyframes"
        keys: list[Path] = []
        transcripts: dict[int, list[str]] = {}
        with (self.cache / "encode.log").open("wb") as log:
            encoder = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
            if encoder.stdin is None:
                raise ValueError("Missing encoder pipe")
            number = 0
            try:
                for index, scene in enumerate(SCENES):
                    decoder = self.decode(scene[2], scene[1] - scene[0])
                    if decoder.stdout is None:
                        raise ValueError("Missing decoder pipe")
                    try:
                        for _ in range(round((scene[1] - scene[0]) * 10)):
                            data = decoder.stdout.read(1280 * 720 * 3)
                            if len(data) != 1280 * 720 * 3:
                                raise ValueError("Incomplete original frame")
                            raw = Image.frombytes("RGB", (1280, 720), data)
                            image = self.frame(raw, number / 30)
                            if index < 3:
                                transcripts[index] = image.info["transcript"]
                            payload = image.tobytes()
                            for _ in range(3):
                                encoder.stdin.write(payload)
                                if number in KEYFRAMES:
                                    path = (
                                        keydir
                                        / f"{len(keys) + 1:02d}_video_{round(number / 30):02d}s.png"
                                    )
                                    image.save(path)
                                    keys.append(path)
                                number += 1
                    finally:
                        decoder.stdout.close()
                        if decoder.wait(timeout=30):
                            raise ValueError("Source decoder failed")
                    print(f"Rendered scene {index + 1}/10 ({number}/1350 frames)", flush=True)
            finally:
                encoder.stdin.close()
                if encoder.wait(timeout=120):
                    raise ValueError("Encoder failed")
        master_meta = probe(self.ffmpeg, partial, self.cache / "master_decode.log")
        partial.replace(master)
        web = master.with_name("project6_linkedin_web.mp4")
        command = [
            self.ffmpeg,
            "-y",
            "-v",
            "error",
            "-i",
            str(master),
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
            "-map_metadata",
            "-1",
            str(web),
        ]
        self.commands.append(command)
        subprocess.run(command, check=True, capture_output=True)
        web_meta = probe(self.ffmpeg, web, self.cache / "web_decode.log")
        Image.open(keys[2]).save(self.output / "images/project6_thumbnail.png")
        contact(keys, self.output / "images/video_keyframe_contact_sheet.png", 5)
        for i, number in enumerate(KEYFRAMES):
            command = [
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
            ]
            self.commands.append(command)
            subprocess.run(command, check=True, capture_output=True)
        write_json(
            self.output / "manifests/video_manifest.json",
            {
                **self.manifest(),
                "master": master_meta,
                "web": web_meta,
                "scenes": SCENES,
                "frames": 1350,
                "outputs": artifacts([master, web]),
                "keyframes": artifacts(keys),
                "commands": self.commands,
                "source_frame_repetition": "10fps source repeated 3x to 30fps; no "
                "motion interpolation",
            },
        )
        story = validate_first15(transcripts)
        if story["automated_status"] != "PASS":
            raise ValueError("First-15-second rendered story incomplete")
        story["encoded_keyframes"] = artifacts([keydir / f"decoded_{i:02d}.png" for i in (1, 2, 3)])
        story["render_binding"] = "Renderer.frame scenes 0-2; same renderer for preview and encode"
        write_json(self.output / "manifests/first_15_seconds_story_validation.json", story)
        write_json(self.preview / "first_15_seconds_story_validation.json", story)


def artifacts(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        {"path": str(p), "sha256": checksum(p), "mtime_ns": p.stat().st_mtime_ns} for p in paths
    ]


def contact(paths: list[Path], output: Path, columns: int) -> None:
    size = (270, 338) if columns == 5 else (640, 400)
    sheet = Image.new(
        "RGB",
        (columns * size[0], math.ceil(len(paths) / columns) * size[1]),
        TOKENS["background_primary"],
    )
    for i, path in enumerate(paths):
        with Image.open(path) as image:
            sheet.paste(
                image.resize(size, Image.Resampling.LANCZOS),
                (i % columns * size[0], i // columns * size[1]),
            )
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("previews", "production"))
    args = parser.parse_args()
    root = Path.cwd()
    renderer = Renderer(root)
    if args.mode == "previews":
        renderer.prepare()
        renderer.previews()
    else:
        # Do not rewrite tokens/contract after previews; production must follow them.
        for i, scene in enumerate(SCENES):
            history = renderer.tracks[renderer.tracks.source_timestamp.between(1200, scene[2])]
            renderer.layers[i], renderer.layer_evidence[str(i)] = density_layer(history)
        renderer.static()
        renderer.video()


if __name__ == "__main__":
    main()
