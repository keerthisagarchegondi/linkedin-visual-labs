"""Typed deterministic timeline for Project 3 V5 video."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMELINE_PATH = Path("assets/p02_monopoly_ai/v5_motion_timeline.json")


@dataclass(frozen=True)
class SceneSpec:
    """One contiguous scene in the frozen video timeline."""

    scene_id: str
    start_seconds: float
    end_seconds: float
    anchor: str
    camera: str
    fps: int

    @property
    def start_frame(self) -> int:
        return round(self.start_seconds * self.fps)

    @property
    def end_frame_exclusive(self) -> int:
        return round(self.end_seconds * self.fps)

    @property
    def frame_count(self) -> int:
        return self.end_frame_exclusive - self.start_frame

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


@dataclass(frozen=True)
class TimelineSpec:
    """Strongly typed immutable 60-second video contract."""

    fps: int
    duration_seconds: float
    frame_count: int
    scenes: tuple[SceneSpec, ...]

    def scene_for_frame(
        self,
        frame_index: int,
    ) -> SceneSpec:
        if not (0 <= frame_index < self.frame_count):
            raise IndexError(f"Frame outside timeline: {frame_index}")

        for scene in self.scenes:
            if scene.start_frame <= frame_index < scene.end_frame_exclusive:
                return scene

        raise RuntimeError(f"No scene owns frame {frame_index}")

    def local_frame(
        self,
        frame_index: int,
    ) -> int:
        scene = self.scene_for_frame(frame_index)

        return frame_index - scene.start_frame

    def progress(
        self,
        frame_index: int,
    ) -> float:
        """Return scene-local progress in [0, 1]."""

        scene = self.scene_for_frame(frame_index)

        if scene.frame_count <= 1:
            return 1.0

        local = frame_index - scene.start_frame

        return local / (scene.frame_count - 1)


def _expect_number(
    value: object,
    *,
    name: str,
) -> float:
    if isinstance(
        value,
        bool,
    ) or not isinstance(
        value,
        (int, float),
    ):
        raise TypeError(f"{name} must be numeric.")

    return float(value)


def _expect_string(
    value: object,
    *,
    name: str,
) -> str:
    if (
        not isinstance(
            value,
            str,
        )
        or not value.strip()
    ):
        raise TypeError(f"{name} must be a non-empty string.")

    return value.strip()


def load_timeline(
    path: Path = DEFAULT_TIMELINE_PATH,
) -> TimelineSpec:
    """Load and validate the frozen JSON timeline."""

    raw = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        raw,
        dict,
    ):
        raise TypeError("Timeline root must be an object.")

    fps_raw = raw.get("fps")

    frame_count_raw = raw.get("frame_count")

    duration_raw = raw.get("duration_seconds")

    scenes_raw = raw.get("scenes")

    if not isinstance(
        fps_raw,
        int,
    ):
        raise TypeError("Timeline fps must be int.")

    if not isinstance(
        frame_count_raw,
        int,
    ):
        raise TypeError("Timeline frame_count must be int.")

    duration = _expect_number(
        duration_raw,
        name="duration_seconds",
    )

    if not isinstance(
        scenes_raw,
        list,
    ):
        raise TypeError("Timeline scenes must be a list.")

    scenes: list[SceneSpec] = []

    for index, item in enumerate(scenes_raw):
        if not isinstance(
            item,
            dict,
        ):
            raise TypeError(f"Timeline scene must be object: index={index}")

        scene = SceneSpec(
            scene_id=_expect_string(
                item.get("id"),
                name=f"scenes[{index}].id",
            ),
            start_seconds=_expect_number(
                item.get("start"),
                name=f"scenes[{index}].start",
            ),
            end_seconds=_expect_number(
                item.get("end"),
                name=f"scenes[{index}].end",
            ),
            anchor=_expect_string(
                item.get("anchor"),
                name=f"scenes[{index}].anchor",
            ),
            camera=_expect_string(
                item.get("camera"),
                name=f"scenes[{index}].camera",
            ),
            fps=fps_raw,
        )

        if scene.end_seconds <= scene.start_seconds:
            raise ValueError(f"Scene duration must be positive: {scene.scene_id}")

        scenes.append(scene)

    timeline = TimelineSpec(
        fps=fps_raw,
        duration_seconds=duration,
        frame_count=frame_count_raw,
        scenes=tuple(scenes),
    )

    validate_timeline(timeline)

    return timeline


def validate_timeline(
    timeline: TimelineSpec,
) -> None:
    """Validate exact frozen Project 3 video boundaries."""

    if timeline.fps != 30:
        raise ValueError(f"Expected 30 FPS; got {timeline.fps}")

    if timeline.duration_seconds != 60.0:
        raise ValueError("Expected exactly 60 seconds.")

    if timeline.frame_count != 1800:
        raise ValueError("Expected exactly 1800 frames.")

    if len(timeline.scenes) != 13:
        raise ValueError("Expected exactly 13 scenes.")

    cursor = 0

    for scene in timeline.scenes:
        if scene.start_frame != cursor:
            raise ValueError(
                "Timeline frame gap/overlap before "
                f"{scene.scene_id}: "
                f"expected={cursor}, "
                f"actual={scene.start_frame}"
            )

        cursor = scene.end_frame_exclusive

    if cursor != timeline.frame_count:
        raise ValueError(f"Timeline does not terminate at frame {timeline.frame_count}.")
