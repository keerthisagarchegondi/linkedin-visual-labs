from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat

PACKAGE = "p27_prediction_time_integrity_auditor"

REPO = Path(__file__).resolve().parents[4]

ASSETS = REPO / "assets" / PACKAGE

DOCS = REPO / "docs" / "projects" / PACKAGE

DASHBOARD = ASSETS / "dashboard"

PUBLICATION = ASSETS / "publication"

IMAGES = ASSETS / "images"

RELEASE = ASSETS / "release"

EXPECTED_STEP5_FINGERPRINT = "7954203abe1cb0f5457c3658f2105cd16a0800528e81723ee970d259afe60ed0"

EXPECTED_RELEASE_DATA_SHA = "7d240598a0a3a0d7b73ab7c678b2a5c75661fa4721254f9db5dcd9d0c8c8f870"

EXPECTED_CLAIM_REGISTER_SHA = "b39a756a31e264030a105d990cdc17998afb664ecd28d9a3e3c459a837347a7f"

EXPECTED_FEATURE_CONTRACT_SHA = "1b42a4121f91278845504f114d7c10ecf74cd0ccf34eca9924e3914f047c87de"

EXPECTED_DASHBOARD_SHA = "33e68fe7e22131865f456a652073fce654fa0716427087506af1dd093cdf8e87"

EXPECTED_CASES = {
    "S1_CURRENT_CALL_DURATION",
    "S2_RANDOM_TEMPORAL_MIXING",
    "S3_GLOBAL_SUPERVISED_TRANSFORMATION",
    "S4_DUPLICATE_OVERLAP",
    "S5_POST_OUTCOME_CONFIRMATION_PROXY",
}

EXPECTED_MODELS = {
    "logistic_regression",
    "histogram_gradient_boosting",
}

FIGURES = (
    "audit_pipeline.png",
    "feature_availability_contract.png",
    "split_integrity_comparison.png",
    "model_performance_comparison.png",
    "leakage_inflation_map.png",
    "calibration_comparison.png",
    "business_targeting_distortion.png",
)

SCREENSHOTS = (
    "01_executive_decision.png",
    "02_leakage_cases.png",
    "03_feature_contract.png",
    "04_model_results.png",
    "05_audit_evidence.png",
    "06_publication.png",
)

FORBIDDEN_PREVIEW_NUMBERS = (
    "0.953",
    ".953",
    "0.778",
    ".778",
    "0.758",
    ".758",
    "0.677",
    ".677",
    "-0.081",
    "-.081",
    "+0.276",
    "+.276",
)

FORBIDDEN_PREVIEW_INTEGER_PATTERNS = (
    re.compile(r"(?<!\d)784(?!\d)"),
    re.compile(r"(?<!\d)321(?!\d)"),
    re.compile(r"(?<!\d)464(?!\d)"),
)

PLACEHOLDER_PATTERNS = (
    re.compile(
        r"\bTODO\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bTBD\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bFIXME\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bCHANGEME\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bLOREM\s+IPSUM\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"<\s*AUTHOR\s*>",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bYOUR\s+NAME\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bINSERT\s+(?:TEXT|VALUE|NAME|DOI|VENUE)\b",
        re.IGNORECASE,
    ),
)


def sha256(
    path: Path,
) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(
    path: Path,
) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        value,
        dict,
    ):
        raise RuntimeError(f"Expected JSON object: {path}")

    return value


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def assert_close(
    actual: float,
    expected: float,
    *,
    tolerance: float = 1e-8,
    label: str,
) -> None:
    if not math.isclose(
        actual,
        expected,
        rel_tol=tolerance,
        abs_tol=tolerance,
    ):
        raise RuntimeError(f"{label} mismatch: expected={expected}, actual={actual}")


def release_data() -> dict[str, Any]:
    return load_json(ASSETS / "release_data.json")


def claim_register() -> dict[str, Any]:
    return load_json(ASSETS / "claim_register.json")


def feature_contract() -> dict[str, Any]:
    return load_json(ASSETS / "feature_availability_contract.json")


