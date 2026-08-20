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
    DieTypeDefinition,
    OutputContract,
    PairCaseDefinition,
    PairDecisionDefinition,
    PairExperimentDefinition,
    PairModelPriorDefinition,
    PairObservationDefinition,
    PairOutputContract,
    PairPanelPlacement,
    PairVideoContract,
    PixelRegion,
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
        (
            str,
            bytes,
        ),
    ):
        return value

    raise DiceConfigurationError(f"{name} must be a sequence")


def _int_value(
    value: object,
    *,
    name: str,
) -> int:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        int,
    ):
        raise DiceConfigurationError(f"{name} must be an integer")

    return value


def _float_value(
    value: object,
    *,
    name: str,
) -> float:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        (
            int,
            float,
        ),
    ):
        raise DiceConfigurationError(f"{name} must be numeric")

    return float(value)


def _bool_value(
    value: object,
    *,
    name: str,
) -> bool:
    if not isinstance(
        value,
        bool,
    ):
        raise DiceConfigurationError(f"{name} must be a boolean")

    return value


def _string_value(
    value: object,
    *,
    name: str,
) -> str:
    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise DiceConfigurationError(f"{name} must be a non-empty string")

    return value


def _relative_project_output(
    value: object,
    *,
    name: str,
) -> Path:
    text = _string_value(
        value,
        name=name,
    )

    path = Path(text)

    if path.is_absolute():
        raise DiceConfigurationError(f"{name} must be repository-relative")

    project_root = Path("outputs/p01_bayesian_dice")

    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise DiceConfigurationError(f"{name} must remain under outputs/p01_bayesian_dice") from exc

    return path


###############################################################################
# AUTHORITATIVE PAIR CONFIGURATION
###############################################################################


def _build_pair_die_types(
    raw: object,
) -> dict[
    str,
    DieTypeDefinition,
]:
    mapping = _mapping(
        raw,
        name="pair_experiment.die_types",
    )

    result: dict[
        str,
        DieTypeDefinition,
    ] = {}

    for type_id, raw_definition in mapping.items():
        definition = _mapping(
            raw_definition,
            name=f"pair_experiment.die_types.{type_id}",
        )

        require_keys(
            definition,
            (
                "id",
                "label",
                "probabilities",
            ),
            name=f"pair_experiment.die_types.{type_id}",
        )

        result[type_id] = DieTypeDefinition(
            type_id=type_id,
            short_id=_string_value(
                definition["id"],
                name=f"{type_id}.id",
            ),
            label=_string_value(
                definition["label"],
                name=f"{type_id}.label",
            ),
            probabilities=(
                ProbabilityVector.from_sequence(
                    _sequence(
                        definition["probabilities"],
                        name=(f"{type_id}.probabilities"),
                    )
                )
            ),
        )

    return result


def _build_pair_cases(
    raw: object,
) -> dict[
    str,
    PairCaseDefinition,
]:
    mapping = _mapping(
        raw,
        name="pair_experiment.pair_cases",
    )

    result: dict[
        str,
        PairCaseDefinition,
    ] = {}

    for case_id, raw_definition in mapping.items():
        definition = _mapping(
            raw_definition,
            name=f"pair_experiment.pair_cases.{case_id}",
        )

        require_keys(
            definition,
            (
                "label",
                "die_1",
                "die_2",
                "truth_loaded",
                "seed",
            ),
            name=f"pair_experiment.pair_cases.{case_id}",
        )

        result[case_id] = PairCaseDefinition(
            case_id=case_id,
            label=_string_value(
                definition["label"],
                name=f"{case_id}.label",
            ),
            die_1_type=_string_value(
                definition["die_1"],
                name=f"{case_id}.die_1",
            ),
            die_2_type=_string_value(
                definition["die_2"],
                name=f"{case_id}.die_2",
            ),
            truth_loaded=_bool_value(
                definition["truth_loaded"],
                name=f"{case_id}.truth_loaded",
            ),
            seed=_int_value(
                definition["seed"],
                name=f"{case_id}.seed",
            ),
        )

    return result


