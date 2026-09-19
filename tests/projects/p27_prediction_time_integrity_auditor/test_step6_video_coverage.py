from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import (
    video,
)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def source_assets() -> Path:
    return repository_root() / "assets" / "p27_prediction_time_integrity_auditor"


def copy_evidence(
    target: Path,
) -> Path:
    target.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name in (
        "release_data.json",
        "claim_register.json",
    ):
        (target / name).write_bytes((source_assets() / name).read_bytes())

    return target


def valid_probe(
    *,
    filename: str = "video.mp4",
) -> dict[str, Any]:
    return {
        "path": filename,
        "width": 1080,
        "height": 1350,
        "codec": "h264",
        "pixel_format": "yuv420p",
        "frame_rate": 30.0,
        "nb_frames": 1350,
        "duration_seconds": 45.0,
        "size_bytes": 200_000,
        "sha256": "a" * 64,
    }


def test_contract_helpers_and_hash(
    tmp_path: Path,
) -> None:
    contract = video.VideoContract()

    assert contract.to_dict() == {
        "width": 1080,
        "height": 1350,
        "fps": 30,
        "duration_seconds": 45.0,
        "frame_count": 1350,
    }

    assert video._ease(-1.0) == 0.0
    assert video._ease(2.0) == 1.0

    assert (
        video._progress(
            0.0,
            1.0,
            1.0,
        )
        == 1.0
    )

    assert (
        video._progress(
            -100.0,
            0.0,
            1.0,
        )
        == 0.0
    )

    assert (
        video._progress(
            100.0,
            0.0,
            1.0,
        )
        == 1.0
    )

    path = tmp_path / "hash.bin"

    path.write_bytes(b"project7")

    digest = video.file_sha256(path)

    assert len(digest) == 64


def test_load_video_evidence_validation(
    tmp_path: Path,
) -> None:
    root = copy_evidence(tmp_path / "assets")

    release, claims = video.load_video_evidence(root)

    assert release["step5_fingerprint_sha256"] == video.STEP5_FINGERPRINT

    assert isinstance(
        claims,
        dict,
    )

    release_path = root / "release_data.json"

    claims_path = root / "claim_register.json"

    original_release = release_path.read_bytes()
    original_claims = claims_path.read_bytes()

    release_path.write_text(
        "[]\n",
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="release_data",
    ):
        video.load_video_evidence(root)

    release_path.write_bytes(original_release)

    claims_path.write_text(
        "[]\n",
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="claim_register",
    ):
        video.load_video_evidence(root)

    claims_path.write_bytes(original_claims)

    payload = json.loads(release_path.read_text(encoding="utf-8"))

    payload["step5_fingerprint_sha256"] = "drift"

    release_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="fingerprint drift",
    ):
        video.load_video_evidence(root)

    release_path.write_bytes(original_release)

    payload = json.loads(release_path.read_text(encoding="utf-8"))

    payload["release_status"] = "BLOCK"

    release_path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match="not PASS",
    ):
        video.load_video_evidence(root)


def test_case_lookup_and_claim_guards() -> None:
    release, claims = video.load_video_evidence(source_assets())

    row = video._case_model_row(
        release,
        "S1_CURRENT_CALL_DURATION",
        "histogram_gradient_boosting",
    )

    assert row["case_id"] == "S1_CURRENT_CALL_DURATION"

    broken_release = dict(release)

    broken_release["leakage_model_results"] = {}

    with pytest.raises(
        RuntimeError,
        match="missing",
    ):
        video._case_model_row(
            broken_release,
            "S1",
            "model",
        )

    with pytest.raises(
        RuntimeError,
        match="exactly one",
    ):
        video._case_model_row(
            release,
            "NO_SUCH_CASE",
            "NO_SUCH_MODEL",
        )

    approved = video._approved_claim_ids(claims)

    assert set(video.CLAIM_IDS_USED).issubset(approved)

    with pytest.raises(
        RuntimeError,
        match="entries missing",
    ):
        video._approved_claim_ids(
            {
                "claims": {},
            }
        )

    with pytest.raises(
        RuntimeError,
        match="unapproved claims",
    ):
        video._approved_claim_ids(
            {
                "claims": [],
            }
        )


def test_render_frame_clamps_time() -> None:
    release, claims = video.load_video_evidence(source_assets())

    before = video.render_frame(
        release,
        claims,
        -100.0,
    )

    after = video.render_frame(
        release,
        claims,
        1000.0,
    )

    assert before.size == (
        1080,
        1350,
    )

    assert after.size == (
        1080,
        1350,
    )


def test_ffmpeg_path_prefers_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    expected = tmp_path / "ffmpeg.exe"

    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: str(expected) if name == "ffmpeg" else None,
    )

    assert video._ffmpeg_path() == expected.resolve()


