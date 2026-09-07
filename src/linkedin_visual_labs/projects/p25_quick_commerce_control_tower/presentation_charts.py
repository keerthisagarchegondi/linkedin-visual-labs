"""Read-only display aggregations and offline chart specifications."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    NAMES,
    Evidence,
    records,
)

WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SCENARIOS = ["Base", "+15% demand", "-10% productivity"]


def display_tables(
    demand: pd.DataFrame, predictions: pd.DataFrame, exceptions: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """Derive presentation-only data; no model fit, selection, or persisted analytics."""
    daily = demand.groupby("date", as_index=False)[["demand"]].sum()
    daily["date"] = daily.date.dt.strftime("%Y-%m-%d")
    result = {"demand_history": records(daily)}
    for name, key in [
        ("state_demand", "state_id"),
        ("category_demand", "category"),
        ("store_demand", "store_id"),
    ]:
        result[name] = records(
            demand.groupby(key, as_index=False)[["demand"]]
            .sum()
            .sort_values(["demand", key], ascending=[False, True])
        )
    network = demand.groupby(["date", "weekday"], as_index=False)[["demand"]].sum()
    result["weekday_demand"] = records(
        network.groupby("weekday", as_index=False)[["demand"]].mean()
    )
    context = demand.assign(event=(demand.event_name_1.ne("") | demand.event_name_2.ne("")))
    result["calendar_context"] = [
        {"signal": label, "series_days": int(mask.sum())}
        for label, mask in [
            ("Event", context.event),
            ("Ordinary", ~context.event),
            ("SNAP active", context.snap.eq(1)),
            ("SNAP inactive", context.snap.eq(0)),
        ]
    ]
    selected = min(exceptions, key=lambda r: (r["priority_rank"], r["store_id"], r["category"]))
    sample = predictions.loc[
        predictions.store_id.eq(selected["store_id"])
        & predictions.category.eq(selected["category"])
    ].copy()
    sample["date"] = sample.date.dt.strftime("%Y-%m-%d")
    result["forecast_example"] = records(sample.sort_values(["model_name", "date"]))
    return result


def chart_specs(e: Evidence) -> dict[str, dict[str, Any]]:
    """Every chart carries source names, units and an interpretation."""
    charts: dict[str, dict[str, Any]] = {}

    def add(
        key: str,
        panel: str,
        title: str,
        unit: str,
        meaning: str,
        traces: list[dict[str, Any]],
        source: str,
        **layout: Any,
    ) -> None:
        charts[key] = dict(
            panel=panel,
            title=title,
            unit=unit,
            meaning=meaning,
            source=source,
            data=traces,
            layout={
                "yaxis": {"title": {"text": unit}, "automargin": True},
                "xaxis": {"automargin": True},
                "margin": {"t": 25, "b": 95, "l": 80, "r": 25},
                "font": {"family": "Arial, sans-serif", "size": 14},
                "colorway": ["#008b8d", "#bd6509", "#7254c7", "#62748d", "#b53843"],
                "legend": {"orientation": "h", "y": -0.28},
                "barmode": "group",
                **layout,
            },
        )

    def bars(
        rows: list[dict[str, Any]], x: str, y: str, name: str = "", scale: float = 1
    ) -> dict[str, Any]:
        return dict(
            type="bar",
            x=[r[x] for r in rows],
            y=[r[y] * scale if r[y] is not None else None for r in rows],
            name=name,
        )

    v = e.visuals
    if v:
        add(
            "demand_history",
            "overview",
            "Meet the network: daily demand across 20 streams",
            "Demand units / day",
            "Seasonality and changing demand scale require testing forecasts, "
            "not assuming one model fits everywhere.",
            [
                dict(
                    type="scatter",
                    mode="lines",
                    x=[r["date"] for r in v["demand_history"]],
                    y=[r["demand"] for r in v["demand_history"]],
                    name="Network demand",
                )
            ],
            "demand_daily.parquet",
            shapes=[
                dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0="2016-04-25",
                    x1="2016-05-22",
                    y0=0,
                    y1=1,
                    fillcolor="#bd6509",
                    opacity=0.2,
                    line={"width": 0},
                )
            ],
            annotations=[
                dict(x="2016-05-22", y=1, yref="paper", text="28-day holdout", showarrow=True)
            ],
        )
        for key, column, title in [
            ("state_demand", "state_id", "California (CA), Texas (TX), Wisconsin (WI)"),
            ("category_demand", "category", "Two categories contribute different demand volumes"),
            ("store_demand", "store_id", "Ten stores ranked by measured demand"),
        ]:
            add(
                key,
                "overview",
                title,
                "Demand units · full observed history",
                (
                    "Volume differs across the selected network; comparisons desc"
                    "ribe this M5 scope only."
                ),
                [bars(v[key], column, "demand")],
                "demand_daily.parquet",
                showlegend=False,
            )
        weekday = sorted(v["weekday_demand"], key=lambda r: WEEK.index(r["weekday"]))
        add(
            "weekday_demand",
            "overview",
            "A recurring weekly rhythm in network demand",
            "Mean network demand units / day",
            "Weekly demand patterns justify comparing seasonal baselines "
            "with flexible challengers.",
            [bars(weekday, "weekday", "demand")],
            "demand_daily.parquet",
            showlegend=False,
        )
        add(
            "calendar_context",
            "overview",
            "Available calendar signals: events and SNAP",
            "Store-category days · full history",
            (
                "These are overlapping calendar groupings, not evidence that "
                "events or SNAP caused demand."
            ),
            [bars(v["calendar_context"], "signal", "series_days")],
            "demand_daily.parquet",
            showlegend=False,
        )
        sample = v["forecast_example"]
        if sample:
            first = sample[0]
            traces = []
            for model, name in [("actual", "Actual"), *NAMES.items()]:
                rows = [
                    r
                    for r in sample
                    if r["model_name"] == (first["model_name"] if model == "actual" else model)
                ]
                traces.append(
                    dict(
                        type="scatter",
                        mode="lines",
                        name=name,
                        x=[r["date"] for r in rows],
                        y=[
                            r["actual_units" if model == "actual" else "forecast_units"]
                            for r in rows
                        ],
                    )
                )
            add(
                "forecast_example",
                "arena",
                f"{first['store_id']} / {first['category']}: actual versus four forecasts",
                "Demand units / day",
                (
                    "Selected deterministically as the highest-priority exception"
                    ", not for visual drama."
                ),
                traces,
                "predictions.parquet + dri_exception_queue.csv",
            )
    scores = [
        {**r, "model": NAMES[r["model_name"]]}
        for r in sorted(e.tables["network_scorecard"], key=lambda r: r["wape"])
    ]
    for key, title in [
        ("wape", "HGB has the lowest network WAPE"),
        ("bias", "All four methods underforecast overall"),
    ]:
        add(
            "model_" + key,
            "arena",
            title,
            key.upper() + " (%)",
            (
                "Lower WAPE is better; negative signed bias means underforeca"
                "st. Eligibility is checked locally."
            ),
            [bars(scores, "model", key, scale=100)],
            "network_scorecard.csv",
            showlegend=False,
        )
    add(
        "wape_bias",
        "arena",
        "Accuracy and directional error are different questions",
        "Signed bias (%)",
        "The lowest network error does not imply eligibility in every store-category.",
        [
            dict(
                type="scatter",
                mode="markers+text",
                x=[r["wape"] * 100 for r in scores],
                y=[r["bias"] * 100 for r in scores],
                text=[r["model"] for r in scores],
                textposition="top center",
                marker={"size": 12},
            )
        ],
        "network_scorecard.csv",
        xaxis={"title": {"text": "WAPE (%)"}, "automargin": True},
        showlegend=False,
    )
    add(
        "champion_counts",
        "champion",
        "Local ownership: one review remains unassigned",
        "Store-category series",
        "Different local winners justify a governed portfolio; seasonal naïve has zero champions.",
        [dict(type="bar", x=list(e.counts), y=list(e.counts.values()))],
        "champions.csv",
        showlegend=False,
    )
    queue = sorted(e.tables["dri_exception_queue"], key=lambda r: r["priority_rank"])
    add(
        "exception_rankings",
        "diagnostics",
        "Investigate the highest-priority exceptions first",
        "Fixed weighted priority score",
        "WI_2 / FOODS, CA_1 / FOODS and TX_3 / FOODS lead the deterministic review queue.",
        [
            dict(
                type="bar",
                x=[r["store_id"] + "/" + r["category"] for r in queue],
                y=[r.get("priority_score") for r in queue],
                marker={"color": ["#b53843" if i < 3 else "#62748d" for i in range(len(queue))]},
            )
        ],
        "dri_exception_queue.csv",
        showlegend=False,
    )
    add(
        "under_over",
        "diagnostics",
        "Shortfalls and excesses do not cancel operationally",
        "Demand units · holdout",
        (
            "Underforecast demand can create planning pressure even when "
            "excess forecasts occur on other days."
        ),
        [
            bars(scores, "model", key, name=label)
            for key, label in [
                ("shortfall_units", "Underforecast shortfall"),
                ("excess_units", "Overforecast excess"),
            ]
        ]
        if all("shortfall_units" in r for r in scores)
        else [],
        "network_scorecard.csv",
    )
    add(
        "weekday_wape",
        "diagnostics",
        "Sunday has the highest WAPE for every model",
        "WAPE (%)",
        (
            "Test weekday-specific calibration on a future untouched wind"
            "ow; this is a descriptive holdout pattern."
        ),
        [
            bars(
                sorted(
                    [r for r in e.tables["day_of_week_analysis"] if r["model_name"] == m],
                    key=lambda r: WEEK.index(r["dimension"]),
                ),
                "dimension",
                "wape",
                name=n,
                scale=100,
            )
            for m, n in NAMES.items()
        ],
        "day_of_week_analysis.csv",
    )
    for key, title, meaning in [
        (
            "event_analysis",
            "HGB event versus ordinary days",
            "Descriptive association only: subgroup counts and calendar composition differ.",
        ),
        (
            "snap_analysis",
            "HGB SNAP groups have almost identical WAPE",
            "The small descriptive difference is not a causal effect.",
        ),
    ]:
        add(
            key,
            "diagnostics",
            title,
            "WAPE (%)",
            meaning,
            [
                bars(
                    [r for r in e.tables[key] if r["model_name"] == "hist_gradient_boosting"],
                    "dimension",
                    "wape",
                    scale=100,
                )
            ],
            key + ".csv",
            showlegend=False,
        )
    disagree = sorted(e.tables["champions"], key=lambda r: r["disagreement"], reverse=True)
    add(
        "disagreement",
        "diagnostics",
        "Highest disagreement remains below the review threshold",
        "Mean normalized model range",
        (
            "WI_2 / FOODS is highest at 0.4533, below 0.50; disagreement "
            "does not trigger a review flag."
        ),
        [
            dict(
                type="bar",
                x=[r["store_id"] + "/" + r["category"] for r in disagree],
                y=[r["disagreement"] for r in disagree],
            )
        ],
        "champions.csv",
        showlegend=False,
        shapes=[
            dict(
                type="line",
                xref="paper",
                x0=0,
                x1=1,
                y0=disagree[0]["review_threshold"],
                y1=disagree[0]["review_threshold"],
                line={"color": "#b53843", "dash": "dash"},
            )
        ],
    )
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
        allocation_example,
    )

    date, pairs = allocation_example(e)
    add(
        "allocation",
        "labor",
        f"Fixed-capacity allocation by store · {date}",
        "Labor-hours",
        "First Base day with nonzero redistribution; both plans use identical total hours.",
        [
            dict(type="bar", name=n, x=[r[0] for r in pairs], y=[r[i] for r in pairs])
            for i, n in [(1, "Proportional"), (2, "Optimized")]
        ],
        "labor_allocations.csv",
    )
    add(
        "reallocation",
        "labor",
        f"Who gains and loses hours · {date}",
        "Optimized minus proportional hours",
        "Gains are funded by losses elsewhere; optimization reallocates rather than creates labor.",
        [
            dict(
                type="bar",
                x=[r[0] for r in pairs],
                y=[r[2] - r[1] for r in pairs],
                marker={"color": ["#008b8d" if r[2] >= r[1] else "#bd6509" for r in pairs]},
            )
        ],
        "labor_allocations.csv",
        showlegend=False,
    )
    for key, source, field, title, unit, meaning in [
        (
            "critical",
            "scenario_summary",
            "critical_store_days",
            "Fewer critical store-days under the configured objective",
            "Critical store-days",
            (
                "Critical means more than eight uncovered hours; this improve"
                "s while total actual coverage worsens."
            ),
        ),
        (
            "actual_uncovered",
            "retrospective_summary",
            "actual_uncovered_hours",
            "Prototype validation: actual uncovered workload increases in every scenario",
            "Actual uncovered labor-hours",
            (
                "Constraint mechanics work; equal priorities leave the objective incomplete. "
                "Actual coverage worsens, identifying a need for richer business inputs."
            ),
        ),
    ]:
        add(
            key,
            "labor",
            title,
            unit,
            meaning,
            [
                bars(
                    [e.row(source, scenario=s, allocation_method=m) for s in SCENARIOS],
                    "scenario",
                    field,
                    name=m,
                )
                for m in ["proportional", "optimized"]
            ],
            source + ".csv",
        )
    for field, title, unit in [
        ("required_hours", "Required workload", "Labor-hours"),
        ("allocated_hours", "Used capacity", "Labor-hours"),
        ("unused_capacity", "Unused capacity", "Labor-hours"),
        ("uncovered_hours", "Uncovered workload", "Labor-hours"),
        ("critical_store_days", "Critical store-days", "Store-days"),
    ]:
        add(
            "scenario_" + field,
            "scenario",
            title + " across the three scenarios",
            unit,
            (
                "+15% demand creates the strongest tested pressure; capacity "
                "remains fixed and assumptions are illustrative."
            ),
            [
                bars(
                    [e.row("scenario_summary", scenario=s, allocation_method=m) for s in SCENARIOS],
                    "scenario",
                    field,
                    name=m,
                )
                for m in ["proportional", "optimized"]
            ],
            "scenario_summary.csv",
        )
    counts = Counter(r["risk_status"] for r in e.tables["inventory_proxy"])
    add(
        "inventory",
        "scenario",
        "Synthetic illustrative inventory proxy",
        "Store-category days",
        (
            "Synthetic stock assumptions illustrate triage; these are not"
            " observed inventory risks or probabilities."
        ),
        [dict(type="bar", x=list(counts), y=list(counts.values()))],
        "inventory_proxy.csv",
        showlegend=False,
    )
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_modeling,
    )

    importance = presentation_modeling.importance_rows(e)[:8]
    add(
        "hgb_importance",
        "arena",
        "Which signals mattered most? · Retrospective model interpretation",
        "Mean MAE increase when shuffled (daily demand units)",
        f"{importance[0]['feature']} ranks first in this bounded training sample. "
        "Bar heights compare predictive contribution in the fitted model, not causality. "
        "Last 256 training feature rows, three permutations per raw input; error bars are "
        "permutation standard deviations, not confidence intervals. Correlated lags can share "
        "signal. No grouping or normalization; not held-out importance or a tuning input.",
        [
            dict(
                type="bar",
                x=[r["feature"] for r in importance],
                y=[r["mean_mae_increase"] for r in importance],
                error_y=dict(type="data", array=[r["std_mae_increase"] for r in importance]),
            )
        ],
        "hist_gradient_boosting_importance.parquet",
        showlegend=False,
    )
    return charts
