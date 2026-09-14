"""Deterministic admission and geometry fixtures, independent of video/CV packages."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.aicity_source import (
    CandidateScore,
    EpisodeWindows,
    SourceAdmission,
    TechnicalScreen,
    parse_inventory,
    shortlist,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.calibration import (
    Geometry,
    Line,
    Point,
    Polygon,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.source import (
    Interval,
    VideoMetadata,
)


def windows() -> EpisodeWindows:
    return EpisodeWindows(
        duration_seconds=1800,
        baseline=Interval(start=1260, end=1380),
        buildup=Interval(start=1380, end=1440),
        degraded=Interval(start=1440, end=1650),
        static=Interval(start=1200, end=1800),
    )


def admission() -> SourceAdmission:
    return SourceAdmission(
        metadata=VideoMetadata(
            camera="fixture",
            sha256="a" * 64,
            byte_size=100,
            duration_seconds=1800,
            width=1280,
            height=720,
            nominal_fps=10,
            frame_count=18000,
            time_base_denominator=10240,
            first_pts=0,
            last_pts=17999 * 1024,
            pts_step=1024,
            codec="fixture",
            audio_present=False,
            decode_ok=True,
        ),
        screen=TechnicalScreen(
            duration_seconds=1800,
            width=1280,
            height=720,
            fixed_camera=True,
            no_major_cuts=True,
            normal_timing=True,
            decode_usable=True,
            vehicles_visible=True,
            meaningful_traffic=True,
        ),
        windows=windows(),
        analytical_use="ACADEMIC_ONLY",
        usage_scope="INTERNAL_NONCOMMERCIAL_ACADEMIC",
        agreement_sha256="b" * 64,
        episode_evidence_sha256="c" * 64,
        sustained_beyond_individual_stop=True,
        geometry_useful=True,
        source_approved=True,
        review_rationale="Synthetic review only",
    )


def rectangle(left: float, top: float, right: float, bottom: float) -> Polygon:
    return Polygon(
        points=(
            Point(x=left, y=top),
            Point(x=right, y=top),
            Point(x=right, y=bottom),
            Point(x=left, y=bottom),
        )
    )


def geometry() -> Geometry:
    return Geometry(
        source_sha256="a" * 64,
        camera_id="fixture",
        roi=rectangle(0.1, 0.1, 0.9, 0.9),
        queue_zone=rectangle(0.3, 0.3, 0.6, 0.6),
        entry=Line(start=Point(x=0.2, y=0.2), end=Point(x=0.2, y=0.8)),
        exit=Line(start=Point(x=0.8, y=0.2), end=Point(x=0.8, y=0.8)),
        direction=(1, 0),
        entry_direction=(1, 0),
        exit_direction=(1, 0),
        rationale="Synthetic rightward approach",
    )


def test_inventory_preserves_camera_condition_and_fraction() -> None:
    rows = parse_inventory("vid_name fps frame_num\ncam_7_rain.mp4 8/1 14400")
    assert rows[0].camera_id == "cam_7"
    assert rows[0].condition == "rain"
    assert rows[0].declared_duration == 1800


@pytest.mark.parametrize(
    "text",
    [
        "bad header",
        "vid_name fps frame_num\n../cam_1.mp4 10/1 30",
        "vid_name fps frame_num\ncam_1.mp4 10/0 30",
        "vid_name fps frame_num\ncam_1.mp4 10/1 30\ncam_1.mp4 10/1 30",
    ],
)
def test_inventory_rejects_malformed_or_duplicate_rows(text: str) -> None:
    with pytest.raises(ValueError):
        parse_inventory(text)


def test_duration_and_hd_filter_boundaries() -> None:
    assert TechnicalScreen(duration_seconds=599.99, width=1280, height=720).rejections() == (
        "DURATION_BELOW_600_SECONDS",
    )
    assert TechnicalScreen(duration_seconds=600, width=1280, height=720).rejections() == ()
    low = TechnicalScreen(duration_seconds=600, width=960, height=540)
    assert low.rejections() == ("BELOW_HD",)
    assert low.rejections(better_resolution_available=False) == ()
    assert not low.complete()


def test_unknown_or_failed_technical_review_never_passes() -> None:
    screen = TechnicalScreen(duration_seconds=1800, width=1280, height=720)
    assert not screen.complete()
    failed = TechnicalScreen.model_validate({**screen.model_dump(), "fixed_camera": False})
    assert failed.rejections() == ("FIXED_CAMERA_FAILED",)


def test_ranking_evidence_precedes_weather_with_stable_ties() -> None:
    day = CandidateScore(
        filename="cam_2.mp4", condition="day", factors=(1,) * 13, rationale="Synthetic"
    )
    rain = CandidateScore(
        filename="cam_1_rain.mp4", condition="rain", factors=(2,) * 13, rationale="Stronger episode"
    )
    other = CandidateScore(
        filename="cam_3.mp4", condition="day", factors=(1,) * 13, rationale="Synthetic tie"
    )
    assert shortlist((other, rain, day)) == (rain, day, other)
    with pytest.raises(ValueError, match="unique"):
        shortlist((day, day))


def test_score_shape_and_range_are_strict() -> None:
    with pytest.raises(ValidationError):
        CandidateScore(filename="cam_1", condition="day", factors=(3,) * 13, rationale="bad")
    with pytest.raises(ValidationError):
        CandidateScore(filename="cam_1", condition="day", factors=(1,) * 12, rationale="bad")


def test_exact_static_interval_and_title() -> None:
    assert windows().static_title() == "Ten minutes of traffic in one frame"
    values = windows().model_dump()
    values["static"]["start"] = 1200.1
    with pytest.raises(ValueError, match="exact 600"):
        EpisodeWindows.model_validate(values)


def test_window_ordering_and_containment() -> None:
    for field, end in (("baseline", 1400), ("degraded", 1801), ("static", 1801)):
        values = windows().model_dump()
        values[field]["end"] = end
        with pytest.raises(ValueError, match="windows"):
            EpisodeWindows.model_validate(values)


def test_source_manifest_roundtrip_keeps_publication_separate() -> None:
    record = admission()
    assert SourceAdmission.model_validate_json(record.model_dump_json()) == record
    assert record.source_approved
    assert not record.public_raw_video_reuse_allowed
    assert record.public_derived_visuals == "REVIEW_REQUIRED"


def test_approval_rejects_missing_rights_episode_or_geometry() -> None:
    for field, value in (
        ("analytical_use", "UNKNOWN"),
        ("windows", None),
        ("sustained_beyond_individual_stop", False),
        ("geometry_useful", False),
    ):
        values = admission().model_dump()
        values[field] = value
        with pytest.raises(ValueError, match="prerequisites"):
            SourceAdmission.model_validate(values)


def test_manifest_mismatch_and_bad_hash_fail() -> None:
    values = admission().model_dump()
    values["screen"]["width"] = 1920
    with pytest.raises(ValueError, match="disagree"):
        SourceAdmission.model_validate(values)
    values = admission().model_dump()
    values["agreement_sha256"] = "not-a-hash"
    with pytest.raises(ValueError):
        SourceAdmission.model_validate(values)


def test_geometry_serialization_preserves_relative_only() -> None:
    record = geometry()
    assert Geometry.model_validate_json(record.model_dump_json()) == record
    assert record.calibration == "RELATIVE_ONLY"
    assert record.reference_point == "BOTTOM_CENTER"


def test_normalized_bounds_and_nonfinite_coordinates() -> None:
    for x in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            Point(x=x, y=0.5)


def test_polygon_rejects_bowtie_and_degenerate() -> None:
    for points in (
        (Point(x=0.1, y=0.1), Point(x=0.9, y=0.9), Point(x=0.9, y=0.1), Point(x=0.1, y=0.9)),
        (Point(x=0.1, y=0.1), Point(x=0.2, y=0.2), Point(x=0.3, y=0.3)),
    ):
        with pytest.raises(ValueError):
            Polygon(points=points)


def test_queue_must_be_contained_and_smaller() -> None:
    for queue in (rectangle(0, 0, 0.5, 0.5), geometry().roi):
        values = geometry().model_dump()
        values["queue_zone"] = queue.model_dump()
        with pytest.raises(ValueError, match="queue zone"):
            Geometry.model_validate(values)


def test_entry_exit_must_not_overlap_or_intersect() -> None:
    values = geometry().model_dump()
    values["exit"] = values["entry"]
    with pytest.raises(ValueError, match="intersect"):
        Geometry.model_validate(values)


def test_boundary_cannot_be_on_image_border_or_outside_roi() -> None:
    with pytest.raises(ValueError, match="border"):
        Line(start=Point(x=0, y=0.3), end=Point(x=0.2, y=0.3))
    values = geometry().model_dump()
    values["entry"]["start"]["x"] = 0.05
    with pytest.raises(ValueError, match="outside ROI"):
        Geometry.model_validate(values)


def test_direction_must_be_nonzero_and_forward() -> None:
    for direction in ((0, 0), (-1, 0), (0, 1)):
        values = geometry().model_dump()
        values["direction"] = direction
        with pytest.raises(ValueError, match="direction"):
            Geometry.model_validate(values)


def test_exclusions_cannot_cover_analysis_area() -> None:
    values = geometry().model_dump()
    values["exclusions"] = [rectangle(0.4, 0.4, 0.6, 0.6).model_dump()]
    with pytest.raises(ValueError, match="exclusions"):
        Geometry.model_validate(values)


def test_complete_geometry_has_no_physical_unit_escape() -> None:
    values = geometry().model_dump()
    values["calibration"] = "MPH"
    with pytest.raises(ValueError):
        Geometry.model_validate(values)


def test_local_crossing_direction_rejects_parallel_and_reverse() -> None:
    for direction in ((0, 1), (-1, 0)):
        values = geometry().model_dump()
        values["exit_direction"] = direction
        with pytest.raises(ValueError, match="direction"):
            Geometry.model_validate(values)


def test_curved_approach_has_distinct_valid_local_directions() -> None:
    values = geometry().model_dump()
    values["exit"] = Line(start=Point(x=0.5, y=0.2), end=Point(x=0.8, y=0.2)).model_dump()
    values["direction"] = (0.8, -0.6)
    values["exit_direction"] = (0, -1)
    record = Geometry.model_validate(values)
    assert record.entry_direction != record.exit_direction
