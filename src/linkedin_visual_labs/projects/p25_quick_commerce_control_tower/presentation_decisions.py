"""Decision-led copy and read-only allocation summaries for the public report."""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Any

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    NAMES,
    Evidence,
    number,
)

BUSINESS_QUESTION = (
    "Given the available demand data, which forecasting approach should we trust for each "
    "store-category, and how should we allocate limited labor based on those forecasts? "
    "Did that allocation actually improve outcomes—and if not, what should we change next?"
)
FORECAST_DECISION = "Use a governed portfolio of local champions, not one global model."
IMPACT_CONCLUSION = (
    "The allocation engine works as designed; the current formulation is "
    "incomplete: overall retrospective service coverage did not improve."
)
RECOMMENDATION = (
    "Production use requires richer business inputs. Calibrate service priorities, "
    "productivity and shortage costs, then validate on an untouched period."
)
SPINE = (
    "CONTEXT",
    "DATA",
    "FORECAST DECISION",
    "DIAGNOSIS",
    "OPERATING DECISION",
    "PROTOTYPE VALIDATION",
    "NEXT BEST ACTION",
)
FRAMEWORK = (
    "DATA",
    "FORECAST",
    "SELECT CHAMPION",
    "DIAGNOSE ERRORS",
    "ALLOCATE LABOR",
    "CHECK ACTUAL IMPACT",
    "IMPROVE MODEL / OBJECTIVE",
)
NEXT_ACTIONS = (
    (
        "Service-level priorities by store/category",
        "Measure which shortages matter most to customers and operations.",
    ),
    (
        "Actual labor productivity",
        "Collect store/category/time-of-day rates; current productivity is illustrative.",
    ),
    (
        "Labor schedules and shift constraints",
        "Replace continuous planning hours with feasible operational schedules.",
    ),
    (
        "Cost of unmet demand and service penalties",
        "Calibrate shortage costs; current uncovered penalties are illustrative and equal.",
    ),
    (
        "Inventory and stock availability",
        "Use observed availability; current on-hand inventory is synthetic.",
    ),
    (
        "Lead times and replenishment constraints",
        "Collect constraints that this prototype does not model.",
    ),
    (
        "Additional forecast drivers",
        "Test available promotions, local events, weather, prices and"
        " availability for weak series.",
    ),
    (
        "Future untouched evaluation window",
        "Validate champions and objective changes without retrospective selection bias.",
    ),
)


