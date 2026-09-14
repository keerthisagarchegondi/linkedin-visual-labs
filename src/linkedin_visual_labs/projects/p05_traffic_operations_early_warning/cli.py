"""Read-only traffic configuration and opt-in runtime diagnostics."""

from __future__ import annotations

import hashlib
import importlib
import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Any

import typer

from linkedin_visual_labs.common.config import ConfigurationError, load_yaml_config
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.config import (
    CANONICAL_ROOT,
    DEFAULT_CONFIG_PATH,
    load_traffic_config,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.models import (
    TrafficOperationsConfig,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.paths import (
    PROJECT_ID,
    TrafficPaths,
    _no_redirects,
    _relative,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.runtime import (
    NativeObservation,
    RuntimeConfig,
    RuntimeInventory,
    RuntimeStatus,
    ToolObservation,
    inspect_dependencies,
    inspect_ffprobe,
    load_runtime_config,
    resolve_packaged_ffmpeg,
)

RUNTIME_CONFIG_PATH = Path(f"configs/{PROJECT_ID}/runtime.yaml")
app = typer.Typer(
    name="traffic", help="Recorded traffic configuration and runtime checks.", no_args_is_help=True
)


def _config_path(root: Path, path: Path, *, planning: bool) -> Path:
    """Permit only Project 6 config overrides, including contained absolute paths."""
    relative = path.relative_to(root) if path.is_absolute() else path
    relative = _relative(relative.as_posix())
    if not (planning and relative == DEFAULT_CONFIG_PATH) and not relative.is_relative_to(
        Path(f"configs/{PROJECT_ID}")
    ):
        raise ConfigurationError("configuration must belong to the Project 6 config namespace")
    _no_redirects(root / relative)
    return relative


def _load(
    root: Path,
    config: Path,
    runtime_config: Path,
) -> tuple[TrafficPaths, TrafficOperationsConfig, RuntimeConfig]:
    paths = TrafficPaths(root)
    planning_path = _config_path(root, config, planning=True)
    runtime_path = _config_path(root, runtime_config, planning=False)
    planning = load_traffic_config(planning_path, repository_root=root)
    runtime = (
        load_runtime_config(repository_root=root)
        if runtime_path == RUNTIME_CONFIG_PATH
        else RuntimeConfig.model_validate(load_yaml_config(root / runtime_path))
    )
    for name, _ in TrafficPaths.AREAS:
        paths.area(name)
    return paths, planning, runtime


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for name, value in payload.items():
            rendered = (
                json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
            )
            typer.echo(f"{name}: {rendered}")


def _invalid(error: Exception, as_json: bool) -> None:
    _emit({"configuration_status": "INVALID", "error": str(error)}, as_json)
    raise typer.Exit(code=2) from error


def _step_one_state(root: Path) -> dict[str, str]:
    """Report the recorded state and check only immutable Step 1 implementation files.

    Mutable documentation hashes are historical. Never follow arbitrary state paths.
    Missing evidence is diagnostic; it does not mean the optional native runtime failed.
    """
    path = root / f"docs/projects/{PROJECT_ID}/STATE.json"
    try:
        _no_redirects(path)
        state = json.loads(path.read_text(encoding="utf-8"))
        recorded = state["implementation_steps"]["1"]
        if recorded != "VERIFIED":
            return {"recorded": str(recorded), "verification": "NOT_VERIFIED"}
        hashes = {
            x["path"]: x["sha256"] for x in state["step_1_validation"]["validated_file_sha256"]
        }
        files = (
            f"configs/{PROJECT_ID}.yaml",
            *(
                f"src/linkedin_visual_labs/projects/{PROJECT_ID}/{name}.py"
                for name in ("__init__", "models", "config")
            ),
            *(
                f"tests/projects/{PROJECT_ID}/{name}.py"
                for name in ("test_contract", "test_config")
            ),
        )
        for relative in files:
            candidate = root / relative
            _no_redirects(candidate)
            if hashlib.sha256(candidate.read_bytes()).hexdigest() != hashes[relative]:
                return {"recorded": "VERIFIED", "verification": "HASH_MISMATCH"}
        return {"recorded": "VERIFIED", "verification": "VERIFIED"}
    except (OSError, ValueError, KeyError, TypeError):
        return {"recorded": "UNAVAILABLE", "verification": "UNAVAILABLE"}


def _native_checks() -> tuple[NativeObservation, dict[str, Any]]:
    checks: dict[str, Any] = {}
    imported: dict[str, bool] = {}
    providers: tuple[str, ...] = ()
    for name, expected in (("cv2", "5.0.0"), ("onnxruntime", "1.30.0")):
        imported[name] = False
        try:
            module = importlib.import_module(name)
            imported[name] = True
            observed = str(module.__version__)
            if name == "onnxruntime":
                available = module.get_available_providers()
                if not isinstance(available, (list, tuple)) or not all(
                    isinstance(x, str) for x in available
                ):
                    raise ValueError("invalid ONNX Runtime provider response")
                providers = tuple(available)
            checks[name] = {
                "status": "AVAILABLE" if observed == expected else "BLOCKED",
                "version": observed,
                "detail": "Import succeeded"
                if observed == expected
                else f"Expected runtime version {expected}",
            }
        except Exception as error:
            checks[name] = {"status": "BLOCKED", "detail": f"{type(error).__name__}: {error}"}
    checks["available_providers"] = list(providers)
    return NativeObservation(
        cv2_importable=imported["cv2"],
        onnxruntime_importable=imported["onnxruntime"],
        available_providers=providers,
    ), checks


def _ffmpeg_metadata() -> ToolObservation:
    try:
        installed = version("imageio-ffmpeg")
    except PackageNotFoundError:
        return ToolObservation(
            tool="ffmpeg",
            status=RuntimeStatus.MISSING_OPTIONAL_DEPENDENCY,
            detail="imageio-ffmpeg metadata missing",
        )
    return ToolObservation(
        tool="ffmpeg",
        status=RuntimeStatus.NOT_CONFIGURED,
        package="imageio-ffmpeg",
        package_version=installed,
        detail="Metadata only; packaged executable check requires --check-imports",
    )


@app.command(name="config-check")
def config_check(
    repository_root: Annotated[
        Path, typer.Option("--repository-root", help="Explicit checkout root; no discovery.")
    ] = CANONICAL_ROOT,
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    runtime_config: Annotated[Path, typer.Option("--runtime-config")] = RUNTIME_CONFIG_PATH,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Validate both configurations and paths without executing native tools."""
    try:
        paths, planning, runtime = _load(repository_root, config, runtime_config)
    except (OSError, ValueError) as error:
        _invalid(error, as_json)
        return
    _emit(
        {
            "repository_root": str(paths.repository_root),
            "configuration_status": "VALID",
            "planning_config_status": "VALID",
            "runtime_config_status": "VALID",
            "paths_status": "VALID",
            "source_status": planning.source.status.value,
            "runtime_family": runtime.runtime_family,
            "analysis_status": "BLOCKED",
        },
        as_json,
    )


@app.command(name="doctor")
def doctor(
    repository_root: Annotated[
        Path, typer.Option("--repository-root", help="Explicit checkout root; no discovery.")
    ] = CANONICAL_ROOT,
    config: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG_PATH,
    runtime_config: Annotated[Path, typer.Option("--runtime-config")] = RUNTIME_CONFIG_PATH,
    as_json: Annotated[bool, typer.Option("--json")] = False,
    check_imports: Annotated[
        bool,
        typer.Option(
            "--check-imports",
            help="Explicit native imports and packaged FFmpeg version check; no inference.",
        ),
    ] = False,
    require_runtime: Annotated[
        bool,
        typer.Option(
            "--require-runtime", help="Exit 1 unless native runtime readiness is established."
        ),
    ] = False,
) -> None:
    """Inspect readiness; missing source, model and tracker are expected at Step 2."""
    try:
        paths, planning, runtime = _load(repository_root, config, runtime_config)
    except (OSError, ValueError) as error:
        _invalid(error, as_json)
        return
    native, checks = _native_checks() if check_imports else (None, {})
    inventory = RuntimeInventory(config=runtime, dependencies=inspect_dependencies(), native=native)
    payload = inventory.snapshot()
    runtime_status = inventory.runtime_status
    if sys.version_info[:2] != (3, 13) or (
        check_imports
        and any(checks[name]["status"] != "AVAILABLE" for name in ("cv2", "onnxruntime"))
    ):
        runtime_status = RuntimeStatus.BLOCKED
    ffmpeg = resolve_packaged_ffmpeg() if check_imports else _ffmpeg_metadata()
    payload.update(
        {
            "repository_root": str(paths.repository_root),
            "python_version": platform.python_version(),
            "interpreter": sys.executable,
            "planning_config_status": "VALID",
            "runtime_config_status": "VALID",
            "step_1": _step_one_state(paths.repository_root),
            "selected_runtime": "OpenCV-headless + CPU ONNX Runtime",
            "configured_provider": runtime.execution_provider,
            "gpu_required": runtime.gpu_required,
            "tracker_status": runtime.tracker_status,
            "tracker_owner": runtime.tracker_owner,
            "ffmpeg": ffmpeg.model_dump(mode="json"),
            "ffprobe": inspect_ffprobe(runtime.ffprobe_reference).model_dump(mode="json"),
            "source_status": planning.source.status.value,
            "source_processing_authorized": False,
            "output_root_exists": paths.area("output").exists(),
            "runtime_status": runtime_status.value,
            "native_checks_requested": check_imports,
            "native_checks": checks,
            "analysis_blockers": [
                "Source processing is not authorized",
                "Model artifact not acquired or validated",
                "Geometry/calibration not established",
                "Tracker deferred to Step 6",
            ],
        }
    )
    _emit(payload, as_json)
    if require_runtime and runtime_status != RuntimeStatus.READY:
        raise typer.Exit(code=1)
