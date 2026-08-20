# Project 2 — Zombie Escape: Dijkstra vs ML vs Deep Learning

## Viewer question

> **Who escapes best: Dijkstra, ML, or Deep Learning?**

## Core lesson

This project does not compare machine learning and deep learning against
Dijkstra as though all three were interchangeable shortest-path algorithms.

Instead, it studies routing under incomplete information.

Dijkstra receives the observed city and visible zombie-risk information.

Classical machine learning predicts hidden zombie risk from engineered local
features and then routes using A*.

Deep learning predicts a spatial zombie-risk surface from the full observed
city tensor and then routes using A*.

The simulator retains the hidden true zombie-risk field and uses it only for
evaluation.

An Oracle route may use the true hidden-risk field, but the Oracle is not a
headline contestant. It exists only to measure regret against perfect
information.

## Showcase cities

The project uses three deterministic synthetic downtown-inspired maps:

1. Phoenix Downtown
2. New York Downtown
3. Chicago Downtown

These environments are inspired by broad urban structural characteristics.
They are not geographic replicas of actual city streets.

Every showcase city uses a 36 x 36 logical grid and four-neighbor movement.

### Phoenix Downtown-inspired

Characteristics:

- wider arterial corridors,
- larger blocks,
- more open traversable space,
- lower intersection density,
- fewer hard choke points,
- dispersed hidden risk.

Canonical seed: `4203`.

### New York Downtown-inspired

Characteristics:

- dense orthogonal street structure,
- small blocks,
- many intersections,
- narrow corridors,
- strong choke-point density,
- strongly clustered hidden risk.

Canonical seed: `4201`.

### Chicago Downtown-inspired

Characteristics:

- regular medium-density grid,
- synthetic river barrier,
- limited bridge crossings,
- bridge-related choke points,
- clustered hidden risk.

Canonical seed: `4202`.

## Headline methods

### Dijkstra

Dijkstra is the deterministic baseline.

It operates directly on the observed map and visible zombie-risk surface.

Its estimated risk is therefore:

```text
observed visible risk
```

It does not know the true hidden zombie-risk field.

### Classical ML + A*

The classical machine-learning system uses a Gradient Boosting model.

The model predicts latent zombie risk from engineered local features.

The predicted risk surface is then supplied to A*.

The machine-learning model does not directly generate the path.

### CNN + A*

The deep-learning system uses a small convolutional neural network.

Its input is a multi-channel representation of the observed city.

Its output is a dense predicted zombie-risk surface.

That predicted surface is supplied to A*.

The CNN can learn spatial context unavailable to purely local feature models.

## Common routing objective

All three headline methods use the same planner-cost structure:

```text
planner cost
=
travel-time cost
+
4 × estimated zombie risk
```

Only the source of estimated risk differs.

This is required for a fair comparison.

## Hidden truth

The simulator maintains two risk representations:

```text
Observed risk
True hidden risk
```

Headline contestants may consume observed information only.

The true hidden-risk surface is used after route generation to evaluate route
quality.

## Route evaluation metrics

Every route reports:

- distance,
- estimated travel time,
- true cumulative zombie risk,
- maximum local true risk,
- number of high-risk cells crossed,
- route validity,
- start,
- destination,
- regret against the Oracle route.

A high-risk cell has:

```text
true risk >= 0.65
```

## Per-city winner

The winner for each showcase city is the lexicographically best route using:

1. lowest true cumulative risk,
2. fewest high-risk cells crossed,
3. lowest maximum local true risk,
4. lowest travel time,
5. lowest distance.

A deterministic method-order tie-break is used only if all meaningful metrics
remain equivalent.

## Overall winner

Across the three showcase cities, the overall winner is determined by:

1. most city wins,
2. lowest mean true cumulative risk,
3. lowest mean high-risk-cell count,
4. lowest mean travel time,
5. lowest mean distance.

The final winner must be computed from generated results.

The implementation may not hard-code ML, DL, or Dijkstra as the winner.

## Training and benchmark separation

