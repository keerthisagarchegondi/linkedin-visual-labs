from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.attribution import (
    ATTRIBUTION_METHODS,
    CAUSAL_INTERPRETATION,
    EXPECTED_CONVERSION_EVENTS,
    LOOKBACK_DAYS,
    TIME_DECAY_HALF_LIFE_DAYS,
    attribution_weights,
    build_attribution_outputs,
    reconstruct_journeys,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    stable_frame_hash,
)


def _source(
    journeys: list[
        tuple[
            int,
            int,
            list[tuple[int, int]],
        ]
    ],
    *,
    nonconverters: list[tuple[int, int, int]] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []

    for (
        user_id,
        conversion_id,
        touches,
    ) in journeys:
        conversion_timestamp = max(timestamp for timestamp, _campaign in touches) + 100

        for timestamp, campaign in touches:
            rows.append(
                {
                    "timestamp": timestamp,
                    "media_user_id": user_id,
                    "campaign": campaign,
                    "conversion": 1,
                    "conversion_timestamp": (conversion_timestamp),
                    "conversion_id": (conversion_id),
                    "click": 1,
                    "cost": 0.1,
                }
            )

    for (
        timestamp,
        user_id,
        campaign,
    ) in nonconverters or []:
        rows.append(
            {
                "timestamp": timestamp,
                "media_user_id": user_id,
                "campaign": campaign,
                "conversion": 0,
                "conversion_timestamp": -1,
                "conversion_id": -1,
                "click": 0,
                "cost": 0.1,
            }
        )

    return pd.DataFrame(rows)


def _touches(
    source: pd.DataFrame,
) -> pd.DataFrame:
    touches, _metadata = reconstruct_journeys(
        source,
        expected_rows=None,
    )

    return touches


def _weights(
    source: pd.DataFrame,
    method: str,
) -> np.ndarray[
    Any,
    np.dtype[np.float64],
]:
    return attribution_weights(
        _touches(source),
        method,
    )


def test_exactly_five_methods() -> None:
    assert ATTRIBUTION_METHODS == (
        "FIRST_TOUCH",
        "LAST_TOUCH",
        "LINEAR",
        "POSITION_BASED",
        "TIME_DECAY",
    )

    assert len(ATTRIBUTION_METHODS) == 5


def test_frozen_parameters() -> None:
    assert LOOKBACK_DAYS == 30
    assert TIME_DECAY_HALF_LIFE_DAYS == 7.0
    assert EXPECTED_CONVERSION_EVENTS == 83_155


def test_one_touch_semantics() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    )
                ],
            )
        ]
    )

    for method in ATTRIBUTION_METHODS:
        assert np.allclose(
            _weights(
                source,
                method,
            ),
            [1.0],
        )


def test_two_touch_semantics() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    ),
                    (
                        200,
                        2000,
                    ),
                ],
            )
        ]
    )

    assert np.allclose(
        _weights(
            source,
            "FIRST_TOUCH",
        ),
        [
            1.0,
            0.0,
        ],
    )

    assert np.allclose(
        _weights(
            source,
            "LAST_TOUCH",
        ),
        [
            0.0,
            1.0,
        ],
    )

    assert np.allclose(
        _weights(
            source,
            "LINEAR",
        ),
        [
            0.5,
            0.5,
        ],
    )

    assert np.allclose(
        _weights(
            source,
            "POSITION_BASED",
        ),
        [
            0.5,
            0.5,
        ],
    )

    decay = _weights(
        source,
        "TIME_DECAY",
    )

    assert np.isclose(
        decay.sum(),
        1.0,
    )

    assert decay[1] > decay[0]


def test_multi_touch_semantics() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    ),
                    (
                        200,
                        2000,
                    ),
                    (
                        300,
                        3000,
                    ),
                ],
            )
        ]
    )

    assert np.allclose(
        _weights(
            source,
            "FIRST_TOUCH",
        ),
        [
            1.0,
            0.0,
            0.0,
        ],
    )

    assert np.allclose(
        _weights(
            source,
            "LAST_TOUCH",
        ),
        [
            0.0,
            0.0,
            1.0,
        ],
    )

    assert np.allclose(
        _weights(
            source,
            "LINEAR",
        ),
        [
            1 / 3,
            1 / 3,
            1 / 3,
        ],
    )

    assert np.allclose(
        _weights(
            source,
            "POSITION_BASED",
        ),
        [
            0.4,
            0.2,
            0.4,
        ],
    )

    decay = _weights(
        source,
        "TIME_DECAY",
    )

    assert np.isclose(
        decay.sum(),
        1.0,
    )

    assert decay[2] > decay[1] > decay[0]


