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
