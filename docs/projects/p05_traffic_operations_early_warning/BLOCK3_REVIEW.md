# Project 6 — FAST-TRACK BLOCK 3 review

Scope: Steps 8–11 only. No package installation, detector change, inference,
source acquisition, final poster/video/report, portfolio integration or Git action.
Actual code/configuration hashes were frozen before the final full repository suite.
Final gate status and exact evidence hashes are recorded by STATE.block_3_validation.

## Input acceptance and Step 8

Canonical root and expected project/p05-traffic-operations-early-warning branch
verified. Source/model/geometry, every frozen Block 2 analytical artifact and code
reference matched accepted hashes. Existing unrelated working-tree changes remain
untouched. The prior Block 2 full suite preceded its lifecycle-field correction;
this block's final full suite covers that correction as well as the final Block 3 code.

Metrics use 178 confirmed tracks, 15,727 eligible observations, 131 directional
entries and 81 exits. Excluded: 798 unconfirmed or preconfirmation observations;
507 incomplete journeys cannot contribute completed dwell. Zero invalid-jump tracks
and zero excluded-region observations enter accepted metrics. All 572 original
candidate tracks remain accounted for by the upstream inventory.

The 1-second grid uses exact sampled original frame times. A successfully analyzed
frame with no eligible vehicles is zero occupancy; a missing frame is unavailable.
No stale prediction or carried-forward position inflates counts. Confirmed status
must already be known at the observation; a historical crossing becomes available
no earlier than confirmation. Completed dwell uses 65 accepted, gap-free, ordered
entry/exit pairs, assigned by exit and availability time. Lifetime is never dwell.
The upstream audited completed-journey cohort is retrospective quality screening;
this is not a prospective identity-accuracy evaluation.

The formal 300-second contract remains intact, with explicit long-window columns.
The separate FAST_TRACK operational window is 60 seconds over (t-60,t], classified
CONFIGURED_ASSUMPTION. It consistently governs throughput, imbalance, completed
dwell, density averaging, movement comparison and the warning. It is justified by
the existing 120-second screened baseline, which cannot contain a full 300-second
normal-flow baseline window. No Step 1 model/configuration semantic lock was changed.

The candidate baseline [1260,1380) was retained after the predeclared coverage and
density-spread check. Within-baseline complete-window comparisons use 1320–1379s:
60 overlapping evaluations, not 60 independent trials. Median density-window mean
0.758333 vehicles; p10/p90 0.65/0.935, MAD 0.091667. Median throughput 2 exits/60s;
p10/p90 1/3, MAD 1. Median movement index 0.007695509 image diagonals/second;
p10/p90 0.005886999/0.009528714. Density unit remains vehicles in the configured zone.
The movement index is a median of per-evaluation median observed movements over
60 seconds; it is not physical road speed or a calibrated vehicle-distance measure.

Baseline dwell is unavailable: no operational window supports the minimum three
completed samples. Dwell is excluded from the primary warning rather than imputed.
Elsewhere each supported window records completed sample count, median, linear p10
and p90. The full-episode 65-completed-sample median is 42 seconds, not a baseline
statistic. At least ten observed movement evaluations are required per window.
Warm-up and incomplete coverage remain unavailable; zero-baseline relative changes
remain null. Report absolute imbalance changes across a signed/zero baseline.

## Step 9 — Rules frozen before evaluation

Configuration: configs/p05_traffic_operations_early_warning/block3.json.
The original frozen copy is in ignored block3/rules_before_evaluation.json. Neither
primary nor sensitivity parameters were selected from warning/lead-time results.

Primary evaluation is [1380,1800), after baseline completion. Earlier metric rows
remain available; the warning has no asserted state during calibration. This avoids
using a future fitted baseline to claim earlier prospective alerts. The baseline
false-warning diagnostic separately applies the fitted rule in-sample and says so.

Warning drivers: density mean >=1.758333 vehicles (max of baseline x1.5 and baseline
+1), imbalance >=2 entries minus exits/60s, throughput <=1.5 exits/60s, movement
<=0.005771632 image diagonals/second, density trend >=0.005 vehicles/second over 30s.
Three of five drivers for 30 original seconds establish WARNING. Four for 60s can
establish CRITICAL. At most one driver for 15s resets the latched state. WATCH is a
nonpersistent precursor. Missing evaluations break persistence and become quality
unavailable, never silently NORMAL. Direct critical does not backdate WARNING.

Independent queue outcome: queue-zone occupancy >=3, at least 2 eligible persistent
low-motion tracks in that zone, movement index <=0.005, continuously for 120s.
Low-motion threshold/persistence remain the upstream 0.002 image diagonals/second
and 3s. No warning state/score/lead time enters the queue rule. The 120s filter is a
conservative configured transient-stop assumption; no signal cycle was measured,
so it does not prove every ordinary red-light cycle is shorter than this duration.

