"""Deterministic image and camera motion primitives."""

from __future__ import annotations

import math

from PIL import Image


def clamp01(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            value,
        ),
    )


def lerp(
    start: float,
    end: float,
    progress: float,
) -> float:
    t = clamp01(progress)

    return start + (end - start) * t


def ease_in_out_cubic(
    progress: float,
) -> float:
    t = clamp01(progress)

    if t < 0.5:
        return 4.0 * t * t * t

    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def ease_out_cubic(
    progress: float,
) -> float:
    t = clamp01(progress)

    return 1.0 - (1.0 - t) ** 3


def ease_out_back(
    progress: float,
) -> float:
    t = clamp01(progress)

    c1 = 1.70158

    c3 = c1 + 1.0

    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


def lift_height(
    progress: float,
    *,
    maximum: float,
) -> float:
    """Parabolic lift/carry/drop height."""

    t = clamp01(progress)

    return 4.0 * maximum * t * (1.0 - t)


def camera_zoom(
    image: Image.Image,
    *,
    zoom: float,
    pan_x: float = 0.0,
    pan_y: float = 0.0,
    output_size: tuple[int, int] = (
        1080,
        1080,
    ),
) -> Image.Image:
    """Apply deterministic center zoom and normalized camera pan."""

    source = image.convert("RGB")

    width, height = source.size

    safe_zoom = max(
        1.0,
        zoom,
    )

    crop_width = width / safe_zoom

    crop_height = height / safe_zoom

    max_pan_x = (width - crop_width) / 2.0

    max_pan_y = (height - crop_height) / 2.0

    center_x = (
        width / 2.0
        + max(
            -1.0,
            min(
                1.0,
                pan_x,
            ),
        )
        * max_pan_x
    )

    center_y = (
        height / 2.0
        + max(
            -1.0,
            min(
                1.0,
                pan_y,
            ),
        )
        * max_pan_y
    )

    left = max(
        0.0,
        min(
            width - crop_width,
            center_x - crop_width / 2.0,
        ),
    )

    top = max(
        0.0,
        min(
            height - crop_height,
            center_y - crop_height / 2.0,
        ),
    )

    crop = source.crop(
        (
            round(left),
            round(top),
            round(left + crop_width),
            round(top + crop_height),
        )
    )

    return crop.resize(
        output_size,
        Image.Resampling.LANCZOS,
    )


def crossfade(
    first: Image.Image,
    second: Image.Image,
    progress: float,
) -> Image.Image:
    t = clamp01(progress)

    left = first.convert("RGB")

    right = second.convert("RGB")

    if left.size != right.size:
        right = right.resize(
            left.size,
            Image.Resampling.LANCZOS,
        )

    return Image.blend(
        left,
        right,
        t,
    )


def fade_from_black(
    image: Image.Image,
    progress: float,
) -> Image.Image:
    source = image.convert("RGB")

    black = Image.new(
        "RGB",
        source.size,
        (
            3,
            8,
            14,
        ),
    )

    return crossfade(
        black,
        source,
        progress,
    )


def fade_to_black(
    image: Image.Image,
    progress: float,
) -> Image.Image:
    return fade_from_black(
        image,
        1.0 - clamp01(progress),
    )


def reveal_left_to_right(
    image: Image.Image,
    progress: float,
    *,
    background: tuple[int, int, int] = (
        3,
        8,
        14,
    ),
) -> Image.Image:
    source = image.convert("RGB")

    width, height = source.size

    result = Image.new(
        "RGB",
        source.size,
        background,
    )

    visible_width = round(width * clamp01(progress))

    if visible_width > 0:
        piece = source.crop(
            (
                0,
                0,
                visible_width,
                height,
            )
        )

        result.paste(
            piece,
            (
                0,
                0,
            ),
        )

    return result


def reveal_top_to_bottom(
    image: Image.Image,
    progress: float,
    *,
    background: tuple[int, int, int] = (
        3,
        8,
        14,
    ),
) -> Image.Image:
    source = image.convert("RGB")

    width, height = source.size

    result = Image.new(
        "RGB",
        source.size,
        background,
    )

    visible_height = round(height * clamp01(progress))

    if visible_height > 0:
        piece = source.crop(
            (
                0,
                0,
                width,
                visible_height,
            )
        )

        result.paste(
            piece,
            (
                0,
                0,
            ),
        )

    return result


def pulse(
    progress: float,
    *,
    cycles: float = 1.0,
) -> float:
    t = clamp01(progress)

    return (math.sin(t * math.tau * cycles) + 1.0) / 2.0
