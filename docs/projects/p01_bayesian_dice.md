# Bayesian Dice Detective

## Project identity

Repository project ID:

`p01_bayesian_dice`

Viewer hook:

> Can AI tell a loaded die from a fair die?

Technical description:

> Sequential Bayesian model comparison for a six-sided die.

The word **AI** is used only as an accessible content hook. The actual
analytical method is Bayesian inference. This project does not use a neural
network, reinforcement learning model, large language model, or external AI
service.

---

# 1. Viewer question

The project asks:

> Given only a sequential stream of die rolls, how much evidence is required
> before an automated Bayesian system should become confident that the die is
> loaded?

The important lesson is not that an unusual streak proves cheating.

The lesson is that isolated surprising observations and accumulated statistical
evidence are different things.

The system must therefore expose uncertainty throughout the sequence.

---

# 2. Statistical hypotheses

## H0 — fair die

Under the fair-die hypothesis,

\[
H_0:
p_1=p_2=p_3=p_4=p_5=p_6=\frac{1}{6}.
\]

For an ordered sequence of \(n\) observations, the log likelihood is

\[
\log p(x_{1:n}\mid H_0)
=
n\log\left(\frac{1}{6}\right).
\]

The implementation must calculate this in log space.

## H1 — loaded die

Under the loaded-die hypothesis, the six face probabilities are unknown:

\[
\mathbf{p}
=
(p_1,p_2,p_3,p_4,p_5,p_6).
\]

They follow the symmetric Dirichlet prior

\[
\mathbf{p}\mid H_1
\sim
\operatorname{Dirichlet}(1,1,1,1,1,1).
\]

Let

\[
\boldsymbol{\alpha}
=
(\alpha_1,\ldots,\alpha_6)
\]

and let

\[
n_i
\]

be the cumulative number of observations of face \(i\).

The integrated marginal likelihood of the ordered sequence under H1 is

\[
p(x_{1:n}\mid H_1)
=
\frac{\Gamma(\alpha_0)}
     {\Gamma(\alpha_0+n)}
\prod_{i=1}^{6}
\frac{\Gamma(\alpha_i+n_i)}
     {\Gamma(\alpha_i)},
\]

where

\[
\alpha_0=\sum_{i=1}^{6}\alpha_i.
\]

The implementation must calculate the logarithm of this expression using
log-gamma operations rather than multiplying probabilities directly.

When working only with the count representation, the multinomial
combinatorial factor is common to both hypotheses and therefore cancels from
the Bayes factor.

---

# 3. Prior model probability

The initial contract uses neutral prior model odds:

\[
P(H_1)=0.5
\]

and

\[
P(H_0)=0.5.
\]

The sensitivity analysis in Project 1 — Step 5 will repeat the analysis using:

- 0.10
- 0.25
- 0.50
- 0.75
- 0.90

as prior loaded-die probabilities.

---

# 4. Posterior model probability

After each observation, calculate

\[
P(H_1\mid x_{1:n})
\]

from the model prior and the two marginal likelihoods.

Numerically, the implementation must remain in log space until the final
normalization.

The posterior probability of the fair model is

\[
P(H_0\mid x_{1:n})
=
1-P(H_1\mid x_{1:n}).
\]

No configured roll count may cause floating-point underflow or non-finite
posterior output.

---

# 5. Posterior predictive probabilities

Under H1, the posterior predictive probability of face \(i\) after \(n\)
observations is

\[
P(X_{n+1}=i \mid x_{1:n},H_1)
=
\frac{\alpha_i+n_i}
     {\alpha_0+n}.
\]

All six predictive probabilities must remain in the interval \([0,1]\) and
sum to one within numerical tolerance.

---

# 6. Decision states

The project does not force every sequence into a binary verdict.

The initial contract defines three states.

## Loaded

If

\[
P(H_1\mid x_{1:n}) \ge 0.95,
\]

the state is:

`LOADED`

## Fair

If

\[
P(H_1\mid x_{1:n}) \le 0.05,
\]

the state is:

`FAIR`

## Uncertain

Otherwise the state is:

`UNCERTAIN`

The **detection roll** for a loaded sequence is the first roll at which the
loaded posterior reaches or exceeds 0.95.

A sequence may finish without a loaded detection roll.

That outcome must be represented explicitly rather than converted to a false
positive value or an invented roll number.

---

# 7. Deterministic simulation scenarios

Every scenario uses 180 rolls.

## Fair die

Probabilities:

\[
(1/6,1/6,1/6,1/6,1/6,1/6)
\]