def validate_source() -> dict[str, Any]:
    release = release_data()

    if release.get("release_status") != "PASS":
        raise RuntimeError("Frozen release status is not PASS.")

    if release.get("step5_fingerprint_sha256") != EXPECTED_STEP5_FINGERPRINT:
        raise RuntimeError("Step 5 fingerprint drift.")

    if release.get("safe_release_decision") != "PASS":
        raise RuntimeError("Safe release decision is not PASS.")

    if sha256(ASSETS / "release_data.json") != EXPECTED_RELEASE_DATA_SHA:
        raise RuntimeError("release_data.json hash drift.")

    if sha256(ASSETS / "claim_register.json") != EXPECTED_CLAIM_REGISTER_SHA:
        raise RuntimeError("claim_register.json hash drift.")

    if sha256(ASSETS / "feature_availability_contract.json") != EXPECTED_FEATURE_CONTRACT_SHA:
        raise RuntimeError("feature contract hash drift.")

    contract = feature_contract()

    if contract.get("prediction_moment") != "Immediately before the current outbound call begins.":
        raise RuntimeError("Prediction moment drift.")

    return {
        "release_status": "PASS",
        "step5_fingerprint": EXPECTED_STEP5_FINGERPRINT,
        "prediction_moment": contract["prediction_moment"],
    }


def validate_split() -> dict[str, Any]:
    release = release_data()

    independent = release["independent_validation"]

    assert_close(
        float(independent["temporal_roc_auc_gap"]),
        0.24119243646906585,
        tolerance=1e-7,
        label="temporal ROC AUC gap",
    )

    assert_close(
        float(independent["temporal_pr_auc_gap"]),
        0.042921488063624835,
        tolerance=1e-7,
        label="temporal PR AUC gap",
    )

    return {
        "temporal_roc_auc_gap": independent["temporal_roc_auc_gap"],
        "temporal_pr_auc_gap": independent["temporal_pr_auc_gap"],
    }


def validate_leakage_cases() -> dict[str, Any]:
    rows = read_csv(ASSETS / "leakage_model_results.csv")

    cases = {row["case_id"] for row in rows}

    models = {row["model_id"] for row in rows}

    if cases != EXPECTED_CASES:
        raise RuntimeError(
            f"Leakage-case set drift.\nExpected={sorted(EXPECTED_CASES)}\nFound={sorted(cases)}"
        )

    if models != EXPECTED_MODELS:
        raise RuntimeError("Leakage model set drift.")

    if len(rows) != 10:
        raise RuntimeError(f"Expected 10 leakage model rows; found {len(rows)}.")

    return {
        "scenario_count": len(cases),
        "model_result_count": len(rows),
    }


def _baseline_row(
    *,
    pipeline_id: str,
    model_id: str,
    partition: str,
) -> dict[str, Any]:
    release = release_data()

    rows = [
        row
        for row in release["baseline_model_results"]
        if (
            row.get("pipeline_id") == pipeline_id
            and row.get("model_id") == model_id
            and row.get("partition") == partition
        )
    ]

    if len(rows) != 1:
        raise RuntimeError(
            f"Baseline row cardinality failure: {pipeline_id}/{model_id}/{partition}"
        )

    row = rows[0]

    if not isinstance(
        row,
        dict,
    ):
        raise RuntimeError("Baseline result row must be a JSON object.")

    typed_row: dict[
        str,
        Any,
    ] = {}

    for key, value in row.items():
        if not isinstance(
            key,
            str,
        ):
            raise RuntimeError("Baseline result row contains a non-string key.")

        typed_row[key] = value

    return typed_row


def validate_models() -> dict[str, Any]:
    hgb = _baseline_row(
        pipeline_id="C_PREDICTION_TIME_SAFE",
        model_id="histogram_gradient_boosting",
        partition="test",
    )

    lr = _baseline_row(
        pipeline_id="C_PREDICTION_TIME_SAFE",
        model_id="logistic_regression",
        partition="test",
    )

    assert_close(
        float(hgb["roc_auc"]),
        0.5689190,
        tolerance=1e-6,
        label="safe HGB test ROC AUC",
    )

    assert_close(
        float(lr["roc_auc"]),
        0.6064233,
        tolerance=1e-6,
        label="safe LR test ROC AUC",
    )

    return {
        "models": sorted(EXPECTED_MODELS),
        "safe_hgb_test_roc_auc": hgb["roc_auc"],
        "safe_lr_test_roc_auc": lr["roc_auc"],
    }


def validate_metric_reconciliation() -> dict[str, Any]:
    independent = release_data()["independent_validation"]

    reconciled = int(independent["reconciled_metric_effect_count"])

    mismatches = int(independent["metric_effect_mismatch_count"])

    duplicate_overlap = int(independent["duplicate_train_test_overlap"])

    if reconciled != 60:
        raise RuntimeError(f"Expected 60 reconciled effects; found {reconciled}.")

    if mismatches != 0:
        raise RuntimeError(f"Metric reconciliation mismatches={mismatches}.")

    if duplicate_overlap != 618:
        raise RuntimeError(f"Duplicate overlap expected 618; found {duplicate_overlap}.")

    return {
        "reconciled_effects": reconciled,
        "mismatches": mismatches,
        "duplicate_overlap": duplicate_overlap,
    }


