"""Recruiter-first explanations and progressive report styling; no analytical changes."""

from __future__ import annotations

from html import escape

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    LABOR_LIMIT,
    NAMES,
    RETROSPECTIVE,
    Evidence,
    number,
)

MODEL_GUIDE = (
    (
        "Seasonal Naïve",
        "Transparent baseline",
        "Use demand from exactly 28 days ago as today's forecast.",
        "A sophisticated model must prove it beats a simple, understandable baseline.",
    ),
    (
        "Holt-Winters",
        "Classical statistical forecasting",
        "Models recurring patterns such as weekly seasonality and local trend.",
        "Tests whether traditional time-series structure is enough.",
    ),
    (
        "HistGradientBoosting (HGB)",
        "Machine learning",
        "Learns nonlinear relationships among demand history, store/category identity, "
        "calendar patterns, events and SNAP information.",
        "Tests whether combining predictive signals beats classical time-series rules.",
    ),
    (
        "MLPRegressor (MLP)",
        "Neural-network challenger",
        "A feed-forward neural network learning more flexible relationships from the "
        "same leakage-safe inputs.",
        "Tests whether additional flexibility produces better forecasts; it is not automatically "
        "superior. This is not an LSTM.",
    ),
)
METRIC_GUIDE = (
    (
        "WAPE",
        "Total absolute forecast error as a percentage of total demand.",
        "Lower is better. Illustrative example: 8% WAPE means total absolute error was "
        "roughly 8% of total demand volume; this example is not a measured project score.",
    ),
    (
        "MAE",
        "Average number of units the forecast missed by per observation.",
        "Lower is better. Here an observation is one store-category on one day.",
    ),
    (
        "Bias",
        "Whether forecasts are systematically too high or too low.",
        "Closer to 0% is better. Positive = overall overforecast; negative "
        "= overall underforecast.",
    ),
    (
        "Completeness",
        "Whether every expected forecast was produced.",
        "100% is ideal. Missing predictions cannot qualify a model as champion.",
    ),
    (
        "Model disagreement",
        "How differently competing models see the same demand.",
        "Higher disagreement can prompt human review; agreement alone does not prove accuracy.",
    ),
)
MICRO_DEFINITIONS = (
    ("Champion", "The eligible model with the lowest WAPE for one store-category."),
    ("Holdout", "The test period kept aside when generating forecasts."),
    ("Data leakage", "Using information a model would not actually know at forecast time."),
    (
        "Critical store-day",
        "A store-date whose uncovered forecast workload exceeds the "
        "configured illustrative threshold of 8 labor-hours.",
    ),
)
NAV_LABELS = (
    "Overview",
    "Decision",
    "Models",
    "Champions",
    "Diagnostics",
    "Labor",
    "Scenarios",
    "Governance",
    "DRI",
)

