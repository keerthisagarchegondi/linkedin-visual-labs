"""Project 9 setup and Step 2 semantic-oracle validation."""

from __future__ import annotations

import json
import subprocess
from importlib import resources
from pathlib import Path
from typing import Any

from .adjustment import point_adjust
from .analytics import paired_counts_from_event_hits
from .config import (
    PROJECT_ID,
    Project9Config,
    default_config_path,
    default_config_source,
    derive_seed,
    load_default_config,
    repository_root,
)
from .fixtures import fixture_path, load_fixtures
from .metrics import confusion_counts
from .segments import extract_events


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def current_branch() -> str | None:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repository_root(),
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def validate_semantic_invariants() -> dict[str, int]:
    """Cross-check timeline PA counts against the Step 2 sufficient-count identity."""
    checked = 0
    for fixture in load_fixtures():
        events = extract_events(fixture.labels)
        if tuple((event.start, event.stop) for event in events) != fixture.expected_intervals:
            raise ValueError(f"fixture {fixture.fixture_id} has inconsistent event intervals")
        if fixture.raw_predictions is None:
            continue
        adjusted = point_adjust(fixture.labels, fixture.raw_predictions)
        timeline_raw = confusion_counts(fixture.labels, fixture.raw_predictions)
        timeline_adjusted = confusion_counts(fixture.labels, adjusted)
        if not events:
            if timeline_raw != timeline_adjusted:
                raise ValueError(f"fixture {fixture.fixture_id} changes an all-normal timeline")
            checked += 1
            continue
        event_hits = tuple(
            sum(fixture.raw_predictions[event.start : event.stop]) for event in events
        )
        outside_false_positives = sum(
            prediction
            for label, prediction in zip(fixture.labels, fixture.raw_predictions, strict=True)
            if label == 0
        )
        paired = paired_counts_from_event_hits(
            tuple(event.length for event in events),
            event_hits,
            outside_false_positives,
            sum(1 for label in fixture.labels if label == 0),
        )
        if paired.raw != timeline_raw or paired.adjusted != timeline_adjusted:
            raise ValueError(f"fixture {fixture.fixture_id} violates paired-count equivalence")
        if (
            timeline_raw.f1 is not None
            and timeline_adjusted.f1 is not None
            and timeline_adjusted.f1 < timeline_raw.f1
        ):
            raise ValueError(f"fixture {fixture.fixture_id} violates PA F1 monotonicity")
        checked += 1
    return {"fixtures_checked": checked}


def validate_setup(config: Project9Config | None = None) -> dict[str, Any]:
    selected = load_default_config() if config is None else config
    fixtures = load_fixtures()
    package = resources.files(__package__)
    if default_config_source() == "REPOSITORY_CONFIG":
        root = repository_root()
        docs = root / "docs" / "projects" / PROJECT_ID
        for document in ("PROJECT_CONTRACT.md", "EXPERIMENT_PROTOCOL.md", "STATE.json"):
            if not (docs / document).is_file():
                raise ValueError("required Project 9 setup contracts are missing")
        state_text = (docs / "STATE.json").read_text(encoding="utf-8")
        design_text = (root / "reference" / "project9" / "experiment_design.json").read_text(
            encoding="utf-8"
        )
    else:
        resource_root = package.joinpath("resources")
        state_text = resource_root.joinpath("STATE.json").read_text(encoding="utf-8")
        design_text = resource_root.joinpath("experiment_design.json").read_text(encoding="utf-8")
    state = json.loads(state_text)
    design = json.loads(design_text)
    if state.get("project_id") != PROJECT_ID or state.get("experiment_frozen") is not True:
        raise ValueError("Project 9 state contract is inconsistent")
    if design.get("N") != selected.n_timestamps or design.get("P") != selected.anomalous_timestamps:
        raise ValueError("frozen experiment design does not match canonical config")
    if (
        tuple(design.get("event_lengths", [])) != selected.event_lengths
        or tuple(float(value) for value in design.get("q_values", []))
        != selected.alert_probabilities
    ):
        raise ValueError("frozen experiment grids do not match canonical config")
    if default_config_source() == "REPOSITORY_CONFIG" and not _contained(
        repository_root(), fixture_path()
    ):
        raise ValueError("Project 9 paths must remain within the repository")
    config_text = (
        default_config_path().read_text(encoding="utf-8")
        if default_config_source() == "REPOSITORY_CONFIG"
        else package.joinpath("resources", f"{PROJECT_ID}.yaml").read_text(encoding="utf-8")
    )
    if "preview" in config_text.lower() or "dummy" in config_text.lower():
        raise ValueError("scientific config cannot contain preview or dummy data")
    if derive_seed(selected, "semantic_fixture", fixture="all_normal") != derive_seed(
        selected, "semantic_fixture", fixture="all_normal"
    ):
        raise ValueError("deterministic stream derivation failed")
    semantic = validate_semantic_invariants()
    return {
        "status": "PASS",
        "project_id": PROJECT_ID,
        "fixture_count": len(fixtures),
        "branch": current_branch(),
        "state": state,
        **semantic,
    }
