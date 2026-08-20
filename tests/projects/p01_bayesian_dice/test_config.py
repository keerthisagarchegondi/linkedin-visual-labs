"""Tests for Bayesian Dice configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p01_bayesian_dice.config import (
    DiceConfigurationError,
    load_dice_config,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    DecisionState,
)


def test_load_dice_config_matches_analytical_contract() -> None:
    config = load_dice_config()

    assert config.project_id == "p01_bayesian_dice"
    assert config.roll_count == 180
    assert config.showcase_scenario == "clearly_loaded"

    assert set(config.scenarios) == {
        "fair",
        "mildly_loaded",
        "clearly_loaded",
    }

    assert config.scenario("clearly_loaded").seed == 1

    assert config.model.prior_loaded_probability == pytest.approx(0.5)

    assert config.decision.classify(0.50) is DecisionState.UNCERTAIN

    assert config.video.width_px == 1080
    assert config.video.height_px == 1350
    assert config.video.frame_rate == 30


def test_output_contract_matches_step_1_paths() -> None:
    config = load_dice_config()

    assert config.outputs.simulation == Path("outputs/p01_bayesian_dice/data/simulation.json")

    assert config.outputs.posterior_history == Path(
        "outputs/p01_bayesian_dice/data/posterior_history.csv"
    )

    assert config.outputs.validation == Path("outputs/p01_bayesian_dice/data/validation.json")

    assert config.outputs.video == Path(
        "outputs/p01_bayesian_dice/video/can_ai_tell_loaded_die.mp4"
    )

    assert config.outputs.manifest == Path(
        "outputs/p01_bayesian_dice/manifests/can_ai_tell_loaded_die.json"
    )


def test_unknown_scenario_is_rejected() -> None:
    config = load_dice_config()

    with pytest.raises(
        Exception,
        match="unknown scenario",
    ):
        config.scenario("unknown")


def test_invalid_output_escape_is_rejected(
    tmp_path: Path,
) -> None:
    original = Path("configs/p01_bayesian_dice.yaml").read_text(
        encoding="utf-8",
    )

    modified = original.replace(
        ("outputs/p01_bayesian_dice/data/simulation.json"),
        "../simulation.json",
        1,
    )

    path = tmp_path / "invalid.yaml"

    path.write_text(
        modified,
        encoding="utf-8",
    )

    with pytest.raises(
        DiceConfigurationError,
        match="must remain under",
    ):
        load_dice_config(path)
