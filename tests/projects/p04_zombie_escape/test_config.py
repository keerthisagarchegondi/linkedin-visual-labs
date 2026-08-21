"""Typed configuration tests for Project 2."""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p04_zombie_escape import (
    CityId,
    MethodId,
    RiskEstimator,
    RoutePlanner,
    ZombieConfigError,
    load_zombie_config,
)


def test_authoritative_config_loads() -> None:
    config = load_zombie_config()

    assert config.project.project_id == "p04_zombie_escape"

    assert config.project.authoritative is True


def test_config_has_exact_city_ids() -> None:
    config = load_zombie_config()

    assert tuple(city.city_id for city in config.cities) == (
        CityId.PHOENIX,
        CityId.NEW_YORK,
        CityId.CHICAGO,
    )


def test_config_has_exact_method_ids() -> None:
    config = load_zombie_config()

    assert tuple(method.method_id for method in config.methods) == (
        MethodId.DIJKSTRA,
        MethodId.ML,
        MethodId.DL,
    )


def test_config_preserves_scientific_method_roles() -> None:
    config = load_zombie_config()

    dijkstra = config.method(MethodId.DIJKSTRA)

    ml = config.method(MethodId.ML)

    dl = config.method(MethodId.DL)

    assert dijkstra.risk_estimator is RiskEstimator.OBSERVED_VISIBLE_RISK

    assert dijkstra.route_planner is RoutePlanner.DIJKSTRA

    assert ml.risk_estimator is RiskEstimator.GRADIENT_BOOSTING

    assert ml.route_planner is RoutePlanner.ASTAR

    assert dl.risk_estimator is RiskEstimator.CNN

    assert dl.route_planner is RoutePlanner.ASTAR


def test_config_preserves_exact_video_contract() -> None:
    config = load_zombie_config()

    assert config.video.width_px == 1080
    assert config.video.height_px == 1080
    assert config.video.frame_rate == 30
    assert config.video.duration_seconds == 60.0
    assert config.video.frame_count == 1_800
    assert config.video.dpi == 120


def test_config_preserves_output_root() -> None:
    config = load_zombie_config()

    assert config.outputs.root == Path("outputs/p04_zombie_escape")


def test_config_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ZombieConfigError,
        match="does not exist",
    ):
        load_zombie_config(tmp_path / "missing.yaml")


def test_config_rejects_non_mapping_yaml(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.yaml"

    path.write_text(
        "- this\n- is\n- a\n- list\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ZombieConfigError,
        match="root must be a mapping",
    ):
        load_zombie_config(path)
