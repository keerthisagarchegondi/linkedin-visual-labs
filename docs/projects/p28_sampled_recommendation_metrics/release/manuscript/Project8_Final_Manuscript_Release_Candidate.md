# When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study

**Author:** Keerthi Sagar Chegondi

**Affiliation:** Independent Researcher, Phoenix, Arizona, United States

**Corresponding author:** keerthisagarchegondi@gmail.com

**Keywords:** recommender systems; offline evaluation; negative sampling; average precision; NDCG; AUC; reproducibility

## Abstract

Offline recommender-system evaluation is often performed on sampled candidate sets rather than the full item catalog, but changing the candidate set can alter the metric values used for model selection. This study independently reconstructs and extends a source-reported toy recommendation-ranking example to examine whether changing only the evaluation protocol can change which fixed model appears best.

Three fixed rank profiles, each containing five test cases with one relevant item, are evaluated in a catalog of 10,000 items. We compare full-catalog metrics with analytical expectations under uniform negative sampling with replacement, using 99 sampled negatives as the reference setting. Under full-catalog Average Precision (AP), the model ordering is C > B > A. Under expected sampled AP at m = 99, the ordering reverses completely to A > B > C, even though the model rankings themselves are unchanged.

A sample-size sweep over twelve predefined values of m shows that AP model ordering varies with the number of sampled negatives. The computed grid places the A/B crossover between 500 and 1000 sampled negatives, the A/C crossover between 200 and 500, and B/C crossovers between 50 and 99 and between 200 and 500. These are interval statements over the evaluated grid rather than estimates of exact crossover points.

AUC provides a negative control: its model ordering remains A > C > B across the tested sample-size grid. Analytical expectations are checked using Monte Carlo simulations with 1,000 and 10,000 repetitions, independent critical-number recomputation, and reconciliation against twelve rounded source-reported values.

The results show, for this controlled toy example, that the evaluation candidate set alone can change which model a ranking-sensitive metric selects as best. The study does not imply that sampled evaluation is generally unreliable or that every sampling configuration changes model selection; rather, it demonstrates why recommender-system model comparison should treat the evaluation protocol as part of the measurement design.

## 1. Introduction

### 1.1 Motivation

Offline recommender-system evaluation frequently uses sampled candidate sets because ranking every item in a large catalog can be computationally expensive. Sampling, however, changes the set over which ranking metrics are computed. That makes the evaluation protocol itself a potential source of variation in model comparison, even when the underlying model rankings are fixed.

### 1.2 Research question

This study asks a deliberately narrow question: can changing only the evaluation candidate set change which of several fixed recommendation rank profiles appears best under common offline ranking metrics? The analysis does not retrain models, change predictions, or alter the underlying full-catalog ranks.

### 1.3 Scope of the reproduction-and-extension study

The project reconstructs a selected source-reported toy example from Krichene and Rendle (2020) and then extends it with an explicit analytical expectation calculation, a predefined sample-size sensitivity grid, computed-grid crossover intervals, an AUC negative control, Monte Carlo validation, and an independent numerical reconciliation workflow. The study does not claim to reproduce the complete source paper.

### 1.4 Contributions

The study contributes a compact reproducible demonstration of how candidate-set design can change model selection in a ranking metric; a deterministic mathematical treatment of the sampled-rank distribution; a sample-size sensitivity analysis; an explicit AUC negative control; and a validation workflow that separates analytical calculations, stochastic checks, and source-value reconciliation.

## 2. Source example and study scope

### 2.1 Source-reported toy rank profiles

The experiment starts from the three fixed model profiles reported by Krichene and Rendle (2020), with five test cases per model and one relevant item per case. The full-catalog relevant-item ranks are: Model A [100, 100, 100, 100, 100]; Model B [40, 40, 8437, 9266, 4482]; and Model C [212, 2, 743, 5342, 1548]. Lower ranks indicate earlier placement of the relevant item.

### 2.2 What is reproduced

