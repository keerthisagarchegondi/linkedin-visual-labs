"""Project 6 reference compositions, with immutable analytical bindings."""

from __future__ import annotations

import html
import re

from .design_system import AMBER, BLUE, GREEN, PURPLE, css_tokens
from .presentation import RIGHTS, TABS, Presentation, clock

STYLE = """
*{box-sizing:border-box}
body{margin:0;
background:var(--bg);
color:var(--text);

font:15px/1.35 'DejaVu Sans',Arial,sans-serif}
header{height:153px;
background:white;

padding:50px 30px 10px;
position:relative;
border-top:16px solid #E8EDF2}

.brand{display:flex;
gap:22px;
align-items:center}
.logo{background:var(--dark);
color:white;

padding:18px;
border-radius:18px;
font-size:23px;
font-weight:bold}
h1{font-size:30px;

margin:0 0 3px;
line-height:1.15}
p{color:var(--muted);
margin:10px 0}

.brand p{margin:4px 0}
nav{position:absolute;
right:245px;
bottom:10px;
display:flex;
gap:28px}

button{font:inherit;
cursor:pointer;
background:transparent;
border:0;
color:var(--muted);

padding:4px 0}
button[aria-selected=true]{color:var(--blue);
border-bottom:4px solid var(--blue);

font-weight:bold}
.badge{position:absolute;
right:30px;
top:35px;
background:var(--cream);

color:var(--text);
padding:10px 18px;
border-radius:18px;
font-size:13px;
font-weight:bold}

main{max-width:1600px;
margin:auto;
padding:22px 30px}
h2{font-size:25px;
margin:0 0 16px;

line-height:1.2}
h3{font-size:18px;
margin:0 0 12px}
.section-heading{margin-top:32px}

.grid{display:grid;
gap:22px}
.six{grid-template-columns:repeat(5,1fr) 1.45fr}

.two{grid-template-columns:1fr 1fr}
.four{grid-template-columns:repeat(4,1fr)}

.seven{grid-template-columns:repeat(7,1fr)}
.five{grid-template-columns:repeat(5,1fr)}

.flow-grid{grid-template-columns:3fr 2fr;
gap:34px;
margin-top:32px}

.video-grid{grid-template-columns:2.06fr 1fr;
gap:34px}
.result-grid{grid-template-columns:400px 1fr}

.interpret-grid{grid-template-columns:2.06fr 1fr;
gap:40px}
.card{background:white;

border:1px solid var(--border);
border-radius:16px;
padding:19px;
min-width:0}

.label{font-size:14px;
color:var(--muted);
font-weight:bold}
.big{font-size:28px;

font-weight:bold;
margin:12px 0 8px;
line-height:1.15}
.detail{font-size:13px;
margin:0}

.dark{background:var(--dark);
color:white;
border-color:#627D94}
.dark p{color:#B7C7D5}

.amber{color:var(--amber)}
.blue{color:var(--blue)}
.note{background:var(--cream);

border:1px solid var(--amber);
padding:13px 18px;
border-radius:12px}

.result{border-color:var(--red);
background:#FFECEC}
.result .big{font-size:23px}

.kpi .card{min-height:112px;
padding:14px}
.kpi .big{font-size:22px;
margin:10px 0}
.kpi .label{font-size:12px}
.kpi .detail{font-size:12px}
.flow{height:412px;
overflow:hidden;
background:var(--dark)}

.flow img{width:100%;
height:100%;
object-fit:cover}
.spark-row{display:grid;
grid-template-columns:135px 1fr;

align-items:center;
gap:10px;
margin-bottom:18px}
.spark-row svg{width:100%;
height:65px;

background:white;
border:1px solid var(--border)}
.spark-row b{font-size:14px}

.driver{font-size:13px;
margin-top:18px}
.action{background:#E7F8EE;
border:1px solid var(--green);

display:grid;
grid-template-columns:1.6fr 1fr;
gap:28px;
padding:18px 26px;
border-radius:14px}

.action strong{font-size:21px}
.player-box{display:grid;
grid-template-columns:1.3fr 1fr;
gap:28px;

padding:24px;
height:710px}
.player-box video{width:100%;
height:660px;
background:var(--dark)}

.story{display:grid;
gap:20px;
align-content:start}
.story .card{min-height:160px;
color:var(--text)}

.source-cards{display:grid;
gap:12px}
.source-cards .card{min-height:106px;
padding:14px}

.source-cards .big{margin:8px 0}
.pipeline .card{height:182px;
padding:16px}
.number{display:inline-grid;

place-items:center;
width:42px;
height:42px;
background:var(--blue);
color:white;
border-radius:50%;

font-size:23px;
margin-bottom:12px}
.pipeline h3{display:inline;
font-size:18px;
margin-left:6px}

.contract .card{min-height:175px}
.guards .card{min-height:177px}
.timeline{height:170px;

display:flex;
justify-content:space-around;
align-items:center;
position:relative}

.timeline:before{content:'';
position:absolute;
left:7%;
right:7%;
top:51%;
height:4px;
background:#A6B7C8}

.event{z-index:1;
text-align:center}
.dot{display:block;
width:24px;
height:24px;
border-radius:50%;

background:var(--amber);
margin:18px auto}
.event:last-child .dot{background:var(--bg);
border:3px dashed var(--red)}

.interpret-row{display:grid;
grid-template-columns:185px 1fr;
padding:18px;
margin-bottom:10px;

background:white;
border:1px solid var(--border);
border-radius:10px}
.check{margin:15px 0}

.check:before{content:'•';
color:var(--green);
font-size:25px;
margin-right:14px}

.about-top .card{min-height:255px}
.about-top strong{font-size:23px;
line-height:1.3;
display:block}

.capabilities .card{min-height:178px}
.tech{grid-template-columns:1.65fr 1fr}

.technical{margin-top:26px;
border-top:1px solid var(--border);
padding:14px 0}

.technical summary{cursor:pointer;
color:var(--blue)}
.technical img{max-width:100%}

.technical .grid{grid-template-columns:repeat(2,1fr)}
table{width:100%;
border-collapse:collapse}

td,th{text-align:left;
padding:8px;
border-bottom:1px solid var(--border)}

footer{font-size:12px;
color:var(--muted);
margin-top:16px}
[hidden]{display:none!important}

a{color:var(--blue)}
button:focus-visible,a:focus-visible{outline:3px solid var(--amber);
outline-offset:4px}

.story .card p{color:var(--muted)}
.dark .label{color:#B7C7D5}
.dark p.amber{color:var(--amber)}
.result-grid .dark .big{color:var(--amber);font-size:36px}
.event:first-child .dot{background:var(--green)}
.pipeline .card:nth-child(2) .number{background:var(--green)}
.pipeline .card:nth-child(3) .number{background:var(--amber);color:var(--text)}
.pipeline .card:nth-child(4) .number{background:#8655FF}
.pipeline .card:nth-child(5) .number{background:var(--red)}
.pipeline .card:nth-child(6) .number{background:var(--cyan);color:var(--text)}
.pipeline .card:nth-child(7) .number{background:var(--green)}
.contract .dark h3{font-size:23px;margin-top:14px}
@media(max-width:1200px){header{height:auto;
padding:24px}
nav{position:static;
margin-top:20px}

.badge{position:static;
display:inline-block;
margin-top:12px}
.six,.seven{grid-template-columns:repeat(3,1fr)}

.player-box{height:auto}
.player-box video{height:auto}
.flow-grid{grid-template-columns:1.3fr 1fr}
}

@media(max-width:700px){header{padding:16px}
h1{font-size:23px}
.brand{gap:12px}
.brand p{font-size:13px}

nav{gap:18px;
flex-wrap:wrap}
main{padding:20px}
h2{font-size:22px}
.grid,.six,.two,.four,.seven,.five,
.flow-grid,.video-grid,.result-grid,.interpret-grid,.tech,.technical
.grid{grid-template-columns:1fr}

.player-box,.action{display:block}
.story{margin-top:20px}
.flow{height:310px}
.pipeline .card,
.guards .card,.capabilities .card{height:auto;
min-height:120px}
.interpret-row{grid-template-columns:1fr;
gap:8px}

.timeline{height:220px;
font-size:12px}
.spark-row{grid-template-columns:100px 1fr}
.big{font-size:25px}
}

"""


