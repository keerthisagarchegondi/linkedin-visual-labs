# Project 6 — Approved implementation plan

## Current presentation amendment — Sub-step 4.B, 2026-09-13

Recruiter-facing title: **Traffic Flow Deterioration Early-Warning System**.
REVISED_PRESENTATION_SCOPE.md governs the revised question, KPI hierarchy and story:
**Busy traffic ≠ congestion.** This supersedes the presentation mission below,
not historical analytical decisions or numbered Steps 1–15. Internal identifiers
are unchanged. Steps 1–11 remain VERIFIED. Steps 12–14 retain their technical
implementation and earlier gates, but require revised-story regeneration and
visual acceptance before Step 15. The 1,523-test baseline remains historical.

This bounded task edits documentation only. Next, after explicit authorization,
regenerate the Step 12 picture, Step 13 video and Step 14 five-tab report from
frozen release_data.json/evidence_index.json. Preserve source/model, geometry,
thresholds, original timestamps and all analytical outputs; no inference/tracking
rerun. Keep the Project 6 layout system and create separately hash-bound presentation
claims. Review the static image, ten decoded keyframes, and all five desktop/mobile
tabs; test claim selectors, units, null lead time, source-time mapping and rights flags.
Existing visual gates do not certify the revised story before regeneration.

Actual footage may appear in internal previews now; new manifests must carry
`PUBLICATION_STATUS: PENDING_SOURCE_PERMISSION` and final release approval false.
Pending public permission does not block internal preview generation. Stop after
the authorized block; no Step 15, publication, portfolio integration or Git actions
are implicitly authorized. Checkpoints A/B/C/D remain unchanged.

## Historical plan and analytical implementation record

## Authorization and identity

This document preserves the approved takeover plan and corrected plan audit. The
authorized Step 1 scope now includes the typed contract/configuration foundation
described below. Current acceptance evidence is recorded separately in STATE.json.
A plan describes future work, not authorization. Execute one explicitly requested
step, pass its gate, stop, and obtain authorization before the next step.

- Display: Project 6 — Traffic Operations Early-Warning System.
- Original master-catalog ID: 5 — Traffic Vision and Congestion Warning.
- Internal package: `p05_traffic_operations_early_warning`.
- Only repository: `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
- Required branch: `project/p05-traffic-operations-early-warning`.
- The old `D:\linkedin-visual-labs` clone is prohibited as a source, fallback,
  comparison repository or alternate workspace. No parent-directory clone search.
- Never access ChangeGraph, job_hunter or the separate portfolio repository during
  core work. Portfolio integration is a separately rooted future task only.

## Mission and decision flow

Operations may have camera footage but learn about congestion only after a queue
is obvious. Test whether a licensed fixed-camera episode supports an earlier,
explainable warning against an independently defined sustained visible queue.

Camera → timestamped vehicle detections → temporary anonymous tracks → directed
events/movement → density/dwell/throughput/queue evidence → leading deterioration
→ warning → conditional operational recommendation. Short form:
**Camera → Metric → Warning → Action**.

No airport/company/pickup location, production/live deployment, accuracy, impact,
metric or positive lead-time claim is assumed. Negative and insufficient-evidence
outcomes remain valid. Source imagery and all final values must replace PREVIEW_ONLY
reference content. See [product](PRODUCT_CONTRACT.md), [source](SOURCE_CONTRACT.md),
[metrics](METRIC_CONTRACT.md), and [outputs](OUTPUT_CONTRACT.md).

## Repository-grounded architecture and baseline

Governance inspection confirmed expected root/branch and HEAD
`7c253340c3fced632a9fe6797c5f9d00a9a94521`, with origin
`https://github.com/keerthisagarchegondi/linkedin-visual-labs.git`.
Before governance edits only the 18 reference files were untracked. No Project 6
source package or documentation directory existed. Historical baseline ancestry
`0557673c790dc900db7293586ce96931ede40c96` was confirmed during the audit.

The repository uses setuptools `src/linkedin_visual_labs`, project packages, Typer
apps exported by `projects/__init__.py` and registered by the top-level `cli.py`,
YAML in `configs`, tests under `tests/projects`, small fixtures under `tests/fixtures`,
and ignored `outputs`. Proposed command group is `traffic`.

Reuse `common/config`, validation, path containment, structured logging, namespaced
randomness, plotting, atomic JSON manifest and media conventions. Ordinary Python
modules are canonical logic; no notebook-only implementation. Most recent Project 5
patterns include frozen Pydantic contracts, a no-write pipeline context, Parquet,
hash-bound stage evidence, packaged FFmpeg and portable report/manual acceptance.
Reuse patterns without importing another project's business/presentation modules.

The shared output helper supports `video`, not required `videos` and `report`.
Use a project-local path adapter without changing older projects or common APIs.
Shared probing invokes `ffprobe` through PATH. New media adapters must explicitly
resolve/validate tools. Do not reuse the legacy renderer with an old-clone path.
The global continuity gate performs a fetch; do not execute it in read-only work.
Preserve `contracts/repository_continuity.json` and earlier baselines.

