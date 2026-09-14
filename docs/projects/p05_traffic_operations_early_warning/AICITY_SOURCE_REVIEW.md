# Dataset_A source recovery 1.D

## Decision and scope

Selected **cam_3.mp4** for internal non-commercial academic analysis. Technical and
sampled episode admission passed; final software acceptance is recorded in STATE.
Source admission is not a final queue label, warning result, detector accuracy,
tracking accuracy, measured service capacity, or publication approval.
No geographic location, airport, business operator or operating lever is inferred.

Canonical root and expected branch were verified before edits. Prior RoundaboutHD
screening/rejection remains historical, including a byte-preserved
manifests/roundabouthd_source_manifest.json. No old source was rescreened.

## Inventory and screening

Dataset_A contains 31 original MP4s, three metadata text files and two subsequently
user-supplied agreement PDFs: 36 files. No ROI, MOI or camera calibration files were
supplied. Exact inventory/probe metadata are in aicity_dataset_inventory.json.
25 clips fail duration below 600 seconds (196.6-300 seconds), including every
weather/dawn variant. All six duration survivors also meet HD requirements:

| Camera | Seconds | Resolution | FPS | Initial review |
|---|---:|---|---:|---|
| cam_2 | 1800 | 1280x720 | 10 | Mostly free through flow |
| cam_3 | 1800 | 1280x720 | 10 | Stop-controlled approach; chosen after deeper review |
| cam_4 | 1800 | 1280x960 | 15 | Signal intersection, short approach visibility |
| cam_5 | 1800 | 1280x960 | 10 | Signal intersection, shortlisted |
| cam_6 | 1800 | 1280x960 | 10 | Approach coverage near borders |
| cam_7 | 1800 | 1280x960 | 8 | Most conspicuous accumulation, shortlisted |

Each survivor has 24 uniformly spaced original-PTS frame samples. The three
shortlisted cameras (7, 3, 5) each received 120 samples at 15-second intervals over
the full episode. Four additional cam3 motion sheets use 2-second samples across
1280-1302, 1400-1422, 1500-1522 and 1590-1612 seconds. No detector was used.

Cheap initial ranking favored cam7. Deeper review changes the final ranking:
cam3 24/26, cam7 20/26, cam5 18/26, cam2 17/26, cam4 17/26, cam6 16/26.
The 13 ordinal factors and reasons are recorded in the screening summary; scores
are configured reviewer judgments, not operational metrics. Lower camera ID breaks
the final cam2/cam4 tie. No user selection or result-target tuning was required.

Cam7 repeatedly clears much of its visible queue (for example near 900, 1020,
1170, 1290 and 1560 seconds). Cam5 alternates stopped groups and discharge. Those
sampled observations do not establish degradation beyond normal signal cycles.
Cam3 retains an approach queue across multiple different head departures in the
selected later episode. The 1500 and 1590 motion sheets support replenishment and
retained upstream accumulation, rather than one stopped vehicle or one red phase.
No numeric throughput decline is asserted from visual screening.

Low-cost appearance proxies are in ignored cam_3/5/7_deep.json evidence. Each uses
absolute grayscale difference from the full-episode sampled median (>25/255), plus
successive 15-second image differences in an explicitly diagnostic rectangle.
These noncausal screening proxies are not vehicle counts, movement speed, queue
counts or discharge rates. Shadows, reflections and stationary-object absorption
limit them. They are not inputs to a leading warning or approved analytical geometry.

## Source, timing and windows

Filename: cam_3.mp4; bytes: 241985291.
SHA-256: f368eea873bbfd60bd41bfc9cc2cd17b1e6e64967e091142ba0791f0d317990a.
H.264 High/avc1, yuv420p, 1280x720, 10 fps, no audio, exactly 1800 seconds.
Complete streaming decode to null returned zero: 18000 frames, PTS 0 through
18430976, uniform 1024-tick increments at time base 1/10240. CFR is verified from
all decoded PTS, not assumed from nominal FPS. No severe decode errors were found.
Normal motion is supported by short original-time comparisons and supplied stats;
independent camera acquisition logs were not supplied. Fixed view and absence of
major cuts are sampled visual findings, not exhaustive camera ground truth.

| Original interval | Purpose | Evidence/limitation |
|---|---|---|
| [1260,1380) | Lighter baseline, 120 s | Empty/isolated waiting approach; normal individual stops remain |
| [1380,1440) | Buildup, 60 s | Arrivals increase approach accumulation |
| [1440,1650) | Retained-queue candidate, 210 s | Multiple queued vehicles persist while different vehicles depart |
| [1200,1800) | Static interval, exactly 600 s | One continuous camera; future title: Ten minutes of traffic in one frame |

The selected 120-second baseline cannot itself generate a complete 300-second
rolling baseline window. Do not pad it with buildup, silently shorten the metric
contract, or present partial windows as complete. Step 8 must preserve unavailable
values or separately justify and validate a compatible baseline design. No lead
 time or warning threshold influenced this selection. The episode is a candidate
