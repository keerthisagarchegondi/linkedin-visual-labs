# Project 8 — Independent Implementation Draft

## Manuscript

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

## 4. Independent implementation

### 4.1 Implementation separation

Project 8 was implemented as a self-contained analytical workflow
inside the `p28_sampled_recommendation_metrics` project package. The
implementation starts from the fixed A/B/C rank profiles and the
evaluation assumptions defined for this study. It does not train,
fine-tune, or otherwise estimate recommendation models.

The computational workflow separates four types of evidence:

1. deterministic analytical calculations from the fixed rank profiles;
2. stochastic Monte Carlo simulations used to check the analytical
   expectations;
3. source-reported rounded values used only for reconciliation; and
4. frozen release artifacts used to preserve the validated Project 8
   results.

This separation is important because the source-reported rounded
numbers are not used as inputs to produce the analytical Project 8
results. They are compared against independently calculated values
after those values have been produced.

The term *independent implementation* is used here in this technical
sense. It describes a separately implemented computational
reconstruction and validation workflow. It does not imply a legal
clean-room process, independent discovery of the underlying
phenomenon, or reproduction of every experiment in the source work.

### 4.2 Deterministic configuration

Study assumptions are centralized in the Project 8 configuration
layer rather than being redefined separately in each analysis stage.

The frozen configuration specifies:

- catalog size `N = 10,000`;
- one relevant item per test case;
- five test cases per model profile;
- reference sampled-negative count `m = 99`;
- uniform negative sampling with replacement;
- Monte Carlo seed `20260923`;
- Monte Carlo repetition counts of `1,000` and `10,000`;
- formula tolerance `1e-12`;
- tie tolerance `1e-12`; and
- the twelve-value sampled-negative grid used for sensitivity
  analysis.

Keeping these values under one deterministic contract reduces the
risk that analytical calculations, simulation, validation, and
presentation layers silently use different experimental settings.

### 4.3 Fixed A/B/C rank profiles

The implementation begins with three fixed model profiles:

- Model A: `[100, 100, 100, 100, 100]`
- Model B: `[40, 40, 8437, 9266, 4482]`
- Model C: `[212, 2, 743, 5342, 1548]`

Each value is the full-catalog rank of the single relevant item in one
of five test cases.

These profiles remain unchanged throughout full-catalog evaluation,
sampled analytical evaluation, the sample-size sweep, and Monte Carlo
validation. Consequently, changes in model ordering are attributable
to the evaluation protocol applied to the fixed rankings rather than
to retraining or changing the models.

### 4.4 Analytical evaluation pipeline

The metric and sampling components implement the mathematical
definitions specified in Section 3.

For a relevant item with full-catalog rank `r`, the sampling layer
uses

`p = (r - 1) / (N - 1)`

and the sampled-rank model

`X ~ Binomial(m, p)`

with

`R = 1 + X`.

The analytical pipeline then evaluates full-catalog and expected
sampled AP, NDCG, Recall@10, and AUC from these quantities.

Expected sampled metrics are calculated from the probability
distribution implied by the frozen sampling protocol. They are not
estimated from the Monte Carlo runs. This distinction allows the
simulation layer to act as an independent numerical check of the
analytical expectations rather than as the source of those
expectations.

Model-level results are computed by averaging the five case-level
values for each fixed model profile.

### 4.5 Monte Carlo implementation

The simulation layer independently samples from the frozen
sampled-rank process and compares empirical metric means with their
analytical expectations.

Two repetition counts are used:

- `1,000`; and
- `10,000`.

The random seed is fixed at `20260923`.

For each validation target, the Monte Carlo result passes when

`abs(mc_mean - expectation) <= max(5 * MC_SE, 1e-3)`.

The simulation therefore functions as a reproducibility and numerical
consistency check. It is not used to replace the analytical expected
metric values and is not presented as an inferential hypothesis test.

### 4.6 Validation and source reconciliation

Validation is performed separately from the core analytical
calculation.

Project 8 checks:

- analytical identities and numerical consistency;
- agreement between Monte Carlo means and analytical expectations;
- critical numerical values through an independent recomputation path;
- ordering and tie behavior under the frozen `1e-12` tolerance; and
- reconciliation of twelve rounded source-reported values.

The source reconciliation step is deliberately downstream of the
Project 8 calculations. A rounded source value can support
reconciliation, but it is not substituted for an independently
calculated analytical result.

This design also preserves discrepancies rather than silently
rewriting Project 8 outputs to agree with an external rounded value.

### 4.7 Frozen result artifacts

After the analytical, simulation, and validation stages passed their
quality gates, Project 8 froze the validated research outputs into a
small set of machine-readable artifacts.

The frozen result layer includes:

- `full_metrics.csv`;
- `sampled_metrics.csv`;
- `sample_size_sweep.csv`;
- `validation_results.json`;
- `release_data.json`;
- `claim_register.json`; and
- `run_manifest.json`.

`release_data.json` is the frozen manuscript-facing numerical source
of truth established earlier in Project 8.

The claim register separately records which conclusions are supported
by the validated evidence and which stronger interpretations are
excluded. This prevents later presentation or manuscript steps from
quietly expanding the scientific claims beyond the completed
experiment.

### 4.8 Reproducibility controls

The repository uses several controls to make the Project 8 workflow
auditable and repeatable.

First, the experimental constants and rank profiles are fixed before
manuscript drafting. Second, deterministic analytical calculations
are separated from stochastic simulation. Third, the Monte Carlo seed
and repetition counts are fixed. Fourth, numerical ordering is based
on unrounded values rather than display-rounded values. Fifth, frozen
research artifacts are checked for immutability during later
documentation steps.

The repository also maintains Project 8-specific automated tests.
These tests exercise the scientific implementation and continue to be
run during manuscript construction so that documentation changes do
not silently alter the validated computational pipeline.

Finally, the manuscript workflow records its own state and continuity
metadata. Each completed drafting sub-step identifies the version
created, the validation performed, and the next permitted step.

These controls are intended to support reproducibility of this
specific toy-example study. They do not establish that the
implementation reproduces the complete source paper or that the
observed behavior generalizes to production recommender systems.

## Draft status

- Version: `P28_INDEPENDENT_IMPLEMENTATION_V1`
- Status: draft
- Repository implementation inspected during Step 9.5.
- Analytical calculation, Monte Carlo validation, and source
  reconciliation are explicitly separated.
- Source-reported rounded values are not analytical-result inputs.
- No model training is performed.
- No legal clean-room claim is made.
- No whole-paper reproduction claim is made.
- No first-discovery claim is made.
- Literature attribution remains pending Step 9.15.
- No publication-status claim is made.
- No DOI claim is made.
