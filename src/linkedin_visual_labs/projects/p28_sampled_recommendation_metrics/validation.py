"""Project 8 Step-1 validation."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import Project8Config, load_default_config
from .reference import ReferenceProtocol, load_reference_protocol

EXPECTED_PROFILES = {
    "A": (100, 100, 100, 100, 100),
    "B": (40, 40, 8437, 9266, 4482),
    "C": (212, 2, 743, 5342, 1548),
}


def validate_config(
    config: Project8Config,
) -> list[str]:
    findings: list[str] = []

    if config.n_items != 10_000:
        findings.append("n_items must equal the frozen source value 10000")

    if config.reference_negative_draws != 99:
        findings.append("reference negative draws must equal 99")

    if config.root_seed != 20260923:
        findings.append("root seed differs from the frozen Step-0 value")

    expected_grid = (
        1,
        2,
        5,
        10,
        20,
        50,
        99,
        200,
        500,
        1000,
        5000,
        9999,
    )

    if config.sensitivity_grid_negative_draws != expected_grid:
        findings.append("sensitivity grid differs from the frozen contract")

    return findings


def validate_reference(
    reference: ReferenceProtocol,
) -> list[str]:
    findings: list[str] = []

    if reference.profiles != EXPECTED_PROFILES:
        findings.append("reference profiles differ from the source-verified values")

    return findings


def validate_inputs() -> dict[str, Any]:
    config = load_default_config()
    reference = load_reference_protocol(config=config)

    findings = validate_config(config) + validate_reference(reference)

    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "config": asdict(config),
        "reference": {
            "n_items": reference.n_items,
            "reference_negative_draws": (reference.reference_negative_draws),
            "profiles": {key: list(value) for key, value in reference.profiles.items()},
        },
    }


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]