## Environment, CPU runtime and isolation decision

Current Step 2 execution boundary: 2.A COMPATIBILITY_PASS and 2.B VERIFIED;
the user authorized the combined 2.C CLI, 2.D runtime validation and 2.E acceptance.
Design A and the exact OpenCV-headless 5.0.0.93 / ONNX Runtime 1.30.0 pair are accepted
for this scaffold. Windows CPython 3.13.2 and Linux CPython 3.13.15/glibc 2.43 passed
installation/import/provider checks. See DEPENDENCY_DECISION.md and STATE.json.
Older governance observations below are historical; model compatibility/licensing,
actual PTS probing and performance remain unverified. The remaining Step 2 scope is
diagnostic CLI registration and an optional manual workflow. ffprobe stays NOT_CONFIGURED.
Null thread counts retain runtime
defaults; explicitly configured counts are bounded strict integers 1–64.

Python contract is `>=3.13,<3.14`; the repository `.venv` records Python 3.13.2.
Keep that environment strategy and Windows/Linux support. Base dependencies already
include NumPy, SciPy, pandas, PyArrow, imageio and imageio-ffmpeg. Local metadata
also includes Torch, but generic `.[dev]` intentionally excludes it; Zombie has a
separate optional CPU-Torch job. Governance did not establish CV compatibility;
Sub-step 2.A subsequently passed the bounded cross-platform compatibility gate.
No full baseline tests were run during governance setup; Step 1 later passed 1,203.

Selected design A: optional OpenCV-headless + CPU ONNX Runtime + one future
approved small YOLO-family ONNX detector + a typed ByteTrack-compatible layer using
existing NumPy/SciPy. Isolated extra: `traffic-cv`. Design B (isolated
Ultralytics/ByteTrack) is not installed alongside it. If A fails compatibility,
stop and propose a reviewed design change before adopting B.

Sub-step 2.A verified Python 3.13 Windows AMD64/Linux wheels, version intersections,
CPU provider, transitive dependencies and package terms for the selected pair.
Model-specific weight terms, ONNX operators, preprocessing and class map remain
unverified and require a later approved descriptor. Model export does not erase weight-license terms.
Record model name/source/license/checksum/input size/class map/threshold before use.

Lazy imports keep help, contracts and fixture analytics working without CV. Ordinary
`.[dev]` and generic CI gain no CV/Torch/CUDA dependency. Preserve Ruff, strict mypy,
pytest, current CI job partition and existing Zombie checks. Add a separate optional
Windows/Linux compatibility workflow only in a later authorized scope; real inference is explicitly opted in and
requires approved local source/weights. It must not download either automatically.

Packaged FFmpeg resolution follows the newest project pattern with executable
ownership/version/hash evidence. Do not assume imageio-ffmpeg supplies ffprobe.
Later authorized work must verify an explicit timestamp-probing executable/interface and frame-to-PTS
pairing; 2.B leaves ffprobe NOT_CONFIGURED with no PATH or nominal-FPS fallback. Acquisition of any new tooling
belongs to separately authorized dependency work, not governance setup.

## Source, storage and performance prerequisites

Steps 1–2 can proceed without footage. Step 3 cannot pass without a specific approved
source and documented reuse permission. Prefer a continuous 30–45-minute episode;
approximately 12–15 minutes requires adequate normal/buildup/sustained degraded flow.
No random substitution, inferred permission, fabricated context or preview source.
Independent detection labels are needed before Step 5 acceptance; tracking labels
before Step 6; reserved outcome/evaluation evidence before Step 11.

Store raw source, actual local config, real annotations and private permission in
`data/raw/p05_traffic_operations_early_warning/`; processed intermediates in
`data/processed/p05_traffic_operations_early_warning/`; weights in
`models/weights/p05_traffic_operations_early_warning/`; model caches in
`models/cache/p05_traffic_operations_early_warning/`; tool cache, temporary frames,
checkpoints and local logs in `.cache/p05_traffic_operations_early_warning/`.
All generated artifacts go under ignored `outputs/p05_traffic_operations_early_warning/`.
Preview files remain unchanged under ignored `reference/project6/previews/`.

Stream source frames through bounded buffers. Retain PTS/time base/source-relative
time and ordinal; never retain every decoded frame. At 1080p RGB a frame is about
6.2 MB; 45 minutes at 30 fps would require roughly 504 GB before overhead. This is a
planning illustration, not measured source storage. Benchmark an approved short
pilot before full inference and record actual CPU time, memory, coverage and disk.

Sampling is selected from measured quality/performance, not lead-time success.
Use original time for motion/expiry/windows/dwell/persistence; acknowledge sampling
uncertainty. Changing sampling invalidates downstream evidence. Rendering uses a
separate source-to-edit map. Cache by source/model/config/schema/code/runtime hash;
publish partitions atomically. Resume from compatible tracker state or replay a
known checkpoint, never silently reset identity at partition boundaries. Reject
incomplete/stale outputs from releases. Parquet analytical tables, JSON manifests
and small reviewable CSV/JSON fixtures fit existing conventions.

