"""Prediction-time feature contract for Project 7."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final

from .models import AvailabilityClass

CONTRACT_VERSION: Final[str] = "1.0.0"

PREDICTION_MOMENT: Final[str] = "Immediately before the current outbound call begins."

EXPECTED_INPUT_COLUMNS: Final[tuple[str, ...]] = (
    "age",
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "poutcome",
    "emp.var.rate",
    "cons.price.idx",
    "cons.conf.idx",
    "euribor3m",
    "nr.employed",
)

TARGET_COLUMN: Final[str] = "y"

EXPECTED_COLUMNS: Final[tuple[str, ...]] = (
    *EXPECTED_INPUT_COLUMNS,
    TARGET_COLUMN,
)


@dataclass(frozen=True, slots=True)
class FeatureAvailability:
    """One prediction-time feature-contract record."""

    feature_name: str
    business_definition: str
    source_column: str
    availability_class: AvailabilityClass
    available_at_prediction: bool
    deployment_allowed: bool
    reason: str
    owner: str
    evidence: str
    version: str = CONTRACT_VERSION

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["availability_class"] = self.availability_class.value
        return payload


def _feature(
    name: str,
    definition: str,
    availability: AvailabilityClass,
    *,
    reason: str,
    evidence: str,
) -> FeatureAvailability:
    allowed = availability in {
        AvailabilityClass.PRE_DECISION,
        AvailabilityClass.KNOWN_AT_DECISION,
    }

    return FeatureAvailability(
        feature_name=name,
        business_definition=definition,
        source_column=name,
        availability_class=availability,
        available_at_prediction=allowed,
        deployment_allowed=allowed,
        reason=reason,
        owner="Project 7 prediction-time contract",
        evidence=evidence,
    )


def build_feature_contract() -> tuple[FeatureAvailability, ...]:
    """Return the frozen Version 1 feature availability contract."""

    uci = "UCI Bank Marketing dataset metadata and variable descriptions; DOI 10.24432/C5K306."

    decision = (
        "Defined Project 7 prediction moment: immediately before the current outbound call begins."
    )

    records = (
        _feature(
            "age",
            "Client age.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer attribute known before call prioritization.",
            evidence=uci,
        ),
        _feature(
            "job",
            "Client occupation category.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer attribute known before call prioritization.",
            evidence=uci,
        ),
        _feature(
            "marital",
            "Client marital-status category.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer attribute known before call prioritization.",
            evidence=uci,
        ),
        _feature(
            "education",
            "Client education category.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer attribute known before call prioritization.",
            evidence=uci,
        ),
        _feature(
            "default",
            "Whether the client has credit in default.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer credit attribute predates the current call.",
            evidence=uci,
        ),
        _feature(
            "housing",
            "Whether the client has a housing loan.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer loan attribute predates the current call.",
            evidence=uci,
        ),
        _feature(
            "loan",
            "Whether the client has a personal loan.",
            AvailabilityClass.PRE_DECISION,
            reason="Customer loan attribute predates the current call.",
            evidence=uci,
        ),
        _feature(
            "contact",
            "Communication channel selected for the current contact.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason=(
                "The contact channel is treated as part of the call plan "
                "known when the pre-call ranking decision is executed."
            ),
            evidence=f"{uci} {decision}",
        ),
        _feature(
            "month",
            "Month of the current contact.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason="Calendar context is known immediately before the call.",
            evidence=f"{uci} {decision}",
        ),
        _feature(
            "day_of_week",
            "Day of week of the current contact.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason="Calendar context is known immediately before the call.",
            evidence=f"{uci} {decision}",
        ),
        _feature(
            "duration",
            "Duration in seconds of the current call.",
            AvailabilityClass.DURING_ACTION,
            reason=(
                "UCI explicitly states duration is not known before the "
                "call is performed; therefore it is blocked for pre-call "
                "ranking."
            ),
            evidence=uci,
        ),
        _feature(
            "campaign",
            (
                "Number of contacts performed during the current campaign "
                "for this client, including the current/last contact."
            ),
            AvailabilityClass.UNKNOWN,
            reason=(
                "UCI documents that this count includes the current/last "
                "contact, but the source does not establish the exact "
                "production counter semantics available immediately before "
                "the current call. Block until documented."
            ),
            evidence=f"{uci} {decision}",
        ),
        _feature(
            "pdays",
            "Days since the client was contacted in a previous campaign.",
            AvailabilityClass.PRE_DECISION,
            reason="Historical prior-campaign information predates the call.",
            evidence=uci,
        ),
        _feature(
            "previous",
            "Number of contacts before the current campaign.",
            AvailabilityClass.PRE_DECISION,
            reason="Historical prior-campaign count predates the call.",
            evidence=uci,
        ),
        _feature(
            "poutcome",
            "Outcome of the previous marketing campaign.",
            AvailabilityClass.PRE_DECISION,
            reason="Prior-campaign outcome predates the current call.",
            evidence=uci,
        ),
        _feature(
            "emp.var.rate",
            "Employment variation rate.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason=(
                "Contemporaneous public economic context is treated as "
                "known at the decision timestamp."
            ),
            evidence=uci,
        ),
        _feature(
            "cons.price.idx",
            "Consumer price index.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason=(
                "Contemporaneous public economic context is treated as "
                "known at the decision timestamp."
            ),
            evidence=uci,
        ),
        _feature(
            "cons.conf.idx",
            "Consumer confidence index.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason=(
                "Contemporaneous public economic context is treated as "
                "known at the decision timestamp."
            ),
            evidence=uci,
        ),
        _feature(
            "euribor3m",
            "Three-month Euribor rate.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason=(
                "Contemporaneous public economic context is treated as "
                "known at the decision timestamp."
            ),
            evidence=uci,
        ),
        _feature(
            "nr.employed",
            "Number of employees economic indicator.",
            AvailabilityClass.KNOWN_AT_DECISION,
            reason=(
                "Contemporaneous public economic context is treated as "
                "known at the decision timestamp."
            ),
            evidence=uci,
        ),
    )

    validate_feature_contract(records)
    return records


def validate_feature_contract(
    records: tuple[FeatureAvailability, ...],
) -> None:
    """Validate completeness and release policy."""

    if len(records) != len(EXPECTED_INPUT_COLUMNS):
        raise ValueError("Feature contract must contain every input exactly once.")

    names = tuple(record.feature_name for record in records)

    if names != EXPECTED_INPUT_COLUMNS:
        raise ValueError("Feature-contract order must exactly match source inputs.")

    if len(set(names)) != len(names):
        raise ValueError("Feature contract contains duplicate feature names.")

    by_name = {record.feature_name: record for record in records}

    duration = by_name["duration"]

    if duration.availability_class is not AvailabilityClass.DURING_ACTION:
        raise ValueError("duration must be DURING_ACTION.")

    if duration.deployment_allowed:
        raise ValueError("duration must be blocked for pre-call deployment.")

    campaign = by_name["campaign"]

    if campaign.availability_class is not AvailabilityClass.UNKNOWN:
        raise ValueError("campaign must remain UNKNOWN in Version 1.")

    if campaign.deployment_allowed:
        raise ValueError("campaign must be blocked until semantics are documented.")

    for record in records:
        should_allow = record.availability_class in {
            AvailabilityClass.PRE_DECISION,
            AvailabilityClass.KNOWN_AT_DECISION,
        }

        if record.available_at_prediction != should_allow:
            raise ValueError(f"Availability policy mismatch: {record.feature_name}")

        if record.deployment_allowed != should_allow:
            raise ValueError(f"Deployment policy mismatch: {record.feature_name}")


def feature_contract_payload() -> dict[str, object]:
    """Build machine-readable prediction-time evidence."""

    records = build_feature_contract()

    return {
        "contract_version": CONTRACT_VERSION,
        "prediction_moment": PREDICTION_MOMENT,
        "release_policy": {
            AvailabilityClass.PRE_DECISION.value: "ELIGIBLE",
            AvailabilityClass.KNOWN_AT_DECISION.value: "ELIGIBLE",
            AvailabilityClass.DURING_ACTION.value: "BLOCK",
            AvailabilityClass.POST_OUTCOME.value: "BLOCK",
            AvailabilityClass.UNKNOWN.value: "BLOCK_UNTIL_DOCUMENTED",
        },
        "features": [record.to_dict() for record in records],
    }


def deployment_feature_names() -> tuple[str, ...]:
    """Return only Version 1 deployment-eligible features."""

    return tuple(
        record.feature_name for record in build_feature_contract() if record.deployment_allowed
    )


def blocked_feature_names() -> tuple[str, ...]:
    """Return only blocked/unknown Version 1 features."""

    return tuple(
        record.feature_name for record in build_feature_contract() if not record.deployment_allowed
    )
