"""dunnhumby normalization tests."""

from __future__ import annotations

import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters import (
    dunnhumby,
)


def transaction_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "household_key": [2, 1],
            "BASKET_ID": [20, 10],
            "DAY": [2, 1],
            "PRODUCT_ID": [200, 100],
            "QUANTITY": [1, 2],
            "SALES_VALUE": [4.5, 8.0],
            "STORE_ID": [5, 5],
            "RETAIL_DISC": [-0.5, 0.0],
            "WEEK_NO": [1, 1],
            "COUPON_DISC": [0.0, 0.0],
        }
    )


def test_dunnhumby_transactions_normalize() -> None:
    result = dunnhumby.normalize_transactions(transaction_fixture())

    assert "retail_household_id" in result.columns
    assert "household_key" not in result.columns
    assert "customer_id" not in result.columns

    assert list(result["retail_household_id"]) == [
        1,
        2,
    ]


def test_dunnhumby_rejects_negative_sales() -> None:
    frame = transaction_fixture()

    frame.loc[
        0,
        "SALES_VALUE",
    ] = -2.0

    with pytest.raises(
        ValueError,
        match="sales_value must be nonnegative",
    ):
        dunnhumby.normalize_transactions(frame)


def test_product_taxonomy_requires_columns() -> None:
    frame = pd.DataFrame(
        {
            "PRODUCT_ID": [1],
            "DEPARTMENT": ["GROCERY"],
            "BRAND": ["National"],
            "COMMODITY_DESC": ["CEREAL"],
            "SUB_COMMODITY_DESC": ["READY TO EAT"],
        }
    )

    normalized = dunnhumby.normalize_products(frame)

    assert list(normalized.columns) == [
        "product_id",
        "department",
        "brand",
        "commodity_desc",
        "sub_commodity_desc",
    ]
