"""Structural PNG measurements supporting, never replacing, visual review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from .design_system import BG, HEADER, LIGHT


def palette_contains(colors: list[str], target: str) -> bool:
    """Allow three RGB levels for browser color conversion, not theme differences."""
    rgb = tuple(int(target[i : i + 2], 16) for i in (1, 3, 5))
    return any(
        max(abs(int(color[i : i + 2], 16) - value) for i, value in zip((1, 3, 5), rgb, strict=True))
        <= 3
        for color in colors
    )


def region_stats(path: Path, box: tuple[int, int, int, int]) -> dict[str, Any]:
    with Image.open(path) as image:
        pixels = np.asarray(image.convert("RGB").crop(box), dtype=np.int16)
    flat = pixels.reshape(-1, 3)
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    order = np.argsort(counts)[-5:][::-1]
    luminance = flat @ np.array([0.2126, 0.7152, 0.0722])
    return {
        "dominant": ["#" + "".join(f"{v:02X}" for v in colors[i]) for i in order],
        "brightness": float(luminance.mean()),
        "bright_fraction": float((luminance > 180).mean()),
        "edge_density": float((np.abs(np.diff(pixels, axis=0)).max(axis=2) > 35).mean()),
    }


def compare(reference: Path, actual: Path, *, video: bool) -> dict[str, Any]:
    """Exclude rights-restricted photographic hero pixels from palette acceptance."""
    boxes = (
        {"header": (0, 0, 1080, 103), "caption": (0, 851, 1080, 1245)}
        if video
        else {"canvas": (0, 153, 1600, 1000), "header": (0, 48, 1600, 153)}
    )
    stats = {
        name: {"reference": region_stats(reference, box), "actual": region_stats(actual, box)}
        for name, box in boxes.items()
    }
    token = BG if video else LIGHT
    body = stats["caption" if video else "canvas"]
    palette = palette_contains(body["reference"]["dominant"], token) and palette_contains(
        body["actual"]["dominant"], token
    )
    header = not video or HEADER in stats["header"]["actual"]["dominant"]
    with Image.open(actual) as im:
        dimensions = im.size == ((1080, 1350) if video else (1600, 1000))
    return {
        "reference": reference.name,
        "actual": actual.name,
        "regions": stats,
        "checks": {"dimensions": dimensions, "sampled_palette": palette, "header": header},
        "automated_status": "PASS" if dimensions and palette and header else "REQUIRES_REPAIR",
        "visual_review_required": True,
        "limitations": "Palette and region diagnostics are not perceptual certification. "
        "Reviewer must assess panel arrangement, typography, rights substitutions and overflow.",
    }
