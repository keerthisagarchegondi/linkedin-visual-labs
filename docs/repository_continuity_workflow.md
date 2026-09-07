# Repository Continuity Workflow

This repository is developed from two working copies:

- local Windows clone: `D:\linkedin-visual-labs-git\linkedin-visual-labs`
- GitHub Codespaces clone: `/workspaces/linkedin-visual-labs`

They are two clones of the same GitHub repository. `origin` is the only transfer
mechanism. Never copy changed source files manually between them and never work
in both clones concurrently.

## Continuity files

- `scripts/continuity_gate.py` verifies repository identity, Git synchronization,
  Python/venv state, baseline ancestry, manifest validity, path safety, and an
  optional cross-clone fingerprint.
- `scripts/update_continuity.py` updates the deterministic semantic checkpoint.
- `contracts/repository_continuity.json` stores stable repository identity,
  minimum completed-project baseline, the latest semantic checkpoint, and the explicit
  Windows checkout path in `environment_roots.windows`. The path is configuration,
  not a reset of repository identity, ancestry or project baselines.
- `tests/test_repository_continuity.py` validates the manifest and both CLI tools
  without network access.

## Strict commands

### Windows

```powershell
Set-Location "D:\linkedin-visual-labs-git\linkedin-visual-labs"
& ".\.venv\Scripts\Activate.ps1"
python scripts\continuity_gate.py --expected-branch "<branch>"
```

### Codespaces

```bash
cd /workspaces/linkedin-visual-labs
source .venv/bin/activate
python scripts/continuity_gate.py --expected-branch "<branch>"
```

A transfer-safe result requires:

```text
TRANSFER_SAFE=YES
CONTINUITY_GATE=PASS
```

## New branch before first push

Use `--allow-no-upstream` only before the first `git push -u origin <branch>`.
The result is diagnostic and never transfer-safe. After pushing, rerun without
relaxation.

## Semantic checkpoints

Update after a meaningful completed sub-step, then stage the manifest with the
implementation commit. The manifest must remain deterministic and contain no
machine path, timestamp, hostname, username, or environment ID.

## Switching clones

In the active clone:

1. finish the requested sub-step;
2. update the continuity checkpoint;
3. run required gates;
4. stage an explicit allowlist;
5. commit and push;
6. run the strict gate;
7. record the fingerprint.

In the inactive clone:

1. prove no local work exists;
2. fetch and prune;
3. switch to the same branch;
4. pull with `--ff-only`;
5. activate the root `.venv`;
6. run the gate with `--expected-fingerprint`;
7. continue only if the fingerprint matches.

## Merge flow

1. feature branch clean, tested, committed, pushed;
2. strict feature-branch gate passes;
3. switch to clean synchronized `main`;
4. merge with `--no-ff`;
5. run appropriate post-merge gates;
6. push `main`;
7. fetch and prove local `main == origin/main`;
8. run strict main gate;
9. synchronize the inactive clone before future work.

## Safety rules

Never use `git add .`, `git add -A`, force push, history rewriting,
`git reset --hard`, or `git clean -fd` unless an explicitly authorized recovery
requires it. Use repository-local Git identity and `git --no-pager`. Normalize
text provenance across CRLF/LF and reject case-colliding tracked paths.
