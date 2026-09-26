# Project 8 — Continuity

## Current milestone

Step 2 — rank metrics and analytical sampling engine.

## Completed

- Step 0 — repository/source/contract freeze.
- Step 1 — minimal scaffold and reproducibility contracts.
- Step 2 — deterministic rank metrics and analytical sampled expectations.

## Deterministic scientific engine

Implemented:

- one-based rank validation;
- AP / reciprocal-rank equivalence for the single-positive setting;
- untruncated NDCG;
- Recall@10;
- full-catalog AUC;
- arithmetic averaging;
- uniform-with-replacement outrank probability;
- stable binomial PMF;
- expected sampled AP through PMF summation;
- independent AP closed form;
- expected sampled NDCG;
- expected sampled Recall@10;
- expected sampled AUC;
- independent AUC identity;
- explicit `p=0` and `p=1` branches;
- small-space exact-enumeration reconciliation.

## Scientific result status

No final Project 8 experiment result has been frozen.

Step 2 validates mathematical machinery only.

## Next permitted step after Step 2 PASS

Project 8 — Step 3 — Monte Carlo engine and independent scientific validation.

## Step 3 implementation

The repository now contains an independent Monte Carlo path based on explicit
Bernoulli negative-draw simulation.

Step 3 validates:

- SHA-256-derived deterministic random streams;
- no use of Python `hash()`;
- five-instance averaging inside every repetition;
- distinct Monte Carlo mean, sample standard deviation, and standard error;
- 1,000-repetition source-protocol validation;
- 10,000-repetition higher-precision validation;
- deterministic reruns;
- analytical-versus-Monte-Carlo agreement under the frozen acceptance rule;
- independent AP PMF-versus-closed-form reconciliation.

Model profiles use independent streams. Metrics within a model profile share
the same sampled evaluation events. Step 3 therefore makes no paired
cross-model uncertainty claim.

No final result or ranking-reversal claim is frozen at Step 3.

## Step 4 scientific freeze

Step 4 computes and freezes the complete scientific evidence package.

The frozen artifacts are stored under:

`assets/p28_sampled_recommendation_metrics/frozen/`

They become the sole scientific source of truth for Steps 5–10.

Frozen decisions include:

- full-catalog metrics and tie-preserving model orderings;
- expected sampled metrics at m=99;
- the entire preregistered sample-size grid;
- source-protocol and high-precision Monte Carlo validation;
- independent critical-number recomputation;
- AUC as a negative control;
- source-reference reconciliation without definition changes;
- crossover intervals only between adjacent computed sample counts;
- a public-safety claim register.

Exact crossover points between computed grid values are not inferred.

Step 4 freezes scientific results but does not freeze visual/output design.

## Step 5 output design freeze — awaiting user approval

Steps 5.1–5.36 define the evidence-backed communication design for:

- three static research figures;
- one self-contained HTML dashboard;
- one approximately 45-second six-scene explainer video;
- manuscript figure/table hierarchy;
- LinkedIn communication narrative;
- cross-artifact terminology, attribution, limitation and visual rules.

The scientific source of truth remains the frozen Step-4 release package.

Step 5.37 requires explicit user review and approval.

Until that approval is received:

- `results_frozen` remains `true`;
- `output_design_frozen` remains `false`;
- Step 6 is not allowed;
- no Step-5 Git checkpoint is committed.

## Step 5 specification freeze

Step 5 is complete.

The user reviewed the preview renderings for:

- the approximately 45-second video;
- the dashboard;
- the manuscript.

The previews were accepted as design references.

The output design is now frozen.

Important implementation constraint:

Preview images are reference-only and must not be used as backgrounds,
flattened canvases, stock imagery, or composited substitutes for the
actual coded production artifacts.

Steps 6–10 must generate their outputs programmatically from:

1. the frozen Step-4 scientific release data; and
2. the frozen Step-5 output design contract.

Next allowed step:

`Project 8 — Step 6 — Final static research figures`

## Step 6 final static research figures

Step 6 is complete.

Three final research figures were generated programmatically from the
frozen Step-4 scientific release data and frozen Step-5 design contract:

1. `figure_1_ap_reversal`
   - full-catalog AP versus expected sampled AP at `m=99`
   - ordering reversal `C>B>A` to `A>B>C`

2. `figure_2_sample_size_sensitivity`
   - AP, NDCG and Recall@10 on the predefined frozen sample-size grid
   - no exact uncomputed crossover inference

3. `figure_3_negative_control_validation`
   - AUC negative control
   - analytical versus Monte Carlo validation

