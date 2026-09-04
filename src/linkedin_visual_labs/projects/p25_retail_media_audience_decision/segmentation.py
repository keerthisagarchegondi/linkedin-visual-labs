"""Governed ML audience segmentation for Project 4."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances, silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)

RANDOM_STATE: Final[int] = 42

CANDIDATE_K: Final[tuple[int, ...]] = (
    3,
    4,
    5,
    6,
)

AUDIENCE_TAXONOMY_VERSION: Final[str] = "1.0.0"

MIN_PRIMARY_AUDIENCE_FRACTION: Final[float] = 0.02
MIN_SECONDARY_AUDIENCE_FRACTION: Final[float] = 0.02
MIN_AUDIENCE_ABSOLUTE: Final[int] = 50

CATEGORY_AFFINITY_PREFIXES: Final[tuple[str, ...]] = (
    "department_affinity_",
    "commodity_affinity_",
    "brand_affinity_",
)

BASE_APPROVED_FEATURES: Final[tuple[str, ...]] = (
    "recency_days",
    "frequency",
    "monetary_value",
    "average_order_value",
    "purchase_frequency_per_30d",
    "median_days_between_orders",
    "repeat_purchase_indicator",
    "items_per_basket",
    "average_line_items_per_basket",
    "average_distinct_products_per_basket",
    "category_breadth",
    "category_concentration",
    "retail_discount_dependency",
    "coupon_usage_rate",
    "coupon_redemption_rate",
    "promotion_dependency",
    "full_price_purchase_share",
    "discount_amount_per_sales_dollar",
)

LOG1P_FEATURES: Final[tuple[str, ...]] = (
    "frequency",
    "monetary_value",
    "average_order_value",
    "purchase_frequency_per_30d",
    "median_days_between_orders",
    "category_breadth",
)

BANNED_MODEL_COLUMNS: Final[tuple[str, ...]] = (
    "household_id",
    "last_purchase_date",
    "dominant_department",
    "dominant_category",
    "dominant_brand",
    "raw_quantity_mean_per_basket",
    "raw_quantity_median_per_basket",
    "raw_quantity_p95_per_basket",
    "raw_quantity_p99_per_basket",
)


@dataclass(frozen=True)
class SegmentationFrames:
    """All governed outputs for Step 4."""

    audience_profiles: pd.DataFrame
    audience_taxonomy: pd.DataFrame
    audience_membership: pd.DataFrame
    audience_overlap: pd.DataFrame
    pca_projection: pd.DataFrame
    k_evaluation: pd.DataFrame
    metadata: dict[str, object]


@dataclass(frozen=True)
class PreparedFeatures:
    """Preprocessed KMeans feature matrix and feature metadata."""

    matrix: np.ndarray
    feature_names: tuple[str, ...]
    approved_features: tuple[str, ...]
    log1p_features: tuple[str, ...]
    scaled_only_features: tuple[str, ...]


def _slug(
    value: object,
) -> str:
    text = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        str(value).strip(),
    ).strip("_")

    return text.upper() if text else "UNKNOWN"


def _numeric_series(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    return pd.to_numeric(
        frame[column],
        errors="coerce",
    )


def _approved_features(
    frame: pd.DataFrame,
) -> tuple[str, ...]:
    approved: list[str] = []

    for column in BASE_APPROVED_FEATURES:
        if column not in frame.columns:
            continue

        values = _numeric_series(
            frame,
            column,
        )

        if values.notna().any():
            approved.append(column)

    affinity_columns = sorted(
        column
        for column in frame.columns
        if any(column.startswith(prefix) for prefix in CATEGORY_AFFINITY_PREFIXES)
    )

    for column in affinity_columns:
        values = _numeric_series(
            frame,
            column,
        )

        if values.notna().any():
            approved.append(column)

    if not approved:
        raise ValueError("No approved segmentation features are available.")

    banned = sorted(set(approved) & set(BANNED_MODEL_COLUMNS))

    if banned:
        raise ValueError(f"Leakage / governed model columns selected: {banned}")

    required_rfm = {
        "recency_days",
        "frequency",
        "monetary_value",
    }

    missing_rfm = sorted(required_rfm - set(approved))

    if missing_rfm:
        raise ValueError(f"True RFM missing from segmentation feature set: {missing_rfm}")

    return tuple(approved)


def _log1p_array(
    values: np.ndarray,
) -> np.ndarray:
    array = np.asarray(
        values,
        dtype=float,
    )

    if np.any(array < 0):
        raise ValueError("log1p segmentation features must be nonnegative.")

    return np.log1p(array)


def _prepare_features(
    frame: pd.DataFrame,
) -> PreparedFeatures:
    approved = _approved_features(frame)

    numeric = frame.loc[
        :,
        list(approved),
    ].copy()

    for column in approved:
        numeric[column] = pd.to_numeric(
            numeric[column],
            errors="coerce",
        )

    all_null_features = [column for column in approved if numeric[column].isna().all()]

    if all_null_features:
        raise ValueError(f"Segmentation features are entirely missing: {all_null_features}")

    for column in approved:
        if not numeric[column].isna().any():
            continue

        median_value = numeric[column].median()

        if pd.isna(median_value):
            raise ValueError(
                f"Could not compute deterministic median for segmentation feature: {column}"
            )

        numeric[column] = numeric[column].fillna(median_value)

    if numeric.isna().any().any():
        remaining = {
            column: int(numeric[column].isna().sum())
            for column in approved
            if numeric[column].isna().any()
        }

        raise ValueError(f"Segmentation preprocessing left missing values: {remaining}")

    log_features = tuple(column for column in LOG1P_FEATURES if column in approved)

    scaled_features = tuple(column for column in approved if column not in log_features)

    transformers: list[
        tuple[
            str,
            Pipeline | StandardScaler,
            list[str],
        ]
    ] = []

    if log_features:
        log_pipeline = Pipeline(
            steps=[
                (
                    "log1p",
                    FunctionTransformer(
                        _log1p_array,
                        validate=False,
                    ),
                ),
                (
                    "scale",
                    StandardScaler(),
                ),
            ]
        )

        transformers.append(
            (
                "log_numeric",
                log_pipeline,
                list(log_features),
            )
        )

    if scaled_features:
        transformers.append(
            (
                "scaled_numeric",
                StandardScaler(),
                list(scaled_features),
            )
        )

    preprocessing = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )

    matrix_raw = preprocessing.fit_transform(numeric)

    matrix = np.asarray(
        matrix_raw,
        dtype=float,
    )

    if matrix.ndim != 2:
        raise ValueError("Segmentation preprocessing did not produce a 2D matrix.")

    if matrix.shape[0] != len(frame):
        raise ValueError("Segmentation feature row count changed during preprocessing.")

    if not np.isfinite(matrix).all():
        raise ValueError("Segmentation feature matrix contains non-finite values.")

    feature_names = (
        *log_features,
        *scaled_features,
    )

    if len(feature_names) != matrix.shape[1]:
        raise ValueError("Preprocessed feature-name count does not match matrix width.")

    return PreparedFeatures(
        matrix=matrix,
        feature_names=tuple(feature_names),
        approved_features=approved,
        log1p_features=log_features,
        scaled_only_features=scaled_features,
    )


def _minimum_audience_size(
    population: int,
    fraction: float,
) -> int:
    return max(
        MIN_AUDIENCE_ABSOLUTE,
        math.ceil(population * fraction),
    )


def _actionability_score(
    centers: np.ndarray,
) -> float:
    if centers.size == 0:
        return 0.0

    strong_signals = (np.abs(centers) >= 0.75).sum(axis=1)

    actionable = (strong_signals >= 2).mean()

    return float(actionable)


def _profile_distinctiveness(
    centers: np.ndarray,
) -> tuple[float, float]:
    if centers.shape[0] < 2:
        return (
            0.0,
            0.0,
        )

    distances = pairwise_distances(
        centers,
        metric="euclidean",
    )

    upper = distances[
        np.triu_indices(
            distances.shape[0],
            k=1,
        )
    ]

    return (
        float(upper.mean()),
        float(upper.min()),
    )


def _evaluate_candidates(
    prepared: PreparedFeatures,
    population: int,
) -> pd.DataFrame:
    minimum_size = _minimum_audience_size(
        population,
        MIN_PRIMARY_AUDIENCE_FRACTION,
    )

    records: list[dict[str, object]] = []

    for k in CANDIDATE_K:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20,
            algorithm="lloyd",
        )

        labels = model.fit_predict(prepared.matrix)

        sizes = np.bincount(
            labels,
            minlength=k,
        )

        min_size = int(sizes.min())

        max_size = int(sizes.max())

        silhouette = float(
            silhouette_score(
                prepared.matrix,
                labels,
                metric="euclidean",
            )
        )

        mean_distance, min_distance = _profile_distinctiveness(model.cluster_centers_)

        actionability = _actionability_score(model.cluster_centers_)

        records.append(
            {
                "k": k,
                "silhouette_score": silhouette,
                "minimum_segment_size": min_size,
                "maximum_segment_size": max_size,
                "minimum_segment_share": min_size / population,
                "maximum_segment_share": max_size / population,
                "profile_distinctiveness_mean": mean_distance,
                "profile_distinctiveness_min": min_distance,
                "business_actionability_score": actionability,
                "minimum_size_required": minimum_size,
                "minimum_size_pass": bool(min_size >= minimum_size),
            }
        )

    evaluation = (
        pd.DataFrame(records)
        .sort_values(
            "k",
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    eligible = evaluation.loc[evaluation["minimum_size_pass"]].copy()

    if eligible.empty:
        raise ValueError("No candidate k satisfies the governed minimum audience size.")

    ranked = eligible.sort_values(
        [
            "silhouette_score",
            "business_actionability_score",
            "profile_distinctiveness_min",
            "minimum_segment_share",
            "k",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            True,
        ],
        kind="mergesort",
    )

    selected_k = int(ranked.iloc[0]["k"])

    evaluation["selected"] = evaluation["k"] == selected_k

    return evaluation


def _deterministic_primary_ids(
    customer: pd.DataFrame,
    raw_labels: np.ndarray,
) -> tuple[pd.Series, dict[int, str]]:
    labelled = customer.loc[
        :,
        [
            "household_id",
            "monetary_value",
            "frequency",
            "recency_days",
        ],
    ].copy()

    labelled["_cluster"] = raw_labels

    profiles = (
        labelled.groupby(
            "_cluster",
            as_index=False,
            sort=True,
        )
        .agg(
            median_monetary_value=(
                "monetary_value",
                "median",
            ),
            median_frequency=(
                "frequency",
                "median",
            ),
            median_recency=(
                "recency_days",
                "median",
            ),
        )
        .sort_values(
            [
                "median_monetary_value",
                "median_frequency",
                "median_recency",
                "_cluster",
            ],
            ascending=[
                False,
                False,
                True,
                True,
            ],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    mapping = {
        int(row["_cluster"]): f"P{index:02d}"
        for index, (
            _row_index,
            row,
        ) in enumerate(
            profiles.iterrows(),
            start=1,
        )
    }

    primary = pd.Series(
        raw_labels,
        index=customer.index,
    ).map(mapping)

    if primary.isna().any():
        raise ValueError("Primary segment deterministic-ID mapping failed.")

    return (
        primary.astype("string"),
        mapping,
    )


def _primary_profile_frame(
    customer: pd.DataFrame,
) -> pd.DataFrame:
    grouped = customer.groupby(
        "primary_segment_id",
        as_index=False,
        sort=True,
    ).agg(
        member_count=(
            "household_id",
            "size",
        ),
        median_recency_days=(
            "recency_days",
            "median",
        ),
        average_order_frequency=(
            "frequency",
            "mean",
        ),
        median_order_frequency=(
            "frequency",
            "median",
        ),
        average_monetary_value=(
            "monetary_value",
            "mean",
        ),
        median_monetary_value=(
            "monetary_value",
            "median",
        ),
        average_order_value=(
            "average_order_value",
            "mean",
        ),
        median_promotion_dependency=(
            "promotion_dependency",
            "median",
        ),
        average_category_breadth=(
            "category_breadth",
            "mean",
        ),
        dominant_category=(
            "dominant_category",
            lambda values: (
                values.astype("string")
                .value_counts(dropna=False)
                .sort_index(kind="mergesort")
                .idxmax()
            ),
        ),
    )

    grouped["customer_share"] = grouped["member_count"] / len(customer)

    return grouped


def _governed_primary_names(
    profiles: pd.DataFrame,
    customer: pd.DataFrame,
) -> tuple[
    dict[str, str],
    dict[str, str],
]:
    global_monetary = float(customer["monetary_value"].median())

    global_frequency = float(customer["frequency"].median())

    global_recency = float(customer["recency_days"].median())

    global_promotion = float(customer["promotion_dependency"].median())

    names: dict[str, str] = {}

    definitions: dict[str, str] = {}

    for _index, row in profiles.iterrows():
        segment_id = str(row["primary_segment_id"])

        high_value = float(row["median_monetary_value"]) >= global_monetary * 1.20

        high_frequency = float(row["median_order_frequency"]) >= global_frequency * 1.20

        lapsed = float(row["median_recency_days"]) >= max(
            global_recency * 1.30,
            global_recency + 14.0,
        )

        promotion_sensitive = float(row["median_promotion_dependency"]) >= max(
            0.50,
            global_promotion + 0.10,
        )

        if high_value and high_frequency and not lapsed:
            base_name = "High-Value Loyalists"
        elif high_value and lapsed:
            base_name = "Lapsed High-Value Customers"
        elif promotion_sensitive and high_frequency:
            base_name = "Promotion-Responsive Regulars"
        elif high_frequency and not lapsed:
            base_name = "Frequent Core Shoppers"
        elif lapsed:
            base_name = "Re-engagement Candidates"
        elif high_value:
            base_name = "High-Value Occasional Shoppers"
        elif promotion_sensitive:
            base_name = "Promotion-Oriented Shoppers"
        else:
            base_name = "Developing Core Shoppers"

        name = f"{base_name} — {segment_id}"

        definition = (
            f"{segment_id}: {int(row['member_count'])} households "
            f"({float(row['customer_share']):.1%}); "
            f"median recency {float(row['median_recency_days']):.0f} days, "
            f"median frequency {float(row['median_order_frequency']):.1f} baskets, "
            f"average monetary value ${float(row['average_monetary_value']):,.2f}, "
            f"average order value ${float(row['average_order_value']):,.2f}, "
            f"dominant category {row['dominant_category']}, "
            f"promotion dependency "
            f"{float(row['median_promotion_dependency']):.1%}."
        )

        names[segment_id] = name

        definitions[segment_id] = definition

    if len(set(names.values())) != len(names):
        raise ValueError("Governed primary segment names are not unique.")

    return (
        names,
        definitions,
    )


def _secondary_masks(
    customer: pd.DataFrame,
    minimum_size: int,
) -> tuple[
    dict[str, pd.Series],
    dict[str, tuple[str, str]],
    list[str],
]:
    masks: dict[str, pd.Series] = {}

    metadata: dict[str, tuple[str, str]] = {}

    omitted: list[str] = []

    def add_rule(
        audience_id: str,
        name: str,
        definition: str,
        mask: pd.Series,
    ) -> None:
        normalized = mask.fillna(False).astype(bool)

        if int(normalized.sum()) < minimum_size:
            omitted.append(audience_id)
            return

        masks[audience_id] = normalized

        metadata[audience_id] = (
            name,
            definition,
        )

    monetary_threshold = float(customer["monetary_value"].quantile(0.75))

    frequency_threshold = float(customer["frequency"].quantile(0.75))

    recency_threshold = float(customer["recency_days"].quantile(0.75))

    promotion_threshold = float(customer["promotion_dependency"].quantile(0.75))

    add_rule(
        "A_HIGH_VALUE",
        "High Value",
        (
            "Households at or above the 75th percentile of "
            f"monetary value (${monetary_threshold:,.2f})."
        ),
        customer["monetary_value"] >= monetary_threshold,
    )

    add_rule(
        "A_HIGH_FREQUENCY",
        "High Frequency",
        (
            "Households at or above the 75th percentile of "
            f"purchase frequency ({frequency_threshold:.1f} baskets)."
        ),
        customer["frequency"] >= frequency_threshold,
    )

    add_rule(
        "A_PROMOTION_SENSITIVE",
        "Promotion Sensitive",
        (
            "Households at or above the 75th percentile of "
            "promotion dependency and with non-zero promotion usage."
        ),
        (customer["promotion_dependency"] >= promotion_threshold)
        & (customer["promotion_dependency"] > 0),
    )

    add_rule(
        "A_REENGAGEMENT",
        "Lapsed / Re-engagement",
        (
            "Households at or above the 75th percentile of "
            f"recency ({recency_threshold:.1f} days since purchase)."
        ),
        customer["recency_days"] >= recency_threshold,
    )

    category_counts = (
        customer["dominant_category"]
        .astype("string")
        .value_counts(dropna=False)
        .rename_axis("dominant_category")
        .reset_index(
            name="member_count",
        )
        .sort_values(
            [
                "member_count",
                "dominant_category",
            ],
            ascending=[
                False,
                True,
            ],
            kind="mergesort",
        )
    )

    category_index = 1

    for _row_index, row in category_counts.iterrows():
        if category_index > 5:
            break

        member_count = int(row["member_count"])

        if member_count < minimum_size:
            continue

        category = str(row["dominant_category"])

        audience_id = f"A_CATEGORY_{category_index:02d}"

        add_rule(
            audience_id,
            f"{category} Affinity",
            (f"Households whose dominant transactional category is {category}."),
            customer["dominant_category"].astype("string") == category,
        )

        category_index += 1

    return (
        masks,
        metadata,
        omitted,
    )


def _membership_frame(
    customer: pd.DataFrame,
    secondary_masks: dict[str, pd.Series],
) -> pd.DataFrame:
    primary = customer.loc[
        :,
        [
            "household_id",
            "primary_segment_id",
        ],
    ].rename(
        columns={
            "primary_segment_id": "audience_id",
        }
    )

    primary["audience_type"] = "PRIMARY_ML_SEGMENT"

    primary["is_primary"] = True

    primary["membership"] = True

    records = [
        primary.loc[
            :,
            [
                "household_id",
                "audience_id",
                "audience_type",
                "is_primary",
                "membership",
            ],
        ]
    ]

    for audience_id in sorted(secondary_masks):
        mask = secondary_masks[audience_id]

        members = customer.loc[
            mask,
            [
                "household_id",
            ],
        ].copy()

        members["audience_id"] = audience_id

        members["audience_type"] = "SECONDARY_ACTIVATION"

        members["is_primary"] = False

        members["membership"] = True

        records.append(members)

    membership = pd.concat(
        records,
        ignore_index=True,
    )

    return membership.sort_values(
        [
            "household_id",
            "is_primary",
            "audience_id",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="mergesort",
    ).reset_index(drop=True)


def _taxonomy_frame(
    profiles: pd.DataFrame,
    primary_names: dict[str, str],
    primary_definitions: dict[str, str],
    secondary_masks: dict[str, pd.Series],
    secondary_metadata: dict[str, tuple[str, str]],
    primary_minimum_size: int,
    secondary_minimum_size: int,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for _index, row in profiles.iterrows():
        audience_id = str(row["primary_segment_id"])

        records.append(
            {
                "audience_id": audience_id,
                "audience_name": primary_names[audience_id],
                "audience_type": "PRIMARY_ML_SEGMENT",
                "exclusive": True,
                "definition": primary_definitions[audience_id],
                "taxonomy_version": AUDIENCE_TAXONOMY_VERSION,
                "minimum_size": primary_minimum_size,
                "member_count": int(row["member_count"]),
                "privacy_classification": ("PSEUDONYMOUS_AGGREGATED_BEHAVIORAL_SEGMENT"),
                "status": "ACTIVE",
            }
        )

    for audience_id in sorted(secondary_masks):
        name, definition = secondary_metadata[audience_id]

        records.append(
            {
                "audience_id": audience_id,
                "audience_name": name,
                "audience_type": "SECONDARY_ACTIVATION",
                "exclusive": False,
                "definition": definition,
                "taxonomy_version": AUDIENCE_TAXONOMY_VERSION,
                "minimum_size": secondary_minimum_size,
                "member_count": int(secondary_masks[audience_id].sum()),
                "privacy_classification": ("PSEUDONYMOUS_RULE_BASED_BEHAVIORAL_AUDIENCE"),
                "status": "ACTIVE",
            }
        )

    taxonomy = (
        pd.DataFrame(records)
        .sort_values(
            [
                "audience_type",
                "audience_id",
            ],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    if taxonomy["audience_name"].duplicated().any():
        duplicates = taxonomy.loc[
            taxonomy["audience_name"].duplicated(keep=False),
            "audience_name",
        ].tolist()

        raise ValueError(f"Audience taxonomy contains duplicate names: {duplicates}")

    if (taxonomy["member_count"] < taxonomy["minimum_size"]).any():
        raise ValueError("Audience taxonomy violates governed minimum audience size.")

    return taxonomy


def _audience_profile_frame(
    customer: pd.DataFrame,
    taxonomy: pd.DataFrame,
    membership: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _index, taxon in taxonomy.iterrows():
        audience_id = str(taxon["audience_id"])

        household_ids = membership.loc[
            membership["audience_id"] == audience_id,
            "household_id",
        ]

        subset = customer.loc[customer["household_id"].isin(household_ids)]

        if subset.empty:
            raise ValueError(f"Audience profile has no members: {audience_id}")

        dominant_category = (
            subset["dominant_category"]
            .astype("string")
            .value_counts(dropna=False)
            .sort_index(kind="mergesort")
            .idxmax()
        )

        rows.append(
            {
                "audience_id": audience_id,
                "audience_name": taxon["audience_name"],
                "audience_type": taxon["audience_type"],
                "member_count": len(subset),
                "customer_share": len(subset) / len(customer),
                "median_recency_days": float(subset["recency_days"].median()),
                "average_order_frequency": float(subset["frequency"].mean()),
                "average_monetary_value": float(subset["monetary_value"].mean()),
                "average_order_value": float(subset["average_order_value"].mean()),
                "dominant_category": str(dominant_category),
                "promotion_dependency": float(subset["promotion_dependency"].mean()),
                "category_breadth": float(subset["category_breadth"].mean()),
            }
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "audience_type",
                "audience_id",
            ],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )


def _overlap_frame(
    membership: pd.DataFrame,
) -> pd.DataFrame:
    secondary = membership.loc[membership["audience_type"] == "SECONDARY_ACTIVATION"]

    audience_ids = sorted(secondary["audience_id"].astype(str).unique())

    member_sets = {
        audience_id: set(
            secondary.loc[
                secondary["audience_id"] == audience_id,
                "household_id",
            ].astype(str)
        )
        for audience_id in audience_ids
    }

    rows: list[dict[str, object]] = []

    for audience_a in audience_ids:
        members_a = member_sets[audience_a]

        for audience_b in audience_ids:
            members_b = member_sets[audience_b]

            intersection = members_a & members_b
            union = members_a | members_b

            rows.append(
                {
                    "audience_a": audience_a,
                    "audience_b": audience_b,
                    "audience_a_size": len(members_a),
                    "audience_b_size": len(members_b),
                    "intersection_count": len(intersection),
                    "overlap_pct_of_a": (len(intersection) / len(members_a) if members_a else 0.0),
                    "overlap_pct_of_b": (len(intersection) / len(members_b) if members_b else 0.0),
                    "jaccard_index": (len(intersection) / len(union) if union else 0.0),
                }
            )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "audience_a",
                "audience_b",
            ],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )


def _canonicalize_float_frame(
    frame: pd.DataFrame,
    *,
    decimals: int = 12,
) -> pd.DataFrame:
    """Canonicalize floating analytical evidence for stable output."""

    canonical = frame.copy()

    for column in canonical.columns:
        if not pd.api.types.is_float_dtype(canonical[column]):
            continue

        values = canonical[column].round(decimals)

        values = values.mask(
            values == 0.0,
            0.0,
        )

        canonical[column] = values

    return canonical


def _pca_projection(
    customer: pd.DataFrame,
    prepared: PreparedFeatures,
) -> tuple[
    pd.DataFrame,
    tuple[float, float],
]:
    pca = PCA(
        n_components=2,
        svd_solver="full",
    )

    coordinates = pca.fit_transform(prepared.matrix)
    # PCA_SIGN_CANONICALIZATION
    for component_index in range(2):
        loadings = pca.components_[component_index]

        pivot_index = int(np.argmax(np.abs(loadings)))

        if loadings[pivot_index] < 0:
            coordinates[
                :,
                component_index,
            ] *= -1.0

    projection = pd.DataFrame(
        {
            "household_id": customer["household_id"].astype("string"),
            "primary_segment_id": customer["primary_segment_id"].astype("string"),
            "pc1": coordinates[
                :,
                0,
            ],
            "pc2": coordinates[
                :,
                1,
            ],
        }
    )

    explained = tuple(float(value) for value in pca.explained_variance_ratio_)

    if len(explained) != 2:
        raise ValueError("PCA did not produce exactly two explained-variance values.")

    return (
        projection,
        (
            explained[0],
            explained[1],
        ),
    )


def build_segmentation_frames(
    customer_features: pd.DataFrame,
) -> SegmentationFrames:
    """Build deterministic primary ML segments and overlapping audiences."""

    customer = customer_features.copy()

    required = {
        "household_id",
        "recency_days",
        "frequency",
        "monetary_value",
        "average_order_value",
        "promotion_dependency",
        "category_breadth",
        "dominant_category",
    }

    missing = sorted(required - set(customer.columns))

    if missing:
        raise ValueError(f"Customer feature store missing Step 4 columns: {missing}")

    if customer.empty:
        raise ValueError("Customer feature store is empty.")

    if customer["household_id"].isna().any():
        raise ValueError("Customer feature store contains null household IDs.")

    if customer["household_id"].duplicated().any():
        raise ValueError("Customer feature store is not one row per household.")

    customer = customer.sort_values(
        "household_id",
        kind="mergesort",
    ).reset_index(drop=True)

    prepared = _prepare_features(customer)

    k_evaluation = _evaluate_candidates(
        prepared,
        len(customer),
    )

    selected_rows = k_evaluation.loc[k_evaluation["selected"]]

    if len(selected_rows) != 1:
        raise ValueError("Exactly one candidate k must be selected.")

    selected_k = int(selected_rows.iloc[0]["k"])

    final_model = KMeans(
        n_clusters=selected_k,
        random_state=RANDOM_STATE,
        n_init=20,
        algorithm="lloyd",
    )

    raw_labels = final_model.fit_predict(prepared.matrix)

    primary_ids, _cluster_mapping = _deterministic_primary_ids(
        customer,
        raw_labels,
    )

    customer["primary_segment_id"] = primary_ids

    primary_profiles = _primary_profile_frame(customer)

    primary_names, primary_definitions = _governed_primary_names(
        primary_profiles,
        customer,
    )

    primary_minimum_size = _minimum_audience_size(
        len(customer),
        MIN_PRIMARY_AUDIENCE_FRACTION,
    )

    secondary_minimum_size = _minimum_audience_size(
        len(customer),
        MIN_SECONDARY_AUDIENCE_FRACTION,
    )

    secondary_masks, secondary_metadata, omitted_secondary = _secondary_masks(
        customer,
        secondary_minimum_size,
    )

    membership = _membership_frame(
        customer,
        secondary_masks,
    )

    taxonomy = _taxonomy_frame(
        primary_profiles,
        primary_names,
        primary_definitions,
        secondary_masks,
        secondary_metadata,
        primary_minimum_size,
        secondary_minimum_size,
    )

    profiles = _audience_profile_frame(
        customer,
        taxonomy,
        membership,
    )

    overlap = _overlap_frame(membership)

    pca_projection, pca_explained = _pca_projection(
        customer,
        prepared,
    )

    metadata: dict[str, object] = {
        "segmentation_objective": (
            "Create mutually exclusive behavioral customer segments "
            "for retail-media planning while preserving separate, "
            "overlapping rule-based activation audiences."
        ),
        "analysis_unit": "household_id",
        "population": len(customer),
        "random_state": RANDOM_STATE,
        "candidate_k": list(CANDIDATE_K),
        "selected_k": selected_k,
        "approved_feature_set": list(prepared.approved_features),
        "true_rfm_features": [
            "recency_days",
            "frequency",
            "monetary_value",
        ],
        "category_affinity_features": [
            column
            for column in prepared.approved_features
            if any(column.startswith(prefix) for prefix in CATEGORY_AFFINITY_PREFIXES)
        ],
        "promotion_behavior_features": [
            column
            for column in prepared.approved_features
            if column
            in {
                "retail_discount_dependency",
                "coupon_usage_rate",
                "coupon_redemption_rate",
                "promotion_dependency",
                "full_price_purchase_share",
                "discount_amount_per_sales_dollar",
            }
        ],
        "basket_value_features": [
            column
            for column in prepared.approved_features
            if column
            in {
                "average_order_value",
                "items_per_basket",
                "average_line_items_per_basket",
                "average_distinct_products_per_basket",
                "purchase_frequency_per_30d",
                "median_days_between_orders",
                "category_breadth",
                "category_concentration",
            }
        ],
        "log1p_features": list(prepared.log1p_features),
        "standardized_features": list(prepared.approved_features),
        "categorical_model_features": [],
        "categorical_preprocessing": (
            "not required; categorical retail behavior enters KMeans "
            "through numeric affinity shares, while dominant category "
            "is reserved for profiling and activation rules"
        ),
        "leakage_exclusions": list(BANNED_MODEL_COLUMNS),
        "raw_quantity_policy": (
            "diagnostic-only; raw quantity metrics are excluded from the KMeans feature set"
        ),
        "primary_segments_mutually_exclusive": True,
        "secondary_activation_audiences_overlap": True,
        "primary_minimum_audience_size": primary_minimum_size,
        "secondary_minimum_audience_size": secondary_minimum_size,
        "omitted_secondary_audiences_below_minimum_size": omitted_secondary,
        "taxonomy_version": AUDIENCE_TAXONOMY_VERSION,
        "pca_rule": ("PCA is visualization-only and never used to fit or select KMeans clusters"),
        "pca_explained_variance_ratio": [
            pca_explained[0],
            pca_explained[1],
        ],
        "k_selection_rule": (
            "eligible k must satisfy minimum segment size; "
            "deterministic lexicographic selection maximizes "
            "silhouette, business actionability, minimum centroid "
            "distinctiveness, minimum segment share, then prefers "
            "smaller k"
        ),
        "privacy_policy": (
            "audience taxonomy is behavioral and non-PII; "
            "household IDs are source-scoped pseudonymous activation keys"
        ),
    }

    metadata["missing_value_strategy"] = (
        "deterministic median imputation in the numeric "
        "model-preprocessing layer; source feature values remain "
        "unchanged and all-null model features fail closed"
    )

    metadata["missing_value_counts"] = {
        column: int(
            pd.to_numeric(
                customer[column],
                errors="coerce",
            )
            .isna()
            .sum()
        )
        for column in prepared.approved_features
        if pd.to_numeric(
            customer[column],
            errors="coerce",
        )
        .isna()
        .any()
    }

    # OUTPUT_FLOAT_CANONICALIZATION
    profiles = _canonicalize_float_frame(profiles)

    overlap = _canonicalize_float_frame(overlap)

    pca_projection = _canonicalize_float_frame(pca_projection)

    k_evaluation = _canonicalize_float_frame(k_evaluation)

    frames = SegmentationFrames(
        audience_profiles=profiles,
        audience_taxonomy=taxonomy,
        audience_membership=membership,
        audience_overlap=overlap,
        pca_projection=pca_projection,
        k_evaluation=k_evaluation,
        metadata=metadata,
    )

    validate_segmentation_frames(
        frames,
        customer,
    )

    return frames


def validate_segmentation_frames(
    frames: SegmentationFrames,
    customer_features: pd.DataFrame,
) -> None:
    """Validate Step 4 segmentation invariants."""

    population = len(customer_features)

    membership = frames.audience_membership
    taxonomy = frames.audience_taxonomy
    overlap = frames.audience_overlap
    pca = frames.pca_projection

    primary = membership.loc[membership["is_primary"].astype(bool)]

    primary_counts = primary.groupby(
        "household_id",
        sort=True,
    )["audience_id"].size()

    if len(primary_counts) != population:
        raise ValueError("Not every customer has a primary segment.")

    if not (primary_counts == 1).all():
        raise ValueError("Every customer must have exactly one primary segment.")

    primary_taxonomy = taxonomy.loc[taxonomy["audience_type"] == "PRIMARY_ML_SEGMENT"]

    if not primary_taxonomy["exclusive"].astype(bool).all():
        raise ValueError("Primary ML segments must be mutually exclusive.")

    secondary_taxonomy = taxonomy.loc[taxonomy["audience_type"] == "SECONDARY_ACTIVATION"]

    if secondary_taxonomy["exclusive"].astype(bool).any():
        raise ValueError("Secondary activation audiences must allow overlap.")

    if (taxonomy["member_count"] < taxonomy["minimum_size"]).any():
        raise ValueError("Audience minimum-size governance failed.")

    if taxonomy["audience_name"].duplicated().any():
        raise ValueError("Audience taxonomy contains duplicate governed names.")

    if taxonomy["definition"].astype(str).str.strip().eq("").any():
        raise ValueError("Audience taxonomy contains blank definitions.")

    if taxonomy["privacy_classification"].astype(str).str.strip().eq("").any():
        raise ValueError("Audience taxonomy contains blank privacy classifications.")

    if len(pca) != population:
        raise ValueError("PCA projection row count does not equal customer population.")

    if not {
        "pc1",
        "pc2",
    }.issubset(pca.columns):
        raise ValueError("PCA projection does not contain pc1 and pc2.")

    if not np.isfinite(
        pca[
            [
                "pc1",
                "pc2",
            ]
        ].to_numpy(dtype=float)
    ).all():
        raise ValueError("PCA projection contains non-finite values.")

    secondary = membership.loc[membership["audience_type"] == "SECONDARY_ACTIVATION"]

    if not secondary.empty:
        secondary_counts = secondary.groupby(
            "household_id",
            sort=True,
        )["audience_id"].nunique()

        if int(secondary_counts.max()) < 2:
            raise ValueError("Secondary activation audiences do not exhibit any overlap.")

    if not overlap.empty:
        for column in (
            "overlap_pct_of_a",
            "overlap_pct_of_b",
            "jaccard_index",
        ):
            values = pd.to_numeric(
                overlap[column],
                errors="raise",
            )

            if (values < -1e-12).any() or (values > 1.0 + 1e-12).any():
                raise ValueError(f"Audience overlap metric outside [0,1]: {column}")

    if frames.metadata.get("pca_rule") != (
        "PCA is visualization-only and never used to fit or select KMeans clusters"
    ):
        raise ValueError("PCA visualization-only governance rule is missing.")

    approved = set(
        cast(
            list[str],
            frames.metadata.get(
                "approved_feature_set",
                [],
            ),
        )
    )

    raw_quantity_columns = {
        "raw_quantity_mean_per_basket",
        "raw_quantity_median_per_basket",
        "raw_quantity_p95_per_basket",
        "raw_quantity_p99_per_basket",
    }

    if approved & raw_quantity_columns:
        raise ValueError("Diagnostic raw quantity leaked into KMeans feature set.")


def _write_frames(
    frames: SegmentationFrames,
    output_dir: Path,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = {
        "audience_profiles": frames.audience_profiles,
        "audience_taxonomy": frames.audience_taxonomy,
        "audience_membership": frames.audience_membership,
        "audience_overlap": frames.audience_overlap,
        "audience_pca": frames.pca_projection,
        "k_evaluation": frames.k_evaluation,
    }

    for name, frame in outputs.items():
        frame.to_csv(
            output_dir / f"{name}.csv",
            index=False,
            lineterminator="\n",
        )

        frame.to_parquet(
            output_dir / f"{name}.parquet",
            index=False,
        )

    manifest = {
        "metadata": frames.metadata,
        "stable_frame_hashes": {name: stable_frame_hash(frame) for name, frame in outputs.items()},
    }

    (output_dir / "segmentation_manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def build_from_step3_outputs(
    repository_root: Path,
    output_dir: Path,
) -> SegmentationFrames:
    """Build deterministic Step 4 outputs from frozen Step 3 artifacts."""

    customer_path = (
        repository_root
        / "outputs"
        / "p25_retail_media_audience_decision"
        / "step3_retail_customer_intelligence"
        / "customer_features.parquet"
    )

    if not customer_path.is_file():
        raise FileNotFoundError(customer_path)

    customer = pd.read_parquet(customer_path)

    first = build_segmentation_frames(customer)

    second = build_segmentation_frames(customer)

    first_hashes = {
        "audience_profiles": stable_frame_hash(first.audience_profiles),
        "audience_taxonomy": stable_frame_hash(first.audience_taxonomy),
        "audience_membership": stable_frame_hash(first.audience_membership),
        "audience_overlap": stable_frame_hash(first.audience_overlap),
        "audience_pca": stable_frame_hash(first.pca_projection),
        "k_evaluation": stable_frame_hash(first.k_evaluation),
    }

    second_hashes = {
        "audience_profiles": stable_frame_hash(second.audience_profiles),
        "audience_taxonomy": stable_frame_hash(second.audience_taxonomy),
        "audience_membership": stable_frame_hash(second.audience_membership),
        "audience_overlap": stable_frame_hash(second.audience_overlap),
        "audience_pca": stable_frame_hash(second.pca_projection),
        "k_evaluation": stable_frame_hash(second.k_evaluation),
    }

    if first_hashes != second_hashes:
        raise ValueError("Step 4 audience segmentation is not deterministic.")

    _write_frames(
        second,
        output_dir,
    )

    validate_output_directory(output_dir)

    return second


def validate_output_directory(
    output_dir: Path,
) -> None:
    """Validate materialized Step 4 output inventory."""

    expected = (
        "audience_profiles.csv",
        "audience_profiles.parquet",
        "audience_taxonomy.csv",
        "audience_taxonomy.parquet",
        "audience_membership.csv",
        "audience_membership.parquet",
        "audience_overlap.csv",
        "audience_overlap.parquet",
        "audience_pca.csv",
        "audience_pca.parquet",
        "k_evaluation.csv",
        "k_evaluation.parquet",
        "segmentation_manifest.json",
    )

    missing = [filename for filename in expected if not (output_dir / filename).is_file()]

    if missing:
        raise ValueError(f"Step 4 outputs missing: {missing}")

    membership_csv = pd.read_csv(output_dir / "audience_membership.csv")

    membership_parquet = pd.read_parquet(output_dir / "audience_membership.parquet")

    if len(membership_csv) != len(membership_parquet):
        raise ValueError("Step 4 CSV/Parquet membership row counts differ.")
