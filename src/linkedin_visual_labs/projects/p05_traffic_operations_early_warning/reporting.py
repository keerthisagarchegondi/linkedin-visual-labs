"""Portable five-tab evidence report; allowlisted derived assets only."""

from __future__ import annotations

import html
import shutil
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .block2 import write_json
from .evidence import artifact
from .presentation import RIGHTS, TABS, Presentation, captions, clock

STYLE = ""  # Detailed narrative is styled by the shared report design.
SCRIPT = """
const tabs=[...document.querySelectorAll('[role=tab]')];

function select(id){tabs.forEach(b=>{const on=b.id===id;
b.setAttribute('aria-selected',on);

b.tabIndex=on?0:-1;
document.getElementById(b.getAttribute('aria-controls')).hidden=!on;
});
}
tabs.forEach((b,i)=>{b.addEventListener('click',()=>select(b.id));
b.addEventListener('keydown',e=>{
let n=i;
if(e.key==='ArrowRight')n=(i+1)%tabs.length;
else if(e.key==='ArrowLeft')n=(i+tabs.length-1)%tabs.length;

else if(e.key==='Home')n=0;
else if(e.key==='End')n=tabs.length-1;
else return;

e.preventDefault();
select(tabs[n].id);
tabs[n].focus();
});
});

document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{
document.querySelector('video').currentTime=Number(b.dataset.time);
}));

"""


def esc(value: object) -> str:
    return html.escape(str(value))


class AssetParser(HTMLParser):
    """Collect explicit local document references without a browser dependency."""

    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"src", "href", "poster"} and value is not None:
                self.references.append(value)


def validate_report_assets(report: Path) -> list[str]:
    parser = AssetParser()
    parser.feed((report / "index.html").read_text(encoding="utf-8"))
    for value in parser.references:
        path = report / value
        if ":" in value or not path.resolve().is_relative_to(report.resolve()):
            raise ValueError("Nonportable or foreign report asset")
        if not path.is_file():
            raise ValueError(f"Missing report asset: {value}")
    return sorted(set(parser.references))


def card(label: str, value: str, detail: str) -> str:
    return f"""<div class="card"><div class="label">{esc(label)}</div><div
class="big">{esc(value)}</div><p>{esc(detail)}</p></div>"""


