# Optional PyTorch CI repair

The reported Bayesian Dice and generic CI jobs both exhausted runner disk during
pip installation, before tests began. Both installed `.[dev]`, which inherited
the universal `project.dependencies` entry `torch>=2.6`. On Linux that default
distribution brought in the CUDA stack. This was a dependency-boundary failure,
not a Project 5 model or test failure.

Source/test import inspection found PyTorch only in Zombie Escape
(`p04_zombie_escape`, historically Project 2): `dl_model.py`, `dl_tensors.py`,
and their `dl_pipeline.py` consumers. Direct test imports occur in
`test_dl_model.py` and `test_dl_tensors.py`; `test_dl_pipeline.py` depends on
them indirectly. Bayesian Dice, Monopoly and Project 5 do not use PyTorch.
The Zombie package public API and CLI previously imported the DL modules eagerly,
making unrelated commands depend on torch as well.

## Repair and retained coverage

- Move the unchanged requirement `torch>=2.6` into the `zombie-dl` extra.
  Base and `dev` retain all other dependencies and shared developer tools.
- Preserve public DL exports with lazy loading and static type-checking imports.
  Load DL command dependencies only when those commands execute. Missing torch
  produces an actionable `.[zombie-dl]` installation message.
- Generic CI installs `.[dev]`, verifies torch is absent, and runs all tests
  outside Zombie. A dedicated `zombie-dl` job installs CPU PyTorch first from
  the official CPU index, then `.[dev,zombie-dl]`, checks that CUDA is absent,
  runs all Zombie tests, and runs full strict mypy on `src tests`.
- The existing Python quality checks job depends on `zombie-dl`, retaining the
  relocated checks behind the existing quality status. It runs even if that job
  fails and explicitly requires its success, avoiding a skipped required status.
  No tests are dropped,
  skipped, xfailed or weakened. Formatting and lint still cover the repository.
- Bayesian Dice remains on `.[dev]`, verifies torch is absent and retains its
  tests and deterministic schedule validation. Its duplicate full-repository
  mypy invocation is centralized in the always-triggered generic CI workflow's
  dedicated job. Both workflows retain their event triggers.
- Codespaces already installs `.[dev]`; its configuration needs no edit. README
  documents the optional CPU installation for full tests/typing and DL work.

## Local validation

Fresh pip resolution with `--ignore-installed` for editable `.[dev]` succeeded:
89 packages, zero torch, triton, cuda-toolkit, nvidia-* or cuda-* packages.
This was a Windows Python 3.13 dry-run, not a claim of a hosted Linux CI run.
Built package metadata evaluated with Linux markers also excludes torch for
base/dev and includes `torch>=2.6; extra == "zombie-dl"` for the optional extra.
The editable `.[dev,zombie-dl]` dry-run succeeded and explicitly resolved the
requirement to the already installed torch 2.14.0. No packages were installed.
The CPU index follows https://docs.pytorch.org/get-started/locally/.

| Check | Result |
|---|---|
| Generic CI test partition | 773 passed, 36 failed, 1 warning |
| Zombie CI test partition, before new API regression | 198 passed, 1 failed |
| Import/CLI/API regression run | 17 passed |
| Bayesian Dice tests, included in generic partition | 173 passed |
| Project 5 tests, included in generic partition | 360 passed |
| Four environment-specific failed tests, approved external retry | 4 passed, 1 pytest cache-permission warning |
| Bayesian Dice deterministic schedule | PASS |
| Both workflow YAML files | Parsed and job/test partition validated |
| Ruff format and lint | PASS, 215 files already formatted |
| Full strict mypy | PASS, 192 source files |
| Git whitespace check | PASS |

All 37 initial failing node IDs exactly match the previous Project 5 validation
record: 33 missing ignored Monopoly production/runtime prerequisites, two common
FFmpeg tests, one Zombie FFmpeg test, and the repository-local pytest temp-path
test. The four environment cases pass externally. The 33 Monopoly prerequisites
remain unresolved and may block subsequent CI after installation succeeds.
No runtime artifacts were fabricated, tracked or committed to conceal this.
This repair does not claim that hosted PR CI is already green.

New tests cover dependency metadata and complementary CI coverage, import/CLI
execution with torch explicitly blocked (including every Project 5 module),
the missing-extra error, and identity of the existing public DL implementations
when the optional dependency is available. Existing tests were not edited.

All canonical Project 5 analytical files and all generated outputs retained
their before-repair SHA-256 hashes. The four accepted recruiter artifacts still
match `manual_acceptance.json`; Step 6D manual acceptance remains PASS. Project 5
source, tests, configuration, validation documentation and continuity contract
are unchanged. No retraining or production-output regeneration occurred.

## Command ledger

All commands ran in the authorized checkout with its `.venv/Scripts/python.exe`.
Git reads used a process-only `-c safe.directory` override.

- `Get-Content`, `rg` and file listings inspected the request, pyproject, source
  and test torch imports, both workflows, README, devcontainer Dockerfile,
  post-create script and configuration, and affected public API/CLI modules.
- Git status/diff and an inline Python SHA-256 snapshot established the clean
  starting tree and protected source/output hashes.
- Deterministic Python edits and `apply_patch` updated the six existing files
  and added the three files listed below. Early regression runs exposed and
  corrected an incomplete lazy-import edit and a missing test-partition edit;
  the final regressions pass.
- `python -m pip install --dry-run --ignore-installed --no-build-isolation
  --report .cache/ci-repair-dev.json -e ".[dev]"`: sandbox network denied;
  approved external retry passed, 89 packages and no GPU framework dependencies.
- `python -m pip install --dry-run --no-build-isolation --report
  .cache/ci-repair-zombie-deps.json -e ".[dev,zombie-dl]"`: passed externally.
- `python -m pytest --ignore=tests/projects/p04_zombie_escape
  --basetemp=.cache/ci-repair-generic-tmp
  --junitxml=.cache/ci-repair-generic.xml`: results in table.
- `python -m pytest tests/projects/p04_zombie_escape --no-cov
  --basetemp=.cache/ci-repair-zombie-tmp
  --junitxml=.cache/ci-repair-zombie.xml`: results in table.
- `python -m pytest tests/test_optional_dependencies.py
  tests/projects/p04_zombie_escape/test_optional_api.py tests/test_cli.py
  tests/projects/p25_quick_commerce_control_tower/test_cli.py --no-cov -q`:
  17 passed.
- Focused external pytest retry ran the two common animation failures, Zombie
  FFmpeg command test and root-discovery temp-path test: 4 passed.
- `python -m linkedin_visual_labs.projects.p01_bayesian_dice.pair_video schedule`
  plus JSON assertions: exit 0, no stderr, 1,350 monotonic frames at 30 fps,
  first roll 1 and last roll 10,000.
- `python -m ruff format --check .`, `python -m ruff check .`,
  `python -m mypy --strict src tests`, `git diff --check`: passed.
- Inline Python parsed YAML, pip reports and JUnit results, matched all failure
  IDs to prior documentation, and checked source/output hashes, Git index and
  ignore policy. Logs and reports are local-only under ignored `.cache/ci-repair-*`.

Files changed: `pyproject.toml`, `.github/workflows/ci.yml`,
`.github/workflows/p01-bayesian-dice.yml`, `README.md`, Zombie `__init__.py` and
`cli.py`. Files added: `tests/test_optional_dependencies.py`,
`tests/projects/p04_zombie_escape/test_optional_api.py`, and this document.
No staging, commit, push, PR merge or publication was performed.
