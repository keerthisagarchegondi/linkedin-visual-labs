from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.incrementality import (
    CONTROL,
    MENS_TREATMENT,
    WOMENS_TREATMENT,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.uplift import (
    POST_TREATMENT_COLUMNS,
    TREATMENT_COLUMNS,
    _qini_statistic,
    _randomized_gain_curve,
    build_uplift_comparison,
    build_uplift_frames,
)


def _synthetic_uplift_experiment() -> pd.DataFrame:
    generator = np.random.default_rng(42)

    rows: list[dict[str, object]] = []

    segments = (
        CONTROL,
        MENS_TREATMENT,
        WOMENS_TREATMENT,
    )

    for segment_index, segment in enumerate(segments):
        for index in range(500):
            history = float(10 + index % 100)

            recency = float(1 + index % 12)

            channel = "Phone" if index % 3 == 0 else ("Web" if index % 3 == 1 else "Multichannel")

            history_segment = "high" if history >= 70 else ("medium" if history >= 40 else "low")

            newbie = int(index % 5 == 0)

            base = 0.02 + 0.002 * (history / 10.0)

            mens_effect = 0.10 if history < 50 else -0.01

            womens_effect = 0.08 if channel == "Web" else 0.01

            probability = base

            if segment == MENS_TREATMENT:
                probability += mens_effect

            if segment == WOMENS_TREATMENT:
                probability += womens_effect

            probability = float(
                np.clip(
                    probability,
                    0.001,
                    0.85,
                )
            )

            conversion = int(generator.random() < probability)

            visit = int(
                conversion
                or generator.random()
                < min(
                    0.90,
                    probability + 0.20,
                )
            )

            spend = float(20 + history * 0.3) if conversion else 0.0

            rows.append(
                {
                    "recency": recency,
                    "history_segment": history_segment,
                    "history": history,
                    "mens": int(index % 4 == 0),
                    "womens": int(index % 6 == 0),
                    "zip_code": str(10000 + index % 8),
                    "newbie": newbie,
                    "channel": channel,
                    "segment": segment,
                    "visit": visit,
                    "conversion": conversion,
                    "spend": spend,
                    "_test_segment_index": segment_index,
                }
            )

    return pd.DataFrame(rows)


def test_uplift_model_excludes_treatment_and_post_treatment_features() -> None:
    frame = _synthetic_uplift_experiment()

    comparison = build_uplift_comparison(
        frame,
        treatment_name=MENS_TREATMENT,
    )

    approved = {
        str(value).lower()
        for value in cast(
            list[str],
            comparison.metadata["approved_features"],
        )
    }

    assert not (approved & POST_TREATMENT_COLUMNS)

    assert not (approved & TREATMENT_COLUMNS)


def test_uplift_reproducibility() -> None:
    frame = _synthetic_uplift_experiment()

    first = build_uplift_comparison(
        frame,
        treatment_name=MENS_TREATMENT,
    )

    second = build_uplift_comparison(
        frame,
        treatment_name=MENS_TREATMENT,
    )

    assert stable_frame_hash(first.test_scores) == stable_frame_hash(second.test_scores)

    assert stable_frame_hash(first.metrics) == stable_frame_hash(second.metrics)


def test_qini_curve_and_statistic_are_finite() -> None:
    frame = pd.DataFrame(
        {
            "_stable_row_id": np.arange(12),
            "uplift_score": np.linspace(
                1.0,
                0.0,
                12,
            ),
            "received_treatment": [
                1,
                0,
                1,
                0,
                1,
                0,
                1,
                0,
                1,
                0,
                1,
                0,
            ],
            "conversion_outcome": [
                1,
                0,
                1,
                0,
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
        }
    )

    curve = _randomized_gain_curve(
        frame,
        treatment_probability=0.5,
    )

    qini = _qini_statistic(curve)

    assert len(curve) == len(frame)

    assert np.isfinite(qini)

    assert {
        "population_fraction",
        "cumulative_incremental_conversions",
        "random_targeting_gain",
        "qini_gain_above_random",
    }.issubset(curve.columns)


def test_both_treatment_models_and_recommendations() -> None:
    frame = _synthetic_uplift_experiment()

    outputs = build_uplift_frames(frame)

    models = set(outputs.evaluation_metrics["model"])

    assert {
        "T_LEARNER_LOGISTIC_REGRESSION",
        "SIMPLE_PRETREATMENT_SEGMENT_RULE",
        "RANDOM_TARGETING",
    }.issubset(models)

    assert set(outputs.evaluation_metrics["treatment"]) == {
        MENS_TREATMENT,
        WOMENS_TREATMENT,
    }

    assert not outputs.treatment_recommendations.empty

    assert (
        outputs.treatment_recommendations["best_treatment"]
        .isin(
            [
                MENS_TREATMENT,
                WOMENS_TREATMENT,
            ]
        )
        .all()
    )


def test_high_value_not_equated_to_high_uplift() -> None:
    outputs = build_uplift_frames(_synthetic_uplift_experiment())

    evidence = outputs.high_value_uplift_evidence.iloc[0]

    assert not bool(evidence["sets_identical"])

    assert (
        int(evidence["high_value_not_high_uplift_count"]) > 0
        or int(evidence["high_uplift_not_high_value_count"]) > 0
    )
