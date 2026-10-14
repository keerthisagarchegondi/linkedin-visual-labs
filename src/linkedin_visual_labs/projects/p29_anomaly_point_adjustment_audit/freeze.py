"""Deterministic transformation of Project 9 prefreeze evidence into frozen release data."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import PROJECT_ID, load_default_config, repository_root
from .experiment import PREFREEZE_STATUS, frozen_conditions, prefreeze_path

RELEASE_SCHEMA_VERSION = "p29-release-data-v1"


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON document must be an object")
    return value


def _finite(value: object) -> bool:
    if isinstance(value, float):
        return value == value and value not in (float("inf"), float("-inf"))
    if isinstance(value, dict):
        return all(_finite(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite(item) for item in value)
    return True


def release_paths() -> tuple[Path, Path, Path]:
    root = repository_root() / "outputs" / PROJECT_ID
    return (
        root / "data" / "release_data.json",
        root / "manifests" / "claim_register.json",
        root / "manifests" / "scientific_freeze_receipt.json",
    )


def build_release_data() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load and reconcile prefreeze data without rerunning the experiment."""
    config = load_default_config()
    input_path = prefreeze_path() / "PREFREEZE_condition_summaries.json"
    prefreeze = _read_json(input_path)
    conditions = prefreeze.get("conditions")
    if prefreeze.get("status") != PREFREEZE_STATUS or not isinstance(conditions, list):
        raise ValueError("prefreeze artifact is not a valid Project 9 prefreeze payload")
    expected = frozen_conditions(config)
    if len(conditions) != 45 or {item.condition_id for item in expected} != {
        item.get("condition_id") for item in conditions if isinstance(item, dict)
    }:
        raise ValueError("prefreeze condition grid does not match the frozen design")
    if not _finite(prefreeze) or any(
        item.get("repetitions") != 2000 for item in conditions if isinstance(item, dict)
    ):
        raise ValueError("prefreeze values must be finite and retain 2,000 repetitions")
    primary = [
        item for item in conditions if item.get("event_length") == 200 and item.get("q") == 0.01
    ]
    if len(primary) != 1:
        raise ValueError("frozen primary condition must occur exactly once")
    q_slice = [item for item in conditions if item.get("q") == 0.01]
    if len(q_slice) != 9:
        raise ValueError("q=0.01 event-length slice is incomplete")
    input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    release: dict[str, Any] = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "project_id": PROJECT_ID,
        "experiment_version": config.experiment_version,
        "scientific_results_status": "FROZEN",
        "release_data_status": "FROZEN",
        "prefreeze_input_sha256": input_hash,
        "condition_summaries": conditions,
        "primary_condition": primary[0],
        "event_length_sweep_q_0_01": q_slice,
        "formatting_policy": {"f1_decimal_places": 3, "probability_percent_decimal_places": 1},
        "limitations_reference": "claim_register.json",
    }
    claims = _claims(release)
    receipt = {
        "project_id": PROJECT_ID,
        "freeze_status": "FROZEN",
        "prefreeze_input_sha256": input_hash,
        "release_data_sha256": _canonical_hash(release),
        "claim_register_sha256": _canonical_hash(claims),
        "source_discrepancy_status": "UNRESOLVED",
        "publication_scope_status": "EDITORIAL_SCOPE_CHECK_NEEDED",
    }
    return release, claims, receipt


def _claims(release: dict[str, Any]) -> dict[str, Any]:
    primary = release["primary_condition"]
    assert isinstance(primary, dict)
    approved = [
        {
            "claim_id": "P9-C001",
            "claim_class": "MONTE_CARLO_ESTIMATE",
            "statement": (
                "Primary-condition paired raw and adjusted F1 values are frozen in release data."
            ),
            "condition_ids": [primary["condition_id"]],
            "public_release_allowed": True,
            "validation_status": "PASS",
        },
        {
            "claim_id": "P9-C002",
            "claim_class": "MATHEMATICAL_DERIVATION",
            "statement": (
                "Event-hit probability increases with event length under the declared "
                "Bernoulli model."
            ),
            "public_release_allowed": True,
            "validation_status": "PASS",
        },
    ]
    limitations = [
        "synthetic anomaly labels",
        "random scores are label-independent",
        "no trained detector is evaluated in version 1",
        "does not show random guessing outperforms modern anomaly systems",
        "does not establish all event-aware metrics are invalid",
        "Monte Carlo uncertainty describes this synthetic model only",
        "partial replication",
        "source Eq. 6\u20137 ambiguity remains unresolved",
        "point adjustment retrospectively uses ground-truth event boundaries",
    ]
    blocked = [
        "I discovered point-adjustment inflation.",
        "Random beats AI.",
        "Random beats state-of-the-art anomaly detectors.",
        "All anomaly metrics are broken.",
        "All event-aware metrics are invalid.",
        "This proves production anomaly systems are misleading.",
        "This project is peer reviewed.",
        "This project is published.",
    ]
    return {
        "schema_version": "p29-claim-register-v1",
        "project_id": PROJECT_ID,
        "approved_claims": approved,
        "limitation_claims": [
            {
                "claim_id": f"P9-L{index:03d}",
                "claim_class": "LIMITATION",
                "statement": text,
                "public_release_allowed": True,
            }
            for index, text in enumerate(limitations, 1)
        ],
        "blocked_claims": [
            {
                "claim_id": f"P9-U{index:03d}",
                "claim_class": "UNSUPPORTED",
                "statement": text,
                "public_release_allowed": False,
            }
            for index, text in enumerate(blocked, 1)
        ],
    }


def freeze_results() -> dict[str, str]:
    release, claims, receipt = build_release_data()
    release_path, claims_path, receipt_path = release_paths()
    for path, value in ((release_path, release), (claims_path, claims), (receipt_path, receipt)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "release_data": str(release_path),
        "release_data_sha256": _canonical_hash(release),
        "claim_register": str(claims_path),
        "claim_register_sha256": _canonical_hash(claims),
    }
