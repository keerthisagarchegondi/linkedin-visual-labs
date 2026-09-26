from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Any

PROJECT = "p28_sampled_recommendation_metrics"

PROFILE_ORDER = (
    "A",
    "B",
    "C",
)

PROFILE_COLORS = {
    "A": "#0072B2",
    "B": "#D55E00",
    "C": "#009E73",
}

NEGATIVE_CONTROL_COLOR = "#6B7280"

SCREENSHOT_ROUTES = (
    "overview",
    "ap-reversal",
    "sensitivity",
    "validation",
    "methods-evidence",
)


def _load_json(
    path: Path,
) -> dict[str, Any]:

    value = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        value,
        dict,
    ):
        raise TypeError(f"Expected JSON object at {path}")

    return value


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def load_dashboard_inputs(
    repo: Path,
) -> dict[str, Any]:

    frozen = repo / "assets" / "p28_sampled_recommendation_metrics" / "frozen"

    docs = repo / "docs" / "projects" / "p28_sampled_recommendation_metrics"

    figures = repo / "assets" / "p28_sampled_recommendation_metrics" / "figures"

    release = _load_json(frozen / "release_data.json")

    validation = _load_json(frozen / "validation_results.json")

    claims = _load_json(frozen / "claim_register.json")

    run_manifest = _load_json(frozen / "run_manifest.json")

    contract = _load_json(docs / "OUTPUT_DESIGN_CONTRACT.json")

    figure_manifest = _load_json(figures / "figure_manifest.json")

    if release.get("results_frozen") is not True:
        raise RuntimeError("Step-4 release data is not frozen.")

    if contract.get("status") != "FROZEN":
        raise RuntimeError("Step-5 output contract is not frozen.")

    if contract.get("output_design_frozen") is not True:
        raise RuntimeError("Step-5 design is not frozen.")

    if figure_manifest.get("status") != "PASS":
        raise RuntimeError("Step-6 figure manifest is not PASS.")

    if figure_manifest.get("preview_images_used") is not False:
        raise RuntimeError("Step-6 provenance unexpectedly used preview images.")

    if release["ranking_reversal"]["full_ap_ordering"] != "C>B>A":
        raise RuntimeError("Unexpected frozen full AP ordering.")

    if release["ranking_reversal"]["sampled_ap_ordering_m99"] != "A>B>C":
        raise RuntimeError("Unexpected frozen sampled AP ordering.")

    if release["auc_negative_control_status"] != "PASS":
        raise RuntimeError("AUC negative control is not PASS.")

    return {
        "release": release,
        "validation": validation,
        "claims": claims,
        "run_manifest": run_manifest,
        "contract": contract,
        "figure_manifest": figure_manifest,
    }


def dashboard_payload(
    inputs: dict[str, Any],
) -> dict[str, Any]:

    release = inputs["release"]

    validation = inputs["validation"]

    claims = inputs["claims"]

    run_manifest = inputs["run_manifest"]

    full = release["full_catalog"]

    sampled = release["sampled_m99"]

    grid = [int(value) for value in release["contract"]["sample_size_grid"]]

    sweep = release["sample_size_sweep"]

    sensitivity: dict[
        str,
        dict[
            str,
            list[float],
        ],
    ] = {}

    for metric in (
        "ap",
        "ndcg",
        "recall_at_10",
        "auc",
    ):
        sensitivity[metric] = {}

        for profile in PROFILE_ORDER:
            sensitivity[metric][profile] = [
                float(sweep[str(m)]["metrics"][profile][metric]) for m in grid
            ]

    supported_claims = [
        {
            "id": str(item["claim_id"]),
            "claim": str(item["claim"]),
            "classification": str(item["classification"]),
        }
        for item in claims["claims"]
        if item.get("status") == "SUPPORTED" and item.get("public_safe") is True
    ]

    rejected_claims = [
        {
            "id": str(item["claim_id"]),
            "claim": str(item["claim"]),
        }
        for item in claims["claims"]
        if item.get("status") != "SUPPORTED" or item.get("public_safe") is False
    ]

    source_mc = validation["source_protocol_monte_carlo"]

    high_mc = validation["high_precision_monte_carlo"]

    independent = validation["independent_critical_number_recomputation"]

    reconciliation = validation["source_reference_reconciliation"]

    return {
        "meta": {
            "project": ("Project 8 — Sampled Recommendation Metrics"),
            "scientific_question": (release["scientific_question"]),
            "n_items": int(release["contract"]["n_items"]),
            "reference_m": int(release["contract"]["reference_negative_draws"]),
            "test_cases_per_profile": 5,
            "grid": grid,
            "root_seed": int(release["contract"]["root_seed"]),
            "source_repetitions": int(release["contract"]["source_repetitions"]),
            "high_precision_repetitions": int(release["contract"]["high_precision_repetitions"]),
        },
        "profiles": release["profiles"],
        "colors": {
            **PROFILE_COLORS,
            "negative_control": (NEGATIVE_CONTROL_COLOR),
        },
        "full": {
            "metrics": full["metrics"],
            "orderings": {
                metric: full["orderings"][metric]["text"]
                for metric in (
                    "ap",
                    "ndcg",
                    "recall_at_10",
                    "auc",
                )
            },
        },
        "sampled_m99": {
            "metrics": sampled["metrics"],
            "orderings": {
                metric: sampled["orderings"][metric]["text"]
                for metric in (
                    "ap",
                    "ndcg",
                    "recall_at_10",
                    "auc",
                )
            },
        },
        "sensitivity": sensitivity,
        "crossover_intervals": release["crossover_intervals"],
        "crossover_policy": release["crossover_policy"],
        "validation": {
            "auc_negative_control": (release["auc_negative_control_status"]),
            "source_mc_pass": bool(source_mc["all_accepted"]),
            "high_precision_mc_pass": bool(high_mc["all_accepted"]),
            "independent_recomputation": str(independent["status"]),
            "source_reconciliation": str(reconciliation["status"]),
            "rows_reconciled": int(reconciliation["rows_reconciled"]),
        },
        "claims": {
            "supported": supported_claims,
            "rejected": rejected_claims,
        },
        "provenance": {
            "scientific_source": (
                "assets/p28_sampled_recommendation_metrics/frozen/release_data.json"
            ),
            "validation_source": (
                "assets/p28_sampled_recommendation_metrics/frozen/validation_results.json"
            ),
            "claim_source": (
                "assets/p28_sampled_recommendation_metrics/frozen/claim_register.json"
            ),
            "design_source": (
                "docs/projects/p28_sampled_recommendation_metrics/OUTPUT_DESIGN_CONTRACT.json"
            ),
            "step6_source": (
                "assets/p28_sampled_recommendation_metrics/figures/figure_manifest.json"
            ),
            "input_head": str(run_manifest["input_head"]),
            "definition_changes_performed": bool(run_manifest["definition_changes_performed"]),
            "exact_crossover_inference_performed": bool(
                run_manifest["exact_crossover_inference_performed"]
            ),
            "seed_searching_performed": bool(run_manifest["seed_searching_performed"]),
            "preview_images_used": False,
        },
    }