Seed:

`101`

Purpose:

- establish expected behavior under H0;
- estimate sequential false-positive behavior;
- demonstrate that ordinary random variation can look suspicious.

## Mildly loaded die

Probabilities:

\[
(0.15,0.15,0.15,0.15,0.15,0.25)
\]

Seed:

`202`

Purpose:

- represent a difficult alternative;
- demonstrate that weak bias may require substantial evidence;
- prevent the project from implying that every loaded die is easy to detect.

The mild scenario has no mandatory 95% detection-rate target.

Its detection rate must be reported rather than optimized away.

## Clearly loaded die

Probabilities:

\[
(0.12,0.12,0.12,0.12,0.12,0.40)
\]

Seed:

`1`

Purpose:

- provide a clearly distinguishable alternative;
- support the initial LinkedIn narrative;
- define the primary true-positive calibration benchmark.

This is the initial showcase scenario.

---

# 8. Randomness contract

All randomness must use the shared deterministic random-state infrastructure.

Canonical implementation behavior:

- NumPy `Generator`
- no global `numpy.random.seed`
- no hidden mutable random state
- explicit seed in every generated dataset
- seed persisted in the generation manifest

Repeated execution using the same configuration and seed must reproduce the
same roll sequence exactly.

---

# 9. Sequential inference contract

After every roll, the inference history must contain:

- roll index;
- observed face;
- cumulative count of each face;
- log marginal likelihood under H0;
- log marginal likelihood under H1;
- log Bayes factor H1 versus H0;
- posterior loaded-die probability;
- posterior fair-die probability;
- six H1 posterior predictive probabilities;
- current decision state.

The sequential history is part of the canonical analytical output, not a
visualization-only intermediate.

---

# 10. Output contract

## Simulation JSON

Path:

`outputs/p01_bayesian_dice/data/simulation.json`

Required fields:

- `project_id`
- `scenario_id`
- `scenario_label`
- `seed`
- `roll_count`
- `true_probabilities`
- `rolls`
- `final_counts`

Faces are represented externally as integers 1 through 6.

## Posterior history CSV

Path:

`outputs/p01_bayesian_dice/data/posterior_history.csv`

Columns:

1. `roll_index`
2. `observed_face`
3. `count_1`
4. `count_2`
5. `count_3`
6. `count_4`
7. `count_5`
8. `count_6`
9. `log_marginal_h0`
10. `log_marginal_h1`
11. `log_bayes_factor_h1_h0`
12. `posterior_loaded`
13. `posterior_fair`
14. `predictive_face_1`
15. `predictive_face_2`
16. `predictive_face_3`
17. `predictive_face_4`
18. `predictive_face_5`
19. `predictive_face_6`
20. `decision_state`

## Validation JSON

Path:

`outputs/p01_bayesian_dice/data/validation.json`

Required analytical outputs:

- false-positive rate;
- clearly-loaded true-positive rate;
- clearly-loaded miss rate;
- clearly-loaded average detection roll;
- mildly-loaded detection rate;
- posterior calibration buckets;
- prior sensitivity results.

## Video

Path:

`outputs/p01_bayesian_dice/video/can_ai_tell_loaded_die.mp4`

Specification:

- 1080 × 1350
- 4:5
- H.264
- yuv420p
- 30 fps
- approximately 45 seconds for the initial storyboard

## Manifest

Path:

`outputs/p01_bayesian_dice/manifests/can_ai_tell_loaded_die.json`

The shared foundation manifest fields remain authoritative.

The manifest must include at minimum:

- project ID;
- asset name;
- generation timestamp;
- Git commit when available;
- configuration path;
- random seed;
- width;
- height;
- frame rate;
- duration;
- important result metrics.

---

# 11. Calibration contract

Project 1 — Step 5 will run 1,000 deterministic repetitions for each scenario.

Primary metrics:

## False-positive rate

Fraction of fair-die simulations that ever cross the loaded threshold.

Initial acceptance target:

\[
FPR \le 0.05.
\]

## Clearly-loaded true-positive rate

Fraction of clearly-loaded simulations that cross the loaded threshold.

Initial acceptance target:

\[
TPR \ge 0.95.
\]

## Clearly-loaded miss rate

Fraction of clearly-loaded simulations that never cross the loaded threshold.

Initial acceptance target:

\[
MissRate \le 0.05.
\]

## Clearly-loaded average detection roll

Mean first threshold-crossing roll among detected clearly-loaded simulations.

