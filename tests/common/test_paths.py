"""Tests for repository and output path management."""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.common.paths import (
    RepositoryRootNotFoundError,
    UnsafeOutputPathError,
    build_project_paths,
    discover_repository_root,
    safe_project_output_path,
)


def create_fake_repository(root: Path) -> Path:
    """Create only the repository markers required for path tests."""
    (root / "src" / "linkedin_visual_labs").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "linkedin-visual-labs"\nversion = "0.0.0"\n',
        encoding="utf-8",
    )
    return root


def test_discover_repository_root_from_nested_directory(
    tmp_path: Path,
) -> None:
    repo = create_fake_repository(tmp_path / "repo")
    nested = repo / "a" / "b" / "c"
    nested.mkdir(parents=True)

    assert discover_repository_root(nested) == repo.resolve()


def test_discover_repository_root_fails_without_markers(
    tmp_path: Path,
) -> None:
    start = tmp_path / "not-a-repository"
    start.mkdir()

    with pytest.raises(RepositoryRootNotFoundError):
        discover_repository_root(start)


def test_build_project_paths_creates_expected_directories(
    tmp_path: Path,
) -> None:
    repo = create_fake_repository(tmp_path / "repo")

    paths = build_project_paths(
        "p01_bayesian_dice",
        repository_root=repo,
    )

    assert paths.output_root == (repo / "outputs" / "p01_bayesian_dice").resolve()
    assert paths.data.is_dir()
    assert paths.images.is_dir()
    assert paths.video.is_dir()
    assert paths.manifests.is_dir()


def test_safe_project_output_path_allows_nested_file(
    tmp_path: Path,
) -> None:
    repo = create_fake_repository(tmp_path / "repo")

    result = safe_project_output_path(
        "p04_zombie_escape",
        "data",
        "nested/routes.json",
        repository_root=repo,
    )

    expected = (
        repo / "outputs" / "p04_zombie_escape" / "data" / "nested" / "routes.json"
    ).resolve()

    assert result == expected
    assert result.parent.is_dir()


def test_safe_project_output_path_rejects_parent_traversal(
    tmp_path: Path,
) -> None:
    repo = create_fake_repository(tmp_path / "repo")

    with pytest.raises(UnsafeOutputPathError):
        safe_project_output_path(
            "p01_bayesian_dice",
            "data",
            "../../../README.md",
            repository_root=repo,
        )


def test_safe_project_output_path_rejects_absolute_path(
    tmp_path: Path,
) -> None:
    repo = create_fake_repository(tmp_path / "repo")

    with pytest.raises(UnsafeOutputPathError):
        safe_project_output_path(
            "p01_bayesian_dice",
            "data",
            Path("/tmp/escape.json"),
            repository_root=repo,
        )
