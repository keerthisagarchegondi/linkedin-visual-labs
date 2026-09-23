from __future__ import annotations

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.schemas import (
    CITATION_STATES,
    CLAIM_CLASSES,
    MANUSCRIPT_STATES,
    SOCIAL_STATES,
    SOFTWARE_STATES,
)


def test_schema_vocabularies_match_frozen_contract() -> None:
    assert "SOURCE_REPORTED" in CLAIM_CLASSES
    assert "REPLICATED_COMPUTATION" in CLAIM_CLASSES
    assert "MATHEMATICAL_DERIVATION" in CLAIM_CLASSES
    assert "UNSUPPORTED" in CLAIM_CLASSES

    assert SOFTWARE_STATES == (
        "DRAFT",
        "VALIDATED",
        "RELEASED",
        "ARCHIVED",
    )

    assert "PUBLISHED" in MANUSCRIPT_STATES
    assert SOCIAL_STATES == (
        "DRAFT",
        "APPROVED",
        "POSTED",
    )

    assert CITATION_STATES == (
        "NOT_CHECKED",
        "CHECKED_NO_VERIFIED_MATCH",
        "VERIFIED_MATCHES",
    )
