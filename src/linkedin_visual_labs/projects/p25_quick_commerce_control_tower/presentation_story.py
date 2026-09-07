"Shared narrative and storyboards assembled once from verified evidence."

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    LABOR_LIMIT,
    NAMES,
    RECOMMENDATIONS,
    Evidence,
    number,
)

VIDEO_TITLES = {
    "forecast_model_arena": ("Four Forecasting Methods Enter. Which One Should Run the Network?"),
    "forecast_to_labor_optimizer": "The Best Forecast Still Needs an Operating Decision",
}

SECTIONS = (
    "Executive Decision",
    "Model Arena",
    "Champion Model Map",
    "Why Forecasts Missed",
    "Labor Optimizer",
    "Scenario Lab",
    "Governance and Assumptions",
    "What I Would Do as the Forecast Accuracy DRI",
)
QUESTION = (
    "Which forecasts should own each store-category, why do they miss,"
    " and how should a constrained labor network respond?"
)
METHODS = (
    "Seasonal naïve: uses demand from exactly 28 days earlier.",
    ("Holt-Winters: captures local level/trend and recurring weekly seasonality."),
    (
        "HistGradientBoosting: learns nonlinear relationships across store"
        "s, categories, safe lagged demand, calendar events and SNAP."
    ),
    (
        "MLP: a feed-forward neural-network challenger with hidden layers "
        "128, 64, 32, using the same leakage-safe information contract."
    ),
)
METRICS = (
    "WAPE = total absolute forecast error / total actual demand; poole"
    "d at network level. MAE = mean absolute error in demand units per"
    " day. Bias = signed error / actual demand; negative means underfo"
    "recast. Completeness = valid unique expected predictions / 28. Di"
    "sagreement = mean per-date model forecast range / training-derive"
    "d demand scale, with model coverage recorded."
)


@dataclass(frozen=True)
class Scene:
    title: str
    caption: str
    items: tuple[tuple[str, str], ...]
    kind: str = "cards"
    seconds: int = 3
    role: str = "setup"
    actions: tuple[str, ...] = ()
    world: str = "forecast"


def assumption_lines(e: Evidence) -> tuple[str, ...]:
    c = e.stages["operations"]["configuration"]["labor"]
    p = c["productivity_units_per_hour"]
    return (
        f"FOODS {p['FOODS']:g}; HOUSEHOLD {p['HOUSEHOLD']:g} demand units/labor-hour.",
        "".join(
            (
                "Staffing: ",
                format(c["minimum_staffing"] * c["shift_hours"], "g"),
                "\u2013",
                format(c["maximum_staffing"] * c["shift_hours"], "g"),
                " hours/store-day (",
                format(c["shift_hours"], "g"),
                "-hour shift translation).",
            )
        ),
        f"Fixed network capacity: {c['daily_network_hours']:g} hours/day.",
        "".join(
            (
                "Labor cost: ",
                format(c["cost_per_hour"], "g"),
                " currency units/hour; uncovered penalty: ",
                format(c["uncovered_hour_penalty"], "g"),
                " \u00d7 priority per uncovered hour.",
            )
        ),
        "".join(
            (
                "All priorities = ",
                format(next(iter(c["store_priority_weights"].values())), "g"),
                "; critical store-day means uncovered >",
                format(c["critical_uncovered_hours"], "g"),
                " hours.",
            )
        ),
    )