OVERVIEW_CSS = """
body{background:#edf2f5;color:#18324b;font-size:17px;line-height:1.65}
main{max-width:1280px;padding:32px 28px}
header{border-radius:20px;padding:42px 48px;box-shadow:0 12px 40px #142e4912}
header h2{font-size:25px;line-height:1.45;font-weight:500;max-width:920px}
header p{font-size:15px;color:#dbe8f3;max-width:1000px}
h1{font-size:46px;letter-spacing:-.035em;margin:18px 0}
h2{letter-spacing:-.025em}h3{line-height:1.4}
nav{position:sticky;top:0;z-index:5;flex-wrap:nowrap;overflow-x:auto;
 background:#edf2f5f5;gap:4px;padding:12px 4px;border-bottom:1px solid #cfdae4}
nav a{white-space:nowrap;text-decoration:none;font-weight:650;font-size:14px;
 background:transparent;border-radius:8px;padding:9px 13px}
nav a:hover,nav a:focus-visible{background:#dcebe9;color:#075c5e;outline:2px solid #14787a}
section{scroll-margin-top:84px;margin:28px 0 44px;padding:36px 40px;
 border:1px solid #d9e2e9;box-shadow:0 7px 22px #142e4907;border-radius:18px}
section>h2{margin:12px 0 28px}section>small{color:#147477}
.overview-lead{font-size:24px;line-height:1.5;max-width:900px;margin-bottom:28px}
.overview-block{padding:24px 0;border-top:1px solid #e0e7ed}
.overview-block h3{font-size:25px;margin:8px 0 20px}
.overview-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.overview-grid article{margin:0;padding:22px;border:1px solid #e0e7ed;background:#f8fafb}
.overview-grid h4{font-size:20px;margin:8px 0;color:#15364e}
.overview-grid p{margin:9px 0}.overview-grid small{letter-spacing:.05em}
.overview-grid .why{color:#465d70;border-top:1px solid #dde6ed;padding-top:12px}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0}
.legend span{background:#e6f1ef;padding:9px 14px;border-radius:8px;font-weight:650}
.journey{padding:20px;background:#eaf1f8;border-left:4px solid #3471a4;
 line-height:1.9;border-radius:0 10px 10px 0}
.result-bridge{background:#f1f7f6;border:1px solid #cddfdb;padding:24px;border-radius:12px}
.result-bridge li{padding:5px 0}.definition-list{display:grid;gap:10px}
.definition-list p{margin:0;padding:12px 16px;background:#f5f8fa;border-radius:8px}
abbr[title]{text-decoration:underline dotted;text-underline-offset:4px;cursor:help}
.brief{gap:14px}.brief>div{margin:0;background:#f6f8fa;border-left:3px solid #cfdddf}
.brief>div p{margin:8px 0}.cards article,.recommendations article{border:1px solid #e0e7ed}
.recommendations h3{font-size:18px;line-height:1.55}.hero-metric{font-size:26px}
details{border:1px solid #dce5eb;background:#fafcfd;border-radius:10px;margin:18px 0}
summary{cursor:pointer;padding:16px 20px;color:#22526a;font-weight:650}
summary:focus-visible{outline:2px solid #14787a}.scroll{margin:0;padding:0 16px 16px}
th{color:#264559;font-size:13px;letter-spacing:.02em}td{font-variant-numeric:tabular-nums}
tbody tr:nth-child(even){background:#f5f8fa}tbody tr:hover{background:#e9f2f2}
.chart{border:1px solid #e1e7ed;border-radius:12px;margin:20px 0;overflow:hidden}
.warning{border-left-width:4px;border-radius:0 10px 10px 0;font-size:16px}
@media(max-width:760px){main{padding:12px}header,section{padding:24px 20px}
 h1{font-size:34px}header h2{font-size:22px}.overview-lead{font-size:21px}
 .overview-grid{grid-template-columns:1fr}nav a{padding:8px;font-size:13px}}
"""


