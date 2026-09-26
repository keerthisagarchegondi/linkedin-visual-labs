# Project 8 — Mathematical Methods Draft

## Manuscript

**When Sampled Recommendation Metrics Change Model Selection: A Reproducible Toy-Example Study**

## 3. Mathematical methods

### 3.1 Evaluation setting

Let \(N = 10{,}000\) denote the full candidate-catalog size. Each
test case contains exactly one relevant item and \(N-1\) nonrelevant
items. For a given model and test case, let \(r \in
\{1,\ldots,N\}\) denote the full-catalog rank of the relevant item,
where smaller values indicate better ranking.

Project 8 evaluates three fixed model profiles, A, B, and C. Each
profile contains five test cases. The rank profiles are treated as
fixed inputs throughout the study; model fitting and prediction
generation are outside the scope of the experiment.

The full-catalog evaluation uses all \(N\) candidates. The sampled
evaluation keeps the relevant item and samples \(m\) negative items
uniformly with replacement from the \(N-1\) nonrelevant items.

The reference sampled setting is:

\[
m = 99.
\]

Therefore, the reference sampled candidate set contains 100 items in
total: one relevant item and 99 sampled negatives.

### 3.2 Sampled-rank distribution

For a test case whose relevant item has full-catalog rank \(r\), there
are \(r-1\) nonrelevant items ranked ahead of the relevant item among
the \(N-1\) available negatives.

The probability that a uniformly sampled negative item is ranked ahead
of the relevant item is therefore

\[
p = \frac{r-1}{N-1}.
\]

Let \(X\) denote the number of sampled negatives that are ranked ahead
of the relevant item when \(m\) negatives are drawn with replacement.
Under the frozen Project 8 sampling protocol,

\[
X \sim \operatorname{Binomial}(m,p).
\]

The sampled rank \(R\) of the relevant item is then

\[
R = 1 + X.
\]

Thus,

\[
R - 1 \sim
\operatorname{Binomial}\left(
m,
\frac{r-1}{N-1}
\right).
\]

This distribution is the basis for the analytical sampled-metric
expectations used throughout Project 8.

### 3.3 Average Precision

Because each test case contains exactly one relevant item, full-catalog
Average Precision reduces to reciprocal rank:

\[
\operatorname{AP}_{\text{full}}(r)
=
\frac{1}{r}.
\]

Under sampled evaluation, the corresponding AP value for realized
sampled rank \(R\) is

\[
\operatorname{AP}_{\text{sampled}}(R)
=
\frac{1}{R}.
\]

The analytical expected sampled AP for a full-catalog rank \(r\) and
sample size \(m\) is therefore

\[
\mathbb{E}
\left[
\operatorname{AP}_{\text{sampled}}
\mid r,m
\right]
=
\sum_{x=0}^{m}
\frac{1}{1+x}
\binom{m}{x}
p^x
(1-p)^{m-x},
\]

where

\[
p = \frac{r-1}{N-1}.
\]

Model-level AP is obtained by averaging the test-case AP values over
the five fixed cases in the corresponding model profile.

### 3.4 NDCG

Project 8 uses the untruncated one-relevant-item NDCG definition.

For full-catalog rank \(r\),

\[
\operatorname{NDCG}_{\text{full}}(r)
=
\frac{1}{\log_2(r+1)}.
\]

For sampled rank \(R\),

\[
\operatorname{NDCG}_{\text{sampled}}(R)
=
\frac{1}{\log_2(R+1)}.
\]

Accordingly, the analytical expected sampled NDCG is

\[
\mathbb{E}
\left[
\operatorname{NDCG}_{\text{sampled}}
\mid r,m
\right]
=
\sum_{x=0}^{m}
\frac{1}{\log_2(x+2)}
\binom{m}{x}
p^x
(1-p)^{m-x}.
\]

As with AP, model-level NDCG is the arithmetic mean over the five fixed
test cases.

### 3.5 Recall@10

With one relevant item per test case, Recall@10 is the indicator that
the relevant item appears within the top ten positions.

For full-catalog rank \(r\),

\[
\operatorname{Recall@10}_{\text{full}}(r)
=
\mathbf{1}(r \leq 10).
\]

For sampled rank \(R\),

\[
\operatorname{Recall@10}_{\text{sampled}}(R)
=
\mathbf{1}(R \leq 10).
\]

Because \(R=1+X\), the analytical sampled expectation is

\[
\mathbb{E}
\left[
\operatorname{Recall@10}_{\text{sampled}}
\mid r,m
\right]
=
\Pr(X \leq 9),
\]

where

\[
X \sim \operatorname{Binomial}(m,p).
\]

Equivalently,

\[
\Pr(X \leq 9)
=
\sum_{x=0}^{\min(9,m)}
\binom{m}{x}
p^x
(1-p)^{m-x}.
\]

### 3.6 AUC

For the one-relevant-item ranking setting, full-catalog AUC is defined
as the fraction of nonrelevant items ranked below the relevant item.

