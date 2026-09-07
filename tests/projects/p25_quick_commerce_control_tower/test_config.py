"""Contract tests for authoritative settings and invalid YAML variants."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from linkedin_visual_labs.common.config import ConfigurationError, load_yaml_config
from linkedin_visual_labs.common.paths import discover_repository_root
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    DEFAULT_CONFIG_PATH,
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import CommerceConfig


def test_authoritative_configuration() -> None:
    config = load_commerce_config()
    assert config.project_id == "p25_quick_commerce_control_tower"
    assert config.data.holdout_days == 28
    assert config.data.categories == ("FOODS", "HOUSEHOLD")
    assert config.data.expected_store_count == 10
    assert config.data.expected_series_count == 20
    assert config.forecasting.mlp.hidden_layer_sizes == (128, 64, 32)
    assert config.forecasting.seasonal_naive.lag == 28
    assert config.forecasting.holt_winters.seasonal_periods == 7
    assert config.forecasting.hist_gradient_boosting.early_stopping is False
    assert config.forecasting.mlp.early_stopping is False
    assert 0 <= config.governance.absolute_bias_guardrail <= 1
    assert config.labor.classification == "illustrative"
    assert 0 < config.labor.minimum_staffing <= config.labor.maximum_staffing
    assert config.labor.daily_network_hours >= (
        config.labor.minimum_staffing * config.labor.shift_hours * 10
    )
    assert len(config.labor.store_priority_weights) == 10
    assert (config.output.width, config.output.height, config.output.fps) == (1080, 1350, 30)
    assert [(s.name, s.demand_multiplier, s.productivity_multiplier) for s in config.scenarios] == [
        ("Base", 1.0, 1.0),
        ("+15% demand", 1.15, 1.0),
        ("-10% productivity", 1.0, 0.90),
    ]
    assert all(s.capacity_multiplier == 1.0 for s in config.scenarios)


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("data", "holdout_days", 0),
        ("data", "holdout_days", -28),
        ("data", "holdout_days", 7),
        ("data", "holdout_days", True),
        ("data", "categories", ["FOODS", "HOBBIES"]),
        ("data", "categories", ["FOODS", "FOODS"]),
        ("data", "expected_store_count", 0),
        ("data", "expected_store_count", 9),
        ("data", "expected_series_count", 19),
        ("governance", "absolute_bias_guardrail", -0.1),
        ("governance", "absolute_bias_guardrail", 1.1),
        ("governance", "absolute_bias_guardrail", float("nan")),
        ("labor", "minimum_staffing", 13),
        ("labor", "daily_network_hours", 1.0),
        ("labor", "cost_per_hour", -1.0),
        ("labor", "classification", "measured"),
        ("labor", "productivity_units_per_hour", {"FOODS": 90.0}),
        ("labor", "store_priority_weights", {}),
        ("output", "width", 0),
        ("output", "height", -1),
        ("output", "width", 1081),
        ("output", "fps", 0),
        ("output", "fps", 60),
        ("paths", "output", "outputs/unrelated"),
        ("paths", "cache", "../escape"),
    ],
)
def test_invalid_configuration_is_rejected(section: str, key: str, value: object) -> None:
    raw = deepcopy(load_yaml_config(discover_repository_root() / DEFAULT_CONFIG_PATH))
    raw[section][key] = value
    with pytest.raises(ValidationError):
        CommerceConfig.model_validate(raw)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("demand_multiplier", 0.0),
        ("productivity_multiplier", -1.0),
        ("productivity_multiplier", 0.80),
        ("capacity_multiplier", 1.1),
    ],
)
def test_invalid_scenario_multiplier(key: str, value: float) -> None:
    raw = load_yaml_config(discover_repository_root() / DEFAULT_CONFIG_PATH)
    raw["scenarios"][2][key] = value
    with pytest.raises(ValidationError):
        CommerceConfig.model_validate(raw)


@pytest.mark.parametrize("mutation", ["architecture", "duplicate_scenario", "seed", "unknown"])
def test_model_seed_and_schema_rejections(mutation: str) -> None:
    raw: dict[str, Any] = load_yaml_config(discover_repository_root() / DEFAULT_CONFIG_PATH)
    if mutation == "architecture":
        raw["forecasting"]["mlp"]["hidden_layer_sizes"] = [128, 64]
    elif mutation == "duplicate_scenario":
        raw["scenarios"][1] = raw["scenarios"][0]
    elif mutation == "seed":
        raw["seed"] = -1
    else:
        raw["unexpected"] = "not supported"
    with pytest.raises(ValidationError):
        CommerceConfig.model_validate(raw)


def test_loader_wraps_invalid_yaml_model(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(yaml.safe_dump({"seed": 47}), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="invalid commerce configuration"):
        load_commerce_config(path, repository_root=tmp_path)


def test_loader_is_independent_of_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = discover_repository_root()
    monkeypatch.chdir(tmp_path)
    assert load_commerce_config(repository_root=root).data.holdout_days == 28
