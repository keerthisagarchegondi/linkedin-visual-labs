"""Classical ML model tests."""

from __future__ import annotations

import pandas as pd

from linkedin_visual_labs.projects.p04_zombie_escape import (
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_data import (
    _generate_split,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_features import (
    FEATURE_COLUMNS,
)
from linkedin_visual_labs.projects.p04_zombie_escape.ml_model import (
    predict_risk,
    train_ml_risk_model,
)


def _small_dataset() -> pd.DataFrame:
    config = load_zombie_config()

    return pd.concat(
        [
            _generate_split(
                config,
                split="training",
                count=20,
                base_seed=8101,
            ),
            _generate_split(
                config,
                split="validation",
                count=5,
                base_seed=8102,
            ),
            _generate_split(
                config,
                split="benchmark",
                count=5,
                base_seed=8103,
            ),
        ],
        ignore_index=True,
    )


def test_model_training_is_deterministic() -> None:
    dataset = _small_dataset()

    first = train_ml_risk_model(
        dataset,
        random_seed=4304,
    )

    second = train_ml_risk_model(
        dataset,
        random_seed=4304,
    )

    features = dataset.loc[
        :,
        list(FEATURE_COLUMNS),
    ].head(100)

    first_prediction = predict_risk(
        first,
        features,
    )

    second_prediction = predict_risk(
        second,
        features,
    )

    assert (first_prediction == second_prediction).all()


def test_predictions_are_clamped_to_unit_interval() -> None:
    dataset = _small_dataset()

    trained = train_ml_risk_model(
        dataset,
        random_seed=4304,
    )

    prediction = predict_risk(
        trained,
        dataset.loc[
            :,
            list(FEATURE_COLUMNS),
        ].head(500),
    )

    assert (prediction >= 0.0).all()

    assert (prediction <= 1.0).all()
