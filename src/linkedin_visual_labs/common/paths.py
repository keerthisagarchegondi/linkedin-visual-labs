"""Repository and generated-output path management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.common.validation import (
    ValidationError,
    validate_project_id,
)

OUTPUT_CATEGORIES = (
    "data",
    "images",
    "video",
    "manifests",
)


class RepositoryRootNotFoundError(RuntimeError):
    """Raised when the repository root cannot be discovered."""


class UnsafeOutputPathError(ValidationError):
    """Raised when a requested output path escapes its allowed directory."""


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Canonical generated-output directories for one project."""

    repository_root: Path
    project_id: str
    output_root: Path
    data: Path
    images: Path
    video: Path
    manifests: Path

    def category(self, name: str) -> Path:
        """Return the path belonging to a supported output category."""
        categories = {
            "data": self.data,
            "images": self.images,
            "video": self.video,
            "manifests": self.manifests,
        }

        try:
            return categories[name]
        except KeyError as exc:
            allowed = ", ".join(OUTPUT_CATEGORIES)
            raise ValidationError(
                f"unsupported output category {name!r}; allowed: {allowed}"
            ) from exc

    def create(self) -> ProjectPaths:
        """Create all canonical generated-output directories."""
        for path in (
            self.output_root,
            self.data,
            self.images,
            self.video,
            self.manifests,
        ):
            path.mkdir(parents=True, exist_ok=True)

        return self


def _looks_like_repository_root(path: Path) -> bool:
    return (path / "pyproject.toml").is_file() and (path / "src" / "linkedin_visual_labs").is_dir()


def _search_parents(start: Path) -> Path | None:
    candidate = start.resolve()

    if candidate.is_file():
        candidate = candidate.parent

    for directory in (candidate, *candidate.parents):
        if _looks_like_repository_root(directory):
            return directory

    return None


def discover_repository_root(start: Path | str | None = None) -> Path:
    """Discover the LinkedIn Visual Labs repository root.

    Search begins at ``start`` when supplied, otherwise at the current
    working directory. If the current working directory is outside the
    repository, the installed source-module location is used as a fallback.
    """
    primary_start = Path.cwd() if start is None else Path(start)

    discovered = _search_parents(primary_start)

    if discovered is not None:
        return discovered

    if start is None:
        module_start = Path(__file__)
        discovered = _search_parents(module_start)

        if discovered is not None:
            return discovered

    raise RepositoryRootNotFoundError(
        f"could not discover repository root from {primary_start.resolve()}"
    )


def build_project_paths(
    project_id: str,
    *,
    repository_root: Path | str | None = None,
    create: bool = True,
) -> ProjectPaths:
    """Build canonical generated-output paths for a project."""
    canonical_project_id = validate_project_id(project_id)

    root = (
        discover_repository_root() if repository_root is None else Path(repository_root).resolve()
    )

    if not _looks_like_repository_root(root):
        raise RepositoryRootNotFoundError(
            f"not a valid LinkedIn Visual Labs repository root: {root}"
        )

    output_root = root / "outputs" / canonical_project_id

    paths = ProjectPaths(
        repository_root=root,
        project_id=canonical_project_id,
        output_root=output_root,
        data=output_root / "data",
        images=output_root / "images",
        video=output_root / "video",
        manifests=output_root / "manifests",
    )

    if create:
        paths.create()

    return paths


def ensure_path_within(
    candidate: Path | str,
    allowed_root: Path | str,
) -> Path:
    """Require a path to remain inside an allowed directory."""
    candidate_path = Path(candidate).resolve()
    root_path = Path(allowed_root).resolve()

    try:
        candidate_path.relative_to(root_path)
    except ValueError as exc:
        raise UnsafeOutputPathError(
            f"output path escapes allowed directory: {candidate_path}"
        ) from exc

    return candidate_path


def safe_project_output_path(
    project_id: str,
    category: str,
    relative_path: Path | str,
    *,
    repository_root: Path | str | None = None,
    create_parent: bool = True,
) -> Path:
    """Create a safe path beneath one project's output category.

    Absolute paths and path traversal outside the requested project output
    category are rejected.
    """
    relative = Path(relative_path)

    if relative.is_absolute():
        raise UnsafeOutputPathError("relative_path must be relative, not absolute")

    if str(relative) in {"", "."}:
        raise UnsafeOutputPathError("relative_path must identify a file or nested output path")

    paths = build_project_paths(
        project_id,
        repository_root=repository_root,
        create=True,
    )

    category_root = paths.category(category).resolve()
    candidate = (category_root / relative).resolve()

    ensure_path_within(candidate, category_root)

    if candidate == category_root:
        raise UnsafeOutputPathError("relative_path must not resolve to the category root")

    if create_parent:
        candidate.parent.mkdir(parents=True, exist_ok=True)

    return candidate