The planned generated dataset contains:

```text
2,000 synthetic training cities
400 synthetic validation cities
400 synthetic benchmark cities
```

The three showcase cities are excluded from model training.

Canonical training seeds are fixed in configuration.

## Final video

The primary artifact is:

```text
outputs/p04_zombie_escape/video/
zombie_escape_dijkstra_vs_ml_vs_dl.mp4
```

Video contract:

```text
1080 x 1080
30 fps
60.0 seconds
1,800 frames
H.264
yuv420p
```

## Scene 1 — Overview

Duration:

```text
0–5 seconds
150 frames
```

Geometry:

```text
Heading:
1080 x 45

Content:
1080 x 1035
```

The content contains a 3 x 3 grid.

Columns:

```text
Dijkstra
ML + A*
CNN + A*
```

Rows:

```text
Phoenix
New York
Chicago
```

Each cell is:

```text
360 x 345
```

## Scene 2 — New York

Duration:

```text
5–20 seconds
450 frames
```

Geometry:

```text
Heading       1080 x 45
Dijkstra      1080 x 330
ML + A*       1080 x 330
CNN + A*      1080 x 330
Result        1080 x 45
```

Each method layer contains:

```text
Map area      780 x 330
Metric area   300 x 330
```

## Scene 3 — Chicago

Duration:

```text
20–35 seconds
450 frames
```

Uses the same geometry as New York.

## Scene 4 — Phoenix

Duration:

```text
35–50 seconds
450 frames
```

Uses the same geometry as New York.

## Scene 5 — Final summary

Duration:

```text
50–60 seconds
300 frames
```

Geometry:

```text
Heading             1080 x 45
Comparison board    1080 x 855
Final takeaway      1080 x 180
```

The comparison includes:

- city results,
- city winners,
- average true risk,
- average time,
- average distance,
- overall winner.

## Final takeaway

The intended conceptual conclusion is:

> **Optimization finds the best route for the costs it knows. Learning can
> help estimate the danger it cannot see.**

The actual winning method is never predetermined.

## Visual-quality contract

Project 2 inherits the visual-quality lessons from Project 1.

Requirements include:

- exact 1080 x 1080 frames,
- 120-DPI rendering basis,
- readable typography,
- no text clipping,
- no unintended tracked-text overlap,
- deterministic region geometry,
- visible routes,
- visible start and destination markers,
- high-contrast risk maps,
- method and city labels that remain readable on mobile,
- automated preview validation before final video rendering.

Minimum typography targets:

```text
Main heading            >= 12 pt
Major title             >= 9 pt
Primary metric          >= 7 pt
Secondary metric        >= 6 pt
Technical footer        >= 5 pt
```

Encoding target:

```text
libx264
CRF 16
medium preset
animation tuning
yuv420p
faststart
```

## Supporting outputs

Planned generated artifacts include:

```text
outputs/p04_zombie_escape/data/cities.json

outputs/p04_zombie_escape/data/training_dataset.parquet

outputs/p04_zombie_escape/data/predicted_risk_maps.json

outputs/p04_zombie_escape/data/routes.json

outputs/p04_zombie_escape/data/evaluation_summary.json

outputs/p04_zombie_escape/models/ml_risk_model

outputs/p04_zombie_escape/models/cnn_risk_model

outputs/p04_zombie_escape/previews/

outputs/p04_zombie_escape/images/thumbnail.png

outputs/p04_zombie_escape/manifests/
zombie_escape_dijkstra_vs_ml_vs_dl.json
```

Generated artifacts remain outside Git.

## Acceptance philosophy

The project is not accepted merely because it produces a visually attractive
video.

The analytical pipeline must also prove:

- deterministic cities,
- valid routes,
- common route-cost structure,
- hidden truth unavailable to headline methods,
- holdout showcase environments,
- valid ML and DL predictions,
- exact route evaluation,
- deterministic winner computation,
- reproducible frame schedule,
- exact media characteristics,
- validated visual layout,
- source-quality gates,
- generated-output isolation.
