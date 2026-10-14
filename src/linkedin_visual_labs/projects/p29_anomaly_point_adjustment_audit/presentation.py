"""Step 5 presentation artifacts rendered exclusively from frozen release data."""

# ruff: noqa: E501, RUF001

from __future__ import annotations

import base64
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from PIL import Image, ImageColor, ImageDraw, ImageFont

from .config import PROJECT_ID, repository_root

matplotlib.use("Agg")

FIGURE_STEMS = (
    "01_same_alerts_different_f1",
    "02_event_length_sensitivity",
    "03_probability_validation",
)
DASHBOARD_TABS = (
    "The Story",
    "See the Mechanism",
    "The Experiment",
    "Results",
    "45s Video",
    "Why It Matters",
)
VIDEO_SIZE = (1080, 1350)
VIDEO_FPS = 30
VIDEO_SECONDS = 45
SAFE_BOX = (96, 120, 984, 1200)


def presentation_root() -> Path:
    """Return the ignored Step 5 presentation output root."""
    return repository_root() / "outputs" / PROJECT_ID


def release_data_path() -> Path:
    return presentation_root() / "data" / "release_data.json"


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_release(path: Path | None = None) -> dict[str, Any]:
    """Load the fixed Step 4 input and reject non-frozen input."""
    source = path or release_data_path()
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("project_id") != PROJECT_ID:
        raise ValueError("release data is not a Project 9 object")
    if (
        data.get("scientific_results_status") != "FROZEN"
        or data.get("release_data_status") != "FROZEN"
    ):
        raise ValueError("Step 5 requires frozen release data")
    return data


def _primary(release: dict[str, Any]) -> dict[str, Any]:
    primary = release.get("primary_condition")
    if not isinstance(primary, dict):
        raise ValueError("frozen release data does not have a primary condition")
    return primary


def _f1(condition: dict[str, Any], key: str) -> float:
    metric = condition.get(key)
    if not isinstance(metric, dict) or not isinstance(metric.get("mean"), int | float):
        raise ValueError(f"missing frozen {key}.mean")
    return float(metric["mean"])