def _json_for_script(
    value: dict[str, Any],
) -> str:

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    ).replace(
        "</",
        "<\\/",
    )


def build_html(
    payload: dict[str, Any],
) -> str:

    frozen_json = _json_for_script(payload)

    question = html.escape(str(payload["meta"]["scientific_question"]))

    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>Project 8 — Sampled Recommendation Metrics</title>
<style>
:root {{
  --bg: #F7F7F5;
  --surface: #FFFFFF;
  --surface-soft: #F3F4F6;
  --text: #111827;
  --muted: #6B7280;
  --line: #E5E7EB;
  --line-strong: #D1D5DB;
  --a: #0072B2;
  --b: #D55E00;
  --c: #009E73;
  --negative: #6B7280;
  --blue-soft: #EAF4FB;
  --green-soft: #EAF7F2;
  --orange-soft: #FFF2EA;
  --purple-soft: #F2EEFF;
  --red-soft: #FFF0F0;
  --yellow-soft: #FFF8DD;
  --shadow: 0 8px 24px rgba(17,24,39,.055);
  --radius: 18px;
}}
* {{
  box-sizing: border-box;
}}
html {{
  background: var(--bg);
  scroll-behavior: smooth;
}}
body {{
  margin: 0;
  min-width: 1180px;
  font-family:
    Inter,
    ui-sans-serif,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Arial,
    sans-serif;
  background: var(--bg);
  color: var(--text);
}}
button {{
  font: inherit;
}}
.shell {{
  width: 100%;
  min-height: 100vh;
}}
.topbar {{
  height: 86px;
  padding: 18px 34px 14px 34px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  background: rgba(247,247,245,.98);
}}
.brand {{
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.eyebrow {{
  font-size: 11px;
  font-weight: 750;
  letter-spacing: .105em;
  text-transform: uppercase;
  color: var(--a);
}}
.brand h1 {{
  margin: 0;
  font-size: 23px;
  line-height: 1.18;
  letter-spacing: -.02em;
}}
.brand p {{
  margin: 0;
  color: var(--muted);
  font-size: 11.5px;
}}
.badges {{
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  max-width: 510px;
  justify-content: flex-end;
}}
.badge {{
  padding: 7px 10px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 700;
  border: 1px solid var(--line);
  background: var(--surface);
  white-space: nowrap;
}}
.badge.good {{
  background: var(--green-soft);
  border-color: #BDE5D5;
  color: #06684D;
}}
.badge.ap {{
  background: var(--blue-soft);
  border-color: #C7E1F2;
  color: #075E90;
}}
.badge.auc {{
  background: var(--purple-soft);
  border-color: #DDD3FF;
  color: #5942A6;
}}
.tabs {{
  height: 52px;
  padding: 0 34px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface);
  border-bottom: 1px solid var(--line);
}}
.tab {{
  border: 0;
  background: transparent;
  padding: 9px 14px;
  border-radius: 10px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}}
.tab:hover {{
  background: var(--surface-soft);
}}
.tab.active {{
  color: #075E90;
  background: var(--blue-soft);
}}
.page {{
  display: none;
  padding: 22px 34px 28px 34px;
}}
.page.active {{
  display: block;
}}
.grid {{
  display: grid;
  gap: 14px;
}}
.grid.four {{
  grid-template-columns: repeat(4, minmax(0,1fr));
}}
.grid.two {{
  grid-template-columns: repeat(2, minmax(0,1fr));
}}
.grid.three {{
  grid-template-columns: repeat(3, minmax(0,1fr));
}}
.card {{
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 16px;
}}
.card.flat {{
  box-shadow: none;
}}
.metric-card {{
  min-height: 104px;
}}
.card-label {{
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 750;
  letter-spacing: .035em;
  text-transform: uppercase;
}}
.big-order {{
  margin-top: 8px;
  font-size: 25px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: -.035em;
}}
.small-note {{
  color: var(--muted);
  font-size: 10.5px;
  line-height: 1.45;
}}
.insight {{
  margin-top: 14px;
  padding: 13px 16px;
  border: 1px solid #CDE3F1;
  background: var(--blue-soft);
  border-radius: 14px;
  font-size: 12px;
  font-weight: 700;
}}
.section-title {{
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  margin-bottom: 12px;
}}
.section-title h2 {{
  margin: 0;
  font-size: 18px;
  letter-spacing: -.02em;
}}
.section-title p {{
  margin: 3px 0 0 0;
  color: var(--muted);
  font-size: 11px;
}}
.chart-card {{
  min-height: 386px;
}}
.chart {{
  width: 100%;
  height: 280px;
}}
.chart.tall {{
  height: 330px;
}}
.chart svg {{
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}}
.reversal-banner {{
  margin-top: 12px;
  display: grid;
  grid-template-columns: 1fr 70px 1fr;
  align-items: center;
  text-align: center;
  background: var(--red-soft);
  border: 1px solid #F2CECE;
  border-radius: 14px;
  padding: 12px 14px;
}}
.reversal-banner .order {{
  font-size: 21px;
  font-weight: 800;
}}
.reversal-banner .arrow {{
  color: #A14545;
  font-size: 24px;
  font-weight: 800;
}}
.profile-strip {{
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(3,minmax(0,1fr));
  gap: 8px;
}}
.profile {{
  background: var(--surface-soft);
  border-radius: 11px;
  padding: 9px 10px;
  font-size: 10px;
  overflow-wrap: anywhere;
}}
.profile strong {{
  display: inline-block;
  margin-right: 5px;
}}
.pill {{
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 9.5px;
  font-weight: 750;
  border: 1px solid var(--line);
  background: var(--surface);
}}
.pill.good {{
  color: #05684B;
  background: var(--green-soft);
  border-color: #BEE3D5;
}}
.pill.warn {{
  color: #8A5B00;
  background: var(--yellow-soft);
  border-color: #EAD797;
}}
.legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 9.5px;
  color: var(--muted);
}}
.legend-item {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
}}
.legend-dot {{
  width: 8px;
  height: 8px;
  border-radius: 50%;
}}
.table-wrap {{
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 13px;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--surface);
  font-size: 10px;
}}
th {{
  padding: 9px 8px;
  text-align: left;
  background: var(--surface-soft);
  border-bottom: 1px solid var(--line);
  color: #374151;
  font-weight: 800;
}}
td {{
  padding: 9px 8px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}}
