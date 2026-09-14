"""Dataset_A admission declarations; screening cannot establish final traffic metrics."""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .models import Contract, Positive, PositiveInt, Sha256, Text
from .source import AnalysisWindows, VideoMetadata


class InventoryRow(Contract):
    filename: str = Field(pattern=r"^cam_[1-9]\d*(?:_[a-z]+)?\.mp4$")
    fps_numerator: PositiveInt
    fps_denominator: PositiveInt
    frame_count: PositiveInt

    @property
    def declared_duration(self) -> Fraction:
        return Fraction(self.frame_count * self.fps_denominator, self.fps_numerator)

    @property
    def camera_id(self) -> str:
        return "_".join(self.filename.split("_")[:2]).removesuffix(".mp4")

    @property
    def condition(self) -> str:
        parts = self.filename.removesuffix(".mp4").split("_")
        return parts[2] if len(parts) == 3 else "day"


def parse_inventory(text: str) -> tuple[InventoryRow, ...]:
    """Parse supplied stats strictly, without treating declared timing as verified PTS."""
    lines = text.strip().splitlines()
    if not lines or lines[0].split() != ["vid_name", "fps", "frame_num"]:
        raise ValueError("invalid Dataset_A stats header")
    rows: dict[str, InventoryRow] = {}
    for line in lines[1:]:
        fields = line.split()
        if len(fields) != 3 or not re.fullmatch(r"[1-9]\d*/[1-9]\d*", fields[1]):
            raise ValueError("invalid stats row or rational FPS")
        numerator, denominator = map(int, fields[1].split("/"))
        if not re.fullmatch(r"[1-9]\d*", fields[2]):
            raise ValueError("invalid frame count")
        row = InventoryRow(
            filename=fields[0],
            fps_numerator=numerator,
            fps_denominator=denominator,
            frame_count=int(fields[2]),
        )
        if row.filename in rows:
            raise ValueError("duplicate video filename")
        rows[row.filename] = row
    if not rows:
        raise ValueError("empty video inventory")
    return tuple(rows[name] for name in sorted(rows))


class TechnicalScreen(Contract):
    duration_seconds: Positive
    width: PositiveInt
    height: PositiveInt
    fixed_camera: bool | None = Field(default=None, strict=True)
    no_major_cuts: bool | None = Field(default=None, strict=True)
    normal_timing: bool | None = Field(default=None, strict=True)
    decode_usable: bool | None = Field(default=None, strict=True)
    vehicles_visible: bool | None = Field(default=None, strict=True)
    meaningful_traffic: bool | None = Field(default=None, strict=True)

    def rejections(self, *, better_resolution_available: bool = True) -> tuple[str, ...]:
        reasons = []
        if self.duration_seconds < 600:
            reasons.append("DURATION_BELOW_600_SECONDS")
        if (self.width < 1280 or self.height < 720) and better_resolution_available:
            reasons.append("BELOW_HD")
        for field in (
            "fixed_camera",
            "no_major_cuts",
            "normal_timing",
            "decode_usable",
            "vehicles_visible",
            "meaningful_traffic",
        ):
            if getattr(self, field) is False:
                reasons.append(field.upper() + "_FAILED")
        return tuple(reasons)

    def complete(self) -> bool:
        return not self.rejections() and all(
            value is True
            for value in (
                self.fixed_camera,
                self.no_major_cuts,
                self.normal_timing,
                self.decode_usable,
                self.vehicles_visible,
                self.meaningful_traffic,
            )
        )


Score = Annotated[int, Field(strict=True, ge=0, le=2)]


class CandidateScore(Contract):
    filename: Text
    condition: Literal["day", "moderate", "dawn", "rain", "snow", "night"]
    factors: tuple[Score, ...] = Field(min_length=13, max_length=13)
    rationale: Text


def shortlist(scores: tuple[CandidateScore, ...], limit: int = 3) -> tuple[CandidateScore, ...]:
    """Evidence scores outrank weather preference; a rank never implies admission."""
    if not 3 <= limit <= 5 or len({s.filename for s in scores}) != len(scores):
        raise ValueError("shortlist requires unique candidates and a limit of 3 to 5")
    conditions = {"day": 0, "moderate": 1, "dawn": 2, "rain": 3, "snow": 3, "night": 4}
    return tuple(
        sorted(scores, key=lambda s: (-sum(s.factors), conditions[s.condition], s.filename))[:limit]
    )


class EpisodeWindows(AnalysisWindows):
    @model_validator(mode="after")
    def ten_minute_mode(self) -> Self:
        if self.duration_seconds < 600 or self.static.end - self.static.start != 600:
            raise ValueError("Dataset_A requires an exact 600-second static interval")
        if self.baseline.end - self.baseline.start < 120:
            raise ValueError("baseline must cover at least 120 original seconds")
        if self.degraded.end - self.degraded.start < 60:
            raise ValueError("degraded candidate must cover at least 60 original seconds")
        return self


class SourceAdmission(Contract):
    """Internal academic admission, explicitly independent of public image permission.

    Booleans are reviewed declarations, not automated proofs. Evidence files and
    hashes must be checked by the caller; this schema alone cannot authenticate them.
    """

    mode: Literal["AICITY_DATASET_A_600"] = "AICITY_DATASET_A_600"
    metadata: VideoMetadata
    screen: TechnicalScreen
    windows: EpisodeWindows | None = None
    analytical_use: Literal["ACADEMIC_ONLY", "UNKNOWN", "DENIED"]
    usage_scope: Literal["INTERNAL_NONCOMMERCIAL_ACADEMIC"]
    public_raw_video_reuse_allowed: Literal[False] = False
    public_derived_visuals: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"
    agreement_sha256: Sha256
    episode_evidence_sha256: Sha256
    sustained_beyond_individual_stop: bool = Field(strict=True)
    geometry_useful: bool = Field(strict=True)
    source_approved: bool = Field(strict=True)
    review_rationale: Text

    @model_validator(mode="after")
    def approval(self) -> Self:
        if (
            self.metadata.duration_seconds != self.screen.duration_seconds
            or self.metadata.width != self.screen.width
            or self.metadata.height != self.screen.height
        ):
            raise ValueError("screen and source metadata disagree")
        if self.windows and self.windows.duration_seconds != self.metadata.duration_seconds:
            raise ValueError("windows belong to a different source duration")
        if self.source_approved and not (
            self.screen.complete()
            and self.metadata.decode_ok
            and self.windows is not None
            and self.analytical_use == "ACADEMIC_ONLY"
            and self.sustained_beyond_individual_stop
            and self.geometry_useful
        ):
            raise ValueError("source approval prerequisites are incomplete")
        return self
