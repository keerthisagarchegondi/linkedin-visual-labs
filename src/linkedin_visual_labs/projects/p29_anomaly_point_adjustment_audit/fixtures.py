"""Small, auditable semantic fixture loading for future Project 9 semantics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SemanticFixture:
    fixture_id: str
    purpose: str
    labels: tuple[int, ...]
    raw_predictions: tuple[int, ...] | None
    expected_intervals: tuple[tuple[int, int], ...]


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[4] / "reference" / "project9" / "semantic_fixtures.json"


def _binary_vector(value: object, *, name: str) -> tuple[int, ...]:
    if (
        not isinstance(value, list)
        or not value
        or any(type(item) is not int or item not in (0, 1) for item in value)
    ):
        raise ValueError(f"{name} must be a non-empty binary integer list")
    return tuple(value)


def fixture_from_mapping(value: dict[str, Any]) -> SemanticFixture:
    if set(value) != {"fixture_id", "purpose", "labels", "raw_predictions", "expected_intervals"}:
        raise ValueError("fixture keys must match the schema exactly")
    fixture_id, purpose = value["fixture_id"], value["purpose"]
    if (
        not isinstance(fixture_id, str)
        or not fixture_id
        or not isinstance(purpose, str)
        or not purpose
    ):
        raise ValueError("fixture_id and purpose must be non-empty strings")
    labels = _binary_vector(value["labels"], name="labels")
    predictions = (
        None
        if value["raw_predictions"] is None
        else _binary_vector(value["raw_predictions"], name="raw_predictions")
    )
    if predictions is not None and len(predictions) != len(labels):
        raise ValueError("raw_predictions must have the same length as labels")
    if not isinstance(value["expected_intervals"], list):
        raise TypeError("expected_intervals must be a list")
    intervals: list[tuple[int, int]] = []
    previous_stop = 0
    for interval in value["expected_intervals"]:
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or any(type(item) is not int for item in interval)
        ):
            raise ValueError("each expected interval must be [start, stop]")
        start, stop = interval
        if (
            not 0 <= start < stop <= len(labels)
            or start < previous_stop
            or any(item != 1 for item in labels[start:stop])
        ):
            raise ValueError(
                "expected intervals must be ordered, bounded, half-open positive ranges"
            )
        previous_stop = stop
        intervals.append((start, stop))
    return SemanticFixture(fixture_id, purpose, labels, predictions, tuple(intervals))


def load_fixtures(path: Path | None = None) -> tuple[SemanticFixture, ...]:
    if path is None and not fixture_path().is_file():
        text = (
            resources.files(__package__)
            .joinpath("resources", "semantic_fixtures.json")
            .read_text(encoding="utf-8")
        )
    else:
        text = (fixture_path() if path is None else path).read_text(encoding="utf-8")
    raw = json.loads(text)
    if (
        not isinstance(raw, dict)
        or set(raw) != {"fixtures"}
        or not isinstance(raw["fixtures"], list)
    ):
        raise ValueError("fixture document must contain only a fixtures list")
    fixtures = tuple(
        fixture_from_mapping(value) for value in raw["fixtures"] if isinstance(value, dict)
    )
    if len(fixtures) != len(raw["fixtures"]) or len({item.fixture_id for item in fixtures}) != len(
        fixtures
    ):
        raise ValueError("fixture IDs must be unique and entries must be mappings")
    return fixtures