The reproduced phenomenon is the selected toy example in which the full-catalog AP ordering differs from the expected sampled AP ordering. Under full-catalog AP, the ordering is C > B > A. Under expected sampled AP at m = 99, the ordering is A > B > C. The fixed rank profiles themselves do not change.

### 2.3 What is independently verified

Project 8 independently computes the metric values from the frozen rank profiles, derives the sampled-rank distribution, evaluates analytical expectations, checks the results through Monte Carlo simulation at 1,000 and 10,000 repetitions, independently recomputes critical numerical values, and reconciles twelve rounded source-reported values.

### 2.4 What is independently extended

The project evaluates the predefined sampled-negative grid m = {1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999}; records the grid intervals over which AP pairwise orderings change; and documents AUC as a negative control whose analytical expectation is invariant to m under the frozen sampling protocol.

### 2.5 Interpretation boundary

The project does not claim first discovery of the general sampled-evaluation issue, does not infer how often reversals occur in production systems, does not estimate exact crossover points between uncomputed grid values, and does not claim that sampled evaluation is universally unreliable.

## 3. Mathematical methods

### 3.1 Evaluation setting

Let N = 10,000 denote the full candidate-catalog size. Each test case contains exactly one relevant item and N - 1 nonrelevant items. For a given test case, let r be the full-catalog rank of the relevant item. The sampled evaluation retains the relevant item and draws m negatives uniformly with replacement from the N - 1 nonrelevant items. The reference sampled setting is m = 99.

### 3.2 Sampled-rank distribution

There are r - 1 nonrelevant items ranked ahead of the relevant item. Therefore the probability that a uniformly sampled negative is ranked ahead is p = (r - 1)/(N - 1). If X is the number of sampled negatives ahead of the relevant item, then X ~ Binomial(m, p), and sampled rank R = 1 + X.

### 3.3 Average Precision

With one relevant item per test case, full-catalog AP reduces to reciprocal rank: AP_full(r) = 1/r. Under sampled evaluation, AP_sampled(R) = 1/R. The analytical expectation is E[AP_sampled | r,m] = sum_{x=0}^m [1/(1+x)] * BinomialPMF(x; m,p).

### 3.4 NDCG

The study uses untruncated one-relevant-item NDCG. Full-catalog NDCG is 1/log2(r+1), sampled NDCG is 1/log2(R+1), and the expected sampled value is obtained by averaging 1/log2(x+2) over the Binomial(m,p) distribution.

### 3.5 Recall@10

With one relevant item, Recall@10 is the indicator that the relevant item appears within the first ten positions. Thus Recall@10_full = I(r <= 10) and Recall@10_sampled = I(R <= 10). Because R = 1 + X, the analytical expectation is P(X <= 9).

### 3.6 AUC

Full-catalog AUC is (N-r)/(N-1). For sampled evaluation, AUC_sampled = 1 - X/m. Since E[X] = mp, E[AUC_sampled | r,m] = 1 - p = (N-r)/(N-1), exactly matching full-catalog AUC under this protocol. This equality motivates its use as a negative control.

### 3.7 Model-level aggregation

Each model-level metric is the arithmetic mean of its five case-level values. No weighting across cases is applied.

### 3.8 Sample-size sensitivity grid

Expected sampled metrics are evaluated on the frozen grid m = [1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999]. Crossover statements are reported only as intervals between adjacent evaluated grid points; no interpolation is used to estimate exact crossover locations.

### 3.9 Numerical ordering and tie policy

All orderings are determined from unrounded numerical values. The frozen formula tolerance and tie tolerance are both 1e-12. Values within the tie tolerance are treated as tied.

### 3.10 Monte Carlo validation

Analytical expectations are checked with 1,000 and 10,000 Monte Carlo repetitions using seed 20260923. A Monte Carlo result passes when abs(mc_mean - expectation) <= max(5*MC_SE, 1e-3). This is a numerical validation rule rather than an inferential hypothesis test.

## 4. Independent implementation

### 4.1 Implementation separation

