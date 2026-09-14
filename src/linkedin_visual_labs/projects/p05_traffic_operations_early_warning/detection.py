"""CPU YOLOX-Nano inference with source-clock sampling and bounded writes.

Pre/postprocessing follows Megvii YOLOX's Apache-2.0 ONNX demo contract.
Implementation is project-local; see THIRD_PARTY_NOTICES.md for provenance.
"""

from __future__ import annotations

import hashlib
import importlib
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .calibration import Geometry, Point
from .source import VideoMetadata

VEHICLES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
FloatArray = NDArray[np.float32]
ImageArray = NDArray[np.uint8]


def checksum(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@dataclass(frozen=True)
class DetectionConfig:
    input_size: int = 416
    analysis_fps: int = 3
    confidence: float = 0.1
    nms_iou: float = 0.45
    minimum_box_pixels: float = 6
    crop: tuple[int, int, int, int] = (550, 250, 1280, 550)

    def __post_init__(self) -> None:
        if self.input_size != 416 or self.analysis_fps not in (3, 5):
            raise ValueError("approved artifact is fixed 416; sampling must be 3 or 5 FPS")
        if not 0 < self.confidence < 1 or not 0 < self.nms_iou < 1:
            raise ValueError("invalid confidence/NMS")
        x1, y1, x2, y2 = self.crop
        if not (0 <= x1 < x2 <= 1280 and 0 <= y1 < y2 <= 720):
            raise ValueError("crop outside approved source")
        if not math.isfinite(self.minimum_box_pixels) or self.minimum_box_pixels <= 0:
            raise ValueError("invalid minimum box size")


def sampled(frame: int, fps: int, source_fps: int = 10) -> bool:
    """First source frame at/after each rational sampling deadline; no time rescaling."""
    if frame < 0 or not 0 < fps <= source_fps:
        raise ValueError("invalid sampling clock")
    return frame == 0 or frame * fps // source_fps > (frame - 1) * fps // source_fps


def preprocess(image: ImageArray, size: int = 416) -> tuple[FloatArray, float]:
    if image.ndim != 3 or image.shape[2] != 3 or min(image.shape[:2]) <= 0:
        raise ValueError("expected nonempty BGR image")
    cv = importlib.import_module("cv2")
    ratio = min(size / image.shape[0], size / image.shape[1])
    resized = cv.resize(image, (int(image.shape[1] * ratio), int(image.shape[0] * ratio)))
    canvas = np.full((size, size, 3), 114, dtype=np.uint8)
    canvas[: resized.shape[0], : resized.shape[1]] = resized
    return np.ascontiguousarray(canvas.transpose(2, 0, 1)[None], dtype=np.float32), ratio


def box_iou(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    intersection = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(
        0.0, min(a[3], b[3]) - max(a[1], b[1])
    )
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - intersection
    return intersection / union if union > 0 else 0.0


def suppress(boxes: FloatArray, scores: FloatArray, threshold: float) -> list[int]:
    """Stable class-agnostic vehicle NMS; equal confidence keeps original row order."""
    order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))
    keep: list[int] = []
    for i in order:
        if all(box_iou(tuple(boxes[i]), tuple(boxes[j])) <= threshold for j in keep):
            keep.append(i)
    return keep


def decode(output: FloatArray, ratio: float, config: DetectionConfig) -> list[tuple[float, ...]]:
    if output.shape != (1, 3549, 85) or not np.isfinite(output).all() or ratio <= 0:
        raise ValueError("unexpected or nonfinite YOLOX output")
    predictions = output[0].copy()
    grids, strides = [], []
    for stride in (8, 16, 32):
        length = config.input_size // stride
        x, y = np.meshgrid(np.arange(length), np.arange(length))
        grids.append(np.stack((x, y), axis=-1).reshape(-1, 2))
        strides.append(np.full((length * length, 1), stride))
    grid, scale = np.concatenate(grids), np.concatenate(strides)
    predictions[:, :2] = (predictions[:, :2] + grid) * scale
    if np.max(predictions[:, 2:4]) > 20:
        raise ValueError("invalid log-width/height")
    predictions[:, 2:4] = np.exp(predictions[:, 2:4]) * scale
    classes = predictions[:, 5:].argmax(axis=1)
    confidence = predictions[:, 4] * predictions[np.arange(len(predictions)), classes + 5]
    eligible = np.isin(classes, list(VEHICLES)) & (confidence >= config.confidence)
    chosen = predictions[eligible]
    classes, confidence = classes[eligible], confidence[eligible]
    boxes = np.empty((len(chosen), 4), dtype=np.float32)
    boxes[:, :2] = (chosen[:, :2] - chosen[:, 2:4] / 2) / ratio
    boxes[:, 2:] = (chosen[:, :2] + chosen[:, 2:4] / 2) / ratio
    x1, y1, x2, y2 = config.crop
    boxes[:, (0, 2)] = np.clip(boxes[:, (0, 2)], 0, x2 - x1) + x1
    boxes[:, (1, 3)] = np.clip(boxes[:, (1, 3)], 0, y2 - y1) + y1
    keep = suppress(boxes, confidence.astype(np.float32), config.nms_iou)
    return [
        (*map(float, boxes[i]), float(confidence[i]), float(classes[i]))
        for i in keep
        if min(boxes[i, 2] - boxes[i, 0], boxes[i, 3] - boxes[i, 1]) >= config.minimum_box_pixels
    ]


