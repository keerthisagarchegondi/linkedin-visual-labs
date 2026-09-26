from __future__ import annotations

import hashlib
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
    "sample-size-sweep",
    "validation",
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

    template = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>Project 8 — Sampled Recommendation Metrics</title>
<style>
:root {
  --page:#F5F9FF;
  --surface:#FFFFFF;
  --border:#D8E3F2;
  --navy:#0F2147;
  --text:#17284D;
  --muted:#5F6F8F;
  --a:#0072B2;
  --b:#D55E00;
  --c:#009E73;
  --blue-soft:#EBF5FF;
  --blue-border:#C8E2FC;
  --green-soft:#ECFAF4;
  --green-border:#C9EBDD;
  --purple-soft:#F4EFFF;
  --purple-border:#DED0FB;
  --red-soft:#FFF0F1;
  --red-border:#FFBFC5;
  --yellow-soft:#FFF7DD;
  --yellow-border:#F2D895;
  --shadow:0 7px 22px rgba(27,61,111,.055);
}

* {
  box-sizing:border-box;
}

html,
body {
  margin:0;
  width:100%;
  min-width:1180px;
  min-height:100%;
  background:
    linear-gradient(
      180deg,
      #FFFFFF 0,
      #F7FAFF 155px,
      var(--page) 100%
    );
  color:var(--text);
  font-family:
    Inter,
    "Segoe UI",
    Arial,
    sans-serif;
}

body {
  overflow-x:auto;
}

button {
  font:inherit;
}

.header {
  min-height:95px;
  padding:17px 24px 12px;
  display:flex;
  justify-content:space-between;
  gap:24px;
  align-items:flex-start;
}

.header h1 {
  margin:0;
  color:var(--navy);
  font-size:31px;
  line-height:1.05;
  letter-spacing:-.027em;
  font-weight:800;
}

.header p {
  margin:7px 0 0;
  color:#506184;
  font-size:14px;
}

.header-badges {
  display:flex;
  gap:7px;
  justify-content:flex-end;
  flex-wrap:wrap;
  padding-top:9px;
}

.badge {
  min-height:38px;
  padding:0 15px;
  display:inline-flex;
  gap:8px;
  align-items:center;
  justify-content:center;
  border:1px solid var(--border);
  border-radius:20px;
  background:#F2F5FA;
  color:#20345B;
  font-size:11px;
  font-weight:750;
  white-space:nowrap;
}

.badge.green {
  background:#DDF6E9;
  border-color:#C4EAD6;
  color:#087153;
}

.badge.blue {
  background:#E8F1FF;
  border-color:#BFD8FF;
  color:#0A5ED1;
}

.badge.purple {
  background:#F0E7FF;
  border-color:#D8C2FF;
  color:#5C20C2;
}

.badge-dot {
  width:18px;
  height:18px;
  border-radius:50%;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  background:#0C8E68;
  color:#FFF;
}

.nav {
  margin:0 24px;
  height:57px;
  display:grid;
  grid-template-columns:repeat(4,1fr);
  border:1px solid #D6E1F0;
  border-radius:7px;
  overflow:hidden;
  background:#FFF;
}

.nav-button {
  border:0;
  border-right:1px solid #DDE5F0;
  background:transparent;
  color:#27385C;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:13px;
  font-size:13px;
  font-weight:760;
}

.nav-button:last-child {
  border-right:0;
}

.nav-button.active {
  background:
    linear-gradient(
      180deg,
      #258AF5,
      #1478E9
    );
  color:#FFF;
}

.nav-icon {
  font-size:17px;
  font-weight:900;
}

.page {
  display:none;
  padding:10px 24px 18px;
}

.page.active {
  display:block;
}

.overview-shell {
  border:1px solid #D9E4F2;
  border-radius:7px;
  background:#FFF;
  padding:14px 15px 13px;
}

.overview-shell h2 {
  margin:0 0 12px;
  color:var(--navy);
  font-size:18px;
}

.kpi-grid {
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:12px;
}

.kpi {
  min-height:92px;
  border-radius:7px;
  padding:15px 16px;
  display:grid;
  grid-template-columns:45px 1fr;
  gap:13px;
  align-items:center;
  border:1px solid var(--border);
}

.kpi.blue {
  background:var(--blue-soft);
  border-color:var(--blue-border);
}

.kpi.green {
  background:var(--green-soft);
  border-color:var(--green-border);
}

.kpi.purple {
  background:var(--purple-soft);
  border-color:var(--purple-border);
}

.kpi.mint {
  background:#EBFAF4;
  border-color:#C8EBDE;
}