def bullets(items: list[str] | tuple[str, ...], *, ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    return (
        "<"
        + tag
        + ">"
        + "".join("<li>" + html.escape(item) + "</li>" for item in items)
        + "</"
        + tag
        + ">"
    )


def allocation_summary(e: Evidence) -> list[dict[str, Any]]:
    """Average canonical Base allocations over every available planning date."""
    rows = [r for r in e.tables["labor_allocations"] if r["scenario"] == "Base"]
    result = []
    for store in sorted({r["store_id"] for r in rows}):
        averages: dict[str, float] = {}
        dates: dict[str, set[str]] = {}
        for method in ("proportional", "optimized"):
            selected = [
                r for r in rows if r["store_id"] == store and r["allocation_method"] == method
            ]
            dates[method] = {r["date"] for r in selected}
            if not selected or len(dates[method]) != len(selected):
                raise ValueError("Allocation summary requires one row per store/method/date")
            averages[method] = sum(float(r["allocated_hours"]) for r in selected) / len(selected)
        if dates["proportional"] != dates["optimized"]:
            raise ValueError("Allocation summary requires matched dates")
        delta = averages["optimized"] - averages["proportional"]
        result.append(
            dict(
                store=store,
                optimized_hours=averages["optimized"],
                proportional_hours=averages["proportional"],
                difference_hours=delta,
                direction="More" if delta > 1e-7 else "Fewer" if delta < -1e-7 else "Same",
                planning_days=len(dates["optimized"]),
            )
        )
    return result


def executive(e: Evidence) -> str:
    p = e.row("scenario_summary", scenario="Base", allocation_method="proportional")
    o = e.row("scenario_summary", scenario="Base", allocation_method="optimized")
    ap = e.row("retrospective_summary", scenario="Base", allocation_method="proportional")
    ao = e.row("retrospective_summary", scenario="Base", allocation_method="optimized")
    return (
        "<p>The first-pass optimizer demonstrates redistribution of a fixed labor pool and "
        f"reduces configured critical store-days from {p['critical_store_days']} to "
        f"{o['critical_store_days']} in Base. However, retrospective actual-demand coverage "
        "shows the limits of equal priority weights: actual uncovered workload increases "
        f"from {number(ap['actual_uncovered_hours'])} to "
        f"{number(ao['actual_uncovered_hours'])} hours.</p>"
        "<p>This identifies what the objective needs next: realistic service priorities, "
        "productivity, shift, inventory and shortage-cost inputs. These results support "
        "prototype calibration, not production deployment of the current objective.</p>"
    )


def introduction(key: str, e: Evidence) -> str:
    titles = {
        "overview": "PROJECT OVERVIEW",
        "arena": "DECISION 01 — Which forecasting model should we trust?",
        "champion": "The operating forecast portfolio",
        "diagnostics": "WHERE SHOULD THE FORECAST OWNER INVESTIGATE NEXT?",
        "labor": "DECISION 02 — Given the forecast, where should fixed labor go?",
        "scenario": "How resilient is this allocation?",
        "governance": "How this becomes an operating system",
    }
    questions = {
        "overview": BUSINESS_QUESTION,
        "arena": "Which forecasting model should we trust?",
        "champion": "Which forecast should own each store-category?",
        "diagnostics": "Where should the forecast owner investigate next?",
        "labor": "We have 480 labor hours per day. How should those hours be d"
        "istributed across stores?",
        "scenario": "Which tested pressure exposes the largest capacity gap?",
        "governance": "What data and logic would make this decision better?",
    }
    copy = "<h2>" + html.escape(titles[key]) + "</h2>"
    if key == "overview":
        copy += (
            "<p>This project tests how a retail network could move from demand forecasting "
            "to an operating decision.</p>"
            + bullets(
                [
                    "Decision 1: Which forecasting model should own each store-category?",
                    "Decision 2: Given those forecasts and fixed labor capacity, "
                    "how should labor be allocated across stores?",
                ]
            )
            + "<p>Finally, the allocation is checked against retrospective actual demand "
            "to see whether the decision improved outcomes.</p>"
        )
    copy += (
        '<p class="decision-question"><b>QUESTION</b><br>' + html.escape(questions[key]) + "</p>"
    )
    if key == "overview":
        copy += (
            '<div class="decision-framework" aria-label="Decision framework">'
            + "".join(
                "<span>"
                + html.escape(label)
                + ('</span><b aria-hidden="true">↓</b>' if i < len(FRAMEWORK) - 1 else "</span>")
                for i, label in enumerate(FRAMEWORK)
            )
            + "</div>"
        )
        copy += '<p class="story-spine">' + " → ".join(SPINE) + "</p>"
    copy += "<h3>EVIDENCE</h3>"
    if key == "overview":
        copy += (
            "<p>Public M5 Walmart sales history: 10 stores in CA (California), TX (Texas) "
            "and WI (Wisconsin); FOODS and HOUSEHOLD; 20 daily demand series.</p>"
            "<p>What makes demand difficult enough that one forecast mode"
            "l may not work everywhere?</p>"
        )
    if key == "arena":
        copy += "<p>Four approaches, one common 28-day holdout:</p>" + bullets(
            [
                "Seasonal Naïve — baseline: demand from 28 days earlier.",
                "Holt-Winters — classical statistics: local trend and weekly seasonality.",
                "HGB — machine learning: nonlinear patterns in leakage-safe d"
                "emand and calendar inputs.",
                "MLP — neural network: a 128/64/32 challenger using the same safe inputs.",
            ]
        )
    if key == "arena":
        copy += (
            "<p><b>Read the evidence:</b> WAPE is absolute error divided by actual demand; "
            "lower is better. Negative bias means underforecast. A champion must have 28 valid "
            "nonnegative predictions, absolute bias within 10%, and deterministic validation; "
            "then lowest eligible WAPE wins. No qualifying model means review, "
            "not a relaxed rule.</p>"
        )
    if key == "champion":
        copy += (
            "<p>This map is the final output of Decision 01.</p><p>"
            + html.escape(
                " / ".join(f"{name}: {e.counts[name]}" for name in ("HGB", "MLP", "Holt-Winters"))
                + f" / Review required: {e.counts['No eligible champion']}"
            )
            + "</p>"
        )
        copy += "<p><strong>TX_3 / FOODS: No eligible champion—review required.</strong></p>"
    if key == "labor":
        settings = e.stages["operations"]["configuration"]["labor"]
        copy += (
            '<div class="constraint-strip">'
            + bullets(
                [
                    f"{settings['daily_network_hours']:g} total hours/day",
                    f"{settings['minimum_staffing'] * settings['shift_hours']:g} minimum/store-day",
                    f"{settings['maximum_staffing'] * settings['shift_hours']:g} maximum/store-day",
                    "Labor cannot be created.",
                ]
            )
            + "</div><p>Proportional baseline versus HiGHS optimized allocation.</p>"
        )
    return copy


def implication(key: str, e: Evidence) -> str:
    best = min(e.tables["network_scorecard"], key=lambda r: r["wape"])
    statements = {
        "overview": FORECAST_DECISION,
        "arena": f"{NAMES[best['model_name']]} leads the network at "
        f"{number(best['wape'], percent=True)} WAPE. "
        "It is the strongest single network-wide method, but store-category behavior is "
        "heterogeneous. A global model means one method used everywhere; a local champion "
        "is the best eligible method for one store-category. This is one governed framework "
        "making local model decisions, not 20 separate projects. No model is globally eligible "
        "across all 20 series. TX_3 / FOODS has no eligible champion and is routed to review "
        "rather than assigned a method that does not meet the governance standard.",
        "champion": "The best forecasting system is a governed portfolio of local champions. "
        "Selection is retrospective; confirm ownership on an untouched period.",
        "diagnostics": "Highest-priority review opportunities: WI_2 / FOODS, CA_1 / FOODS "
        "and TX_3 / FOODS; test"
        " changes on future data.",
        "labor": "The optimizer redistributes capacity, but the objective need"
        "s richer inputs. Check prototype validation next.",
        "scenario": "+15% demand creates the strongest tested pressure. Capacity "
        "remains fixed; shortages remain.",
        "governance": RECOMMENDATION,
    }
    return (
        '<div class="decision-answer"><h3>DECISION / IMPLICATION</h3><p>'
        + html.escape(statements[key])
        + "</p></div>"
    )


def diagnostic_actions(e: Evidence) -> str:
    copy = '<div class="overview-grid">'
    for r in sorted(e.tables["dri_exception_queue"], key=lambda r: r["priority_rank"])[:3]:
        copy += (
            "<article><h3>"
            + html.escape(r["store_id"] + " / " + r["category"])
            + "</h3>"
            + bullets(
                [
                    "Pattern: Repeated underforecast in this holdout.",
                    f"Evidence: {number(r.get('wape'), percent=True)} WAPE / "
                    f"{number(r['shortfall_units'])} unit shortfall / "
                    f"disagreement {number(r.get('disagreement'))}.",
                    "Risk: May understate required workload.",
                    "Next experiment: Audit inputs; test recalibration or store-category "
                    "interactions on an untouched window.",
                ]
            )
            + "</article>"
        )
    return copy + "</div>"


def impact(e: Evidence) -> str:
    p = e.row("scenario_summary", scenario="Base", allocation_method="proportional")
    o = e.row("scenario_summary", scenario="Base", allocation_method="optimized")
    ap = e.row("retrospective_summary", scenario="Base", allocation_method="proportional")
    ao = e.row("retrospective_summary", scenario="Base", allocation_method="optimized")
    return (
        "<h2>PROTOTYPE VALIDATION — DID THE OBJECTIVE CAPTURE THE RIGHT OUTCOME?</h2>"
        "<p>Constraint performance → allocation behavior → retrospective outcome "
        "→ next calibration step</p><p><b>QUESTION</b><br>Did the allocation respect "
        "constraints, redistribute capacity and improve actual coverage?</p>"
        "<h3>EVIDENCE</h3>"
        + "<p><b>YES — constraint performance:</b> fixed labor capacity, staffing bounds, "
        "nonnegative allocation and workload constraints were respected. Feasible optimized "
        "solutions are recorded for each scenario.</p>"
        + bullets(
            [
                "YES — capacity redistribution: Base configured critical store-days improved: "
                f"{p['critical_store_days']} → {o['critical_store_days']}.",
                "NOT YET — retrospective actual uncovered workload worsened: "
                f"{number(ap['actual_uncovered_hours'])} → "
                f"{number(ao['actual_uncovered_hours'])} hours.",
            ]
        )
        + "<h3>DECISION / IMPLICATION</h3><p><strong>"
        + IMPACT_CONCLUSION
        + "</strong></p>"
        "<p>All stores have equal priority weights. The optimizer redistributes shortages under "
        "its mathematical objective; it does not know which shortages matter more to the business. "
        "The optimizer is functioning as designed, but the current objective does not yet "
        "encode enough of the real operating decision. The business objective is under-specified; "
        "the evidence identifies the next calibration inputs.</p>"
        "<p>This is a conditional retrospective comparison, not a cau"
        "sal service-impact estimate.</p>"
        "<p><strong>" + RECOMMENDATION + "</strong></p>"
    )


def next_actions() -> str:
    return (
        "<h3>What data / logic is missing?</h3>"
        + bullets([title + ": " + detail for title, detail in NEXT_ACTIONS], ordered=True)
        + "<p>More model sophistication is not necessarily the next pri"
        "ority. Improve the operational "
        "objective, business-priority data and forecast drivers for weak series first.</p>"
    )


class CopyCounter(HTMLParser):
    """Count initially exposed prose across tabs, excluding charts/tables/disclosures/code."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[bool] = []
        self.words: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("meta", "link", "img", "br", "hr", "input", "source", "wbr"):
            return
        hidden = tag in ("script", "style", "details", "table", "svg", "noscript")
        self.stack.append(hidden or (self.stack[-1] if self.stack else False))

    def handle_endtag(self, tag: str) -> None:
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source", "wbr") and self.stack:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if not self.stack or not self.stack[-1]:
            self.words.extend(re.findall(r"\b[\w'-]+\b", data))


def copy_words(document: str) -> int:
    parser = CopyCounter()
    parser.feed(document.split("<script")[0])
    return len(parser.words)
