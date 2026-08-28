"""Project 3 polished rendered-3D strategy-piece pipeline.

The base artwork comes from Microsoft's MIT-licensed Fluent Emoji 3D
rendered PNG assets.

Project 3 transforms the source artwork deterministically into a
metallic-silver game-piece treatment while preserving the original 3D
lighting, shading, contours, and alpha transparency.

No Blender runtime is required.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import (
    Image,
    ImageEnhance,
    ImageFilter,
)

PIECE_NAMES = {
    "collector": "silver_sports_coupe",
    "specialist": "silver_yacht",
    "cash_protector": "silver_armored_vault",
    "aggressive_builder": "silver_construction_loader",
}


SOURCE_MANIFEST = Path("assets/p02_monopoly_ai/fluent_3d_manifest.json")


OUTPUT_SIZE = 768


STRATEGY_ACCENTS = {
    "collector": (
        0,
        119,
        182,
    ),
    "specialist": (
        166,
        30,
        105,
    ),
    "cash_protector": (
        4,
        120,
        87,
    ),
    "aggressive_builder": (
        198,
        93,
        0,
    ),
}


def load_source_images() -> dict[
    str,
    Path,
]:
    """Return the four frozen Fluent Emoji source PNGs."""

    if not SOURCE_MANIFEST.is_file():
        raise FileNotFoundError(SOURCE_MANIFEST)

    raw = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))

    if not isinstance(
        raw,
        dict,
    ):
        raise ValueError("Fluent asset manifest must be a JSON object")

    assets = raw.get("assets")

    if not isinstance(
        assets,
        dict,
    ):
        raise ValueError("Fluent asset manifest has no assets object")

    result: dict[
        str,
        Path,
    ] = {}

    for strategy in PIECE_NAMES:
        raw_path = assets.get(strategy)

        if not isinstance(
            raw_path,
            str,
        ):
            raise ValueError(f"missing source asset for {strategy}")

        source = Path(raw_path)

        if not source.is_file():
            raise FileNotFoundError(source)

        result[strategy] = source

    return result


def _content_bbox(
    alpha: Image.Image,
) -> tuple[
    int,
    int,
    int,
    int,
]:
    bbox = alpha.getbbox()

    if bbox is None:
        raise ValueError("source sprite has no visible pixels")

    return bbox


def _crop_and_pad(
    image: Image.Image,
) -> Image.Image:
    """Normalize visible-object scale across all four source sprites."""

    rgba = image.convert("RGBA")

    bbox = _content_bbox(rgba.getchannel("A"))

    visible = rgba.crop(bbox)

    width, height = visible.size

    longest = max(
        width,
        height,
    )

    padding = int(longest * 0.14)

    canvas_size = longest + padding * 2

    canvas = Image.new(
        "RGBA",
        (
            canvas_size,
            canvas_size,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    x = (canvas_size - width) // 2

    y = (canvas_size - height) // 2

    canvas.alpha_composite(
        visible,
        (
            x,
            y,
        ),
    )

    return canvas.resize(
        (
            OUTPUT_SIZE,
            OUTPUT_SIZE,
        ),
        Image.Resampling.LANCZOS,
    )


def _metallic_luminance(
    image: Image.Image,
) -> Image.Image:
    """Map existing 3D shading into a polished silver tonal range."""

    rgba = image.convert("RGBA")

    array = np.asarray(
        rgba,
        dtype=np.float32,
    )

    rgb = array[:, :, :3]

    alpha = array[:, :, 3:]

    luminance = (0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]) / 255.0

    # Preserve source 3D lighting but compress it into
    # a die-cast silver tonal range.
    shaped = np.clip(
        luminance,
        0.0,
        1.0,
    )

    shaped = np.power(
        shaped,
        0.82,
    )

    dark = np.array(
        [
            74.0,
            82.0,
            92.0,
        ],
        dtype=np.float32,
    )

    bright = np.array(
        [
            244.0,
            247.0,
            250.0,
        ],
        dtype=np.float32,
    )

    silver = dark[None, None, :] + (bright - dark)[None, None, :] * shaped[:, :, None]

    # Slight cool highlight bias.
    silver[:, :, 2] = np.clip(
        silver[:, :, 2] * 1.025,
        0.0,
        255.0,
    )

    output = np.concatenate(
        (
            silver,
            alpha,
        ),
        axis=2,
    )

    return Image.fromarray(
        np.clip(
            output,
            0.0,
            255.0,
        ).astype(np.uint8),
        mode="RGBA",
    )


def _add_ground_shadow(
    image: Image.Image,
) -> Image.Image:
    """Add subtle miniature-object grounding without flattening sprite."""

    alpha = image.getchannel("A")

    bbox = alpha.getbbox()

    if bbox is None:
        return image

    left, _top, right, bottom = bbox

    width = right - left

    shadow_height = max(
        12,
        int(width * 0.085),
    )

    shadow = Image.new(
        "RGBA",
        image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    shadow_alpha = Image.new(
        "L",
        image.size,
        0,
    )

    ellipse = Image.new(
        "L",
        (
            max(
                1,
                int(width * 0.72),
            ),
            shadow_height,
        ),
        110,
    )

    ellipse = ellipse.filter(
        ImageFilter.GaussianBlur(
            radius=max(
                3.0,
                shadow_height * 0.22,
            )
        )
    )

    shadow_x = left + (width - ellipse.width) // 2

    shadow_y = min(
        image.height - ellipse.height,
        bottom - ellipse.height // 3,
    )

    shadow_alpha.paste(
        ellipse,
        (
            shadow_x,
            shadow_y,
        ),
    )

    shadow.putalpha(shadow_alpha)

    result = Image.new(
        "RGBA",
        image.size,
        (
            0,
            0,
            0,
            0,
        ),
    )

    result.alpha_composite(shadow)

    result.alpha_composite(image)

    return result


def _add_accent_badge(
    image: Image.Image,
    *,
    strategy: str,
) -> Image.Image:
    """Small color identity mark while leaving body metallic silver."""

    accent = STRATEGY_ACCENTS[strategy]

    result = image.copy()

    badge_size = 50

    badge = Image.new(
        "RGBA",
        (
            badge_size,
            badge_size,
        ),
        (
            0,
            0,
            0,
            0,
        ),
    )

    yy, xx = np.ogrid[
        :badge_size,
        :badge_size,
    ]

    center = (badge_size - 1) / 2.0

    radius = badge_size * 0.37

    mask = (xx - center) ** 2 + (yy - center) ** 2 <= radius**2

    data = np.zeros(
        (
            badge_size,
            badge_size,
            4,
        ),
        dtype=np.uint8,
    )

    data[mask, 0] = accent[0]

    data[mask, 1] = accent[1]

    data[mask, 2] = accent[2]

    data[mask, 3] = 245

    badge = Image.fromarray(
        data,
        mode="RGBA",
    )

    x = result.width - badge_size - 34

    y = result.height - badge_size - 34

    result.alpha_composite(
        badge,
        (
            x,
            y,
        ),
    )

    return result


def render_piece_asset(
    strategy_id: str,
    path: Path,
) -> None:
    """Create one polished silver rendered-3D sprite."""

    sources = load_source_images()

    if strategy_id not in sources:
        raise ValueError(f"unknown strategy: {strategy_id}")

    with Image.open(sources[strategy_id]) as source_image:
        normalized = _crop_and_pad(source_image)

    metallic = _metallic_luminance(normalized)

    metallic = ImageEnhance.Contrast(metallic).enhance(1.12)

    metallic = ImageEnhance.Sharpness(metallic).enhance(1.18)

    grounded = _add_ground_shadow(metallic)

    final = _add_accent_badge(
        grounded,
        strategy=strategy_id,
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final.save(
        path,
        format="PNG",
        optimize=False,
        compress_level=9,
    )

    if path.stat().st_size < 10_000:
        raise RuntimeError(f"rendered sprite too small: {path}")


def render_all_piece_assets(
    output_directory: Path,
    *,
    show_progress: bool = True,
) -> dict[
    str,
    Path,
]:
    """Render all four frozen strategy sprites."""

    result: dict[
        str,
        Path,
    ] = {}

    for index, (
        strategy,
        asset_name,
    ) in enumerate(
        PIECE_NAMES.items(),
        start=1,
    ):
        if show_progress:
            print(
                f"[3D SPRITE] {index}/4 {strategy}",
                flush=True,
            )

        path = output_directory / (asset_name + ".png")

        render_piece_asset(
            strategy,
            path,
        )

        result[strategy] = path

    return result


def ensure_piece_assets(
    output_directory: Path,
) -> dict[
    str,
    Path,
]:
    """Return the rendered sprites, generating them if necessary."""

    result = {
        strategy: (output_directory / (asset_name + ".png"))
        for strategy, asset_name in PIECE_NAMES.items()
    }

    if all(path.is_file() and path.stat().st_size >= 10_000 for path in result.values()):
        return result

    return render_all_piece_assets(
        output_directory,
        show_progress=False,
    )
