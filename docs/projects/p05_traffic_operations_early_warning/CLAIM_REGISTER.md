## Current presentation amendment - Sub-step 4.C.C

PRESENTATION_V3_CONTRACT.md and BLOCK4CC_REVIEW.md supersede older presentation
status below. Steps12-14 are VERIFIED_REVISED_SCOPE_V3. Current outputs use6-15x
source-time ramps, causal rolling contours, fading trails and violet/magenta fields
with near-white detections, emerald entry, gold exit and coral warning accents.
The old light-blue/orange combination is DEPRECATED_VISUAL_STYLE. All analytics
and canonical24:00 KPIs remain unchanged. No physical queue absence or measured
false-escalation benefit is claimed. Source imagery remains internal-only pending
public permission. Step15 and Git/publication actions are not authorized.

## Current presentation amendment - Sub-step 4.C.B

PRESENTATION_V2_CONTRACT.md and BLOCK4CB_REVIEW.md supersede older presentation
status/wording below. Steps12-14 now use original-preview sampled colors and real
source footage in all internal production derivatives. Canonical24:00 numeric
scope is(1380,1440]:3.70 mean observed occupancy,8 entries/3 exits/net+5,
3 eligible exits/60s,0.0113054 image diagonals/s; WARNING at24:00. Independent
queue rule not satisfied; no physical queue absence or false-alarm reduction
claim. Existing analytical claims/evidence remain immutable. Public source-image
permission is pending, Step15 not started, and no Git/publication action is authorized.

# Project 6 — Claim register and publication governance

## Current presentation interpretation — Sub-step 4.B

Recruiter-facing name: Traffic Flow Deterioration Early-Warning System.
REVISED_PRESENTATION_SCOPE.md contains the presentation claim-to-field mapping,
classifications, frozen release/index hashes and mandatory caveats. Headline:
**Busy traffic ≠ congestion.** P6-B3-01 supports the configured deterioration
warning at24:00; P6-B3-02 supports queue not established and unavailable lead time;
P6-B3-05 supports conditional review with MONITOR as the configured alternative.
Density/imbalance increased while comparison throughput/movement remained active.
This does not prove healthy flow, physical queue absence or classifier accuracy.

Preserve all six original machine-readable claims and their analytical approval
scope. Future presentation derivatives must bind exact wording, field selectors,
upstream hashes and classifications separately. Revised internal story approval
does not automatically approve final public artifacts. Do not hide the297s unmatched
warning or promote the in-sample zero-warning baseline to false-positive accuracy.
Do not headline queue/congestion prediction or positive lead time. Supported rolling
dwell49.15s has108 overlapping windows, not108 independent vehicle journeys.

Actual source footage is allowed for internal preview/design review under4.B;
new presentation manifests must carry `PUBLICATION_STATUS: PENDING_SOURCE_PERMISSION`.
Existing public source-imagery/final-release approval remains false. The complete
supported/prohibited claim list and source treatment are in the revised contract.

## Current Block 3 aggregate analytical claims

These six records supersede historical unreviewed categories for their exact scoped
wording only. Content approval is for aggregate derived charts/text; final artifact
release and all raw/excerpted/transformed source imagery remain unapproved. No
accuracy or physical queue-absence claim is approved. Machine-readable records in
data/claim_register.json retain exact evidence SHA-256, approval scope and step11.

| claim_id | claim_text | classification | evidence_path | calculation | unit | caveat | approved_for_publication | reviewer_status |
|---|---|---|---|---|---|---|---|---|
| P6-B3-01 | The configured warning first qualified at 1440.0 source seconds. | DERIVED | outputs/p05_traffic_operations_early_warning/data/warning_summary.json | First full warning persistence completion after baseline | source seconds | Configured, model-derived analysis; no independent accuracy or physical queue-absence claim. Aggregate content approval does not authorize source imagery. | True | APPROVED |
| P6-B3-02 | Result: NO_VISIBLE_QUEUE_EVENT; qualifying queue onset and lead time are unavailable. | DERIVED | outputs/p05_traffic_operations_early_warning/data/warning_summary.json | Independent queue outcome and signed onset arithmetic | classification; seconds or null | Configured, model-derived analysis; no independent accuracy or physical queue-absence claim. Aggregate content approval does not authorize source imagery. | True | APPROVED |
| P6-B3-03 | Baseline warning exposure: 0 of 60 evaluable seconds. | DERIVED | outputs/p05_traffic_operations_early_warning/data/warning_summary.json | In-sample exposure with frozen rule | seconds | Configured, model-derived analysis; no independent accuracy or physical queue-absence claim. Aggregate content approval does not authorize source imagery. | True | APPROVED |
| P6-B3-04 | Completed dwell uses 65 eligible journeys; incomplete journeys are excluded. | DERIVED | outputs/p05_traffic_operations_early_warning/data/metric_quality_summary.json | Reconciled complete gap-free crossing pairs | journeys | Configured, model-derived analysis; no independent accuracy or physical queue-absence claim. Aggregate content approval does not authorize source imagery. | True | APPROVED |
| P6-B3-05 | Consider escalating the recorded deterioration for review. | ILLUSTRATIVE_RECOMMENDATION | outputs/p05_traffic_operations_early_warning/data/recommendation.json | Enabled prototype review action linked to actual warning drivers | conditional action | Configured, model-derived analysis; no independent accuracy or physical queue-absence claim. Aggregate content approval does not authorize source imagery. | True | APPROVED |
| P6-B3-06 | Operational comparisons use an explicit 60-second fast-track window; the formal window remains 300 seconds. | CONFIGURED_ASSUMPTION | outputs/p05_traffic_operations_early_warning/data/baseline_summary.json | Baseline interval duration and declared window policy | seconds | Configured, model-derived analysis; no independent accuracy or physical queue-absence claim. Aggregate content approval does not authorize source imagery. | True | APPROVED |

