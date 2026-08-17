"""Pipeline context scaffolding for Bayesian Dice Detective."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from linkedin_visual_labs.common.paths import (
    ProjectPaths,
    build_project_paths,
    discover_repository_root,
    safe_project_output_path,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.config import (
    DEFAULT_CONFIG_PATH,
    load_dice_config,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    DiceProjectConfig,
)


@dataclass(frozen=True, slots=True)
class DicePipelineContext:
    """Resolved configuration and repository paths for Project 1."""

    configuration: DiceProjectConfig
    repository_root: Path
    project_paths: ProjectPaths

    def output_files(self) -> dict[str, Path]:
        """Return canonical safe absolute output-file paths."""
        return {
            "simulation": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "simulation.json",
                repository_root=self.repository_root,
            ),
            "posterior_history": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "posterior_history.csv",
                repository_root=self.repository_root,
            ),
            "validation": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "validation.json",
                repository_root=self.repository_root,
            ),
            "video": safe_project_output_path(
                self.configuration.project_id,
                "video",
                "can_ai_tell_loaded_die.mp4",
                repository_root=self.repository_root,
            ),
            "manifest": safe_project_output_path(
                self.configuration.project_id,
                "manifests",
                "can_ai_tell_loaded_die.json",
                repository_root=self.repository_root,
            ),
        }


def build_pipeline_context(
    configuration_path: Path | str = DEFAULT_CONFIG_PATH,
) -> DicePipelineContext:
    """Load configuration and resolve canonical Project 1 paths."""
    repository_root = discover_repository_root()

    configuration = load_dice_config(configuration_path)

    project_paths = build_project_paths(
        configuration.project_id,
        repository_root=repository_root,
        create=True,
    )

    return DicePipelineContext(
        configuration=configuration,
        repository_root=repository_root,
        project_paths=project_paths,
    )
