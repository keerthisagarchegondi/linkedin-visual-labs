# Appendix G — Reproducibility

## G.1 Reproducibility objective

This appendix records the frozen analytical contract, deterministic settings,
validation rules, and artifact lineage for Project 8, **When Sampled Recommendation
Metrics Change Model Selection: A Reproducible Toy-Example Study**.

The purpose is to make the reported toy-example results auditable and repeatable
without expanding the manuscript's claims beyond the completed experiment.

## G.2 Frozen study configuration

The study uses the following fixed configuration:

| Item | Frozen value |
|---|---|
| Catalog size | `N = 10,000` |
| Relevant items per test case | `1` |
| Test cases per model profile | `5` |
| Reference sampled negatives | `m = 99` |
| Negative sampling | Uniform, with replacement |
| Monte Carlo seed | `20260923` |
| Monte Carlo repetitions | `1,000` and `10,000` |
| Formula tolerance | `1e-12` |
| Tie tolerance | `1e-12` |
| Sample-size grid | `1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999` |

No manuscript step changes these scientific settings.

## G.3 Fixed rank profiles

The three model profiles are abstract fixed rank profiles rather than trained
models.

| Model | Full-catalog relevant-item ranks |
|---|---|
| A | `[100, 100, 100, 100, 100]` |
| B | `[40, 40, 8437, 9266, 4482]` |
| C | `[212, 2, 743, 5342, 1548]` |

The rank profiles remain unchanged across full-catalog evaluation, sampled
analytical evaluation, the sample-size sweep, and Monte Carlo validation.

## G.4 Mathematical contract

For a test case with full-catalog relevant-item rank `r`:

`p = (r - 1) / (N - 1)`

`X ~ Binomial(m, p)`

`R = 1 + X`

where `X` is the number of sampled negatives ranked ahead of the relevant item
and `R` is the sampled rank.

The metric definitions used in the frozen implementation are:

- Full-catalog AP: `1 / r`
- Sampled AP: `1 / R`
- Full-catalog NDCG: `1 / log2(r + 1)`
- Sampled NDCG: `1 / log2(R + 1)`
- Full-catalog Recall@10: `I(r <= 10)`
- Sampled Recall@10: `I(R <= 10)`
- Full-catalog AUC: `(N - r) / (N - 1)`
- Sampled AUC: `1 - X / m`

Model-level results are arithmetic means across the five fixed cases.

## G.5 Frozen full-catalog baseline

Displayed manuscript values are rounded to four decimal places.

| Model | AP | AUC | NDCG | Recall@10 |
|---|---:|---:|---:|---:|
| A | 0.0100 | 0.9901 | 0.1502 | 0.0000 |
| B | 0.0101 | 0.5548 | 0.1217 | 0.0000 |
| C | 0.1014 | 0.8431 | 0.2080 | 0.2000 |

Frozen orderings:

- AP: `C > B > A`
- AUC: `A > C > B`
- NDCG: `C > A > B`
- Recall@10: `C > A = B`

Orderings are determined from unrounded values, not from displayed four-decimal
values.

## G.6 Frozen expected sampled results at m = 99

Displayed manuscript values are rounded to four decimal places.

| Model | AP | AUC | NDCG | Recall@10 |
|---|---:|---:|---:|---:|
| A | 0.6366 | 0.9901 | 0.7290 | 1.0000 |
| B | 0.3407 | 0.5548 | 0.4473 | 0.4000 |
| C | 0.3262 | 0.8431 | 0.4600 | 0.5694 |

Frozen orderings at `m = 99`:

- AP: `A > B > C`
- AUC: `A > C > B`
- NDCG: `A > C > B`
- Recall@10: `A > C > B`

The central toy-example result is the AP ordering change from `C > B > A` in
the full catalog to `A > B > C` at `m = 99`, while the underlying rank profiles
remain fixed.

## G.7 Sample-size sensitivity contract

The predefined sampled-negative grid is:

`1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999`

Key AP ordering checkpoints:

- `m = 1`: `A > C > B`
- `m = 99`: `A > B > C`
- `m = 500`: `C > A > B`
- `m = 1000`: `C > B > A`
- `m = 9999`: `C > B > A`

Computed-grid AP crossover intervals:

- A/B: `500–1000`
- A/C: `200–500`
- B/C: `50–99`
- B/C: `200–500`

These are interval statements over adjacent evaluated grid points only. The
project does not interpolate or estimate exact crossover locations.

## G.8 AUC negative control

Under the frozen sampling protocol:

`E[AUC_sampled | r, m] = AUC_full(r)`

Therefore, expected sampled AUC is invariant to `m` in this toy setting.

The frozen AUC ordering is:

`A > C > B`

across the tested sample-size grid.