def validate_auditor() -> dict[str, Any]:
    release = release_data()

    independent = release["independent_validation"]

    if release["safe_release_decision"] != "PASS":
        raise RuntimeError("Safe release decision drift.")

    if independent["safe_release_status"] != "PASS":
        raise RuntimeError("Independent safe release status drift.")

    if independent["no_false_pass"] is not True:
        raise RuntimeError("Independent no_false_pass is not true.")

    rows = read_csv(ASSETS / "leakage_model_results.csv")

    invalid = [
        row
        for row in rows
        if row.get("actual_auditor_result")
        not in {
            "BLOCK",
            "WARN",
            "PASS",
        }
    ]

    if invalid:
        raise RuntimeError("Invalid auditor result detected.")

    return {
        "safe_release": "PASS",
        "no_false_pass": True,
    }


def validate_claim_register() -> dict[str, Any]:
    claims = claim_register()

    raw = claims["claims"]

    approved = [claim for claim in raw if claim.get("approved_for_public_use") is True]

    if len(approved) != 8:
        raise RuntimeError(f"Expected eight approved claims; found {len(approved)}.")

    if claims["preview_claims_approved"] is not False:
        raise RuntimeError("Preview claims unexpectedly approved.")

    if claims["unsupported_claims_approved"] is not False:
        raise RuntimeError("Unsupported claims unexpectedly approved.")

    ids = [str(claim["claim_id"]) for claim in approved]

    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate approved claim IDs.")

    return {
        "approved_claim_count": len(approved),
        "approved_claim_ids": sorted(ids),
    }


def validate_figures() -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    for filename in FIGURES:
        path = IMAGES / filename

        if not path.is_file():
            raise RuntimeError(f"Research figure missing: {filename}")

        with Image.open(path) as image:
            if image.size != (
                1080,
                1350,
            ):
                raise RuntimeError(f"{filename}: unexpected geometry {image.size}")

            if image.mode != "RGB":
                raise RuntimeError(f"{filename}: expected RGB; found {image.mode}")

        results.append(
            {
                "filename": filename,
                "sha256": sha256(path),
            }
        )

    return {
        "figure_count": len(results),
        "figures": results,
    }


def _find_binary(
    name: str,
) -> Path:
    found = shutil.which(name)

    if found:
        return Path(found)

    exe = name if name.lower().endswith(".exe") else f"{name}.exe"

    candidates: list[Path] = []

    local = os.environ.get("LOCALAPPDATA")

    if local:
        winget_root = Path(local) / "Microsoft" / "WinGet" / "Packages"

        if winget_root.exists():
            candidates.extend(winget_root.glob(f"**/{exe}"))

    for root in (
        Path(r"C:\ffmpeg"),
        Path(r"C:\Program Files"),
        Path(r"C:\Program Files (x86)"),
    ):
        if root.exists():
            candidates.extend(root.glob(f"**/{exe}"))

    candidates = sorted({path.resolve() for path in candidates if path.is_file()})

    if not candidates:
        raise RuntimeError(f"{name} could not be resolved.")

    return candidates[0]


def _referenced_mp4s() -> set[Path]:
    found: set[Path] = set()

    json_files = list(ASSETS.rglob("*.json"))

    json_files.extend(DOCS.rglob("*.json"))

    pattern = re.compile(
        r'([^"\r\n]+\.mp4)',
        flags=re.IGNORECASE,
    )

    for json_path in json_files:
        try:
            text = json_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for token in pattern.findall(text):
            cleaned = token.replace(
                "\\\\",
                "\\",
            ).strip()

            candidate = Path(cleaned)

            possible: list[Path] = []

            if candidate.is_absolute():
                possible.append(candidate)
            else:
                possible.extend(
                    [
                        REPO / candidate,
                        ASSETS / candidate,
                        json_path.parent / candidate,
                    ]
                )

            for path in possible:
                if path.is_file() and path.suffix.lower() == ".mp4":
                    found.add(path.resolve())

    return found


def production_video() -> Path:
    candidates = _referenced_mp4s()

    if not candidates:
        candidates = {
            path.resolve()
            for path in ASSETS.rglob("*.mp4")
            if not any(
                marker in path.name.lower()
                for marker in (
                    "preview",
                    "draft",
                    "temp",
                    "scene",
                    "keyframe",
                    "test",
                )
            )
        }

    if not candidates:
        raise RuntimeError("No Project 7 production MP4 found.")

    preferred = [
        path
        for path in candidates
        if any(
            marker in path.name.lower()
            for marker in (
                "final",
                "master",
                "project7",
                "prediction",
                "integrity",
            )
        )
    ]

    pool = preferred if preferred else list(candidates)

    selected = sorted(
        pool,
        key=lambda path: (
            path.stat().st_size,
            path.as_posix(),
        ),
        reverse=True,
    )[0]

    return selected


