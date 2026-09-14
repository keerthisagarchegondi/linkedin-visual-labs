# Project 6 — Revised presentation scope, Sub-step 4.B

## Authority and identity

Recruiter-facing title: **Traffic Flow Deterioration Early-Warning System**.
Approved scope revision dated 2026-09-13. Internal package remains
`p05_traffic_operations_early_warning`; branch and canonical repository are unchanged.
This amendment supersedes earlier presentation/business-story framing, including
the original mission in PRODUCT_CONTRACT.md, and permits actual source footage for
internal previews. Analytical contracts, source/model, geometry, thresholds, original
timestamps, frozen evidence and public permission restrictions remain unchanged.

## Business question and narrative

“Can fixed-camera traffic footage detect sustained deterioration in traffic-flow
conditions and distinguish a busy road from a confirmed congestion/queue event?”

**Busy traffic ≠ congestion.**

The system detects operational deterioration without automatically turning every
dense traffic episode into a congestion alert. This episode illustrates separation
of two configured rules; it does not establish general classification accuracy.

Camera → Detect → Track → Measure flow → Detect operational pressure → Issue
deterioration warning → Independently validate congestion/queue → Recommend
review/monitoring.

Show the busier interval using actual footage in internal design review. Vehicle
accumulation and inflow/outflow imbalance increase; WATCH is followed by WARNING.
Throughput and relative movement remain active and their comparison medians rise.
Separately, the independent queue rule does not qualify. Interpret this as
configured operational pressure, not confirmed congestion. Do not claim those two
median increases alone caused the queue rule to fail or independently prove healthy flow.

Primary: **TRAFFIC DETERIORATION WARNING — Triggered at 24:00**.
Secondary: **CONFIRMED CONGESTION / QUEUE — Not established**.
Action: **Consider escalating the recorded deterioration for review.**
Alternative: MONITOR. Both are conditional illustrative prototype responses.
Retain `NO_VISIBLE_QUEUE_EVENT`, null queue onset and null lead time in technical
evidence. An unmatched warning is not demonstrated early warning of congestion.

## KPI hierarchy

1. Traffic state: NORMAL / WATCH / WARNING. Retain CRITICAL in the analytical model;
   do not imply it occurred here.
2. Density: time-labelled current evidence when available, baseline and change.
   Comparison medians of rolling mean counts are not instantaneous occupancy.
3. Flow balance: entries versus exits and rolling accumulation pressure. Full-clip
   entry-minus-exit counts are not a census of net physical vehicles present.
4. Throughput: eligible exits per60s operational window; fractional comparison
   medians are valid. The formal300s contract remains unchanged.
5. Relative movement: image diagonals/second, not MPH or physical speed.
6. Completed-journey dwell: sample-supported rolling medians; exclude incomplete
   journeys. No baseline dwell increase is available.
7. Queue validation: NOT CONFIRMED by the configured independent rule; no claim
   of physical queue absence or independent human ground truth.
8. Action: REVIEW / MONITOR, restricted to enabled actions.

## Evidence binding and supported claims

All selectors below refer to `outputs/p05_traffic_operations_early_warning/data/`.
Frozen release_data.json SHA-256:
`c80ff9c1da0bbe2c1ca603731635419165a677b1b214635a197c0d68e0947751`.
Frozen evidence_index.json SHA-256:
`1d9a579b8beceebc36d04a5cf25877a5b6b59d4e0ecf026725a1a20974e21b56`.
Reverify the index and upstream hashes before rendering.

| Claim | Classification | release_data.json selector / existing claim | Qualification |
|---|---|---|---|
| Warning1440s /24:00 | DERIVED | result.warning_timestamp; P6-B3-01 | Original-time persistence completion |
| Queue not established; lead unavailable | DERIVED | result.result_classification, visible_queue_timestamp, lead_time_seconds; P6-B3-02 | Rule outcome, not physical queue absence |
| Density0.7583→4.45,+486.8% | DERIVED | metric_changes.density_window_mean | Medians of rolling mean vehicle counts |
| Throughput2→3.5 exits/60s | DERIVED | metric_changes.throughput | Comparison medians, not every window |
| Movement0.0076955→0.0089943,+16.9% | DERIVED | metric_changes.movement_index | Image diagonals/second |
| Rolling imbalance median-1→2 | DERIVED | metric_changes.inflow_outflow_imbalance | No percentage interpretation |
| Supported rolling dwell median49.15s | DERIVED | metric_changes.median_completed_dwell_seconds | 108 overlapping windows, not108 independent journeys; baseline unavailable |
| 131 entries,81 exits;572 candidates,178 confirmed,65 completed journeys | DERIVED | eligibility; P6-B3-04 | Full1800s episode; fragmentation caveat |
| NORMAL1380,WATCH1383,WARNING1440,NORMAL1737,WATCH1754,NORMAL1758 | DERIVED | result.transitions | Original seconds; evaluation1380–1800s |
| Primary density level; supporting imbalance and density trend | DERIVED | result.primary_driver, supporting_drivers | No causal diagnosis |
| Zero baseline warning episodes;297s unmatched warning | DERIVED | result.baseline_false_warning; unmatched_warning | Only60 evaluable in-sample baseline seconds; no false-alarm accuracy claim |
| Consider escalating the recorded deterioration for review; MONITOR alternative | ILLUSTRATIVE_RECOMMENDATION | recommendation; P6-B3-05 | No actual intervention or validated impact |

