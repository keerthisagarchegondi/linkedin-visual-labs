from __future__ import annotations

import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.retail_features import (
    build_feature_frames,
)


def _transactions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "household_id": [
                "h1",
                "h1",
                "h1",
                "h2",
            ],
            "basket_id": [
                "b1",
                "b1",
                "b2",
                "b3",
            ],
            "product_id": [
                "p1",
                "p2",
                "p1",
                "p2",
            ],
            "transaction_timestamp": pd.to_datetime(
                [
                    "2024-01-01",
                    "2024-01-01",
                    "2024-01-11",
                    "2024-01-21",
                ]
            ),
            "sales_value": [
                10.0,
                5.0,
                20.0,
                30.0,
            ],
            "quantity": [
                1,
                2,
                1,
                3,
            ],
            "retail_discount": [
                0.0,
                -1.0,
                0.0,
                0.0,
            ],
            "coupon_discount": [
                0.0,
                0.0,
                -2.0,
                0.0,
            ],
            "coupon_match_discount": [
                0.0,
                0.0,
                0.0,
                0.0,
            ],
        }
    )


def _products() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "product_id": [
                "p1",
                "p2",
            ],
            "department": [
                "Grocery",
                "Fresh",
            ],
            "commodity": [
                "Snacks",
                "Produce",
            ],
            "brand": [
                "A",
                "B",
            ],
        }
    )


def test_true_rfm_semantics() -> None:
    frames = build_feature_frames(
        _transactions(),
        _products(),
    )

    customer = frames.customer_features.set_index("household_id")

    assert (
        customer.loc[
            "h1",
            "frequency",
        ]
        == 2
    )

    assert customer.loc[
        "h1",
        "monetary_value",
    ] == pytest.approx(35.0)

    assert (
        customer.loc[
            "h1",
            "recency_days",
        ]
        == 10
    )

    assert (
        customer.loc[
            "h2",
            "recency_days",
        ]
        == 0
    )


def test_order_and_value_metrics() -> None:
    frames = build_feature_frames(
        _transactions(),
        _products(),
    )

    customer = frames.customer_features.set_index("household_id")

    assert customer.loc[
        "h1",
        "average_order_value",
    ] == pytest.approx(17.5)

    assert customer.loc[
        "h1",
        "items_per_basket",
    ] == pytest.approx(2.0)

    assert bool(
        customer.loc[
            "h1",
            "repeat_purchase_indicator",
        ]
    )

    assert not bool(
        customer.loc[
            "h2",
            "repeat_purchase_indicator",
        ]
    )


def test_category_and_promotion_features() -> None:
    frames = build_feature_frames(
        _transactions(),
        _products(),
    )

    customer = frames.customer_features.set_index("household_id")

    assert (
        customer.loc[
            "h1",
            "category_breadth",
        ]
        == 2
    )

    assert (
        customer.loc[
            "h1",
            "dominant_category",
        ]
        == "Snacks"
    )

    assert customer.loc[
        "h1",
        "coupon_redemption_rate",
    ] == pytest.approx(0.5)

    assert customer.loc[
        "h1",
        "promotion_dependency",
    ] == pytest.approx(1.0)

    assert customer.loc[
        "h2",
        "full_price_purchase_share",
    ] == pytest.approx(1.0)


def test_reconciliation() -> None:
    frames = build_feature_frames(
        _transactions(),
        _products(),
    )

    assert (
        frames.retail_kpis.loc[
            0,
            "customers",
        ]
        == 2
    )

    assert (
        frames.retail_kpis.loc[
            0,
            "orders_baskets",
        ]
        == 3
    )

    assert frames.retail_kpis.loc[
        0,
        "retail_sales",
    ] == pytest.approx(65.0)

    assert frames.customer_features["monetary_value"].sum() == pytest.approx(65.0)

    assert frames.category_performance["retail_sales"].sum() == pytest.approx(65.0)


def test_generation_is_deterministic() -> None:
    first = build_feature_frames(
        _transactions(),
        _products(),
    )

    second = build_feature_frames(
        _transactions(),
        _products(),
    )

    pd.testing.assert_frame_equal(
        first.customer_features,
        second.customer_features,
    )

    pd.testing.assert_frame_equal(
        first.retail_kpis,
        second.retail_kpis,
    )

    pd.testing.assert_frame_equal(
        first.category_performance,
        second.category_performance,
    )


def test_real_dunnhumby_source_relative_day_schema() -> None:
    transactions = pd.DataFrame(
        {
            "retail_household_id": [
                "h1",
                "h1",
                "h1",
                "h2",
            ],
            "basket_id": [
                "b1",
                "b1",
                "b2",
                "b3",
            ],
            "day": [
                1,
                1,
                11,
                21,
            ],
            "product_id": [
                "p1",
                "p2",
                "p1",
                "p2",
            ],
            "quantity": [
                1,
                2,
                1,
                3,
            ],
            "sales_value": [
                10.0,
                5.0,
                20.0,
                30.0,
            ],
            "retail_disc": [
                0.0,
                -1.0,
                0.0,
                0.0,
            ],
            "coupon_disc": [
                0.0,
                0.0,
                -2.0,
                0.0,
            ],
            "coupon_match_disc": [
                0.0,
                0.0,
                0.0,
                0.0,
            ],
        }
    )

    frames = build_feature_frames(
        transactions,
        _products(),
    )

    customer = frames.customer_features.set_index("household_id")

    assert (
        customer.loc[
            "h1",
            "frequency",
        ]
        == 2
    )

    assert customer.loc[
        "h1",
        "monetary_value",
    ] == pytest.approx(35.0)

    assert (
        customer.loc[
            "h1",
            "recency_days",
        ]
        == 10
    )

    assert (
        customer.loc[
            "h2",
            "recency_days",
        ]
        == 0
    )

    assert customer.loc[
        "h1",
        "median_days_between_orders",
    ] == pytest.approx(10.0)

    assert frames.metadata["time_axis_type"] == "source_relative_day"

    assert frames.metadata["observation_start"] == "1"

    assert frames.metadata["observation_end"] == "21"

    assert frames.metadata["observation_days"] == 21


def test_robust_basket_quantity_kpis() -> None:
    frames = build_feature_frames(
        _transactions(),
        _products(),
    )

    kpi = frames.retail_kpis.iloc[0]

    assert kpi["average_units_per_basket"] == pytest.approx(7.0 / 3.0)

    assert kpi["average_line_items_per_basket"] == pytest.approx(4.0 / 3.0)

    assert kpi["median_units_per_basket"] == pytest.approx(3.0)

    assert kpi["p95_units_per_basket"] >= kpi["median_units_per_basket"]

    assert kpi["p99_units_per_basket"] >= kpi["p95_units_per_basket"]

    assert bool(kpi["raw_quantity_metric_outlier_sensitive"])

    assert frames.metadata["dashboard_items_per_basket_recommendation"]
