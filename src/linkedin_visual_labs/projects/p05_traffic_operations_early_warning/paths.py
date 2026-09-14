"""Explicit, immutable Project 6 paths; no discovery, creation or data access."""

from __future__ import annotations

import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import ClassVar

from linkedin_visual_labs.common.config import ConfigurationError

PROJECT_ID = "p05_traffic_operations_early_warning"


def _no_redirects(path: Path) -> None:
    """Inspect lexical components before following any symlink/reparse target."""
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ConfigurationError("redirected path component rejected")


def _relative(value: str) -> Path:
    path = Path(value)
    windows = PureWindowsPath(value)
    if (
        not value
        or value == "."
        or path.is_absolute()
        or windows.drive
        or windows.root
        or "\\" in value
        or ":" in value
        or ".." in path.parts
        or any(part.rstrip(" .") != part for part in path.parts)
    ):
        raise ConfigurationError("expected a nonempty contained relative path")
    return path


@dataclass(frozen=True, slots=True)
class TrafficPaths:
    """Trust only an explicitly injected checkout with matching package identity.

    A small fixture checkout may be injected. No parent search or fallback exists.
    Root identity checks read pyproject.toml only; storage checks inspect metadata.
    """

    repository_root: Path
    AREAS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("planning_config", f"configs/{PROJECT_ID}.yaml"),
        ("runtime_config", f"configs/{PROJECT_ID}/runtime.yaml"),
        ("raw", f"data/raw/{PROJECT_ID}"),
        ("processed", f"data/processed/{PROJECT_ID}"),
        ("output", f"outputs/{PROJECT_ID}"),
        ("data", f"outputs/{PROJECT_ID}/data"),
        ("images", f"outputs/{PROJECT_ID}/images"),
        ("videos", f"outputs/{PROJECT_ID}/videos"),
        ("report", f"outputs/{PROJECT_ID}/report"),
        ("manifests", f"outputs/{PROJECT_ID}/manifests"),
        ("weights", f"models/weights/{PROJECT_ID}"),
        ("model_cache", f"models/cache/{PROJECT_ID}"),
        ("cache", f".cache/{PROJECT_ID}"),
    )

    def __post_init__(self) -> None:
        root = self.repository_root
        lexical = root.as_posix().lower()
        prohibited = ("d:/linkedin-visual-labs", "/mnt/d/linkedin-visual-labs")
        if (
            not root.is_absolute()
            or PureWindowsPath(root).drive.startswith("\\\\")
            or ".." in root.parts
            or any(part.rstrip(" .") != part for part in root.parts[1:])
            or any(lexical == p or lexical.startswith(p + "/") for p in prohibited)
            or any(
                p.lower() in {"changegraph", "job_hunter", "my-portfolio-keerthi"}
                for p in root.parts
            )
        ):
            raise ConfigurationError("foreign or nonabsolute repository root rejected")
        _no_redirects(root / "pyproject.toml")
        _no_redirects(root / "src/linkedin_visual_labs")
        try:
            metadata = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
            project = metadata.get("project")
            if (
                not isinstance(project, dict)
                or project.get("name") != "linkedin-visual-labs"
                or not (root / "src/linkedin_visual_labs").is_dir()
            ):
                raise ConfigurationError("foreign checkout identity rejected")
        except (OSError, ValueError) as error:
            raise ConfigurationError(f"invalid explicit checkout: {error}") from error

    def area(self, name: str) -> Path:
        """Return one fixed Project 6 location without creating it."""
        try:
            relative = dict(self.AREAS)[name]
        except KeyError as error:
            raise ConfigurationError("unknown Project 6 path area") from error
        result = self.repository_root / relative
        _no_redirects(result)
        return result

    def child(self, area: str, relative: str) -> Path:
        """Build a contained storage child; config paths are fixed file locations."""
        if area in {"planning_config", "runtime_config"}:
            raise ConfigurationError("configuration locations cannot have children")
        result = self.area(area) / _relative(relative)
        _no_redirects(result)
        return result