## Future file inventory

All paths are relative to the canonical repository, never another clone. `P` means
`src/linkedin_visual_labs/projects/p05_traffic_operations_early_warning/`; `T` means
`tests/projects/p05_traffic_operations_early_warning/`; `F` means
`tests/fixtures/p05_traffic_operations_early_warning/`; `D` means this documentation
directory; `O` means `outputs/p05_traffic_operations_early_warning/`.

```text
P/: __init__.py, cli.py, config.py, models.py, paths.py, runtime.py, media.py,
    evidence.py, source.py, calibration.py, detection.py, tracking.py,
    trajectories.py, events.py, metrics.py, queue_outcome.py, warning.py,
    recommendations.py, validation.py, visualization.py, video.py,
    reporting.py, pipeline.py, release.py
T/: __init__.py, conftest.py, test_contract.py, test_config.py, test_models.py,
    test_paths.py, test_cli.py, test_runtime.py, test_media.py, test_evidence.py,
    test_source.py, test_calibration.py, test_detection.py, test_tracking.py,
    test_trajectories.py, test_events.py, test_metrics.py, test_queue_outcome.py,
    test_warning.py, test_recommendations.py, test_validation.py,
    test_visualization.py, test_video.py, test_reporting.py, test_pipeline.py,
    test_release.py, test_portability.py, test_real_inference.py
F/: README.md, fixture_manifest.json, source_metadata.json, source_location.yaml,
    detections.csv, expected_tracks.csv, expected_events.csv, expected_metrics.csv,
    expected_queue_outcome.csv, expected_warning_timeline.csv,
    expected_recommendation.json, independent_annotations.json
configs/p05_traffic_operations_early_warning.yaml
configs/p05_traffic_operations_early_warning/source_location.example.yaml
configs/p05_traffic_operations_early_warning/runtime_constraints.txt
.github/workflows/p05-traffic-cv.yml
D/: IMPLEMENTATION_PLAN.md, PRODUCT_CONTRACT.md, SOURCE_CONTRACT.md,
    METRIC_CONTRACT.md, OUTPUT_CONTRACT.md, REQUIREMENT_TRACEABILITY.md,
    CLAIM_REGISTER.md, STATE.json, CONTINUITY.md
Later D/: README.md, VALIDATION_PROTOCOL.md, DEPENDENCY_DECISION.md,
          THIRD_PARTY_NOTICES.md, manual_acceptance.json
```

Only the nine required governance documents exist from this setup. Source/tests,
configs, optional workflow and later documents are future files, not scaffolding
authorized now. Future existing-file changes are limited to pyproject.toml,
projects/__init__.py, top-level cli.py, tests/test_cli.py,
tests/test_optional_dependencies.py, .github/workflows/ci.yml and root README.md.
AGENTS.md/.gitignore governance changes preserve original content. No unrelated
project, common helper or global continuity contract modification is planned.

## Common gates and test strategy

Every step uses focused deterministic tests with independently specified small
oracles, full Python annotations and fixed/namespaced seeds. Run relevant checks
after each implementation step; do not weaken tests or undertake unrelated repairs.
Record exact commands/results, changed files, upstream hashes, evidence, limitations,
next-step permission and state/traceability updates. Full baseline work is separate
from this governance setup; no full repository baseline is asserted here.

Future machine-readable gates carry stage/schema, source/config/model/code identities,
upstream artifact hashes, tests, quality status and PASS/FAIL/BLOCKED. A gate never
passes solely because its expected output file exists. Core unit/fixture/integration
tests are lightweight; real-inference smoke is separate and opt-in. Independent
annotation protocols and quality thresholds precede final evaluation. Freeze a
sensitivity neighborhood and publish unfavorable variants rather than choosing the
best lead time. False-warning evidence includes counts/durations and evaluable
non-queue exposure; overlapping windows are not independent trials.

Required refusal chain: no approved source → no real calibration/inference; failed
detection quality → no tracking; failed tracking quality → no final dwell/throughput;
invalid events → no final metrics; invalid metrics → no warning; unsupported claims
→ no public visuals. Diagnostics/insufficient-quality classifications are allowed,
but cannot invent downstream values. Step 11 final validation never replaces early gates.

## Step 1 — Lock source, business, metric, and output contracts

- Objective: explicitly review and freeze the persisted planning contracts.
- Prerequisites: verified governance and explicit Step 1 authorization.
- Likely files: D contracts/state/traceability/claims; P/__init__.py, models.py,
  config.py; configs/p05_traffic_operations_early_warning.yaml; T/test_contract.py,
  test_config.py. VALIDATION_PROTOCOL.md and README.md remain later work.
