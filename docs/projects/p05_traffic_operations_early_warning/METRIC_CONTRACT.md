# Project 6 — Metric contract

## Status, eligibility and analytical clock

Step 1 implements immutable metric/configuration declarations; no measurements or
runtime evaluators exist. Checked-in metric, queue and warning review remains required.
Numeric detection/motion/queue thresholds and minimum sample counts are deliberately
unselected pending the approved protocol and source. This is an explicit gate, not
permission to invent defaults from preview values.

All calculations use original source timestamps (PTS and time base), not accelerated
playback time. Retain source/frame/track/event identifiers through the chain. Define
eligibility and geometry version explicitly. Proposed vehicle reference point is
bottom-center; reject ambiguous crossings and distinguish observed, predicted-only,
interpolated, incomplete and censored observations. Long unsupported predictions
must not inflate occupancy or queue evidence.

Temporary IDs are clip-local and analytical, not persistent vehicle identities.
Track fragmentation cannot be silently repaired by inventing identity. Step 1 locks
re-entry/session policy: entry/exit and throughput must not double-count the same
eligible track in a window; completed sessions require paired valid observations.

## Implemented semantic locks

AnalysisConfig fixes original-source time, BOTTOM_CENTER, exclusion of unsupported
predictions and preservation of censoring. Sampling/presentation cannot rescale
analytical time; fragmentation cannot invent identity. MetricsConfig fixes throughput
and imbalance to 300 seconds over (t-window,t], unique directional tracks per window,
independently paired completed visits and exit-assigned completed original-time dwell.
Median and completed sample count accompany dwell; percentile bounds must be ordered
within 0..100, sample counts positive and coverage in (0,1]. Final percentile method,
thresholds, coverage, baseline and trend choices remain unresolved in the YAML.

Missing samples are UNAVAILABLE, missing evaluations BREAK_PERSISTENCE, warm-up
requires a full window, and zero/undefined baseline percentage delta is UNAVAILABLE.
Queue persistence declares duration, consecutive valid windows, or a required
proportion over a declared window count. Rule completeness is validated before
FROZEN; this does not execute a queue/warning rule or establish numerical validity.

ResultContract fixes signed visible-queue minus warning time, null for missing
onsets, no negative clamping and uncertainty separate from rounding. TransitionPolicy
declares missing evidence as quality-unavailable, full WARNING persistence as onset,
explicit reset persistence/hysteresis and no backdating from direct CRITICAL.
CalibrationConfig defaults to RELATIVE_ONLY; physical units require approved
source/geometry/method/evidence, and the root config must bind the approved source.
ClaimRecord likewise rejects physical units without applicable calibration evidence.

## Metric definitions

| Metric | Definition | Unit and evidence |
|---|---|---|
| Occupancy | Active anonymous tracks whose configured reference point lies inside the analysis zone | Vehicles; eligible track IDs, geometry and timestamp |
| Density | Initially the number of active tracked vehicles inside a defined zone | Vehicles, not vehicles per lane-mile |
| Entry | Unique eligible tracks crossing the entry boundary in the valid direction | Count; directed crossing events and original times |
| Exit | Unique eligible tracks crossing the exit boundary in the valid direction | Count; directed crossing events and original times |
| Throughput | Unique eligible exit crossings in the configured trailing window | Exits per window; default planning window 300 seconds (5 minutes) |
| Dwell | Original elapsed time between valid zone entry and valid zone exit for completed eligible tracks | Seconds; median, appropriate percentile range and completed sample size |
| Relative movement | Image-plane displacement normalized by original frame interval and, where justified, documented perspective band | Normalized image-plane distance per second; never MPH without calibration |
| Low-motion vehicle | Eligible track below configured normalized movement threshold for a persistent configured duration | Boolean per track/time, with threshold/duration evidence |
| Queue count | Eligible low-motion tracks within the configured queue zone | Vehicles with track/time/zone evidence |
| Queue persistence | Original-time duration or explicitly defined proportion of consecutive windows in which the independent queue outcome is active | Seconds or labeled proportion; cadence and missingness policy required |
| Inflow–outflow imbalance | Rolling unique entries minus rolling unique exits | Vehicles per configured window |

Dwell percentiles are calculated from eligible completed observations assigned by
their exit time, using a specified percentile method. Right-censored, left-censored,
lost and incomplete tracks are reported separately, never silently completed or
given zero dwell. Sampling/interpolation uncertainty must accompany any supported
crossing-time estimate. Boundary jitter requires explicit hysteresis/deduplication.

## Windows, baseline and insufficient evidence

