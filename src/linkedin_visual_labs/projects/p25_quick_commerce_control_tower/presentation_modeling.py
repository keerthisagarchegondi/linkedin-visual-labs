"""Read-only modeling transparency grounded in the implemented Step 2/3 pipeline."""

from __future__ import annotations

from typing import Any

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    Evidence,
)


def importance_rows(e: Evidence) -> list[dict[str, Any]]:
    """Rank raw input permutations without grouping, clipping or rescaling their effects."""
    rows = e.tables["hist_gradient_boosting_importance"]
    if not rows or any(
        r["classification"] != "training_in_sample_interpretation"
        or r["sample_policy"] != "last_256_training_feature_rows"
        or r["sample_rows"] != 256
        or r["repeats"] != 3
        for r in rows
    ):
        raise ValueError("Unexpected HGB interpretation provenance")
    return sorted(rows, key=lambda r: (-float(r["mean_mae_increase"]), str(r["feature"])))


def modeling_html() -> str:
    return """
<details class="modeling-transparency"><summary>How the modeling dataset was built</summary>
<h3>Target / dependent variable</h3>
<p>Daily demand units at date \u00d7 store \u00d7 category: the value the models forecast.</p>
<h3>Features / independent variables</h3>
<p>Historical demand: lag 28, lag 35, lag 42, lag 49 and lag 56; 7-day and 14-day
historical means ending at t\u221228. Calendar: weekday, month, event name/type (both
calendar event slots) and state-specific SNAP indicator. Entity: store and category.</p>
<h3>Data preparation</h3>
<p>Source schema and identifier validation; ordered d_N demand-column validation;
filtering to FOODS and HOUSEHOLD; DuckDB aggregation from item-level M5 data to
store-category-date before loading the compact result into pandas; continuous-date
and duplicate-grain checks; nonnegative-demand validation; complete calendar joins;
state-specific SNAP mapping; published raw file checksum verification and SHA-256
recording; deterministic caching with verified metadata.</p>
<p>Missing demand and required canonical fields are rejected, not imputed. Genuine
zeros remain. Empty event labels mean no event; absent optional second-event columns
become empty strings. Initial training rows without full lag history are excluded
from model-ready training features; all 560 holdout observations remain.</p>
<h3>Leakage-safe feature engineering</h3>
<p class="workload-flow">Raw demand → aggregate store-category series → safe historical lags
→ rolling historical summaries → calendar/event/SNAP context → model-ready features</p>
<p>Every demand-derived feature uses information available at forecast time. The common
holdout is 28 days, so lag 28+ and rolling windows ending at t\u221228 never read actual
demand inside that future window. Event and SNAP schedules are assumed known at origin.
Targets remain separate from predictors; preprocessing is fitted on training data only.</p>
<h3>Model-specific preprocessing</h3>
<ul><li>Seasonal Naïve: lag-28 demand; no scaling.</li>
<li>Holt-Winters: local time-series fit with weekly seasonality; no feature
standardization required.</li>
<li>HistGradientBoosting: tree splits generally do not need numeric standardization;
numeric inputs pass through. Store/category, weekday and event name/type fields use deterministic
dense one-hot encoding fitted on training data; unknown categories are ignored.</li>
<li>MLP: the same categorical encoding plus StandardScaler for numeric features.
The target is also standardized using training data only and predictions are transformed
back to demand units. Hidden layers: 128, 64, 32.</li></ul>
<h3>How models were validated</h3>
<p>Level 1 — Forecast performance: WAPE measures total absolute error relative to demand;
MAE measures average absolute error in daily units; bias measures signed error relative
to demand, with negative values indicating underforecast.</p>
<p>Level 2 — Governance quality: complete unique 28-day predictions, finite values,
nonnegative postprocessing (finite negatives clipped to zero and recorded), absolute
bias ≤ 10%, and deterministic validation. Missing/nonfinite forecasts are rejected.</p>
<p>Among eligible models, lowest WAPE becomes the local champion with stable tie-breaking.
Lowest raw error alone is insufficient: an incomplete model or one beyond the bias
guardrail should not win. No eligible model triggers review. Selection and reported
local performance use the same holdout; confirm on an untouched period before promotion.</p>
</details>
"""


def diagnostics_purpose() -> str:
    return """<h3>Why diagnose forecast error?</h3>
<p>Convert forecast misses into an action backlog. Find operationally meaningful misses;
investigate concentration by store, category, weekday, event or SNAP context; review
model disagreement; turn recurring patterns into model, data or process experiments.</p>
<p class="workload-flow">Forecast error → prioritize → investigate → form hypothesis
→ test experiment → recalibrate/retrain</p>
<p>Highest-value forecast improvement opportunities:</p>"""


def production_inputs(*, optimizer: bool = False) -> str:
    title = (
        "What would improve the optimizer?"
        if optimizer
        else "What would make this production-ready?"
    )
    return (
        '<details class="production-inputs"><summary>' + title + "</summary>"
        "<p>The prototype intentionally uses simplified illustrative assumptions, equal "
        "priorities and illustrative productivity. It tests constrained allocation mechanics; "
        "production-optimal staffing requires calibration with actual operational economics.</p>"
        "<ul><li>Differentiated store-specific service importance and category-specific "
        "shortage / SLA cost</li><li>Actual store/category productivity variation</li>"
        "<li>Employee shift structure, scheduling constraints and local staffing rules</li>"
        "<li>Labor availability</li><li>Peak-period service-level targets and event-specific "
        "operational policies</li><li>Inventory availability, replenishment timing and "
        "constraints</li><li>Forecast uncertainty</li></ul></details>"
    )


def operating_system() -> str:
    return """<div class="overview-grid operating-system">
<article><h3>MONITOR</h3><p>WAPE, bias, completeness and disagreement.</p></article>
<article><h3>REVIEW</h3><p>No-eligible-champion series, high-priority exceptions and persistent
variance drivers.</p></article>
<article><h3>EXPERIMENT</h3><p>Features, recalibration, retraining, optimization priorities
and operational assumptions.</p></article>
<article><h3>DEPLOY / ESCALATE</h3><p>Promote a validated challenger; escalate ambiguous
series; validate objective changes on untouched periods.</p></article></div>
<details><summary>Proposed review cadence, triggers and ownership</summary>
<p>Review each completed 28-day window. Retraining review: incumbent WAPE exceeds the
matched seasonal-naïve baseline on that untouched window. Recalibration review: absolute
bias exceeds 10%. Escalate incomplete/invalid forecasts or no eligible champion immediately;
review disagreement above 0.50 and operational shortfall above 8 hours. These triggers
request investigation, never automatic promotion. Version thresholds before evaluation.</p>
<p>Operations owns capacity and service assumptions; Product owns decision usefulness;
Engineering owns reliable data and execution; Data Science owns leakage-safe evaluation,
diagnostics and challenger experiments. Monitor clipping alongside the core metrics.
These are proposed practices, not an implemented production service.</p></details>"""


def takeaway(e: Evidence) -> str:
    from html import escape

    return (
        "<p>This prototype demonstrates an end-to-end forecasting operating loop: compare "
        "methods, govern local champions, diagnose misses, translate demand into constrained "
        "labor allocation and stress-test the operating objective.</p><p>"
        + escape(e.portfolio)
        + " Selection is retrospective. The analysis identifies the operational parameters "
        "needed for production calibration; it does not measure production impact.</p>"
    )