.kpi-icon {
  width:42px;
  height:42px;
  border-radius:7px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:21px;
  font-weight:900;
}

.kpi.blue .kpi-icon {
  background:#D6EAFF;
  color:#1478E9;
}

.kpi.green .kpi-icon {
  background:#D7F3E6;
  color:#087C5A;
}

.kpi.purple .kpi-icon {
  background:#E6DAFF;
  color:#6024C7;
}

.kpi.mint .kpi-icon {
  background:#D9F4E8;
  color:#078563;
}

.kpi-label {
  font-size:11px;
  line-height:1.35;
  color:#24375C;
  font-weight:720;
}

.kpi-value {
  margin-top:4px;
  font-size:22px;
  font-weight:820;
}

.kpi.blue .kpi-value {
  color:#176DDB;
}

.kpi.green .kpi-value {
  color:#07815D;
}

.kpi.purple .kpi-value {
  color:#5D20C8;
}

.insight-strip {
  margin-top:12px;
  min-height:49px;
  border:1px solid #D8E7F8;
  border-radius:7px;
  background:#F3F8FE;
  display:flex;
  align-items:center;
  padding:9px 16px;
  gap:14px;
  color:#1D3157;
  font-size:12px;
  font-weight:620;
}

.insight-icon {
  color:#D79800;
  font-size:20px;
}

.overview-panels {
  display:grid;
  grid-template-columns:
    minmax(0,1.08fr)
    minmax(0,.90fr)
    minmax(0,1.03fr);
  gap:11px;
  margin-top:10px;
}

.panel,
.detail-card {
  min-width:0;
  border:1px solid #D8E3F0;
  border-radius:7px;
  background:#FFF;
  padding:12px 13px;
  box-shadow:var(--shadow);
}

.panel-title {
  margin:0 0 10px;
  color:var(--navy);
  font-size:18px;
  font-weight:800;
}

.panel-subtitle {
  color:#415476;
  font-size:10px;
  font-weight:720;
  margin-bottom:5px;
}

.ap-two {
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:13px;
}

.chart {
  width:100%;
  height:205px;
}

.chart.sweep {
  height:248px;
}

.chart.detail {
  height:330px;
}

.chart svg {
  display:block;
  width:100%;
  height:100%;
  overflow:visible;
}

.reversal-box {
  margin-top:7px;
  height:48px;
  border:1px solid var(--red-border);
  background:var(--red-soft);
  border-radius:7px;
  display:flex;
  align-items:center;
  justify-content:center;
  gap:12px;
  font-size:20px;
  font-weight:830;
}

.reversal-full {
  color:#D51D2A;
}

.reversal-sampled {
  color:#0868D2;
}

.rank-box {
  margin-top:9px;
  border:1px solid #DDE7F2;
  background:#F8FBFF;
  border-radius:7px;
  padding:8px 10px;
  font-size:9.5px;
  color:#405271;
  line-height:1.45;
}

.rank-line {
  margin-top:3px;
  display:flex;
  flex-wrap:wrap;
  gap:9px;
}

.crossover-box {
  margin-top:10px;
  border:1px solid var(--yellow-border);
  background:var(--yellow-soft);
  border-radius:7px;
  padding:9px 11px;
}

.crossover-head {
  color:#5A4111;
  font-size:10.5px;
  font-weight:800;
}

.crossover-list {
  margin:7px 0 0 17px;
  padding:0;
  color:#394B69;
  font-size:9.5px;
  line-height:1.55;
}

.crossover-foot {
  margin-top:5px;
  color:#6B7280;
  font-size:8.8px;
}

.validation-table-wrap {
  border:1px solid #D5DFEC;
  border-radius:6px;
  overflow:hidden;
}

.validation-table {
  width:100%;
  border-collapse:collapse;
  table-layout:fixed;
  font-size:8.2px;
}

.validation-table th,
.validation-table td {
  border-right:1px solid #DCE5F0;
  border-bottom:1px solid #DCE5F0;
  padding:6px 4px;
  text-align:center;
  white-space:nowrap;
}

.validation-table th:last-child,
.validation-table td:last-child {
  border-right:0;
}

.validation-table thead th {
  background:#F2F6FB;
  color:#273C62;
  font-weight:800;
}

.validation-table .group {
  background:#EEF4FB;
}

.validation-table .metric {
  text-align:left;
  font-weight:800;
}

.order-blue {
  color:#0B6CD8;
  font-weight:800;
}

.pass-grid {
  margin-top:10px;
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:7px;
}

