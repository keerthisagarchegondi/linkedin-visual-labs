# Project 9: Point Adjustment Under Random Scores

## Purpose and scope

Project 9 is an independent partial replication and controlled finite-sample audit of point adjustment in time-series anomaly detection. It compares the same Bernoulli random-alert predictions under raw pointwise and point-adjusted scoring. It is not a detector benchmark, a claim that random alerts beat trained detectors, or a claim that all event-aware metrics are invalid.

## Source attribution and boundary

Kim et al., *Towards a Rigorous Evaluation of Time-Series Anomaly Detection* (AAAI 2022, DOI `10.1609/aaai.v36i7.20680`) established that point adjustment can overestimate performance and that random anomaly scores can produce high point-adjusted F1. Project 9 does not claim that finding as new.

The Project 9 contribution is limited to an independently implemented, fully specified controlled study that separates fixed prevalence, event cardinality, alert probability, finite-run mean F1, and ratio-of-expected-counts references. It reports uncertainty and preserves negative or inconclusive outcomes.

## Source protocol versus Project 9 model

The published PA protocol is the retrospective, label-aware evaluation rule in Kim et al. Eq. (4): after at least one threshold crossing inside a ground-truth anomaly segment, all positions in that segment are credited as predicted anomalous; outside-segment predictions remain governed by the threshold rule. It uses ground-truth segment boundaries and does not improve a detector.

Project 9 uses its own explicit generative model, recorded in `EXPERIMENT_PROTOCOL.md`. It must never silently substitute that model for a source equation or imply that it is the paper's exact derivation.

## Claim status

Permitted future claim families are `SOURCE_REPORTED`, `SOURCE_DISCREPANCY`, `REPLICATED_COMPUTATION`, `CONTROLLED_EXTENSION`, `MATHEMATICAL_DERIVATION`, `MONTE_CARLO_ESTIMATE`, `INTERPRETATION`, and `LIMITATION`. Public release blocks `UNSUPPORTED` claims.

The prohibited-claim list is literal: "I discovered point-adjustment inflation."; "Random beats AI."; "Random beats state-of-the-art anomaly detectors."; "All anomaly metrics are broken."; "All event-aware metrics are invalid."; "This proves real-world systems are misleading."; "This is peer reviewed" before peer review; "This is published" before verified publication; and any O-1 or immigration claim in scholarly or recruiter-facing material.

## Publication scope

`publication_scope_status = EDITORIAL_SCOPE_CHECK_NEEDED`. ReScience C is a plausible replication destination only if the study supplies substantial replication evidence and openly licensed reproducible materials. TMLR explicitly accepts reproducibility studies, but contribution sufficiency depends on convincing evidence and audience interest. No venue eligibility is guaranteed.