def validate_video() -> dict[str, Any]:
    video = production_video()

    ffprobe = _find_binary("ffprobe")

    ffmpeg = _find_binary("ffmpeg")

    result = subprocess.run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            ("stream=width,height,r_frame_rate,nb_frames,pix_fmt,codec_name:format=duration"),
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    metadata = json.loads(result.stdout)

    streams = metadata.get("streams", [])

    if len(streams) != 1:
        raise RuntimeError("Expected exactly one primary video stream.")

    stream = streams[0]

    width = int(stream["width"])

    height = int(stream["height"])

    duration = float(metadata["format"]["duration"])

    numerator, denominator = str(stream["r_frame_rate"]).split("/")

    fps = float(numerator) / float(denominator)

    if (
        width,
        height,
    ) != (
        1080,
        1350,
    ):
        raise RuntimeError(f"Video geometry drift: {width}x{height}")

    if not (44.8 <= duration <= 45.2):
        raise RuntimeError(f"Video duration drift: {duration}")

    if not (29.8 <= fps <= 30.2):
        raise RuntimeError(f"Video FPS drift: {fps}")

    if stream.get("pix_fmt") != "yuv420p":
        raise RuntimeError("Production video pixel format must be yuv420p.")

    nb_frames_raw = stream.get("nb_frames")

    if nb_frames_raw not in (
        None,
        "N/A",
    ):
        frames = int(nb_frames_raw)

        if not (1345 <= frames <= 1355):
            raise RuntimeError(f"Video frame-count drift: {frames}")
    else:
        frames = None

    # --------------------------------------------------------------
    # Content sanity:
    # extract five frames and reject blank / near-uniform output.
    # --------------------------------------------------------------

    sample_times = (
        2.0,
        11.0,
        22.0,
        33.0,
        43.0,
    )

    sample_stats: list[dict[str, float]] = []

    with tempfile.TemporaryDirectory(prefix="p7-video-content-") as tmp:
        temp_root = Path(tmp)

        for index, timestamp in enumerate(
            sample_times,
            start=1,
        ):
            frame = temp_root / f"frame_{index}.png"

            subprocess.run(
                [
                    str(ffmpeg),
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-ss",
                    str(timestamp),
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    "-y",
                    str(frame),
                ],
                check=True,
            )

            if not frame.is_file():
                raise RuntimeError("Video content frame extraction failed.")

            with Image.open(frame) as image:
                gray = image.convert("L")

                stat = ImageStat.Stat(gray)

                stddev = float(stat.stddev[0])

                extrema = gray.getextrema()

            minimum = extrema[0]

            maximum = extrema[1]

            if isinstance(
                minimum,
                tuple,
            ) or isinstance(
                maximum,
                tuple,
            ):
                raise RuntimeError("Expected scalar extrema for grayscale video-validation frame.")

            contrast = float(maximum - minimum)

            if stddev < 5.0:
                raise RuntimeError(
                    f"Video sample is near-uniform / blank: t={timestamp}, stddev={stddev}"
                )

            if contrast < 20.0:
                raise RuntimeError(
                    f"Video sample lacks visual contrast: t={timestamp}, contrast={contrast}"
                )

            sample_stats.append(
                {
                    "timestamp": timestamp,
                    "stddev": stddev,
                    "contrast": contrast,
                }
            )

    return {
        "path": str(video.relative_to(REPO)).replace(
            "\\",
            "/",
        ),
        "sha256": sha256(video),
        "size_bytes": video.stat().st_size,
        "width": width,
        "height": height,
        "duration": duration,
        "fps": fps,
        "frames": frames,
        "codec": stream.get("codec_name"),
        "pix_fmt": stream.get("pix_fmt"),
        "content_samples": sample_stats,
    }


