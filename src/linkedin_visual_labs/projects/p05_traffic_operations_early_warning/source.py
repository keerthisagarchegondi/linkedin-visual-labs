"""Local source-screening contracts, never detector or final operational metrics."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from pathlib import PurePosixPath
from statistics import mean, median, pvariance
from typing import Self

from pydantic import Field, model_validator

from .models import Contract, Nonnegative, Positive, PositiveInt, Sha256, Text


class VideoMetadata(Contract):
    camera: Text
    sha256: Sha256
    byte_size: PositiveInt
    duration_seconds: Positive
    width: PositiveInt
    height: PositiveInt
    nominal_fps: Positive
    frame_count: PositiveInt
    time_base_denominator: PositiveInt
    first_pts: int = Field(strict=True)
    last_pts: int = Field(strict=True)
    pts_step: PositiveInt
    codec: Text
    audio_present: bool = Field(strict=True)
    decode_ok: bool = Field(strict=True)

    @model_validator(mode="after")
    def consistent_clock(self) -> Self:
        expected = self.first_pts + (self.frame_count - 1) * self.pts_step
        if self.last_pts != expected:
            raise ValueError("CFR metadata requires a complete uniform original PTS sequence")
        actual = self.frame_count * self.pts_step / self.time_base_denominator
        if not math.isclose(actual, self.duration_seconds, abs_tol=0.001):
            raise ValueError("duration differs from decoded frame timing")
        if not math.isclose(
            self.nominal_fps, self.time_base_denominator / self.pts_step, abs_tol=0.001
        ):
            raise ValueError("nominal and decoded average FPS disagree")
        return self

    def timestamp(self, ordinal: int) -> float:
        """Zero-based decoded ordinal; relative to the original first PTS."""
        if not 0 <= ordinal < self.frame_count:
            raise ValueError("frame outside source")
        return ordinal * self.pts_step / self.time_base_denominator


class Box(Contract):
    xmin: Nonnegative
    ymin: Nonnegative
    xmax: Positive
    ymax: Positive

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        if self.xmin >= self.xmax or self.ymin >= self.ymax:
            raise ValueError("inverted or empty box")
        return self

    def check_bounds(self, width: int, height: int) -> None:
        if self.xmax > width or self.ymax > height:
            raise ValueError("box outside source dimensions")


class Annotation(Contract):
    frame: int = Field(strict=True, ge=0)
    track: int | None = Field(default=None, strict=True, ge=1)
    class_id: int = Field(strict=True, ge=0)
    box: Box
    score: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)


def integer(token: str) -> int:
    """Reject fractional identifiers instead of truncating them."""
    value = float(token)
    if not math.isfinite(value) or not value.is_integer():
        raise ValueError("integer identifier required")
    return int(value)


def label_frame(member: str) -> int:
    path = PurePosixPath(member)
    if path.is_absolute() or ".." in path.parts or "\\" in member:
        raise ValueError("unsafe archive member")
    match = re.fullmatch(r"img(\d{6})\.txt", path.name)
    if match is None:
        raise ValueError("unknown frame filename")
    return int(match[1])


def parse_label(text: str, frame: int) -> tuple[Annotation, ...]:
    """Observed six-column pixel XYXY representation, not normalized YOLO XYWH."""
    result = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 6:
            raise ValueError("expected class xmin ymin xmax ymax score")
        result.append(
            Annotation(
                frame=frame,
                class_id=integer(fields[0]),
                box=Box(
                    **dict(
                        zip(("xmin", "ymin", "xmax", "ymax"), map(float, fields[1:5]), strict=True)
                    )
                ),
                score=float(fields[5]),
            )
        )
    return tuple(result)


def parse_sct(text: str, *, frame_origin: int) -> tuple[Annotation, ...]:
    """Explicit origin required; no implicit interpretation of dataset filenames."""
    if frame_origin not in (0, 1):
        raise ValueError("unsupported frame origin")
    result = []
    seen: set[tuple[int, int]] = set()
    previous: dict[int, int] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 7:
            raise ValueError("expected frame track xmin ymin xmax ymax class")
        frame, track = integer(fields[0]) - frame_origin, integer(fields[1])
        if (frame, track) in seen or frame <= previous.get(track, -1):
            raise ValueError("duplicate or out-of-order per-track frame")
        seen.add((frame, track))
        previous[track] = frame
        result.append(
            Annotation(
                frame=frame,
                track=track,
                class_id=integer(fields[6]),
                box=Box(
                    **dict(
                        zip(("xmin", "ymin", "xmax", "ymax"), map(float, fields[2:6]), strict=True)
                    )
                ),
            )
        )
    return tuple(result)


class Interval(Contract):
    start: Nonnegative
    end: Positive

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.end <= self.start:
            raise ValueError("empty or reversed interval")
        return self


class AnalysisWindows(Contract):
    duration_seconds: Positive
    baseline: Interval
    buildup: Interval
    degraded: Interval
    static: Interval

    @model_validator(mode="after")
    def source_bounds(self) -> Self:
        if not (
            self.baseline.end <= self.buildup.start
            and self.buildup.end <= self.degraded.start
            and self.degraded.end <= self.duration_seconds
            and self.static.end <= self.duration_seconds
        ):
            raise ValueError("overlapping, unordered or out-of-source windows")
        return self

    def static_title(self) -> str:
        seconds = self.static.end - self.static.start
        if math.isclose(seconds, 600, abs_tol=1):
            return "Ten minutes of traffic in one frame"
        return f"{seconds:g} seconds of traffic in one frame"


class ScreeningBin(Contract):
    start: Nonnegative
    end: Positive
    annotated_count_mean: Nonnegative
    movement_median: Nonnegative | None


class ScreeningSummary(Contract):
    camera: Text
    scope: str = "SOURCE_SCREENING_ONLY_NOT_FINAL_TRAFFIC_METRICS"
    input_rows: int
    excluded_rows: int
    duplicate_keys: int
    tracks: int
    annotated_count_mean: Nonnegative
    annotated_count_median: Nonnegative
    annotated_count_variance: Nonnegative
    track_span_median_seconds: Nonnegative
    maximum_low_motion_run_seconds: Nonnegative
    maximum_two_low_motion_run_seconds: Nonnegative
    maximum_three_low_motion_run_seconds: Nonnegative
    bins: tuple[ScreeningBin, ...]


def screening_indicators(text: str, metadata: VideoMetadata) -> ScreeningSummary:
    """Conservative annotation-only review with explicit exclusions and no GT writes.

    Camera-local SCT frame IDs use the empirically checked one-based mapping.
    Every duplicate key is excluded, rather than arbitrarily choosing a box.
    Motion compares observations one original second apart, never across a gap.
    Low motion is <0.002 image diagonals/second, for boxes >=60 pixels tall with
    bottom-center below 25% image height. These are screening assumptions only.
    Counts describe supplied SCT coverage, not all vehicles or physical density.
    """
    if not metadata.decode_ok:
        raise ValueError("screening requires successful source decoding")
    lines = [line for line in text.splitlines() if line.strip()]
    rows: list[Annotation] = []
    for line in lines:
        try:
            row = parse_sct(line, frame_origin=1)[0]
            row.box.check_bounds(metadata.width, metadata.height)
            metadata.timestamp(row.frame)
            rows.append(row)
        except ValueError:
            continue
    keys = Counter((r.frame, r.track) for r in rows)
    valid = [r for r in rows if keys[r.frame, r.track] == 1]
    tracks: dict[int, dict[int, Annotation]] = defaultdict(dict)
    counts = [0] * metadata.frame_count
    low_counts = [0] * metadata.frame_count
    movements: dict[int, list[float]] = defaultdict(list)
    for row in valid:
        assert row.track is not None
        tracks[row.track][row.frame] = row
        counts[row.frame] += 1
    step_seconds = metadata.pts_step / metadata.time_base_denominator
    lag = round(1 / step_seconds)
    if not math.isclose(lag * step_seconds, 1, abs_tol=0.0001):
        raise ValueError("screening requires an exact one-second frame lag")
    spans = []
    longest = 0
    for observations in tracks.values():
        ordered = sorted(observations)
        spans.append((ordered[-1] - ordered[0]) * step_seconds)
        run = 0
        previous = -2
        for frame in ordered:
            row = observations[frame]
            old = observations.get(frame - lag)
            slow = False
            if old is not None and all(f in observations for f in range(frame - lag, frame)):
                dx = (row.box.xmin + row.box.xmax - old.box.xmin - old.box.xmax) / 2
                dy = row.box.ymax - old.box.ymax
                movement = math.hypot(dx, dy) / math.hypot(metadata.width, metadata.height)
                movements[frame].append(movement)
                slow = (
                    movement < 0.002
                    and row.box.ymax > metadata.height * 0.25
                    and row.box.ymax - row.box.ymin >= 60
                )
            run = (run + 1 if frame == previous + 1 else 1) if slow else 0
            longest = max(longest, run)
            low_counts[frame] += int(slow)
            previous = frame

    def simultaneous(minimum: int) -> float:
        run = maximum = 0
        for value in low_counts:
            run = run + 1 if value >= minimum else 0
            maximum = max(maximum, run)
        return maximum * step_seconds

    bins = []
    frames_per_bin = round(30 / step_seconds)
    for start in range(0, metadata.frame_count, frames_per_bin):
        end = min(start + frames_per_bin, metadata.frame_count)
        speeds = [v for frame in range(start, end) for v in movements[frame]]
        bins.append(
            ScreeningBin(
                start=start * step_seconds,
                end=end * step_seconds,
                annotated_count_mean=mean(counts[start:end]),
                movement_median=median(speeds) if speeds else None,
            )
        )
    return ScreeningSummary(
        camera=metadata.camera,
        input_rows=len(lines),
        excluded_rows=len(lines) - len(valid),
        duplicate_keys=sum(v > 1 for v in keys.values()),
        tracks=len(tracks),
        annotated_count_mean=mean(counts),
        annotated_count_median=median(counts),
        annotated_count_variance=pvariance(counts),
        track_span_median_seconds=median(spans) if spans else 0.0,
        maximum_low_motion_run_seconds=longest * step_seconds,
        maximum_two_low_motion_run_seconds=simultaneous(2),
        maximum_three_low_motion_run_seconds=simultaneous(3),
        bins=tuple(bins),
    )


def rank_cameras(scores: dict[str, tuple[int, ...]]) -> tuple[str, ...]:
    """Fourteen documented reviewer ratings, each 0-2; deterministic tie break.

    Ranking is not approval and cannot fabricate a qualifying episode.
    """
    if not scores or any(
        len(v) != 14 or any(type(s) is not int or not 0 <= s <= 2 for s in v)
        for v in scores.values()
    ):
        raise ValueError("fourteen integer 0-2 ratings required per camera")
    return tuple(sorted(scores, key=lambda camera: (-sum(scores[camera]), camera)))
