"""Generic ingestion contract tests."""

from __future__ import annotations

import pandas as pd
import pytest

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    canonical_schema_fingerprint,
    ensure_no_generic_identity,
    ensure_no_pii_columns,
    stable_sort,
)


def test_schema_fingerprint_is_deterministic() -> None:
    frame = pd.DataFrame(
        {
            "source_specific_id": [2, 1],
            "value": [3.0, 4.0],
        }
    )

    assert canonical_schema_fingerprint(frame) == canonical_schema_fingerprint(frame.copy())


def test_generic_identity_is_rejected() -> None:
    frame = pd.DataFrame(
        {
            "customer_id": [1],
        }
    )

    with pytest.raises(
        ValueError,
        match="Generic cross-source identity",
    ):
        ensure_no_generic_identity(frame)


def test_pii_column_is_rejected() -> None:
    frame = pd.DataFrame(
        {
            "email_address": ["hidden@example.invalid"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Potential PII",
    ):
        ensure_no_pii_columns(frame)


def test_stable_sort_is_order_independent() -> None:
    left = pd.DataFrame(
        {
            "id": [3, 1, 2],
            "value": ["c", "a", "b"],
        }
    )

    right = left.sample(
        frac=1.0,
        random_state=91,
    )

    expected = stable_sort(
        left,
        ["id"],
    )

    actual = stable_sort(
        right,
        ["id"],
    )

    pd.testing.assert_frame_equal(
        actual,
        expected,
    )
