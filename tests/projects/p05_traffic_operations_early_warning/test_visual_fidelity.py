"""Small structural contracts; no proprietary previews required by ordinary CI."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.design_system import (
    BG,
    HEADER,
    HERO_BOX,
    OVERLAY_BOXES,
    TAB_REFERENCES,
    VIDEO_REFERENCES,
    css_tokens,
    ease,
)
from linkedin_visual_labs.projects.p05_traffic_operations_early_warning.visual_fidelity import (
    compare,
    palette_contains,
)


def test_reference_mapping_and_geometry() -> None:
    assert len(VIDEO_REFERENCES) == len(OVERLAY_BOXES) == 10
    assert len(TAB_REFERENCES) == 5
    assert VIDEO_REFERENCES[2] == "03_video_10s_teaser_result.png"
    assert HERO_BOX == (0, 103, 1080, 851)
    assert OVERLAY_BOXES[2] == (676, 151, 1040, 813)


@pytest.mark.parametrize("value", [-1.0, 0.0, 0.25, 0.5, 0.75, 1.0, 2.0])
def test_presentation_easing_bounded(value: float) -> None:
    assert 0 <= ease(value) <= 1
    assert ease(value) <= ease(value + 0.01)


def test_css_uses_sampled_report_palette() -> None:
    assert "#F4F7FA" in css_tokens()
    assert "#F2A93B" in css_tokens()
    assert "#2F80ED" in css_tokens()
    assert palette_contains(["#F3F7FA"], "#F4F7FA")
    assert not palette_contains(["#FFFFFF"], "#F4F7FA")


def test_audit_rejects_wrong_palette_and_dimensions(tmp_path: Path) -> None:
    reference, actual = tmp_path / "reference.png", tmp_path / "actual.png"
    im = Image.new("RGB", (1080, 1350), BG)
    im.paste(HEADER, (0, 0, 1080, 103))
    im.save(reference)
    im.save(actual)
    assert compare(reference, actual, video=True)["automated_status"] == "PASS"
    Image.new("RGB", (1080, 1350), "white").save(actual)
    assert compare(reference, actual, video=True)["automated_status"] == "REQUIRES_REPAIR"
    Image.new("RGB", (100, 100), BG).save(actual)
    assert not compare(reference, actual, video=True)["checks"]["dimensions"]
