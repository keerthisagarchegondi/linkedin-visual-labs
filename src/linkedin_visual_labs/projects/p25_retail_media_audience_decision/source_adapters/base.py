"""Shared contracts and deterministic helpers for source adapters."""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    EvidenceClass,
    SourceId,
)

GENERIC_ID_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "customer_id",
        "user_id",
        "person_id",
        "id",
    }
)

PII_COLUMN_TOKENS: Final[tuple[str, ...]] = (
    "email",
    "phone",
    "first_name",
    "last_name",
    "full_name",
    "street_address",
    "postal_address",
    "ssn",
)


@dataclass(frozen=True, slots=True)
class CachePolicy:
    """Raw and normalized cache locations for one source."""

    source_id: SourceId
    raw_dir: Path
    normalized_dir: Path
    provenance_dir: Path


@dataclass(frozen=True, slots=True)
class SourceResult:
    """One normalized source result."""

    source_id: SourceId
    evidence_class: EvidenceClass
    normalized_files: tuple[Path, ...]
    provenance_file: Path
    row_count: int


class SourceAdapter(Protocol):
    """Generic callable contract for a Project 4 source adapter."""

    def __call__(
        self,
        policy: CachePolicy,
        offline: bool,
        **kwargs: object,
    ) -> SourceResult:
        """Fetch, normalize, validate, and cache one source."""

        ...


def sha256_file(path: Path) -> str:
    """Return a streaming SHA256 for a file."""

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def canonical_schema_fingerprint(frame: pd.DataFrame) -> str:
    """Fingerprint a DataFrame schema without hashing its values."""

    schema = [
        {
            "column": str(column),
            "dtype": str(frame[column].dtype),
        }
        for column in frame.columns
    ]

    payload = json.dumps(
        schema,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def stable_frame_hash(frame: pd.DataFrame) -> str:
    """Hash canonical CSV serialization of a normalized frame."""

    payload = frame.to_csv(
        index=False,
        lineterminator="\n",
    ).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()


def ensure_no_generic_identity(frame: pd.DataFrame) -> None:
    """Reject generic cross-source customer identity columns."""

    found = GENERIC_ID_COLUMNS.intersection({str(column).lower() for column in frame.columns})

    if found:
        raise ValueError(f"Generic cross-source identity columns are prohibited: {sorted(found)}")


def ensure_no_pii_columns(frame: pd.DataFrame) -> None:
    """Reject obvious PII-bearing column names."""

    offending = [
        str(column)
        for column in frame.columns
        if any(token in str(column).lower() for token in PII_COLUMN_TOKENS)
    ]

    if offending:
        raise ValueError(f"Potential PII columns prohibited: {sorted(offending)}")


def require_columns(
    frame: pd.DataFrame,
    required: set[str],
    *,
    label: str,
) -> None:
    """Require canonical source columns."""

    missing = sorted(required - set(frame.columns))

    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def stable_sort(
    frame: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Return a deterministically ordered copy."""

    return frame.sort_values(
        columns,
        kind="mergesort",
        na_position="last",
    ).reset_index(drop=True)


def download_file(
    url: str,
    destination: Path,
    *,
    expected_sha256: str | None = None,
    offline: bool = False,
) -> Path:
    """Download one immutable raw artifact or reuse its cache."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if destination.is_file():
        if expected_sha256 is not None:
            actual = sha256_file(destination)

            if actual != expected_sha256:
                raise ValueError(
                    f"Cached file hash mismatch: {destination}; "
                    f"expected={expected_sha256}; actual={actual}"
                )

        return destination

    if offline:
        raise FileNotFoundError(f"Offline mode: required cached file missing: {destination}")

    temporary = destination.with_suffix(destination.suffix + ".partial")

    if temporary.exists():
        temporary.unlink()

    request = urllib.request.Request(
        url,
        headers={"User-Agent": ("linkedin-visual-labs/p25-retail-media-audience-decision")},
    )

    try:
        with (
            urllib.request.urlopen(
                request,
                timeout=120,
            ) as response,
            temporary.open("wb") as output,
        ):
            shutil.copyfileobj(
                response,
                output,
                length=1024 * 1024,
            )
    except (
        urllib.error.URLError,
        TimeoutError,
    ) as exc:
        temporary.unlink(
            missing_ok=True,
        )

        raise RuntimeError(f"Download failed for {url}: {exc}") from exc

    if expected_sha256 is not None:
        actual = sha256_file(temporary)

        if actual != expected_sha256:
            temporary.unlink(
                missing_ok=True,
            )

            raise ValueError(
                "Downloaded artifact failed SHA256 validation: "
                f"expected={expected_sha256}; actual={actual}"
            )

    temporary.replace(destination)

    return destination