.pass-card {
  min-height:64px;
  border:1px solid #D9E5F1;
  border-radius:6px;
  background:#F8FBFF;
  display:grid;
  grid-template-columns:37px 1fr;
  gap:8px;
  align-items:center;
  padding:8px;
}

.pass-check {
  width:31px;
  height:31px;
  border-radius:50%;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#0A936D;
  color:#FFF;
  font-size:18px;
}

.pass-copy {
  color:#273A60;
  font-size:9px;
  line-height:1.35;
}

.pass-copy strong {
  color:#07825F;
}

.detail-card {
  padding:17px;
}

.detail-heading {
  margin:0;
  color:var(--navy);
  font-size:22px;
}

.detail-note {
  margin:5px 0 14px;
  color:var(--muted);
  font-size:11px;
}

.detail-grid-two {
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:15px;
}

.detail-grid-three {
  display:grid;
  grid-template-columns:repeat(3,1fr);
  gap:13px;
}

.evidence-grid {
  margin-top:14px;
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:12px;
}

.evidence-card {
  border:1px solid #DEE7F2;
  border-radius:7px;
  background:#F8FBFF;
  padding:11px 12px;
  font-size:10px;
  line-height:1.5;
}

.claim-row {
  margin-top:7px;
  padding:7px 8px;
  border:1px solid #E1E8F1;
  border-radius:5px;
  background:#FFF;
}

.claim-id {
  color:#0A6ED8;
  font-weight:800;
  margin-right:6px;
}

.footer {
  min-height:57px;
  padding:12px 25px 14px;
  border-top:1px solid #DDE6F1;
  background:#FFF;
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:16px;
  color:#63718D;
  font-size:9.3px;
}

.footer-left {
  display:flex;
  align-items:center;
  gap:10px;
}

.footer-right {
  white-space:nowrap;
}
</style>
</head>

<body>
<div id="app">

<header class="header">
  <div>
    <h1>Project 8 — Sampled Recommendation Metrics</h1>
    <p>
      Reproduction-and-extension study of a source-reported toy example
      attributed to Krichene &amp; Rendle
    </p>
  </div>

  <div class="header-badges">
    <span class="badge green">
      <span class="badge-dot">&#10003;</span>
      Results frozen
    </span>
    <span class="badge blue">Hero metric: AP</span>
    <span class="badge purple">Negative control: AUC</span>
    <span class="badge">Toy example</span>
  </div>
</header>

<nav class="nav" aria-label="Primary dashboard navigation">
  <button class="nav-button" data-route="overview" data-contract-tab="Overview">
    <span class="nav-icon">&#9636;</span>
    Overview
  </button>

  <button class="nav-button" data-route="ap-reversal" data-contract-tab="AP reversal">
    <span class="nav-icon">&#9637;</span>
    AP reversal
  </button>

  <button class="nav-button" data-route="sample-size-sweep" data-contract-tab="Sample-size sweep">
    <span class="nav-icon">&#8767;</span>
    Sample-size sweep
  </button>

  <button class="nav-button" data-route="validation" data-contract-tab="Validation">
    <span class="nav-icon">&#9679;</span>
    Validation
  </button>
</nav>

<main>

<section
  class="page"
  data-page="overview"
  data-preview-contract="approved-overview-three-panel-v1"
