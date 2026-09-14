"""Small YAML fixtures exercise loading without creating analytical directories."""

from __future__ import annotations

import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from linkedin_visual_labs.common.config import ConfigurationError
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.config import (
    DEFAULT_CONFIG_PATH,
    contained_path,
    load_traffic_config,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.models import (
    OUTPUT,
    RAW,
    ClaimRecord,
    EvidenceReference,
    SourceStatus,
    TrafficOperationsConfig,
)

ROOT = Path(__file__).resolve().parents[3]


def payload() -> dict[str, Any]:
    return load_traffic_config(repository_root=ROOT).model_dump(mode="json")


def write_fixture(root: Path, data: dict[str, Any]) -> None:
    """Fixture setup writes YAML only; loading must not write anything."""
    directory = root / "configs"
    directory.mkdir()
    (root / DEFAULT_CONFIG_PATH).write_text(yaml.safe_dump(data), encoding="utf-8")


def test_checked_in_config_is_unapproved_non_executable_and_deterministic() -> None:
    first = load_traffic_config(repository_root=ROOT)
    second = load_traffic_config(repository_root=ROOT)
    assert first.model_dump_json() == second.model_dump_json()
    assert first.source.status == SourceStatus.SOURCE_REVIEW_REQUIRED
    assert first.source.candidate is None
    assert not first.queue_outcome.executable and not first.warning.executable
    assert first.recommendations.actions == ()
    assert first.outputs.static.source_interval is None
    assert first.analysis.calibration.status == "RELATIVE_ONLY"
    assert first.metrics.low_motion_threshold is None
    assert isinstance(first.outputs.report_tabs, tuple)
    with pytest.raises(ValidationError):
        first.source.status = SourceStatus.SOURCE_APPROVED


def test_loader_has_no_directory_or_file_side_effects(tmp_path: Path) -> None:
    write_fixture(tmp_path, payload())
    before = {
        p.relative_to(tmp_path): p.read_bytes() if p.is_file() else None
        for p in tmp_path.rglob("*")
    }
    load_traffic_config(repository_root=tmp_path)
    after = {
        p.relative_to(tmp_path): p.read_bytes() if p.is_file() else None
        for p in tmp_path.rglob("*")
    }
    assert before == after


@pytest.mark.parametrize(
    "section",
    [
        "project",
        "source",
        "analysis",
        "metrics",
        "queue_outcome",
        "warning",
        "recommendations",
        "privacy",
        "outputs",
    ],
)
def test_unknown_nested_fields_rejected(tmp_path: Path, section: str) -> None:
    data = payload()
    data[section]["unexpected"] = True
    write_fixture(tmp_path, data)
    with pytest.raises(ConfigurationError, match="Extra inputs"):
        load_traffic_config(repository_root=tmp_path)


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("metrics", "throughput_window_seconds", True),
        ("metrics", "throughput_window_seconds", "300"),
        ("metrics", "low_motion_threshold", float("nan")),
        ("metrics", "low_motion_threshold", float("inf")),
        ("source", "status", "ACCEPTED"),
        ("source", "status", "SOURCE_PENDING"),
        ("privacy", "plate_ocr", 0),
        ("analysis", "sampling_rescales_time", "false"),
    ],
)
def test_invalid_yaml_variants(tmp_path: Path, section: str, field: str, value: object) -> None:
    data = payload()
    data[section][field] = value
    write_fixture(tmp_path, data)
    with pytest.raises(ConfigurationError):
        load_traffic_config(repository_root=tmp_path)


@pytest.mark.parametrize(
    "path",
    [
        "../configs/file.yaml",
        "/foreign/file.yaml",
        "D:/linkedin-visual-labs/configs/file.yaml",
        "Z:/file.yaml",
        "//server/share/file.yaml",
        "configs/../../file.yaml",
        "data/raw/p02_monopoly_ai/file.yaml",
    ],
)
def test_foreign_config_paths_are_rejected(tmp_path: Path, path: str) -> None:
    with pytest.raises(ConfigurationError):
        load_traffic_config(path, repository_root=tmp_path)


