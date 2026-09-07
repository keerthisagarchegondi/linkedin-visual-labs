# Clean-runner CI repair

## Monopoly: release-artifact integration tests

The 33 failing cases are classified as `monopoly_release_artifacts`. Only those
cases are marked; their assertions and test bodies remain intact. Collection
was compared by exact node ID against the original failure list: 33 matches,
no additional cases. The other 164 Monopoly tests remain ordinary CI tests.

Evidence inspected before choosing this boundary:

- `docs/projects/p02_monopoly_ai.md` identifies the completed canonical
  10,000-game tournament, measured statistics, representative game 8721 and
  named-property narrative. It states generated media and scratch artifacts
  are not stored in Git.
- Rules sections 1.53 and 1.56–1.58 require the canonical tournament, validated
  summary, real representative-game events and source hashes; renderers may
  not independently invent/recompute a winner.
- `video_replay.load_replay()` requires `step8_input_manifest.json` and reads
  the referenced representative summary and event bundle. Preview runtime
  also loads previously validated tournament inputs under `validation/`.
  The marked tests assert specific event/property stories and measured metrics.
- The tracked source has a reader but no generator for the Step 8 input
  manifest. Historical commit `d41b71e` introduced these cinematic tests; its
  source likewise contains the manifest reader and no tracked generator.
  Its generic workflow ran plain pytest without preparing release evidence.
- `/outputs/` is ignored, and none of these runtime outputs is tracked. There
  were no existing pytest markers defining the missing clean/release boundary.

A smaller generated fixture would not satisfy this frozen release-evidence
contract. There is no bounded tracked prerequisite-generation command that
restores the complete Step 8 bundle. The fix therefore separates release
validation from ordinary clean-checkout tests rather than fabricating evidence.

Only generic CI adds `-m "not monopoly_release_artifacts"`. Global pytest
defaults still include the tests and still fail when evidence is absent.
The Monopoly project documentation now records prerequisites and the command:

```bash
python -m pytest tests/projects/p02_monopoly_ai -m monopoly_release_artifacts
```

Run that command after restoring the complete validated release bundle with
valid referenced paths. The 33 artifact tests were collected and preserved,
not claimed to pass in the absence of that bundle. No generated outputs were
created or committed to satisfy them.

## Project 5 proof containment

Evaluation previously authorized proofs against the repository checkout root,
although its prediction files used the context's configurable output root.
This rejected a valid proof under an external pytest output directory and also
allowed proofs elsewhere inside the checkout outside the project output root.

`resolve_validation_record()` retains existing repository-relative CLI paths
and absolute run-all paths, then calls the unchanged `ensure_path_within()`
against `context.paths.output_root`. Evaluation validates this boundary before
reading artifacts. Hash/configuration binding and leakage-proof checks are
unchanged. The configured root is the authority, not a root chosen by the
proof-file caller. Pathlib resolution retains traversal/symlink containment.

Tests cover an output root separate from the checkout, rejection of siblings,
checkout-only paths and traversal, and production relative/absolute proof
paths. The existing real-artifact runner/CLI test also passed with pytest's
actual temporary directory outside this checkout. Native pathlib operations
are shared between Windows and POSIX; no OS-specific root strings were added.

## Project 5 FFmpeg discovery

The previous glob and suffix filter required exactly one binary with suffix
empty or `.exe`. Versioned Linux executable names such as
`ffmpeg-linux-x86_64-v7.0.2` have suffix `.2` and were rejected. This caused the
encode and cascading empty-video failures before actual media validation.

The installed imageio-ffmpeg resolver was inspected: `get_ffmpeg_exe()` supports
the package binary but also honors `IMAGEIO_FFMPEG_EXE` and fallback discovery.
The repair invokes that API in a fresh isolated Python subprocess with the
override removed and PATH cleared in a copied environment. Parent environment
and package resolver cache are not mutated. The result must exist and belong
to the installed imageio-ffmpeg distribution's file inventory; a conda/system
fallback outside that inventory is rejected. No binary filename or runner
location is assumed. The executable is then queried for its version.

Existing media validation continues recording the executable, version and
SHA-256. Encoding parameters are unchanged. Tests cover actual installed API
resolution, ignored overrides, unchanged parent environment, Windows and
versioned Linux names, package-ownership rejection, short real H.264 encoding
and full decoding at 1080 × 1350 / 30fps / yuv420p, and the intended empty-file
validation. Temporary media is test-only; accepted videos were not regenerated.

## Scope and commands

The optional `zombie-dl` extra, lightweight base/dev and Dice installs, dedicated
Zombie tests/full strict typing, and dependency of the existing quality status
on that job remain intact. No Project 5 model, result, scenario, presentation
content or continuity-contract change was made.

