"""Frozen Project 7 Step 6 visual design tokens."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, cast

type RGB = tuple[int, int, int]
type RGBA = tuple[int, int, int, int]

PACKAGE: Final = "p27_prediction_time_integrity_auditor"

EXPECTED_CONTRACT_SHA256: Final = "1458c71f6853afddae5a0da7a73870ba3230eee2144daf5189b6ca207f280469"


@dataclass(frozen=True, slots=True)
class CanvasContract:
    width_px: int
    height_px: int
    fps: int
    duration_seconds: float
    render_scale: float

    @property
    def internal_width_px(self) -> int:
        return round(self.width_px * self.render_scale)

    @property
    def internal_height_px(self) -> int:
        return round(self.height_px * self.render_scale)


@dataclass(frozen=True, slots=True)
class TypographyStyle:
    role: str
    font_file: str
    size_px: int
    line_height_px: int
    tracking_em: float
    uppercase: bool
    max_width_px: int | None
    max_lines: int | None

    @property
    def tracking_px(self) -> float:
        return self.size_px * self.tracking_em


@dataclass(frozen=True, slots=True)
class StatusStyle:
    fill: str
    border: str
    text: str


def repository_root() -> Path:
    current = Path(__file__).resolve()

    for parent in current.parents:
        if (parent / "pyproject.toml").is_file() and (parent / "src").is_dir():
            return parent

    raise RuntimeError("Repository root not found.")


def contract_path() -> Path:
    return repository_root() / "assets" / PACKAGE / "style" / "p27_step6_visual_contract.json"


def contract_sha256() -> str:
    return hashlib.sha256(contract_path().read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def load_visual_contract() -> Mapping[str, Any]:
    path = contract_path()

    digest = contract_sha256()

    if digest != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError(f"Visual-contract checksum drift: {digest}")

    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload["meta"]["contract_version"] != "1.0":
        raise RuntimeError("Visual-contract version drift.")

    return cast(
        Mapping[str, Any],
        payload,
    )


def canvas_contract() -> CanvasContract:
    contract = load_visual_contract()

    canvas = contract["canvas"]
    aa = contract["effects"]["antialiasing"]

    result = CanvasContract(
        width_px=int(canvas["width_px"]),
        height_px=int(canvas["height_px"]),
        fps=int(canvas["fps"]),
        duration_seconds=float(canvas["duration_seconds"]),
        render_scale=float(aa["render_scale"]),
    )

    if result.internal_width_px != int(aa["internal_width_px"]):
        raise RuntimeError("Internal width drift.")

    if result.internal_height_px != int(aa["internal_height_px"]):
        raise RuntimeError("Internal height drift.")

    return result


def typography_style(role: str) -> TypographyStyle:
    raw = load_visual_contract()["typography"].get(role)

    if not isinstance(raw, Mapping):
        raise KeyError(role)

    font_file = raw.get("font_file")

    if not isinstance(font_file, str):
        raise RuntimeError(f"No font_file for typography role {role!r}.")

    return TypographyStyle(
        role=role,
        font_file=font_file,
        size_px=int(raw["size_px"]),
        line_height_px=int(raw["line_height_px"]),
        tracking_em=float(raw.get("tracking_em", 0.0)),
        uppercase=bool(raw.get("uppercase", False)),
        max_width_px=(int(raw["max_width_px"]) if raw.get("max_width_px") is not None else None),
        max_lines=(int(raw["max_lines"]) if raw.get("max_lines") is not None else None),
    )


def font_path_for_role(role: str) -> Path:
    style = typography_style(role)

    path = repository_root() / style.font_file

    if not path.is_file():
        raise RuntimeError(f"Frozen font missing: {path}")

    return path


def palette_color(name: str) -> str:
    value = load_visual_contract()["palette"].get(name)

    if not isinstance(value, str):
        raise KeyError(name)

    return value


def hex_to_rgb(value: str) -> RGB:
    value = value.strip()

    if len(value) != 7 or not value.startswith("#"):
        raise ValueError(value)

    return (
        int(value[1:3], 16),
        int(value[3:5], 16),
        int(value[5:7], 16),
    )


def hex_to_rgba(
    value: str,
    alpha: int = 255,
) -> RGBA:
    if not 0 <= alpha <= 255:
        raise ValueError(alpha)

    r, g, b = hex_to_rgb(value)

    return r, g, b, alpha


def scale_value(
    value: int | float,
) -> int:
    return round(float(value) * canvas_contract().render_scale)


def scale_box(
    box: Sequence[int | float],
) -> tuple[int, int, int, int]:
    if len(box) != 4:
        raise ValueError("Expected four coordinates.")

    return (
        scale_value(box[0]),
        scale_value(box[1]),
        scale_value(box[2]),
        scale_value(box[3]),
    )


def status_style(
    status: str,
) -> StatusStyle:
    raw = load_visual_contract()["status_pills"].get(status.lower())

    if not isinstance(raw, Mapping):
        raise KeyError(status)

    return StatusStyle(
        fill=str(raw["fill"]),
        border=str(raw["border"]),
        text=str(raw["text"]),
    )


def scene_contract(
    scene_id: str,
) -> Mapping[str, Any]:
    matches = [
        item for item in load_visual_contract()["scene_sequence"] if item["scene_id"] == scene_id
    ]

    if len(matches) != 1:
        raise KeyError(scene_id)

    return cast(
        Mapping[str, Any],
        matches[0],
    )


def frozen_scene_ids() -> tuple[str, ...]:
    return tuple(str(item["scene_id"]) for item in load_visual_contract()["scene_sequence"])


def scene_duration_total() -> float:
    return sum(float(item["duration_s"]) for item in load_visual_contract()["scene_sequence"])