- Scope: identity; metric eligibility, windows, samples, missingness; independent
  outcome/warning; result precedence; privacy; source/model approval; output schemas,
  quality protocol and exact future file inventory. Separate unresolved source facts
  from locked semantic rules. Implement frozen typed declarations, strict validation
  and a no-write YAML loader; unresolved numerical rules remain REVIEW_REQUIRED.
- Non-scope: runtime scaffold, CLI registration, dependencies, source acquisition,
  detector models, inference, metric computation or state-machine execution.
- Tests: contract/state consistency, 15-step mapping, eight result classes, six action
  and six claim classes, privacy/timing rules, preview and path exclusions.
- Evidence: reviewed contracts and explicit Step 1 acceptance/state/test record.
- Acceptance gate: all requirements mapped, rules coherent, no invented source facts
  or preview constants, unresolved choices have owners and dependent gates.
- Blockers: unapproved scope or unresolved contract contradictions.
- Stop condition: finish contract gate or record failure; do not start runtime scaffolding.
- Next permitted step: Step 2 after acceptance and separate authorization; no checkpoint.

## Step 2 — Dependency isolation, scaffold, and registration

Bounded sequence: 2.A compatibility verification; 2.B exact isolated extra, separate
runtime YAML/constraints, paths.py/runtime.py, three focused test modules and dependency
notices; 2.C exactly config-check/doctor; 2.D existing Windows/Linux disposable
runtime validation; 2.E all preserved repository acceptance gates and state recording.
Runtime READY must never imply analysis READY. The user's bounded remainder request
authorizes 2.C–2.E together; it does not authorize Step 3.

- Objective: typed lightweight traffic interface and verified single runtime design.
- Prerequisites: Step 1 accepted; authorization for dependency/tool compatibility work.
- Actual Step 2 files: P/cli.py, paths.py, runtime.py; matching T tests and package
  marker; project runtime configs; optional manual p05-traffic-runtime.yml;
  D/DEPENDENCY_DECISION.md, THIRD_PARTY_NOTICES.md; named CLI registration and pyproject.
- Scope: integrate the Step 1 config/models; no-write context/help, lazy imports,
  runtime containment, explicit opt-in CPU imports, packaged FFmpeg version/provenance,
  and separate runtime versus analysis readiness. Source probing/frame PTS interfaces,
  media.py, evidence.py and pipeline.py are deferred to their later owning steps.
- Non-scope: weights, source, real analytics, unrelated project changes.
- Tests: imports blocked, CLI/help, config rejection, path escapes, missing extra,
  CPU provider, mocked probing, Windows/Linux Python 3.13 compatibility and dependency isolation.
- Evidence: exact dependency/tool decision, STATE.json step_2_validation, and ignored
  .cache/p05_traffic_operations_early_warning/step2-final command records; no output manifest.
- Acceptance gate: one compatible set and timestamp-tooling design; ordinary .[dev]
  remains free of new CV/Torch/CUDA; existing quality partition preserved.
- Blockers: incompatible wheels, unacceptable terms, transitive conflicts or failed gates.
  Unconfigured ffprobe/PTS tooling blocks future source-timing acceptance, not this diagnostic step.
- Stop condition: no source/model work on failure.
- Next permitted step: Step 3 after acceptance/authorization; no checkpoint.

## Step 3 — Source acquisition, licensing, metadata, and windows

- Objective: approve one source and original analytical timeline.
- Prerequisites: Step 2; specific source, suitable permission and acquisition authorization.
- Likely files: P/source.py, source models/CLI; T/test_source.py; F/source_metadata.json;
  D/SOURCE_CONTRACT.md and source review state.
- Scope: approved local ingest or approved acquisition, actual checksum/metadata,
  continuity/PTS, rights, baseline/evaluation and picture intervals.
- Non-scope: random substitution, fabricated context, calibration or inference.
- Tests: rights absent, corrupt file, hash mismatch, bad windows, cuts, variable timing,
  duplicate/missing PTS, interrupted ingestion.
- Evidence: O/manifests/source.json, data/frame_timestamps.parquet, private rights record.
- Acceptance gate: rights, camera, episode, visibility and timing accepted.
- Blockers: no approved source, inadequate duration/episode, unclear rights or timing.
- Stop condition: reject/block source; no real calibration/inference.
- Next permitted step: Step 4 after acceptance/authorization; no checkpoint.

## Step 4 — Camera geometry, zones, and calibration

- Objective: inspectable zones and directed entry/exit boundaries.
- Prerequisites: accepted source/timing and explicit authorization.
- Likely files: P/calibration.py, config/models; T/test_calibration.py; F/source_location.yaml.
- Scope: normalized polygons, bottom-center reference point, line direction/hysteresis,
  geometry/source hash and calibration preview; physical calibration only with evidence.
- Non-scope: invented dimensions/MPH, unsupported hotspot claims, detection.
- Tests: invalid/self-intersecting polygons, edges, transforms, line direction and source mismatch.
- Evidence: O/images/calibration_preview.png and manifests/calibration.json.
- Acceptance gate: reviewed geometry supports intended measurements; unsupported units disabled.
- Blockers: boundaries or queue zone not observable or meaningful.
- Stop condition: no analytical detection configuration proceeds with failed geometry.
- Next permitted step: Step 5 after Checkpoint A review and authorization; Git separately authorized.

