"""Offline display contracts; hypothetical evidence and actual short media."""

from __future__ import annotations

import copy
import io
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from PIL import ImageChops
from typer.testing import CliRunner

from linkedin_visual_labs.cli import app
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_media as media,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    build_pipeline_context,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
    Canvas,
    champion_canvas,
    scene_canvas,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    LABOR_LIMIT,
    NAMES,
    RETROSPECTIVE,
    Evidence,
    load_evidence,
    number,
    validate_story,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_html import (
    report_html,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    SECTIONS,
    section_briefs,
    storyboards,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.rendering import validate_html


@pytest.fixture()
def evidence() -> Evidence:
    """Deliberately hypothetical table values; no ignored runtime artifact dependency."""
    tables: dict[str, list[dict[str, Any]]] = {}
    stores = list(load_commerce_config().labor.store_priority_weights)
    cells = [
        dict(
            store_id=s,
            category=c,
            champion_model=None,
            review_flag=False,
            review_threshold=0.5,
            wape=0.08,
            bias=-0.02,
            improvement_percentage_points=2.0,
            disagreement=0.12,
        )
        for s in stores
        for c in ("FOODS", "HOUSEHOLD")
    ]
    eligible = [r for r in cells if (r["store_id"], r["category"]) != ("TX_3", "FOODS")]
    for r, m in zip(
        eligible, ["hist_gradient_boosting"] * 9 + ["mlp"] * 7 + ["holt_winters"] * 3, strict=True
    ):
        r["champion_model"] = m
    no = next(r for r in cells if r["champion_model"] is None)
    no.update(wape=None, bias=None, improvement_percentage_points=None)
    tables["hist_gradient_boosting_importance"] = [
        dict(
            feature=f,
            mean_mae_increase=v,
            std_mae_increase=0.25,
            model_name="hist_gradient_boosting",
            sample_rows=256,
            repeats=3,
            classification="training_in_sample_interpretation",
            sample_policy="last_256_training_feature_rows",
            not_for_tuning="true",
        )
        for f, v in [("lag_28", 4.0), ("weekday", 8.0), ("lag_35", -0.5)]
    ]
    tables["champions"] = cells
    tables["network_scorecard"] = [
        dict(
            model_name=m,
            wape=0.07 + i * 0.01,
            bias=-0.03,
            mae=150.0 + i,
            completeness=1.0,
            globally_eligible=False,
        )
        for i, m in enumerate(NAMES)
    ]
    tables["local_champion_portfolio"] = [
        dict(portfolio=p, wape=w, covered_series=19)
        for p, w in [("local_champions", 0.07), ("seasonal_naive_same_coverage", 0.1)]
    ]
    tables["dri_exception_queue"] = [
        dict(
            store_id=s,
            category="FOODS",
            priority_rank=i + 1,
            observed_pattern="Test-only underforecast pattern.",
            evidence="Test evidence: 4 event and 24 ordinary dates.",
            operational_implication="Review planning inputs.",
            recommended_experiment="Test recalibration on untouched data.",
        )
        for i, s in enumerate(["WI_2", "CA_1", "TX_3"])
    ]
    for tab, dimension in [("event_analysis", "event"), ("snap_analysis", "active")]:
        tables[tab] = [
            dict(
                model_name="hist_gradient_boosting",
                dimension=dimension,
                wape=0.07,
                comparison_wape=0.08,
                observations=80,
                comparison_observations=480,
            )
        ]
    tables["day_of_week_analysis"] = [
        dict(model_name=m, dimension="Sunday", wape=0.12, observations=80) for m in NAMES
    ]
    tables["scenario_summary"] = []
    tables["retrospective_summary"] = []
    tables["tradeoff_summary"] = []
    for s in ("Base", "+15% demand", "-10% productivity"):
        for m in ("proportional", "optimized"):
            tables["scenario_summary"].append(
                dict(
                    scenario=s,
                    allocation_method=m,
                    required_hours=500.0,
                    total_capacity=480.0,
                    allocated_hours=480.0,
                    unused_capacity=0.0,
                    uncovered_hours=20.0,
                    weighted_uncovered_hours=20.0,
                    labor_cost=10560.0,
                    objective=12560.0,
                    critical_store_days=2 if m == "proportional" else 1,
                    constrained_stores=2,
                    stores_at_minimum=0,
                    stores_at_maximum=0,
                    feasibility="feasible",
                )
            )
            tables["retrospective_summary"].append(
                dict(
                    scenario=s,
                    allocation_method=m,
                    actual_required_hours=550.0,
                    actual_uncovered_hours=70.0 if m == "proportional" else 80.0,
                    actual_critical_store_days=3,
                )
            )
        tables["tradeoff_summary"].append(
            dict(
                scenario=s,
                gained_hours_stores=2,
                lost_hours_stores=1,
                shortage_improved_store_days=2,
                shortage_worsened_store_days=1,
                shortage_unchanged_store_days=7,
            )
        )
    tables["labor_allocations"] = [
        dict(
            scenario="Base",
            date="2016-04-25",
            store_id=store,
            allocation_method=method,
            allocated_hours=20.0 if method == "proportional" else (24.0 if i % 2 else 16.0),
        )
        for i, store in enumerate(stores)
        for method in ("proportional", "optimized")
    ]
    tables["inventory_proxy"] = [
        dict(risk_status=r, synthetic=True, illustrative=True)
        for r in ("Healthy", "Monitor", "Reorder", "Expedite")
    ]
    config = load_commerce_config().model_dump(mode="json")
    stages: dict[str, dict[str, Any]] = {
        "operations": {"configuration": config},
        "demand_daily": dict(
            stores=10,
            series=20,
            training_start="2011-01-29",
            training_end="2016-04-24",
            holdout_start="2016-04-25",
            holdout_end="2016-05-22",
            record_id="TEST_ONLY",
            source_files=[],
        ),
    }
    import pandas as pd

    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_charts import (
        display_tables,
    )

    demand = pd.DataFrame(
        [
            dict(
                date=date,
                store_id=store,
                state_id=store[:2],
                category=category,
                demand=100 + day % 7 * 10,
                weekday=date.day_name(),
                event_name_1="Event" if day % 13 == 0 else "",
                event_name_2="",
                snap=day % 2,
            )
            for day, date in enumerate(pd.date_range("2016-01-01", periods=60))
            for store in stores
            for category in ["FOODS", "HOUSEHOLD"]
        ]
    )
    predictions = pd.DataFrame(
        [
            dict(
                date=date,
                store_id="WI_2",
                category="FOODS",
                model_name=model,
                actual_units=100 + day % 7 * 10,
                forecast_units=95 + day % 7 * 9 + index,
            )
            for day, date in enumerate(pd.date_range("2016-04-25", periods=28))
            for index, model in enumerate(NAMES)
        ]
    )
    for row in tables["network_scorecard"]:
        row.update(shortfall_units=120, excess_units=40)
    for index, row in enumerate(tables["dri_exception_queue"]):
        row.update(priority_score=0.03 - index * 0.005, shortfall_units=300 - index * 50)
    return Evidence(
        tables, stages, {}, display_tables(demand, predictions, tables["dri_exception_queue"])
    )


def png_bytes(evidence: Evidence) -> bytes:
    stream = io.BytesIO()
    champion_canvas(evidence).image.save(stream, format="PNG")
    return stream.getvalue()


def test_map_geometry_and_all_cells(evidence: Evidence) -> None:
    canvas = champion_canvas(evidence)
    assert canvas.image.size == (1080, 1350)
    canvas.validate()
    text = " ".join(b.text for b in canvas.boxes)
    assert len(evidence.tables["champions"]) == 20
    for row in evidence.tables["champions"]:
        assert row["store_id"] in text
    assert "No eligible champion" in text and "Review required" in text
    assert text.count("Disagreement") == 20
    assert text.count("no flag") == 20
    assert "WAPE undefined" in text
    assert not ImageChops.difference(canvas.image, champion_canvas(evidence).image).getbbox()


def test_map_metric_mutation_changes_pixels(evidence: Evidence) -> None:
    first = champion_canvas(evidence).image
    evidence.tables["champions"][0]["wape"] = 0.0912
    after = champion_canvas(evidence)
    assert "9.12%" in " ".join(b.text for b in after.boxes)
    assert ImageChops.difference(first, after.image).getbbox()


@pytest.mark.parametrize("section", SECTIONS)
def test_eight_business_sections(evidence: Evidence, section: str) -> None:
    doc = report_html(evidence, png_bytes(evidence))
    if section == "Governance and Assumptions":
        assert "<h2>How this becomes an operating system</h2>" in doc
        assert "<h3>Governance and Assumptions</h3>" in doc
    elif section == "What I Would Do as the Forecast Accuracy DRI":
        assert "<summary>What I Would Do as the Forecast Accuracy DRI</summary>" in doc
        assert "Proposed review cadence, triggers and ownership" in doc
    else:
        assert f"<h2>{section}</h2>" in doc
    brief = next(b for b in section_briefs(evidence) if b["title"] == section)
    assert all(brief[k] for k in ("question", "view", "finding", "action"))


def test_html_offline_numeric_reconciliation(evidence: Evidence) -> None:
    png = png_bytes(evidence)
    doc = report_html(evidence, png)
    validate_html(doc, evidence, png)
    assert "7.00%" in doc and "10.00%" in doc
    assert "<script src=" not in doc and "<link " not in doc
    assert "Plotly.newPlot" in doc
    with pytest.raises(ValueError, match="reconcile"):
        validate_html(doc.replace("7.00%", "6.00%"), evidence, png)
    with pytest.raises(ValueError, match="external"):
        validate_html(
            doc.replace("</head>", '<script src="https://invalid.test/x.js"></script></head>'),
            evidence,
            png,
        )


def test_html_escaping(evidence: Evidence) -> None:
    evidence.tables["dri_exception_queue"][0]["observed_pattern"] = "<img src=x onerror=alert(1)>"
    doc = report_html(evidence, png_bytes(evidence))
    assert "&lt;img src=x onerror=alert(1)&gt;" in doc
    assert "<img src=x" not in doc


def test_narrative_limitations(evidence: Evidence) -> None:
    doc = report_html(evidence, png_bytes(evidence))
    for text in (
        RETROSPECTIVE,
        LABOR_LIMIT,
        "No single model passed eligibility",
        "Synthetic illustrative inventory proxy",
        "Retrospective actual coverage worsened overall",
        "The optimizer reallocates fixed capacity; it never creates labor",
    ):
        assert text in doc
    for claim in (
        "optimizer improved overall service",
        "optimizer reduced actual uncovered workload",
        "optimizer created labor",
        "optimization created efficiency",
        "DoorDash improvement",
    ):
        assert claim not in doc


@pytest.mark.parametrize("video", ["forecast_model_arena", "forecast_to_labor_optimizer"])
def test_seven_animated_beats_geometry(evidence: Evidence, video: str) -> None:
    scenes = storyboards(evidence)[video]
    assert len(scenes) == 7 and sum(s.seconds for s in scenes) == 30
    for i, s in enumerate(scenes):
        assert 3 <= len(s.caption.split()) <= 18
        assert len(s.caption.split()) / s.seconds <= 5
        canvas = scene_canvas(evidence, s, i, video)
        canvas.validate()
        assert canvas.image.convert("L").getbbox() is not None
    if video == "forecast_model_arena":
        assert "7.00%" in str(scenes) and "RETROSPECTIVE" in str(scenes)
    else:
        assert "70.00 → 80.00" in str(scenes)


@pytest.mark.parametrize("field", ["review_flag", "champion_model", "actual_coverage", "objective"])
def test_changed_story_rejected(evidence: Evidence, field: str) -> None:
    validate_story(evidence)
    e = copy.deepcopy(evidence)
    if field == "review_flag":
        e.tables["champions"][0]["review_flag"] = True
    elif field == "champion_model":
        e.tables["champions"][0]["champion_model"] = "seasonal_naive"
    elif field == "actual_coverage":
        e.tables["retrospective_summary"][1]["actual_uncovered_hours"] = 0
    else:
        e.tables["scenario_summary"][1]["objective"] = 0
    with pytest.raises(ValueError):
        validate_story(e)


def test_layout_rejects_overflow_and_overlap() -> None:
    c = Canvas()
    with pytest.raises(ValueError, match="layout height"):
        c.text("Long message " * 20, 40, 40, 100, 20)
    c.text("First", 40, 40, 500, 40)
    c.text("Second", 40, 40, 500, 40)
    with pytest.raises(ValueError, match="Overlapping"):
        c.validate()


def test_undefined_numeric_display() -> None:
    assert number(None) == "undefined"
    assert number(0.0794, percent=True) == "7.94%"
    assert number(-0.0514, percent=True) == "-5.14%"


def test_missing_evidence_fails_closed(tmp_path: Path) -> None:
    context = build_pipeline_context()
    context = replace(context, paths=replace(context.paths, data=tmp_path))
    with pytest.raises(FileNotFoundError):
        load_evidence(context)


def test_corrupt_canonical_hash_rejected(tmp_path: Path) -> None:
    context = build_pipeline_context()
    context = replace(context, paths=replace(context.paths, data=tmp_path))
    for name in ("demand_daily", "predictions", "operations"):
        (tmp_path / f"{name}.metadata.json").write_text("{}", encoding="utf-8")
    (tmp_path / "evaluation.metadata.json").write_text(
        json.dumps({"artifact_sha256": {"champions": "incorrect"}}), encoding="utf-8"
    )
    (tmp_path / "champions.csv").write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_evidence(context)


def test_packaged_ffmpeg_ignores_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMAGEIO_FFMPEG_EXE", "nonexistent.exe")
    path, version = media.packaged_ffmpeg()
    assert "imageio_ffmpeg" in str(path) and path.is_file()
    assert version.startswith("ffmpeg version")


def test_short_real_encode_full_decode_and_content(evidence: Evidence, tmp_path: Path) -> None:
    name = "forecast_model_arena"
    scene = replace(storyboards(evidence)[name][0], seconds=1)
    path = tmp_path / "short.mp4"
    media.encode_video(evidence, (scene,), name, path)
    result = media.validate_video(path, expected_frames=30)
    assert result["codec"] == "h264" and result["pixel_format"] == "yuv420p"
    assert result["width"] == 1080 and result["height"] == 1350
    assert result["duration_seconds"] == 1 and result["fps"] == 30
    assert result["frame_count"] == 30 and result["full_decode"]
    assert max(media.validate_scene_pixels(evidence, (scene,), name, path)) < 3
    with pytest.raises(ValueError, match="mismatch"):
        media.validate_video(path, expected_frames=31)


def test_cli_render_validate_registered() -> None:
    result = CliRunner().invoke(app, ["commerce", "--help"])
    assert result.exit_code == 0
    assert "render" in result.stdout and "validate" in result.stdout


def test_missing_packaged_binary_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(media, "distribution", lambda _: SimpleNamespace(files=()))
    with pytest.raises(ValueError, match="packaged FFmpeg"):
        media.packaged_ffmpeg()


def test_empty_video_rejected(tmp_path: Path) -> None:
    path = tmp_path / "empty.mp4"
    path.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        media.validate_video(path)


@pytest.mark.parametrize(
    "term",
    [
        "Walmart sales history",
        "CA = California",
        "TX = Texas",
        "WI = Wisconsin",
        "California store 1",
        "California store 2",
        "Texas store 3",
        "Wisconsin store 2",
        "food-related merchandise",
        "household merchandise",
        "CA_3 / FOODS",
        "Four approaches enter the arena",
        "Transparent baseline",
        "Classical statistical",
        "Machine learning",
        "Neural-network challenger",
        "Why include it?",
        "Training history versus the holdout",
        "Data leakage",
        "mutation tests",
        "How do we judge a forecast?",
        "WAPE",
        "MAE",
        "Bias",
        "Completeness",
        "Model disagreement",
        "10% guardrail",
        "No eligible champion",
        "Results in plain English",
    ],
)
def test_recruiter_overview_visible_explanations(evidence: Evidence, term: str) -> None:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_overview as overview,
    )

    assert term in overview.overview_html(evidence)


