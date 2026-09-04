"""Randomized Hillstrom incrementality analysis for Project 4."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import NormalDist
from typing import Final

import numpy as np
import pandas as pd

CONTROL: Final[str] = "No E-Mail"
MENS_TREATMENT: Final[str] = "Mens E-Mail"
WOMENS_TREATMENT: Final[str] = "Womens E-Mail"

TREATMENTS: Final[tuple[str, ...]] = (
    MENS_TREATMENT,
    WOMENS_TREATMENT,
)

CONFIDENCE_LEVEL: Final[float] = 0.95
BOOTSTRAP_ITERATIONS: Final[int] = 5000
RANDOM_STATE: Final[int] = 42


SEGMENT_ALIASES: Final[tuple[str, ...]] = (
    "segment",
    "treatment",
    "email_segment",
    "experiment_segment",
)

VISIT_ALIASES: Final[tuple[str, ...]] = (
    "visit",
    "visited",
)

CONVERSION_ALIASES: Final[tuple[str, ...]] = (
    "conversion",
    "converted",
)

SPEND_ALIASES: Final[tuple[str, ...]] = (
    "spend",
    "revenue",
)


@dataclass(frozen=True)
class HillstromSchema:
    """Resolved Hillstrom experiment columns."""

    segment: str
    visit: str
    conversion: str
    spend: str


@dataclass(frozen=True)
class IncrementalityFrames:
    """Governed randomized-experiment outputs."""

    group_metrics: pd.DataFrame
    treatment_effects: pd.DataFrame
    bootstrap_distribution: pd.DataFrame
    metadata: dict[str, object]


def _resolve_column(
    frame: pd.DataFrame,
    aliases: tuple[str, ...],
    concept: str,
) -> str:
    lookup = {str(column).strip().lower(): str(column) for column in frame.columns}

    for alias in aliases:
        if alias in lookup:
            return lookup[alias]

    raise ValueError(f"Hillstrom {concept} column not found; available={list(frame.columns)}")


def resolve_hillstrom_schema(
    frame: pd.DataFrame,
) -> HillstromSchema:
    """Resolve the minimum randomized-outcome schema."""

    return HillstromSchema(
        segment=_resolve_column(
            frame,
            SEGMENT_ALIASES,
            "treatment segment",
        ),
        visit=_resolve_column(
            frame,
            VISIT_ALIASES,
            "visit",
        ),
        conversion=_resolve_column(
            frame,
            CONVERSION_ALIASES,
            "conversion",
        ),
        spend=_resolve_column(
            frame,
            SPEND_ALIASES,
            "spend",
        ),
    )


def canonicalize_hillstrom(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return a canonical randomized-experiment analysis frame."""

    schema = resolve_hillstrom_schema(frame)

    canonical = frame.copy()

    canonical["experiment_segment"] = canonical[schema.segment].astype("string").str.strip()

    canonical["visit_outcome"] = pd.to_numeric(
        canonical[schema.visit],
        errors="raise",
    ).astype(int)

    canonical["conversion_outcome"] = pd.to_numeric(
        canonical[schema.conversion],
        errors="raise",
    ).astype(int)

    canonical["spend_outcome"] = pd.to_numeric(
        canonical[schema.spend],
        errors="raise",
    ).astype(float)

    valid_segments = {
        CONTROL,
        MENS_TREATMENT,
        WOMENS_TREATMENT,
    }

    observed = set(canonical["experiment_segment"].dropna().astype(str))

    if observed != valid_segments:
        raise ValueError(
            "Hillstrom randomized segments differ from governed "
            f"contract. observed={sorted(observed)}"
        )

    for column in (
        "visit_outcome",
        "conversion_outcome",
    ):
        values = set(canonical[column].unique())

        if not values.issubset(
            {
                0,
                1,
            }
        ):
            raise ValueError(f"{column} is not binary: {sorted(values)}")

    if (canonical["spend_outcome"] < 0).any():
        raise ValueError("Hillstrom spend must be nonnegative.")

    return canonical