Commands ran with the existing virtual environment in the authorized checkout:

- `Get-Content`, targeted `rg`, `git log`, `git show` and historical `git grep`
  inspected the request, source/contracts/tests/workflows and manifest history.
  Failed wildcard/missing-file lookups were corrected with explicit source paths.
- Inline Python recorded source/output SHA-256 hashes under ignored
  `.cache/clean-runner-before.json`; deterministic edits and apply_patch made
  the changes. Ruff corrected formatting; strict mypy exposed and guided the
  correction of the distribution-path annotation and test monkeypatch target.
- Focused pytest on portability/presentation/evaluation initially encountered
  sandbox temp-directory permissions. The approved external retry selected
  `portability or packaged or empty_video or short_real_encode or real_artifact_runner`:
  **10 passed, 84 deselected**.
- `pytest tests/projects/p02_monopoly_ai -m monopoly_release_artifacts
  --collect-only --no-cov -q`: **33 selected, 164 deselected**; exact-node audit PASS.
- `pytest --ignore=tests/projects/p04_zombie_escape
  -m "not monopoly_release_artifacts" -o cache_dir=.cache/clean-runner-pytest
  --junitxml=.cache/clean-runner-generic.xml`: approved external run uses the
  normal temporary-directory and FFmpeg environment; detailed results below.
- `pytest tests/projects/p04_zombie_escape/test_optional_api.py
  tests/projects/p04_zombie_escape/test_cli.py tests/test_optional_dependencies.py
  --no-cov --basetemp=.cache/clean-runner-boundary-tmp
  -o cache_dir=.cache/clean-runner-boundary-cache -q`: **10 passed**.
- `ruff format --check .`, `ruff check .`, `mypy --strict src tests`, YAML parsing
  and workflow partition assertions, `git diff --check`, source/output hash
  comparison and Git index/ignore checks form the final audit.

All logs/JUnit output stay under ignored `.cache/clean-runner-*`. No staging,
commit, push, PR merge or publication is authorized or performed.

## Final local results

| Check | Result |
|---|---|
| Generic clean-checkout CI equivalent | 781 passed, 33 deselected, 0 failed, 1 warning; 243.73 seconds |
| All Project 5 tests, included above | 365 passed |
| Bayesian Dice, included above | 173 passed |
| Ordinary Monopoly tests, included above | 164 passed |
| Shared path security tests, included above | 6 passed |
| Optional dependency tests, included above | 2 passed |
| Focused external portability/media/evaluation checks | 10 passed, 84 deselected |
| Zombie CLI/API and dependency boundary run | 10 passed |
| Release-artifact collection | Exactly the 33 original failing Monopoly nodes |
| Ruff formatting/lint | PASS; 217 files already formatted |
| Strict mypy on src/tests | PASS; 193 source files |
| Both workflow YAML files and partition assertions | PASS |
| Git whitespace/index/ignore audit | PASS; staged files 0 |

The single warning is pandas' date-format inference warning from the intentional
invalid-calendar input test. It is not a failed assertion. New tests are the
five cases in `test_portability.py`; the existing missing-package media test now
simulates absent package ownership rather than a particular wheel directory.

Final source/output SHA-256 comparison confirms all canonical Project 5
analytical files and all four manually accepted recruiter artifacts are
unchanged. The artifacts also match `manual_acceptance.json`, whose result
remains PASS. The continuity contract, optional dependency repair and ignore
rules are unchanged. No production artifact was regenerated.

Files changed:

- `.github/workflows/ci.yml`
- `pyproject.toml`
- `docs/projects/p02_monopoly_ai.md`
- `src/linkedin_visual_labs/projects/p25_quick_commerce_control_tower/evaluation.py`
- `src/linkedin_visual_labs/projects/p25_quick_commerce_control_tower/presentation_media.py`
- `tests/projects/p02_monopoly_ai/test_preview_v5.py`
- `tests/projects/p02_monopoly_ai/test_video.py`
- `tests/projects/p02_monopoly_ai/test_video_v5.py`
- `tests/projects/p25_quick_commerce_control_tower/test_presentation.py`

Files added: `tests/projects/p25_quick_commerce_control_tower/test_portability.py`
and this document. HEAD remains `cfb30794686853e68e9a4fd2b44c5f8b2d29a019` on
`project/p26-quick-commerce-control-tower`.

No unexplained local failure remains. The artifact-only Monopoly command still
requires the absent complete release bundle; those tests were not run or claimed
passing. Linux filename behavior is covered by deterministic mocked API results,
and real media tests passed on the installed Windows package. Hosted Linux CI
has not been rerun by this task and is not claimed green.

**READY TO COMMIT CLEAN-RUNNER CI REPAIR**
