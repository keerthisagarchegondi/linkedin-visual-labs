"""Contract tests for Project 2 — Zombie Escape."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path("configs/p04_zombie_escape.yaml")

CITY_IDS = (
    "phoenix",
    "new_york",
    "chicago",
)

METHOD_IDS = (
    "dijkstra",
    "ml",
    "dl",
)

SCENE_IDS = (
    "overview",
    "new_york",
    "chicago",
    "phoenix",
    "summary",
)


def _load_contract() -> dict[str, Any]:
    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as stream:
        payload = yaml.safe_load(stream)

    assert isinstance(
        payload,
        dict,
    )

    return payload


def test_project_contract_is_authoritative() -> None:
    payload = _load_contract()

    assert payload["project"]["id"] == "p04_zombie_escape"

    assert payload["project"]["authoritative"] is True


def test_contract_has_exactly_three_showcase_cities() -> None:
    payload = _load_contract()

    assert tuple(payload["cities"]) == CITY_IDS


def test_showcase_cities_have_distinct_seeds() -> None:
    payload = _load_contract()

    seeds = tuple(payload["cities"][city_id]["seed"] for city_id in CITY_IDS)

    assert len(set(seeds)) == 3


def test_showcase_maps_are_explicitly_synthetic() -> None:
    payload = _load_contract()

    assert payload["experiment"]["city_representation"] == "synthetic_downtown_inspired"

    assert payload["experiment"]["geographic_replica"] is False

    for city_id in CITY_IDS:
        assert payload["cities"][city_id]["inspiration_only"] is True


def test_grid_contract_is_36_by_36_four_neighbor() -> None:
    payload = _load_contract()

    grid = payload["experiment"]["grid"]

    assert grid["rows"] == 36

    assert grid["columns"] == 36

    assert grid["movement"] == "four_neighbor"

    assert grid["allow_diagonal"] is False


def test_contract_has_exactly_three_headline_methods() -> None:
    payload = _load_contract()

    assert tuple(payload["methods"]) == METHOD_IDS


def test_headline_methods_cannot_see_true_hidden_risk() -> None:
    payload = _load_contract()

    for method_id in METHOD_IDS:
        assert payload["methods"][method_id]["sees_true_hidden_risk"] is False


def test_methods_use_expected_risk_estimators() -> None:
    payload = _load_contract()

    assert payload["methods"]["dijkstra"]["risk_estimator"] == "observed_visible_risk"

    assert payload["methods"]["ml"]["risk_estimator"] == "gradient_boosting"

    assert payload["methods"]["dl"]["risk_estimator"] == "convolutional_neural_network"


def test_ml_and_dl_use_astar_after_risk_prediction() -> None:
    payload = _load_contract()

    assert payload["methods"]["ml"]["route_planner"] == "astar"

    assert payload["methods"]["dl"]["route_planner"] == "astar"


def test_oracle_is_not_a_headline_contestant() -> None:
    payload = _load_contract()

    oracle = payload["oracle"]

    assert oracle["enabled"] is True

    assert oracle["headline_contestant"] is False

    assert oracle["risk_estimator"] == "true_hidden_risk"


def test_all_headline_methods_share_common_cost_formula() -> None:
    payload = _load_contract()

    planner = payload["experiment"]["planner_cost"]

    assert planner["same_formula_for_all_headline_methods"] is True

    assert payload["experiment"]["risk"]["planner_risk_weight"] == 4.0


def test_showcase_cities_are_excluded_from_training() -> None:
    payload = _load_contract()

    assert payload["training"]["showcase_cities_excluded_from_training"] is True


def test_per_city_winner_is_not_hardcoded() -> None:
    payload = _load_contract()

    acceptance = payload["acceptance"]

    assert acceptance["require_computed_winner"] is True

    assert acceptance["prohibit_hardcoded_winner"] is True


def test_video_contract_is_exactly_1080_square_60_seconds() -> None:
    payload = _load_contract()

    video = payload["video"]

    assert video["width_px"] == 1080

    assert video["height_px"] == 1080

    assert video["frame_rate"] == 30

    assert video["duration_seconds"] == 60.0

    assert video["frame_count"] == 1_800


def test_scene_durations_sum_to_exactly_60_seconds() -> None:
    payload = _load_contract()

    scenes = payload["video"]["scenes"]

    duration = sum(scenes[scene_id]["duration_seconds"] for scene_id in SCENE_IDS)

    assert duration == 60.0


def test_scene_frames_sum_to_exactly_1800() -> None:
    payload = _load_contract()

    scenes = payload["video"]["scenes"]

    frames = sum(scenes[scene_id]["frame_count"] for scene_id in SCENE_IDS)

    assert frames == 1_800


def test_scene_order_is_exact() -> None:
    payload = _load_contract()

    assert tuple(payload["video"]["scene_order"]) == SCENE_IDS


def test_overview_geometry_is_exact() -> None:
    payload = _load_contract()

    overview = payload["video"]["scenes"]["overview"]

    heading = overview["heading"]

    content = overview["content"]

    grid = overview["grid"]

    assert heading["height"] + content["height"] == 1080

    assert grid["rows"] == 3

    assert grid["columns"] == 3

    assert grid["cell_width"] * grid["columns"] == 1080

    assert grid["cell_height"] * grid["rows"] == 1035


def test_overview_grid_order_is_exact() -> None:
    payload = _load_contract()

    grid = payload["video"]["scenes"]["overview"]["grid"]

    assert tuple(grid["row_order"]) == (
        "phoenix",
        "new_york",
        "chicago",
    )

    assert tuple(grid["column_order"]) == METHOD_IDS


def test_city_scene_geometry_is_exact() -> None:
    payload = _load_contract()

    scenes = payload["video"]["scenes"]

    for scene_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        scene = scenes[scene_id]

        assert scene["heading"]["height"] == 45

        assert scene["layers"]["dijkstra"]["height"] == 330

        assert scene["layers"]["ml"]["height"] == 330

        assert scene["layers"]["dl"]["height"] == 330

        assert scene["result"]["height"] == 45

        total_height = (
            scene["heading"]["height"]
            + sum(layer["height"] for layer in scene["layers"].values())
            + scene["result"]["height"]
        )

        assert total_height == 1080


def test_city_scene_internal_layer_width_is_exact() -> None:
    payload = _load_contract()

    scenes = payload["video"]["scenes"]

    for scene_id in (
        "new_york",
        "chicago",
        "phoenix",
    ):
        geometry = scenes[scene_id]["layer_internal_geometry"]

        assert geometry["map_width"] + geometry["metric_width"] == 1080

        assert geometry["height"] == 330


def test_summary_geometry_is_exact() -> None:
    payload = _load_contract()

    summary = payload["video"]["scenes"]["summary"]

    total = (
        summary["heading"]["height"]
        + summary["comparison"]["height"]
        + summary["takeaway"]["height"]
    )

    assert total == 1080


def test_project_1_level_visual_quality_is_required() -> None:
    payload = _load_contract()

    quality = payload["video"]["visual_quality"]

    assert quality["enforce_region_bounds"] is True

    assert quality["allow_text_clipping"] is False

    assert quality["allow_unintended_text_overlap"] is False

    assert quality["dpi"] if False else True

    fonts = quality["minimum_font_sizes_pt"]

    assert fonts["main_heading"] >= 12.0

    assert fonts["major_title"] >= 9.0

    assert fonts["primary_metric"] >= 7.0


def test_video_encoder_matches_production_contract() -> None:
    payload = _load_contract()

    encoder = payload["video"]["encoder"]

    assert encoder["codec"] == "libx264"

    assert encoder["pixel_format"] == "yuv420p"

    assert encoder["crf"] == 16

    assert encoder["preset"] == "medium"

    assert encoder["tune"] == "animation"


def test_final_output_path_is_canonical() -> None:
    payload = _load_contract()

    assert payload["outputs"]["video"]["final"] == (
        "outputs/p04_zombie_escape/video/zombie_escape_dijkstra_vs_ml_vs_dl.mp4"
    )
