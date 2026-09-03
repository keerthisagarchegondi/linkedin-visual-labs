from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from .models import SourceId
from .pipeline import cache_policy
from .source_adapters.base import stable_frame_hash

TOP_DEPARTMENT_AFFINITIES: Final[int] = 12
TOP_COMMODITY_AFFINITIES: Final[int] = 20
TOP_BRAND_AFFINITIES: Final[int] = 10


HOUSEHOLD_ALIASES: Final[tuple[str, ...]] = (
    "household_id",
    "retail_household_id",
    "household_key",
    "household",
)

BASKET_ALIASES: Final[tuple[str, ...]] = (
    "basket_id",
    "basket_key",
    "basket",
)

PRODUCT_ALIASES: Final[tuple[str, ...]] = (
    "product_id",
    "product_key",
    "product",
    "upc",
)

SOURCE_DAY_ALIASES: Final[tuple[str, ...]] = (
    "day",
    "transaction_day",
    "day_index",
)


TIMESTAMP_ALIASES: Final[tuple[str, ...]] = (
    "transaction_timestamp",
    "transaction_datetime",
    "transaction_date",
    "timestamp",
    "date",
    *SOURCE_DAY_ALIASES,
)

SALES_ALIASES: Final[tuple[str, ...]] = (
    "sales_value",
    "sales",
    "net_sales",
)

QUANTITY_ALIASES: Final[tuple[str, ...]] = (
    "quantity",
    "units",
    "qty",
)

RETAIL_DISCOUNT_ALIASES: Final[tuple[str, ...]] = (
    "retail_discount",
    "retail_disc",
)

COUPON_DISCOUNT_ALIASES: Final[tuple[str, ...]] = (
    "coupon_discount",
    "coupon_disc",
)

COUPON_MATCH_DISCOUNT_ALIASES: Final[tuple[str, ...]] = (
    "coupon_match_discount",
    "coupon_match_disc",
)

DEPARTMENT_ALIASES: Final[tuple[str, ...]] = (
    "department",
    "department_desc",
)

COMMODITY_ALIASES: Final[tuple[str, ...]] = (
    "commodity",
    "commodity_desc",
    "category",
    "category_desc",
)

BRAND_ALIASES: Final[tuple[str, ...]] = (
    "brand",
    "brand_desc",
)


@dataclass(frozen=True)
class RetailFeatureFrames:
    customer_features: pd.DataFrame
    retail_kpis: pd.DataFrame
    category_performance: pd.DataFrame
    metadata: dict[str, object]


def _pick_column(
    frame: pd.DataFrame,
    aliases: tuple[str, ...],
    *,
    required: bool,
) -> str | None:
    lowered = {str(column).lower(): str(column) for column in frame.columns}

    for alias in aliases:
        actual = lowered.get(alias.lower())

        if actual is not None:
            return actual

    if required:
        raise ValueError(
            f"Missing required column. Accepted aliases={aliases}; actual={list(frame.columns)}"
        )

    return None


def _slug(
    value: object,
) -> str:
    text = str(value).strip().lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text,
    ).strip("_")

    return text or "unknown"


def _as_numeric(
    series: pd.Series,
) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def _as_datetime(
    series: pd.Series,
) -> pd.Series:
    return pd.to_datetime(
        series,
        errors="coerce",
        utc=False,
    )


def _is_source_day_column(
    column: str,
) -> bool:
    return column.lower() in SOURCE_DAY_ALIASES


def _standardize_time_values(
    series: pd.Series,
    *,
    source_column: str,
) -> pd.Series:
    if _is_source_day_column(source_column):
        return pd.to_numeric(
            series,
            errors="coerce",
        ).astype("Int64")

    return _as_datetime(series)


def _elapsed_days(
    later: object,
    earlier: object,
) -> int:
    if isinstance(
        later,
        pd.Timestamp,
    ) and isinstance(
        earlier,
        pd.Timestamp,
    ):
        return int((later - earlier).days)

    return int(str(later)) - int(str(earlier))


def _elapsed_day_series(
    later: object,
    earlier: pd.Series,
) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(earlier.dtype):
        later_timestamp = pd.Timestamp(str(later))

        earlier_timestamp = pd.to_datetime(
            earlier,
            errors="raise",
        )

        return (later_timestamp - earlier_timestamp).dt.days

    later_numeric = float(str(later))

    earlier_numeric = pd.to_numeric(
        earlier,
        errors="raise",
    )

    return later_numeric - earlier_numeric


def _time_value_for_metadata(
    value: object,
) -> str:
    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    return str(value)