def test_overview_first_navigation_and_detail_preservation(evidence: Evidence) -> None:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.rendering import (
        ResourceParser,
    )

    png = png_bytes(evidence)
    doc = report_html(evidence, png)
    parser = ResourceParser()
    parser.feed(doc)
    assert parser.section_ids == ["overview"] + [f"section-{i}" for i in range(1, 9)]
    assert len(parser.anchors) == 7
    assert set(parser.anchors) <= set(parser.ids)
    assert "position:sticky" in doc and "<details><summary>" in doc
    assert doc.count("<table>") >= 8
    assert "<abbr title=" in doc
    with pytest.raises(ValueError, match="anchor"):
        validate_html(doc.replace('href="#panel-overview"', 'href="#missing"'), evidence, png)


@pytest.mark.parametrize("video", ["forecast_model_arena", "forecast_to_labor_optimizer"])
def test_social_timing_primary_result_and_second_hook(evidence: Evidence, video: str) -> None:
    scenes = storyboards(evidence)[video]
    time = 0
    result_times = []
    hooks = []
    assert scenes[0].role == "setup"
    for scene in scenes:
        if scene.role == "primary_result":
            result_times.append(time)
        if scene.role == "second_hook":
            hooks.append(time)
        time += scene.seconds
    assert time == 30
    assert min(result_times) <= 10 and max(result_times) < 15
    assert hooks == [15]
    first_half = str(scenes[:4])
    if video == "forecast_model_arena":
        assert "7.00% WAPE" in first_half and "No model qualified everywhere" in first_half
        assert "RETROSPECTIVE" in first_half and "28 days" in first_half
    else:
        assert "480 hours/day" in first_half and "70.00 → 80.00" in first_half
        assert "actual uncovered hours increase" in first_half


