"""Typed Project 4 configuration tests."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.config import (
    load_config,
)

ROOT = Path(__file__).resolve().parents[3]
PROJECT_ID = "p25_retail_media_audience_decision"


def test_expanded_config_loads() -> None:
    """The frozen expanded configuration must validate."""

    config = load_config(ROOT / "configs" / f"{PROJECT_ID}.yaml")

    assert config.project["number"] == 4
    assert config.segmentation.candidate_k == [
        3,
        4,
        5,
        6,
    ]
    assert config.uplift.enabled is True
    assert config.dashboard.width_px == 1536
    assert config.dashboard.height_px == 1024
    assert config.dashboard.screenshot_renderer == "playwright_chromium"


def test_four_public_sources_are_enabled() -> None:
    """The dashboard contract freezes four evidence environments."""

    config = load_config(ROOT / "configs" / f"{PROJECT_ID}.yaml")

    assert set(config.sources) == {
        "dunnhumby",
        "hillstrom",
        "criteo",
        "retailrocket",
    }

    assert all(source.enabled for source in config.sources.values())