@dataclass(frozen=True)
class Detection:
    detection_id: str
    frame_index: int
    source_timestamp: float
    analysis_frame_index: int
    class_id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    reference_x: float
    reference_y: float
    roi_eligible: bool

    def __post_init__(self) -> None:
        if (
            self.class_id not in VEHICLES
            or VEHICLES[self.class_id] != self.class_name
            or not 0 <= self.confidence <= 1
            or not 0 <= self.x1 < self.x2 <= 1280
            or not 0 <= self.y1 < self.y2 <= 720
            or self.frame_index < 0
            or self.analysis_frame_index < 0
            or not math.isfinite(self.source_timestamp)
            or self.source_timestamp < 0
        ):
            raise ValueError("invalid detection observation")
        if self.reference_x != (self.x1 + self.x2) / 2 or self.reference_y != self.y2:
            raise ValueError("reference must be bottom-center")


class Detector:
    def __init__(self, path: Path, expected_sha256: str, config: DetectionConfig) -> None:
        if checksum(path) != expected_sha256:
            raise ValueError("model checksum mismatch")
        ort = importlib.import_module("onnxruntime")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        if self.session.get_providers() != ["CPUExecutionProvider"]:
            raise ValueError("CPU provider required")
        if self.session.get_inputs()[0].shape != [1, 3, 416, 416]:
            raise ValueError("model input shape mismatch")
        self.input_name: str = self.session.get_inputs()[0].name
        self.config = config
        self.inference_seconds = 0.0

    def infer(self, frame: ImageArray) -> list[tuple[float, ...]]:
        x1, y1, x2, y2 = self.config.crop
        tensor, ratio = preprocess(frame[y1:y2, x1:x2], self.config.input_size)
        start = time.perf_counter()
        output = np.asarray(self.session.run(None, {self.input_name: tensor})[0], dtype=np.float32)
        self.inference_seconds += time.perf_counter() - start
        return decode(output, ratio, self.config)


def detect_video(
    source: Path,
    detector: Detector,
    metadata: VideoMetadata,
    geometry: Geometry,
    output: Path,
    *,
    start_frame: int = 0,
    end_frame: int = 18000,
) -> dict[str, Any]:
    """Stream a checksum-verified CFR source; completed Parquet published atomically."""
    if checksum(source) != metadata.sha256 or geometry.source_sha256 != metadata.sha256:
        raise ValueError("source/geometry hash mismatch")
    if (
        not metadata.decode_ok
        or metadata.nominal_fps != 10
        or not 0 <= start_frame < end_frame <= metadata.frame_count
    ):
        raise ValueError("unsupported clock or interval")
    cv = importlib.import_module("cv2")
    arrow, parquet = importlib.import_module("pyarrow"), importlib.import_module("pyarrow.parquet")
    capture = cv.VideoCapture(str(source))
    capture.set(cv.CAP_PROP_POS_FRAMES, start_frame)
    schema = arrow.schema(
        [
            (name, typ)
            for name, typ in (
                ("detection_id", arrow.string()),
                ("frame_index", arrow.int64()),
                ("source_timestamp", arrow.float64()),
                ("analysis_frame_index", arrow.int64()),
                ("class_id", arrow.int64()),
                ("class_name", arrow.string()),
                ("confidence", arrow.float64()),
                *(
                    (k, arrow.float64())
                    for k in ("x1", "y1", "x2", "y2", "reference_x", "reference_y")
                ),
                ("roi_eligible", arrow.bool_()),
            )
        ]
    )
    temporary = output.with_suffix(".partial.parquet")
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = parquet.ParquetWriter(temporary, schema)
    batch: list[dict[str, Any]] = []
    frame_records: list[dict[str, int | float]] = []
    decode_seconds = 0.0
    row_count = roi_count = 0
    started = time.perf_counter()
    try:
        for frame_index in range(start_frame, end_frame):
            tick = time.perf_counter()
            ok, frame = capture.read()
            decode_seconds += time.perf_counter() - tick
            if not ok or frame.shape[:2] != (720, 1280):
                raise ValueError("source decode failed or dimensions changed")
            timestamp = metadata.timestamp(frame_index)
            if abs(capture.get(cv.CAP_PROP_POS_MSEC) / 1000 - timestamp) > 0.051:
                raise ValueError("decoder timestamp disagrees with verified original PTS")
            if not sampled(frame_index, detector.config.analysis_fps):
                continue
            analysis_index = len(frame_records)
            decoded = detector.infer(frame)
            for index, (x1, y1, x2, y2, confidence, cls) in enumerate(decoded):
                rx, ry = (x1 + x2) / 2, y2
                eligible = geometry.roi.contains(Point(x=rx / 1280, y=ry / 720))
                item = Detection(
                    f"{frame_index}:{index}",
                    frame_index,
                    timestamp,
                    analysis_index,
                    int(cls),
                    VEHICLES[int(cls)],
                    confidence,
                    x1,
                    y1,
                    x2,
                    y2,
                    rx,
                    ry,
                    eligible,
                )
                batch.append(asdict(item))
                row_count += 1
                roi_count += int(eligible)
            frame_records.append(
                {
                    "frame_index": frame_index,
                    "source_timestamp": timestamp,
                    "analysis_frame_index": analysis_index,
                    "detections": len(decoded),
                }
            )
            if len(batch) >= 1000:
                writer.write_table(arrow.Table.from_pylist(batch, schema=schema))
                batch.clear()
        if batch:
            writer.write_table(arrow.Table.from_pylist(batch, schema=schema))
    finally:
        capture.release()
        writer.close()
    temporary.replace(output)
    return {
        "rows": row_count,
        "roi_rows": roi_count,
        "frames": frame_records,
        "decode_seconds": decode_seconds,
        "inference_seconds": detector.inference_seconds,
        "wall_seconds": time.perf_counter() - started,
        "config": asdict(detector.config),
    }