## Step 5 — Timestamped vehicle detection

- Objective: reproducible source-linked detections with quality accepted before tracking.
- Prerequisites: Steps 1–4; approved model/license/checksum and acquisition; independent
  detection annotations and frozen acceptance protocol.
- Likely files: P/detection.py, detection functions in validation.py, runtime/media/models/CLI;
  T/test_detection.py, test_validation.py, test_real_inference.py; F detections/annotations.
- Scope: short smoke before full episode, streamed sampling, preprocessing/inference,
  coordinate restoration, vehicle class map, thresholds/NMS, timestamped partitions.
- Non-scope: tracking, identities, automatic source/model changes, ungrounded accuracy.
- Tests: fake session outputs, class map, letterboxing, invalid boxes, ties/empty frames,
  timestamp joins, model hash, restart; separate approved real smoke.
- Evidence: detection partitions/contact sheet, independent quality/sample sizes,
  runtime/coverage findings and detection/model provenance manifest.
- Acceptance gate: frozen detection quality thresholds pass representative independent samples;
  full output remains schema/timing valid.
- Blockers: weak detections, missing independent labels, incompatible/unapproved model.
- Stop condition: record INSUFFICIENT_DETECTION_QUALITY; no real tracking.
- Next permitted step: Step 6 after detection acceptance and authorization; no checkpoint.

## Step 6 — ByteTrack multi-object tracking

- Objective: temporary associations suitable for unique counts and dwell eligibility.
- Prerequisites: detection gate; reviewed ByteTrack provenance; independent tracking labels.
- Likely files: P/tracking.py, tracking validation/models; T/test_tracking.py and validation
  tests; F/expected_tracks.csv.
- Scope: two-stage association, motion/lifecycle, original-time expiry, stable ties/IDs,
  occlusion, restart state and fragmentation evidence.
- Non-scope: face/plate/driver identity, persistent or cross-camera re-identification.
- Tests: crossing objects, low-confidence recovery, occlusion, gaps, expiry, IDs and restart parity.
- Evidence: tracks/contact sheet, quality/fragmentation diagnostics, tracking manifest.
- Acceptance gate: independently assessed association/count suitability meets frozen thresholds;
  predicted-only positions distinguished from detections.
- Blockers: fragmentation/identity errors invalidate counts or completed dwell.
- Stop condition: INSUFFICIENT_TRACK_QUALITY; no final dwell/throughput derivation.
- Next permitted step: Step 7 after tracking acceptance/authorization; no checkpoint.

## Step 7 — Trajectories, events, and reconciliation

- Objective: auditable directed crossings and zone sessions.
- Prerequisites: accepted tracks and geometry.
- Likely files: P/trajectories.py, events.py and event validation;
  T/test_trajectories.py, test_events.py; F/expected_events.csv.
- Scope: trajectories, hysteresis, direction, eligible unique crossings/re-entry,
  completed/censored sessions, duplicate prevention and reconciliation.
- Non-scope: disappearance-as-exit, silent fragment merging, physical speed.
- Tests: jitter, reverse crossings, starts inside, boundary gaps, repeated visits,
  duplicate IDs, lost/censored observations and reconciliation failure.
- Evidence: trajectory/event tables and events manifest with join/accounting proof.
- Acceptance gate: valid source/track/time joins and explained counts/uncertainty.
- Blockers: unexplained counts or ambiguous eligibility.
- Stop condition: invalid event reconciliation blocks final metrics.
- Next permitted step: Step 8 after event acceptance/authorization; no checkpoint.

## Step 8 — Operational metrics and normal-flow baselines

- Objective: causal original-time operational summaries and defensible baseline.
- Prerequisites: reconciled events/tracks and approved normal interval.
- Likely files: P/metrics.py, metric validation/config; T/test_metrics.py; F/expected_metrics.csv.
- Scope: occupancy/density, initial 300-second throughput, completed dwell percentiles/count,
  relative/low motion, imbalance, trends, baseline deltas and explicit availability.
- Non-scope: warning, future leakage, completed censored dwell, unsupported physical units.
- Tests: endpoints, duplicates, irregular samples, warm-up, sparse/zero/null, no completed
  dwell, percentile method, baseline contamination and independently calculated aggregates.
- Evidence: operational metrics, normal_baseline.json, reconciliation and metrics manifest.
- Acceptance gate: measurements reconcile; minimum evidence rules and causal time hold.
- Blockers: unsuitable baseline, inconsistent counts, inadequate required evidence.
- Stop condition: invalid metrics block warning evaluation.
- Next permitted step: Step 9 after Checkpoint B review and authorization.

## Step 9 — Visible-queue outcome and early-warning state machine