def validate_dashboard() -> dict[str, Any]:
    path = DASHBOARD / "p27_prediction_time_integrity_auditor.html"

    if not path.is_file():
        raise RuntimeError("Approved dashboard missing.")

    if sha256(path) != EXPECTED_DASHBOARD_SHA:
        raise RuntimeError("Approved dashboard SHA drift.")

    source = path.read_text(encoding="utf-8")

    tabs = (
        "Executive Decision",
        "Leakage Cases",
        "Feature Contract",
        "Model Results",
        "Audit Evidence",
        "Publication",
    )

    for tab in tabs:
        if tab not in source:
            raise RuntimeError(f"Dashboard tab missing: {tab}")

    if source.count('data-tab-panel="') != 6:
        raise RuntimeError("Dashboard panel count is not six.")

    if re.search(
        r'<div class="block-kicker">',
        source,
        flags=re.IGNORECASE,
    ):
        raise RuntimeError("Old visible block-kicker scaffold returned.")

    if re.search(
        r'<div class="eyebrow">\s*TAB\s+[1-6]\s*</div>',
        source,
        flags=re.IGNORECASE,
    ):
        raise RuntimeError("Old TAB N scaffold returned.")

    if source.count('class="journal-lead"') != 6:
        raise RuntimeError("Dashboard journal-lead count drift.")

    for filename in SCREENSHOTS:
        if not (DASHBOARD / "screenshots" / filename).is_file():
            raise RuntimeError(f"Dashboard screenshot missing: {filename}")

    if not (DASHBOARD / "p27_prediction_time_integrity_auditor_contact_sheet.png").is_file():
        raise RuntimeError("Dashboard contact sheet missing.")

    return {
        "tab_count": 6,
        "journal_leads": 6,
        "html_sha256": sha256(path),
    }


def validate_manuscript() -> dict[str, Any]:
    state = load_json(DOCS / "STEP8_PUBLICATION_STATE.json")

    if state["status"] != "PASS":
        raise RuntimeError("Step 8 state is not PASS.")

    manuscript = PUBLICATION / "leakagebench_manuscript.md"

    html_path = PUBLICATION / "leakagebench_manuscript.html"

    trace = PUBLICATION / "leakagebench_claim_traceability.csv"

    for path in (
        manuscript,
        html_path,
        trace,
    ):
        if not path.is_file():
            raise RuntimeError(f"Publication artifact missing: {path.name}")

    text = manuscript.read_text(encoding="utf-8")

    required = (
        "## Abstract",
        "## 1. Introduction",
        "## 2. Prediction-Time Contract",
        "## 3. Benchmark Design",
        "## 4. Released Results",
        "## 5. Research Figures",
        "## 6. Discussion",
        "## 7. Limitations",
        "## 8. Reproducibility and Evidence Provenance",
        "## 9. Data Availability",
        "## 10. Code and Artifact Availability",
        "## 11. Responsible Communication Statement",
        "## 12. Conclusion",
    )

    for heading in required:
        if heading not in text:
            raise RuntimeError(f"Manuscript heading missing: {heading}")

    rows = read_csv(trace)

    if len(rows) != 8:
        raise RuntimeError("Claim traceability must contain eight rows.")

    return {
        "traceability_rows": len(rows),
        "markdown_sha256": sha256(manuscript),
        "html_sha256": sha256(html_path),
    }


def validate_publication_metadata() -> dict[str, Any]:
    metadata = load_json(PUBLICATION / "leakagebench_publication_metadata.json")

    if metadata["external_publication_ready"] is not False:
        raise RuntimeError("External publication unexpectedly ready.")

    if metadata["external_publication_status"] != "LOCKED":
        raise RuntimeError("External publication must remain LOCKED.")

    if metadata["authors"] != []:
        raise RuntimeError("Author metadata was invented.")

    if metadata["publication_venue"] is not None:
        raise RuntimeError("Publication venue was invented.")

    if metadata["manuscript_doi"] is not None:
        raise RuntimeError("Manuscript DOI was invented.")

    if metadata["manuscript_license"] is not None:
        raise RuntimeError("Manuscript license was invented.")

    if metadata["peer_reviewed"] is not False:
        raise RuntimeError("Peer-review status drift.")

    if metadata["approved_public_claim_count"] != 8:
        raise RuntimeError("Approved claim count drift.")

    return {
        "external_publication": "LOCKED",
        "peer_reviewed": False,
        "approved_claims": 8,
    }


def _text_without_embedded_images(
    path: Path,
) -> str:
    text = path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".html":
        text = re.sub(
            r'data:image/[^"\']+',
            "DATA_IMAGE_REMOVED",
            text,
            flags=re.IGNORECASE,
        )

    return text


def placeholder_scan() -> dict[str, Any]:
    targets = (
        PUBLICATION / "leakagebench_manuscript.md",
        PUBLICATION / "leakagebench_manuscript.html",
    )

    failures: list[str] = []

    for path in targets:
        text = _text_without_embedded_images(path)

        for pattern in PLACEHOLDER_PATTERNS:
            match = pattern.search(text)

            if match:
                failures.append(f"{path.name}: {match.group(0)}")

    if failures:
        raise RuntimeError("Manuscript placeholder scan failed:\n" + "\n".join(failures))

    return {
        "files_scanned": [path.name for path in targets],
        "placeholder_matches": 0,
    }