Each final figure exists as PNG and SVG.

Preview images were not used in production rendering.

Next allowed step:

`Project 8 — Step 7 — Final self-contained HTML dashboard`

## Step 7 final self-contained HTML dashboard

Step 7 is complete.

Final dashboard:

`assets/p28_sampled_recommendation_metrics/dashboard/index.html`

Implementation properties:

- self-contained HTML;
- inline CSS;
- inline JavaScript;
- browser-generated SVG chart primitives;
- frozen Step-4 scientific evidence;
- frozen Step-5 visual contract;
- no preview images;
- no stock images;
- no Step-6 figures used as flattened dashboard backgrounds;
- no external JavaScript;
- no external stylesheet dependencies.

Frozen dashboard sections:

1. Overview
2. Sensitivity
3. Validation
4. Methods & Evidence

Canonical browser viewport:

`1440x900`

Five actual browser-rendered reference screenshots and one contact
sheet are hashed into the dashboard manifest.

Next allowed step:

`Project 8 — Step 8 — Final ~45-second animated explainer video`

## Step 7 — Sub-step 7.1.B approved-preview visual-fidelity reconstruction

The Step-7 presentation layer was reconstructed to follow the approved visual preview while preserving all frozen scientific values.

Primary navigation:

1. Overview
2. AP reversal
3. Sample-size sweep
4. Validation

The Overview contains four KPI cards, one insight strip, and the AP reversal, sample-size sweep and validation panels simultaneously.

Methods & Evidence remains supporting content inside Validation rather than a top-level tab.

Visual contract: `APPROVED_PREVIEW_V1`.

## Step 7 — Sub-step 7.1.C.1 recruiter-readable dashboard approval and official freeze

The recruiter-readable 7.1.C preview was reviewed and approved.

The official dashboard now leads with a plain-English project explanation before presenting technical evidence.

Audience layers:

- recruiter / hiring-manager explanation;
- beginner analyst experiment walkthrough;
- detailed technical metrics and validation.

The Overview story order is:

1. What is this project?
2. Experiment in three steps
3. Main finding / why it matters
4. KPI summary
5. Technical evidence

Typography was enlarged across KPI labels, panel subtitles, rank-profile text, crossover findings, validation tables, PASS cards, evidence text and footer copy.

Scientific values and frozen inputs were unchanged.

Audience contract: `RECRUITER_BEGINNER_TECHNICAL_V1`.

## Step 9 — Sub-step 9.1 final manuscript-structure freeze and Step-9 entry gate

Project 8 entered Step 9 with the manuscript architecture frozen under `P28_MANUSCRIPT_CONTRACT_V1`.

Frozen manuscript title:

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

The manuscript is structured to distinguish:

- reproduction of the selected source-reported toy example;
- independent verification;
- extension through sample-size sensitivity, computed-grid crossover intervals, and the AUC negative control.

Central scientific contract remains:

- full AP: `C > B > A`;
- sampled AP at `m = 99`: `A > B > C`;
- AUC: `A > C > B`.

No exact crossover values may be inferred between computed grid points.

No universal sampled-metric reversal claim is permitted.

Step 8 video status is recorded truthfully as an accepted creative artifact generated outside the Windows repository workflow. No repository file path, repository hash, DOI, archive identifier, or publication status is invented for that artifact.

Next allowed sub-step:

**Project 8 — Step 9 — Sub-step 9.2 — Draft abstract from validated claims**

## Step 9 — Sub-step 9.2 abstract draft

Drafted the Project 8 manuscript abstract as `P28_ABSTRACT_V1` from the frozen validated scientific contract.

The abstract follows the frozen sequence:

1. Background
2. Problem
3. Study design
4. Central AP result
5. Sample-size extension
6. AUC negative control
7. Validation
8. Bounded conclusion

Central results:

- full AP: `C > B > A`;
- sampled AP at `m = 99`: `A > B > C`;
- AUC negative control: `A > C > B`.

Repairs:

- `9.2.A`: replaced a negated phrase that collided with the literal prohibited-claim scanner;
- `9.2.A.A`: changed semantic validation to normalize Markdown whitespace before matching logical-order, crossover, and bounded-conclusion markers.

The 9.2.A.A repair did not alter the abstract prose or scientific meaning.

The abstract reports only computed-grid crossover intervals and does not claim exact crossover points.

No universal sampled-metric failure, novelty, publication, peer-review, or DOI claim is made.

Primary-source reference verification remains deferred to Step 9.15.

Next allowed sub-step:

**Project 8 — Step 9 — Sub-step 9.3 — Draft original finding/scope section**