Baseline interval [1260,1380); complete-window comparison timestamps [1320,1380).
Later screened comparison [1440,1650). Percentages are frozen relative_change×100,
rounded for display. Increasing throughput/movement must remain visible alongside
increasing density. The supplied low-motion start/end counts are not fields in the
frozen release or indexed summary claims: omit them until an exact validated
indexed binding is established. Do not invent evidence selectors.

This contract approves the revised internal story, not blanket public release.
Future presentation-derivative claims require exact wording, selectors, hashes,
classification and review status. Preserve the original six machine-readable claims.

## Prohibited claims

Do not headline “traffic jam predicted”, “congestion predicted”, “queue predicted”,
“early congestion detection”, “lead-time prediction” or “queue forecast” except
to explain an unsatisfied condition. No positive lead time, physical queue absence,
all-metrics deterioration, independent detector/tracker accuracy, general false-alarm
performance, causal diagnosis, physical speed/distance, live/production deployment,
real intervention or business impact. No invented airport/location, preview numbers,
AI imagery as source, persistent identity, recognition or identifiable face/plate focus.

## Video and static story

Preserve Project6 reference layout, muted comprehension,1080×1350,30fps,
H.264/yuv420p,44.0–46.5s,target45s. Preview analytical values remain PREVIEW_ONLY.

| Keyframe | Revised message |
|---|---|
| 00:00 | Busy traffic ≠ congestion; problem with actual internal-preview footage |
| 00:05 | Detect and anonymously track; real aligned execution glimpse |
| 00:10 | Warning24:00; congestion/queue not established; lead not reportable |
| 00:15 | Define deterioration separately from independent queue validation |
| 00:20 | Occlusion, fragmentation and journey eligibility limitations |
| 00:25 | Density/imbalance rise while throughput/movement remain active |
| 00:30 | Actual WATCH→WARNING drivers and persistence completion |
| 00:35 | Warning versus nonqualifying queue timeline, not a lead-time countdown |
| 00:40 | Conditional review / monitor recommendation |
| End near00:45 | Camera → Metric → Warning → Action; recorded prototype and permission status |

Bind excerpts/boxes to original timestamps. Acceleration is presentation only.
Static picture retains “Ten minutes of traffic in one frame”, interval[1200,1800),
1080×1350PNG, real trajectories and qualified metric annotations.

## Five-tab report story

Dashboard answers what happened, why the warning fired and what Operations should
consider, using the KPI order and separate warning/queue-validation cards.
Video explains the1800s-to-45s edit map without changing analytical time.
Method explains Detect → Track → Measure → Aggregate → Warn → Act, independence,
privacy, sampling and relative-only calibration. Results retains raw classification,
null queue/lead, actual deltas,297s unmatched warning, in-sample baseline diagnostic,
sensitivity and computational-validation limitations. About covers the revised
problem, stakeholders, role, technology, source/license, privacy, limitations and roadmap.
Use Recorded analysis or Portfolio prototype; never Live/Production.

## Source treatment and publication permission

Retain AI City Challenge2021 Track1 Dataset_A/cam_3.mp4:1800s,1280×720,
source10fps,analysis3fps; existing YOLOX-Nano model and analytical configuration.
The user permits actual footage for **INTERNAL PREVIEW / DESIGN REVIEW** now.
Pending permission does not block internal generation. Every new presentation
manifest must carry `PUBLICATION_STATUS: PENDING_SOURCE_PERMISSION`, purpose
`INTERNAL_PREVIEW_DESIGN_REVIEW`, actual source-pixel usage, source and frozen-evidence
hashes, and `final_artifact_release_approved: false`. Label assets as internal previews.
Do not relabel historical manifests as if new artifacts were generated.
Intent to obtain permission is not permission received. Frozen publication flags
stay unchanged. Public source-pixel distribution requires documented permission
and separate final artifact review. Keep outputs/private permissions ignored.
No separate portfolio repository access, Git mutation or publication is authorized.

## Acceptance and next action

Sub-step4.B updates only the seven named existing documents and this new contract.
No media regeneration or analytical execution occurs here. Steps1–11 remain VERIFIED;
Steps12–14 retain technical gates, with revised-story acceptance pending; Step15
remains NOT_STARTED. Next, after explicit authorization, regenerate presentation-only
derivatives from frozen evidence, enforce internal-preview manifests, test
story/result/units/time/rights consistency, review the static image, ten decoded
video keyframes and five desktop/mobile tabs, and update acceptance evidence.
Do not rerun detection/tracking or alter source, model, geometry or thresholds.