def _build_pair_outputs(
    raw: object,
) -> PairOutputContract:
    outputs = _mapping(
        raw,
        name="pair_experiment.outputs",
    )

    required = (
        "simulation",
        "history",
        "summary",
        "validation",
        "preview_directory",
        "video",
        "manifest",
    )

    require_keys(
        outputs,
        required,
        name="pair_experiment.outputs",
    )

    parsed: dict[
        str,
        Path,
    ] = {}

    for key in required:
        entry = _mapping(
            outputs[key],
            name=f"pair_experiment.outputs.{key}",
        )

        require_keys(
            entry,
            ("path",),
            name=f"pair_experiment.outputs.{key}",
        )

        parsed[key] = _relative_project_output(
            entry["path"],
            name=f"pair_experiment.outputs.{key}.path",
        )

    return PairOutputContract(
        simulation=parsed["simulation"],
        history=parsed["history"],
        summary=parsed["summary"],
        validation=parsed["validation"],
        preview_directory=parsed["preview_directory"],
        video=parsed["video"],
        manifest=parsed["manifest"],
    )


def _pixel_region(
    raw: object,
    *,
    name: str,
) -> PixelRegion:
    value = _mapping(
        raw,
        name=name,
    )

    require_keys(
        value,
        (
            "x_px",
            "y_px",
            "width_px",
            "height_px",
        ),
        name=name,
    )

    return PixelRegion(
        x_px=_int_value(
            value["x_px"],
            name=f"{name}.x_px",
        ),
        y_px=_int_value(
            value["y_px"],
            name=f"{name}.y_px",
        ),
        width_px=_int_value(
            value["width_px"],
            name=f"{name}.width_px",
        ),
        height_px=_int_value(
            value["height_px"],
            name=f"{name}.height_px",
        ),
    )


def _build_pair_video(
    raw: object,
) -> PairVideoContract:
    video = _mapping(
        raw,
        name="pair_experiment.video",
    )

    require_keys(
        video,
        (
            "width_px",
            "height_px",
            "aspect_ratio",
            "frame_rate",
            "target_duration_seconds",
            "heading",
            "middle_grid",
            "panels",
            "result_strip",
            "technical_footer",
            "typography",
        ),
        name="pair_experiment.video",
    )

    heading_mapping = _mapping(
        video["heading"],
        name="pair_experiment.video.heading",
    )

    require_keys(
        heading_mapping,
        ("text",),
        name="pair_experiment.video.heading",
    )

    grid_mapping = _mapping(
        video["middle_grid"],
        name="pair_experiment.video.middle_grid",
    )

    require_keys(
        grid_mapping,
        (
            "columns",
            "rows",
            "panel_width_px",
            "panel_height_px",
        ),
        name="pair_experiment.video.middle_grid",
    )

    result_mapping = _mapping(
        video["result_strip"],
        name="pair_experiment.video.result_strip",
    )

    require_keys(
        result_mapping,
        (
            "cell_count",
            "cell_width_px",
        ),
        name="pair_experiment.video.result_strip",
    )

    typography = _mapping(
        video["typography"],
        name="pair_experiment.video.typography",
    )

    require_keys(
        typography,
        (
            "auto_fit",
            "enforce_region_bounds",
            "allow_text_clipping",
            "allow_artist_overlap",
        ),
        name="pair_experiment.video.typography",
    )

    panel_placements: list[PairPanelPlacement] = []

    for raw_panel in _sequence(
        video["panels"],
        name="pair_experiment.video.panels",
    ):
        panel = _mapping(
            raw_panel,
            name="pair_experiment.video.panel",
        )

        require_keys(
            panel,
            (
                "case_id",
                "row",
                "column",
            ),
            name="pair_experiment.video.panel",
        )

        panel_placements.append(
            PairPanelPlacement(
                case_id=_string_value(
                    panel["case_id"],
                    name="panel.case_id",
                ),
                row=_int_value(
                    panel["row"],
                    name="panel.row",
                ),
                column=_int_value(
                    panel["column"],
                    name="panel.column",
                ),
            )
        )

    return PairVideoContract(
        width_px=_int_value(
            video["width_px"],
            name="pair_experiment.video.width_px",
        ),
        height_px=_int_value(
            video["height_px"],
            name="pair_experiment.video.height_px",
        ),
        aspect_ratio=_string_value(
            video["aspect_ratio"],
            name="pair_experiment.video.aspect_ratio",
        ),
        frame_rate=_int_value(
            video["frame_rate"],
            name="pair_experiment.video.frame_rate",
        ),
        target_duration_seconds=_float_value(
            video["target_duration_seconds"],
            name="pair_experiment.video.target_duration_seconds",
        ),
        heading=_pixel_region(
            video["heading"],
            name="pair_experiment.video.heading",
        ),
        heading_text=_string_value(
            heading_mapping["text"],
            name="pair_experiment.video.heading.text",
        ),
        middle_grid=_pixel_region(
            video["middle_grid"],
            name="pair_experiment.video.middle_grid",
        ),
        columns=_int_value(
            grid_mapping["columns"],
            name="pair_experiment.video.middle_grid.columns",
        ),
        rows=_int_value(
            grid_mapping["rows"],
            name="pair_experiment.video.middle_grid.rows",
        ),
        panel_width_px=_int_value(
            grid_mapping["panel_width_px"],
            name="pair_experiment.video.middle_grid.panel_width_px",
        ),
        panel_height_px=_int_value(
            grid_mapping["panel_height_px"],
            name="pair_experiment.video.middle_grid.panel_height_px",
        ),
        panel_placements=tuple(panel_placements),
        result_strip=_pixel_region(
            video["result_strip"],
            name="pair_experiment.video.result_strip",
        ),
        result_cell_count=_int_value(
            result_mapping["cell_count"],
            name="pair_experiment.video.result_strip.cell_count",
        ),
        result_cell_width_px=_int_value(
            result_mapping["cell_width_px"],
            name="pair_experiment.video.result_strip.cell_width_px",
        ),
        technical_footer=_string_value(
            video["technical_footer"],
            name="pair_experiment.video.technical_footer",
        ),
        auto_fit_typography=_bool_value(
            typography["auto_fit"],
            name="pair_experiment.video.typography.auto_fit",
        ),
        enforce_region_bounds=_bool_value(
            typography["enforce_region_bounds"],
            name=("pair_experiment.video.typography.enforce_region_bounds"),
        ),
        allow_text_clipping=_bool_value(
            typography["allow_text_clipping"],
            name=("pair_experiment.video.typography.allow_text_clipping"),
        ),
        allow_artist_overlap=_bool_value(
            typography["allow_artist_overlap"],
            name=("pair_experiment.video.typography.allow_artist_overlap"),
        ),
    )


