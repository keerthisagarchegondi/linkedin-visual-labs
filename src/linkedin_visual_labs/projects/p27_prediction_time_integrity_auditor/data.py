"""Official UCI Bank Marketing ingestion for Project 7."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import urllib.request
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from .config import repository_root
from .contracts import (
    EXPECTED_COLUMNS,
    EXPECTED_INPUT_COLUMNS,
    TARGET_COLUMN,
    feature_contract_payload,
)

OFFICIAL_DATASET_PAGE: Final[str] = "https://archive.ics.uci.edu/dataset/222/bank+marketing"

OFFICIAL_DOWNLOAD_URL: Final[str] = (
    "https://archive.ics.uci.edu/static/public/222/bank+marketing.zip"
)

DATASET_DOI: Final[str] = "10.24432/C5K306"
DATASET_LICENSE: Final[str] = "CC BY 4.0"
DATASET_ID: Final[int] = 222
PREFERRED_FILE: Final[str] = "bank-additional-full.csv"

EXPECTED_ROW_COUNT: Final[int] = 41_188
EXPECTED_INPUT_COUNT: Final[int] = 20

SEPARATOR: Final[str] = ";"
ENCODING: Final[str] = "utf-8"

TARGET_MAPPING: Final[dict[str, int]] = {
    "no": 0,
    "yes": 1,
}


@dataclass(frozen=True, slots=True)
class SourcePaths:
    """Local ignored official-source paths."""

    raw_root: Path
    outer_archive: Path
    extracted_csv: Path


@dataclass(frozen=True, slots=True)
class LoadedDataset:
    """Validated official source records."""

    rows: tuple[dict[str, str], ...]
    source_order: tuple[int, ...]

    @property
    def normalized_target(self) -> tuple[int, ...]:
        return tuple(TARGET_MAPPING[row[TARGET_COLUMN]] for row in self.rows)


def source_paths() -> SourcePaths:
    """Return ignored raw-source locations."""

    root = repository_root() / "data" / "p27_prediction_time_integrity_auditor" / "raw"

    return SourcePaths(
        raw_root=root,
        outer_archive=root / "bank+marketing.zip",
        extracted_csv=root / PREFERRED_FILE,
    )


def sha256_file(
    path: Path,
) -> str:
    """Compute SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _download_to_temp(
    destination: Path,
) -> None:
    request = urllib.request.Request(
        OFFICIAL_DOWNLOAD_URL,
        headers={"User-Agent": ("linkedin-visual-labs/p27-prediction-time-integrity-auditor")},
    )

    temp = destination.with_suffix(destination.suffix + ".download")

    try:
        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"Unexpected UCI HTTP status: {response.status}")

            with temp.open("wb") as handle:
                shutil.copyfileobj(
                    response,
                    handle,
                )

        if temp.stat().st_size <= 0:
            raise RuntimeError("Downloaded UCI archive is empty.")

        temp.replace(destination)
    finally:
        if temp.exists():
            temp.unlink()


def _extract_preferred_csv(
    outer_archive: Path,
    destination: Path,
) -> None:
    """Extract nested bank-additional-full.csv without extractall."""

    with zipfile.ZipFile(
        outer_archive,
        "r",
    ) as outer:
        nested_candidates = [
            name
            for name in outer.namelist()
            if name.replace("\\", "/").endswith("bank-additional.zip")
        ]

        if len(nested_candidates) != 1:
            raise RuntimeError(
                "Expected exactly one bank-additional.zip "
                f"inside UCI archive; found {nested_candidates!r}"
            )

        nested_bytes = outer.read(nested_candidates[0])

    with zipfile.ZipFile(
        io.BytesIO(nested_bytes),
        "r",
    ) as nested:
        csv_candidates = [
            name for name in nested.namelist() if name.replace("\\", "/").endswith(PREFERRED_FILE)
        ]

        if len(csv_candidates) != 1:
            raise RuntimeError(f"Expected exactly one preferred CSV; found {csv_candidates!r}")

        payload = nested.read(csv_candidates[0])

    if not payload:
        raise RuntimeError("Preferred UCI CSV is empty.")

    temp = destination.with_suffix(destination.suffix + ".extract")

    try:
        temp.write_bytes(payload)
        temp.replace(destination)
    finally:
        if temp.exists():
            temp.unlink()


