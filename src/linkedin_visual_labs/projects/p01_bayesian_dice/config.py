"""YAML-to-domain configuration loading for Bayesian Dice Detective."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from linkedin_visual_labs.common.config import (
    ConfigurationError,
    load_yaml_config,
)
from linkedin_visual_labs.common.validation import (
    require_keys,
    require_mapping,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    BayesianModelDefinition,
    CalibrationDefinition,
    DecisionThresholds,
    DiceModelError,
    DiceProjectConfig,
    OutputContract,
    ProbabilityVector,
    ScenarioDefinition,
    VideoContract,
)

DEFAULT_CONFIG_PATH = Path("configs/p01_bayesian_dice.yaml")


class DiceConfigurationError(ConfigurationError):
    """Raised when the Bayesian Dice YAML contract is invalid."""


def _mapping(
    value: object,
    *,
    name: str,
) -> Mapping[str, Any]:
    try:
        return require_mapping(
            value,
            name=name,
        )
    except Exception as exc:
        raise DiceConfigurationError(str(exc)) from exc


def _sequence(
    value: object,
    *,
    name: str,
) -> Sequence[object]:
    if isinstance(
        value,
        Sequence,
    ) and not isinstance(
        value,
        (str, bytes),
    ):
        return value

    raise DiceConfigurationError(f"{name} must be a sequence")


def _int_value(
    value: object,
    *,
    name: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DiceConfigurationError(f"{name} must be an integer")

    return value


def _float_value(
    value: object,
    *,
    name: str,
) -> float:
    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise DiceConfigurationError(f"{name} must be numeric")

    return float(value)


def _string_value(
    value: object,
    *,
    name: str,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiceConfigurationError(f"{name} must be a non-empty string")

    return value


def _build_scenarios(
    raw: object,
) -> dict[str, ScenarioDefinition]:
    scenarios_mapping = _mapping(
        raw,
        name="simulation.scenarios",
    )

    scenarios: dict[str, ScenarioDefinition] = {}

    for scenario_id, raw_scenario in scenarios_mapping.items():
        scenario = _mapping(
            raw_scenario,
            name=f"scenario {scenario_id}",
        )

        require_keys(
            scenario,
            (
                "label",
                "probabilities",
                "seed",
            ),
            name=f"scenario {scenario_id}",
        )

        scenarios[scenario_id] = ScenarioDefinition(
            scenario_id=scenario_id,
            label=_string_value(
                scenario["label"],
                name=f"{scenario_id}.label",
            ),
            probabilities=ProbabilityVector.from_sequence(
                _sequence(
                    scenario["probabilities"],
                    name=f"{scenario_id}.probabilities",
                )
            ),
            seed=_int_value(
                scenario["seed"],
                name=f"{scenario_id}.seed",
            ),
        )

    return scenarios


def _build_output_contract(
    raw: object,
) -> OutputContract:
    outputs = _mapping(
        raw,
        name="outputs",
    )

    required = (
        "simulation",
        "posterior_history",
        "validation",
        "video",
        "manifest",
    )

    require_keys(
        outputs,
        required,
        name="outputs",
    )

    parsed: dict[str, Path] = {}

    for key in required:
        entry = _mapping(
            outputs[key],
            name=f"outputs.{key}",
        )

        require_keys(
            entry,
            ("path",),
            name=f"outputs.{key}",
        )

        path_text = _string_value(
            entry["path"],
            name=f"outputs.{key}.path",
        )

        path = Path(path_text)

        if path.is_absolute():
            raise DiceConfigurationError(f"outputs.{key}.path must be repository-relative")

        expected_prefix = Path("outputs/p01_bayesian_dice")

        try:
            path.relative_to(expected_prefix)
        except ValueError as exc:
            raise DiceConfigurationError(
                f"outputs.{key}.path must remain under outputs/p01_bayesian_dice"
            ) from exc

        parsed[key] = path

    return OutputContract(
        simulation=parsed["simulation"],
        posterior_history=parsed["posterior_history"],
        validation=parsed["validation"],
        video=parsed["video"],
        manifest=parsed["manifest"],
    )


def load_dice_config(
    path: Path | str = DEFAULT_CONFIG_PATH,
) -> DiceProjectConfig:
    """Load the Project 1 YAML contract into typed domain models."""
    config_path = Path(path)

    try:
        raw = load_yaml_config(
            config_path,
            required_keys=(
                "project",
                "model",
                "decision",
                "simulation",
                "calibration",
                "outputs",
                "video",
            ),
        )

        project = _mapping(
            raw["project"],
            name="project",
        )
        model = _mapping(
            raw["model"],
            name="model",
        )
        hypotheses = _mapping(
            model["hypotheses"],
            name="model.hypotheses",
        )
        fair_hypothesis = _mapping(
            hypotheses["fair"],
            name="model.hypotheses.fair",
        )
        loaded_hypothesis = _mapping(
            hypotheses["loaded"],
            name="model.hypotheses.loaded",
        )
        decision = _mapping(
            raw["decision"],
            name="decision",
        )
        simulation = _mapping(
            raw["simulation"],
            name="simulation",
        )
        calibration = _mapping(
            raw["calibration"],
            name="calibration",
        )
        video = _mapping(
            raw["video"],
            name="video",
        )

        require_keys(
            project,
            (
                "id",
                "name",
                "hook",
                "technical_description",
            ),
            name="project",
        )

        require_keys(
            model,
            (
                "hypotheses",
                "prior_loaded_probability",
            ),
            name="model",
        )

        require_keys(
            fair_hypothesis,
            ("probabilities",),
            name="model.hypotheses.fair",
        )

        require_keys(
            loaded_hypothesis,
            ("dirichlet_alpha",),
            name="model.hypotheses.loaded",
        )

        require_keys(
            decision,
            (
                "fair_threshold",
                "loaded_threshold",
            ),
            name="decision",
        )

        require_keys(
            simulation,
            (
                "roll_count",
                "scenarios",
                "showcase_scenario",
            ),
            name="simulation",
        )

        require_keys(
            calibration,
            (
                "repetitions_per_scenario",
                "master_seed",
                "posterior_bucket_count",
                "prior_sensitivity",
                "primary_loaded_scenario",
            ),
            name="calibration",
        )

        require_keys(
            video,
            (
                "width_px",
                "height_px",
                "frame_rate",
                "target_duration_seconds",
                "opening_hook",
                "technical_footer",
            ),
            name="video",
        )

        fair_probabilities = ProbabilityVector.from_sequence(
            _sequence(
                fair_hypothesis["probabilities"],
                name="model.hypotheses.fair.probabilities",
            )
        )

        alpha_values = tuple(
            _float_value(
                value,
                name="Dirichlet alpha",
            )
            for value in _sequence(
                loaded_hypothesis["dirichlet_alpha"],
                name="model.hypotheses.loaded.dirichlet_alpha",
            )
        )

        prior_sensitivity = tuple(
            _float_value(
                value,
                name="prior_sensitivity",
            )
            for value in _sequence(
                calibration["prior_sensitivity"],
                name="calibration.prior_sensitivity",
            )
        )

        return DiceProjectConfig(
            project_id=_string_value(
                project["id"],
                name="project.id",
            ),
            name=_string_value(
                project["name"],
                name="project.name",
            ),
            hook=_string_value(
                project["hook"],
                name="project.hook",
            ),
            technical_description=_string_value(
                project["technical_description"],
                name="project.technical_description",
            ),
            model=BayesianModelDefinition(
                fair_probabilities=fair_probabilities,
                dirichlet_alpha=alpha_values,
                prior_loaded_probability=_float_value(
                    model["prior_loaded_probability"],
                    name="model.prior_loaded_probability",
                ),
            ),
            decision=DecisionThresholds(
                fair_threshold=_float_value(
                    decision["fair_threshold"],
                    name="decision.fair_threshold",
                ),
                loaded_threshold=_float_value(
                    decision["loaded_threshold"],
                    name="decision.loaded_threshold",
                ),
            ),
            roll_count=_int_value(
                simulation["roll_count"],
                name="simulation.roll_count",
            ),
            scenarios=_build_scenarios(simulation["scenarios"]),
            showcase_scenario=_string_value(
                simulation["showcase_scenario"],
                name="simulation.showcase_scenario",
            ),
            calibration=CalibrationDefinition(
                repetitions_per_scenario=_int_value(
                    calibration["repetitions_per_scenario"],
                    name="calibration.repetitions_per_scenario",
                ),
                master_seed=_int_value(
                    calibration["master_seed"],
                    name="calibration.master_seed",
                ),
                posterior_bucket_count=_int_value(
                    calibration["posterior_bucket_count"],
                    name="calibration.posterior_bucket_count",
                ),
                prior_sensitivity=prior_sensitivity,
                primary_loaded_scenario=_string_value(
                    calibration["primary_loaded_scenario"],
                    name="calibration.primary_loaded_scenario",
                ),
            ),
            outputs=_build_output_contract(raw["outputs"]),
            video=VideoContract(
                width_px=_int_value(
                    video["width_px"],
                    name="video.width_px",
                ),
                height_px=_int_value(
                    video["height_px"],
                    name="video.height_px",
                ),
                frame_rate=_int_value(
                    video["frame_rate"],
                    name="video.frame_rate",
                ),
                target_duration_seconds=_float_value(
                    video["target_duration_seconds"],
                    name="video.target_duration_seconds",
                ),
                opening_hook=_string_value(
                    video["opening_hook"],
                    name="video.opening_hook",
                ),
                technical_footer=_string_value(
                    video["technical_footer"],
                    name="video.technical_footer",
                ),
            ),
            configuration_path=config_path,
        )

    except DiceConfigurationError:
        raise
    except (
        ConfigurationError,
        DiceModelError,
        KeyError,
    ) as exc:
        raise DiceConfigurationError(f"invalid Bayesian Dice configuration: {exc}") from exc
