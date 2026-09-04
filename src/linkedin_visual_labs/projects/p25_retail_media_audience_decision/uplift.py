"""Deterministic Hillstrom uplift modeling for Project 4."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.incrementality import (
    CONTROL,
    MENS_TREATMENT,
    RANDOM_STATE,
    WOMENS_TREATMENT,
    build_incrementality_frames,
    canonicalize_hillstrom,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)

TEST_SIZE: Final[float] = 0.30
UPLIFT_K: Final[float] = 0.20
HIGH_UPLIFT_QUANTILE: Final[float] = 0.80
LOW_UPLIFT_QUANTILE: Final[float] = 0.20
HIGH_VALUE_QUANTILE: Final[float] = 0.75
MIN_AUDIENCE_ABSOLUTE: Final[int] = 50
MIN_AUDIENCE_FRACTION: Final[float] = 0.02

POST_TREATMENT_COLUMNS: Final[set[str]] = {
    "visit",
    "visited",
    "visit_outcome",
    "conversion",
    "converted",
    "conversion_outcome",
    "spend",
    "revenue",
    "spend_outcome",
}

TREATMENT_COLUMNS: Final[set[str]] = {
    "segment",
    "treatment",
    "email_segment",
    "experiment_segment",
}

IDENTIFIER_COLUMNS: Final[set[str]] = {
    "customer_id",
    "user_id",
    "household_id",
    "id",
}

KNOWN_PRETREATMENT_COLUMNS: Final[tuple[str, ...]] = (
    "recency",
    "history",
    "history_segment",
    "mens",
    "womens",
    "zip_code",
    "newbie",
    "channel",
)


@dataclass(frozen=True)
class UpliftComparison:
    """One treatment-vs-control uplift result."""

    treatment: str
    test_scores: pd.DataFrame
    all_scores: pd.DataFrame
    metrics: pd.DataFrame
    curve: pd.DataFrame
    metadata: dict[str, object]


@dataclass(frozen=True)
class UpliftFrames:
    """All Step 5 uplift outputs."""

    individual_scores: pd.DataFrame
    evaluation_metrics: pd.DataFrame
    qini_curve: pd.DataFrame
    uplift_scorecards: pd.DataFrame
    treatment_recommendations: pd.DataFrame
    high_value_uplift_evidence: pd.DataFrame
    metadata: dict[str, object]


def _candidate_feature_columns(
    frame: pd.DataFrame,
) -> tuple[str, ...]:
    lookup = {str(column).strip().lower(): str(column) for column in frame.columns}

    approved = [lookup[name] for name in KNOWN_PRETREATMENT_COLUMNS if name in lookup]

    if not approved:
        raise ValueError("No recognized pre-treatment Hillstrom features found.")

    normalized = {str(column).strip().lower() for column in approved}

    leakage = (normalized & POST_TREATMENT_COLUMNS) | (normalized & TREATMENT_COLUMNS)

    if leakage:
        raise ValueError(f"Treatment/post-treatment leakage selected: {sorted(leakage)}")

    return tuple(approved)


def _split_feature_types(
    frame: pd.DataFrame,
    features: tuple[str, ...],
) -> tuple[
    list[str],
    list[str],
]:
    numeric: list[str] = []
    categorical: list[str] = []

    for column in features:
        if pd.api.types.is_numeric_dtype(frame[column]):
            numeric.append(column)
        else:
            categorical.append(column)

    return (
        numeric,
        categorical,
    )


def _preprocessor(
    frame: pd.DataFrame,
    features: tuple[str, ...],
) -> ColumnTransformer:
    numeric, categorical = _split_feature_types(
        frame,
        features,
    )

    transformers: list[
        tuple[
            str,
            object,
            list[str],
        ]
    ] = []

    if numeric:
        numeric_pipeline = Pipeline(
            steps=[
                (
                    "impute",
                    SimpleImputer(strategy="median"),
                ),
                (
                    "scale",
                    StandardScaler(),
                ),
            ]
        )

        transformers.append(
            (
                "numeric",
                numeric_pipeline,
                numeric,
            )
        )

    if categorical:
        categorical_pipeline = Pipeline(
            steps=[
                (
                    "impute",
                    SimpleImputer(strategy="most_frequent"),
                ),
                (
                    "one_hot",
                    OneHotEncoder(
                        handle_unknown="ignore",
                    ),
                ),
            ]
        )

        transformers.append(
            (
                "categorical",
                categorical_pipeline,
                categorical,
            )
        )

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
    )


def _response_model(
    frame: pd.DataFrame,
    features: tuple[str, ...],
) -> Pipeline:
    return Pipeline(
        steps=[
            (
                "preprocess",
                _preprocessor(
                    frame,
                    features,
                ),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    solver="lbfgs",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def _positive_probability(
    model: Pipeline,
    features: pd.DataFrame,
) -> np.ndarray:
    probabilities = model.predict_proba(features)

    classifier = cast(
        LogisticRegression,
        model.named_steps["model"],
    )

    classes = list(classifier.classes_)

    if 1 not in classes:
        raise ValueError("Binary response model has no positive class.")

    positive_index = classes.index(1)

    return probabilities[
        :,
        positive_index,
    ]


def _randomized_gain_curve(
    data: pd.DataFrame,
    *,
    treatment_probability: float,
) -> pd.DataFrame:
    ordered = data.sort_values(
        [
            "uplift_score",
            "_stable_row_id",
        ],
        ascending=[
            False,
            True,
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    treatment = ordered["received_treatment"].to_numpy(dtype=float)

    outcome = ordered["conversion_outcome"].to_numpy(dtype=float)

    transformed_outcome = outcome * treatment / treatment_probability - outcome * (
        1.0 - treatment
    ) / (1.0 - treatment_probability)

    cumulative_gain = np.cumsum(transformed_outcome)

    population_fraction = np.arange(
        1,
        len(ordered) + 1,
        dtype=float,
    ) / len(ordered)

    total_gain = float(cumulative_gain[-1])

    random_gain = population_fraction * total_gain

    return pd.DataFrame(
        {
            "population_fraction": population_fraction,
            "cumulative_incremental_conversions": cumulative_gain,
            "random_targeting_gain": random_gain,
            "qini_gain_above_random": (cumulative_gain - random_gain),
        }
    )


def _qini_statistic(
    curve: pd.DataFrame,
) -> float:
    x = curve["population_fraction"].to_numpy(dtype=float)

    y = curve["qini_gain_above_random"].to_numpy(dtype=float)

    return float(
        np.trapezoid(
            y,
            x,
        )
    )


def _uplift_at_k(
    data: pd.DataFrame,
    *,
    fraction: float = UPLIFT_K,
) -> float:
    count = max(
        1,
        int(np.ceil(len(data) * fraction)),
    )

    selected = data.sort_values(
        [
            "uplift_score",
            "_stable_row_id",
        ],
        ascending=[
            False,
            True,
        ],
        kind="mergesort",
    ).head(count)

    treatment = selected.loc[
        selected["received_treatment"] == 1,
        "conversion_outcome",
    ]

    control = selected.loc[
        selected["received_treatment"] == 0,
        "conversion_outcome",
    ]

    if treatment.empty or control.empty:
        return 0.0

    return float(treatment.mean() - control.mean())


def _simple_rule_scores(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> pd.Series:
    preferred = [
        column
        for column in (
            "history_segment",
            "channel",
            "zip_code",
        )
        if column in train.columns
    ]

    if preferred:
        grouping_column = preferred[0]

        group_scores: dict[
            str,
            float,
        ] = {}

        for value, group in train.groupby(
            grouping_column,
            dropna=False,
            sort=True,
        ):
            treatment = group.loc[
                group["received_treatment"] == 1,
                "conversion_outcome",
            ]

            control = group.loc[
                group["received_treatment"] == 0,
                "conversion_outcome",
            ]

            if treatment.empty or control.empty:
                score = 0.0
            else:
                score = float(treatment.mean() - control.mean())

            group_scores[str(value)] = score

        return test[grouping_column].astype("string").map(group_scores).fillna(0.0).astype(float)

    if "history" in train.columns:
        quantiles = pd.qcut(
            pd.to_numeric(
                train["history"],
                errors="coerce",
            ).rank(method="first"),
            q=4,
            labels=False,
        )

        enriched = train.copy()

        enriched["_rule_group"] = quantiles

        scores: dict[
            int,
            float,
        ] = {}

        for group_id, group in enriched.groupby(
            "_rule_group",
            sort=True,
        ):
            treatment = group.loc[
                group["received_treatment"] == 1,
                "conversion_outcome",
            ]

            control = group.loc[
                group["received_treatment"] == 0,
                "conversion_outcome",
            ]

            if treatment.empty or control.empty:
                score = 0.0
            else:
                score = float(treatment.mean() - control.mean())

            scores[int(cast(int, group_id))] = score

        edges = (
            pd.to_numeric(
                train["history"],
                errors="coerce",
            )
            .quantile(
                [
                    0.25,
                    0.50,
                    0.75,
                ]
            )
            .to_numpy()
        )

        test_history = pd.to_numeric(
            test["history"],
            errors="coerce",
        ).fillna(
            pd.to_numeric(
                train["history"],
                errors="coerce",
            ).median()
        )

        groups = np.digitize(
            test_history,
            edges,
            right=True,
        )

        return pd.Series(
            [
                scores.get(
                    int(group),
                    0.0,
                )
                for group in groups
            ],
            index=test.index,
            dtype=float,
        )

    return pd.Series(
        np.zeros(
            len(test),
            dtype=float,
        ),
        index=test.index,
    )


def build_uplift_comparison(
    source: pd.DataFrame,
    *,
    treatment_name: str,
) -> UpliftComparison:
    """Build one deterministic treatment-vs-control T-learner."""

    canonical = canonicalize_hillstrom(source)

    comparison = canonical.loc[
        canonical["experiment_segment"].isin(
            [
                CONTROL,
                treatment_name,
            ]
        )
    ].copy()

    comparison["received_treatment"] = (comparison["experiment_segment"] == treatment_name).astype(
        int
    )

    comparison["_stable_row_id"] = np.arange(
        len(comparison),
        dtype=int,
    )

    features = _candidate_feature_columns(comparison)

    feature_lookup = {str(column).strip().lower(): str(column) for column in features}

    forbidden = (set(feature_lookup) & POST_TREATMENT_COLUMNS) | (
        set(feature_lookup) & TREATMENT_COLUMNS
    )

    if forbidden:
        raise ValueError(f"Forbidden uplift features selected: {sorted(forbidden)}")

    stratify_key = (
        comparison["received_treatment"].astype(str)
        + "_"
        + comparison["conversion_outcome"].astype(str)
    )

    train, test = train_test_split(
        comparison,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify_key,
    )

    train = train.sort_values(
        "_stable_row_id",
        kind="mergesort",
    )

    test = test.sort_values(
        "_stable_row_id",
        kind="mergesort",
    )

    treatment_train = train.loc[train["received_treatment"] == 1]

    control_train = train.loc[train["received_treatment"] == 0]

    if (
        treatment_train["conversion_outcome"].nunique() < 2
        or control_train["conversion_outcome"].nunique() < 2
    ):
        raise ValueError("T-learner training split lacks binary outcome variation.")

    treatment_model = _response_model(
        treatment_train,
        features,
    )

    control_model = _response_model(
        control_train,
        features,
    )

    treatment_model.fit(
        treatment_train.loc[
            :,
            list(features),
        ],
        treatment_train["conversion_outcome"],
    )

    control_model.fit(
        control_train.loc[
            :,
            list(features),
        ],
        control_train["conversion_outcome"],
    )

    test_features = test.loc[
        :,
        list(features),
    ]

    treatment_probability = _positive_probability(
        treatment_model,
        test_features,
    )

    control_probability = _positive_probability(
        control_model,
        test_features,
    )

    scored_test = test.loc[
        :,
        [
            "_stable_row_id",
            "experiment_segment",
            "received_treatment",
            "conversion_outcome",
        ],
    ].copy()

    scored_test["predicted_treatment_response"] = treatment_probability

    scored_test["predicted_control_response"] = control_probability

    scored_test["uplift_score"] = treatment_probability - control_probability

    randomization_probability = float(scored_test["received_treatment"].mean())

    curve = _randomized_gain_curve(
        scored_test,
        treatment_probability=randomization_probability,
    )

    qini = _qini_statistic(curve)

    uplift_at_k = _uplift_at_k(scored_test)

    simple_rule = _simple_rule_scores(
        train,
        test,
    )

    simple_test = scored_test.copy()

    simple_test["uplift_score"] = simple_rule.to_numpy(dtype=float)

    simple_curve = _randomized_gain_curve(
        simple_test,
        treatment_probability=randomization_probability,
    )

    simple_qini = _qini_statistic(simple_curve)

    simple_uplift_at_k = _uplift_at_k(simple_test)

    random_test = scored_test.copy()

    random_test["uplift_score"] = 0.0

    random_qini = 0.0

    random_uplift_at_k = _uplift_at_k(random_test)

    metrics = pd.DataFrame(
        [
            {
                "treatment": treatment_name,
                "model": "T_LEARNER_LOGISTIC_REGRESSION",
                "test_customers": len(scored_test),
                "uplift_at_20pct": uplift_at_k,
                "qini_statistic": qini,
                "final_cumulative_incremental_conversions": float(
                    curve["cumulative_incremental_conversions"].iloc[-1]
                ),
            },
            {
                "treatment": treatment_name,
                "model": "SIMPLE_PRETREATMENT_SEGMENT_RULE",
                "test_customers": len(scored_test),
                "uplift_at_20pct": simple_uplift_at_k,
                "qini_statistic": simple_qini,
                "final_cumulative_incremental_conversions": float(
                    simple_curve["cumulative_incremental_conversions"].iloc[-1]
                ),
            },
            {
                "treatment": treatment_name,
                "model": "RANDOM_TARGETING",
                "test_customers": len(scored_test),
                "uplift_at_20pct": random_uplift_at_k,
                "qini_statistic": random_qini,
                "final_cumulative_incremental_conversions": float(
                    curve["random_targeting_gain"].iloc[-1]
                ),
            },
        ]
    )

    all_features = comparison.loc[
        :,
        list(features),
    ]

    all_scores = comparison.loc[
        :,
        [
            "_stable_row_id",
            "experiment_segment",
            "conversion_outcome",
        ],
    ].copy()

    all_scores["predicted_treatment_response"] = _positive_probability(
        treatment_model,
        all_features,
    )

    all_scores["predicted_control_response"] = _positive_probability(
        control_model,
        all_features,
    )

    all_scores["uplift_score"] = (
        all_scores["predicted_treatment_response"] - all_scores["predicted_control_response"]
    )

    metadata: dict[str, object] = {
        "treatment": treatment_name,
        "control": CONTROL,
        "outcome": "conversion",
        "model_family": "TwoModels/T-learner logistic regression",
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "approved_features": list(features),
        "post_treatment_exclusions": sorted(POST_TREATMENT_COLUMNS),
        "treatment_feature_exclusions": sorted(TREATMENT_COLUMNS),
        "evaluation_population": "held-out randomized comparison test set",
    }

    return UpliftComparison(
        treatment=treatment_name,
        test_scores=scored_test,
        all_scores=all_scores,
        metrics=metrics,
        curve=curve,
        metadata=metadata,
    )


def _minimum_audience_size(
    population: int,
) -> int:
    return max(
        MIN_AUDIENCE_ABSOLUTE,
        int(np.ceil(population * MIN_AUDIENCE_FRACTION)),
    )


def build_uplift_frames(
    source: pd.DataFrame,
) -> UpliftFrames:
    """Build both Hillstrom treatment uplift models."""

    canonical = canonicalize_hillstrom(source).reset_index(drop=True)

    canonical["_global_row_id"] = np.arange(
        len(canonical),
        dtype=int,
    )

    mens = build_uplift_comparison(
        canonical,
        treatment_name=MENS_TREATMENT,
    )

    womens = build_uplift_comparison(
        canonical,
        treatment_name=WOMENS_TREATMENT,
    )

    evaluation = pd.concat(
        [
            mens.metrics,
            womens.metrics,
        ],
        ignore_index=True,
    )

    mens_curve = mens.curve.copy()

    mens_curve["treatment"] = MENS_TREATMENT

    womens_curve = womens.curve.copy()

    womens_curve["treatment"] = WOMENS_TREATMENT

    qini_curve = pd.concat(
        [
            mens_curve,
            womens_curve,
        ],
        ignore_index=True,
    )

    # Refit full comparison models through comparison function outputs.
    # Scores are joined using the original canonical row position within
    # each treatment/control comparison.

    mens_comparison = canonical.loc[
        canonical["experiment_segment"].isin(
            [
                CONTROL,
                MENS_TREATMENT,
            ]
        )
    ].copy()

    mens_comparison["_stable_row_id"] = np.arange(
        len(mens_comparison),
        dtype=int,
    )

    mens_lookup = mens.all_scores.set_index("_stable_row_id")["uplift_score"]

    mens_comparison["mens_uplift_score"] = mens_comparison["_stable_row_id"].map(mens_lookup)

    womens_comparison = canonical.loc[
        canonical["experiment_segment"].isin(
            [
                CONTROL,
                WOMENS_TREATMENT,
            ]
        )
    ].copy()

    womens_comparison["_stable_row_id"] = np.arange(
        len(womens_comparison),
        dtype=int,
    )

    womens_lookup = womens.all_scores.set_index("_stable_row_id")["uplift_score"]

    womens_comparison["womens_uplift_score"] = womens_comparison["_stable_row_id"].map(
        womens_lookup
    )

    mens_global = mens_comparison.set_index("_global_row_id")["mens_uplift_score"]

    womens_global = womens_comparison.set_index("_global_row_id")["womens_uplift_score"]

    individual = canonical.loc[
        :,
        [
            "_global_row_id",
            "experiment_segment",
        ],
    ].copy()

    individual["mens_uplift_score"] = individual["_global_row_id"].map(mens_global)

    individual["womens_uplift_score"] = individual["_global_row_id"].map(womens_global)

    # Score treatment rows absent from the opposite binary comparison
    # using comparison-distribution medians only for recommendation
    # completeness would be semantically wrong. Keep them null instead.
    # Recommendation eligibility requires both treatment scores.

    eligible = individual.loc[
        individual[
            [
                "mens_uplift_score",
                "womens_uplift_score",
            ]
        ]
        .notna()
        .all(axis=1)
    ].copy()

    # Only No E-Mail customers naturally belong to both binary
    # comparison populations, giving a clean common recommendation
    # population free of cross-treatment identity fabrication.

    if not (eligible["experiment_segment"] == CONTROL).all():
        raise ValueError("Common treatment recommendation population must be control customers.")

    high_thresholds = {
        MENS_TREATMENT: float(eligible["mens_uplift_score"].quantile(HIGH_UPLIFT_QUANTILE)),
        WOMENS_TREATMENT: float(eligible["womens_uplift_score"].quantile(HIGH_UPLIFT_QUANTILE)),
    }

    low_thresholds = {
        MENS_TREATMENT: float(eligible["mens_uplift_score"].quantile(LOW_UPLIFT_QUANTILE)),
        WOMENS_TREATMENT: float(eligible["womens_uplift_score"].quantile(LOW_UPLIFT_QUANTILE)),
    }

    eligible["best_treatment"] = np.where(
        eligible["mens_uplift_score"] >= eligible["womens_uplift_score"],
        MENS_TREATMENT,
        WOMENS_TREATMENT,
    )

    eligible["best_uplift_score"] = eligible[
        [
            "mens_uplift_score",
            "womens_uplift_score",
        ]
    ].max(axis=1)

    eligible["potential_negative_uplift"] = eligible["best_uplift_score"] < 0

    eligible["high_uplift"] = (
        (eligible["best_treatment"] == MENS_TREATMENT)
        & (eligible["mens_uplift_score"] >= high_thresholds[MENS_TREATMENT])
    ) | (
        (eligible["best_treatment"] == WOMENS_TREATMENT)
        & (eligible["womens_uplift_score"] >= high_thresholds[WOMENS_TREATMENT])
    )

    eligible["low_uplift"] = (
        (eligible["best_treatment"] == MENS_TREATMENT)
        & (eligible["mens_uplift_score"] <= low_thresholds[MENS_TREATMENT])
    ) | (
        (eligible["best_treatment"] == WOMENS_TREATMENT)
        & (eligible["womens_uplift_score"] <= low_thresholds[WOMENS_TREATMENT])
    )

    minimum_size = _minimum_audience_size(len(eligible))

    audience_records: list[dict[str, object]] = []

    audience_masks = {
        "PERSUADABLE_HIGH_UPLIFT": eligible["high_uplift"],
        "LOW_UPLIFT": eligible["low_uplift"],
        "POTENTIAL_NEGATIVE_UPLIFT": eligible["potential_negative_uplift"],
    }

    for audience_id, mask in audience_masks.items():
        count = int(mask.sum())

        audience_records.append(
            {
                "audience_id": audience_id,
                "member_count": count,
                "minimum_size": minimum_size,
                "minimum_size_pass": count >= minimum_size,
                "mean_best_uplift": (
                    float(
                        eligible.loc[
                            mask,
                            "best_uplift_score",
                        ].mean()
                    )
                    if count
                    else 0.0
                ),
            }
        )

    scorecards = pd.DataFrame(audience_records)

    recommendations = eligible.copy()

    recommendations["recommended_action"] = np.where(
        recommendations["potential_negative_uplift"],
        "SUPPRESS_EMAIL",
        np.where(
            recommendations["high_uplift"],
            "PRIORITIZE_RECOMMENDED_TREATMENT",
            "STANDARD_ELIGIBILITY",
        ),
    )

    # High value != high uplift evidence.
    history_column = next(
        (column for column in canonical.columns if str(column).strip().lower() == "history"),
        None,
    )

    if history_column is None:
        raise ValueError(
            "Hillstrom pre-treatment history feature required for "
            "high-value vs high-uplift distinction."
        )

    history_by_id = canonical.set_index("_global_row_id")[history_column]

    recommendations["history_value"] = recommendations["_global_row_id"].map(history_by_id)

    high_value_threshold = float(
        pd.to_numeric(
            recommendations["history_value"],
            errors="raise",
        ).quantile(HIGH_VALUE_QUANTILE)
    )

    recommendations["high_value"] = (
        pd.to_numeric(
            recommendations["history_value"],
            errors="raise",
        )
        >= high_value_threshold
    )

    high_value_mask = recommendations["high_value"].astype(bool)

    high_uplift_mask = recommendations["high_uplift"].astype(bool)

    overlap_count = int((high_value_mask & high_uplift_mask).sum())

    high_value_count = int(high_value_mask.sum())

    high_uplift_count = int(high_uplift_mask.sum())

    evidence = pd.DataFrame(
        [
            {
                "population": len(recommendations),
                "high_value_threshold": high_value_threshold,
                "high_value_count": high_value_count,
                "high_uplift_count": high_uplift_count,
                "high_value_and_high_uplift_count": overlap_count,
                "high_value_not_high_uplift_count": (high_value_count - overlap_count),
                "high_uplift_not_high_value_count": (high_uplift_count - overlap_count),
                "sets_identical": bool(high_value_mask.equals(high_uplift_mask)),
            }
        ]
    )

    metadata: dict[str, object] = {
        "uplift_outcome": "conversion",
        "model_family": "TwoModels/T-learner logistic regression",
        "comparisons": [
            f"{MENS_TREATMENT} vs {CONTROL}",
            f"{WOMENS_TREATMENT} vs {CONTROL}",
        ],
        "evaluation": "deterministic held-out randomized test set",
        "uplift_at_k": UPLIFT_K,
        "high_uplift_quantile": HIGH_UPLIFT_QUANTILE,
        "low_uplift_quantile": LOW_UPLIFT_QUANTILE,
        "recommendation_population": (
            "No E-Mail randomized control customers with both counterfactual "
            "uplift scores; no cross-source or cross-treatment identity fabrication"
        ),
        "minimum_recommendation_audience_size": minimum_size,
        "high_value_policy": ("pre-treatment history >= 75th percentile"),
        "high_value_not_equal_high_uplift": bool(not evidence.iloc[0]["sets_identical"]),
        "mens_model": mens.metadata,
        "womens_model": womens.metadata,
    }

    return UpliftFrames(
        individual_scores=individual,
        evaluation_metrics=evaluation,
        qini_curve=qini_curve,
        uplift_scorecards=scorecards,
        treatment_recommendations=recommendations,
        high_value_uplift_evidence=evidence,
        metadata=metadata,
    )


def _canonical_float_frame(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    canonical = frame.copy()

    for column in canonical.columns:
        if pd.api.types.is_float_dtype(canonical[column]):
            canonical[column] = canonical[column].round(12)

    return canonical


def write_step5_outputs(
    source: pd.DataFrame,
    output_dir: Path,
) -> tuple[
    object,
    UpliftFrames,
]:
    """Build, verify determinism, and write Step 5 outputs."""

    incrementality = build_incrementality_frames(source)

    first = build_uplift_frames(source)

    second = build_uplift_frames(source)

    first_frames = {
        "individual_scores": _canonical_float_frame(first.individual_scores),
        "evaluation_metrics": _canonical_float_frame(first.evaluation_metrics),
        "qini_curve": _canonical_float_frame(first.qini_curve),
        "uplift_scorecards": _canonical_float_frame(first.uplift_scorecards),
        "treatment_recommendations": _canonical_float_frame(first.treatment_recommendations),
        "high_value_uplift_evidence": _canonical_float_frame(first.high_value_uplift_evidence),
    }

    second_frames = {
        "individual_scores": _canonical_float_frame(second.individual_scores),
        "evaluation_metrics": _canonical_float_frame(second.evaluation_metrics),
        "qini_curve": _canonical_float_frame(second.qini_curve),
        "uplift_scorecards": _canonical_float_frame(second.uplift_scorecards),
        "treatment_recommendations": _canonical_float_frame(second.treatment_recommendations),
        "high_value_uplift_evidence": _canonical_float_frame(second.high_value_uplift_evidence),
    }

    first_hashes = {name: stable_frame_hash(frame) for name, frame in first_frames.items()}

    second_hashes = {name: stable_frame_hash(frame) for name, frame in second_frames.items()}

    if first_hashes != second_hashes:
        differing = sorted(
            name for name in first_hashes if first_hashes[name] != second_hashes[name]
        )

        raise ValueError(f"Step 5 uplift outputs are not deterministic; differing={differing}")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    incrementality_frames = {
        "incrementality_group_metrics": _canonical_float_frame(incrementality.group_metrics),
        "incrementality_treatment_effects": _canonical_float_frame(
            incrementality.treatment_effects
        ),
        "incrementality_bootstrap_distribution": _canonical_float_frame(
            incrementality.bootstrap_distribution
        ),
    }

    all_outputs = {
        **incrementality_frames,
        **second_frames,
    }

    for name, frame in all_outputs.items():
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
        "incrementality_metadata": incrementality.metadata,
        "uplift_metadata": second.metadata,
        "stable_frame_hashes": {
            name: stable_frame_hash(frame) for name, frame in all_outputs.items()
        },
    }

    (output_dir / "step5_manifest.json").write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return (
        incrementality,
        second,
    )
