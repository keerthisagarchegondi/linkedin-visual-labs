"""Read-only YAML loading with explicit root and Project 6 path containment."""

from __future__ import annotations

import stat
from pathlib import Path, PureWindowsPath

from pydantic import ValidationError

from linkedin_visual_labs.common.config import ConfigurationError, load_yaml_config
from linkedin_visual_labs.common.paths import ensure_path_within
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.models import (
    OUTPUT,
    PROCESSED,
    RAW,
    Contract,
    EvidenceReference,
    SourceCandidate,
    TrafficOperationsConfig,
)

CANONICAL_ROOT = Path("D:/linkedin-visual-labs-git/linkedin-visual-labs")
DEFAULT_CONFIG_PATH = Path("configs/p05_traffic_operations_early_warning.yaml")


def contained_path(root: Path, relative: str, allowed: Path) -> Path:
    """Check lexical paths and existing redirection before resolving; never mkdir."""
    windows = PureWindowsPath(relative)
    path = Path(relative)
    if (
        path.is_absolute()
        or windows.drive
        or windows.root
        or "\\" in relative
        or ":" in relative
        or ".." in path.parts
    ):
        raise ConfigurationError("expected a repository-relative contained path")
    if not path.is_relative_to(allowed):
        raise ConfigurationError("path belongs outside the approved area")
    current = root
    for part in ("", *path.parts):
        current = current / part
        if current.exists() or current.is_symlink():
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or (
                getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ConfigurationError("redirected path component rejected")
    return ensure_path_within(current, root / allowed)


def validate_references(model: Contract, root: Path) -> None:
    """Inspect typed references, not arbitrary strings that resemble filenames."""
    if isinstance(model, EvidenceReference):
        allowed = next(
            Path(area) for area in (RAW, PROCESSED, OUTPUT) if Path(model.path).is_relative_to(area)
        )
        contained_path(root, model.path, allowed)
    if isinstance(model, SourceCandidate) and model.raw_file_path is not None:
        contained_path(root, model.raw_file_path, Path(RAW))
    for name in type(model).model_fields:
        value = getattr(model, name)
        if isinstance(value, Contract):
            validate_references(value, root)
        elif isinstance(value, tuple):
            for item in value:
                if isinstance(item, Contract):
                    validate_references(item, root)


def load_traffic_config(
    path: Path | str = DEFAULT_CONFIG_PATH,
    *,
    repository_root: Path = CANONICAL_ROOT,
) -> TrafficOperationsConfig:
    """Use an explicit root (injectable for fixtures); never discover another clone.

    Pydantic normalizes only declared enum strings and list-to-tuple fields.
    Numeric fields remain strict. File existence is not source approval.
    """
    if not repository_root.is_absolute():
        raise ConfigurationError("repository_root must be explicit and absolute")
    try:
        config_path = contained_path(repository_root, Path(path).as_posix(), Path("configs"))
        model = TrafficOperationsConfig.model_validate(load_yaml_config(config_path))
        for area in (RAW, PROCESSED, OUTPUT):
            contained_path(repository_root, area, Path(area))
        validate_references(model, repository_root)
        return model
    except (ValidationError, ValueError, OSError) as error:
        raise ConfigurationError(f"invalid Project 6 configuration: {error}") from error
