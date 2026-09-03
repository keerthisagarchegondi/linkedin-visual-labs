"""Independent ingestion and evidence-boundary validation."""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.provenance import (
    validate_provenance,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    GENERIC_ID_COLUMNS,
    canonical_schema_fingerprint,
    ensure_no_generic_identity,
    ensure_no_pii_columns,
    sha256_file,
)

PUBLIC_SOURCE_IDS: Final[tuple[str, ...]] = (
    "dunnhumby",
    "hillstrom",
    "criteo",
    "retailrocket",
)


def validate_normalized_file(
    path: Path,
) -> pd.DataFrame:
    """Load and validate one normalized parquet."""

    if not path.is_file():
        raise FileNotFoundError(f"Normalized source missing: {path}")

    frame = pd.read_parquet(path)

    if frame.empty:
        raise ValueError(f"Normalized source is empty: {path}")

    ensure_no_generic_identity(frame)
    ensure_no_pii_columns(frame)

    return frame


def validate_source_provenance(
    provenance_path: Path,
    normalized_root: Path,
) -> None:
    """Reconcile one provenance manifest against normalized files."""

    manifest = validate_provenance(provenance_path)

    normalized = manifest["normalized_files"]

    if not isinstance(
        normalized,
        list,
    ):
        raise ValueError("normalized_files must be a list.")

    for record in normalized:
        if not isinstance(
            record,
            dict,
        ):
            raise ValueError("Invalid normalized provenance record.")

        filename = str(record["filename"])

        candidates = list(normalized_root.rglob(filename))

        if len(candidates) != 1:
            raise ValueError(
                f"Expected exactly one normalized file named {filename}; found {len(candidates)}"
            )

        path = candidates[0]

        frame = validate_normalized_file(path)

        if int(record["row_count"]) != len(frame):
            raise ValueError(f"Row-count mismatch for {filename}")

        if str(record["sha256"]) != sha256_file(path):
            raise ValueError(f"Content hash mismatch for {filename}")

        if str(record["schema_fingerprint"]) != canonical_schema_fingerprint(frame):
            raise ValueError(f"Schema fingerprint mismatch for {filename}")


def validate_source_specific_identity(
    frames: dict[str, pd.DataFrame],
) -> None:
    """Prove that evidence environments retain separate identity namespaces."""

    required_identity = {
        "hillstrom": "anonymous_customer_id",
        "dunnhumby": "retail_household_id",
        "criteo": "media_user_id",
        "retailrocket": "visitor_id",
    }

    for source, identity in required_identity.items():
        frame = frames[source]

        if identity not in frame.columns:
            raise ValueError(f"{source} missing source-specific identity {identity}")

        generic = GENERIC_ID_COLUMNS.intersection({str(column).lower() for column in frame.columns})

        if generic:
            raise ValueError(f"{source} exposes prohibited generic IDs: {sorted(generic)}")


def validate_all(
    *,
    cache_root: Path,
) -> dict[str, int]:
    """Validate all four cached evidence environments."""

    normalized_root = cache_root / "normalized"

    provenance_root = cache_root / "provenance"

    hillstrom = validate_normalized_file(normalized_root / "hillstrom" / "hillstrom.parquet")

    dunnhumby = validate_normalized_file(normalized_root / "dunnhumby" / "transactions.parquet")

    criteo = validate_normalized_file(normalized_root / "criteo" / "criteo_attribution.parquet")

    retailrocket = validate_normalized_file(normalized_root / "retailrocket" / "events.parquet")

    frames = {
        "hillstrom": hillstrom,
        "dunnhumby": dunnhumby,
        "criteo": criteo,
        "retailrocket": retailrocket,
    }

    validate_source_specific_identity(frames)

    for source in PUBLIC_SOURCE_IDS:
        validate_source_provenance(
            provenance_root / f"{source}.json",
            normalized_root,
        )

    return {source: len(frame) for source, frame in frames.items()}
