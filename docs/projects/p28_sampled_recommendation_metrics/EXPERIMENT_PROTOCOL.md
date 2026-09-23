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
