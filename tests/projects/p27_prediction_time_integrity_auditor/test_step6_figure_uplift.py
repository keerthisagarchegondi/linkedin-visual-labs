from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.visualization import (
    FIGURE_FILES,
    load_release_context,
    render_all_figures,
)

EXPECTED_STEP5_FINGERPRINT = "7954203abe1cb0f5457c3658f2105cd16a0800528e81723ee970d259afe60ed0"


def _sha(
    path: Path,
) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_release_evidence(
    source: Path,
    target: Path,
) -> None:
    target.mkdir(
        parents=True,
        exist_ok=True,
    )

    for name in (
        "release_data.json",
        "claim_register.json",
    ):
        (target / name).write_bytes((source / name).read_bytes())


def test_frozen_release_context_loads(
    tmp_path: Path,
) -> None:
    repo = Path(__file__).resolve().parents[3]

    assets = repo / "assets" / "p27_prediction_time_integrity_auditor"

    temp_assets = tmp_path / "p27"

    _copy_release_evidence(
        assets,
        temp_assets,
    )

    release, claims = load_release_context(temp_assets)

    assert release["step5_fingerprint_sha256"] == EXPECTED_STEP5_FINGERPRINT

    assert release["safe_release_decision"] == "PASS"

    assert isinstance(
        claims["claims"],
        list,
    )


def test_all_seven_uplift_figures_render_deterministically(
    tmp_path: Path,
) -> None:
    repo = Path(__file__).resolve().parents[3]

    source_assets = repo / "assets" / "p27_prediction_time_integrity_auditor"

    first_root = tmp_path / "first"

    second_root = tmp_path / "second"

    _copy_release_evidence(
        source_assets,
        first_root,
    )

    _copy_release_evidence(
        source_assets,
        second_root,
    )

    first = render_all_figures(first_root)

    second = render_all_figures(second_root)

    assert tuple(path.name for path in first) == FIGURE_FILES

    assert tuple(path.name for path in second) == FIGURE_FILES

    assert len(first) == 7
    assert len(second) == 7

    for first_path, second_path in zip(
        first,
        second,
        strict=True,
    ):
        assert first_path.is_file()
        assert second_path.is_file()

        assert first_path.stat().st_size > 20_000
        assert second_path.stat().st_size > 20_000

        assert _sha(first_path) == _sha(second_path)

        with Image.open(first_path) as image:
            assert image.size == (
                1080,
                1350,
            )

            assert image.mode == "RGB"


def test_release_data_not_mutated_by_rendering(
    tmp_path: Path,
) -> None:
    repo = Path(__file__).resolve().parents[3]

    assets = repo / "assets" / "p27_prediction_time_integrity_auditor"

    temp_assets = tmp_path / "render"

    _copy_release_evidence(
        assets,
        temp_assets,
    )

    before = json.loads((temp_assets / "release_data.json").read_text(encoding="utf-8"))

    render_all_figures(temp_assets)

    after = json.loads((temp_assets / "release_data.json").read_text(encoding="utf-8"))

    assert before == after