def _build_pair_experiment(
    raw: object,
) -> PairExperimentDefinition:
    pair = _mapping(
        raw,
        name="pair_experiment",
    )

    require_keys(
        pair,
        (
            "authoritative",
            "viewer_question",
            "observation",
            "roll_count_per_case",
            "die_types",
            "pair_cases",
            "pair_order",
            "bayesian_models",
            "decision",
            "outputs",
            "video",
        ),
        name="pair_experiment",
    )

    observation = _mapping(
        pair["observation"],
        name="pair_experiment.observation",
    )

    require_keys(
        observation,
        (
            "type",
            "minimum",
            "maximum",
            "individual_faces_visible_to_inference",
        ),
        name="pair_experiment.observation",
    )

    bayesian_models = _mapping(
        pair["bayesian_models"],
        name="pair_experiment.bayesian_models",
    )

    require_keys(
        bayesian_models,
        (
            "sum_probabilities",
            "model_priors",
            "loaded_probability_definition",
        ),
        name="pair_experiment.bayesian_models",
    )

    sum_probabilities = _mapping(
        bayesian_models["sum_probabilities"],
        name="pair_experiment.bayesian_models.sum_probabilities",
    )

    require_keys(
        sum_probabilities,
        (
            "derive_by_convolution",
            "hard_code_sum_pmf",
        ),
        name="pair_experiment.bayesian_models.sum_probabilities",
    )

    raw_priors = _mapping(
        bayesian_models["model_priors"],
        name="pair_experiment.bayesian_models.model_priors",
    )

    priors = {
        case_id: _float_value(
            value,
            name=f"model_priors.{case_id}",
        )
        for case_id, value in raw_priors.items()
    }

    decision = _mapping(
        pair["decision"],
        name="pair_experiment.decision",
    )

    require_keys(
        decision,
        (
            "fair_threshold",
            "loaded_threshold",
            "headline_roll_metric",
            "stable_decision_definition",
        ),
        name="pair_experiment.decision",
    )

    stable = _mapping(
        decision["stable_decision_definition"],
        name="pair_experiment.decision.stable_decision_definition",
    )

    require_keys(
        stable,
        (
            "require_same_final_state_through_end",
            "use_first_threshold_crossing_as_headline",
        ),
        name="pair_experiment.decision.stable_decision_definition",
    )

    pair_order = tuple(
        _string_value(
            value,
            name="pair_experiment.pair_order",
        )
        for value in _sequence(
            pair["pair_order"],
            name="pair_experiment.pair_order",
        )
    )

    return PairExperimentDefinition(
        authoritative=_bool_value(
            pair["authoritative"],
            name="pair_experiment.authoritative",
        ),
        viewer_question=_string_value(
            pair["viewer_question"],
            name="pair_experiment.viewer_question",
        ),
        observation=PairObservationDefinition(
            observation_type=_string_value(
                observation["type"],
                name="pair_experiment.observation.type",
            ),
            minimum=_int_value(
                observation["minimum"],
                name="pair_experiment.observation.minimum",
            ),
            maximum=_int_value(
                observation["maximum"],
                name="pair_experiment.observation.maximum",
            ),
            individual_faces_visible_to_inference=_bool_value(
                observation["individual_faces_visible_to_inference"],
                name=("pair_experiment.observation.individual_faces_visible_to_inference"),
            ),
        ),
        roll_count_per_case=_int_value(
            pair["roll_count_per_case"],
            name="pair_experiment.roll_count_per_case",
        ),
        die_types=_build_pair_die_types(pair["die_types"]),
        pair_cases=_build_pair_cases(pair["pair_cases"]),
        pair_order=pair_order,
        model_priors=PairModelPriorDefinition(values=priors),
        loaded_probability_definition=_string_value(
            bayesian_models["loaded_probability_definition"],
            name=("pair_experiment.bayesian_models.loaded_probability_definition"),
        ),
        derive_sum_pmf_by_convolution=_bool_value(
            sum_probabilities["derive_by_convolution"],
            name=("pair_experiment.bayesian_models.sum_probabilities.derive_by_convolution"),
        ),
        hard_code_sum_pmf=_bool_value(
            sum_probabilities["hard_code_sum_pmf"],
            name=("pair_experiment.bayesian_models.sum_probabilities.hard_code_sum_pmf"),
        ),
        decision=PairDecisionDefinition(
            fair_threshold=_float_value(
                decision["fair_threshold"],
                name="pair_experiment.decision.fair_threshold",
            ),
            loaded_threshold=_float_value(
                decision["loaded_threshold"],
                name="pair_experiment.decision.loaded_threshold",
            ),
            headline_roll_metric=_string_value(
                decision["headline_roll_metric"],
                name="pair_experiment.decision.headline_roll_metric",
            ),
            require_same_final_state_through_end=_bool_value(
                stable["require_same_final_state_through_end"],
                name=("pair_experiment.decision.require_same_final_state_through_end"),
            ),
            use_first_threshold_crossing_as_headline=_bool_value(
                stable["use_first_threshold_crossing_as_headline"],
                name=("pair_experiment.decision.use_first_threshold_crossing_as_headline"),
            ),
        ),
        outputs=_build_pair_outputs(pair["outputs"]),
        video=_build_pair_video(pair["video"]),
    )


