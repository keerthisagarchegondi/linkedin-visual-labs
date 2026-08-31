from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

W = H = 1080
FPS = 30
FRAMES = 1800
TOP_H = 58
STAGE_H = 742
RAIL_H = 112
CAPTION_H = H - TOP_H - STAGE_H - RAIL_H

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "work" / "inputs"
OUTPUTS = ROOT / "outputs"
BOARD_PATH = ROOT / "work" / "cinematic_board_v3.png"
SPRITES_PATH = ROOT / "work" / "game_objects_v3.png"
FFMPEG = Path(r"D:\linkedin-visual-labs\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe")

summary = json.loads((INPUTS / "tournament_summary.json").read_text(encoding="utf-8"))
game = json.loads((INPUTS / "representative_game.json").read_text(encoding="utf-8"))
events = json.loads((INPUTS / "representative_game_events.json").read_text(encoding="utf-8"))["events"]
stats = {r["strategy_id"]: r for r in summary["strategy_summary"]}

ORDER = ["collector", "aggressive_builder", "cash_protector", "specialist"]
RAIL_ORDER = ["specialist", "cash_protector", "aggressive_builder", "collector"]
NAMES = {
    "collector": "COLLECTOR",
    "aggressive_builder": "AGGRESSIVE\nBUILDER",
    "cash_protector": "CASH\nPROTECTOR",
    "specialist": "SPECIALIST",
}
COLORS = {
    "collector": (60, 208, 103),
    "aggressive_builder": (247, 144, 36),
    "cash_protector": (44, 157, 238),
    "specialist": (171, 82, 230),
}

FONT_COND = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
FONT_SANS = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_SANS_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")
FONT_SERIF = Path(r"C:\Windows\Fonts\georgiab.ttf")
for required in (FONT_COND, FONT_SANS, FONT_SANS_BOLD, FONT_SERIF, BOARD_PATH, SPRITES_PATH, FFMPEG):
    if not required.is_file():
        raise FileNotFoundError(required)


def font(size: int, family: str = "sans", bold: bool = False) -> ImageFont.FreeTypeFont:
    p = FONT_SERIF if family == "serif" else FONT_COND if family == "cond" else FONT_SANS_BOLD if bold else FONT_SANS
    return ImageFont.truetype(str(p), size)


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3.0 - 2.0 * x)


def ease_out(x: float) -> float:
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def ease_in_out(x: float) -> float:
    x = clamp(x)
    return 4 * x**3 if x < 0.5 else 1 - ((-2 * x + 2) ** 3) / 2


def spring(x: float) -> float:
    x = clamp(x)
    return 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


def lerp(a: float, b: float, p: float) -> float:
    return a + (b - a) * p


def rgba(color: tuple[int, int, int], a: int = 255) -> tuple[int, int, int, int]:
    return color + (a,)


def text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, size: int,
         fill=(244, 244, 236), anchor="la", family="sans", bold=False,
         stroke=0, spacing=4, align="left") -> None:
    draw.multiline_text(xy, value, font=font(size, family, bold), fill=fill, anchor=anchor,
                        stroke_width=stroke, stroke_fill=(0, 0, 0), spacing=spacing, align=align)


def rounded(draw: ImageDraw.ImageDraw, box, radius, fill, outline=None, width=1) -> None:
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=width)


def alpha_composite_at(base: Image.Image, overlay: Image.Image, xy: tuple[int, int]) -> None:
    base.alpha_composite(overlay, xy)


BOARD_SOURCE = Image.open(BOARD_PATH).convert("RGB")
SPRITE_SHEET = Image.open(SPRITES_PATH).convert("RGBA")


def crop_cell(row: int, col: int, cols: int) -> Image.Image:
    sh = SPRITE_SHEET.height / 3
    sw = SPRITE_SHEET.width / cols
    pad = 8
    box = (int(col * sw + pad), int(row * sh + pad), int((col + 1) * sw - pad), int((row + 1) * sh - pad))
    im = SPRITE_SHEET.crop(box)
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


DICE = [crop_cell(0, i, 3) for i in range(3)]
TOKENS = {
    "collector": crop_cell(1, 0, 4),
    "aggressive_builder": crop_cell(1, 1, 4),
    "specialist": crop_cell(1, 2, 4),
    "cash_protector": crop_cell(1, 3, 4),
}
HOUSE = crop_cell(2, 0, 3)
MONEY = crop_cell(2, 1, 3)
DEED = crop_cell(2, 2, 3)