The Project 8 workflow separates deterministic analytical calculations, stochastic Monte Carlo validation, source-value reconciliation, and frozen release artifacts. Rounded source-reported numbers are not used as inputs to generate the analytical results.

### 4.2 Deterministic configuration

The catalog size, rank profiles, sampling protocol, reference m, sample-size grid, tolerances, Monte Carlo seed, and repetition counts are frozen centrally so that analytical, simulation, validation, and presentation stages use the same experimental contract.

### 4.3 Fixed rank profiles

Models A, B, and C are abstract fixed rank profiles rather than trained models. No model fitting, fine-tuning, or prediction generation occurs in this study.

### 4.4 Analytical and simulation layers

Expected sampled metrics are computed analytically from the Binomial sampled-rank distribution. Monte Carlo simulation then samples from the same frozen process to provide an independent numerical check rather than serving as the source of the expectations.

### 4.5 Validation and freezing

The workflow includes formula checks, ordering/tie checks, independent critical-number recomputation, reconciliation to twelve rounded source values, and frozen machine-readable release artifacts. Later manuscript and presentation work is expected to consume those frozen results rather than recomputing or editing them ad hoc.

### 4.6 Meaning of 'independent implementation'

Here, independent implementation means a separately implemented computational reconstruction and validation workflow. It does not imply a legal clean-room process, first discovery of the sampled-evaluation phenomenon, or complete reproduction of the original source work.

## 5. Results

### 5.1 Full-catalog metrics

The full-catalog results establish the baseline before candidate sampling is introduced. AP orders the models C > B > A; AUC orders them A > C > B; NDCG orders them C > A > B; and Recall@10 orders them C > A = B. The small AP difference between B and A exceeds the frozen 1e-12 tie tolerance, whereas A and B are exactly tied on Recall@10 in this five-case toy example.

### 5.2 Expected sampled metrics at m = 99

At the reference sampled setting, expected AP values are A = 0.6366, B = 0.3407, and C = 0.3262, giving A > B > C. Expected sampled NDCG values are A = 0.7290, B = 0.4473, and C = 0.4600, giving A > C > B. Expected Recall@10 values are A = 1.0000, B = 0.4000, and C = 0.5694, giving A > C > B. AUC remains A > C > B with the same model-level values as the full catalog.

### 5.3 AP model-selection reversal

The central result is the AP ordering change from C > B > A under full-catalog evaluation to A > B > C under expected sampled evaluation at m = 99. Because the model rank profiles are unchanged, this is a complete reversal produced solely by the change in evaluation candidate set in this controlled toy example.

### 5.4 NDCG and Recall@10

NDCG also changes ordering, from C > A > B in the full catalog to A > C > B at m = 99. Recall@10 changes from C > A = B to A > C > B. These shifts show that the effect is not confined to AP, although the direction and magnitude differ by metric.

### 5.5 AUC negative control

AUC provides a contrasting result. Its expected sampled values are invariant to m under the frozen protocol, and the ordering remains A > C > B across the tested grid. This negative control demonstrates that candidate-set sensitivity is metric-dependent within the toy setting rather than an unavoidable property of every evaluated metric.

## 6. Sample-size sensitivity

### 6.1 AP ordering over m

The AP model ordering is not constant over the predefined sample-size grid. At m = 1 the ordering is A > C > B; at m = 99 it is A > B > C; at m = 500 it is C > A > B; and at m = 1000 and m = 9999 it is C > B > A. Thus, increasing the number of sampled negatives can change which model appears best and can eventually recover the full-catalog AP ordering on this grid.

### 6.2 Computed-grid crossover intervals

Pairwise AP ordering changes occur between adjacent tested grid points in the following intervals: A/B between 500 and 1000; A/C between 200 and 500; and B/C between 50 and 99 and again between 200 and 500. These are computed-grid intervals only. The study does not estimate exact crossover locations inside those intervals.

### 6.3 AUC stability across m

Across the same grid, the AUC ordering remains A > C > B and the analytical expected AUC values match the full-catalog values. The maximum analytical difference between sampled and full AUC is zero under the frozen formulation.

