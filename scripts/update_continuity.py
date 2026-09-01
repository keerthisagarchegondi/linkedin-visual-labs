"""Update the deterministic semantic repository-continuity checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Any

MANIFEST_RELATIVE_PATH = Path("contracts/repository_continuity.json")
EXPECTED_REPOSITORY_KEY = "keerthisagarchegondi/linkedin-visual-labs"
EXPECTED_ORIGIN_URL = "https://github.com/keerthisagarchegondi/linkedin-visual-labs.git"
EXPECTED_DEFAULT_BRANCH = "main"
BASELINE_COMMIT = "0557673c790dc900db7293586ce96931ede40c96"


class UpdateError(RuntimeError):
    """Raised when the continuity checkpoint cannot be updated safely."""


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Run a command and fail with decoded diagnostics."""

    completed = subprocess.run(
        tuple(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed.returncode != 0:
        rendered = " ".join(command)
        message = completed.stderr.strip() or completed.stdout.strip()
        raise UpdateError(f"Command failed ({completed.returncode}): {rendered}\n{message}")

    return completed


def run_git(root: Path, *arguments: str) -> str:
    """Run Git from the repository root and return stdout."""

    return run_command(
        ("git", "-C", str(root), *arguments),
        cwd=root,
    ).stdout.strip()


def discover_repository_root() -> Path:
    """Resolve and verify the repository root."""

    script_root = Path(__file__).resolve().parents[1]
    git_root = Path(run_git(script_root, "rev-parse", "--show-toplevel")).resolve()

    if script_root != git_root:
        raise UpdateError(
            "scripts/update_continuity.py must live directly below the "
            f"repository root: script_root={script_root}; git_root={git_root}"
        )

    return git_root


def initial_manifest() -> dict[str, Any]:
    """Return the stable repository identity and baseline contract."""

    return {
        "schema_version": "1.0",
        "repository": {
            "key": EXPECTED_REPOSITORY_KEY,
            "origin_url": EXPECTED_ORIGIN_URL,
            "default_branch": EXPECTED_DEFAULT_BRANCH,
        },
        "minimum_baseline": {
            "commit": BASELINE_COMMIT,
            "label": "Project 3 complete: Monopoly AI Landlord Arena",
        },
        "checkpoint": {},
    }


def load_manifest(path: Path) -> dict[str, Any]:
    """Load the existing manifest and preserve its stable identity block."""

    if not path.exists():
        return initial_manifest()

    payload = json.loads(path.read_text(encoding="utf-8-sig"))

    if not isinstance(payload, dict):
        raise UpdateError("Continuity manifest must be a JSON object.")

    expected = initial_manifest()

    if payload.get("repository") != expected["repository"]:
        raise UpdateError("Continuity manifest repository identity drifted.")

    if payload.get("minimum_baseline") != expected["minimum_baseline"]:
        raise UpdateError("Continuity manifest minimum baseline drifted.")

    return payload


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Return stable JSON bytes for hashing."""

    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def write_json_lf(path: Path, payload: dict[str, Any]) -> None:
    """Write pretty JSON as UTF-8 without BOM and with LF newlines."""

    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)


def nonblank(value: str, *, name: str) -> str:
    """Validate and normalize one required string."""

    normalized = value.strip()

    if not normalized:
        raise UpdateError(f"{name} must not be blank.")

    return normalized


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Update contracts/repository_continuity.json after a meaningful project checkpoint."
        )
    )
    parser.add_argument("--project-number", required=True, type=int)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--phase", default="implementation")
    parser.add_argument("--step", required=True)
    parser.add_argument("--substep", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--status",
        choices=("in_progress", "complete", "blocked"),
        default="in_progress",
    )
    parser.add_argument(
        "--expected-branch",
        required=True,
        help="Branch assertion before updating the checkpoint.",
    )
    return parser


def main() -> int:
    """Update the semantic checkpoint deterministically."""

    arguments = build_parser().parse_args()

    if arguments.project_number < 0:
        raise UpdateError("project-number must be zero or greater.")

    root = discover_repository_root()
    manifest_path = root / MANIFEST_RELATIVE_PATH

    remotes = tuple(line.strip() for line in run_git(root, "remote").splitlines() if line.strip())

    if remotes != ("origin",):
        raise UpdateError(f"Expected exactly one remote named origin; found {remotes}")

    branch = run_git(root, "branch", "--show-current")

    if not branch:
        raise UpdateError("Cannot update continuity checkpoint from detached HEAD.")

    if branch != arguments.expected_branch:
        raise UpdateError(
            f"Unexpected branch: actual={branch}; expected={arguments.expected_branch}"
        )

    payload = load_manifest(manifest_path)
    payload["schema_version"] = "1.0"
    payload["checkpoint"] = {
        "project_number": arguments.project_number,
        "project_id": nonblank(arguments.project_id, name="project-id"),
        "project_name": nonblank(arguments.project_name, name="project-name"),
        "phase": nonblank(arguments.phase, name="phase"),
        "step": nonblank(arguments.step, name="step"),
        "substep": nonblank(arguments.substep, name="substep"),
        "label": nonblank(arguments.label, name="label"),
        "status": arguments.status,
    }

    write_json_lf(manifest_path, payload)

    validated = json.loads(manifest_path.read_text(encoding="utf-8"))

    if validated != payload:
        raise UpdateError("Continuity manifest round-trip validation failed.")

    digest = hashlib.sha256(canonical_json_bytes(validated)).hexdigest()
    checkpoint = validated["checkpoint"]

    print("=" * 88)
    print("LINKEDIN VISUAL LABS - CONTINUITY CHECKPOINT UPDATED")
    print("=" * 88)
    print(f"Manifest: {manifest_path}")
    print(f"Branch: {branch}")
    print(f"Project: {checkpoint['project_number']} / {checkpoint['project_id']}")
    print(f"Step: {checkpoint['step']} / sub-step {checkpoint['substep']}")
    print(f"Status: {checkpoint['status']}")
    print(f"Label: {checkpoint['label']}")
    print(f"MANIFEST_FINGERPRINT={digest}")
    print("UPDATE_CONTINUITY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
