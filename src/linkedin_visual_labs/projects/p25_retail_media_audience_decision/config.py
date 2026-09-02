"""Typed configuration loading for Project 4."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class SourceConfig(BaseModel):
    """Configuration for one evidence source."""

    model_config = ConfigDict(
        extra="allow",
        frozen=True,
    )

    enabled: bool
    evidence_label: str
    cache_path: Path


class SegmentationConfig(BaseModel):
    """ML segmentation configuration."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    algorithm: str
    candidate_k: list[int]
    random_state: int
    minimum_audience_size: int = Field(gt=0)
    pca_components: int = Field(
        default=2,
        ge=2,
        le=2,
    )


class UpliftConfig(BaseModel):
    """Uplift-model configuration."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    enabled: bool
    baseline: str
    random_state: int
    test_fraction: float = Field(
        gt=0.0,
        lt=1.0,
    )
    evaluation: list[str]


class DashboardConfig(BaseModel):
    """Canonical dashboard rendering configuration."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    title: str
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)
    theme: str
    reference_sha256: str
    screenshot_renderer: str
    self_contained_html: bool
    kpis: list[str]


class ProjectConfig(BaseModel):
    """Validated top-level Project 4 configuration."""

    model_config = ConfigDict(
        extra="allow",
        frozen=True,
    )

    schema_version: str
    project: dict[str, Any]
    sources: dict[str, SourceConfig]
    segmentation: SegmentationConfig
    uplift: UpliftConfig
    dashboard: DashboardConfig


def load_config(
    path: Path,
) -> ProjectConfig:
    """Load and validate Project 4 YAML configuration."""

    raw: Any = yaml.safe_load(
        path.read_text(
            encoding="utf-8-sig",
        )
    )

    if not isinstance(
        raw,
        dict,
    ):
        raise ValueError("Project 4 configuration root must be a mapping.")

    return ProjectConfig.model_validate(raw)
