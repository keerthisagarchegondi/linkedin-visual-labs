"""Machine-readable schema vocabulary for Project 8."""

from __future__ import annotations

from typing import Final

CLAIM_CLASSES: Final[tuple[str, ...]] = (
    "SOURCE_REPORTED",
    "REPLICATED_COMPUTATION",
    "MONTE_CARLO_ESTIMATE",
    "MATHEMATICAL_DERIVATION",
    "INTERPRETATION",
    "LIMITATION",
    "FUTURE_WORK",
    "UNSUPPORTED",
)

SOFTWARE_STATES: Final[tuple[str, ...]] = (
    "DRAFT",
    "VALIDATED",
    "RELEASED",
    "ARCHIVED",
)

MANUSCRIPT_STATES: Final[tuple[str, ...]] = (
    "DRAFT",
    "READY_FOR_REVIEW",
    "SUBMITTED",
    "UNDER_REVIEW",
    "REVISION_REQUIRED",
    "ACCEPTED",
    "PUBLISHED",
    "REJECTED",
    "WITHDRAWN",
)

SOCIAL_STATES: Final[tuple[str, ...]] = (
    "DRAFT",
    "APPROVED",
    "POSTED",
)

CITATION_STATES: Final[tuple[str, ...]] = (
    "NOT_CHECKED",
    "CHECKED_NO_VERIFIED_MATCH",
    "VERIFIED_MATCHES",
)
