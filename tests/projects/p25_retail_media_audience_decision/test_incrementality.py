from __future__ import annotations

import numpy as np
import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.incrementality import (
    BOOTSTRAP_ITERATIONS,
    CONTROL,
    MENS_TREATMENT,
    WOMENS_TREATMENT,
    _bootstrap_spend_difference,
    build_incrementality_frames,
)


def _known_experiment() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for index in range(1000):
        rows.append(
            {
                "segment": CONTROL,
                "visit": int(index < 200),
                "conversion": int(index < 100),
                "spend": 10.0 if index < 100 else 0.0,
                "history": float(index + 1),
            }
        )

        rows.append(
            {
                "segment": MENS_TREATMENT,
                "visit": int(index < 300),
                "conversion": int(index < 150),
                "spend": 10.0 if index < 150 else 0.0,
                "history": float(index + 1),
            }
        )

        rows.append(
            {
                "segment": WOMENS_TREATMENT,
                "visit": int(index < 250),
                "conversion": int(index < 120),
                "spend": 10.0 if index < 120 else 0.0,
                "history": float(index + 1),
            }
        )

    return pd.DataFrame(rows)


def test_known_incrementality_case() -> None:
    frames = build_incrementality_frames(_known_experiment())

    mens = frames.treatment_effects.loc[
        frames.treatment_effects["treatment"] == MENS_TREATMENT
    ].iloc[0]

    womens = frames.treatment_effects.loc[
        frames.treatment_effects["treatment"] == WOMENS_TREATMENT
    ].iloc[0]

    assert np.isclose(
        mens["incremental_visit_rate"],
        0.10,
    )

    assert np.isclose(
        mens["incremental_conversion_rate"],
        0.05,
    )

    assert np.isclose(
        mens["incremental_spend_per_customer"],
        0.50,
    )

    assert np.isclose(
        mens["incremental_spend_per_1000"],
        500.0,
    )

    assert np.isclose(
        womens["incremental_conversion_rate"],
        0.02,
    )


def test_confidence_intervals_order_correctly() -> None:
    frames = build_incrementality_frames(_known_experiment())

    for _index, row in frames.treatment_effects.iterrows():
        assert (
            row["incremental_visit_rate_ci_lower"]
            <= row["incremental_visit_rate"]
            <= row["incremental_visit_rate_ci_upper"]
        )

        assert (
            row["incremental_conversion_rate_ci_lower"]
            <= row["incremental_conversion_rate"]
            <= row["incremental_conversion_rate_ci_upper"]
        )

        assert (
            row["incremental_spend_per_customer_ci_lower"]
            <= row["incremental_spend_per_customer"]
            <= row["incremental_spend_per_customer_ci_upper"]
        )


def test_spend_bootstrap_is_deterministic() -> None:
    treatment = np.array(
        [
            0.0,
            0.0,
            5.0,
            10.0,
            20.0,
        ]
    )

    control = np.array(
        [
            0.0,
            0.0,
            0.0,
            5.0,
            10.0,
        ]
    )

    first, first_low, first_high = _bootstrap_spend_difference(
        treatment,
        control,
        iterations=250,
        random_state=42,
    )

    second, second_low, second_high = _bootstrap_spend_difference(
        treatment,
        control,
        iterations=250,
        random_state=42,
    )

    assert np.array_equal(
        first,
        second,
    )

    assert first_low == second_low
    assert first_high == second_high


def test_default_bootstrap_iteration_contract() -> None:
    frames = build_incrementality_frames(_known_experiment())

    assert set(frames.treatment_effects["bootstrap_iterations"]) == {BOOTSTRAP_ITERATIONS}


def test_spend_per_converter_is_not_claimed_as_causal() -> None:
    frames = build_incrementality_frames(_known_experiment())

    assert (
        frames.group_metrics["spend_per_converter_interpretation"]
        .eq("DESCRIPTIVE_POST_TREATMENT_CONDITIONED")
        .all()
    )
