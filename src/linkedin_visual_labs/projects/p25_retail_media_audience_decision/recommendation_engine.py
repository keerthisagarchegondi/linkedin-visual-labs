"""Governed recommendation engine for Project 4 Step 8."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Final, cast

import pandas as pd

PRIVACY_MIN_AUDIENCE_SIZE: Final[int] = 100
ACTIVATION_MIN_AUDIENCE_SIZE: Final[int] = 500
CAUSAL_CONFIDENCE_LEVEL: Final[float] = 0.95

RANDOM_SEED: Final[int] = 20260904


RECOMMENDATION_CLASSES: Final[tuple[str, ...]] = (
    "MEASURED_RECOMMENDATION",
    "ACTIVATION_HYPOTHESIS",
    "INSUFFICIENT_EVIDENCE",
    "HOLDOUT_RECOMMENDED",
    "SUPPRESSION_RECOMMENDED",
)


NEXT_ACTIONS: Final[tuple[str, ...]] = (
    "SCALE",
    "RETEST",
    "MAINTAIN_HOLDOUT",
    "SUPPRESS",
    "INVESTIGATE",
)


CAUSAL_DOMAIN: Final[str] = "HILLSTROM_RANDOMIZED_EXPERIMENT"

RETAIL_DOMAIN: Final[str] = "DUNNHUMBY_RETAIL_BEHAVIOR"

MEDIA_DOMAIN: Final[str] = "CRITEO_MEDIA_ATTRIBUTION"

FUNNEL_DOMAIN: Final[str] = "RETAILROCKET_EVENT_FUNNEL"


@dataclass(frozen=True)
class DecisionEvidence:
    recommendation_id: str
    evidence_domain: str
    audience_id: str
    audience_name: str
    audience_size: int
    evidence_class: str

    causal_evidence_present: bool
    randomized_evidence_present: bool

    incremental_effect: float | None
    confidence_level: float | None
    ci_lower: float | None
    ci_upper: float | None

    uplift_score: float | None
    top20_uplift_score: float | None

    customer_value_signal: bool
    category_opportunity_signal: bool
    lapsed_opportunity_signal: bool
    promotion_sensitive_signal: bool

    attribution_credit_signal: bool
    raw_response_signal: bool

    source_artifact: str
    source_record: str
    targeting_quality_score: float | None = None
    targeting_action_eligible: bool = False


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    evidence_domain: str
    audience_id: str
    audience_name: str
    audience_size: int

    recommendation_class: str
    next_action: str

    causal_evidence_present: bool
    incremental_effect: float | None
    ci_lower: float | None
    ci_upper: float | None
    uplift_score: float | None

    privacy_threshold_pass: bool
    activation_size_pass: bool
    confidence_threshold_pass: bool

    recommendation_reason: str
    guardrail_reason: str

    source_artifact: str
    source_record: str

    deterministic_priority: int
    targeting_quality_score: float | None = None
    targeting_action_eligible: bool = False


def _float_scalar(
    value: object,
) -> float:
    return float(
        cast(
            Any,
            value,
        )
    )


def _int_scalar(
    value: object,
) -> int:
    return int(
        cast(
            Any,
            value,
        )
    )


def classify_recommendation(
    evidence: DecisionEvidence,
) -> Recommendation:
    """Deterministically classify one governed recommendation."""

    privacy_pass = evidence.audience_size >= PRIVACY_MIN_AUDIENCE_SIZE

    activation_pass = evidence.audience_size >= ACTIVATION_MIN_AUDIENCE_SIZE

    positive_causal = (
        evidence.causal_evidence_present
        and evidence.randomized_evidence_present
        and evidence.incremental_effect is not None
        and evidence.ci_lower is not None
        and evidence.ci_lower > 0
    )

    negative_causal = (
        evidence.causal_evidence_present
        and evidence.randomized_evidence_present
        and evidence.incremental_effect is not None
        and evidence.ci_upper is not None
        and evidence.ci_upper < 0
    )

    confidence_pass = positive_causal or negative_causal

    uplift_positive = (
        evidence.uplift_score is not None
        and evidence.uplift_score > 0
        and evidence.top20_uplift_score is not None
        and evidence.top20_uplift_score > 0
    )

    uplift_nonpositive = evidence.uplift_score is not None and evidence.uplift_score <= 0

    targeting_quality_positive = (
        evidence.targeting_quality_score is not None and evidence.targeting_quality_score > 0
    )

    # --------------------------------------------------------
    # 8.31 Minimum audience/privacy guardrail.
    # --------------------------------------------------------

    if not privacy_pass:
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="INSUFFICIENT_EVIDENCE",
            next_action="INVESTIGATE",
            causal_evidence_present=(evidence.causal_evidence_present),
            incremental_effect=evidence.incremental_effect,
            ci_lower=evidence.ci_lower,
            ci_upper=evidence.ci_upper,
            uplift_score=evidence.uplift_score,
            privacy_threshold_pass=False,
            activation_size_pass=False,
            confidence_threshold_pass=confidence_pass,
            recommendation_reason=(
                "Audience is below the frozen Project 4 privacy reporting threshold."
            ),
            guardrail_reason=(
                "No activation decision is emitted for audiences "
                f"below {PRIVACY_MIN_AUDIENCE_SIZE} records."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=50,
        )

    # --------------------------------------------------------
    # 8.18 Raw response cannot become causal recommendation.
    # 8.19 Attribution cannot become causal recommendation.
    # 8.20 Retail value cannot become treatment recommendation.
    # --------------------------------------------------------

    if evidence.evidence_domain in {
        MEDIA_DOMAIN,
        FUNNEL_DOMAIN,
    }:
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="MEASURED_RECOMMENDATION",
            next_action="INVESTIGATE",
            causal_evidence_present=False,
            incremental_effect=None,
            ci_lower=None,
            ci_upper=None,
            uplift_score=None,
            privacy_threshold_pass=privacy_pass,
            activation_size_pass=activation_pass,
            confidence_threshold_pass=False,
            recommendation_reason=(
                "Descriptive media/funnel evidence is retained as a "
                "measurement recommendation rather than a treatment "
                "effect claim."
            ),
            guardrail_reason=(
                "Attribution credit and event-volume funnel ratios "
                "cannot masquerade as randomized incrementality."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=40,
        )

    if evidence.evidence_domain == RETAIL_DOMAIN:
        if not activation_pass:
            return Recommendation(
                recommendation_id=evidence.recommendation_id,
                evidence_domain=evidence.evidence_domain,
                audience_id=evidence.audience_id,
                audience_name=evidence.audience_name,
                audience_size=evidence.audience_size,
                recommendation_class="INSUFFICIENT_EVIDENCE",
                next_action="INVESTIGATE",
                causal_evidence_present=False,
                incremental_effect=None,
                ci_lower=None,
                ci_upper=None,
                uplift_score=None,
                privacy_threshold_pass=privacy_pass,
                activation_size_pass=False,
                confidence_threshold_pass=False,
                recommendation_reason=(
                    "Retail opportunity exists but the audience is "
                    "below the activation-size threshold."
                ),
                guardrail_reason=("Retail value/behavior alone cannot establish treatment effect."),
                targeting_quality_score=evidence.targeting_quality_score,
                targeting_action_eligible=evidence.targeting_action_eligible,
                source_artifact=evidence.source_artifact,
                source_record=evidence.source_record,
                deterministic_priority=45,
            )

        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="ACTIVATION_HYPOTHESIS",
            next_action="RETEST",
            causal_evidence_present=False,
            incremental_effect=None,
            ci_lower=None,
            ci_upper=None,
            uplift_score=None,
            privacy_threshold_pass=privacy_pass,
            activation_size_pass=activation_pass,
            confidence_threshold_pass=False,
            recommendation_reason=(
                "Retail customer-value or behavioral evidence supports "
                "a testable activation hypothesis."
            ),
            guardrail_reason=(
                "A randomized holdout is required before claiming incremental treatment impact."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=30,
        )

    # --------------------------------------------------------
    # Hillstrom randomized causal domain.
    # --------------------------------------------------------

    if evidence.evidence_domain != CAUSAL_DOMAIN:
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="INSUFFICIENT_EVIDENCE",
            next_action="INVESTIGATE",
            causal_evidence_present=False,
            incremental_effect=None,
            ci_lower=None,
            ci_upper=None,
            uplift_score=None,
            privacy_threshold_pass=privacy_pass,
            activation_size_pass=activation_pass,
            confidence_threshold_pass=False,
            recommendation_reason=(
                "Evidence domain is not approved for a causal activation decision."
            ),
            guardrail_reason=(
                "Only randomized Hillstrom evidence can directly drive "
                "causal treatment actions in Project 4."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=50,
        )

    if not activation_pass:
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="INSUFFICIENT_EVIDENCE",
            next_action="INVESTIGATE",
            causal_evidence_present=True,
            incremental_effect=evidence.incremental_effect,
            ci_lower=evidence.ci_lower,
            ci_upper=evidence.ci_upper,
            uplift_score=evidence.uplift_score,
            privacy_threshold_pass=privacy_pass,
            activation_size_pass=False,
            confidence_threshold_pass=confidence_pass,
            recommendation_reason=(
                "Randomized evidence exists but the audience is below "
                "the activation-size threshold."
            ),
            guardrail_reason=("Minimum activation audience size is required."),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=45,
        )

    if (
        positive_causal
        and uplift_positive
        and evidence.targeting_action_eligible
        and targeting_quality_positive
    ):
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="MEASURED_RECOMMENDATION",
            next_action="SCALE",
            causal_evidence_present=True,
            incremental_effect=evidence.incremental_effect,
            ci_lower=evidence.ci_lower,
            ci_upper=evidence.ci_upper,
            uplift_score=evidence.uplift_score,
            privacy_threshold_pass=True,
            activation_size_pass=True,
            confidence_threshold_pass=True,
            recommendation_reason=(
                "Positive randomized incremental effect and positive "
                "held-out uplift evidence agree."
            ),
            guardrail_reason=(
                "Scale only while retaining an experimental holdout for continued measurement."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=10,
        )

    if negative_causal and uplift_nonpositive:
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="SUPPRESSION_RECOMMENDED",
            next_action="SUPPRESS",
            causal_evidence_present=True,
            incremental_effect=evidence.incremental_effect,
            ci_lower=evidence.ci_lower,
            ci_upper=evidence.ci_upper,
            uplift_score=evidence.uplift_score,
            privacy_threshold_pass=True,
            activation_size_pass=True,
            confidence_threshold_pass=True,
            recommendation_reason=(
                "Randomized incremental evidence is negative and uplift evidence is non-positive."
            ),
            guardrail_reason=(
                "Suppression is supported only inside the randomized evidence domain."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=15,
        )

    if confidence_pass:
        return Recommendation(
            recommendation_id=evidence.recommendation_id,
            evidence_domain=evidence.evidence_domain,
            audience_id=evidence.audience_id,
            audience_name=evidence.audience_name,
            audience_size=evidence.audience_size,
            recommendation_class="HOLDOUT_RECOMMENDED",
            next_action="MAINTAIN_HOLDOUT",
            causal_evidence_present=True,
            incremental_effect=evidence.incremental_effect,
            ci_lower=evidence.ci_lower,
            ci_upper=evidence.ci_upper,
            uplift_score=evidence.uplift_score,
            privacy_threshold_pass=True,
            activation_size_pass=True,
            confidence_threshold_pass=True,
            recommendation_reason=(
                "Randomized effect is statistically directional but "
                "uplift evidence does not agree strongly enough for "
                "Scale or Suppress."
            ),
            guardrail_reason=(
                "Maintain randomized holdout until causal and targeting evidence agree."
            ),
            targeting_quality_score=evidence.targeting_quality_score,
            targeting_action_eligible=evidence.targeting_action_eligible,
            source_artifact=evidence.source_artifact,
            source_record=evidence.source_record,
            deterministic_priority=20,
        )

    return Recommendation(
        recommendation_id=evidence.recommendation_id,
        evidence_domain=evidence.evidence_domain,
        audience_id=evidence.audience_id,
        audience_name=evidence.audience_name,
        audience_size=evidence.audience_size,
        recommendation_class="HOLDOUT_RECOMMENDED",
        next_action="RETEST",
        causal_evidence_present=True,
        incremental_effect=evidence.incremental_effect,
        ci_lower=evidence.ci_lower,
        ci_upper=evidence.ci_upper,
        uplift_score=evidence.uplift_score,
        privacy_threshold_pass=True,
        activation_size_pass=True,
        confidence_threshold_pass=False,
        recommendation_reason=("Randomized confidence interval is inconclusive."),
        guardrail_reason=(
            "Retest with holdout; raw response differences must not "
            "be promoted into causal recommendations."
        ),
        source_artifact=evidence.source_artifact,
        source_record=evidence.source_record,
        deterministic_priority=25,
    )


def recommendations_frame(
    evidence_rows: list[DecisionEvidence],
) -> pd.DataFrame:
    """Build deterministic recommendation table."""

    recommendations = [classify_recommendation(evidence) for evidence in evidence_rows]

    frame = pd.DataFrame([asdict(recommendation) for recommendation in recommendations])

    if frame.empty:
        return frame

    return frame.sort_values(
        [
            "deterministic_priority",
            "evidence_domain",
            "audience_id",
            "recommendation_id",
        ],
        kind="mergesort",
    ).reset_index(drop=True)


def validate_recommendations(
    recommendations: pd.DataFrame,
) -> None:
    """Enforce Step 8 causal and privacy governance."""

    if recommendations.empty:
        raise ValueError("Recommendation table is empty.")

    if not set(recommendations["recommendation_class"]).issubset(set(RECOMMENDATION_CLASSES)):
        raise ValueError("Unknown recommendation class.")

    if not set(recommendations["next_action"]).issubset(set(NEXT_ACTIONS)):
        raise ValueError("Unknown next action.")

    causal_actions = recommendations["next_action"].isin(
        [
            "SCALE",
            "SUPPRESS",
        ]
    )

    if not recommendations.loc[
        causal_actions,
        "causal_evidence_present",
    ].all():
        raise ValueError("Scale/Suppress without causal evidence.")

    if not recommendations.loc[
        causal_actions,
        "activation_size_pass",
    ].all():
        raise ValueError("Scale/Suppress below activation-size threshold.")

    if not recommendations.loc[
        causal_actions,
        "confidence_threshold_pass",
    ].all():
        raise ValueError("Scale/Suppress without directional confidence.")

    forbidden_causal_domains = recommendations["evidence_domain"].isin(
        [
            RETAIL_DOMAIN,
            MEDIA_DOMAIN,
            FUNNEL_DOMAIN,
        ]
    )

    forbidden_actions = recommendations["next_action"].isin(
        [
            "SCALE",
            "SUPPRESS",
        ]
    )

    if (forbidden_causal_domains & forbidden_actions).any():
        raise ValueError("Noncausal evidence drove a causal treatment action.")

    privacy_fail = recommendations["audience_size"] < PRIVACY_MIN_AUDIENCE_SIZE

    if (
        not recommendations.loc[
            privacy_fail,
            "recommendation_class",
        ]
        .eq("INSUFFICIENT_EVIDENCE")
        .all()
    ):
        raise ValueError("Privacy-threshold audience received actionable recommendation.")


def build_evidence_trace(
    evidence_rows: list[DecisionEvidence],
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    """Trace every recommendation to its evidence."""

    evidence = pd.DataFrame([asdict(row) for row in evidence_rows])

    if evidence.empty:
        raise ValueError("Evidence trace cannot be empty.")

    trace = evidence.merge(
        recommendations[
            [
                "recommendation_id",
                "recommendation_class",
                "next_action",
                "privacy_threshold_pass",
                "activation_size_pass",
                "confidence_threshold_pass",
                "recommendation_reason",
                "guardrail_reason",
            ]
        ],
        on="recommendation_id",
        how="left",
        validate="one_to_one",
    )

    if trace["next_action"].isna().any():
        raise ValueError("Recommendation missing from evidence trace.")

    trace["cross_source_identity_join"] = False

    trace["cross_source_row_join"] = False

    return trace.sort_values(
        [
            "evidence_domain",
            "audience_id",
            "recommendation_id",
        ],
        kind="mergesort",
    ).reset_index(drop=True)


def build_executive_recommendations(
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    """Create compact executive decision layer."""

    validate_recommendations(recommendations)

    executive = recommendations.copy()

    executive["executive_priority"] = (
        executive["deterministic_priority"]
        .rank(
            method="dense",
            ascending=True,
        )
        .astype(int)
    )

    executive = executive.sort_values(
        [
            "executive_priority",
            "deterministic_priority",
            "recommendation_id",
        ],
        kind="mergesort",
    )

    return executive.reset_index(drop=True)
