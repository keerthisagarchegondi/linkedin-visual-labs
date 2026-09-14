"""Strict operational contracts, metadata-only inspection and fake tool execution."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from importlib.metadata import Distribution, PackageNotFoundError, PackagePath
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from linkedin_visual_labs.common.config import ConfigurationError
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning import runtime
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.runtime import (
    CPU_PROVIDER,
    DEPENDENCIES,
    DependencyObservation,
    ExecutableReference,
    ModelDescriptor,
    NativeObservation,
    RuntimeConfig,
    RuntimeInventory,
    RuntimeStatus,
    inspect_dependencies,
    inspect_ffprobe,
    load_runtime_config,
    resolve_packaged_ffmpeg,
)

ROOT = Path(__file__).resolve().parents[3]


def test_checked_in_config_and_deterministic_serialization() -> None:
    config = load_runtime_config(repository_root=ROOT)
    assert config.model is None
    assert config.tracker_status == "NOT_IMPLEMENTED" and config.tracker_owner == "STEP_6"
    assert not config.source_processing_authorized and config.source_status == "REVIEW_REQUIRED"
    assert config.ffprobe_reference is None and config.ffmpeg_policy == "PACKAGED_ONLY"
    assert config.intra_op_threads is None and config.inter_op_threads is None
    assert config.model_dump_json() == load_runtime_config(repository_root=ROOT).model_dump_json()
    with pytest.raises(ValidationError):
        config.gpu_required = True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("runtime_family", "ULTRALYTICS"),
        ("opencv_variant", "GUI"),
        ("execution_provider", "AzureExecutionProvider"),
        ("gpu_required", True),
        ("gpu_required", 0),
        ("gpu_required", "false"),
        ("source_processing_authorized", True),
        ("source_processing_authorized", 0),
        ("source_status", "APPROVED"),
        ("tracker_status", "AVAILABLE"),
        ("tracker_owner", "STEP_2"),
        ("ffmpeg_policy", "PATH"),
        ("intra_op_threads", 0),
        ("intra_op_threads", 65),
        ("intra_op_threads", True),
        ("intra_op_threads", "2"),
        ("inter_op_threads", 2.5),
        ("inter_op_threads", float("nan")),
        ("extra", 1),
        ("model", {}),
    ],
)
def test_invalid_runtime_fields(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        RuntimeConfig.model_validate({field: value})


def test_loader_strict_and_no_storage_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "src/linkedin_visual_labs").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname="linkedin-visual-labs"\n')
    target = tmp_path / "configs/p05_traffic_operations_early_warning/runtime.yaml"
    target.parent.mkdir(parents=True)
    target.write_text(yaml.safe_dump(RuntimeConfig().model_dump(mode="json")))
    before = set(tmp_path.rglob("*"))
    original = Path.open

    def guarded_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        assert self in {target, tmp_path / "pyproject.toml"}, self
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    assert load_runtime_config(repository_root=tmp_path).model is None
    assert set(tmp_path.rglob("*")) == before
    target.write_text("intra_op_threads: '2'\n")
    with pytest.raises(ConfigurationError):
        load_runtime_config(repository_root=tmp_path)


@pytest.mark.parametrize("mode", ["present", "absent", "wrong_version"])
def test_metadata_observations(monkeypatch: pytest.MonkeyPatch, mode: str) -> None:
    def fake_version(name: str) -> str:
        if mode == "absent":
            raise PackageNotFoundError(name)
        return dict(DEPENDENCIES)[name] if mode == "present" else "0.0.0"

    monkeypatch.setattr(runtime, "version", fake_version)
    observations = inspect_dependencies()
    expected = {
        "present": RuntimeStatus.AVAILABLE,
        "absent": RuntimeStatus.MISSING_OPTIONAL_DEPENDENCY,
        "wrong_version": RuntimeStatus.BLOCKED,
    }[mode]
    assert len(observations) == 2 and all(o.status == expected for o in observations)


@pytest.mark.parametrize(
    ("cv2_ok", "ort_ok", "providers", "expected"),
    [
        (True, True, (CPU_PROVIDER,), RuntimeStatus.READY),
        (True, True, ("AzureExecutionProvider", CPU_PROVIDER), RuntimeStatus.READY),
        (True, True, ("AzureExecutionProvider",), RuntimeStatus.BLOCKED),
        (False, True, (CPU_PROVIDER,), RuntimeStatus.BLOCKED),
        (True, False, (CPU_PROVIDER,), RuntimeStatus.BLOCKED),
    ],
)
def test_readiness_requires_native_cpu_evidence(
    cv2_ok: bool, ort_ok: bool, providers: tuple[str, ...], expected: RuntimeStatus
) -> None:
    deps = tuple(
        DependencyObservation(distribution=n, expected_version=v, installed_version=v)
        for n, v in DEPENDENCIES
    )
    inventory = RuntimeInventory(config=RuntimeConfig(), dependencies=deps)
    assert inventory.runtime_status == RuntimeStatus.NOT_CONFIGURED
    native = NativeObservation(
        cv2_importable=cv2_ok, onnxruntime_importable=ort_ok, available_providers=providers
    )
    inventory = RuntimeInventory(config=RuntimeConfig(), dependencies=deps, native=native)
    assert inventory.runtime_status == expected
    assert inventory.analysis_status == RuntimeStatus.BLOCKED
    snapshot = inventory.snapshot()
    assert snapshot["runtime_status"] == expected.value
    assert snapshot["analysis_status"] == "BLOCKED"
    assert snapshot["model_status"] == "NOT_CONFIGURED"
    assert json.dumps(snapshot, sort_keys=True) == json.dumps(inventory.snapshot(), sort_keys=True)


def test_incomplete_or_incompatible_inventory_never_ready() -> None:
    assert (
        RuntimeInventory(config=RuntimeConfig(), dependencies=()).runtime_status
        == RuntimeStatus.BLOCKED
    )
    deps = tuple(
        DependencyObservation(distribution=n, expected_version=v, installed_version=None)
        for n, v in DEPENDENCIES
    )
    assert (
        RuntimeInventory(config=RuntimeConfig(), dependencies=deps).runtime_status
        == RuntimeStatus.MISSING_OPTIONAL_DEPENDENCY
    )


def descriptor() -> dict[str, Any]:
    return dict(
        model_id="synthetic-test-only",
        provider="fixture",
        source_url="https://example.invalid/test",
        artifact_filename="fixture.bin",
        model_license="synthetic",
        code_license="synthetic",
        sha256="0" * 64,
        input_width=32,
        input_height=32,
        layout="NCHW",
        class_map=((0, "vehicle"),),
        preprocessing_contract="fixture",
        output_contract="fixture",
        onnx_compatibility="not an actual model",
        confidence_threshold=0.5,
    )


def test_descriptor_is_immutable_metadata_not_acquisition() -> None:
    model = ModelDescriptor.model_validate(descriptor())
    assert model.approval_status == "REVIEW_REQUIRED"
    assert RuntimeConfig(model=model).source_processing_authorized is False
    assert (
        RuntimeInventory(config=RuntimeConfig(model=model), dependencies=()).model_status
        == RuntimeStatus.NOT_YET_ACQUIRED
    )
    with pytest.raises(ValidationError):
        model.input_width = 64


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("artifact_filename", "../x"),
        ("artifact_filename", "D:x"),
        ("sha256", "bad"),
        ("input_width", True),
        ("input_height", 0),
        ("confidence_threshold", "0.5"),
        ("confidence_threshold", float("inf")),
        ("class_map", ((0, "car"), (0, "bus"))),
        ("class_map", ((-1, "car"),)),
        ("class_map", ()),
        ("source_url", "file:///model"),
        ("extra", 1),
    ],
)
def test_descriptor_rejects_invalid_metadata(field: str, value: object) -> None:
    data = descriptor()
    data[field] = value
    with pytest.raises(ValidationError):
        ModelDescriptor.model_validate(data)


def test_ffprobe_never_uses_path_or_opens_reference() -> None:
    assert inspect_ffprobe().status == RuntimeStatus.NOT_CONFIGURED
    reference = ExecutableReference(path="/explicit/future/ffprobe", sha256="0" * 64)
    assert inspect_ffprobe(reference).status == RuntimeStatus.BLOCKED
    with pytest.raises(ValidationError):
        ExecutableReference(path="ffprobe", sha256="0" * 64)


class FakeDistribution(Distribution):
    def __init__(self, root: Path) -> None:
        self.root = root

    def read_text(self, filename: str) -> str | None:
        return "Name: imageio-ffmpeg\nVersion: 0.6.0\n" if filename == "METADATA" else None

    def locate_file(self, path: str | os.PathLike[str]) -> Path:
        return self.root / path

    @property
    def files(self) -> list[PackagePath]:
        return [PackagePath("imageio_ffmpeg/binaries/ffmpeg-fixture.exe")]


@pytest.mark.parametrize("mode", ["success", "failure", "timeout", "missing", "bad_version"])
def test_packaged_ffmpeg_bounded_no_media(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    package = FakeDistribution(tmp_path)
    executable = package.locate_file(package.files[0])
    executable.parent.mkdir(parents=True)
    if mode != "missing":
        executable.write_bytes(b"synthetic executable fixture, never executed")
    monkeypatch.setattr(runtime, "distribution", lambda name: package)
    monkeypatch.setenv("IMAGEIO_FFMPEG_EXE", "untrusted")
    monkeypatch.setenv("PATH", "untrusted")

    def fake_run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert command == [str(executable), "-version"]
        assert kwargs["env"]["PATH"] == ""
        assert "IMAGEIO_FFMPEG_EXE" not in kwargs["env"]
        assert kwargs["timeout"] == 3
        if mode == "failure":
            raise subprocess.CalledProcessError(1, command)
        if mode == "timeout":
            raise subprocess.TimeoutExpired(command, 3)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="invalid" if mode == "bad_version" else "ffmpeg version fixture\nmore",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    observed = resolve_packaged_ffmpeg(timeout_seconds=3)
    assert observed.status == (
        RuntimeStatus.AVAILABLE if mode == "success" else RuntimeStatus.BLOCKED
    )
    if mode == "success":
        assert observed.sha256 == hashlib.sha256(executable.read_bytes()).hexdigest()
        assert observed.package_version == "0.6.0"
    assert os.environ["PATH"] == "untrusted"


def test_ffmpeg_missing_package(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> Distribution:
        raise PackageNotFoundError(name)

    monkeypatch.setattr(runtime, "distribution", missing)
    assert resolve_packaged_ffmpeg().status == RuntimeStatus.MISSING_OPTIONAL_DEPENDENCY


@pytest.mark.parametrize("count", [0, 2])
def test_ffmpeg_ambiguous_or_missing_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    class Ambiguous(FakeDistribution):
        @property
        def files(self) -> list[PackagePath]:
            return [PackagePath(f"imageio_ffmpeg/binaries/ffmpeg-{i}") for i in range(count)]

    monkeypatch.setattr(runtime, "distribution", lambda name: Ambiguous(tmp_path))
    assert resolve_packaged_ffmpeg().status == RuntimeStatus.BLOCKED


@pytest.mark.parametrize("timeout", [0.0, -1.0, 61.0, float("nan")])
def test_ffmpeg_timeout_bounds(timeout: float) -> None:
    with pytest.raises(ValueError):
        resolve_packaged_ffmpeg(timeout_seconds=timeout)


@pytest.mark.parametrize("mode", ["duplicate", "wrong_expected", "wrong_installed"])
def test_readiness_rejects_mismatched_metadata(mode: str) -> None:
    deps = [
        DependencyObservation(distribution=n, expected_version=v, installed_version=v)
        for n, v in DEPENDENCIES
    ]
    if mode == "duplicate":
        deps.append(deps[0])
    else:
        name, expected = DEPENDENCIES[0]
        deps[0] = DependencyObservation(
            distribution=name,
            expected_version="0" if mode == "wrong_expected" else expected,
            installed_version="0" if mode == "wrong_installed" else expected,
        )
    assert (
        RuntimeInventory(config=RuntimeConfig(), dependencies=tuple(deps)).runtime_status
        == RuntimeStatus.BLOCKED
    )


def test_import_and_metadata_need_no_cv_or_executable() -> None:
    code = """
import importlib, importlib.abc, sys, subprocess
blocked = {"cv2", "onnxruntime", "torch", "ultralytics", "supervision",
           "bytetrack", "yolox", "imageio_ffmpeg"}
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in blocked:
            raise AssertionError("unexpected import: " + fullname)
def no_execute(*args, **kwargs):
    raise AssertionError("unexpected process execution")
sys.meta_path.insert(0, Block())
subprocess.run = no_execute
prefix = "linkedin_visual_labs.projects.p05_traffic_operations_early_warning"
for suffix in ("", ".models", ".config", ".paths", ".runtime"):
    importlib.import_module(prefix + suffix)
r = importlib.import_module(prefix + ".runtime")
r.inspect_dependencies()
r.inspect_ffprobe()
assert not blocked.intersection(sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
