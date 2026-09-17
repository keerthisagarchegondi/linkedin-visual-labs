from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.config import (
    repository_root,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.contracts import (
    EXPECTED_COLUMNS,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.data import (
    EXPECTED_ROW_COUNT,
    TARGET_MAPPING,
    _read_rows,
    build_source_profile,
    dataset_fingerprint,
    load_official_dataset,
    source_paths,
)


def test_official_source_exists_after_step1_acquisition() -> None:
    paths = source_paths()

    assert paths.outer_archive.is_file()
    assert paths.extracted_csv.is_file()


def test_official_dataset_shape_schema_and_target() -> None:
    dataset = load_official_dataset(acquire=False)

    assert len(dataset.rows) == EXPECTED_ROW_COUNT
    assert dataset.source_order[0] == 0
    assert dataset.source_order[-1] == EXPECTED_ROW_COUNT - 1
    assert dataset.source_order == tuple(range(EXPECTED_ROW_COUNT))

    assert tuple(dataset.rows[0]) == EXPECTED_COLUMNS
    assert set(dataset.normalized_target) == {0, 1}
    assert TARGET_MAPPING == {
        "no": 0,
        "yes": 1,
    }


def test_official_source_loading_is_deterministic() -> None:
    first = load_official_dataset(acquire=False)
    second = load_official_dataset(acquire=False)

    assert dataset_fingerprint(first) == dataset_fingerprint(second)


def test_source_profile_is_complete() -> None:
    dataset = load_official_dataset(acquire=False)

    profile = build_source_profile(dataset)

    assert profile["row_count"] == EXPECTED_ROW_COUNT
    assert profile["input_count"] == 20
    assert profile["target_values"] == [
        "no",
        "yes",
    ]

    source_order = profile["source_order"]

    assert isinstance(
        source_order,
        dict,
    )
    assert source_order["preserved"] is True
    assert source_order["first_index"] == 0
    assert source_order["last_index"] == EXPECTED_ROW_COUNT - 1


def test_unknown_columns_are_rejected(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad.csv"

    columns = [
        *EXPECTED_COLUMNS,
        "unexpected_column",
    ]

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter=";",
        )

        writer.writeheader()

        row = {column: "0" for column in columns}

        writer.writerow(row)

    with pytest.raises(
        ValueError,
        match="schema mismatch",
    ):
        _read_rows(path)


def test_committed_step1_evidence_reconciles() -> None:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))

    profile = json.loads((root / "source_profile.json").read_text(encoding="utf-8"))

    feature_contract = json.loads(
        (root / "feature_availability_contract.json").read_text(encoding="utf-8")
    )

    assert manifest["row_count"] == EXPECTED_ROW_COUNT
    assert profile["row_count"] == EXPECTED_ROW_COUNT

    assert manifest["dataset_fingerprint_sha256"] == profile["dataset_fingerprint_sha256"]

    assert manifest["doi"] == "10.24432/C5K306"
    assert manifest["license"] == "CC BY 4.0"

    assert len(feature_contract["features"]) == 20


def test_no_raw_source_is_inside_tracked_project_assets() -> None:
    assets = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    forbidden = {
        "bank+marketing.zip",
        "bank-additional.zip",
        "bank-additional-full.csv",
    }

    assert not any(path.name in forbidden for path in assets.rglob("*") if path.is_file())