def test_relative_root_rejected() -> None:
    with pytest.raises(ConfigurationError, match="absolute"):
        load_traffic_config(repository_root=Path("relative"))


def test_reparse_component_rejected_without_following_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A Windows junction is modeled without privileged creation or external access.
    directory = tmp_path / "configs"
    directory.mkdir()
    original = Path.lstat

    class ReparseStat:
        st_mode = stat.S_IFDIR
        st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT

    def redirected(path: Path) -> Any:
        return ReparseStat() if path == directory else original(path)

    monkeypatch.setattr(Path, "lstat", redirected)
    with pytest.raises(ConfigurationError, match="redirected"):
        contained_path(tmp_path, "configs/fixture.yaml", Path("configs"))


def test_symlink_component_rejected_without_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    directory = tmp_path / "configs"
    directory.mkdir()
    original = Path.lstat

    class LinkStat:
        st_mode = stat.S_IFLNK
        st_file_attributes = 0

    def redirected(path: Path) -> Any:
        return LinkStat() if path == directory else original(path)

    monkeypatch.setattr(Path, "lstat", redirected)
    with pytest.raises(ConfigurationError, match="redirected"):
        contained_path(tmp_path, "configs/fixture.yaml", Path("configs"))


def test_pending_source_reference_does_not_create_raw_storage(tmp_path: Path) -> None:
    data = payload()
    data["source"]["status"] = "SOURCE_PENDING"
    data["source"]["candidate"] = {
        "source_id": "synthetic",
        "source_name": "Synthetic metadata",
        "raw_file_path": f"{RAW}/future.mp4",
        "evidence": [{"evidence_id": "planned", "path": f"{OUTPUT}/manifests/future.json"}],
    }
    write_fixture(tmp_path, data)
    assert load_traffic_config(repository_root=tmp_path).source.status == "SOURCE_PENDING"
    assert not (tmp_path / "data").exists()
    assert not (tmp_path / "outputs").exists()


def test_cross_contract_source_and_freeze_guards() -> None:
    data = payload()
    data["outputs"]["static"]["source_interval"] = {"start_seconds": 0, "end_seconds": 600}
    with pytest.raises(ValidationError, match="approved source"):
        TrafficOperationsConfig.model_validate(data)
    data = payload()
    data["source"]["candidate"] = {"source_id": "fixture", "source_name": "Synthetic"}
    with pytest.raises(ValidationError, match="status mismatch"):
        TrafficOperationsConfig.model_validate(data)


def test_physical_claim_without_calibration_is_rejected() -> None:
    with pytest.raises(ValidationError, match="calibration"):
        ClaimRecord.model_validate(
            {
                "claim_id": "fixture",
                "claim_text": "Synthetic distance",
                "classification": "UNSUPPORTED",
                "unit": "METERS",
            }
        )


@pytest.mark.parametrize("suffix", ["file.json", "private/file.json", "data"])
def test_evidence_output_category_is_restricted(suffix: str) -> None:
    with pytest.raises(ValidationError, match="output category"):
        EvidenceReference(evidence_id="synthetic", path=f"{OUTPUT}/{suffix}")


def test_import_and_config_without_cv_or_media_runtime(tmp_path: Path) -> None:
    code = """
import importlib.abc
import sys
from pathlib import Path
blocked = {'cv2', 'onnx', 'onnxruntime', 'ultralytics', 'yolox', 'bytetrack',
           'byte_tracker', 'torch', 'ffmpeg', 'imageio_ffmpeg'}
class NoRuntime(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if (fullname.split('.')[0] in blocked
                or fullname.endswith('.p05_traffic_operations_early_warning.runtime')):
            raise ImportError('Forbidden runtime import: ' + fullname)
sys.meta_path.insert(0, NoRuntime())
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.config import (
    load_traffic_config,
)
config = load_traffic_config(repository_root=Path(sys.argv[1]))
assert not config.warning.executable
assert not blocked.intersection(sys.modules)
print('CONTRACT_IMPORT_SMOKE_PASS')
"""
    result = subprocess.run(
        [sys.executable, "-B", "-c", code, str(ROOT)],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CONTRACT_IMPORT_SMOKE_PASS" in result.stdout