## Historical category register and prior reviews

Earlier status statements below describe earlier stages, not the current Block 3 acceptance.


## Current state

This is a category register established during governance setup. No final analytical
claim, source approval, detector/tracking accuracy or operating impact is established.
Every seeded row is unapproved for publication. Step 1 implements ClaimRecord
declarations and validation; acceptance evidence is recorded in STATE.json.
All evidence paths below are planned destinations, not assertions that files exist.

## Record schema

| Field | Meaning |
|---|---|
| claim_id | Stable unique category/claim identifier |
| claim_text | Exact proposed public wording; final values inserted only from approved evidence |
| classification | MEASURED, DERIVED, CONFIGURED_ASSUMPTION, ILLUSTRATIVE_RECOMMENDATION, PREVIEW_ONLY or UNSUPPORTED |
| evidence_path | Repository-relative artifact and row/field selector, or absent until generated |
| calculation | Reproducible formula/method with named inputs; no hidden arithmetic |
| unit | Supported unit or not applicable |
| caveat | Source, model, sampling, calibration and inference limitations |
| approved_for_publication | Boolean false until explicit review of exact evidence/artifacts |
| reviewer_status | NOT_REVIEWED, REVIEW_REQUIRED, APPROVED or REJECTED |
| source_manifest_reference | Source identity/hash reference where relevant |
| evidence_id | Stable key into future data/evidence_index.json |
| last_validated_step | Null until an actual gate validates the claim |

Classification is not approval. A MEASURED label alone cannot establish accuracy or
truth. Material changes to source/config/model/timestamps/artifacts invalidate prior
approval and require new hashes, validation and review.

The typed ClaimRecord uses an immutable tuple of EvidenceReference records (ID,
path, optional selector, hash, review), calculation, unit/calibration, caveat, reviewer
status, source-manifest reference and last validated step. Legacy NOT_REVIEWED table
rows remain unapproved; normalize that planning label to REVIEW_REQUIRED before
constructing a typed record. PREVIEW_ONLY and UNSUPPORTED cannot be approved.
Other approval requires reviewed hash-bearing evidence, calculation, caveat, reviewer
APPROVED and validated step 1–15. Approved evidence must reside under public output
categories, and approved_evidence_hashes must match its exact ordered hashes.
Changing hashes invalidates the declaration. Future artifact existence/hash checks
remain Step 11/15 responsibilities; a planned path alone never proves evidence.

## Seeded claim categories

Paths in this table are beneath `outputs/p05_traffic_operations_early_warning/`.
For every row source_manifest_reference is absent pending source approval and
last_validated_step is null. No numeric final value is seeded.

