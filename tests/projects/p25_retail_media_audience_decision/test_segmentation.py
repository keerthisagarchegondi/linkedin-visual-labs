from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.segmentation import (
    CANDIDATE_K,
    build_segmentation_frames,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)


def _synthetic_customer_features() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    categories = (
        "Snacks",
        "Produce",
        "Beverages",
        "Frozen",
    )

    for group in range(4):
        for index in range(60):
            household_id = f"h{group:02d}_{index:03d}"

            recency = 8 + group * 28 + index % 7

            frequency = 80 - group * 15 + index % 5

            monetary = 1800.0 - group * 330.0 + index * 3.0

            aov = 24.0 + group * 4.0 + index % 3

            promotion = min(
                0.95,
                0.10 + group * 0.20 + (index % 5) * 0.02,
            )

            category = categories[group]

            affinity = {
                f"commodity_affinity_{value.lower()}": (
                    0.72 if value == category else 0.09333333333333334
                )
                for value in categories
            }

            rows.append(
                {
                    "household_id": household_id,
                    "recency_days": float(recency),
                    "frequency": float(frequency),
                    "monetary_value": monetary,
                    "average_order_value": aov,
                    "purchase_frequency_per_30d": (frequency / 24.0),
                    "median_days_between_orders": (6.0 + group * 2.0),
                    "repeat_purchase_indicator": 1,
                    "items_per_basket": (7.0 + group),
                    "average_line_items_per_basket": (7.0 + group),
                    "average_distinct_products_per_basket": (7.0 + group),
                    "category_breadth": (8.0 + group * 2.0),
                    "category_concentration": (0.45 + group * 0.07),
                    "retail_discount_dependency": promotion,
                    "coupon_usage_rate": promotion * 0.5,
                    "coupon_redemption_rate": promotion * 0.5,
                    "promotion_dependency": promotion,
                    "full_price_purchase_share": (1.0 - promotion),
                    "discount_amount_per_sales_dollar": (promotion * 0.08),
                    "dominant_department": "GROCERY",
                    "dominant_category": category,
                    "dominant_brand": f"Brand-{group}",
                    "raw_quantity_mean_per_basket": (500.0 + group * 10000.0),
                    **affinity,
                }
            )

    frame = pd.DataFrame(rows)

    return frame.sort_values(
        "household_id",
        kind="mergesort",
    ).reset_index(drop=True)


def test_kmeans_segmentation_is_deterministic() -> None:
    customer = _synthetic_customer_features()

    first = build_segmentation_frames(customer)

    second = build_segmentation_frames(customer)

    assert stable_frame_hash(first.audience_membership) == stable_frame_hash(
        second.audience_membership
    )

    assert stable_frame_hash(first.audience_taxonomy) == stable_frame_hash(second.audience_taxonomy)

    assert stable_frame_hash(first.k_evaluation) == stable_frame_hash(second.k_evaluation)

    assert tuple(first.k_evaluation["k"].astype(int)) == CANDIDATE_K

    assert first.k_evaluation["selected"].sum() == 1


def test_exactly_one_primary_segment_per_customer() -> None:
    customer = _synthetic_customer_features()

    frames = build_segmentation_frames(customer)

    primary = frames.audience_membership.loc[frames.audience_membership["is_primary"]]

    counts = primary.groupby("household_id")["audience_id"].size()

    assert len(counts) == len(customer)

    assert (counts == 1).all()

    assert primary["audience_id"].astype(str).str.match(r"^P\d{2}$").all()


def test_secondary_activation_audiences_can_overlap() -> None:
    customer = _synthetic_customer_features()

    frames = build_segmentation_frames(customer)

    secondary = frames.audience_membership.loc[
        frames.audience_membership["audience_type"] == "SECONDARY_ACTIVATION"
    ]

    counts = secondary.groupby("household_id")["audience_id"].nunique()

    assert int(counts.max()) >= 2

    secondary_taxonomy = frames.audience_taxonomy.loc[
        frames.audience_taxonomy["audience_type"] == "SECONDARY_ACTIVATION"
    ]

    assert not secondary_taxonomy["exclusive"].astype(bool).any()


def test_governed_minimum_audience_size() -> None:
    frames = build_segmentation_frames(_synthetic_customer_features())

    assert (
        frames.audience_taxonomy["member_count"] >= frames.audience_taxonomy["minimum_size"]
    ).all()


def test_governed_audience_names_and_privacy() -> None:
    frames = build_segmentation_frames(_synthetic_customer_features())

    taxonomy = frames.audience_taxonomy

    assert not taxonomy["audience_name"].duplicated().any()

    assert taxonomy["audience_name"].astype(str).str.strip().ne("").all()

    assert taxonomy["definition"].astype(str).str.strip().ne("").all()

    assert taxonomy["taxonomy_version"].eq("1.0.0").all()

    assert (
        taxonomy["privacy_classification"]
        .astype(str)
        .str.contains(
            "BEHAVIORAL",
            regex=False,
        )
        .all()
    )


def test_pca_is_two_component_visualization_only() -> None:
    customer = _synthetic_customer_features()

    frames = build_segmentation_frames(customer)

    assert len(frames.pca_projection) == len(customer)

    assert {
        "pc1",
        "pc2",
    }.issubset(frames.pca_projection.columns)

    assert np.isfinite(
        frames.pca_projection[
            [
                "pc1",
                "pc2",
            ]
        ].to_numpy(dtype=float)
    ).all()

    assert frames.metadata["pca_rule"] == (
        "PCA is visualization-only and never used to fit or select KMeans clusters"
    )


def test_raw_quantity_is_excluded_from_ml_features() -> None:
    frames = build_segmentation_frames(_synthetic_customer_features())

    approved = set(cast(list[str], frames.metadata["approved_feature_set"]))

    assert "raw_quantity_mean_per_basket" not in approved

    assert "last_purchase_date" not in approved

    assert {
        "recency_days",
        "frequency",
        "monetary_value",
    }.issubset(approved)


def test_overlap_matrix_is_analytically_valid() -> None:
    frames = build_segmentation_frames(_synthetic_customer_features())

    overlap = frames.audience_overlap

    assert not overlap.empty

    assert (overlap["intersection_count"] >= 0).all()

    for column in (
        "overlap_pct_of_a",
        "overlap_pct_of_b",
        "jaccard_index",
    ):
        assert (overlap[column] >= 0).all()

        assert (overlap[column] <= 1).all()

    diagonal = overlap.loc[overlap["audience_a"] == overlap["audience_b"]]

    assert np.allclose(
        diagonal["jaccard_index"].to_numpy(dtype=float),
        1.0,
    )


def test_structural_missing_interorder_interval_is_median_imputed() -> None:
    customer = _synthetic_customer_features()

    customer.loc[
        customer.index[:3],
        "median_days_between_orders",
    ] = np.nan

    frames = build_segmentation_frames(customer)

    assert len(frames.pca_projection) == len(customer)

    assert frames.metadata["missing_value_strategy"] == (
        "deterministic median imputation in the numeric "
        "model-preprocessing layer; source feature values remain "
        "unchanged and all-null model features fail closed"
    )

    missing = cast(
        dict[str, int],
        frames.metadata["missing_value_counts"],
    )

    assert missing["median_days_between_orders"] == 3

    assert customer["median_days_between_orders"].isna().sum() == 3
