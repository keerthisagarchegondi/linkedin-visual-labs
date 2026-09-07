"""Load typed Project 5 settings using shared YAML and repository utilities."""

from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError as PydanticValidationError

from linkedin_visual_labs.common.config import ConfigurationError, load_yaml_config
from linkedin_visual_labs.common.paths import discover_repository_root, ensure_path_within
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig

DEFAULT_CONFIG_PATH = Path("configs/p25_quick_commerce_control_tower.yaml")


def load_commerce_config(
    path: Path | str = DEFAULT_CONFIG_PATH,
    *,
    repository_root: Path | str | None = None,
) -> CommerceConfig:
    """Resolve repository-relative settings without creating any output directories."""
    root = (
        discover_repository_root() if repository_root is None else Path(repository_root).resolve()
    )
    config_path = ensure_path_within(root / Path(path), root)
    raw = load_yaml_config(config_path)
    try:
        return CommerceConfig.model_validate(raw)
    except PydanticValidationError as exc:
        raise ConfigurationError(f"invalid commerce configuration: {exc}") from exc