def acquire_official_source(
    *,
    force_download: bool = False,
) -> SourcePaths:
    """Acquire and extract the official UCI archive deterministically."""

    paths = source_paths()

    paths.raw_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    if force_download or not paths.outer_archive.exists():
        _download_to_temp(paths.outer_archive)

    if force_download or not paths.extracted_csv.exists():
        _extract_preferred_csv(
            paths.outer_archive,
            paths.extracted_csv,
        )

    return paths


def _read_rows(
    path: Path,
) -> tuple[dict[str, str], ...]:
    with path.open(
        "r",
        encoding=ENCODING,
        newline="",
    ) as handle:
        reader = csv.DictReader(
            handle,
            delimiter=SEPARATOR,
        )

        fieldnames = tuple(reader.fieldnames or ())

        if fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                "Official source schema mismatch. "
                f"Expected {EXPECTED_COLUMNS!r}; "
                f"found {fieldnames!r}."
            )

        rows = tuple(dict(row) for row in reader)

    return rows


def _validate_rows(
    rows: tuple[dict[str, str], ...],
) -> None:
    if len(rows) != EXPECTED_ROW_COUNT:
        raise ValueError(f"Official source row-count mismatch: {len(rows)} != {EXPECTED_ROW_COUNT}")

    target_values = {row[TARGET_COLUMN] for row in rows}

    if target_values != set(TARGET_MAPPING):
        raise ValueError(f"Unexpected target values: {target_values!r}")

    for index, row in enumerate(rows):
        if tuple(row) != EXPECTED_COLUMNS:
            raise ValueError(f"Row {index} schema/order mismatch.")

        if any(value is None for value in row.values()):
            raise ValueError(f"Row {index} contains null parser values.")

    numeric_columns = (
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

    for column in numeric_columns:
        for index, row in enumerate(rows):
            try:
                value = float(row[column])
            except ValueError as exc:
                raise ValueError(f"Non-numeric {column} at row {index}.") from exc

            if (
                column
                in {
                    "age",
                    "duration",
                    "campaign",
                    "pdays",
                    "previous",
                    "nr.employed",
                }
                and value < 0
            ):
                raise ValueError(f"Unexpected negative {column} at row {index}.")


def load_official_dataset(
    *,
    acquire: bool = True,
) -> LoadedDataset:
    """Load and strictly validate the preferred official UCI CSV."""

    paths = acquire_official_source() if acquire else source_paths()

    if not paths.extracted_csv.is_file():
        raise FileNotFoundError(paths.extracted_csv)

    rows = _read_rows(paths.extracted_csv)

    _validate_rows(rows)

    source_order = tuple(range(len(rows)))

    return LoadedDataset(
        rows=rows,
        source_order=source_order,
    )


def _numeric_range(
    rows: tuple[dict[str, str], ...],
    column: str,
) -> dict[str, float]:
    values = [float(row[column]) for row in rows]

    return {
        "min": min(values),
        "max": max(values),
    }


def dataset_fingerprint(
    dataset: LoadedDataset,
) -> str:
    """Stable source-order-sensitive dataset fingerprint."""

    digest = hashlib.sha256()

    for source_index, row in zip(
        dataset.source_order,
        dataset.rows,
        strict=True,
    ):
        digest.update(str(source_index).encode("ascii"))
        digest.update(b"|")

        for column in EXPECTED_COLUMNS:
            digest.update(column.encode("utf-8"))
            digest.update(b"=")
            digest.update(row[column].encode("utf-8"))
            digest.update(b"|")

        digest.update(b"\n")

    return digest.hexdigest()


def build_source_profile(
    dataset: LoadedDataset,
) -> dict[str, object]:
    """Generate deterministic descriptive source evidence."""

    rows = dataset.rows

    target_counts = Counter(row[TARGET_COLUMN] for row in rows)

    unknown_counts = {
        column: sum(
            row[column].strip().lower()
            in {
                "",
                "unknown",
                "nonexistent",
            }
            for row in rows
        )
        for column in EXPECTED_INPUT_COLUMNS
    }

    numeric_columns = (
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

    return {
        "row_count": len(rows),
        "input_count": len(EXPECTED_INPUT_COLUMNS),
        "columns": list(EXPECTED_COLUMNS),
        "target_column": TARGET_COLUMN,
        "target_values": sorted(target_counts),
        "target_counts": dict(sorted(target_counts.items())),
        "source_order": {
            "preserved": True,
            "first_index": dataset.source_order[0],
            "last_index": dataset.source_order[-1],
            "ordered_by_source": True,
        },
        "unknown_like_counts": unknown_counts,
        "numeric_ranges": {
            column: _numeric_range(
                rows,
                column,
            )
            for column in numeric_columns
        },
        "dataset_fingerprint_sha256": dataset_fingerprint(dataset),
    }


def build_source_manifest(
    paths: SourcePaths,
    dataset: LoadedDataset,
    *,
    accessed_on: str,
) -> dict[str, object]:
    """Generate official-source provenance."""

    return {
        "source_type": "OFFICIAL_UCI_DIRECT_DOWNLOAD",
        "dataset_id": DATASET_ID,
        "dataset_name": "Bank Marketing",
        "preferred_file": PREFERRED_FILE,
        "official_dataset_page": OFFICIAL_DATASET_PAGE,
        "official_download_url": OFFICIAL_DOWNLOAD_URL,
        "doi": DATASET_DOI,
        "license": DATASET_LICENSE,
        "accessed_on": accessed_on,
        "archive_sha256": sha256_file(paths.outer_archive),
        "archive_bytes": paths.outer_archive.stat().st_size,
        "extracted_file_sha256": sha256_file(paths.extracted_csv),
        "extracted_file_bytes": paths.extracted_csv.stat().st_size,
        "separator": SEPARATOR,
        "encoding": ENCODING,
        "row_count": len(dataset.rows),
        "input_count": EXPECTED_INPUT_COUNT,
        "columns": list(EXPECTED_COLUMNS),
        "missing_value_conventions": {
            "categorical_unknown_token": "unknown",
            "pdays_not_previously_contacted_token": 999,
            "note": (
                "Source-specific sentinels/tokens are preserved; "
                "no imputation is performed in Step 1."
            ),
        },
        "target_mapping": TARGET_MAPPING,
        "source_ordering": (
            "Official preferred file documented by UCI as ordered by "
            "date; file row order is preserved with zero-based "
            "source_order."
        ),
        "dataset_fingerprint_sha256": dataset_fingerprint(dataset),
    }


def write_step1_evidence(
    *,
    accessed_on: str,
) -> tuple[Path, Path, Path]:
    """Acquire source and write deterministic committed Step 1 evidence."""

    paths = acquire_official_source()
    dataset = load_official_dataset(acquire=False)

    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_path = root / "source_manifest.json"
    profile_path = root / "source_profile.json"
    contract_path = root / "feature_availability_contract.json"

    payloads = {
        manifest_path: build_source_manifest(
            paths,
            dataset,
            accessed_on=accessed_on,
        ),
        profile_path: build_source_profile(dataset),
        contract_path: feature_contract_payload(),
    }

    for path, payload in payloads.items():
        path.write_text(
            json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    return (
        manifest_path,
        profile_path,
        contract_path,
    )