tr:last-child td {{
  border-bottom: 0;
}}
.validation-grid {{
  display: grid;
  grid-template-columns: repeat(2,minmax(0,1fr));
  gap: 10px;
}}
.validation-item {{
  border: 1px solid #CBE6D9;
  background: var(--green-soft);
  border-radius: 13px;
  padding: 12px;
}}
.validation-item strong {{
  display: block;
  font-size: 11px;
  color: #075F49;
}}
.validation-item span {{
  display: block;
  margin-top: 3px;
  color: var(--muted);
  font-size: 9.5px;
}}
.callout {{
  border-radius: 13px;
  padding: 12px 14px;
  font-size: 10px;
  line-height: 1.45;
}}
.callout.yellow {{
  background: var(--yellow-soft);
  border: 1px solid #EAD797;
}}
.callout.green {{
  background: var(--green-soft);
  border: 1px solid #C2E3D6;
}}
.callout.gray {{
  background: var(--surface-soft);
  border: 1px solid var(--line);
}}
.claim-list {{
  display: grid;
  gap: 8px;
}}
.claim {{
  border: 1px solid var(--line);
  background: var(--surface);
  border-radius: 11px;
  padding: 10px 11px;
  font-size: 10px;
  line-height: 1.4;
}}
.claim-id {{
  display: inline-block;
  margin-right: 7px;
  color: var(--a);
  font-weight: 800;
}}
.methods-grid {{
  display: grid;
  grid-template-columns: 1.18fr .82fr;
  gap: 14px;
}}
.kv {{
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 8px 14px;
  font-size: 10.5px;
}}
.kv dt {{
  color: var(--muted);
  font-weight: 700;
}}
.kv dd {{
  margin: 0;
  overflow-wrap: anywhere;
}}
.formula {{
  display: block;
  padding: 9px 11px;
  margin-top: 8px;
  border-radius: 10px;
  background: #FAFAFA;
  border: 1px solid var(--line);
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 10px;
}}
.footer {{
  padding: 11px 34px 18px 34px;
  color: var(--muted);
  font-size: 9.5px;
}}
.footer strong {{
  color: #374151;
}}
.focus-ap .overview-summary {{
  display: none;
}}
.focus-ap #ap-reversal-card {{
  outline: 3px solid rgba(0,114,178,.17);
  box-shadow: 0 14px 38px rgba(0,114,178,.10);
}}
.focus-ap #ap-reversal-card .chart {{
  height: 330px;
}}
</style>
</head>
<body>
<div class="shell" id="app-shell">

<header class="topbar">
  <div class="brand">
    <div class="eyebrow">Reproduction + extension · frozen evidence</div>
    <h1>Project 8 — Sampled Recommendation Metrics</h1>
    <p>{question}</p>
  </div>
  <div class="badges">
    <span class="badge good">Results frozen</span>
    <span class="badge good">Design frozen</span>
    <span class="badge ap">Hero metric · AP</span>
    <span class="badge auc">Negative control · AUC</span>
    <span class="badge">Toy example · 5 test cases/profile</span>
  </div>
</header>

<nav class="tabs" aria-label="Dashboard sections">
  <button class="tab" data-route="overview">Overview</button>
  <button class="tab" data-route="sensitivity">Sensitivity</button>
  <button class="tab" data-route="validation">Validation</button>
  <button class="tab" data-route="methods-evidence">Methods &amp; Evidence</button>