def esc(value: object) -> str:
    return html.escape(str(value))


def card(label: str, value: str, detail: str = "", extra: str = "") -> str:
    return (
        f'<div class="card {extra}"><div class="label">{esc(label)}</div>'
        f'<div class="big">{esc(value)}</div><p class="detail">{esc(detail)}</p></div>'
    )


def chart(p: Presentation, column: str, label: str, color: str) -> str:
    rows = p.metrics[(p.metrics.timestamp >= 1260) & (p.metrics.timestamp < 1800)]
    points = ""
    if column in rows:
        rows = rows[rows[column].notna()]
        hi = max(float(rows[column].max()), 1e-9) if len(rows) else 1.0
        lo = min(float(rows[column].min()), 0.0) if len(rows) else 0.0
        points = " ".join(
            f"{8 + (float(t) - 1260) / 540 * 394:.2f},{56 - (float(v) - lo) / (hi - lo) * 48:.2f}"
            for t, v in zip(rows.timestamp, rows[column], strict=True)
        )
    return (
        f'<div class="spark-row"><b>{label}</b><svg viewBox="0 0 410 65" role="img" '
        f'aria-label="{label}, original time 21:00 to 30:00, separate scale">'
        f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{points}"/></svg></div>'
    )


def build_report(p: Presentation, detailed: str, script: str) -> str:
    r = p.release
    changes = r["metric_changes"]

    def delta(key: str) -> str:
        a, b = (changes[key][k] for k in ("baseline_median", "screened_interval_median"))
        return ("N/A" if a is None else f"{a:.3g}") + " → " + ("N/A" if b is None else f"{b:.3g}")

    result = esc(r["result"]["result_classification"])
    recommendation = esc(r["recommendation"]["wording"])
    alternative = esc(r["recommendation"]["alternative_action"].title())
    chart_stack = "".join(
        chart(p, key, label, color)
        for key, label, color in (
            ("density_window_mean", "Density", AMBER),
            ("median_completed_dwell_seconds", "Completed dwell", BLUE),
            ("throughput", "Throughput", GREEN),
            ("movement_index", "Movement", PURPLE),
        )
    )
    dashboard = '<h2>1. Operations Overview</h2><div class="grid six kpi">'
    dashboard += card(
        "Density / zone vehicles", delta("density_window_mean"), "Baseline → comparison median"
    )
    dashboard += card(
        "Throughput / exits per 60s", delta("throughput"), "Increased; mixed evidence"
    )
    dashboard += card(
        "Completed dwell / seconds", delta("median_completed_dwell_seconds"), "Baseline unavailable"
    )
    dashboard += card("Visible queue", "Not qualified", "Independent outcome rule")
    dashboard += card("Lead time", "Not reportable", "Null onset; never zero")
    dashboard += card("ACTUAL WARNING", p.warning, "NO_VISIBLE_QUEUE_EVENT", "result") + "</div>"
    dashboard += f"""<div class="grid flow-grid"><div><h2>2. Flow Map</h2><div class="flow">
<img src="assets/flow_map.png" alt="Actual normalized trajectories; configured queue zone, no
measured hotspot"></div>
<p class="detail">20:00-30:00 original time · derived geometry · no physical scale</p></div>
<div><h2>3. Why the Warning Fired</h2>{chart_stack}<div class="note driver"><b>Primary: density
level</b><br>
Supporting: inflow-outflow imbalance + density trend. Charts retain mixed
signals.</div></div></div>
<h2 class="section-heading">4. Operational Recommendation</h2><div class="action"><div>
<div class="label">CONDITIONAL RESPONSE</div><strong>{recommendation}</strong></div><div>
Alternative: {alternative}<br>Illustrative operational response; facility controls
unknown.</div></div>"""
    video = """
<div class="grid video-grid"><div><h2>1. LinkedIn Explainer</h2><div class="card dark player-box">
<video controls preload="metadata" poster="assets/project6_thumbnail.png"><source
src="assets/project6_linkedin_web.mp4" type="video/mp4"></video><div
class="story"><h3>45-SECOND STORYBOARD</h3>"""
    for time, title, detail in (
        (0, "00-15 sec", "Business problem, execution glimpse, actual null-lead result."),
        (15, "15-30 sec", "Define metrics, reconcile tracks, retain mixed evidence."),
        (30, "30-45 sec", "Persistent warning, independent outcome, conditional review."),
    ):
        video += (
            f'<div class="card"><button data-time="{time}" class="amber">{title}</button>'
            f"<p>{detail}</p></div>"
        )
    video += '</div></div></div><div><h2>2. Source and Time Contract</h2><div class="source-cards">'
    for label, value, detail in (
        ("Source clip", "30 minutes", "One stationary historical camera"),
        (
            "Normal baseline",
            "-".join(clock(v) for v in p.rules["baseline"]),
            "Short baseline; no generalization",
        ),
        (
            "Comparison interval",
            "-".join(clock(v) for v in r["screened_comparison_interval"]),
            "Source-screened; not a validated degraded label",
        ),
        ("Independent queue", "Not qualified", "No target onset available"),
        ("Metric windows", "60 seconds", "FAST_TRACK; formal 300-second contract retained"),
    ):
        video += card(label, value, detail)
    video += """
<div class="note">Playback accelerates; calculations always use original timestamps.
No source footage is embedded.</div></div></div></div>"""
    method = '<h2>1. Method</h2><div class="grid seven pipeline">'
    for i, (title, detail) in enumerate(
        (
            ("Detect", "YOLOX-Nano vehicle detections; CPU ONNX."),
            ("Track", "ByteTrack-compatible clip-local association."),
            ("Measure", "Entry, exit, completed dwell and zone count."),
            ("Aggregate", "60-second windows; original time."),
            ("Warn", "Leading deterioration plus persistence."),
            ("Validate", "Independent scalar reconciliation; no accuracy claim."),
            ("Act", "Conditional review of the recorded evidence."),
        )
    ):
        method += (
            f'<div class="card"><span class="number">{i + 1}</span><h3>{title}</h3>'
            f"<p>{detail}</p></div>"
        )
    method += f"""
</div><h2 class="section-heading">2. Congestion Contract</h2><div class="grid two contract">
<div class="card dark"><div class="label">WARNING WHEN</div><h3>Density level + imbalance +
density trend</h3>
<p class="amber">{p.rules["warning"]["minimum_drivers"]} leading drivers persist for
{p.rules["warning"]["persistence_seconds"]}s.</p>
NORMAL → WATCH → WARNING; CRITICAL is configured, not observed.</div><div class="card">
<h3 class="blue">INDEPENDENT QUEUE OUTCOME</h3><p>Queue count ≥
{p.rules["queue"]["queue_count"]}; occupancy ≥
{p.rules["queue"]["zone_occupancy"]}; movement ≤ {p.rules["queue"]["movement_ceiling"]} for
{p.rules["queue"]["persistence_seconds"]}s. Not a duplicated warning rule.</p>
Dwell includes completed eligible journeys only; incomplete tracks remain censored.</div></div>
<h2 class="section-heading">3. Technical and Privacy Guardrails</h2><div class="grid five
guards">"""
    for title, detail in (
        ("Relative metrics", "Image-plane movement, not MPH or physical distance."),
        ("Anonymous IDs", "Temporary clip-local analytical IDs; aggregate public output."),
        ("No identity", "No facial recognition, plate OCR or external lookup."),
        ("Fixed camera", "One viewpoint; no cross-camera identity."),
        ("Explainable rule", "Classified evidence; no production or impact claim."),
    ):
        method += f'<div class="card"><h3>{title}</h3><p>{detail}</p></div>'
    method += "</div>"
    timeline = '<div class="card timeline">'
    for label, value in (
        ("Normal", clock(r["result"]["transitions"][0]["timestamp"])),
        ("Warning", p.warning),
        ("Visible queue", "Not qualified"),
    ):
        timeline += f'<div class="event"><b>{value}</b><span class="dot"></span>{label}</div>'
    timeline += "</div>"
    results = '<h2>1. Results</h2><div class="grid result-grid">'
    results += card("LEAD TIME", "Not reportable", result, "dark") + timeline + "</div>"
    results += (
        '<h2 class="section-heading">2. Metric Changes at Warning</h2><div class="grid four">'
    )
    for label, key in (
        ("Density", "density_window_mean"),
        ("Completed dwell", "median_completed_dwell_seconds"),
        ("Throughput", "throughput"),
        ("Net inflow", "inflow_outflow_imbalance"),
    ):
        results += card(label, delta(key), "Baseline → screened comparison medians")
    results += (
        '</div><h2 class="section-heading">3. Interpretation and Validation</h2>'
        '<div class="grid interpret-grid"><div>'
    )
    sensitivity = p.summary()["sensitivity_warning_range"]
    false = r["result"]["baseline_false_warning"]
    for label, detail in (
        (
            "Observed pattern",
            "Density and imbalance increased; throughput and movement also increased.",
        ),
        (
            "Evidence",
            f"{r['unmatched_warning']['warning_state_seconds']}-second unmatched warning. "
            "Queue onset remains null.",
        ),
        (
            "Sensitivity",
            f"{sensitivity[0]:g}-{sensitivity[1]:g}s warning onset; queue remained unqualified.",
        ),
        ("Operational response", r["recommendation"]["wording"]),
    ):
        results += (
            f'<div class="interpret-row"><b class="blue">{label}</b>'
            f"<span>{esc(detail)}</span></div>"
        )
    results += f"""
</div><div class="card"><h3>VALIDATION CHECKS</h3><div class="check">
{false["baseline_false_warning_count"]}
baseline false-warning episodes (in-sample)</div><div
class="check">{false["warning_seconds"]}/{false["evaluable_seconds"]}
evaluable baseline seconds</div><div class="check">Original-time computation reconciles</div>
<div class="check">{p.counts["candidate_tracks"]} candidates →
{p.counts["eligible_confirmed_tracks"]} confirmed →
{p.counts["completed_dwell_samples"]} completed</div><p>No independent detector/tracker
accuracy established.
This is not proof of physical queue absence.</p></div></div>"""
    about = """
<h2>1. About the Project</h2><div class="grid two about-top"><div class="card dark">
<h3 class="amber">BUSINESS PROBLEM</h3><strong>Operations may already have camera footage but
learn about
congestion only after a queue becomes obvious.</strong><p>PROJECT QUESTION</p>Can anonymous
vehicle movement
support an earlier, explainable warning?</div><div class="card"><h3 class="blue">THE HARD PART
WAS NOT OBJECT DETECTION</h3>
<p>• Define congestion operationally.</p><p>• Reconcile fragmented tracks through occlusion.</p>
<p>• Separate persistent warning from independent outcome.</p><p>• Link conditional action to
evidence.</p>
<p>• Preserve privacy and report null results honestly.</p></div></div>
<h2 class="section-heading">2. Capability Demonstrated</h2><div class="grid four
capabilities">"""
    for title, detail in (
        (
            "Metric leadership",
            "Translate operational concerns into explicit measurable definitions.",
        ),
        ("Technical execution", "Source screening, CPU pipeline, validation and visual packaging."),
        ("Stakeholder framing", "Operations, Engineering, Analytics and Privacy perspectives."),
        ("Decision product", "Camera → metric → warning → evidence → conditional action."),
    ):
        about += f'<div class="card"><h3>{title}</h3><p>{detail}</p></div>'
    about += """
</div><h2 class="section-heading">3. Technology, Data and Limits</h2><div class="grid tech">
<div class="card"><h3 class="blue">STACK AND SOURCE</h3><b>Python · ONNX Runtime · YOLOX-Nano ·
ByteTrack-compatible
tracking · Parquet · Pillow · packaged FFmpeg</b><p>AI City 2021 Track 1, cam_3. Source imagery
restricted;
aggregate derived output only.</p></div><div class="note"><h3>LIMITATIONS AND ROADMAP</h3>One
camera, short baseline,
fragmented tracks, no established physical queue onset. Future work: independent labels, longer
baseline,
stronger tracking and verified operating levers. No deployment or impact claim.</div></div>"""
    old_panels = re.findall(r'<section role="tabpanel"[^>]*>(.*?)</section>', detailed, re.DOTALL)
    bodies = (dashboard, video, method, results, about)
    panels = "".join(
        f'<section role="tabpanel" id="panel-{tab.lower()}" aria-labelledby="tab-{tab.lower()}" '
        f'{"hidden" if i else ""}>{body}<details class="technical">'
        "<summary>Evidence, definitions and limitations</summary>"
        f"{old_panels[i]}</details></section>"
        for i, (tab, body) in enumerate(zip(TABS, bodies, strict=True))
    )
    nav = "".join(
        f'<button role="tab" id="tab-{tab.lower()}" aria-controls="panel-{tab.lower()}" '
        f'aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}">{tab}</button>'
        for i, tab in enumerate(TABS)
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1"><title>Project 6 — Traffic Operations
Early-Warning System</title>
<style>{css_tokens()}{STYLE}</style></head><body><header><div class="brand"><div
class="logo">P6</div><div>
<h1>Traffic Operations Early-Warning System</h1><p>From anonymous vehicle tracking to an
explainable warning decision.</p>
</div></div><span class="badge">RECORDED PROTOTYPE</span><nav role="tablist" aria-label="Report
sections">{nav}</nav>
</header><main>{panels}<footer>{esc(RIGHTS)}<br>Final release acceptance remains Step
15.</footer></main>
<script>{script}</script></body></html>"""
