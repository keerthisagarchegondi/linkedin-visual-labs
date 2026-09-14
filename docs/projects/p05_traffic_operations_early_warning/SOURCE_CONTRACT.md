# Project 6 — Source contract

## Current scope: Dataset_A recovery 1.D — 2026-09-12

This section supersedes all historical current/latest-source statements below.
The explicit recovery authorization uses one continuous Dataset_A video >=600 s,
with an exactly 600-second static interval and sustained deterioration beyond one
individual stop or normal signal cycle. Prior RoundaboutHD remains rejected.
cam_3.mp4 passes technical and sampled internal academic episode admission; final
Step 3/4 software acceptance is recorded in STATE.json. See AICITY_SOURCE_REVIEW.md
and ignored aicity_source_screening_summary.json/source_manifest.json.
New aicity_source.py implements this scoped mode without rewriting frozen Step 1
planning defaults. Internal academic admission is separate from public reuse:
the 2021 agreement is not an open license. LinkedIn/portfolio footage and annotated
excerpts are unapproved; transformation does not automatically permit publication.
The 120-second lighter baseline does not relax the 300-second rolling window.

## Current RoundaboutHD scope — 2026-09-12

The latest authorization replaces earlier acquisition attempts with four locally
supplied RoundaboutHD cameras. Do not reopen earlier sources. Ten-minute camera
episodes are explicitly admissible in this scope if analytical gates pass; the
older 720-second planning floor is not an admission blocker for this dataset.
Use actual continuous duration, without stitching cameras or forcing 600 seconds.

Internal source screening is authorized even when public reuse rights require
review. Keep internal analytical admission separate from public raw-video and
derivative publication approval. The Bath archive records "Software: MIT License";
the copied package contains no LICENSE/README. Preserve exact documented wording,
provenance limitations and required public privacy/rights review. This authorization
does not establish detector accuracy, an operating lever, or publication clearance.

The new source.py provides original-PTS metadata consistency, empirical label/SCT
parsing, explicit exclusion of invalid/duplicate screening observations, annotated
count/movement summaries and deterministic reviewer-score ranking. It is separate
from unchanged Step 1 planning declarations. Screening is not final operational
metrics, tracking implementation, or source approval. SCT span is not completed
dwell; counts describe annotation coverage. No cross-camera identities are joined.

Four complete decodes each yielded 9000 frames, 600 seconds and uniform 1024-tick
steps at time base 1/15360. The current episode review is SOURCE_REJECTED_EPISODE:
screened variation and brief yielding do not establish the required sustained
normal-to-buildup-to-degraded story. Cam02 ranks first for further consideration,
but there is no approved primary camera or analysis window. Step 4 remains blocked.
See outputs/p05_traffic_operations_early_warning/manifests/source_screening_summary.json
and annotation_format_report.json. This is an evidence-limited admission decision,
not proof that no queue occurs anywhere in the dataset.

## Authorized short-horizon amendment — 2026-09-12

The latest user authorization permits `FAST_TRACK_SHORT_HORIZON_SOURCE` for
Steps 3–4. This narrowly supersedes the duration floor and static-interval rules
below for that explicit mode only. The long-episode preference remains available.
The original Step 1 Python schema/configuration still enforce the older contract;
this amendment is not a claim that short-source ingestion is implemented or verified.

A short source may pass only with at least 45 continuous original seconds, one
stationary or demonstrably stable high-angle camera, no stitching or scene cuts,
adequate vehicle visibility, observable temporal change, an independently definable
degraded/queue outcome, and sufficient pre-outcome evidence to evaluate a leading
warning. Record ordered, source-bounded freer-flow, buildup and sustained degraded
intervals in original seconds. Constant-state footage, invalid timelapse timing,
unreliable camera movement, inadequate geometry, or material unresolved rights
concerns fail admission. Duration alone never establishes an adequate episode.

Use the longest useful continuous source interval for the later static picture;
never fabricate 600 seconds. Public wording must disclose the exact interval and
classify the analysis as a short-horizon recorded prototype, not long-horizon
operational validation. All privacy, evidence, timestamp, outcome independence,
conditional recommendation and negative-result requirements remain unchanged.
The 300-second metric-window contract is not silently shortened: unavailable full
windows stay unavailable; any later change requires an evidence-backed design and
validation before metrics are accepted.

