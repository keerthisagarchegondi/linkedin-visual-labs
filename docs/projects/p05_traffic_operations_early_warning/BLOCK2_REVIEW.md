# Project 6 — FAST-TRACK BLOCK 2 review

Scope: Steps 5–7 only, authorized by the Block 2 request. Steps 1–4 and the
approved cam_3 source/geometry are preserved. Step 8 and all later work remain
NOT_STARTED. This report supersedes older model-not-acquired assertions for this
block only; earlier validation records remain historical evidence.

## Detector and source

Exactly one official YOLOX-Nano 0.1.1rc0 ONNX artifact was downloaded:
https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0/yolox_nano.onnx

SHA-256: `c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d`.
Size: 3,659,407 bytes. Upstream Apache-2.0; no separate weight restriction found.
See THIRD_PARTY_NOTICES.md. Approval for this internal inference does not confer
source-video publication rights or independent training-data rights.

Input: 416 x 416, float32 NCHW BGR, 0–255, top-left padding 114, no RGB conversion,
normalization or division by 255. Raw grid output [1,3549,85] decoded with strides
8/16/32. COCO winning classes 2 car, 3 motorcycle, 5 bus, 7 truck. Confidence is
objectness times class probability. Minimum confidence 0.10; class-agnostic NMS
IoU 0.45; minimum box dimension 6 source pixels. Context crop (550,250,1280,550)
restores boxes to source coordinates and does not change the accepted ROI.

The existing isolated Windows Python 3.13 CV environment used ONNX Runtime CPU
provider only, two intra-op threads and one inter-op thread. No packages installed,
no Torch/Ultralytics/supervision stack, no GPU. Ordinary development dependencies
and generic CI remain unchanged. Linux real inference was not rerun in this block.

cam_3.mp4 is 1,800 seconds, 1280 x 720, 10 FPS with independently verified original
CFR PTS. Every decoded frame retains its original index; 3 FPS rational sampling
selects 5,400 frames (indices 0,4,7,10,...). The last sampled timestamp is 1799.7s.
All analytics retain source time. No acceleration enters the analytical clock.

A 30-second smoke (1440–1470s) produced 657 boxes, 488 ROI-eligible, in 2.114s.
Visual review passed the bounded usability gate before the full run. Full output:
28,691 detections, 18,569 ROI-eligible; decode 41.164s, inference 71.855s, complete
streaming loop 133.262s. Source processing was 13.51 source seconds per wall second
for this batch, excluding model startup, source hashing, contact sheets and tests.
This is not a production/live performance claim. Peak RAM was not measured.

## Tracking and diagnostic limitations

tracking.py is an independent project-local ByteTrack-compatible adaptation of the
two-stage association approach, not the upstream implementation or a benchmark
replication. NumPy constant-velocity box Kalman prediction and existing SciPy
Hungarian matching: high score 0.50, new-track score 0.55, high/low IoU gates
0.20/0.40, lost buffer 2 original seconds, confirmation after 3 observations,
maximum normalized motion 0.15 image diagonals per second. This is not road speed.
Low-confidence detections recover active tracks but never spawn or resurrect lost
tracks. Predictions only assist matching; they never become observation rows.
IDs reset per clip invocation. No appearance, plate, face or external identities.

572 candidate tracks; 178 confirmed; 394 unconfirmed. 346 have one observation;
411 span less than two seconds. 40 lost-track recoveries; zero duplicate births
suppressed in this run (the suppression path is covered by deterministic tests).
Median confirmed observed duration: 32.8 seconds. 16,525 observation rows. The
canonical tracking writer took 5.816s including table input/output; initial matching
and output measurement was 1.407s. Do not compare these as identical timing scopes.

Reviewed 1440.0–1443.4s maintains queued vehicle IDs. Three completed-journey sheets
inspect IDs 195/434/482 at entry and exit. Background/sign false positives,
occlusion, transient candidates and car/truck fluctuations remain visible. A large
main-road vehicle can geometrically overlap the configured 2D ROI; ROI membership
is not lane identity. Directional crossing eligibility is essential. Future metrics
must expose this contamination risk and the limited complete-journey sample.
No precision, recall, mAP, MOTA, IDF1 or identity-switch accuracy is claimed.

## Events and reconciliation

All trajectory points are observations, with explicit gaps. Entry/exit use each
accepted line's separate local direction, segment intersection and 0.001 normalized
hysteresis. Gaps above 1 second reset crossing anchors and low-motion persistence.
Each eligible track crosses each boundary at most once. Crossings timestamp the
current observed hysteresis completion and store the preceding observation bound.
Retrospective confirmation admits observed history; it is not an online alert time.

