from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

MANIFEST = ROOT / "assets" / "p02_monopoly_ai" / "project_completion.json"

PROVENANCE = ROOT / "assets" / "p02_monopoly_ai" / "cinematic_v3_provenance.json"

DOC = ROOT / "docs" / "projects" / "p02_monopoly_ai.md"

README = ROOT / "README.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def _load_json(path: Path) -> dict[str, object]:
    payload = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    assert isinstance(payload, dict)

    return payload


def test_project_completion_manifest_is_complete() -> None:
    payload = _load_json(MANIFEST)

    assert payload["project_id"] == "p02_monopoly_ai"
    assert payload["project_number"] == 3
    assert payload["status"] == "complete"

    simulation = payload["simulation"]
    assert isinstance(simulation, dict)
    assert simulation["game_count"] == 10000
    assert simulation["strategy_game_rows"] == 40000
    assert simulation["master_seed"] == 73031

    result = payload["result"]
    assert isinstance(result, dict)
    assert result["headline_winner"] == "collector"


def test_completion_video_matches_provenance() -> None:
    completion = _load_json(MANIFEST)
    provenance = _load_json(PROVENANCE)

    accepted_video = completion["accepted_video"]
    artifact = provenance["artifact"]

    assert isinstance(accepted_video, dict)
    assert isinstance(artifact, dict)

    assert accepted_video["filename"] == artifact["filename"]
    assert accepted_video["sha256"] == artifact["sha256"]
    assert accepted_video["frame_count"] == 1800
    assert accepted_video["fps"] == 30


def test_project_document_declares_final_result() -> None:
    text = DOC.read_text(
        encoding="utf-8",
    )

    assert "**Complete.**" in text
    assert "Collector won most often" in text
    assert "37.72%" in text
    assert "10,000" in text
    assert "40,000" in text


def test_readme_contains_project_completion_marker() -> None:
    text = README.read_text(
        encoding="utf-8",
    )

    assert "<!-- P02_MONOPOLY_AI_STATUS_START -->" in text
    assert "<!-- P02_MONOPOLY_AI_STATUS_END -->" in text
    assert "**Status: Complete**" in text


def test_ci_contains_repository_quality_gates() -> None:
    text = CI.read_text(
        encoding="utf-8",
    ).lower()

    assert "ruff" in text
    assert "mypy" in text
    assert "pytest" in text
