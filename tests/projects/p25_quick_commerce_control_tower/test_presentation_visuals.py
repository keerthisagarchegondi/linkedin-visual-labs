"""Chart reconciliation, isolated JavaScript behavior and animated evidence contracts."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import ImageChops

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_charts as charts,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_navigation as navigation,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_world as world,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
    allocation_example,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    Evidence,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_html import (
    report_html,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    Scene,
    storyboards,
)

from .test_presentation import evidence as evidence
from .test_presentation import png_bytes


@pytest.mark.parametrize(
    "key",
    [
        "demand_history",
        "state_demand",
        "category_demand",
        "store_demand",
        "weekday_demand",
        "calendar_context",
        "model_wape",
        "model_bias",
        "wape_bias",
        "forecast_example",
        "champion_counts",
        "exception_rankings",
        "under_over",
        "weekday_wape",
        "event_analysis",
        "snap_analysis",
        "disagreement",
        "allocation",
        "reallocation",
        "critical",
        "actual_uncovered",
        "scenario_required_hours",
        "scenario_allocated_hours",
        "scenario_unused_capacity",
        "scenario_uncovered_hours",
        "scenario_critical_store_days",
        "inventory",
    ],
)
def test_chart_has_reconcilable_data(evidence: Evidence, key: str) -> None:
    spec = charts.chart_specs(evidence)[key]
    assert spec["source"] and spec["meaning"] and spec["unit"] and spec["title"]
    assert spec["data"]
    for trace in spec["data"]:
        assert len(trace["x"]) == len(trace["y"]) > 0
        assert all(value is not None for value in trace["y"])
        assert trace["type"] in ("bar", "scatter")


def test_eda_grain_and_totals(evidence: Evidence) -> None:
    v = evidence.visuals
    total = sum(r["demand"] for r in v["demand_history"])
    assert total == 60 * 20 * 100 + sum(day % 7 * 10 for day in range(60)) * 20
    for key in ("state_demand", "category_demand", "store_demand"):
        assert sum(r["demand"] for r in v[key]) == total
    assert len(v["state_demand"]) == 3 and len(v["category_demand"]) == 2
    assert len(v["store_demand"]) == 10 and len(v["weekday_demand"]) == 7
    assert len(v["forecast_example"]) == 28 * 4
    assert {(r["store_id"], r["category"]) for r in v["forecast_example"]} == {("WI_2", "FOODS")}
    signals = {r["signal"]: r["series_days"] for r in v["calendar_context"]}
    assert signals["Event"] + signals["Ordinary"] == 1200
    assert signals["SNAP active"] + signals["SNAP inactive"] == 1200


def test_chart_values_follow_metric_and_allocation_mutations(evidence: Evidence) -> None:
    evidence.tables["network_scorecard"][0]["wape"] = 0.0123
    spec = charts.chart_specs(evidence)
    assert spec["model_wape"]["data"][0]["y"][0] == pytest.approx(1.23)
    assert sum(spec["champion_counts"]["data"][0]["y"]) == 20
    assert abs(sum(spec["reallocation"]["data"][0]["y"])) < 1e-9
    for index in range(3):
        assert (
            spec["actual_uncovered"]["data"][1]["y"][index]
            > spec["actual_uncovered"]["data"][0]["y"][index]
        )


def test_seven_tabs_offline_content_and_one_provenance(evidence: Evidence) -> None:
    doc = report_html(evidence, png_bytes(evidence))
    visible = doc.split("<script")[0]
    for key, label in navigation.TABS:
        assert f'data-tab="{key}"' in visible and f">{label}</a>" in visible
        assert f'data-panel="{key}"' in visible
    assert not re.search(r"<[^>]+\shidden(?:[\s=>])", visible)
    assert "DoorDash" not in visible
    assert visible.count(navigation.PROVENANCE) == 1
    assert visible.count("Chart values · accessible evidence") == 28
    assert "EXECUTIVE DECISION" in visible
    assert "<script src=" not in doc and "<link " not in doc
    assert doc.index(navigation.CONTROLLER) < doc.index("const specs=")


@pytest.mark.parametrize("failure", [False, True])
def test_actual_tab_controller_in_isolated_javascript(tmp_path: Path, failure: bool) -> None:
    """Execute the shipped controller against a minimal DOM; no browser or network."""
    executable = shutil.which("node")
    assert executable, "JavaScript runtime is required for controller validation"
    harness = """
const assert=require('node:assert/strict');
const ids=IDS;
const tabs=ids.map(id=>({dataset:{tab:id},events:{},attrs:{},tabIndex:0,
 addEventListener(k,f){this.events[k]=f;},
 setAttribute(k,v){if(FAIL)throw Error('injected DOM error');this.attrs[k]=v;},
 focus(){this.focused=true;}}));
