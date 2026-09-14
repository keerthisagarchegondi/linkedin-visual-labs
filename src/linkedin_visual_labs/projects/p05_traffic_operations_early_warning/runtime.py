"""Operational records and explicit packaged-tool inspection, without CV imports."""

from __future__ import annotations

import hashlib
import os
import subprocess
from enum import StrEnum
from importlib.metadata import PackageNotFoundError, distribution, version
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from linkedin_visual_labs.common.config import ConfigurationError, load_yaml_config
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.paths import (
    TrafficPaths,
    _no_redirects,
)

DEPENDENCIES = (("opencv-python-headless", "5.0.0.93"), ("onnxruntime", "1.30.0"))
CPU_PROVIDER: Literal["CPUExecutionProvider"] = "CPUExecutionProvider"
Text = Annotated[str, Field(min_length=1, pattern=r"\S")]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ThreadCount = Annotated[int, Field(ge=1, le=64)]


class RuntimeRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True, validate_default=True)


class RuntimeStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING_OPTIONAL_DEPENDENCY = "MISSING_OPTIONAL_DEPENDENCY"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_YET_ACQUIRED = "NOT_YET_ACQUIRED"
    BLOCKED = "BLOCKED"
    READY = "READY"


class ModelDescriptor(RuntimeRecord):
    """Future reviewed metadata only; validation never authenticates model bytes."""

    model_id: Text
    provider: Text
    source_url: Text
    artifact_filename: Text
    model_license: Text
    code_license: Text
    approval_status: Literal["REVIEW_REQUIRED", "APPROVED"] = "REVIEW_REQUIRED"
    sha256: Digest
    input_width: Annotated[int, Field(gt=0)]
    input_height: Annotated[int, Field(gt=0)]
    layout: Literal["NCHW", "NHWC"]
    class_map: tuple[tuple[int, str], ...]
    preprocessing_contract: Text
    output_contract: Text
    onnx_compatibility: Text
    execution_provider: Literal["CPUExecutionProvider"] = CPU_PROVIDER
    confidence_threshold: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]

    @field_validator("artifact_filename")
    @classmethod
    def filename_only(cls, value: str) -> str:
        if (
            value in {".", ".."}
            or "/" in value
            or "\\" in value
            or ":" in value
            or PureWindowsPath(value).drive
        ):
            raise ValueError("model artifact must be a filename, not a path")
        return value

    @model_validator(mode="after")
    def descriptor_contract(self) -> Self:
        if not self.source_url.startswith("https://"):
            raise ValueError("model source must be an explicit HTTPS reference")
        ids = [item[0] for item in self.class_map]
        if not ids or len(ids) != len(set(ids)) or any(i < 0 for i in ids):
            raise ValueError("class map requires unique nonnegative class IDs")
        if any(not name.strip() for _, name in self.class_map):
            raise ValueError("class labels cannot be blank")
        return self


class ExecutableReference(RuntimeRecord):
    """Future explicit reference; never searched on PATH or executed by loading."""

    path: Text
    sha256: Digest
    approval_status: Literal["REVIEW_REQUIRED", "APPROVED"] = "REVIEW_REQUIRED"

    @field_validator("path")
    @classmethod
    def absolute_reference(cls, value: str) -> str:
        if not (PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()):
            raise ValueError("explicit absolute executable reference required")
        if ".." in PurePosixPath(value.replace("\\", "/")).parts:
            raise ValueError("executable reference cannot traverse parents")
        return value


class RuntimeConfig(RuntimeRecord):
    schema_version: Literal["1.0"] = "1.0"
    runtime_family: Literal["ONNX_RUNTIME"] = "ONNX_RUNTIME"
    opencv_variant: Literal["HEADLESS"] = "HEADLESS"
    execution_provider: Literal["CPUExecutionProvider"] = CPU_PROVIDER
    gpu_required: bool = False
    intra_op_threads: ThreadCount | None = None
    inter_op_threads: ThreadCount | None = None
    model: ModelDescriptor | None = None
    tracker_status: Literal["NOT_IMPLEMENTED"] = "NOT_IMPLEMENTED"
    tracker_owner: Literal["STEP_6"] = "STEP_6"
    source_status: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"
    source_processing_authorized: bool = False
    ffmpeg_policy: Literal["PACKAGED_ONLY"] = "PACKAGED_ONLY"
    ffprobe_reference: ExecutableReference | None = None

    @model_validator(mode="after")
    def disabled_processing(self) -> Self:
        if self.gpu_required or self.source_processing_authorized:
            raise ValueError("GPU and source processing must remain disabled")
        return self


class DependencyObservation(RuntimeRecord):
    distribution: str
    expected_version: str
    installed_version: str | None

    @property
    def status(self) -> RuntimeStatus:
        if self.installed_version is None:
            return RuntimeStatus.MISSING_OPTIONAL_DEPENDENCY
        if self.installed_version != self.expected_version:
            return RuntimeStatus.BLOCKED
        return RuntimeStatus.AVAILABLE


class NativeObservation(RuntimeRecord):
    """Evidence supplied by a future explicit doctor; no native checking here."""

    cv2_importable: bool
    onnxruntime_importable: bool
    available_providers: tuple[str, ...]


class ToolObservation(RuntimeRecord):
    tool: Literal["ffmpeg", "ffprobe"]
    status: RuntimeStatus
    executable: str | None = None
    version: str | None = None
    sha256: Digest | None = None
    package: str | None = None
    package_version: str | None = None
    detail: str


