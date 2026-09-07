"""Strict local/Codespaces continuity gate for LinkedIn Visual Labs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

EXPECTED_REPOSITORY_KEY = "github.com/keerthisagarchegondi/linkedin-visual-labs"
EXPECTED_MANIFEST_KEY = "keerthisagarchegondi/linkedin-visual-labs"
EXPECTED_ORIGIN_URL = "https://github.com/keerthisagarchegondi/linkedin-visual-labs.git"
EXPECTED_DEFAULT_BRANCH = "main"
BASELINE_COMMIT = "0557673c790dc900db7293586ce96931ede40c96"
MANIFEST_RELATIVE_PATH = Path("contracts/repository_continuity.json")
REQUIRED_PATHS = (
    Path("README.md"),
    Path("pyproject.toml"),
    Path("src/linkedin_visual_labs"),
    Path("tests"),
    Path(".github/workflows/ci.yml"),
    Path("scripts/continuity_gate.py"),
    Path("scripts/update_continuity.py"),
    Path("tests/test_repository_continuity.py"),
    Path("docs/repository_continuity_workflow.md"),
    MANIFEST_RELATIVE_PATH,
)


class ContinuityError(RuntimeError):
    """Raised when a continuity check cannot be evaluated."""


@dataclass(frozen=True)
class CheckResult:
    """One continuity check result."""

    name: str
    passed: bool
    detail: str


class Recorder:
    """Collect and display continuity checks."""

    def __init__(self) -> None:
        self._results: list[CheckResult] = []

    def add(self, name: str, passed: bool, detail: str) -> None:
        result = CheckResult(name=name, passed=passed, detail=detail)
        self._results.append(result)
        marker = "PASS" if passed else "FAIL"
        print(f"[{marker}] {name}: {detail}")

    @property
    def failures(self) -> tuple[CheckResult, ...]:
        return tuple(result for result in self._results if not result.passed)


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command with stable decoded output."""

    completed = subprocess.run(
        tuple(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if check and completed.returncode != 0:
        rendered = " ".join(command)
        message = completed.stderr.strip() or completed.stdout.strip()
        raise ContinuityError(f"Command failed ({completed.returncode}): {rendered}\n{message}")

    return completed


def run_git(
    root: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run Git from the repository root."""

    return run_command(
        ("git", "-C", str(root), *arguments),
        cwd=root,
        check=check,
    )


def discover_repository_root() -> Path:
    """Resolve and verify the repository root from this script."""

    script_root = Path(__file__).resolve().parents[1]
    git_root_result = run_git(script_root, "rev-parse", "--show-toplevel")
    git_root = Path(git_root_result.stdout.strip()).resolve()

    if script_root != git_root:
        raise ContinuityError(
            "scripts/continuity_gate.py must live directly below the repository "
            f"root: script_root={script_root}; git_root={git_root}"
        )

    return git_root


def normalize_repository_url(value: str) -> str:
    """Normalize common HTTPS and SSH GitHub URL forms."""

    normalized = value.strip().replace("\\", "/")
    prefixes = ("https://", "http://", "ssh://git@", "ssh://")

    for prefix in prefixes:
        if normalized.casefold().startswith(prefix.casefold()):
            normalized = normalized[len(prefix) :]
            break

    if normalized.casefold().startswith("git@github.com:"):
        normalized = "github.com/" + normalized.split(":", maxsplit=1)[1]
    elif normalized.casefold().startswith("git@"):
        normalized = normalized[4:]

    normalized = normalized.rstrip("/")

    if normalized.casefold().endswith(".git"):
        normalized = normalized[:-4]

    return normalized.casefold()


def same_path(left: Path, right: Path) -> bool:
    """Compare resolved paths using platform case behavior."""

    left_text = str(left.resolve())
    right_text = str(right.resolve())

    if os.name == "nt":
        return left_text.casefold() == right_text.casefold()

    return left_text == right_text


def expected_environment_root(manifest: dict[str, Any], *, platform: str | None = None) -> Path:
    """Return the contracted root for the current platform."""

    if (os.name if platform is None else platform) == "nt":
        roots = manifest.get("environment_roots")
        value = roots.get("windows") if isinstance(roots, dict) else None
        if not isinstance(value, str) or not PureWindowsPath(value).is_absolute():
            raise ContinuityError("environment_roots.windows must be an absolute checkout path")
        return Path(value)

    return Path("/workspaces/linkedin-visual-labs")


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Return stable JSON bytes independent of whitespace and line endings."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def load_manifest(root: Path) -> dict[str, Any]:
    """Load and minimally validate the continuity manifest."""

    path = root / MANIFEST_RELATIVE_PATH
    payload = json.loads(path.read_text(encoding="utf-8-sig"))

    if not isinstance(payload, dict):
        raise ContinuityError("Continuity manifest must be a JSON object.")

    return payload


def tracked_paths(root: Path) -> tuple[str, ...]:
    """Return tracked repository paths with canonical separators."""

    return tuple(
        line.strip().replace("\\", "/")
        for line in run_git(root, "ls-files").stdout.splitlines()
        if line.strip()
    )


def case_collisions(paths: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """Find tracked paths that collide on case-insensitive filesystems."""

    grouped: dict[str, list[str]] = {}

    for path in paths:
        grouped.setdefault(path.casefold(), []).append(path)

    return {key: tuple(sorted(values)) for key, values in grouped.items() if len(set(values)) > 1}


def parse_ahead_behind(value: str) -> tuple[int, int]:
    """Parse `git rev-list --left-right --count HEAD...@{u}`."""

    fields = value.split()

    if len(fields) != 2:
        raise ValueError(f"Unexpected ahead/behind output: {value!r}")

    return int(fields[0]), int(fields[1])


def checkpoint_label(payload: dict[str, Any]) -> str:
    """Render the semantic checkpoint compactly."""

    checkpoint = payload.get("checkpoint")

    if not isinstance(checkpoint, dict):
        return "<missing checkpoint>"

    return (
        f"Project {checkpoint.get('project_number')} / "
        f"{checkpoint.get('project_id')} / step {checkpoint.get('step')} / "
        f"sub-step {checkpoint.get('substep')} / "
        f"{checkpoint.get('status')}: {checkpoint.get('label')}"
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Verify that a LinkedIn Visual Labs clone is safe, synchronized, "
            "and semantically continuous with its peer clone."
        )
    )
    parser.add_argument(
        "--expected-branch",
        required=True,
        help="Branch that must be checked out.",
    )
    parser.add_argument(
        "--expected-fingerprint",
        help="Fingerprint that must match the other clone during handoff.",
    )
    parser.add_argument(
        "--allow-no-upstream",
        action="store_true",
        help=(
            "Diagnostic exception for a new branch before its first push. "
            "The result is never transfer-safe."
        ),
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Diagnostic only; the result is never transfer-safe.",
    )
    return parser


def main() -> int:
    """Run the continuity gate."""

    arguments = build_parser().parse_args()
    recorder = Recorder()

    try:
        root = discover_repository_root()
    except (ContinuityError, OSError) as exc:
        print(f"[FAIL] repository root: {exc}")
        return 1

    print("=" * 92)
    print("LINKEDIN VISUAL LABS - REPOSITORY CONTINUITY GATE")
    print("=" * 92)
    print(f"Root: {root}")
    print(f"Expected branch: {arguments.expected_branch}")
    print()

    try:
        expected_root = expected_environment_root(load_manifest(root))
        recorder.add(
            "environment root",
            same_path(root, expected_root),
            f"actual={root}; expected={expected_root}",
        )
    except (ContinuityError, OSError, ValueError, TypeError) as exc:
        recorder.add("environment root", False, str(exc))

    remotes: tuple[str, ...] = ()

    try:
        remotes = tuple(
            line.strip() for line in run_git(root, "remote").stdout.splitlines() if line.strip()
        )
        recorder.add("single remote", remotes == ("origin",), f"remotes={remotes}")
    except ContinuityError as exc:
        recorder.add("single remote", False, str(exc))

    if remotes == ("origin",):
        try:
            origin = run_git(root, "remote", "get-url", "origin").stdout.strip()
            recorder.add(
                "origin repository",
                normalize_repository_url(origin) == EXPECTED_REPOSITORY_KEY,
                f"origin={origin}",
            )
        except ContinuityError as exc:
            recorder.add("origin repository", False, str(exc))
    else:
        recorder.add("origin repository", False, "origin is not the only remote")

    try:
        run_git(root, "fetch", "--prune", "origin")
        recorder.add("fetch origin", True, "git fetch --prune origin succeeded")
    except ContinuityError as exc:
        recorder.add("fetch origin", False, str(exc))

    branch_result = run_git(
        root,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
        check=False,
    )
    attached = branch_result.returncode == 0
    branch = branch_result.stdout.strip() if attached else "<detached>"
    recorder.add("attached HEAD", attached, f"branch={branch}")
    recorder.add(
        "expected branch",
        branch == arguments.expected_branch,
        f"actual={branch}; expected={arguments.expected_branch}",
    )

    status = run_git(
        root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ).stdout
    clean = not status.strip()
    recorder.add(
        "working tree",
        clean or arguments.allow_dirty,
        "clean" if clean else "dirty (allowed for diagnosis only)",
    )

    upstream_result = run_git(
        root,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{u}",
        check=False,
    )
    upstream_exists = upstream_result.returncode == 0
    upstream = upstream_result.stdout.strip() if upstream_exists else "<none>"
    recorder.add(
        "upstream",
        upstream_exists or arguments.allow_no_upstream,
        upstream,
    )

    ahead = 0
    behind = 0

    if upstream_exists:
        try:
            counts = run_git(
                root,
                "rev-list",
                "--left-right",
                "--count",
                "HEAD...@{u}",
            ).stdout.strip()
            ahead, behind = parse_ahead_behind(counts)
            recorder.add(
                "upstream synchronization",
                ahead == 0 and behind == 0,
                f"ahead={ahead}; behind={behind}; upstream={upstream}",
            )
        except (ContinuityError, ValueError) as exc:
            recorder.add("upstream synchronization", False, str(exc))
    elif arguments.allow_no_upstream:
        recorder.add(
            "upstream synchronization",
            True,
            "not evaluated before first push",
        )
    else:
        recorder.add("upstream synchronization", False, "no upstream configured")

    recorder.add(
        "Python version",
        sys.version_info[:2] == (3, 13),
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )

    expected_venv = root / ".venv"
    active_venv = sys.prefix != sys.base_prefix and same_path(Path(sys.prefix), expected_venv)
    recorder.add(
        "root virtual environment",
        active_venv,
        f"sys.prefix={sys.prefix}; expected={expected_venv}",
    )

    git_name = run_git(root, "config", "--local", "--get", "user.name", check=False)
    git_email = run_git(
        root,
        "config",
        "--local",
        "--get",
        "user.email",
        check=False,
    )
    identity_ok = (
        git_name.returncode == 0
        and git_email.returncode == 0
        and git_name.stdout.strip() == "Keerthi Sagar Chegondi"
        and git_email.stdout.strip() == "keerthisagarchegondi@gmail.com"
    )
    recorder.add(
        "repository-local Git identity",
        identity_ok,
        f"name={git_name.stdout.strip()!r}; email={git_email.stdout.strip()!r}",
    )

    missing = tuple(path.as_posix() for path in REQUIRED_PATHS if not (root / path).exists())
    recorder.add(
        "required repository files",
        not missing,
        "all present" if not missing else f"missing={missing}",
    )

    try:
        tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8-sig"))
        recorder.add("pyproject.toml", True, "valid TOML")
    except (OSError, tomllib.TOMLDecodeError) as exc:
        recorder.add("pyproject.toml", False, str(exc))

    manifest: dict[str, Any] = {}

    try:
        manifest = load_manifest(root)
        repository = manifest.get("repository")
        baseline = manifest.get("minimum_baseline")
        checkpoint = manifest.get("checkpoint")
        manifest_valid = (
            manifest.get("schema_version") == "1.0"
            and isinstance(repository, dict)
            and repository.get("key") == EXPECTED_MANIFEST_KEY
            and repository.get("origin_url") == EXPECTED_ORIGIN_URL
            and repository.get("default_branch") == EXPECTED_DEFAULT_BRANCH
            and isinstance(baseline, dict)
            and baseline.get("commit") == BASELINE_COMMIT
            and isinstance(checkpoint, dict)
        )
        recorder.add(
            "continuity manifest",
            manifest_valid,
            checkpoint_label(manifest),
        )
    except (ContinuityError, OSError, ValueError, TypeError) as exc:
        recorder.add("continuity manifest", False, str(exc))

    tracked = tracked_paths(root)
    tracked_set = set(tracked)
    recorder.add(
        "manifest tracked",
        MANIFEST_RELATIVE_PATH.as_posix() in tracked_set,
        MANIFEST_RELATIVE_PATH.as_posix(),
    )

    collisions = case_collisions(tracked)
    recorder.add(
        "case-insensitive path safety",
        not collisions,
        "no collisions" if not collisions else json.dumps(collisions, sort_keys=True),
    )

    baseline_origin = run_git(
        root,
        "merge-base",
        "--is-ancestor",
        BASELINE_COMMIT,
        "origin/main",
        check=False,
    )
    recorder.add(
        "Project 3 baseline in origin/main",
        baseline_origin.returncode == 0,
        BASELINE_COMMIT,
    )

    baseline_head = run_git(
        root,
        "merge-base",
        "--is-ancestor",
        BASELINE_COMMIT,
        "HEAD",
        check=False,
    )
    recorder.add(
        "Project 3 baseline in HEAD",
        baseline_head.returncode == 0,
        BASELINE_COMMIT,
    )

    unstaged = run_git(root, "diff", "--check", check=False)
    recorder.add(
        "unstaged whitespace",
        unstaged.returncode == 0,
        unstaged.stdout.strip() or unstaged.stderr.strip() or "clean",
    )

    staged = run_git(root, "diff", "--cached", "--check", check=False)
    recorder.add(
        "staged whitespace",
        staged.returncode == 0,
        staged.stdout.strip() or staged.stderr.strip() or "clean",
    )

    head = "<unavailable>"
    tree = "<unavailable>"
    fingerprint = "<unavailable>"

    try:
        head = run_git(root, "rev-parse", "HEAD").stdout.strip()
        tree = run_git(root, "rev-parse", "HEAD^{tree}").stdout.strip()

        if manifest:
            manifest_hash = hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()
            fingerprint_payload = "\n".join(
                (EXPECTED_REPOSITORY_KEY, branch, head, tree, manifest_hash)
            ).encode("utf-8")
            fingerprint = hashlib.sha256(fingerprint_payload).hexdigest()
    except ContinuityError as exc:
        recorder.add("continuity fingerprint", False, str(exc))

    if arguments.expected_fingerprint:
        recorder.add(
            "expected fingerprint",
            fingerprint == arguments.expected_fingerprint,
            f"actual={fingerprint}; expected={arguments.expected_fingerprint}",
        )

    transfer_safe = (
        not recorder.failures
        and clean
        and upstream_exists
        and ahead == 0
        and behind == 0
        and not arguments.allow_dirty
        and not arguments.allow_no_upstream
    )

    print()
    print("-" * 92)
    print(f"BRANCH={branch}")
    print(f"HEAD={head}")
    print(f"TREE={tree}")
    print(f"UPSTREAM={upstream}")
    print(f"CHECKPOINT={checkpoint_label(manifest) if manifest else '<unavailable>'}")
    print(f"CONTINUITY_FINGERPRINT={fingerprint}")
    if arguments.expected_fingerprint:
        print(
            "EXPECTED_FINGERPRINT_MATCH="
            f"{'YES' if fingerprint == arguments.expected_fingerprint else 'NO'}"
        )
    print(f"TRANSFER_SAFE={'YES' if transfer_safe else 'NO'}")
    print("-" * 92)

    if recorder.failures:
        print("CONTINUITY_GATE=FAIL")
        print("Failed checks:")
        for failure in recorder.failures:
            print(f"- {failure.name}: {failure.detail}")
        return 1

    if arguments.allow_dirty or arguments.allow_no_upstream:
        print("CONTINUITY_GATE=DIAGNOSTIC_PASS")
        print("This result is not sufficient for switching work between clones.")
        return 0

    print("CONTINUITY_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
