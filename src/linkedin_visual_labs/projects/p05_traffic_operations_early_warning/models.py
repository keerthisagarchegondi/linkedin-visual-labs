"""Immutable Step 1 declarations; no traffic analysis or runtime evaluation."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Literal, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

PROJECT_ID = "p05_traffic_operations_early_warning"
RAW = f"data/raw/{PROJECT_ID}"
PROCESSED = f"data/processed/{PROJECT_ID}"
OUTPUT = f"outputs/{PROJECT_ID}"
BUSINESS_QUESTION = (
    "Can an ordinary fixed camera warn Operations that congestion is developing before a "
    "sustained queue becomes visually obvious?"
)


def strict_boolean(value: object) -> object:
    if type(value) is not bool:
        raise ValueError("boolean required")
    return value


PositiveInt = Annotated[int, Field(strict=True, gt=0)]
NonnegativeInt = Annotated[int, Field(strict=True, ge=0)]
Number = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Positive = Annotated[float, Field(strict=True, gt=0, allow_inf_nan=False)]
Nonnegative = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]
Proportion = Annotated[float, Field(strict=True, gt=0, le=1, allow_inf_nan=False)]
Text = Annotated[str, Field(strict=True, min_length=1, pattern=r"\S")]
Sha256 = Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
Always = Annotated[Literal[True], BeforeValidator(strict_boolean)]
Never = Annotated[Literal[False], BeforeValidator(strict_boolean)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)


class SourceStatus(StrEnum):
    SOURCE_PENDING = "SOURCE_PENDING"
    SOURCE_APPROVED = "SOURCE_APPROVED"
    SOURCE_REVIEW_REQUIRED = "SOURCE_REVIEW_REQUIRED"
    SOURCE_REJECTED_LICENSE = "SOURCE_REJECTED_LICENSE"
    SOURCE_REJECTED_DURATION = "SOURCE_REJECTED_DURATION"
    SOURCE_REJECTED_CAMERA = "SOURCE_REJECTED_CAMERA"
    SOURCE_REJECTED_EPISODE = "SOURCE_REJECTED_EPISODE"
    SOURCE_REJECTED_QUALITY = "SOURCE_REJECTED_QUALITY"


class ReviewStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class KnownBoolean(StrEnum):
    YES = "YES"
    NO = "NO"
    UNKNOWN = "UNKNOWN"


class ResultClassification(StrEnum):
    POSITIVE_EARLY_WARNING = "POSITIVE_EARLY_WARNING"
    WARNING_AT_VISIBLE_ONSET = "WARNING_AT_VISIBLE_ONSET"
    LATE_WARNING = "LATE_WARNING"
    NO_VALID_WARNING = "NO_VALID_WARNING"
    NO_VISIBLE_QUEUE_EVENT = "NO_VISIBLE_QUEUE_EVENT"
    INSUFFICIENT_SOURCE_EPISODE = "INSUFFICIENT_SOURCE_EPISODE"
    INSUFFICIENT_DETECTION_QUALITY = "INSUFFICIENT_DETECTION_QUALITY"
    INSUFFICIENT_TRACK_QUALITY = "INSUFFICIENT_TRACK_QUALITY"


class ClaimClassification(StrEnum):
    MEASURED = "MEASURED"
    DERIVED = "DERIVED"
    CONFIGURED_ASSUMPTION = "CONFIGURED_ASSUMPTION"
    ILLUSTRATIVE_RECOMMENDATION = "ILLUSTRATIVE_RECOMMENDATION"
    PREVIEW_ONLY = "PREVIEW_ONLY"
    UNSUPPORTED = "UNSUPPORTED"


class WarningState(StrEnum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ActionType(StrEnum):
    MONITOR = "MONITOR"
    INVESTIGATE_SERVICE_DELAY = "INVESTIGATE_SERVICE_DELAY"
    DISPATCH_SUPPORT_STAFF = "DISPATCH_SUPPORT_STAFF"
    METER_ENTRY = "METER_ENTRY"
    OPEN_OVERFLOW_CAPACITY = "OPEN_OVERFLOW_CAPACITY"
    ESCALATE_FOR_REVIEW = "ESCALATE_FOR_REVIEW"


class Availability(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    UNSUPPORTED = "UNSUPPORTED"


class CalibrationStatus(StrEnum):
    RELATIVE_ONLY = "RELATIVE_ONLY"
    PHYSICAL_CALIBRATED = "PHYSICAL_CALIBRATED"


class RuleStatus(StrEnum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FROZEN = "FROZEN"


class Unit(StrEnum):
    VEHICLES = "VEHICLES"
    SECONDS = "SECONDS"
    PROPORTION = "PROPORTION"
    NORMALIZED_PER_SECOND = "NORMALIZED_PER_SECOND"
    EXITS_PER_WINDOW = "EXITS_PER_WINDOW"
    VEHICLES_PER_SECOND = "VEHICLES_PER_SECOND"
    SECONDS_PER_SECOND = "SECONDS_PER_SECOND"
    EXITS_PER_WINDOW_PER_SECOND = "EXITS_PER_WINDOW_PER_SECOND"
    MPH = "MPH"
    FEET = "FEET"
    METERS = "METERS"
    VEHICLES_PER_LANE_MILE = "VEHICLES_PER_LANE_MILE"


PHYSICAL_UNITS = frozenset((Unit.MPH, Unit.FEET, Unit.METERS, Unit.VEHICLES_PER_LANE_MILE))


def project_relative(value: str, roots: tuple[str, ...]) -> str:
    """Pure lexical validation, including Windows syntax on Linux; never accesses disk."""
    windows = PureWindowsPath(value)
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or ":" in value
        or windows.drive
        or windows.root
        or path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != value
    ):
        raise ValueError("expected normalized repository-relative path without traversal")
    if not any(path.is_relative_to(root) and str(path) != root for root in roots):
        raise ValueError("path must identify a file inside the approved Project 6 area")
    if path.is_relative_to(OUTPUT):
        parts = path.relative_to(OUTPUT).parts
        if len(parts) < 2 or parts[0] not in ("data", "images", "videos", "report", "manifests"):
            raise ValueError("evidence must use an approved output category")
    return value


RawPath = Annotated[
    Text, BeforeValidator(lambda v: project_relative(v, (RAW,)) if isinstance(v, str) else v)
]
EvidencePath = Annotated[
    Text,
    BeforeValidator(
        lambda v: project_relative(v, (RAW, PROCESSED, OUTPUT)) if isinstance(v, str) else v
    ),
]


class EvidenceReference(Contract):
    evidence_id: Text
    path: EvidencePath
    sha256: Sha256 | None = None
    selector: Text | None = None
    review: ReviewStatus = ReviewStatus.REVIEW_REQUIRED

    @model_validator(mode="after")
    def accepted_hash(self) -> Self:
        if self.review == ReviewStatus.APPROVED and self.sha256 is None:
            raise ValueError("approved evidence requires its actual hash")
        return self


def approved(evidence: EvidenceReference | None) -> bool:
    return evidence is not None and evidence.review == ReviewStatus.APPROVED


class PermittedUse(Contract):
    analysis: KnownBoolean = KnownBoolean.UNKNOWN
    derivatives: KnownBoolean = KnownBoolean.UNKNOWN
    excerpts: KnownBoolean = KnownBoolean.UNKNOWN
    image: KnownBoolean = KnownBoolean.UNKNOWN
    video: KnownBoolean = KnownBoolean.UNKNOWN
    report: KnownBoolean = KnownBoolean.UNKNOWN


class SourceCandidate(Contract):
    source_id: Text
    source_name: Text
    owner: Text | None = None
    acquisition_method: Text | None = None
    license_or_ownership_basis: Text | None = None
    private_evidence: EvidenceReference | None = None
    permitted_use: PermittedUse = PermittedUse()
    attribution_requirement: Text | None = None
    raw_file_path: RawPath | None = None
    checksum_sha256: Sha256 | None = None
    duration_seconds: Positive | None = None
    width: PositiveInt | None = None
    height: PositiveInt | None = None
    codec: Text | None = None
    nominal_frame_rate: Positive | None = None
    average_frame_rate: Positive | None = None
    variable_frame_rate: KnownBoolean = KnownBoolean.UNKNOWN
    timestamp_characteristics: Text | None = None
    timing_review: ReviewStatus = ReviewStatus.UNKNOWN
    camera_continuity: ReviewStatus = ReviewStatus.UNKNOWN
    scene_cuts: KnownBoolean = KnownBoolean.UNKNOWN
    camera_motion: KnownBoolean = KnownBoolean.UNKNOWN
    episode_review: ReviewStatus = ReviewStatus.UNKNOWN
    quality_review: ReviewStatus = ReviewStatus.UNKNOWN
    location_wording: Text = "Unspecified location"
    location_evidence: EvidenceReference | None = None
    privacy_concerns: tuple[Text, ...] = ()
    privacy_treatment: Text | None = None
    privacy_review: ReviewStatus = ReviewStatus.UNKNOWN
    status: SourceStatus = SourceStatus.SOURCE_PENDING
    reviewer_decision: ReviewStatus = ReviewStatus.REVIEW_REQUIRED
    reasons: tuple[Text, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    short_episode_justification: Text | None = None

    @model_validator(mode="after")
    def approval_contract(self) -> Self:
        if self.location_wording != "Unspecified location" and not approved(self.location_evidence):
            raise ValueError("specific location wording requires reviewed evidence")
        if self.status.name.startswith("SOURCE_REJECTED") and not self.reasons:
            raise ValueError("source rejection requires reasons")
        if self.status != SourceStatus.SOURCE_APPROVED:
            return self
        required = (
            self.owner,
            self.acquisition_method,
            self.license_or_ownership_basis,
            self.attribution_requirement,
            self.raw_file_path,
            self.checksum_sha256,
            self.duration_seconds,
            self.width,
            self.height,
            self.codec,
            self.timestamp_characteristics,
            self.privacy_treatment,
        )
        if any(value is None for value in required):
            raise ValueError("source approval requires complete rights and technical metadata")
        if (
            not approved(self.private_evidence)
            or not self.evidence
            or not all(approved(item) for item in self.evidence)
        ):
            raise ValueError("source approval requires reviewed rights and source evidence")
        if not all(value == KnownBoolean.YES for value in self.permitted_use.model_dump().values()):
            raise ValueError("source approval requires every intended use")
        if self.variable_frame_rate == KnownBoolean.UNKNOWN or (
            self.nominal_frame_rate is None and self.average_frame_rate is None
        ):
            raise ValueError("source approval requires frame timing metadata")
        if (
            any(
                value != ReviewStatus.APPROVED
                for value in (
                    self.timing_review,
                    self.camera_continuity,
                    self.episode_review,
                    self.quality_review,
                    self.privacy_review,
                    self.reviewer_decision,
                )
            )
            or self.scene_cuts != KnownBoolean.NO
            or self.camera_motion != KnownBoolean.NO
        ):
            raise ValueError(
                "source approval requires accepted timing/camera/episode/privacy review"
            )
        if self.duration_seconds is not None and (
            self.duration_seconds < 720
            or (self.duration_seconds < 1800 and self.short_episode_justification is None)
        ):
            raise ValueError("source approval violates duration/short-episode policy")
        return self


class SourceConfig(Contract):
    status: SourceStatus = SourceStatus.SOURCE_REVIEW_REQUIRED
    candidate: SourceCandidate | None = None
    planning_floor_seconds: PositiveInt = 720
    preferred_seconds: tuple[PositiveInt, PositiveInt] = (1800, 2700)
    duration_policy_classification: Literal[ClaimClassification.CONFIGURED_ASSUMPTION] = (
        ClaimClassification.CONFIGURED_ASSUMPTION
    )

    @model_validator(mode="after")
    def coherent_source(self) -> Self:
        if self.planning_floor_seconds != 720 or self.preferred_seconds != (1800, 2700):
            raise ValueError("duration policy change requires a versioned contract revision")
        if self.candidate is None and self.status != SourceStatus.SOURCE_REVIEW_REQUIRED:
            raise ValueError("no candidate requires SOURCE_REVIEW_REQUIRED")
        if self.candidate is not None and self.status != self.candidate.status:
            raise ValueError("candidate/source status mismatch")
        return self


class CalibrationConfig(Contract):
    status: CalibrationStatus = CalibrationStatus.RELATIVE_ONLY
    units: tuple[Unit, ...] = (
        Unit.VEHICLES,
        Unit.SECONDS,
        Unit.PROPORTION,
        Unit.NORMALIZED_PER_SECOND,
        Unit.EXITS_PER_WINDOW,
    )
    source_id: Text | None = None
    geometry_id: Text | None = None
    method: Text | None = None
    evidence: EvidenceReference | None = None

    @model_validator(mode="after")
    def physical_evidence(self) -> Self:
        if self.status == CalibrationStatus.RELATIVE_ONLY:
            if PHYSICAL_UNITS.intersection(self.units):
                raise ValueError("physical units require calibration")
        elif not (self.source_id and self.geometry_id and self.method and approved(self.evidence)):
            raise ValueError("physical calibration requires source, geometry, method and evidence")
        return self


class ResultContract(Contract):
    precedence: tuple[ResultClassification, ...] = (
        ResultClassification.INSUFFICIENT_SOURCE_EPISODE,
        ResultClassification.INSUFFICIENT_DETECTION_QUALITY,
        ResultClassification.INSUFFICIENT_TRACK_QUALITY,
        ResultClassification.NO_VISIBLE_QUEUE_EVENT,
        ResultClassification.NO_VALID_WARNING,
    )
    positive: Literal[ResultClassification.POSITIVE_EARLY_WARNING] = (
        ResultClassification.POSITIVE_EARLY_WARNING
    )
    zero: Literal[ResultClassification.WARNING_AT_VISIBLE_ONSET] = (
        ResultClassification.WARNING_AT_VISIBLE_ONSET
    )
    negative: Literal[ResultClassification.LATE_WARNING] = ResultClassification.LATE_WARNING
    formula: Literal["visible_queue_timestamp - warning_timestamp"] = (
        "visible_queue_timestamp - warning_timestamp"
    )
    missing_onset_lead_time: None = None
    clamp_negative: Never = False
    preserve_quality_facts: Always = True
    invalid_metrics_block_evaluation: Always = True
    uncertainty_separate_from_rounding: Always = True

    @model_validator(mode="after")
    def fixed_precedence(self) -> Self:
        expected = (
            "INSUFFICIENT_SOURCE_EPISODE",
            "INSUFFICIENT_DETECTION_QUALITY",
            "INSUFFICIENT_TRACK_QUALITY",
            "NO_VISIBLE_QUEUE_EVENT",
            "NO_VALID_WARNING",
        )
        if tuple(self.precedence) != expected:
            raise ValueError("invalid result precedence")
        return self


class AnalysisConfig(Contract):
    clock: Literal["ORIGINAL_SOURCE_TIMESTAMPS"] = "ORIGINAL_SOURCE_TIMESTAMPS"
    sampling_rescales_time: Never = False
    presentation_rescales_time: Never = False
    reference_point: Literal["BOTTOM_CENTER"] = "BOTTOM_CENTER"
    exclude_unsupported_predictions: Always = True
    invent_fragment_identity: Never = False
    distinguish_censoring: Always = True
    calibration: CalibrationConfig = CalibrationConfig()
    result: ResultContract = ResultContract()


class MetricsConfig(Contract):
    throughput_window_seconds: PositiveInt = 300
    imbalance_window_seconds: PositiveInt = 300
    window_closure: Literal["(t-window,t]"] = "(t-window,t]"
    occupancy: Literal["ELIGIBLE_ACTIVE_TRACK_REFERENCE_IN_ZONE"] = (
        "ELIGIBLE_ACTIVE_TRACK_REFERENCE_IN_ZONE"
    )
    density: Literal["VEHICLE_COUNT_IN_ZONE"] = "VEHICLE_COUNT_IN_ZONE"
    crossings: Literal["DIRECTIONAL_UNIQUE_TRACK_PER_WINDOW"] = (
        "DIRECTIONAL_UNIQUE_TRACK_PER_WINDOW"
    )
    visits: Literal["INDEPENDENT_VALID_ENTRY_EXIT_PAIRS"] = "INDEPENDENT_VALID_ENTRY_EXIT_PAIRS"
    dwell: Literal["COMPLETED_EXIT_ASSIGNED_ORIGINAL_SECONDS"] = (
        "COMPLETED_EXIT_ASSIGNED_ORIGINAL_SECONDS"
    )
    movement: Literal["NORMALIZED_DISPLACEMENT_PER_SOURCE_SECOND"] = (
        "NORMALIZED_DISPLACEMENT_PER_SOURCE_SECOND"
    )
    queue_count: Literal["ELIGIBLE_LOW_MOTION_TRACKS_IN_QUEUE_ZONE"] = (
        "ELIGIBLE_LOW_MOTION_TRACKS_IN_QUEUE_ZONE"
    )
    imbalance: Literal["UNIQUE_ENTRIES_MINUS_UNIQUE_EXITS"] = "UNIQUE_ENTRIES_MINUS_UNIQUE_EXITS"
    missing_samples: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    missing_evaluation: Literal["BREAK_PERSISTENCE"] = "BREAK_PERSISTENCE"
    warmup: Literal["FULL_WINDOW_REQUIRED"] = "FULL_WINDOW_REQUIRED"
    zero_baseline_delta: Literal["UNAVAILABLE"] = "UNAVAILABLE"
    median_required: Always = True
    completed_sample_count_required: Always = True
    review: RuleStatus = RuleStatus.REVIEW_REQUIRED
    percentile_range: tuple[Nonnegative, Nonnegative] | None = None
    percentile_method: Literal["linear", "nearest", "lower", "higher", "midpoint"] | None = None
    minimum_completed_samples: PositiveInt | None = None
    minimum_coverage: Proportion | None = None
    low_motion_threshold: Nonnegative | None = None
    low_motion_duration_seconds: Positive | None = None
    baseline_method: Text | None = None
    trend_method: Text | None = None
    review_evidence: EvidenceReference | None = None

    @model_validator(mode="after")
    def metric_contract(self) -> Self:
        if self.throughput_window_seconds != 300 or self.imbalance_window_seconds != 300:
            raise ValueError("initial throughput and imbalance windows must both be 300 seconds")
        if self.percentile_range is not None:
            low, high = self.percentile_range
            if not 0 <= low < high <= 100:
                raise ValueError("percentiles must be ordered within 0..100")
        if self.review == RuleStatus.FROZEN and (
            any(
                value is None
                for value in (
                    self.percentile_range,
                    self.percentile_method,
                    self.minimum_completed_samples,
                    self.minimum_coverage,
                    self.low_motion_threshold,
                    self.low_motion_duration_seconds,
                    self.baseline_method,
                    self.trend_method,
                )
            )
            or not approved(self.review_evidence)
        ):
            raise ValueError("frozen metrics require complete reviewed measurement configuration")
        return self


class QueueSignal(StrEnum):
    QUEUE_ZONE_OCCUPANCY = "QUEUE_ZONE_OCCUPANCY"
    LOW_MOTION_COUNT = "LOW_MOTION_COUNT"
    QUEUE_COUNT = "QUEUE_COUNT"
    MOVEMENT = "MOVEMENT"


class LeadingSignal(StrEnum):
    DENSITY_LEVEL = "DENSITY_LEVEL"
    DENSITY_TREND = "DENSITY_TREND"
    COMPLETED_DWELL_LEVEL = "COMPLETED_DWELL_LEVEL"
    COMPLETED_DWELL_TREND = "COMPLETED_DWELL_TREND"
    THROUGHPUT_FLATTENING = "THROUGHPUT_FLATTENING"
    THROUGHPUT_DECLINE = "THROUGHPUT_DECLINE"
    INFLOW_OUTFLOW_IMBALANCE = "INFLOW_OUTFLOW_IMBALANCE"


class Predicate(Contract):
    unit: Unit
    comparator: Literal["GT", "GE", "LT", "LE"]
    threshold: Number | None = None
    provenance: Literal[ClaimClassification.CONFIGURED_ASSUMPTION] = (
        ClaimClassification.CONFIGURED_ASSUMPTION
    )
    rationale: Text | None = None
    evidence: EvidenceReference | None = None


class QueuePredicate(Predicate):
    signal: QueueSignal

    @model_validator(mode="after")
    def compatible_unit(self) -> Self:
        expected = (
            Unit.NORMALIZED_PER_SECOND if self.signal == QueueSignal.MOVEMENT else Unit.VEHICLES
        )
        if self.unit != expected:
            raise ValueError("queue signal/unit mismatch")
        return self


class WarningPredicate(Predicate):
    signal: LeadingSignal

    @model_validator(mode="after")
    def compatible_unit(self) -> Self:
        expected = {
            LeadingSignal.DENSITY_LEVEL: Unit.VEHICLES,
            LeadingSignal.DENSITY_TREND: Unit.VEHICLES_PER_SECOND,
            LeadingSignal.COMPLETED_DWELL_LEVEL: Unit.SECONDS,
            LeadingSignal.COMPLETED_DWELL_TREND: Unit.SECONDS_PER_SECOND,
            LeadingSignal.THROUGHPUT_FLATTENING: Unit.EXITS_PER_WINDOW_PER_SECOND,
            LeadingSignal.THROUGHPUT_DECLINE: Unit.EXITS_PER_WINDOW_PER_SECOND,
            LeadingSignal.INFLOW_OUTFLOW_IMBALANCE: Unit.VEHICLES,
        }[self.signal]
        if self.unit != expected:
            raise ValueError("leading signal/unit mismatch")
        return self


class PersistenceConfig(Contract):
    mode: Literal["DURATION", "CONSECUTIVE_WINDOWS", "PROPORTION"]
    duration_seconds: Positive | None = None
    window_count: PositiveInt | None = None
    proportion: Proportion | None = None
    missing_evaluation: Literal["BREAK_PERSISTENCE"] = "BREAK_PERSISTENCE"

    @model_validator(mode="after")
    def complete_persistence(self) -> Self:
        shape = (
            self.duration_seconds is not None,
            self.window_count is not None,
            self.proportion is not None,
        )
        expected = {
            "DURATION": (True, False, False),
            "CONSECUTIVE_WINDOWS": (False, True, False),
            "PROPORTION": (False, True, True),
        }
        if shape != expected[self.mode]:
            raise ValueError("persistence mode/parameters mismatch")
        return self


class RuleConfig(Contract):
    status: RuleStatus = RuleStatus.REVIEW_REQUIRED
    cadence_seconds: Positive | None = None
    composition: Literal["ALL", "ANY", "AT_LEAST"] | None = None
    minimum_signals: PositiveInt | None = None
    persistence: PersistenceConfig | None = None
    unavailable_data: Literal["BLOCK_EVALUATION"] | None = None
    review_evidence: EvidenceReference | None = None

    @property
    def executable(self) -> bool:
        return self.status == RuleStatus.FROZEN

    def validate_rule(
        self, predicates: tuple[QueuePredicate, ...] | tuple[WarningPredicate, ...]
    ) -> None:
        signals = [item.signal.value for item in predicates]
        if len(signals) != len(set(signals)):
            raise ValueError("duplicate canonical signals")
        if self.composition == "AT_LEAST":
            if self.minimum_signals is None or self.minimum_signals > len(predicates):
                raise ValueError("AT_LEAST requires a valid minimum signal count")
        elif self.minimum_signals is not None:
            raise ValueError("minimum_signals only belongs to AT_LEAST")
        if self.status == RuleStatus.FROZEN:
            if (
                not predicates
                or self.cadence_seconds is None
                or self.composition is None
                or self.persistence is None
                or self.unavailable_data is None
                or not approved(self.review_evidence)
            ):
                raise ValueError("incomplete FROZEN rule")
            if any(
                item.threshold is None or item.rationale is None or not approved(item.evidence)
                for item in predicates
            ):
                raise ValueError("frozen thresholds require reviewed provenance")


class QueueOutcomeConfig(RuleConfig):
    predicates: tuple[QueuePredicate, ...] = ()

    @model_validator(mode="after")
    def complete(self) -> Self:
        self.validate_rule(self.predicates)
        return self


class TransitionPolicy(Contract):
    entry: Literal["COMPLETE_STATE_RULE"] = "COMPLETE_STATE_RULE"
    reset: Literal["COMPLETE_RESET_RULE"] = "COMPLETE_RESET_RULE"
    reset_persistence: PersistenceConfig
    hysteresis: Nonnegative
    missing_evidence: Literal["QUALITY_UNAVAILABLE_NOT_NORMAL"] = "QUALITY_UNAVAILABLE_NOT_NORMAL"
    direct_critical: Literal["NO_BACKDATED_WARNING"] = "NO_BACKDATED_WARNING"
    warning_onset: Literal["FIRST_COMPLETE_WARNING_PERSISTENCE"] = (
        "FIRST_COMPLETE_WARNING_PERSISTENCE"
    )


class WarningConfig(RuleConfig):
    predicates: tuple[WarningPredicate, ...] = ()
    leading_rationale: Text | None = None
    transitions: TransitionPolicy | None = None
    depends_on_queue_outcome: Never = False

    @model_validator(mode="after")
    def complete(self) -> Self:
        self.validate_rule(self.predicates)
        if self.status == RuleStatus.FROZEN and (
            self.leading_rationale is None or self.transitions is None
        ):
            raise ValueError(
                "frozen warning requires leading rationale and transition declarations"
            )
        return self


class ActionConfig(Contract):
    action: ActionType
    availability: Availability
    eligible: Annotated[bool, Field(strict=True)] = False
    conditional_wording: Text | None = None
    context_evidence: EvidenceReference | None = None

    @model_validator(mode="after")
    def available_only(self) -> Self:
        if self.eligible and self.availability != Availability.ENABLED:
            raise ValueError("only ENABLED actions may be eligible")
        if self.availability == Availability.ENABLED and (
            not approved(self.context_evidence)
            or self.conditional_wording is None
            or not self.conditional_wording.startswith("Consider ")
        ):
            raise ValueError("enabled actions require context evidence and conditional wording")
        return self


class RecommendationsConfig(Contract):
    actions: tuple[ActionConfig, ...] = ()
    no_enabled_action: Literal["NO_ACTION_WITH_REASON"] = "NO_ACTION_WITH_REASON"

    @model_validator(mode="after")
    def unique_actions(self) -> Self:
        if len({item.action for item in self.actions}) != len(self.actions):
            raise ValueError("duplicate action declaration")
        return self


class ClaimRecord(Contract):
    claim_id: Text
    claim_text: Text
    classification: ClaimClassification
    evidence: tuple[EvidenceReference, ...] = ()
    calculation: Text | None = None
    unit: Unit | None = None
    calibration: CalibrationConfig = CalibrationConfig()
    caveat: Text | None = None
    reviewer_status: ReviewStatus = ReviewStatus.REVIEW_REQUIRED
    approved_for_publication: Annotated[bool, Field(strict=True)] = False
    source_manifest_reference: EvidenceReference | None = None
    last_validated_step: Annotated[int, Field(strict=True, ge=1, le=15)] | None = None
    approved_evidence_hashes: tuple[Sha256, ...] = ()

    @model_validator(mode="after")
    def publication(self) -> Self:
        if self.unit in PHYSICAL_UNITS and (
            self.calibration.status != CalibrationStatus.PHYSICAL_CALIBRATED
            or self.unit not in self.calibration.units
        ):
            raise ValueError("physical claim units require applicable calibration evidence")
        if self.approved_for_publication:
            if self.classification in (
                ClaimClassification.PREVIEW_ONLY,
                ClaimClassification.UNSUPPORTED,
            ):
                raise ValueError("preview/unsupported claims cannot be approved")
            if (
                not self.evidence
                or not all(approved(item) for item in self.evidence)
                or self.reviewer_status != ReviewStatus.APPROVED
                or not self.calculation
                or not self.caveat
                or self.last_validated_step is None
            ):
                raise ValueError(
                    "publication requires validated evidence, calculation, caveat and review"
                )
            for item in self.evidence:
                project_relative(item.path, (OUTPUT,))
            if tuple(item.sha256 for item in self.evidence) != self.approved_evidence_hashes:
                raise ValueError("publication approval must bind the exact evidence hashes")
        return self


class PrivacyConfig(Contract):
    vehicle_only: Always = True
    clip_local_anonymous_ids: Always = True
    aggregate_public_metrics: Always = True
    face_recognition: Never = False
    facial_identity: Never = False
    plate_ocr: Never = False
    driver_identity: Never = False
    persistent_vehicle_identity: Never = False
    cross_camera_identity: Never = False
    external_vehicle_lookup: Never = False
    enforcement_citations: Never = False


class SourceInterval(Contract):
    start_seconds: Nonnegative
    end_seconds: Positive

    @model_validator(mode="after")
    def ten_minutes(self) -> Self:
        if self.end_seconds - self.start_seconds != 600:
            raise ValueError("static interval must be one continuous 600 seconds")
        return self


class StaticOutput(Contract):
    width: PositiveInt = 1080
    height: PositiveInt = 1350
    format: Literal["PNG"] = "PNG"
    title: Literal["Ten minutes of traffic in one frame"] = "Ten minutes of traffic in one frame"
    source_interval: SourceInterval | None = None

    @model_validator(mode="after")
    def canvas(self) -> Self:
        if (self.width, self.height) != (1080, 1350):
            raise ValueError("static canvas must be 1080x1350")
        return self


class VideoOutput(Contract):
    width: PositiveInt = 1080
    height: PositiveInt = 1350
    fps: PositiveInt = 30
    aspect: Literal["4:5"] = "4:5"
    codec: Literal["H.264"] = "H.264"
    pixel_format: Literal["yuv420p"] = "yuv420p"
    duration_seconds: Annotated[float, Field(strict=True, ge=44, le=46.5, allow_inf_nan=False)] = (
        45.0
    )
    frame_count: Annotated[int, Field(strict=True, ge=1320, le=1395)] = 1350
    keyframe_seconds: tuple[NonnegativeInt, ...] = (0, 5, 10, 15, 20, 25, 30, 35, 40)
    closing_selector: Literal["LAST_FRAME"] = "LAST_FRAME"
    closing_time_formula: Literal["(frame_count - 1) / 30"] = "(frame_count - 1) / 30"
    audio: Literal["OPTIONAL"] = "OPTIONAL"
    muted_comprehension: Always = True

    @model_validator(mode="after")
    def video_contract(self) -> Self:
        if (self.width, self.height, self.fps) != (1080, 1350, 30):
            raise ValueError("video must be 1080x1350 at 30 fps")
        if abs(self.duration_seconds * 30 - self.frame_count) > 1e-9:
            raise ValueError("duration/frame-count mismatch")
        if self.keyframe_seconds != (0, 5, 10, 15, 20, 25, 30, 35, 40):
            raise ValueError("invalid keyframe sequence")
        return self


class OutputConfig(Contract):
    raw_root: Literal["data/raw/p05_traffic_operations_early_warning"] = (
        "data/raw/p05_traffic_operations_early_warning"
    )
    processed_root: Literal["data/processed/p05_traffic_operations_early_warning"] = (
        "data/processed/p05_traffic_operations_early_warning"
    )
    output_root: Literal["outputs/p05_traffic_operations_early_warning"] = (
        "outputs/p05_traffic_operations_early_warning"
    )
    categories: tuple[str, ...] = ("data", "images", "videos", "report", "manifests")
    static: StaticOutput = StaticOutput()
    video: VideoOutput = VideoOutput()
    report_tabs: tuple[str, ...] = ("Dashboard", "Video", "Method", "Results", "About")

    @model_validator(mode="after")
    def exact_layout(self) -> Self:
        if self.report_tabs != ("Dashboard", "Video", "Method", "Results", "About"):
            raise ValueError("report tabs must match exact order")
        if self.categories != ("data", "images", "videos", "report", "manifests"):
            raise ValueError("invalid output categories")
        return self


class ProjectConfig(Contract):
    schema_version: Literal["1.0"] = "1.0"
    package: Literal["p05_traffic_operations_early_warning"] = (
        "p05_traffic_operations_early_warning"
    )
    display_name: Literal["Project 6 — Traffic Operations Early-Warning System"] = (
        "Project 6 — Traffic Operations Early-Warning System"
    )
    business_question: str = BUSINESS_QUESTION
    public_shorthand: Literal["Camera → Metric → Warning → Action"] = (
        "Camera → Metric → Warning → Action"
    )
    stakeholders: tuple[str, ...] = ("OPERATIONS", "ENGINEERING", "ANALYTICS", "PRIVACY_GOVERNANCE")

    @model_validator(mode="after")
    def business_contract(self) -> Self:
        if self.business_question != BUSINESS_QUESTION or self.stakeholders != (
            "OPERATIONS",
            "ENGINEERING",
            "ANALYTICS",
            "PRIVACY_GOVERNANCE",
        ):
            raise ValueError("business question/stakeholder contract is fixed")
        return self


class TrafficOperationsConfig(Contract):
    project: ProjectConfig
    source: SourceConfig
    analysis: AnalysisConfig
    metrics: MetricsConfig
    queue_outcome: QueueOutcomeConfig
    warning: WarningConfig
    recommendations: RecommendationsConfig
    privacy: PrivacyConfig
    outputs: OutputConfig

    @model_validator(mode="after")
    def independent_contracts(self) -> Self:
        # No aliases are accepted; signal namespaces are deliberately disjoint.
        queue_signals = frozenset(item.signal.value for item in self.queue_outcome.predicates)
        warning_signals = frozenset(item.signal.value for item in self.warning.predicates)
        if queue_signals and queue_signals == warning_signals:
            raise ValueError("warning and outcome cannot require identical signals")
        if (self.queue_outcome.executable or self.warning.executable) and (
            self.metrics.review != RuleStatus.FROZEN
        ):
            raise ValueError("frozen rules require reviewed measurement definitions")
        source = self.source.candidate
        if self.analysis.calibration.status == CalibrationStatus.PHYSICAL_CALIBRATED and (
            source is None
            or self.source.status != SourceStatus.SOURCE_APPROVED
            or (self.analysis.calibration.source_id != source.source_id)
        ):
            raise ValueError("calibration must bind the approved source")
        interval = self.outputs.static.source_interval
        if interval is not None and (
            source is None
            or self.source.status != SourceStatus.SOURCE_APPROVED
            or source.duration_seconds is None
            or interval.end_seconds > source.duration_seconds
        ):
            raise ValueError("picture interval must fit the approved source")
        return self