## 7. Monte Carlo validation

### 7.1 Validation design

Analytical expectations were checked at two simulation scales, 1,000 and 10,000 repetitions, using the fixed seed 20260923. For each validation target, the observed Monte Carlo mean was required to fall within max(5*MC_SE, 1e-3) of the analytical expectation.

### 7.2 Outcome

The Monte Carlo validation passed at both repetition counts for the frozen validation targets. The higher repetition count provides a tighter stochastic check, while the analytical expectations remain the manuscript's primary numerical results.

### 7.3 Interpretation

These simulations are validation checks, not inferential tests. They support the internal consistency of the analytical implementation but do not establish population-level uncertainty or statistical significance for the toy rank profiles.

## 8. Source reconciliation and discrepancy handling

### 8.1 Rounded-source reconciliation

Twelve rounded source-reported values were reconciled against the independently calculated Project 8 values. The reconciliation passed, meaning the project values were consistent with the source values at their reported precision.

### 8.2 Separation from computation

The reconciliation is downstream of the analytical calculations. Source-reported rounded values are not substituted into the pipeline and are not used to force agreement.

### 8.3 Discrepancy policy

Where numerical presentation differs because of rounding, Project 8 preserves the internally calculated full-precision value and treats the source number as a rounded comparison point. This avoids turning a source display convention into a computational dependency.

## 9. Discussion

### 9.1 Evaluation protocol as measurement design

The toy example shows that model comparison can depend not only on model outputs but also on the candidate set over which the metric is evaluated. In that sense, negative-sampling design is part of the measurement system. A model-selection result should therefore be interpreted together with the evaluation protocol that produced it.

### 9.2 Metric dependence

The contrast between AP/NDCG/Recall@10 and AUC is central. The sampled candidate set changes some ranking-sensitive metric orderings, while expected AUC remains invariant under the same sampling assumptions. This suggests that sensitivity to candidate sampling depends on the mathematical form of the metric, not simply on the fact that sampling occurred.

### 9.3 Practical implication

For offline recommender comparisons, reporting the sampling protocol, sample size, replacement rule, catalog size, and metric definitions is important for reproducibility. When practical, sensitivity checks across candidate-set sizes can reveal whether a model-selection conclusion is robust to the evaluation design.

## 10. Limitations

### 10.1 Toy-example scale

The study uses three abstract model profiles and five test cases per model. It is designed as a controlled analytical demonstration, not an estimate of production frequency or effect size.

### 10.2 One relevant item per case

The metric simplifications and sampled-rank derivations rely on one relevant item per test case. Multi-relevant-item settings may behave differently.

### 10.3 Sampling protocol

The analysis assumes uniform negative sampling with replacement. Other sampling distributions or without-replacement schemes are outside the frozen experiment.

### 10.4 Fixed catalog and grid

The catalog size is fixed at 10,000 and the sensitivity study uses twelve predefined m values. Crossover results are interval statements over that grid, not exact threshold estimates.

### 10.5 No online inference

No conclusions are drawn about online engagement, business outcomes, calibration, user utility, or production recommender-system performance.

### 10.6 Reproduction scope

The project reconstructs and extends a selected source-reported toy example. It does not claim complete reproduction of the source paper.

## 11. Reproducibility

### 11.1 Frozen analysis contract

Reproducibility is supported by a frozen configuration defining N, the A/B/C rank profiles, the sampling protocol, the m grid, numerical tolerances, Monte Carlo repetition counts, and the random seed.

### 11.2 Analytical and stochastic separation

Analytical expectations are computed deterministically, while Monte Carlo simulation is used only as an independent check. This separation makes it possible to detect implementation errors rather than merely reproducing the same simulation output.

### 11.3 Frozen artifacts

The validated project freezes full-catalog results, sampled results, the sample-size sweep, validation results, release data, the claim register, and the run manifest. The manuscript is intended to consume those artifacts as its numerical source of truth.

### 11.4 Automated regression

Project 8 maintains an automated test suite. During the manuscript-building workflow, 169 Project 8 tests passed after the completed drafting steps available before this consolidated manuscript was assembled.

