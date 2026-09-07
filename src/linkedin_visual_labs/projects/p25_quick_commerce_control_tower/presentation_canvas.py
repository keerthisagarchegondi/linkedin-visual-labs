"Exact portrait canvases with measured text bounds and deterministic layouts."

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from matplotlib.font_manager import findfont
from PIL import Image, ImageDraw, ImageFont

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    COLORS,
    NAMES,
    Evidence,
    number,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import Scene

WIDTH, HEIGHT = 1080, 1350
BG, INK, MUTED = "#f4f7fb", "#142e49", "#52647a"
FONT = Path(findfont("DejaVu Sans"))
BOLD = Path(findfont("DejaVu Sans:weight=bold"))


@dataclass(frozen=True)
class TextBox:
    text: str
    bounds: tuple[int, int, int, int]
    font_size: int


class Canvas:
    def __init__(self) -> None:
        self.image = Image.new("RGB", (WIDTH, HEIGHT), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.boxes: list[TextBox] = []

    def text(
        self,
        text: str,
        x: int,
        y: int,
        width: int,
        height: int,
        size: int = 26,
        color: str = INK,
        bold: bool = False,
    ) -> None:
        font = ImageFont.truetype(str(BOLD if bold else FONT), size)
        lines: list[str] = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = (line + " " + word).strip()
                if self.draw.textlength(candidate, font=font) > width:
                    if not line:
                        raise ValueError(f"Unbreakable text exceeds width: {word}")
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
        line_height = size + 7
        if (len(lines) - 1) * line_height + size > height:
            raise ValueError(
                f"Text exceeds layout height ({len(lines) * line_height}>{height}): {text}"
            )
        for i, line in enumerate(lines):
            bounds = self.draw.textbbox((x, y + i * line_height), line, font=font, anchor="lt")
            if not (
                32 <= bounds[0] <= bounds[2] <= WIDTH - 32
                and 24 <= bounds[1] <= bounds[3] <= HEIGHT - 24
            ):
                raise ValueError(f"Text outside safe margins: {text}")
            self.draw.text((x, y + i * line_height), line, font=font, fill=color, anchor="lt")
            self.boxes.append(
                TextBox(
                    line, (int(bounds[0]), int(bounds[1]), int(bounds[2]), int(bounds[3])), size
                )
            )

    def card(self, bounds: tuple[int, int, int, int], color: str = "#ffffff") -> None:
        self.draw.rounded_rectangle(bounds, radius=14, fill=color, outline="#dbe3ee", width=1)

    def validate(self) -> None:
        for i, a in enumerate(self.boxes):
            if a.font_size < 17:
                raise ValueError("Unreadably small label")
            for b in self.boxes[i + 1 :]:
                ax, ay, ar, ab = a.bounds
                bx, by, br, bb = b.bounds
                if max(ax, bx) < min(ar, br) and max(ay, by) < min(ab, bb):
                    raise ValueError(f"Overlapping text: {a.text} / {b.text}")


def champion_canvas(e: Evidence, caption: str | None = None) -> Canvas:
    c = Canvas()
    c.text("PROJECT 5 / RETROSPECTIVE CHAMPION MAP", 40, 32, 1000, 30, 19, "#1265ca", True)
    c.text("Local ownership. No universal winner.", 40, 78, 1000, 100, 39, bold=True)
    c.text("Public M5 · 28-day holdout · 2016-04-25 to 2016-05-22", 40, 141, 1000, 40, 21, MUTED)
    counts = "  |  ".join(f"{name} {count}" for name, count in e.counts.items())
    c.text(counts, 40, 186, 1000, 65, 20, bold=True)
    c.text("STORE", 40, 257, 110, 30, 18, MUTED, True)
    for category, x in [("FOODS", 170), ("HOUSEHOLD", 605)]:
        c.text(category, x, 257, 400, 30, 19, MUTED, True)
    for i, store in enumerate(sorted({r["store_id"] for r in e.tables["champions"]})):
        y = 295 + i * 85
        c.text(store, 40, y + 25, 110, 40, 23, bold=True)
        for category, x in [("FOODS", 170), ("HOUSEHOLD", 605)]:
            row = e.row("champions", store_id=store, category=category)
            name = NAMES.get(row["champion_model"], "No eligible champion")
            c.card((x - 10, y - 5, x + 410, y + 80))
            c.draw.rounded_rectangle((x - 10, y - 5, x - 4, y + 80), radius=3, fill=COLORS[name])
            c.text(
                name + (" · Review required" if row["champion_model"] is None else ""),
                x,
                y,
                397,
                25,
                17,
                COLORS[name],
                True,
            )
            c.text(
                "".join(
                    (
                        "WAPE ",
                        format(number(row["wape"], percent=True), ""),
                        "  |  Bias ",
                        format(number(row["bias"], percent=True), ""),
                    )
                ),
                x,
                y + 22,
                400,
                23,
                17,
            )
            c.text(
                f"vs naïve: {number(row['improvement_percentage_points'], signed=True)} pp",
                x,
                y + 42,
                400,
                23,
                17,
            )
            c.text(
                f"Disagreement {row['disagreement']:.4f} · no flag", x, y + 61, 400, 23, 17, MUTED
            )
    if caption is None:
        caption = (
            "RETROSPECTIVE: selected and scored on the same holdout; not futur"
            "e performance. TX_3 / FOODS requires review; its planning conting"
            "ency is not a champion. No disagreement exceeds 0.50."
        )
    c.text(caption, 40, 1165, 1000, 160, 23, MUTED)
    c.validate()
    return c


def allocation_example(e: Evidence) -> tuple[str, list[tuple[str, float, float]]]:
    """First canonical Base date with redistribution; never invent display allocations."""
    rows = [r for r in e.tables["labor_allocations"] if r["scenario"] == "Base"]
    for date in sorted({r["date"] for r in rows}):
        daily = [r for r in rows if r["date"] == date]
        stores = sorted({r["store_id"] for r in daily})
        pairs = []
        for store in stores:
            p = next(
                r
                for r in daily
                if r["store_id"] == store and r["allocation_method"] == "proportional"
            )
            o = next(
                r for r in daily if r["store_id"] == store and r["allocation_method"] == "optimized"
            )
            pairs.append((store, float(p["allocated_hours"]), float(o["allocated_hours"])))
        if sum(abs(p - o) for _, p, o in pairs) > 1e-7:
            return str(date), pairs
    raise ValueError("No canonical allocation redistribution example")


def scene_canvas(e: Evidence, scene: Scene, index: int, video: str) -> Canvas:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_world import (
        world_canvas,
    )

    return world_canvas(e, scene, 0.5)


def motion_frame(canvas: Canvas, e: Evidence, scene: Scene, progress: float) -> Image.Image:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_world import (
        world_canvas,
    )

    return world_canvas(e, scene, progress).image
