"""Small deterministic editorial tests; no real source, model or video required."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from PIL import Image, ImageDraw

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.presentation import (
    KEYFRAMES,
    TITLE,
    Presentation,
    captions,
    checked_path,
    clock,
    interval_tracks,
    normalize_coordinates,
    validate_release,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.reporting import (
    report_html,
    validate_report_assets,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.video import (
    validate_video_metadata,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.visualization import (
    frame,
    project_point,
    static_image,
    text,
)


@pytest.fixture
def example(tmp_path: Path) -> Presentation:
    counts = dict(
        candidate_tracks=17,
        eligible_confirmed_tracks=9,
        completed_dwell_samples=4,
        eligible_entries=7,
        eligible_exits=5,
        incomplete_journeys_excluded_from_dwell=13,
    )
    result = dict(
        result_classification="NO_VISIBLE_QUEUE_EVENT",
        warning_timestamp=1451.0,
        visible_queue_timestamp=None,
        lead_time_seconds=None,
        baseline_false_warning=dict(
            baseline_false_warning_count=0, warning_seconds=0, evaluable_seconds=60
        ),
        transitions=[
            dict(timestamp=1380, state="NORMAL"),
            dict(timestamp=1400, state="WATCH"),
            dict(timestamp=1451, state="WARNING"),
        ],
    )
    changes = {
        key: dict(baseline_median=1.0, screened_interval_median=2.0, relative_change=1.0)
        for key in (
            "density_window_mean",
            "throughput",
            "movement_index",
            "queue_count",
            "median_completed_dwell_seconds",
            "inflow_outflow_imbalance",
        )
    }
    claim = dict(
        claim_id="fixture",
        claim_text="Fixture only",
        classification="DERIVED",
        evidence_path="fixture.json",
        evidence_sha256="a" * 64,
        calculation="fixture",
        unit="count",
        caveat="Synthetic",
        approved_for_publication=True,
        reviewer_status="APPROVED",
    )
    release: dict[str, Any] = dict(
        analytical_status="VERIFIED",
        repository_gates="PASS",
        publication=dict(aggregate_analytical_content_approved=True),
        claims=[claim],
        result=result,
        eligibility=counts,
        metric_changes=changes,
        baseline={},
        screened_comparison_interval=[1440, 1650],
        unmatched_warning=dict(warning_state_seconds=12),
        recommendation=dict(
            wording="Consider reviewing fixture evidence.", alternative_action="MONITOR"
        ),
    )

    def point(x: float, y: float) -> dict[str, float]:
        return dict(x=x, y=y)

    geometry = dict(
        roi=dict(points=[point(0.48, 0.47), point(0.96, 0.58), point(0.96, 0.73)]),
        queue_zone=dict(points=[point(0.6, 0.59), point(0.9, 0.63), point(0.9, 0.68)]),
        entry=dict(start=point(0.92, 0.6), end=point(0.92, 0.7)),
        exit=dict(start=point(0.5, 0.535), end=point(0.64, 0.535)),
    )
    trajectories = pd.DataFrame(
        dict(
            track_id=[1, 1, 2],
            source_timestamp=[1200, 1200.4, 1800],
            confirmed=[True, True, True],
            reference_x=[0.8, 0.79, 0.6],
            reference_y=[0.62, 0.62, 0.6],
        )
    )
    metrics = pd.DataFrame(
        dict(
            timestamp=[1260, 1400, 1799],
            density_window_mean=[1.0, 2.0, 1.0],
            throughput=[1.0, 2.0, 1.0],
            movement_index=[0.01, 0.02, 0.01],
        )
    )
    rules = dict(
        queue=dict(
            persistence_seconds=120, queue_count=2, zone_occupancy=3, movement_ceiling=0.005
        ),
        warning=dict(minimum_drivers=3, persistence_seconds=30),
        baseline=[1260, 1380],
        evaluation_start=1380,
        evaluation_end_exclusive=1800,
    )
    return Presentation(
        tmp_path,
        tmp_path,
        release,
        geometry,
        trajectories,
        pd.DataFrame(dict(track_id=[1], completed_eligible=[True])),
        metrics,
        rules,
        pd.DataFrame(dict(warning_timestamp=[1441.0, 1461.0])),
        {"artifacts": {}},
    )


def test_static_dimensions_and_trajectory_pixels(example: Presentation) -> None:
    im = static_image(example)
    assert im.size == (1080, 1350)
    x, y = project_point(0.795, 0.62, 490)
    assert im.getpixel((x, y)) != (52, 73, 93)
    assert TITLE == "Ten minutes of traffic in one frame"


def test_pixel_coordinates_use_verified_dimensions() -> None:
    pixels = pd.DataFrame(dict(reference_x=[640.0], reference_y=[360.0]))
    normalized = normalize_coordinates(pixels, 1280, 720)
    assert normalized.reference_x.tolist() == [0.5]
    assert normalized.reference_y.tolist() == [0.5]
    assert pixels.reference_x.tolist() == [640.0]


def test_invalid_geometry_dimensions_fail() -> None:
    pixels = pd.DataFrame(dict(reference_x=[1500.0], reference_y=[360.0]))
    with pytest.raises(ValueError):
        normalize_coordinates(pixels, 1280, 720)
    with pytest.raises(ValueError):
        normalize_coordinates(pixels, 0, 720)


def test_interval_is_half_open_and_confirmed(example: Presentation) -> None:
    selected = interval_tracks(example.trajectories, 1200, 1800)
    assert selected.track_id.tolist() == [1, 1]
    with pytest.raises(ValueError):
        interval_tracks(example.trajectories, 0, 599)


def test_null_time_is_not_zero() -> None:
    assert clock(None) == "Not reportable"
    assert clock(0) == "00:00"


def test_changed_release_values_propagate(example: Presentation) -> None:
    example.release["screened_comparison_interval"] = [1452, 1600]
    content = report_html(example)
    assert "24:11" in content
    assert "17 candidates" in content
    assert "24:00" not in content
    assert "572" not in content
    assert "24:11" in captions(example)[2][1]


@pytest.mark.parametrize("field", ["analytical_status", "repository_gates", "claims"])
def test_missing_release_approval_rejected(example: Presentation, field: str) -> None:
    bad = copy.deepcopy(example.release)
    bad[field] = None
    with pytest.raises(ValueError):
        validate_release(bad)


def test_denied_public_claim_rejected(example: Presentation) -> None:
    bad = copy.deepcopy(example.release)
    bad["claims"][0]["approved_for_publication"] = False
    with pytest.raises(ValueError):
        validate_release(bad)


def test_inconsistent_queue_result_rejected(example: Presentation) -> None:
    bad = copy.deepcopy(example.release)
    bad["result"]["lead_time_seconds"] = 0
    with pytest.raises(ValueError):
        validate_release(bad)


def test_unapproved_aggregate_rejected(example: Presentation) -> None:
    bad = copy.deepcopy(example.release)
    bad["publication"]["aggregate_analytical_content_approved"] = False
    with pytest.raises(ValueError):
        validate_release(bad)


def test_stale_hash_rejected(tmp_path: Path) -> None:
    path = tmp_path / "x.json"
    path.write_text("{}")
    with pytest.raises(ValueError):
        checked_path(tmp_path, dict(path="x.json", sha256="a" * 64))


def test_foreign_path_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        checked_path(tmp_path, dict(path="../outside.json", sha256="a" * 64))


@pytest.mark.parametrize("number", KEYFRAMES)
def test_all_required_scenes_render(example: Presentation, number: int) -> None:
    assert frame(example, number).size == (1080, 1350)


def test_actual_animation_changes_pixels(example: Presentation) -> None:
    assert frame(example, 450).tobytes() != frame(example, 550).tobytes()


def test_video_contract_and_rejection() -> None:
    good = dict(
        width=1080,
        height=1350,
        fps=30.0,
        codec="h264",
        pixel_format="yuv420p",
        frames=1350,
        duration=45.0,
    )
    validate_video_metadata(good)
    for key, value in [
        ("fps", 25),
        ("codec", "vp9"),
        ("pixel_format", "yuv444p"),
        ("duration", 43),
    ]:
        with pytest.raises(ValueError):
            validate_video_metadata({**good, key: value})


def test_scene_order_nulls_and_captions(example: Presentation) -> None:
    scenes = captions(example)
    assert len(scenes) == 10 and all(all(part for part in scene) for scene in scenes)
    assert "Not reportable" in scenes[2][2]
    assert "120s" in scenes[7][2]
    assert "Illustrative" in scenes[8][2]
    assert KEYFRAMES[-1] / 30 < 45


def test_report_navigation_and_responsive_structure(example: Presentation) -> None:
    page = report_html(example)
    assert page.count('role="tab"') == 5
    assert page.count('role="tabpanel"') == 5
    assert "ArrowRight" in page and "aria-controls" in page
    assert "@media(max-width:700px)" in page
    assert 'name="viewport"' in page


def test_report_rights_and_no_raw_assets(example: Presentation) -> None:
    page = report_html(example)
    assert "no source pixels" in page
    assert 'src="assets/project6_linkedin_web.mp4"' in page
    assert "data/raw/" not in page
    assert 'src="cam_3' not in page
    assert "NO_VISIBLE_QUEUE_EVENT" in page
    assert "47-second" not in page


def test_deterministic_report_and_summary(example: Presentation) -> None:
    assert report_html(example) == report_html(example)
    assert example.summary()["result"]["lead_time_seconds"] is None
    assert example.summary()["source_pixels"] is False


def test_overflow_and_frame_range_fail_closed(example: Presentation) -> None:
    draw = ImageDraw.Draw(Image.new("RGB", (100, 100)))
    with pytest.raises(ValueError):
        text(draw, (0, 0), "unbreakable" * 40, width=100)
    with pytest.raises(ValueError):
        frame(example, 1350)


@pytest.mark.parametrize("reference", ["missing.png", "../outside.png", "https://remote/x.png"])
def test_missing_or_foreign_assets_rejected(tmp_path: Path, reference: str) -> None:
    (tmp_path / "index.html").write_text(f'<img src="{reference}">', encoding="utf-8")
    with pytest.raises(ValueError):
        validate_report_assets(tmp_path)


def test_portable_assets_accepted(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text('<a href="report_data.json">Data</a>', encoding="utf-8")
    (tmp_path / "report_data.json").write_text("{}", encoding="utf-8")
    assert validate_report_assets(tmp_path) == ["report_data.json"]
