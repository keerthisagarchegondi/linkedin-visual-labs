# Bayesian Dice Detective

## Revised project contract

Viewer question:

> How many rolls before knowing whether a pair of dice is loaded?

The revised experiment models a game in which two dice are rolled and only
their sum is used for inference.

Examples include Monopoly, Catan, backgammon, and other two-dice games.

The word "AI" may be used in social-media copy, but the analytical method is
Bayesian inference. The project does not use a neural network or external AI
service.

---

# 1. Experimental question

Three kinds of six-sided dice exist:

- fair / unloaded;
- partially loaded;
- fully loaded.

They form six unique unordered pair cases:

1. UU — Fair + Fair
2. UP — Fair + Partially Loaded
3. UF — Fair + Fully Loaded
4. PP — Partially Loaded + Partially Loaded
5. PF — Partially Loaded + Fully Loaded
6. FF — Fully Loaded + Fully Loaded

Each case is rolled 10,000 times.

The inference engine observes only:

`sum = die_1 + die_2`

and therefore receives observations from 2 through 12.

Individual die faces are retained for simulation provenance but are not
available to the Bayesian inference algorithm.

---

# 2. Die definitions

## U — fair die

\[
p_U =
(1/6,1/6,1/6,1/6,1/6,1/6)
\]

## P — partially loaded die

\[
p_P =
(0.15,0.15,0.15,0.15,0.15,0.25)
\]

## F — fully loaded die

\[
p_F =
(0.12,0.12,0.12,0.12,0.12,0.40)
\]

Each vector must:

- contain exactly six finite non-negative probabilities;
- sum to one within numerical tolerance.

---

# 3. Pair-sum probability models

For pair model \(M_{AB}\), let the two die probability vectors be \(p_A\) and
\(p_B\).

For observed sum \(s\),

\[
P(S=s \mid M_{AB})
=
\sum_{\substack{i,j\in\{1,\dots,6\}\\i+j=s}}
p_A(i)p_B(j).
\]

The sum distribution therefore contains eleven probabilities corresponding to:

\[
s \in \{2,3,\dots,12\}.
\]

The implementation must derive these distributions by convolution rather than
hard-code them.

Every derived sum probability vector must sum to one.

---

# 4. Six Bayesian hypotheses

The model space is:

\[
M_{UU}, M_{UP}, M_{UF}, M_{PP}, M_{PF}, M_{FF}.
\]

These are exact probability models rather than unknown Dirichlet alternatives.

For cumulative sum counts \(n_2,\dots,n_{12}\), the log likelihood under model
\(M\) is:

\[
\log p(x_{1:n}\mid M)
=
\sum_{s=2}^{12}
n_s \log q_{M,s},
\]

where \(q_{M,s}\) is the probability of sum \(s\) under model \(M\).

All likelihood calculations must remain in log space.

---

# 5. Model priors

The project begins neutral on the viewer-facing fair-versus-loaded question:

\[
P(\text{fully fair pair}) = 0.50
\]

and:

\[
P(\text{some loading}) = 0.50.
\]

The exact model priors are:

\[
P(M_{UU})=0.50
\]

and:

\[
P(M_{UP})
=
P(M_{UF})
=
P(M_{PP})
=
P(M_{PF})
=
P(M_{FF})
=
0.10.
\]

Therefore before any observation:

\[
P(\text{loaded})=0.50.
\]

---

# 6. Posterior probabilities

After every observed sum, calculate the posterior probability of all six exact
models using log-space normalization.

For model \(M_k\),

\[
P(M_k\mid x)
=
\frac{
P(M_k)p(x\mid M_k)
}{
\sum_j P(M_j)p(x\mid M_j)
}.
\]

The six posterior probabilities must:

- remain in `[0,1]`;
- sum to one within `1e-12`.

---

# 7. Viewer-facing loaded probability

The pair is defined as fully fair only under `M_UU`.

Therefore:

\[
P(\text{loaded}\mid x)
=
1-P(M_{UU}\mid x).
\]

And:

\[
P(\text{fair}\mid x)
=
P(M_{UU}\mid x).
\]

A pair is "loaded" whenever at least one component die is loaded.

---

# 8. Decision states

## FAIR

If:

\[
P(\text{loaded}\mid x)\le0.05
\]

the state is:

`FAIR`

## LOADED

If:

\[
P(\text{loaded}\mid x)\ge0.95
\]

the state is:

`LOADED`

## UNCERTAIN

Otherwise:

`UNCERTAIN`

---

# 9. First threshold crossing

For diagnostic purposes retain:

- first FAIR threshold crossing;
- first LOADED threshold crossing.

