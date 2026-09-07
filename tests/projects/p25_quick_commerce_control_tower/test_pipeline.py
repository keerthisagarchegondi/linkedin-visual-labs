"""Read-only context, containment, and shared deterministic randomness checks."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from linkedin_visual_labs.common.paths import UnsafeOutputPathError, discover_repository_root
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    DEFAULT_CONFIG_PATH,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    build_pipeline_context,
)


def test_context_does_not_create_outputs(tmp_path: Path) -> None:
    root = discover_repository_root()
    (tmp_path / "src/linkedin_visual_labs").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "configs").mkdir()
    (tmp_path / DEFAULT_CONFIG_PATH).write_bytes((root / DEFAULT_CONFIG_PATH).read_bytes())
    context = build_pipeline_context(repository_root=tmp_path)
    assert context.resolve_output_path("images/map.png") == (
        tmp_path / "outputs/p25_quick_commerce_control_tower/images/map.png"
    )
    assert not (tmp_path / "outputs").exists()
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / ".cache").exists()


@pytest.mark.parametrize("path", ["../other/map.png", ".", "images/../.."])
def test_output_escape_rejected(path: str) -> None:
    with pytest.raises(UnsafeOutputPathError):
        build_pipeline_context().resolve_output_path(path)


def test_absolute_output_rejected() -> None:
    context = build_pipeline_context()
    with pytest.raises(UnsafeOutputPathError):
        context.resolve_output_path(context.paths.output_root / "map.png")


def test_seed_reproducibility() -> None:
    context = build_pipeline_context()
    first = context.create_rng("smoke").integers(0, 100000, size=20)
    second = context.create_rng("smoke").integers(0, 100000, size=20)
    other = context.create_rng("other").integers(0, 100000, size=20)
    np.testing.assert_array_equal(first, second)
    assert not np.array_equal(first, other)
