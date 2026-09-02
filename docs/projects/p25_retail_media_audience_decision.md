# Retail Media Audience Decision Studio

## Status

Project 4 contract/scaffold frozen. Analytical implementation starts in Step 2.

## Product question

How would an analytics and data-product owner turn independent customer,
experiment, behavioral-funnel, and media evidence into governed audiences and
defensible activation decisions?

## Evidence architecture

The project deliberately maintains separate evidence environments:

- dunnhumby Complete Journey — retail customer behavior and true RFM.
- Hillstrom — randomized treatment/control incrementality and uplift modeling.
- Criteo Attribution — anonymized media journeys and attribution.
- Retailrocket — behavioral view/add-to-cart/transaction funnel.
- Synthetic journeys — deterministic unit-test fixtures only.

Unrelated customer identities are never joined or fabricated.

## Causal language

Attribution distributes observed conversion credit.

Incrementality estimates whether an intervention caused an outcome that would
otherwise not have occurred.

Only evidence designed for causal inference may support causal claims.

## Dashboard

The canonical recruiter-facing product is a self-contained HTML dashboard with
a 1536×1024 canonical PNG snapshot.

The uploaded preview is an art-direction reference identified by the frozen
contract in:

    assets/p25_retail_media_audience_decision/visual_reference.json

Its verified source-image SHA256 is:

    abe93962fc863ec9d21ef3574d7152b7759718b21c30e27cd160136dfb2360e3

Mock values are never production data.

The final dashboard preserves the reference composition, density, hierarchy,
dark visual language, KPI row, analytical-panel structure, lower tables, and
provenance treatment while displaying only metrics supported by validated
Project 4 outputs.

## Criteo cost semantics

Criteo cost and CPO values are transformed source values.

Project 4 therefore uses the public label Media Cost Index and does not claim
literal advertiser spend or literal monetary ROAS from those transformed
values.

## Licensing and redistribution

Raw third-party datasets remain outside Git.

Each source's applicable terms must be verified at acquisition and recorded in
provenance before public artifacts are frozen.

Criteo Attribution is treated as CC BY-NC-SA 4.0 evidence.

dunnhumby and Retailrocket remain acquisition-gated until the exact terms
applicable to the downloaded copies are recorded.

## Machine learning

Core Version 1 includes:

- true RFM features;
- behavioral and category features;
- KMeans candidate k values 3, 4, 5, and 6;
- deterministic model selection;
- PCA visualization;
- randomized uplift modeling using a TwoModels/T-learner baseline;
- uplift-at-k, Qini, and cumulative-gain evaluation.

Deep learning is intentionally outside core Version 1.

## Repository interface

Run the root project namespace with:

    python -m linkedin_visual_labs retail-media --help

Step 1 registers scaffold interfaces only.

Analytical implementations arrive in the subsequent Project 4 steps.

## Frozen commands

    python -m linkedin_visual_labs retail-media fetch-data
    python -m linkedin_visual_labs retail-media validate-data
    python -m linkedin_visual_labs retail-media build-features
    python -m linkedin_visual_labs retail-media segment
    python -m linkedin_visual_labs retail-media train-uplift
    python -m linkedin_visual_labs retail-media measure
    python -m linkedin_visual_labs retail-media build-funnel
    python -m linkedin_visual_labs retail-media attribute
    python -m linkedin_visual_labs retail-media recommend
    python -m linkedin_visual_labs retail-media build-dashboard
    python -m linkedin_visual_labs retail-media validate-outputs
    python -m linkedin_visual_labs retail-media run-all