</nav>

<main>

<section class="page" data-page="overview">

  <div class="overview-summary">
    <div class="grid four">

      <article class="card metric-card">
        <div class="card-label">Full-catalog AP ordering</div>
        <div class="big-order" style="color:#009E73">C &gt; B &gt; A</div>
        <p class="small-note">
          Catalog evaluation uses all 10,000 candidate items.
        </p>
      </article>

      <article class="card metric-card">
        <div class="card-label">Expected sampled AP · m=99</div>
        <div class="big-order" style="color:#0072B2">A &gt; B &gt; C</div>
        <p class="small-note">
          Same rank profiles; evaluation set is reduced to 100 candidates.
        </p>
      </article>

      <article class="card metric-card">
        <div class="card-label">AUC negative control</div>
        <div class="big-order" style="color:#6B7280">A &gt; C &gt; B</div>
        <p class="small-note">
          Ordering is invariant in expectation across the frozen m grid.
        </p>
      </article>

      <article class="card metric-card">
        <div class="card-label">Validation</div>
        <div class="big-order" style="font-size:20px;color:#05684B">PASS</div>
        <p class="small-note">
          1,000-run + 10,000-run Monte Carlo protocols passed.
        </p>
      </article>

    </div>

    <div class="insight">
      Same frozen rankings + a different evaluation candidate set
      → different metric values → potentially different model selection.
    </div>
  </div>

  <article class="card chart-card" id="ap-reversal-card" style="margin-top:14px">

    <div class="section-title">
      <div>
        <h2>AP model selection reverses at m=99</h2>
        <p>
          The recommendation profiles are fixed. Only the evaluation protocol changes.
        </p>
      </div>
      <span class="pill good">Replicated computation</span>
    </div>

    <div class="grid two">
      <div>
        <div class="card-label">Full-catalog AP</div>
        <div class="chart" id="chart-full-ap"></div>
      </div>
      <div>
        <div class="card-label">Expected sampled AP · m=99</div>
        <div class="chart" id="chart-sampled-ap"></div>
      </div>
    </div>

    <div class="reversal-banner">
      <div>
        <div class="small-note">Full catalog</div>
        <div class="order">C &gt; B &gt; A</div>
      </div>
      <div class="arrow">→</div>
      <div>
        <div class="small-note">Expected sampled · m=99</div>
        <div class="order">A &gt; B &gt; C</div>
      </div>
    </div>

    <div class="profile-strip">
      <div class="profile">
        <strong style="color:#0072B2">A</strong>
        <span id="profile-a"></span>
      </div>
      <div class="profile">
        <strong style="color:#D55E00">B</strong>
        <span id="profile-b"></span>
      </div>
      <div class="profile">
        <strong style="color:#009E73">C</strong>
        <span id="profile-c"></span>
      </div>
    </div>

  </article>

</section>

<section class="page" data-page="sensitivity">

  <div class="section-title">
    <div>
      <h2>Sample-size sensitivity</h2>
      <p>
        Expected sampled metrics across the predefined frozen negative-sample grid.
      </p>
    </div>
    <span class="pill warn">No interpolation · no exact crossover inference</span>
  </div>

  <div class="grid three">

    <article class="card chart-card">
      <div class="card-label">Average Precision</div>
      <div class="chart tall" id="chart-sweep-ap"></div>
    </article>

    <article class="card chart-card">
      <div class="card-label">NDCG</div>
      <div class="chart tall" id="chart-sweep-ndcg"></div>
    </article>

    <article class="card chart-card">
      <div class="card-label">Recall@10</div>
      <div class="chart tall" id="chart-sweep-recall"></div>
    </article>

  </div>

  <div class="grid two" style="margin-top:14px">

    <article class="card">
      <div class="card-label">Frozen AP crossover intervals</div>
      <div id="crossover-list" style="margin-top:10px"></div>
    </article>

    <article class="card">
      <div class="card-label">Interpretation boundary</div>
      <div class="callout yellow" style="margin-top:10px">
        Adjacent computed-grid intervals may be reported when a pairwise
        relation changes. The dashboard does not infer an exact crossover
        between grid points.
      </div>
      <div class="small-note" style="margin-top:10px">
        Frozen grid:
        1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999.
      </div>
    </article>

  </div>

</section>

<section class="page" data-page="validation">

  <div class="section-title">
    <div>
      <h2>Validation and negative control</h2>
      <p>
        AUC behaves differently from AP/NDCG/Recall@10 under the frozen sampling protocol.
      </p>
    </div>
    <span class="pill good">Frozen validation evidence</span>
  </div>

  <div class="grid two">

    <article class="card chart-card">
      <div class="card-label">AUC negative control across m</div>
      <div class="chart tall" id="chart-auc-control"></div>
      <p class="small-note">
        Expected sampled AUC equals full-catalog AUC across every tested m.
      </p>
    </article>

    <article class="card">
      <div class="card-label">Validation gates</div>

      <div class="validation-grid" style="margin-top:11px">
        <div class="validation-item">
          <strong>Source-protocol Monte Carlo · PASS</strong>
          <span>1,000 repetitions.</span>
        </div>
        <div class="validation-item">
          <strong>High-precision Monte Carlo · PASS</strong>
          <span>10,000 repetitions.</span>
        </div>
        <div class="validation-item">
          <strong>Independent recomputation · PASS</strong>
          <span>Critical values reproduced independently.</span>
        </div>
        <div class="validation-item">
          <strong>Published-value reconciliation · PASS</strong>
          <span>12 rounded reference rows reconciled.</span>
        </div>
      </div>

      <div class="callout gray" style="margin-top:12px">
        No seed searching. No metric-definition changes.
        No exact crossover inference beyond the frozen grid.
      </div>

    </article>

  </div>

  <article class="card" style="margin-top:14px">

    <div class="section-title">
      <div>
        <h2>Metric ordering comparison</h2>
        <p>
          Same three profiles, evaluated under full catalog and expected sampling at m=99.
        </p>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Metric</th>
            <th>Full A</th>
            <th>Full B</th>
            <th>Full C</th>
            <th>Full ordering</th>
            <th>m=99 A</th>
            <th>m=99 B</th>
            <th>m=99 C</th>
            <th>m=99 ordering</th>
          </tr>
        </thead>
        <tbody id="metric-table-body"></tbody>
      </table>
    </div>

  </article>

