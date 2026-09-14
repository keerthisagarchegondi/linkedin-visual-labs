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

# Project 6 — Output contract

## Current presentation scope — Sub-step 4.B, 2026-09-13

Use **Traffic Flow Deterioration Early-Warning System** and the complete story
contract in REVISED_PRESENTATION_SCOPE.md. This section supersedes older output
status/presentation wording below only. Existing Steps 12–14 artifacts are technically
verified but await revised-story regeneration; no revised media is generated in4.B.

Primary result: TRAFFIC DETERIORATION WARNING — Triggered at24:00.
Secondary: CONFIRMED CONGESTION / QUEUE — Not established. Retain technical
NO_VISIBLE_QUEUE_EVENT, null queue onset and null lead; do not imply physical queue
absence. Prioritize state, density, flow balance, throughput, relative movement,
sample-supported dwell, queue validation, then review/monitor. Label comparison
medians and intervals accurately; do not present them as instantaneous observations.

Preserve PNG1080×1350, continuous static interval[1200,1800), video1080×1350,
30fps,H.264/yuv420p,44.0–46.5s and ten keyframes; retain five ordered report tabs.
Source-to-edit mapping uses original analytical timestamps regardless of acceleration.
Frozen release_data.json and evidence_index.json remain immutable. Revised derivative
claims/manifests must link exact selectors and hashes; no analytical reruns.

Actual AI City source footage is permitted for INTERNAL PREVIEW / DESIGN REVIEW.
New presentation manifests must set `PUBLICATION_STATUS: PENDING_SOURCE_PERMISSION`,
purpose `INTERNAL_PREVIEW_DESIGN_REVIEW`, actual source-pixel usage and
`final_artifact_release_approved: false`, with source/evidence hashes. Assets must
visibly identify internal-preview status. Public permission pending does not block
internal rendering; it does block public source-pixel distribution. Do not rewrite
historical manifests or frozen publication flags. Keep media/private permissions
ignored and require separate artifact approval before any public handoff.

## Historical output decisions

## Current scope: Dataset_A recovery 1.D — 2026-09-12

This section supersedes historical source/output status statements below.
Selected cam_3 static interval [1200,1800) is exactly 600 original seconds. The
future title is "Ten minutes of traffic in one frame"; no approximate interval is
accepted in this Dataset_A mode. No static picture or final video is produced now.
Current internal artifacts: aicity_dataset_inventory.json,
aicity_source_screening_summary.json, aicity_episode_review.json, source_manifest.json,
calibration.json, images/aicity_source_screening/ and calibration_preview.png.
The RoundaboutHD source_manifest was preserved as roundabouthd_source_manifest.json.
All remain ignored and unapproved for public distribution. Calibration preview is
source-linked RELATIVE_ONLY configuration, not physical measurement or final metrics.
Only an independently permitted public artifact set may reach a future portfolio
handoff; annotated source footage does not automatically bypass academic restrictions.

## Current RoundaboutHD screening outputs — 2026-09-12

The user-authorized ten-minute-camera scope supersedes earlier short-stock-footage
acquisition wording. Use the selected camera's actual full continuous interval;
never concatenate views. An approximately ten-minute interval can carry the title
"Ten minutes of traffic in one frame", with exact seconds disclosed. Current files
each contain exactly 600 seconds, but no static interval or title is approved for
release because the source episode gate has not passed.

Generated internal diagnostics are four camera contact sheets and targeted review
images under images/source_screening/, plus source_screening_summary.json,
annotation_format_report.json, source_provenance.json and source_manifest.json in
manifests/. source_manifest.json is a blocked-screening record, not source approval.
It explicitly has no primary camera. No calibration_preview.png is generated before
source admission. Screening outputs and source-visible signs/plates are not approved
public artifacts. Unchanged Step 1 output declarations remain historical planning
defaults; their existence does not override this source gate.

## Authorized short-horizon amendment — 2026-09-12