def test_ffmpeg_path_imageio_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake = tmp_path / "imageio-ffmpeg.exe"

    fake.write_bytes(b"x")

    monkeypatch.setattr(
        shutil,
        "which",
        lambda _name: None,
    )

    module = SimpleNamespace(get_ffmpeg_exe=lambda: str(fake))

    monkeypatch.setitem(
        sys.modules,
        "imageio_ffmpeg",
        module,
    )

    assert video._ffmpeg_path() == fake.resolve()


def test_ffprobe_path_resolution(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ffmpeg = tmp_path / "ffmpeg.exe"

    ffmpeg.write_bytes(b"x")

    direct = tmp_path / "from-path" / "ffprobe.exe"

    monkeypatch.setattr(
        shutil,
        "which",
        lambda name: str(direct) if name == "ffprobe" else None,
    )

    assert video._ffprobe_path(ffmpeg) == direct.resolve()

    monkeypatch.setattr(
        shutil,
        "which",
        lambda _name: None,
    )

    sibling = tmp_path / "ffprobe.exe"

    sibling.write_bytes(b"x")

    assert video._ffprobe_path(ffmpeg) == sibling.resolve()

    sibling.unlink()

    with pytest.raises(
        RuntimeError,
        match="could not be resolved",
    ):
        video._ffprobe_path(ffmpeg)


def test_validate_probe_success_and_failures() -> None:
    probe = valid_probe()

    video._validate_probe(probe)

    cases: tuple[
        tuple[str, object, str],
        ...,
    ] = (
        (
            "width",
            999,
            "width mismatch",
        ),
        (
            "height",
            999,
            "height mismatch",
        ),
        (
            "codec",
            "vp9",
            "codec mismatch",
        ),
        (
            "pixel_format",
            "yuv444p",
            "pixel format mismatch",
        ),
        (
            "frame_rate",
            29.0,
            "frame rate mismatch",
        ),
        (
            "duration_seconds",
            10.0,
            "duration outside",
        ),
        (
            "nb_frames",
            100,
            "frame count mismatch",
        ),
    )

    for (
        key,
        value,
        message,
    ) in cases:
        candidate = dict(probe)

        candidate[key] = value

        with pytest.raises(
            RuntimeError,
            match=message,
        ):
            video._validate_probe(candidate)

    no_frame_count = dict(probe)

    no_frame_count["nb_frames"] = None

    video._validate_probe(no_frame_count)


def test_write_keyframes_contact_sheet_thumbnail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    release, claims = video.load_video_evidence(source_assets())

    monkeypatch.setattr(
        video,
        "render_frame",
        lambda *_args, **_kwargs: Image.new(
            "RGB",
            (
                40,
                50,
            ),
            (
                1,
                2,
                3,
            ),
        ),
    )

    keyframes = video._write_keyframes(
        release,
        claims,
        tmp_path / "keyframes",
    )

    assert len(keyframes) == 10

    sheet = tmp_path / "sheet.png"

    video._write_contact_sheet(
        keyframes,
        sheet,
    )

    assert sheet.is_file()

    with Image.open(sheet) as image:
        assert image.size == (
            1020,
            510,
        )

    thumbnail = tmp_path / "thumbnail.png"

    video._write_thumbnail(
        release,
        claims,
        thumbnail,
    )

    assert thumbnail.is_file()

    with pytest.raises(
        RuntimeError,
        match="ten keyframes",
    ):
        video._write_contact_sheet(
            keyframes[:9],
            tmp_path / "bad.png",
        )


def test_encode_primary_without_real_ffmpeg(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    release, claims = video.load_video_evidence(source_assets())

    output = tmp_path / "primary.mp4"

    fake_ffmpeg = tmp_path / "ffmpeg.exe"

    fake_ffmpeg.write_bytes(b"x")

    monkeypatch.setattr(
        video,
        "_ffmpeg_path",
        lambda: fake_ffmpeg,
    )

    monkeypatch.setattr(
        video,
        "VIDEO_FRAME_COUNT",
        3,
    )

    monkeypatch.setattr(
        video,
        "VIDEO_WIDTH",
        2,
    )

    monkeypatch.setattr(
        video,
        "VIDEO_HEIGHT",
        2,
    )

    monkeypatch.setattr(
        video,
        "render_frame",
        lambda *_args, **_kwargs: Image.new(
            "RGB",
            (
                2,
                2,
            ),
        ),
    )

    class FakeInput:
        def __init__(
            self,
        ) -> None:
            self.writes = 0
            self.closed = False

        def write(
            self,
            data: bytes,
        ) -> int:
            self.writes += 1
            return len(data)

        def close(
            self,
        ) -> None:
            self.closed = True

    class FakeError:
        def read(
            self,
        ) -> bytes:
            return b""

    class FakeProcess:
        def __init__(
            self,
            destination: Path,
        ) -> None:
            self.stdin = FakeInput()
            self.stdout = None
            self.stderr = FakeError()
            self.destination = destination

        def wait(
            self,
        ) -> int:
            self.destination.write_bytes(b"x" * 100_001)

            return 0

    def fake_popen(
        command: list[str],
        **_kwargs: Any,
    ) -> FakeProcess:
        return FakeProcess(Path(command[-1]))

    monkeypatch.setattr(
        subprocess,
        "Popen",
        fake_popen,
    )

    video._encode_primary(
        release,
        claims,
        output,
    )

    assert output.is_file()
    assert output.stat().st_size > 100_000


def test_encode_web_without_real_ffmpeg(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    primary = tmp_path / "primary.mp4"

    primary.write_bytes(b"x")

    output = tmp_path / "web.mp4"

    fake_ffmpeg = tmp_path / "ffmpeg.exe"

    fake_ffmpeg.write_bytes(b"x")

    monkeypatch.setattr(
        video,
        "_ffmpeg_path",
        lambda: fake_ffmpeg,
    )

    def fake_run(
        command: list[str],
        **_kwargs: Any,
    ) -> SimpleNamespace:
        Path(command[-1]).write_bytes(b"x" * 100_001)

        return SimpleNamespace(
            returncode=0,
            stderr=b"",
        )

    monkeypatch.setattr(
        subprocess,
        "run",
        fake_run,
    )

    video._encode_web(
        primary,
        output,
    )

    assert output.stat().st_size > 100_000


def test_probe_video_without_real_ffprobe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    media = tmp_path / "media.mp4"

    media.write_bytes(b"x" * 100_001)

    fake_ffmpeg = tmp_path / "ffmpeg.exe"

    fake_probe = tmp_path / "ffprobe.exe"

    fake_ffmpeg.write_bytes(b"x")

    fake_probe.write_bytes(b"x")

    monkeypatch.setattr(
        video,
        "_ffmpeg_path",
        lambda: fake_ffmpeg,
    )

    monkeypatch.setattr(
        video,
        "_ffprobe_path",
        lambda _ffmpeg: fake_probe,
    )

    payload = {
        "streams": [
            {
                "codec_name": "h264",
                "pix_fmt": "yuv420p",
                "width": 1080,
                "height": 1350,
                "avg_frame_rate": "30/1",
                "nb_frames": "1350",
                "duration": "45.0",
            }
        ],
        "format": {
            "duration": "45.0",
            "size": "100001",
        },
    }

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(payload),
            stderr="",
        ),
    )

    result = video._probe_video(media)

    assert result["codec"] == "h264"

    assert result["frame_rate"] == 30.0

    assert result["duration_seconds"] == 45.0


def test_build_video_outputs_without_encoding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    assets = copy_evidence(tmp_path / "assets")

    def fake_encode(
        _release: dict[str, Any],
        _claims: dict[str, Any],
        output: Path,
    ) -> None:
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_bytes(b"x" * 100_001)

    def fake_web(
        _primary: Path,
        output: Path,
    ) -> None:
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output.write_bytes(b"y" * 100_001)

    monkeypatch.setattr(
        video,
        "_encode_primary",
        fake_encode,
    )

    monkeypatch.setattr(
        video,
        "_encode_web",
        fake_web,
    )

    monkeypatch.setattr(
        video,
        "render_frame",
        lambda *_args, **_kwargs: Image.new(
            "RGB",
            (
                40,
                50,
            ),
            (
                10,
                20,
                30,
            ),
        ),
    )

    def fake_probe(
        path: Path,
    ) -> dict[str, Any]:
        return valid_probe(filename=path.name)

    monkeypatch.setattr(
        video,
        "_probe_video",
        fake_probe,
    )

    manifest = video.build_video_outputs(assets)

    assert manifest["scope"] == "PROJECT7_STEP6_VIDEO"

    assert manifest["keyframe_count"] == 10

    assert manifest["muted_comprehension"] is True

    assert manifest["evidence_policy"]["business_logic_recomputed"] is False

    manifest_path = assets / "video" / "video_manifest.json"

    assert manifest_path.is_file()

    loaded = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert loaded["manifest_sha256"] == manifest["manifest_sha256"]


def test_probe_validation_failure_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    media = tmp_path / "media.mp4"

    media.write_bytes(b"x")

    fake = tmp_path / "fake.exe"

    fake.write_bytes(b"x")

    monkeypatch.setattr(
        video,
        "_ffmpeg_path",
        lambda: fake,
    )

    monkeypatch.setattr(
        video,
        "_ffprobe_path",
        lambda _ffmpeg: fake,
    )

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="probe failed",
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="ffprobe failed",
    ):
        video._probe_video(media)
