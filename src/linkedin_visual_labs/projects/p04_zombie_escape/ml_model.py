"""Classical Gradient Boosting risk model for Zombie Escape."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingRegressor,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

from linkedin_visual_labs.projects.p04_zombie_escape.ml_features import (
    FEATURE_COLUMNS,
    LABEL_COLUMN,
)


@dataclass(frozen=True, slots=True)
class RiskModelMetrics:
    """Deterministic regression metrics."""

    mae: float
    rmse: float
    r2: float


@dataclass(frozen=True, slots=True)
class TrainedMLRiskModel:
    """Model plus deterministic training/evaluation metadata."""

    model: HistGradientBoostingRegressor
    feature_columns: tuple[str, ...]
    validation_metrics: RiskModelMetrics
    benchmark_metrics: RiskModelMetrics
    training_rows: int
    validation_rows: int
    benchmark_rows: int
    random_seed: int


def train_ml_risk_model(
    dataset: pd.DataFrame,
    *,
    random_seed: int,
) -> TrainedMLRiskModel:
    """Train deterministic Gradient Boosting without hidden-feature leakage."""
    train = dataset[dataset["split"] == "training"]

    validation = dataset[dataset["split"] == "validation"]

    benchmark = dataset[dataset["split"] == "benchmark"]

    if train.empty or validation.empty or benchmark.empty:
        raise ValueError("Training, validation, and benchmark splits must all be non-empty")

    model = HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.08,
        max_iter=220,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        l2_regularization=0.10,
        random_state=random_seed,
    )

    model.fit(
        train.loc[
            :,
            FEATURE_COLUMNS,
        ],
        train[LABEL_COLUMN],
    )

    validation_metrics = _metrics(
        validation[LABEL_COLUMN].to_numpy(),
        model.predict(
            validation.loc[
                :,
                FEATURE_COLUMNS,
            ]
        ),
    )

    benchmark_metrics = _metrics(
        benchmark[LABEL_COLUMN].to_numpy(),
        model.predict(
            benchmark.loc[
                :,
                FEATURE_COLUMNS,
            ]
        ),
    )

    return TrainedMLRiskModel(
        model=model,
        feature_columns=FEATURE_COLUMNS,
        validation_metrics=validation_metrics,
        benchmark_metrics=benchmark_metrics,
        training_rows=len(train),
        validation_rows=len(validation),
        benchmark_rows=len(benchmark),
        random_seed=random_seed,
    )


def predict_risk(
    trained: TrainedMLRiskModel,
    features: pd.DataFrame,
) -> npt.NDArray[np.float64]:
    """Predict and clamp per-cell risk to the simulator range [0, 1]."""
    missing = set(trained.feature_columns) - set(features.columns)

    if missing:
        raise ValueError("Missing ML feature columns: " + ", ".join(sorted(missing)))

    model_features = features.loc[
        :,
        list(trained.feature_columns),
    ]

    predictions: npt.NDArray[np.float64] = np.asarray(
        trained.model.predict(model_features),
        dtype=np.float64,
    )

    clipped: npt.NDArray[np.float64] = np.asarray(
        np.clip(
            predictions,
            0.0,
            1.0,
        ),
        dtype=np.float64,
    )

    return clipped


def persist_ml_risk_model(
    trained: TrainedMLRiskModel,
    directory: Path,
) -> tuple[
    Path,
    Path,
]:
    """Persist model binary and human-readable metadata."""
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = directory / "model.joblib"

    metadata_path = directory / "metadata.json"

    joblib.dump(
        trained.model,
        model_path,
        compress=3,
    )

    metadata: dict[
        str,
        Any,
    ] = {
        "schema_version": 1,
        "model_family": "gradient_boosting",
        "implementation": ("HistGradientBoostingRegressor"),
        "random_seed": (trained.random_seed),
        "feature_columns": list(trained.feature_columns),
        "training_rows": (trained.training_rows),
        "validation_rows": (trained.validation_rows),
        "benchmark_rows": (trained.benchmark_rows),
        "validation_metrics": {
            "mae": (trained.validation_metrics.mae),
            "rmse": (trained.validation_metrics.rmse),
            "r2": (trained.validation_metrics.r2),
        },
        "benchmark_metrics": {
            "mae": (trained.benchmark_metrics.mae),
            "rmse": (trained.benchmark_metrics.rmse),
            "r2": (trained.benchmark_metrics.r2),
        },
        "hidden_truth_feature_leakage": False,
    }

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        model_path,
        metadata_path,
    )


def _metrics(
    truth: np.ndarray,
    prediction: np.ndarray,
) -> RiskModelMetrics:
    return RiskModelMetrics(
        mae=float(
            mean_absolute_error(
                truth,
                prediction,
            )
        ),
        rmse=float(
            mean_squared_error(
                truth,
                prediction,
            )
            ** 0.5
        ),
        r2=float(
            r2_score(
                truth,
                prediction,
            )
        ),
    )
