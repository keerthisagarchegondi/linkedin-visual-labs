# Project 6 — Product contract

## Status and identity

Step 1 implements this contract as immutable declarations in the Project 6
models.py and a no-write configuration loader. STATE.json records gate acceptance.
No source approval, analytical evaluation, runtime or public result is established.

- Display: Project 6 — Traffic Operations Early-Warning System.
- Master-catalog identity: 5 — Traffic Vision and Congestion Warning.
- Package: `p05_traffic_operations_early_warning`.
- Repository: `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
- Branch: `project/p05-traffic-operations-early-warning`.

## Business problem and primary question

Operations may already have camera footage but learn about congestion only after
a queue becomes visually obvious.

Can an ordinary fixed camera warn Operations that congestion is developing before
a sustained queue becomes visually obvious? This is a recorded-analysis portfolio
prototype, not merely a detector demonstration or a claim of live deployment.

## Core decision flow

Camera → vehicle detections → temporary anonymous tracks → zone entries/exits/movement
→ density/dwell/throughput/queue evidence → persistent deterioration → warning
→ conditional action.

The independently defined visible-queue outcome is evaluated alongside the warning
to establish whether warning was early, simultaneous, late, or unsupported.

Recruiter-facing short form: **Camera → Metric → Warning → Action**.

## Stakeholders

| Stakeholder | Product responsibility and evidence needed |
|---|---|
| Operations | Understandable early warning, alert reason, measured response time where available, practical conditional response |
| Engineering | Reliable ingestion, stable timestamps, reproducible detections, track continuity, fault-tolerant bounded processing |
| Analytics | Explicit congestion definition, normal-flow baseline, rolling metrics, independent warning/outcome definitions, auditable lead time |
| Privacy/governance | No face/plate recognition, persistent identity or cross-camera re-identification; aggregate public outputs; truthful source/license documentation |

These are intended stakeholder perspectives, not evidence of a real organization
using or commissioning the system. Do not fabricate airport, pickup-zone, company,
source-location, production, live-monitoring, or operating-authority context.

## Outcome and warning independence

Visible queue uses outcome-state evidence: configured queue-zone occupancy,
eligible low-motion vehicle count, queue count, and persistence. Leading warning
primarily uses density/dwell level and trend, throughput flattening or decline,
inflow–outflow imbalance, simultaneous deterioration, and persistence.

They have separate configuration, evaluation, and evidence. Warning must not
duplicate the complete visible-queue rule or require the queue outcome to activate.
Shared primitive measurements do not justify identical compound definitions.
Independent source annotations validate the outcome without looking to the warning
timestamp for its label. Step 11 cannot replace earlier detection/track/event gates.

## Truthful result classifications

| Result | Meaning |
|---|---|
| POSITIVE_EARLY_WARNING | Both valid onsets exist and signed lead time is positive |
| WARNING_AT_VISIBLE_ONSET | Both valid onsets exist at the same supported analytical time |
| LATE_WARNING | Both valid onsets exist and signed lead time is negative |
| NO_VALID_WARNING | A valid queue episode has no qualifying warning |
| NO_VISIBLE_QUEUE_EVENT | Adequately evaluated footage has no qualifying visible-queue event |
| INSUFFICIENT_SOURCE_EPISODE | Source duration/episode/timing cannot support the intended analysis |
| INSUFFICIENT_DETECTION_QUALITY | Detection acceptance fails or required independent quality evidence is absent |
| INSUFFICIENT_TRACK_QUALITY | Tracking acceptance fails or cannot support unique counts/completed dwell |

Retain event-presence and quality facts separately from a primary classification.
ResultContract locks precedence: insufficient source, detection, then track quality;
adequate evaluation with no queue; queue without warning; then positive/zero/negative
signed onset relationship. This is a declaration, not a runtime classifier. An inadequate episode
must not be described as a validated absence of queue. Missing onsets mean null lead
time, not zero. Invalid events/metrics are gate failures, not invented traffic states.

`lead_time_seconds = visible_queue_timestamp - warning_timestamp`.
Both timestamps are the first original-time evaluations satisfying their complete
persistence rules, never backdated to persistence start. A negative 14-second result
would mean warning occurred 14 seconds after the independently defined queue
outcome; this example is explanatory, not an observed Project 6 result.

## Public-claim classifications

| Classification | Usage |
|---|---|
| MEASURED | An observed/validated measurement; includes actual lead time measured between two derived onsets, with provenance and uncertainty |
| DERIVED | Model outputs, tracks, metrics or rule-derived timestamps; not ground truth merely because generated |
| CONFIGURED_ASSUMPTION | Geometry, thresholds, windows, action availability and other declared assumptions |
| ILLUSTRATIVE_RECOMMENDATION | Conditional proposed operating response without independently established real authority/context |
| PREVIEW_ONLY | Reference imagery, values, timestamps, identities and scenario claims; never release evidence |
| UNSUPPORTED | A claim without adequate evidence; prohibited from public release |

Every important public claim must reference the durable claim register, evidence,
calculation, unit, caveat, reviewer status and publication approval. No detector or
tracking accuracy claim without independent ground truth. Do not fabricate metrics,
timestamps, lead time, operational impact, or model performance. Do not tune solely
for a positive result. Negative, late, zero-lead, inconclusive and source-limited
results remain valid reportable outcomes within their evidence limits.

## Conditional recommendations

Possible actions: `MONITOR`, `INVESTIGATE_SERVICE_DELAY`,
`DISPATCH_SUPPORT_STAFF`, `METER_ENTRY`, `OPEN_OVERFLOW_CAPACITY`,
`ESCALATE_FOR_REVIEW`.

Emit an action only if enabled in the approved source-location configuration. All
public wording remains conditional, for example “Consider opening overflow capacity.”
Do not infer overflow space, staffing authority, road control, or service-delay
causes from imagery. When real levers are unestablished, classify a response as
illustrative or use an enabled escalation-for-review action. If no action is enabled,
emit a supported no-action decision with a reason. Never actually dispatch, meter,
open capacity, or claim measured business benefit from this prototype.

## Privacy and calibration

Version 1 uses vehicle-only analytical classes where applicable, temporary clip-local
anonymous analytical IDs, and aggregate public metrics. IDs are nonpersistent and
must not link across clips. No facial recognition, face identification, license-plate
OCR/recognition, driver identity, persistent vehicle identity, cross-camera
re-identification, external vehicle lookup, enforcement, or citation workflows.
Avoid making recognizable plates/faces a focal point in public artifacts.

Use vehicle counts and normalized image-plane movement. Exact MPH, feet, lane-mile
density, or physical distances require genuine documented calibration; they are
otherwise prohibited. Do not use invented airport signs or AI-generated footage as
observed reality.

## Final story and release boundary

Use the preview pack only for canvas, hierarchy, layout direction, scene order,
captions and tab organization. Its claim that some metric definitions/rendering
choices are guaranteed does not override these contracts. All analytical preview
content is PREVIEW_ONLY and must be replaced by approved source/evidence.

The first 15 seconds communicate the business problem, an execution glimpse, and
the actual supported result. Final artifacts explain the full Camera → Metric →
Warning → Action chain, uncertainty and limitations. Use “Recorded analysis” or
“Portfolio prototype”; “Validated historical clip” requires completed validation.
Do not label the report Live or Production without independent truth.

The five-tab report and public artifact handoff are produced only in the canonical
repository. Separate portfolio integration is not authorized by this contract.

## Implemented Step 1 boundary

ProjectConfig fixes the business question, identity, stakeholder vocabulary and public
shorthand. ResultClassification, WarningState and ClaimClassification retain their
exact approved vocabularies. QueueOutcomeConfig and WarningConfig use separate,
disjoint enum signal namespaces, reject aliases and duplicate canonical signals, and
compare order-independent required-signal sets. A warning cannot consume the queue
outcome boolean. FROZEN requires complete reviewed predicates, cadence, composition,
persistence and unavailable-data policy; warning additionally requires a leading
rationale and explicit transition declarations. This proves schema separation only;
temporal independence still needs later independent source annotation.

ActionConfig permits eligibility only for ENABLED actions with reviewed context and
conditional "Consider ..." wording. Empty actions are a valid supported no-action
configuration. PrivacyConfig fixes the eight prohibited identity/enforcement
capabilities to false and requires vehicle-only, clip-local aggregate analysis.
Step 1 adds no evaluator, state machine, recommendation selector or operating lever.

## Related contracts

- [Source acceptance](SOURCE_CONTRACT.md)
- [Metric semantics](METRIC_CONTRACT.md)
- [Outputs and public acceptance](OUTPUT_CONTRACT.md)
- [Claim governance](CLAIM_REGISTER.md)
- [Numbered implementation and gates](IMPLEMENTATION_PLAN.md)