For an approved `FAST_TRACK_SHORT_HORIZON_SOURCE` shorter than 600 seconds, the
static picture must use the longest useful continuous approved interval supported
by the source. Its title must accurately describe that interval, with exact
duration disclosed alongside it. Do not retain "Ten minutes of traffic in one
frame" or imply a 600-second interval for a shorter source. For example, a genuine
180-second interval may be titled "Three minutes of traffic in one frame"; a
non-round interval may use its precise seconds. Examples are not source results.

This exception supersedes only the fixed static duration/title requirements below
for that explicit source mode. PNG dimensions remain 1080×1350. Source-time
provenance, continuity, derived-data reconciliation and publication gates remain
mandatory. Video/dashboard/report wording must disclose the exact source duration
and "short-horizon recorded prototype" limitation; previews supply layout only.
Lead time remains signed original seconds or unavailable. No long-horizon
validation, fake ten-minute interval or fabricated positive warning is permitted.

The Step 1 StaticOutput/SourceInterval validators retain their original version
until the scoped implementation and focused tests pass. This amendment does not
claim a source manifest, static interval, final title or calibration preview exists.

## Status and paths

All outputs below are planned; Step 1 validates their declarations but produces no
analytical output. Root: `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
Output root: `outputs/p05_traffic_operations_early_warning/` beneath that repository.
Use `data/`, `images/`, `videos/`, `report/` and `manifests/`. The existing shared
helper uses singular `video`; a future project-local adapter must implement these
required paths without changing earlier projects. All runtime output stays ignored.

## Implemented Step 1 output validation

StaticOutput fixes PNG 1080×1350 and "Ten minutes of traffic in one frame".
SourceInterval must span exactly 600 continuous original seconds, fit an approved
source, and remains null in the checked-in config. VideoOutput fixes 1080×1350, 4:5,
30 fps, H.264 and yuv420p. Duration is 44.0–46.5 seconds inclusive, with integer
frame_count 1320–1395 and duration × 30 equal to frame_count; target is 45/1350.
Keyframes are exactly 0,5,10,15,20,25,30,35,40 seconds plus LAST_FRAME, whose time
is (frame_count - 1) / 30. A frame at exactly 45.0 seconds is not required.
Audio remains optional and muted comprehension mandatory.

OutputConfig enforces ordered Dashboard, Video, Method, Results, About tabs and
data/images/videos/report/manifests categories. Config validation accepts only
project-local raw/processed/output references, rejects traversal, foreign absolute,
drive/UNC/old-clone/sibling paths and detectable symlink/reparse components, and
creates no directory. Config/model loading requires no CV or FFmpeg runtime.
No pixels, metric values, onsets, lead time or recommendation enter the planning YAML.
Rendering, file probing and public handoff validation remain later steps.

## Structured data and reconciliation

| Relative data path | Contract |
|---|---|
| data/frame_timestamps.parquet | Source/stream/frame ordinal/PTS/time base/elapsed time and validity |
| data/detections/ | Partitioned vehicle boxes, class/confidence, original frame time, detector/config IDs |
| data/tracks/ | Partitioned clip-local IDs, detection links, observed/predicted status, time/lifecycle |
| data/trajectories.parquet | Eligible source-linked position sequences and movement provenance |
| data/zone_events.parquet | Directed crossing/zone/session events, eligibility and censoring reasons |
| data/operational_metrics.parquet | Original-time windows, units, sample sizes, coverage, deltas, availability |
| data/normal_baseline.json | Approved normal interval, method, summary and exclusions |
| data/queue_outcome.parquet | Independent rule/persistence/onset evidence |
| data/warning_timeline.parquet | State/driver/persistence evidence and first complete WARNING onset |
| data/recommendation.json | Enabled conditional action or no-action, reasons and claim/evidence links |
| data/validation_results.json | Stage and independent final findings with sample sizes/uncertainty |
| data/false_warning_evidence.parquet | Warning episodes, durations and evaluable non-queue exposure |
| data/sensitivity_results.parquet | Predeclared variants, including unfavorable results |
| data/claim_register.json | Machine-readable classified claim/approval ledger |
| data/release_data.json | Supported result, onsets or null, signed lead, caveats and approved summary |
| data/evidence_index.json | Stable evidence IDs mapping artifacts/rows/calculations to claims |

Crossing events are typed records in zone_events, not an independently maintained
counter. All tables require schema versions, keys, units and upstream identities.
No hidden manual arithmetic. Reconcile source → detections → tracks → events →
metrics → queue outcome and warning → recommendation → release evidence → visuals.
Outcome and warning are independent branches using accepted metrics, not identical
rules or a causal dependency of warning on completed queue activation.

Use actual source time and null for unavailable values. Missing/censored data never
become zero/completed dwell. No source/weight/private-license blobs belong in the
public data package. Raw IDs may exist in ignored analytical data, but public metrics
are aggregate and any illustrative ID display remains temporary and clip-local.

## Manifests and acceptance

Expected files under manifests: `gates.json`, `source.json`, `calibration.json`,
`detection.json`, `tracking.json`, `events.json`, `metrics.json`, `warning.json`,
`recommendation.json`, `validation.json`, `evidence_freeze.json`, `picture.json`,
`video.json`, `report.json`, `release.json`, `public_handoff.json`.

Each applicable stage records schema, source/config/model/code/runtime identities,
upstream hashes, artifact hashes, row/time coverage, quality/test result, limitations
and permitted next stage. Source/model provenance includes name/source/license,
checksum, model input size, class map and threshold as applicable. Do not put private
permission text or secrets in public manifests. Record dirty provenance when relevant
rather than presenting an uncommitted run as an exact clean revision.

gates.json records PASS/FAIL/BLOCKED and upstream evidence for each stage. Step 1
contract evidence may initially live in STATE.json. Existence is not acceptance.
Stale hashes, partial partitions, missing annotations or failed predecessors block
downstream execution. Final approval binds exact reviewed bytes and is invalidated
by subsequent artifact/configuration/source changes.

## Images and static picture

Expected diagnostic images: `images/calibration_preview.png`,
`images/detection_contact_sheet.png`, `images/tracking_contact_sheet.png`,
`images/metric_trends.png`. These are generated from the approved source, not previews.

Final picture: `images/trajectory_map.png`, title **Ten minutes of traffic in one frame**.
Require 1080 × 1350 PNG and one real continuous approved 600-second interval. Show
actual anonymous trajectories, entry/exit boundaries, queue/analysis zone, supported
direction/dwell encoding, measured compact summary and source/prototype disclaimer.
Measured congestion hotspot is allowed only with supporting evidence; no decorative
hotspot presented as measurement. No unsupported physical units. Do not stitch
unrelated intervals or substitute synthetic tracks. Inadequate trajectories/interval
block this deliverable and must not be marked complete.

## LinkedIn video

- `videos/annotated_analysis_preview.mp4`: bounded internal diagnostic rendition.
- `videos/linkedin_master.mp4`: final master.
- `videos/linkedin_web.mp4`: web-optimized copy of the accepted story/evidence.
- Canvas 1080 × 1350; aspect 4:5; 30 fps; H.264; yuv420p; duration 44.0–46.5 seconds.
- Default editorial target 45 seconds; 1320–1395 frames meet duration bounds at 30 fps.
- Audio optional; muted comprehension required. Full decode and metadata validation.

| Keyframe / evidence filename under images/video_keyframes/ | Story |
|---|---|
| 01_video_00s_hook.png | 00:00 business problem and truthful source context |
| 02_video_05s_detection.png | 00:05 actual detection execution glimpse |
| 03_video_10s_teaser_result.png | 00:10 actual supported classification and lead time, or explicit unavailable result |
| 04_video_15s_metric_definition.png | 00:15 congestion-definition challenge |
| 05_video_20s_tracking_challenge.png | 00:20 tracking/occlusion challenge |
| 06_video_25s_operational_metrics.png | 00:25 detections converted to operating metrics |
| 07_video_30s_warning_logic.png | 00:30 persistent leading deterioration and warning |
| 08_video_35s_lead_time.png | 00:35 warning versus independently defined visible queue |
| 09_video_40s_action.png | 00:40 conditional operational action |
| 10_video_45s_close.png | Last actual frame near 00:45: Camera → Metric → Warning → Action |

The last filename is a scene label; manifest time must be the actual final frame time.
By 10–15 seconds the viewer must understand problem, execution and actual result.
Never promise positive warning before evaluation. Every number/caption comes from
validated release evidence. A negative result remains signed and explained.

Accelerated source playback/selected excerpts require an edit map from output frames
to original source times. The map does not alter dwell, throughput, queue/warning
persistence, onsets or lead time. Display source elapsed time unless independently
supported wall-clock time exists. Sampling uncertainty is distinct from edit speed.

## Five-tab portable report

`report/index.html` plus relative `report/assets/`; screenshots under
`images/report_screenshots/`: `dashboard.png`, `video.png`, `method.png`,
`results.png`, `about.png`. Self-contained or portable local assets; no private paths.

| Tab | Required content |
|---|---|
| Dashboard | What happened? Why did warning fire? What should Operations consider? Actual classification, drivers and conditional response |
| Video | Accepted video; explain condensation of the whole episode into about 45 seconds without changing analytical time |
| Method | Detect → Track → Measure → Aggregate → Warn → Act; metrics, independent outcome/warning, privacy and source/calibration limits |
| Results | Actual classification, warning/queue timestamp or absence, signed lead/null, metric deltas, tracking quality, false warnings, sensitivity and independent validation |
| About | Business problem, stakeholder perspectives, challenges, role, technology, source/license, privacy, limitations and roadmap |

Do not label recorded analysis Live or Production unless those facts later become
independently true. Prefer Recorded analysis, Portfolio prototype, or Validated
historical clip only after its validation gate passes. Public wording must not
fabricate airport, pickup, company or operating-authority context.

## Claim, reference and publication boundaries

Every important public claim requires claim_id, evidence, calculation, unit,
classification, caveat, approval status and reviewer status. Use CLAIM_REGISTER.md.
PREVIEW_ONLY constants and UNSUPPORTED claims are prohibited from release outputs.
No model/tracking accuracy without independent ground truth, no operational impact
or production claims, and no identifiable face/plate focal points.

The unchanged reference pack contains three top-level files, ten LinkedIn frames and
five portfolio tabs. Its layout/story hierarchy is usable, its metrics/location/
timestamps/boxes/results are not evidence. Neither numerical resemblance nor a
matching airport background is a release requirement.

Public handoff is an explicit allowlist of accepted report/media, sanitized claims/
results, attribution, hashes and acceptance. Full raw source, real annotations,
private permissions, weights and unrestricted track tables are excluded. Separate
portfolio integration is later work in its own repository/task; no cross-repository
editing or publishing is authorized here.


## FAST-TRACK BLOCK 2 evidence update

Block 2 adds ignored typed observation/event Parquet files and hash-linked detection, tracking and trajectory manifests. See BLOCK2_REVIEW.md for exact names and censoring semantics. No final metrics, outcome, warning or public artifact release is implied.


## FAST-TRACK BLOCK 3 amendment

Block 3 materializes operational_metrics.parquet, baseline_summary.json, metric_quality_summary.json, warning_timeline.parquet, queue_outcome_timeline.parquet, warning_summary.json, sensitivity_results.parquet, recommendation.json, validation_results.json, release_data.json, evidence_index.json and claim_register.json. Exact bytes are linked by metrics_manifest.json, warning_manifest.json and validation_manifest.json. Diagnostic images only: metric_trends.png and warning_queue_timeline.png. release_data.json is the sole analytical input for later renderers. Aggregate-content approval never approves raw, excerpted or transformed source imagery or final artifact release.


## Block4 materialized output names and rights

The explicit Block4 request chooses videos/project6_linkedin_master.mp4 and
videos/project6_linkedin_web.mp4, superseding the earlier generic linkedin filenames.
Both are45s/1350frames/30fps/H264/yuv420p/1080x1350. The ten keyframes are
images/video_keyframes/01_video_00s.png through10_video_45s.png; final time1349/30s.
See BLOCK4_REVIEW.md for every image/report path. All are ignored generated assets.
manifests/trajectory_map_manifest.json,video_manifest.json and
report/report_manifest.json bind outputs; manifests/block4_visual_acceptance.json
binds visual review. report/evidence_index.json extends the original frozen index
without modifying it. Source pixels excluded; final release approval remainsfalse.
