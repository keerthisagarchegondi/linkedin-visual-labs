"""Decision order, concise exposed copy, allocation summary and question-led videos."""

from __future__ import annotations

import re
from typing import Any

import pytest

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_decisions as decisions,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_navigation as navigation,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    Evidence,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_html import (
    report_html,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    storyboards,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_world import (
    world_canvas,
)

from .test_presentation import evidence as evidence
from .test_presentation import png_bytes


def document(e: Evidence) -> str:
    return report_html(e, png_bytes(e))


def test_overview_decision_order(evidence: Evidence) -> None:
    doc = document(evidence)
    parts = [
        '<section id="overview">',
        "<h2>PROJECT OVERVIEW</h2>",
        decisions.BUSINESS_QUESTION,
        "Decision framework",
        'id="visual-demand_history"',
        "DECISION 01 — WHICH FORECASTS SHOULD WE TRUST?",
        "<h2>EXECUTIVE DECISION</h2>",
    ]
    positions = [doc.index(part) for part in parts]
    assert positions == sorted(positions)
    assert doc.index('id="impact-check"') > doc.index('id="section-5"')
    assert doc.index('id="impact-check"') < doc.index('id="panel-scenario"')
    assert "How this becomes an operating system" in doc and "FINAL EXECUTIVE ANSWER" in doc
    assert decisions.RECOMMENDATION in doc


@pytest.mark.parametrize("key", [key for key, _ in navigation.TABS])
def test_each_tab_has_question_evidence_decision(evidence: Evidence, key: str) -> None:
    intro = decisions.introduction(key, evidence)
    assert intro.index("QUESTION") < intro.index("EVIDENCE")
    assert "DECISION / IMPLICATION" in decisions.implication(key, evidence)
    assert decisions.implication("arena" if key == "overview" else key, evidence) in document(
        evidence
    )


def test_framework_and_compact_copy(evidence: Evidence) -> None:
    doc = document(evidence)
    assert all(label in doc for label in decisions.FRAMEWORK)
    assert decisions.copy_words(doc) < 2300
    parser = decisions.CopyCounter()
    parser.feed(doc.split("<script")[0])
    exposed = " ".join(parser.words)
    assert exposed.count("WAPE is absolute error") == 1
    assert exposed.count("Data leakage means") <= 1
    assert "Definitions and technical reference" in doc


def test_copy_measure_excludes_disclosures_tables_and_code() -> None:
    sample = (
        "<p>Three exposed words</p><details><summary>Hidden summary</summary>"
        "<div><p>Hidden prose here</p></div></details><table><tr><td>123</td></tr></table>"
        "<p>Two more</p><script>ignored code</script>"
    )
    assert decisions.copy_words(sample) == 5


def test_final_allocation_averages_match_all_dates(evidence: Evidence) -> None:
    rows = evidence.tables["labor_allocations"]
    additions: list[dict[str, Any]] = []
    for r in rows:
        additions.append({**r, "date": "2016-04-26", "allocated_hours": r["allocated_hours"] + 2})
    rows.extend(additions)
    summaries = decisions.allocation_summary(evidence)
    assert len(summaries) == 10
    for summary in summaries:
        selected = [
            r["allocated_hours"]
            for r in rows
            if r["store_id"] == summary["store"] and r["allocation_method"] == "optimized"
        ]
        assert summary["optimized_hours"] == pytest.approx(sum(selected) / len(selected))
        assert summary["planning_days"] == 2
        assert summary["difference_hours"] == pytest.approx(
            summary["optimized_hours"] - summary["proportional_hours"]
        )
    assert sum(s["difference_hours"] for s in summaries) == pytest.approx(0)
    assert {s["direction"] for s in summaries} == {"More", "Fewer"}
    doc = document(evidence)
    assert "What was the final labor allocation?" in doc
    assert "Date-level allocation evidence" in doc
    assert "Final optimized hours/day" in doc


@pytest.mark.parametrize("defect", ["duplicate", "unmatched"])
def test_allocation_summary_rejects_bad_grain(evidence: Evidence, defect: str) -> None:
    rows = evidence.tables["labor_allocations"]
    if defect == "duplicate":
        rows.append(dict(rows[0]))
    else:
        rows[0]["date"] = "2016-04-26"
    with pytest.raises(ValueError, match="Allocation summary"):
        decisions.allocation_summary(evidence)


def test_impact_is_direct_and_conditional(evidence: Evidence) -> None:
    text = decisions.impact(evidence)
    assert "2 → 1" in text and "70.00 → 80.00" in text
    assert decisions.IMPACT_CONCLUSION in text and decisions.RECOMMENDATION in text
    assert "equal priority weights" in text and "business objective is under-specified" in text
    assert "not a causal service-impact estimate" in text


@pytest.mark.parametrize(
    "term",
    [
        "Service-level priorities",
        "Actual labor productivity",
        "Labor schedules",
        "Cost of unmet demand",
        "Inventory and stock availability",
        "Lead times",
        "Additional forecast drivers",
        "Future untouched evaluation window",
    ],
)
def test_next_actions_specify_missing_inputs(term: str) -> None:
    assert term in decisions.next_actions()


@pytest.mark.parametrize("video", ["forecast_model_arena", "forecast_to_labor_optimizer"])
def test_video_question_answer_timing(evidence: Evidence, video: str) -> None:
    scenes = storyboards(evidence)[video]
    assert [s.seconds for s in scenes] == (
        [3, 4, 4, 4, 8, 4, 3] if video == "forecast_model_arena" else [3, 4, 4, 4, 7, 5, 3]
    )
    assert sum(s.seconds for s in scenes) == 30
    assert scenes[4].role == "second_hook" and sum(s.seconds for s in scenes[:4]) == 15
    assert scenes[-1].role == "final_answer" and sum(s.seconds for s in scenes[:-1]) == 27
    answer = " ".join(b.text for b in world_canvas(evidence, scenes[-1], 0.1).boxes)
    if video == "forecast_model_arena":
        assert scenes[4].title == "Which forecast should run each store?"
        assert "governed" in answer and "Different demand patterns" in answer
        assert "7.00% WAPE" in scenes[2].title
        assert all(s.world == "forecast" for s in scenes)
    else:
        assert scenes[4].title == "The allocation engine worked."
        assert "Actual coverage worsened under equal priorities" in scenes[4].caption
        assert "Encode the business objective better" in answer and "Then optimize" in answer
        assert "shortage costs" in scenes[5].caption
        assert "shock" not in [s.kind for s in scenes]
    assert not re.search(r"DoorDash", str(scenes))