def preview_number_scan() -> dict[str, Any]:
    targets = (
        PUBLICATION / "leakagebench_manuscript.md",
        PUBLICATION / "leakagebench_manuscript.html",
        PUBLICATION / "leakagebench_publication_metadata.json",
        PUBLICATION / "leakagebench_claim_traceability.csv",
        DASHBOARD / "p27_prediction_time_integrity_auditor.html",
    )

    failures: list[str] = []

    for path in targets:
        text = _text_without_embedded_images(path)

        for token in FORBIDDEN_PREVIEW_NUMBERS:
            if token in text:
                failures.append(f"{path.name}: forbidden preview value {token}")

        for pattern in FORBIDDEN_PREVIEW_INTEGER_PATTERNS:
            match = pattern.search(text)

            if match:
                failures.append(f"{path.name}: forbidden preview integer {match.group(0)}")

    if failures:
        raise RuntimeError("Preview-number leakage detected:\n" + "\n".join(failures))

    return {
        "files_scanned": [path.name for path in targets],
        "preview_number_matches": 0,
    }


def _traceability_value(
    value: Any,
) -> str:
    """Return the Step 8 CSV representation of a claim field."""

    if value is None:
        return ""

    if isinstance(
        value,
        (
            dict,
            list,
        ),
    ):
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
        )

    return str(value)


def claim_evidence_reconciliation() -> dict[str, Any]:
    """Reconcile frozen claims against publication traceability.

    Frozen V1 mandatory fields are:
      claim_id
      claim
      claim_label
      evidence
      approved_for_public_use

    Traceability fields such as scope, caveat, metric, unit,
    calculation, value and review_status are optional. They must
    reconcile exactly when present, and remain blank when absent.
    """

    register = claim_register()

    approved = {
        str(claim["claim_id"]): claim
        for claim in register["claims"]
        if claim.get("approved_for_public_use") is True
    }

    if len(approved) != 8:
        raise RuntimeError(f"Expected exactly eight approved frozen claims; found {len(approved)}.")

    trace_rows = read_csv(PUBLICATION / "leakagebench_claim_traceability.csv")

    if len(trace_rows) != 8:
        raise RuntimeError(f"Expected eight traceability rows; found {len(trace_rows)}.")

    required_columns = (
        "claim_id",
        "claim",
        "claim_label",
        "metric",
        "value",
        "unit",
        "evidence",
        "calculation",
        "scope",
        "caveat",
        "approved_for_public_use",
        "review_status",
    )

    if trace_rows:
        missing_columns = [column for column in required_columns if column not in trace_rows[0]]

        if missing_columns:
            raise RuntimeError(f"Claim traceability CSV missing columns: {missing_columns}")

    trace: dict[str, dict[str, str]] = {}

    for row in trace_rows:
        claim_id = row["claim_id"].strip()

        if not claim_id:
            raise RuntimeError("Traceability row has empty claim_id.")

        if claim_id in trace:
            raise RuntimeError(f"Duplicate traceability claim ID: {claim_id}")

        trace[claim_id] = row

    if set(trace) != set(approved):
        missing = sorted(set(approved) - set(trace))

        extra = sorted(set(trace) - set(approved))

        raise RuntimeError(f"Claim ID set mismatch.\nMissing={missing}\nExtra={extra}")

    mandatory_fields = (
        "claim_id",
        "claim",
        "claim_label",
        "evidence",
        "approved_for_public_use",
    )

    compared_fields = (
        "claim_id",
        "claim",
        "claim_label",
        "metric",
        "value",
        "unit",
        "evidence",
        "calculation",
        "scope",
        "caveat",
        "approved_for_public_use",
        "review_status",
    )

    optional_blank_fields: dict[
        str,
        list[str],
    ] = {}

    for claim_id, claim in approved.items():
        for field in mandatory_fields:
            if field not in claim:
                raise RuntimeError(f"{claim_id}: missing mandatory field {field!r}.")

        public_text = str(claim["claim"]).strip()

        if not public_text:
            raise RuntimeError(f"{claim_id}: empty public claim text.")

        label = str(claim["claim_label"]).strip()

        if not label:
            raise RuntimeError(f"{claim_id}: empty claim_label.")

        if label in {
            "PREVIEW_ONLY",
            "UNSUPPORTED",
        }:
            raise RuntimeError(f"{claim_id}: prohibited approved claim class {label}.")

        evidence = claim["evidence"]

        if isinstance(
            evidence,
            list,
        ):
            if not evidence:
                raise RuntimeError(f"{claim_id}: empty evidence list.")

            if any(not str(item).strip() for item in evidence):
                raise RuntimeError(f"{claim_id}: evidence list contains an empty reference.")

        elif not str(evidence).strip():
            raise RuntimeError(f"{claim_id}: missing evidence.")

        if claim["approved_for_public_use"] is not True:
            raise RuntimeError(f"{claim_id}: approval state drift.")

        trace_claim = trace[claim_id]

        for field in compared_fields:
            expected = _traceability_value(claim.get(field))

            actual = trace_claim.get(
                field,
                "",
            )

            if actual != expected:
                raise RuntimeError(
                    f"{claim_id}: traceability field "
                    f"{field!r} drift.\n"
                    f"Expected={expected!r}\n"
                    f"Actual={actual!r}"
                )

        optional_blank_fields[claim_id] = [
            field
            for field in (
                "metric",
                "value",
                "unit",
                "calculation",
                "scope",
                "caveat",
                "review_status",
            )
            if _traceability_value(claim.get(field)) == ""
        ]

    return {
        "approved_claims": len(approved),
        "traceability_rows": len(trace_rows),
        "mismatches": 0,
        "mandatory_evidence_fields": "PASS",
        "optional_blank_fields_preserved": (optional_blank_fields),
        "frozen_claim_register_mutated": False,
    }