def _binary_rate_ci(
    successes: int,
    population: int,
) -> tuple[float, float]:
    if population <= 0:
        raise ValueError("Binary-rate population must be positive.")

    p = successes / population

    z = float(NormalDist().inv_cdf(0.5 + CONFIDENCE_LEVEL / 2.0))

    standard_error = np.sqrt(p * (1.0 - p) / population)

    return (
        max(
            0.0,
            float(p - z * standard_error),
        ),
        min(
            1.0,
            float(p + z * standard_error),
        ),
    )


def _difference_in_proportions_ci(
    treatment: np.ndarray,
    control: np.ndarray,
) -> tuple[float, float]:
    treatment = np.asarray(
        treatment,
        dtype=float,
    )

    control = np.asarray(
        control,
        dtype=float,
    )

    p_t = float(treatment.mean())

    p_c = float(control.mean())

    effect = p_t - p_c

    standard_error = np.sqrt(p_t * (1.0 - p_t) / len(treatment) + p_c * (1.0 - p_c) / len(control))

    z = float(NormalDist().inv_cdf(0.5 + CONFIDENCE_LEVEL / 2.0))

    return (
        float(effect - z * standard_error),
        float(effect + z * standard_error),
    )


def _difference_in_means_ci(
    treatment: np.ndarray,
    control: np.ndarray,
) -> tuple[float, float]:
    treatment = np.asarray(
        treatment,
        dtype=float,
    )

    control = np.asarray(
        control,
        dtype=float,
    )

    effect = float(treatment.mean() - control.mean())

    treatment_variance = float(treatment.var(ddof=1))

    control_variance = float(control.var(ddof=1))

    standard_error = np.sqrt(treatment_variance / len(treatment) + control_variance / len(control))

    z = float(NormalDist().inv_cdf(0.5 + CONFIDENCE_LEVEL / 2.0))

    return (
        float(effect - z * standard_error),
        float(effect + z * standard_error),
    )


def _bootstrap_spend_difference(
    treatment: np.ndarray,
    control: np.ndarray,
    *,
    iterations: int = BOOTSTRAP_ITERATIONS,
    random_state: int = RANDOM_STATE,
) -> tuple[
    np.ndarray,
    float,
    float,
]:
    treatment = np.asarray(
        treatment,
        dtype=float,
    )

    control = np.asarray(
        control,
        dtype=float,
    )

    generator = np.random.default_rng(random_state)

    differences = np.empty(
        iterations,
        dtype=float,
    )

    for iteration in range(iterations):
        treatment_sample = generator.choice(
            treatment,
            size=len(treatment),
            replace=True,
        )

        control_sample = generator.choice(
            control,
            size=len(control),
            replace=True,
        )

        differences[iteration] = treatment_sample.mean() - control_sample.mean()

    alpha = (1.0 - CONFIDENCE_LEVEL) / 2.0

    lower = float(
        np.quantile(
            differences,
            alpha,
        )
    )

    upper = float(
        np.quantile(
            differences,
            1.0 - alpha,
        )
    )

    return (
        differences,
        lower,
        upper,
    )