</section>

<section class="page" data-page="methods-evidence">

  <div class="section-title">
    <div>
      <h2>Methods &amp; evidence</h2>
      <p>
        What the study starts from, what is computed, and what may safely be claimed.
      </p>
    </div>
    <span class="pill">Evidence-first view</span>
  </div>

  <div class="methods-grid">

    <div class="grid">

      <article class="card">
        <div class="card-label">Evaluation protocol</div>

        <dl class="kv" style="margin-top:12px">
          <dt>Input</dt>
          <dd>
            Fixed source-reported A/B/C relevant-item rank profiles.
          </dd>

          <dt>Catalog size</dt>
          <dd>10,000 candidate items.</dd>

          <dt>Cases/profile</dt>
          <dd>5 held-out test cases.</dd>

          <dt>Reference sampling</dt>
          <dd>
            Keep the relevant item + sample 99 negatives.
          </dd>

          <dt>Sampling rule</dt>
          <dd>
            Uniform negative sampling with replacement.
          </dd>

          <dt>Sampled rank</dt>
          <dd>
            R = 1 + X, where X ~ Binomial(m,p),
            p=(r&minus;1)/(N&minus;1).
          </dd>

          <dt>AP</dt>
          <dd>1 / rank for one relevant item.</dd>

          <dt>NDCG</dt>
          <dd>1 / log2(rank + 1), untruncated.</dd>

          <dt>Recall@10</dt>
          <dd>Indicator(rank ≤ 10).</dd>

          <dt>AUC</dt>
          <dd>(N &minus; rank)/(N &minus; 1); negative control.</dd>
        </dl>

        <span class="formula">
          Project 8 starts after model scoring/ranking.
          Raw customer features and model training are outside this study.
        </span>

      </article>

      <article class="card">
        <div class="card-label">Study limitation</div>
        <div class="callout yellow" style="margin-top:10px">
          This is a controlled toy example with five cases per profile and one
          relevant item per case. It demonstrates that a model-selection reversal
          can occur; it does not estimate how frequently or how strongly the effect
          occurs in production recommender systems.
        </div>
      </article>

    </div>

    <div class="grid">

      <article class="card">
        <div class="card-label">Supported public claims</div>
        <div class="claim-list" id="supported-claims" style="margin-top:10px"></div>
      </article>

      <article class="card">
        <div class="card-label">Claims deliberately rejected / bounded</div>
        <div class="claim-list" id="rejected-claims" style="margin-top:10px"></div>
      </article>

    </div>

  </div>

  <article class="card" style="margin-top:14px">

    <div class="card-label">Provenance</div>

    <dl class="kv" id="provenance-list" style="margin-top:12px"></dl>

  </article>

</section>

</main>

<footer class="footer">
  <strong>Attribution:</strong>
  independently reproduces and extends a toy ranking example attributed
  to Krichene &amp; Rendle. A/B/C rank profiles are source-reported;
  analytical derivations, sample-size sweep, Monte Carlo validation,
  independent recomputation, figures and dashboard are independently implemented.
</footer>

</div>

<script id="frozen-data" type="application/json">{frozen_json}</script>

<script>
"use strict";

const DATA = JSON.parse(
  document.getElementById("frozen-data").textContent
);

const ROUTES = new Set([
  "overview",
  "ap-reversal",
  "sensitivity",
  "validation",
  "methods-evidence"
]);

function svgElement(name, attrs = {{}}) {{
  const node = document.createElementNS(
    "http://www.w3.org/2000/svg",
    name
  );

  for (const [key, value] of Object.entries(attrs)) {{
    node.setAttribute(key, String(value));
  }}

  return node;
}}

function clear(node) {{
  while (node.firstChild) {{
    node.removeChild(node.firstChild);
  }}
}}

function makeSvg(container, viewWidth = 620, viewHeight = 280) {{
  clear(container);

  const svg = svgElement("svg", {{
    viewBox: `0 0 ${{viewWidth}} ${{viewHeight}}`,
    role: "img",
    "aria-hidden": "true"
  }});

  container.appendChild(svg);

  return svg;
}}

function addText(svg, x, y, text, options = {{}}) {{
  const node = svgElement("text", {{
    x,
    y,
    fill: options.fill || "#374151",
    "font-size": options.size || 11,
    "font-weight": options.weight || 500,
    "text-anchor": options.anchor || "start"
  }});

  node.textContent = text;

  svg.appendChild(node);

  return node;
}}

