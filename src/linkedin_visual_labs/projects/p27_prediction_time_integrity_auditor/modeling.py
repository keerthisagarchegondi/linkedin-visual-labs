"""Deterministic Step 2 baseline modeling."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .data import LoadedDataset
from .metrics import evaluate_probabilities
from .preprocessing import (
    histogram_preprocessor,
    logistic_preprocessor,
    pipeline_b_features,
    pipeline_c_features,
)
from .splits import (
    SplitIndices,
    chronological_split,
    dataset_fingerprints,
    overlap_counts,
    random_comparison_split,
    split_summary,
    validate_chronological_order,
)

SEED: Final[int] = 1729

MODEL_NAMES: Final[tuple[str, ...]] = (
    "logistic_regression",
    "histogram_gradient_boosting",
)


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    """One model/pipeline/partition evaluation."""

    pipeline_id: str
    model_id: str
    partition: str
    feature_count: int
    train_rows: int
    evaluation_rows: int
    metrics: dict[str, float | int]

    def to_dict(self) -> dict[str, object]:
        return {
            "pipeline_id": self.pipeline_id,
            "model_id": self.model_id,
            "partition": self.partition,
            "feature_count": self.feature_count,
            "train_rows": self.train_rows,
            "evaluation_rows": self.evaluation_rows,
            "metrics": self.metrics,
        }


def dataset_frame(
    dataset: LoadedDataset,
) -> tuple[pd.DataFrame, pd.Series]:
    """Convert strict Step 1 rows to modeling frame and target."""

    frame = pd.DataFrame(dataset.rows)

    target = pd.Series(
        dataset.normalized_target,
        name="y",
        dtype="int64",
    )

    numeric = (
        "age",
        "duration",
        "campaign",
        "pdays",
        "previous",
        "emp.var.rate",
        "cons.price.idx",
        "cons.conf.idx",
        "euribor3m",
        "nr.employed",
    )

    for column in numeric:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    return frame, target


def build_model_pipeline(
    model_id: str,
    features: tuple[str, ...],
) -> Pipeline:
    """Create one predetermined model configuration."""

    if model_id == "logistic_regression":
        return Pipeline(
            steps=[
                (
                    "preprocessor",
                    logistic_preprocessor(features),
                ),
                (
                    "model",
                    LogisticRegression(
                        solver="liblinear",
                        max_iter=1000,
                        random_state=SEED,
                    ),
                ),
            ]
        )

    if model_id == "histogram_gradient_boosting":
        return Pipeline(
            steps=[
                (
                    "preprocessor",
                    histogram_preprocessor(features),
                ),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        learning_rate=0.08,
                        max_iter=120,
                        max_leaf_nodes=15,
                        min_samples_leaf=20,
                        l2_regularization=0.1,
                        random_state=SEED,
                    ),
                ),
            ]
        )

    raise ValueError(f"Unknown model_id: {model_id}")


def model_parameter_manifest() -> dict[str, object]:
    """Frozen bounded model configurations."""

    return {
        "logistic_regression": {
            "solver": "liblinear",
            "max_iter": 1000,
            "random_state": SEED,
        },
        "histogram_gradient_boosting": {
            "learning_rate": 0.08,
            "max_iter": 120,
            "max_leaf_nodes": 15,
            "min_samples_leaf": 20,
            "l2_regularization": 0.1,
            "random_state": SEED,
        },
    }


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


def _evaluate_one(
    frame: pd.DataFrame,
    target: pd.Series,
    split: SplitIndices,
    *,
    pipeline_id: str,
    model_id: str,
    features: tuple[str, ...],
) -> list[EvaluationRecord]:
    """Fit train only, then evaluate validation/test."""

    x_train, y_train = _take(
        frame,
        target,
        split.train,
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

    records: list[EvaluationRecord] = []

    for partition, indices in (
        (
            "validation",
            split.validation,
        ),
        (
            "test",
            split.test,
        ),
    ):
        x_eval, y_eval = _take(
            frame,
            target,
            indices,
            features,
        )

        probabilities = estimator.predict_proba(x_eval)[:, 1]

        bundle = evaluate_probabilities(
            y_eval.tolist(),
            probabilities.tolist(),
        )

        records.append(
            EvaluationRecord(
                pipeline_id=pipeline_id,
                model_id=model_id,
                partition=partition,
                feature_count=len(features),
                train_rows=len(split.train),
                evaluation_rows=len(indices),
                metrics=bundle.to_dict(),
            )
        )

    return records


def run_baselines(
    dataset: LoadedDataset,
) -> dict[str, Any]:
    """Execute deterministic Pipeline B/C baseline evaluation."""

    frame, target = dataset_frame(dataset)

    y = target.tolist()

    chronological = chronological_split(len(dataset.rows))

    validate_chronological_order(chronological)

    random = random_comparison_split(
        y,
        seed=SEED,
    )

    fingerprints = dataset_fingerprints(dataset)

    chronological_overlap = overlap_counts(
        fingerprints,
        chronological,
    )

    if any(chronological_overlap.values()):
        raise RuntimeError("Prediction-time-safe chronological split contains exact-row overlap.")

    pipeline_b = pipeline_b_features()
    pipeline_c = pipeline_c_features()

    if "duration" in pipeline_b:
        raise RuntimeError("Pipeline B cannot contain duration.")

    if {
        "duration",
        "campaign",
    } & set(pipeline_c):
        raise RuntimeError("Pipeline C contains a blocked/unknown feature.")

    evaluations: list[EvaluationRecord] = []

    for model_id in MODEL_NAMES:
        evaluations.extend(
            _evaluate_one(
                frame,
                target,
                random,
                pipeline_id="B_PARTIALLY_CORRECTED",
                model_id=model_id,
                features=pipeline_b,
            )
        )

        evaluations.extend(
            _evaluate_one(
                frame,
                target,
                chronological,
                pipeline_id="C_PREDICTION_TIME_SAFE",
                model_id=model_id,
                features=pipeline_c,
            )
        )

    payload: dict[str, Any] = {
        "scope": "PROJECT7_STEP2_BASELINE_ONLY",
        "seed": SEED,
        "models": list(MODEL_NAMES),
        "model_parameters": model_parameter_manifest(),
        "pipelines": {
            "B_PARTIALLY_CORRECTED": {
                "split": "STRATIFIED_RANDOM_70_15_15",
                "features": list(pipeline_b),
                "duration_removed": True,
                "fully_prediction_time_safe": False,
            },
            "C_PREDICTION_TIME_SAFE": {
                "split": "CHRONOLOGICAL_SOURCE_ORDER_70_15_15",
                "features": list(pipeline_c),
                "blocked_features_absent": True,
                "fully_prediction_time_safe": True,
            },
        },
        "splits": {
            "chronological": split_summary(
                y,
                fingerprints,
                chronological,
                policy="CHRONOLOGICAL_SOURCE_ORDER_70_15_15",
                seed=None,
            ),
            "random_comparison": split_summary(
                y,
                fingerprints,
                random,
                policy="STRATIFIED_RANDOM_70_15_15",
                seed=SEED,
            ),
        },
        "evaluations": [record.to_dict() for record in evaluations],
    }

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=True,
    ).encode("utf-8")

    payload["baseline_fingerprint_sha256"] = hashlib.sha256(canonical).hexdigest()

    return payload