class RuntimeInventory(RuntimeRecord):
    config: RuntimeConfig
    dependencies: tuple[DependencyObservation, ...]
    native: NativeObservation | None = None

    @property
    def runtime_status(self) -> RuntimeStatus:
        observed = {item.distribution: item for item in self.dependencies}
        if len(observed) != len(self.dependencies) or set(observed) != dict(DEPENDENCIES).keys():
            return RuntimeStatus.BLOCKED
        for name, expected in DEPENDENCIES:
            item = observed[name]
            if item.expected_version != expected:
                return RuntimeStatus.BLOCKED
            if item.status != RuntimeStatus.AVAILABLE:
                return item.status
        if self.native is None:
            return RuntimeStatus.NOT_CONFIGURED
        if (
            self.native.cv2_importable
            and self.native.onnxruntime_importable
            and CPU_PROVIDER in self.native.available_providers
        ):
            return RuntimeStatus.READY
        return RuntimeStatus.BLOCKED

    @property
    def analysis_status(self) -> RuntimeStatus:
        """Step 2 never authenticates source/model/calibration or enables analysis."""
        return RuntimeStatus.BLOCKED

    @property
    def model_status(self) -> RuntimeStatus:
        return (
            RuntimeStatus.NOT_CONFIGURED
            if self.config.model is None
            else RuntimeStatus.NOT_YET_ACQUIRED
        )

    def snapshot(self) -> dict[str, object]:
        """Serialize explicit readiness without claiming that metadata runs analysis."""
        return {
            **self.model_dump(mode="json"),
            "dependencies": [
                {**item.model_dump(mode="json"), "status": item.status.value}
                for item in self.dependencies
            ],
            "runtime_status": self.runtime_status.value,
            "analysis_status": self.analysis_status.value,
            "model_status": self.model_status.value,
        }


def load_runtime_config(*, repository_root: Path) -> RuntimeConfig:
    """Read only the fixed operational YAML inside the explicitly supplied checkout."""
    path = TrafficPaths(repository_root).area("runtime_config")
    try:
        return RuntimeConfig.model_validate(load_yaml_config(path))
    except (ValidationError, ValueError, OSError) as error:
        raise ConfigurationError(f"invalid Project 6 runtime configuration: {error}") from error


def inspect_dependencies() -> tuple[DependencyObservation, ...]:
    """Read distribution metadata only; presence is not native import readiness."""
    observations = []
    for name, expected in DEPENDENCIES:
        try:
            installed = version(name)
        except PackageNotFoundError:
            installed = None
        observations.append(
            DependencyObservation(
                distribution=name, expected_version=expected, installed_version=installed
            )
        )
    return tuple(observations)


def inspect_ffprobe(reference: ExecutableReference | None = None) -> ToolObservation:
    """Record configuration only; do not inspect or execute a future reference."""
    return ToolObservation(
        tool="ffprobe",
        status=RuntimeStatus.NOT_CONFIGURED if reference is None else RuntimeStatus.BLOCKED,
        detail="No deterministic ffprobe configured"
        if reference is None
        else "Verification deferred",
    )


def resolve_packaged_ffmpeg(*, timeout_seconds: float = 10.0) -> ToolObservation:
    """Explicitly check an imageio-owned binary, never PATH or environment overrides.

    Enumerating installed package records avoids the package API's fallback search.
    Only the selected binary's -version is executed; no media is opened or encoded.
    """
    if not 0 < timeout_seconds <= 60:
        raise ValueError("FFmpeg timeout must be positive and at most 60 seconds")
    try:
        package = distribution("imageio-ffmpeg")
        files = package.files or ()
        candidates = [
            Path(str(package.locate_file(item)))
            for item in files
            if str(item).replace("\\", "/").startswith("imageio_ffmpeg/binaries/ffmpeg-")
            and len(PurePosixPath(str(item).replace("\\", "/")).parts) == 3
        ]
        if len(candidates) != 1:
            raise ValueError("expected exactly one package-owned FFmpeg binary")
        executable = candidates[0]
        _no_redirects(executable)
        if not executable.is_absolute() or executable.is_symlink() or not executable.is_file():
            raise ValueError("packaged FFmpeg is missing or redirected")
        environment = os.environ.copy()
        environment.pop("IMAGEIO_FFMPEG_EXE", None)
        environment["PATH"] = ""
        result = subprocess.run(
            [str(executable), "-version"],
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        first_line = result.stdout.splitlines()[0] if result.stdout else ""
        if not first_line.startswith("ffmpeg version "):
            raise ValueError("unexpected packaged FFmpeg version response")
        with executable.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        return ToolObservation(
            tool="ffmpeg",
            status=RuntimeStatus.AVAILABLE,
            executable=str(executable),
            version=first_line,
            sha256=digest,
            package="imageio-ffmpeg",
            package_version=package.version,
            detail="Packaged binary ownership and version checked",
        )
    except PackageNotFoundError:
        return ToolObservation(
            tool="ffmpeg",
            status=RuntimeStatus.MISSING_OPTIONAL_DEPENDENCY,
            detail="imageio-ffmpeg distribution missing",
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return ToolObservation(tool="ffmpeg", status=RuntimeStatus.BLOCKED, detail=str(error))