- Objective: signed lead time against independently defined queue persistence.
- Prerequisites: accepted metrics; independent rules/cadence frozen before final evaluation.
- Likely files: P/queue_outcome.py, warning.py, config/models/validation; matching T tests;
  F/expected_queue_outcome.csv and expected_warning_timeline.csv.
- Scope: outcome, NORMAL/WATCH/WARNING/CRITICAL, deterioration drivers, persistence/reset,
  first complete-rule timestamps, uncertainty and all eight result classifications.
- Non-scope: circular/duplicated rules, backdating, positive-result tuning.
- Tests: early/equal/late/absent outcomes, all classifications, missing windows, persistence
  interruption, boundaries, direct critical transition, independence and no future leakage.
- Evidence: queue/warning timelines, drivers, arithmetic/config hashes and warning manifest.
- Acceptance gate: timestamps follow full persistence rules; warning does not require outcome
  activation; inputs and timing uncertainty are valid.
- Blockers: circular rules, bad metrics, ambiguous timing or unsupported precision.
- Stop condition: failed warning gate prevents supported recommendations.
- Next permitted step: Step 10 after acceptance/authorization; no checkpoint.

## Step 10 — Explainable recommendation engine

- Objective: evidence-linked conditional operating suggestions.
- Prerequisites: validated warning and source-location enabled actions.
- Likely files: P/recommendations.py, config/models; T/test_recommendations.py;
  F/expected_recommendation.json.
- Scope: deterministic action filtering/priorities, evidence IDs, conditional wording,
  illustrative/review classification or explicit no-action reason.
- Non-scope: real dispatch/road control, invented levers, causal impact claims.
- Tests: six actions enabled/disabled, absent evidence, conflicts, unavailable levers and wording.
- Evidence: recommendation.json, rule IDs and recommendation manifest.
- Acceptance gate: every emitted action enabled; context supported or clearly illustrative;
  valid no-action outcome when no action available.
- Blockers: unsupported enabled-action claim or invalid warning evidence.
- Stop condition: no unsupported action; record supported no-action when appropriate.
- Next permitted step: Step 11 after decision acceptance/authorization; no checkpoint.

## Step 11 — Independent validation, evidence freeze, and claim register

- Objective: defend the final result without replacing early quality gates.
- Prerequisites: accepted prior gates, reserved independent annotations and frozen protocol.
- Likely files: P/validation.py, evidence.py; T/test_validation.py, test_evidence.py;
  D/VALIDATION_PROTOCOL.md, CLAIM_REGISTER.md.
- Scope: held-out or disclosed limited evaluation, independent outcome annotation,
  quality/event checks, false-warning exposure, predeclared sensitivity, reconciliation,
  claim classification, immutable analytical evidence hashes.
- Non-scope: model-output ground truth, cherry-picked best thresholds, one-clip generalization.
- Tests: annotation/source mismatch, tamper, missing joins/evidence, changed configuration,
  unsupported claims and classification/approval checks.
- Evidence: validation, false-warning/sensitivity tables, claim register and evidence_freeze.json.
- Acceptance gate: each public claim has evidence/classification/caveat; uncertainty and negative
  outcomes retained; complete source-to-claim joins verified.
- Blockers: inadequate independent evidence, quality failures or unsupported claims.
- Stop condition: unsupported claims cannot become public visuals. A limited-result account
  needs separate acceptance and must not invent missing measurements.
- Next permitted step: Step 12 after Checkpoint C review and authorization.

## Step 12 — Ten minutes of traffic in one frame

- Objective: evidence-backed static trajectory picture.
- Prerequisites: approved claims, adequate tracks, approved continuous 600-second interval.
- Likely files: P/visualization.py; T/test_visualization.py.
- Scope: 1080 × 1350 PNG, actual anonymous trajectories, boundaries/queue zone, supported
  direction/dwell encoding, measured summary, source/prototype disclaimer; hotspot only if supported.
- Non-scope: montage-as-continuous, preview data, unsupported physical/heatmap claims.
- Tests: interval continuity/duration, canvas, track joins, metric agreement, unsupported-layer rejection.
- Evidence: trajectory_map.png, picture.json and human-reviewed artifact hash.
- Acceptance gate: readable/privacy-reviewed picture matches its exact source interval/evidence.
- Blockers: inadequate continuous interval/trajectories or unapproved claims.
- Stop condition: do not substitute synthetic imagery or mark unmet picture complete.
- Next permitted step: Step 13 after acceptance/authorization; required picture remains a release gate.

## Step 13 — Final LinkedIn video

- Objective: muted-comprehensible actual result in approximately 45 seconds.
- Prerequisites: frozen evidence/claims and public excerpt rights.
- Likely files: P/video.py, media.py; T/test_video.py, test_media.py.
- Scope: 1080 × 1350, 4:5, 30 fps, H.264, yuv420p, 44.0–46.5 seconds;
  master/web renditions, ten keyframes and separate source/edit map.
- Non-scope: altered analytical clock, fabricated context/results, positive-only narrative.
- Tests: 1320–1395 frames at 30 fps, full decode, metadata, keyframes, source mapping,
  first-15-second actual-result evidence, negative/unavailable text and readability review.