The maximum analytical sampled-versus-full AUC difference is `0.0000`.

## G.9 Monte Carlo validation

Analytical sampled-metric expectations are checked with two simulation scales:

- `1,000` repetitions
- `10,000` repetitions

The fixed random seed is:

`20260923`

For each validation target, the acceptance criterion is:

`abs(mc_mean - expectation) <= max(5 * MC_SE, 1e-3)`

This rule is a numerical validation criterion rather than an inferential
hypothesis test.

The frozen Project 8 validation record reports that the Monte Carlo checks
passed at both repetition counts.

## G.10 Independent numerical verification

Project 8 distinguishes three numerical evidence layers:

1. analytical expectations computed from the frozen formulas;
2. Monte Carlo estimates used as stochastic validation checks; and
3. rounded source-reported values used for reconciliation.

The workflow also includes an independent recomputation of critical numerical
values.

Twelve rounded source-reported values were reconciled successfully. Source
values are not substituted into the analytical pipeline and are not used to
force agreement.

## G.11 Frozen artifact inventory

The validated research outputs are frozen into the following artifacts:

- `full_metrics.csv`
- `sampled_metrics.csv`
- `sample_size_sweep.csv`
- `validation_results.json`
- `release_data.json`
- `claim_register.json`
- `run_manifest.json`

`release_data.json` is the frozen manuscript-facing numerical source of truth.

The claim register records which conclusions are supported and which stronger
interpretations are outside scope.

## G.12 Implementation separation

The Project 8 workflow separates:

- deterministic configuration;
- metric definitions;
- analytical sampled expectations;
- Monte Carlo simulation;
- validation;
- source reconciliation; and
- result freezing / release artifacts.

Source-reported rounded values are downstream reconciliation evidence and are
not analytical-result inputs.

No model training is performed in Project 8.

## G.13 Regression status

During the completed manuscript-building workflow, the Project 8 regression
suite reported:

`169 passed`

The frozen inputs were also checked for immutability during the validated
documentation steps.

This appendix records that validated status; it does not claim that later,
unexecuted repository changes would automatically preserve the same result.

## G.14 Manuscript reproducibility controls

The manuscript workflow preserves reproducibility by:

1. freezing the scientific configuration before drafting;
2. using full-precision values for ordering and tie decisions;
3. restricting displayed metric/result values to four decimal places;
4. keeping analytical calculations separate from stochastic simulation;
5. fixing the Monte Carlo seed and repetition counts;
6. preserving the predefined sample-size grid;
7. refusing exact crossover interpolation;
8. separating source reconciliation from analytical computation; and
9. checking frozen research artifacts for immutability during validated steps.

## G.15 Reference anchor

The primary source verified for the source-reported toy example is:

Krichene, W., and Rendle, S. (2020). *On Sampled Metrics for Item Recommendation*.
Proceedings of the 26th ACM SIGKDD International Conference on Knowledge
Discovery & Data Mining, 1748–1757. DOI: `10.1145/3394486.3403226`.

The bibliography file generated in Step 9.16 is:

`Project8_references.bib`

## G.16 Scope and interpretation limits

This reproducibility appendix does not establish that:

- sampled evaluation is generally unreliable;
- every sampled metric changes model ordering;
- the same reversal occurs for all datasets or sampling protocols;
- the toy example estimates production frequency or production effect size;
- any exact AP crossover occurs at a specific untested `m`;
- the complete source paper has been reproduced;
- Project 8 is the first work to identify the sampled-evaluation issue; or
- the current manuscript has a publication or DOI status.

The appendix documents reproducibility of the specific frozen Project 8
toy-example analysis only.

## G.17 Reproduction checklist

A faithful reproduction should verify all of the following:

- [ ] `N = 10,000`
- [ ] one relevant item per test case
- [ ] five cases per model
- [ ] A/B/C rank profiles match the frozen values
- [ ] uniform negative sampling with replacement
- [ ] sampled-rank model uses `X ~ Binomial(m,p)` and `R = 1 + X`
- [ ] reference setting uses `m = 99`
- [ ] the predefined 12-value `m` grid is unchanged
- [ ] formula tolerance is `1e-12`
- [ ] tie tolerance is `1e-12`
- [ ] Monte Carlo seed is `20260923`
- [ ] Monte Carlo repetitions are `1,000` and `10,000`
- [ ] validation rule is `abs(mc_mean - expectation) <= max(5 * MC_SE, 1e-3)`
- [ ] full-catalog AP ordering is `C > B > A`
- [ ] expected sampled AP ordering at `m = 99` is `A > B > C`
- [ ] AUC ordering remains `A > C > B` across the tested grid
- [ ] crossover claims are interval-only
- [ ] source-reported rounded values are reconciliation-only
- [ ] no universal or production-generalization claim is introduced
