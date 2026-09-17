"""Five frozen Version 1 leakage scenarios for Project 7."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression

from .contracts import EXPECTED_INPUT_COLUMNS
from .data import LoadedDataset
from .metrics import MetricBundle, evaluate_probabilities
from .modeling import MODEL_NAMES, SEED, build_model_pipeline, dataset_frame
from .preprocessing import pipeline_c_features
from .splits import (
    SplitIndices,
    chronological_split,
    dataset_fingerprints,
    overlap_counts,
    random_comparison_split,
)

AuditResult = Literal["PASS", "WARN", "BLOCK"]

TEMPORAL_BLOCK_ROC_AUC_GAP: Final[float] = 0.02
TEMPORAL_BLOCK_PR_AUC_GAP: Final[float] = 0.02
DUPLICATE_INJECTION_FRACTION: Final[float] = 0.10

SCENARIO_IDS: Final[tuple[str, ...]] = (
    "S1_CURRENT_CALL_DURATION",
    "S2_RANDOM_TEMPORAL_MIXING",
    "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
    "S4_DUPLICATE_OVERLAP",
    "S5_POST_OUTCOME_CONFIRMATION_PROXY",
)


@dataclass(frozen=True, slots=True)
class ModelComparison:
    """One unsafe-versus-safe model comparison."""

    model_id: str
    leaked_metrics: dict[str, float | int]
    safe_metrics: dict[str, float | int]
    metric_effect: dict[str, float]
    campaign_yield_overstatement: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class LeakageCaseRecord:
    """One frozen Step 3 leakage-case evidence record."""

    case_id: str
    name: str
    evidence_class: str
    setup: str
    expected_auditor_result: str
    actual_auditor_result: AuditResult
    violation: str
    metric_effect: dict[str, object]
    business_effect: dict[str, object]
    caveat: str
    required_correction: str
    observed_or_injected: str
    model_results: tuple[ModelComparison, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["model_results"] = [result.to_dict() for result in self.model_results]
        return payload


def scenario_catalog() -> tuple[dict[str, str], ...]:
    """Return exactly the five frozen Version 1 cases."""

    return (
        {
            "case_id": "S1_CURRENT_CALL_DURATION",
            "name": "Current-call duration",
            "evidence_class": "OBSERVED_DATASET_CONDITION",
            "expected_auditor_result": "BLOCK",
            "observed_or_injected": "OBSERVED",
        },
        {
            "case_id": "S2_RANDOM_TEMPORAL_MIXING",
            "name": "Random temporal mixing",
            "evidence_class": "EVALUATION_DESIGN_EXPERIMENT",
            "expected_auditor_result": "WARN_OR_BLOCK",
            "observed_or_injected": "EVALUATION_DESIGN_EXPERIMENT",
        },
        {
            "case_id": "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
            "name": "Global supervised transformation",
            "evidence_class": "CONTROLLED_INJECTION",
            "expected_auditor_result": "BLOCK",
            "observed_or_injected": "CONTROLLED_INJECTION",
        },
        {
            "case_id": "S4_DUPLICATE_OVERLAP",
            "name": "Duplicate overlap",
            "evidence_class": "CONTROLLED_INJECTION",
            "expected_auditor_result": "BLOCK",
            "observed_or_injected": "CONTROLLED_INJECTION",
        },
        {
            "case_id": "S5_POST_OUTCOME_CONFIRMATION_PROXY",
            "name": "Post-outcome confirmation proxy",
            "evidence_class": "CONTROLLED_INJECTION",
            "expected_auditor_result": "BLOCK",
            "observed_or_injected": "CONTROLLED_INJECTION",
        },
    )


def _take(
    frame: pd.DataFrame,
    target: pd.Series,
    indices: tuple[int, ...],
    features: tuple[str, ...],
) -> tuple[pd.DataFrame, pd.Series]:
    return (
        frame.iloc[list(indices)][list(features)],
        target.take(list(indices)),
    )


def _fit_metrics(
    frame: pd.DataFrame,
    target: pd.Series,
    train_indices: tuple[int, ...],
    test_indices: tuple[int, ...],
    features: tuple[str, ...],
    model_id: str,
) -> MetricBundle:
    """Fit on explicit training rows and evaluate explicit test rows."""

    x_train, y_train = _take(
        frame,
        target,
        train_indices,
        features,
    )

    x_test, y_test = _take(
        frame,
        target,
        test_indices,
        features,
    )

    estimator = build_model_pipeline(
        model_id,
        features,
    )

    estimator.fit(
        x_train,
        y_train,
    )

    probabilities = estimator.predict_proba(x_test)[:, 1]

    return evaluate_probabilities(
        y_test.tolist(),
        probabilities.tolist(),
    )


def _delta(
    leaked: MetricBundle,
    safe: MetricBundle,
) -> dict[str, float]:
    return {
        "roc_auc": leaked.roc_auc - safe.roc_auc,
        "pr_auc": leaked.pr_auc - safe.pr_auc,
        "brier_score_raw_difference": (leaked.brier_score - safe.brier_score),
        "expected_calibration_error_raw_difference": (
            leaked.expected_calibration_error - safe.expected_calibration_error
        ),
        "top_decile_lift": (leaked.top_decile_lift - safe.top_decile_lift),
        "conversions_per_1000": (leaked.conversions_per_1000 - safe.conversions_per_1000),
    }


def _comparison(
    model_id: str,
    leaked: MetricBundle,
    safe: MetricBundle,
) -> ModelComparison:
    return ModelComparison(
        model_id=model_id,
        leaked_metrics=leaked.to_dict(),
        safe_metrics=safe.to_dict(),
        metric_effect=_delta(
            leaked,
            safe,
        ),
        campaign_yield_overstatement=(leaked.conversions_per_1000 - safe.conversions_per_1000),
    )


def _safe_reference_metrics(
    frame: pd.DataFrame,
    target: pd.Series,
    chronological: SplitIndices,
) -> dict[str, MetricBundle]:
    features = pipeline_c_features()

    return {
        model_id: _fit_metrics(
            frame,
            target,
            chronological.train,
            chronological.test,
            features,
            model_id,
        )
        for model_id in MODEL_NAMES
    }


def _duration_features() -> tuple[str, ...]:
    safe = set(pipeline_c_features())

    return tuple(
        feature for feature in EXPECTED_INPUT_COLUMNS if feature in safe or feature == "duration"
    )


def temporal_audit_result(
    comparisons: tuple[ModelComparison, ...],
) -> AuditResult:
    """Scenario-level Step 3 policy; generalized auditor is Step 4."""

    should_block = any(
        result.metric_effect["roc_auc"] >= TEMPORAL_BLOCK_ROC_AUC_GAP
        or result.metric_effect["pr_auc"] >= TEMPORAL_BLOCK_PR_AUC_GAP
        for result in comparisons
    )

    return "BLOCK" if should_block else "WARN"


def duplicate_injection_indices(
    test_indices: tuple[int, ...],
    *,
    fraction: float = DUPLICATE_INJECTION_FRACTION,
) -> tuple[int, ...]:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1].")

    count = max(
        1,
        math.ceil(len(test_indices) * fraction),
    )

    return tuple(test_indices[:count])


def _case_duration(
    frame: pd.DataFrame,
    target: pd.Series,
    chronological: SplitIndices,
    safe: dict[str, MetricBundle],
) -> LeakageCaseRecord:
    features = _duration_features()

    comparisons = tuple(
        _comparison(
            model_id,
            _fit_metrics(
                frame,
                target,
                chronological.train,
                chronological.test,
                features,
                model_id,
            ),
            safe[model_id],
        )
        for model_id in MODEL_NAMES
    )

    return LeakageCaseRecord(
        case_id="S1_CURRENT_CALL_DURATION",
        name="Current-call duration",
        evidence_class="OBSERVED_DATASET_CONDITION",
        setup=("Include observed UCI duration in a model intended for pre-call ranking."),
        expected_auditor_result="BLOCK",
        actual_auditor_result="BLOCK",
        violation=(
            "duration is created during the current call and "
            "does not exist at the pre-call prediction moment."
        ),
        metric_effect={result.model_id: result.metric_effect for result in comparisons},
        business_effect={
            result.model_id: {"campaign_yield_overstatement": (result.campaign_yield_overstatement)}
            for result in comparisons
        },
        caveat=("The numerical inflation is measured rather than predetermined."),
        required_correction=("Remove duration from every pre-call ranking model."),
        observed_or_injected="OBSERVED",
        model_results=comparisons,
    )


def _case_temporal_mixing(
    frame: pd.DataFrame,
    target: pd.Series,
    chronological: SplitIndices,
    random_split: SplitIndices,
    safe: dict[str, MetricBundle],
) -> LeakageCaseRecord:
    features = pipeline_c_features()

    comparisons = tuple(
        _comparison(
            model_id,
            _fit_metrics(
                frame,
                target,
                random_split.train,
                random_split.test,
                features,
                model_id,
            ),
            safe[model_id],
        )
        for model_id in MODEL_NAMES
    )

    actual = temporal_audit_result(comparisons)

    return LeakageCaseRecord(
        case_id="S2_RANDOM_TEMPORAL_MIXING",
        name="Random temporal mixing",
        evidence_class="EVALUATION_DESIGN_EXPERIMENT",
        setup=(
            "Compare deterministic stratified random evaluation "
            "with chronological source-order evaluation."
        ),
        expected_auditor_result="WARN_OR_BLOCK",
        actual_auditor_result=actual,
        violation=("Random splitting mixes source-order periods and is not fully prospective."),
        metric_effect={result.model_id: result.metric_effect for result in comparisons},
        business_effect={
            result.model_id: {"campaign_yield_overstatement": (result.campaign_yield_overstatement)}
            for result in comparisons
        },
        caveat=("Source-order indices are used; no calendar dates are invented."),
        required_correction=("Use chronological source-order holdout for deployability evidence."),
        observed_or_injected="EVALUATION_DESIGN_EXPERIMENT",
        model_results=comparisons,
    )


def _target_mean_mapping(
    values: list[str],
    targets: list[int],
    fit_indices: tuple[int, ...],
) -> tuple[dict[str, float], float]:
    sums: dict[str, int] = {}
    counts: dict[str, int] = {}

    for index in fit_indices:
        key = values[index]

        sums[key] = (
            sums.get(
                key,
                0,
            )
            + targets[index]
        )

        counts[key] = (
            counts.get(
                key,
                0,
            )
            + 1
        )

    mapping = {key: sums[key] / counts[key] for key in sorted(counts)}

    fallback = sum(targets[index] for index in fit_indices) / len(fit_indices)

    return (
        mapping,
        fallback,
    )


def _encoded_values(
    values: list[str],
    mapping: dict[str, float],
    fallback: float,
    indices: tuple[int, ...],
) -> np.ndarray:
    return np.asarray(
        [
            mapping.get(
                values[index],
                fallback,
            )
            for index in indices
        ],
        dtype=float,
    ).reshape(-1, 1)


def _direct_numeric_model(
    model_id: str,
) -> Any:
    if model_id == "logistic_regression":
        return LogisticRegression(
            solver="liblinear",
            max_iter=1000,
            random_state=SEED,
        )

    if model_id == "histogram_gradient_boosting":
        return HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=120,
            max_leaf_nodes=15,
            min_samples_leaf=20,
            l2_regularization=0.1,
            random_state=SEED,
        )

    raise ValueError(f"Unknown model_id: {model_id}")


def _target_encoding_metrics(
    values: list[str],
    targets: list[int],
    chronological: SplitIndices,
    model_id: str,
    *,
    contaminated: bool,
) -> MetricBundle:
    fit_indices = tuple(range(len(targets))) if contaminated else chronological.train

    mapping, fallback = _target_mean_mapping(
        values,
        targets,
        fit_indices,
    )

    x_train = _encoded_values(
        values,
        mapping,
        fallback,
        chronological.train,
    )

    x_test = _encoded_values(
        values,
        mapping,
        fallback,
        chronological.test,
    )

    y_train = np.asarray(
        [targets[index] for index in chronological.train],
        dtype=int,
    )

    y_test = [targets[index] for index in chronological.test]

    estimator = _direct_numeric_model(model_id)

    estimator.fit(
        x_train,
        y_train,
    )

    probabilities = estimator.predict_proba(x_test)[:, 1]

    return evaluate_probabilities(
        y_test,
        probabilities.tolist(),
    )


def _case_global_transformation(
    frame: pd.DataFrame,
    target: pd.Series,
    chronological: SplitIndices,
) -> LeakageCaseRecord:
    values = frame["job"].astype(str).tolist()

    targets = [int(value) for value in target.tolist()]

    comparisons = tuple(
        _comparison(
            model_id,
            _target_encoding_metrics(
                values,
                targets,
                chronological,
                model_id,
                contaminated=True,
            ),
            _target_encoding_metrics(
                values,
                targets,
                chronological,
                model_id,
                contaminated=False,
            ),
        )
        for model_id in MODEL_NAMES
    )

    return LeakageCaseRecord(
        case_id="S3_GLOBAL_SUPERVISED_TRANSFORMATION",
        name="Global supervised transformation",
        evidence_class="CONTROLLED_INJECTION",
        setup=(
            "Fit deterministic job target-mean encoding on the "
            "complete dataset before splitting, then compare with "
            "training-only target encoding."
        ),
        expected_auditor_result="BLOCK",
        actual_auditor_result="BLOCK",
        violation=(
            "The contaminated transformation uses validation/test targets before model evaluation."
        ),
        metric_effect={result.model_id: result.metric_effect for result in comparisons},
        business_effect={
            result.model_id: {"campaign_yield_overstatement": (result.campaign_yield_overstatement)}
            for result in comparisons
        },
        caveat=(
            "Target encoding is a controlled injection and not an observed UCI transformation."
        ),
        required_correction=(
            "Split first and fit supervised transformations using training rows only."
        ),
        observed_or_injected="CONTROLLED_INJECTION",
        model_results=comparisons,
    )


def _case_duplicate_overlap(
    dataset: LoadedDataset,
    frame: pd.DataFrame,
    target: pd.Series,
    chronological: SplitIndices,
    safe: dict[str, MetricBundle],
) -> LeakageCaseRecord:
    injected = duplicate_injection_indices(chronological.test)

    contaminated_train = chronological.train + injected

    features = pipeline_c_features()

    comparisons = tuple(
        _comparison(
            model_id,
            _fit_metrics(
                frame,
                target,
                contaminated_train,
                chronological.test,
                features,
                model_id,
            ),
            safe[model_id],
        )
        for model_id in MODEL_NAMES
    )

    fingerprints = dataset_fingerprints(dataset)

    overlap = overlap_counts(
        fingerprints,
        SplitIndices(
            train=contaminated_train,
            validation=chronological.validation,
            test=chronological.test,
        ),
    )

    detected = overlap["train_test"]

    if detected <= 0:
        raise RuntimeError("Duplicate injection created no detectable overlap.")

    return LeakageCaseRecord(
        case_id="S4_DUPLICATE_OVERLAP",
        name="Duplicate overlap",
        evidence_class="CONTROLLED_INJECTION",
        setup=(
            f"Inject {len(injected)} deterministic test rows into "
            "training and independently detect exact-row overlap."
        ),
        expected_auditor_result="BLOCK",
        actual_auditor_result="BLOCK",
        violation=(f"Detected {detected} prohibited train/test row fingerprints."),
        metric_effect={result.model_id: result.metric_effect for result in comparisons},
        business_effect={
            "detected_train_test_overlap": detected,
            **{
                result.model_id: {
                    "campaign_yield_overstatement": (result.campaign_yield_overstatement)
                }
                for result in comparisons
            },
        },
        caveat=("Large metric inflation is not required for this integrity violation."),
        required_correction=(
            "Deduplicate and split before fitting; require zero prohibited train/test overlap."
        ),
        observed_or_injected="CONTROLLED_INJECTION",
        model_results=comparisons,
    )


def _case_post_outcome_proxy(
    frame: pd.DataFrame,
    target: pd.Series,
    chronological: SplitIndices,
    safe: dict[str, MetricBundle],
) -> LeakageCaseRecord:
    contaminated = frame.copy()

    proxy = "post_outcome_confirmation_proxy"

    contaminated[proxy] = [
        ("confirmed_positive" if int(value) == 1 else "confirmed_negative")
        for value in target.tolist()
    ]

    features = (
        *pipeline_c_features(),
        proxy,
    )

    comparisons = tuple(
        _comparison(
            model_id,
            _fit_metrics(
                contaminated,
                target,
                chronological.train,
                chronological.test,
                features,
                model_id,
            ),
            safe[model_id],
        )
        for model_id in MODEL_NAMES
    )

    return LeakageCaseRecord(
        case_id="S5_POST_OUTCOME_CONFIRMATION_PROXY",
        name="Post-outcome confirmation proxy",
        evidence_class="CONTROLLED_INJECTION",
        setup=("Create an explicitly synthetic confirmation feature derived from the target."),
        expected_auditor_result="BLOCK",
        actual_auditor_result="BLOCK",
        violation=(
            "The injected field is derived from the outcome and cannot exist at prediction time."
        ),
        metric_effect={result.model_id: result.metric_effect for result in comparisons},
        business_effect={
            result.model_id: {"campaign_yield_overstatement": (result.campaign_yield_overstatement)}
            for result in comparisons
        },
        caveat=(
            "This proxy is a benchmark-only controlled injection "
            "and is not an observed UCI variable."
        ),
        required_correction=("Remove all post-outcome proxies from training and scoring inputs."),
        observed_or_injected="CONTROLLED_INJECTION",
        model_results=comparisons,
    )


def run_leakage_cases(
    dataset: LoadedDataset,
) -> dict[str, Any]:
    """Execute exactly five deterministic Version 1 cases."""

    catalog = scenario_catalog()

    if tuple(row["case_id"] for row in catalog) != SCENARIO_IDS:
        raise RuntimeError("Scenario catalog differs from frozen order.")

    frame, target = dataset_frame(dataset)

    chronological = chronological_split(len(dataset.rows))

    random_split = random_comparison_split(
        target.tolist(),
        seed=SEED,
    )

    safe = _safe_reference_metrics(
        frame,
        target,
        chronological,
    )

    cases = (
        _case_duration(
            frame,
            target,
            chronological,
            safe,
        ),
        _case_temporal_mixing(
            frame,
            target,
            chronological,
            random_split,
            safe,
        ),
        _case_global_transformation(
            frame,
            target,
            chronological,
        ),
        _case_duplicate_overlap(
            dataset,
            frame,
            target,
            chronological,
            safe,
        ),
        _case_post_outcome_proxy(
            frame,
            target,
            chronological,
            safe,
        ),
    )

    if tuple(case.case_id for case in cases) != SCENARIO_IDS:
        raise RuntimeError("Scenario execution differs from frozen order.")

    payload: dict[str, Any] = {
        "scope": "PROJECT7_STEP3_FIVE_LEAKAGE_CASES",
        "seed": SEED,
        "scenario_count": 5,
        "scenario_ids": list(SCENARIO_IDS),
        "temporal_governance_policy": {
            "warn_default": True,
            "block_if_any_model_roc_auc_gap_gte": (TEMPORAL_BLOCK_ROC_AUC_GAP),
            "block_if_any_model_pr_auc_gap_gte": (TEMPORAL_BLOCK_PR_AUC_GAP),
        },
        "duplicate_injection_fraction": (DUPLICATE_INJECTION_FRACTION),
        "cases": [case.to_dict() for case in cases],
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=True,
    ).encode("utf-8")

    payload["step3_fingerprint_sha256"] = hashlib.sha256(canonical).hexdigest()

    return payload


def write_step3_evidence(
    payload: dict[str, Any],
    output_root: Path,
) -> tuple[Path, Path]:
    """Write deterministic Step 3 evidence artifacts."""

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_path = output_root / "leakage_case_results.json"

    manifest_path = output_root / "leakage_case_manifest.json"

    results_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            allow_nan=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    manifest = {
        "scope": payload["scope"],
        "seed": payload["seed"],
        "scenario_count": payload["scenario_count"],
        "scenario_ids": payload["scenario_ids"],
        "temporal_governance_policy": payload["temporal_governance_policy"],
        "duplicate_injection_fraction": payload["duplicate_injection_fraction"],
        "step3_fingerprint_sha256": payload["step3_fingerprint_sha256"],
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            allow_nan=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return (
        results_path,
        manifest_path,
    )
