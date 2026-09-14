"""Traffic CLI commands remain diagnostic, read-only and explicitly native opt-in."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning import cli
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.runtime import (
    DEPENDENCIES,
    DependencyObservation,
    RuntimeStatus,
    ToolObservation,
)

ROOT = Path(__file__).resolve().parents[3]
PROJECT = "p05_traffic_operations_early_warning"
RUNNER = CliRunner()


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    (tmp_path / "src/linkedin_visual_labs").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname="linkedin-visual-labs"\n')
    (tmp_path / f"configs/{PROJECT}").mkdir(parents=True)
    for relative in (f"configs/{PROJECT}.yaml", f"configs/{PROJECT}/runtime.yaml"):
        (tmp_path / relative).write_bytes((ROOT / relative).read_bytes())
    return tmp_path


def invoke(root: Path, *args: str) -> Any:
    return RUNNER.invoke(cli.app, [args[0], "--repository-root", str(root), *args[1:]])


def install_fake_metadata(monkeypatch: pytest.MonkeyPatch, *, missing: bool = False) -> None:
    observations = tuple(
        DependencyObservation(
            distribution=n, expected_version=v, installed_version=None if missing else v
        )
        for n, v in DEPENDENCIES
    )
    monkeypatch.setattr(cli, "inspect_dependencies", lambda: observations)


def install_fake_native(monkeypatch: pytest.MonkeyPatch, mode: str = "success") -> None:
    cv = ModuleType("cv2")
    ort = ModuleType("onnxruntime")
    cv.__dict__["__version__"] = "0.0" if mode == "wrong_cv_version" else "5.0.0"
    ort.__dict__["__version__"] = "0.0" if mode == "wrong_ort_version" else "1.30.0"
    providers = (
        ["AzureExecutionProvider"]
        if mode == "missing_cpu"
        else ["AzureExecutionProvider", "CPUExecutionProvider"]
    )
    ort.__dict__["get_available_providers"] = lambda: 123 if mode == "bad_providers" else providers

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("No source/model/session/inference call permitted")

    cv.__dict__["VideoCapture"] = forbidden
    ort.__dict__["InferenceSession"] = forbidden
    original = importlib.import_module

    def fake_import(name: str, package: str | None = None) -> ModuleType:
        if name in {"cv2", "onnxruntime"}:
            if mode == f"broken_{name}":
                raise OSError("synthetic native loading failure")
            return cv if name == "cv2" else ort
        return original(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    monkeypatch.setattr(
        cli,
        "resolve_packaged_ffmpeg",
        lambda: ToolObservation(
            tool="ffmpeg", status=RuntimeStatus.AVAILABLE, detail="synthetic tool observation"
        ),
    )


def test_exact_help_commands() -> None:
    result = RUNNER.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "config-check" in result.stdout and "doctor" in result.stdout
    command = get_command(cli.app)
    assert isinstance(command, TyperGroup)
    assert set(command.commands) == {"config-check", "doctor"}


@pytest.mark.parametrize("as_json", [False, True])
def test_valid_configuration(checkout: Path, as_json: bool) -> None:
    result = invoke(checkout, "config-check", *(["--json"] if as_json else []))
    assert result.exit_code == 0, result.output
    if as_json:
        payload = json.loads(result.stdout)
        assert payload["configuration_status"] == "VALID"
        assert payload["analysis_status"] == "BLOCKED"
    else:
        assert "configuration_status: VALID" in result.stdout


@pytest.mark.parametrize(
    ("option", "content"),
    [("--config", "privacy: {face_recognition: true}"), ("--runtime-config", "gpu_required: true")],
)
def test_invalid_configurations(checkout: Path, option: str, content: str) -> None:
    relative = f"configs/{PROJECT}/invalid.yaml"
    (checkout / relative).write_text(content)
    result = invoke(checkout, "config-check", option, relative, "--json")
    assert result.exit_code == 2
    assert json.loads(result.stdout)["configuration_status"] == "INVALID"


@pytest.mark.parametrize("absolute", [False, True])
def test_config_overrides(checkout: Path, absolute: bool) -> None:
    planning = Path(f"configs/{PROJECT}/planning-copy.yaml")
    runtime = Path(f"configs/{PROJECT}/runtime-copy.yaml")
    (checkout / planning).write_bytes((checkout / f"configs/{PROJECT}.yaml").read_bytes())
    (checkout / runtime).write_bytes((checkout / f"configs/{PROJECT}/runtime.yaml").read_bytes())
    result = invoke(
        checkout,
        "config-check",
        "--config",
        str(checkout / planning if absolute else planning),
        "--runtime-config",
        str(checkout / runtime if absolute else runtime),
    )
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "path",
    [
        "../outside.yaml",
        "configs/other_project.yaml",
        "D:/linkedin-visual-labs/configs/x.yaml",
        "configs/p05_traffic_operations_early_warning/.. /outside.yaml",
    ],
)
def test_config_path_escape(checkout: Path, path: str) -> None:
    result = invoke(checkout, "config-check", "--runtime-config", path, "--json")
    assert result.exit_code == 2


@pytest.mark.parametrize("missing", [False, True])
def test_metadata_doctor(checkout: Path, monkeypatch: pytest.MonkeyPatch, missing: bool) -> None:
    install_fake_metadata(monkeypatch, missing=missing)
    result = invoke(checkout, "doctor", "--json")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["native_checks_requested"] is False and payload["native"] is None
    assert payload["runtime_status"] == (
        "MISSING_OPTIONAL_DEPENDENCY" if missing else "NOT_CONFIGURED"
    )
    assert payload["analysis_status"] == "BLOCKED"
    assert payload["model_status"] == "NOT_CONFIGURED"
    assert payload["source_status"] == "SOURCE_REVIEW_REQUIRED"
    assert payload["tracker_owner"] == "STEP_6" and payload["tracker_status"] == "NOT_IMPLEMENTED"
    assert payload["ffprobe"]["status"] == "NOT_CONFIGURED"
    assert payload["output_root_exists"] is False


@pytest.mark.parametrize(
    "mode",
    [
        "success",
        "broken_cv2",
        "broken_onnxruntime",
        "missing_cpu",
        "wrong_cv_version",
        "wrong_ort_version",
        "bad_providers",
    ],
)
def test_required_native_runtime(
    checkout: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    install_fake_metadata(monkeypatch)
    install_fake_native(monkeypatch, mode)
    result = invoke(checkout, "doctor", "--check-imports", "--require-runtime", "--json")
    assert result.exit_code == (0 if mode == "success" else 1), result.output
    payload = json.loads(result.stdout)
    assert payload["runtime_status"] == ("READY" if mode == "success" else "BLOCKED")
    assert payload["analysis_status"] == "BLOCKED"
    assert payload["source_processing_authorized"] is False
    if mode == "success":
        assert payload["native_checks"]["cv2"]["version"] == "5.0.0"
        assert payload["native_checks"]["onnxruntime"]["version"] == "1.30.0"
        assert "CPUExecutionProvider" in payload["native_checks"]["available_providers"]


def test_require_runtime_never_silently_enables_imports(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_fake_metadata(monkeypatch)
    result = invoke(checkout, "doctor", "--require-runtime", "--json")
    assert result.exit_code == 1
    assert json.loads(result.stdout)["native_checks_requested"] is False


def test_missing_metadata_cannot_be_ready(checkout: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_metadata(monkeypatch, missing=True)
    install_fake_native(monkeypatch)
    result = invoke(checkout, "doctor", "--check-imports", "--require-runtime", "--json")
    assert result.exit_code == 1


def test_native_failure_is_diagnostic_without_require_flag(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_fake_metadata(monkeypatch)
    install_fake_native(monkeypatch, "broken_cv2")
    assert invoke(checkout, "doctor", "--check-imports").exit_code == 0


@pytest.mark.parametrize("command", ["config-check", "doctor"])
def test_diagnostics_no_writes_native_or_data_access(
    checkout: Path, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    before = {p.relative_to(checkout): p.read_bytes() for p in checkout.rglob("*") if p.is_file()}
    original = Path.open

    def guarded(self: Path, *args: Any, **kwargs: Any) -> Any:
        mode = kwargs.get("mode", args[0] if args else "r")
        assert not any(x in mode for x in "wax+")
        if self.is_relative_to(checkout):
            relative = self.relative_to(checkout).as_posix()
            assert relative == "pyproject.toml" or relative.startswith(("configs/", "docs/"))
        return original(self, *args, **kwargs)

    def no_process(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("metadata-only diagnostics must not execute tools")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "open", guarded)
        patch.setattr(subprocess, "run", no_process)
        result = invoke(checkout, command, "--json")
    assert result.exit_code == 0, result.output
    assert before == {
        p.relative_to(checkout): p.read_bytes() for p in checkout.rglob("*") if p.is_file()
    }


def test_actual_step_one_hash_state() -> None:
    assert cli._step_one_state(ROOT) == {"recorded": "VERIFIED", "verification": "VERIFIED"}


def test_lazy_top_level_and_unrelated_commands() -> None:
    code = """
import importlib.abc, sys
class Block(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {
            "cv2", "onnxruntime", "torch", "ultralytics", "supervision", "bytetrack", "yolox"
        }:
            raise AssertionError("unexpected native import " + fullname)
sys.meta_path.insert(0, Block())
from typer.testing import CliRunner
from linkedin_visual_labs.cli import app
for args in (["--help"], ["traffic", "--help"], ["dice", "--help"],
             ["monopoly", "--help"], ["zombie", "--help"], ["commerce", "--help"], ["version"]):
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
