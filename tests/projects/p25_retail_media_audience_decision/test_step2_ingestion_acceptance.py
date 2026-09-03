"""Step 2 ingestion acceptance tests that complement source-specific tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from linkedin_visual_labs.cli import app
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    EvidenceClass,
    SourceId,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.provenance import (
    write_provenance,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters import (
    criteo,
    dunnhumby,
    hillstrom,
    retailrocket,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    canonical_schema_fingerprint,
    download_file,
    ensure_no_generic_identity,
    ensure_no_pii_columns,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.validation import (
    validate_source_specific_identity,
)

runner = CliRunner()


def _hillstrom_frames() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.Series[str],
]:
    features = pd.DataFrame(
        {
            "recency": [1, 3, 2],
            "history": [100.0, 50.0, 200.0],
            "history_segment": [
                "100-200",
                "50-100",
                "200-350",
            ],
            "mens": [1, 1, 0],
            "womens": [0, 1, 1],
            "zip_code": [
                "Urban",
                "Rural",
                "Suburban",
            ],
            "newbie": [0, 0, 1],
            "channel": [
                "Web",
                "Multichannel",
                "Phone",
            ],
        }
    )

    targets = pd.DataFrame(
        {
            "visit": [1, 1, 0],
            "conversion": [1, 0, 0],
            "spend": [25.0, 0.0, 0.0],
        }
    )

    treatment = pd.Series(
        [
            "Mens E-Mail",
            "No E-Mail",
            "Womens E-Mail",
        ],
        dtype="string",
    )

    return features, targets, treatment


def _dunnhumby_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "household_key": [2, 1],
            "BASKET_ID": [20, 10],
            "DAY": [2, 1],
            "PRODUCT_ID": [200, 100],
            "QUANTITY": [1, 2],
            "SALES_VALUE": [5.5, 10.0],
            "STORE_ID": [1, 1],
            "RETAIL_DISC": [0.0, -1.0],
            "TRANS_TIME": [1200, 1100],
            "WEEK_NO": [1, 1],
            "COUPON_DISC": [0.0, 0.0],
        }
    )


def _criteo_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [3, 1, 2],
            "uid": [30, 10, 20],
            "campaign": [300, 100, 200],
            "conversion": [0, 1, 0],
            "conversion_timestamp": [-1, 5, -1],
            "conversion_id": [-1, 99, -1],
            "attribution": [0, 1, 0],
            "click": [0, 1, 0],
            "click_pos": [0, 0, 0],
            "click_nb": [0, 1, 0],
            "cost": [0.2, 0.5, 0.3],
            "cpo": [0.0, 1.0, 0.0],
            "time_since_last_click": [-1, 0, -1],
            "cat1": ["A", "B", "C"],
        }
    )


def _retailrocket_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [
                1433221332117,
                1433221332118,
                1433221332119,
            ],
            "visitorid": [1, 1, 1],
            "event": [
                "view",
                "addtocart",
                "transaction",
            ],
            "itemid": [100, 100, 100],
            "transactionid": [
                None,
                None,
                999,
            ],
        }
    )


def test_2_51_and_2_52_cli_contracts() -> None:
    help_result = runner.invoke(
        app,
        [
            "retail-media",
            "--help",
        ],
    )

    assert help_result.exit_code == 0
    assert "fetch-data" in help_result.stdout
    assert "validate-data" in help_result.stdout


def test_2_53_four_source_fixtures_normalize() -> None:
    features, targets, treatment = _hillstrom_frames()

    hillstrom_frame = hillstrom.normalize_hillstrom(
        features,
        targets,
        treatment,
    )

    dunnhumby_frame = dunnhumby.normalize_transactions(_dunnhumby_frame())

    criteo_frame = criteo.normalize_criteo_chunk(_criteo_frame())

    retailrocket_frame = retailrocket.normalize_events(_retailrocket_frame())

    assert len(hillstrom_frame) == 3
    assert len(dunnhumby_frame) == 2
    assert len(criteo_frame) == 3
    assert len(retailrocket_frame) == 3


def test_2_54_missing_columns_are_rejected() -> None:
    features, targets, treatment = _hillstrom_frames()

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        hillstrom.normalize_hillstrom(
            features.drop(columns=["history"]),
            targets,
            treatment,
        )

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        criteo.normalize_criteo_chunk(_criteo_frame().drop(columns=["click"]))

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        retailrocket.normalize_events(_retailrocket_frame().drop(columns=["event"]))


def test_2_55_invalid_domains_are_rejected() -> None:
    bad_criteo = _criteo_frame()
    bad_criteo.loc[
        bad_criteo.index[0],
        "click",
    ] = 2

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        criteo.normalize_criteo_chunk(bad_criteo)

    bad_retailrocket = _retailrocket_frame()
    bad_retailrocket.loc[
        bad_retailrocket.index[0],
        "event",
    ] = "unknown"

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        retailrocket.normalize_events(bad_retailrocket)


def test_2_56_corrupted_normalized_file_breaks_provenance(
    tmp_path: Path,
) -> None:
    from linkedin_visual_labs.projects.p25_retail_media_audience_decision.validation import (
        validate_source_provenance,
    )

    normalized = tmp_path / "hillstrom.parquet"
    raw = tmp_path / "raw.csv"
    manifest = tmp_path / "provenance.json"

    frame = pd.DataFrame(
        {
            "value": [1, 2],
        }
    )

    frame.to_parquet(
        normalized,
        index=False,
    )

    raw.write_text(
        "value\n1\n2\n",
        encoding="utf-8",
    )

    write_provenance(
        path=manifest,
        source_id=SourceId.HILLSTROM,
        evidence_class=EvidenceClass.RANDOMIZED_EXPERIMENT,
        publisher_source="test fixture",
        transport_source="test fixture",
        normalized_files=[normalized],
        frames=[frame],
        raw_files=[raw],
        license_or_terms="test only",
    )

    validate_source_provenance(
        provenance_path=manifest,
        normalized_root=tmp_path,
    )

    with normalized.open("ab") as handle:
        handle.write(b"corruption")

    with pytest.raises(
        (
            ValueError,
            RuntimeError,
            OSError,
            AssertionError,
            KeyError,
        )
    ):
        validate_source_provenance(
            provenance_path=manifest,
            normalized_root=tmp_path,
        )


def test_2_57_hillstrom_normalization_is_order_independent() -> None:
    features, targets, treatment = _hillstrom_frames()

    first = hillstrom.normalize_hillstrom(
        features,
        targets,
        treatment,
    )

    order = [
        2,
        0,
        1,
    ]

    second = hillstrom.normalize_hillstrom(
        features.iloc[order].reset_index(drop=True),
        targets.iloc[order].reset_index(drop=True),
        treatment.iloc[pd.Index(order)].reset_index(drop=True),
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_2_57_criteo_sampling_is_deterministic() -> None:
    raw = _criteo_frame()

    normalized_first = criteo.normalize_criteo_chunk(raw.copy(deep=True))

    normalized_second = criteo.normalize_criteo_chunk(raw.copy(deep=True))

    pd.testing.assert_frame_equal(
        normalized_first,
        normalized_second,
    )

    first = criteo._deterministic_keep_mask(
        normalized_first.copy(deep=True),
        max_rows=2,
    )

    second = criteo._deterministic_keep_mask(
        normalized_second.copy(deep=True),
        max_rows=2,
    )

    pd.testing.assert_series_equal(
        first,
        second,
        check_dtype=True,
        check_names=True,
        check_exact=True,
    )

    third = criteo._deterministic_keep_mask(
        normalized_first.copy(deep=True),
        max_rows=1,
    )

    fourth = criteo._deterministic_keep_mask(
        normalized_second.copy(deep=True),
        max_rows=1,
    )

    pd.testing.assert_series_equal(
        third,
        fourth,
        check_dtype=True,
        check_names=True,
        check_exact=True,
    )


def test_2_57_four_schemas_remain_source_specific() -> None:
    features, targets, treatment = _hillstrom_frames()

    frames = [
        hillstrom.normalize_hillstrom(
            features,
            targets,
            treatment,
        ),
        dunnhumby.normalize_transactions(_dunnhumby_frame()),
        criteo.normalize_criteo_chunk(_criteo_frame()),
        retailrocket.normalize_events(_retailrocket_frame()),
    ]

    fingerprints = {canonical_schema_fingerprint(frame) for frame in frames}

    assert len(fingerprints) == 4


def test_2_58_pii_columns_are_rejected() -> None:
    frame = pd.DataFrame(
        {
            "email": [
                "test@example.invalid",
            ],
        }
    )

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        ensure_no_pii_columns(frame)


def test_2_59_generic_identity_is_rejected() -> None:
    frame = pd.DataFrame(
        {
            "customer_id": [
                "1",
            ],
        }
    )

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        ensure_no_generic_identity(frame)


def test_2_59_cross_source_identity_validation_rejects_generic_ids() -> None:
    frames = {
        "hillstrom": pd.DataFrame(
            {
                "customer_id": [
                    "same-id",
                ],
            }
        ),
        "criteo": pd.DataFrame(
            {
                "customer_id": [
                    "same-id",
                ],
            }
        ),
    }

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        validate_source_specific_identity(frames)


def test_no_fabricated_offline_download_fallback(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "missing.bin"

    with pytest.raises((ValueError, RuntimeError, TypeError, FileNotFoundError, OSError, KeyError)):
        download_file(
            "https://example.invalid/missing.bin",
            destination,
            offline=True,
        )
