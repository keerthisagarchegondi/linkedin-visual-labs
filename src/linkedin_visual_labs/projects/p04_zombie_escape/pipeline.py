"""Pipeline context for Project 2 — Zombie Escape."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape.config import (
    DEFAULT_CONFIG_PATH,
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    OutputDefinition,
    ZombieConfigError,
    ZombieProjectConfig,
)


@dataclass(frozen=True, slots=True)
class ZombiePipelineContext:
    """Resolved Project 2 execution context."""

    repository_root: Path
    config_path: Path
    configuration: ZombieProjectConfig

    @property
    def outputs(self) -> OutputDefinition:
        """Return canonical generated-output locations."""
        return self.configuration.outputs

    def resolve_output_path(
        self,
        relative_output_path: Path,
    ) -> Path:
        """Resolve one validated Project-2 output path against the repo."""
        try:
            relative_output_path.relative_to(self.configuration.outputs.root)
        except ValueError as exc:
            raise ZombieConfigError(
                f"Output path is outside the Project 2 output root: {relative_output_path}"
            ) from exc

        return self.repository_root / relative_output_path


def build_pipeline_context(
    *,
    repository_root: Path | str | None = None,
    config_path: Path | str = DEFAULT_CONFIG_PATH,
) -> ZombiePipelineContext:
    """Build the typed deterministic Project 2 pipeline context."""
    root = (Path.cwd() if repository_root is None else Path(repository_root)).resolve()

    requested_config = Path(config_path)

    resolved_config = (
        requested_config if requested_config.is_absolute() else (root / requested_config)
    )

    configuration = load_zombie_config(resolved_config)

    return ZombiePipelineContext(
        repository_root=root,
        config_path=resolved_config,
        configuration=configuration,
    )
