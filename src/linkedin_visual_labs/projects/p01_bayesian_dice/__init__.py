"""Bayesian Dice Detective project package."""

from linkedin_visual_labs.projects.p01_bayesian_dice.config import (
    DEFAULT_CONFIG_PATH,
    DiceConfigurationError,
    load_dice_config,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.models import (
    FACE_COUNT,
    PROBABILITY_SUM_TOLERANCE,
    BayesianModelDefinition,
    CalibrationDefinition,
    DecisionState,
    DecisionThresholds,
    DiceModelError,
    DiceProjectConfig,
    OutputContract,
    ProbabilityVector,
    ScenarioDefinition,
    VideoContract,
)
from linkedin_visual_labs.projects.p01_bayesian_dice.pipeline import (
    DicePipelineContext,
    build_pipeline_context,
)

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "FACE_COUNT",
    "PROBABILITY_SUM_TOLERANCE",
    "BayesianModelDefinition",
    "CalibrationDefinition",
    "DecisionState",
    "DecisionThresholds",
    "DiceConfigurationError",
    "DiceModelError",
    "DicePipelineContext",
    "DiceProjectConfig",
    "OutputContract",
    "ProbabilityVector",
    "ScenarioDefinition",
    "VideoContract",
    "build_pipeline_context",
    "load_dice_config",
]