###############################################################################
# TEMPORARY LEGACY CONFIGURATION
###############################################################################


def _build_legacy_scenarios(
    raw: object,
) -> dict[
    str,
    ScenarioDefinition,
]:
    scenarios_mapping = _mapping(
        raw,
        name="simulation.scenarios",
    )

    scenarios: dict[
        str,
        ScenarioDefinition,
    ] = {}

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


def _build_legacy_output_contract(
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

    parsed: dict[
        str,
        Path,
    ] = {}

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

        parsed[key] = _relative_project_output(
            entry["path"],
            name=f"outputs.{key}.path",
        )

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
    """Load transitional Project 1 YAML into typed domain models."""
    config_path = Path(path)

    try:
        raw = load_yaml_config(
            config_path,
            required_keys=(
                "project",
                "pair_experiment",
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

        pair_experiment = _build_pair_experiment(raw["pair_experiment"])

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
                name=("model.hypotheses.loaded.dirichlet_alpha"),
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
            pair_experiment=pair_experiment,
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
            scenarios=_build_legacy_scenarios(simulation["scenarios"]),
            showcase_scenario=_string_value(
                simulation["showcase_scenario"],
                name="simulation.showcase_scenario",
            ),
            calibration=CalibrationDefinition(
                repetitions_per_scenario=_int_value(
                    calibration["repetitions_per_scenario"],
                    name=("calibration.repetitions_per_scenario"),
                ),
                master_seed=_int_value(
                    calibration["master_seed"],
                    name="calibration.master_seed",
                ),
                posterior_bucket_count=_int_value(
                    calibration["posterior_bucket_count"],
                    name=("calibration.posterior_bucket_count"),
                ),
                prior_sensitivity=prior_sensitivity,
                primary_loaded_scenario=_string_value(
                    calibration["primary_loaded_scenario"],
                    name=("calibration.primary_loaded_scenario"),
                ),
            ),
            outputs=_build_legacy_output_contract(raw["outputs"]),
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
