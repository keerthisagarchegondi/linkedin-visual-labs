"""Deterministic Project 9 pre-freeze timelines and paired count simulation."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, stdev

import numpy as np

from .analytics import (
    event_hit_probability,
    expected_adjusted_counts,
    expected_adjusted_recall,
    expected_raw_counts,
    ratio_of_expected_counts_f1,
)
from .config import PROJECT_ID, Project9Config, derive_seed, repository_root
from .metrics import ConfusionCounts
from .segments import Event

SEED_STREAM_VERSION = "p29-streams-v1"
PREFREEZE_STATUS = "PREFREEZE"
MC_TOLERANCE_MULTIPLIER = 6.0
DEFAULT_BATCH_SIZE = 128


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class Timeline:
    labels: tuple[int, ...]
    events: tuple[Event, ...]
    gaps: tuple[int, ...]
    labels_sha256: str
    events_sha256: str
    layout_sha256: str


@dataclass(frozen=True, slots=True)
class Condition:
    event_length: int
    q: float
    repetitions: int
    condition_id: str


@dataclass(frozen=True, slots=True)
class MetricSummary:
    mean: float
    sd: float
    se: float


def build_equal_event_timeline(n_timestamps: int, positives: int, event_length: int) -> Timeline:
    """Evenly allocate normal timestamps across K+1 gaps, remainder to earliest gaps."""
    if min(n_timestamps, positives, event_length) <= 0 or positives >= n_timestamps:
        raise ValueError("timeline values must be positive with positives < n_timestamps")
    if positives % event_length:
        raise ValueError("event_length must divide positives")
    event_count = positives // event_length
    normals = n_timestamps - positives
    if normals < event_count - 1:
        raise ValueError("insufficient normal timestamps for non-merging internal gaps")
    base, remainder = divmod(normals, event_count + 1)
    gaps = tuple(base + (1 if index < remainder else 0) for index in range(event_count + 1))
    if any(gap < 1 for gap in gaps[1:-1]):
        raise ValueError("deterministic gap allocation violates internal-gap contract")
    labels: list[int] = []
    events: list[Event] = []
    for index in range(event_count):
        labels.extend((0,) * gaps[index])
        start = len(labels)
        labels.extend((1,) * event_length)
        events.append(Event(start, len(labels)))
    labels.extend((0,) * gaps[-1])
    values = tuple(labels)
    metadata = {"N": n_timestamps, "P": positives, "L": event_length, "gaps": gaps}
    return Timeline(
        values,
        tuple(events),
        gaps,
        _digest(values),
        _digest([(event.start, event.stop) for event in events]),
        _digest(metadata),
    )


def condition_id(config: Project9Config, event_length: int, q: float, repetitions: int) -> str:
    """Return a portable identity independent of grid ordering or machine state."""
    payload: dict[str, object] = {
        "experiment_version": config.experiment_version,
        "N": config.n_timestamps,
        "P": config.anomalous_timestamps,
        "prevalence": config.prevalence,
        "event_length": event_length,
        "q": q,
        "repetitions": repetitions,
        "seed_stream_version": SEED_STREAM_VERSION,
    }
    return _digest(payload)


def frozen_conditions(
    config: Project9Config, repetitions: int | None = None
) -> tuple[Condition, ...]:
    selected_repetitions = config.initial_repetitions if repetitions is None else repetitions
    return tuple(
        Condition(
            length, q, selected_repetitions, condition_id(config, length, q, selected_repetitions)
        )
        for length in config.event_lengths
        for q in config.alert_probabilities
    )


def _summary(values: list[float]) -> MetricSummary:
    if not values:
        raise ValueError("summary needs at least one value")
    deviation = 0.0 if len(values) == 1 else stdev(values)
    return MetricSummary(mean(values), deviation, deviation / math.sqrt(len(values)))


def _metric_values(counts: ConfusionCounts) -> tuple[float, float, float]:
    """Translate nullable metric contract for positive-label experiment conditions."""
    if counts.precision is None or counts.recall is None or counts.f1 is None:
        raise AssertionError("Project 9 positive-label conditions must have defined rates")
    return counts.precision, counts.recall, counts.f1


def simulate_condition(
    config: Project9Config, condition: Condition, *, batch_size: int = DEFAULT_BATCH_SIZE
) -> dict[str, object]:
    """Run paired sufficient-count replicates with seed-per-replicate batch invariance."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    timeline = build_equal_event_timeline(
        config.n_timestamps, config.anomalous_timestamps, condition.event_length
    )
    event_count = len(timeline.events)
    normal_count = config.n_timestamps - config.anomalous_timestamps
    raw_f1: list[float] = []
    adjusted_f1: list[float] = []
    raw_precision: list[float] = []
    adjusted_precision: list[float] = []
    raw_recall: list[float] = []
    adjusted_recall: list[float] = []
    raw_tp: list[float] = []
    raw_fp: list[float] = []
    for batch_start in range(0, condition.repetitions, batch_size):
        for replicate in range(batch_start, min(batch_start + batch_size, condition.repetitions)):
            seed = derive_seed(
                config,
                "condition_simulation",
                stream_version=SEED_STREAM_VERSION,
                event_length=condition.event_length,
                q=condition.q,
                replicate=replicate,
            )
            rng = np.random.default_rng(seed)
            hits = rng.binomial(condition.event_length, condition.q, size=event_count)
            false_positives = int(rng.binomial(normal_count, condition.q))
            raw_true_positive = int(hits.sum())
            adjusted_true_positive = condition.event_length * int((hits > 0).sum())
            raw = ConfusionCounts(
                raw_true_positive,
                false_positives,
                config.anomalous_timestamps - raw_true_positive,
                normal_count - false_positives,
            )
            adjusted = ConfusionCounts(
                adjusted_true_positive,
                false_positives,
                config.anomalous_timestamps - adjusted_true_positive,
                normal_count - false_positives,
            )
            raw_p, raw_r, raw_value = _metric_values(raw)
            adjusted_p, adjusted_r, adjusted_value = _metric_values(adjusted)
            raw_precision.append(raw_p)
            raw_recall.append(raw_r)
            raw_f1.append(raw_value)
            adjusted_precision.append(adjusted_p)
            adjusted_recall.append(adjusted_r)
            adjusted_f1.append(adjusted_value)
            raw_tp.append(float(raw_true_positive))
            raw_fp.append(float(false_positives))
    raw_reference = expected_raw_counts(
        (condition.event_length,) * event_count, condition.q, normal_count
    )
    adjusted_reference = expected_adjusted_counts(
        (condition.event_length,) * event_count, condition.q, normal_count
    )
    delta = [adjusted - raw for raw, adjusted in zip(raw_f1, adjusted_f1, strict=True)]
    raw_summary, adjusted_summary, delta_summary = (
        _summary(raw_f1),
        _summary(adjusted_f1),
        _summary(delta),
    )
    expected_recall = expected_adjusted_recall((condition.event_length,) * event_count, condition.q)
    tolerance = MC_TOLERANCE_MULTIPLIER * max(
        adjusted_summary.se, 1.0 / math.sqrt(condition.repetitions)
    )
    checks = {
        "bounded_metrics": all(0.0 <= value <= 1.0 for value in raw_f1 + adjusted_f1),
        "paired_f1_monotonic": all(delta_value >= -1e-15 for delta_value in delta),
        "analytical_adjusted_recall": abs(mean(adjusted_recall) - expected_recall) <= tolerance,
        "analytical_raw_tp": abs(mean(raw_tp) - raw_reference.true_positive)
        <= MC_TOLERANCE_MULTIPLIER * max(1.0, math.sqrt(raw_reference.true_positive)),
        "analytical_raw_fp": abs(mean(raw_fp) - raw_reference.false_positive)
        <= MC_TOLERANCE_MULTIPLIER * max(1.0, math.sqrt(raw_reference.false_positive)),
    }
    if not all(checks.values()):
        raise ValueError(f"predeclared condition validation failed: {checks}")
    return {
        "status": PREFREEZE_STATUS,
        "project_id": PROJECT_ID,
        "experiment_id": f"{PROJECT_ID}-v{config.experiment_version}",
        "condition_id": condition.condition_id,
        "N": config.n_timestamps,
        "P": config.anomalous_timestamps,
        "prevalence": config.prevalence,
        "event_length": condition.event_length,
        "event_count": event_count,
        "q": condition.q,
        "repetitions": condition.repetitions,
        "seed_stream_version": SEED_STREAM_VERSION,
        "rng": {"name": "numpy.default_rng", "numpy_version": np.__version__},
        "timeline": {
            "labels_sha256": timeline.labels_sha256,
            "events_sha256": timeline.events_sha256,
            "layout_sha256": timeline.layout_sha256,
            "gaps": timeline.gaps,
        },
        "raw_f1": asdict(raw_summary),
        "adjusted_f1": asdict(adjusted_summary),
        "delta_f1": asdict(delta_summary),
        "raw_precision_mean": mean(raw_precision),
        "adjusted_precision_mean": mean(adjusted_precision),
        "raw_recall_mean": mean(raw_recall),
        "adjusted_recall_mean": mean(adjusted_recall),
        "analytical_event_hit_probability": event_hit_probability(
            condition.event_length, condition.q
        ),
        "analytical_expected_adjusted_recall": expected_recall,
        "ratio_expected_counts_raw_f1": ratio_of_expected_counts_f1(raw_reference),
        "ratio_expected_counts_adjusted_f1": ratio_of_expected_counts_f1(adjusted_reference),
        "validation": checks,
    }


