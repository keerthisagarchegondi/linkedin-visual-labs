"""Prediction-Time Integrity Auditor."""

from .auditor import (
    AUDIT_ORDER,
    AuditFinding,
    EvidenceReference,
    ReleaseDecision,
    approve_public_claim,
    build_step4_audit,
    release_decision,
    write_step4_evidence,
)
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
from .validation import (
    IndependentValidation,
    MetricReconciliation,
    build_claim_register,
    build_release_data,
    freeze_step5_release,
    independently_validate,
    independently_validate_frozen_release,
)
from .video import VideoContract, load_video_evidence
from .visualization import render_all_figures

__all__ = [
    "AUDIT_ORDER",
    "DUPLICATE_INJECTION_FRACTION",
    "EXPECTED_COLUMNS",
    "EXPECTED_INPUT_COLUMNS",
    "MODEL_NAMES",
    "PREDICTION_MOMENT",
    "SCENARIO_IDS",
    "TEMPORAL_BLOCK_PR_AUC_GAP",
    "TEMPORAL_BLOCK_ROC_AUC_GAP",
    "AuditFinding",
    "AvailabilityClass",
    "EvidenceReference",
    "IndependentValidation",
    "MetricBundle",
    "MetricReconciliation",
    "ProjectConfig",
    "ReleaseDecision",
    "SplitConfig",
    "SplitIndices",
    "VideoContract",
    "acquire_official_source",
    "approve_public_claim",
    "blocked_feature_names",
    "build_claim_register",
    "build_feature_contract",
    "build_model_pipeline",
    "build_release_data",
    "build_step4_audit",
    "chronological_split",
    "deployment_feature_names",
    "duplicate_injection_indices",
    "evaluate_probabilities",
    "freeze_step5_release",
    "independently_validate",
    "independently_validate_frozen_release",
    "load_config",
    "load_official_dataset",
    "load_video_evidence",
    "pipeline_b_features",
    "pipeline_c_features",
    "random_comparison_split",
    "release_decision",
    "render_all_figures",
    "run_baselines",
    "run_leakage_cases",
    "scenario_catalog",
    "temporal_audit_result",
    "write_step3_evidence",
    "write_step4_evidence",
]

__version__ = "0.7.0"
