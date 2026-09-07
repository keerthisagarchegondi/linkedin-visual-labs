"Final artifact orchestration; preserves all upstream analytical files."

from __future__ import annotations

import io
import json
import re
import subprocess
from dataclasses import asdict
from html.parser import HTMLParser
from pathlib import Path
from time import perf_counter
from typing import Any

from PIL import Image, ImageChops

from linkedin_visual_labs.common.media import validate_png_dimensions, write_generation_manifest
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import (
    presentation_charts,
    presentation_decisions,
    presentation_navigation,
    presentation_world,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
    BOLD,
    FONT,
    allocation_example,
    champion_canvas,
    scene_canvas,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    INVENTORY_LABEL,
    LABOR_LIMIT,
    RETROSPECTIVE,
    Evidence,
    load_evidence,
    sha256,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_html import (
    report_html,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_media import (
    encode_video,
    packaged_ffmpeg,
    validate_scene_pixels,
    validate_video,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import (
    SECTIONS,
    VIDEO_TITLES,
    storyboards,
)


class ResourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.bad: list[str] = []
        self.sections = 0
        self.section_ids: list[str] = []
        self.ids: list[str] = []
        self.anchors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "section":
            self.sections += 1
            self.section_ids.append(dict(attrs).get("id") or "")
        for key, value in attrs:
            if key == "id" and value:
                self.ids.append(value)
            if key == "href" and value and value.startswith("#"):
                self.anchors.append(value[1:])
            if key in ("src", "href") and value and not value.startswith(("data:", "#")):
                self.bad.append(value)


def validate_html(document: str, e: Evidence, png: bytes) -> None:
    parser = ResourceParser()
    parser.feed(document)
    if parser.bad or parser.sections != 9:
        raise ValueError("HTML requires external resources or lacks sections")
    if parser.section_ids != ["overview"] + [f"section-{i}" for i in range(1, 9)]:
        raise ValueError("Overview must precede the analytical sections")
    if len(parser.ids) != len(set(parser.ids)) or any(a not in parser.ids for a in parser.anchors):
        raise ValueError("Broken or duplicate navigation anchor")
    for required in (
        "PROJECT OVERVIEW",
        *SECTIONS,
        RETROSPECTIVE,
        LABOR_LIMIT,
        INVENTORY_LABEL,
        presentation_navigation.PROVENANCE,
    ):
        if required not in document:
            raise ValueError(f"Missing narrative: {required}")
    for required in (
        presentation_decisions.BUSINESS_QUESTION,
        presentation_decisions.IMPACT_CONCLUSION,
        presentation_decisions.RECOMMENDATION,
        "What was the final labor allocation?",
        "PROTOTYPE VALIDATION",
        "How this becomes an operating system",
    ):
        if required not in document:
            raise ValueError(f"Missing decision narrative: {required}")
    # Exact regeneration reconciles chart data, tables, captions and all headline text.
    if document != report_html(e, png):
        raise ValueError("HTML does not reconcile with canonical evidence")
    visible = document.split("<script")[0].lower()
    if "doordash" in visible or visible.count(presentation_navigation.PROVENANCE.lower()) != 1:
        raise ValueError("Expected one general provenance statement")
    if len(parser.anchors) != 7:
        raise ValueError("Expected seven tab anchors")
    if re.search(r"\b(?:todo|tbd|placeholder)\b", visible):
        raise ValueError("Unfinished report text")


def render_outputs(context: PipelineContext) -> Path:
    start = perf_counter()
    e = load_evidence(context)
    context.paths.create()
    png = context.paths.images / "champion_model_map.png"
    html = context.resolve_output_path("reports/control_tower.html")
    html.parent.mkdir(parents=True, exist_ok=True)
    canvas = champion_canvas(e)
    buffer = io.BytesIO()
    canvas.image.save(buffer, format="PNG")
    if not png.exists() or png.read_bytes() != buffer.getvalue():
        png.write_bytes(buffer.getvalue())
    html.write_text(report_html(e, png.read_bytes()), encoding="utf-8")
    boards = storyboards(e)
    layout = {
        "champion_map": [asdict(b) for b in canvas.boxes],
        "scenes": {
            name: [
                [asdict(b) for b in scene_canvas(e, s, i, name).boxes] for i, s in enumerate(scenes)
            ]
            for name, scenes in boards.items()
        },
    }
    layout_path = context.paths.manifests / "layout_validation.json"
    write_generation_manifest(layout, layout_path)
    board_path = context.paths.manifests / "storyboards.json"
    write_generation_manifest(
        {name: [asdict(s) for s in scenes] for name, scenes in boards.items()}, board_path
    )
    runtimes: dict[str, float] = {"report_and_png": perf_counter() - start}
    for name, scenes in boards.items():
        tick = perf_counter()
        encode_video(e, scenes, name, context.paths.video / f"{name}.mp4")
        runtimes[name] = perf_counter() - tick
    tick = perf_counter()
    validations = validate_outputs(context)
    runtimes["output_validation"] = perf_counter() - tick
    runtimes["total_render"] = perf_counter() - start
    paths = [png, html, layout_path, board_path] + [
        context.paths.video / f"{name}.mp4" for name in boards
    ]
    executable, version = packaged_ffmpeg()
    git = subprocess.run(
        [
            "git",
            "-c",
            f"safe.directory={context.paths.repository_root.as_posix()}",
            "rev-parse",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    manifest: dict[str, Any] = {
        "project_id": context.paths.project_id,
        "configuration": context.configuration.model_dump(mode="json"),
        "source": e.stages["demand_daily"],
        "data_grain": "date \u00d7 store \u00d7 category; labor date \u00d7 store",
        "seed": context.configuration.seed,
        "model_configurations": e.stages["predictions"]["configuration"]["forecasting"],
        "model_scores": e.tables["network_scorecard"],
        "champion_counts": e.counts,
        "no_champion_count": e.counts["No eligible champion"],
        "retrospective_caveat": RETROSPECTIVE,
        "diagnostic_priorities": e.tables["dri_exception_queue"][:3],
        "labor_assumptions": e.stages["operations"]["configuration"]["labor"],
        "scenario_results": e.tables["scenario_summary"],
        "retrospective_actual_results": e.tables["retrospective_summary"],
        "inventory_classification": INVENTORY_LABEL,
        "upstream_metadata": e.stages,
        "upstream_sha256": e.hashes,
        "artifacts": {str(p): {"sha256": sha256(p), "size_bytes": p.stat().st_size} for p in paths},
        "png": {"width": 1080, "height": 1350},
        "media_validation": validations,
        "ffmpeg": {"executable": str(executable), "version": version, "sha256": sha256(executable)},
        "fonts": {str(p): sha256(p) for p in (FONT, BOLD)},
        "git_revision": git.stdout.strip() if git.returncode == 0 else None,
        "git_worktree": "uncommitted changes; not transfer-safe",
        "stage_runtimes_seconds": runtimes,
        "validation_status": "automated_checks_passed_browser_review_pending",
        "readiness": "READY FOR MANUAL STEP 6D REVIEW",
        "presentation_revision": (
            "Step 6D; modeling transparency and prototype calibration narrative"
        ),
        "video_titles": VIDEO_TITLES,
        "narrative": {
            "business_question": presentation_decisions.BUSINESS_QUESTION,
            "story_spine": presentation_decisions.SPINE,
            "forecast_decision": presentation_decisions.FORECAST_DECISION,
            "impact_conclusion": presentation_decisions.IMPACT_CONCLUSION,
            "recommendation": presentation_decisions.RECOMMENDATION,
            "final_base_allocation_summary": presentation_decisions.allocation_summary(e),
            "initially_exposed_prose_words": presentation_decisions.copy_words(
                html.read_text(encoding="utf-8")
            ),
            "copy_metric": "all tabs; excludes closed details, tables, scripts and SVG",
        },
        "tabs": list(presentation_navigation.TABS),
        "chart_specs": presentation_charts.chart_specs(e),
        "animation": {
            "world": (
                "persistent ten-store, three-state network; category-stream motion illustrative"
            ),
            "labor_transfers": presentation_world.transfers(e),
            "allocation_example_date": allocation_example(e)[0],
            "actions": {
                name: [asdict(scene) for scene in scenes] for name, scenes in boards.items()
            },
            "validation": "every encoded frame validates text bounds and intersections",
        },
        "executive_decision": e.executive,
    }
    path = context.paths.manifests / "run_manifest.json"
    write_generation_manifest(manifest, path)
    # Recheck upstream hashes after all rendering/decoding: analytics must remain frozen.
    for source, expected in e.hashes.items():
        if sha256(Path(source)) != expected:
            raise ValueError("Rendering modified upstream evidence")
    return path


def validate_outputs(context: PipelineContext) -> dict[str, Any]:
    e = load_evidence(context)
    png = context.paths.images / "champion_model_map.png"
    validate_png_dimensions(png, expected_width=1080, expected_height=1350)
    with Image.open(png) as image:
        if ImageChops.difference(image.convert("RGB"), champion_canvas(e).image).getbbox():
            raise ValueError("Champion map pixels do not reconcile")
    validate_html(
        context.resolve_output_path("reports/control_tower.html").read_text(encoding="utf-8"),
        e,
        png.read_bytes(),
    )
    result: dict[str, Any] = {
        "html_self_contained": True,
        "html_validation_method": "structural resource audit and exact evidence regeneration",
        "browser_visual_inspection": "not verified: local file URL blocked by browser policy",
        "champion_map_reconciliation": True,
        "narrative_reconciliation": True,
        "geometry_validation": True,
        "geometry_scope": "PIL frame text; CSS containment contracts. Browser geometry pending.",
        "tab_validation": "isolated JavaScript controller execution; browser review pending",
        "chart_count": len(presentation_charts.chart_specs(e)),
    }
    for name, scenes in storyboards(e).items():
        path = context.paths.video / f"{name}.mp4"
        metadata = validate_video(path, expected_frames=sum(s.seconds * 30 for s in scenes))
        if not 28 <= metadata["duration_seconds"] <= 32:
            raise ValueError("Social video duration must be 28-32 seconds")
        metadata["decoded_scene_mean_pixel_errors"] = validate_scene_pixels(e, scenes, name, path)
        result[name] = metadata
    board_path = context.paths.manifests / "storyboards.json"
    if json.loads(board_path.read_text(encoding="utf-8")) != json.loads(
        json.dumps({name: [asdict(s) for s in scenes] for name, scenes in storyboards(e).items()})
    ):
        raise ValueError("Storyboard provenance mismatch")
    return result
