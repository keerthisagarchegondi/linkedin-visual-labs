# Project 8 — Final Manuscript Structure

## Manuscript title

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

## Manuscript status

Structure frozen at:

**Project 8 — Step 9 — Sub-step 9.1**

The structure below is the authoritative manuscript architecture for
Project 8 unless a later explicitly approved repair changes it.

The scientific results themselves remain governed by the frozen
Project 8 scientific artifacts and are not redefined by this document.

---

## Front matter

1. Title
2. Author
3. Affiliation
4. Corresponding-author information
5. Keywords

---

# Abstract

The abstract must follow this fixed logic:

1. Background
2. Problem
3. Study design
4. Central Average Precision result
5. Sample-size extension
6. AUC negative control
7. Validation
8. Bounded conclusion

The abstract must not contain unsupported novelty language,
publication-status claims, DOI claims, or universal conclusions.

---

# 1. Introduction

## 1.1 Motivation

Explain why recommender-system evaluation commonly uses sampled
candidate sets and why model selection can depend on the evaluation
protocol.

## 1.2 Research question

Primary question:

> Can changing only the evaluation candidate set change which fixed
> recommendation model appears best?

## 1.3 Scope of this reproduction-and-extension study

Clearly separate:

- reproduction;
- independent verification;
- extension.

## 1.4 Contributions

Summarize only claims supported by the frozen Project 8 evidence.

---

# 2. Source example and study scope

## 2.1 Source-reported toy rank profiles

Document the three fixed rank profiles:

- Model A;
- Model B;
- Model C.

Each profile contains five test cases.

## 2.2 What is reproduced

Describe the source-reported toy setting and the central sampled
evaluation phenomenon.

## 2.3 What is independently extended

Document:

- analytical expectations;
- larger deterministic Monte Carlo validation;
- sample-size sweep;
- computed-grid crossover intervals;
- explicit AUC negative control;
- independent critical-number recomputation.

## 2.4 Claims intentionally outside scope

Do not claim:

- sampled metrics are universally wrong;
- every sampled metric reverses model selection;
- the toy result establishes production frequency;
- exact crossover points between uncomputed grid values;
- the complete source paper has been independently reproduced.

---

# 3. Mathematical methods

## 3.1 Full-catalog evaluation setup

Frozen catalog size:

- `N = 10,000`

One relevant item is present for each test case.

## 3.2 Sampled evaluation protocol

Reference sampled-negative count:

- `m = 99`

Uniform negative sampling is performed with replacement.

## 3.3 Sampled-rank distribution

For full-catalog relevant-item rank `r`:

- `p = (r - 1) / (N - 1)`
- `X ~ Binomial(m, p)`
- `R = 1 + X`

where `R` is the sampled rank.

## 3.4 Average Precision

For the one-relevant-item setting:

- full-catalog AP = `1 / r`;
- sampled AP = `1 / R`.

## 3.5 NDCG

Untruncated one-relevant-item NDCG:

- `1 / log2(r + 1)`

and equivalently under sampled rank `R`.

## 3.6 Recall@10

- `1` when rank is at most 10;
- `0` otherwise.

## 3.7 AUC

Full-catalog AUC:

- `(N - r) / (N - 1)`

Sampled AUC:

- `1 - X / m`

## 3.8 Analytical expectations

Document exact analytical expectations used by the frozen result
pipeline.

## 3.9 Ordering and tie policy

Use frozen numerical tolerances and tie policy.

Do not introduce ranking differences through rounded display values.

---

# 4. Independent implementation

## 4.1 Implementation separation from source calculations

Explain that Project 8 independently implements the mathematical
evaluation procedure rather than copying source outputs into the
result pipeline.

## 4.2 Deterministic configuration

Record deterministic configuration and random seed.

Frozen Monte Carlo seed:

- `20260923`

## 4.3 Frozen A/B/C rank profiles

Use the source-reported toy rank profiles frozen by Project 8.

## 4.4 Sample-size grid

Frozen grid:

- `1`
- `2`
- `5`
- `10`
- `20`
- `50`
- `99`
- `200`
- `500`
- `1000`
- `5000`
- `9999`

## 4.5 Validation tolerances

Analytical and formula tolerance:

- `1e-12`

Monte Carlo acceptance criterion:

- `abs(MC mean - analytical expectation)`
- must be at most
- `max(5 * MC standard error, 1e-3)`

## 4.6 Reproducibility controls

Document:

- deterministic configuration;
- frozen inputs;
- explicit seeds;
- generated receipts;
- independent recomputation;
- claim register.

---

# 5. Results

## 5.1 Full-catalog metrics

Present:

- AP;
- NDCG;
- Recall@10;
- AUC.

## 5.2 Expected sampled metrics at m = 99

Present the analytical expected sampled values.

## 5.3 AP model-selection reversal

Central frozen result:

- full AP ordering: `C > B > A`;
- sampled AP at `m = 99`: `A > B > C`.

This is the central model-selection reversal.

## 5.4 NDCG and Recall@10 behavior

Present only frozen validated results.

## 5.5 AUC negative control

Frozen AUC ordering:

- `A > C > B`

The ordering remains unchanged across the tested sample-size grid.

---

# 6. Sample-size sensitivity analysis

## 6.1 Expected AP across m

Show analytical expected AP across the frozen sample-size grid.

## 6.2 Model ordering across m

Document only orderings computed on the frozen grid.

## 6.3 Computed-grid crossover intervals

