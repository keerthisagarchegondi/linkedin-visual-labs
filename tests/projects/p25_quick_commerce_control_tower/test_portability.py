"""Configured proof containment and package-owned cross-platform FFmpeg resolution."""

from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from linkedin_visual_labs.common.paths import UnsafeOutputPathError
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import evaluation
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_media as media,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    build_pipeline_context,
)


def test_proof_uses_configured_boundary(tmp_path: Path) -> None:
    context = build_pipeline_context()
    context = replace(
        context,
        paths=replace(
            context.paths, repository_root=tmp_path / "checkout", output_root=tmp_path / "run"
        ),
    )
    proof = tmp_path / "run" / "proof.json"
    assert evaluation.resolve_validation_record(context, proof) == proof.resolve()
    for outside in (
        tmp_path / "proof.json",
        tmp_path / "checkout" / "proof.json",
        proof.parent / ".." / "escape.json",
    ):
        with pytest.raises(UnsafeOutputPathError):
            evaluation.run_evaluation(context, outside)


def test_production_proof_paths_remain_compatible() -> None:
    context = build_pipeline_context()
    relative = Path("outputs/p25_quick_commerce_control_tower/manifests/forecast_validation.json")
    expected = context.paths.manifests / "forecast_validation.json"
    assert evaluation.resolve_validation_record(context, relative) == expected.resolve()
    assert evaluation.resolve_validation_record(context, expected) == expected.resolve()


@pytest.mark.parametrize("name", ["ffmpeg-linux-x86_64-v7.0.2", "ffmpeg-win-x86_64-v7.1.exe"])
def test_api_result_is_not_filtered_by_filename_suffix(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / name
    executable.write_bytes(b"package-owned-test-binary")
    monkeypatch.setenv("IMAGEIO_FFMPEG_EXE", "untrusted")
    original_path = os.environ["PATH"]
    calls = 0

    def run(command: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if calls == 1:
            assert "IMAGEIO_FFMPEG_EXE" not in kwargs["env"]
            assert kwargs["env"]["PATH"] == ""
            assert "get_ffmpeg_exe" in command[-1]
            return subprocess.CompletedProcess(command, 0, str(executable) + "\n", "")
        assert command == [str(executable.resolve()), "-version"]
        return subprocess.CompletedProcess(command, 0, "ffmpeg version test\n", "")

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(
        media,
        "distribution",
        lambda _: SimpleNamespace(files=[executable], locate_file=lambda p: p),
    )
    assert media.packaged_ffmpeg() == (executable.resolve(), "ffmpeg version test")
    assert os.environ["IMAGEIO_FFMPEG_EXE"] == "untrusted"
    assert os.environ["PATH"] == original_path


def test_api_fallback_outside_package_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "ffmpeg"
    executable.write_bytes(b"not-owned-by-package")
    monkeypatch.setattr(
        subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=str(executable))
    )
    monkeypatch.setattr(media, "distribution", lambda _: SimpleNamespace(files=()))
    with pytest.raises(ValueError, match="packaged FFmpeg"):
        media.packaged_ffmpeg()