def test_four_touch_position_based() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                    (300, 3000),
                    (400, 4000),
                ],
            )
        ]
    )

    assert np.allclose(
        _weights(
            source,
            "POSITION_BASED",
        ),
        [
            0.4,
            0.1,
            0.1,
            0.4,
        ],
    )


def test_composite_key_handles_reused_conversion_id() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    )
                ],
            ),
            (
                20,
                1,
                [
                    (
                        200,
                        2000,
                    )
                ],
            ),
        ]
    )

    touches, metadata = reconstruct_journeys(
        source,
        expected_rows=None,
    )

    assert touches["journey_id"].nunique() == 2

    assert metadata["raw_unique_conversion_ids"] == 1

    assert metadata["real_conversion_events"] == 2


def test_same_user_same_timestamp_different_conversion_ids_stay_distinct() -> None:
    source = pd.DataFrame(
        {
            "timestamp": [
                100,
                100,
            ],
            "media_user_id": [
                10,
                10,
            ],
            "campaign": [
                1000,
                2000,
            ],
            "conversion": [
                1,
                1,
            ],
            "conversion_timestamp": [
                300,
                300,
            ],
            "conversion_id": [
                1,
                2,
            ],
            "click": [
                1,
                1,
            ],
            "cost": [
                0.1,
                0.1,
            ],
        }
    )

    touches, metadata = reconstruct_journeys(
        source,
        expected_rows=None,
    )

    assert touches["journey_id"].nunique() == 2

    assert metadata["real_conversion_events"] == 2


def test_composite_key_must_have_one_conversion_timestamp() -> None:
    source = pd.DataFrame(
        {
            "timestamp": [
                100,
                200,
            ],
            "media_user_id": [
                10,
                10,
            ],
            "campaign": [
                1000,
                2000,
            ],
            "conversion": [
                1,
                1,
            ],
            "conversion_timestamp": [
                300,
                400,
            ],
            "conversion_id": [
                1,
                1,
            ],
            "click": [
                1,
                1,
            ],
            "cost": [
                0.1,
                0.1,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="multiple conversion timestamps",
    ):
        reconstruct_journeys(
            source,
            expected_rows=None,
        )


def test_nonconverter_behavior() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    )
                ],
            )
        ],
        nonconverters=[
            (
                50,
                99,
                9000,
            ),
            (
                60,
                99,
                9001,
            ),
        ],
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    assert outputs.metadata["real_nonconverting_users"] == 1

    for method in ATTRIBUTION_METHODS:
        rows = outputs.attribution_comparison.loc[
            outputs.attribution_comparison["method"] == method
        ]

        assert np.isclose(
            rows["attributed_conversion_credit"].sum(),
            1.0,
        )


def test_weight_conservation() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            ),
            (
                11,
                2,
                [
                    (300, 3000),
                    (400, 4000),
                    (500, 5000),
                ],
            ),
        ]
    )

    touches = _touches(source)

    for method in ATTRIBUTION_METHODS:
        weights = attribution_weights(
            touches,
            method,
        )

        totals = (
            pd.Series(
                weights,
                index=touches.index,
            )
            .groupby(touches["journey_id"])
            .sum()
        )

        assert np.allclose(
            totals.to_numpy(dtype=float),
            1.0,
        )


def test_attributed_totals_reconcile_by_method() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            ),
            (
                11,
                2,
                [
                    (300, 2000),
                    (400, 3000),
                ],
            ),
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    totals = outputs.attribution_comparison.groupby("method")["attributed_conversion_credit"].sum()

    assert set(totals.index) == set(ATTRIBUTION_METHODS)

    assert np.allclose(
        totals.to_numpy(dtype=float),
        2.0,
    )


def test_campaign_shares_reconcile() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            ),
            (
                11,
                2,
                [
                    (300, 1000),
                    (400, 3000),
                ],
            ),
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    for method in ATTRIBUTION_METHODS:
        rows = outputs.attribution_comparison.loc[
            outputs.attribution_comparison["method"] == method
        ]

        assert np.isclose(
            rows["attributed_conversion_credit"].sum(),
            2.0,
        )

        assert np.isclose(
            rows["attribution_share"].sum(),
            1.0,
        )