def test_allocation_motion_uses_canonical_hours(evidence: Evidence) -> None:
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
        allocation_example,
        motion_frame,
    )

    date, pairs = allocation_example(evidence)
    assert date == "2016-04-25"
    assert len(pairs) == 10
    assert sum(p for _, p, _ in pairs) == sum(o for _, _, o in pairs) == 200
    scene = storyboards(evidence)["forecast_to_labor_optimizer"][2]
    canvas = scene_canvas(evidence, scene, 2, "forecast_to_labor_optimizer")
    assert ImageChops.difference(
        motion_frame(canvas, evidence, scene, 0), motion_frame(canvas, evidence, scene, 1)
    ).getbbox()
    assert not ImageChops.difference(
        motion_frame(canvas, evidence, scene, 0.5), motion_frame(canvas, evidence, scene, 0.5)
    ).getbbox()


def test_social_large_type_and_card_safe_bounds(evidence: Evidence) -> None:
    for video, scenes in storyboards(evidence).items():
        for i, scene in enumerate(scenes):
            c = scene_canvas(evidence, scene, i, video)
            c.validate()
            captions = [b for b in c.boxes if b.bounds[1] >= 1120]
            assert captions and all(b.font_size >= 30 for b in captions)
            assert all(b.font_size >= 20 for b in c.boxes)


def test_report_layout_and_contrast_contract() -> None:
    from PIL import ImageColor

    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_overview as overview,
    )

    css = overview.OVERVIEW_CSS
    assert "minmax(0,1fr)" in css and "overflow-x:auto" in css
    assert "scroll-margin-top:84px" in css and "max-width:760px" in css
    assert "outline:2px" in css and "font-size:17px" in css

    def luminance(color: str) -> float:
        channels = ImageColor.getrgb(color)
        rgb = [c / 255 for c in channels]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    for foreground, background in [
        ("#18324b", "#edf2f5"),
        ("#147477", "#f8fafb"),
        ("#465d70", "#f8fafb"),
        ("#dbe8f3", "#142e49"),
    ]:
        first, second = sorted((luminance(foreground), luminance(background)))
        assert (second + 0.05) / (first + 0.05) >= 4.5
