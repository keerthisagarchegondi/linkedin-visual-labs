# Repository operating rules

These rules apply to all work in this repository.

- Work only inside `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
- Never modify `D:\linkedin-visual-labs`.
- Never modify unrelated project packages.
- Never access ChangeGraph or job_hunter.
- Preserve the existing repository architecture.
- Use complete, coherent deterministic file edits.
- Preserve all existing quality gates.
- Use full type annotations for Python implementation.
- Use fixed deterministic seeds.
- Keep raw datasets, caches, fitted models, preview media, and generated large media out of Git.
- Never weaken or delete tests merely to make checks pass.
- Run the relevant tests after every implementation step.
- Report every file created or changed.
- Report every command run and its result.
- Stop after the explicitly requested implementation step.
- Do not stage, commit, push, force-push, or rewrite Git history unless explicitly instructed later.
- Keep `reference/project5/` local-only and unstaged. Preserve its exact exclusion in `.gitignore`; do not broaden it to unrelated reference content.
- Do not modify `contracts/repository_continuity.json` unless an existing continuity gate explicitly requires a compatible Project 5 update and the reason is explained first. Preserve repository identity, ancestry, and all earlier-project baselines.

## Project 5 identity and scope

- Active project branch: `project/p26-quick-commerce-control-tower`.
- Internal package: `p25_quick_commerce_control_tower`.
- The approved implementation plan is `docs/projects/p25_quick_commerce_control_tower/IMPLEMENTATION_PLAN.md`.
- The authoritative analytical and recruiter-facing narrative contract is `docs/projects/p25_quick_commerce_control_tower/PRODUCT_CONTRACT.md`.
- A plan describes future work; it does not authorize that work. Implement only the step explicitly requested by the user.

## Project 6 identity and canonical workspace

The Project 5 section above remains applicable to Project 5. For Project 6, use the
following identity and scope; do not apply the Project 5 branch as its active branch.

- Display name: Project 6 — Traffic Operations Early-Warning System.
- Original master-catalog ID: 5 — Traffic Vision and Congestion Warning.
- Internal package: `p05_traffic_operations_early_warning`.
- Required branch: `project/p05-traffic-operations-early-warning`.
- Only workspace: `D:\linkedin-visual-labs-git\linkedin-visual-labs`.
- Never access or use `D:\linkedin-visual-labs`, `D:\ChangeGraph`,
  `D:\job_hunter`, or `D:\My-portfolio-Keerthi` during Project 6 core work.
- The old `D:\linkedin-visual-labs` clone is prohibited as a fallback, comparison
  source, or alternate implementation workspace. Do not search for another clone.
- Future portfolio integration belongs to a separately rooted, explicitly authorized
  task. This workspace may prepare only the approved public artifact handoff.
- Authoritative Project 6 files are under
  `docs/projects/p05_traffic_operations_early_warning/`. Read its implementation,
  product, source, metric, output, traceability, claim, state, and continuity files.

## Project 6 execution discipline and repository safety

- Plan before each step; execute only one explicitly authorized step at a time.
- Preserve numbered Project 6 Steps 1–15 and their independent acceptance gates.
- Do not begin the next step until the current gate passes and the next step is
  explicitly authorized. Stop after the requested step.
- Governance/documentation setup is separate from implementation Step 1. Creating
  planning contracts does not start or complete Step 1.
- Resume from actual Git state, contracts, `STATE.json`, `CONTINUITY.md`, manifests,
  and gate evidence. Do not trust conversation memory or state assertions alone.
- Verify the canonical root, expected branch, dirty state, and actual interfaces
  before editing. Stop on a wrong branch; do not switch automatically.
- Preserve architecture, existing projects, quality gates, and valid tests/contracts.
- Prefer coherent full-file or syntax-aware changes over fragile text replacement.
- Do not bulk-format unrelated files or modify unrelated projects for convenience.
- Never weaken contracts/tests or remove failing tests to obtain a passing result.
- Use fully annotated Python modules and deterministic configuration/seeds.

## Project 6 truthfulness, time, and analytical independence

- Never fabricate airport, pickup-zone, company, or source-location context,
  metrics, timestamps, lead time, model/tracking accuracy, operational impact,
  production deployment, or live monitoring.
- Never overlay invented signs onto unrelated footage as observed reality.
- `reference/project6/previews/` is a layout/story reference only. All analytical
  preview values are `PREVIEW_ONLY`; never copy them into final configuration or
  release claims. AI-generated/preview imagery is not observed source data.
- Do not tune thresholds solely to force a positive early-warning result. Negative,
  late, zero-lead, inconclusive, and source-limited outcomes remain reportable.
- Every important public claim needs classified, validated, traceable evidence.
- Source ownership/reuse permission must pass before real inference; do not acquire
  random substitute footage or infer permission from public accessibility.
- All analytics use original source timestamps. Accelerated playback is presentation
  only and must never rescale dwell, throughput, queue/warning persistence,
  warning timestamp, visible-queue timestamp, or lead time.
- Sampling changes require quality/uncertainty revalidation; they do not change the
  analytical clock. Never backdate a persistence-completion timestamp.
- Define visible queue independently from warning. Warning primarily uses leading
  deterioration, never a restatement of the complete visible-queue rule.
- Use counts and normalized image-plane movement. Exact MPH, feet, lane-mile
  density, and other physical distances require genuine documented calibration.
- Recommendations are conditional, evidence-linked, and restricted to configured
  available levers; unsupported context requires illustrative wording or review.
- Failed source approval blocks calibration/inference; failed detection quality
  blocks tracking; failed tracking quality blocks final dwell/throughput; invalid
  events block final metrics; invalid metrics block warning; unsupported claims
  block public visual release. Keep diagnostic failures explicit.

## Project 6 privacy and dependency safety

- Vehicle-only analytical classes where applicable; aggregate public metrics.
- Temporary anonymous track IDs are analytical only, nonpersistent, and local to
  one approved clip. Do not make identifiable plates/faces a public focal point.
- Do not implement facial recognition, face identification, license-plate OCR,
  driver identity, persistent vehicle identity, cross-camera re-identification,
  external vehicle lookup, or enforcement/citation workflows.
- Prefer CPU-first operation; do not require a GPU.
- Isolate heavy CV dependencies from ordinary `.[dev]` installation and generic CI.
  Do not leak CUDA dependencies. Use lazy imports so ordinary repository commands
  remain functional without the Project 6 CV extra.
- Verify actual Python 3.13 Windows/Linux compatibility before accepting a runtime;
  do not install both proposed stacks blindly or assume user PATH contains FFmpeg.

## Project 6 Git and artifact safety

- Keep raw footage, downloaded weights, model caches, temporary extracted frames,
  large generated outputs, private source-license records, and local execution
  logs out of Git. A specific small model artifact requires explicit policy approval.
- Keep Project 6 previews local and ignored; preserve the exact Project 5 exclusion.
- Do not delete ignored files or untrack existing files automatically.
- Checkpoints A/B/C/D follow Steps 1–4/5–8/9–11/12–15 respectively, with final review
  before D. A checkpoint or plan does not authorize Git actions.
- Do not stage, commit, push, or create a PR unless a later instruction explicitly
  authorizes that Git action. Preserve the existing global continuity contract.
