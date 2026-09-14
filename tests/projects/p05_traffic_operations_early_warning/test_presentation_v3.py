"""Causal presentation-time and dynamic-style contracts; no real inference."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.presentation_v2 import (
    TOKENS,
    canonical_metrics,
    validate_first15,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.presentation_v3 import (
    COLORS,
    history_at,
    playback_contract,
    require_fresh,
    source_time,
    trail_alpha,
    validate_colors,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.render_v3 import (
    ENTRY_EXIT_ARROW_SIZE,
    ENTRY_EXIT_CROSSING_HALO_WIDTH,
    ENTRY_EXIT_CROSSING_PULSE_BASE,
    ENTRY_EXIT_CROSSING_PULSE_MAX_WIDTH,
    ENTRY_EXIT_CROSSING_PULSE_RATE,
    ENTRY_EXIT_GLOW_WIDTH,
    ENTRY_EXIT_LABEL_SIZE,
    ENTRY_EXIT_LINE_WIDTH,
    DynamicRenderer,
    palette,
    validate_motion,
)


@pytest.mark.parametrize("a,b", [(0, 3.9), (4, 8.9), (9, 14.9), (20, 24.9), (30, 34.9), (35, 39.9)])
def test_accelerated_mapping(a: float, b: float) -> None:
    assert 6 <= (source_time(b) - source_time(a)) / (b - a) <= 15.1


def test_quantization_never_uses_future_source_frame() -> None:
    for n in range(1350):
        t = n / 30
        assert 0 <= source_time(t, quantized=False) - source_time(t) < 0.100001
    assert source_time(44.8) == source_time(44.99)


def test_history_excludes_future_and_left_boundary() -> None:
    data = pd.DataFrame({"source_timestamp": [54.9, 55, 55.1, 100, 100.1]})
    original = data.copy()
    assert history_at(data, 100).source_timestamp.tolist() == [55.1, 100]
    pd.testing.assert_frame_equal(data, original)
    with pytest.raises(ValueError):
        history_at(data, 100, 0)


def test_trails_fade_and_disappear() -> None:
    values = [trail_alpha(age) for age in range(61)]
    assert values == sorted(values, reverse=True)
    assert values[-1] == trail_alpha(-1) == 0


def test_semantic_palette_is_distinct_and_scoped() -> None:
    roles = [
        "box_default",
        "trajectory_primary",
        "density_high",
        "entry_color",
        "exit_color",
        "warning_active",
    ]
    assert len({COLORS[key] for key in roles}) == len(roles)
    assert "#1CBCDD" not in [COLORS[k] for k in roles]
    previous = dict(TOKENS)
    with palette():
        assert TOKENS["box_default"] == "#F4F7FA"
    assert previous == TOKENS


def test_timebase_metadata() -> None:
    contract = playback_contract()
    assert contract["analytics_timebase"] == "ORIGINAL_SOURCE_TIME"
    assert contract["presentation_playback"] == "ACCELERATED_FOR_VISUALIZATION"
    assert not contract["future_observations"]


def test_dynamic_opening_retains_first15() -> None:
    renderer = DynamicRenderer.__new__(DynamicRenderer)
    renderer.kpis = canonical_metrics(
        {
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
    )
    source = Image.new("RGB", (1080, 1080))
    transcripts = {}
    with patch.object(DynamicRenderer, "scene_pixels", return_value=source), palette():
        for i, t in enumerate((0, 8.8, 14.8)):
            transcripts[i] = renderer.frame(source, t).info["transcript"]
    assert validate_first15(transcripts)["automated_status"] == "PASS"


def test_motion_gate_rejects_static_contours(tmp_path: Path) -> None:
    proof = tmp_path / "proof.mp4"
    proof.write_bytes(b"fixture-only")
    rows: list[dict[str, Any]] = [
        {
            "scene": 0,
            "source_hash": str(i),
            "field_hash": "STATIC",
            "trail_hash": str(i),
            "source_timestamp": i * 10,
            "display_time": i,
            "active_ids": [i],
            "maximum_observation_time": i * 10,
        }
        for i in range(3)
    ]
    with pytest.raises(ValueError, match="Motion proof failed"):
        validate_motion(rows, tmp_path / "motion.json", proof)


def test_future_points_do_not_change_earlier_contours() -> None:
    from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.render_v2 import (
        density_layer,
    )

    past = pd.DataFrame(
        [
            {"track_id": 1, "source_timestamp": 80 + i, "reference_x": 700 + i, "reference_y": 500}
            for i in range(20)
        ]
    )
    future = past.assign(source_timestamp=past.source_timestamp + 50, reference_x=1000)
    combined = pd.concat([past, future])
    with palette():
        before, _ = density_layer(history_at(past, 100))
        same, _ = density_layer(history_at(combined, 100))
        later, _ = density_layer(history_at(combined, 150))
    assert np.array_equal(np.asarray(before), np.asarray(same))
    assert not np.array_equal(np.asarray(before), np.asarray(later))


def test_deprecated_palette_is_rejected() -> None:
    validate_colors(COLORS)
    with pytest.raises(ValueError, match="DEPRECATED_VISUAL_STYLE"):
        validate_colors(TOKENS)


def test_freshness_fails_closed(tmp_path: Path) -> None:
    contract, output = tmp_path / "contract", tmp_path / "output"
    contract.touch()
    output.touch()
    os.utime(output, ns=(100, 100))
    with pytest.raises(ValueError, match="Stale"):
        require_fresh([output], [contract])
    os.utime(contract, ns=(50, 50))
    require_fresh([output], [contract])


def test_entry_exit_visual_settings_are_visibility_focused() -> None:
    assert 2 <= ENTRY_EXIT_LINE_WIDTH <= 4
    assert ENTRY_EXIT_LINE_WIDTH < ENTRY_EXIT_GLOW_WIDTH
    assert ENTRY_EXIT_CROSSING_PULSE_BASE >= 6
    assert ENTRY_EXIT_CROSSING_PULSE_RATE >= 4.5
    assert ENTRY_EXIT_CROSSING_PULSE_MAX_WIDTH >= 4


def test_entry_exit_labels_and_arrows_are_configured_for_readability() -> None:
    assert ENTRY_EXIT_LABEL_SIZE >= 20
    assert ENTRY_EXIT_LABEL_SIZE <= 24
    assert ENTRY_EXIT_CROSSING_PULSE_BASE + 3 * ENTRY_EXIT_CROSSING_PULSE_RATE >= 18
    assert ENTRY_EXIT_ARROW_SIZE >= 12
    assert ENTRY_EXIT_CROSSING_HALO_WIDTH > 0


def test_freshness_contract_uses_frozen_v3_dependencies(tmp_path: Path) -> None:
    contract = tmp_path / "dependency_contract.txt"
    contract.touch()
    os.utime(contract, ns=(50, 50))
    outputs = [tmp_path / "output_one.txt", tmp_path / "output_two.txt"]
    for path in outputs:
        path.write_text("x", encoding="utf-8")
        os.utime(path, ns=(200, 200))
    require_fresh(outputs, [contract])


def test_no_unintended_contract_shift() -> None:
    contract = playback_contract()
    assert contract["analytics_timebase"] == "ORIGINAL_SOURCE_TIME"
    assert (
        contract["kpi_scope"]
        == "Fixed audited 24:00 snapshot (1380,1440], not current montage readings."
    )
    assert contract["close_hold_seconds"] == 0.25