function drawHorizontalBars(container, values) {{
  const width = 620;
  const height = 270;

  const margin = {{
    left: 46,
    right: 92,
    top: 18,
    bottom: 34
  }};

  const innerWidth =
    width - margin.left - margin.right;

  const innerHeight =
    height - margin.top - margin.bottom;

  const svg =
    makeSvg(
      container,
      width,
      height
    );

  const entries =
    ["A", "B", "C"]
      .map(profile => [
        profile,
        Number(values[profile])
      ])
      .sort((left, right) => right[1] - left[1]);

  const maxValue =
    Math.max(
      ...entries.map(item => item[1]),
      0.001
    );

  const rowHeight =
    innerHeight / entries.length;

  for (let i = 0; i <= 4; i += 1) {{
    const x =
      margin.left
      + (innerWidth * i / 4);

    svg.appendChild(
      svgElement("line", {{
        x1: x,
        x2: x,
        y1: margin.top,
        y2: margin.top + innerHeight,
        stroke: "#E5E7EB",
        "stroke-width": 1
      }})
    );

    addText(
      svg,
      x,
      height - 9,
      (maxValue * i / 4).toFixed(
        maxValue < 0.15 ? 3 : 2
      ),
      {{
        size: 9,
        fill: "#6B7280",
        anchor: "middle"
      }}
    );
  }}

  entries.forEach((entry, index) => {{
    const profile = entry[0];
    const value = entry[1];

    const y =
      margin.top
      + rowHeight * index
      + rowHeight / 2;

    const x2 =
      margin.left
      + innerWidth * value / maxValue;

    svg.appendChild(
      svgElement("line", {{
        x1: margin.left,
        x2,
        y1: y,
        y2: y,
        stroke: DATA.colors[profile],
        "stroke-width": 8,
        "stroke-linecap": "round",
        opacity: .28
      }})
    );

    svg.appendChild(
      svgElement("circle", {{
        cx: x2,
        cy: y,
        r: 8,
        fill: DATA.colors[profile],
        stroke: "#FFFFFF",
        "stroke-width": 2
      }})
    );

    addText(
      svg,
      margin.left - 15,
      y + 4,
      profile,
      {{
        size: 12,
        weight: 800,
        anchor: "end",
        fill: DATA.colors[profile]
      }}
    );

    addText(
      svg,
      Math.min(
        x2 + 13,
        width - margin.right + 6
      ),
      y + 4,
      value.toFixed(5),
      {{
        size: 10,
        weight: 750
      }}
    );
  }});
}}

function logPosition(value, minimum, maximum) {{
  const minLog = Math.log10(minimum);
  const maxLog = Math.log10(maximum);

  return (
    Math.log10(value) - minLog
  ) / (
    maxLog - minLog
  );
}}

function drawLineChart(
  container,
  series,
  options = {{}}
) {{
  const width = 620;
  const height = 320;

  const margin = {{
    left: 48,
    right: 20,
    top: 22,
    bottom: 52
  }};

  const innerWidth =
    width - margin.left - margin.right;

  const innerHeight =
    height - margin.top - margin.bottom;

  const svg =
    makeSvg(
      container,
      width,
      height
    );

  const xValues =
    DATA.meta.grid;

  let allY = [];

  for (const profile of ["A", "B", "C"]) {{
    allY = allY.concat(
      series[profile]
    );
  }}

  const yMin =
    options.yMin !== undefined
      ? Number(options.yMin)
      : 0;

  let yMax =
    options.yMax !== undefined
      ? Number(options.yMax)
      : Math.max(...allY);

  if (yMax <= yMin) {{
    yMax = yMin + 1;
  }}

  const xMin =
    Math.min(...xValues);

  const xMax =
    Math.max(...xValues);

  for (let i = 0; i <= 4; i += 1) {{
    const y =
      margin.top
      + innerHeight * i / 4;

    svg.appendChild(
      svgElement("line", {{
        x1: margin.left,
        x2: margin.left + innerWidth,
        y1: y,
        y2: y,
        stroke: "#E5E7EB",
        "stroke-width": 1
      }})
    );

    const value =
      yMax - (
        yMax - yMin
      ) * i / 4;

    addText(
      svg,
      margin.left - 8,
      y + 3,
      value.toFixed(2),
      {{
        size: 9,
        fill: "#6B7280",
        anchor: "end"
      }}
    );
  }}

  const tickValues = [
    1,
    10,
    99,
    1000,
    9999
  ];

  for (const tick of tickValues) {{
    const fraction =
      logPosition(
        tick,
        xMin,
        xMax
      );

    const x =
      margin.left
      + fraction * innerWidth;

    svg.appendChild(
      svgElement("line", {{
        x1: x,
        x2: x,
        y1: margin.top,
        y2: margin.top + innerHeight,
        stroke: "#F0F1F2",
        "stroke-width": 1
      }})
    );

    addText(
      svg,
      x,
      height - 25,
      String(tick),
      {{
        size: 9,
        fill: "#6B7280",
        anchor: "middle"
      }}
    );
  }}

  for (const profile of ["A", "B", "C"]) {{

    const points =
      xValues.map((m, index) => {{

        const xFraction =
          logPosition(
            m,
            xMin,
            xMax
          );

        const yValue =
          Number(
            series[profile][index]
          );

        const yFraction =
          (
            yValue - yMin
          ) / (
            yMax - yMin
          );

        return {{
          x:
            margin.left
            + xFraction * innerWidth,
          y:
            margin.top
            + innerHeight
            - yFraction * innerHeight,
          value: yValue,
          m
        }};
      }});

    const polyline =
      svgElement(
        "polyline",
        {{
          points:
            points
              .map(
                point =>
                  `${{point.x}},${{point.y}}`
              )
              .join(" "),
          fill: "none",
          stroke: DATA.colors[profile],
          "stroke-width": 2.4,
          "stroke-linejoin": "round",
          "stroke-linecap": "round"
        }}
      );

    svg.appendChild(
      polyline
    );

    for (const point of points) {{
      svg.appendChild(
        svgElement("circle", {{
          cx: point.x,
          cy: point.y,
          r: 3.3,
          fill: DATA.colors[profile],
          stroke: "#FFFFFF",
          "stroke-width": 1
        }})
      );
    }}

    const finalPoint =
      points[
        points.length - 1
      ];

    addText(
      svg,
      finalPoint.x - 2,
      finalPoint.y - 8,
      profile,
      {{
        size: 10,
        weight: 800,
        fill: DATA.colors[profile],
        anchor: "end"
      }}
    );
  }}

  addText(
    svg,
    margin.left + innerWidth / 2,
    height - 5,
    "Number of sampled negatives (m, log scale)",
    {{
      size: 9,
      fill: "#6B7280",
      anchor: "middle"
    }}
  );
}}