def _read_normalized_tables(
    repository_root: Path,
) -> dict[str, pd.DataFrame]:
    policy = cache_policy(
        repository_root,
        name="dunnhumby",
        source_id=SourceId.DUNNHUMBY,
    )

    normalized_dir = Path(policy.normalized_dir)

    parquets = sorted(normalized_dir.rglob("*.parquet"))

    if not parquets:
        raise FileNotFoundError("No normalized dunnhumby Parquet files found.")

    tables: dict[str, pd.DataFrame] = {}

    for path in parquets:
        tables[path.stem] = pd.read_parquet(path)

    return tables


def _role_score(
    frame: pd.DataFrame,
    alias_groups: tuple[tuple[str, ...], ...],
) -> int:
    columns = {str(column).lower() for column in frame.columns}

    score = 0

    for aliases in alias_groups:
        if any(alias.lower() in columns for alias in aliases):
            score += 1

    return score


def _select_transactions(
    tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    required_groups = (
        HOUSEHOLD_ALIASES,
        BASKET_ALIASES,
        PRODUCT_ALIASES,
        SALES_ALIASES,
    )

    candidates: list[tuple[int, int, str, pd.DataFrame]] = []

    for name, frame in tables.items():
        score = _role_score(
            frame,
            required_groups,
        )

        candidates.append(
            (
                score,
                len(frame),
                name,
                frame,
            )
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
        ),
        reverse=True,
    )

    if not candidates:
        raise ValueError("No normalized dunnhumby tables available.")

    score, _rows, name, frame = candidates[0]

    if score != len(required_groups):
        raise ValueError(
            "Could not identify transaction table. "
            f"Best candidate={name!r}; "
            f"score={score}/{len(required_groups)}; "
            f"columns={list(frame.columns)}"
        )

    return frame.copy()


def _select_products(
    tables: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    candidates: list[tuple[int, int, str, pd.DataFrame]] = []

    for name, frame in tables.items():
        product_score = _role_score(
            frame,
            (PRODUCT_ALIASES,),
        )

        taxonomy_score = _role_score(
            frame,
            (
                DEPARTMENT_ALIASES,
                COMMODITY_ALIASES,
                BRAND_ALIASES,
            ),
        )

        score = product_score * 10 + taxonomy_score

        candidates.append(
            (
                score,
                len(frame),
                name,
                frame,
            )
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
        ),
        reverse=True,
    )

    if not candidates:
        raise ValueError("No normalized dunnhumby tables available.")

    score, _rows, name, frame = candidates[0]

    if score < 11:
        raise ValueError(
            "Could not identify product taxonomy table. "
            f"Best candidate={name!r}; "
            f"score={score}; "
            f"columns={list(frame.columns)}"
        )

    return frame.copy()


