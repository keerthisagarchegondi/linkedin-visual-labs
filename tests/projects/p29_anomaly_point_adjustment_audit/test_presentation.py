from __future__ import annotations

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.presentation import (
    DASHBOARD_TABS,
    FIGURE_STEMS,
    _beat_alpha,
    _ease_out_cubic,
    _event_sweep,
    _smoothstep,
    load_frozen_release,
    presentation_root,
    render_dashboard,
    render_figures,
    render_social_copy,
    render_video,
)


def test_frozen_release_is_accepted() -> None:
    assert load_frozen_release()["scientific_results_status"] == "FROZEN"


def test_continuous_motion_easing_has_exact_endpoints_and_midpoint_motion() -> None:
    assert _smoothstep(0.0) == 0.0
    assert _smoothstep(1.0) == 1.0
    assert _ease_out_cubic(0.0) == 0.0
    assert _ease_out_cubic(1.0) == 1.0
    assert 0.0 < _smoothstep(0.5) < 1.0
    assert 0.0 < _beat_alpha(5.0, 4.8, 10.4) < 1.0


def test_event_length_visualization_binds_to_frozen_q_point_01_sweep() -> None:
    release = load_frozen_release()
    rows = _event_sweep(release)
    assert [int(row["event_length"]) for row in rows] == [1, 5, 10, 20, 50, 100, 200, 500, 1000]
    assert all(float(row["q"]) == 0.01 for row in rows)
    assert float(rows[-1]["adjusted_f1"]["mean"]) > float(rows[0]["adjusted_f1"]["mean"])


def test_figures_dashboard_and_social_are_frozen_formatting() -> None:
    release = load_frozen_release()
    artifact_root = presentation_root() / "test_render"
    figures = render_figures(release, artifact_root)
    assert {path.stem for path in figures} == set(FIGURE_STEMS)
    assert {path.suffix for path in figures} == {".png", ".pdf"}
    render_video(release, artifact_root)
    dashboard = render_dashboard(release, artifact_root)
    text = dashboard.read_text(encoding="utf-8")
    assert all(tab in text for tab in DASHBOARD_TABS)
    assert "THE ALERTS STAYED THE SAME. THE REPORTED F1 CHANGED." in text
    assert "IMAGINE JUDGING A SMOKE ALARM" in text
    assert f"{release['primary_condition']['raw_f1']['mean']:.3f}" in text
    assert f"{release['primary_condition']['adjusted_f1']['mean']:.3f}" in text
    assert "DUMMY" not in text
    assert "http://" not in text and "https://" not in text
    social = render_social_copy(release, artifact_root)
    assert all(path.is_file() for path in social)