- Evidence: videos, keyframes, edit map, video manifest and reviewed hashes.
- Acceptance gate: OUTPUT_CONTRACT technical/story requirements and muted/privacy review pass.
- Blockers: rights, readability, misleading timestamps or unsupported claims.
- Stop condition: no release of invalid video.
- Next permitted step: Step 14 after acceptance/authorization; no checkpoint.

## Step 14 — Five-tab dashboard/report package

- Objective: portable evidence-backed Dashboard, Video, Method, Results and About.
- Prerequisites: accepted public claims/media.
- Likely files: P/reporting.py; T/test_reporting.py, test_portability.py.
- Scope: five tabs, relative local assets, evidence links, all result states,
  accessibility, Recorded analysis/Portfolio prototype wording.
- Non-scope: hosting, production/live claims, separate portfolio repository editing.
- Tests: navigation, escaping, portable links, null/negative results, claim agreement,
  no private paths/data, no unsupported Live/Production labels.
- Evidence: report/index.html, screenshots, report manifest and review findings.
- Acceptance gate: all tabs and assets work; actual evidence resolves; no private material.
- Blockers: stale metrics, broken links, private data or unsupported language.
- Stop condition: withhold invalid report.
- Next permitted step: Step 15 after acceptance/authorization; no checkpoint.

## Step 15 — End-to-end hardening and release acceptance

- Objective: accept the reproducible complete prototype and public handoff.
- Prerequisites: all required earlier gates/deliverables accepted.
- Likely files: P/release.py, pipeline.py, evidence.py; T/test_release.py,
  test_pipeline.py, test_portability.py; final D documents/manual_acceptance.json; root README.md.
- Scope: fixture end-to-end and controlled approved-source run, restart/corruption,
  regression, claim audit, explicit public/Git allowlists and hash-bound manual acceptance.
- Non-scope: deployment, portfolio integration, autonomous Git publication.
- Tests: relevant Ruff formatting/lint, strict mypy, pytest/CI partitions, reject bad
  upstream gates, deterministic fixture replay, stale caches, media decode and portability.
- Evidence: release/public_handoff manifests, exact accepted hashes, gate/test results,
  measured runtime/storage and final review.
- Acceptance gate: required stages/assets pass; no forbidden Git/public material;
  accepted hashes match final artifacts and repository quality gates are preserved.
- Blockers: any unmet source/quality/evidence/privacy/reproducibility/artifact/regression criterion.
- Stop condition: complete only after actual acceptance; otherwise explicit blocked/incomplete state.
- Next permitted step: Checkpoint D review; Git actions separately authorized. No core next step.

## Checkpoints, risks, handoff and completion

| Checkpoint | Boundary | Review |
|---|---|---|
| A | Steps 1–4 | Contracts, isolation, source rights/timing, geometry |
| B | Steps 5–8 | Detection/tracking quality, events and metrics |
| C | Steps 9–11 | Independent outcome, warning, response and frozen claims |
| D | Steps 12–15 plus final review | Required media/report, regression and release hashes |

Commit candidates are code, approved configuration/templates, docs, small synthetic
fixtures, tests and specifically approved small public assets. Never stage by broad
directory assumption; no source, weights, private permissions, previews, caches or
large generated output. No checkpoint authorizes staging/commit/push/PR on its own.

| Risk | Honest fallback |
|---|---|
| Source licensing fails | Block acquisition/use/publication; approve a replacement explicitly |
| Inadequate episode | INSUFFICIENT_SOURCE_EPISODE; no fabricated normal/buildup |
| Poor detection | INSUFFICIENT_DETECTION_QUALITY; no downstream tracking |
| Fragmented tracks | Censor invalid dwell; INSUFFICIENT_TRACK_QUALITY when necessary |
| No queue or warning | NO_VISIBLE_QUEUE_EVENT or NO_VALID_WARNING; null lead |
| Zero/late warning | Preserve zero/signed negative result and limitations |
| CPU too slow | Benchmark smaller approved input/model or sampling; revalidate quality |
| Dependency incompatibility | Block Step 2; reviewed version/design change, no dual stack |
| Sampling/time uncertainty | Report uncertainty; withhold unsupported precise lead |
| One-episode evidence | Clip-limited claims, no generalization or causal business impact |
| Unsupported lever | Conditional illustrative response or enabled review/no-action |
| Misleading visuals/stale cache | Hash/claim rejection; never copy preview results |

Handoff consists only of approved portable report/media, sanitized results/claims,
attribution, checksums and acceptance record. Later portfolio integration belongs to
a separate Codex task rooted at `D:\My-portfolio-Keerthi`; accessing that repository
from this core project is prohibited. No cross-repository editing is planned here.