def _standardize_transactions(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    household = _pick_column(
        frame,
        HOUSEHOLD_ALIASES,
        required=True,
    )

    basket = _pick_column(
        frame,
        BASKET_ALIASES,
        required=True,
    )

    product = _pick_column(
        frame,
        PRODUCT_ALIASES,
        required=True,
    )

    timestamp = _pick_column(
        frame,
        TIMESTAMP_ALIASES,
        required=True,
    )

    sales = _pick_column(
        frame,
        SALES_ALIASES,
        required=True,
    )

    quantity = _pick_column(
        frame,
        QUANTITY_ALIASES,
        required=False,
    )

    retail_discount = _pick_column(
        frame,
        RETAIL_DISCOUNT_ALIASES,
        required=False,
    )

    coupon_discount = _pick_column(
        frame,
        COUPON_DISCOUNT_ALIASES,
        required=False,
    )

    coupon_match_discount = _pick_column(
        frame,
        COUPON_MATCH_DISCOUNT_ALIASES,
        required=False,
    )

    household_column = str(household)

    basket_column = str(basket)

    product_column = str(product)

    timestamp_column = str(timestamp)

    sales_column = str(sales)

    output = pd.DataFrame(
        {
            "household_id": frame[household_column].astype("string"),
            "basket_id": frame[basket_column].astype("string"),
            "product_id": frame[product_column].astype("string"),
            "transaction_timestamp": _standardize_time_values(
                frame[timestamp_column],
                source_column=timestamp_column,
            ),
            "sales_value": _as_numeric(frame[sales_column]),
        }
    )

    if quantity is None:
        output["quantity"] = 1.0
    else:
        output["quantity"] = _as_numeric(frame[quantity])

    for canonical, source_column in (
        (
            "retail_discount",
            retail_discount,
        ),
        (
            "coupon_discount",
            coupon_discount,
        ),
        (
            "coupon_match_discount",
            coupon_match_discount,
        ),
    ):
        if source_column is None:
            output[canonical] = 0.0
        else:
            output[canonical] = _as_numeric(frame[source_column])

    output = output.dropna(
        subset=[
            "household_id",
            "basket_id",
            "transaction_timestamp",
            "sales_value",
        ]
    ).copy()

    output["sales_value"] = output["sales_value"].fillna(0.0)

    output["quantity"] = output["quantity"].fillna(0.0)

    for column in (
        "retail_discount",
        "coupon_discount",
        "coupon_match_discount",
    ):
        output[column] = output[column].fillna(0.0)

    if _is_source_day_column(timestamp_column):
        output["transaction_date"] = pd.to_numeric(
            output["transaction_timestamp"],
            errors="raise",
        ).astype("int64")
    else:
        output["transaction_date"] = output["transaction_timestamp"].dt.normalize()

    output["retail_discount_amount"] = output["retail_discount"].abs()

    output["coupon_discount_amount"] = output["coupon_discount"].abs()

    output["coupon_match_discount_amount"] = output["coupon_match_discount"].abs()

    output["total_discount_amount"] = (
        output["retail_discount_amount"]
        + output["coupon_discount_amount"]
        + output["coupon_match_discount_amount"]
    )

    output["has_retail_discount"] = output["retail_discount_amount"] > 0

    output["has_coupon"] = (
        output["coupon_discount_amount"] + output["coupon_match_discount_amount"] > 0
    )

    output["has_promotion"] = output["total_discount_amount"] > 0

    output = output.sort_values(
        [
            "household_id",
            "transaction_timestamp",
            "basket_id",
            "product_id",
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    return output


def _standardize_products(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    product = _pick_column(
        frame,
        PRODUCT_ALIASES,
        required=True,
    )

    department = _pick_column(
        frame,
        DEPARTMENT_ALIASES,
        required=False,
    )

    commodity = _pick_column(
        frame,
        COMMODITY_ALIASES,
        required=False,
    )

    brand = _pick_column(
        frame,
        BRAND_ALIASES,
        required=False,
    )

    output = pd.DataFrame(
        {
            "product_id": frame[str(product)].astype("string"),
        }
    )

    for canonical, source_column in (
        (
            "department",
            department,
        ),
        (
            "commodity",
            commodity,
        ),
        (
            "brand",
            brand,
        ),
    ):
        if source_column is None:
            output[canonical] = "UNKNOWN"
        else:
            output[canonical] = (
                frame[source_column]
                .astype("string")
                .fillna("UNKNOWN")
                .str.strip()
                .replace(
                    "",
                    "UNKNOWN",
                )
            )

    output = (
        output.drop_duplicates(
            subset=["product_id"],
            keep="first",
        )
        .sort_values(
            ["product_id"],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    return output


def _basket_table(
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    basket = (
        transactions.groupby(
            [
                "household_id",
                "basket_id",
            ],
            as_index=False,
            sort=True,
        )
        .agg(
            transaction_date=(
                "transaction_date",
                "min",
            ),
            sales_value=(
                "sales_value",
                "sum",
            ),
            quantity=(
                "quantity",
                "sum",
            ),
            total_discount_amount=(
                "total_discount_amount",
                "sum",
            ),
            has_retail_discount=(
                "has_retail_discount",
                "max",
            ),
            has_coupon=(
                "has_coupon",
                "max",
            ),
            has_promotion=(
                "has_promotion",
                "max",
            ),
        )
        .sort_values(
            [
                "household_id",
                "transaction_date",
                "basket_id",
            ],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    return basket


def _median_days_between_orders(
    baskets: pd.DataFrame,
) -> pd.Series:
    unique_dates = (
        baskets[
            [
                "household_id",
                "transaction_date",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            [
                "household_id",
                "transaction_date",
            ],
            kind="mergesort",
        )
    )

    differences = unique_dates.groupby(
        "household_id",
        sort=True,
    )["transaction_date"].diff()

    if pd.api.types.is_timedelta64_dtype(differences.dtype):
        unique_dates["days_between_orders"] = differences.dt.days
    else:
        unique_dates["days_between_orders"] = pd.to_numeric(
            differences,
            errors="coerce",
        )

    result: pd.Series = unique_dates.groupby(
        "household_id",
        sort=True,
    )["days_between_orders"].median()

    return result


def _dominant_value(
    joined: pd.DataFrame,
    column: str,
) -> pd.Series:
    grouped: pd.DataFrame = joined.groupby(
        [
            "household_id",
            column,
        ],
        as_index=False,
        sort=True,
    ).agg(
        sales_value=(
            "sales_value",
            "sum",
        ),
    )

    grouped = grouped.sort_values(
        [
            "household_id",
            "sales_value",
            column,
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="mergesort",
    )

    winners: pd.DataFrame = grouped.drop_duplicates(
        subset=[
            "household_id",
        ],
        keep="first",
    )

    result: pd.Series = winners.set_index(
        "household_id",
    )[column]

    return result


def _category_concentration(
    joined: pd.DataFrame,
) -> pd.Series:
    grouped: pd.DataFrame = joined.groupby(
        [
            "household_id",
            "commodity",
        ],
        as_index=False,
        sort=True,
    ).agg(
        sales_value=(
            "sales_value",
            "sum",
        ),
    )

    totals: pd.Series = grouped.groupby(
        "household_id",
        sort=True,
    )["sales_value"].transform(
        "sum",
    )

    grouped["share"] = np.where(
        totals > 0,
        grouped["sales_value"] / totals,
        0.0,
    )

    grouped["share_sq"] = grouped["share"] ** 2

    result: pd.Series = grouped.groupby(
        "household_id",
        sort=True,
    )["share_sq"].sum()

    return result


def _top_values(
    joined: pd.DataFrame,
    column: str,
    limit: int,
) -> list[str]:
    grouped: pd.DataFrame = joined.groupby(
        column,
        as_index=False,
        dropna=False,
        sort=True,
    ).agg(
        sales_value=(
            "sales_value",
            "sum",
        ),
    )

    values: pd.DataFrame = grouped.sort_values(
        [
            "sales_value",
            column,
        ],
        ascending=[
            False,
            True,
        ],
        kind="mergesort",
    )

    selected: pd.Series = values[column].head(limit)

    return [str(value) for value in selected.tolist()]


def _add_affinity_columns(
    features: pd.DataFrame,
    joined: pd.DataFrame,
    *,
    source_column: str,
    prefix: str,
    limit: int,
) -> pd.DataFrame:
    result = features.copy()

    top_values = _top_values(
        joined,
        source_column,
        limit,
    )

    household_sales = joined.groupby(
        "household_id",
        sort=True,
    )["sales_value"].sum()

    grouped = joined.groupby(
        [
            "household_id",
            source_column,
        ],
        as_index=False,
        sort=True,
    )["sales_value"].sum()

    for value in top_values:
        column_name = f"{prefix}__{_slug(value)}"

        subset = grouped[grouped[source_column].astype("string") == str(value)].set_index(
            "household_id"
        )["sales_value"]

        numerator = result["household_id"].map(subset).fillna(0.0)

        denominator = result["household_id"].map(household_sales).fillna(0.0)

        result[column_name] = np.where(
            denominator > 0,
            numerator / denominator,
            0.0,
        )

    return result


def build_feature_frames(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
) -> RetailFeatureFrames:
    tx = _standardize_transactions(transactions)

    product = _standardize_products(products)

    if tx.empty:
        raise ValueError("Transactions are empty after normalization.")

    observation_start = tx["transaction_date"].min()

    observation_end = tx["transaction_date"].max()

    if pd.isna(observation_start) or pd.isna(observation_end):
        raise ValueError("Observation window cannot be determined.")

    if observation_end < observation_start:
        raise ValueError("Observation end precedes observation start.")

    observation_days = max(
        _elapsed_days(
            observation_end,
            observation_start,
        )
        + 1,
        1,
    )

    baskets = _basket_table(tx)

    household = baskets.groupby(
        "household_id",
        as_index=False,
        sort=True,
    ).agg(
        last_purchase_date=(
            "transaction_date",
            "max",
        ),
        frequency=(
            "basket_id",
            "nunique",
        ),
        monetary_value=(
            "sales_value",
            "sum",
        ),
        total_items=(
            "quantity",
            "sum",
        ),
        retail_discount_baskets=(
            "has_retail_discount",
            "sum",
        ),
        coupon_redemption_baskets=(
            "has_coupon",
            "sum",
        ),
        promotion_baskets=(
            "has_promotion",
            "sum",
        ),
        total_discount_amount=(
            "total_discount_amount",
            "sum",
        ),
    )

    household["recency_days"] = _elapsed_day_series(
        observation_end,
        household["last_purchase_date"],
    )

    household["basket_count"] = household["frequency"]

    household["total_sales_value"] = household["monetary_value"]

    household["average_order_value"] = np.where(
        household["frequency"] > 0,
        household["monetary_value"] / household["frequency"],
        0.0,
    )

    basket_structure = tx.groupby(
        [
            "household_id",
            "basket_id",
        ],
        as_index=False,
        sort=True,
    ).agg(
        raw_quantity=(
            "quantity",
            "sum",
        ),
        line_items=(
            "product_id",
            "size",
        ),
        distinct_products=(
            "product_id",
            "nunique",
        ),
    )

    household_basket_structure = (
        basket_structure.groupby(
            "household_id",
            as_index=False,
            sort=True,
        )
        .agg(
            average_line_items_per_basket=(
                "line_items",
                "mean",
            ),
            average_distinct_products_per_basket=(
                "distinct_products",
                "mean",
            ),
            raw_quantity_mean_per_basket=(
                "raw_quantity",
                "mean",
            ),
        )
        .set_index("household_id")
    )

    household["average_line_items_per_basket"] = (
        household["household_id"]
        .map(household_basket_structure["average_line_items_per_basket"])
        .fillna(0.0)
    )

    household["items_per_basket"] = household["average_line_items_per_basket"]

    household["average_distinct_products_per_basket"] = (
        household["household_id"]
        .map(household_basket_structure["average_distinct_products_per_basket"])
        .fillna(0.0)
    )

    household["raw_quantity_mean_per_basket"] = (
        household["household_id"]
        .map(household_basket_structure["raw_quantity_mean_per_basket"])
        .fillna(0.0)
    )

    household["purchase_frequency_per_30d"] = household["frequency"] / observation_days * 30.0

    median_days = _median_days_between_orders(baskets)

    household["median_days_between_orders"] = household["household_id"].map(median_days)

    household["repeat_purchase_indicator"] = household["frequency"] >= 2

    household["retail_discount_dependency"] = np.where(
        household["frequency"] > 0,
        household["retail_discount_baskets"] / household["frequency"],
        0.0,
    )

    household["coupon_usage_rate"] = np.where(
        household["frequency"] > 0,
        household["coupon_redemption_baskets"] / household["frequency"],
        0.0,
    )

    household["coupon_redemption_rate"] = household["coupon_usage_rate"]

    household["promotion_dependency"] = np.where(
        household["frequency"] > 0,
        household["promotion_baskets"] / household["frequency"],
        0.0,
    )

    household["full_price_purchase_share"] = 1.0 - household["promotion_dependency"]

    household["discount_amount_per_sales_dollar"] = np.where(
        household["monetary_value"] > 0,
        household["total_discount_amount"] / household["monetary_value"],
        0.0,
    )

    joined = tx.merge(
        product,
        on="product_id",
        how="left",
        validate="many_to_one",
    )

    for column in (
        "department",
        "commodity",
        "brand",
    ):
        joined[column] = joined[column].astype("string").fillna("UNKNOWN")

    category_breadth = joined.groupby(
        "household_id",
        sort=True,
    )["commodity"].nunique()

    household["category_breadth"] = (
        household["household_id"].map(category_breadth).fillna(0).astype("int64")
    )

    household["dominant_department"] = (
        household["household_id"]
        .map(
            _dominant_value(
                joined,
                "department",
            )
        )
        .fillna("UNKNOWN")
    )

    household["dominant_category"] = (
        household["household_id"]
        .map(
            _dominant_value(
                joined,
                "commodity",
            )
        )
        .fillna("UNKNOWN")
    )

    household["dominant_brand"] = (
        household["household_id"]
        .map(
            _dominant_value(
                joined,
                "brand",
            )
        )
        .fillna("UNKNOWN")
    )

    household["category_concentration"] = (
        household["household_id"].map(_category_concentration(joined)).fillna(0.0)
    )

    household = _add_affinity_columns(
        household,
        joined,
        source_column="department",
        prefix="department_affinity_share",
        limit=TOP_DEPARTMENT_AFFINITIES,
    )

    household = _add_affinity_columns(
        household,
        joined,
        source_column="commodity",
        prefix="category_affinity_share",
        limit=TOP_COMMODITY_AFFINITIES,
    )

    household = _add_affinity_columns(
        household,
        joined,
        source_column="brand",
        prefix="brand_affinity_share",
        limit=TOP_BRAND_AFFINITIES,
    )

    household["observation_start"] = observation_start

    household["observation_end"] = observation_end

    household["observation_days"] = observation_days

    household = household.sort_values(
        ["household_id"],
        kind="mergesort",
    ).reset_index(drop=True)

    category_performance = joined.groupby(
        [
            "department",
            "commodity",
        ],
        as_index=False,
        sort=True,
    ).agg(
        retail_sales=(
            "sales_value",
            "sum",
        ),
        units=(
            "quantity",
            "sum",
        ),
        households=(
            "household_id",
            "nunique",
        ),
        baskets=(
            "basket_id",
            "nunique",
        ),
        discounted_sales_lines=(
            "has_promotion",
            "sum",
        ),
    )

    total_sales = float(tx["sales_value"].sum())

    category_performance["sales_share"] = np.where(
        total_sales != 0,
        category_performance["retail_sales"] / total_sales,
        0.0,
    )

    category_performance["average_basket_value"] = np.where(
        category_performance["baskets"] > 0,
        category_performance["retail_sales"] / category_performance["baskets"],
        0.0,
    )

    category_performance = category_performance.sort_values(
        [
            "retail_sales",
            "department",
            "commodity",
        ],
        ascending=[
            False,
            True,
            True,
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    total_households = int(tx["household_id"].nunique())

    total_baskets = int(baskets.shape[0])

    total_items = float(tx["quantity"].sum())

    repeat_households = int((household["repeat_purchase_indicator"]).sum())

    retail_kpis = pd.DataFrame(
        [
            {
                "observation_start": observation_start,
                "observation_end": observation_end,
                "observation_days": observation_days,
                "customers": total_households,
                "orders_baskets": total_baskets,
                "retail_sales": total_sales,
                "average_order_value": (total_sales / total_baskets if total_baskets else 0.0),
                "items": total_items,
                "items_per_basket": (total_items / total_baskets if total_baskets else 0.0),
                "purchase_frequency_per_customer": (
                    total_baskets / total_households if total_households else 0.0
                ),
                "repeat_customer_rate": (
                    repeat_households / total_households if total_households else 0.0
                ),
                "discounted_basket_rate": float(baskets["has_promotion"].mean()),
                "coupon_basket_rate": float(baskets["has_coupon"].mean()),
            }
        ]
    )

    basket_raw_quantity = pd.to_numeric(
        baskets["quantity"],
        errors="raise",
    ).astype("float64")

    basket_line_items = (
        tx.groupby(
            [
                "household_id",
                "basket_id",
            ],
            sort=True,
        )
        .size()
        .astype("float64")
    )

    basket_distinct_products = (
        tx.groupby(
            [
                "household_id",
                "basket_id",
            ],
            sort=True,
        )["product_id"]
        .nunique()
        .astype("float64")
    )

    average_line_items_per_basket = float(basket_line_items.mean()) if total_baskets else 0.0

    median_line_items_per_basket = float(basket_line_items.median()) if total_baskets else 0.0

    average_distinct_products_per_basket = (
        float(basket_distinct_products.mean()) if total_baskets else 0.0
    )

    median_distinct_products_per_basket = (
        float(basket_distinct_products.median()) if total_baskets else 0.0
    )

    raw_quantity_mean_per_basket = float(basket_raw_quantity.mean()) if total_baskets else 0.0

    raw_quantity_median_per_basket = float(basket_raw_quantity.median()) if total_baskets else 0.0

    raw_quantity_p95_per_basket = (
        float(basket_raw_quantity.quantile(0.95)) if total_baskets else 0.0
    )

    raw_quantity_p99_per_basket = (
        float(basket_raw_quantity.quantile(0.99)) if total_baskets else 0.0
    )

    retail_kpis["items_per_basket"] = average_line_items_per_basket

    retail_kpis["average_line_items_per_basket"] = average_line_items_per_basket

    retail_kpis["median_line_items_per_basket"] = median_line_items_per_basket

    retail_kpis["average_distinct_products_per_basket"] = average_distinct_products_per_basket

    retail_kpis["median_distinct_products_per_basket"] = median_distinct_products_per_basket

    retail_kpis["raw_quantity_mean_per_basket"] = raw_quantity_mean_per_basket

    retail_kpis["raw_quantity_median_per_basket"] = raw_quantity_median_per_basket

    retail_kpis["raw_quantity_p95_per_basket"] = raw_quantity_p95_per_basket

    retail_kpis["raw_quantity_p99_per_basket"] = raw_quantity_p99_per_basket

    retail_kpis["raw_quantity_metric_outlier_sensitive"] = True

    time_axis_type = (
        "calendar_date"
        if isinstance(
            observation_start,
            pd.Timestamp,
        )
        else "source_relative_day"
    )

    metadata: dict[str, object] = {
        "observation_start": _time_value_for_metadata(observation_start),
        "observation_end": _time_value_for_metadata(observation_end),
        "observation_days": observation_days,
        "time_axis_type": time_axis_type,
        "time_axis_note": (
            "dunnhumby DAY is a source-relative sequential day index; "
            "no calendar date is fabricated"
            if time_axis_type == "source_relative_day"
            else "input contains real calendar dates"
        ),
        "analysis_unit": "household_id",
        "recency_definition": ("elapsed days from observation end to household last purchase"),
        "frequency_definition": ("distinct household-basket pairs within observation window"),
        "monetary_definition": (
            "sum of normalized transaction sales_value within observation window"
        ),
        "coupon_redemption_definition": (
            "basket contains non-zero normalized coupon or coupon-match discount"
        ),
        "promotion_dependency_definition": (
            "share of household baskets containing any retail/coupon/coupon-match discount"
        ),
    }

    metadata["items_per_basket_definition"] = (
        "mean normalized transaction product-line count per "
        "household-basket; executive-safe basket-intensity metric"
    )

    metadata["items_per_basket_alias"] = "average_line_items_per_basket"

    metadata["basket_intensity_primary_metric"] = "average_line_items_per_basket"

    metadata["basket_variety_secondary_metric"] = "average_distinct_products_per_basket"

    metadata["raw_quantity_policy"] = (
        "normalized QUANTITY is retained only as a diagnostic because "
        "its extreme concentration makes aggregate raw quantity "
        "unsuitable for executive physical-unit interpretation"
    )

    metadata["raw_quantity_classification"] = "NOT_EXECUTIVE_SAFE"

    metadata["raw_quantity_diagnostic_metrics"] = [
        "raw_quantity_mean_per_basket",
        "raw_quantity_median_per_basket",
        "raw_quantity_p95_per_basket",
        "raw_quantity_p99_per_basket",
    ]

    metadata["executive_safe_basket_metrics"] = [
        "average_line_items_per_basket",
        "median_line_items_per_basket",
        "average_distinct_products_per_basket",
        "median_distinct_products_per_basket",
    ]

    metadata["winsorization_policy"] = (
        "do not winsorize raw quantity merely to manufacture an executive items-per-basket KPI"
    )

    metadata["quantity_diagnostic_evidence"] = {
        "top_0_1pct_raw_quantity_share": 0.20398154141389507,
        "top_0_5pct_raw_quantity_share": 0.725773633192551,
        "top_1pct_raw_quantity_share": 0.9872814964839143,
        "top_5pct_raw_quantity_share": 0.9889433909784253,
    }

    result = RetailFeatureFrames(
        customer_features=household,
        retail_kpis=retail_kpis,
        category_performance=category_performance,
        metadata=metadata,
    )

    validate_feature_frames(
        result,
        tx,
    )

    return result


def validate_feature_frames(
    frames: RetailFeatureFrames,
    standardized_transactions: pd.DataFrame,
) -> None:
    customer = frames.customer_features
    retail_kpis = frames.retail_kpis
    category = frames.category_performance

    if customer.empty:
        raise ValueError("customer_features is empty.")

    if retail_kpis.shape[0] != 1:
        raise ValueError("retail_kpis must contain exactly one row.")

    if category.empty:
        raise ValueError("category_performance is empty.")

    if customer["household_id"].duplicated().any():
        raise ValueError("customer_features must contain one row per household.")

    nonnegative_columns = (
        "recency_days",
        "frequency",
        "monetary_value",
        "basket_count",
        "total_sales_value",
        "average_order_value",
        "items_per_basket",
        "purchase_frequency_per_30d",
        "category_breadth",
        "category_concentration",
        "retail_discount_dependency",
        "coupon_usage_rate",
        "coupon_redemption_rate",
        "promotion_dependency",
        "full_price_purchase_share",
    )

    for column in nonnegative_columns:
        values = pd.to_numeric(
            customer[column],
            errors="coerce",
        )

        if values.isna().any():
            raise ValueError(f"{column} contains invalid numeric values.")

        if (values < -1e-12).any():
            raise ValueError(f"{column} contains negative values.")

    share_columns = [
        column
        for column in customer.columns
        if (
            column.endswith("_share")
            or column
            in {
                "retail_discount_dependency",
                "coupon_usage_rate",
                "coupon_redemption_rate",
                "promotion_dependency",
                "full_price_purchase_share",
                "category_concentration",
            }
        )
    ]

    for column in share_columns:
        values = pd.to_numeric(
            customer[column],
            errors="coerce",
        )

        if (values < -1e-12).any() or (values > 1.0 + 1e-12).any():
            raise ValueError(f"{column} is outside [0, 1].")

    transaction_sales = float(standardized_transactions["sales_value"].sum())

    customer_sales = float(customer["monetary_value"].sum())

    kpi_sales = float(retail_kpis.iloc[0]["retail_sales"])

    category_sales = float(category["retail_sales"].sum())

    tolerance = max(
        1e-8,
        abs(transaction_sales) * 1e-10,
    )

    for label, value in (
        (
            "customer_features",
            customer_sales,
        ),
        (
            "retail_kpis",
            kpi_sales,
        ),
        (
            "category_performance",
            category_sales,
        ),
    ):
        if not math.isclose(
            transaction_sales,
            value,
            abs_tol=tolerance,
            rel_tol=1e-10,
        ):
            raise ValueError(
                "Retail sales reconciliation failed for "
                f"{label}: source={transaction_sales}; "
                f"derived={value}"
            )

    expected_baskets = int(
        standardized_transactions[
            [
                "household_id",
                "basket_id",
            ]
        ]
        .drop_duplicates()
        .shape[0]
    )

    customer_baskets = int(customer["frequency"].sum())

    kpi_baskets = int(retail_kpis.iloc[0]["orders_baskets"])

    if expected_baskets != customer_baskets:
        raise ValueError("Basket reconciliation failed between source and customer_features.")

    if expected_baskets != kpi_baskets:
        raise ValueError("Basket reconciliation failed between source and retail_kpis.")

    expected_customers = int(standardized_transactions["household_id"].nunique())

    if len(customer) != expected_customers:
        raise ValueError("Customer reconciliation failed.")

    if int(retail_kpis.iloc[0]["customers"]) != expected_customers:
        raise ValueError("retail_kpis customer count does not reconcile.")

    category_share_sum = float(category["sales_share"].sum())

    if transaction_sales > 0 and not math.isclose(
        category_share_sum,
        1.0,
        abs_tol=1e-8,
        rel_tol=1e-8,
    ):
        raise ValueError("Category sales shares do not sum to one.")


def build_from_cache(
    repository_root: Path,
    output_dir: Path,
) -> RetailFeatureFrames:
    repository_root = repository_root.resolve()
    output_dir = output_dir.resolve()

    tables = _read_normalized_tables(repository_root)

    transactions = _select_transactions(tables)

    products = _select_products(tables)

    first = build_feature_frames(
        transactions,
        products,
    )

    second = build_feature_frames(
        transactions,
        products,
    )

    for label, left, right in (
        (
            "customer_features",
            first.customer_features,
            second.customer_features,
        ),
        (
            "retail_kpis",
            first.retail_kpis,
            second.retail_kpis,
        ),
        (
            "category_performance",
            first.category_performance,
            second.category_performance,
        ),
    ):
        left_hash = stable_frame_hash(left)

        right_hash = stable_frame_hash(right)

        if left_hash != right_hash:
            raise RuntimeError(f"{label} is not deterministic: {left_hash} != {right_hash}")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    customer_csv = output_dir / "customer_features.csv"

    customer_parquet = output_dir / "customer_features.parquet"

    retail_kpis_csv = output_dir / "retail_kpis.csv"

    retail_kpis_parquet = output_dir / "retail_kpis.parquet"

    category_csv = output_dir / "category_performance.csv"

    category_parquet = output_dir / "category_performance.parquet"

    first.customer_features.to_csv(
        customer_csv,
        index=False,
        lineterminator="\n",
    )

    first.customer_features.to_parquet(
        customer_parquet,
        index=False,
    )

    first.retail_kpis.to_csv(
        retail_kpis_csv,
        index=False,
        lineterminator="\n",
    )

    first.retail_kpis.to_parquet(
        retail_kpis_parquet,
        index=False,
    )

    first.category_performance.to_csv(
        category_csv,
        index=False,
        lineterminator="\n",
    )

    first.category_performance.to_parquet(
        category_parquet,
        index=False,
    )

    manifest = {
        "schema_version": "1.0.0",
        "step": "3",
        "analysis_unit": "household_id",
        "metadata": first.metadata,
        "outputs": {
            "customer_features": {
                "rows": len(first.customer_features),
                "stable_frame_hash": stable_frame_hash(first.customer_features),
            },
            "retail_kpis": {
                "rows": len(first.retail_kpis),
                "stable_frame_hash": stable_frame_hash(first.retail_kpis),
            },
            "category_performance": {
                "rows": len(first.category_performance),
                "stable_frame_hash": stable_frame_hash(first.category_performance),
            },
        },
    }

    (output_dir / "retail_feature_manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return first


def validate_output_directory(
    output_dir: Path,
) -> None:
    required = (
        "customer_features.csv",
        "customer_features.parquet",
        "retail_kpis.csv",
        "retail_kpis.parquet",
        "category_performance.csv",
        "category_performance.parquet",
        "retail_feature_manifest.json",
    )

    for filename in required:
        path = output_dir / filename

        if not path.is_file():
            raise FileNotFoundError(f"Required Step 3 output missing: {path}")

    customer_csv = pd.read_csv(output_dir / "customer_features.csv")

    customer_parquet = pd.read_parquet(output_dir / "customer_features.parquet")

    if len(customer_csv) != len(customer_parquet):
        raise ValueError("customer_features CSV/Parquet row counts differ.")

    if customer_parquet["household_id"].duplicated().any():
        raise ValueError("customer_features has duplicate household IDs.")

    manifest = json.loads((output_dir / "retail_feature_manifest.json").read_text(encoding="utf-8"))

    if manifest.get("analysis_unit") != "household_id":
        raise ValueError("Step 3 manifest analysis unit is not household_id.")