131 entry events and 81 exit events. Journey partition: 65 complete gap-free pairs,
65 entry-only, 15 exit-only, 32 confirmed censored without boundaries, one gapped or
invalid pair, and 394 short fragments. All 572 are accounted for; 507 are not
complete eligible journeys. Start/end-inside flags describe the retained ROI-only
observation boundaries, not inferred physical crossings. Track inventory records
lost/removed lifecycle. Only completed pairs have elapsed entry-to-exit values;
no aggregate dwell statistics or throughput was calculated.

Low-motion evidence uses displacement/image diagonal/original seconds, threshold
0.002 with 3-second persistence: 10 starts and 10 ends; no right-censored active
intervals at track end. Queue-zone transitions: 192 enters and 200 leaves, which
need not balance because observations may start/end inside and repeat transitions.
These are primitive events, not a frozen visible-queue outcome or warning.

All 16 machine-readable reconciliation checks pass: unique keys, exact detection
joins, unchanged clocks/coordinates, ROI-only rows, confirmed observed event joins,
event uncertainty bounds, unique directional crossings, exhaustive journey
partition, gap-free ordered complete pairs, censored elapsed exclusion, and exact
entry/exit count/timestamp agreement. Event processing took 1.689s.

## Evidence and resumption

Ignored output root: outputs/p05_traffic_operations_early_warning/.
Data: detections.parquet, detection_summary.json, tracks.parquet,
track_inventory.parquet, track_quality_summary.json, trajectories.parquet,
zone_events.parquet, crossing_events.parquet, journeys.parquet,
event_reconciliation.json. Current data footprint approximately 4.3 MB.
Manifests: detection_manifest.json -> tracking_manifest.json ->
trajectory_manifest.json, each hash-linked to source, geometry, code and outputs;
block2_quality_review.json preserves the internal visual review limitations.
Images: detection_smoke_contact_sheet.png, detection_contact_sheet.png,
tracking_contact_sheet.png, crossing_trajectory_contact_sheet.png.

Raw source, model, all data, images, logs and manifests remain ignored. No final
poster, LinkedIn video or report was generated. Public reuse remains unapproved.
Canonical logic: detection.py, tracking.py, events.py, block2.py. Reproduction uses
Detector/DetectionConfig/detect_video in the optional CV interpreter; build_tracking
and build_events in the primary interpreter. See the ignored block2/full_detection.py
and reconcile.py invocation records. Never rerun without rechecking source admission,
source/geometry/model hashes and current authorization. Completed-stage reuse needs
matching code/config/input hashes; interrupted detection restarts its bounded stage.
Partial Parquet files are never accepted as final outputs. No decoded-frame cache.

40 deterministic tests cover Steps 5–7. Final gate evidence is bound in STATE.json
and .cache/p05_traffic_operations_early_warning/block2/validation.json after the
single full-suite run. Internal diagnostic acceptance does not replace independent
Step 11 validation. The 120s lighter baseline cannot supply an entire 300s rolling
normal baseline; the metric contract remains unchanged.

Next permitted action, requiring explicit authorization: PROJECT6 FAST-TRACK BLOCK 3
— Metrics + queue outcome + warning + recommendation + evidence. No Git checkpoint
is performed or authorized by this block.


## Final contract correction and validation order

The single full suite passed 1,432 tests before the final lifecycle-field enrichment.
A final contract review added per-observation age, hit count, missed sampled-frame
count, source-pixel displacement, relative movement and confirmation-at-observation.
The existing 40 tests were extended with assertions; focused 40 and all 378 Project 6
tests, Ruff and strict mypy passed again on corrected code. The full suite was not
repeated, honoring the explicit once-only limit. This order is preserved in the
machine-readable validation record; the full run does not cover that correction.

Final artifacts retain 16,525 tracked observations with the added fields; event
counts and all 16 reconciliation checks are unchanged. Final tracking writer:
5.464s; event writer: 1.626s; structured data: approximately 4.63 MB. Median duration
across all 572 candidates is zero seconds because 346 have one observation. Median
confirmed duration remains 32.8s. The short-under-2s candidate rate is 71.85%; invalid
observed jumps: zero under the configured gate; 32 tracks recovered across 40
recovery episodes. 177 confirmed tracks ended lost/removed; one remained active at
clip end. Lost/removed is a lifecycle state, not necessarily a broken journey.

All detector/tracker/event thresholds are CONFIGURED_ASSUMPTION values, not
empirically optimal settings. No analytical clock or threshold was tuned to force
an outcome. Earlier timings above remain observations of earlier writer runs.