for later independent queue validation; sampled review is not ground truth.

## License and publication boundary

The supplied DataLicenseAgreement_AICityChallenge_2021.pdf is authoritative for this
review; AIC2020-DataLicenseAgreement.pdf remains supporting historical context.
Both originals and extracted exact text remain local and ignored, with hashes.
The terms limit access/use to participants accepting the agreement, restrict use
during the challenge to challenge purposes, require protecting access and prohibit
providing the Data to nonparticipants. After the challenge, use by participants is
limited to non-commercial academic purposes. No ownership is inferred. Submitted
metadata may be used by NVIDIA for commercial or non-commercial purposes.

ANALYTICAL_USE_ALLOWED: conditional non-commercial academic use only, under the
agreement and the user's authorized internal study scope. This is not an open/CC
license and does not assert independent verification of participant registration.
PUBLIC_RAW_VIDEO_REUSE_ALLOWED: false for the intended LinkedIn/portfolio release.
The minimal research-paper reproduction exception requires acknowledgements and
redaction of faces/plates; it is not a general promotional-video exception.
Public derived visuals require separate review. Merely overlaying annotations on
Data does not bypass these restrictions. Prefer abstract aggregate visuals for the
future handoff, still subject to applicable permission; obtain explicit footage
permission before LinkedIn/portfolio excerpts. No public artifact is approved here.

## Geometry

Configured normalized bottom-center geometry is in manifests/calibration.json:
ROI [(0.48,0.47),(0.96,0.58),(0.96,0.73),(0.48,0.63)].
Queue [(0.60,0.59),(0.90,0.625),(0.90,0.68),(0.60,0.65)].
Entry [(0.92,0.60),(0.92,0.70)], valid crossing (-1,0).
Exit [(0.50,0.535),(0.64,0.535)], valid crossing (0,-1).
Overall journey direction (-0.956,-0.293): right-to-left then upward curve.
Background/through-road context y=0..0.44 and lower grass y=0.76..1 are excluded;
analysis also ignores everything outside ROI. No perspective bands are needed now.
Geometry is RELATIVE_ONLY and configured, never measured physical calibration.
No MPH, feet, meters, lane-mile density or real capacity. Traffic entering a clip
already in the zone is censored for completed dwell until later eligibility logic.
Turning paths, occlusion, boundary retention and track eligibility need Step 6/7
validation; this schema does not establish reliable counts by itself.

calibration_preview.png uses the real frame at original 1500.000 seconds. It shows
all regions, boundaries, direction and internal/public-rights disclaimers.

## Implementation and repeatable evidence

New aicity_source.py: strict stats parsing, rational declared FPS, duration/HD and
review gates, deterministic 13-factor ranking, exact 600-second windows, internal
admission schema separating public permission. Existing source.py and Step 1
models/config remain unchanged. New calibration.py: convex normalized regions,
contained proper queue subset, inset distinct boundaries, crossing directions,
disjoint context exclusions, serialization and RELATIVE_ONLY constraint.
No CLI command or ordinary dependency changed. Actual source/calibration live in
ignored manifests; checked-in Step 1 YAML remains a historical unapproved planning
declaration. Future Block 2 must read and hash-check the new source admission and
calibration manifests explicitly, not treat the planning YAML as the selected clip.

25 deterministic tests cover inventory, filters, stable ranking, exact interval,
source schema/admission failures, geometry containment, degenerate polygons,
coordinates, boundaries, local/overall direction, exclusions and serialization.
Real smoke validation is the selected full decode plus actual-schema validation
and visual geometry review. No inference/tracking/metrics implementation exists.

Execution evidence lives in .cache/p05_traffic_operations_early_warning/aicity-recovery-1d/.
The local runners before.py, screen.py, deep.py, license.py, timing.py, motion.py,
produce.py, gates.py, document.py and finalize.py capture orchestration. Exact FFmpeg
argument lists/results are in media_commands.json, deep_commands.json,
motion_commands.json, calibration_command.json and cam_3_timing.json. Gates have
individual JSON/log files; validation.json and scope-review.json bind final results
and changed-file hashes. Only sampled frames are retained; full decode streams to
null. Raw files are never renamed, moved, edited or downloaded by these runners.

The initial inventory process encountered newly uploaded PDFs and failed while
attempting text decoding; its corrected rerun treats PDFs as binary metadata.
PDF extraction initially failed console encoding, then passed with UTF-8 output.
One initial local lint finding was fixed only in new calibration code. These
failures did not cause fallback downloads, weakened tests or Git changes.

Final software acceptance: Steps 3/4 VERIFIED; 25 focused, 338 Project 6 and
1392 full repository tests passed. Full suite ran once. Ruff format/lint and
strict mypy (213 files) passed. No dependency or Git action; 1367 baseline tests
preserved. Exact commands, warnings, evidence hashes and file scope are bound in
STATE.json and the ignored validation/scope-review records.
