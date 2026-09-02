"""Typed shared contracts for Project 4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SourceId(StrEnum):
    """Supported Project 4 evidence sources."""

    DUNNHUMBY = "dunnhumby_complete_journey"
    HILLSTROM = "hillstrom"
    CRITEO = "criteo_attribution"
    RETAILROCKET = "retailrocket"
    SYNTHETIC_FIXTURE = "synthetic_attribution_fixture"


class EvidenceClass(StrEnum):
    """Evidence classes that remain analytically separate."""

    RETAIL_BEHAVIOR = "RETAIL CUSTOMER BEHAVIOR"
    RANDOMIZED_EXPERIMENT = "REAL RANDOMIZED EXPERIMENT"
    MEDIA_ATTRIBUTION = "MEDIA ATTRIBUTION"
    BEHAVIORAL_FUNNEL = "BEHAVIORAL FUNNEL"
    TEST_FIXTURE = "TEST FIXTURE ONLY"


class NextAction(StrEnum):
    """Governed decision-engine actions."""

    SCALE = "Scale"
    RETEST = "Retest"
    MAINTAIN_HOLDOUT = "Maintain Holdout"
    SUPPRESS = "Suppress"
    INVESTIGATE = "Investigate"


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Minimal provenance contract shared by source adapters."""

    source_id: SourceId
    evidence_class: EvidenceClass
    schema_version: str
    raw_redistribution_allowed: bool