def _release_payload(
    video: Path,
) -> list[
    tuple[
        Path,
        str,
    ]
]:
    paths: list[Path] = []

    for filename in (
        "release_data.json",
        "claim_register.json",
        "feature_availability_contract.json",
        "benchmark_model_results.csv",
        "leakage_model_results.csv",
        "leakage_inflation_results.csv",
        "independent_reconciliation.csv",
    ):
        paths.append(ASSETS / filename)

    for filename in FIGURES:
        paths.append(IMAGES / filename)

    paths.append(video)

    paths.append(DASHBOARD / "p27_prediction_time_integrity_auditor.html")

    paths.append(DASHBOARD / "dashboard_manifest.json")

    paths.append(DASHBOARD / "p27_prediction_time_integrity_auditor_contact_sheet.png")

    for filename in SCREENSHOTS:
        paths.append(DASHBOARD / "screenshots" / filename)

    for path in sorted(PUBLICATION.iterdir()):
        if path.is_file() and path.name != "leakagebench_publication_manifest.json":
            paths.append(path)

    for path in sorted((REPO / "src" / "linkedin_visual_labs" / "projects" / PACKAGE).glob("*.py")):
        paths.append(path)

    for filename in (
        "STEP7_DASHBOARD_STATE.json",
        "STEP8_PUBLICATION_STATE.json",
    ):
        paths.append(DOCS / filename)

    unique: dict[str, Path] = {}

    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"Release payload missing: {path}")

        relative = path.relative_to(REPO)

        arcname = "LeakageBench/" + relative.as_posix()

        unique[arcname] = path

    return [
        (
            path,
            arcname,
        )
        for arcname, path in sorted(unique.items())
    ]


