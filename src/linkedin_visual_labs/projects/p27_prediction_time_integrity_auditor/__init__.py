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
from .data import acquire_official_source, load_official_dataset
from .leakage_cases import (
    DUPLICATE_INJECTION_FRACTION,
    SCENARIO_IDS,
    TEMPORAL_BLOCK_PR_AUC_GAP,
    TEMPORAL_BLOCK_ROC_AUC_GAP,
    duplicate_injection_indices,
    run_leakage_cases,
    scenario_catalog,
    temporal_audit_result,
    write_step3_evidence,
)
from .metrics import MetricBundle, evaluate_probabilities
from .modeling import MODEL_NAMES, build_model_pipeline, run_baselines
from .models import AvailabilityClass, ProjectConfig, SplitConfig
from .preprocessing import pipeline_b_features, pipeline_c_features
from .splits import (
    SplitIndices,
    chronological_split,
    random_comparison_split,
)

__all__ = [
    "DUPLICATE_INJECTION_FRACTION",
    "EXPECTED_COLUMNS",
    "EXPECTED_INPUT_COLUMNS",
    "MODEL_NAMES",
    "PREDICTION_MOMENT",
    "SCENARIO_IDS",
    "TEMPORAL_BLOCK_PR_AUC_GAP",
    "TEMPORAL_BLOCK_ROC_AUC_GAP",
    "AvailabilityClass",
    "MetricBundle",
    "ProjectConfig",
    "SplitConfig",
    "SplitIndices",
    "acquire_official_source",
    "blocked_feature_names",
    "build_feature_contract",
    "build_model_pipeline",
    "chronological_split",
    "deployment_feature_names",
    "duplicate_injection_indices",
    "evaluate_probabilities",
    "load_config",
    "load_official_dataset",
    "pipeline_b_features",
    "pipeline_c_features",
    "random_comparison_split",
    "run_baselines",
    "run_leakage_cases",
    "scenario_catalog",
    "temporal_audit_result",
    "write_step3_evidence",
]

__version__ = "0.4.0"