def overview_html(e: Evidence) -> str:
    d = e.stages["demand_daily"]
    best = min(e.tables["network_scorecard"], key=lambda r: r["wape"])

    def block(title: str, body: str) -> str:
        return '<div class="overview-block"><h3>' + escape(title) + "</h3>" + body + "</div>"

    result = (
        '<section id="overview"><small>START HERE / PROJECT OVERVIEW</small>'
        '<h2>PROJECT OVERVIEW</h2><p class="overview-lead">'
        "From demand forecasting to constrained operating decisions</p>"
        "<p>A quick-commerce or retail network must anticipate demand at each location "
        "before it happens. Forecasts are useful only if they lead to decisions. "
        "This portfolio prototype uses public M5 retail data; it is not a DoorDash "
        "production system.</p><ol><li>Which approach works best for each store-category?"
        "</li><li>Where do forecasts miss, and what should we investigate?</li>"
        "<li>How should forecasted demand become constrained labor planning?</li>"
        "<li>What happens when demand rises or productivity falls?</li></ol>"
    )
    result += block(
        "What am I looking at?",
        (
            "<p>M5 is a public retail-demand forecasting dataset built from Walmart sales history. "
            "We forecast daily units of merchandise demanded, aggregated within "
            "each store-category.</p>"
            '<div class="legend"><span>10 stores</span><span>3 states</span>'
            "<span>2 categories</span><span>20 daily demand series</span></div>"
            '<div class="legend"><span>CA = California</span><span>TX = Texas</span>'
            "<span>WI = Wisconsin</span></div>"
            "<p><b>CA_1</b> = California store 1; <b>CA_2</b> = California store 2; "
            "<b>TX_3</b> = Texas store 3; <b>WI_2</b> = Wisconsin store 2. "
            "These are dataset identifiers, not customer names or street addresses.</p>"
            "<p><b>FOODS</b> = food-related merchandise. <b>HOUSEHOLD</b> = household merchandise. "
            "<b>CA_3 / FOODS</b> means daily FOODS demand for California store 3.</p>"
            "<p>Calendar events and SNAP information provide context. SNAP refers to the "
            "Supplemental Nutrition Assistance Program; its state-specific calendar flag is "
            "a predictive input, not evidence of what caused an error.</p>"
        ),
    )
    result += block(
        "What are we forecasting?",
        (
            '<p class="journey">Historical daily demand → information available '
            "at forecast issuance "
            "→ predict the next 28 days → actual demand is revealed afterward → "
            "score the forecast</p>"
            "<p>All four models predict the same 28 dates. A fair competition requires every "
            "competitor to face the same test.</p>"
        ),
    )
    models = "".join(
        "<article><small>"
        + escape(kind)
        + "</small><h4>"
        + escape(name)
        + "</h4><p>"
        + escape(explanation)
        + '</p><p class="why"><b>Why include it?</b> '
        + escape(reason)
        + "</p></article>"
        for name, kind, explanation, reason in MODEL_GUIDE
    )
    result += block(
        "Four approaches enter the arena",
        (
            '<p class="journey">Simple baseline → classical statistics → machine learning '
            "→ neural network</p><p>The purpose is to determine which approach earns ownership "
            "of each forecasting decision. Complexity is not the selection rule.</p>"
            '<div class="overview-grid">' + models + "</div>"
        ),
    )
    result += block(
        "Training history versus the holdout",
        (
            '<div class="overview-grid"><article><small>TRAINING HISTORY</small><h4>'
            + escape(d["training_start"] + " through " + d["training_end"])
            + "</h4><p>The models learn from this period.</p></article>"
            "<article><small>TEST / HOLDOUT</small><h4>"
            + escape(d["holdout_start"] + " through " + d["holdout_end"])
            + "</h4><p>These 28 days are kept aside to evaluate the forecasts.</p></article></div>"
            "<p><b>Data leakage</b> happens when a model learns information it would not actually "
            "know at forecast time. Models must not look at actual test-period demand while "
            "generating forecasts. Automated mutation tests altered holdout actual values and "
            "verified that forecasts did not change.</p>"
        ),
    )
    definitions = "".join(
        '<article><h4><abbr title="'
        + escape(explanation, quote=True)
        + '">'
        + escape(name)
        + "</abbr></h4><p>"
        + escape(explanation)
        + '</p><p class="why">'
        + escape(interpretation)
        + "</p></article>"
        for name, explanation, interpretation in METRIC_GUIDE
    )
    result += block(
        "How do we judge a forecast?",
        (
            '<div class="overview-grid">' + definitions + "</div>"
            "<p>WAPE is the primary champion-ranking metric after governance checks. "
            "A low score does not excuse missing or systematically biased forecasts.</p>"
        ),
    )
    result += block(
        "What does champion model mean?",
        (
            "<p>A <b>champion</b> is the eligible model that earns ownership of one "
            "store-category forecast. For each store-category:</p>"
            "<ol><li>Did it produce all 28 forecasts?</li>"
            "<li>Are forecasts valid and nonnegative?</li>"
            "<li>Is absolute bias within the 10% guardrail?</li>"
            "<li>Did deterministic validation pass?</li>"
            "<li>Among models that pass, which has the lowest WAPE?</li></ol>"
            "<p>Different demand patterns may favor different approaches. There need not be "
            "one champion for the whole network. <b>No eligible champion—review required</b> "
            "means none of the four passed all requirements for that series. "
            "<b>TX_3 / FOODS</b> is the real example: Texas store 3, food merchandise.</p>"
        ),
    )
    counts = "; ".join(f"{name}: {count}" for name, count in e.counts.items())
    result += block(
        "Results in plain English",
        (
            '<div class="result-bridge"><ol><li>'
            + escape(NAMES[best["model_name"]])
            + " was the strongest single network-wide model at "
            + number(best["wape"], percent=True)
            + " WAPE.</li>"
            "<li>No single model qualified across every store-category.</li><li>"
            + escape(counts)
            + ".</li><li>"
            + escape(e.portfolio)
            + "</li><li>"
            + escape(RETROSPECTIVE)
            + "</li><li>Forecast accuracy alone is not enough: "
            "forecasts then become a constrained labor-allocation problem.</li><li>"
            + escape(LABOR_LIMIT)
            + "</li></ol></div>"
        ),
    )
    result += block(
        "Keep these terms nearby",
        '<div class="definition-list">'
        + "".join(
            '<p><abbr title="'
            + escape(value, quote=True)
            + '"><b>'
            + escape(term)
            + "</b></abbr> — "
            + escape(value)
            + "</p>"
            for term, value in MICRO_DEFINITIONS
        )
        + "</div><p>Continue to the decision brief, then open detailed evidence where useful.</p>",
    )
    return result + "</section>"
