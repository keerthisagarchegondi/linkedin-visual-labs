# Project 8 — Experiment Protocol

## Primary experiments

1. Full-catalog metric calculation.
2. Expected and simulated sampled evaluation at `m = 99`.
3. Frozen negative-draw sensitivity sweep.

## Sensitivity grid

`[1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999]`

## Monte Carlo

- source-protocol comparison: 1,000 repetitions;
- high-precision numerical validation: 10,000 repetitions;
- root seed: `20260923`.

No seed searching is permitted.

## Output discipline

Validated release tables become the only source for downstream figures,
dashboard, video, manuscript, and social material.

## Step 2 deterministic mathematical contract

One-based rank metrics:

- AP = `1/r`
- untruncated NDCG = `1/log2(r+1)`
- Recall@10 = `I(r <= 10)`
- AUC = `(N-r)/(N-1)`

The AP definition equals reciprocal rank only because this study has exactly
one relevant item per evaluation instance.

For source rank `r`, define:

`p = (r-1)/(N-1)`

For `m` uniform irrelevant-item draws with replacement:

`X ~ Binomial(m, p)`

and sampled rank is:

`R = 1 + X`

Expected sampled metrics are calculated through explicit PMF summation.

AP additionally uses the independently derived identity:

`E[1/(1+X)] = [1-(1-p)^(m+1)] / [(m+1)p]`

with explicit `p=0` and `p=1` branches and stable `log1p`/`expm1`
evaluation.

For sampled AUC:

`AUC_sampled = 1 - X/m`

therefore:

`E[AUC_sampled] = 1 - E[X]/m = 1-p`

which equals full-catalog AUC:

`(N-r)/(N-1)`.

This identity is an expectation result. It does not assert that every random
sample preserves a model ordering.

## Step 3 Monte Carlo validation contract

Step 3 introduces an independent stochastic computational path.

The root seed remains the frozen Step-0 value `20260923`.

Random streams are derived deterministically as:

`SHA-256(root_seed + canonical experiment stream key) -> integer seed`

The implementation must not call Python's process-randomized `hash()`.

Each model profile receives a separate deterministic stream. Within a model
profile, AP, NDCG, Recall@10, and AUC are computed from the same simulated
sampled ranks in each repetition because they describe the same sampled
evaluation event.

Separate profile streams mean Step 3 does not estimate cross-model covariance
and must not describe model-to-model Monte Carlo differences as paired unless a
later protocol explicitly introduces paired streams.

For every repetition:

1. simulate all five source instances;
2. compute each metric per instance;
3. average the five values arithmetically.

Across repetitions, report three distinct quantities:

- Monte Carlo mean;
- sample standard deviation across repetition-level means;
- Monte Carlo standard error = standard deviation / sqrt(repetitions).

The source-protocol experiment uses 1,000 repetitions.

The higher-precision validation experiment uses 10,000 repetitions.

A Monte Carlo estimate validates an analytical expectation when:

`abs(mc_mean - analytical_expectation) <= max(5 * MC_SE, 1e-3)`

Seed searching, retrying alternative seeds to obtain agreement, or selecting a
seed after observing results is prohibited.
