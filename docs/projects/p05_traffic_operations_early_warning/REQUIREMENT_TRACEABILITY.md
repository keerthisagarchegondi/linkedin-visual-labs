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

# Project 6 — Requirement traceability

## Current scope revision — Sub-step 4.B

This section supersedes older current/latest status statements below for presentation
scope only. Steps1–11 remain VERIFIED. Steps12–14 are technically implemented and
historically verified; revised-story regeneration and acceptance are pending.
Step15 remains NOT_STARTED. REVISED_PRESENTATION_SCOPE.md is the current story contract.

| Requirement | Binding | Current acceptance |
|---|---|---|
| Revised title/question and Busy traffic ≠ congestion | Revised scope; README; implementation plan | Documentation revised |
| Warning24:00 versus independent queue not established | release_data.result; existing P6-B3-01/02 | Frozen analytical evidence preserved |
| Eight-KPI hierarchy, units, intervals and claim caveats | Revised scope evidence table; CLAIM_REGISTER | Story contract revised; rendering pending |
| No source/model/geometry/threshold or timestamp changes | Frozen release/index hashes and unchanged implementation/configuration | Preservation checked in4.B |
| Actual footage for internal preview only | OUTPUT_CONTRACT; revised scope source treatment | Authorized; no new media generated |
| PUBLICATION_STATUS: PENDING_SOURCE_PERMISSION | Future presentation manifests; STATE.presentation_scope_revision | Required for regenerated artifacts; not public clearance |
| Steps12/13/14 revised static/video/five-tab story | Revised scope scene/tab plan | REGENERATION_REQUIRED |
| Independent queue/raw null-lead result retained | STATE and immutable release_data.json | VERIFIED historical analytical result |
| No implicit release/Git/portfolio authorization | Revised scope acceptance; CONTINUITY | Separate authorization required |

The earlier1,523-test run is retained as baseline evidence, not represented as a
new run. Bounded JSON, indexed-evidence SHA and file-preservation checks validate
this documentation-only revision. Historical requirements and all15 steps follow.

## Latest Step 3/4 execution — RoundaboutHD local screening

The latest source-specific authorization supersedes earlier acquisition plans.
P6-R03 is BLOCKED_SOURCE, not VERIFIED: four local videos passed complete decoding
and CFR metadata reconciliation, but bounded screening did not establish a sustained
normal-to-buildup-to-degraded episode. P6-R04 remains NOT_STARTED behind that gate.
See ROUNDABOUTHD_SOURCE_REVIEW.md, STATE.json and ignored source_screening_summary.json.

New source.py and test_source.py cover original-clock metadata, empirical ZIP/SCT
schemas, explicit duplicate/box exclusions, screening-only count/movement indicators,
deterministic ranking and source-bounded interval declarations. No existing tests
were changed. No detector, tracker, final metrics or geometry implementation is
claimed. Source/publication approval remain false; historical rejections are retained.

## Status semantics

PLANNED means a requirement is mapped but not implemented. NOT_STARTED means the
numbered implementation step has not begun. IN_PROGRESS requires explicit active
authorization. VERIFIED requires actual gate evidence, not a written plan. BLOCKED
means a dependent prerequisite or gate prevents execution. Governance verification
is separate from numbered implementation verification.

Step 1 contract implementation is VERIFIED against its acceptance gates; Step 2 is
IN_PROGRESS, with 2.A COMPATIBILITY_PASS and 2.B acceptance recorded in STATE.json.
Steps 3–15 remain NOT_STARTED. No source, model, analytical result or public artifact is
verified. STATE.json records actual validation separately. Paths refer only to the canonical repository;
P means the proposed Project 6 package, T its tests, O its ignored output root as
defined in IMPLEMENTATION_PLAN.md. “None” means a contract is not applicable, not
missing evidence for a claim.

## Numbered step coverage

