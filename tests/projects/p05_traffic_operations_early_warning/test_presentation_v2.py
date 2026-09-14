"""Deterministic presentation checks without source, model or private references."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest
from PIL import Image

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.presentation_v2 import (
    SCENES,
    TOKENS,
    canonical_metrics,
    extract_tokens,
    scene_index,
    validate_first15,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.render_v2 import (
    Renderer,
    density_layer,
    point,
    text,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.report_v2 import document


def audit_fixture() -> dict[str, Any]:
    return {
        "fixed_window_comparisons": [
            {},
            {
                "entry": 8,
                "exit": 3,
                "imbalance": 5,
                "density_mean": 3.7,
                "movement_index": 0.011305435163455783,
            },
        ],
        "records": [{"metric_id": "warning_state", "exact_value": "WARNING"}],
    }


def test_palette_requires_original_pixel_evidence(tmp_path: Path) -> None:
    path = tmp_path / "reference.png"
    im = Image.new("RGB", (len(TOKENS), 1))
    im.putdata([tuple(bytes.fromhex(value[1:])) for value in TOKENS.values()])
    im.save(path)
    result = extract_tokens([path])
    assert result["tokens"] == TOKENS
    assert all(v["exact_pixel_count"] > 0 for v in result["sampling"].values())
    Image.new("RGB", im.size, "black").save(path)
    with pytest.raises(ValueError, match="Unsampled"):
        extract_tokens([path])


@pytest.mark.parametrize(
    "time,index", [(0, 0), (3.9, 0), (4, 1), (9, 2), (14.99, 2), (15, 3), (35, 7), (44.99, 9)]
)
def test_exact_scene_boundary(time: float, index: int) -> None:
    assert scene_index(time) == index


@pytest.mark.parametrize("time", [-1, 45, 100])
def test_invalid_edit_time_rejected(time: float) -> None:
    with pytest.raises(ValueError):
        scene_index(time)


def test_source_time_is_not_persistence_time() -> None:
    assert SCENES[2][:3] == (9, 15, 1440)
    assert sum(scene[1] - scene[0] for scene in SCENES) == 45


def test_canonical_window_and_units() -> None:
    values = canonical_metrics(audit_fixture())
    assert [v[1] for v in values] == ["WARNING", "3.70", "+5", "3", "0.0113054"]
    assert "Image diagonals/s" in values[4]


@pytest.mark.parametrize(
    "key,value",
    [("density_mean", 4.45), ("exit", 81), ("movement_index", 0.009), ("imbalance", 50)],
)
def test_mixed_window_metrics_rejected(key: str, value: float) -> None:
    audit = audit_fixture()
    audit["fixed_window_comparisons"][1][key] = value
    with pytest.raises(ValueError):
        canonical_metrics(audit)


def story_fixture() -> dict[int, list[str]]:
    return {
        0: ["TRAFFIC-CAMERA ANALYTICS"],
        1: ["DETECT TRACK FLOW METRICS", "3.70 +5 0.0113054"],
        2: [
            "TRAFFIC WARNING QUALIFIED 24:00",
            "CONGESTION NOT CONFIRMED",
            "Independent sustained-queue rule",
            "Withhold a congestion claim",
            "Consider REVIEW / MONITOR",
        ],
    }


def test_first15_requires_rendered_concepts() -> None:
    assert validate_first15(story_fixture())["automated_status"] == "PASS"
    missing = story_fixture()
    missing[2] = ["WARNING 24:00"]
    assert validate_first15(missing)["automated_status"] == "FAIL"


def test_source_overlay_transform() -> None:
    assert point(560, 0) == (0, 0)
    assert point(1280, 720) == (1080, 1080)


def test_observation_density_reconciles_without_duplicate_paths() -> None:
    rows = [
        {"track_id": 1, "source_timestamp": i / 10, "reference_x": 700 + i, "reference_y": 500}
        for i in range(30)
    ]
    layer, evidence = density_layer(pd.DataFrame(rows))
    assert layer.size == (1080, 1080)
    assert evidence["histogram_sum"] == evidence["observations"] == 30
    assert evidence["track_ids"] == 1
    assert evidence["contour_paths"] > 0
    assert evidence["not_physical_density_or_speed"]
    assert layer.getchannel("A").getextrema()[0] == 0


def test_text_overflow_rejected() -> None:
    with pytest.raises(ValueError, match="overflow"):
        text(Image.new("RGB", (100, 20)), (0, 10), "several long words", 20, width=50)


def test_actual_opening_renderer_expresses_contract() -> None:
    renderer = Renderer.__new__(Renderer)
    renderer.kpis = canonical_metrics(audit_fixture())
    source = Image.new("RGB", (1080, 1080), (65, 85, 45))
    transcripts = {}
    with patch.object(Renderer, "scene_pixels", return_value=source):
        for i, t in enumerate((0, 5, 10)):
            frame = renderer.frame(source, t)
            transcripts[i] = frame.info["transcript"]
            # Large unoccluded source area survives composition unchanged.
            assert frame.getpixel((500, 500)) == (65, 85, 45)
    assert validate_first15(transcripts)["automated_status"] == "PASS"


def test_report_primary_kpis_and_rights() -> None:
    renderer = Renderer.__new__(Renderer)
    renderer.kpis = canonical_metrics(audit_fixture())
    page = document(renderer)
    assert page.count('role="tabpanel"') == 5
    assert "PENDING_SOURCE_PERMISSION" in page
    assert "NOT CONFIRMED" in page and "REVIEW / MONITOR" in page
    assert "0.0113054" in page and "3.70" in page
    assert "Lead time is null" in page
    assert "no public clearance" in page.lower()


def test_custom_palette_has_no_default_colormap() -> None:
    import inspect

    source = inspect.getsource(density_layer)
    assert "np.interp" in source
    assert "jet" not in source and "viridis" not in source
    assert 'colors=[TOKENS["density_mid"]]' in source