def storyboards(e: Evidence) -> dict[str, tuple[Scene, ...]]:
    """Seven spatially continuous beats; results complete before the second hook."""
    labor = e.stages["operations"]["configuration"]["labor"]
    local = e.row("local_champion_portfolio", portfolio="local_champions")
    naive = e.row("local_champion_portfolio", portfolio="seasonal_naive_same_coverage")
    prop = e.row("scenario_summary", scenario="Base", allocation_method="proportional")
    opt = e.row("scenario_summary", scenario="Base", allocation_method="optimized")
    ap = e.row("retrospective_summary", scenario="Base", allocation_method="proportional")
    ao = e.row("retrospective_summary", scenario="Base", allocation_method="optimized")
    score = tuple(
        (NAMES[r["model_name"]], number(r["wape"], percent=True) + " WAPE")
        for r in sorted(e.tables["network_scorecard"], key=lambda r: r["wape"])
    )
    portfolio = number(local["wape"], percent=True) + " vs " + number(naive["wape"], percent=True)
    priorities = tuple(
        (r["store_id"] + " / " + r["category"], "Review evidence")
        for r in sorted(e.tables["dri_exception_queue"], key=lambda r: r["priority_rank"])[:3]
    )

    def scene(
        title: str,
        caption: str,
        kind: str,
        seconds: int,
        actions: tuple[str, ...],
        items: tuple[tuple[str, str], ...] = (),
        role: str = "setup",
        world: str = "forecast",
    ) -> Scene:
        return Scene(title, caption, items, kind, seconds, role, actions, world)

    return {
        "forecast_model_arena": (
            scene(
                "One forecast model for every store?",
                "One network contains different demand patterns.",
                "world",
                3,
                ("node_movement", "demand_pulses"),
            ),
            scene(
                "Four approaches. The SAME 28 days.",
                "20 series. Four approaches. Same 28-day holdout. No holdout leakage.",
                "contenders",
                4,
                ("algorithm_entry", "holdout_window"),
                (
                    ("Seasonal naïve", "Baseline"),
                    ("Holt-Winters", "Statistics"),
                    ("HGB", "Machine learning"),
                    ("MLP", "Neural network"),
                ),
            ),
            scene(
                f"{score[0][0]} leads: {score[0][1]}",
                "Strongest network score. Lines show a priority review opportunity.",
                "race",
                4,
                ("forecast_line_progression",),
                score,
                "primary_result",
            ),
            scene(
                "Different stores favor different approaches.",
                "No model qualified everywhere. RETROSPECTIVE selection is not future performance.",
                "assignment",
                4,
                ("counter_transition", "champion_assignment"),
                (*score, ("Retrospective matched WAPE", portfolio)),
                "primary_result",
            ),
            scene(
                "Which forecast should run each store?",
                "TX_3 / FOODS: no eligible champion. Governance routes this exception to review.",
                "review",
                8,
                ("portfolio_ownership", "warning_state"),
                role="second_hook",
            ),
            scene(
                "Where should the owner investigate next?",
                "WI_2 / FOODS. CA_1 / FOODS. TX_3 / FOODS. High-value improvement opportunities.",
                "chase",
                4,
                ("exception_chase", "error_pulses"),
                priorities,
            ),
            scene(
                "Use governed local champions.",
                "Review the exceptions. Improve the features. Re-test.",
                "loop",
                3,
                ("operating_loop",),
                role="final_answer",
            ),
        ),
        "forecast_to_labor_optimizer": (
            scene(
                f"{labor['daily_network_hours']:g} labor hours. Ten stores.",
                "Where should the hours go?",
                "world",
                3,
                ("node_movement", "demand_pulses", "fixed_pool"),
                (("Fixed daily capacity", f"{labor['daily_network_hours']:g} hours/day"),),
                world="labor",
            ),
            scene(
                "Demand becomes required labor.",
                "Illustrative productivity assumptions convert forecast units into workload hours.",
                "conversion",
                4,
                ("demand_conversion", "workload_growth"),
                world="labor",
            ),
            scene(
                "Proportional versus optimized allocation.",
                "Move the same hours between stores. Labor is reallocated, not created.",
                "comparison",
                4,
                ("labor_token_movement", "critical_state"),
                role="primary_result",
                world="labor",
            ),
            scene(
                "HiGHS moves the SAME labor hours.",
                (
                    "Configured critical days decrease; actual uncovered hours increase. "
                    "Same capacity, different allocation."
                ),
                "allocation_result",
                4,
                ("counter_transition", "impact_warning"),
                (
                    (
                        "Critical store-days",
                        f"{prop['critical_store_days']} → {opt['critical_store_days']}",
                    ),
                    (
                        "Actual uncovered hours",
                        f"{number(ap['actual_uncovered_hours'])} → "
                        f"{number(ao['actual_uncovered_hours'])}",
                    ),
                ),
                "primary_result",
                "labor",
            ),
            scene(
                "The allocation engine worked.",
                (
                    "Actual coverage worsened under equal priorities. "
                    "The objective needs richer business inputs."
                ),
                "impact",
                7,
                ("objective_flow", "shortage_redistribution"),
                role="second_hook",
                world="labor",
            ),
            scene(
                "What is missing from the decision?",
                (
                    "Service priorities, productivity, shift constraints, shortage costs "
                    "and inventory / replenishment."
                ),
                "missing_inputs",
                5,
                ("objective_inputs",),
                world="labor",
            ),
            scene(
                "Forecast better. Encode the business objective better.",
                "Then optimize. Validate on an untouched period before adoption.",
                "loop",
                3,
                ("operating_loop",),
                role="final_answer",
                world="labor",
            ),
        ),
    }