>
  <div class="overview-shell">

    <h2>Overview</h2>

    <div class="kpi-grid">

      <article class="kpi blue">
        <div class="kpi-icon">&#9819;</div>
        <div>
          <div class="kpi-label">Full-catalog AP ordering:</div>
          <div class="kpi-value">C &gt; B &gt; A</div>
        </div>
      </article>

      <article class="kpi green">
        <div class="kpi-icon">&#9637;</div>
        <div>
          <div class="kpi-label">Sampled AP ordering at m=99:</div>
          <div class="kpi-value">A &gt; B &gt; C</div>
        </div>
      </article>

      <article class="kpi purple">
        <div class="kpi-icon">&#8767;</div>
        <div>
          <div class="kpi-label">AUC ordering (full and sampled):</div>
          <div class="kpi-value">A &gt; C &gt; B</div>
        </div>
      </article>

      <article class="kpi mint">
        <div class="kpi-icon">&#10003;</div>
        <div class="kpi-label">
          Monte Carlo validation passed —
          1,000 and 10,000 repetitions.
        </div>
      </article>

    </div>

    <div class="insight-strip">
      <span class="insight-icon">&#9733;</span>
      <span>
        Same rank profiles, different evaluation candidate set,
        different model winner.
      </span>
    </div>

  </div>

  <div
    class="overview-panels"
    data-preview-contract="overview-main-three-column"
  >

    <article
      class="panel"
      id="overview-ap-panel"
      data-overview-panel="ap-reversal"
    >
      <h2 class="panel-title">AP reversal</h2>

      <div class="ap-two">
        <div>
          <div class="panel-subtitle">Full catalog AP</div>
          <div class="chart" id="overview-full-ap"></div>
        </div>

        <div>
          <div class="panel-subtitle">Expected sampled AP (m = 99)</div>
          <div class="chart" id="overview-sampled-ap"></div>
        </div>
      </div>

      <div class="reversal-box">
        <span class="reversal-full">C &gt; B &gt; A</span>
        <span>&#8594;</span>
        <span class="reversal-sampled">A &gt; B &gt; C</span>
      </div>

      <div class="rank-box">
        <strong>
          Fixed source-reported rank profiles (per user, 5 users):
        </strong>

        <div class="rank-line">
          <span><strong>A =</strong> <span id="overview-profile-a"></span></span>
          <span><strong>B =</strong> <span id="overview-profile-b"></span></span>
          <span><strong>C =</strong> <span id="overview-profile-c"></span></span>
        </div>
      </div>
    </article>

    <article
      class="panel"
      id="overview-sweep-panel"
      data-overview-panel="sample-size-sweep"
    >
      <h2 class="panel-title">Sample-size sweep</h2>

      <div class="panel-subtitle">
        AP vs. number of sampled negatives (m)
      </div>

      <div class="chart sweep" id="overview-ap-sweep"></div>

      <div class="crossover-box">
        <div class="crossover-head">
          Crossover findings (intervals from computed grid values):
        </div>

        <ul class="crossover-list" id="overview-crossovers"></ul>

        <div class="crossover-foot">
          Exact crossover points are not inferred beyond computed grid values.
        </div>
      </div>
    </article>

    <article
      class="panel"
      id="overview-validation-panel"
      data-overview-panel="validation"
    >
      <h2 class="panel-title">Validation</h2>

      <div class="validation-table-wrap">
        <table class="validation-table">
          <thead>
            <tr>
              <th></th>
              <th class="group" colspan="4">Full catalog metrics</th>
              <th class="group" colspan="4">Sampled m = 99 metrics</th>
            </tr>
            <tr>
              <th>Metric</th>
              <th>A</th>
              <th>B</th>
              <th>C</th>
              <th>Ordering</th>
              <th>A</th>
              <th>B</th>
              <th>C</th>
              <th>Ordering</th>
            </tr>
          </thead>
          <tbody id="overview-validation-body"></tbody>
        </table>
      </div>

      <div class="pass-grid">
        <div class="pass-card">
          <div class="pass-check">&#10003;</div>
          <div class="pass-copy">
            Source rounding reconciliation:
            <strong>PASS</strong>
          </div>
        </div>

        <div class="pass-card">
          <div class="pass-check">&#10003;</div>
          <div class="pass-copy">
            Independent recomputation:
            <strong>PASS</strong>
          </div>
        </div>

        <div class="pass-card">
          <div class="pass-check">&#10003;</div>
          <div class="pass-copy">
            AUC negative control invariant across tested m:
            <strong>PASS</strong>
          </div>
        </div>

        <div class="pass-card">
          <div class="pass-check">&#10003;</div>
          <div class="pass-copy">
            No seed searching, no definition changes:
            <strong>PASS</strong>
          </div>
        </div>
      </div>
    </article>

  </div>
</section>

<section class="page" data-page="ap-reversal">
  <article class="detail-card">
    <h2 class="detail-heading">AP reversal</h2>
    <p class="detail-note">
      The A/B/C rank profiles are fixed. Only the evaluation candidate set changes.
    </p>

    <div class="detail-grid-two">
      <div>
        <div class="panel-subtitle">Full-catalog AP</div>
        <div class="chart detail" id="detail-full-ap"></div>
      </div>

      <div>
        <div class="panel-subtitle">Expected sampled AP at m=99</div>
        <div class="chart detail" id="detail-sampled-ap"></div>
      </div>
    </div>

    <div class="reversal-box">
      <span class="reversal-full">C &gt; B &gt; A</span>
      <span>&#8594;</span>
      <span class="reversal-sampled">A &gt; B &gt; C</span>
    </div>

    <div class="rank-box">
      <strong>Frozen rank profiles:</strong>
      <div class="rank-line">
        <span><strong>A =</strong> <span id="detail-profile-a"></span></span>
        <span><strong>B =</strong> <span id="detail-profile-b"></span></span>
        <span><strong>C =</strong> <span id="detail-profile-c"></span></span>
      </div>
    </div>
  </article>