Current acquisition scope is up to three official Pixabay traffic candidates,
starting with SuperTomBob's canonical page 1115. Record canonical page, title,
creator, publication date, exact applicable license/terms, original filename,
acquisition date, byte size and SHA-256. Review actual footage for third-party
rights and suitability. Public availability is not source approval. Preserve the
Figshare and Zenodo rejection records without reopening either source.

No short-horizon source is approved by this documentation amendment. Source and
geometry gates remain blocked until local bytes, timing and episode review pass.

## Current status and approval boundary

No source has been provided or independently approved for Project 6. Current source
status is `SOURCE_REVIEW_REQUIRED`; the Step 1 YAML candidate is null. Step 1 processes
no video and acquires nothing. Source acceptance belongs to Step 3; no real calibration or inference may
proceed until its gate passes. Steps 1–2 may address contracts and scaffold without
source footage. Public accessibility or visual similarity is never permission.

## Implemented Step 1 declaration and approval validation

SourceStatus contains SOURCE_PENDING, SOURCE_APPROVED, SOURCE_REVIEW_REQUIRED and
SOURCE_REJECTED_LICENSE/DURATION/CAMERA/EPISODE/QUALITY. PENDING requires a described
candidate; REVIEW_REQUIRED permits no candidate. SourceConfig rejects mismatched
candidate/container status. ReviewStatus explicitly includes UNKNOWN, REVIEW_REQUIRED,
APPROVED and REJECTED; missing facts never imply approval.

SourceCandidate covers identity/name, owner/acquisition/license, private evidence,
six permitted uses, attribution, raw path/hash, duration/dimensions/codec/FPS/VFR,
timestamp and camera reviews, cuts/motion, episode/quality review, location evidence,
privacy concerns/treatment/review, decision/reasons and evidence references.
Approval requires complete technical and rights metadata, all six uses YES, known
timing, no cuts/motion, accepted camera/episode/quality/privacy/reviewer decisions,
and reviewed hash-bearing rights/source evidence. Specific location wording requires
reviewed evidence; the neutral default is "Unspecified location".

SourceConfig fixes the 720-second planning floor and preferred 1800–2700-second range
as CONFIGURED_ASSUMPTION. Nonpositive/nonfinite duration or FPS and nonpositive or
noninteger dimensions fail immediately. There is no universal resolution minimum or
2700-second rejection maximum. Positive short candidates remain reviewable; approval
below 720 seconds is rejected, and 720–1799 seconds requires episode justification.
No real evidence is authenticated by schema validation alone: Step 3 must inspect
the source, rights, hashes and reviewer evidence. Tests use synthetic metadata only.
The loader checks project-local containment and existing redirections without
creating raw storage, acquiring media or discovering another repository.

## Allowed source categories, in preference order

1. Personally recorded and owned fixed-camera traffic footage collected legally.
2. Public traffic dataset/video with explicit reuse permission suitable for portfolio use.
3. Licensed stock footage permitting analytical transformation and portfolio display.

Ownership claims still require a documented basis and consideration of collection,
privacy, third-party content, display and redistribution restrictions. Permission
must cover the intended annotated excerpts, static picture, report and public video.
Do not assume permission to redistribute the full source just because excerpts are
permitted. Keep private proof out of Git and out of the public handoff.

## Rejected or not automatically acceptable

- Ordinary YouTube uploads without explicit reusable licensing.
- Unauthorized live traffic-camera downloads.
- News or movie footage without separately established suitable rights.
- AI-generated or preview footage presented as observed traffic.
- Unrelated clips stitched together and called one continuous event.
- Misrepresented branding, location or business context.
- Detector-demo footage lacking normal-to-congested transition.
- Footage selected only to reproduce a preview lead time.

Every analytical value or scene assumption in the reference pack is PREVIEW_ONLY,
not source evidence, approved location context or a final configuration target.

Never automatically download or substitute random footage. A source replacement
requires explicit approval, a new hash and invalidation of all dependent evidence.

## Required source metadata

These are schema fields, not filled source facts. Unknown values remain null or
explicitly review-required in future manifests; they never become fabricated values.