## 12. Contribution statement

### 12.1 Scientific contribution

The contribution is a reproducible reconstruction and structured extension of a selected toy recommendation-evaluation example. The work combines an explicit sampled-rank distribution, analytical expectations for four metrics, a sample-size sensitivity study, computed-grid crossover intervals, an AUC negative control, Monte Carlo checks, and source-value reconciliation.

### 12.2 Originality boundary

The manuscript does not claim first discovery of sampled-evaluation bias. Its original contribution lies in the independently implemented, auditable combination of reconstruction, analytical derivation, sensitivity analysis, validation, and bounded interpretation for this fixed example.

## 13. AI-assistance disclosure

### 13.1 Disclosure

Generative AI tools were used to assist with manuscript drafting, wording refinement, coding/orchestration guidance, documentation structure, formatting, and publication-preparation artifacts. The numerical results, formulas, validation conditions, and scientific claims were constrained to the project's frozen analytical artifacts and validation contract. AI-generated prose and code guidance were treated as draft material subject to execution, consistency checks, and human review.

### 13.2 Responsibility

The author reviewed and approved the final content and remains responsible for the study design, source verification, interpretation, execution of repository code, validation review, and publication submission. AI was not treated as a scientific authority, peer reviewer, or author, and it did not independently certify the reported results.
## 14. Data and code availability

### 14.1 Project status

The study materials are organized within the Project 8 repository workflow. At the time of this manuscript draft, no DOI or publication status is claimed. Archive, citation, and publication metadata are intended to be finalized in later release steps after reference verification.

## Appendix A. Frozen rank profiles

| Model | Five full-catalog relevant-item ranks |
|---|---|
| A | [100, 100, 100, 100, 100] |
| B | [40, 40, 8437, 9266, 4482] |
| C | [212, 2, 743, 5342, 1548] |

## Appendix B. Full-catalog metrics

| Model | AP | AUC | NDCG | Recall@10 |
|---|---:|---:|---:|---:|
| A | 0.0100 | 0.9901 | 0.1502 | 0 |
| B | 0.0101 | 0.5548 | 0.1217 | 0 |
| C | 0.1014 | 0.8431 | 0.2080 | 0.2000 |

## Appendix C. Expected sampled metrics at m = 99

| Model | AP | AUC | NDCG | Recall@10 |
|---|---:|---:|---:|---:|
| A | 0.6366 | 0.9901 | 0.7290 | 1.0000 |
| B | 0.3407 | 0.5548 | 0.4473 | 0.4000 |
| C | 0.3262 | 0.8431 | 0.4600 | 0.5694 |

## Appendix D. Sample-size sensitivity summary

- m grid: 1, 2, 5, 10, 20, 50, 99, 200, 500, 1000, 5000, 9999
- AP ordering at m=1: A > C > B
- AP ordering at m=99: A > B > C
- AP ordering at m=500: C > A > B
- AP ordering at m=1000: C > B > A
- AP ordering at m=9999: C > B > A
- Computed-grid crossover interval A/B: 500-1000
- Computed-grid crossover interval A/C: 200-500
- Computed-grid crossover intervals B/C: 50-99 and 200-500
- AUC ordering across tested grid: A > C > B

## Appendix E. Monte Carlo validation summary

Analytical sampled-metric expectations were checked at `1,000` and `10,000` repetitions with random seed `20260923`. The validation criterion was `abs(mc_mean - expectation) <= max(5 * MC_SE, 1e-3)`. The frozen Project 8 validation record reports that these checks passed. The simulations are numerical validation checks and are not inferential hypothesis tests.

## Appendix F. Source reconciliation summary

Twelve rounded source-reported values were reconciled successfully against independently calculated Project 8 results. Source-reported values were used only for downstream reconciliation and were not substituted into the analytical pipeline. Full-precision Project 8 values remain the computational source of truth; manuscript-facing metric values are displayed to four decimal places.

## Appendix G. Reproducibility