</section>

<section class="page" data-page="sample-size-sweep">
  <article class="detail-card">
    <h2 class="detail-heading">Sample-size sweep</h2>

    <p class="detail-note">
      Expected sampled metrics across the predefined frozen negative-sample grid.
    </p>

    <div class="detail-grid-three">
      <div>
        <div class="panel-subtitle">Average Precision</div>
        <div class="chart detail" id="detail-ap-sweep"></div>
      </div>

      <div>
        <div class="panel-subtitle">NDCG</div>
        <div class="chart detail" id="detail-ndcg-sweep"></div>
      </div>

      <div>
        <div class="panel-subtitle">Recall@10</div>
        <div class="chart detail" id="detail-recall-sweep"></div>
      </div>
    </div>

    <div class="crossover-box">
      <div class="crossover-head">Frozen AP crossover intervals</div>
      <ul class="crossover-list" id="detail-crossovers"></ul>
      <div class="crossover-foot">
        Only adjacent computed-grid intervals are reported.
        Exact crossover locations are not inferred.
      </div>
    </div>
  </article>
</section>

<section class="page" data-page="validation">
  <article class="detail-card">
    <h2 class="detail-heading">Validation</h2>

    <p class="detail-note">
      Frozen metric comparison, AUC negative control,
      Monte Carlo checks and evidence boundaries.
    </p>

    <div class="detail-grid-two">
      <div>
        <div class="validation-table-wrap">
          <table class="validation-table">
            <thead>
              <tr>
                <th></th>
                <th class="group" colspan="4">Full catalog</th>
                <th class="group" colspan="4">Sampled m = 99</th>
              </tr>
              <tr>
                <th>Metric</th>
                <th>A</th>
                <th>B</th>
                <th>C</th>
                <th>Ordering</th>
                <th>A</th>
                <th>B</th>
                <th>C</th>
                <th>Ordering</th>
              </tr>
            </thead>
            <tbody id="detail-validation-body"></tbody>
          </table>
        </div>

        <div class="pass-grid">
          <div class="pass-card">
            <div class="pass-check">&#10003;</div>
            <div class="pass-copy">
              Source-protocol Monte Carlo:
              <strong>PASS</strong>
            </div>
          </div>

          <div class="pass-card">
            <div class="pass-check">&#10003;</div>
            <div class="pass-copy">
              High-precision Monte Carlo:
              <strong>PASS</strong>
            </div>
          </div>

          <div class="pass-card">
            <div class="pass-check">&#10003;</div>
            <div class="pass-copy">
              Independent recomputation:
              <strong>PASS</strong>
            </div>
          </div>

          <div class="pass-card">
            <div class="pass-check">&#10003;</div>
            <div class="pass-copy">
              12 reference values reconciled:
              <strong>PASS</strong>
            </div>
          </div>
        </div>
      </div>

      <div>
        <div class="panel-subtitle">
          AUC negative control across sampled m
        </div>
        <div class="chart detail" id="detail-auc"></div>
      </div>
    </div>

    <div class="evidence-grid">
      <div class="evidence-card">
        <strong>Methods &amp; Evidence</strong>
        <div>Catalog size: 10,000 items.</div>
        <div>One relevant item per case.</div>
        <div>Five cases per A/B/C profile.</div>
        <div>Uniform negative sampling with replacement.</div>
        <div>Reference sampled negatives: m = 99.</div>
        <div>Root seed: 20260923.</div>
      </div>

      <div class="evidence-card">
        <strong>Evidence boundaries</strong>
        <div id="supported-claims"></div>
        <div id="rejected-claims"></div>
      </div>
    </div>
  </article>
</section>

</main>

<footer class="footer">
  <div class="footer-left">
    <span>
      This dashboard summarizes a reproduction-and-extension study on fixed
      toy-example rank profiles; it does not retrain recommendation models
      or use raw customer-level features.
    </span>
  </div>

  <div class="footer-right">
    Project 8 — Sampled Recommendation Metrics | Results frozen
  </div>
</footer>

</div>

<script id="frozen-data" type="application/json">__FROZEN_JSON__</script>

<script>
"use strict";

const DATA =
  JSON.parse(
    document.getElementById(
      "frozen-data"
    ).textContent
  );

const ROUTES =
  new Set([
    "overview",
    "ap-reversal",
    "sample-size-sweep",
    "validation"
  ]);