| Requirement | Source contract | Metric contract | Step / status | Expected code area | Test / acceptance gate | Evidence output (planned) | Publication claim |
|---|---|---|---|---|---|---|---|
| P6-R01 Identity, source/business/metric/output rules | Approval boundary | Eligibility/time/units | Step 1 / VERIFIED | P/models.py, config.py; checked-in YAML; D contracts; both T test modules | 149 focused tests; 1203 full-suite tests; import/Ruff/mypy/pip/doctor PASS | STATE.json step_1_validation | P6-C04 remains unapproved |
| P6-R02 Lightweight typed scaffold/runtime | No source needed yet | Typed timing/quality interfaces | Step 2 / IN_PROGRESS | P paths/runtime implemented in 2.B; CLI/media remain deferred | 2.A Windows/Linux compatibility; 2.B strict config, path, dependency/import and packaged FFmpeg tests; full quality gates | DEPENDENCY_DECISION.md; STATE.json; ignored 2.A evidence | Compatibility only; no analysis/performance claim |
| P6-R03 Licensed continuous source/timing | Full source schema/statuses | Original time/windows | Step 3 / NOT_STARTED | P/source.py | Rights, hash, episode, cuts/PTS/window tests | source.json; frame_timestamps.parquet | Source attribution after approval |
| P6-R04 Observable geometry | Fixed camera/boundaries | Reference point/direction/units | Step 4 / NOT_STARTED | P/calibration.py | Polygon/transform/boundary/source checks; review | calibration_preview.png; calibration.json | P6-C04 |
| P6-R05 Timestamped vehicle detections | Approved source/model rights | Frame-time identity | Step 5 / NOT_STARTED | P/detection.py; early validation | Mock inference and independent detection quality before tracking | detections/; detection.json; contact sheet | P6-C02, P6-C10 |
| P6-R06 Clip-local tracking | Independent labeled sequences | Eligibility/gaps/censoring | Step 6 / NOT_STARTED | P/tracking.py; early validation | Occlusion, association, restart and independent track-quality gate | tracks/; tracking.json; contact sheet | P6-C03, P6-C10 |
| P6-R07 Trajectories/events | Approved geometry/source | Crossings/deduplication/sessions | Step 7 / NOT_STARTED | P/trajectories.py, events.py | Direction, jitter, gaps, censoring and event reconciliation | trajectories.parquet; zone_events.parquet; events.json | P6-C03, P6-C05 |
| P6-R08 Metrics/baseline | Approved normal interval | All metric definitions | Step 8 / NOT_STARTED | P/metrics.py | Window/censoring/missingness/causal aggregate oracles | operational_metrics.parquet; normal_baseline.json; metrics.json | P6-C05 |
| P6-R09 Independent queue/warning | Independent outcome annotation | Distinct rules/states/onsets/lead | Step 9 / NOT_STARTED | P/queue_outcome.py, warning.py | All eight classifications, persistence, independence and signed arithmetic | queue_outcome.parquet; warning_timeline.parquet; warning.json | P6-C06, P6-C07, P6-C08 |
| P6-R10 Conditional enabled actions | Actual operating levers | Valid driver evidence | Step 10 / NOT_STARTED | P/recommendations.py | Enabled actions, unavailable levers, conditional/no-action result | recommendation.json; recommendation manifest | P6-C09 |
| P6-R11 Independent validation/claims | Reserved annotation and source hashes | Quality/false warning/sensitivity | Step 11 / NOT_STARTED | P/validation.py, evidence.py | Tamper/joins/ground truth and claim gate | validation_results.json; evidence_freeze.json; claim_register.json | P6-C02 through P6-C11 subject to review |
| P6-R12 Ten-minute picture | One continuous 600-second interval | Actual eligible trajectories/summary | Step 12 / NOT_STARTED | P/visualization.py | Interval/canvas/metric links; privacy/readability | trajectory_map.png; picture.json | Approved P6-C03/P6-C05 only |
| P6-R13 LinkedIn video | Public excerpt rights/source-edit map | Original analytical clock | Step 13 / NOT_STARTED | P/video.py, media.py | 1080×1350/30fps/H.264/yuv420p/duration/decode/ten scenes/first 15 seconds | master/web videos; keyframes; video.json | Approved actual result and conditional response |
| P6-R14 Five-tab portable report | Attribution/private-material boundary | Definitions/actual evidence | Step 14 / NOT_STARTED | P/reporting.py | Tabs, links, null/negative results, privacy and truthful labels | report/index.html; screenshots; report.json | Approved claims only; no Live/Production |
| P6-R15 Hardened release | Rights and source unchanged | Full chain validated | Step 15 / NOT_STARTED | P/release.py, pipeline.py, evidence.py | Regression, restart, full decode, stale evidence, hash-bound review | release.json; public_handoff.json; acceptance record | Only exact approved final claim/artifact set |

## Step 1 concrete implementation trace

