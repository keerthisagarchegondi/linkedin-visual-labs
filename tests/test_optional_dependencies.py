"""Regression coverage for optional PyTorch and complete CI test partitioning."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_optional_dependency_and_ci_partition() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["optional-dependencies"]["zombie-dl"] == ["torch>=2.6"]
    assert not any("torch" in dep for dep in project["dependencies"])
    assert not any("torch" in dep for dep in project["optional-dependencies"]["dev"])
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert workflow["jobs"]["quality"]["needs"] == "zombie-dl"
    assert workflow["jobs"]["quality"]["if"] == "${{ always() }}"
    quality = "\n".join(step.get("run", "") for step in workflow["jobs"]["quality"]["steps"])
    zombie = "\n".join(step.get("run", "") for step in workflow["jobs"]["zombie-dl"]["steps"])
    assert ".[dev]" in quality
    assert not any("torch" in line for line in quality.splitlines() if "pip install" in line)
    assert "find_spec('torch') is None" in quality
    assert 'test "${{ needs.zombie-dl.result }}" = success' in quality
    assert "pytest --ignore=tests/projects/p04_zombie_escape" in quality
    assert "pytest tests/projects/p04_zombie_escape" in zombie
    assert "mypy --strict src tests" in zombie
    assert ".[dev,zombie-dl]" in zombie
    assert "--index-url https://download.pytorch.org/whl/cpu" in zombie


def test_cli_and_project5_import_without_torch() -> None:
    code = """
import importlib
import importlib.abc
import pkgutil
import sys

class NoTorch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "torch" or fullname.startswith("torch."):
            raise ModuleNotFoundError("torch intentionally unavailable", name="torch")

sys.meta_path.insert(0, NoTorch())
import linkedin_visual_labs
from linkedin_visual_labs.cli import app
from typer.testing import CliRunner
import linkedin_visual_labs.projects.p25_quick_commerce_control_tower as project
for info in pkgutil.walk_packages(project.__path__, project.__name__ + "."):
    importlib.import_module(info.name)
for args in (["--help"], ["dice", "--help"], ["commerce", "--help"], ["zombie", "--help"]):
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
assert "torch" not in sys.modules
import linkedin_visual_labs.projects.p04_zombie_escape as zombie
try:
    zombie.ZombieRiskCNN
except ModuleNotFoundError as exc:
    assert ".[zombie-dl]" in str(exc)
else:
    raise AssertionError("DL export did not require optional dependency")
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr
