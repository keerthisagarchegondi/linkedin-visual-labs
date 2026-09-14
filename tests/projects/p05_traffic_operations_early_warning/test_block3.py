"""Deterministic Steps 8-11 evidence tests without native CV or footage."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.metrics import (
    MetricPlan,
    baseline,
    calculate,
    deviation,
    percentile,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.queue_outcome import (
    QueueRule,
    evaluate_queue,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.recommendations import (
    recommend,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.validation import (
    assert_number,
    independent_onsets,
    quantile,
    verify_claim,
    verify_onsets,
    verify_recommendation,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.warning import (
    WarningRule,
    baseline_false_warnings,
    evaluate_warning,
    first_time,
    result,
    sensitivity,
    variants,
)


def metric_fixture() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, list[dict[str, Any]], MetricPlan
]:
    p = pd.DataFrame(
        [
            {
                "source_timestamp": float(t),
                "track_id": 1,
                "queue_zone": True,
                "low_motion_active": t >= 3,
                "observation_gap": False,
                "relative_movement_per_second": 0.01,
            }
            for t in range(12)
        ]
    )
    e = pd.DataFrame(
        [
            {
                "source_timestamp": float(t),
                "available_timestamp": float(t),
                "track_id": i,
                "event_type": kind,
            }
            for i, t, kind in [(1, 1, "ENTRY"), (1, 4, "EXIT"), (2, 5, "EXIT")]
        ]
    )
    d = pd.DataFrame([{"exit_timestamp": 4.0, "available_timestamp": 4.0, "dwell_seconds": 3.0}])
    f = [{"source_timestamp": float(t), "frame_index": t * 10} for t in range(12)]
    return (
        p,
        e,
        d,
        f,
        MetricPlan(
            window_seconds=3,
            baseline_start=0,
            baseline_end=12,
            minimum_dwell_samples=1,
            minimum_movement_samples=1,
            trend_seconds=1,
        ),
    )


def test_occupancy_and_zone() -> None:
    p, e, d, f, c = metric_fixture()
    m = calculate(p, e, d, f, 12, c)
    assert m.occupancy_count.tolist() == [1] * 12
    assert m.queue_count.iloc[2] == 0 and m.queue_count.iloc[3] == 1


def test_window_left_endpoint_excluded() -> None:
    p, e, d, f, c = metric_fixture()
    m = calculate(p, e, d, f, 12, c)
    assert m.entries.iloc[4] == 0 and m.throughput.iloc[4] == 1 and m.throughput.iloc[7] == 1


def test_warmup_is_unavailable() -> None:
    p, e, d, f, c = metric_fixture()
    m = calculate(p, e, d, f, 12, c)
    assert pd.isna(m.throughput.iloc[2]) and m.window_quality.iloc[2] == "WARMUP"


def test_missing_frame_breaks_coverage() -> None:
    p, e, d, f, c = metric_fixture()
    m = calculate(p, e, d, [r for r in f if r["source_timestamp"] != 4], 12, c)
    assert pd.isna(m.occupancy_count.iloc[4]) and pd.isna(m.throughput.iloc[5])


def test_sparse_dwell_unavailable() -> None:
    p, e, d, f, c = metric_fixture()
    m = calculate(p, e, d, f, 12, replace(c, minimum_dwell_samples=3))
    assert m.dwell_sample_size.iloc[4] == 1 and pd.isna(m.median_completed_dwell_seconds.iloc[4])


def test_dwell_exit_assignment() -> None:
    p, e, d, f, c = metric_fixture()
    m = calculate(p, e, d, f, 12, c)
    assert m.median_completed_dwell_seconds.iloc[4] == 3 and m.dwell_sample_size.iloc[7] == 0


def test_baseline_excludes_leading_partial_window() -> None:
    p, e, d, f, c = metric_fixture()
    b = baseline(calculate(p, e, d, f, 12, c), c)
    assert (
        b["comparison_timestamps"] == [3, 12]
        and b["statistics"]["density_window_mean"]["sample_size"] == 9
    )


@pytest.mark.parametrize(
    "value,reference,expected", [(2, 1, 1), (2, 0, None), (None, 2, None), (2, None, None)]
)
def test_normalization(
    value: float | None, reference: float | None, expected: float | None
) -> None:
    assert deviation(value, reference) == expected


def test_percentile_and_empty() -> None:
    assert percentile([1, 3], 50) == 2 and percentile([], 50) is None


def test_formal_window_lock() -> None:
    with pytest.raises(ValueError):
        MetricPlan(formal_window_seconds=60)


def test_delayed_confirmation_does_not_leak() -> None:
    p, e, d, f, c = metric_fixture()
    e.loc[0, "available_timestamp"] = 3
    assert calculate(p, e, d, f, 12, replace(c, window_seconds=1)).entries.iloc[1] == 0


def signals(n: int = 12) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": float(t),
                "frame_available": True,
                "window_available": True,
                "density_window_mean": 5.0,
                "throughput": 0.0,
                "inflow_outflow_imbalance": 3.0,
                "movement_index": 0.001,
                "density_trend": 0.02,
                "queue_count": 2,
                "queue_zone_occupancy": 3,
            }
            for t in range(n)
        ]
    )


def rule() -> WarningRule:
    return WarningRule(
        density_threshold=2,
        throughput_ceiling=1,
        movement_ceiling=0.005,
        persistence_seconds=3,
        critical_seconds=6,
        reset_seconds=2,
    )


@pytest.mark.parametrize(
    "w,q,classification,lead",
    [
        (10.0, 20.0, "POSITIVE_EARLY_WARNING", 10.0),
        (20.0, 20.0, "WARNING_AT_VISIBLE_ONSET", 0.0),
        (30.0, 20.0, "LATE_WARNING", -10.0),
        (None, 20.0, "NO_VALID_WARNING", None),
        (10.0, None, "NO_VISIBLE_QUEUE_EVENT", None),
    ],
)
def test_signed_result_classes(
    w: float | None, q: float | None, classification: str, lead: float | None
) -> None:
    r = result(w, q)
    assert r["result_classification"] == classification and r["lead_time_seconds"] == lead


def test_queue_persistence_completion_not_backdated() -> None:
    q = evaluate_queue(signals(), QueueRule(persistence_seconds=3), 0)
    assert first_time(q, "visible_queue") == 3


def test_transient_queue_rejected() -> None:
    m = signals()
    m.loc[3:, "queue_count"] = 0
    assert (
        first_time(evaluate_queue(m, QueueRule(persistence_seconds=3), 0), "visible_queue") is None
    )


def test_queue_missingness_breaks_persistence() -> None:
    m = signals()
    m.loc[2, "frame_available"] = False
    assert first_time(evaluate_queue(m, QueueRule(persistence_seconds=3), 0), "visible_queue") == 6


def test_density_alone_not_queue() -> None:
    m = signals()
    m["queue_count"] = 0
    assert not evaluate_queue(m, QueueRule(persistence_seconds=1), 0).visible_queue.any()


def test_warning_full_persistence_and_critical() -> None:
    w = evaluate_warning(signals(), rule(), 0)
    assert first_time(w, "warning_qualified") == 3 and w.state.iloc[6] == "CRITICAL"


def test_direct_critical_cannot_backdate_warning() -> None:
    w = evaluate_warning(signals(), replace(rule(), critical_seconds=1), 0)
    assert w.state.iloc[1] == "CRITICAL" and first_time(w, "warning_qualified") == 3


def test_missing_warning_is_not_normal() -> None:
    m = signals()
    m.loc[2, "movement_index"] = float("nan")
    w = evaluate_warning(m, rule(), 0)
    assert pd.isna(w.state.iloc[2]) and first_time(w, "warning_qualified") == 6


def test_warning_reset_hysteresis() -> None:
    m = signals()
    m.loc[5:, ["density_window_mean", "inflow_outflow_imbalance", "density_trend"]] = 0
    m.loc[5:, "throughput"] = 5
    m.loc[5:, "movement_index"] = 0.1
    w = evaluate_warning(m, rule(), 0)
    assert w.state.iloc[5] == "WARNING" and w.state.iloc[7] == "NORMAL"


def test_baseline_false_warning_exposure() -> None:
    r = baseline_false_warnings(signals(), rule(), 0, 12)
    assert (
        r["baseline_false_warning_count"] == 1
        and r["warning_seconds"] == 9
        and r["evaluable_seconds"] == 12
    )


def test_sensitivity_neighborhood_is_fixed() -> None:
    w = rule()
    q = QueueRule()
    v = variants(w, q)
    assert len(v) == 5 and v[0] == ("PRIMARY", w, q) and w.density_threshold == 2


def test_sensitivity_is_deterministic() -> None:
    args = (signals(), rule(), QueueRule(persistence_seconds=3), 0, 0, 12)
    pd.testing.assert_frame_equal(sensitivity(*args), sensitivity(*args))


def summary_fixture() -> dict[str, Any]:
    return {
        "warning_timestamp": 3.0,
        "primary_driver": "DENSITY_LEVEL",
        "supporting_drivers": ["DENSITY_TREND"],
    }


def test_recommendation_enabled_and_conditional() -> None:
    s = summary_fixture()
    r = recommend(s, ["MONITOR", "ESCALATE_FOR_REVIEW"])
    assert r["recommended_action"] == "ESCALATE_FOR_REVIEW" and r["wording"].startswith("Consider ")
    verify_recommendation(r, s, ["MONITOR", "ESCALATE_FOR_REVIEW"])


def test_disabled_recommendation_not_emitted() -> None:
    assert recommend(summary_fixture(), [])["recommended_action"] is None


def test_unestablished_facility_action_rejected() -> None:
    with pytest.raises(ValueError, match="facility"):
        recommend(summary_fixture(), ["OPEN_OVERFLOW_CAPACITY"])


def test_missing_warning_recommends_monitor() -> None:
    assert recommend({"warning_timestamp": None}, ["MONITOR"])["recommended_action"] == "MONITOR"


def test_recommendation_link_tamper_fails() -> None:
    s = summary_fixture()
    r = recommend(s, ["ESCALATE_FOR_REVIEW"])
    r["supporting_metric_ids"] = []
    with pytest.raises(ValueError, match="evidence"):
        verify_recommendation(r, s, ["ESCALATE_FOR_REVIEW"])


def test_independent_onsets_match_known_oracle() -> None:
    from dataclasses import asdict

    cfg = {
        "warning": asdict(rule()),
        "queue": asdict(QueueRule(persistence_seconds=5)),
        "evaluation_start": 0,
    }
    r = independent_onsets(signals(), cfg)
    assert r == {"warning_timestamp": 3.0, "visible_queue_timestamp": 5.0, "lead_time_seconds": 2.0}


def test_onset_arithmetic_mismatch_fails() -> None:
    with pytest.raises(ValueError):
        verify_onsets({"lead_time_seconds": 1}, {"lead_time_seconds": -1})


def test_missing_value_cannot_be_zero() -> None:
    with pytest.raises(ValueError):
        assert_number(0, None, "missing")


def claim_fixture() -> dict[str, Any]:
    return {
        "claim_id": "test",
        "claim_text": "Derived signal",
        "classification": "DERIVED",
        "evidence_path": "data/metric.json",
        "calculation": "configured rule",
        "unit": "seconds",
        "caveat": "not ground truth",
        "approved_for_publication": True,
        "reviewer_status": "APPROVED",
        "evidence_sha256": "a" * 64,
    }


@pytest.mark.parametrize("classification", ["PREVIEW_ONLY", "UNSUPPORTED"])
def test_preview_and_unsupported_claims_rejected(classification: str) -> None:
    c = claim_fixture()
    c["classification"] = classification
    with pytest.raises(ValueError):
        verify_claim(c)


def test_claim_requires_evidence_hash() -> None:
    c = claim_fixture()
    del c["evidence_sha256"]
    with pytest.raises(ValueError):
        verify_claim(c)


def test_independent_percentile() -> None:
    assert quantile([10, 0], 10) == 1 and quantile([], 50) is None


def test_lower_level_parquet_recomputation_and_tamper(tmp_path: Path) -> None:
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.block2 import (
        build_events,
        build_tracking,
    )
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.detection import sampled
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.metrics import (
        eligible_inputs,
        normalize,
    )
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.validation import (
        recompute_metrics,
        verify_baseline,
    )

    from .test_block2 import fixture_geometry, observation

    data = tmp_path / "data"
    data.mkdir()
    obs = [observation(f) for f in range(120) if sampled(f, 3)]
    frames = [{"source_timestamp": d.source_timestamp, "frame_index": d.frame_index} for d in obs]
    pd.DataFrame([asdict(d) for d in obs]).to_parquet(data / "detections.parquet", index=False)
    (data / "detection_summary.json").write_text(json.dumps({"frames": frames}))
    build_tracking(data / "detections.parquet", data / "detection_summary.json", tmp_path)
    build_events(tmp_path, fixture_geometry())
    tr = pd.read_parquet(data / "tracks.parquet")
    tj = pd.read_parquet(data / "trajectories.parquet")
    ev = pd.read_parquet(data / "crossing_events.parquet")
    js = pd.read_parquet(data / "journeys.parquet")
    p, e, d, q = eligible_inputs(tr, tj, ev, js)
    cfg = metric_fixture()[-1]
    m = calculate(p, e, d, frames, 12, cfg)
    b = baseline(m, cfg)
    m = normalize(m, b)
    assert q["eligible_confirmed_tracks"] == 1 and q["completed_dwell_samples"] == 0
    assert (
        recompute_metrics(tr, ev, js, frames, fixture_geometry(), m, asdict(cfg))["status"]
        == "PASS"
    )
    verify_baseline(m, b)
    m.loc[4, "throughput"] = 99
    with pytest.raises(ValueError, match="throughput"):
        recompute_metrics(tr, ev, js, frames, fixture_geometry(), m, asdict(cfg))


def test_eligibility_rejects_duplicate_crossings() -> None:
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.metrics import (
        eligible_inputs,
    )

    t = pd.DataFrame({"detection_id": ["a"]})
    e = pd.DataFrame({"track_id": [1, 1], "event_type": ["ENTRY", "ENTRY"]})
    with pytest.raises(ValueError, match="duplicate crossing"):
        eligible_inputs(t, t, e, pd.DataFrame())


def test_evidence_index_rejects_changed_bytes(tmp_path: Path) -> None:
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.evidence import (
        artifact,
        verify_index,
    )

    p = tmp_path / "evidence.json"
    p.write_text("{}")
    index = {"artifacts": {"test": artifact(tmp_path, p)}}
    verify_index(tmp_path, index)
    p.write_text('{"changed":true}')
    with pytest.raises(ValueError, match="hash"):
        verify_index(tmp_path, index)


def test_unknown_claim_classification_rejected() -> None:
    c = claim_fixture()
    c["classification"] = "INVENTED"
    with pytest.raises(ValueError):
        verify_claim(c)