Initial acceptance target:

\[
AverageDetectionRoll \le 90.
\]

## Mildly-loaded detection rate

Report this value without imposing the clearly-loaded target.

This is intentionally a harder scenario.

## Posterior calibration

Use 10 posterior buckets across \([0,1]\).

For each non-empty bucket report:

- observation count;
- mean predicted loaded probability;
- empirical loaded frequency.

No manual bucket scoring is permitted.

## Prior sensitivity

Repeat the configured analysis using prior loaded probabilities:

- 0.10
- 0.25
- 0.50
- 0.75
- 0.90

The results must be machine-readable.

---

# 12. Video storyboard

The opening must immediately display:

> How many rolls before the model becomes suspicious?

Do not begin with an explanation of Bayes' theorem.

## Beat 1 — Unknown die

A die begins rolling.

The viewer is not told whether it is fair or loaded.

## Beat 2 — Evidence begins

Show:

- observed face;
- cumulative counts;
- posterior loaded probability.

## Beat 3 — Suspicious streak

A visually suspicious streak occurs.

The sequence is deterministic under the configured showcase seed.

The streak is not itself treated as proof.

## Beat 4 — Uncertainty

The model remains visibly uncertain if the 0.95 loaded threshold has not been
crossed.

This is a core narrative requirement.

## Beat 5 — Evidence accumulates

More rolls arrive.

Update:

- counts;
- posterior;
- posterior predictive distribution;
- suspicion gauge.

## Beat 6 — Threshold event

If the posterior reaches 0.95, visually mark the first threshold-crossing
roll.

Never fabricate a crossing if one does not occur.

## Beat 7 — Final verdict

Show:

- final posterior loaded probability;
- final state;
- detection roll when applicable.

## Beat 8 — Reveal

Reveal the true six face probabilities only after the inference sequence has
played out.

## Beat 9 — Technical footer

Display:

> Bayesian inference · Dirichlet model · Sequential evidence · Python

The video must remain understandable without audio.

---

# 13. Acceptance criteria

Project 1 is not complete merely because a video renders.

## Configuration

- exactly six face probabilities per scenario;
- every probability is finite and non-negative;
- every scenario sums to one within `1e-12`;
- fair scenario equals the uniform distribution;
- mild and clear scenarios differ from the fair distribution;
- clearly-loaded scenario is more strongly biased than mildly-loaded;
- seeds are deterministic non-negative integers;
- roll count is 180;
- model prior probability is within `[0,1]`;
- fair threshold is below loaded threshold.

## Simulation

- same seed and probabilities reproduce the identical sequence;
- different configured seeds do not reproduce the identical complete
  sequence;
- generated faces are always integers 1 through 6;
- final counts sum to roll count.

## Inference

- all posterior values remain within `[0,1]`;
- posterior fair plus posterior loaded equals one within tolerance;
- predictive probabilities sum to one within `1e-12`;
- log-space calculations are used;
- no configured run produces NaN or infinity;
- known small analytical cases match independently calculated values.

## Calibration

- false-positive rate is at most 0.05;
- clearly-loaded true-positive rate is at least 0.95;
- clearly-loaded miss rate is at most 0.05;
- clearly-loaded average detection roll is at most 90;
- mild-die performance is reported separately;
- posterior calibration buckets are machine-readable;
- prior sensitivity is machine-readable;
- no human scoring is required.

## Media

- video is 1080 × 1350;
- frame rate is 30 fps;
- codec is H.264;
- pixel format is yuv420p;
- manifest is generated;
- seed is persisted;
- important result metrics are persisted.

---

# 14. Scope exclusions

The initial implementation does not include:

- neural networks;
- reinforcement learning;
- external AI APIs;
- model training;
- physical camera-based die recognition;
- live video inference;
- change-point detection;
- switching the die halfway through;
- the future “rigged streak that is actually fair” variant.

Those variants remain future extensions.

---

# 15. Future-compatible variants

The architecture must later be able to support:

> This streak looks rigged. It isn't.

and:

> I switched the die halfway. When did the model notice?

Neither variant is part of the initial Project 1 implementation.

---

# 16. Definition of Step 1 success

Project 1 — Step 1 succeeds when:

- the YAML configuration parses;
- all deterministic scenarios validate;
- the statistical formulas and decision states are documented;
- output schemas are fixed;
- storyboard beats are fixed;
- acceptance criteria are machine-checkable;
- no simulation or inference implementation has been prematurely added;
- Ruff, mypy, pytest, and Git integrity remain green.
