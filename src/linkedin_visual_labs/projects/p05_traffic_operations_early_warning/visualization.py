"""Deterministic derived-only raster design; all analytical values are bound inputs."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import matplotlib
from PIL import Image, ImageDraw, ImageFont

from .design_system import (
    AMBER,
    BG,
    BLUE,
    BORDER,
    CREAM,
    CYAN,
    DARK_INK,
    GREEN,
    HEADER,
    INK,
    MUTED,
    PANEL,
    PURPLE,
    RED,
    VIDEO_SIZE,
    ease,
)
from .presentation import TITLE, Presentation, clock, interval_tracks

TEAL = CYAN
SIZE = VIDEO_SIZE


@lru_cache(maxsize=32)
def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path(matplotlib.get_data_path()) / "fonts/ttf" / name
    return ImageFont.truetype(str(path), size)


def text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    size: int = 28,
    color: str = INK,
    width: int = 936,
    bold: bool = False,
) -> int:
    """Measured word wrapping, explicit vertical endpoint for overflow checks."""
    x, y = xy
    face = font(size, bold)
    for paragraph in value.split("\n"):
        line = ""
        for word in paragraph.split():
            if draw.textlength(word, font=face) > width:
                raise ValueError(f"Unbreakable visual text: {word}")
            proposed = (line + " " + word).strip()
            if draw.textlength(proposed, font=face) > width:
                draw.text((x, y), line, font=face, fill=color)
                y += int(size * 1.4)
                line = word
            else:
                line = proposed
        draw.text((x, y), line, font=face, fill=color)
        y += int(size * 1.4)
    return y


def base(label: str) -> Image.Image:
    im = Image.new("RGB", SIZE, BG)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 1080, 102), fill=HEADER)
    text(d, (42, 18), "PROJECT 6", 17, MUTED, bold=True)
    text(d, (42, 50), "Traffic Operations Early-Warning System", 29, bold=True)
    d.rounded_rectangle((802, 22, 1040, 51), radius=12, fill=CREAM)
    text(d, (817, 26), "RECORDED PROTOTYPE", 16, DARK_INK, bold=True)
    text(d, (55, 1250), label, 17, MUTED)
    return im


def project_point(x: float, y: float, top: int = 440) -> tuple[int, int]:
    """Uniform source-pixel scaling; no physical-distance interpretation."""
    return round(104 + (x - 0.46) * 1700), round(top + (y - 0.44) * 956.25)


def geometry(
    draw: ImageDraw.ImageDraw, p: Presentation, top: int = 440, labels: bool = True
) -> None:
    def pt(value: dict[str, float]) -> tuple[int, int]:
        return project_point(value["x"], value["y"], top)

    draw.rounded_rectangle((64, top - 36, 1016, top + 350), radius=22, fill=PANEL)
    for name, color in (("roi", "#34495d"), ("queue_zone", "#4c4436")):
        points = [pt(v) for v in p.geometry[name]["points"]]
        draw.polygon(points, fill=color, outline=MUTED)
    for name, color in (("entry", TEAL), ("exit", AMBER)):
        line = p.geometry[name]
        a, b = pt(line["start"]), pt(line["end"])
        draw.line((a, b), fill=color, width=6)
        text(draw, (a[0] - 25, a[1] - 38), name.upper(), 22, color, width=180, bold=True)
    if labels:
        text(draw, (95, top + 305), "ANALYSIS ROI  /  SHADED QUEUE ZONE", 22, MUTED)


def paths(draw: ImageDraw.ImageDraw, p: Presentation, progress: float, top: int = 440) -> None:
    selected = interval_tracks(p.trajectories, 1200, 1800)
    selected = selected[selected.source_timestamp <= 1200 + 600 * progress]
    completed = set(p.journeys.loc[p.journeys.completed_eligible, "track_id"])
    for identity, group in selected.groupby("track_id", sort=True):
        points = [
            project_point(float(x), float(y), top)
            for x, y in zip(group.reference_x, group.reference_y, strict=True)
        ]
        times = group.source_timestamp.tolist()
        good = identity in completed
        for i in range(1, len(points)):
            if times[i] - times[i - 1] <= 1.0 and (good or i % 4 < 2):
                draw.line((points[i - 1], points[i]), fill=TEAL if good else BLUE, width=2)
        if len(points) > 1:
            x, y = points[-1]
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=TEAL if good else BLUE)


def timeline(draw: ImageDraw.ImageDraw, p: Presentation, y: int, progress: float = 1.0) -> None:
    draw.line((95, y, 975, y), fill="#40566c", width=8)
    transitions = p.release["result"]["transitions"]
    for i, transition in enumerate(transitions):
        start = float(transition["timestamp"])
        end = float(transitions[i + 1]["timestamp"]) if i + 1 < len(transitions) else 1800.0
        end = min(end, 1200 + 600 * progress)
        if end > start:
            a = 95 + (start - 1200) / 600 * 880
            b = 95 + (end - 1200) / 600 * 880
            color = AMBER if transition["state"] == "WARNING" else TEAL
            draw.line((a, y, b, y), fill=color, width=8)
    text(draw, (95, y + 16), "20:00", 22, MUTED)
    text(draw, (880, y + 16), "30:00", 22, MUTED)
    onset = p.release["result"]["warning_timestamp"]
    x = round(95 + (onset - 1200) / 600 * 880)
    draw.line((x, y - 20, x, y + 12), fill=AMBER, width=3)
    text(draw, (x - 15, y - 62), "WARNING " + p.warning, 25, AMBER)


def panel(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = PANEL) -> None:
    d.rounded_rectangle(box, radius=20, fill=fill, outline="#627D94", width=2)


def metric_card(
    d: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    value: str,
    detail: str,
    width: int = 295,
    height: int = 100,
) -> None:
    d.rounded_rectangle((x, y, x + width, y + height), radius=15, fill=INK, outline=BORDER, width=2)
    text(d, (x + 15, y + 10), label, 18, "#526B82", width=width - 30, bold=True)
    text(d, (x + 15, y + 38), value, 29, DARK_INK, width=width - 30, bold=True)
    text(d, (x + 15, y + height - 24), detail, 16, DARK_INK, width=width - 30)


def traffic_hero(
    p: Presentation, progress: float, markers: bool = False, annotations: bool = True
) -> Image.Image:
    """Uniform crop of real normalized geometry; schematic grid is editorial only."""
    im = Image.new("RGB", (1080, 748), HEADER)
    d = ImageDraw.Draw(im)
    for y in range(748):
        v = int(25 + 16 * (1 - abs(y - 374) / 374))
        d.line((0, y, 1080, y), fill=(v, v + 13, v + 24))
    for x in range(0, 1080, 60):
        d.line((x, 0, x, 748), fill="#2B3E50")
    for y in range(0, 748, 60):
        d.line((0, y, 1080, y), fill="#2B3E50")
    geometry(d, p, 235, labels=annotations)
    paths(d, p, min(1.0, 0.20 + progress * 0.8), 235)
    text(d, (45, 30), "DERIVED TRAFFIC GEOMETRY", 26, INK, bold=True)
    if annotations:
        text(d, (45, 78), "20:00-30:00 original source interval", 22, MUTED)
    if markers:
        selected = interval_tracks(p.trajectories, 1200, 1800)
        t = 1200 + 600 * min(0.999, 0.20 + progress * 0.8)
        near = selected[(selected.source_timestamp >= t - 1) & (selected.source_timestamp <= t)]
        for px, py in near[["reference_x", "reference_y"]].to_numpy(dtype=float):
            x, y = project_point(float(px), float(py), 235)
            d.rectangle((x - 20, y - 14, x + 20, y + 14), outline=CYAN, width=3)
    if annotations:
        text(d, (45, 635), "Real paths / editorial markers / no physical scale", 22, MUTED)
        text(d, (45, 680), "Source imagery is not redistributed", 22, MUTED)
    return im


def static_image(p: Presentation) -> Image.Image:
    im = base("DERIVED ONLY / NO SOURCE PIXELS / ORIGINAL ANALYTICAL TIME")
    d = ImageDraw.Draw(im)
    text(d, (55, 130), TITLE + ".", 49, INK, width=980, bold=True)
    text(d, (55, 270), "One continuous interval / 20:00-30:00", 27, AMBER)
    geometry(d, p, 490)
    paths(d, p, 1.0, 490)
    text(d, (80, 365), "TEN-MINUTE TRAJECTORY STUDY", 23, CYAN, bold=True)
    text(d, (80, 855), "Solid cyan: completed / dashed blue: incomplete", 23, MUTED)
    timeline(d, p, 965)
    c = p.counts
    for i, (label, value) in enumerate(
        (
            ("CONFIRMED", c["eligible_confirmed_tracks"]),
            ("COMPLETED", c["completed_dwell_samples"]),
            ("EXITS", c["eligible_exits"]),
        )
    ):
        metric_card(d, 55 + 325 * i, 1040, label, str(value), "Full 30-minute episode")
    text(d, (55, 1170), "No qualifying queue. Lead time: Not reportable.", 29, AMBER, bold=True)
    return im


def spark(
    d: ImageDraw.ImageDraw,
    p: Presentation,
    column: str,
    box: tuple[int, int, int, int],
    color: str,
    progress: float = 1.0,
) -> None:
    x, y, right, bottom = box
    d.rectangle(box, fill=INK, outline=BORDER)
    rows = p.metrics[(p.metrics.timestamp >= 1260) & (p.metrics.timestamp < 1800)]
    if column not in rows:
        text(d, (x + 10, y + 8), "Unavailable", 18, DARK_INK, width=right - x - 20)
        return
    rows = rows[rows[column].notna()]
    maximum = max(float(rows[column].max()), 1e-9) if len(rows) else 1.0
    minimum = min(float(rows[column].min()), 0.0) if len(rows) else 0.0
    points = [
        (
            round(x + 8 + (float(t) - 1260) / 540 * (right - x - 16)),
            round(bottom - 8 - (float(v) - minimum) / (maximum - minimum) * (bottom - y - 16)),
        )
        for t, v in zip(rows.timestamp, rows[column], strict=True)
        if t <= 1260 + 540 * max(0.05, progress)
    ]
    if len(points) > 1:
        d.line(points, fill=color, width=3)


def result_panel(d: ImageDraw.ImageDraw, p: Presentation) -> None:
    panel(d, (676, 151, 1040, 813))
    text(d, (705, 180), "EVENT EVIDENCE", 20, MUTED, bold=True)
    for i, (label, value, color) in enumerate(
        (
            ("WARNING", p.warning, AMBER),
            ("VISIBLE QUEUE", "Not qualified", RED),
            ("LEAD TIME", "Not reportable", MUTED),
        )
    ):
        y = 265 + 156 * i
        d.ellipse((699, y, 721, y + 22), fill=color)
        d.line((710, y + 24, 710, y + 120), fill="#627D94", width=3)
        text(d, (740, y - 5), label, 19, color, width=275, bold=True)
        text(d, (740, y + 38), value, 25, INK, width=275, bold=True)
    d.rounded_rectangle((696, 746, 1021, 795), radius=12, fill=CREAM)
    text(
        d,
        (708, 758),
        p.release["result"]["result_classification"],
        16,
        DARK_INK,
        width=305,
        bold=True,
    )


def frame(p: Presentation, number: int) -> Image.Image:
    if not 0 <= number < 1350:
        raise ValueError("Frame outside 45-second edit")
    seconds = number / 30
    scene = min(int(seconds // 5), 8) if seconds < 44 else 9
    start = scene * 5 if scene < 9 else 44
    progress = min(1.0, (seconds - start) / (4 if scene == 8 else 5))
    im = base("DERIVED VISUALS / NO SOURCE PIXELS / ORIGINAL-TIME ANALYTICS")
    im.paste(traffic_hero(p, progress, scene in (1, 2, 4, 5), scene in (0, 4, 9)), (0, 103))
    d = ImageDraw.Draw(im)
    c = p.counts
    changes = p.release["metric_changes"]

    def delta(key: str) -> str:
        item = changes[key]
        a, b = item["baseline_median"], item["screened_interval_median"]
        return ("N/A" if a is None else f"{a:.3g}") + " → " + ("N/A" if b is None else f"{b:.3g}")

    if scene == 1:
        panel(d, (45, 786, 560, 837))
        text(d, (66, 798), "DETECT → TRACK / CLIP-LOCAL ONLY", 22, INK, bold=True)
    elif scene == 2:
        result_panel(d, p)
    elif scene == 3:
        panel(d, (560, 171, 1034, 815))
        text(d, (590, 204), "CHALLENGE 1", 23, AMBER, bold=True)
        text(d, (590, 254), "Congestion is not\none metric.", 33, width=420, bold=True)
        definitions = (
            ("DENSITY", "Vehicles in zone", AMBER),
            ("DWELL", "Completed time", BLUE),
            ("THROUGHPUT", "Eligible exits", GREEN),
            ("PERSISTENCE", "Rule duration", PURPLE),
        )
        for i, (label, meaning, color) in enumerate(definitions):
            x, y = 590 + (i % 2) * 221, 414 + (i // 2) * 158
            d.rounded_rectangle(
                (x, y, x + 205, y + 137), radius=15, fill=INK, outline=color, width=2
            )
            text(d, (x + 12, y + 20), label, 18, color, width=183, bold=True)
            text(d, (x + 12, y + 64), meaning, 21, DARK_INK, width=183)
    elif scene == 4:
        panel(d, (440, 250, 1030, 540))
        text(d, (470, 279), "RECONCILE BEFORE MEASURING", 23, CYAN, bold=True)
        for i, (key, label) in enumerate(
            (
                ("candidate_tracks", "candidate tracks"),
                ("eligible_confirmed_tracks", "confirmed"),
                ("completed_dwell_samples", "completed journeys"),
            )
        ):
            text(d, (475, 333 + 61 * i), str(c[key]), 35, INK, bold=True)
            text(d, (625, 342 + 61 * i), label, 24, MUTED, width=360)
        text(d, (460, 590), "Full episode. Gaps stay explicit.", 25, CYAN)
    elif scene == 5:
        panel(d, (690, 470, 1015, 740))
        text(d, (710, 495), "JOURNEY ELIGIBILITY", 20, BLUE, width=285, bold=True)
        text(d, (710, 548), "Entry + exit\nNo invalid gap\nCompleted dwell only", 23, width=285)
        for i, (label, key) in enumerate(
            (
                ("DENSITY", "density_window_mean"),
                ("EXITS / 60s", "throughput"),
                ("NET INFLOW / 60s", "inflow_outflow_imbalance"),
            )
        ):
            metric_card(d, 55 + 325 * i, 1130, label, delta(key), "Baseline → comparison")
    elif scene == 6:
        d.rectangle((0, 103, 620, 851), fill=PANEL)
        for i, item in enumerate(p.release["result"]["transitions"][:3]):
            y = 230 + 155 * i
            color = (GREEN, AMBER, RED)[i]
            d.ellipse((55, y, 85, y + 30), fill=color)
            if i == min(2, int(progress * 3)):
                d.ellipse((48, y - 7, 92, y + 37), outline=color, width=3)
            text(d, (110, y - 7), item["state"], 34, color, bold=True)
            text(d, (110, y + 48), clock(item["timestamp"]), 31)
        text(d, (55, 742), "Persistence completion time", 23, MUTED, width=510)
        panel(d, (636, 146, 1038, 818))
        for i, (label, col, color) in enumerate(
            (
                ("DENSITY", "density_window_mean", AMBER),
                ("COMPLETED DWELL", "median_completed_dwell_seconds", BLUE),
                ("THROUGHPUT", "throughput", GREEN),
                ("MOVEMENT", "movement_index", PURPLE),
            )
        ):
            y = 166 + 156 * i
            metric_card(d, 656, y, label, "", "Separate vertical scale", 362, 145)
            spark(d, p, col, (675, y + 59, 999, y + 111), color, 0.25 + 0.75 * ease(progress))
    elif scene == 7:
        panel(d, (80, 185, 560, 322))
        text(d, (105, 210), "CONFIGURED ZONES", 27, BLUE, bold=True)
        text(d, (105, 258), "No measured hotspot claimed", 23, MUTED, width=430)
        panel(d, (565, 660, 1030, 810))
        text(d, (590, 680), "QUEUE RULE: NOT QUALIFIED", 23, AMBER, width=420, bold=True)
        text(d, (590, 725), "Independent outcome / null onset", 23, MUTED, width=420)
        d.rounded_rectangle((55, 1135, 1025, 1220), radius=18, fill=CREAM, outline=AMBER)
        text(
            d,
            (77, 1150),
            "Warning " + p.warning + " / queue not qualified",
            24,
            DARK_INK,
            bold=True,
        )
        text(d, (77, 1184), "Lead time: Not reportable", 24, DARK_INK)
    elif scene == 8:
        panel(d, (456, 241, 1020, 765))
        text(d, (490, 278), "DETERIORATION WARNING", 26, RED, width=495, bold=True)
        text(d, (490, 327), "Recorded analysis / " + p.warning, 28, INK, width=495, bold=True)
        d.line((490, 383, 986, 383), fill=MUTED, width=2)
        text(
            d,
            (490, 415),
            "Primary: density level\nSupporting: imbalance + trend",
            24,
            MUTED,
            width=490,
        )
        d.rounded_rectangle((490, 520, 986, 663), radius=18, fill=AMBER)
        text(
            d,
            (512, 540),
            p.release["recommendation"]["wording"],
            28,
            DARK_INK,
            width=450,
            bold=True,
        )
        text(
            d,
            (490, 691),
            "Alternative: " + p.release["recommendation"]["alternative_action"].title(),
            24,
        )
    headings = (
        ("The camera could see traffic.", "Could it warn Operations?"),
        ("Raw footage alone", "could not warn Operations."),
        ("The warning fired at " + p.warning + ".", "A queue onset did not qualify."),
        ("Challenge #1:", "Define congestion operationally."),
        ("Challenge #2:", "Vehicles disappear and reappear."),
        ("Detections became", "operational metrics."),
        ("The warning came from", "persistent deterioration."),
        ("The warning fired.", "The independent queue rule did not."),
        ("Turn insight into action.", "Give Operations evidence to review."),
        ("Camera → Metric → Warning", "→ Evidence → Action"),
    )
    a, b = headings[scene]
    y = text(d, (55, 895), a, 45, INK, width=975, bold=True)
    y = text(d, (55, y + 1), b, 43, AMBER, width=975, bold=True)
    details = (
        "Camera footage → operating metrics → explainable warning. Can the signal precede a queue?",
        "Actual coordinates. Editorial markers. Vehicle-only analysis; "
        "no face or plate recognition.",
        p.release["result"]["result_classification"] + ". Lead time: Not reportable.",
        "Unique exits, completed dwell, zone counts. Warning and queue have separate rules.",
        "Occlusion and fragmentation limit interpretation. Only eligible journeys supply dwell.",
        "Entry/exit events create metrics. Values below are window medians; evidence is mixed.",
        f"{p.rules['warning']['minimum_drivers']} leading drivers / "
        f"{p.rules['warning']['persistence_seconds']}s persistence. "
        "Density level, imbalance and trend.",
        "The separate queue rule did not satisfy "
        f"{p.rules['queue']['persistence_seconds']}s persistence.",
        "Illustrative operational response. Real facility controls and the cause are unknown.",
        "Better alerts start with knowing when not to overclaim.",
    )
    end = text(d, (55, y + 23), details[scene], 24, MUTED, width=960)
    if end > (1125 if scene in (5, 7) else 1230):
        raise ValueError("Caption overflow")
    if scene == 9:
        for i, (letter, label, color) in enumerate(
            (
                ("D", "DETECT", BLUE),
                ("T", "TRACK", GREEN),
                ("M", "MEASURE", AMBER),
                ("V", "VALIDATE", RED),
                ("A", "ACT", PURPLE),
            )
        ):
            x = 60 + 200 * i
            d.ellipse((x, 1110, x + 76, 1186), outline=color, width=5)
            text(d, (x + 24, 1128), letter, 30, color, bold=True)
            text(d, (x - 2, 1200), label, 18, INK, width=155, bold=True)
    d.rectangle((0, 1280, 1080, 1350), fill="#09121D")
    d.line((55, 1310, 790, 1310), fill="#667788", width=7)
    x = round(55 + 735 * (number + 1) / 1350)
    d.line((55, 1310, x, 1310), fill=INK, width=7)
    d.ellipse((x - 8, 1302, x + 8, 1318), fill=INK)
    text(d, (825, 1298), f"00:{int(seconds):02d} / 00:45", 20)
    return im


def contact_sheet(paths: list[Path], destination: Path, columns: int) -> None:
    width, height = 324, 430
    result = Image.new(
        "RGB", (columns * width, ((len(paths) + columns - 1) // columns) * height), BG
    )
    for i, path in enumerate(paths):
        with Image.open(path) as source:
            small = source.copy()
        small.thumbnail((width - 16, height - 16))
        result.paste(small, (i % columns * width + 8, i // columns * height + 8))
    result.save(destination)