Initial trailing-window convention: `(t - 300 seconds, t]`. Changes require approved
evidence, configuration versioning and rerunning dependent validation. Evaluation
cadence is explicit original time; it is not the number of decoded/rendered frames.

Freeze baseline interval, trend definition, minimum completed-track sample size,
coverage requirement, persistence duration/window count and missing-data behavior
before final evaluation. Do not choose them solely to maximize lead time. Baseline
uses only approved normal-flow observations; causal rolling metrics use no future
observations. Percentage deltas against zero/undefined baselines are unavailable,
not infinite claims. Publish absolute values and denominators where appropriate.

Sparse windows report sample count, observed coverage and availability reason.
Insufficient dwell samples produce unavailable dwell statistics, not zero. Warning
rules must explicitly handle unavailable drivers and cannot silently lower their
required evidence. Missing windows break required consecutive persistence unless
an independently justified frozen rule says otherwise. Insufficient data is a
quality state, not `NORMAL`. Retain warm-up and censored counts.

## Independently defined visible-queue outcome

The final outcome configuration is independent from warning. Candidate outcome-state
signals are queue-zone occupancy, low-motion vehicle count, queue count and sustained
persistence. Geometry, count thresholds, duration and evaluation cadence are explicit
configured assumptions. Independent source annotation validates whether this rule
captures a visible queue; rule output alone is not human ground truth.

`visible_queue_timestamp` is the first original-time evaluation satisfying the
complete configured outcome persistence rule. Do not backdate to the first window
in its persistence interval.

## Leading warning and states

Candidate leading signals: density level/trend, completed-dwell level/trend,
throughput flattening/decline, inflow–outflow imbalance, multiple simultaneously
deteriorating metrics and persistence. Shared primitive data are allowed; copying
the complete outcome rule or requiring outcome activation is prohibited.

States: `NORMAL`, `WATCH`, `WARNING`, `CRITICAL`. Step 1 locks transition, reset,
hysteresis, missing-data and direct-to-critical semantics. `warning_timestamp` is
the first evaluation satisfying the complete WARNING persistence rule. A direct
critical condition does not authorize an invented earlier warning timestamp.

## Lead time and classification

`lead_time_seconds = visible_queue_timestamp - warning_timestamp`.

Use signed seconds with source-time uncertainty. Positive means early, zero means
same supported onset, negative means late. Do not round an uncertain interval into
an unsupported claim of exact simultaneity or positive lead. Missing onset means
null lead time. Preserve separate quality/event facts and lock primary-classification
precedence before evaluation.

Supported results: `POSITIVE_EARLY_WARNING`, `WARNING_AT_VISIBLE_ONSET`,
`LATE_WARNING`, `NO_VALID_WARNING`, `NO_VISIBLE_QUEUE_EVENT`,
`INSUFFICIENT_SOURCE_EPISODE`, `INSUFFICIENT_DETECTION_QUALITY`,
`INSUFFICIENT_TRACK_QUALITY`. Invalid event/metric gates block evaluation; never
substitute normal traffic or a successful warning for an analytical failure.

All preview values are PREVIEW_ONLY. No timestamps, thresholds or sampling/edit
choices may be changed just to make lead time positive.

## Units, privacy and validation gates

No exact MPH, feet, lane-mile density or physical distance without genuine calibration.
Use counts, seconds, explicit proportions and normalized image-plane quantities.
No face recognition, license-plate OCR, driver identity, persistent IDs or cross-camera
re-identification. Public metrics are aggregate; examples cannot expose private identity.

Reconcile source → detections → tracks → events → metrics → queue outcome/warning
→ recommendation → release claims → visuals. Stage-specific independent detection
and track quality gates precede events; reconciled events precede metrics; validated
metrics precede warning. Final independent validation in Step 11 checks the whole
chain without replacing these gates. Tests must include known synthetic oracles,
window endpoints, missingness, censoring, duplicates, no future leakage, every result
classification, false-warning exposure, and a predeclared sensitivity neighborhood.


## FAST-TRACK BLOCK 3 amendment

Block 3 adds MetricPlan with a separate CONFIGURED_ASSUMPTION 60-second FAST_TRACK operational window and 1-second original-time cadence. Formal 300-second columns and Step 1 declarations remain unchanged. Baseline1260–1380 uses complete comparison windows1320–1379. Minimum completed dwell sample3; linear p10/p90. Known-at-observation confirmation and delayed crossing availability prevent premature counts. No baseline dwell is supported. See BLOCK3_REVIEW.md and the frozen block3.json for exact rules and limitations.
