# Project 1 — Bayesian Dice Detective

## Question

**How many rolls before knowing whether a pair of dice is loaded?**

This project is a deterministic Bayesian experiment and visualization that
compares six possible pair-of-dice models using only the observed sum of each
pair roll.

## Experiment

Each physical die is one of three types:

| Type | Meaning | Face probabilities 1–6 |
|---|---|---|
| U | Unloaded | 1/6 for every face |
| P | Partially loaded | 0.15, 0.15, 0.15, 0.15, 0.15, 0.25 |
| F | Fully loaded | 0.12, 0.12, 0.12, 0.12, 0.12, 0.40 |

The six unordered pair models are:

| Internal ID | Viewer-facing label |
|---|---|
| UU | Unloaded - Unloaded |
| UP | Unloaded - Partially Loaded |
| UF | Unloaded - Fully Loaded |
| PP | Partially Loaded - Partially Loaded |
| PF | Partially Loaded - Fully Loaded |
| FF | Fully Loaded - Fully Loaded |

Internal IDs remain stable machine-readable identifiers. Viewer-facing
visualizations use the descriptive labels.

## Observation model

The simulation retains both physical die faces for provenance.

Bayesian inference receives only:

```text
pair sum ∈ {2, 3, ..., 12}
```

The eleven-value pair-sum probability mass function for each model is derived
by convolution from the two constituent die probability distributions.

Pair-sum PMFs are never hard-coded.

## Bayesian models

The six exact models are:

```text
M_UU
M_UP
M_UF
M_PP
M_PF
M_FF
```

All six pair-sum PMFs are required to be distinct.

## Priors

The prior model probabilities are:

```text
P(M_UU) = 0.50
P(M_UP) = 0.10
P(M_UF) = 0.10
P(M_PP) = 0.10
P(M_PF) = 0.10
P(M_FF) = 0.10
```

Therefore:

```text
P(fair)   = P(M_UU)
P(loaded) = 1 - P(M_UU)
```

The video reports the latter quantity as **Loaded Probability**.

## Sequential Bayesian inference

For cumulative pair-sum counts `n_s` and model probabilities `q_M,s`:

```text
log L_M = Σ_s n_s log(q_M,s)
```

Posterior normalization is performed in log space.

The implementation also applies an explicit floating-point normalization after
exponentiation so posterior probabilities remain numerically normalized during
long 10,000-roll sequences.

## Decision thresholds

The sequential classification thresholds are:

```text
FAIR      if P(loaded) <= 0.05

UNCERTAIN if 0.05 < P(loaded) < 0.95

LOADED    if P(loaded) >= 0.95
```

## Headline metric

The headline result is **Stable Roll**, not the first threshold crossing.

For a case whose final state is FAIR or LOADED, the Stable Roll is the earliest
roll after which every remaining roll through roll 10,000 retains that same
final decision state.

The first FAIR and LOADED threshold crossings are retained only as diagnostic
metrics.

## Canonical experiment

The canonical experiment contains:

```text
10,000 pair rolls per case
6 cases
60,000 observed pair sums
```

Canonical deterministic seeds are:

| Case | Seed |
|---|---:|
| UU | 1101 |
| UP | 1102 |
| UF | 1103 |
| PP | 1104 |
| PF | 1105 |
| FF | 1106 |

The required final truth alignment is:

```text
UU -> FAIR
UP -> LOADED
UF -> LOADED
PP -> LOADED
PF -> LOADED
FF -> LOADED
```

Automated validation fails if a canonical case does not produce the required
truth-aligned final state.

## Canonical data artifacts

Generated runtime artifacts live under the ignored `outputs/` tree:

```text
outputs/p01_bayesian_dice/data/pair_simulation.json
outputs/p01_bayesian_dice/data/pair_case_histories.csv
outputs/p01_bayesian_dice/data/pair_case_summary.json
outputs/p01_bayesian_dice/data/pair_validation.json
```

The canonical pair history contains exactly 60,000 inference records.

## Authoritative implementation

The authoritative pair-dice execution path is implemented through:

```text
config.py
models.py
simulation.py
pair_inference.py
pair_metrics.py
pair_visualization.py
pair_video.py
pipeline.py
```

Legacy single-die compatibility modules may remain in the repository while
compatibility tests are retained, but they are not part of the authoritative
Project 1 execution path and are not exposed through the Project 1 package-root
API.

## Visualization contract

The production video uses:

```text
1080 x 1080 pixels
1:1 aspect ratio
30 fps
approximately 45 seconds
1,350 scheduled frames
H.264
yuv420p
```

The six analytical panels are synchronized to the same actual Bayesian roll
index.

The nonlinear frame schedule may repeat or skip real roll indices to improve
visual pacing, but posterior probabilities are never interpolated.

Every canonical Stable Roll is explicitly represented in the frame schedule.

## Viewer-facing panel content

Each panel displays:

- descriptive case name,
- current real roll index,
- Loaded Probability,
- FAIR / UNCERTAIN / LOADED decision badge,
- cumulative pair-sum counts for sums 2 through 12,
- Loaded Probability trajectory,
- final Stable Roll,
- final Loaded Probability.

