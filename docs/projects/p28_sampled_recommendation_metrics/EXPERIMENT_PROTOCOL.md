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