P = src/linkedin_visual_labs/projects/p05_traffic_operations_early_warning;
T = tests/projects/p05_traffic_operations_early_warning. All model/validator entries
below are in P/models.py unless identified as loader functions in P/config.py.
Test names are in T/test_contract.py or T/test_config.py. Verification covers typed
declarations and synthetic failure cases only; later analytical obligations stay PLANNED.
All Step 1 rows below are VERIFIED by 149 passing focused cases and the full 1,203-test
run (1,054 retained plus 149 new). No tests failed, errored, skipped or xfailed.
The exact commands, warnings, elapsed times and reviewed file hashes are in
STATE.json under step_1_validation. This verifies no actual source or public claim.

| Requirement | Model / validator | Test evidence |
|---|---|---|
| Identity, business question, strict immutable YAML | ProjectConfig.business_contract; Contract; load_traffic_config | test_checked_in_config_is_unapproved_non_executable_and_deterministic; test_unknown_nested_fields_rejected; test_invalid_yaml_variants |
| Source states, complete rights/review and finite metadata | SourceCandidate.approval_contract; SourceConfig.coherent_source | test_approval_requires_complete_metadata; test_unknown_review_never_approves; test_every_required_right; test_source_strictness |
| Source floor/preference and neutral location | SourceCandidate.approval_contract | test_source_review_states_duration_and_location; test_candidate_complete_synthetic_approval_and_no_maximum |
| Original clock, censoring, windows and samples | AnalysisConfig; MetricsConfig.metric_contract | test_metric_invalid_variants; test_metric_semantics_and_frozen_completeness; test_static_interval_tabs_and_original_time |
| Queue completeness and persistence | QueueOutcomeConfig.complete; RuleConfig.validate_rule; PersistenceConfig.complete_persistence | test_frozen_rule_requires_complete_evidence; test_rule_status_duplicates_and_disjoint_signals |
| Leading warning separation and transitions | WarningConfig.complete; WarningPredicate.compatible_unit; TrafficOperationsConfig.independent_contracts | test_warning_signal_alias_and_outcome_rejection; test_warning_freeze_requires_rationale_transitions_and_provenance |
| Signed/null result and precedence declarations | ResultContract.fixed_precedence | test_enum_vocabularies_and_result_declarations |
| Calibration and physical claim units | CalibrationConfig.physical_evidence; ClaimRecord.publication | test_physical_units_need_calibration; test_physical_claim_without_calibration_is_rejected |
| Enabled-only conditional actions and no-action | ActionConfig.available_only; RecommendationsConfig.unique_actions | test_unavailable_action_not_eligible; test_enabled_action_and_no_action |
| Claim classes, approval evidence, exact hashes | ClaimRecord.publication; EvidenceReference.accepted_hash | test_preview_and_unsupported_never_publish; test_publication_requires_evidence_review_and_caveat; test_claim_hash_binding_and_planned_evidence |
| Privacy fixed prohibitions | PrivacyConfig; strict_boolean | test_privacy_cannot_enable_prohibited_features; test_invalid_yaml_variants |
| PNG, continuous interval, video, final frame, ordered tabs | StaticOutput; SourceInterval.ten_minutes; VideoOutput; OutputConfig | test_static_interval_tabs_and_original_time; test_invalid_video_contract; test_frame_bounds_and_closing_selector; test_cross_contract_source_and_freeze_guards |
| Path containment and no loader writes | project_relative; loader contained_path/validate_references | test_source_path_rejection; test_foreign_config_paths_are_rejected; test_reparse_component_rejected_without_following_target; test_symlink_component_rejected_without_creation; test_evidence_output_category_is_restricted; test_loader_has_no_directory_or_file_side_effects |
| No CV/media/Torch import requirement | loader load_traffic_config | test_import_and_config_without_cv_or_media_runtime |

## Cross-cutting requirements