function svgElement(
  name,
  attrs = {}
) {
  const node =
    document.createElementNS(
      "http://www.w3.org/2000/svg",
      name
    );

  for (
    const [key, value]
    of Object.entries(
      attrs
    )
  ) {
    node.setAttribute(
      key,
      String(value)
    );
  }

  return node;
}

function clearNode(
  node
) {
  while (
    node.firstChild
  ) {
    node.removeChild(
      node.firstChild
    );
  }
}

function makeSvg(
  container,
  width,
  height
) {
  clearNode(
    container
  );

  const svg =
    svgElement(
      "svg",
      {
        viewBox:
          `0 0 ${width} ${height}`
      }
    );

  container.appendChild(
    svg
  );

  return svg;
}

function addText(
  svg,
  x,
  y,
  text,
  options = {}
) {
  const node =
    svgElement(
      "text",
      {
        x,
        y,
        fill:
          options.fill
          || "#465675",
        "font-size":
          options.size
          || 10,
        "font-weight":
          options.weight
          || 500,
        "text-anchor":
          options.anchor
          || "start"
      }
    );

  node.textContent =
    text;

  svg.appendChild(
    node
  );
}

function metricLabel(
  metric
) {
  return {
    ap: "AP",
    ndcg: "NDCG",
    recall_at_10: "Recall@10",
    auc: "AUC"
  }[
    metric
  ];
}

function metricValue(
  metric,
  value
) {
  const number =
    Number(
      value
    );

  return number.toFixed(
    metric === "recall_at_10"
      ? 4
      : 5
  );
}

function drawVerticalBars(
  id,
  values,
  maximum
) {
  const container =
    document.getElementById(
      id
    );

  if (!container) {
    return;
  }

  const width = 260;
  const height = 215;

  const margin = {
    left: 37,
    right: 10,
    top: 10,
    bottom: 31
  };

  const innerWidth =
    width
    - margin.left
    - margin.right;

  const innerHeight =
    height
    - margin.top
    - margin.bottom;

  const svg =
    makeSvg(
      container,
      width,
      height
    );

  for (
    let tick = 0;
    tick <= 4;
    tick += 1
  ) {
    const fraction =
      tick / 4;

    const y =
      margin.top
      + innerHeight
      - fraction
      * innerHeight;

    svg.appendChild(
      svgElement(
        "line",
        {
          x1: margin.left,
          x2:
            margin.left
            + innerWidth,
          y1: y,
          y2: y,
          stroke: "#E4EAF2"
        }
      )
    );

    addText(
      svg,
      margin.left - 7,
      y + 3,
      (
        maximum
        * fraction
      ).toFixed(
        maximum <= .15
          ? 2
          : 1
      ),
      {
        size: 8,
        anchor: "end"
      }
    );
  }

  const profiles =
    ["A", "B", "C"];

  const gap = 17;

  const barWidth =
    (
      innerWidth
      - gap * 4
    ) / 3;

  profiles.forEach(
    (
      profile,
      index
    ) => {

      const value =
        Number(
          values[
            profile
          ]
        );

      const x =
        margin.left
        + gap
        + index
        * (
          barWidth
          + gap
        );

      const barHeight =
        innerHeight
        * value
        / maximum;

      const y =
        margin.top
        + innerHeight
        - barHeight;

      svg.appendChild(
        svgElement(
          "rect",
          {
            x,
            y,
            width:
              barWidth,
            height:
              Math.max(
                barHeight,
                1
              ),
            fill:
              DATA.colors[
                profile
              ]
          }
        )
      );

      addText(
        svg,
        x
        + barWidth / 2,
        Math.max(
          9,
          y - 5
        ),
        value.toFixed(
          5
        ),
        {
          size: 8,
          weight: 750,
          anchor: "middle"
        }
      );

      addText(
        svg,
        x
        + barWidth / 2,
        height - 9,
        profile,
        {
          size: 9,
          weight: 750,
          anchor: "middle"
        }
      );
    }
  );
}

function logPosition(
  value
) {
  return (
    Math.log10(
      value
    )
  ) / (
    Math.log10(
      9999
    )
  );
}

