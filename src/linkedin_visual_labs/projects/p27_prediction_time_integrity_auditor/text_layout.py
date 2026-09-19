"""Deterministic text layout for Project 7 Step 6."""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

from PIL import ImageDraw, ImageFont

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.design_tokens import (
    TypographyStyle,
    canvas_contract,
    font_path_for_role,
    typography_style,
)


@lru_cache(maxsize=64)
def font_for_role(
    role: str,
    *,
    supersampled: bool = True,
) -> ImageFont.FreeTypeFont:
    style = typography_style(role)

    scale = canvas_contract().render_scale if supersampled else 1.0

    return ImageFont.truetype(
        str(font_path_for_role(role)),
        size=round(style.size_px * scale),
    )


def normalized_text(
    text: str,
    style: TypographyStyle,
) -> str:
    return text.upper() if style.uppercase else text


def tracking_px(
    style: TypographyStyle,
    *,
    supersampled: bool = True,
) -> float:
    scale = canvas_contract().render_scale if supersampled else 1.0

    return style.tracking_px * scale


def measure_tracked_text(
    text: str,
    *,
    role: str,
    supersampled: bool = True,
) -> float:
    style = typography_style(role)

    text = normalized_text(
        text,
        style,
    )

    if not text:
        return 0.0

    font = font_for_role(
        role,
        supersampled=supersampled,
    )

    width = float(font.getlength(text))

    width += max(0, len(text) - 1) * tracking_px(
        style,
        supersampled=supersampled,
    )

    return width


def draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    role: str,
    fill: str | tuple[int, int, int] | tuple[int, int, int, int],
    anchor: str = "la",
    supersampled: bool = True,
) -> tuple[float, float, float, float]:
    style = typography_style(role)

    value = normalized_text(
        text,
        style,
    )

    font = font_for_role(
        role,
        supersampled=supersampled,
    )

    tracking = tracking_px(
        style,
        supersampled=supersampled,
    )

    width = measure_tracked_text(
        value,
        role=role,
        supersampled=supersampled,
    )

    x, y = xy

    if anchor.startswith("m"):
        cursor = x - width / 2
        left = cursor
        right = x + width / 2
    elif anchor.startswith("r"):
        cursor = x - width
        left = cursor
        right = x
    else:
        cursor = x
        left = x
        right = x + width

    for index, char in enumerate(value):
        draw.text(
            (cursor, y),
            char,
            font=font,
            fill=fill,
            anchor="la",
        )

        cursor += float(font.getlength(char))

        if index < len(value) - 1:
            cursor += tracking

    scale = canvas_contract().render_scale if supersampled else 1.0

    return (
        left,
        y,
        right,
        y + style.line_height_px * scale,
    )


def _width(
    words: Iterable[str],
    *,
    role: str,
) -> float:
    return measure_tracked_text(
        " ".join(words),
        role=role,
        supersampled=False,
    )


def balanced_greedy_wrap(
    text: str,
    *,
    role: str,
    max_width_px: int,
    max_lines: int | None = None,
    min_words_on_last_line: int = 2,
) -> tuple[str, ...]:
    words = [word for word in text.split() if word]

    if not words:
        return ()

    lines: list[list[str]] = []
    current: list[str] = []

    for word in words:
        candidate = [
            *current,
            word,
        ]

        if (
            current
            and _width(
                candidate,
                role=role,
            )
            > max_width_px
        ):
            lines.append(current)
            current = [word]
        else:
            current = candidate

    if current:
        lines.append(current)

    if len(lines) >= 2 and len(lines[-1]) < min_words_on_last_line:
        previous = lines[-2]
        final = lines[-1]

        while len(final) < min_words_on_last_line and len(previous) > 1:
            candidate = [
                previous[-1],
                *final,
            ]

            if (
                _width(
                    candidate,
                    role=role,
                )
                > max_width_px
            ):
                break

            final.insert(
                0,
                previous.pop(),
            )

    result = tuple(" ".join(line) for line in lines)

    if max_lines is not None and len(result) > max_lines:
        raise ValueError(f"{len(result)} lines exceeds {max_lines}.")

    return result


def wrap_for_role(
    text: str,
    *,
    role: str,
) -> tuple[str, ...]:
    style = typography_style(role)

    if style.max_width_px is None:
        raise ValueError(f"No max width for {role!r}.")

    return balanced_greedy_wrap(
        text,
        role=role,
        max_width_px=style.max_width_px,
        max_lines=style.max_lines,
    )