Observed warning transitions: NORMAL 1380, WATCH 1383, WARNING 1440, NORMAL 1737,
WATCH 1754, NORMAL 1758. No CRITICAL transition. Primary driver at onset: density
level. Supporting: inflow–outflow imbalance and density trend. Throughput decline
and movement decline did not drive that onset.

No configured queue event qualified. The post-baseline eligible low-motion queue
count never exceeded zero. visible_queue_timestamp=null; lead_time_seconds=null;
result_classification=NO_VISIBLE_QUEUE_EVENT. This is not proof of no physically
visible queue. Model jitter, fragmentation, geometry and the strict primitive
low-motion contract limit the interpretation. No threshold was relaxed to create
an event. One unmatched warning episode lasted 297 seconds; no useful positive early
warning has been demonstrated.

Baseline false-warning episodes 0, warning exposure 0/60 evaluable seconds (0%). This
is in-sample and cannot establish a general false-alarm rate. Sensitivity was exactly
five predeclared rows: primary; density threshold±20%; queue persistence±30s.
Warning onsets respectively 1440,1430,1447,1440,1440. All queue onsets and lead times
remain null; all baseline warning counts zero. The primary rule remains headline.

## Mixed screened-interval evidence

The source-screened candidate [1440,1650) is not relabeled as a validated queue.
Its median rolling density 4.45 is +486.81% over baseline. Median throughput 3.5 is
+75%; movement 0.008994308 is +16.88%. Thus several measures indicate busier flowing
traffic, not universal deterioration. Median supported rolling dwell is 49.15s over
108 overlapping supported evaluations; baseline comparison is unavailable. This is
not a median over 108 independent vehicles. Median imbalance changes from -1 to +2.
Queue count is 0 in both intervals; percentage change is unavailable.

## Step 10 — Conditional recommendation

Enabled actions are MONITOR and ESCALATE_FOR_REVIEW, scoped to prototype analytical
monitoring/review. No facility control lever is enabled. Selected action:
ESCALATE_FOR_REVIEW; alternative MONITOR. Wording: “Consider escalating the recorded
deterioration for review.” Classification ILLUSTRATIVE_RECOMMENDATION. Possible
imbalance is an interpretation, not an established cause. No staffing, road control,
metering or overflow capacity is implied. Evidence IDs are the actual onset drivers.

## Step 11 — Independent validation and freeze

validation.py uses a separate scalar pathway from raw tracked observations and
crossings: it independently recomputes geometric membership, displacement, low
motion, confirmation, unique crossings, paired completed dwell and every metric
row. Python statistics/linear interpolation check medians/percentiles; baseline
statistics and normalization are separately checked. All 1,800 rows, 212 crossings,
65 completed samples and 42s full-episode median reconcile. Separate count-based
persistence recomputes queue/warning onsets and signed/null arithmetic. Recommendation
action/evidence links are checked. This is independent software recomputation, not
independent human annotation or detection/tracking/queue accuracy validation.

release_data.json is the only future renderer input for analytical claims. Six
aggregate-content claims are approved with exact source evidence hashes, calculation,
unit, caveat and reviewer status. The evidence index and metrics/warning/validation
manifests bind inputs, configuration, code and output bytes. Final artifact release
remains false. Raw footage, excerpts and transformed source imagery remain NOT
APPROVED; annotation/transformation does not automatically confer publication rights.
No source imagery appears in these diagnostic charts.

Diagnostic images: metric_trends.png and warning_queue_timeline.png, visually
reviewed for correct labels, original times and null queue/lead-time interpretation.
No final recruiter poster, LinkedIn video or five-tab report is generated.

## Gate/logging incident and resumption

An initial copied gate helper still targeted the ignored Block 2 log directory.
It overwrote focused/format/ruff/mypy logs and command JSON there before correction.
The new raw outputs are preserved under block3/initial_*; the incident is recorded
in logging_incident.json. Original Block 2 raw logs were not fabricated/restored.
Its immutable validation.json still records original gate results; all frozen
analytical inputs/manifests and source/model/code hashes remained unchanged.
All subsequent gates write only block3. This is disclosed rather than claiming
that every ignored historical log was preserved.

Final test results are in STATE.json and block3/validation.json after the mandatory
single full suite. 46 focused cases cover metrics, missingness, causal availability,
all signed/absent result classes, persistence/hysteresis, sensitivity, enabled actions,
independent scalar fixtures, tampering and claim approval. Preserve all existing tests.
Next: PROJECT6 FAST-TRACK BLOCK 4 — Static trajectory visual + LinkedIn video +
five-tab report, only after explicit authorization. Step 12 remains NOT_STARTED.

Final software gates:46focused,424Project6 and1478repository tests passed. Full suite ran once after final code/config freeze; Ruff and strict mypy225files passed. Steps8–11VERIFIED; Step12NOT_STARTED. Result remains NO_VISIBLE_QUEUE_EVENT.
