from __future__ import annotations

import pandas as pd

from linkedin_visual_labs.projects.p25_retail_media_audience_decision.recommendation_engine import (
    ACTIVATION_MIN_AUDIENCE_SIZE,
    CAUSAL_DOMAIN,
    FUNNEL_DOMAIN,
    MEDIA_DOMAIN,
    PRIVACY_MIN_AUDIENCE_SIZE,
    RETAIL_DOMAIN,
    DecisionEvidence,
    build_evidence_trace,
    classify_recommendation,
    recommendations_frame,
    validate_recommendations,
)


def _evidence(
    *,
    recommendation_id: str = "R1",
    evidence_domain: str = CAUSAL_DOMAIN,
    audience_size: int = 1000,
    causal: bool = True,
    randomized: bool = True,
    effect: float | None = 0.03,
    lower: float | None = 0.01,
    upper: float | None = 0.05,
    uplift: float | None = 0.02,
    top20: float | None = 0.05,
    customer_value: bool = False,
    attribution: bool = False,
    raw_response: bool = False,
) -> DecisionEvidence:
    return DecisionEvidence(
        recommendation_id=recommendation_id,
        evidence_domain=evidence_domain,
        audience_id="A1",
        audience_name="Audience 1",
        audience_size=audience_size,
        evidence_class="TEST_EVIDENCE",
        causal_evidence_present=causal,
        randomized_evidence_present=randomized,
        incremental_effect=effect,
        confidence_level=0.95,
        ci_lower=lower,
        ci_upper=upper,
        uplift_score=uplift,
        top20_uplift_score=top20,
        customer_value_signal=customer_value,
        category_opportunity_signal=False,
        lapsed_opportunity_signal=False,
        promotion_sensitive_signal=False,
        attribution_credit_signal=attribution,
        raw_response_signal=raw_response,
        source_artifact="test",
        source_record="row-1",
    )


def test_positive_causal_and_uplift_can_scale() -> None:
    result = classify_recommendation(_evidence())

    assert result.next_action == "SCALE"
    assert result.recommendation_class == "MEASURED_RECOMMENDATION"


def test_negative_causal_and_uplift_can_suppress() -> None:
    result = classify_recommendation(
        _evidence(
            effect=-0.03,
            lower=-0.05,
            upper=-0.01,
            uplift=-0.02,
            top20=-0.01,
        )
    )

    assert result.next_action == "SUPPRESS"
    assert result.recommendation_class == "SUPPRESSION_RECOMMENDED"


def test_inconclusive_causal_evidence_retests() -> None:
    result = classify_recommendation(
        _evidence(
            effect=0.01,
            lower=-0.01,
            upper=0.03,
        )
    )

    assert result.next_action == "RETEST"
    assert result.recommendation_class == "HOLDOUT_RECOMMENDED"


def test_high_value_retail_alone_cannot_scale() -> None:
    result = classify_recommendation(
        _evidence(
            evidence_domain=RETAIL_DOMAIN,
            causal=False,
            randomized=False,
            effect=None,
            lower=None,
            upper=None,
            uplift=None,
            top20=None,
            customer_value=True,
        )
    )

    assert result.next_action == "RETEST"
    assert result.recommendation_class == "ACTIVATION_HYPOTHESIS"


def test_attribution_cannot_become_causal_action() -> None:
    result = classify_recommendation(
        _evidence(
            evidence_domain=MEDIA_DOMAIN,
            causal=False,
            randomized=False,
            effect=None,
            lower=None,
            upper=None,
            uplift=None,
            top20=None,
            attribution=True,
        )
    )

    assert result.next_action == "INVESTIGATE"
    assert not result.causal_evidence_present


def test_funnel_response_cannot_become_causal_action() -> None:
    result = classify_recommendation(
        _evidence(
            evidence_domain=FUNNEL_DOMAIN,
            causal=False,
            randomized=False,
            effect=None,
            lower=None,
            upper=None,
            uplift=None,
            top20=None,
            raw_response=True,
        )
    )

    assert result.next_action == "INVESTIGATE"
    assert not result.causal_evidence_present


def test_privacy_threshold_blocks_activation() -> None:
    result = classify_recommendation(_evidence(audience_size=(PRIVACY_MIN_AUDIENCE_SIZE - 1)))

    assert result.recommendation_class == "INSUFFICIENT_EVIDENCE"

    assert result.next_action == "INVESTIGATE"


def test_activation_size_blocks_scale() -> None:
    result = classify_recommendation(_evidence(audience_size=(ACTIVATION_MIN_AUDIENCE_SIZE - 1)))

    assert result.next_action == "INVESTIGATE"
    assert not result.activation_size_pass


def test_trace_forbids_cross_source_join_claim() -> None:
    evidence = [_evidence()]

    recommendations = recommendations_frame(evidence)

    trace = build_evidence_trace(
        evidence,
        recommendations,
    )

    assert not trace["cross_source_identity_join"].any()

    assert not trace["cross_source_row_join"].any()


def test_deterministic_next_action() -> None:
    evidence = [
        _evidence(recommendation_id="R2"),
        _evidence(
            recommendation_id="R1",
            evidence_domain=RETAIL_DOMAIN,
            causal=False,
            randomized=False,
            effect=None,
            lower=None,
            upper=None,
            uplift=None,
            top20=None,
        ),
    ]

    first = recommendations_frame(evidence)

    second = recommendations_frame(list(reversed(evidence)))

    pd.testing.assert_frame_equal(
        first,
        second,
    )


def test_global_guard_rejects_noncausal_scale() -> None:
    frame = pd.DataFrame(
        [
            {
                "recommendation_id": "BAD",
                "evidence_domain": MEDIA_DOMAIN,
                "audience_id": "M1",
                "audience_name": "Media",
                "audience_size": 1000,
                "recommendation_class": "MEASURED_RECOMMENDATION",
                "next_action": "SCALE",
                "causal_evidence_present": False,
                "incremental_effect": None,
                "ci_lower": None,
                "ci_upper": None,
                "uplift_score": None,
                "privacy_threshold_pass": True,
                "activation_size_pass": True,
                "confidence_threshold_pass": False,
                "recommendation_reason": "bad",
                "guardrail_reason": "bad",
                "source_artifact": "test",
                "source_record": "test",
                "deterministic_priority": 1,
            }
        ]
    )

    try:
        validate_recommendations(frame)
    except ValueError:
        return

    raise AssertionError("Noncausal Scale should have been rejected.")
