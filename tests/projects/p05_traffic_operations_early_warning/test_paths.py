"""Contained path contracts use small injected checkouts, never other repositories."""

from __future__ import annotations

import stat
from dataclasses import FrozenInstanceError
from os import stat_result
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from linkedin_visual_labs.common.config import ConfigurationError
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.paths import TrafficPaths

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("metadata", ["project = 1", "[project]\nname = 123", "broken ["])
def test_malformed_checkout_identity_is_configuration_error(tmp_path: Path, metadata: str) -> None:
    checkout(tmp_path)
    (tmp_path / "pyproject.toml").write_text(metadata)
    with pytest.raises(ConfigurationError):
        TrafficPaths(tmp_path)


def checkout(root: Path) -> TrafficPaths:
    (root / "src/linkedin_visual_labs").mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nname="linkedin-visual-labs"\n')
    return TrafficPaths(root)


@pytest.mark.parametrize(("name", "relative"), TrafficPaths.AREAS)
def test_exact_contained_locations(tmp_path: Path, name: str, relative: str) -> None:
    paths = checkout(tmp_path)
    before = set(tmp_path.rglob("*"))
    assert paths.area(name) == tmp_path / relative
    assert paths.area(name).is_relative_to(tmp_path)
    assert set(tmp_path.rglob("*")) == before


def test_actual_checkout_and_immutability() -> None:
    paths = TrafficPaths(ROOT)
    assert (
        paths.area("runtime_config")
        == ROOT / "configs/p05_traffic_operations_early_warning/runtime.yaml"
    )
    with pytest.raises(FrozenInstanceError):
        paths.__setattr__("repository_root", ROOT / "src")


@pytest.mark.parametrize(
    "relative",
    [
        "../sibling",
        "a/../../x",
        "/outside",
        "D:/outside",
        "D:x",
        "\\\\server\\x",
        "a\\b",
        "a:b",
        ".. /sibling",
        "folder./child",
        "",
        ".",
    ],
)
def test_child_escape_rejected(tmp_path: Path, relative: str) -> None:
    paths = checkout(tmp_path)
    with pytest.raises(ConfigurationError):
        paths.child("raw", relative)


@pytest.mark.parametrize("name", ["foreign", "../p02_monopoly_ai", "outputs/p02_monopoly_ai"])
def test_sibling_area_rejected(tmp_path: Path, name: str) -> None:
    with pytest.raises(ConfigurationError):
        checkout(tmp_path).area(name)


def test_child_is_project_local_without_creation(tmp_path: Path) -> None:
    paths = checkout(tmp_path)
    target = paths.child("weights", "future/model.bin")
    assert (
        target == tmp_path / "models/weights/p05_traffic_operations_early_warning/future/model.bin"
    )
    assert not target.parent.exists()
    with pytest.raises(ConfigurationError):
        paths.child("planning_config", "runtime.yaml")


@pytest.mark.parametrize(
    "value",
    [
        "relative",
        "D:/linkedin-visual-labs",
        "D:/linkedin-visual-labs/nested",
        "D:/linkedin-visual-labs.",
        "D:/linkedin-visual-labs ",
        "\\\\?\\D:\\linkedin-visual-labs",
        "\\\\server\\share\\linkedin-visual-labs",
        "/mnt/d/linkedin-visual-labs",
        "D:/ChangeGraph",
        "D:/job_hunter",
        "D:/My-portfolio-Keerthi",
    ],
)
def test_prohibited_roots_rejected_without_inspection(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    def no_stat(self: Path) -> stat_result:
        raise AssertionError("foreign root must be rejected before filesystem inspection")

    monkeypatch.setattr(Path, "lstat", no_stat)
    with pytest.raises(ConfigurationError):
        TrafficPaths(Path(value))


def test_no_parent_discovery_and_foreign_identity(tmp_path: Path) -> None:
    checkout(tmp_path)
    child = tmp_path / "nested"
    child.mkdir()
    with pytest.raises(ConfigurationError):
        TrafficPaths(child)
    with pytest.raises(ConfigurationError):
        TrafficPaths(tmp_path / "nested/..")
    (tmp_path / "pyproject.toml").write_text('[project]\nname="foreign"\n')
    with pytest.raises(ConfigurationError):
        TrafficPaths(tmp_path)


@pytest.mark.parametrize("kind", ["symlink", "junction"])
def test_redirect_refused_before_following_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    paths = checkout(tmp_path)
    redirect = tmp_path / "data"
    original = Path.lstat

    def fake_stat(self: Path) -> stat_result:
        if self == redirect:
            return cast(
                stat_result,
                SimpleNamespace(
                    st_mode=stat.S_IFLNK if kind == "symlink" else stat.S_IFDIR,
                    st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT
                    if kind == "junction"
                    else 0,
                ),
            )
        if self.is_relative_to(redirect):
            raise AssertionError("redirect target inspected")
        return original(self)

    monkeypatch.setattr(Path, "lstat", fake_stat)
    with pytest.raises(ConfigurationError, match="redirected"):
        paths.area("raw")


def test_redirect_in_root_ancestry_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout(tmp_path)
    original = Path.lstat

    def fake_stat(self: Path) -> stat_result:
        if self == tmp_path:
            return cast(stat_result, SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0))
        return original(self)

    monkeypatch.setattr(Path, "lstat", fake_stat)
    with pytest.raises(ConfigurationError, match="redirected"):
        TrafficPaths(tmp_path)
