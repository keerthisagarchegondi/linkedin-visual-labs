"""Configuration loading for Project 2 — Zombie Escape."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    ZombieConfigError,
    ZombieProjectConfig,
)

DEFAULT_CONFIG_PATH = Path("configs/p04_zombie_escape.yaml")


def load_zombie_config(
    path: Path | str = DEFAULT_CONFIG_PATH,
) -> ZombieProjectConfig:
    """Load and validate the authoritative Project 2 YAML contract."""
    config_path = Path(path)

    if not config_path.is_file():
        raise ZombieConfigError(f"Zombie Escape config does not exist: {config_path}")

    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ZombieConfigError(f"Invalid Zombie Escape YAML: {config_path}") from exc

    if not isinstance(
        raw,
        dict,
    ):
        raise ZombieConfigError("Zombie Escape YAML root must be a mapping")

    return ZombieProjectConfig.from_mapping(raw)