Definition of done: approved source/model provenance; original-time reconciliation
through all layers; independent quality/outcome validation; all result classes;
false-warning and sensitivity evidence; every public claim classified and supported;
specified PNG/video/five-tab report; privacy/rights and exact-hash manual acceptance;
CPU capability; lightweight ordinary installation; relevant regression gates; and
durable state/continuity. Negative results may satisfy a validated prototype;
missing required evidence/deliverables may not be called a complete release.

Resume only through [CONTINUITY.md](CONTINUITY.md), actual Git state and gate evidence.

## Step 2 final acceptance — 2.C–2.E

Step 2 VERIFIED after 138 focused Step 2 tests, 287 Project 6 tests, and all 1,341
repository tests passed (27 added to the preserved 1,314 baseline). No failures,
errors, skips, deselection, xfails or xpasses. Ruff format/lint, strict mypy, pip,
CLI/package smoke and dependency isolation passed. Existing pandas/calendar and
pytest-cache permission warnings remain; no tests or gates were weakened.

The traffic group exposes exactly config-check and doctor. Config-check validates
both configs and contained paths without writes. Doctor is metadata-only by default;
--check-imports opts into cv2/onnxruntime and packaged FFmpeg -version only.
--require-runtime returns 1 for unavailable/unusable native runtime; invalid config
returns 2. Missing source/model/tracker blocks analysis, not CPU runtime readiness.
Contract-only imports remain independent of the runtime scaffold through lazy
traffic registration. The test package marker avoids collision with root CLI tests.

Existing disposable Windows 3.13.2 and Linux 3.13.15 environments passed actual
declared-extra/constraint checks, both doctor native modes and pip consistency.
OpenCV distribution 5.0.0.93 / cv2 5.0.0 and ONNX Runtime 1.30.0 expose
CPUExecutionProvider on both. No reinstall was necessary. Base/dev declarations
and active dependency graph remain CV/GPU-free; the populated primary environment's
pre-existing optional Torch is distinct and unchanged. Zombie and ordinary CI are
unchanged. p05-traffic-runtime.yml is manual-only for Windows/Linux Python 3.13;
its remote execution is not claimed. It acquires packages only, never models/data.

STATE.json step_2_validation binds final commands, local evidence hashes and accepted
files. The ignored step2-final cache contains runners, snapshots and command records.
Earlier acceptance sections/hashes are historical; this section supersedes their
Step 2 IN_PROGRESS / next-2.C statements. Preserve unchanged Step 1 code/config/test
hashes. FFprobe and original-PTS probing remain future source-timing requirements.

Source remains REVIEW_REQUIRED/unapproved; model NOT_SELECTED/NOT_ACQUIRED; tracker
NOT_IMPLEMENTED (Step 6); analysis NOT_STARTED. No model download, traffic access,
inference, geometry, tracking or analytical pipeline was performed. Existing full
regression tests may exercise unrelated deterministic synthetic fixtures.
Next: Project 6 — Step 3 — Source acquisition, licensing, metadata, and analysis
windows, only after explicit authorization. Steps 3–15 remain NOT_STARTED.
No checkpoint follows Step 2; no staging, commit or push was performed.

## Recovery 1.D execution design (authorized Steps 3-4 only)

The user explicitly bundled these two steps. Dataset_A stats/probes -> duration/HD
filter -> 24 PTS samples per survivor -> three-camera dense shortlist -> episode
and timing review -> internal academic admission -> relative geometry and preview
-> 25 deterministic tests and repository gates. Exact scope and evidence are in
AICITY_SOURCE_REVIEW.md. Step numbers, later prerequisites and Git checkpoints
are unchanged. Code lives in aicity_source.py/calibration.py; source.py and frozen
Step 1 defaults are preserved. Next Block 2 must consume the source-specific ignored
manifests and bind their hashes. This entry authorizes no next block or Git action.


## FAST-TRACK BLOCK 2 evidence update

Block 2 executed Steps 5–7 with the explicitly authorized internal sanity/diagnostic quality gate. Independent accuracy validation remains Step 11 work, not a fabricated acceptance claim. See BLOCK2_REVIEW.md and STATE.json for final gate status. Step 8 remains NOT_STARTED.


## FAST-TRACK BLOCK 3 amendment

The explicitly authorized Block 3 executes Steps8–11 as one bounded block, retaining independent stage gates. Step8 metric/baseline reconciliation passes; Step9 preserves NO_VISIBLE_QUEUE_EVENT and null lead time; Step10 emits an enabled illustrative review recommendation; Step11 validates independent arithmetic and freezes aggregate evidence, without an accuracy claim. Final software acceptance is recorded in STATE.json. Step12 and later remain NOT_STARTED. No checkpoint/Git action was authorized.


## FAST-TRACK BLOCK 4 acceptance

The explicitly authorized Steps12-14 retain separate static/video/report gates and
are VERIFIED after derived-only rendering and visual review. See BLOCK4_REVIEW.md
for the bounded design, exact modules, limitations and output inventory. 35 focused,
459 Project6 and1513 repository tests pass; full run once on final frozen code.
Step15 remains NOT_STARTED. No CheckpointD or Git action occurred.