| Requirement / status | Contract links | Steps | Gate and evidence | Claim consequence |
|---|---|---|---|---|
| P6-X01 Canonical-only workspace / PLANNED | AGENTS, CONTINUITY | 1–15 | Root/branch/status; no prohibited repository | No alternate-source provenance |
| P6-X02 Preview boundary / PLANNED | PRODUCT, OUTPUT | 1, 11–15 | Preview hashes/ignore; release claim audit | PREVIEW_ONLY excluded |
| P6-X03 Privacy / PLANNED | PRODUCT, SOURCE, METRIC | 1–15 | No identity workflows; clip-local IDs; public review | Aggregate supported public evidence |
| P6-X04 Time/calibration / PLANNED | SOURCE, METRIC, OUTPUT | 3–15 | PTS joins, uncertainty, edit map; unit checks | No unsupported physical units/precision |
| P6-X05 Negative results / PLANNED | PRODUCT, METRIC | 1, 9–15 | Eight classifications and signed/null fixtures | No positive-only narrative |
| P6-X06 Causal validation / PLANNED | SOURCE, METRIC | 5–11 | Early independent quality, no future leakage, reserved evaluation | Accuracy requires ground truth |
| P6-X07 Dependency/regression safety / PLANNED | IMPLEMENTATION_PLAN | 2–15 | Lazy imports, preserved Ruff/mypy/pytest/CI | No unverified runtime claims |
| P6-X08 Streaming/storage/restart / PLANNED | SOURCE, OUTPUT | 2–15 | Bounded pilot, hashes, atomic partitions, scoped ignored paths | No stale/incomplete release evidence |
| P6-X09 Conditional action / PLANNED | PRODUCT, SOURCE | 10–15 | Enabled-action evidence and conditional words | P6-C09; impact remains unsupported |
| P6-X10 Checkpoints/authorization / PLANNED | AGENTS, CONTINUITY | 1–15 | A:1–4, B:5–8, C:9–11, D:12–15 plus review | No automatic Git/publication |
| P6-X11 Continuity / PLANNED | STATE, CONTINUITY | Every step | Actual Git/files/manifests/gates checked, not state alone | No invented completion |
| P6-X12 Portfolio separation / PLANNED | OUTPUT, CONTINUITY | 14–15 | Public allowlist and hashes only | Separate future integration task |
| P6-X13 Failed prerequisite stops downstream / PLANNED | All contracts | 3–15 | Source→detection→tracking→events→metrics→warning→claims refusal chain | Diagnostic failure only, no invented measurements |

## Updating traceability

Before each authorized step, record its local plan and required predecessors. During
execution mark only that step IN_PROGRESS. VERIFIED requires test commands/results,
upstream/artifact hashes and reviewer acceptance where required. Failure becomes
BLOCKED with reason, owner and permitted recovery. Preserve earlier evidence; changes
to inputs invalidate affected downstream gates. Do not mark any implementation step
verified because governance documents or a future-output path exist.

## Sub-step 2.B acceptance

Sub-step 2.B VERIFIED: 111 new focused tests; 260 Project 6 tests; 1314
collected and 1314 passed repository-wide, retaining all 1,203 baseline tests.
No failures, errors, skips, deselection, xfails or xpasses. Ruff format/lint, strict
mypy, pip consistency, package version and packaged FFmpeg checks passed.
STATE.json step_2b_validation binds commands, local evidence and reviewed file hashes.
Full Step 2 remains IN_PROGRESS. Sub-step 2.C requires separate explicit authorization.

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

## Recovery 1.D Step 3/4 implementation evidence

P6-R03: aicity_source.py and test_aicity_source.py cover inventory, technical
filters, ordinal ranking, admission and original-time windows. Actual evidence:
aicity_dataset_inventory.json, aicity_episode_review.json, source_manifest.json
and full original-PTS decode. P6-R04: calibration.py and the same focused tests
cover relative normalized geometry; calibration.json and calibration_preview.png
record the actual selected-camera configuration. Final acceptance counts/hashes
are in STATE.aicity_recovery_1d_validation. Source and geometry evidence establish
no final P6-C05-C11 claim. Public source reuse remains restricted.


## FAST-TRACK BLOCK 2 evidence update

Steps 5–7 -> detection.py, tracking.py, events.py, block2.py -> test_block2.py (40 deterministic tests) -> ignored detection/tracking/trajectory manifests and event_reconciliation.json. Internal diagnostic acceptance is separate from independent accuracy and public-release acceptance.


## FAST-TRACK BLOCK 3 amendment

Steps8–11 map to metrics.py, queue_outcome.py, warning.py, recommendations.py, validation.py and evidence.py; source-specific rules live in configs/p05_traffic_operations_early_warning/block3.json. test_block3.py contains46focused cases including an independent lower-level Parquet fixture and tamper rejection. Generated evidence paths are indexed by data/evidence_index.json. Final gate hashes/counts are in STATE.block_3_validation.


## Block4 traceability

Step12 -> presentation.py + visualization.static_image -> coordinate, interval,
title, dimensions and hash-admission tests -> trajectory_map_manifest.json.
Step13 -> visualization.frame + video.py -> ten-scene, null, animation, metadata
tests and real full-decode/keyframe comparisons -> video_manifest.json.
Step14 -> reporting.py -> navigation, responsive structure, conditional wording,
asset containment and missing-asset rejection tests; actual desktop/phone browser
checks -> report_manifest.json + block4_visual_acceptance.json. 35 focused cases.
All gate counts and exact evidence hashes are in STATE.block_4_validation.