def section_briefs(e: Evidence) -> list[dict[str, Any]]:
    "Each major section explicitly answers question, view, finding and action."
    details = (
        (
            "Which forecasts should own decisions?",
            "Network comparison, local ownership and operating trade-offs.",
            e.executive,
            " ".join(RECOMMENDATIONS),
        ),
        (
            "Does complexity beat a transparent baseline?",
            "Four methods on the same 28-day holdout.",
            "HGB has the lowest pooled WAPE, but no globally eligible winner.",
            ("Select by complete forecasts, bias guardrails and WAPE, not sophistication."),
        ),
        (
            "Who owns each store-category?",
            "Ten stores \u00d7 two categories; model, errors and review states.",
            " ".join(f"{k}: {v}." for k, v in e.counts.items()),
            (
                "Escalate TX_3 / FOODS. Keep seasonal-naïve contingency separate f"
                "rom champion governance."
            ),
        ),
        (
            "Where should the forecast owner investigate first?",
            ("Ranked deterministic exception evidence and calendar associations."),
            (
                "WI_2 / FOODS, CA_1 / FOODS, then TX_3 / FOODS lead the queue. Loc"
                "al event samples are insufficient for causal attribution."
            ),
            (
                "Use the observed pattern → measured evidence → operational implic"
                "ation → recommended experiment sequence."
            ),
        ),
        (
            "How should a constrained network allocate labor?",
            "Proportional allocation versus HiGHS with identical assumptions.",
            LABOR_LIMIT,
            (
                "Calibrate the objective on untouched data; inspect both improved "
                "and worsened shortages."
            ),
        ),
        (
            "Which shock creates the greatest pressure?",
            "Base, +15% demand and -10% productivity under fixed capacity.",
            (
                "+15% demand has the highest required workload and uncovered hours"
                " among these tests."
            ),
            (
                "Test demand-response options and productivity recovery, subject t"
                "o an explicit capacity decision."
            ),
        ),
        (
            "What can this prototype legitimately claim?",
            "Data provenance, governance rules and illustrative inputs.",
            (
                "Forecast evidence is historical; selection is retrospective; labo"
                "r is illustrative; inventory is synthetic."
            ),
            "Require prospective validation before claiming production value.",
        ),
        (
            "How would a Forecast Accuracy DRI run the process?",
            "A proposed cross-functional monitoring and experiment loop.",
            (
                "TX_3 / FOODS needs governance escalation; WI_2 / FOODS needs diag"
                "nostic prioritization."
            ),
            (
                "Maintain champion/challenger models, publish review thresholds an"
                "d validate changes on untouched data."
            ),
        ),
    )
    return [
        dict(title=title, question=q, view=v, finding=f, action=a)
        for title, (q, v, f, a) in zip(SECTIONS, details, strict=True)
    ]
