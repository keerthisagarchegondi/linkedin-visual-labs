from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

RENDERER = (
    ROOT
    / "src"
    / "linkedin_visual_labs"
    / "projects"
    / "p02_monopoly_ai"
    / "cinematic_v3_renderer.py"
)

PROVENANCE = ROOT / "assets" / "p02_monopoly_ai" / "cinematic_v3_provenance.json"


def _sha256(path: Path) -> str:
    text = path.read_text(
        encoding="utf-8-sig",
    )

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    digest = hashlib.sha256()
    digest.update(normalized.encode("utf-8"))

    return digest.hexdigest()


def test_cinematic_v3_renderer_is_valid_python() -> None:
    source = RENDERER.read_text(encoding="utf-8")
    ast.parse(source, filename=str(RENDERER))


def test_cinematic_v3_provenance_matches_renderer() -> None:
    payload = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    assert payload["artifact"]["filename"] == "project3_property_trading_cinematic_v3_60s.mp4"

    assert (
        payload["artifact"]["sha256"]
        == "d018a85a1eda8cd31dfdb2e4e44c1ae349dc770b9b0c5318a51906c355a05501"
    )

    assert payload["artifact"]["duration_seconds"] == 60
    assert payload["artifact"]["width"] == 1080
    assert payload["artifact"]["height"] == 1080
    assert payload["artifact"]["fps"] == 30
    assert payload["artifact"]["frame_count"] == 1800
    assert payload["artifact"]["codec"] == "h264"
    assert payload["artifact"]["pixel_format"] == "yuv420p"

    assert payload["renderer"]["source_sha256"] == _sha256(RENDERER)