Frozen intervals:

- A/B: `500–1000`
- A/C: `200–500`
- B/C: `50–99`
- B/C: `200–500`

These are interval statements only.

No exact crossover value may be inferred or reported.

## 6.4 NDCG sensitivity

Present frozen analytical results.

## 6.5 Recall@10 sensitivity

Present frozen analytical results.

## 6.6 AUC invariance

Report the tested-grid negative-control result.

Do not convert the tested-grid result into a universal theorem.

---

# 7. Monte Carlo validation

## 7.1 Source-scale replication: 1,000 repetitions

Present the lower-repetition Monte Carlo validation.

## 7.2 Higher-precision validation: 10,000 repetitions

Present the higher-repetition validation.

## 7.3 Acceptance criterion

Use the frozen Monte Carlo acceptance criterion.

## 7.4 Analytical-versus-simulation agreement

Report PASS/FAIL results exactly as supported by the frozen
validation artifacts.

---

# 8. Source reconciliation and discrepancy analysis

## 8.1 Reference-value reconciliation

Document comparison with source-reported rounded values.

## 8.2 Rounding treatment

Twelve rounded source values were reconciled in the frozen Project 8
validation.

## 8.3 Independent critical-number recomputation

Document the independent recomputation check.

## 8.4 Residual uncertainty

Distinguish:

- exact analytical outputs;
- rounded source-reported values;
- Monte Carlo estimates.

---

# 9. Discussion

## 9.1 What the AP reversal demonstrates

The fixed toy example demonstrates that changing the evaluation
candidate set can change which model AP selects as best.

## 9.2 Why evaluation candidate sets matter

Discuss the measurement protocol without generalizing beyond
supported evidence.

## 9.3 Why AUC behaves differently here

Use the AUC negative control to contrast metric sensitivity.

## 9.4 Implications for recommender-system evaluation

Discuss implications as bounded interpretation, not universal
empirical frequency.

## 9.5 What should not be inferred from this toy example

Explicitly reject:

- universal reversal;
- universal sampled-metric failure;
- production-frequency estimates;
- exact crossover claims.

---

# 10. Limitations

Must include at minimum:

- toy-example scale;
- five cases per model;
- one relevant item per test case;
- fixed source-reported rank profiles;
- no model training;
- no claim of production prevalence;
- limited metric family;
- sampled-negative protocol considered here;
- finite sample-size grid.

---

# 11. Reproducibility

## 11.1 Repository organization

Document project-specific paths.

## 11.2 Frozen inputs

List frozen scientific inputs.

## 11.3 Deterministic seeds

Document all seeds.

## 11.4 Environment

Document relevant runtime and dependency information.

## 11.5 Reproduction commands

Provide deterministic reproduction commands.

## 11.6 Generated artifacts

List manuscript, figures, dashboard, validation, and video artifacts
only when they actually exist.

---

# 12. Contribution statement

Use a bounded contribution statement.

The manuscript must not claim discovery of the general phenomenon of
sampled-evaluation bias.

The Project 8 contribution is an independent, reproducible
reconstruction and extension of the selected toy example, including
analytical expectations, deterministic validation, sample-size
sensitivity analysis, crossover-interval reporting, and an explicit
negative control.

---

# 13. AI-assistance disclosure

Disclose material AI assistance truthfully.

The final wording is drafted in Step 9.14.

---

# 14. Data and code availability

Do not claim public availability until the relevant repository/archive
is actually public.

---

# 15. Conflict-of-interest statement

Draft truthfully.

Do not invent disclosures.

---

# 16. Funding statement

Draft truthfully.

Do not invent funding.

---

# 17. References

All references must pass Step 9.15 primary-source verification before
the final reference list is frozen.

---

# Appendix A — Complete source-reported rank profiles

# Appendix B — Metric definitions and derivations

# Appendix C — Full analytical result tables

# Appendix D — Sample-size sweep

# Appendix E — Monte Carlo validation tables

# Appendix F — Source reconciliation

# Appendix G — Reproducibility receipt

# Appendix H — Claim/evidence linkage

# Appendix I — AI assistance log

---

# Frozen manuscript framing

The manuscript must consistently distinguish:

## Reproduction

Reconstruction of the selected source-reported toy example.

## Independent verification

Independent formulas, implementation, analytical calculations,
Monte Carlo validation, source reconciliation, and critical-number
recomputation.

## Extension

Sample-size sensitivity analysis, computed-grid crossover intervals,
and explicit AUC negative-control analysis.

---

# Frozen central result

Full-catalog Average Precision:

`C > B > A`

Expected sampled Average Precision at `m = 99`:

`A > B > C`

AUC negative control:

`A > C > B`

---

# Frozen manuscript tone

The manuscript must be:

- technically precise;
- readable;
- reproducible;
- bounded in its conclusions;
- explicit about uncertainty;
- explicit about reproduction versus extension.

The manuscript must not use unsupported language such as:

- groundbreaking;
- proves sampled metrics are wrong;
- sampled evaluation always fails;
- industry-changing;
- first-ever;
- universally;
- exact crossover point;

unless a later verified source and approved manuscript revision
specifically supports such language.

---

# Step 9 abstract-order contract

The eventual abstract must use this sequence:

1. Background
2. Problem
3. Study design
4. Central AP result
5. Sample-size extension
6. AUC negative control
7. Validation
8. Bounded conclusion

No abstract prose is drafted in Step 9.1.
