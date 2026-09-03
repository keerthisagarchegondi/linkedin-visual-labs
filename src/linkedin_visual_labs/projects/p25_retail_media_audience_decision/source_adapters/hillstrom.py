"""Hillstrom randomized experiment adapter."""

from __future__ import annotations

import hashlib
from typing import Final

import pandas as pd
from sklift.datasets import fetch_hillstrom  # type: ignore[import-untyped]

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
    ensure_no_generic_identity,
    ensure_no_pii_columns,
    require_columns,
    stable_sort,
)

FEATURE_COLUMNS: Final[set[str]] = {
    "recency",
    "history",
    "history_segment",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
}

OUTCOME_COLUMNS: Final[set[str]] = {
    "visit",
    "conversion",
    "spend",
}

TREATMENTS: Final[set[str]] = {
    "Mens E-Mail",
    "Womens E-Mail",
    "No E-Mail",
}


def normalize_hillstrom(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    treatment: pd.Series,
) -> pd.DataFrame:
    """Create the canonical Hillstrom analytical table."""

    data = features.copy()

    data.columns = [str(column).strip().lower() for column in data.columns]

    target_frame = targets.copy()

    target_frame.columns = [str(column).strip().lower() for column in target_frame.columns]

    require_columns(
        data,
        FEATURE_COLUMNS,
        label="Hillstrom features",
    )

    require_columns(
        target_frame,
        OUTCOME_COLUMNS,
        label="Hillstrom outcomes",
    )

    data = pd.concat(
        [
            data.reset_index(drop=True),
            target_frame.reset_index(drop=True),
        ],
        axis=1,
    )

    data["treatment"] = treatment.reset_index(drop=True).astype("string")

    if set(data["treatment"].dropna().unique()) != TREATMENTS:
        raise ValueError(
            "Hillstrom treatment arms do not match "
            f"the frozen contract: {sorted(data['treatment'].unique())}"
        )

    for column in (
        "visit",
        "conversion",
    ):
        values = set(
            pd.to_numeric(
                data[column],
                errors="raise",
            )
            .dropna()
            .astype(int)
            .unique()
        )

        if not values.issubset(
            {
                0,
                1,
            }
        ):
            raise ValueError(f"{column} must be binary; found {sorted(values)}")

        data[column] = pd.to_numeric(
            data[column],
            errors="raise",
        ).astype("int8")

    data["spend"] = pd.to_numeric(
        data["spend"],
        errors="raise",
    ).astype(float)

    if (data["spend"] < 0).any():
        raise ValueError("Hillstrom spend must be nonnegative.")

    for column in (
        "recency",
        "history",
    ):
        data[column] = pd.to_numeric(
            data[column],
            errors="raise",
        )

        if (data[column] < 0).any():
            raise ValueError(f"Hillstrom {column} must be nonnegative.")

    canonical_sort = [
        "recency",
        "history",
        "history_segment",
        "mens",
        "womens",
        "zip_code",
        "newbie",
        "channel",
        "treatment",
        "visit",
        "conversion",
        "spend",
    ]

    data = stable_sort(
        data,
        canonical_sort,
    )

    identity_payload = data[canonical_sort].astype("string").fillna("<NULL>").agg("|".join, axis=1)

    duplicate_rank = (
        identity_payload.groupby(
            identity_payload,
            sort=False,
        )
        .cumcount()
        .astype(str)
    )

    data.insert(
        0,
        "anonymous_customer_id",
        [
            "hillstrom_" + hashlib.sha256(f"{payload}|{rank}".encode()).hexdigest()[:20]
            for payload, rank in zip(
                identity_payload,
                duplicate_rank,
                strict=True,
            )
        ],
    )

    if not data["anonymous_customer_id"].is_unique:
        raise ValueError("Hillstrom anonymous customer IDs are not unique.")

    data.insert(
        1,
        "evidence_class",
        EvidenceClass.RANDOMIZED_EXPERIMENT.value,
    )

    ensure_no_generic_identity(data)
    ensure_no_pii_columns(data)

    return data


def fetch_and_normalize(
    policy: CachePolicy,
    *,
    offline: bool,
) -> SourceResult:
    """Fetch Hillstrom via scikit-uplift and normalize it."""

    policy.raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    policy.normalized_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataset = fetch_hillstrom(
        target_col="all",
        data_home=str(policy.raw_dir),
        dest_subdir="hillstrom",
        download_if_missing=not offline,
    )

    features = dataset.data
    targets = dataset.target
    treatment = dataset.treatment

    if not isinstance(features, pd.DataFrame):
        raise TypeError("fetch_hillstrom.data must be a DataFrame.")

    if not isinstance(targets, pd.DataFrame):
        raise TypeError("fetch_hillstrom(target_col='all').target must be a DataFrame.")

    if not isinstance(treatment, pd.Series):
        raise TypeError("fetch_hillstrom.treatment must be a Series.")

    normalized = normalize_hillstrom(
        features,
        targets,
        treatment,
    )

    output = policy.normalized_dir / "hillstrom.parquet"

    normalized.to_parquet(
        output,
        index=False,
    )

    raw_files = list(policy.raw_dir.rglob("hillstorm_no_indices.csv.gz"))

    provenance = write_provenance(
        path=(policy.provenance_dir / "hillstrom.json"),
        source_id=SourceId.HILLSTROM,
        evidence_class=EvidenceClass.RANDOMIZED_EXPERIMENT,
        publisher_source=("Kevin Hillstrom MineThatData Email Analytics Challenge"),
        transport_source=("sklift.datasets.fetch_hillstrom"),
        normalized_files=[
            output,
        ],
        frames=[
            normalized,
        ],
        raw_files=raw_files,
        license_or_terms=(
            "Public analytical challenge dataset; raw cache not redistributed by this project."
        ),
    )

    return SourceResult(
        source_id=SourceId.HILLSTROM,
        evidence_class=EvidenceClass.RANDOMIZED_EXPERIMENT,
        normalized_files=(output,),
        provenance_file=provenance,
        row_count=len(normalized),
    )