def _save_figure(figure: Figure, stem: str, figures_dir: Path) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    png, pdf = figures_dir / f"{stem}.png", figures_dir / f"{stem}.pdf"
    figure.savefig(png, dpi=180, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return [png, pdf]


def render_figures(release: dict[str, Any], root: Path | None = None) -> list[Path]:
    """Render the three contract figures without deriving any new result values."""
    figures_dir = (root or presentation_root()) / "figures"
    primary = _primary(release)
    raw, adjusted = _f1(primary, "raw_f1"), _f1(primary, "adjusted_f1")
    outputs: list[Path] = []
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(
        ["Raw pointwise", "Point-adjusted"], [raw, adjusted], color=["#5D7185", "#0A8F87"]
    )
    ax.set_ylim(0, 1)
    ax.set_ylabel("Frozen mean F1")
    ax.set_title("Same random alerts, different scoring credit")
    for bar, value in zip(bars, (raw, adjusted), strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.025,
            f"{value:.3f}",
            ha="center",
            weight="bold",
        )
    ax.text(
        0.5,
        -0.2,
        "Primary condition: q=0.01, event length=200, 2,000 paired repetitions",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
    )
    outputs.extend(_save_figure(fig, FIGURE_STEMS[0], figures_dir))
    sweep = release.get("event_length_sweep_q_0_01")
    if not isinstance(sweep, list) or not all(isinstance(item, dict) for item in sweep):
        raise ValueError("frozen event-length sweep is unavailable")
    ordered = sorted(sweep, key=lambda item: int(item["event_length"]))
    lengths = [int(item["event_length"]) for item in ordered]
    adjusted_values = [_f1(item, "adjusted_f1") for item in ordered]
    raw_values = [_f1(item, "raw_f1") for item in ordered]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(lengths, raw_values, marker="o", label="Raw pointwise F1", color="#5D7185")
    ax.plot(lengths, adjusted_values, marker="o", label="Point-adjusted F1", color="#0A8F87")
    ax.set_xscale("log")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Event length (timestamps; log scale)")
    ax.set_ylabel("Frozen mean F1")
    ax.set_title("Event length changes point-adjusted credit")
    ax.legend(frameon=False)
    outputs.extend(_save_figure(fig, FIGURE_STEMS[1], figures_dir))
    observed = [float(item["adjusted_recall_mean"]) for item in ordered]
    analytical = [float(item["analytical_expected_adjusted_recall"]) for item in ordered]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(lengths, observed, marker="o", label="Monte Carlo adjusted recall", color="#0A8F87")
    ax.plot(
        lengths,
        analytical,
        marker="s",
        linestyle="--",
        label="Frozen analytical expectation",
        color="#E76F51",
    )
    ax.set_xscale("log")
    ax.set_ylim(0, 1)
    ax.set_xlabel("Event length (timestamps; log scale)")
    ax.set_ylabel("Probability / recall")
    ax.set_title("Observed event hits follow the declared Bernoulli model")
    ax.legend(frameon=False)
    outputs.extend(_save_figure(fig, FIGURE_STEMS[2], figures_dir))
    return outputs


def _inline_image(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _event_sweep(release: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the frozen q=0.01 event-length rows in display order."""
    sweep = release.get("event_length_sweep_q_0_01")
    if not isinstance(sweep, list) or not all(isinstance(item, dict) for item in sweep):
        raise ValueError("frozen q=0.01 event-length sweep is unavailable")
    return sorted(sweep, key=lambda item: int(item["event_length"]))


def render_dashboard(release: dict[str, Any], root: Path | None = None) -> Path:
    """Create an offline dashboard with the six required public-facing tabs."""
    target_root = root or presentation_root()
    figures = target_root / "figures"
    primary = _primary(release)
    raw, adjusted = _f1(primary, "raw_f1"), _f1(primary, "adjusted_f1")
    delta = float(primary["delta_f1"]["mean"])
    hit = float(primary["analytical_event_hit_probability"])
    probability = f"{hit * 100:.1f}%"
    rows = "".join(
        f"<tr><td>{int(row['event_length'])}</td><td>{_f1(row, 'raw_f1'):.3f}</td>"
        f"<td>{_f1(row, 'adjusted_f1'):.3f}</td><td>+{float(row['delta_f1']['mean']):.3f}</td>"
        f"<td>{float(row['analytical_event_hit_probability']) * 100:.1f}%</td></tr>"
        for row in _event_sweep(release)
    )
    figure_cards = "".join(
        f'<article class="figure"><img alt="{stem}" src="data:image/png;base64,{_inline_image(figures / (stem + ".png"))}"></article>'
        for stem in FIGURE_STEMS
    )
    video = target_root / "video" / "project9_linkedin_45s.mp4"
    video_data = _inline_image(video) if video.is_file() else ""
    buttons = "".join(
        f'<button class="tabbtn{" active" if index == 0 else ""}" data-tab="tab{index}">{tab}</button>'
        for index, tab in enumerate(DASHBOARD_TABS)
    )
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Project 9 — Point-adjustment audit</title><style>:root{{--ink:#f7fbff;--muted:#a7b6cc;--teal:#4ee0c3;--amber:#f4b84b;--red:#ec6473;--line:#294364}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 85% 0,#16345f,#07101f 42%,#050a14);color:var(--ink);font:17px/1.55 system-ui,sans-serif}}body:before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.25;background:repeating-linear-gradient(62deg,transparent 0 58px,#10254a 60px 84px,transparent 86px 155px)}}main{{max-width:1240px;margin:auto;padding:24px;position:relative}}.top,.tabs{{display:flex;gap:10px;align-items:center}}.top{{justify-content:space-between}}.brand,.eyebrow{{color:var(--teal);font-size:13px;font-weight:900;letter-spacing:.1em}}.badge{{border:1px solid #876421;border-radius:999px;color:var(--amber);padding:7px 11px;font-size:12px;font-weight:850}}.hero,.card{{background:linear-gradient(180deg,rgba(20,37,67,.96),rgba(9,18,34,.96));border:1px solid var(--line);border-radius:24px;box-shadow:0 20px 60px #0005}}.hero{{padding:42px;margin:20px 0}}h1{{font-size:clamp(42px,6vw,74px);line-height:.96;letter-spacing:-.055em;margin:12px 0 20px}}h2{{font-size:29px;line-height:1.1}}.lead,.muted{{color:var(--muted)}}.lead{{font-size:20px}}.hook{{color:var(--teal);font-weight:900;font-size:26px}}.tabs{{position:sticky;top:0;z-index:2;overflow:auto;padding:14px 0;background:#07101fee;backdrop-filter:blur(12px)}}.tabbtn{{white-space:nowrap;border:1px solid var(--line);border-radius:999px;background:#0b172b;color:var(--muted);padding:10px 16px;font-weight:850;cursor:pointer}}.tabbtn.active{{background:var(--teal);color:#061018}}.tab{{display:none}}.tab.active{{display:block}}.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}}.card{{padding:24px}}.s12{{grid-column:span 12}}.s6{{grid-column:span 6}}.s4{{grid-column:span 4}}.story,.compare,.flow{{display:grid;gap:14px}}.story{{grid-template-columns:repeat(3,1fr)}}.compare{{grid-template-columns:1fr 1fr}}.flow{{grid-template-columns:repeat(5,1fr)}}.box{{background:#09162a;border:1px solid var(--line);border-radius:18px;padding:18px}}.num{{display:grid;place-items:center;width:34px;height:34px;border-radius:50%;background:var(--teal);color:#061018;font-weight:900}}.timeline{{height:200px;background:#071323;border:1px solid var(--line);border-radius:18px;position:relative;overflow:hidden}}.track{{position:absolute;left:7%;right:7%;top:50%;height:8px;background:#627494}}.event,.fill{{position:absolute;left:27%;width:50%;top:calc(50% - 43px);height:86px;border-radius:22px}}.event{{background:#3c2730;border:2px solid var(--red)}}.fill{{background:#4ee0c344;border:2px solid var(--teal)}}.hit{{position:absolute;left:59%;top:calc(50% - 13px);width:26px;height:26px;border-radius:50%;background:var(--teal);box-shadow:0 0 0 13px #4ee0c322}}.metric{{font-size:58px;font-weight:900}}.teal{{color:var(--teal)}}.amber{{color:var(--amber)}}.figure{{margin:12px 0;padding:12px;background:#09162a;border:1px solid var(--line);border-radius:18px}}img,video{{width:100%;display:block;border-radius:12px}}table{{width:100%;border-collapse:collapse;min-width:650px}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:right}}th:first-child,td:first-child{{text-align:left}}.scroll{{overflow:auto}}footer{{padding:30px 0;color:var(--muted);font-size:13px}}@media(max-width:850px){{.s6,.s4{{grid-column:span 12}}.story,.compare,.flow{{grid-template-columns:1fr}}.hero{{padding:28px}}}}</style></head><body><main><div class="top"><b class="brand">LINKEDIN VISUAL LABS • PROJECT 9</b><b class="badge">FROZEN REPRODUCIBLE STUDY</b></div><header class="hero"><div class="eyebrow">A MEASUREMENT PROBLEM, NOT A MODEL DEMO</div><h1>Can a scoring rule make a weak detector look good?</h1><p class="lead">A controlled synthetic audit of point adjustment, using frozen paired random alerts.</p><p class="hook">THE ALERTS STAYED THE SAME. THE REPORTED F1 CHANGED.</p></header><nav class="tabs">{buttons}</nav><section id="tab0" class="tab active"><div class="grid"><article class="card s12"><div class="eyebrow">IMAGINE JUDGING A SMOKE ALARM</div><h2>One beep during a long fire can receive full-event credit.</h2><p class="lead">Raw credit recognizes only what was detected; a generous rule can credit an entire event after one alert touches it.</p></article><article class="card s12"><div class="story"><div class="box"><div class="num">1</div><h3>ANOMALY DETECTOR</h3><p class="muted">Flags unusual timestamps.</p></div><div class="box"><div class="num">2</div><h3>ANOMALY EVENT</h3><p class="muted">A contiguous anomalous run.</p></div><div class="box"><div class="num">3</div><h3>THE SCORING QUESTION</h3><p class="muted">How much credit should one touch earn?</p></div></div></article></div></section><section id="tab1" class="tab"><div class="grid"><article class="card s12"><div class="eyebrow">SAME ALERT • TWO EVALUATIONS</div><h2>THE PREDICTIONS DID NOT CHANGE. ONLY THE EVALUATION CHANGED.</h2><div class="compare"><div class="box"><h3>RAW POINTWISE SCORING</h3><div class="timeline"><div class="track"></div><div class="event"></div><div class="hit"></div></div><p class="muted">Credit only the timestamp actually predicted.</p></div><div class="box"><h3>POINT-ADJUSTED SCORING</h3><div class="timeline"><div class="track"></div><div class="event"></div><div class="fill"></div><div class="hit"></div></div><p class="muted">The same touch receives event-level credit under the declared rule.</p></div></div></article><article class="card s12"><h2 class="teal">P(hit event) = 1 − (1 − q)^L</h2><p>At frozen primary L={int(primary["event_length"])}, q={primary["q"]:.2%}, analytical P(hit event) = <b class="teal">{probability}</b>.</p></article></div></section><section id="tab2" class="tab"><div class="grid"><article class="card s12"><div class="eyebrow">CONTROLLED, PAIRED DESIGN</div><h2>What Project 9 actually tests</h2><div class="flow">{"".join(f'<div class="box"><div class="num">{i}</div><b>{x}</b><p class="muted">{y}</p></div>' for i, (x, y) in enumerate((("Generate random alerts", "Label-independent."), ("Freeze predictions", "Same alerts twice."), ("Score twice", "Raw and adjusted."), ("Change event length", "Controlled grid."), ("Validate the math", "Monte Carlo + analytical.")), 1))}</div></article><article class="card s12"><p class="lead">20,000 timestamps · 1,000 anomalous timestamps · 5% prevalence · L=1, 5, 10, 20, 50, 100, 200, 500, 1000 · q=0.001, 0.005, 0.01, 0.05, 0.10 · 2,000 repetitions · 45 conditions.</p><p class="hook">PRIMARY: L=200, q=0.01</p><p class="muted">No surveys, interviews, human participants, trained-detector comparison, “random beats AI” claim, or “all metrics are broken” claim.</p></article></div></section><section id="tab3" class="tab"><div class="grid"><article class="card s12"><div class="eyebrow">FROZEN HEADLINE RESULT</div><h2>SAME RANDOM ALERTS. DIFFERENT REPORTED F1.</h2><div class="compare"><div class="box"><span class="muted">RAW POINTWISE F1</span><div class="metric">{raw:.3f}</div></div><div class="box"><span class="muted">POINT-ADJUSTED F1</span><div class="metric teal">{adjusted:.3f}</div></div></div><p class="hook amber">ΔF1 = +{delta:.3f} · L=200 · q=1% · 2,000 paired runs</p></article><article class="card s12"><h2>Event-length sensitivity at q = 0.01</h2><div class="scroll"><table><thead><tr><th>Event length</th><th>Raw F1</th><th>Adjusted F1</th><th>ΔF1</th><th>Analytical P(hit)</th></tr></thead><tbody>{rows}</tbody></table></div></article><article class="card s12">{figure_cards}</article></div></section><section id="tab4" class="tab"><div class="grid"><article class="card s12"><div class="eyebrow">45-SECOND EXPLAINER</div><h2>Can a stranger understand the project in 45 seconds?</h2><video controls playsinline src="data:video/mp4;base64,{video_data}"></video><p class="muted">Smoke alarm → anomaly event → raw scoring → point adjustment → long events → frozen result and limitations.</p></article></div></section><section id="tab5" class="tab"><div class="grid"><article class="card s12"><div class="eyebrow">WHY IT MATTERS</div><h2>The skill demonstrated is not “I built an anomaly detector.”</h2><p class="hook">It is: “I audited the ruler used to judge a model.”</p><p class="lead">Measurement design matters in analytics, fraud, forecasting, recommendations, experiments, and ML benchmarking. This controlled study does not empirically study each domain.</p></article><article class="card s12"><div class="story"><div class="box"><b>45s VIDEO</b></div><div class="box"><b>STORY-FIRST HTML</b></div><div class="box"><b>VALIDATED FIGURES</b></div></div></article></div></section><footer>Frozen release data only · synthetic Monte Carlo study · no tracker · no backend · no external CDN.</footer></main><script>const b=[...document.querySelectorAll('.tabbtn')],p=[...document.querySelectorAll('.tab')];b.forEach(x=>x.onclick=()=>{{b.forEach(y=>y.classList.remove('active'));p.forEach(y=>y.classList.remove('active'));x.classList.add('active');document.getElementById(x.dataset.tab).classList.add('active')}});</script></body></html>"""
    html = html.replace(
        "45-SECOND EXPLAINER</div><h2>Can a stranger understand the project in 45 seconds?</h2>",
        "45-SECOND CINEMATIC EXPLAINER</div><h2>From one alert to the full event-length pattern.</h2>",
    ).replace(
        "Smoke alarm → anomaly event → raw scoring → point adjustment → long events → frozen result and limitations.",
        "Smoke-alarm hook → anomaly translation → identical alerts / two scores → event-hit probability → paired experiment → frozen primary result → event-length pattern → interpretation, limits, and conclusion.",
    )
    output = target_root / "dashboard" / "project9_anomaly_evaluation.html"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidate = Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf")
    return ImageFont.truetype(candidate, size) if candidate.exists() else ImageFont.load_default()


def _wrap(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    width: int,
) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _video_frame(title: str, body: str, metric: str, second: int) -> np.ndarray:
    image = Image.new("RGB", VIDEO_SIZE, "#07101F")
    draw = ImageDraw.Draw(image)
    offset = (second * 17) % 190
    for x in range(-190 + offset, VIDEO_SIZE[0] + 190, 190):
        draw.polygon(((x, 0), (x + 46, 0), (x + 410, 1350), (x + 364, 1350)), fill="#0C1B36")
    draw.rounded_rectangle((96, 120, 512, 168), radius=20, fill="#352B13", outline="#866522")
    draw.text((120, 132), "FROZEN REPRODUCIBLE STUDY", font=_font(18, True), fill="#F4B84B")
    draw.rectangle((96, 192, 984, 204), fill="#4EE0C3")
    heading, text = _font(62, True), _font(35)
    metric_font = _font(56 if len(metric) > 20 else 82, True)
    y = 250
    for line in _wrap(draw, title, heading, 888):
        draw.text((96, y), line, font=heading, fill="white")
        y += 72
    y += 35
    for line in _wrap(draw, body, text, 888):
        draw.text((96, y), line, font=text, fill="#D8E8F0")
        y += 49
    if metric:
        bbox = draw.textbbox((0, 0), metric, font=metric_font)
        draw.rounded_rectangle(
            (96, 795, 984, 1008), radius=28, fill="#101F39", outline="#294364", width=3
        )
        pulse = 8 + (second % 5) * 3
        draw.ellipse((520 - pulse, 850 - pulse, 520 + pulse, 850 + pulse), fill="#4EE0C3")
        draw.text(((1080 - (bbox[2] - bbox[0])) / 2, 875), metric, font=metric_font, fill="#4EE0C3")
    draw.line((130, 1070, 950, 1070), fill="#627494", width=7)
    draw.rounded_rectangle(
        (405, 1027, 750, 1113), radius=20, fill="#3C2730", outline="#EC6473", width=3
    )
    draw.ellipse((595, 1048, 635, 1088), fill="#4EE0C3")
    draw.text(
        (96, 1150),
        "Project 9 · synthetic Monte Carlo research artifact",
        font=_font(24),
        fill="#9FB3C8",
    )
    draw.rectangle((96, 1190, 984, 1206), fill="#274C77")
    draw.rectangle((96, 1190, 96 + int(888 * (second + 1) / VIDEO_SECONDS), 1206), fill="#4EE0C3")
    return np.asarray(image)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a normalized animation value."""
    return max(low, min(high, value))


def _smoothstep(value: float) -> float:
    """Return a continuously differentiable easing value with exact endpoints."""
    value = _clamp(value)
    return value * value * (3.0 - 2.0 * value)


def _ease_out_cubic(value: float) -> float:
    """Return a smooth decelerating easing value with exact endpoints."""
    return 1.0 - (1.0 - _clamp(value)) ** 3


def _beat_alpha(time_seconds: float, start: float, end: float, overlap: float = 0.55) -> float:
    """Return continuous opacity for a beat with entry and exit overlap."""
    return _smoothstep((time_seconds - start) / overlap) * (
        1.0 - _smoothstep((time_seconds - (end - overlap)) / overlap)
    )


def _layer_text(
    image: Image.Image,
    position: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    alpha: float,
    width: int = 860,
) -> None:
    """Draw wrapped text through a translucent layer without quantizing motion state."""
    layer = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    y = position[1]
    rgba = (*ImageColor.getrgb(fill), round(255 * _clamp(alpha)))
    for line in _wrap(draw, text, font, width):
        draw.text((round(position[0]), round(y)), line, font=font, fill=rgba)
        y += draw.textbbox((0, 0), line, font=font)[3] + 10
    image.alpha_composite(layer)


def _cinematic_frame(release: dict[str, Any], time_seconds: float) -> np.ndarray:
    """Render one continuously interpolated, evidence-bound cinematic video frame."""
    primary = _primary(release)
    raw, adjusted = _f1(primary, "raw_f1"), _f1(primary, "adjusted_f1")
    delta = float(primary["delta_f1"]["mean"])
    hit = float(primary["analytical_event_hit_probability"])
    sweep = _event_sweep(release)
    image = Image.new("RGBA", VIDEO_SIZE, "#07101f")
    draw = ImageDraw.Draw(image)
    drift = 38.0 * math.sin(time_seconds * 0.22)
    for x in range(-220, 1300, 180):
        px = x + drift
        draw.polygon(((px, 0), (px + 50, 0), (px + 460, 1350), (px + 410, 1350)), fill="#0b1c38")
    for y in range(180, 1280, 140):
        draw.line((80, y + drift * 0.12, 1000, y - drift * 0.12), fill="#153356", width=1)
    draw.rounded_rectangle(
        (96, 120, 490, 168), radius=20, fill="#332a14", outline="#866522", width=2
    )
    draw.text((120, 132), "FROZEN REPRODUCIBLE STUDY", font=_font(18, True), fill="#f4b84b")
    draw.rectangle((96, 192, 984, 202), fill="#4ee0c3")
    title_font, body_font = _font(58, True), _font(31)

    beats = (
        (
            0.0,
            5.4,
            "ONE ALERT. HOW MUCH CREDIT SHOULD IT GET?",
            "A long red event receives one teal alert—then the scoring credit expands.",
            "hook",
        ),
        (
            4.8,
            10.4,
            "FROM SMOKE ALARM TO ANOMALY EVENT",
            "The same time-series alert can be scored pointwise or with point adjustment.",
            "mechanism",
        ),
        (
            9.8,
            16.3,
            "THE ALERTS DIDN'T CHANGE. THE SCORE DID.",
            "Raw scoring credits the touch. Point adjustment gives event-wide credit under the declared rule.",
            "split",
        ),
        (
            15.7,
            22.3,
            "WHY EVENT LENGTH MATTERS",
            "Longer events create more chances for random label-independent alerts to touch an event.",
            "probability",
        ),
        (
            21.7,
            28.3,
            "WHAT PROJECT 9 TESTED",
            "Freeze one alert vector. Score it twice. Vary event length and alert probability. Validate against math.",
            "pipeline",
        ),
        (
            27.7,
            34.3,
            "SAME RANDOM ALERTS. DIFFERENT REPORTED F1.",
            "Primary frozen condition: L=200, q=1%, 2,000 paired runs.",
            "result",
        ),
        (
            33.7,
            39.5,
            "THE PATTERN EXPLAINS THE RESULT",
            "At q=1%, raw F1 stays low while adjusted F1 rises with event length.",
            "curve",
        ),
        (
            38.9,
            43.4,
            "WHAT IT SHOWS — AND WHAT IT DOES NOT",
            "Metric design can materially change this synthetic evaluation; it is not a detector benchmark.",
            "limits",
        ),
        (
            42.8,
            45.0,
            "PROJECT 9",
            "THE ALERTS STAYED THE SAME. THE EVALUATION CHANGED THE STORY.",
            "end",
        ),
    )
    for start, end, title, body, kind in beats:
        alpha = _beat_alpha(time_seconds, start, end)
        if alpha <= 0.001:
            continue
        progress = _ease_out_cubic((time_seconds - start) / 0.7)
        offset_y = 26.0 * (1.0 - progress)
        _layer_text(image, (96.0, 250.0 + offset_y), title, title_font, "#f7fbff", alpha)
        _layer_text(image, (96.0, 425.0 + offset_y), body, body_font, "#c9d8e8", alpha)
        if kind in {"hook", "mechanism", "split"}:
            event_left, event_width = 165.0, 750.0
            event_top, event_bottom = 720.0, 820.0
            draw.rounded_rectangle(
                (
                    round(event_left),
                    round(event_top),
                    round(event_left + event_width),
                    round(event_bottom),
                ),
                radius=34,
                fill="#47252e",
                outline="#ec6473",
                width=3,
            )
            alert_x = event_left + event_width * (0.34 + 0.05 * math.sin(time_seconds * 1.7))
            pulse = 14.0 + 9.0 * (0.5 + 0.5 * math.sin(time_seconds * 4.0))
            draw.ellipse(
                (
                    round(alert_x - pulse),
                    round(770 - pulse),
                    round(alert_x + pulse),
                    round(770 + pulse),
                ),
                fill="#4ee0c3",
            )
            fill_alpha = alpha * (
                _smoothstep((time_seconds - 1.5) / 1.4)
                if kind == "hook"
                else _smoothstep((time_seconds - 11.1) / 1.7)
            )
            if kind != "hook" and time_seconds < 11.1:
                fill_alpha = 0.0
            if fill_alpha > 0:
                overlay = Image.new("RGBA", VIDEO_SIZE, (0, 0, 0, 0))
                odraw = ImageDraw.Draw(overlay)
                odraw.rounded_rectangle(
                    (
                        round(event_left),
                        round(event_top),
                        round(event_left + event_width * fill_alpha),
                        round(event_bottom),
                    ),
                    radius=34,
                    fill=(78, 224, 195, round(150 * fill_alpha)),
                )
                image.alpha_composite(overlay)
        elif kind == "probability":
            lengths = [1, 5, 20, 100, int(primary["event_length"])]
            p = _smoothstep((time_seconds - start) / (end - start))
            drawn = max(1, math.ceil(p * len(lengths)))
            for index, length in enumerate(lengths[:drawn]):
                x = 130 + index * 175
                probability = 1.0 - (1.0 - float(primary["q"])) ** length
                bar_height: float = 70 + 260 * probability
                draw.rounded_rectangle(
                    (x, 1010 - bar_height, x + 105, 1010), radius=16, fill="#4ee0c3"
                )
                draw.text((x, 1030), f"L={length}", font=_font(22, True), fill="#c9d8e8")
                draw.text(
                    (x, 980 - bar_height),
                    f"{probability:.0%}",
                    font=_font(22, True),
                    fill="#f4b84b",
                )
            _layer_text(
                image,
                (96.0, 650.0),
                "P(hit) = 1 − (1 − q)^L   •   q = 1%",
                _font(36, True),
                "#4ee0c3",
                alpha,
            )
        elif kind == "pipeline":
            labels = (
                "RANDOM\nALERTS",
                "FREEZE\nPREDICTIONS",
                "RAW + PA\nSCORES",
                "VARY L / q",
                "CHECK\nMATH",
            )
            p = _smoothstep((time_seconds - start) / 3.5)
            for index, label in enumerate(labels):
                local = _smoothstep(p * len(labels) - index)
                pipeline_x = 90.0 + index * 195.0 + 22.0 * (1.0 - local)
                draw.rounded_rectangle(
                    (round(pipeline_x), 750, round(pipeline_x + 165), 915),
                    radius=24,
                    fill="#102542",
                    outline="#35577a",
                    width=2,
                )
                for line_index, line in enumerate(label.split("\n")):
                    draw.text(
                        (round(pipeline_x + 18), 790 + line_index * 35),
                        line,
                        font=_font(20, True),
                        fill="#4ee0c3",
                    )
                if index < len(labels) - 1 and local > 0:
                    draw.line(
                        (round(pipeline_x + 166), 832, round(pipeline_x + 186), 832),
                        fill="#f4b84b",
                        width=4,
                    )
        elif kind == "result":
            p = _smoothstep((time_seconds - start) / 2.5)
            adjusted_display = raw + (adjusted - raw) * p
            for x, label, value, color in (
                (110, "RAW F1", raw, "#8ca0b8"),
                (555, "POINT-ADJUSTED F1", adjusted_display, "#4ee0c3"),
            ):
                draw.rounded_rectangle(
                    (x, 710, x + 410, 930), radius=28, fill="#10213d", outline="#35577a", width=2
                )
                draw.text((x + 28, 750), label, font=_font(22, True), fill="#c9d8e8")
                draw.text((x + 28, 795), f"{value:.3f}", font=_font(78, True), fill=color)
            _layer_text(
                image,
                (240.0, 975.0),
                f"ΔF1 +{delta:.3f}   •   P(hit) {hit:.1%}",
                _font(35, True),
                "#f4b84b",
                alpha,
            )
        elif kind == "curve":
            p = _smoothstep((time_seconds - start) / 3.8)
            x0, y0, width, height = 135.0, 1080.0, 800.0, 300.0
            draw.line((round(x0), round(y0), round(x0 + width), round(y0)), fill="#a7b6cc", width=2)
            points_raw: list[tuple[int, int]] = []
            points_adjusted: list[tuple[int, int]] = []
            visible = max(2, math.ceil(p * len(sweep)))
            for index, row in enumerate(sweep[:visible]):
                curve_x = x0 + width * index / (len(sweep) - 1)
                points_raw.append((round(curve_x), round(y0 - height * _f1(row, "raw_f1"))))
                points_adjusted.append(
                    (round(curve_x), round(y0 - height * _f1(row, "adjusted_f1")))
                )
            if len(points_raw) > 1:
                draw.line(points_raw, fill="#8ca0b8", width=7, joint="curve")
                draw.line(points_adjusted, fill="#4ee0c3", width=7, joint="curve")
            draw.text((x0, 1120), "event length →", font=_font(24, True), fill="#c9d8e8")
            draw.text((x0 + 500, 730), "adjusted F1", font=_font(24, True), fill="#4ee0c3")
            draw.text((x0 + 500, 1035), "raw F1", font=_font(24, True), fill="#8ca0b8")
        elif kind == "limits":
            for x, heading, lines, color in (
                (
                    96,
                    "WHAT IT SHOWS",
                    "Metric design can change reported evaluation in this synthetic setup.",
                    "#4ee0c3",
                ),
                (
                    548,
                    "WHAT IT DOES NOT SHOW",
                    "Random beats AI • all event-aware metrics are invalid • production systems are invalid.",
                    "#f4b84b",
                ),
            ):
                draw.rounded_rectangle(
                    (x, 720, x + 436, 1030), radius=28, fill="#10213d", outline="#35577a", width=2
                )
                _layer_text(
                    image, (float(x + 26), 755.0), heading, _font(25, True), color, alpha, 380
                )
                _layer_text(image, (float(x + 26), 815.0), lines, _font(25), "#d8e8f0", alpha, 370)
        elif kind == "end":
            _layer_text(
                image,
                (96.0, 700.0),
                "REPRODUCIBLE STUDY   •   FIGURES   •   INTERACTIVE HTML   •   MANUSCRIPT",
                _font(25, True),
                "#4ee0c3",
                alpha,
            )
    draw.text(
        (96, 1150),
        "Project 9 · synthetic Monte Carlo research artifact",
        font=_font(24),
        fill="#9fb3c8",
    )
    draw.rectangle((96, 1190, 984, 1206), fill="#274c77")
    draw.rectangle((96, 1190, round(96 + 888 * time_seconds / VIDEO_SECONDS), 1206), fill="#4ee0c3")
    return np.asarray(image.convert("RGB"))


def render_video_frames(
    release: dict[str, Any], start_frame: int, end_frame: int, frame_output_dir: Path
) -> list[Path]:
    """Render an inclusive-exclusive globally indexed range of cinematic PNG frames."""
    total_frames = VIDEO_SECONDS * VIDEO_FPS
    if not 0 <= start_frame < end_frame <= total_frames:
        raise ValueError("frame range must be within the fixed video frame contract")
    frame_output_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    for frame_index in range(start_frame, end_frame):
        output = frame_output_dir / f"frame_{frame_index:06d}.png"
        Image.fromarray(_cinematic_frame(release, frame_index / VIDEO_FPS)).save(output)
        rendered.append(output)
    return rendered


def render_video(
    release: dict[str, Any], root: Path | None = None
) -> tuple[Path, list[Path], Path]:
    """Render and decode the required 45-second 1080x1350 H.264 video."""
    target_root = root or presentation_root()
    video = target_root / "video" / "project9_linkedin_45s.mp4"
    video.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio.get_writer(
        video, fps=VIDEO_FPS, codec="libx264", pixelformat="yuv420p", macro_block_size=None
    )
    try:
        for frame_index in range(VIDEO_SECONDS * VIDEO_FPS):
            writer.append_data(_cinematic_frame(release, frame_index / VIDEO_FPS))
    finally:
        writer.close()
    key_dir = target_root / "video" / "keyframes"
    key_dir.mkdir(parents=True, exist_ok=True)
    reader = imageio.get_reader(video)
    keys: list[Path] = []
    try:
        for second in range(0, VIDEO_SECONDS + 1, 5):
            index = min(second * VIDEO_FPS, VIDEO_SECONDS * VIDEO_FPS - 1)
            frame = reader.get_data(index)
            output = key_dir / f"keyframe_{second:02d}s.png"
            imageio.imwrite(output, frame)
            keys.append(output)
    finally:
        reader.close()
    thumbs = [Image.open(path).resize((216, 270)) for path in keys]
    sheet = Image.new("RGB", (216 * 5, 270 * 2), "white")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % 5) * 216, (index // 5) * 270))
        thumb.close()
    contact = target_root / "video" / "project9_contact_sheet.png"
    sheet.save(contact)
    return video, keys, contact


def render_social_copy(release: dict[str, Any], root: Path | None = None) -> list[Path]:
    """Write social drafts constrained to the frozen, supported scope."""
    target_root = root or presentation_root()
    primary = _primary(release)
    raw, adjusted = _f1(primary, "raw_f1"), _f1(primary, "adjusted_f1")
    directory = target_root / "linkedin"
    directory.mkdir(parents=True, exist_ok=True)
    post = directory / "linkedin_post.md"
    comment = directory / "resource_comment.md"
    alt = directory / "figure_alt_text.md"
    post.write_text(
        f"# Same alerts, different evaluation credit\n\nIn a frozen synthetic Monte Carlo setup, label-independent random alerts scored {raw:.3f} raw F1 and {adjusted:.3f} point-adjusted F1 in the primary condition (q=0.01, event length=200). The alerts did not change; the scoring rule did.\n\nThis is not a detector benchmark. It uses synthetic labels, no trained detector, and retrospective event boundaries. The artifact is a reproducible prompt to report evaluation rules alongside model results.\n",
        encoding="utf-8",
    )
    comment.write_text(
        "Resources: the offline dashboard, three figures, 45-second explainer, frozen release data, and claim register are bundled in the Project 9 output artifact. The study is a synthetic Monte Carlo demonstration and not peer reviewed or published.\n",
        encoding="utf-8",
    )
    alt.write_text(
        "# Figure alt text\n\n1. Bar chart: frozen primary-condition mean F1 is lower for raw pointwise scoring and higher for point-adjusted scoring with the same random alerts.\n\n2. Line chart: raw F1 stays low while point-adjusted F1 rises as anomaly-event length rises.\n\n3. Line chart: Monte Carlo adjusted recall closely follows the frozen analytical expected event-hit probability as event length rises.\n",
        encoding="utf-8",
    )
    return [post, comment, alt]


def render_presentation(root: Path | None = None) -> dict[str, str]:
    """Build all Step 5 outputs from the frozen artifact and record provenance."""
    release = load_frozen_release()
    root = root or presentation_root()
    figures = render_figures(release, root)
    video, keys, contact = render_video(release, root)
    dashboard = render_dashboard(release, root)
    social = render_social_copy(release, root)
    release_hash = _hash_file(release_data_path())
    manifest: dict[str, Any] = {
        "project_id": PROJECT_ID,
        "release_data_sha256": release_hash,
        "figures": [str(path) for path in figures],
        "dashboard": str(dashboard),
        "video": str(video),
        "video_keyframes": [str(path) for path in keys],
        "contact_sheet": str(contact),
        "social_drafts": [str(path) for path in social],
        "status": "RENDERED_FROM_FROZEN_RELEASE_DATA",
    }
    output = root / "manifests" / "presentation_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    component_manifests = {
        "figure_manifest.json": {
            "project_id": PROJECT_ID,
            "release_data_sha256": release_hash,
            "figure_stems": list(FIGURE_STEMS),
            "files": [str(path) for path in figures],
        },
        "dashboard_manifest.json": {
            "project_id": PROJECT_ID,
            "release_data_sha256": release_hash,
            "tabs": list(DASHBOARD_TABS),
            "file": str(dashboard),
            "offline_self_contained": True,
        },
        "video_manifest.json": {
            "project_id": PROJECT_ID,
            "release_data_sha256": release_hash,
            "file": str(video),
            "fps": VIDEO_FPS,
            "dimensions": [1080, 1350],
            "duration_seconds": VIDEO_SECONDS,
            "decoded_keyframes": [str(path) for path in keys],
            "contact_sheet": str(contact),
        },
    }
    for name, component in component_manifests.items():
        (output.parent / name).write_text(
            json.dumps(component, indent=2, sort_keys=True), encoding="utf-8"
        )
    return {
        "manifest": str(output),
        "release_data_sha256": release_hash,
        "status": manifest["status"],
    }


def validate_presentation(root: Path | None = None) -> dict[str, Any]:
    """Validate the required assets and media properties after rendering."""
    root = root or presentation_root()
    required = [
        root / "figures" / f"{stem}{extension}"
        for stem in FIGURE_STEMS
        for extension in (".png", ".pdf")
    ]
    dashboard = root / "dashboard" / "project9_anomaly_evaluation.html"
    video = root / "video" / "project9_linkedin_45s.mp4"
    required.extend([dashboard, video, root / "video" / "project9_contact_sheet.png"])
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise ValueError(f"missing presentation outputs: {missing}")
    dashboard_text = dashboard.read_text(encoding="utf-8")
    if tuple(DASHBOARD_TABS) != tuple(title for title in DASHBOARD_TABS if title in dashboard_text):
        raise ValueError("dashboard does not contain the required six tabs")
    reader = imageio.get_reader(video)
    try:
        metadata = reader.get_meta_data()
        first = reader.get_data(0)
    finally:
        reader.close()
    fps = float(metadata.get("fps", 0))
    if tuple(first.shape[:2]) != (1350, 1080) or not math.isclose(
        fps, VIDEO_FPS, rel_tol=0.0, abs_tol=0.01
    ):
        raise ValueError("video dimensions or frame rate do not meet contract")
    keyframes = sorted((root / "video" / "keyframes").glob("keyframe_*s.png"))
    if len(keyframes) != 10:
        raise ValueError("decoded video keyframes must cover 0s through 45s at 5s increments")
    return {
        "status": "PASS",
        "video_fps": fps,
        "video_size": [1080, 1350],
        "keyframes": len(keyframes),
        "required_assets": len(required),
    }
