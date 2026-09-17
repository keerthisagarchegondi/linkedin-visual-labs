"""Prediction-Time Integrity Auditor."""

from .config import load_config
from .contracts import (
    EXPECTED_COLUMNS,
    EXPECTED_INPUT_COLUMNS,
    PREDICTION_MOMENT,
    blocked_feature_names,
    build_feature_contract,
    deployment_feature_names,
)
from .data import (
    acquire_official_source,
    load_official_dataset,
)
from .models import (
    AvailabilityClass,
    ProjectConfig,
    SplitConfig,
)

__all__ = [
    "EXPECTED_COLUMNS",
    "EXPECTED_INPUT_COLUMNS",
    "PREDICTION_MOMENT",
    "AvailabilityClass",
    "ProjectConfig",
    "SplitConfig",
    "acquire_official_source",
    "blocked_feature_names",
    "build_feature_contract",
    "deployment_feature_names",
    "load_config",
    "load_official_dataset",
]

__version__ = "0.2.0"
