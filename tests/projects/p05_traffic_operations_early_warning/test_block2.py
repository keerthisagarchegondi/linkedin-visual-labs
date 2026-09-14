"""Small deterministic analytical fixtures; no native CV or model dependency."""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning import detection
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.block2 import (
    build_events,
    build_tracking,
    reconcile,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.calibration import (
    Geometry,
    Line,
    Point,
    Polygon,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.detection import (
    Detection,
    DetectionConfig,
    Detector,
    box_iou,
    decode,
    preprocess,
    sampled,
    suppress,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.events import (
    EventConfig,
    derive_track,
    directed_crossing,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.tracking import (
    Tracker,
    TrackingConfig,
)


def observation(frame: int = 0, x: float = 900, confidence: float = 0.8) -> Detection:
    return Detection(
        f"{frame}:0",
        frame,
        frame / 10,
        frame * 3 // 10,
        2,
        "car",
        confidence,
        x,
        400,
        x + 60,
        460,
        x + 30,
        460,
        True,
    )


def fixture_geometry() -> Geometry:
    def polygon(x1: float, y1: float, x2: float, y2: float) -> Polygon:
        return Polygon(
            points=(Point(x=x1, y=y1), Point(x=x2, y=y1), Point(x=x2, y=y2), Point(x=x1, y=y2))
        )

    return Geometry(
        source_sha256="a" * 64,
        camera_id="fixture",
        roi=polygon(0.1, 0.1, 0.95, 0.9),
        queue_zone=polygon(0.4, 0.5, 0.8, 0.8),
        entry=Line(start=Point(x=0.8, y=0.2), end=Point(x=0.8, y=0.85)),
        exit=Line(start=Point(x=0.4, y=0.2), end=Point(x=0.4, y=0.85)),
        direction=(-1, 0),
        entry_direction=(-1, 0),
        exit_direction=(-1, 0),
        rationale="Synthetic test geometry",
    )


def tracked() -> Tracker:
    tracker = Tracker()
    for frame in (0, 4, 7):
        tracker.update(frame / 10, [observation(frame)])
    return tracker


def test_track_confirmation_requires_three_observations() -> None:
    t = tracked()
    assert len(t.tracks) == 1 and t.tracks[0].confirmed
    assert t.tracks[0].stages == ["BIRTH", "CONFIRM", "CONFIRM"]


def test_low_score_recovers_active_track_without_birth() -> None:
    t = tracked()
    t.update(1, [observation(10, confidence=0.2)])
    assert len(t.tracks) == 1 and t.tracks[0].stages[-1] == "LOW"


def test_low_score_alone_cannot_create_track() -> None:
    t = Tracker()
    t.update(0, [observation(confidence=0.2)])
    assert not t.tracks


def test_lost_track_recovered_by_high_score() -> None:
    t = tracked()
    t.update(1, [])
    t.update(1.4, [observation(14)])
    assert len(t.tracks) == 1 and t.tracks[0].recoveries == 1


def test_low_score_does_not_resurrect_lost_track() -> None:
    t = tracked()
    t.update(1, [])
    t.update(1.4, [observation(14, confidence=0.2)])
    assert t.tracks[0].status == "LOST" and len(t.tracks[0].observations) == 3


def test_expired_track_gets_new_clip_local_identity() -> None:
    t = tracked()
    t.update(3, [observation(30)])
    assert len(t.tracks) == 2 and t.tracks[0].status == "REMOVED"


def test_ids_reset_for_new_clip() -> None:
    assert tracked().tracks[0].track_id == tracked().tracks[0].track_id == 1


def test_prediction_never_creates_observation() -> None:
    t = tracked()
    t.update(1, [])
    assert len(t.tracks[0].observations) == 3


def test_roi_exclusions_cannot_create_tracks() -> None:
    t = Tracker()
    t.update(0, [replace(observation(), roi_eligible=False)])
    assert not t.tracks


def test_implausible_jump_is_not_joined() -> None:
    t = tracked()
    t.update(1, [observation(10, x=100)])
    assert len(t.tracks) == 2 and t.tracks[0].status == "LOST"


def test_duplicate_detection_key_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        Tracker().update(0, [observation(), observation()])


def test_duplicate_birth_over_active_track_is_suppressed() -> None:
    t = tracked()
    d = observation(10)
    t.update(1, [d, replace(d, detection_id="10:1")])
    assert len(t.tracks) == 1 and t.duplicate_births_suppressed == 1


def test_repeated_crossing_cannot_count_same_track_twice() -> None:
    obs = [
        observation(f, x=x * 1280 - 30) for f, x in ((0, 0.82), (4, 0.78), (7, 0.82), (10, 0.78))
    ]
    _, events, _ = derive_track(1, obs, True, fixture_geometry())
    assert sum(e["event_type"] == "ENTRY" for e in events) == 1


def test_frame_clock_reversal_rejected() -> None:
    with pytest.raises(ValueError, match="increase"):
        tracked().update(0.5, [])


def test_detection_frame_clock_mismatch_rejected() -> None:
    with pytest.raises(ValueError, match="clock mismatch"):
        Tracker().update(1, [observation()])


def test_unconfirmed_miss_removes_candidate() -> None:
    t = Tracker()
    t.update(0, [observation()])
    t.update(0.4, [])
    assert t.tracks[0].status == "REMOVED" and not t.tracks[0].confirmed


def test_invalid_tracking_config_rejected() -> None:
    with pytest.raises(ValueError):
        TrackingConfig(high_score=0.9, birth_score=0.8)
    with pytest.raises(ValueError):
        TrackingConfig(lost_seconds=0)


def test_directed_crossing_rejects_reverse_and_jitter() -> None:
    line = fixture_geometry().entry
    assert directed_crossing(Point(x=0.81, y=0.6), Point(x=0.79, y=0.6), line, (-1, 0), 0.001)
    assert not directed_crossing(Point(x=0.79, y=0.6), Point(x=0.81, y=0.6), line, (-1, 0), 0.001)
    assert not directed_crossing(
        Point(x=0.8001, y=0.6), Point(x=0.7999, y=0.6), line, (-1, 0), 0.001
    )


def test_crossing_extension_outside_segment_rejected() -> None:
    assert not directed_crossing(
        Point(x=0.81, y=0.95), Point(x=0.79, y=0.95), fixture_geometry().entry, (-1, 0), 0.001
    )


def journey_observations() -> list[Detection]:
    return [
        observation(f, x=x * 1280 - 30)
        for f, x in ((0, 0.82), (4, 0.78), (7, 0.6), (10, 0.42), (14, 0.38))
    ]


def test_completed_journey_preserves_observed_crossing_times() -> None:
    _, events, j = derive_track(1, journey_observations(), True, fixture_geometry())
    assert j["completed_eligible"] and j["entry_timestamp"] == 0.4 and j["exit_timestamp"] == 1.4
    assert j["completed_elapsed_seconds"] == pytest.approx(1)
    assert len([e for e in events if e["event_type"] == "ENTRY"]) == 1


def test_censored_track_has_no_completed_elapsed_time() -> None:
    _, _, j = derive_track(1, journey_observations()[:3], True, fixture_geometry())
    assert j["classification"] == "ENTRY_ONLY" and j["completed_elapsed_seconds"] is None


def test_unconfirmed_fragment_emits_no_events() -> None:
    _, events, j = derive_track(1, journey_observations(), False, fixture_geometry())
    assert not events and j["classification"] == "SHORT_FRAGMENT"


def test_long_gap_does_not_create_crossing() -> None:
    obs = [observation(0, x=0.82 * 1280 - 30), observation(30, x=0.78 * 1280 - 30)]
    _, events, j = derive_track(1, obs, True, fixture_geometry())
    assert not any(e["event_type"] == "ENTRY" for e in events) and j["gap_count"] == 1


def test_low_motion_persistence_is_not_backdated() -> None:
    obs = [observation(f) for f in range(0, 41, 4)]
    trajectory, events, j = derive_track(1, obs, True, fixture_geometry())
    slow = [e for e in events if e["event_type"] == "LOW_MOTION_START"]
    assert slow[0]["source_timestamp"] == 3.2 and slow[0]["interval_start_timestamp"] == 0
    assert j["low_motion_censored"] and trajectory[-1]["low_motion_active"]


def test_low_motion_gap_resets_persistence() -> None:
    obs = [observation(f) for f in (0, 4, 7, 10, 14, 40, 44)]
    _, events, _ = derive_track(1, obs, True, fixture_geometry())
    assert not any(e["event_type"] == "LOW_MOTION_START" for e in events)


def test_trajectory_clock_and_configuration_validation() -> None:
    with pytest.raises(ValueError, match="nonmonotonic"):
        derive_track(1, [observation(), observation()], True, fixture_geometry())
    with pytest.raises(ValueError):
        EventConfig(maximum_gap_seconds=float("nan"))


def test_tracking_events_fixture_is_deterministic() -> None:
    first = tracked()
    second = tracked()
    assert derive_track(1, first.tracks[0].observations, True, fixture_geometry()) == derive_track(
        1, second.tracks[0].observations, True, fixture_geometry()
    )


def test_parquet_pipeline_reconciles_and_rejects_retimming(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    observations = [observation(f, x=900 - f) for f in (0, 4, 7, 10, 14)]
    pd.DataFrame([asdict(d) for d in observations]).to_parquet(
        data / "detections.parquet", index=False
    )
    (data / "detection_summary.json").write_text(
        json.dumps(
            {
                "frames": [
                    {"frame_index": d.frame_index, "source_timestamp": d.source_timestamp}
                    for d in observations
                ]
            }
        )
    )
    quality = build_tracking(data / "detections.parquet", data / "detection_summary.json", tmp_path)
    assert quality["confirmed_count"] == 1
    assert quality["invalid_observed_jump_count"] == 0
    assert build_events(tmp_path, fixture_geometry())["status"] == "PASS"
    tables = [
        pd.read_parquet(data / name)
        for name in ("detections.parquet", "tracks.parquet", "trajectories.parquet")
    ]
    events = pd.concat(
        [
            pd.read_parquet(data / "zone_events.parquet"),
            pd.read_parquet(data / "crossing_events.parquet"),
        ]
    )
    journeys = pd.read_parquet(data / "journeys.parquet")
    assert all(reconcile(tables[0], tables[1], tables[2], events, journeys).values())
    assert tables[1].hit_count.tolist() == [1, 2, 3, 4, 5]
    assert tables[1].track_age_seconds.tolist() == [0, 0.4, 0.7, 1, 1.4]
    assert tables[1].lost_frame_count.tolist() == [0, 0, 0, 0, 0]
    assert tables[1].confirmed_at_observation.tolist() == [False, False, True, True, True]
    assert tables[1].displacement_source_pixels.iloc[1] == 4
    assert tables[1].relative_movement_per_second.iloc[1] > 0
    tables[2].loc[0, "source_timestamp"] = 999
    assert not reconcile(tables[0], tables[1], tables[2], events, journeys)[
        "trajectory_clock_and_identity_unchanged"
    ]


def test_parquet_tracking_empty_result_is_blocked(tmp_path: Path) -> None:
    detection_path = tmp_path / "detections.parquet"
    summary = tmp_path / "summary.json"
    pd.DataFrame([asdict(observation(confidence=0.2))]).to_parquet(detection_path, index=False)
    summary.write_text(json.dumps({"frames": [{"frame_index": 0, "source_timestamp": 0}]}))
    with pytest.raises(ValueError, match="no tracks"):
        build_tracking(detection_path, summary, tmp_path)


def test_preprocessing_preserves_bgr_range_and_top_left_padding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def resize(image: detection.ImageArray, size: tuple[int, int]) -> detection.ImageArray:
        return np.broadcast_to(image[0, 0], (size[1], size[0], 3)).copy()

    monkeypatch.setattr(importlib, "import_module", lambda _: SimpleNamespace(resize=resize))
    image = np.zeros((20, 40, 3), dtype=np.uint8)
    image[:] = [10, 20, 30]
    tensor, ratio = preprocess(image)
    assert tensor.shape == (1, 3, 416, 416) and ratio == 10.4
    assert tensor[0, :, 0, 0].tolist() == [10, 20, 30]
    assert tensor[0, :, -1, -1].tolist() == [114, 114, 114]
    assert tensor.dtype == np.float32


def test_invalid_image_fails_before_native_import() -> None:
    with pytest.raises(ValueError, match="BGR"):
        preprocess(np.zeros((0, 4, 3), dtype=np.uint8))


def test_three_fps_uses_original_frame_clock() -> None:
    frames = [i for i in range(18000) if sampled(i, 3)]
    assert len(frames) == 5400 and frames[:7] == [0, 4, 7, 10, 14, 17, 20]
    assert 1000 in frames and 1000 / 10 == 100


def test_five_fps_and_invalid_sampling() -> None:
    assert [i for i in range(10) if sampled(i, 5)] == [0, 2, 4, 6, 8]
    with pytest.raises(ValueError):
        sampled(-1, 3)


def test_nms_is_stable_and_suppresses_duplicate_classes() -> None:
    boxes = np.array([[0, 0, 20, 20], [1, 1, 21, 21], [50, 50, 70, 70]], dtype=np.float32)
    assert suppress(boxes, np.array([0.8, 0.8, 0.7], dtype=np.float32), 0.45) == [0, 2]
    assert box_iou((0, 0, 1, 1), (2, 2, 3, 3)) == 0


def test_output_decoding_vehicle_filter_and_crop_restoration() -> None:
    raw = np.zeros((1, 3549, 85), dtype=np.float32)
    raw[0, 0, :4] = [2, 2, np.log(2), np.log(2)]
    raw[0, 0, 4] = 0.8
    raw[0, 0, 7] = 0.9  # COCO car probability at 5+2
    result = decode(raw, 1, DetectionConfig())
    assert len(result) == 1
    assert result[0][:4] == (558.0, 258.0, 574.0, 274.0)
    raw[0, 0, 5] = 1  # person wins; cannot relabel it as a vehicle
    assert decode(raw, 1, DetectionConfig()) == []


@pytest.mark.parametrize("shape", [(1, 1, 85), (3549, 85)])
def test_output_shape_is_not_silently_guessed(shape: tuple[int, ...]) -> None:
    with pytest.raises(ValueError, match="YOLOX"):
        decode(np.zeros(shape, dtype=np.float32), 1, DetectionConfig())


def test_nonfinite_output_and_threshold_contract() -> None:
    raw = np.zeros((1, 3549, 85), dtype=np.float32)
    raw[0, 0, 0] = np.nan
    with pytest.raises(ValueError):
        decode(raw, 1, DetectionConfig())
    with pytest.raises(ValueError):
        DetectionConfig(confidence=0)


def test_detection_schema_rejects_invalid_class_box_and_reference() -> None:
    for change in ({"class_id": 0}, {"x2": 1400}, {"reference_y": 459}, {"confidence": 1.1}):
        with pytest.raises(ValueError):
            replace(observation(), **change)


def test_model_hash_fails_before_import(tmp_path: Path) -> None:
    model = tmp_path / "fixture.onnx"
    model.write_bytes(b"not a real model")
    with pytest.raises(ValueError, match="checksum"):
        Detector(model, "a" * 64, DetectionConfig())
