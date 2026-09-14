# Project 6 — Step 15.2 Final Claims + Metric Freeze

**Status:** `PASS`

## Canonical headline

> Traffic pressure warning at 24:00; independent congestion validation did not confirm a sustained queue.

## Frozen recruiter-facing KPI set

- Traffic state: **WARNING**
- Warning onset: **24:00**
- Last-60s mean observed zone occupancy: **3.70**
- Entry–exit balance: **+5 (8 in / 3 out)**
- Throughput: **3 eligible exits / 60s**
- Relative movement index: **0.0113054 image diagonals/s**
- Congestion / queue: **NOT CONFIRMED**
- Lead time: **Not reportable**

Window:

`(23:00,24:00]`

## Frozen first-15-second story

Camera → Vehicles → Flow Metrics → WARNING → Congestion Validation → Review / Monitor

## Operational interpretation

The system identified traffic pressure based on the configured multi-signal warning logic, but the independent sustained-queue rule did not qualify. The release therefore does not make a congestion-prediction or lead-time claim.

## Approved action

- Primary: **Escalate for review**
- Alternative: **Monitor**
- Classification: illustrative / conditional operational response

## Historical metrics permitted only with context

- `4.45`: later-interval rolling occupancy only.
- `+486.8%`: later-versus-baseline descriptive comparison only.
- `131 entries / 81 exits`: full 30-minute episode totals only.
- `49.15s`: supported rolling dwell statistic only; no baseline-change claim.

## Prohibited release claims

- Queue predicted.
- Congestion predicted.
- Positive warning lead time.
- Confirmed congestion.
- Proven intervention impact.
- Production traffic deployment.
- Live production monitoring.

## Publication status

`PENDING_SOURCE_PERMISSION`

This is a publication-only constraint. It does not alter the analytical result.

## Step 15.3 report-context review

Some historical values remain present in the report and require contextual verification during Video + Report Acceptance.

- `81` — `full_episode_exits`

## Freeze files

- `outputs\p05_traffic_operations_early_warning\manifests\final_claims_metric_freeze.json`
- `outputs\p05_traffic_operations_early_warning\manifests\frozen_presentation_contract.json`

## Status

- Step 15: `IN_PROGRESS`
- Sub-step 15.2: `VERIFIED`

Next:

**Project 6 — Step 15 — Sub-step 15.3 — Video + Report Acceptance**
