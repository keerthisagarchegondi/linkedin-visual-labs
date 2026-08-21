"""Pipeline-context tests for Project 2."""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p04_zombie_escape import (
    ZombieConfigError,
    build_pipeline_context,
)


def test_pipeline_context_loads_authoritative_config() -> None:
    context = build_pipeline_context()

    assert context.configuration.project.authoritative is True

    assert context.outputs.root == Path("outputs/p04_zombie_escape")


def test_pipeline_context_resolves_canonical_video_path() -> None:
    context = build_pipeline_context()

    expected = context.repository_root / (
        "outputs/p04_zombie_escape/video/zombie_escape_dijkstra_vs_ml_vs_dl.mp4"
    )

    assert context.resolve_output_path(context.outputs.final_video) == expected


def test_pipeline_context_rejects_output_escape() -> None:
    context = build_pipeline_context()

    with pytest.raises(
        ZombieConfigError,
        match="outside",
    ):
        context.resolve_output_path(Path("outputs/not_project_2/file.json"))