function drawLineChart(
  id,
  series,
  options = {}
) {
  const container =
    document.getElementById(
      id
    );

  if (!container) {
    return;
  }

  const width = 480;
  const height = 275;

  const margin = {
    left: 42,
    right: 17,
    top: 17,
    bottom: 45
  };

  const innerWidth =
    width
    - margin.left
    - margin.right;

  const innerHeight =
    height
    - margin.top
    - margin.bottom;

  const svg =
    makeSvg(
      container,
      width,
      height
    );

  const yMinimum =
    options.yMin
    ?? 0;

  const yMaximum =
    options.yMax
    ?? 1;

  for (
    let tick = 0;
    tick <= 4;
    tick += 1
  ) {
    const y =
      margin.top
      + innerHeight
      * tick / 4;

    svg.appendChild(
      svgElement(
        "line",
        {
          x1:
            margin.left,
          x2:
            margin.left
            + innerWidth,
          y1: y,
          y2: y,
          stroke:
            "#E3E9F1"
        }
      )
    );

    const value =
      yMaximum
      - (
        yMaximum
        - yMinimum
      )
      * tick / 4;

    addText(
      svg,
      margin.left - 6,
      y + 3,
      value.toFixed(
        2
      ),
      {
        size: 8,
        anchor: "end"
      }
    );
  }

  for (
    const tick
    of DATA.meta.grid
  ) {
    const x =
      margin.left
      + logPosition(
          tick
        )
        * innerWidth;

    addText(
      svg,
      x,
      height - 24,
      String(
        tick
      ),
      {
        size: 7,
        anchor: "middle"
      }
    );
  }

  for (
    const profile
    of ["A", "B", "C"]
  ) {
    const points =
      DATA.meta.grid.map(
        (
          m,
          index
        ) => {

          const value =
            Number(
              series[
                profile
              ][
                index
              ]
            );

          const x =
            margin.left
            + logPosition(
                m
              )
              * innerWidth;

          const y =
            margin.top
            + innerHeight
            - (
                value
                - yMinimum
              )
              / (
                yMaximum
                - yMinimum
              )
              * innerHeight;

          return {
            x,
            y
          };
        }
      );

    svg.appendChild(
      svgElement(
        "polyline",
        {
          points:
            points
              .map(
                point =>
                  `${point.x},${point.y}`
              )
              .join(
                " "
              ),
          fill:
            "none",
          stroke:
            DATA.colors[
              profile
            ],
          "stroke-width":
            2
        }
      )
    );

    for (
      const point
      of points
    ) {
      svg.appendChild(
        svgElement(
          "circle",
          {
            cx:
              point.x,
            cy:
              point.y,
            r:
              3,
            fill:
              DATA.colors[
                profile
              ]
          }
        )
      );
    }
  }
}

function renderProfiles() {

  for (
    const profile
    of ["A", "B", "C"]
  ) {
    const value =
      `[${DATA.profiles[
        profile
      ].join(", ")}]`;

    for (
      const prefix
      of [
        "overview",
        "detail"
      ]
    ) {
      const node =
        document.getElementById(
          `${prefix}-profile-${profile.toLowerCase()}`
        );

      if (node) {
        node.textContent =
          value;
      }
    }
  }
}

function renderValidation(
  bodyId
) {
  const body =
    document.getElementById(
      bodyId
    );

  if (!body) {
    return;
  }

  body.innerHTML = "";

  for (
    const metric
    of [
      "ap",
      "ndcg",
      "recall_at_10",
      "auc"
    ]
  ) {
    const row =
      document.createElement(
        "tr"
      );

    const cells = [
      metricLabel(
        metric
      ),
      metricValue(
        metric,
        DATA.full.metrics.A[
          metric
        ]
      ),
      metricValue(
        metric,
        DATA.full.metrics.B[
          metric
        ]
      ),
      metricValue(
        metric,
        DATA.full.metrics.C[
          metric
        ]
      ),
      DATA.full.orderings[
        metric
      ],
      metricValue(
        metric,
        DATA.sampled_m99.metrics.A[
          metric
        ]
      ),
      metricValue(
        metric,
        DATA.sampled_m99.metrics.B[
          metric
        ]
      ),
      metricValue(
        metric,
        DATA.sampled_m99.metrics.C[
          metric
        ]
      ),
      DATA.sampled_m99.orderings[
        metric
      ]
    ];

    cells.forEach(
      (
        text,
        index
      ) => {
        const cell =
          document.createElement(
            "td"
          );

        cell.textContent =
          text;

        if (index === 0) {
          cell.className =
            "metric";
        }

        if (
          index === 4
          || index === 8
        ) {
          cell.classList.add(
            "order-blue"
          );
        }

        row.appendChild(
          cell
        );
      }
    );

    body.appendChild(
      row
    );
  }
}

