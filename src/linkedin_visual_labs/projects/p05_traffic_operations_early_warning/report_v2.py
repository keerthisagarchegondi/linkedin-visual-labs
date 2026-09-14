"""Portable internal five-tab report using the same 4.C.B visual contract."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .block2 import write_json
from .presentation import TABS
from .presentation_v2 import BUILD, SCENES, STATUS, TOKENS
from .render_v2 import Renderer, artifacts
from .reporting import SCRIPT, validate_report_assets


def document(renderer: Renderer, *, accelerated: bool = False) -> str:
    build_name = "PROJECT6_4.C.C" if accelerated else BUILD
    history_label = "23:15-24:00; trails23:00-24:00" if accelerated else "20:00-24:00"
    cards = "".join(
        f'<div class="kpi" title="{html.escape(detail)}"><small>{label}</small>'
        f"<strong>{value}</strong><span>{detail}</span></div>"
        for label, value, detail in renderer.kpis
    )
    nav = "".join(
        f'<button role="tab" id="tab-{i}" aria-controls="panel-{i}" '
        f'aria-selected="{str(i == 0).lower()}" tabindex="{0 if i == 0 else -1}">{tab}</button>'
        for i, tab in enumerate(TABS)
    )
    decision = """<div class="decision"><div><small>WHAT HAPPENED?</small>
    <h2>TRAFFIC PRESSURE <em>WARNING</em></h2><strong>24:00</strong>
    <p>Original source elapsed time</p></div><div><small>INDEPENDENT QUEUE CHECK</small>
    <h2>CONGESTION<br>NOT CONFIRMED</h2><p>The configured sustained-queue rule was not satisfied.
    This does not prove physical queue absence.</p></div><div><small>CONDITIONAL RESPONSE</small>
    <h2>REVIEW / MONITOR</h2><p>Consider escalating for review. Illustrative prototype action;
    no road control or measured operating impact.</p></div></div>"""
    dashboard = f"""<div class="overview"><figure><img src="assets/scene.png"
    alt="Actual cam_3 vehicles with observed trails, concentration contours and configured
    boundaries">
    <figcaption>Actual source 24:00. History {history_label}; contours count observations,
    not physical density. Anonymous IDs; no face or plate recognition.</figcaption></figure>
    <aside><small>WHY DID THE SYSTEM WARN?</small><h2>Higher accumulation.<br>
    Positive imbalance.<br><em>Continuing discharge.</em></h2><p>Density level, density trend and
    entry-exit imbalance qualified the configured warning. Throughput and movement did not
    establish a decline at onset.</p><div class="kpis">{cards}</div>
    <p class="scope">Fixed 24:00 snapshot. All numeric KPIs use (23:00,24:00] original time.
    Occupancy is the mean of 60 integer-second observed-track counts.</p></aside></div>{decision}"""
    mapping = "".join(
        f"<tr><td>{a:g}-{b:g}s</td><td>{c:g}-{c + b - a:g}s</td><td>{title}</td></tr>"
        for a, b, c, title, _ in SCENES
    )
    playback_description = (
        "Selected excerpts play at1x with explicit cuts. Native10fps frames repeat three times."
    )
    if accelerated:
        from .presentation_v3 import playback_contract

        playback_description = (
            "Excerpts use6-15x speed ramps, followed by a short final hold. "
            "Fifteen sampled presentation frames/second repeat twice for30fps. "
            "Contours use45source seconds of causal history; trails fade over60source seconds."
        )
        mapping = "".join(
            f"<tr><td>{r['display_start']:g}-{r['display_end']:g}s</td>"
            f"<td>{r['source_start']:g}-{r['source_end']:.1f}s</td>"
            f"<td>{r['speed_start']:g}x to {r['speed_end']:g}x</td></tr>"
            for r in playback_contract()["scenes"]
        )
    video = f"""<div class="split"><video controls preload="metadata"
    poster="assets/thumbnail.png" src="assets/project6_linkedin_web.mp4"></video><article>
    <h2>The complete concept in 15 seconds.</h2><p>Camera footage becomes detections, anonymous
    tracks, flow metrics, a pressure warning, an independent queue check and conditional action.</p>
    <h3>30 minutes condensed into 45 seconds</h3><p>{playback_description} Analytics always
    retain original timestamps. The 24:00 KPI snapshot is labeled separately from moving
    footage.</p>
    <table><tr><th>Edit</th><th>Original source seconds</th><th>Scene</th></tr>{mapping}</table>
    <p>Muted comprehension supported. Internal review only; source permission pending.</p>
    </article></div>"""
    method = """<h2>DETECT → TRACK → MEASURE → AGGREGATE → WARN → VALIDATE → ACT</h2>
    <div class="columns"><article><h3>Observed vehicles to operational metrics</h3>
    <p>YOLOX-Nano ONNX detector, CPU runtime and ByteTrack-compatible temporary clip-local tracks.
    Counts use configured reference points inside the zone; entry and exit use eligible unique
    directional crossings. Missing predictions are not occupancy observations.</p>
    <p>Throughput counts eligible exits in (t-60,t]. Occupancy averages 60 integer-second counts.
    Relative movement uses nested medians of image-plane displacement per original second;
    at least ten valid seconds support the rolling index. No calibrated MPH or distance.</p>
    <p>Dwell uses completed eligible entry-to-exit journeys. Incomplete and censored tracks
    do not become completed observations. Dwell is excluded from headline KPIs.</p></article>
    <article><h3>Warning and outcome are separate</h3><p>Warning: at least three of five configured
    signals for 30 seconds; CRITICAL uses four for 60 seconds. Reset requires no more than one
    driver for 15 seconds. Timestamp means persistence completion, never backdating.</p>
    <p>Queue: at least two low-motion tracks, queue-zone occupancy at least three, movement
    index at most 0.005 image diagonals/s, sustained for 120 seconds. No qualifying outcome.
    These are configured assumptions, not a universal congestion definition.</p>
    <p>Formal metric window remains 300s; this historical fast-track analysis uses 60s.</p>
    </article><article><h3>Privacy and visual encoding</h3><p>Vehicle-only classes. No face
    recognition,
    plate OCR, driver identity, persistent IDs or cross-camera lookup. Public metrics are
    aggregate.</p>
    <p>Contours are observation-weighted trajectory concentration. Repeated positions and longer
    tracks contribute more. Equal-length arrows encode image-plane direction, not speed.
    Trails never bridge observation gaps greater than one second.</p>
    <p>Boxes use the most recent accepted observation within 0.4 original seconds. Sparse sampling
    can cause brief positional lag. Dense paths are not duplicate vehicles.</p></article></div>"""
    results = f"""{decision}<div class="columns"><article><h3>At warning onset</h3>
    <p>Mean observed occupancy 3.70; 8 entries and 3 exits, balance +5; throughput 3 eligible
    exits/60s;
    relative movement 0.0113054 image diagonals/s. Numeric scope: (1380,1440].</p>
    <p>Review warranted; congestion not established by the configured outcome. Lead time is null
    and not reportable because there is no qualified queue onset.</p></article>
    <article><h3>Tracking and validation limits</h3><p>Full [0,1800) processing: 178 confirmed track
    IDs, 65 eligible completed journeys. These are not independent accuracy measures or a physical
    vehicle census. Fragmentation, occlusion and incomplete journeys remain limitations.</p>
    <p>Independent computational reconciliation passed. No human-labeled detection/tracking accuracy
    or physical queue-absence validation is established.</p></article>
    <article><h3>False-warning and sensitivity evidence</h3><p>WARNING remained latched for 297s,
    [1440,1737), including hysteresis. Only 53 evaluated ticks fully qualified the warning rule.
    Baseline exposure: 0/60 in-sample evaluable seconds; not false-alarm accuracy.</p>
    <p>Sensitivity warning onset range: 1430-1447 original seconds. This is a configured sensitivity
    sweep, not a confidence interval. No held-out business benefit has been
    measured.</p></article></div>
    <details><summary>Secondary historical comparison and complete metric truth</summary>
    <p>Median 60s mean observed occupancy: 0.7583333 across 60 rolling endpoints [1320,1380), versus
    4.45 across 210 endpoints [1440,1650). Overlapping, unequal windows and different vehicles;
    descriptive comparison only. These are not the 24:00 snapshot.</p>
    <p><a href="assets/presentation_metrics.json">Audited metric records, formulas and upstream
    hashes</a></p>
    <p><a href="assets/release_data.json">Frozen analytical release and classified claims</a></p>
    <p><a href="assets/presentation_manifest.json">Current presentation
    provenance</a></p></details>"""
    about = """<div class="columns"><article><h2>Camera evidence for Operations</h2>
    <p>Project 6 - Traffic Flow Deterioration Early-Warning System. A recorded-analysis portfolio
    prototype explores whether existing camera footage can support explainable operational
    review.</p>
    <p>Operations needs understandable reasons and conditional actions. Engineering needs
    reproducible
    timing and recoverable processing. Analytics needs independent outcomes and reconciled metrics.
    Governance needs privacy, lawful reuse and bounded claims.</p></article><article><h2>Role
    and challenges</h2>
    <p>Project scope spans pipeline design, source review, CPU detection/tracking, temporal metrics,
    rule evaluation, computational validation and evidence-backed visual communication.</p>
    <p>Challenges: occlusions and fragments, defining congestion independently, separating pressure
    from throughput, preserving original time and avoiding mixed-window KPI claims.</p>
    <p>Technology: Python, ONNX Runtime, YOLOX-Nano, ByteTrack-compatible tracking, pandas/Parquet,
    Pillow, NumPy, FFmpeg and portable HTML.</p></article><article><h2>Source, license and
    roadmap</h2>
    <p>AI City Challenge 2021 Track 1, Dataset_A/cam_3.mp4. 30-minute fixed-camera recording.
    No specific road, airport or operating location is asserted.</p>
    <p>PUBLICATION: PENDING_SOURCE_PERMISSION. Internal final-quality review is authorized;
    source-imagery publication is not cleared. This is not live monitoring or production
    deployment.</p>
    <p>Future work: independent annotations, broader episodes, calibration where warranted,
    robustness
    and runtime evaluation. No persistent identity, recognition or enforcement
    workflow.</p></article></div>"""
    sections = "".join(
        f'<section role="tabpanel" id="panel-{i}" aria-labelledby="tab-{i}" '
        f"{'hidden' if i else ''}>{body}</section>"
        for i, body in enumerate((dashboard, video, method, results, about))
    )
    css = f""":root{{--bg:{TOKENS["background_primary"]};--panel:{TOKENS["panel_fill"]};
    --cyan:{TOKENS["trajectory_primary"]};--amber:{TOKENS["warning_active"]};
    --blue:{TOKENS["trajectory_secondary"]};--ink:{TOKENS["text_primary"]};}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
    font:16px/1.45 Arial,sans-serif}}header{{padding:20px 28px 12px;background:#0B1A2A}}
    h1{{font-size:26px;margin:0}}header p{{margin:5px 0;color:#DBE4ED}}
    nav{{display:flex;padding:0 28px;border-bottom:1px solid #667788}}button{{background:none;
    border:0;color:white;font-size:17px;padding:16px 28px;cursor:pointer}}
    button[aria-selected=true]{{border-bottom:3px solid var(--amber);color:var(--amber)}}
    section{{padding:22px
    28px}}[hidden]{{display:none!important}}h2{{font-size:23px;line-height:1.25}}
    h3{{color:var(--cyan)}}em{{font-style:normal;color:var(--amber)}}small{{color:#DBE4ED;
    font-size:12px;letter-spacing:1px}}p{{color:#DBE4ED}}.overview{{display:grid;
    grid-template-columns:minmax(0,1.45fr) minmax(390px,1fr);gap:24px}}figure{{margin:0}}
    figure img{{width:100%;height:495px;object-fit:cover;object-position:center
    53%;border-radius:10px}}
    figcaption{{font-size:12px;color:#DBE4ED;padding:7px 0}}aside h2{{margin:8px 0}}
    aside p{{font-size:14px;margin:10px
    0}}.kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
    .kpi{{border:1px solid #667788;border-radius:8px;padding:9px;background:var(--panel)}}
    .kpi small{{font-size:10px;display:block}}.kpi strong{{display:block;font-size:24px}}
    .kpi span{{font-size:11px;color:#DBE4ED}}.scope{{font-size:12px!important}}
    .decision{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:16px}}
    .decision>div{{padding:16px 20px;border:1px solid #667788;border-top:3px solid var(--amber);
    border-radius:8px;background:var(--panel)}}.decision h2{{margin:7px 0;font-size:21px}}
    .decision strong{{font-size:30px;color:var(--amber)}}.decision p{{font-size:13px;margin:4px 0}}
    .columns{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}
    .columns article{{padding:20px;background:var(--panel);border-top:3px solid var(--blue)}}
    .split{{display:grid;grid-template-columns:460px
    1fr;gap:30px}}video{{width:100%;max-height:730px}}
    table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{text-align:left;
    border-bottom:1px solid #667788;padding:7px}}a{{color:var(--cyan)}}details{{margin-top:20px}}
    footer{{padding:10px 28px;font-size:12px;color:var(--amber)}}
    @media(max-width:900px){{.overview,.columns,.split,.decision{{grid-template-columns:1fr}}
    nav{{overflow:auto;padding:0}}button{{padding:14px}}figure img{{height:auto}}
    .kpis{{grid-template-columns:repeat(2,1fr)}}section{{padding:16px}}h1{{font-size:21px}}}}
    """
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Project 6 - Recorded traffic analysis</title><style>{css}</style></head><body>
    <header><h1>Traffic Flow Deterioration Early-Warning System</h1>
    <p>BUSY TRAFFIC ≠ CONGESTION · Recorded analysis · Internal portfolio prototype</p></header>
    <nav role="tablist" aria-label="Project report">{nav}</nav>{sections}
    <footer>{build_name} · PUBLICATION: {STATUS} · No public clearance or measured impact.</footer>
    <script>{SCRIPT}</script></body></html>"""


def build(renderer: Renderer, *, accelerated: bool = False) -> None:
    report = renderer.output / "report"
    assets = report / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for source, name in (
        (
            renderer.preview / "linkedin_video_frames/03_video_10s_warning_validation.png",
            "thumbnail.png",
        ),
        (renderer.output / "videos/project6_linkedin_web.mp4", "project6_linkedin_web.mp4"),
        (renderer.output / "data/presentation_metrics.json", "presentation_metrics.json"),
        (renderer.output / "data/release_data.json", "release_data.json"),
    ):
        shutil.copyfile(source, assets / name)
    # Save the actual rendered hero alone, rather than a page screenshot as report content.
    history = renderer.tracks[renderer.tracks.source_timestamp.between(1200, 1440)]
    from .render_v2 import density_layer

    renderer.layers[2], _ = density_layer(history)
    renderer.scene_pixels(renderer.raw_frame(1440), 1440, 2).save(assets / "scene.png")
    write_json(assets / "presentation_manifest.json", renderer.manifest())
    (report / "index.html").write_text(
        document(renderer, accelerated=accelerated), encoding="utf-8"
    )
    references = validate_report_assets(report)
    write_json(
        renderer.output / "manifests/report_manifest.json",
        {
            **renderer.manifest(),
            "tabs": list(TABS),
            "assets": references,
            "outputs": artifacts([report / "index.html", *[report / p for p in references]]),
            "screenshots_status": "PENDING_BROWSER_CAPTURE",
        },
    )
    print(json.dumps({"report": str(report / "index.html"), "references": references}))


if __name__ == "__main__":
    build(Renderer(Path.cwd()))
