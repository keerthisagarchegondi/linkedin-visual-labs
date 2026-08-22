"""Deterministic lightweight CNN risk model for Zombie Escape."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import torch
from torch import Tensor, nn
from torch.optim import Adam

from linkedin_visual_labs.projects.p04_zombie_escape.dl_tensors import (
    INPUT_CHANNEL_COUNT,
    build_city_batch,
    city_indices_for_epoch,
    split_contract,
)
from linkedin_visual_labs.projects.p04_zombie_escape.models import (
    ZombieProjectConfig,
)


@dataclass(frozen=True, slots=True)
class DLRiskMetrics:
    """Dense risk-regression metrics over traversable cells."""

    mae: float
    rmse: float


@dataclass(frozen=True, slots=True)
class TrainedDLRiskModel:
    """Trained CNN and deterministic metadata."""

    model: ZombieRiskCNN
    validation_metrics: DLRiskMetrics
    benchmark_metrics: DLRiskMetrics
    training_cities: int
    validation_cities: int
    benchmark_cities: int
    epochs: int
    batch_size: int
    random_seed: int


class ZombieRiskCNN(nn.Module):
    """Small same-resolution CNN producing one dense risk map."""

    def __init__(
        self,
        *,
        input_channels: int = INPUT_CHANNEL_COUNT,
    ) -> None:
        super().__init__()

        self.network = nn.Sequential(
            nn.Conv2d(
                input_channels,
                16,
                kernel_size=3,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                16,
                16,
                kernel_size=3,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                16,
                8,
                kernel_size=3,
                padding=1,
            ),
            nn.ReLU(),
            nn.Conv2d(
                8,
                1,
                kernel_size=1,
            ),
            nn.Sigmoid(),
        )

    def forward(
        self,
        inputs: Tensor,
    ) -> Tensor:
        """Predict a dense [B, 1, H, W] risk map."""
        output = cast(
            Tensor,
            self.network(inputs),
        )

        return output


def configure_deterministic_torch(
    seed: int,
) -> None:
    """Configure deterministic CPU execution for Project 2 DL."""
    torch.manual_seed(seed)

    torch.use_deterministic_algorithms(True)

    torch.set_num_threads(1)

    if hasattr(
        torch,
        "set_num_interop_threads",
    ):
        with suppress(RuntimeError):
            torch.set_num_interop_threads(1)


def train_dl_risk_model(
    config: ZombieProjectConfig,
    *,
    random_seed: int,
    epochs: int = 8,
    batch_size: int = 32,
    training_city_limit: int | None = None,
    validation_city_limit: int | None = None,
    benchmark_city_limit: int | None = None,
) -> TrainedDLRiskModel:
    """Train deterministic CNN using full synthetic city tensors."""
    if epochs <= 0:
        raise ValueError("epochs must be positive")

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    configure_deterministic_torch(random_seed)

    device = torch.device("cpu")

    model = ZombieRiskCNN().to(device)

    optimizer = Adam(
        model.parameters(),
        lr=0.0015,
        weight_decay=1e-5,
    )

    frozen_training_count, _ = split_contract(
        config,
        "training",
    )

    frozen_validation_count, _ = split_contract(
        config,
        "validation",
    )

    frozen_benchmark_count, _ = split_contract(
        config,
        "benchmark",
    )

    training_count = _resolved_limit(
        frozen_training_count,
        training_city_limit,
    )

    validation_count = _resolved_limit(
        frozen_validation_count,
        validation_city_limit,
    )

    benchmark_count = _resolved_limit(
        frozen_benchmark_count,
        benchmark_city_limit,
    )

    # STEP6_DL_PROGRESS_LOGGING
    progress = (
        training_city_limit is None
        and validation_city_limit is None
        and benchmark_city_limit is None
    )

    if progress:
        print(
            (f"[DL] full frozen training started | epochs={epochs} | batch_size={batch_size}"),
            flush=True,
        )

    for epoch in range(epochs):
        if progress:
            print(
                f"[DL] epoch {epoch + 1}/{epochs} started",
                flush=True,
            )

        model.train()

        indices = city_indices_for_epoch(
            count=training_count,
            seed=random_seed,
            epoch=epoch,
            shuffle=True,
        )

        total_batches = (len(indices) + batch_size - 1) // batch_size

        for batch_number, batch_indices in enumerate(
            _batched(
                indices,
                batch_size,
            ),
            start=1,
        ):
            if progress:
                print(
                    (
                        f"[DL] epoch "
                        f"{epoch + 1}/{epochs} | "
                        f"batch "
                        f"{batch_number}/{total_batches} "
                        "started"
                    ),
                    flush=True,
                )

            inputs, targets, masks = build_city_batch(
                config,
                split="training",
                indices=batch_indices,
            )

            inputs = inputs.to(device)

            targets = targets.to(device)

            masks = masks.to(device)

            optimizer.zero_grad(set_to_none=True)

            prediction = model(inputs)

            loss = _masked_mse_loss(
                prediction,
                targets,
                masks,
            )

            backward = cast(
                Callable[[], None],
                loss.backward,
            )

            backward()

            optimizer.step()

    validation_metrics = evaluate_dl_risk_model(
        model,
        config,
        split="validation",
        city_count=validation_count,
        batch_size=batch_size,
    )

    benchmark_metrics = evaluate_dl_risk_model(
        model,
        config,
        split="benchmark",
        city_count=benchmark_count,
        batch_size=batch_size,
    )

    return TrainedDLRiskModel(
        model=model,
        validation_metrics=validation_metrics,
        benchmark_metrics=benchmark_metrics,
        training_cities=training_count,
        validation_cities=validation_count,
        benchmark_cities=benchmark_count,
        epochs=epochs,
        batch_size=batch_size,
        random_seed=random_seed,
    )


def evaluate_dl_risk_model(
    model: ZombieRiskCNN,
    config: ZombieProjectConfig,
    *,
    split: str,
    city_count: int,
    batch_size: int,
) -> DLRiskMetrics:
    """Evaluate dense regression metrics on one deterministic split."""
    model.eval()

    absolute_error_sum = 0.0
    squared_error_sum = 0.0
    observed_count = 0.0

    indices = tuple(range(city_count))

    with torch.no_grad():
        for batch_indices in _batched(
            indices,
            batch_size,
        ):
            inputs, targets, masks = build_city_batch(
                config,
                split=split,
                indices=batch_indices,
            )

            prediction = model(inputs)

            difference = prediction - targets

            absolute_error_sum += float((difference.abs() * masks).sum().item())

            squared_error_sum += float((difference.square() * masks).sum().item())

            observed_count += float(masks.sum().item())

    if observed_count <= 0.0:
        raise RuntimeError("DL evaluation split contains no traversable cells")

    mae = absolute_error_sum / observed_count

    rmse = math.sqrt(squared_error_sum / observed_count)

    return DLRiskMetrics(
        mae=mae,
        rmse=rmse,
    )


def predict_dense_risk(
    model: ZombieRiskCNN,
    inputs: Tensor,
) -> Tensor:
    """Predict deterministic dense risk on CPU."""
    model.eval()

    with torch.no_grad():
        prediction = model(inputs.unsqueeze(0)).squeeze(0)

    clipped = cast(
        Tensor,
        prediction.clamp(
            0.0,
            1.0,
        ),
    )

    return clipped


def persist_dl_risk_model(
    trained: TrainedDLRiskModel,
    directory: Path,
) -> tuple[
    Path,
    Path,
]:
    """Persist deterministic CNN checkpoint and metadata."""
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    checkpoint_path = directory / "checkpoint.pt"

    metadata_path = directory / "metadata.json"

    torch.save(
        {
            "model_state_dict": (trained.model.state_dict()),
            "input_channels": (INPUT_CHANNEL_COUNT),
            "random_seed": (trained.random_seed),
        },
        checkpoint_path,
    )

    metadata: dict[
        str,
        Any,
    ] = {
        "schema_version": 1,
        "model_family": ("convolutional_neural_network"),
        "implementation": ("ZombieRiskCNN"),
        "device": "cpu",
        "input_channel_count": (INPUT_CHANNEL_COUNT),
        "random_seed": (trained.random_seed),
        "epochs": (trained.epochs),
        "batch_size": (trained.batch_size),
        "training_cities": (trained.training_cities),
        "validation_cities": (trained.validation_cities),
        "benchmark_cities": (trained.benchmark_cities),
        "validation_metrics": {
            "mae": (trained.validation_metrics.mae),
            "rmse": (trained.validation_metrics.rmse),
        },
        "benchmark_metrics": {
            "mae": (trained.benchmark_metrics.mae),
            "rmse": (trained.benchmark_metrics.rmse),
        },
        "hidden_truth_input_leakage": False,
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
        checkpoint_path,
        metadata_path,
    )


def load_dl_checkpoint(
    checkpoint_path: Path,
) -> ZombieRiskCNN:
    """Load a persisted Project 2 CNN checkpoint on CPU."""
    payload = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=True,
    )

    model = ZombieRiskCNN(input_channels=int(payload["input_channels"]))

    model.load_state_dict(payload["model_state_dict"])

    model.eval()

    return model


def _masked_mse_loss(
    prediction: Tensor,
    target: Tensor,
    mask: Tensor,
) -> Tensor:
    squared_error = (prediction - target).square()

    weighted = squared_error * mask

    denominator = mask.sum().clamp_min(1.0)

    return weighted.sum() / denominator


def _batched(
    values: tuple[int, ...],
    batch_size: int,
) -> tuple[
    tuple[int, ...],
    ...,
]:
    return tuple(
        values[start : start + batch_size]
        for start in range(
            0,
            len(values),
            batch_size,
        )
    )


def _resolved_limit(
    frozen_count: int,
    requested: int | None,
) -> int:
    if requested is None:
        return frozen_count

    if requested <= 0:
        raise ValueError("DL city limit must be positive")

    if requested > frozen_count:
        raise ValueError("DL city limit cannot exceed frozen split count")

    return requested
