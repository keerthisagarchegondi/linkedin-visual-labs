# Project 6 — Dependency decision

## Decision and boundary

Design A is selected: OpenCV-headless plus CPU ONNX Runtime. The isolated
`traffic-cv` extra contains exactly `opencv-python-headless==5.0.0.93` and
`onnxruntime==1.30.0`. The narrow file
`configs/p05_traffic_operations_early_warning/runtime_constraints.txt` repeats only
these validated direct constraints; it is not a repository lock file.
Base dependencies, dev, zombie-dl, metadata and build configuration are preserved.
Ordinary `.[dev]` does not activate traffic-cv. No Project 6 Torch, CUDA, NVIDIA,
Ultralytics, model exporter or tracker requirement is added. Design B is not selected.

Sub-step 2.A installed the actual current base/dev declarations plus both candidates
in separate ignored environments. Windows used CPython 3.13.2 AMD64; Linux used
managed CPython 3.13.15 x86_64, build 20260901, GNU/glibc 2.43 under WSL.
Resolution, installation, NumPy/SciPy/cv2/ORT imports and pip consistency passed on
both. Both reported CPUExecutionProvider and AzureExecutionProvider. CPU is required;
the additional provider is not a GPU requirement. NumPy 2.5.3 and SciPy 1.18.1 were
compatible in that transaction. All 92 shared/platform-resolved packages were reviewed;
shared versions match. Windows adds colorama/tzdata; Linux adds pexpect/ptyprocess.
No prohibited package appeared in either closure.

Local evidence is ignored and must not be committed:
`.cache/p05_traffic_operations_early_warning/windows-py313/evidence/compatibility-summary.json`
and the corresponding Windows/Linux `resolution.json`, `installation.json`,
`runtime-result.json`, `wheel-inventory.json` and `license-review.json` files.
The summary includes exact wheel URLs/tags/hashes, uv 0.12.13 provenance/checksums,
interpreter identities, installed notices and preservation checks. Existence alone
is not renewed acceptance: verify hashes and current declarations when resuming.
Compatibility is installation/import evidence, not whole-repository regression
against every future allowed transitive version. Performance is unmeasured.

## Operational configuration and readiness

`runtime.yaml` is separate from the Step 1 planning YAML. It fixes ONNX_RUNTIME,
HEADLESS and CPUExecutionProvider, forbids GPU/source processing, and keeps the
detector descriptor null. Thread counts are null (runtime defaults, not benchmark
recommendations); explicitly supplied counts must be strict integers 1–64.
No source path, detector URL/checksum, inference threshold or benchmark is seeded.

Frozen operational records and strict loading live in `runtime.py`. Metadata-only
dependency inspection does not import CV libraries or establish native readiness.
RuntimeInventory requires both exact distributions and separately supplied successful
native import/CPU-provider evidence before reporting runtime READY. Sub-step 2.B
does not collect native evidence; explicit doctor behavior belongs to 2.C.
Its snapshot keeps runtime, analysis and model statuses distinct. Analysis remains
BLOCKED even when runtime is READY: approved source, acquired/hash-validated detector,
geometry/calibration and later gates are absent. A descriptor is metadata, not proof
of artifact acquisition or approval. No detector has been selected or acquired;
selection/acquisition remains Step 5. Model licensing is unresolved.
Tracker remains NOT_IMPLEMENTED with STEP_6 ownership; the ByteTrack-compatible
adapter and its provenance are deferred to Step 6.

## Paths and tools

TrafficPaths requires an explicit absolute repository root, validates the checkout's
pyproject identity and package directory, and never searches parents for another
clone. Explicit fixture/CI checkouts can be injected. Known prohibited roots and
lexical traversal, Windows trailing-dot/space aliases and UNC/device roots are
rejected before inspecting their contents. Every path lookup
checks existing symlink/reparse components, including root ancestry, before following
targets. Fixed Project 6 areas isolate raw, processed, output/data/images/videos/report/
manifests, weights, model cache and temporary cache. Helpers create no directories,
open no source/model, and do not expand Step 1 evidence-reference permissions.
These checks are not a defense against concurrent hostile filesystem replacement;
later actual file operations must revalidate immediately before opening.

The explicit packaged FFmpeg resolver follows the repository's ownership/version/hash
pattern without importing Project 5. It enumerates imageio-ffmpeg's installed binary
records rather than calling an API that can fall back to another executable. Exactly
one existing unredirected package-owned binary is required. It executes only `-version`
with a bounded timeout, clears PATH and IMAGEIO_FFMPEG_EXE in the child environment,
and records version, SHA-256 and package provenance. Imports and config loading do
not invoke the resolver. No encoding or source probing occurs.

ffprobe remains NOT_CONFIGURED. A future explicit absolute reference plus hash can
be represented, but stays BLOCKED until separate deterministic verification is
implemented and approved; this scaffold never executes it. Original-PTS probing
and frame pairing remain outstanding later work, not satisfied by FFmpeg version.

## Validation and next boundary

Focused tests cover strict configuration, paths/redirects, runtime versus analysis,
metadata presence/absence, packaged-tool success/failure/timeout, descriptor safety,
and subprocess import blocking. Dependency tests check exact extras/constraints,
preserve Zombie's optional declaration, and traverse active installed base/dev
metadata without network or optional CV imports. Ordinary tests do not depend on
ignored compatibility evidence. Final counts and gate commands belong to STATE.json.

No CLI registration or workflow change belongs to 2.B. Full Step 2 remains IN_PROGRESS.
Sub-step 2.C requires separate explicit authorization; Step 3 remains unstarted.

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
