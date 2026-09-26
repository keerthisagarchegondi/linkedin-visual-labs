# Project 8 — Final Output Specification

Status: **FROZEN — USER APPROVED**

Scientific source of truth:

`assets/p28_sampled_recommendation_metrics/frozen/release_data.json`

This specification controls Steps 6–10 after explicit approval.

---

## 1. Frozen evidence summary

- Full-catalog AP ordering: **C>B>A**
- Expected sampled AP ordering at `m=99`: **A>B>C**
- Full-catalog NDCG ordering: **C>A>B**
- Expected sampled NDCG ordering at `m=99`: **A>C>B**
- Full-catalog Recall@10 ordering: **C>A=B**
- Expected sampled Recall@10 ordering at `m=99`: **A>C>B**
- Full-catalog AUC ordering: **A>C>B**
- Expected sampled AUC ordering at `m=99`: **A>C>B**
- Frozen sample-size grid: **[1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999]**
- Numerical tie tolerance: **1e-12**
- Computed-grid crossover records: **12**

Scientific results are already frozen. Step 5 does not change them.

---

## 2. Strongest evidence-backed headline

> **At 99 sampled negatives, expected AP reverses the model ordering in the frozen A/B/C toy example.**

Short public hook:

> **Same underlying rankings. Different evaluation protocol. Different AP model ordering.**

AP is the primary public metric because the frozen result directly reproduces the ranking-reversal phenomenon that motivates the project.

---

## 3. Secondary findings

1. The sampled-metric behavior changes across the predefined sample-size grid.
2. NDCG and Recall@10 provide supporting evidence that evaluation behavior is metric-specific.
3. AUC acts as the explicit negative control under the frozen protocol.
4. The 1,000-run and 10,000-run Monte Carlo experiments agree with analytical expectations under the preregistered rule.
5. Independent recomputation supports the critical numerical results.
6. Genuine ties remain ties under the frozen `1e-12` tolerance.

---

## 4. Findings not to over-emphasize

Do **not** imply:

- a universal failure of sampled recommendation evaluation;
- production prevalence or real-world frequency;
- an exact crossover between uncomputed `m` values;
- that every sampled metric reverses model selection;
- that A/B/C represent trained production systems;
- paired cross-model Monte Carlo uncertainty;
- a ground-truth universally "best" model.

---

## 5. Metric hierarchy

### Primary

**Average Precision (AP)**

Used for:
- hero headline,
- Figure 1,
- primary dashboard comparison,
- video reversal scene,
- manuscript headline result,
- LinkedIn hook.

### Supporting public metrics

- **NDCG**
- **Recall@10**

Used mainly for sample-size sensitivity.

### Negative control

- **AUC**

Used publicly because it is scientifically important that the project shows a metric that does **not** exhibit the same reversal pathology.

### Detailed evidence / appendix

- complete raw metric tables;
- complete m sweep;
- Monte Carlo SD and SE;
- source-reference reconciliation;
- independent numerical-difference table.

---

## 6. Frozen terminology

Use:

- **full-catalog evaluation**
- **sampled evaluation**
- **expected sampled metric**
- **sampled negatives (`m`)**
- **model profile A/B/C**
- **ranking reversal**
- **computed-grid crossover interval**
- **Monte Carlo standard error (SE)**
- **negative control**

Avoid:

- exact crossover threshold;
- ground-truth best model;
- sampling always picks the wrong model;
- all sampled metrics are biased in the same way;
- paired cross-model Monte Carlo comparison;
- production prevalence;
- universal recommender-system conclusion.

---

## 7. Attribution

Required full language:

> This project independently reproduces and extends a toy ranking example attributed to **Krichene & Rendle**. The A/B/C rank profiles are source-reported inputs; the analytical derivations, Monte Carlo validation, sample-size sweep, visualizations, and communication artifacts are independently implemented here.

Short figure language:

> Toy-example rank profiles adapted from Krichene & Rendle; calculations reproduced independently.

---

## 8. Mandatory toy-example limitation

