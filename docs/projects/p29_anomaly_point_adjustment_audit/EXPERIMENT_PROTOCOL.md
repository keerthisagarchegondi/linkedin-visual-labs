# Project 9 Experiment Protocol

## Frozen design

- `N = 20000`; `P = 1000`; prevalence `P / N = 0.05`.
- Event cardinalities: `1, 5, 10, 20, 50, 100, 200, 500, 1000`.
- Bernoulli alert probabilities: `0.001, 0.005, 0.01, 0.05, 0.10`.
- Primary presentation condition: `L = 200`, `q = 0.01`.
- Initial repetitions: `2000` per condition. Only a documented runtime pilot may change repetitions; it may not change conditions, grids, primary condition, thresholds, or seeds to improve results.

## Event layout

For equal length `L`, `K = P / L`. Events are deterministic disjoint half-open intervals `[start, stop)` with `stop - start = L`, at least one normal timestamp between events, and no boundary crossing or accidental merging. Generation rules and checksums will be frozen with implementation.

## Explicit generative model

For independent per-timestamp Bernoulli alerts with probability `q`, event-hit probability is `h(L,q) = 1 - (1-q)^L`. Required properties: `h(L,0)=0`, `h(L,1)=1`, and `h(1,q)=q`.

For disjoint events `L_j`, `P = sum(L_j)` and `N0 = N - P`:

- `E[TP_raw] = Pq`; `E[FP_raw] = N0q`.
- `E[FP_adjusted] = N0q`.
- `E[TP_adjusted] = sum(L_j * (1 - (1-q)^L_j))`.
- Expected adjusted recall is `E[TP_adjusted] / P` when `P > 0`.

`E[F1]` is not, in general, F1 applied to expected counts. The latter is named `ratio_of_expected_counts_f1` and is a reference, not exact finite-run expected F1.

## Step 2 scoring conventions and reference scope

Events are maximal contiguous positive-label runs represented as immutable half-open intervals `[start, stop)`. Raw and adjusted scoring use explicit binary pointwise vectors and immutable confusion counts. Precision is `None` when no positives are predicted; recall is `None` when no labels are positive; F1 is `None` only when neither labels nor predictions are positive. Thus undefined rates are not silently reported as zero.

Standard point adjustment takes a fresh copy of the raw predictions. A raw positive anywhere in a true event marks that whole event positive; values outside true events are unchanged. The raw artifact is never mutated or aliased.

The Step 2 exact enumerator is intentionally limited to small timelines with at least one positive label, so every enumerated F1 is defined under this convention. It enumerates all binary prediction vectors and their Bernoulli probability mass; it is an exact finite-run reference, not a Monte Carlo result. No Project 9 result has been generated at this step.

## Randomness and paired comparison

Later implementation uses NumPy's documented RNG and an explicit stream-ID scheme, never Python `hash()`. Semantic-fixture, condition-simulation, and presentation seeds are separate. Random-score generation accepts length and RNG only; it cannot read labels or tune a threshold from labels.

Each replicate generates one raw prediction artifact. Raw metrics use it directly; PA receives a copy. Scores, labels, and raw predictions may not be mutated. The raw prediction hash must match before and after evaluation.

The sufficient-count simulator uses `Z_j ~ Binomial(L_j,q)` and `F ~ Binomial(N0,q)`; raw `TP=sum(Z_j)`, adjusted `TP=sum(L_j * 1{Z_j>0})`, and both false-positive counts equal `F`. The same `Z_j` and `F` pair raw and adjusted values. Batched counts are required; no repetitions-by-timestamps-by-settings tensor. A timeline implementation remains the semantic oracle for fixtures.