const panels=ids.map(id=>({dataset:{panel:id},hidden:false}));
global.document={querySelectorAll:s=>s==='[data-tab]'?tabs:panels};
global.window={dispatchEvent(){}};
CONTROLLER
if(FAIL){assert(panels.every(p=>!p.hidden));}
else{
 assert.equal(panels[0].hidden,false);assert(panels.slice(1).every(p=>p.hidden));
 for(let i=0;i<tabs.length;i++){
  tabs[i].events.click({preventDefault(){}});
  assert.equal(tabs[i].attrs['aria-selected'],'true');
  assert.deepEqual(panels.map(p=>p.hidden),ids.map((_,j)=>j!==i));
 }
 tabs[6].events.keydown({key:'ArrowRight',preventDefault(){}});
 assert.equal(panels[0].hidden,false);assert(tabs[0].focused);
 tabs[0].events.keydown({key:'End',preventDefault(){}});
 assert.equal(panels[6].hidden,false);
}
console.log('controller passed');
"""
    script = harness.replace("IDS", json.dumps([k for k, _ in navigation.TABS]))
    script = script.replace("FAIL", str(failure).lower()).replace(
        "CONTROLLER", navigation.CONTROLLER
    )
    path = tmp_path / "controller.cjs"
    path.write_text(script, encoding="utf-8")
    result = subprocess.run([executable, str(path)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "controller passed" in result.stdout


@pytest.mark.parametrize("width", [360, 760, 1024, 1280, 1920])
def test_responsive_containment_rules(width: int) -> None:
    """CSS contract, not a claim of browser-computed geometry."""
    css = navigation.CSS
    for rule in [
        "minmax(0,1fr)",
        "min-width:0",
        "max-width:100%",
        "overflow-x:auto",
        "height:450px",
        "min-height:450px",
        "scroll-padding-top:110px",
        "scroll-margin-top:110px",
        "position:relative",
        "flex-wrap:wrap",
    ]:
        assert rule in css
    content = min(width, 1280) - (24 if width <= 760 else 48)
    assert 0 < content <= width
    if width <= 760:
        assert "nav{position:relative" in css


def test_animation_actions_and_exact_transport(evidence: Evidence) -> None:
    boards = storyboards(evidence)
    actions = {action for scenes in boards.values() for scene in scenes for action in scene.actions}
    assert {
        "node_movement",
        "forecast_line_progression",
        "champion_assignment",
        "labor_token_movement",
        "counter_transition",
    } <= actions
    assert all(
        scene.actions and scene.kind != "cards" for scenes in boards.values() for scene in scenes
    )
    _, pairs = allocation_example(evidence)
    moves = world.transfers(evidence)
    for store, before, after in pairs:
        incoming = sum(amount for _, dest, amount in moves if dest == store)
        outgoing = sum(amount for src, _, amount in moves if src == store)
        assert before + incoming - outgoing == pytest.approx(after)


@pytest.mark.parametrize("video", ["forecast_model_arena", "forecast_to_labor_optimizer"])
def test_motion_and_geometry_across_beats(evidence: Evidence, video: str) -> None:
    for scene in storyboards(evidence)[video]:
        early = world.world_canvas(evidence, scene, 0.1)
        late = world.world_canvas(evidence, scene, 0.9)
        # Exclude headline/caption; evidence objects within the world must actually change.
        assert ImageChops.difference(
            early.image.crop((32, 300, 1048, 1100)), late.image.crop((32, 300, 1048, 1100))
        ).getbbox()
        for p in (0, 0.1, 0.4, 0.7, 1):
            world.world_canvas(evidence, scene, p).validate()
    assert world.ease(0) == 0 and world.ease(1) == 1
    assert world.ease(0.25) < 0.25 and world.ease(0.75) > 0.75


def test_network_effects_do_not_cross_store_labels(evidence: Evidence) -> None:
    # Scenario mechanics remain available, but are not an unrelated video narrative branch.
    scene = Scene(
        "Scenario pressure",
        "Capacity stays fixed under each scenario.",
        (),
        kind="shock",
        world="labor",
        actions=("scenario_shock",),
    )
    for progress in (0.25, 0.4, 0.75, 0.9):
        image = world.world_canvas(evidence, scene, progress).image
        for x, y in world.positions(evidence).values():
            interior = image.crop((x - 110, y - 23, x + 110, y + 23))
            colors = interior.getcolors(interior.width * interior.height)
            assert colors is not None
            assert all(color != (189, 101, 9) for _, color in colors)