def build_release(
    video: Path,
) -> dict[str, Any]:
    RELEASE.mkdir(
        parents=True,
        exist_ok=True,
    )

    checksum_file = RELEASE / "artifact_checksums.sha256"

    zip_path = RELEASE / "LeakageBench_Project7_release.zip"

    zip_checksum = RELEASE / "LeakageBench_Project7_release.zip.sha256"

    manifest_path = RELEASE / "step9_release_manifest.json"

    payload = _release_payload(video)

    checksum_lines = [f"{sha256(path)}  {arcname}" for path, arcname in payload]

    checksum_file.write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    checksum_arcname = "LeakageBench/" + checksum_file.relative_to(REPO).as_posix()

    if zip_path.exists():
        zip_path.unlink()

    fixed_time = (
        1980,
        1,
        1,
        0,
        0,
        0,
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path, arcname in payload:
            info = zipfile.ZipInfo(
                arcname,
                fixed_time,
            )

            info.compress_type = zipfile.ZIP_DEFLATED

            info.external_attr = 0o100644 << 16

            archive.writestr(
                info,
                path.read_bytes(),
            )

        info = zipfile.ZipInfo(
            checksum_arcname,
            fixed_time,
        )

        info.compress_type = zipfile.ZIP_DEFLATED

        info.external_attr = 0o100644 << 16

        archive.writestr(
            info,
            checksum_file.read_bytes(),
        )

    zip_sha = sha256(zip_path)

    zip_checksum.write_text(
        f"{zip_sha}  {zip_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )

    expected_entries = {arcname for _, arcname in payload}

    expected_entries.add(checksum_arcname)

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:
        names = set(archive.namelist())

        if names != expected_entries:
            missing = sorted(expected_entries - names)

            extra = sorted(names - expected_entries)

            raise RuntimeError(f"Release ZIP content mismatch.\nMissing={missing}\nExtra={extra}")

        for path, arcname in payload:
            archived_hash = hashlib.sha256(archive.read(arcname)).hexdigest()

            if archived_hash != sha256(path):
                raise RuntimeError(f"ZIP hash mismatch: {arcname}")

    manifest = {
        "schema_version": 1,
        "release_identity": ("LeakageBench Project 7"),
        "status": "PASS",
        "step5_fingerprint": (EXPECTED_STEP5_FINGERPRINT),
        "approved_dashboard_sha256": (EXPECTED_DASHBOARD_SHA),
        "payload_file_count": len(payload),
        "checksums_file": checksum_file.name,
        "zip_filename": zip_path.name,
        "zip_sha256": zip_sha,
        "zip_size_bytes": (zip_path.stat().st_size),
        "production_video": str(video.relative_to(REPO)).replace(
            "\\",
            "/",
        ),
        "business_logic_recomputed": False,
        "external_publication_status": "LOCKED",
    }

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return manifest


def verify_release() -> dict[str, Any]:
    manifest = load_json(RELEASE / "step9_release_manifest.json")

    zip_path = RELEASE / manifest["zip_filename"]

    if not zip_path.is_file():
        raise RuntimeError("Release ZIP missing.")

    actual_zip_sha = sha256(zip_path)

    if actual_zip_sha != manifest["zip_sha256"]:
        raise RuntimeError("Release ZIP SHA mismatch.")

    sidecar = RELEASE / "LeakageBench_Project7_release.zip.sha256"

    expected_line = f"{actual_zip_sha}  {zip_path.name}"

    actual_line = sidecar.read_text(encoding="utf-8").strip()

    if actual_line != expected_line:
        raise RuntimeError("Release ZIP sidecar checksum mismatch.")

    return {
        "zip_filename": zip_path.name,
        "zip_sha256": actual_zip_sha,
        "zip_size_bytes": (zip_path.stat().st_size),
    }


def validate_all() -> dict[str, Any]:
    video = validate_video()

    gates = {
        "9.2_source_validation": validate_source(),
        "9.3_split_validation": validate_split(),
        "9.4_leakage_cases": validate_leakage_cases(),
        "9.5_models": validate_models(),
        "9.6_metric_reconciliation": (validate_metric_reconciliation()),
        "9.7_auditor_release": validate_auditor(),
        "9.8_claim_register": validate_claim_register(),
        "9.9_research_figures": validate_figures(),
        "9.10_video": video,
        "9.11_dashboard": validate_dashboard(),
        "9.12_manuscript": validate_manuscript(),
        "9.13_publication_metadata": (validate_publication_metadata()),
    }

    return gates


def run_all() -> dict[str, Any]:
    RELEASE.mkdir(
        parents=True,
        exist_ok=True,
    )

    gates = validate_all()

    video_path = REPO / gates["9.10_video"]["path"]

    release_manifest = build_release(video_path)

    release_verification = verify_release()

    receipt = {
        "schema_version": 1,
        "status": "PASS",
        "run_all": "PASS",
        "gates": gates,
        "9.14_checksums": {
            "status": "PASS",
            "path": (f"assets/{PACKAGE}/release/artifact_checksums.sha256"),
        },
        "9.15_release_zip": {
            "status": "PASS",
            "filename": release_manifest["zip_filename"],
            "sha256": release_manifest["zip_sha256"],
        },
        "9.16_release_zip_verification": {
            "status": "PASS",
            **release_verification,
        },
        "business_logic_recomputed": False,
        "external_publication_status": "LOCKED",
    }

    receipt_path = RELEASE / "run_all_receipt.json"

    receipt_path.write_text(
        json.dumps(
            receipt,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=(f"python -m linkedin_visual_labs.projects.{PACKAGE}.release_acceptance"),
    )

    parser.add_argument(
        "command",
        choices=(
            "run-all",
            "validate",
            "verify-release",
            "placeholder-scan",
            "preview-number-scan",
            "claim-reconcile",
        ),
    )

    args = parser.parse_args()

    if args.command == "run-all":
        result = run_all()

    elif args.command == "validate":
        result = validate_all()

    elif args.command == "verify-release":
        result = verify_release()

    elif args.command == "placeholder-scan":
        result = placeholder_scan()

    elif args.command == "preview-number-scan":
        result = preview_number_scan()

    elif args.command == "claim-reconcile":
        result = claim_evidence_reconciliation()

    else:
        raise AssertionError(args.command)

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
