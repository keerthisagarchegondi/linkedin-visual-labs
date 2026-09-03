"""Deterministic source provenance manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.models import (
    EvidenceClass,
    SourceId,
)
from linkedin_visual_labs.projects.p25_retail_media_audience_decision.source_adapters.base import (
    canonical_schema_fingerprint,
    sha256_file,
)


def write_provenance(
    *,
    path: Path,
    source_id: SourceId,
    evidence_class: EvidenceClass,
    publisher_source: str,
    transport_source: str,
    normalized_files: list[Path],
    frames: list[pd.DataFrame],
    raw_files: list[Path],
    license_or_terms: str,
) -> Path:
    """Write deterministic provenance without host-specific paths."""

    if len(normalized_files) != len(frames):
        raise ValueError("normalized_files and frames must have equal length")

    normalized = []

    for normalized_file, frame in zip(
        normalized_files,
        frames,
        strict=True,
    ):
        normalized.append(
            {
                "filename": normalized_file.name,
                "row_count": len(frame),
                "schema_fingerprint": canonical_schema_fingerprint(frame),
                "sha256": sha256_file(normalized_file),
            }
        )

    raw = [
        {
            "filename": raw_file.name,
            "sha256": sha256_file(raw_file),
        }
        for raw_file in raw_files
        if raw_file.is_file()
    ]

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "source_id": source_id.value,
        "evidence_class": evidence_class.value,
        "publisher_source": publisher_source,
        "transport_source": transport_source,
        "license_or_terms": license_or_terms,
        "raw_files": raw,
        "normalized_files": normalized,
        "raw_redistribution": False,
        "cross_source_identity_join_allowed": False,
    }

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_name(f".{path.name}.tmp")

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    temporary.replace(path)

    return path


def validate_provenance(
    path: Path,
) -> dict[str, Any]:
    """Validate a source provenance manifest."""

    payload: Any = json.loads(
        path.read_text(
            encoding="utf-8",
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(f"Invalid provenance root: {path}")

    required = {
        "schema_version",
        "source_id",
        "evidence_class",
        "publisher_source",
        "transport_source",
        "license_or_terms",
        "normalized_files",
        "raw_redistribution",
        "cross_source_identity_join_allowed",
    }

    missing = sorted(required - set(payload))

    if missing:
        raise ValueError(f"Provenance missing fields: {missing}")

    if payload["raw_redistribution"] is not False:
        raise ValueError("Raw redistribution must remain disabled.")

    if payload["cross_source_identity_join_allowed"] is not False:
        raise ValueError("Cross-source identity joins must remain disabled.")

    return payload