function metricLabel(metric) {{
  const labels = {{
    ap: "AP",
    ndcg: "NDCG",
    recall_at_10: "Recall@10",
    auc: "AUC"
  }};

  return labels[metric];
}}

function fmt(metric, value) {{
  if (metric === "recall_at_10") {{
    return Number(value).toFixed(4);
  }}

  return Number(value).toFixed(5);
}}

function renderMetricTable() {{
  const body =
    document.getElementById(
      "metric-table-body"
    );

  body.innerHTML = "";

  for (
    const metric
    of [
      "ap",
      "ndcg",
      "recall_at_10",
      "auc"
    ]
  ) {{

    const row =
      document.createElement(
        "tr"
      );

    const cells = [
      metricLabel(metric),
      fmt(metric, DATA.full.metrics.A[metric]),
      fmt(metric, DATA.full.metrics.B[metric]),
      fmt(metric, DATA.full.metrics.C[metric]),
      DATA.full.orderings[metric],
      fmt(metric, DATA.sampled_m99.metrics.A[metric]),
      fmt(metric, DATA.sampled_m99.metrics.B[metric]),
      fmt(metric, DATA.sampled_m99.metrics.C[metric]),
      DATA.sampled_m99.orderings[metric]
    ];

    for (const cellText of cells) {{
      const cell =
        document.createElement(
          "td"
        );

      cell.textContent =
        cellText;

      row.appendChild(
        cell
      );
    }}

    body.appendChild(
      row
    );
  }}
}}

function renderProfiles() {{
  for (const profile of ["A", "B", "C"]) {{

    document.getElementById(
      `profile-${{profile.toLowerCase()}}`
    ).textContent =
      `[${{
        DATA.profiles[profile].join(", ")
      }}]`;
  }}
}}

function relationText(interval) {{
  const pair =
    interval.profiles.join("/");

  return (
    `${{pair}}: `
    + `${{interval.lower_computed_m}}\\u2013${{interval.upper_computed_m}}`
  );
}}

function renderCrossovers() {{
  const container =
    document.getElementById(
      "crossover-list"
    );

  container.innerHTML = "";

  const apIntervals =
    DATA.crossover_intervals.filter(
      interval =>
        interval.metric === "ap"
    );

  for (const interval of apIntervals) {{

    const item =
      document.createElement(
        "div"
      );

    item.className =
      "callout gray";

    item.style.marginBottom =
      "7px";

    item.textContent =
      relationText(
        interval
      );

    container.appendChild(
      item
    );
  }}
}}

function renderClaims() {{

  const supported =
    document.getElementById(
      "supported-claims"
    );

  const rejected =
    document.getElementById(
      "rejected-claims"
    );

  supported.innerHTML = "";
  rejected.innerHTML = "";

  for (
    const item
    of DATA.claims.supported
  ) {{

    const node =
      document.createElement(
        "div"
      );

    node.className =
      "claim";

    const id =
      document.createElement(
        "span"
      );

    id.className =
      "claim-id";

    id.textContent =
      item.id;

    node.appendChild(
      id
    );

    node.appendChild(
      document.createTextNode(
        item.claim
      )
    );

    supported.appendChild(
      node
    );
  }}

  for (
    const item
    of DATA.claims.rejected
  ) {{

    const node =
      document.createElement(
        "div"
      );

    node.className =
      "claim";

    const id =
      document.createElement(
        "span"
      );

    id.className =
      "claim-id";

    id.style.color =
      "#A14545";

    id.textContent =
      item.id;

    node.appendChild(
      id
    );

    node.appendChild(
      document.createTextNode(
        item.claim
      )
    );

    rejected.appendChild(
      node
    );
  }}
}}

function renderProvenance() {{

  const list =
    document.getElementById(
      "provenance-list"
    );

  list.innerHTML = "";

  const entries = [
    ["Scientific source", DATA.provenance.scientific_source],
    ["Validation source", DATA.provenance.validation_source],
    ["Claim source", DATA.provenance.claim_source],
    ["Design source", DATA.provenance.design_source],
    ["Step-6 source", DATA.provenance.step6_source],
    ["Input scientific HEAD", DATA.provenance.input_head],
    ["Definition changes", String(DATA.provenance.definition_changes_performed)],
    ["Exact crossover inference", String(DATA.provenance.exact_crossover_inference_performed)],
    ["Seed searching", String(DATA.provenance.seed_searching_performed)],
    ["Preview images used", String(DATA.provenance.preview_images_used)]
  ];

  for (const [key, value] of entries) {{

    const term =
      document.createElement(
        "dt"
      );

    term.textContent =
      key;

    const description =
      document.createElement(
        "dd"
      );

    description.textContent =
      value;

    list.appendChild(
      term
    );

    list.appendChild(
      description
    );
  }}
}}