> The A/B/C profiles form a controlled toy example with five instances per model and one relevant item per instance. The result demonstrates that a ranking reversal can occur under the frozen sampling protocol; it does not estimate how often or how strongly this occurs in production recommender systems.

Sensitivity language:

> Sensitivity conclusions are restricted to the predefined sample-size grid. When a relation changes between adjacent computed values, the project reports that interval and does not infer an exact uncomputed crossover.

---

# 9. Static figures

Exactly **3** final static research figures.

## Figure 1 — Sampling can reverse the AP model ordering

### Question

Does full-catalog AP agree with expected sampled AP at `m=99`?

### Layout

Two-panel ranked-dot comparison.

**Left:** full-catalog AP.

**Right:** expected sampled AP at `m=99`.

Profiles A/B/C retain the same color in both panels.

Frozen orderings printed above panels:

- Full AP: **C>B>A**
- Sampled AP: **A>B>C**

Central annotation:

> Same rank profiles; evaluation protocol changed.

This is the hero figure.

---

## Figure 2 — The ordering depends on how many negatives are sampled

Three vertically aligned small multiples:

1. AP
2. NDCG
3. Recall@10

X-axis uses only the exact frozen grid:

`[1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999]`

Use a log-like/log presentation appropriate to the spacing.

Computed-grid crossover intervals may be annotated.

**No exact uncomputed crossover marker is allowed.**

---

## Figure 3 — Negative control and validation

Upper panel:

- AUC across the sample-size grid;
- explicit full-catalog reference;
- negative-control annotation.

Lower panel:

- analytical expectation versus high-precision Monte Carlo mean;
- A/B/C shown consistently;
- MC SE may be shown where legible.

Detailed SD/SE and reconciliation data remain in tables rather than overcrowding the figure.

---

# 10. Dashboard

## Purpose

An **evidence-first recruiter/research hybrid**.

A recruiter should understand the result in under one minute.

A technical reviewer should be able to audit the result without leaving the HTML.

## Delivery

One self-contained HTML file.

No CDN, external JS, external fonts, remote images, or network dependency.

## Canonical viewport

**1440 × 900 px**

## Visual system

- light research/editorial interface;
- off-white page background;
- white evidence surfaces;
- dark charcoal typography;
- restrained grid lines;
- fixed profile colors.

Profile colors:

- A: `#0072B2`
- B: `#D55E00`
- C: `#009E73`
- AUC/negative-control neutral: `#6B7280`

Font stack:

`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif`

---

## Dashboard tabs

### Overview

- research question;
- one-sentence limitation;
- Figure-1-style AP hero comparison;
- ordering reversal callout;
- validation/scope cards.

### Sensitivity

- metric selector: AP / NDCG / Recall@10 / AUC;
- exact frozen m values only;
- sensitivity chart;
- tie-aware selected-m ordering;
- computed-grid crossover table.

### Validation

- analytical vs 1,000-run MC;
- analytical vs 10,000-run MC;
- sample SD versus MC SE explanation;
- independent recomputation;
- AUC negative-control verification.

### Methods & Evidence

- A/B/C source ranks;
- sampling protocol;
- metric definitions;
- Krichene & Rendle attribution;
- toy-example limitation;
- frozen evidence-file references.

---

## Allowed interactions

- tabs;
- metric selector;
- exact frozen `m` selector;
- hover/tooltips;
- profile highlighting;
- disclosure of methodological details.

## Forbidden interactions

- arbitrary `m` input;
- interpolation;
- browser-side scientific recomputation;
- metric-definition changes;
- sorting that breaks tie semantics;
- animations that imply uncomputed intermediate values.

---

## Dashboard review images

Required screenshots at **1440×900**:

1. Overview
2. Sensitivity — AP / `m=99`
3. Sensitivity — AUC
4. Validation
5. Methods & Evidence

Also create one labeled five-image contact sheet.

---

# 11. Video

Target: **~45 seconds**

Format:

- 16:9
- 1920×1080
- 30 fps
- 6 scenes

## Scene 1 — 0–5 s

Hook.

> Can sampling change which model looks best?

A/B/C model cards establish color identity.