These values describe when the sequence first enters a confident region.

They are not the headline result because the posterior may later leave that
region.

---

# 10. Stable decision roll

The headline "number of rolls required" is the stable decision roll.

If the final decision is `LOADED`, the stable decision roll is the earliest
roll \(r\) for which every classification from roll \(r\) through roll 10,000
remains `LOADED`.

If the final decision is `FAIR`, the stable decision roll is the earliest roll
\(r\) for which every classification from roll \(r\) through roll 10,000
remains `FAIR`.

If the final state is `UNCERTAIN`:

`stable_decision_roll = null`

This avoids presenting a temporary random threshold crossing as the point where
the model permanently resolved the question.

---

# 11. Deterministic pair cases

Every canonical case contains 10,000 pair rolls.

## UU

- Fair + Fair
- seed: 1101
- truth: FAIR

## UP

- Fair + Partially Loaded
- seed: 1102
- truth: LOADED

## UF

- Fair + Fully Loaded
- seed: 1103
- truth: LOADED

## PP

- Partially Loaded + Partially Loaded
- seed: 1104
- truth: LOADED

## PF

- Partially Loaded + Fully Loaded
- seed: 1105
- truth: LOADED

## FF

- Fully Loaded + Fully Loaded
- seed: 1106
- truth: LOADED

The seeds define canonical narrative datasets.

No result value, posterior, threshold crossing, or stable decision roll may be
hard-coded.

---

# 12. Randomness contract

All canonical simulations must:

- use the repository's shared deterministic random infrastructure;
- avoid hidden global random state;
- persist the configured seed;
- reproduce identical pair sequences for identical configuration and seed.

Different pair-case seeds must produce distinct complete canonical sequences.

---

# 13. Pair simulation output

Canonical path:

`outputs/p01_bayesian_dice/data/pair_simulation.json`

The top-level payload contains:

- project ID;
- 10,000-roll case size;
- all six cases.

Each case contains:

- case ID;
- readable label;
- seed;
- die type identifiers;
- both face-probability vectors;
- generated sum sequence;
- final counts for sums 2 through 12.

The simulation may retain individual faces for provenance, but inference must
consume only the sum sequence.

---

# 14. Sequential history output

Canonical path:

`outputs/p01_bayesian_dice/data/pair_case_histories.csv`

For every one of the 60,000 observations store:

- case ID;
- roll index;
- observed sum;
- cumulative counts for sums 2 through 12;
- six model log likelihoods;
- six posterior model probabilities;
- posterior loaded probability;
- posterior fair probability;
- most likely exact model;
- FAIR / UNCERTAIN / LOADED state.

---

# 15. Pair summary output

Canonical path:

`outputs/p01_bayesian_dice/data/pair_case_summary.json`

For each pair case store:

- case ID;
- label;
- generating truth;
- final posterior loaded;
- final posterior fair;
- final highest-probability exact model;
- final decision state;
- first FAIR threshold crossing;
- first LOADED threshold crossing;
- stable decision roll;
- stable decision state;
- final sum counts.

---

# 16. Experiment size

Canonical experiment:

\[
6 \text{ cases}
\times
10,000 \text{ rolls}
=
60,000 \text{ observed sums}.
\]

All six cases must be evaluated.

---

# 17. Square video contract

Canonical output:

`outputs/p01_bayesian_dice/video/how_many_rolls_loaded_dice_pair.mp4`

Video specification:

- width: 1080 px;
- height: 1080 px;
- aspect ratio: 1:1;
- frame rate: 30 fps;
- codec: H.264;
- pixel format: yuv420p;
- target duration: approximately 45 seconds.

---

# 18. Video geometry

The canvas contains three major vertical sections.

## Heading

Coordinates:

- x = 0
- y = 0
- width = 1080
- height = 40

Text:

> How many rolls before knowing whether a pair of dice is loaded?

The title must fit entirely within the assigned region.

## Six-panel analytical grid

Coordinates:

- x = 0
- y = 40
- width = 1080
- height = 1000

Grid:

- 3 columns;
- 2 rows;
- each panel = 360 × 500.

Placement:

Top row:

- UU
- UP
- UF

Bottom row:

- PP
- PF
- FF

## Results strip

Coordinates:

- x = 0
- y = 1040
- width = 1080
- height = 40

It contains six 180-pixel result cells.

Each cell displays compactly:

- case ID;
- stable decision roll;
- final P(load).

---

# 19. Panel content

Every 360 × 500 panel displays:

1. pair-case title;
2. current trial count;
3. current `P(load)`;
4. current status;
5. loaded-posterior gauge;
6. cumulative sum counts for 2 through 12;
7. posterior-loaded trajectory.

