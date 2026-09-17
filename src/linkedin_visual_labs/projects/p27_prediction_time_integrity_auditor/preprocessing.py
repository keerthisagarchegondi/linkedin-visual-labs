"""Prediction-time-safe preprocessing for Project 7."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)

from .contracts import (
    EXPECTED_INPUT_COLUMNS,
    deployment_feature_names,
)

NUMERIC_COLUMNS: Final[tuple[str, ...]] = (
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


def pipeline_b_features() -> tuple[str, ...]:
    """Partially corrected feature set: duration removed only."""

    return tuple(feature for feature in EXPECTED_INPUT_COLUMNS if feature != "duration")


def pipeline_c_features() -> tuple[str, ...]:
    """Prediction-time-safe deployment feature set."""

    return deployment_feature_names()


def column_groups(
    features: Sequence[str],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
]:
    """Split requested columns into numeric/categorical groups."""

    numeric = tuple(feature for feature in features if feature in NUMERIC_COLUMNS)

    categorical = tuple(feature for feature in features if feature not in NUMERIC_COLUMNS)

    if set(numeric) & set(categorical):
        raise ValueError("Numeric and categorical groups overlap.")

    if set(numeric) | set(categorical) != set(features):
        raise ValueError("Column grouping lost requested features.")

    return numeric, categorical


def logistic_preprocessor(
    features: Sequence[str],
) -> ColumnTransformer:
    """Sparse one-hot + scaled numeric transformer for Logistic Regression."""

    numeric, categorical = column_groups(features)

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                list(numeric),
            ),
            (
                "categorical",
                categorical_pipeline,
                list(categorical),
            ),
        ],
        remainder="drop",
    )


def histogram_preprocessor(
    features: Sequence[str],
) -> ColumnTransformer:
    """Dense ordinal representation for Histogram Gradient Boosting."""

    numeric, categorical = column_groups(features)

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="median"),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(strategy="most_frequent"),
            ),
            (
                "encoder",
                OrdinalEncoder(
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                    encoded_missing_value=-1,
                    dtype=float,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                list(numeric),
            ),
            (
                "categorical",
                categorical_pipeline,
                list(categorical),
            ),
        ],
        remainder="drop",
        sparse_threshold=0.0,
    )
