"""No-network declaration and active base/dev dependency-graph isolation checks."""

from __future__ import annotations

import tomllib
from importlib.metadata import requires
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.runtime import DEPENDENCIES

ROOT = Path(__file__).resolve().parents[3]
PROHIBITED = {
    "opencv-python-headless",
    "onnxruntime",
    "torch",
    "torchvision",
    "torchaudio",
    "ultralytics",
    "onnxruntime-gpu",
    "onnx",
    "opencv-python",
    "opencv-contrib-python",
    "supervision",
    "bytetrack",
    "yolox",
    "triton",
}


def test_exact_optional_declarations_and_narrow_constraints() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    optional = project["optional-dependencies"]
    expected = [f"{name}=={value}" for name, value in DEPENDENCIES]
    assert expected == ["opencv-python-headless==5.0.0.93", "onnxruntime==1.30.0"]
    assert optional["traffic-cv"] == expected
    assert optional["zombie-dl"] == ["torch>=2.6"]
    text = (
        ROOT / "configs/p05_traffic_operations_early_warning/runtime_constraints.txt"
    ).read_text()
    assert [line for line in text.splitlines() if line and not line.startswith("#")] == expected
    for declaration in project["dependencies"] + optional["dev"]:
        assert canonicalize_name(Requirement(declaration).name) not in PROHIBITED


def test_dev_active_transitive_graph_has_no_traffic_or_gpu_dependencies() -> None:
    """Walk installed metadata for .[dev], never the primary env's unrelated extras."""
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    pending = [
        Requirement(x) for x in project["dependencies"] + project["optional-dependencies"]["dev"]
    ]
    visited: set[tuple[str, tuple[str, ...]]] = set()
    while pending:
        requirement = pending.pop()
        name = canonicalize_name(requirement.name)
        key = name, tuple(sorted(requirement.extras))
        if key in visited:
            continue
        visited.add(key)
        assert name not in PROHIBITED and not name.startswith(("nvidia-", "cuda-")), name
        for declaration in requires(name) or ():
            child = Requirement(declaration)
            if child.marker is None or any(
                child.marker.evaluate({"extra": extra}) for extra in ("", *requirement.extras)
            ):
                pending.append(child)
