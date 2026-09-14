"""Clip-local, CPU ByteTrack-compatible two-stage association.

Independent implementation: constant-velocity box Kalman filter, high-score
association followed by low-score recovery. Predictions are never observations.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .detection import Detection, box_iou


@dataclass(frozen=True)
class TrackingConfig:
    high_score: float = 0.5
    birth_score: float = 0.55
    high_iou: float = 0.2
    low_iou: float = 0.4
    lost_seconds: float = 2.0
    confirmation_hits: int = 3
    maximum_movement_per_second: float = 0.15

    def __post_init__(self) -> None:
        if not 0.1 < self.high_score <= self.birth_score <= 1:
            raise ValueError("invalid confidence thresholds")
        if not 0 < self.high_iou <= self.low_iou <= 1:
            raise ValueError("invalid association thresholds")
        if not 0 < self.lost_seconds <= 10 or self.confirmation_hits < 2:
            raise ValueError("invalid lifecycle configuration")
        if not 0 < self.maximum_movement_per_second <= 1:
            raise ValueError("invalid image-plane motion gate")


def measurement(detection: Detection) -> NDArray[np.float64]:
    return np.array(
        [
            (detection.x1 + detection.x2) / 2,
            (detection.y1 + detection.y2) / 2,
            detection.x2 - detection.x1,
            detection.y2 - detection.y1,
        ]
    )


@dataclass
class Track:
    track_id: int
    observations: list[Detection]
    mean: NDArray[np.float64]
    covariance: NDArray[np.float64]
    predicted_at: float
    status: str = "UNCONFIRMED"
    recoveries: int = 0
    confirmed: bool = False
    stages: list[str] = field(default_factory=lambda: ["BIRTH"])

    @property
    def last(self) -> Detection:
        return self.observations[-1]

    def predict(self, timestamp: float) -> None:
        dt = timestamp - self.predicted_at
        transition = np.eye(8)
        transition[:4, 4:] = np.eye(4) * dt
        self.mean = transition @ self.mean
        self.covariance = transition @ self.covariance @ transition.T + np.eye(8) * max(dt, 1e-6)
        self.predicted_at = timestamp

    def update(self, detection: Detection, stage: str, hits: int) -> None:
        residual = measurement(detection) - self.mean[:4]
        innovation = self.covariance[:4, :4] + np.eye(4) * 4
        gain = np.linalg.solve(innovation, self.covariance[:4, :]).T
        self.mean += gain @ residual
        # Joseph form retains covariance symmetry and positive semidefiniteness.
        observation = np.eye(4, 8)
        correction = np.eye(8) - gain @ observation
        self.covariance = correction @ self.covariance @ correction.T + gain @ gain.T * 4
        self.recoveries += int(self.status == "LOST")
        self.observations.append(detection)
        self.stages.append(stage)
        self.confirmed = self.confirmed or len(self.observations) >= hits
        self.status = "ACTIVE" if self.confirmed else "UNCONFIRMED"

    @property
    def predicted_box(self) -> tuple[float, ...]:
        x, y, w, h = (float(v) for v in self.mean[:4])
        return x - max(w, 1) / 2, y - max(h, 1) / 2, x + max(w, 1) / 2, y + max(h, 1) / 2


class Tracker:
    """IDs reset per instance; no appearance features or external identity."""

    def __init__(self, config: TrackingConfig | None = None) -> None:
        self.config = config or TrackingConfig()
        self.tracks: list[Track] = []
        self.timestamp = -1.0
        self.duplicate_births_suppressed = 0

    def associate(
        self, tracks: list[Track], detections: list[Detection], minimum_iou: float
    ) -> list[tuple[Track, Detection]]:
        if not tracks or not detections:
            return []
        costs = np.ones((len(tracks), len(detections))) * 1e6
        for i, track in enumerate(tracks):
            for j, detection in enumerate(detections):
                dt = detection.source_timestamp - track.last.source_timestamp
                distance = math.hypot(
                    detection.reference_x - track.last.reference_x,
                    detection.reference_y - track.last.reference_y,
                ) / math.hypot(1280, 720)
                overlap = box_iou(
                    track.predicted_box, (detection.x1, detection.y1, detection.x2, detection.y2)
                )
                if (
                    dt > 0
                    and distance / dt <= self.config.maximum_movement_per_second
                    and overlap >= minimum_iou
                ):
                    costs[i, j] = 1 - overlap
        # Dummy unmatched columns prevent an invalid forced match from displacing
        # an admissible assignment when the rectangular matrix is saturated.
        augmented = np.concatenate((costs, np.ones((len(tracks), len(tracks)))), axis=1)
        rows, columns = importlib.import_module("scipy.optimize").linear_sum_assignment(augmented)
        return [
            (tracks[int(i)], detections[int(j)])
            for i, j in zip(rows, columns, strict=True)
            if j < len(detections) and costs[i, j] < 1
        ]

    def update(self, timestamp: float, detections: list[Detection]) -> None:
        if not math.isfinite(timestamp) or timestamp <= self.timestamp:
            raise ValueError("frame timestamps must strictly increase")
        if any(d.source_timestamp != timestamp for d in detections):
            raise ValueError("detection clock mismatch")
        if len({d.detection_id for d in detections}) != len(detections):
            raise ValueError("duplicate detection IDs")
        self.timestamp = timestamp
        eligible = sorted((d for d in detections if d.roi_eligible), key=lambda d: d.detection_id)
        high = [d for d in eligible if d.confidence >= self.config.high_score]
        low = [d for d in eligible if 0.1 <= d.confidence < self.config.high_score]
        live = []
        for track in self.tracks:
            if track.status == "REMOVED":
                continue
            if timestamp - track.last.source_timestamp > self.config.lost_seconds:
                track.status = "REMOVED"
                continue
            track.predict(timestamp)
            live.append(track)
        matches = self.associate([t for t in live if t.confirmed], high, self.config.high_iou)
        used_tracks = {t.track_id for t, _ in matches}
        used_detections = {d.detection_id for _, d in matches}
        low_matches = self.associate(
            [t for t in live if t.track_id not in used_tracks and t.status == "ACTIVE"],
            low,
            self.config.low_iou,
        )
        for track, detection in matches:
            track.update(detection, "HIGH", self.config.confirmation_hits)
        for track, detection in low_matches:
            track.update(detection, "LOW", self.config.confirmation_hits)
        used_tracks.update(t.track_id for t, _ in low_matches)
        tentative = self.associate(
            [t for t in live if not t.confirmed],
            [d for d in high if d.detection_id not in used_detections],
            self.config.high_iou,
        )
        for track, detection in tentative:
            track.update(detection, "CONFIRM", self.config.confirmation_hits)
        used_tracks.update(t.track_id for t, _ in tentative)
        used_detections.update(d.detection_id for _, d in tentative)
        for track in live:
            if track.track_id not in used_tracks:
                track.status = "LOST" if track.confirmed else "REMOVED"
        for detection in high:
            if (
                detection.detection_id in used_detections
                or detection.confidence < self.config.birth_score
            ):
                continue
            if any(
                t.status == "ACTIVE"
                and box_iou(
                    t.predicted_box, (detection.x1, detection.y1, detection.x2, detection.y2)
                )
                > 0.8
                for t in live
            ):
                self.duplicate_births_suppressed += 1
                continue
            self.tracks.append(
                Track(
                    len(self.tracks) + 1,
                    [detection],
                    np.concatenate((measurement(detection), np.zeros(4))),
                    np.diag([10.0] * 4 + [100.0] * 4),
                    timestamp,
                )
            )