The internal IDs `UU`, `UP`, `UF`, `PP`, `PF`, and `FF` remain machine-readable
keys but are not used as the primary viewer-facing case names.

## Viewer-facing case names

```text
UU -> Unloaded - Unloaded
UP -> Unloaded - Partially Loaded
UF -> Unloaded - Fully Loaded
PP -> Partially Loaded - Partially Loaded
PF -> Partially Loaded - Fully Loaded
FF -> Fully Loaded - Fully Loaded
```

## Video layout

The square canvas is divided into:

```text
Heading:
x=0
y=0
width=1080
height=40

Analytical grid:
x=0
y=40
width=1080
height=1000

3 columns x 2 rows
each panel = 360 x 500

Bottom explanatory strip:
x=0
y=1040
width=1080
height=40
```

The panel order is:

```text
Top row:
UU, UP, UF

Bottom row:
PP, PF, FF
```

## Visual quality contract

The renderer automatically validates:

- exact 1080 x 1080 canvas dimensions,
- analytical panel bounds,
- text bounds,
- clipping,
- tracked text overlap,
- synchronized roll state,
- readable minimum typography.

The final visual design uses descriptive case titles, larger typography,
decision badges, analytical charts, and dedicated per-panel result cards.

## Production video artifact

The final production video is generated at:

```text
outputs/p01_bayesian_dice/video/how_many_rolls_loaded_dice_pair.mp4
```

## Video manifest

The production manifest is generated at:

```text
outputs/p01_bayesian_dice/manifests/how_many_rolls_loaded_dice_pair.json
```

The manifest records:

- project identity,
- experiment question,
- observation model,
- Stable Roll headline metric,
- frame schedule metadata,
- encoder settings,
- media probe metadata,
- automated media validation,
- video SHA-256,
- canonical input SHA-256 hashes,
- final results for all six cases.

## Deterministic frame schedule

The canonical schedule uses:

```text
30 fps
45 seconds
1,350 frames
roll 1 as the first state
roll 10,000 as the final state
```

Roll indices are monotonically non-decreasing.

The schedule is deliberately nonlinear so early evidence and decision
transitions receive more screen time.

Only real Bayesian states are rendered.

No posterior interpolation is permitted.

## Reproduce the schedule

Run:

```bash
python -m \
    linkedin_visual_labs.projects.p01_bayesian_dice.pair_video \
    schedule
```

## Render the production video

Run:

```bash
python -m \
    linkedin_visual_labs.projects.p01_bayesian_dice.pair_video \
    render
```

## Validate the production video

Run:

```bash
python -m \
    linkedin_visual_labs.projects.p01_bayesian_dice.pair_video \
    validate
```

The media validation contract verifies the expected:

```text
1080 x 1080
30 fps
1,350 frames
approximately 45 seconds
H.264
yuv420p
```

## Source-quality validation

Run:

```bash
ruff format --check .
ruff check .
mypy src tests
pytest
```

## Statistical validation

The canonical statistical validation verifies:

- authoritative pair experiment is enabled,
- exactly six canonical cases exist,
- exactly 10,000 rolls exist per case,
- exactly 60,000 total history rows exist,
- inference consumes pair sums rather than individual die faces,
- posterior probabilities remain normalized,
- cumulative pair-sum counts remain internally consistent,
- every final canonical decision matches truth,
- every case has a Stable Roll,
- each Stable Roll is the earliest permanently stable decision,
- final threshold classification agrees with the final posterior.

## Media validation

The production media validation verifies:

- exact frame width,
- exact frame height,
- H.264 codec,
- yuv420p pixel format,
- 30 fps frame rate,
- 1,350-frame count,
- approximately 45-second duration.

## Manifest integrity

The manifest includes SHA-256 hashes for:

```text
pair_simulation.json
pair_case_histories.csv
pair_case_summary.json
pair_validation.json
how_many_rolls_loaded_dice_pair.mp4
```

This connects the rendered artifact to the deterministic canonical experiment
that produced it.

## Generated-output policy

Generated runtime artifacts are intentionally excluded from Git.

The repository tracks:

- source code,
- configuration,
- tests,
- documentation,
- CI configuration.

The repository does not track:

- generated canonical JSON,
- generated CSV histories,
- preview images,
- production MP4 files,
- generated manifests.

## Determinism

Project 1 is reproducible because the following are deterministic:

- die probability definitions,
- pair-model definitions,
- priors,
- decision thresholds,
- seeds,
- pair simulation,
- pair-sum convolution,
- Bayesian inference,
- Stable Roll calculation,
- frame-schedule construction,
- media-validation rules.

## Release acceptance

Project 1 is release-ready only when all of the following pass:

```text
Ruff formatting
Ruff lint
mypy
full pytest suite
Project 1 tests
canonical statistical validation
frame-schedule validation
visual geometry validation
media validation
manifest hash validation
Git diff integrity
generated-output isolation
```

## Final Project 1 contract

Project 1 answers one question:

> **How many rolls before knowing whether a pair of dice is loaded?**

It does so through a deterministic six-model Bayesian experiment, evaluates
60,000 pair-sum observations, reports the earliest permanently stable
classification for every case, and renders those results as a synchronized,
validated production video.
