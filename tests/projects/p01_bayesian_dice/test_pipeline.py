"""Tests for Bayesian Dice pipeline context scaffolding."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p01_bayesian_dice.pipeline import (
    build_pipeline_context,
)


def test_pipeline_context_loads_project_configuration() -> None:
    context = build_pipeline_context()

    assert context.configuration.project_id == "p01_bayesian_dice"

    assert context.project_paths.project_id == "p01_bayesian_dice"

    assert context.repository_root.name == ("linkedin-visual-labs")


def test_pipeline_output_files_are_canonical() -> None:
    context = build_pipeline_context()

    outputs = context.output_files()

    expected_relative = {
        "simulation": Path("outputs/p01_bayesian_dice/data/simulation.json"),
        "posterior_history": Path("outputs/p01_bayesian_dice/data/posterior_history.csv"),
        "validation": Path("outputs/p01_bayesian_dice/data/validation.json"),
        "video": Path("outputs/p01_bayesian_dice/video/can_ai_tell_loaded_die.mp4"),
        "manifest": Path("outputs/p01_bayesian_dice/manifests/can_ai_tell_loaded_die.json"),
    }

    for key, relative_path in expected_relative.items():
        assert outputs[key] == (context.repository_root / relative_path).resolve()


def test_pipeline_creates_project_output_directories() -> None:
    context = build_pipeline_context()

    assert context.project_paths.data.is_dir()
    assert context.project_paths.images.is_dir()
    assert context.project_paths.video.is_dir()
    assert context.project_paths.manifests.is_dir()
