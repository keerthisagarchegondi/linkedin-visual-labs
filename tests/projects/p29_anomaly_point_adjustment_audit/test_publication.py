from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.presentation import (
    load_frozen_release,
)
from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.publication import (
    PUBLIC_CREATOR,
    PUBLIC_VERSION,
    TITLE,
    _manuscript_markdown,
    build_publication,
    publication_inputs,
)
from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.reproduction import (
    build_publication_input_bundle,
)


def test_manuscript_uses_frozen_primary_result() -> None:
    text = _manuscript_markdown(load_frozen_release())
    assert TITLE in text
    assert "P9-C001" in text
    assert "UNRESOLVED" in text


def test_publication_inputs_default_to_canonical_paths() -> None:
    inputs = publication_inputs()
    assert inputs.release_data_path.name == "release_data.json"
    assert inputs.claim_register_path.name == "claim_register.json"
    assert inputs.source_provenance_path.name == "source_provenance.json"
    assert all(
        path.is_file()
        for path in (
            inputs.release_data_path,
            inputs.claim_register_path,
            inputs.source_provenance_path,
        )
    )


def test_publication_inputs_require_complete_clean_bundle(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing clean publication input release_data"):
        publication_inputs(tmp_path)


def test_publication_input_bundle_is_hash_identical(tmp_path: Path) -> None:
    repository = Path.cwd()
    receipt = build_publication_input_bundle(repository, tmp_path)
    manifest = json.loads(receipt.manifest_path.read_text(encoding="utf-8"))
    assert receipt.file_count == 3
    assert all(entry["equality"] == "PASS" for entry in manifest["entries"])
    routed = publication_inputs(receipt.bundle_root)
    assert routed.release_data_path.is_relative_to(receipt.bundle_root)
    assert routed.claim_register_path.is_relative_to(receipt.bundle_root)
    assert routed.source_provenance_path.is_relative_to(receipt.bundle_root)


def test_publication_routes_all_clean_inputs_and_figure_evidence(tmp_path: Path) -> None:
    repository = Path.cwd()
    receipt = build_publication_input_bundle(repository, tmp_path)
    evidence_root = tmp_path / "evidence"
    shutil.copytree(
        repository / "outputs" / "p29_anomaly_point_adjustment_audit" / "figures",
        evidence_root / "figures",
    )
    result = build_publication(
        root=tmp_path / "output",
        evidence_root=evidence_root,
        input_root=receipt.bundle_root,
    )
    assert Path(result["markdown"]).is_relative_to(tmp_path / "output")
    assert Path(result["docx"]).is_file()
    assert Path(result["pdf"]).is_file()


def test_publication_emits_final_public_metadata_without_placeholders(tmp_path: Path) -> None:
    result = build_publication(root=tmp_path / "output")
    metadata_root = Path(result["markdown"]).parents[1] / "publication_metadata"
    citation = (metadata_root / "CITATION.cff").read_text(encoding="utf-8")
    zenodo = json.loads((metadata_root / "zenodo.json").read_text(encoding="utf-8"))
    status = json.loads((metadata_root / "publication_status.json").read_text(encoding="utf-8"))
    manuscript = Path(result["markdown"]).read_text(encoding="utf-8")

    assert f'name: "{PUBLIC_CREATOR}"' in citation
    assert f'version: "{PUBLIC_VERSION}"' in citation
    assert zenodo == {
        "creators": [{"name": PUBLIC_CREATOR}],
        "publication_date": None,
        "title": TITLE,
        "version": PUBLIC_VERSION,
    }
    assert status["author_metadata"] == PUBLIC_CREATOR
    assert status["public_version"] == PUBLIC_VERSION
    assert all(
        status[name] == "NOT_PERFORMED"
        for name in ("github_release", "zenodo", "arxiv", "journal", "portfolio", "linkedin")
    )
    assert "AUTHOR_INPUT_REQUIRED" not in "\n".join(
        (citation, manuscript, json.dumps(zenodo), json.dumps(status))
    )
    assert "0.1.0-local" not in "\n".join(
        (citation, manuscript, json.dumps(zenodo), json.dumps(status))
    )
    assert "orcid" not in json.dumps(zenodo).lower()
    assert "doi" not in json.dumps(zenodo).lower()


def test_publication_clean_mode_never_falls_back_to_canonical_inputs(tmp_path: Path) -> None:
    receipt = build_publication_input_bundle(Path.cwd(), tmp_path)
    (receipt.bundle_root / "manifests" / "claim_register.json").unlink()
    with pytest.raises(FileNotFoundError, match="missing clean publication input claim_register"):
        build_publication(input_root=receipt.bundle_root)
