"""dunnhumby Complete Journey adapter."""

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
    "https://www.kaggle.com/api/v1/datasets/download/frtgnn/dunnhumby-the-complete-journey"
)

REQUIRED_FILES: Final[tuple[str, ...]] = (
    "transaction_data.csv",
    "product.csv",
    "campaign_table.csv",
    "coupon.csv",
    "coupon_redempt.csv",
)

TRANSACTION_COLUMNS: Final[set[str]] = {
    "household_key",
    "basket_id",
    "day",
    "product_id",
    "quantity",
    "sales_value",
    "store_id",
    "retail_disc",
    "week_no",
    "coupon_disc",
}

PRODUCT_COLUMNS: Final[set[str]] = {
    "product_id",
    "department",
    "brand",
    "commodity_desc",
    "sub_commodity_desc",
}


def _extract_required(
    archive: Path,
    raw_dir: Path,
) -> dict[str, Path]:
    """Extract only the raw tables needed by Project 4."""

    raw_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted: dict[str, Path] = {}

    with zipfile.ZipFile(archive) as handle:
        candidates = {
            Path(name).name.lower(): name for name in handle.namelist() if not name.endswith("/")
        }

        for required in REQUIRED_FILES:
            member = candidates.get(required.lower())

            if member is None:
                raise ValueError(f"dunnhumby archive missing required table: {required}")

            destination = raw_dir / required

            if not destination.exists():
                with (
                    handle.open(member) as source,
                    destination.open("wb") as output,
                ):
                    while True:
                        chunk = source.read(1024 * 1024)

                        if not chunk:
                            break

                        output.write(chunk)

            extracted[required] = destination

    return extracted


def _canonical_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Complete Journey column names."""

    result = frame.copy()

    result.columns = [str(column).strip().lower() for column in result.columns]

    return result


def normalize_transactions(
    raw: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Complete Journey transaction lines."""

    frame = _canonical_columns(raw)

    require_columns(
        frame,
        TRANSACTION_COLUMNS,
        label="dunnhumby transactions",
    )

    frame = frame.rename(
        columns={
            "household_key": "retail_household_id",
        }
    )

    numeric = (
        "retail_household_id",
        "basket_id",
        "day",
        "product_id",
        "quantity",
        "sales_value",
        "store_id",
        "retail_disc",
        "week_no",
        "coupon_disc",
    )

    for column in numeric:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

    if (
        frame[
            [
                "retail_household_id",
                "basket_id",
                "product_id",
            ]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("dunnhumby transaction identity fields contain nulls.")

    if (frame["quantity"] < 0).any():
        raise ValueError("dunnhumby quantity must be nonnegative.")

    if (frame["sales_value"] < 0).any():
        raise ValueError("dunnhumby sales_value must be nonnegative.")

    if (frame["day"] < 0).any():
        raise ValueError("dunnhumby day must be nonnegative.")

    frame.insert(
        0,
        "evidence_class",
        EvidenceClass.RETAIL_BEHAVIOR.value,
    )

    frame = stable_sort(
        frame,
        [
            "retail_household_id",
            "day",
            "basket_id",
            "product_id",
        ],
    )

    ensure_no_generic_identity(frame)
    ensure_no_pii_columns(frame)

    return frame


def normalize_products(
    raw: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Complete Journey product taxonomy."""

    frame = _canonical_columns(raw)

    require_columns(
        frame,
        PRODUCT_COLUMNS,
        label="dunnhumby products",
    )

    if frame["product_id"].isna().any():
        raise ValueError("dunnhumby product IDs contain nulls.")

    frame = stable_sort(
        frame,
        [
            "product_id",
        ],
    )

    ensure_no_generic_identity(frame)
    ensure_no_pii_columns(frame)

    return frame


def normalize_small_table(
    raw: pd.DataFrame,
    *,
    table_name: str,
) -> pd.DataFrame:
    """Normalize campaign/coupon supporting tables."""

    frame = _canonical_columns(raw)

    if frame.empty:
        raise ValueError(f"dunnhumby {table_name} table is empty.")

    if "household_key" in frame.columns:
        frame = frame.rename(
            columns={
                "household_key": "retail_household_id",
            }
        )

    frame = stable_sort(
        frame,
        list(frame.columns),
    )

    ensure_no_generic_identity(frame)
    ensure_no_pii_columns(frame)

    return frame


def fetch_and_normalize(
    policy: CachePolicy,
    *,
    offline: bool,
) -> SourceResult:
    """Acquire and normalize required Complete Journey tables."""

    archive = policy.raw_dir.parent / "dunnhumby_complete_journey.zip"

    download_file(
        TRANSPORT_URL,
        archive,
        offline=offline,
    )

    raw_files = _extract_required(
        archive,
        policy.raw_dir,
    )

    transactions = normalize_transactions(
        pd.read_csv(
            raw_files["transaction_data.csv"],
            low_memory=False,
        )
    )

    products = normalize_products(
        pd.read_csv(
            raw_files["product.csv"],
            low_memory=False,
        )
    )

    campaign = normalize_small_table(
        pd.read_csv(
            raw_files["campaign_table.csv"],
            low_memory=False,
        ),
        table_name="campaign_table",
    )

    coupon = normalize_small_table(
        pd.read_csv(
            raw_files["coupon.csv"],
            low_memory=False,
        ),
        table_name="coupon",
    )

    redemption = normalize_small_table(
        pd.read_csv(
            raw_files["coupon_redempt.csv"],
            low_memory=False,
        ),
        table_name="coupon_redempt",
    )

    policy.normalized_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = [
        (
            "transactions.parquet",
            transactions,
        ),
        (
            "products.parquet",
            products,
        ),
        (
            "campaign_table.parquet",
            campaign,
        ),
        (
            "coupon.parquet",
            coupon,
        ),
        (
            "coupon_redempt.parquet",
            redemption,
        ),
    ]

    normalized_files: list[Path] = []
    frames: list[pd.DataFrame] = []

    for filename, frame in outputs:
        path = policy.normalized_dir / filename

        frame.to_parquet(
            path,
            index=False,
        )

        normalized_files.append(path)
        frames.append(frame)

    provenance = write_provenance(
        path=(policy.provenance_dir / "dunnhumby.json"),
        source_id=SourceId.DUNNHUMBY,
        evidence_class=EvidenceClass.RETAIL_BEHAVIOR,
        publisher_source=("https://www.dunnhumby.com/source-files/"),
        transport_source=TRANSPORT_URL,
        normalized_files=normalized_files,
        frames=frames,
        raw_files=[
            archive,
            *raw_files.values(),
        ],
        license_or_terms=(
            "Non-commercial research/analytical use; "
            "Database/Open Database transport metadata; "
            "raw files are not redistributed by Project 4."
        ),
    )

    return SourceResult(
        source_id=SourceId.DUNNHUMBY,
        evidence_class=EvidenceClass.RETAIL_BEHAVIOR,
        normalized_files=tuple(normalized_files),
        provenance_file=provenance,
        row_count=len(transactions),
    )