For relevant-item rank \(r\),

\[
\operatorname{AUC}_{\text{full}}(r)
=
\frac{N-r}{N-1}.
\]

Under sampled evaluation, if \(X\) of the \(m\) sampled negatives are
ranked ahead of the relevant item, then

\[
\operatorname{AUC}_{\text{sampled}}
=
1 - \frac{X}{m}.
\]

Using

\[
\mathbb{E}[X] = mp,
\]

the analytical expected sampled AUC is

\[
\mathbb{E}
\left[
\operatorname{AUC}_{\text{sampled}}
\mid r,m
\right]
=
1-p.
\]

Substituting the frozen definition of \(p\),

\[
1-p
=
1-\frac{r-1}{N-1}
=
\frac{N-r}{N-1}.
\]

Therefore,

\[
\mathbb{E}
\left[
\operatorname{AUC}_{\text{sampled}}
\mid r,m
\right]
=
\operatorname{AUC}_{\text{full}}(r).
\]

This equality explains why AUC serves as a negative control in the
Project 8 toy setting: its analytical expected value is invariant to
the number of sampled negatives under this sampling protocol.

The empirical Project 8 claim remains limited to the tested
sample-size grid and does not assert a universal result outside the
frozen setting.

### 3.7 Model-level aggregation

Each model profile contains five test cases. For a metric \(M\), let

\[
M_i
\]

denote the full-catalog value or analytical sampled expectation for
test case \(i\).

The model-level metric is

\[
\bar{M}
=
\frac{1}{5}
\sum_{i=1}^{5}
M_i.
\]

Model ordering is determined from these five-case means.

No weighting across cases is applied.

### 3.8 Sample-size sensitivity grid

Expected sampled metrics are evaluated on the frozen grid

\[
m \in
\{
1,
2,
5,
10,
20,
50,
99,
200,
500,
1000,
5000,
9999
\}.
\]

The purpose of this grid is to evaluate how expected sampled metric
values and resulting model orderings change as the number of sampled
negatives increases.

Project 8 reports crossover intervals only when adjacent evaluated
grid points produce different model orderings.

No interpolation is used to infer an exact crossover point between
uncomputed values of \(m\).

### 3.9 Numerical ordering and tie policy

All scientific comparisons are performed on the unrounded numerical
values generated by the analytical pipeline.

Display rounding is not used to determine model ordering.

The frozen Project 8 numerical tolerance for formula comparisons is

\[
10^{-12}.
\]

The frozen tie tolerance is also

\[
10^{-12}.
\]

Two metric values whose absolute difference does not exceed the tie
tolerance are treated as tied for ordering purposes.

### 3.10 Monte Carlo validation

Analytical sampled-metric expectations are independently checked by
Monte Carlo simulation.

Project 8 uses two simulation scales:

\[
1{,}000
\]

repetitions and

\[
10{,}000
\]

repetitions.

The frozen random seed is

\[
20260923.
\]

For each validation target, let

\[
\hat{\mu}_{MC}
\]

denote the Monte Carlo mean,

\[
\mu
\]

the analytical expectation, and

\[
SE_{MC}
\]

the Monte Carlo standard error.

The validation criterion is

\[
\left|
\hat{\mu}_{MC}
-
\mu
\right|
\leq
\max
\left(
5SE_{MC},
10^{-3}
\right).
\]

This acceptance rule is used as a numerical validation check rather
than as an inferential hypothesis test.

### 3.11 Independent numerical verification

The mathematical pipeline is complemented by independent
recomputation of critical numerical results and reconciliation of
twelve rounded source-reported values.

The study distinguishes three forms of numerical evidence:

1. exact or numerically evaluated analytical expectations;
2. Monte Carlo estimates used as validation checks; and
3. rounded source-reported values used for reconciliation.

Agreement with a rounded source value is not used as a substitute for
the independent analytical calculation.

### 3.12 Deterministic analysis contract

The mathematical analysis is governed by the following frozen
configuration:

- full candidate catalog: `N = 10,000`;
- one relevant item per test case;
- five test cases per model profile;
- reference sampled negatives: `m = 99`;
- uniform negative sampling with replacement;
- sampled rank: `R = 1 + X`;
- `X ~ Binomial(m, (r-1)/(N-1))`;
- formula tolerance: `1e-12`;
- tie tolerance: `1e-12`;
- Monte Carlo repetitions: `1,000` and `10,000`;
- Monte Carlo seed: `20260923`;
- predefined sample-size grid only.

No mathematical assumptions beyond this frozen contract are introduced
in the manuscript.

## Draft status

- Version: `P28_MATHEMATICAL_METHODS_V1`
- Status: draft
- Derived from the frozen Project 8 scientific contract.
- No new metric definition is introduced.
- No new sampling protocol is introduced.
- No literature-attribution statement is finalized before Step 9.15.
- No publication-status claim is made.
- No DOI claim is made.
