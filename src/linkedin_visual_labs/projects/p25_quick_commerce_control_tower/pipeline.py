"""Validated project context shared by analytical and release orchestration stages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from numpy.random import Generator

from linkedin_visual_labs.common.paths import (
    ProjectPaths,
    UnsafeOutputPathError,
    build_project_paths,
    discover_repository_root,
    ensure_path_within,
)
from linkedin_visual_labs.common.random_state import create_namespaced_rng
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    DEFAULT_CONFIG_PATH,
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import (
    PROJECT_ID,
    CommerceConfig,
)


@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Validated settings and safe, uncreated output locations."""

    configuration: CommerceConfig
    paths: ProjectPaths

    def resolve_output_path(self, relative_path: Path | str) -> Path:
        """Resolve a project-relative output file without creating it."""
        relative = Path(relative_path)
        if relative.is_absolute() or relative == Path("."):
            raise UnsafeOutputPathError("output must be a relative file path")
        resolved = ensure_path_within(self.paths.output_root / relative, self.paths.output_root)
        if resolved == self.paths.output_root:
            raise UnsafeOutputPathError("output must identify a file")
        return resolved

    def create_rng(self, namespace: str) -> Generator:
        """Return a fresh repeatable RNG using the shared namespaced seed utility."""
        return create_namespaced_rng(self.configuration.seed, f"{PROJECT_ID}:{namespace}")


def build_pipeline_context(
    config_path: Path | str = DEFAULT_CONFIG_PATH,
    *,
    repository_root: Path | str | None = None,
) -> PipelineContext:
    """Validate configuration and paths, without data access or output creation."""
    root = (
        discover_repository_root() if repository_root is None else Path(repository_root).resolve()
    )
    config = load_commerce_config(config_path, repository_root=root)
    paths = build_project_paths(PROJECT_ID, repository_root=root, create=False)
    for configured_path in config.paths.model_dump().values():
        ensure_path_within(root / configured_path, root)
    return PipelineContext(configuration=config, paths=paths)
