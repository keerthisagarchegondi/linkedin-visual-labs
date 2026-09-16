# Experiment Protocol

## Pre-registered hypotheses

1. H1 — Post-action feature leakage.
2. H2 — Temporal validation instability.
3. H3 — Transformation contamination.
4. H4 — Duplicate contamination.
5. H5 — Post-outcome proxy.
6. H6 — Business-decision distortion.
7. H7 — Automated deployment gate.

## Source-order split

- first 70%: training;
- next 15%: validation;
- final 15%: test.

No shuffle is permitted before chronological construction.

## Random comparison

The same safe feature set and comparable partition proportions are used with
seed 1729 and stratification where valid.

## Exactly five V1 leakage cases

- current-call duration;
- random temporal mixing;
- global supervised transformation;
- duplicate overlap;
- post-outcome confirmation proxy.

No numerical outcome is pre-specified.