### G.1 Reproducibility objective

This appendix records the frozen analytical contract, deterministic settings,
validation rules, and artifact lineage for Project 8, **When Sampled Recommendation
Metrics Change Model Selection: A Reproducible Toy-Example Study**.

The purpose is to make the reported toy-example results auditable and repeatable
without expanding the manuscript's claims beyond the completed experiment.

### G.2 Frozen study configuration

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

### G.3 Fixed rank profiles

The three model profiles are abstract fixed rank profiles rather than trained
models.

| Model | Full-catalog relevant-item ranks |
|---|---|
| A | `[100, 100, 100, 100, 100]` |
| B | `[40, 40, 8437, 9266, 4482]` |
| C | `[212, 2, 743, 5342, 1548]` |

The rank profiles remain unchanged across full-catalog evaluation, sampled
analytical evaluation, the sample-size sweep, and Monte Carlo validation.

### G.4 Mathematical contract

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

### G.5 Frozen full-catalog baseline

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

### G.6 Frozen expected sampled results at m = 99

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

### G.7 Sample-size sensitivity contract

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

### G.8 AUC negative control

Under the frozen sampling protocol:

`E[AUC_sampled | r, m] = AUC_full(r)`

Therefore, expected sampled AUC is invariant to `m` in this toy setting.

The frozen AUC ordering is:

`A > C > B`

across the tested sample-size grid.

The maximum analytical sampled-versus-full AUC difference is `0.0000`.

### G.9 Monte Carlo validation

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

### G.10 Independent numerical verification

Project 8 distinguishes three numerical evidence layers:

1. analytical expectations computed from the frozen formulas;
2. Monte Carlo estimates used as stochastic validation checks; and
3. rounded source-reported values used for reconciliation.

The workflow also includes an independent recomputation of critical numerical
values.

Twelve rounded source-reported values were reconciled successfully. Source
values are not substituted into the analytical pipeline and are not used to
force agreement.

### G.11 Frozen artifact inventory

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

### G.12 Implementation separation

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

### G.13 Regression status

During the completed manuscript-building workflow, the Project 8 regression
suite reported:

`169 passed`

The frozen inputs were also checked for immutability during the validated
documentation steps.

This appendix records that validated status; it does not claim that later,
unexecuted repository changes would automatically preserve the same result.

### G.14 Manuscript reproducibility controls

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

### G.15 Reference anchor

The primary source verified for the source-reported toy example is:

Krichene, W., and Rendle, S. (2020). *On Sampled Metrics for Item Recommendation*.
Proceedings of the 26th ACM SIGKDD International Conference on Knowledge
Discovery & Data Mining, 1748–1757. DOI: `10.1145/3394486.3403226`.

The bibliography file generated in Step 9.16 is:

`Project8_references.bib`

### G.16 Scope and interpretation limits

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

### G.17 Reproduction checklist

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

## References

1. Krichene, W., & Rendle, S. (2020). On Sampled Metrics for Item Recommendation. *Proceedings of the 26th ACM SIGKDD International Conference on Knowledge Discovery & Data Mining*, 1748-1757. https://doi.org/10.1145/3394486.3403226

2. Krichene, W., & Rendle, S. (2022). On Sampled Metrics for Item Recommendation. *Communications of the ACM, 65*(7), 75-83. https://doi.org/10.1145/3535335

The 2020 KDD paper is the primary citation for the source-reported toy example used in this study. The 2022 *Communications of the ACM* article is included as an optional background version of the same work.

## Final manuscript status

- Consolidates Step 9.1 through Step 9.18 content required for the manuscript refresh.
- Verified bibliography integrated.
- Reproducibility appendix integrated.
- AI-assistance disclosure integrated.
- Displayed metric/result values are limited to four decimal places.
- Counts, seeds, formulas, sample-size grid values, crossover intervals, and tolerances remain exact where appropriate.
- No exact crossover interpolation is claimed.
- No whole-paper reproduction claim is made.
- No first-discovery claim is made.
- No publication or Project 8 DOI claim is made.