| Field | Required evidence/meaning |
|---|---|
| source_id, source_name | Stable identifier and truthful descriptive name |
| owner | Documented rights holder or ownership basis |
| acquisition_method | Local owner delivery or explicitly approved acquisition |
| license_or_ownership_basis | Exact permission record and relevant restrictions |
| permitted_use | Analysis, derivative overlays, excerpts, public video/picture/report rights |
| attribution_requirement | Exact required credit and placement |
| raw_file_path | Repository-contained ignored path, not a public absolute path |
| checksum_sha256 | Actual source-byte checksum |
| duration_seconds | Measured original duration |
| width, height | Positive integer measured resolution |
| nominal_frame_rate, average_frame_rate, variable_frame_rate | Positive finite supplied rates and YES/NO/UNKNOWN VFR status; not a substitute for PTS |
| codec | Actual codec/stream details |
| timestamp_characteristics | PTS, time base, origin, gaps, duplicates, discontinuities, uncertainty |
| camera_continuity | Stationarity, pan/zoom and viewpoint findings |
| scene_cuts, camera_motion | YES/NO/UNKNOWN findings; both NO before approval |
| privacy_concerns | Faces/plates, sensitive context and public-display treatment |
| location_wording, location_evidence | Reviewed wording or neutral unspecified location |
| status, reviewer_decision, reasons, evidence | Acceptance decision, reasons and reviewer evidence |
| Later source manifest: analysis_windows | Approved baseline/evaluation; the Step 1 picture declaration is outputs.static.source_interval |
| Later source manifest: source_config_hash | Approved location/geometry/action configuration linkage when available |

## Episode and camera requirements

Prefer 30–45 continuous minutes: about 10 minutes normal baseline, 10–20 minutes
buildup, and 5–10 minutes sustained queue/degraded flow. Approximately 12–15 minutes
is acceptable only when normal flow, measurable buildup and sustained visible queue
or degraded flow are all present and a defensible baseline/window design remains
possible. A short clip cannot silently change the five-minute metric contract.

Require a stationary camera, no meaningful pan/zoom, no major cuts, vehicles visible
for several seconds, a meaningful entry or exit boundary, stable or recoverable
frame timing, adequate resolution, and an analyzable operational area. No airport,
pickup zone, company, or available operating lever is inferred from resemblance.

## Original timestamps and intervals

All analytics use original source timestamps. Retain source hash, stream, frame
ordinal, PTS/time base and elapsed source time. Wall-clock time may be displayed
only if the source independently establishes it. Recoverable timing must be checked;
do not substitute frame index divided by nominal FPS for variable/unreliable timing.

Sampling must not rescale dwell, throughput, queue/warning persistence or onsets.
It can change estimation uncertainty and requires revalidation if changed. Final
accelerated playback is presentation only. The edit map must retain source-time
references without rewriting analytical timestamps.

Baseline selection must not use final warning success as its criterion. Reserve
independent evaluation samples and record any one-episode limitations. The static
picture uses one real continuous approved 600-second interval, never a montage.

## Status and rejection reasons

| Status | Use |
|---|---|
| SOURCE_PENDING | Described candidate awaits review |
| SOURCE_APPROVED | Rights, episode, timing, camera and quality evidence accepted |
| SOURCE_REJECTED_LICENSE | Permission absent, unsuitable or unverifiable |
| SOURCE_REJECTED_DURATION | Duration cannot support required intervals/windows |
| SOURCE_REJECTED_CAMERA | Camera movement/cuts invalidate fixed-scene analysis |
| SOURCE_REJECTED_EPISODE | Required baseline/buildup/degraded-flow evidence inadequate |
| SOURCE_REJECTED_QUALITY | Visibility/resolution/timing cannot support analysis |
| SOURCE_REVIEW_REQUIRED | Candidate missing or review incomplete |

Record multiple reasons where applicable. Insufficient episode evidence is not proof
of a validated absence of queue. A source failure blocks downstream real processing;
synthetic fixtures may test code only and never replace public source evidence.

## Storage and future acceptance

Raw source, actual local configuration, real annotations and private permissions:
`data/raw/p05_traffic_operations_early_warning/` beneath
`D:\linkedin-visual-labs-git\linkedin-visual-labs`. Generated source/timing evidence
goes to ignored `outputs/p05_traffic_operations_early_warning/`. Public manifests
contain sanitized attribution, status and evidence hashes, not private documents.

Step 3 tests cover missing rights, corrupt input, hash mismatch, invalid intervals,
scene/timing discontinuities, variable frame rate and interrupted ingestion. Source
approval must be reviewed before calibration and any real inference. Approval does
not establish detector/tracking accuracy or permission for operational control.