function renderCharts() {{

  drawHorizontalBars(
    document.getElementById(
      "chart-full-ap"
    ),
    {{
      A: DATA.full.metrics.A.ap,
      B: DATA.full.metrics.B.ap,
      C: DATA.full.metrics.C.ap
    }}
  );

  drawHorizontalBars(
    document.getElementById(
      "chart-sampled-ap"
    ),
    {{
      A: DATA.sampled_m99.metrics.A.ap,
      B: DATA.sampled_m99.metrics.B.ap,
      C: DATA.sampled_m99.metrics.C.ap
    }}
  );

  drawLineChart(
    document.getElementById(
      "chart-sweep-ap"
    ),
    DATA.sensitivity.ap,
    {{
      yMin: 0,
      yMax: 1
    }}
  );

  drawLineChart(
    document.getElementById(
      "chart-sweep-ndcg"
    ),
    DATA.sensitivity.ndcg,
    {{
      yMin: 0,
      yMax: 1
    }}
  );

  drawLineChart(
    document.getElementById(
      "chart-sweep-recall"
    ),
    DATA.sensitivity.recall_at_10,
    {{
      yMin: 0,
      yMax: 1
    }}
  );

  drawLineChart(
    document.getElementById(
      "chart-auc-control"
    ),
    DATA.sensitivity.auc,
    {{
      yMin: 0.5,
      yMax: 1
    }}
  );
}}

function routeFromLocation() {{
  const raw =
    window.location.hash
      .replace(/^#/, "")
      .trim();

  if (!raw) {{
    return "overview";
  }}

  if (!ROUTES.has(raw)) {{
    return "overview";
  }}

  return raw;
}}

function activateRoute(route) {{

  const shell =
    document.getElementById(
      "app-shell"
    );

  shell.classList.remove(
    "focus-ap"
  );

  const pageRoute =
    route === "ap-reversal"
      ? "overview"
      : route;

  for (
    const page
    of document.querySelectorAll(
      ".page"
    )
  ) {{
    page.classList.toggle(
      "active",
      page.dataset.page === pageRoute
    );
  }}

  for (
    const tab
    of document.querySelectorAll(
      ".tab"
    )
  ) {{
    tab.classList.toggle(
      "active",
      tab.dataset.route === pageRoute
    );
  }}

  if (route === "ap-reversal") {{
    shell.classList.add(
      "focus-ap"
    );
  }}

  document.body.dataset.route =
    route;
}}

function boot() {{

  renderProfiles();
  renderMetricTable();
  renderCrossovers();
  renderClaims();
  renderProvenance();
  renderCharts();

  for (
    const tab
    of document.querySelectorAll(
      ".tab"
    )
  ) {{
    tab.addEventListener(
      "click",
      () => {{
        window.location.hash =
          tab.dataset.route;
      }}
    );
  }}

  activateRoute(
    routeFromLocation()
  );

  window.addEventListener(
    "hashchange",
    () => {{
      activateRoute(
        routeFromLocation()
      );
    }}
  );

  window.__P28_DASHBOARD_READY__ = true;
}}

boot();
</script>

</body>
</html>
"""

    return document


def write_dashboard(
    repo: Path,
    output_dir: Path,
) -> dict[str, Any]:

    inputs = load_dashboard_inputs(repo)

    payload = dashboard_payload(inputs)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    html_path = output_dir / "index.html"

    document = build_html(payload)

    html_path.write_text(
        document,
        encoding="utf-8",
        newline="\n",
    )

    if "<script src=" in document.lower():
        raise RuntimeError("Dashboard unexpectedly references external JavaScript.")

    if "<link " in document.lower():
        raise RuntimeError("Dashboard unexpectedly references an external stylesheet.")

    if "background-image:" in document.lower():
        raise RuntimeError("Dashboard may not use background images.")

    if "<img " in document.lower():
        raise RuntimeError("Dashboard may not use flattened image components.")

    if "window.__P28_DASHBOARD_READY__ = true" not in document:
        raise RuntimeError("Dashboard readiness marker missing.")

    manifest = {
        "schema_version": 1,
        "project": PROJECT,
        "step": 7,
        "status": "PASS",
        "generation_method": ("SELF_CONTAINED_HTML_CSS_JS_SVG_FROM_FROZEN_DATA"),
        "results_frozen": True,
        "output_design_frozen": True,
        "static_figures_frozen": True,
        "preview_images_used": False,
        "stock_images_used": False,
        "step6_figures_used_as_backgrounds": False,
        "external_script_dependencies": 0,
        "external_stylesheet_dependencies": 0,
        "canonical_viewport": {
            "width": 1440,
            "height": 900,
        },
        "sections": [
            "Overview",
            "Sensitivity",
            "Validation",
            "Methods & Evidence",
        ],
        "screenshot_routes": list(SCREENSHOT_ROUTES),
        "scientific_contract": {
            "full_ap_ordering": (payload["full"]["orderings"]["ap"]),
            "sampled_ap_ordering_m99": (payload["sampled_m99"]["orderings"]["ap"]),
            "auc_ordering": (payload["full"]["orderings"]["auc"]),
            "sample_size_grid": (payload["meta"]["grid"]),
            "exact_crossover_inference": False,
        },
        "files": {
            "index.html": {
                "bytes": (html_path.stat().st_size),
                "sha256": sha256_file(html_path),
            }
        },
    }

    manifest_path = output_dir / "dashboard_manifest.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return manifest
