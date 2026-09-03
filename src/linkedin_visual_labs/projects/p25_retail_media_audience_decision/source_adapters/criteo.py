"""Criteo Attribution dataset adapter."""

from __future__ import annotations

import math
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

DOWNLOAD_URL: Final = (
    "https://huggingface.co/datasets/criteo/"
    "criteo-attribution-dataset/resolve/main/"
    "criteo_attribution_dataset.tsv.gz?download=true"
)

EXPECTED_SHA256: Final = "94ac7a465564349bc7ba008602211d5990a3c53cc133abc0aadef61ea2391a98"

EXPECTED_TOTAL_ROWS: Final = 16_500_000

REQUIRED_COLUMNS: Final[set[str]] = {
    "timestamp",
    "uid",
    "campaign",
    "conversion",
    "conversion_timestamp",
    "conversion_id",
    "attribution",
    "click",
    "cost",
    "cpo",
    "time_since_last_click",
}


def normalize_criteo_chunk(
    raw: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and normalize one Criteo chunk."""

    frame = raw.copy()

    frame.columns = [str(column).strip().lower() for column in frame.columns]

    require_columns(
        frame,
        REQUIRED_COLUMNS,
        label="Criteo attribution",
    )

    frame = frame.rename(
        columns={
            "uid": "media_user_id",
        }
    )

    for column in (
        "timestamp",
        "conversion_timestamp",
        "conversion_id",
        "click",
        "conversion",
        "attribution",
        "cost",
        "cpo",
        "time_since_last_click",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    for column in (
        "click",
        "conversion",
        "attribution",
    ):
        values = set(frame[column].dropna().astype(int).unique())

        if not values.issubset(
            {
                0,
                1,
            }
        ):
            raise ValueError(f"Criteo {column} must be binary; found {sorted(values)}")

    if (frame["timestamp"] < 0).any():
        raise ValueError("Criteo timestamps must be nonnegative.")

    if (frame["cost"] < 0).any():
        raise ValueError("Criteo cost signal must be nonnegative.")

    frame.insert(
        0,
        "evidence_class",
        EvidenceClass.MEDIA_ATTRIBUTION.value,
    )

    ensure_no_generic_identity(frame)
    ensure_no_pii_columns(frame)

    return frame


def _deterministic_keep_mask(
    frame: pd.DataFrame,
    *,
    max_rows: int,
) -> pd.Series:
    """Approximate a deterministic source-wide sample by row hash."""

    if max_rows <= 0:
        raise ValueError("Criteo max_rows must be positive.")

    fraction = min(
        1.0,
        max_rows / EXPECTED_TOTAL_ROWS,
    )

    denominator = 100_000

    threshold = max(
        1,
        math.ceil(fraction * denominator),
    )

    hash_input = frame[
        [
            "media_user_id",
            "timestamp",
            "campaign",
        ]
    ].astype("string")

    hashes = pd.util.hash_pandas_object(
        hash_input,
        index=False,
        hash_key="0123456789123456",
    )

    return hashes % denominator < threshold


def fetch_and_normalize(
    policy: CachePolicy,
    *,
    offline: bool,
    max_rows: int,
) -> SourceResult:
    """Download, deterministically sample, and normalize Criteo."""

    raw_file = policy.raw_dir / "criteo_attribution_dataset.tsv.gz"

    download_file(
        DOWNLOAD_URL,
        raw_file,
        expected_sha256=EXPECTED_SHA256,
        offline=offline,
    )

    sampled: list[pd.DataFrame] = []

    collected = 0

    for raw_chunk in pd.read_csv(
        raw_file,
        sep="	",
        compression="gzip",
        chunksize=250_000,
        low_memory=False,
    ):
        normalized = normalize_criteo_chunk(raw_chunk)

        mask = _deterministic_keep_mask(
            normalized,
            max_rows=max_rows,
        )

        selected = normalized.loc[mask]

        if not selected.empty:
            sampled.append(selected)

            collected += len(selected)

        if collected >= (max_rows + 250_000):
            break

    if not sampled:
        raise ValueError("Deterministic Criteo sampling produced no rows.")

    frame = pd.concat(
        sampled,
        ignore_index=True,
    )

    frame = stable_sort(
        frame,
        [
            "timestamp",
            "media_user_id",
            "campaign",
        ],
    )

    if len(frame) > max_rows:
        frame = frame.iloc[:max_rows].reset_index(drop=True)

    output = policy.normalized_dir / "criteo_attribution.parquet"

    policy.normalized_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_parquet(
        output,
        index=False,
    )

    provenance = write_provenance(
        path=(policy.provenance_dir / "criteo.json"),
        source_id=SourceId.CRITEO,
        evidence_class=EvidenceClass.MEDIA_ATTRIBUTION,
        publisher_source=("https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/"),
        transport_source=DOWNLOAD_URL,
        normalized_files=[
            output,
        ],
        frames=[
            frame,
        ],
        raw_files=[
            raw_file,
        ],
        license_or_terms=(
            "CC BY-NC-SA 4.0; raw data not redistributed. "
            "Cost values are transformed source values and "
            "must not be represented as literal advertiser spend."
        ),
    )

    return SourceResult(
        source_id=SourceId.CRITEO,
        evidence_class=EvidenceClass.MEDIA_ATTRIBUTION,
        normalized_files=(output,),
        provenance_file=provenance,
        row_count=len(frame),
    )