function renderCrossovers(
  id
) {
  const node =
    document.getElementById(
      id
    );

  if (!node) {
    return;
  }

  node.innerHTML = "";

  for (
    const interval
    of DATA.crossover_intervals.filter(
      item =>
        item.metric === "ap"
    )
  ) {
    const li =
      document.createElement(
        "li"
      );

    li.textContent =
      `AP ${interval.profiles.join("/")} crossover interval: `
      + `${interval.lower_computed_m}\u2013${interval.upper_computed_m}`;

    node.appendChild(
      li
    );
  }
}

function renderClaims() {
  const supported =
    document.getElementById(
      "supported-claims"
    );

  const rejected =
    document.getElementById(
      "rejected-claims"
    );

  if (
    !supported
    || !rejected
  ) {
    return;
  }

  for (
    const claim
    of DATA.claims.supported
  ) {
    const item =
      document.createElement(
        "div"
      );

    item.className =
      "claim-row";

    item.textContent =
      `${claim.id} ${claim.claim}`;

    supported.appendChild(
      item
    );
  }

  for (
    const claim
    of DATA.claims.rejected
  ) {
    const item =
      document.createElement(
        "div"
      );

    item.className =
      "claim-row";

    item.textContent =
      `${claim.id} ${claim.claim}`;

    rejected.appendChild(
      item
    );
  }
}

function renderCharts() {

  const fullAp = {
    A:
      DATA.full.metrics.A.ap,
    B:
      DATA.full.metrics.B.ap,
    C:
      DATA.full.metrics.C.ap
  };

  const sampledAp = {
    A:
      DATA.sampled_m99.metrics.A.ap,
    B:
      DATA.sampled_m99.metrics.B.ap,
    C:
      DATA.sampled_m99.metrics.C.ap
  };

  drawVerticalBars(
    "overview-full-ap",
    fullAp,
    .12
  );

  drawVerticalBars(
    "overview-sampled-ap",
    sampledAp,
    .8
  );

  drawVerticalBars(
    "detail-full-ap",
    fullAp,
    .12
  );

  drawVerticalBars(
    "detail-sampled-ap",
    sampledAp,
    .8
  );

  drawLineChart(
    "overview-ap-sweep",
    DATA.sensitivity.ap,
    {
      yMin:0,
      yMax:1
    }
  );

  drawLineChart(
    "detail-ap-sweep",
    DATA.sensitivity.ap,
    {
      yMin:0,
      yMax:1
    }
  );

  drawLineChart(
    "detail-ndcg-sweep",
    DATA.sensitivity.ndcg,
    {
      yMin:0,
      yMax:1
    }
  );

  drawLineChart(
    "detail-recall-sweep",
    DATA.sensitivity.recall_at_10,
    {
      yMin:0,
      yMax:1
    }
  );

  drawLineChart(
    "detail-auc",
    DATA.sensitivity.auc,
    {
      yMin:.5,
      yMax:1
    }
  );
}

function routeFromLocation() {
  const route =
    window.location.hash
      .replace(
        /^#/,
        ""
      )
      .trim();

  if (
    !route
    || !ROUTES.has(
      route
    )
  ) {
    return "overview";
  }

  return route;
}

function activateRoute(
  route
) {

  for (
    const page
    of document.querySelectorAll(
      ".page"
    )
  ) {
    page.classList.toggle(
      "active",
      page.dataset.page
      === route
    );
  }

  for (
    const button
    of document.querySelectorAll(
      ".nav-button"
    )
  ) {
    button.classList.toggle(
      "active",
      button.dataset.route
      === route
    );
  }
}

function boot() {
  renderProfiles();

  renderValidation(
    "overview-validation-body"
  );

  renderValidation(
    "detail-validation-body"
  );

  renderCrossovers(
    "overview-crossovers"
  );

  renderCrossovers(
    "detail-crossovers"
  );

  renderClaims();

  renderCharts();

  for (
    const button
    of document.querySelectorAll(
      ".nav-button"
    )
  ) {
    button.addEventListener(
      "click",
      () => {
        window.location.hash =
          button.dataset.route;
      }
    );
  }

  activateRoute(
    routeFromLocation()
  );

  window.addEventListener(
    "hashchange",
    () => {
      activateRoute(
        routeFromLocation()
      );
    }
  );

  window.__P28_DASHBOARD_READY__ = true;

  window.__P28_VISUAL_CONTRACT__ =
    "APPROVED_PREVIEW_V1";
}

boot();
</script>

</body>
</html>
"""

    return template.replace(
        "__FROZEN_JSON__",
        frozen_json,
    )


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
            "AP reversal",
            "Sample-size sweep",
            "Validation",
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