def build_incrementality_frames(
    frame: pd.DataFrame,
) -> IncrementalityFrames:
    """Measure randomized ITT effects for Hillstrom."""

    data = canonicalize_hillstrom(frame)

    group_records: list[dict[str, object]] = []

    for segment in (
        CONTROL,
        MENS_TREATMENT,
        WOMENS_TREATMENT,
    ):
        subset = data.loc[data["experiment_segment"] == segment]

        n = len(subset)

        if n == 0:
            raise ValueError(f"Randomized group is empty: {segment}")

        visits = int(subset["visit_outcome"].sum())

        conversions = int(subset["conversion_outcome"].sum())

        spend = float(subset["spend_outcome"].sum())

        visit_rate = visits / n
        conversion_rate = conversions / n
        spend_per_customer = spend / n

        converters = subset.loc[subset["conversion_outcome"] == 1]

        spend_per_converter = (
            float(converters["spend_outcome"].mean()) if not converters.empty else 0.0
        )

        visit_ci_lower, visit_ci_upper = _binary_rate_ci(
            visits,
            n,
        )

        conversion_ci_lower, conversion_ci_upper = _binary_rate_ci(
            conversions,
            n,
        )

        group_records.append(
            {
                "segment": segment,
                "customers": n,
                "visits": visits,
                "conversions": conversions,
                "total_spend": spend,
                "visit_rate": visit_rate,
                "visit_rate_ci_lower": visit_ci_lower,
                "visit_rate_ci_upper": visit_ci_upper,
                "conversion_rate": conversion_rate,
                "conversion_rate_ci_lower": conversion_ci_lower,
                "conversion_rate_ci_upper": conversion_ci_upper,
                "spend_per_customer": spend_per_customer,
                "spend_per_converter": spend_per_converter,
                "spend_per_converter_interpretation": ("DESCRIPTIVE_POST_TREATMENT_CONDITIONED"),
            }
        )

    group_metrics = pd.DataFrame(group_records)

    effect_records: list[dict[str, object]] = []

    bootstrap_records: list[dict[str, object]] = []

    control = data.loc[data["experiment_segment"] == CONTROL]

    for treatment_index, treatment_name in enumerate(TREATMENTS):
        treatment = data.loc[data["experiment_segment"] == treatment_name]

        visit_effect = float(treatment["visit_outcome"].mean() - control["visit_outcome"].mean())

        conversion_effect = float(
            treatment["conversion_outcome"].mean() - control["conversion_outcome"].mean()
        )

        spend_effect = float(treatment["spend_outcome"].mean() - control["spend_outcome"].mean())

        visit_ci = _difference_in_proportions_ci(
            treatment["visit_outcome"].to_numpy(),
            control["visit_outcome"].to_numpy(),
        )

        conversion_ci = _difference_in_proportions_ci(
            treatment["conversion_outcome"].to_numpy(),
            control["conversion_outcome"].to_numpy(),
        )

        spend_ci = _difference_in_means_ci(
            treatment["spend_outcome"].to_numpy(),
            control["spend_outcome"].to_numpy(),
        )

        bootstrap, bootstrap_lower, bootstrap_upper = _bootstrap_spend_difference(
            treatment["spend_outcome"].to_numpy(),
            control["spend_outcome"].to_numpy(),
            random_state=(RANDOM_STATE + treatment_index),
        )

        for iteration, effect in enumerate(bootstrap):
            bootstrap_records.append(
                {
                    "treatment": treatment_name,
                    "iteration": iteration,
                    "incremental_spend_per_customer": float(effect),
                }
            )

        effect_records.append(
            {
                "treatment": treatment_name,
                "control": CONTROL,
                "estimand": "INTENTION_TO_TREAT",
                "incremental_visit_rate": visit_effect,
                "incremental_visit_rate_ci_lower": visit_ci[0],
                "incremental_visit_rate_ci_upper": visit_ci[1],
                "incremental_conversion_rate": conversion_effect,
                "incremental_conversion_rate_ci_lower": conversion_ci[0],
                "incremental_conversion_rate_ci_upper": conversion_ci[1],
                "incremental_spend_per_customer": spend_effect,
                "incremental_spend_per_customer_ci_lower": spend_ci[0],
                "incremental_spend_per_customer_ci_upper": spend_ci[1],
                "incremental_spend_per_1000": spend_effect * 1000.0,
                "bootstrap_spend_ci_lower": bootstrap_lower,
                "bootstrap_spend_ci_upper": bootstrap_upper,
                "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            }
        )

    treatment_effects = pd.DataFrame(effect_records)

    bootstrap_distribution = pd.DataFrame(bootstrap_records)

    metadata: dict[str, object] = {
        "source": "Hillstrom randomized email experiment",
        "comparison_unit": "randomized customer",
        "control": CONTROL,
        "treatments": list(TREATMENTS),
        "causal_estimand": "intention_to_treat_difference_in_means",
        "primary_outcomes": [
            "visit",
            "conversion",
            "spend_per_customer",
        ],
        "spend_per_converter_policy": (
            "descriptive only because converter status is post-treatment"
        ),
        "confidence_level": CONFIDENCE_LEVEL,
        "spend_bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bootstrap_random_state": RANDOM_STATE,
    }

    return IncrementalityFrames(
        group_metrics=group_metrics,
        treatment_effects=treatment_effects,
        bootstrap_distribution=bootstrap_distribution,
        metadata=metadata,
    )