def test_method_sensitivity_visible() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                    (300, 3000),
                ],
            )
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    sensitivity = outputs.attribution_method_sensitivity

    assert (sensitivity["method_credit_range"] > 0).any()

    assert (sensitivity["absolute_first_vs_last_shift"] > 0).any()


def test_first_vs_last_direction() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            )
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    sensitivity = outputs.attribution_method_sensitivity.set_index("campaign_id")

    assert (
        float(
            cast(
                Any,
                sensitivity.loc[
                    "1000",
                    "first_vs_last_shift",
                ],
            )
        )
        < 0
    )

    assert (
        float(
            cast(
                Any,
                sensitivity.loc[
                    "2000",
                    "first_vs_last_shift",
                ],
            )
        )
        > 0
    )


def test_lookback_fails_if_event_dropped() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    )
                ],
            )
        ]
    )

    source["conversion_timestamp"] = source["timestamp"] + 31 * 86_400

    with pytest.raises(
        ValueError,
        match="lookback drops",
    ):
        reconstruct_journeys(
            source,
            expected_rows=None,
        )


def test_post_conversion_touch_fails() -> None:
    source = pd.DataFrame(
        {
            "timestamp": [400],
            "media_user_id": [10],
            "campaign": [1000],
            "conversion": [1],
            "conversion_timestamp": [300],
            "conversion_id": [1],
            "click": [1],
            "cost": [0.1],
        }
    )

    with pytest.raises(
        ValueError,
        match="after conversion",
    ):
        reconstruct_journeys(
            source,
            expected_rows=None,
        )


def test_source_attribution_field_not_required() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            )
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    assert "not used" in str(outputs.metadata["source_attribution_field_policy"])


def test_explicit_noncausal_boundary() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            )
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    assert outputs.metadata["causal_interpretation"] == CAUSAL_INTERPRETATION

    assert outputs.attribution_comparison["causal_interpretation"].eq(CAUSAL_INTERPRETATION).all()

    assert "randomized incrementality" in str(outputs.metadata["causal_separation_policy"])


def test_synthetic_fixture_policy() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (
                        100,
                        1000,
                    )
                ],
            )
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    assert outputs.metadata["synthetic_recruiter_facing_rows"] == 0

    assert "test-only" in str(outputs.metadata["synthetic_fixture_policy"])


def test_determinism() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 2000),
                ],
            ),
            (
                11,
                2,
                [
                    (300, 2000),
                    (400, 3000),
                ],
            ),
        ]
    )

    first = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    second = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    assert stable_frame_hash(first.attribution_comparison) == stable_frame_hash(
        second.attribution_comparison
    )

    assert stable_frame_hash(first.attribution_method_sensitivity) == stable_frame_hash(
        second.attribution_method_sensitivity
    )


def test_same_campaign_multitouch_has_measured_zero_sensitivity() -> None:
    source = _source(
        [
            (
                10,
                1,
                [
                    (100, 1000),
                    (200, 1000),
                    (300, 1000),
                ],
            )
        ]
    )

    outputs = build_attribution_outputs(
        source,
        expected_rows=None,
    )

    sensitivity = outputs.attribution_method_sensitivity

    assert outputs.metadata["multi_touch_journeys"] == 1

    assert outputs.metadata["same_campaign_multi_touch_journeys"] == 1

    assert outputs.metadata["cross_campaign_journeys"] == 0

    assert outputs.metadata["campaigns_with_method_sensitivity"] == 0

    assert outputs.metadata["campaigns_with_first_last_shift"] == 0

    assert outputs.metadata["method_sensitivity_status"] == "MEASURED_ZERO_NO_CROSS_CAMPAIGN_PATHS"

    assert outputs.metadata["method_sensitivity_policy"] == "MEASURED_NOT_REQUIRED_NONZERO"

    assert np.allclose(
        sensitivity["method_credit_range"].to_numpy(dtype=float),
        0.0,
    )

    assert np.allclose(
        sensitivity["absolute_first_vs_last_shift"].to_numpy(dtype=float),
        0.0,
    )

    assert (
        sensitivity["method_sensitivity_status"].eq("MEASURED_ZERO_NO_CROSS_CAMPAIGN_PATHS").all()
    )

    for method in ATTRIBUTION_METHODS:
        rows = outputs.attribution_comparison.loc[
            outputs.attribution_comparison["method"] == method
        ]

        assert np.isclose(
            rows["attributed_conversion_credit"].sum(),
            1.0,
        )
