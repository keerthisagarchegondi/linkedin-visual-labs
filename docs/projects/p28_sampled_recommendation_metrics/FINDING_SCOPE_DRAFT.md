# Project 8 — Finding and Study Scope Draft

## Manuscript

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

## 2. Source example and study scope

### 2.1 Source-reported toy rank profiles

This study begins from a fixed toy recommendation-ranking example
reported in the source literature. The example contains three abstract
model profiles, labeled A, B, and C, with five test cases per profile
and one relevant item per test case. Project 8 does not train these
models or infer how their rankings were produced. Instead, it treats
the reported rank profiles as fixed inputs and asks how the same
rankings are scored under different evaluation candidate sets.

The full evaluation catalog contains 10,000 items. The reference
sampled setting keeps the relevant item and draws 99 negative items
uniformly with replacement. Because the model rankings are held fixed,
the comparison isolates the effect of the evaluation protocol rather
than changes in model fitting, model parameters, training data, or
prediction generation.

### 2.2 What is reproduced

The principal reproduced phenomenon is a model-selection reversal
under Average Precision (AP) when the evaluation candidate set changes.

For the fixed rank profiles, full-catalog AP orders the models as:

`C > B > A`

At the reference sampled setting with `m = 99` negative items, the
analytical expected sampled AP ordering is:

`A > B > C`

Thus, for this controlled toy example, changing the evaluation
candidate set is sufficient to reverse the complete AP ordering even
though the underlying rank profiles remain unchanged.

This result is treated as a reproduction of the selected
source-reported toy phenomenon, not as a claim that Project 8
discovered the general issue of sampled recommender-system evaluation.

### 2.3 What is independently verified

Project 8 independently verifies the toy example rather than treating
reported output values as authoritative inputs to the result pipeline.

The verification includes:

1. independent implementation of the full-catalog metric formulas;
2. analytical expectations for sampled evaluation;
3. deterministic Monte Carlo validation with 1,000 repetitions;
4. higher-precision Monte Carlo validation with 10,000 repetitions;
5. independent recomputation of critical numerical results; and
6. reconciliation of twelve rounded source-reported values.

The Monte Carlo checks are evaluated against the frozen acceptance
criterion:

`abs(MC mean - analytical expectation) <= max(5 * MC standard error, 1e-3)`

These checks provide independent numerical support for the Project 8
results while preserving the distinction between exact analytical
expectations, stochastic simulation estimates, and rounded
source-reported values.

### 2.4 What Project 8 extends

Project 8 extends the selected toy example in three principal ways.

First, it evaluates expected sampled metrics over the predefined
sample-size grid:

`1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999`

This makes it possible to examine how metric values and model ordering
change as the number of sampled negatives increases.

Second, it reports computed-grid intervals within which AP ordering
changes occur. The frozen intervals are:

- A/B: `500–1000`
- A/C: `200–500`
- B/C: `50–99`
- B/C: `200–500`

These intervals indicate where the ordering differs between adjacent
evaluated grid points. They are not estimates of exact crossover
locations between those grid points.

Third, Project 8 uses AUC as an explicit negative control. Across the
tested sample-size grid, the AUC ordering remains:

`A > C > B`

The contrast between AP and AUC shows that the observed ranking
sensitivity is metric-dependent within this toy setting. It does not
establish that one metric is universally preferable to another.

### 2.5 Central finding

The central Project 8 finding is therefore narrowly stated:

> For the fixed three-profile toy example examined here, changing only
> the evaluation candidate set changes the model ordering selected by
> Average Precision: full-catalog AP gives `C > B > A`, while expected
> sampled AP at `m = 99` gives `A > B > C`.

The important experimental feature is that the rank profiles do not
change. The measured difference arises from changing the candidate set
over which the metric is evaluated.

This establishes a concrete, independently reproducible example in
which evaluation design affects model selection.

### 2.6 What this study does not establish

The study does not establish that sampled evaluation is generally
unreliable.

It does not establish that:

- every sampled metric changes model ordering;
- every recommendation model comparison is sensitive to negative
  sampling;
- the same reversal occurs for all datasets, catalog sizes, relevance
  structures, or sampling distributions;
- the observed toy behavior estimates how frequently model-selection
  reversals occur in production systems;
- any exact AP crossover point lies at a particular value between the
  evaluated sample-size grid points;
- the entire source paper has been independently reproduced;
- Project 8 is the first work to identify the general issue of sampled
  recommendation evaluation.

Accordingly, the Project 8 contribution is best characterized as an
independent reproducible reconstruction and extension of a selected
source-reported toy example, with analytical expectations,
deterministic simulation checks, sample-size sensitivity analysis,
computed-grid crossover intervals, and an explicit AUC negative
control.

## Draft status

- Version: `P28_FINDING_SCOPE_V1`
- Status: draft
- Based only on frozen Project 8 scientific claims.
- Primary-source literature verification remains pending Step 9.15.
- No novelty claim is made.
- No publication-status claim is made.
- No DOI claim is made.