def detailed_report_html(p: Presentation) -> str:
    r = p.release
    result = r["result"]
    counts = p.counts
    changes = r["metric_changes"]
    cards = '<div class="grid">' + card("Warning onset", p.warning, "Original source elapsed time")
    cards += card("Visible queue", "Not qualified", "Independent configured outcome")
    cards += (
        card("Lead time", "Not reportable", "No qualifying queue onset; null, never zero")
        + "</div>"
    )
    rows = ""
    for key, label in (
        ("density_window_mean", "Mean zone vehicles /60s"),
        ("throughput", "Eligible exits /60s"),
        ("movement_index", "Image diagonals /second"),
        ("median_completed_dwell_seconds", "Rolling completed dwell /seconds"),
        ("inflow_outflow_imbalance", "Net entries /60s"),
    ):
        values = changes[key]
        cells = [
            "Unavailable" if values[n] is None else f"{values[n]:.4g}"
            for n in ("baseline_median", "screened_interval_median")
        ]
        rows += f"<tr><td>{label}</td><td>{cells[0]}</td><td>{cells[1]}</td></tr>"
    baseline = "-".join(clock(v) for v in p.rules["baseline"])
    comparison = "-".join(clock(v) for v in r["screened_comparison_interval"])
    metrics = f"""<table><thead><tr><th>Metric</th><th>Baseline {baseline}</th><th>Comparison
{comparison}</th></tr></thead><tbody>{rows}</tbody></table><p>Window medians;
comparison interval was source-screened, not a validated degraded label.
Throughput and movement increased, so the evidence is mixed. Baseline dwell is
unsupported. Overlapping windows are not independent vehicles.</p>"""
    recommendation = f"""<div
class="note"><strong>{esc(r["recommendation"]["wording"])}</strong><p>Alternative:
{esc(r["recommendation"]["alternative_action"].title())}. Illustrative
operational response; real facility controls and cause are unknown.</p></div>"""
    dashboard = f"""<h2>Deterioration qualified. The queue outcome did not.</h2><p
class="badge">{esc(result["result_classification"])}</p>{cards}<div class="grid
two spaced"><div class="card"><h3>Why did the warning fire?</h3><p>Density
level, inflow-outflow imbalance and density trend satisfied the configured
persistence rule.</p>{metrics}</div><div class="card"><img class="trajectory"
src="assets/trajectory_map.png" alt="Actual ten-minute trajectories on a
schematic background"></div></div><h3>What should Operations
consider?</h3>{recommendation}<img class="spaced"
src="assets/warning_queue_timeline.png" alt="Original-time warning and
independent queue timelines">"""
    chapters = "".join(
        f'''<button data-time="{i * 5 if i < 9 else 44}">{i * 5 if i < 9 else 44:02d}s ·
{esc(v[0])}</button>'''
        for i, v in enumerate(captions(p))
    )
    video = f"""<h2>A recorded episode, explained in 45 seconds.</h2><video controls
preload="metadata" poster="assets/project6_thumbnail.png"><source
src="assets/project6_linkedin_web.mp4" type="video/mp4"></video><div
class="chapters spaced">{chapters}</div><p>Calculations use original timestamps.
The schematic trajectory animation accelerates a continuous 20:00-30:00
interval; narrative charts summarize the episode. Visual playback never changes
dwell, persistence, warning time or outcome time. No source footage is embedded
or offered for download.</p>"""
    method = f"""<h2>Detect → Track → Measure → Aggregate → Warn → Validate →
Act</h2><div class="grid two"><div class="card"><h3>Source and
execution</h3><p>AI City Challenge 2021 Track 1, cam_3. One stationary 30-minute
historical clip. Internal non-commercial academic analysis is supported; public
source imagery is restricted.</p><p>YOLOX-Nano / CPU ONNX Runtime /
ByteTrack-compatible association. Analytical sampling: 3 FPS, retaining original
timestamps. Vehicle classes only; temporary clip-local tracks.</p></div><div
class="card"><h3>Metrics and eligibility</h3><p>Occupancy counts configured
reference points inside the ROI. Density is a zone vehicle count. Throughput
counts unique eligible exits. Completed entry-to-exit pairs supply dwell;
incomplete tracks are censored. Movement is normalized image-plane displacement,
not road speed.</p><p>60-second fast-track window; formal 300-second contract
retained. No physical-distance calibration.</p></div><div class="card"><h3>Two
independent rules</h3><p>Warning: {p.rules["warning"]["minimum_drivers"]}
leading drivers persist for {p.rules["warning"]["persistence_seconds"]} seconds.
NORMAL, WATCH, WARNING and CRITICAL use configured transitions and reset
rules.</p><p>Queue: count ≥ {p.rules["queue"]["queue_count"]}, zone occupancy
≥ {p.rules["queue"]["zone_occupancy"]}, movement ≤
{p.rules["queue"]["movement_ceiling"]} for
{p.rules["queue"]["persistence_seconds"]} seconds. This persistence is a
configured filter, not a measured signal cycle.</p></div><div
class="card"><h3>Validation and privacy</h3><p>Independent scalar recomputation
reconciles observations, crossings, metrics and persistence-completion
timestamps. No human-labelled detector/tracker accuracy is
established.</p><p>High candidate-track fragmentation limits interpretation.
Confirmed tracks are admitted selectively; retrospective journey screening is
not prospective performance validation. No face recognition, plate OCR,
persistent identity or cross-camera tracking.</p></div></div>"""
    sensitivity = p.summary()["sensitivity_warning_range"]
    false = result["baseline_false_warning"]
    results = (
        f"""<h2>Evidence, including the missing outcome.</h2>{cards}<p
class="badge">{esc(result["result_classification"])}</p><div class="grid
spaced">"""
        + card(
            "Baseline warnings",
            str(false["baseline_false_warning_count"]),
            f"""In-sample only: {false["warning_seconds"]}/{false["evaluable_seconds"]}
evaluable seconds; not held-out accuracy.""",
        )
        + card(
            "Unmatched warning",
            f"{r['unmatched_warning']['warning_state_seconds']} seconds",
            "No target queue outcome qualified.",
        )
        + card(
            "Sensitivity onset",
            f"{sensitivity[0]:g}-{sensitivity[1]:g}s",
            "Queue onset remained null in the frozen sensitivity runs.",
        )
        + f"""</div><div class="note spaced">This result does not prove no physical queue
existed; it means the configured independent outcome rule was not satisfied by
the available evidence. Evaluation:
{clock(p.rules["evaluation_start"])}-{clock(p.rules["evaluation_end_exclusive"])}.</div><h3>Track
quality — full episode</h3><p>{counts["candidate_tracks"]} candidates →
{counts["eligible_confirmed_tracks"]} confirmed →
{counts["completed_dwell_samples"]} completed journeys.
{counts["incomplete_journeys_excluded_from_dwell"]} incomplete journeys excluded
from completed dwell. {counts["eligible_entries"]} entries /
{counts["eligible_exits"]} exits. Independent computation: PASS. Independent
accuracy: not established.</p>{metrics}<img src="assets/metric_trends.png"
alt="Metric trends with original-time baseline"><p><a
href="report_data.json">Structured report evidence</a> · <a
href="evidence_index.json">Input hash index</a> · <a
href="claims.json">Classified claim bindings</a></p>"""
    )
    about = (
        """<h2>From a camera to a reviewable decision.</h2><div class="grid two"><div
class="card"><h3>Business question</h3><p>Operations often sees an obvious queue
before it gets a usable warning. This prototype asks whether ordinary camera
evidence can support an earlier, explainable signal.</p><h3>Stakeholder
perspectives</h3><p>Operations needs a reason to investigate; engineering needs
reproducible processing; analytics needs independent outcomes; governance needs
traceable claims and privacy.</p><h3>My role</h3><p>Project design, source
screening, CPU pipeline, metric contracts, validation, visual storytelling and
evidence packaging.</p></div><div class="card"><h3>Technical
challenges</h3><p>Occlusion and fragmented tracks, perspective without physical
calibration, short baseline support, separate warning and queue definitions, and
truthful null results.</p><h3>Stack</h3><p>Python, ONNX Runtime, YOLOX-Nano,
ByteTrack-compatible tracking, Parquet, Pillow, packaged FFmpeg and portable
HTML.</p></div><div class="card"><h3>Source, rights and privacy</h3><p>"""
        + esc(RIGHTS)
        + """</p><p>No identifiable faces or plates are exposed. No raw footage, private
license evidence, model weights or unrestricted track tables are included in
this report.</p></div><div class="card"><h3>Limitations and roadmap</h3><p>One
historical camera, high candidate fragmentation, limited baseline, no
independent detection/tracking accuracy and no established physical queue onset.
No causal intervention impact is established.</p><p>Next research: independently
label queue onset, lengthen the baseline, evaluate stronger tracking, calibrate
perspective, test other cameras separately, map actual facility levers and
consider a controlled pilot. These are future work.</p></div></div>"""
    )
    bodies = [dashboard, video, method, results, about]
    nav = "".join(
        f'''<button role="tab" id="tab-{tab.lower()}" aria-controls="panel-{tab.lower()}"
aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}">{tab}</button>'''
        for i, tab in enumerate(TABS)
    )
    panels = "".join(
        f"""<section role="tabpanel" id="panel-{tab.lower()}"
aria-labelledby="tab-{tab.lower()}" {"hidden" if i else ""}>{body}</section>"""
        for i, (tab, body) in enumerate(zip(TABS, bodies, strict=True))
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1"><title>Project 6 — Traffic
Operations Early-Warning
System</title><style>{STYLE}</style></head><body><main><header><p
class="eyebrow">PROJECT 6 / RECORDED ANALYSIS / PORTFOLIO
PROTOTYPE</p><h1>Traffic Operations<br>Early-Warning System</h1><p>A warning is
evidence to investigate. An early-warning claim needs an independent
outcome.</p></header><nav role="tablist" aria-label="Report
sections">{nav}</nav>{panels}<footer>{esc(RIGHTS)}<br>Local visual package.
Final release acceptance remains Step
15.</footer></main><script>{SCRIPT}</script></body></html>"""


def report_html(p: Presentation) -> str:
    from .report_design import build_report

    return build_report(p, detailed_report_html(p), SCRIPT)


def write_report(p: Presentation) -> dict[str, Any]:
    from .visualization import traffic_hero

    report = p.output / "report"
    assets = report / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    traffic_hero(p, 1.0).save(assets / "flow_map.png")
    names = [
        "trajectory_map.png",
        "project6_thumbnail.png",
        "metric_trends.png",
        "warning_queue_timeline.png",
    ]
    for name in names:
        shutil.copyfile(p.output / "images" / name, assets / name)
    shutil.copyfile(
        p.output / "videos/project6_linkedin_web.mp4", assets / "project6_linkedin_web.mp4"
    )
    (report / "index.html").write_text(report_html(p), encoding="utf-8")
    write_json(report / "report_data.json", p.summary())
    # This extended index references the original immutable index and validated derivatives.
    write_json(report / "evidence_index.json", p.index)
    bindings = [
        {
            "claim_id": "P6-B4-" + key.upper(),
            "classification": "DERIVED",
            "selector": key,
            "evidence": artifact(p.root, p.output / "data/release_data.json"),
            "approval_scope": "Explicit Block 4 derived-only rendering authorization",
            "caveat": "Configured model-derived evidence; no accuracy or impact claim",
        }
        for key in ("result", "metric_changes", "eligibility", "unmatched_warning")
    ]
    write_json(
        report / "claims.json", {"release_claims": p.release["claims"], "render_bindings": bindings}
    )
    validated_assets = validate_report_assets(report)
    files = sorted(v for v in report.rglob("*") if v.is_file() and v.name != "report_manifest.json")
    manifest = {
        "schema_version": "1.0",
        "tabs": list(TABS),
        "source_pixels": False,
        "portable": True,
        "validated_assets": validated_assets,
        "final_release_approved": False,
        "inputs": p.index,
        "outputs": [artifact(p.root, path) for path in files],
    }
    write_json(report / "report_manifest.json", manifest)
    return manifest
