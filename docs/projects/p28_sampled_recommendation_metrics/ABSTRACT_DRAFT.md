# Project 8 — Abstract Draft

## Manuscript

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

## Abstract

Offline recommender-system evaluation is often performed on sampled
candidate sets rather than the full item catalog, but changing the
candidate set can alter the metric values used for model selection.
This study independently reconstructs and extends a source-reported
toy recommendation-ranking example to examine whether changing only
the evaluation protocol can change which fixed model appears best.

Three fixed rank profiles, each containing five test cases with one
relevant item, are evaluated in a catalog of 10,000 items. We compare
full-catalog metrics with analytical expectations under uniform
negative sampling with replacement, using 99 sampled negatives as the
reference setting. Under full-catalog Average Precision (AP), the
model ordering is C > B > A. Under expected sampled AP at m = 99,
the ordering reverses completely to A > B > C, even though the model
rankings themselves are unchanged.

A sample-size sweep over twelve predefined values of m shows that AP
model ordering varies with the number of sampled negatives. The
computed grid places the A/B crossover between 500 and 1000 sampled
negatives, the A/C crossover between 200 and 500, and B/C crossovers
between 50 and 99 and between 200 and 500. These are interval
statements over the evaluated grid rather than estimates of exact
crossover points.

AUC provides a negative control: its model ordering remains A > C > B
across the tested sample-size grid. Analytical expectations are
checked using Monte Carlo simulations with 1,000 and 10,000
repetitions, independent critical-number recomputation, and
reconciliation against twelve rounded source-reported values.

The results show, for this controlled toy example, that the evaluation
candidate set alone can change which model a ranking-sensitive metric
selects as best. The study does not imply that sampled evaluation is generally
unreliable or that every sampling configuration changes model
selection; rather, it demonstrates why recommender-system model
comparison should treat the evaluation protocol as part of the
measurement design.

## Abstract status

- Draft version: `P28_ABSTRACT_V1`
- Based only on frozen validated Project 8 claims.
- Literature-context wording remains provisional until Step 9.15.
- No novelty claim is made.
- No DOI claim is made.
- No publication-status claim is made.
