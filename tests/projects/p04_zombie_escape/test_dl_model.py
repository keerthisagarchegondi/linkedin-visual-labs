"""Deep-learning model regression tests for Project 2."""

from __future__ import annotations

import torch

from linkedin_visual_labs.projects.p04_zombie_escape import (
    load_zombie_config,
)
from linkedin_visual_labs.projects.p04_zombie_escape.dl_model import (
    ZombieRiskCNN,
    predict_dense_risk,
    train_dl_risk_model,
)


def test_cnn_preserves_spatial_resolution() -> None:
    model = ZombieRiskCNN()

    inputs = torch.zeros(
        (
            3,
            8,
            36,
            36,
        ),
        dtype=torch.float32,
    )

    output = model(inputs)

    assert output.shape == (
        3,
        1,
        36,
        36,
    )


def test_cnn_output_is_bounded_to_unit_interval() -> None:
    model = ZombieRiskCNN()

    inputs = torch.rand(
        (
            2,
            8,
            36,
            36,
        ),
        dtype=torch.float32,
    )

    output = model(inputs)

    assert torch.all(output >= 0.0)

    assert torch.all(output <= 1.0)


def test_small_cnn_training_is_deterministic() -> None:
    config = load_zombie_config()

    first = train_dl_risk_model(
        config,
        random_seed=4305,
        epochs=1,
        batch_size=4,
        training_city_limit=8,
        validation_city_limit=3,
        benchmark_city_limit=3,
    )

    second = train_dl_risk_model(
        config,
        random_seed=4305,
        epochs=1,
        batch_size=4,
        training_city_limit=8,
        validation_city_limit=3,
        benchmark_city_limit=3,
    )

    for first_parameter, second_parameter in zip(
        first.model.parameters(),
        second.model.parameters(),
        strict=True,
    ):
        assert torch.equal(
            first_parameter,
            second_parameter,
        )

    assert first.validation_metrics == second.validation_metrics

    assert first.benchmark_metrics == second.benchmark_metrics


def test_dense_prediction_is_deterministic() -> None:
    config = load_zombie_config()

    trained = train_dl_risk_model(
        config,
        random_seed=4305,
        epochs=1,
        batch_size=4,
        training_city_limit=8,
        validation_city_limit=3,
        benchmark_city_limit=3,
    )

    inputs = torch.rand(
        (
            8,
            36,
            36,
        ),
        generator=torch.Generator().manual_seed(901),
    )

    first = predict_dense_risk(
        trained.model,
        inputs,
    )

    second = predict_dense_risk(
        trained.model,
        inputs,
    )

    assert torch.equal(
        first,
        second,
    )


def test_training_metadata_uses_requested_limits() -> None:
    config = load_zombie_config()

    trained = train_dl_risk_model(
        config,
        random_seed=4305,
        epochs=1,
        batch_size=4,
        training_city_limit=8,
        validation_city_limit=3,
        benchmark_city_limit=3,
    )

    assert trained.random_seed == 4305
    assert trained.epochs == 1
    assert trained.batch_size == 4
    assert trained.training_cities == 8
    assert trained.validation_cities == 3
    assert trained.benchmark_cities == 3
