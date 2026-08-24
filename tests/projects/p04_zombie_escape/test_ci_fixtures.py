"""CI fixture integrity tests for Project 2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

FIXTURE_ROOT = Path("tests/fixtures/p04_zombie_escape")

DATA = FIXTURE_ROOT / "data"

MANIFEST = FIXTURE_ROOT / "fixture_manifest.json"


def test_fixture_manifest_exists() -> None:
    assert MANIFEST.is_file()


def test_fixture_bundle_contains_required_artifacts() -> None:
    required = {
        "cities.json",
        "predicted_risk_maps.json",
        "routes.json",
        "evaluation_summary.json",
        "route_comparison.csv",
        "overall_comparison.csv",
        "search_traces.json",
    }

    actual = {path.name for path in DATA.iterdir() if path.is_file()}

    assert actual == required


def test_fixture_hashes_match_manifest() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))

    files = payload["files"]

    assert isinstance(
        files,
        dict,
    )

    for filename, metadata in files.items():
        assert isinstance(
            filename,
            str,
        )

        assert isinstance(
            metadata,
            dict,
        )

        path = DATA / filename

        content = path.read_bytes()

        assert metadata["bytes"] == len(content)

        assert metadata["sha256"] == hashlib.sha256(content).hexdigest()
