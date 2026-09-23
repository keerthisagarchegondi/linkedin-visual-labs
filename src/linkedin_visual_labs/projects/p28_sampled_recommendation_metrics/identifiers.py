"""Stable Project 8 experiment and evidence identifiers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def canonical_json(value: Mapping[str, Any]) -> str:
    """Serialize mapping deterministically for stable fingerprints."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def stable_fingerprint(value: Mapping[str, Any]) -> str:
    """Return a stable SHA-256 fingerprint for a mapping."""
    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def experiment_id(
    *,
    experiment_kind: str,
    protocol: Mapping[str, Any],
) -> str:
    """Create a stable experiment identifier."""
    if not experiment_kind or experiment_kind.strip() != experiment_kind:
        raise ValueError("experiment_kind must be a non-empty stripped string")

    digest = stable_fingerprint(
        {
            "experiment_kind": experiment_kind,
            "protocol": protocol,
        }
    )[:16]

    return f"p28-exp-{experiment_kind}-{digest}"


def evidence_id(
    *,
    evidence_kind: str,
    payload: Mapping[str, Any],
) -> str:
    """Create a stable evidence identifier."""
    if not evidence_kind or evidence_kind.strip() != evidence_kind:
        raise ValueError("evidence_kind must be a non-empty stripped string")

    digest = stable_fingerprint(
        {
            "evidence_kind": evidence_kind,
            "payload": payload,
        }
    )[:16]

    return f"p28-evidence-{evidence_kind}-{digest}"
