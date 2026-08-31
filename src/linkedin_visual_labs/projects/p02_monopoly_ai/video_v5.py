"""Final deterministic motion renderer for Project 3 V5."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from linkedin_visual_labs.projects.p02_monopoly_ai.preview_v5 import (
    HEIGHT,
    WIDTH,
    PreviewRuntime,
    board_point,
    downsample,
    grounded_piece,
    load_runtime,
    movement_route_indices,
    render_board_stage,
    validate_preview_semantics,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_motion import (
    camera_zoom,
    clamp01,
    crossfade,
    ease_in_out_cubic,
    ease_out_cubic,
    fade_from_black,
    fade_to_black,
    lerp,
    lift_height,
    reveal_left_to_right,
    reveal_top_to_bottom,
)
from linkedin_visual_labs.projects.p02_monopoly_ai.video_timeline import (
    SceneSpec,
    TimelineSpec,
    load_timeline,
)

ANCHOR_DIRECTORY = Path("outputs/p02_monopoly_ai/visual/v5_preview_lab")

VIDEO_DIRECTORY = Path("outputs/p02_monopoly_ai/video_v5")

FRAME_DIRECTORY = VIDEO_DIRECTORY / "frames"

KEYFRAME_DIRECTORY = VIDEO_DIRECTORY / "keyframes"

FINAL_VIDEO_PATH = VIDEO_DIRECTORY / "project3_step8_v5_final.mp4"

ANCHOR_KEYS = (
    "01_dice_hit",
    "02_piece_race",
    "03_property_purchase",
    "04_house_build",
    "05_rent_hit",
    "06_cash_crash",
    "07_survival_question",
    "08_strategy_personalities",
    "09_gameplay_story",
    "10_scale_10000",
    "11_leaderboard_ci",
    "12_risk_reward",
    "13_result",
)


@dataclass(frozen=True)
class VideoContext:
    """Immutable runtime inputs for deterministic frame rendering."""

    timeline: TimelineSpec
    preview: PreviewRuntime
    anchors: dict[str, Image.Image]


def _load_anchor(
    key: str,
) -> Image.Image:
    path = ANCHOR_DIRECTORY / f"{key}.png"

    if not path.is_file():
        raise FileNotFoundError(f"Missing approved V5 anchor: {path}")

    with Image.open(path) as source:
        image = source.convert("RGB").copy()

    if image.size != (
        WIDTH,
        HEIGHT,
    ):
        raise RuntimeError(f"Approved anchor has unexpected dimensions: {key} {image.size}")

    return image


def load_video_context() -> VideoContext:
    timeline = load_timeline()

    preview = load_runtime()

    validate_preview_semantics(preview)

    anchors = {key: _load_anchor(key) for key in ANCHOR_KEYS}

    return VideoContext(
        timeline=timeline,
        preview=preview,
        anchors=anchors,
    )


def _anchor(
    context: VideoContext,
    key: str,
) -> Image.Image:
    try:
        return context.anchors[key]
    except KeyError as exc:
        raise RuntimeError(f"Unknown approved anchor: {key}") from exc


def _full_board_for_move(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    """Render actual piece lift/carry/drop on a full playable board."""

    turn = context.preview.story.move_turn

    route = movement_route_indices(turn)

    distance = len(route) - 1

    if distance <= 0:
        raise RuntimeError("Movement scene contains zero route distance.")

    t = clamp01(progress)

    route_position = t * distance

    segment = min(
        distance - 1,
        int(route_position),
    )

    local = route_position - segment

    start_space = route[segment]

    end_space = route[segment + 1]

    start_x, start_y = board_point(
        start_space,
        left=0.0,
        top=0.0,
        size=float(WIDTH),
    )

    end_x, end_y = board_point(
        end_space,
        left=0.0,
        top=0.0,
        size=float(WIDTH),
    )

    eased = ease_in_out_cubic(local)

    x = lerp(
        start_x,
        end_x,
        eased,
    )

    y = lerp(
        start_y,
        end_y,
        eased,
    )

    lift = lift_height(
        local,
        maximum=70.0,
    )

    canvas = render_board_stage(
        state=turn.state_before,
        active=None,
        board_left=0,
        board_top=0,
        board_size=WIDTH,
        dim=0.02,
    )

    grounded_piece(
        canvas,
        strategy=turn.strategy_id,
        x=x,
        y=y - lift - 30.0,
        size=150,
        shadow_scale=(1.0 + lift / 180.0),
    )

    return downsample(canvas).convert("RGB")


def _full_board_establishing(
    context: VideoContext,
    *,
    beat_index: int,
) -> Image.Image:
    beats = context.preview.story.narrative_beats

    safe_index = max(
        0,
        min(
            len(beats) - 1,
            beat_index,
        ),
    )

    turn = beats[safe_index].turn

    canvas = render_board_stage(
        state=turn.state_after,
        active=None,
        board_left=70,
        board_top=70,
        board_size=940,
        dim=0.02,
    )

    x, y = board_point(
        turn.to_position,
        left=70.0,
        top=70.0,
        size=940.0,
    )

    grounded_piece(
        canvas,
        strategy=turn.strategy_id,
        x=x,
        y=y - 25.0,
        size=105,
    )

    return downsample(canvas).convert("RGB")


def _animated_anchor(
    image: Image.Image,
    progress: float,
    *,
    zoom_start: float,
    zoom_end: float,
    pan_x_start: float = 0.0,
    pan_x_end: float = 0.0,
    pan_y_start: float = 0.0,
    pan_y_end: float = 0.0,
) -> Image.Image:
    t = ease_in_out_cubic(progress)

    return camera_zoom(
        image,
        zoom=lerp(
            zoom_start,
            zoom_end,
            t,
        ),
        pan_x=lerp(
            pan_x_start,
            pan_x_end,
            t,
        ),
        pan_y=lerp(
            pan_y_start,
            pan_y_end,
            t,
        ),
    )


# ---------------------------------------------------------------------
# V5.66 - Cold open 0:00-0:07
# ---------------------------------------------------------------------


def render_cold_open_dice(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "01_dice_hit",
    )

    if progress < 0.18:
        board = _full_board_for_move(
            context,
            0.0,
        )

        return crossfade(
            board,
            camera_zoom(
                anchor,
                zoom=1.08,
            ),
            ease_out_cubic(progress / 0.18),
        )

    local = (progress - 0.18) / 0.82

    return _animated_anchor(
        anchor,
        local,
        zoom_start=1.08,
        zoom_end=1.0,
    )


def render_cold_open_move(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    if progress < 0.72:
        return _full_board_for_move(
            context,
            ease_in_out_cubic(progress / 0.72),
        )

    anchor = _anchor(
        context,
        "02_piece_race",
    )

    dynamic = _full_board_for_move(
        context,
        1.0,
    )

    return crossfade(
        dynamic,
        anchor,
        ease_out_cubic((progress - 0.72) / 0.28),
    )


def render_cold_open_purchase(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    board = _full_board_establishing(
        context,
        beat_index=0,
    )

    anchor = _anchor(
        context,
        "03_property_purchase",
    )

    if progress < 0.20:
        return crossfade(
            board,
            anchor,
            ease_out_cubic(progress / 0.20),
        )

    return _animated_anchor(
        anchor,
        (progress - 0.20) / 0.80,
        zoom_start=1.04,
        zoom_end=1.0,
        pan_x_start=0.08,
        pan_x_end=0.0,
    )


def render_cold_open_build(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    board = _full_board_establishing(
        context,
        beat_index=2,
    )

    anchor = _anchor(
        context,
        "04_house_build",
    )

    if progress < 0.18:
        return crossfade(
            board,
            anchor,
            ease_out_cubic(progress / 0.18),
        )

    return _animated_anchor(
        anchor,
        (progress - 0.18) / 0.82,
        zoom_start=1.07,
        zoom_end=1.0,
        pan_x_start=-0.05,
        pan_x_end=0.0,
    )


def render_cold_open_rent(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "05_rent_hit",
    )

    return _animated_anchor(
        anchor,
        progress,
        zoom_start=1.05,
        zoom_end=1.0,
        pan_y_start=0.05,
        pan_y_end=0.0,
    )


def render_cold_open_cash(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "06_cash_crash",
    )

    return _animated_anchor(
        anchor,
        progress,
        zoom_start=1.06,
        zoom_end=1.0,
        pan_x_start=-0.04,
        pan_x_end=0.0,
    )


def render_cold_open_question(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "07_survival_question",
    )

    if progress < 0.22:
        return fade_from_black(
            anchor,
            progress / 0.22,
        )

    return _animated_anchor(
        anchor,
        (progress - 0.22) / 0.78,
        zoom_start=1.03,
        zoom_end=1.0,
    )


# ---------------------------------------------------------------------
# V5.67 - Strategy introduction 0:07-0:14
# ---------------------------------------------------------------------


def render_strategies(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "08_strategy_personalities",
    )

    reveal = min(
        1.0,
        progress * 1.35,
    )

    base = reveal_left_to_right(
        anchor,
        ease_out_cubic(reveal),
    )

    return camera_zoom(
        base,
        zoom=lerp(
            1.03,
            1.0,
            ease_out_cubic(progress),
        ),
    )


# ---------------------------------------------------------------------
# V5.68 - Representative game 0:14-0:31
# ---------------------------------------------------------------------


def render_representative_game(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    """Alternate full-board continuity with approved event close-ups."""

    t = clamp01(progress)

    boundaries = (
        0.00,
        0.12,
        0.25,
        0.38,
        0.52,
        0.66,
        0.80,
        1.00,
    )

    if t < boundaries[1]:
        board = _full_board_establishing(
            context,
            beat_index=0,
        )

        return _animated_anchor(
            board,
            t / boundaries[1],
            zoom_start=1.0,
            zoom_end=1.04,
        )

    closeups = (
        "03_property_purchase",
        "09_gameplay_story",
        "04_house_build",
        "05_rent_hit",
        "06_cash_crash",
        "09_gameplay_story",
    )

    for index in range(
        1,
        len(boundaries) - 1,
    ):
        start = boundaries[index]

        end = boundaries[index + 1]

        if not (start <= t <= end):
            continue

        local = (t - start) / (end - start)

        anchor = _anchor(
            context,
            closeups[index - 1],
        )

        board = _full_board_establishing(
            context,
            beat_index=min(
                index,
                5,
            ),
        )

        if local < 0.18:
            return crossfade(
                board,
                anchor,
                ease_out_cubic(local / 0.18),
            )

        if local > 0.84:
            return crossfade(
                anchor,
                board,
                ease_in_out_cubic((local - 0.84) / 0.16),
            )

        middle = (local - 0.18) / 0.66

        return _animated_anchor(
            anchor,
            middle,
            zoom_start=1.035,
            zoom_end=1.0,
        )

    return _anchor(
        context,
        "09_gameplay_story",
    ).copy()


# ---------------------------------------------------------------------
# V5.69 - Scale reveal 0:31-0:39
# ---------------------------------------------------------------------


def render_scale(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "10_scale_10000",
    )

    t = ease_out_cubic(progress)

    return camera_zoom(
        anchor,
        zoom=lerp(
            1.22,
            1.0,
            t,
        ),
    )


# ---------------------------------------------------------------------
# V5.70 - Leaderboard / CI 0:39-0:50
# ---------------------------------------------------------------------


def render_leaderboard(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "11_leaderboard_ci",
    )

    if progress < 0.72:
        return reveal_top_to_bottom(
            anchor,
            ease_out_cubic(progress / 0.72),
        )

    return _animated_anchor(
        anchor,
        (progress - 0.72) / 0.28,
        zoom_start=1.02,
        zoom_end=1.0,
    )


# ---------------------------------------------------------------------
# V5.71 - Risk / reward 0:50-0:55
# ---------------------------------------------------------------------


def render_risk_reward(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "12_risk_reward",
    )

    return reveal_left_to_right(
        anchor,
        ease_out_cubic(
            min(
                1.0,
                progress * 1.25,
            )
        ),
    )


# ---------------------------------------------------------------------
# V5.72 - Result / proof / disclaimer 0:55-1:00
# ---------------------------------------------------------------------


def render_result(
    context: VideoContext,
    progress: float,
) -> Image.Image:
    anchor = _anchor(
        context,
        "13_result",
    )

    t = clamp01(progress)

    if t < 0.16:
        return fade_from_black(
            camera_zoom(
                anchor,
                zoom=1.08,
                pan_y=-0.08,
            ),
            t / 0.16,
        )

    if t < 0.72:
        local = (t - 0.16) / 0.56

        return camera_zoom(
            anchor,
            zoom=lerp(
                1.08,
                1.0,
                ease_out_cubic(local),
            ),
            pan_y=lerp(
                -0.08,
                0.0,
                local,
            ),
        )

    if t > 0.94:
        return fade_to_black(
            anchor,
            (t - 0.94) / 0.06,
        )

    return anchor.copy()


# ---------------------------------------------------------------------
# V5.73 - Deterministic 1,800-frame router
# ---------------------------------------------------------------------


def render_scene_frame(
    context: VideoContext,
    scene: SceneSpec,
    progress: float,
) -> Image.Image:
    renderers = {
        "cold_open_dice": render_cold_open_dice,
        "cold_open_move": render_cold_open_move,
        "cold_open_purchase": render_cold_open_purchase,
        "cold_open_build": render_cold_open_build,
        "cold_open_rent": render_cold_open_rent,
        "cold_open_cash": render_cold_open_cash,
        "cold_open_question": render_cold_open_question,
        "strategies": render_strategies,
        "representative_game": render_representative_game,
        "scale_10000": render_scale,
        "leaderboard": render_leaderboard,
        "risk_reward": render_risk_reward,
        "result": render_result,
    }

    try:
        renderer = renderers[scene.scene_id]
    except KeyError as exc:
        raise RuntimeError(f"No renderer registered for scene {scene.scene_id}") from exc

    image = renderer(
        context,
        progress,
    ).convert("RGB")

    if image.size != (
        WIDTH,
        HEIGHT,
    ):
        raise RuntimeError(f"Scene returned invalid dimensions: {scene.scene_id} {image.size}")

    return image


def render_frame(
    context: VideoContext,
    frame_index: int,
) -> Image.Image:
    if not (0 <= frame_index < context.timeline.frame_count):
        raise IndexError(f"Invalid frame index: {frame_index}")

    scene = context.timeline.scene_for_frame(frame_index)

    progress = context.timeline.progress(frame_index)

    return render_scene_frame(
        context,
        scene,
        progress,
    )


def frame_path(
    frame_index: int,
) -> Path:
    return FRAME_DIRECTORY / f"frame_{frame_index:04d}.png"


def render_frame_to_disk(
    context: VideoContext,
    frame_index: int,
    *,
    directory: Path = FRAME_DIRECTORY,
) -> Path:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = directory / f"frame_{frame_index:04d}.png"

    image = render_frame(
        context,
        frame_index,
    )

    image.save(
        destination,
        format="PNG",
        compress_level=4,
    )

    return destination
