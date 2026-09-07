"Offline HTML report; embedded charts and canonical evidence, no web server."

from __future__ import annotations

import base64
import html
import json
import re
from collections import Counter
from typing import Any

from plotly.offline import get_plotlyjs  # type: ignore[import-untyped]

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    INVENTORY_LABEL,
    LABOR_LIMIT,
    NAMES,
    NO_IMPACT,
    RECOMMENDATIONS,
    RETROSPECTIVE,
    Evidence,
    number,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    METHODS,
    METRICS,
    QUESTION,
    assumption_lines,
    section_briefs,
)


def table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    def cell(value: Any) -> str:
        if isinstance(value, float):
            return number(value)
        return html.escape("undefined" if value is None else str(value))

    return (
        '<div class="scroll"><table><thead><tr>'
        + "".join("<th>" + html.escape(label) + "</th>" for _, label in columns)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join("<td>" + cell(row[key]) + "</td>" for key, _ in columns) + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )


def paragraphs(lines: tuple[str, ...] | list[str]) -> str:
    return "".join("<p>" + html.escape(line) + "</p>" for line in lines)


def _analytical_html(e: Evidence, png: bytes) -> str:
    briefs = section_briefs(e)
    network = [
        dict(
            r,
            model=NAMES[r["model_name"]],
            local_champions=e.counts[NAMES[r["model_name"]]],
            wape_display=number(r["wape"], percent=True),
            bias_display=number(r["bias"], percent=True),
            completeness_display=number(r["completeness"], percent=True),
        )
        for r in sorted(e.tables["network_scorecard"], key=lambda r: r["wape"])
    ]
    sections: list[str] = []
    for i, b in enumerate(briefs):
        body = (
            '<div class="brief">'
            + "".join(
                f"<div><b>{label}</b><p>{html.escape(b[key])}</p></div>"
                for key, label in [
                    ("question", "Business question"),
                    ("view", "What you are looking at"),
                    ("finding", "Measured finding"),
                    ("action", "Operating decision"),
                ]
            )
            + "</div>"
        )
        if i == 0:
            body += table(
                [{"model": name, "count": count} for name, count in e.counts.items()],
                [("model", "Local ownership"), ("count", "Champions / unassigned")],
            )
            body += (
                '<div class="hero-metric">'
                + html.escape(e.portfolio)
                + '</div><p class="warning">'
                + RETROSPECTIVE
                + "</p>"
            )
            body += (
                '<div class="recommendations">'
                + "".join(
                    "".join(
                        (
                            "<article><small>RECOMMENDATION ",
                            format(j + 1, ""),
                            "</small><h3>",
                            format(html.escape(r), ""),
                            "</h3></article>",
                        )
                    )
                    for j, r in enumerate(RECOMMENDATIONS)
                )
                + "</div>"
            )
        elif i == 1:
            body += (
                '<div class="cards">'
                + "".join("<article>" + html.escape(m) + "</article>" for m in METHODS)
                + "</div>"
            )
            body += paragraphs(
                (
                    (
                        "All four methods forecast the identical 28-day holdout. Forecasts"
                        " were generated without holdout actual leakage. Direct-horizon fe"
                        "atures use lag 28 or older, safe rolling endpoints and training-o"
                        "nly preprocessing. Calendar and SNAP schedules are assumed known "
                        "at issuance."
                    ),
                    METRICS,
                    (
                        "Eligibility: complete finite nonnegative forecasts, absolute bias"
                        " within 10%, deterministic validation; then lowest WAPE. No autom"
                        "atic guardrail relaxation."
                    ),
                )
            )
            body += table(
                network,
                [
                    ("model", "Model"),
                    ("wape_display", "WAPE"),
                    ("mae", "MAE units/day"),
                    ("bias_display", "Bias"),
                    ("completeness_display", "Completeness"),
                    ("globally_eligible", "Globally eligible"),
                    ("local_champions", "Local champions"),
                ],
            ) + (
                '<div id="network-chart" class="chart" aria-label="Network WAPE comparison"></div>'
            )
        elif i == 2:
            body += (
                (
                    '<img class="champion-map" alt="Retrospective champion map: 20 cel'
                    'ls; TX_3 FOODS has no eligible champion" src="data:image/png;base'
                    "64,"
                )
                + base64.b64encode(png).decode("ascii")
                + '">'
            )
            body += paragraphs(
                (
                    (
                        "Each cell reports WAPE, signed bias, WAPE percentage-point improv"
                        "ement versus seasonal naïve and disagreement. Undefined champion "
                        "metrics remain undefined. No disagreement review flags crossed 0."
                        "50."
                    ),
                    (
                        "TX_3 / FOODS: No eligible champion—review required. Seasonal naïv"
                        "e is a contingency forecast for planning, never an eligible champ"
                        "ion."
                    ),
                )
            )
        elif i == 3:
            for r in sorted(e.tables["dri_exception_queue"], key=lambda r: r["priority_rank"])[:3]:
                body += (
                    "".join(
                        (
                            "<article><h3>",
                            format(html.escape(r["store_id"] + " / " + r["category"]), ""),
                            " · priority ",
                            format(r["priority_rank"], ""),
                            "</h3>",
                        )
                    )
                    + "".join(
                        f"<p><b>{label}:</b> {html.escape(r[key])}</p>"
                        for key, label in [
                            ("observed_pattern", "Observed pattern"),
                            ("evidence", "Measured evidence"),
                            ("operational_implication", "Operational implication"),
                            ("recommended_experiment", "Recommended experiment"),
                        ]
                    )
                    + "</article>"
                )
            for tab, desc in [
                ("event_analysis", "Event / ordinary"),
                ("snap_analysis", "SNAP active / inactive"),
            ]:
                row = e.row(
                    tab,
                    model_name="hist_gradient_boosting",
                    dimension="event" if tab == "event_analysis" else "active",
                )
                body += "".join(
                    (
                        "<p><b>HGB ",
                        format(desc, ""),
                        " WAPE:</b> ",
                        format(number(row["wape"], percent=True), ""),
                        " / ",
                        format(number(row["comparison_wape"], percent=True), ""),
                        "; n=",
                        format(row["observations"], ""),
                        " / ",
                        format(row["comparison_observations"], ""),
                        " store-category-days.</p>",
                    )
                )
            worst = [
                max(
                    [r for r in e.tables["day_of_week_analysis"] if r["model_name"] == m],
                    key=lambda r: r["wape"],
                )
                for m in NAMES
            ]
            body += table(
                [
                    dict(
                        r,
                        model=NAMES[r["model_name"]],
                        local_champions=e.counts[NAMES[r["model_name"]]],
                        wape_display=number(r["wape"], percent=True),
                    )
                    for r in worst
                ],
                [
                    ("model", "Model"),
                    ("dimension", "Worst weekday"),
                    ("wape_display", "WAPE"),
                    ("observations", "Observations"),
                ],
            )
            high = max(e.tables["champions"], key=lambda r: r["disagreement"])
            body += paragraphs(
                (
                    "".join(
                        (
                            "Highest disagreement: ",
                            format(high["store_id"], ""),
                            " / ",
                            format(high["category"], ""),
                            " = ",
                            format(high["disagreement"], ".4f"),
                            ", below review threshold ",
                            format(high["review_threshold"], ".2f"),
                            ". No flags triggered.",
                        )
                    ),
                    (
                        "Association is not causation. Event, SNAP and weekday comparisons"
                        " do not establish causes. Local event samples are insufficient fo"
                        "r causal attribution."
                    ),
                )
            )
        elif i == 4:
            body += paragraphs(assumption_lines(e))
            body += paragraphs(
                (
                    (
                        "Inputs: champion/contingency forecasts divided by illustrative ca"
                        "tegory productivity; aggregate to store-day. Actual holdout deman"
                        "d never enters allocation decisions."
                    ),
                    (
                        "Proportional: minima first; distribute remaining hours by unmet w"
                        "orkload, cap at store maxima and redistribute saturation. HiGHS L"
                        "P: minimize Σ(cost \u00d7 h + penalty "
                        "\u00d7 priority \u00d7 u), subject to min "
                        "≤ h ≤ max, Σh ≤ 480 per day, u ≥ required \u2212 h and u ≥ 0."
                    ),
                    (
                        "The optimizer reallocates fixed capacity; it never creates labor "
                        "or productivity and does not reduce physical workload. Equal prio"
                        "rities produce equal aggregate configured objective totals within"
                        " numerical tolerance. The demonstrated behavior is constraint-awa"
                        "re redistribution, not proven service improvement."
                    ),
                )
            )
            body += table(
                e.tables["tradeoff_summary"],
                [
                    ("scenario", "Scenario"),
                    ("gained_hours_stores", "Stores gaining"),
                    ("lost_hours_stores", "Stores losing"),
                    ("shortage_improved_store_days", "Days improved"),
                    ("shortage_worsened_store_days", "Days worsened"),
                    ("shortage_unchanged_store_days", "Days unchanged"),
                ],
            )
            body += (
                "<p>Distinct-store gain/loss sets can overlap across dates.</p><h3"
                ">Retrospective actual coverage worsened overall</h3>"
            )
            body += table(
                e.tables["retrospective_summary"],
                [
                    ("scenario", "Scenario"),
                    ("allocation_method", "Method"),
                    ("actual_required_hours", "Actual workload h"),
                    ("actual_uncovered_hours", "Actual uncovered h"),
                    ("actual_critical_store_days", "Actual critical days"),
                ],
            )
            body += (
                '<p class="warning">'
                + LABOR_LIMIT
                + (
                    " The formulation requires governance and calibration on future un"
                    'touched data.</p><div id="actual-chart" class="chart" aria-label='
                    '"Retrospective actual uncovered workload"></div>'
                )
            )
        elif i == 5:
            body += table(
                e.tables["scenario_summary"],
                [
                    ("scenario", "Scenario"),
                    ("allocation_method", "Method"),
                    ("required_hours", "Required h"),
                    ("total_capacity", "Available h"),
                    ("allocated_hours", "Used h"),
                    ("unused_capacity", "Unused h"),
                    ("uncovered_hours", "Uncovered h"),
                    ("weighted_uncovered_hours", "Weighted h"),
                    ("labor_cost", "Cost"),
                    ("objective", "Objective"),
                    ("critical_store_days", "Critical days"),
                    ("constrained_stores", "Constrained stores"),
                    ("stores_at_minimum", "At minimum"),
                    ("stores_at_maximum", "At maximum"),
                    ("feasibility", "Feasibility"),
                ],
            )
            body += paragraphs(
                (
                    (
                        "Base: review the distribution of gaps before using the prototype "
                        "for staffing. +15% demand: test demand-response options and expli"
                        "cit capacity alternatives outside this fixed-capacity experiment."
                        " -10% productivity: investigate workflow bottlenecks and test pro"
                        "ductivity recovery. These are recommendations, not measured benef"
                        "its."
                    ),
                    (
                        "-10% productivity scales workload by 1 / 0.90, not merely 10%. Th"
                        "e daily cap stays fixed at 480 hours; unused hours on one date ca"
                        "nnot cover another date. Retrospective actual demand is unchanged"
                        " by the +15% forecast shock."
                    ),
                )
            )
            counts = Counter(r["risk_status"] for r in e.tables["inventory_proxy"])
            body += (
                "<h3>"
                + INVENTORY_LABEL
                + "</h3>"
                + table(
                    [
                        {"risk": k, "count": counts[k]}
                        for k in ("Healthy", "Monitor", "Reorder", "Expedite")
                    ],
                    [("risk", "Synthetic status"), ("count", "Snapshots")],
                )
            )
            body += paragraphs(
                (
                    (
                        "Seed 47. Synthetic on-hand = floor(mean forecast \u00d7 Uniform[0,7));"
                        " days of cover = synthetic on-hand / mean forecast over up to sev"
                        "en days. Independent snapshots, not a depletion trajectory. Exped"
                        "ite <1 day; Reorder [1,2); Monitor [2,4); Healthy ≥4."
                    ),
                    (
                        "Zero forecast: zero synthetic stock, undefined cover, Healthy onl"
                        "y as a disclosed no-demand convention. Very low positive demand u"
                        "ses exact arithmetic; missing input is rejected."
                    ),
                    (
                        "Synthetic illustrative inventory proxy. Not measured M5 inventory"
                        ", not stockout probability, not replenishment optimization; no le"
                        "ad-time, supplier, purchase-order or DoorDash inventory data."
                    ),
                )
            )
        elif i == 6:
            body += table(
                [
                    {"class": k, "meaning": v}
                    for k, v in [
                        ("PUBLIC REAL DATA", "M5 historical retail demand"),
                        ("MEASURED", "Historical common-holdout model backtest"),
                        ("RETROSPECTIVE", "Local champion selection and portfolio performance"),
                        (
                            "ILLUSTRATIVE",
                            (
                                "Productivity, labor costs, staffing limits, capacity, penalties a"
                                "nd priorities"
                            ),
                        ),
                        ("SYNTHETIC", "On-hand inventory"),
                        ("PROTOTYPE", "Labor optimization"),
                    ]
                ],
                [("class", "Classification"), ("meaning", "Meaning")],
            )
            body += paragraphs(
                (
                    RETROSPECTIVE,
                    NO_IMPACT,
                    (
                        "No production-service claim. No DoorDash impact measurement. Actu"
                        "al coverage worsening and equal objective totals must remain visi"
                        "ble. Labor priorities, productivity and inventory thresholds were"
                        " not tuned to improve the visual story."
                    ),
                )
            )
            d = e.stages["demand_daily"]
            body += "".join(
                (
                    "<p>Source: public M5 retail demand, Zenodo record ",
                    format(d["record_id"], ""),
                    ". Training ",
                    format(d["training_start"], ""),
                    " through ",
                    format(d["training_end"], ""),
                    "; holdout ",
                    format(d["holdout_start"], ""),
                    " through ",
                    format(d["holdout_end"], ""),
                    ".</p>",
                )
            )
            body += table(
                d["source_files"],
                [("filename", "Source file"), ("sha256", "SHA-256"), ("url", "Source URL")],
            )
        else:
            body += paragraphs(
                (
                    (
                        "Maintain champion/challenger models by store-category. Monitor WA"
                        "PE, bias, completeness, clipping and disagreement; rank recurring"
                        " variance drivers and convert evidence into experiments."
                    ),
                    (
                        "Proposed operating policy, not an implemented production service:"
                        " review each completed 28-day window. Retraining review: incumben"
                        "t WAPE worse than the matched seasonal-naïve baseline on that unt"
                        "ouched window. Recalibration review: absolute bias exceeds the ex"
                        "isting 10% guardrail. These triggers request investigation, never"
                        " automatic promotion."
                    ),
                    (
                        "Escalate no-eligible-champion states or incomplete/invalid foreca"
                        "sts immediately; review disagreement above the existing 0.50 thre"
                        "shold and operational shortfall above the configured 8-hour criti"
                        "cal threshold. TX_3 / FOODS illustrates governance escalation; WI"
                        "_2 / FOODS illustrates diagnostic prioritization."
                    ),
                    (
                        "Maintain and publish retraining, recalibration and escalation thr"
                        "esholds with versioned configuration before future evaluation. Va"
                        "lidate optimization-objective changes on untouched data; do not c"
                        "alibrate priorities against this displayed holdout."
                    ),
                    (
                        "Operations owns capacity and service assumptions; Product owns de"
                        "cision usefulness; Engineering owns reliable data and execution; "
                        "Data Science owns leakage-safe evaluation, diagnostics and challe"
                        "nger experiments. Coordinate all four disciplines."
                    ),
                )
            )
        sections.append(
            "".join(
                (
                    '<section id="section-',
                    format(i + 1, ""),
                    '"><small>DECISION ',
                    format(i + 1, "02d"),
                    "</small><h2>",
                    format(html.escape(b["title"]), ""),
                    "</h2>",
                    format(body, ""),
                    "</section>",
                )
            )
        )
    safe_evidence = json.dumps(e.tables, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")
    chart_data = json.dumps(
        [{"name": NAMES[r["model_name"]], "wape": r["wape"] * 100} for r in network]
    )
    return (
        (
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width,initial-scale=1"><tit'
            "le>Project 5 | Quick-Commerce Control Tower</title><style>\n*{box-"
            "sizing:border-box}body{margin:0;background:#f4f7fb;color:#142e49;"
            "font:17px/1.65 system-ui,sans-serif}main{max-width:1240px;margin:"
            "auto;padding:36px}header{background:#142e49;color:white;padding:4"
            "8px;border-radius:24px}h1{font-size:44px;line-height:1.15;max-wid"
            "th:1000px}h2{font-size:32px;line-height:1.25}h3{font-size:21px}sm"
            "all{font-weight:750;letter-spacing:.12em;color:#087e8b}header sma"
            "ll{color:#7cdde1}nav{display:flex;flex-wrap:wrap;gap:12px;padding"
            ":24px 0}a{color:#145bc3}nav a{font-size:14px;padding:6px 12px;bac"
            "kground:white;border-radius:20px}section{margin:30px 0;padding:32"
            "px;background:white;border:1px solid #dce4ef;border-radius:20px}p"
            "{overflow-wrap:anywhere}.brief,.cards,.recommendations{display:gr"
            "id;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.brief>"
            "div,article{background:#f4f7fb;padding:20px;border-radius:12px;ma"
            "rgin:12px 0}.brief b{color:#087e8b}.recommendations{grid-template"
            "-columns:repeat(3,minmax(0,1fr))}.hero-metric{font-size:29px;font"
            "-weight:750;margin-top:24px}.warning{border-left:5px solid #b5384"
            "3;background:#fff2ef;padding:20px}.scroll{overflow:auto;margin:24"
            "px 0}table{border-collapse:collapse;width:100%;font-size:15px}th,"
            "td{padding:12px;text-align:left;border-bottom:1px solid #dce4ef;w"
            "hite-space:nowrap}th{background:#eaf0f7}.champion-map{width:100%;"
            "max-width:900px;display:block;margin:auto}.chart{height:390px;wid"
            "th:100%}footer{padding:30px;font-size:14px}@media(max-width:760px"
            "){main{padding:12px}header,section{padding:22px}h1{font-size:32px"
            "}.brief,.cards,.recommendations{grid-template-columns:1fr}}\n</sty"
            "le></head><body><main><header><small>PROJECT 5 / FORECAST ACCURAC"
            "Y OWNERSHIP</small><h1>Quick-Commerce Control Tower</h1><h2>"
        )
        + html.escape(QUESTION)
        + (
            "</h2><p>Public M5 retail demand · 10 stores · FOODS + HOUSEHOLD ·"
            " 20 store-category series</p><p>Common 28-day holdout: 2016-04-25"
            " through 2016-05-22</p><p>Forecast → Select → Diagnose → Allocate"
            " → Stress-test</p><p>Real public demand history and measured hist"
            "orical backtest results are combined with illustrative labor assu"
            "mptions and synthetic inventory inputs.</p><p>"
        )
        + NO_IMPACT
        + "</p></header><nav>"
        + "".join(
            f'<a href="#section-{i + 1}">{html.escape(b["title"])}</a>'
            for i, b in enumerate(briefs)
        )
        + "</nav>"
        + "".join(sections)
        + (
            "<footer>Canonical evidence is embedded below. All figures use ver"
            "ified Step 4/5 artifacts; source hashes and media validation are "
            "recorded in run_manifest.json. "
        )
        + NO_IMPACT
        + ('</footer></main><script type="application/json" id="canonical-evidence">')
        + safe_evidence
        + "</script><script>"
        + str(get_plotlyjs())
        + """</script><script>
const n="""
        + chart_data
        + (
            ";Plotly.newPlot('network-chart',[{x:n.map(r=>r.name),y:n.map(r=>r"
            ".wape),type:'bar',marker:{color:['#008b8d','#bd6509','#62748d','#"
            "7254c7']}}],{title:'Measured network WAPE — lower is better',yaxi"
            "s:{title:'WAPE (%)'},margin:{t:55,b:65},paper_bgcolor:'white'},{r"
            "esponsive:true,displayModeBar:false});\nconst e=JSON.parse(documen"
            "t.getElementById('canonical-evidence').textContent());const s=['B"
            "ase','+15% demand','-10% productivity'];Plotly.newPlot('actual-ch"
            "art',['proportional','optimized'].map((m,i)=>({name:m,x:s,y:s.map"
            "(k=>e.retrospective_summary.find(r=>r.scenario===k&&r.allocation_"
            "method===m).actual_uncovered_hours),type:'bar',marker:{color:i?'#"
            "b53843':'#62748d'}})),{title:'Retrospective actual uncovered hour"
            "s — lower is better',barmode:'group',yaxis:{title:'Uncovered hour"
            "s'},margin:{t:55,b:65}},{responsive:true,displayModeBar:false});\n"
            "</script></body></html>"
        )
    )


def report_html(e: Evidence, png: bytes) -> str:
    """Introduce the project before retaining every original analytical section."""
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_overview as overview,
    )

    document = _analytical_html(e, png)
    anchors = ["overview"] + [f"section-{i}" for i in range(1, 9)]
    navigation = (
        '<nav aria-label="Report sections">'
        + "".join(
            f'<a href="#{anchor}">{label}</a>'
            for anchor, label in zip(anchors, overview.NAV_LABELS, strict=True)
        )
        + "</nav>"
    )
    document = re.sub(r"<nav>.*?</nav>", lambda _: navigation, document, count=1)
    document = document.replace(
        '<section id="section-1">', overview.overview_html(e) + '<section id="section-1">', 1
    )
    document = document.replace("</style>", overview.OVERVIEW_CSS + "</style>", 1)
    # Preserve every analytical row; disclose detailed tables after the plain-English reading.
    for index in (2, 4, 5, 6, 7):
        pattern = rf'(<section id="section-{index}">)(.*?)(</section>)'

        def disclose(match: re.Match[str]) -> str:
            content = re.sub(
                r'(<div class="scroll">.*?</table></div>)',
                r"<details><summary>How we measured it · open evidence table</summary>\1</details>",
                match[2],
                flags=re.DOTALL,
            )
            return match[1] + content + match[3]

        document = re.sub(pattern, disclose, document, flags=re.DOTALL)
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_charts as charts,
    )
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_decisions as decisions,
    )
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_modeling as modeling,
    )
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
        presentation_navigation as nav,
    )

    specs = charts.chart_specs(e)
    old_sections = dict(re.findall(r'<section id="([^"]+)">(.*?)</section>', document, re.DOTALL))
    groups = [
        ("overview", ["overview", "section-1"]),
        ("arena", ["section-2"]),
        ("champion", ["section-3"]),
        ("diagnostics", ["section-4"]),
        ("labor", ["section-5"]),
        ("scenario", ["section-6"]),
        ("governance", ["section-7", "section-8"]),
    ]
    panels = []
    for key, members in groups:
        figures = "".join(
            '<figure class="visual-card"><h3>'
            + html.escape(spec["title"])
            + "</h3>"
            + f'<div id="visual-{name}" class="chart" role="img" aria-label="'
            + html.escape(spec["title"] + "; " + spec["unit"])
            + '"></div>'
            + "<p><b>What this means:</b> "
            + html.escape(spec["meaning"])
            + "</p><small>Source: "
            + html.escape(spec["source"])
            + "</small><details><summary>Chart values · accessible evidence</summary>"
            + '<div class="scroll">'
            + table(
                [
                    {"series": trace.get("name", spec["title"]), "label": label, "value": value}
                    for trace in spec["data"]
                    for label, value in zip(trace.get("x", []), trace.get("y", []), strict=True)
                ],
                [("series", "Series"), ("label", "Date / group"), ("value", spec["unit"])],
            )
            + "</div></details></figure>"
            for name, spec in specs.items()
            if spec["panel"] == key
        )
        extra = ""
        if key == "overview":
            extra = (
                '<div class="timeline" aria-label="Common forecast timeline">'
                "<p>Historical training<br><b>2011-01-29 \u2013 2016-04-24</b></p>"
                "<p>→ Forecast origin<br><b>No holdout actuals in features</b></p>"
                + (
                    "<p>→ Same 28-day holdout<br><b>2016-04-25 \u2013 2016-05-22</b><b"
                    "r>All four methods</p></div>"
                )
            )
        if key == "labor":
            productivity = e.stages["operations"]["configuration"]["labor"][
                "productivity_units_per_hour"
            ]
            extra = (
                '<div class="workload-flow"><p>Selected forecasts<br>FOODS + HOUSEHOLD units</p>'
                + "<p>→ Divide by illustrative productivity<br>"
                + f"FOODS {productivity['FOODS']:g}; "
                + f"HOUSEHOLD {productivity['HOUSEHOLD']:g} units/hour</p>"
                + (
                    "<p>→ Sum required hours per store-day<br>Allocate within fix"
                    "ed staffing and capacity</p></div>"
                )
            )
        if key == "governance":
            extra = '<p class="provenance">' + nav.PROVENANCE + "</p>"
        figure_parts = re.findall(r"<figure.*?</figure>", figures, re.DOTALL)
        chart_html: dict[str, str] = {}
        for part in figure_parts:
            match = re.search(r'id="visual-([^"]+)"', part)
            if match is None:
                raise ValueError("Chart figure is missing its identifier")
            chart_html[match[1]] = part
        if key == "overview":
            calendar = chart_html.pop("calendar_context", "")
            history = chart_html.pop("demand_history", "")
            visuals = '<div class="visual-grid">' + history + "</div>"
            visuals += (
                "<details><summary>Explore state/category mix, store variation "
                "and weekday patterns</summary>"
                + '<div class="visual-grid">'
                + "".join(chart_html.values())
                + "</div></details>"
            )
            visuals += (
                "<details><summary>Additional calendar context</summary>" + calendar + "</details>"
            )
            body = (
                '<section id="overview">'
                + decisions.introduction(key, e)
                + extra
                + visuals
                + "</section>"
            )
            body += (
                '<section id="section-1"><h2>DECISION 01 — WHICH FORECASTS SHOULD WE TRUST?</h2>'
                + decisions.implication("arena", e)
                + "<h2>EXECUTIVE DECISION</h2>"
                + decisions.executive(e)
                + modeling.production_inputs()
                + "<p><b>Short result:</b> "
                + html.escape(e.portfolio)
                + "</p>"
                + "<p>RETROSPECTIVE: selected and scored on the same holdout; n"
                "ot future performance.</p>"
                + "<p>Use Forecast Arena and Champion Map for ownership; Labor "
                "Optimizer for allocation and impact; Governance / DRI for ne"
                "xt actions.</p>"
                + "<details><summary>Definitions and technical reference</summary>"
                + old_sections["overview"]
                + old_sections["section-1"]
                + "</details></section>"
            )
        else:
            main_figures = figures
            impact_figures = ""
            if key == "labor":
                impact_figures = chart_html.pop("critical") + chart_html.pop("actual_uncovered")
                main_figures = "".join(chart_html.values())
            lead = decisions.introduction(key, e)
            if key == "arena":
                lead += modeling.modeling_html()
            if key == "diagnostics":
                lead += modeling.diagnostics_purpose() + decisions.diagnostic_actions(e)
            if key == "champion":
                main_figures = (
                    "".join(re.findall(r"<img[^>]+>", old_sections["section-3"])) + main_figures
                )
            if key == "labor":
                lead += extra + "<h3>What was the final labor allocation?</h3>"
                lead += (
                    "<p>Base scenario · average labor-hours per store-day over th"
                    "e complete holdout. Difference = optimized minus proportiona"
                    "l.</p>"
                )
                lead += table(
                    decisions.allocation_summary(e),
                    [
                        ("store", "Store"),
                        ("optimized_hours", "Final optimized hours/day"),
                        ("proportional_hours", "Proportional hours/day"),
                        ("difference_hours", "Difference (hours/day)"),
                        ("direction", "Receives"),
                        ("planning_days", "Planning days"),
                    ],
                )
                final_rows = decisions.allocation_summary(e)
                gains = ", ".join(r["store"] for r in final_rows if r["direction"] == "More")
                losses = ", ".join(r["store"] for r in final_rows if r["direction"] == "Fewer")
                average_used = sum(r["optimized_hours"] for r in final_rows)
                lead += (
                    f"<p><b>Final Base allocation:</b> {average_used:.2f} hours/day on average. "
                    f"More hours: {gains}. Fewer hours: {losses}.</p>"
                )
                lead += (
                    "<details><summary>Date-level allocation evidence</summary>"
                    + table(
                        [r for r in e.tables["labor_allocations"] if r["scenario"] == "Base"],
                        [
                            ("date", "Date"),
                            ("store_id", "Store"),
                            ("allocation_method", "Method"),
                            ("allocated_hours", "Hours"),
                        ],
                    )
                    + "</details>"
                )
            if key == "governance":
                lead += modeling.operating_system() + extra
            body = '<section id="' + members[0] + '">' + lead
            body += decisions.implication(key, e)
            if key == "labor":
                body += "<details><summary>How hours were reallocated · supporting charts</summary>"
            body += '<div class="visual-grid">' + main_figures + "</div>"
            if key == "labor":
                body += "</details>"
            body += "<details><summary>Technical methods and full evidence</summary>"
            if key == "governance":
                body += "<h3>Governance and Assumptions</h3><p>Ownership: forecasting DRI with "
                body += (
                    "store operations and workforce planning. "
                    "Review exceptions before promotion.</p>"
                )
            else:
                body += old_sections[members[0]]
            body += "</details></section>"
            if key == "labor":
                body += '<div id="impact-check" class="impact-check">' + decisions.impact(e)
                body += modeling.production_inputs(optimizer=True)
                body += '<div class="visual-grid">' + impact_figures + "</div></div>"
            if key == "governance":
                body += (
                    '<section id="section-8"><h2>FINAL EXECUTIVE ANSWER</h2>' + modeling.takeaway(e)
                )
                body += "<details><summary>What I Would Do as the Forecast Accuracy DRI</summary>"
                body += decisions.next_actions() + "</details></section>"
        panels.append(
            f'<div id="panel-{key}" class="tab-panel" data-panel="{key}" '
            f'role="tabpanel" aria-labelledby="tab-{key}">' + body + "</div>"
        )
    navigation = (
        '<nav role="tablist" aria-label="Report sections">'
        + "".join(
            f'<a id="tab-{key}" role="tab" data-tab="{key}" href="#panel-{key}" '
            f'aria-controls="panel-{key}" aria-selected="false">{label}</a>'
            for key, label in nav.TABS
        )
        + "</nav>"
    )
    # Retain the original styles, hero, all explanations and evidence tables.
    prefix = document.split("<nav", 1)[0]
    prefix = prefix.replace("</style>", nav.CSS + "</style>", 1)
    prefix = re.sub(
        r"<header>.*?</header>",
        "<header><small>PROJECT 5 / PUBLIC-DATA PORTFOLIO</small>"
        "<h1>Quick-Commerce Control Tower</h1></header>",
        prefix,
        flags=re.DOTALL,
    )
    prefix = prefix.replace(
        "</style>",
        ".decision-framework{display:flex;flex-direction:column;align-items:center;gap:6px;"
        "background:#e5eef6;padding:20px;margin:20px 0}.decision-framework span{font-weight:700;"
        "text-align:center;overflow-wrap:anywhere}.story-spine{font-size:14px;line-height:1.8}"
        ".impact-check,.decision-answer{padding:24px;border-left:5px "
        "solid #008b8d;background:#edf6f5;"
        "margin:24px 0;min-width:0}.decision-answer{border-color:#008b8d;background:#edf6f5}"
        ".constraint-strip ul{display:flex;flex-wrap:wrap;gap:30px;padding:20px;list-style:none}"
        "</style>",
        1,
    )
    visible = prefix + navigation + "".join(panels) + "</main>"
    visible = visible.replace(NO_IMPACT, "")
    visible = visible.replace("No production-service claim. No DoorDash impact measurement.", "")
    visible = visible.replace("or DoorDash inventory data", "or observed inventory data")
    visible = visible.replace(
        (
            "This portfolio prototype uses public M5 retail data; it is n"
            "ot a DoorDash production system."
        ),
        "This public-data portfolio case study connects forecasting to operating decisions.",
    )
    visible = re.sub(r'<div id="(?:network|actual)-chart".*?</div>', "", visible)
    payload = json.dumps(specs, ensure_ascii=False).replace("<", "\\u003c")
    evidence_json = json.dumps(e.tables, ensure_ascii=False).replace("<", "\\u003c")
    return (
        visible
        + (
            "<noscript><p>All report panels remain available without Java"
            "Script. Evidence tables accompany the charts.</p></noscript>"
        )
        + "<script>"
        + nav.CONTROLLER
        + "</script>"
        + '<script type="application/json" id="canonical-evidence">'
        + evidence_json
        + "</script>"
        + '<script type="application/json" id="chart-evidence">'
        + payload
        + "</script>"
        + "<script>"
        + str(get_plotlyjs())
        + "</script><script>"
        + "document.addEventListener('toggle',()=>window.dispatchEvent(new Event('resize')),true);"
        + "const specs=JSON.parse(document.getElementById('chart-evidence').textContent);"
        + (
            "Object.entries(specs).forEach(([id,s])=>{try{Plotly.newPlot("
            "'visual-'+id,s.data,s.layout,"
        )
        + (
            "{responsive:true,displayModeBar:false});}catch(error){docume"
            "nt.getElementById('visual-'+id).textContent='Chart unavailab"
            "le; see canonical evidence tables.';}});"
        )
        + "</script></body></html>"
    )