The six panels use the same component renderer and the same visual hierarchy.

No panel-specific hand-tuned layout is allowed.

---

# 20. Animation semantics

All six experiments progress simultaneously.

At any animation frame, every panel displays the same roll index.

A nonlinear frame-to-roll mapping may accelerate long regions, but it must
preserve:

- roll ordering;
- actual posterior trajectories;
- actual threshold events;
- actual stable-decision results.

No posterior or decision value may be interpolated analytically between unseen
rolls.

The display may sample existing computed roll states for frames.

---

# 21. Visual-fit contract

Every textual or graphical artist must remain inside its assigned region.

Automated layout validation must cover:

- title bounds;
- six panel bounds;
- panel headings;
- metric labels;
- metric values;
- posterior gauges;
- sum-count visualizations;
- trajectory axes;
- results strip;
- final footer.

Text clipping is a validation failure.

Artist overlap outside intentionally shared chart elements is a validation
failure.

The implementation should automatically fit typography rather than assume a
single font size will work.

---

# 22. Technical footer

Use only the compact technical footer:

> Bayesian inference · Pair-sum likelihoods · Sequential evidence · Python

Do not include verbose sentences such as:

> Transparent Bayesian model comparison — no neural network.

inside analytical panels.

---

# 23. Preview-frame contract

Before full MP4 encoding, generate representative ignored PNG frames.

At minimum:

- initial frame;
- early evidence;
- one frame near each unique stable-decision event;
- roll 10,000;
- final results frame.

Every preview must be exactly:

`1080 × 1080`

and pass automated geometry checks.

---

# 24. Analytical acceptance criteria

The revised analytical implementation must prove:

- exactly three die types;
- exactly six unique unordered pair cases;
- exactly 10,000 rolls per case;
- exactly 60,000 observed sums;
- every observed sum is in 2 through 12;
- all pair sum PMFs are derived by convolution;
- every pair PMF sums to one;
- all likelihoods are calculated in log space;
- all six posterior probabilities remain in `[0,1]`;
- all six model posteriors sum to one;
- `P(load) = 1 - P(M_UU)`;
- stable-decision calculations are internally consistent;
- no non-finite numerical outputs occur.

Expected final truth alignment:

- UU → FAIR
- UP → LOADED
- UF → LOADED
- PP → LOADED
- PF → LOADED
- FF → LOADED

If a deterministic canonical case does not satisfy this expectation, the
implementation must fail validation rather than silently change the data or
thresholds.

---

# 25. Media acceptance criteria

The final MP4 must be:

- exactly 1080 × 1080;
- 1:1;
- 30 fps;
- H.264;
- yuv420p;
- approximately 45 seconds.

It must visibly contain:

- one heading;
- six pair-case panels;
- all six current roll counts;
- all six P(load) values;
- all six decision states;
- all six posterior gauges;
- all six sum-count displays;
- all six posterior trajectories;
- one six-case results strip.

No manual statistical scoring is required.

---

# 26. Transitional compatibility

The current repository already contains working single-die implementations from
the earlier Steps 2 through 5.

During Revised Step 1 only, their YAML keys remain present so the repository
continues passing its existing tests.

They are not authoritative for the revised project.

Revised Step 2 will migrate:

- typed configuration;
- domain models;
- pipeline contracts;
- tests

to the pair-of-dice design.

Only after that migration is green will the obsolete single-die compatibility
contract be removed.

---

# 27. Revised project roadmap

The remaining project is:

## Revised Step 2

Pair-dice typed configuration and domain-model migration.

## Revised Step 3

Deterministic six-case pair simulation.

## Revised Step 4

Six-model Bayesian sequential inference.

## Revised Step 5

Canonical 60,000-observation experiment and automated validation.

## Revised Step 6

1080 × 1080 six-panel visualization framework.

## Revised Step 7

Animation, CLI orchestration, manifest, and final video rendering.

## Revised Step 8

Documentation, CI, pull request, and merge.

---

# 28. Definition of Revised Step 1 success

Revised Step 1 succeeds when:

- the authoritative pair contract exists in YAML;
- the documentation describes the pair experiment;
- all three die vectors validate;
- all six pair cases validate;
- model priors sum to one;
- prior P(load) equals 0.50;
- video geometry sums exactly to 1080 × 1080;
- panel geometry is exactly 360 × 500;
- result cells are exactly 180 px wide;
- output schemas are fixed;
- legacy committed Steps 2–5 remain operational during migration;
- Ruff passes;
- mypy passes;
- pytest passes;
- Git integrity passes.
