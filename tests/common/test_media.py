"""Tests for PNG, video metadata, and manifest utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linkedin_visual_labs.common.media import (
    MediaValidationError,
    build_generation_manifest,
    read_png_dimensions,
    save_figure_png,
    validate_png_dimensions,
    write_generation_manifest,
)
from linkedin_visual_labs.common.plotting import (
    CanvasSpec,
    create_canvas,
)


def test_save_figure_png_has_exact_dimensions(
    tmp_path: Path,
) -> None:
    spec = CanvasSpec(
        width_px=320,
        height_px=400,
        dpi=100,
        safe_margin_px=20,
    )

    figure, axes = create_canvas(
        spec=spec,
    )

    axes.plot(
        [0, 1],
        [0, 1],
    )

    output = tmp_path / "figure.png"

    metadata = save_figure_png(
        figure,
        output,
        spec=spec,
    )

    assert output.is_file()
    assert metadata.width_px == 320
    assert metadata.height_px == 400


def test_read_png_dimensions_reads_ihdr(
    tmp_path: Path,
) -> None:
    spec = CanvasSpec(
        width_px=200,
        height_px=300,
        dpi=100,
        safe_margin_px=10,
    )

    figure, _ = create_canvas(
        spec=spec,
    )

    output = tmp_path / "figure.png"

    save_figure_png(
        figure,
        output,
        spec=spec,
    )

    metadata = read_png_dimensions(output)

    assert metadata.width_px == 200
    assert metadata.height_px == 300
    assert metadata.format == "PNG"


def test_validate_png_dimensions_rejects_wrong_size(
    tmp_path: Path,
) -> None:
    spec = CanvasSpec(
        width_px=200,
        height_px=300,
        dpi=100,
        safe_margin_px=10,
    )

    figure, _ = create_canvas(
        spec=spec,
    )

    output = tmp_path / "figure.png"

    save_figure_png(
        figure,
        output,
        spec=spec,
    )

    with pytest.raises(
        MediaValidationError,
        match="width mismatch",
    ):
        validate_png_dimensions(
            output,
            expected_width=201,
            expected_height=300,
        )


def test_build_generation_manifest_contains_required_fields(
    tmp_path: Path,
) -> None:
    manifest = build_generation_manifest(
        project_id="p01_bayesian_dice",
        asset_name="test_asset.png",
        configuration_path="configs/p01_bayesian_dice.yaml",
        random_seed=20260816,
        width=1080,
        height=1350,
        repository_root=tmp_path,
        metrics={
            "posterior_loaded": 0.91,
        },
        generation_timestamp="2026-08-16T00:00:00+00:00",
        git_commit="abc123",
    )

    assert manifest == {
        "project_id": "p01_bayesian_dice",
        "asset_name": "test_asset.png",
        "generation_timestamp": ("2026-08-16T00:00:00+00:00"),
        "git_commit": "abc123",
        "configuration_path": ("configs/p01_bayesian_dice.yaml"),
        "random_seed": 20260816,
        "width": 1080,
        "height": 1350,
        "frame_rate": None,
        "duration_seconds": None,
        "metrics": {
            "posterior_loaded": 0.91,
        },
    }


def test_write_generation_manifest_is_valid_json(
    tmp_path: Path,
) -> None:
    manifest = {
        "project_id": "p04_zombie_escape",
        "asset_name": "routes.png",
        "random_seed": 42,
    }

    output = tmp_path / "manifest.json"

    result = write_generation_manifest(
        manifest,
        output,
    )

    payload = json.loads(
        result.read_text(
            encoding="utf-8",
        )
    )

    assert payload == manifest
