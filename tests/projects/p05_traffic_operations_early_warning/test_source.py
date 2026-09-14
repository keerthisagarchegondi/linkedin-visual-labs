"""Small deterministic source-screening fixtures; no real video or detector imports."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.source import (
    AnalysisWindows,
    Box,
    Interval,
    ScreeningSummary,
    VideoMetadata,
    label_frame,
    parse_label,
    parse_sct,
    rank_cameras,
    screening_indicators,
)


def metadata() -> VideoMetadata:
    return VideoMetadata(
        camera="fixture",
        sha256="a" * 64,
        byte_size=100,
        duration_seconds=4.0,
        width=3840,
        height=2160,
        nominal_fps=15.0,
        frame_count=60,
        time_base_denominator=15360,
        first_pts=0,
        last_pts=59 * 1024,
        pts_step=1024,
        codec="fixture",
        audio_present=False,
        decode_ok=True,
    )


def test_original_clock() -> None:
    assert metadata().timestamp(15) == 1.0


def test_frame_outside_source() -> None:
    with pytest.raises(ValueError, match="outside"):
        metadata().timestamp(60)


def test_failed_decode_blocks_screening() -> None:
    values = metadata().model_dump()
    values["decode_ok"] = False
    with pytest.raises(ValueError, match="decoding"):
        screening_indicators("", VideoMetadata.model_validate(values))


def test_inconsistent_pts() -> None:
    values = metadata().model_dump()
    values["last_pts"] = 123
    with pytest.raises(ValidationError, match="PTS"):
        VideoMetadata.model_validate(values)


def test_inconsistent_duration() -> None:
    values = metadata().model_dump()
    values["duration_seconds"] = 600.0
    with pytest.raises(ValidationError, match="duration"):
        VideoMetadata.model_validate(values)


def test_frame_filename() -> None:
    assert label_frame("labels_filtered/img000005.txt") == 5


def test_unsafe_zip_member() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        label_frame("../img000005.txt")


def test_label_format_keeps_pixel_coordinates_and_score() -> None:
    row = parse_label("2 591 960 1132 1317 0.95", 5)[0]
    assert row.box.xmax == 1132
    assert row.score == 0.95
    assert row.track is None


def test_normalized_yolo_not_silently_accepted_as_observed_schema() -> None:
    with pytest.raises(ValueError, match="expected"):
        parse_label("2 0.5 0.5 0.2 0.2", 0)


def test_sct_origin_is_explicit() -> None:
    row = parse_sct("6 1 586.48 961.46 1128.79 1320.84 2", frame_origin=1)[0]
    assert row.frame == 5
    assert row.track == 1


def test_sct_mixed_whitespace() -> None:
    assert parse_sct("1\t1\t10\t20\t30\t40\t2", frame_origin=1)[0].frame == 0


def test_sct_track_grouped_order_allowed() -> None:
    rows = parse_sct("1 1 1 2 3 4 2\n2 1 1 2 3 4 2\n1 2 1 2 3 4 2", frame_origin=1)
    assert [r.frame for r in rows] == [0, 1, 0]


def test_duplicate_sct_key_refused() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        parse_sct("1 1 1 2 3 4 2\n1 1 1 2 3 4 2", frame_origin=1)


def test_fractional_identifier_refused() -> None:
    with pytest.raises(ValueError, match="integer"):
        parse_sct("1 1.5 1 2 3 4 2", frame_origin=1)


def test_box_bounds_refused() -> None:
    with pytest.raises(ValueError, match="outside"):
        Box(xmin=0.0, ymin=0.0, xmax=3841.0, ymax=2160.0).check_bounds(3840, 2160)


def test_empty_box_refused() -> None:
    with pytest.raises(ValidationError):
        Box(xmin=3.0, ymin=2.0, xmax=3.0, ymax=4.0)


def test_screening_excludes_all_duplicates_and_invalid_boxes() -> None:
    result = screening_indicators(
        "1 1 1 2 3 4 2\n1 1 1 2 3 4 2\n2 2 1 2 4000 4 2\n3 3 1 2 3 4 2", metadata()
    )
    assert (result.input_rows, result.excluded_rows, result.duplicate_keys) == (4, 3, 1)
    assert result.tracks == 1
    assert result.annotated_count_mean == pytest.approx(1 / 60)


def test_stationary_screening_uses_original_seconds() -> None:
    text = "\n".join(f"{f} 1 100 600 200 700 2" for f in range(1, 61))
    result = screening_indicators(text, metadata())
    assert result.maximum_low_motion_run_seconds == 3.0
    assert result.maximum_two_low_motion_run_seconds == 0.0


def test_motion_does_not_bridge_missing_annotations() -> None:
    result = screening_indicators("1 1 100 600 200 700 2\n16 1 100 600 200 700 2", metadata())
    assert result.maximum_low_motion_run_seconds == 0.0


def test_screening_json_roundtrip() -> None:
    result = screening_indicators("", metadata())
    assert ScreeningSummary.model_validate_json(result.model_dump_json()) == result
    assert result.bins[0].movement_median is None


def test_ranking_determinism_and_ties() -> None:
    assert rank_cameras({"cam02": (1,) * 14, "cam01": (1,) * 14}) == ("cam01", "cam02")


def test_invalid_ranking_refused() -> None:
    with pytest.raises(ValueError):
        rank_cameras({"cam01": (3,) * 14})


def windows() -> AnalysisWindows:
    return AnalysisWindows(
        duration_seconds=600.0,
        baseline=Interval(start=0.0, end=180.0),
        buildup=Interval(start=180.0, end=210.0),
        degraded=Interval(start=210.0, end=240.0),
        static=Interval(start=0.0, end=600.0),
    )


def test_static_title_and_exact_source_interval() -> None:
    assert windows().static_title() == "Ten minutes of traffic in one frame"
    assert windows().static.end == 600.0


def test_fake_six_hundred_seconds_refused() -> None:
    values = windows().model_dump()
    values["duration_seconds"] = 599.0
    with pytest.raises(ValidationError, match="out-of-source"):
        AnalysisWindows.model_validate(values)


def test_overlapping_windows_refused() -> None:
    values = windows().model_dump()
    values["buildup"] = {"start": 179.0, "end": 210.0}
    with pytest.raises(ValidationError, match="overlapping"):
        AnalysisWindows.model_validate(values)


def test_reversed_interval_refused() -> None:
    with pytest.raises(ValidationError):
        Interval(start=2.0, end=1.0)
