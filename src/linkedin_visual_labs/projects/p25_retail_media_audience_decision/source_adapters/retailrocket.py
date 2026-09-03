"""Retailrocket behavioral event adapter."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Final

import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    EvidenceClass,
    SourceId,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.provenance import (
    write_provenance,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    CachePolicy,
    SourceResult,
    download_file,
    ensure_no_generic_identity,
    ensure_no_pii_columns,
    require_columns,
    stable_sort,
)

TRANSPORT_URL: Final = (
    "https://www.kaggle.com/api/v1/datasets/download/retailrocket/ecommerce-dataset"
)

EVENT_TYPES: Final[set[str]] = {
    "view",
    "addtocart",
    "transaction",
}

REQUIRED_COLUMNS: Final[set[str]] = {
    "timestamp",
    "visitorid",
    "event",
    "itemid",
    "transactionid",
}


def _extract_events(
    archive: Path,
    raw_dir: Path,
) -> Path:
    """Extract only Retailrocket events.csv."""

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = raw_dir / "events.csv"

    if destination.is_file():
        return destination

    with zipfile.ZipFile(archive) as handle:
        candidates = {
            Path(name).name.lower(): name for name in handle.namelist() if not name.endswith("/")
        }

        member = candidates.get("events.csv")

        if member is None:
            raise ValueError("Retailrocket archive does not contain events.csv")

        with handle.open(member) as source, destination.open("wb") as output:
            while True:
                chunk = source.read(1024 * 1024)

                if not chunk:
                    break

                output.write(chunk)

    return destination


def normalize_events(
    raw: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Retailrocket behavioral events."""

    frame = raw.copy()

    frame.columns = [str(column).strip().lower() for column in frame.columns]

    require_columns(
        frame,
        REQUIRED_COLUMNS,
        label="Retailrocket events",
    )

    frame = frame.rename(
        columns={
            "visitorid": "visitor_id",
            "itemid": "item_id",
            "transactionid": "transaction_id",
        }
    )

    frame["timestamp"] = pd.to_numeric(
        frame["timestamp"],
        errors="raise",
    )

    frame["visitor_id"] = pd.to_numeric(
        frame["visitor_id"],
        errors="raise",
    )

    frame["item_id"] = pd.to_numeric(
        frame["item_id"],
        errors="raise",
    )

    frame["event"] = frame["event"].astype("string").str.lower()

    observed = set(frame["event"].dropna().unique())

    unexpected = sorted(observed - EVENT_TYPES)

    if unexpected:
        raise ValueError(f"Unexpected Retailrocket event types: {unexpected}")

    if not EVENT_TYPES.issubset(observed):
        missing = sorted(EVENT_TYPES - observed)

        raise ValueError(f"Retailrocket missing required event types: {missing}")

    if (
        frame[
            [
                "timestamp",
                "visitor_id",
                "item_id",
            ]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Retailrocket identity/timestamp fields contain nulls.")

    if (frame["timestamp"] < 0).any():
        raise ValueError("Retailrocket timestamps must be nonnegative.")

    frame.insert(
        0,
        "evidence_class",
        EvidenceClass.BEHAVIORAL_FUNNEL.value,
    )

    frame = stable_sort(
        frame,
        [
            "timestamp",
            "visitor_id",
            "item_id",
            "event",
        ],
    )

    ensure_no_generic_identity(frame)
    ensure_no_pii_columns(frame)

    return frame


def fetch_and_normalize(
    policy: CachePolicy,
    *,
    offline: bool,
) -> SourceResult:
    """Acquire and normalize Retailrocket behavioral events."""

    archive = policy.raw_dir.parent / "retailrocket.zip"

    download_file(
        TRANSPORT_URL,
        archive,
        offline=offline,
    )

    raw_events = _extract_events(
        archive,
        policy.raw_dir,
    )

    frame = normalize_events(
        pd.read_csv(
            raw_events,
            low_memory=False,
        )
    )

    policy.normalized_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = policy.normalized_dir / "events.parquet"

    frame.to_parquet(
        output,
        index=False,
    )

    provenance = write_provenance(
        path=(policy.provenance_dir / "retailrocket.json"),
        source_id=SourceId.RETAILROCKET,
        evidence_class=EvidenceClass.BEHAVIORAL_FUNNEL,
        publisher_source=("Retailrocket recommender system dataset"),
        transport_source=TRANSPORT_URL,
        normalized_files=[
            output,
        ],
        frames=[
            frame,
        ],
        raw_files=[
            archive,
            raw_events,
        ],
        license_or_terms=(
            "Published anonymized research dataset; raw files not redistributed by Project 4."
        ),
    )

    return SourceResult(
        source_id=SourceId.RETAILROCKET,
        evidence_class=EvidenceClass.BEHAVIORAL_FUNNEL,
        normalized_files=(output,),
        provenance_file=provenance,
        row_count=len(frame),
    )