def run_pilot(config: Project9Config, *, repetitions: int = 128) -> dict[str, object]:
    """Run predeclared short, primary, and long pilot conditions before full sweep."""
    declared = (
        (1, 0.01),
        (config.primary_event_length, config.primary_alert_probability),
        (1000, 0.01),
    )
    started = time.perf_counter()
    results = [
        simulate_condition(
            config,
            Condition(length, q, repetitions, condition_id(config, length, q, repetitions)),
        )
        for length, q in declared
    ]
    elapsed = time.perf_counter() - started
    estimate = (
        elapsed
        * len(frozen_conditions(config))
        * config.initial_repetitions
        / (len(declared) * repetitions)
    )
    return {
        "status": "PASS",
        "purpose": "runtime_and_precision_only",
        "conditions": declared,
        "repetitions": repetitions,
        "batch_size": DEFAULT_BATCH_SIZE,
        "wall_seconds": elapsed,
        "estimated_full_grid_seconds": estimate,
        "results": results,
        "environment": platform.platform(),
    }


def prefreeze_path() -> Path:
    return repository_root() / "outputs" / PROJECT_ID / "prefreeze"


def run_prefreeze_sweep(config: Project9Config) -> dict[str, object]:
    """Generate all frozen condition summaries with replayable per-replicate streams."""
    pilot = run_pilot(config)
    results = [simulate_condition(config, condition) for condition in frozen_conditions(config)]
    payload: dict[str, object] = {
        "status": PREFREEZE_STATUS,
        "replicate_storage": "summary_plus_deterministic_seed_per_replicate_replay",
        "pilot": pilot,
        "conditions": results,
    }
    destination = prefreeze_path()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "PREFREEZE_condition_summaries.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return payload
