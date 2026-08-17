"""Tests for shared YAML configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.common.config import (
    ConfigurationError,
    load_yaml_config,
)


def test_load_yaml_config_returns_mapping(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        ("project_id: p01_bayesian_dice\nseed: 12345\nrolls: 120\n"),
        encoding="utf-8",
    )

    config = load_yaml_config(
        path,
        required_keys=("project_id", "seed"),
    )

    assert config["project_id"] == "p01_bayesian_dice"
    assert config["seed"] == 12345
    assert config["rolls"] == 120


def test_load_yaml_config_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ConfigurationError,
        match="does not exist",
    ):
        load_yaml_config(tmp_path / "missing.yaml")


def test_load_yaml_config_rejects_invalid_yaml(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        "project_id: [unterminated\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError,
        match="invalid YAML",
    ):
        load_yaml_config(path)


def test_load_yaml_config_rejects_non_mapping(
    tmp_path: Path,
) -> None:
    path = tmp_path / "list.yaml"
    path.write_text(
        "- one\n- two\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError,
        match="must be a mapping",
    ):
        load_yaml_config(path)


def test_load_yaml_config_rejects_missing_required_key(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(
        "project_id: p01_bayesian_dice\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ConfigurationError,
        match="missing required keys: seed",
    ):
        load_yaml_config(
            path,
            required_keys=("project_id", "seed"),
        )
