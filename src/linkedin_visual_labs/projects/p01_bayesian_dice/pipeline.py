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
        """Return temporary legacy single-die output-file paths."""
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

    def pair_output_files(self) -> dict[str, Path]:
        """Return authoritative safe absolute pair-experiment output paths."""
        project_output_root = self._project_output_root()

        preview_directory = (project_output_root / "previews").resolve()

        if preview_directory.parent != project_output_root:
            raise RuntimeError("preview directory escaped Project 1 output root")

        return {
            "simulation": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "pair_simulation.json",
                repository_root=self.repository_root,
            ),
            "history": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "pair_case_histories.csv",
                repository_root=self.repository_root,
            ),
            "summary": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "pair_case_summary.json",
                repository_root=self.repository_root,
            ),
            "validation": safe_project_output_path(
                self.configuration.project_id,
                "data",
                "pair_validation.json",
                repository_root=self.repository_root,
            ),
            "preview_directory": preview_directory,
            "video": safe_project_output_path(
                self.configuration.project_id,
                "video",
                "how_many_rolls_loaded_dice_pair.mp4",
                repository_root=self.repository_root,
            ),
            "manifest": safe_project_output_path(
                self.configuration.project_id,
                "manifests",
                "how_many_rolls_loaded_dice_pair.json",
                repository_root=self.repository_root,
            ),
        }

    def _project_output_root(self) -> Path:
        """Resolve Project 1's validated output root via a shared category."""
        anchor = safe_project_output_path(
            self.configuration.project_id,
            "data",
            ".path-anchor",
            repository_root=self.repository_root,
        )

        project_output_root = (anchor.parent.parent).resolve()

        expected_root = (self.repository_root / "outputs" / self.configuration.project_id).resolve()

        if project_output_root != expected_root:
            raise RuntimeError("resolved Project 1 output root differs from expected root")

        return project_output_root


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
