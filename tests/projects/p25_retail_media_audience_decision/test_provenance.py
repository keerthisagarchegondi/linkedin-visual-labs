"""Provenance and cache-integrity tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    EvidenceClass,
    SourceId,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.provenance import (
    validate_provenance,
    write_provenance,
)


def test_provenance_round_trip(
    tmp_path: Path,
) -> None:
    frame = pd.DataFrame(
        {
            "anonymous_customer_id": [
                "a",
                "b",
            ],
            "value": [
                1,
                2,
            ],
        }
    )

    normalized = tmp_path / "hillstrom.parquet"

    frame.to_parquet(
        normalized,
        index=False,
    )

    manifest = write_provenance(
        path=(tmp_path / "hillstrom.json"),
        source_id=SourceId.HILLSTROM,
        evidence_class=EvidenceClass.RANDOMIZED_EXPERIMENT,
        publisher_source="fixture",
        transport_source="fixture",
        normalized_files=[
            normalized,
        ],
        frames=[
            frame,
        ],
        raw_files=[],
        license_or_terms="fixture only",
    )

    payload = validate_provenance(manifest)

    assert payload["raw_redistribution"] is False
    assert payload["cross_source_identity_join_allowed"] is False