## Scene 2 — 5–12 s

Full-catalog baseline.

> Full-catalog AP: **C>B>A**

## Scene 3 — 12–21 s

Sampling protocol appears.

Transition to `m=99`.

> Expected sampled AP: **A>B>C**

The visual emphasizes that the rank profiles did not change.

## Scene 4 — 21–31 s

Sample-size sensitivity.

AP is primary.

NDCG and Recall@10 appear as supporting views.

No invented intermediate evidence.

## Scene 5 — 31–38 s

AUC negative control + independent validation.

> AUC does not show the same pathology.

Analytical and Monte Carlo markers align.

## Scene 6 — 38–45 s

Final takeaway.

> **Evaluation protocol can change model selection.**

Subhead:

> In this controlled toy example, sampled AP reverses the model ordering; AUC does not.

Footer:

> Toy example • five instances/model • one relevant item/instance

---

## Video animation rules

- Animate only between frozen/computed states.
- Never interpolate scientific values as evidence.
- Profile colors never change.
- Tied models receive equal visual rank.
- Axis scales remain stable inside scenes.
- One primary textual idea per scene.
- No decorative kinetic typography that competes with the evidence.

Required review keyframes:

`3s, 9s, 17s, 27s, 35s, 43s`

Create a **3×2** labeled contact sheet.

---

# 12. Manuscript presentation

Working headline:

> **When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

Result order:

1. Full-catalog evaluation.
2. Expected sampled evaluation at `m=99`.
3. AP ranking reversal.
4. Sample-size sensitivity.
5. Metric-specific behavior and AUC negative control.
6. Monte Carlo + independent validation.
7. Limitations and implications.

Figures:

1. Full vs sampled AP.
2. Sample-size sensitivity.
3. Negative control + validation.

Tables:

1. Frozen A/B/C profiles and protocol.
2. Full and `m=99` metrics/orderings.
3. Validation summary.
4. Appendix: full sample-size sweep.

---

# 13. LinkedIn communication

Narrative:

1. Start with the evaluation question.
2. Show full-catalog AP.
3. Show sampled AP at `m=99`.
4. State that the underlying rank profiles stayed fixed.
5. Show sensitivity to `m`.
6. Show AUC as the negative control.
7. Mention analytical + Monte Carlo validation.
8. End with the practical evaluation lesson.
9. Include attribution and limitation.

Preferred hook:

> **I kept the models fixed and changed only the evaluation protocol. The AP model ordering changed.**

Do not use:

> “Your recommender-system metrics are wrong.”

---

# 14. Cross-artifact consistency rules

1. A/B/C colors never change.
2. Values/orderings come only from frozen Step-4 data.
3. Only predefined `m` values may be shown as computed evidence.
4. Ties use the frozen `1e-12` rule.
5. AUC is always described as the negative control.
6. Toy-example limitation appears in every public artifact.
7. Krichene & Rendle attribution appears in publication-oriented outputs.
8. No exact uncomputed crossover claim.
9. No paired cross-model uncertainty claim.
10. Analytical expectation and Monte Carlo estimate remain distinct.
11. The same three core figures anchor dashboard, manuscript, and LinkedIn communication.

---

# 15. Status

**Steps 5.1–5.36: implementation-ready**

**Step 5.37: APPROVED**

**Step 5.38: COMPLETE — SPECIFICATION FROZEN**
---

# 16. Final implementation rule

The Step-5 preview images are **reference-only**.

The production artifacts must be created from code, frozen data, and the approved contracts:

- static figures must be rendered from frozen release data;
- the HTML dashboard must be constructed as real HTML/CSS/JavaScript/chart components;
- the video must be rendered from coded scenes, chart primitives, text, and animation logic;
- the manuscript must be generated from structured content, tables, figures, and frozen evidence.

The preview images must **not** be used as:

- full-frame backgrounds;
- flattened dashboard substitutes;
- manuscript page backgrounds;
- stock images;
- animation canvases over which text is simply overlaid;
- composited shortcuts in place of coded visual components.

This rule is contractual for Steps 6–10.