| claim_id | claim_text/category | classification | evidence_path (planned) / evidence_id | calculation | unit | caveat | approved_for_publication | reviewer_status |
|---|---|---|---|---|---|---|---|---|
| P6-C01 | Preview lead-time example | PREVIEW_ONLY | Not analytical evidence / preview-lead | None; reference only | Preview seconds | Never a threshold target or release claim | false | REJECTED |
| P6-C02 | Detector vehicle output | DERIVED | data/detections/ / vehicle-detections | Approved model inference and postprocessing | Boxes/classes/confidence | Not independently ground-truthed merely because generated; a labeled subset can support a separate measured accuracy claim | false | NOT_REVIEWED |
| P6-C03 | Anonymous tracks | DERIVED | data/tracks/ / anonymous-tracks | Accepted ByteTrack-compatible association | Clip-local tracks | Fragmentation/occlusion and identity uncertainty; no persistent identity | false | NOT_REVIEWED |
| P6-C04 | Zone geometry and rolling window | CONFIGURED_ASSUMPTION | manifests/calibration.json, manifests/metrics.json / measurement-config | Approved geometry/window configuration | Normalized coordinates; seconds | Configuration is not observed capacity or physical calibration | false | NOT_REVIEWED |
| P6-C05 | Occupancy, density, dwell and throughput | DERIVED | data/operational_metrics.parquet / operational-metrics | METRIC_CONTRACT eligible tracks/events/window definitions | Vehicles; seconds; exits/window | Coverage, completed samples, censoring and baseline limitations required | false | NOT_REVIEWED |
| P6-C06 | Warning timestamp | DERIVED | data/warning_timeline.parquet / warning-onset | First original-time evaluation satisfying complete WARNING persistence | Source seconds | No backdating; missing onset remains null | false | NOT_REVIEWED |
| P6-C07 | Visible-queue timestamp | DERIVED | data/queue_outcome.parquet / queue-onset | First evaluation satisfying independent queue persistence | Source seconds | Algorithmic outcome distinct from independently annotated visible queue | false | NOT_REVIEWED |
| P6-C08 | Actual lead time | MEASURED | data/release_data.json / signed-lead | visible_queue_timestamp minus warning_timestamp | Seconds | Measured from two derived timestamps, not independent ground truth; signed/null and temporal uncertainty preserved | false | NOT_REVIEWED |
| P6-C09 | Conditional operating recommendation | ILLUSTRATIVE_RECOMMENDATION | data/recommendation.json / conditional-action | Evidence-linked rule restricted to enabled actions | Action | Remains illustrative unless real operating authority/context independently established; wording always conditional | false | NOT_REVIEWED |
| P6-C10 | Detection/tracking validation performance | MEASURED | data/validation_results.json / independent-quality | Frozen metric against independent annotations with sample size | Explicit validation unit | Only after independent ground truth; no generalization beyond evaluation scope | false | NOT_REVIEWED |
| P6-C11 | False-warning and sensitivity evidence | DERIVED | data/false_warning_evidence.parquet, data/sensitivity_results.parquet / robustness | Warning episodes/exposure and predeclared parameter variants | Counts; seconds; rates with denominator | Overlapping windows not independent trials; do not select best variant | false | NOT_REVIEWED |
| P6-C12 | Live production or real-world impact | UNSUPPORTED | No evidence / unsupported-impact | None | Not applicable | Prohibited without independently established truth; prototype does not control operations | false | REJECTED |

The lead-time classification above follows the approved product vocabulary: MEASURED
from two DERIVED timestamps. It must never be described as independent detector or
human-ground-truth accuracy. Detection output and anonymous tracks remain DERIVED;
ground-truth comparison yields a separate validated performance claim.

## Review workflow

1. Generate accepted upstream artifacts; link exact source/config/model/code hashes.
2. Materialize each proposed final claim with an evidence ID, row/field selectors,
   calculation, unit and caveat. Preserve negative/zero/null/insufficient outcomes.
3. Validate joins and arithmetic; independent quality annotation precedes accuracy claims.
4. Freeze analytical evidence in Step 11. Reviewer approves or rejects exact claims.
5. Render from approved evidence; compare visible numbers/text to the register.
6. Bind publication approval to final artifact hashes in Step 15. Changed bytes or
   stale inputs trigger re-review, not reuse of a prior approval flag.

No PREVIEW_ONLY or UNSUPPORTED row can be promoted merely by copying a number into
configuration. Real results require new supported evidence. Do not fabricate source
location, signs, timestamps, model quality, business context, impact or live status.
Keep private source-license material and identifiable details out of public evidence.

## Recovery 1.D configuration and source evidence

cam_3 source/timing observations are internal source-review evidence, not approved
public claims. P6-C04 now has actual CONFIGURED_ASSUMPTION evidence in ignored
calibration.json/calibration_preview.png; publication remains false. Internal
source admission does not promote any accuracy, metric, queue-onset, warning, lead
time or impact category. Sampled retained-queue interval [1440,1650) is an admission
candidate, not the final independently configured outcome. Public raw or annotated
footage is not permitted by default under the supplied academic agreement.


## FAST-TRACK BLOCK 2 evidence update

Block 2 claim classification: INTERNAL_MEASURED_DIAGNOSTIC, NOT_PUBLIC_APPROVED. Detection/track/event counts and local timings trace to the hash-linked manifests; sample visual observations trace to block2_quality_review.json. Accuracy, source location, operating impact, positive lead time and publication clearance remain UNSUPPORTED/NOT_CLAIMED. 65 complete journeys is an eligibility count, not an accuracy estimate.


## Block4 derived visual claim bindings

The six frozen Block3 claims remain unchanged. report/claims.json adds scoped DERIVED
selector bindings for result, metric_changes, eligibility and unmatched_warning in
the approved release_data.json. Rule/sensitivity/geometry/trajectory/chart references
are hash checked through report/evidence_index.json. The explicit user instruction
authorizes derived-only rendering; it does not approve raw/excerpted/transformed
source imagery or final artifact publication. Full-episode counts are labelled as
such. Null lead time reads Not reportable. No accuracy, positive early-warning,
physical queue-absence, operational control or causal impact claim is approved.
Step15 must review final artifact publication using the exact output hashes.