def make_stage_base() -> Image.Image:
    im = BOARD_SOURCE.resize((W, STAGE_H), Image.Resampling.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(0.94)
    return im.convert("RGBA")


STAGE_BASE = make_stage_base()


def perimeter_points() -> list[tuple[float, float]]:
    # Four perspective edges, starting at START and moving clockwise.
    corners = [(1015, 590), (35, 655), (45, 88), (880, 50)]
    pts: list[tuple[float, float]] = []
    for side in range(4):
        a = corners[side]
        b = corners[(side + 1) % 4]
        for i in range(10):
            p = i / 10
            pts.append((lerp(a[0], b[0], p), lerp(a[1], b[1], p)))
    return pts


PATH = perimeter_points()


def route_position(start: int, end: int, progress: float) -> tuple[float, float, float]:
    steps = (end - start) % 40
    if steps == 0:
        x, y = PATH[end % 40]
        return x, y, 0
    q = clamp(progress) * steps
    step = min(steps - 1, int(q))
    local = smooth(q - step)
    a = PATH[(start + step) % 40]
    b = PATH[(start + step + 1) % 40]
    return lerp(a[0], b[0], local), lerp(a[1], b[1], local), math.sin(math.pi * local) * 22


def depth_scale(y: float) -> float:
    return lerp(0.64, 1.04, clamp((y - 30) / 650))


def paste_sprite(canvas: Image.Image, sprite: Image.Image, center: tuple[float, float], width: float,
                 angle: float = 0, opacity: float = 1, shadow=True, shadow_offset=(10, 14), blur=14) -> None:
    width = max(2, int(width))
    height = max(2, int(sprite.height * width / sprite.width))
    obj = sprite.resize((width, height), Image.Resampling.LANCZOS)
    if angle:
        obj = obj.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    if opacity < 1:
        a = obj.getchannel("A").point(lambda p: int(p * clamp(opacity)))
        obj.putalpha(a)
    x = int(center[0] - obj.width / 2)
    y = int(center[1] - obj.height / 2)
    if shadow:
        mask = obj.getchannel("A")
        sh = Image.new("RGBA", obj.size, (0, 0, 0, 0))
        sh.putalpha(mask.point(lambda p: int(p * 0.46)))
        sh = sh.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(sh, (x + shadow_offset[0], y + shadow_offset[1]))
    canvas.alpha_composite(obj, (x, y))


def camera(stage: Image.Image, center=(540, 360), zoom=1.0) -> Image.Image:
    zoom = max(1.0, zoom)
    cw, ch = W / zoom, STAGE_H / zoom
    left = clamp(center[0] - cw / 2, 0, W - cw)
    top = clamp(center[1] - ch / 2, 0, STAGE_H - ch)
    crop = stage.crop((int(left), int(top), int(left + cw), int(top + ch)))
    return crop.resize((W, STAGE_H), Image.Resampling.LANCZOS)


def header(frame: Image.Image, seconds: int, label: str) -> None:
    d = ImageDraw.Draw(frame, "RGBA")
    d.rectangle((0, 0, W, TOP_H), fill=(2, 5, 7, 255))
    d.line((0, TOP_H - 2, W, TOP_H - 2), fill=(184, 143, 59, 255), width=2)
    text(d, (24, TOP_H / 2), f"{seconds:02d}s", 25, (255, 215, 28, 255), "lm", "cond")
    text(d, (112, TOP_H / 2), label, 27, (250, 248, 238, 255), "lm", "cond", True)


def caption(frame: Image.Image, value: str, kicker: str = "CINEMATIC CAPTION / TURN RESULT") -> None:
    y = TOP_H + STAGE_H + RAIL_H
    d = ImageDraw.Draw(frame, "RGBA")
    d.rectangle((0, y, W, H), fill=(2, 12, 22, 255))
    d.line((0, y, W, y), fill=(178, 139, 61, 255), width=2)
    text(d, (W / 2, y + 23), kicker, 14, (170, 181, 183, 255), "mm", "cond")
    text(d, (W / 2, y + 78), value, 26, (247, 247, 240, 255), "mm", "sans", False, spacing=5, align="center")


def rail(frame: Image.Image, balances: dict[str, float], active: str | None = None,
         bankrupt: set[str] | None = None) -> None:
    bankrupt = bankrupt or set()
    y0 = TOP_H + STAGE_H
    d = ImageDraw.Draw(frame, "RGBA")
    d.rectangle((0, y0, W, y0 + RAIL_H), fill=(3, 10, 15, 255))
    d.line((0, y0, W, y0), fill=(190, 152, 69, 255), width=2)
    text(d, (W / 2, y0 + 15), "COMPACT PLAYER STATUS RAIL", 13, (190, 194, 188, 255), "mm", "cond")
    gap = 12
    cell_w = (W - gap * 5) / 4
    for i, strategy in enumerate(RAIL_ORDER):
        x = gap + i * (cell_w + gap)
        col = COLORS[strategy]
        border = (255, 226, 126, 255) if strategy == active else rgba(col, 230)
        fill = (7, 21, 28, 245) if strategy not in bankrupt else (32, 9, 10, 245)
        rounded(d, (x, y0 + 29, x + cell_w, y0 + 98), 9, fill, border, 2 if strategy == active else 1)
        mini = TOKENS[strategy]
        paste_sprite(frame, mini, (x + 34, y0 + 64), 47, shadow=False)
        display = NAMES[strategy].replace("\n", " ")
        name_size = 15 if strategy != "aggressive_builder" else 13
        text(d, (x + 68, y0 + 49), display, name_size, rgba(col), "lm", "cond", True)
        amount = max(0, int(round(balances.get(strategy, 0))))
        cash_col = (255, 91, 58, 255) if strategy in bankrupt or amount <= 100 else (249, 241, 203, 255)
        cash_label = "BANKRUPT" if strategy in bankrupt else f"${amount:,}"
        text(d, (x + 68, y0 + 76), cash_label, 21, cash_col, "lm", "sans", True)


def blank_frame() -> Image.Image:
    return Image.new("RGBA", (W, H), (2, 8, 14, 255))


def draw_ownership(stage: Image.Image, owned: dict[int, str], houses: dict[int, float]) -> None:
    d = ImageDraw.Draw(stage, "RGBA")
    for space, strategy in owned.items():
        x, y = PATH[space % 40]
        s = depth_scale(y)
        r = 10 * s
        d.ellipse((x - r, y - r * 0.45, x + r, y + r * 0.45), fill=rgba(COLORS[strategy], 225), outline=(255, 240, 190, 230), width=max(1, int(2 * s)))
    for space, progress in houses.items():
        if progress <= 0:
            continue
        x, y = PATH[space % 40]
        p = spring(clamp(progress))
        size = 72 * depth_scale(y) * p
        paste_sprite(stage, HOUSE, (x, y - 25 * p), size, angle=0, shadow=True, shadow_offset=(6, 8), blur=8)


def draw_token(stage: Image.Image, strategy: str, x: float, y: float, lift: float = 0,
               angle: float = 0, opacity: float = 1, emphasize: float = 1) -> None:
    scale = depth_scale(y)
    size = 96 * scale * emphasize
    paste_sprite(stage, TOKENS[strategy], (x, y - lift - size * 0.33), size, angle=angle,
                 opacity=opacity, shadow=True, shadow_offset=(8, 12 + int(lift * .15)), blur=12)


def draw_bill_transfer(stage: Image.Image, p: float, start: tuple[float, float], end: tuple[float, float],
                       amount: int, color=(76, 133, 82)) -> None:
    p = clamp(p)
    x = lerp(start[0], end[0], smooth(p))
    y = lerp(start[1], end[1], smooth(p)) - math.sin(math.pi * p) * 105
    paste_sprite(stage, MONEY, (x, y), 165, angle=lerp(-13, 8, p), shadow=True, blur=10)
    d = ImageDraw.Draw(stage, "RGBA")
    rounded(d, (x - 58, y - 23, x + 58, y + 24), 12, (3, 13, 16, 220), (237, 218, 155, 230), 2)
    text(d, (x, y), f"${amount:,}", 24, (248, 239, 202, 255), "mm", "cond", True)


def dice_tumble(stage: Image.Image, t: float, start=0.0, end=1.15) -> None:
    p = clamp((t - start) / (end - start))
    for i in range(2):
        pp = clamp(p + i * .05)
        x = lerp(340 + i * 130, 455 + i * 120, ease_out(pp))
        bounce = abs(math.sin(pp * math.pi * 2.3)) * (1 - pp) * 150
        y = 420 + i * 15 - bounce
        sprite = DICE[(int(pp * 8) + i) % 3]
        angle = (1 - pp) * (210 if i == 0 else -170)
        # restrained motion blur on fast descent
        if pp < .72:
            paste_sprite(stage, sprite, (x - 15, y + 8), 148, angle=angle + 12, opacity=.20, shadow=False)
        paste_sprite(stage, sprite, (x, y), 154, angle=angle, shadow=True, shadow_offset=(14, 22), blur=18)


def popup_card(frame: Image.Image, title: str, lines: list[tuple[str, str]], color: tuple[int, int, int],
               box=(700, 270, 1040, 650), progress=1.0, danger=False) -> None:
    p = spring(clamp(progress))
    width = int((box[2] - box[0]) * p)
    height = int((box[3] - box[1]) * p)
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2 + int((1 - clamp(progress)) * 22)
    if width < 8 or height < 8:
        return
    card = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card, "RGBA")
    base_fill = (11, 12, 13, 246) if danger else (239, 234, 211, 250)
    outline = (240, 73, 44, 255) if danger else rgba(color)
    rounded(cd, (4, 4, card.width - 5, card.height - 5), 12, base_fill, outline, 4)
    cd.rectangle((20, 22, card.width - 20, 83), fill=outline)
    text(cd, (card.width / 2, 53), title, 25, (255, 252, 239, 255), "mm", "cond", True)
    ink = (246, 245, 235, 255) if danger else (33, 34, 31, 255)
    for i, (label, value) in enumerate(lines):
        yy = 126 + i * 68
        text(cd, (card.width / 2, yy), label, 17, ink, "mm", "cond")
        text(cd, (card.width / 2, yy + 28), value, 25, outline if not danger else (255, 92, 61, 255), "mm", "cond", True)
    card = card.resize((width, height), Image.Resampling.LANCZOS)
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0)); sh.putalpha(card.getchannel("A").filter(ImageFilter.GaussianBlur(16)).point(lambda x: int(x * .55)))
    frame.alpha_composite(sh, (cx - width // 2 + 12, cy - height // 2 + 16))
    frame.alpha_composite(card, (cx - width // 2, cy - height // 2))


def event_chips(frame: Image.Image, t: float, labels: list[tuple[float, str, tuple[int, int, int]]]) -> None:
    d = ImageDraw.Draw(frame, "RGBA")
    visible = [(s, label, c) for s, label, c in labels if t >= s]
    for i, (start, label, color) in enumerate(visible[-6:]):
        p = ease_out(clamp((t - start) / .28))
        x1 = int(754 + (1 - p) * 55)
        y1 = TOP_H + 24 + i * 48
        rounded(d, (x1, y1, 1046, y1 + 38), 18, (2, 12, 18, 224), rgba(color, 225), 2)
        d.ellipse((x1 + 12, y1 + 10, x1 + 30, y1 + 28), fill=rgba(color))
        text(d, (x1 + 21, y1 + 19), "•", 17, (3, 10, 12, 255), "mm", "sans", True)
        text(d, (x1 + 43, y1 + 19), label, 18, (246, 246, 237, 255), "lm", "cond", True)


def cold_balances(t: float) -> dict[str, float]:
    values = {"specialist": 1330, "cash_protector": 1318, "aggressive_builder": 1500, "collector": 1540}
    if t >= 1.4:
        values["specialist"] = lerp(1330, 970, smooth((t - 1.4) / .9))
    if t >= 2.5:
        values["specialist"] = lerp(970, 670, smooth((t - 2.5) / 1.0))
    if t >= 3.5:
        values["cash_protector"] = lerp(1318, 659, smooth((t - 3.5) / 1.4))
        values["collector"] = lerp(1540, 2199, smooth((t - 3.5) / 1.4))
    if t >= 4.6:
        values["cash_protector"] = lerp(659, 0, smooth((t - 4.6) / 1.15))
    return values


COLD_CHIPS = [
    (.00, "ROLL  •  8", (238, 218, 181)),
    (.72, "MOVE  •  6 SPACES", COLORS["specialist"]),
    (1.42, "BUY  •  P15  $360", COLORS["specialist"]),
    (2.35, "BUILD  •  P15 + P16", (45, 142, 81)),
    (3.30, "RENT  •  P21  $1,200", COLORS["collector"]),
    (4.35, "CASH SHOCK  •  $659 → $0", (239, 74, 48)),
]


def render_cold(t: float) -> Image.Image:
    stage = STAGE_BASE.copy()
    owned: dict[int, str] = {}
    if t >= 1.42:
        owned[15] = "specialist"
    if t >= 2.1:
        owned[16] = "specialist"
    if t >= 3.0:
        owned[21] = "collector"
    houses = {
        15: clamp((t - 2.35) / .52),
        16: clamp((t - 2.72) / .52),
        21: clamp((t - 3.05) / .48),
    }
    draw_ownership(stage, owned, houses)

    # Other players remain alive in the same physical world.
    cp_x, cp_y, cp_lift = route_position(17, 21, clamp((t - 3.05) / 1.15))
    draw_token(stage, "cash_protector", cp_x, cp_y, cp_lift, angle=0 if t < 5.2 else lerp(0, 18, smooth((t - 5.2) / .8)))
    draw_token(stage, "collector", *PATH[21], emphasize=1.02)
    draw_token(stage, "aggressive_builder", *PATH[28], emphasize=.94)
    sp_x, sp_y, sp_lift = route_position(9, 15, clamp((t - .65) / 1.05))
    draw_token(stage, "specialist", sp_x, sp_y, sp_lift, emphasize=1.08)

    if t < 1.25:
        dice_tumble(stage, t)
    if 3.42 <= t <= 4.85:
        draw_bill_transfer(stage, (t - 3.42) / 1.43, (cp_x, cp_y - 40), PATH[21], 659)
    if 4.55 <= t <= 5.75:
        draw_bill_transfer(stage, (t - 4.55) / 1.20, (cp_x, cp_y - 20), PATH[21], 659)

    # Camera moves are continuous and overlap the causal actions.
    if t < 1.1:
        center = (500, 400); zoom = lerp(1.42, 1.32, smooth(t / 1.1))
    elif t < 3.3:
        center = (lerp(510, PATH[15][0], smooth((t - 1.1) / 2.2)), lerp(380, PATH[15][1], smooth((t - 1.1) / 2.2))); zoom = 1.28
    elif t < 5.4:
        center = (lerp(PATH[15][0], PATH[21][0], smooth((t - 3.3) / 2.1)), lerp(PATH[15][1], PATH[21][1], smooth((t - 3.3) / 2.1))); zoom = 1.22
    else:
        center = (540, 355); zoom = lerp(1.22, 1.02, smooth((t - 5.4) / 1.6))
    view = camera(stage, center, zoom)
    if t >= 5.75:
        veil = Image.new("RGBA", view.size, (0, 8, 18, int(95 * smooth((t - 5.75) / .7))))
        view = Image.alpha_composite(view, veil)

    frame = blank_frame()
    frame.alpha_composite(view, (0, TOP_H))
    label = "DICE HIT"
    for start, value in [(0.72, "PIECES MOVE"), (1.42, "PROPERTY BOUGHT"), (2.35, "HOUSES BUILT"),
                         (3.30, "RENT TRANSFER"), (4.35, "CASH COLLAPSE"), (5.75, "THE QUESTION")]:
        if t >= start: label = value
    header(frame, int(t), label)
    rail(frame, cold_balances(t), "specialist", {"cash_protector"} if t >= 5.75 else set())
    caption(frame, "A roll becomes a purchase. A purchase becomes rent. One shock can end the game.")
    event_chips(frame, t, COLD_CHIPS)

    if 1.42 <= t < 3.05:
        popup_card(frame, "PROPERTY PURCHASED", [("ASSET", "P15 • GOLD AVE"), ("PRICE", "$360"), ("BUYER", "SPECIALIST")], COLORS["specialist"], progress=(t - 1.42) / .28)
    elif 3.28 <= t < 4.75:
        popup_card(frame, "RENT DUE", [("PROPERTY", "P21 • PARK PLACE"), ("OWED", "$1,200"), ("PAID TO", "COLLECTOR")], COLORS["collector"], progress=(t - 3.28) / .28)
    elif 4.45 <= t < 5.95:
        popup_card(frame, "LIQUIDITY CRITICAL", [("CASH BEFORE", "$659"), ("CASH AFTER", "$0"), ("SHORTFALL", "$541")], (238, 72, 45), progress=(t - 4.45) / .28, danger=True)
    if t >= 5.75:
        d = ImageDraw.Draw(frame, "RGBA")
        a = ease_out((t - 5.75) / .35)
        text(d, (W * .42, TOP_H + 360), "WHICH AI LANDLORD", int(31 * a), (242, 244, 239, int(255 * a)), "mm", "serif")
        text(d, (W * .42, TOP_H + 416), "SURVIVES 10,000 GAMES?", int(44 * a), (250, 250, 243, int(255 * a)), "mm", "serif")
    return frame.convert("RGB")


def strategy_balances() -> dict[str, float]:
    return {k: 1500 for k in ORDER}


def render_strategies(t: float) -> Image.Image:
    u = t - 7
    stage = STAGE_BASE.copy()
    schedule = [
        ("collector", 7.65, 2, 8),
        ("aggressive_builder", 8.85, 12, 18),
        ("cash_protector", 10.05, 22, 26),
        ("specialist", 11.25, 31, 37),
    ]
    active = None
    for strategy, start, a, b in schedule:
        p = clamp((t - start) / 1.05)
        x, y, lift = route_position(a, b, p)
        if start <= t < start + 1.25:
            active = strategy
        draw_token(stage, strategy, x, y, lift, emphasize=1.12 if strategy == active else .94, opacity=1 if t >= start - .15 else .40)
    # At the end, all four pieces move concurrently without resetting the board.
    if t >= 12.55:
        for idx, (strategy, _, a, b) in enumerate(schedule):
            x, y, lift = route_position(b, (b + 3 + idx) % 40, clamp((t - 12.55) / .75))
            draw_token(stage, strategy, x, y, lift, emphasize=1.0)
    view = camera(stage, (540, 350), lerp(1.13, 1.02, smooth(u / 7)))
    frame = blank_frame(); frame.alpha_composite(view, (0, TOP_H))
    header(frame, int(t), "FOUR STRATEGIES • ONE BOARD")
    rail(frame, strategy_balances(), active)
    caption(frame, "Four decision styles enter the same rules engine. Their pieces never stop playing.")
    d = ImageDraw.Draw(frame, "RGBA")
    descriptions = {"collector": "OWNS BROADLY", "aggressive_builder": "BUILDS EARLY", "cash_protector": "GUARDS CASH", "specialist": "COMPLETES GROUPS"}
    for i, (strategy, start, _, _) in enumerate(schedule):
        p = spring(clamp((t - start) / .30))
        if p <= 0:
            continue
        x1 = 27 + i * 260; y1 = TOP_H + 24 + int((1 - p) * -35)
        rounded(d, (x1, y1, x1 + 242, y1 + 78), 10, (3, 14, 21, 225), rgba(COLORS[strategy], 235), 2)
        text(d, (x1 + 121, y1 + 25), NAMES[strategy].replace("\n", " "), 17 if strategy != "aggressive_builder" else 15, rgba(COLORS[strategy]), "mm", "cond", True)
        text(d, (x1 + 121, y1 + 55), descriptions[strategy], 15, (238, 239, 232, 255), "mm", "cond")
    if t < 7.75:
        a = 1 - smooth((t - 7) / .75)
        text(d, (W / 2, TOP_H + 390), "WHICH STRATEGY SURVIVES?", 46, (246, 246, 238, int(255 * a)), "mm", "serif")
    return frame.convert("RGB")


def story_balances(t: float) -> tuple[dict[str, float], set[str]]:
    v = {"specialist": 1330, "cash_protector": 659, "aggressive_builder": 1613, "collector": 1540}
    if t >= 15.0:
        v["specialist"] = lerp(1330, 970, smooth((t - 15.0) / 1.1))
    if t >= 20.0:
        v["specialist"] = lerp(970, 670, smooth((t - 20.0) / 2.0))
    if t >= 24.0:
        v["cash_protector"] = lerp(659, 0, smooth((t - 24.0) / 3.1))
        v["collector"] = lerp(1540, 2199, smooth((t - 24.0) / 3.1))
    bankrupt = {"cash_protector"} if t >= 28.8 else set()
    return v, bankrupt


def render_story(t: float) -> Image.Image:
    stage = STAGE_BASE.copy()
    owned = {15: "specialist", 16: "specialist"} if t >= 17 else {15: "specialist"} if t >= 15 else {}
    if t >= 18.2:
        owned[17] = "specialist"
    if t >= 23:
        owned[21] = "collector"
    houses = {15: clamp((t - 20.1) / .55), 16: clamp((t - 20.7) / .55), 17: clamp((t - 21.3) / .55), 21: clamp((t - 22.0) / .55)}
    draw_ownership(stage, owned, houses)

    # Exact events: turn 257 purchase/build, then turn 306 rent and bankruptcy.
    sp = route_position(11, 15, clamp((t - 14.15) / 1.45)) if t < 17 else (*PATH[15], 0)
    cp = route_position(17, 21, clamp((t - 23.1) / 1.30)) if t >= 23 else (*PATH[17], 0)
    draw_token(stage, "specialist", sp[0], sp[1], sp[2], emphasize=1.08)
    cp_angle = lerp(0, 72, smooth((t - 28.0) / 1.0)) if t >= 28 else 0
    cp_opacity = lerp(1, .50, smooth((t - 29.0) / .8)) if t >= 29 else 1
    draw_token(stage, "cash_protector", cp[0], cp[1], cp[2], angle=cp_angle, opacity=cp_opacity)
    draw_token(stage, "collector", *PATH[21], emphasize=1.03)
    draw_token(stage, "aggressive_builder", *PATH[30], emphasize=.92)

    if 14.1 <= t <= 15.2:
        dice_tumble(stage, t, 14.0, 15.15)
    if 24.1 <= t <= 27.3:
        draw_bill_transfer(stage, (t - 24.1) / 3.2, (cp[0], cp[1] - 40), PATH[21], 659)

    if t < 17:
        center, zoom = PATH[15], 1.24
    elif t < 20:
        center, zoom = (350, 420), 1.12
    elif t < 23:
        center, zoom = (360, 450), 1.26
    elif t < 28:
        center, zoom = PATH[21], 1.22
    else:
        center, zoom = ((lerp(PATH[21][0], 540, smooth((t - 28) / 3)), lerp(PATH[21][1], 350, smooth((t - 28) / 3))), lerp(1.22, 1.02, smooth((t - 28) / 3)))
    view = camera(stage, center, zoom)
    frame = blank_frame(); frame.alpha_composite(view, (0, TOP_H))
    phases = [(14, "ACQUIRE"), (17, "EXPAND"), (20, "BUILD"), (23, "RENT"), (25.5, "CASH SHOCK"), (28, "BANKRUPTCY")]
    label = phases[0][1]
    for start, value in phases:
        if t >= start: label = value
    header(frame, int(t), f"GAME 8,721 • {label}")
    balances, bankrupt = story_balances(t)
    active = "cash_protector" if t >= 23 else "specialist"
    rail(frame, balances, active, bankrupt)
    captions = {
        "ACQUIRE": "Turn 257: Specialist acquires P15 for $360. Cash falls from $1,330 to $970.",
        "EXPAND": "P15, P16 and P17 become one persistent specialist cluster.",
        "BUILD": "Houses rise from their foundations—$150 each on P15 and P16.",
        "RENT": "Turn 306: Cash Protector lands on Collector's P21. Rent due: $1,200.",
        "CASH SHOCK": "Cash Protector pays its remaining $659. The shortfall is $541.",
        "BANKRUPTCY": "Cash reaches zero. The final payment lands before bankruptcy is declared.",
    }
    caption(frame, captions[label], "REPRESENTATIVE GAME / EVENT-LOG REPLAY")
    if 14.85 <= t < 17.0:
        popup_card(frame, "ASSET PURCHASED", [("PROPERTY", "P15 • GOLD AVE"), ("PRICE", "$360"), ("CASH", "$1,330 → $970")], COLORS["specialist"], progress=(t - 14.85) / .30)
    elif 20.0 <= t < 22.8:
        popup_card(frame, "HOUSES BUILT", [("TURN", "257"), ("P15 + P16", "$150 EACH"), ("OWNER", "SPECIALIST")], (37, 132, 72), progress=(t - 20) / .30)
    elif 23.8 <= t < 27.8:
        popup_card(frame, "RENT DUE", [("PROPERTY", "P21 • PARK PLACE"), ("REQUIRED", "$1,200"), ("AVAILABLE", "$659")], COLORS["collector"], progress=(t - 23.8) / .30)
    elif 27.2 <= t < 30.2:
        popup_card(frame, "BANKRUPTCY", [("PLAYER", "CASH PROTECTOR"), ("CASH AFTER", "$0"), ("REASON", "RENT • TURN 306")], (238, 70, 43), progress=(t - 27.2) / .30, danger=True)
    if t >= 30.15:
        d = ImageDraw.Draw(frame, "RGBA")
        p = ease_out((t - 30.15) / .35)
        rounded(d, (315, TOP_H + 282, 765, TOP_H + 392), 14, (2, 12, 20, int(225 * p)), (210, 173, 88, int(245 * p)), 2)
        text(d, (540, TOP_H + 318), "ONE REPRESENTATIVE GAME", 26, (255, 222, 113, int(255 * p)), "mm", "cond", True)
        text(d, (540, TOP_H + 360), "359 turns • Specialist wins", 24, (246, 247, 239, int(255 * p)), "mm", "sans")
    return frame.convert("RGB")


def navy_background() -> Image.Image:
    im = Image.new("RGBA", (W, H), (2, 11, 22, 255))
    d = ImageDraw.Draw(im, "RGBA")
    for y in range(H):
        a = int(28 * (1 - y / H))
        d.line((0, y, W, y), fill=(4, 28, 48, a))
    for r in range(80, 1200, 70):
        d.ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), outline=(25, 70, 94, 26), width=1)
    for i in range(64):
        x = (i * 173 + 41) % W; y = (i * 293 + 89) % H
        d.ellipse((x, y, x + 2, y + 2), fill=(108, 160, 186, 55))
    return im


NAVY = navy_background()


def analytics_header(frame: Image.Image, seconds: int, label: str) -> None:
    header(frame, seconds, label)


def render_scale(t: float) -> Image.Image:
    frame = NAVY.copy(); d = ImageDraw.Draw(frame, "RGBA")
    analytics_header(frame, int(t), "THE SCALE REVEAL")
    u = t - 31
    checkpoints = [(0, 1), (1.05, 10), (2.05, 100), (3.15, 1000), (4.35, 10000)]
    count = 1
    for start, value in checkpoints:
        if u >= start: count = value
    # The representative board becomes the first member of a growing mosaic.
    thumb = STAGE_BASE.resize((116, 82), Image.Resampling.LANCZOS)
    if u < 1.0:
        p = smooth(u)
        w = int(lerp(760, 116, p)); h = int(lerp(535, 82, p))
        one = STAGE_BASE.resize((w, h), Image.Resampling.LANCZOS)
        frame.alpha_composite(one, (int(lerp(160, 72, p)), int(lerp(180, 145, p))))
    else:
        grid_n = 1 if count == 1 else 4 if count == 10 else 7 if count == 100 else 10
        tile_w = 82 if grid_n >= 7 else 118
        tile_h = int(tile_w * .70)
        gap = 8
        total_w = grid_n * tile_w + (grid_n - 1) * gap
        start_x = (W - total_w) // 2
        start_y = 126
        show = min(grid_n * grid_n, max(1, int(ease_out(clamp((u - 1) / 3.2)) * grid_n * grid_n)))
        tiny = STAGE_BASE.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        for i in range(show):
            x = start_x + (i % grid_n) * (tile_w + gap)
            y = start_y + (i // grid_n) * (tile_h + gap)
            frame.alpha_composite(tiny, (x, y))
            d.rectangle((x, y, x + tile_w, y + tile_h), outline=(190, 153, 73, 125), width=1)
    rounded(d, (250, 600, 830, 820), 18, (2, 12, 20, 235), (200, 164, 82, 235), 2)
    text(d, (540, 646), "FULL GAMES SIMULATED", 23, (208, 217, 217, 255), "mm", "cond", True)
    text(d, (540, 724), f"{count:,}", 86, (255, 213, 42, 255), "mm", "cond", True)
    if count == 10000:
        text(d, (540, 787), "100 boards × 100 seeded games", 21, (184, 201, 206, 255), "mm", "sans")
    text(d, (540, 905), "1   →   10   →   100   →   1,000   →   10,000", 27, (234, 238, 231, 255), "mm", "cond", True)
    text(d, (540, 1000), "Not one anecdote. Ten thousand complete games.", 29, (248, 248, 239, 255), "mm", "serif")
    return frame.convert("RGB")


def render_leaderboard(t: float) -> Image.Image:
    frame = NAVY.copy(); d = ImageDraw.Draw(frame, "RGBA")
    analytics_header(frame, int(t), "WHO WON MOST OFTEN?")
    text(d, (540, 112), "WIN RATE WITH 95% WILSON CONFIDENCE INTERVAL", 25, (239, 241, 235, 255), "mm", "cond", True)
    x0, x1 = 350, 920
    y_axis = 825
    max_rate = .42
    for tick in range(0, 41, 10):
        x = lerp(x0, x1, tick / 42)
        d.line((x, 166, x, y_axis), fill=(57, 92, 111, 70), width=1)
        text(d, (x, y_axis + 28), f"{tick}%", 18, (163, 183, 191, 255), "mm", "cond")
    grow = ease_in_out(clamp((t - 39.35) / 4.15))
    for i, strategy in enumerate(ORDER):
        row = stats[strategy]
        y = 245 + i * 142
        col = COLORS[strategy]
        display = NAMES[strategy].replace("\n", " ")
        text(d, (46, y), display, 23 if strategy != "aggressive_builder" else 20, rgba(col), "lm", "cond", True)
        d.line((x0, y, x1, y), fill=(35, 63, 79, 255), width=4)
        bar_x = lerp(x0, x1, row["win_rate"] / max_rate)
        current = lerp(x0, bar_x, grow)
        rounded(d, (x0, y - 25, current, y + 25), 7, rgba(col, 232))
        ci = row["win_rate_ci95"]
        whisk = ease_out(clamp((t - 42.25 - i * .12) / .55))
        center = lerp(x0, x1, row["win_rate"] / max_rate)
        lo = lerp(center, lerp(x0, x1, ci["lower"] / max_rate), whisk)
        hi = lerp(center, lerp(x0, x1, ci["upper"] / max_rate), whisk)
        d.line((lo, y, hi, y), fill=(255, 251, 227, 255), width=6)
        d.line((lo, y - 13, lo, y + 13), fill=(255, 251, 227, 255), width=4)
        d.line((hi, y - 13, hi, y + 13), fill=(255, 251, 227, 255), width=4)
        value_alpha = int(255 * ease_out(clamp((t - 42.4 - i * .12) / .45)))
        text(d, (1008, y), f"{row['win_rate']*100:.2f}%", 27, (250, 243, 204, value_alpha), "rm", "cond", True)
        text(d, (x0, y + 49), f"95% CI  {ci['lower']*100:.2f}%–{ci['upper']*100:.2f}%", 18, (167, 187, 195, value_alpha), "la", "sans")
    if t >= 45.0:
        p = ease_out((t - 45) / .4)
        rounded(d, (42, 880, 1038, 960), 13, (9, 39, 34, int(215 * p)), rgba(COLORS["collector"], int(240 * p)), 2)
        text(d, (540, 920), "COLLECTOR LEADS: 3,772 WINS IN 10,000 GAMES", 28, (*COLORS["collector"], int(255 * p)), "mm", "cond", True)
    text(d, (540, 1025), "Bars stop by 43.6s so the complete result remains readable.", 22, (173, 191, 198, 255), "mm", "sans")
    return frame.convert("RGB")


def render_risk(t: float) -> Image.Image:
    frame = NAVY.copy(); d = ImageDraw.Draw(frame, "RGBA")
    analytics_header(frame, int(t), "RISK / REWARD SNAPSHOT")
    columns = [(400, "WIN RATE", "%"), (665, "BANKRUPTCY", "%"), (920, "MEDIAN CASH", "$")]
    for x, title, _ in columns:
        text(d, (x, 132), title, 23, (238, 241, 235, 255), "mm", "cond", True)
    d.line((532, 100, 532, 862), fill=(82, 111, 126, 150), width=2)
    d.line((795, 100, 795, 862), fill=(82, 111, 126, 150), width=2)
    grow = ease_in_out(clamp((t - 50.3) / 1.5))
    for i, strategy in enumerate(ORDER):
        row = stats[strategy]; col = COLORS[strategy]; y = 235 + i * 150
        paste_sprite(frame, TOKENS[strategy], (62, y), 72, shadow=False)
        text(d, (118, y - 9), NAMES[strategy].replace("\n", " "), 20 if strategy != "aggressive_builder" else 17, rgba(col), "lm", "cond", True)
        values = [row["win_rate"] / .42, row["bankruptcy_rate"] / .60, row["median_finishing_cash"] / 1700]
        labels = [f"{row['win_rate']*100:.1f}%", f"{row['bankruptcy_rate']*100:.1f}%", f"${row['median_finishing_cash']:,.0f}"]
        for j, (x, _, _) in enumerate(columns):
            left = x - 112; right = left + 180 * values[j] * grow
            d.rectangle((left, y - 18, x + 93, y + 18), fill=(16, 39, 52, 235))
            rounded(d, (left, y - 18, right, y + 18), 5, rgba(col, 225))
            text(d, (x + 94, y), labels[j], 19, (249, 243, 210, 255), "rm", "cond", True)
    rounded(d, (105, 885, 975, 965), 13, (3, 18, 29, 230), (82, 121, 139, 220), 2)
    text(d, (540, 925), "Collector wins most often; Aggressive Builder trades resilience for speed.", 26, (240, 242, 236, 255), "mm", "serif")
    text(d, (540, 1030), "Win rate, bankruptcy exposure and ending liquidity tell different parts of the story.", 21, (169, 188, 195, 255), "mm", "sans")
    return frame.convert("RGB")


def render_result(t: float) -> Image.Image:
    frame = NAVY.copy(); d = ImageDraw.Draw(frame, "RGBA")
    analytics_header(frame, int(t), "THE RESULT • THE PROOF")
    # Freeze the final 12 frames by clamping all animation before 59.6s.
    at = min(t, 59.6)
    hero = ease_out(clamp((at - 55.0) / .75))
    if hero > 0:
        glow = Image.new("RGBA", frame.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow, "RGBA")
        gd.ellipse((92, 145, 435, 488), fill=(48, 228, 104, int(62 * hero)))
        glow = glow.filter(ImageFilter.GaussianBlur(52)); frame.alpha_composite(glow)
        paste_sprite(frame, TOKENS["collector"], (270, 315), 280 * hero, shadow=True, shadow_offset=(18, 24), blur=24)
        text(d, (500, 188), "COLLECTOR", 56, rgba(COLORS["collector"], int(255 * hero)), "la", "cond", True)
        text(d, (500, 256), "WINS MOST OFTEN", 39, (247, 247, 239, int(255 * hero)), "la", "serif")
        text(d, (500, 364), "37.72%", 94, (255, 214, 48, int(255 * hero)), "la", "cond", True)
        text(d, (506, 430), "3,772 wins • 10,000 complete games", 25, (207, 219, 219, int(255 * hero)), "la", "sans")
    proof = ease_out(clamp((at - 56.65) / .45))
    if proof > 0:
        rounded(d, (105, 540, 975, 804), 16, (4, 20, 32, int(238 * proof)), (83, 132, 153, int(245 * proof)), 2)
        text(d, (145, 582), "TECHNICAL PROOF", 20, (155, 188, 200, int(255 * proof)), "la", "cond", True)
        ci = stats["collector"]["win_rate_ci95"]
        lines = [
            "•  3,772 wins of 10,000 seeded games",
            f"•  95% Wilson CI: {ci['lower']*100:.2f}%–{ci['upper']*100:.2f}%",
            "•  Collector vs Aggressive Builder: Holm-adjusted p < 1×10⁻³⁰",
            f"•  Master seed {summary['master_seed']} • Representative game 8,721",
        ]
        for i, line in enumerate(lines):
            text(d, (145, 636 + i * 42), line, 24, (228, 235, 229, int(255 * proof)), "la", "sans")
    disclaimer = ease_out(clamp((at - 57.75) / .35))
    if disclaimer > 0:
        rounded(d, (105, 844, 975, 940), 13, (18, 22, 26, int(230 * disclaimer)), (127, 135, 139, int(210 * disclaimer)), 2)
        text(d, (540, 875), "DISCLAIMER", 18, (207, 211, 207, int(255 * disclaimer)), "mm", "cond", True)
        text(d, (540, 911), "Educational simulation—not financial advice. Results depend on modeled rules and settings.", 20, (226, 229, 224, int(255 * disclaimer)), "mm", "sans")
    text(d, (540, 1017), "A reproducible result grounded in the full tournament.", 27, (246, 246, 238, 255), "mm", "serif")
    return frame.convert("RGB")


def render(frame_index: int) -> Image.Image:
    if not 0 <= frame_index < FRAMES:
        raise IndexError(frame_index)
    t = frame_index / FPS
    if t < 7: return render_cold(t)
    if t < 14: return render_strategies(t)
    if t < 31: return render_story(t)
    if t < 39: return render_scale(t)
    if t < 50: return render_leaderboard(t)
    if t < 55: return render_risk(t)
    return render_result(t)


CONTACT_TIMES = [0.30, .90, 1.60, 2.60, 3.60, 4.70, 5.70, 6.50,
                 7.80, 10.20, 13.00, 15.50, 18.50, 21.00, 24.50, 28.80,
                 37.20, 43.80, 52.00, 59.00]


def make_contact_sheet() -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1080, 1350), (2, 8, 13))
    d = ImageDraw.Draw(sheet)
    for i, sec in enumerate(CONTACT_TIMES):
        im = render(min(FRAMES - 1, int(sec * FPS))).resize((270, 270), Image.Resampling.LANCZOS)
        x = (i % 4) * 270; y = (i // 4) * 270
        sheet.paste(im, (x, y))
        d.rectangle((x, y, x + 82, y + 26), fill=(0, 0, 0))
        text(d, (x + 8, y + 13), f"{sec:04.1f}s", 14, (255, 216, 39), "lm", "cond", True)
    path = OUTPUTS / "project3_property_trading_cinematic_v3_contact_sheet.jpg"
    sheet.save(path, quality=95, subsampling=0)
    return path


def encode_video() -> Path:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    target = OUTPUTS / "project3_property_trading_cinematic_v3_60s.mp4"
    cmd = [str(FFMPEG), "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
           "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-frames:v", str(FRAMES),
           "-movflags", "+faststart", str(target)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for i in range(FRAMES):
        proc.stdin.write(render(i).tobytes())
        if i % 150 == 0:
            print(f"rendered {i}/{FRAMES}", flush=True)
    proc.stdin.close()
    rc = proc.wait()
    if rc:
        raise SystemExit(rc)
    return target


def main() -> None:
    if "--contact-sheet" in sys.argv:
        print(make_contact_sheet())
        return
    target = encode_video()
    sheet = make_contact_sheet()
    print(target)
    print(sheet)


if __name__ == "__main__":
    main()
