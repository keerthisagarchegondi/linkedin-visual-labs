from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.config import (
    Project8Config,
    default_config_path,
    load_config,
    load_default_config,
)
from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.identifiers import (
    evidence_id,
    experiment_id,
)
from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.reference import (
    load_reference_protocol,
)
from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.sampling import (
    expected_sampled_recall_at_k,
)
from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.validation import (
    repository_root,
    validate_config,
    validate_reference,
)


def _valid_config_mapping() -> dict[str, object]:
    raw = yaml.safe_load(default_config_path().read_text(encoding="utf-8"))

    assert isinstance(
        raw,
        dict,
    )

    return dict(raw)


def test_config_rejects_negative_root_seed() -> None:
    mapping = _valid_config_mapping()
    mapping["root_seed"] = -1

    with pytest.raises(
        ValueError,
        match="root_seed must be >= 0",
    ):
        Project8Config.from_mapping(mapping)


def test_config_rejects_empty_sensitivity_grid() -> None:
    mapping = _valid_config_mapping()
    mapping["sensitivity_grid_negative_draws"] = []

    with pytest.raises(
        ValueError,
        match="sensitivity grid cannot be empty",
    ):
        Project8Config.from_mapping(mapping)


def test_config_rejects_nonincreasing_sensitivity_grid() -> None:
    mapping = _valid_config_mapping()
    mapping["sensitivity_grid_negative_draws"] = [
        1,
        2,
        2,
    ]

    with pytest.raises(
        ValueError,
        match="sensitivity grid must be strictly increasing",
    ):
        Project8Config.from_mapping(mapping)


def test_config_rejects_reference_draws_equal_candidate_count() -> None:
    mapping = _valid_config_mapping()

    mapping["reference_negative_draws"] = mapping["n_items"]

    with pytest.raises(
        ValueError,
        match="reference negative draws must be < n_items",
    ):
        Project8Config.from_mapping(mapping)


def test_config_rejects_missing_key() -> None:
    mapping = _valid_config_mapping()

    mapping.pop("root_seed")

    with pytest.raises(
        ValueError,
        match="missing config keys",
    ):
        Project8Config.from_mapping(mapping)


def test_config_rejects_nonlist_sensitivity_grid() -> None:
    mapping = _valid_config_mapping()

    mapping["sensitivity_grid_negative_draws"] = (
        1,
        2,
        5,
    )

    with pytest.raises(
        TypeError,
        match="sensitivity_grid_negative_draws must be a list",
    ):
        Project8Config.from_mapping(mapping)


def test_load_config_rejects_nonmapping_yaml(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid_project8_config.yaml"

    path.write_text(
        "- not\n- a\n- mapping\n",
        encoding="utf-8",
    )

    with pytest.raises(
        TypeError,
        match="Project 8 config must decode to a mapping",
    ):
        load_config(path)


@pytest.mark.parametrize(
    "experiment_kind",
    [
        "",
        " leading",
        "trailing ",
    ],
)
def test_experiment_id_rejects_invalid_kind(
    experiment_kind: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="experiment_kind must be a non-empty stripped string",
    ):
        experiment_id(
            experiment_kind=experiment_kind,
            protocol={},
        )


@pytest.mark.parametrize(
    "evidence_kind",
    [
        "",
        " leading",
        "trailing ",
    ],
)
def test_evidence_id_rejects_invalid_kind(
    evidence_kind: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="evidence_kind must be a non-empty stripped string",
    ):
        evidence_id(
            evidence_kind=evidence_kind,
            payload={},
        )


def test_expected_sampled_recall_rejects_noninteger_k() -> None:
    with pytest.raises(
        TypeError,
        match="k must be a plain integer",
    ):
        expected_sampled_recall_at_k(
            100,
            n_items=10_000,
            negative_draws=99,
            k=True,
        )


def test_expected_sampled_recall_rejects_nonpositive_k() -> None:
    with pytest.raises(
        ValueError,
        match="k must be >= 1",
    ):
        expected_sampled_recall_at_k(
            100,
            n_items=10_000,
            negative_draws=99,
            k=0,
        )


def test_validate_config_reports_frozen_contract_mismatches() -> None:
    config = load_default_config()

    altered = replace(
        config,
        n_items=9_999,
        reference_negative_draws=98,
        root_seed=1,
        sensitivity_grid_negative_draws=(
            1,
            2,
            5,
            10,
        ),
    )

    findings = validate_config(altered)

    assert "n_items must equal the frozen source value 10000" in findings

    assert "reference negative draws must equal 99" in findings

    assert "root seed differs from the frozen Step-0 value" in findings

    assert "sensitivity grid differs from the frozen contract" in findings


def test_validate_reference_reports_profile_mismatch() -> None:
    reference = load_reference_protocol()

    altered_profiles = dict(reference.profiles)

    altered_profiles["A"] = (
        99,
        100,
        100,
        100,
        100,
    )

    altered = replace(
        reference,
        profiles=altered_profiles,
    )

    findings = validate_reference(altered)

    assert findings == ["reference profiles differ from the source-verified values"]


def test_repository_root_resolves_current_repository() -> None:
    root = repository_root()

    assert root.is_dir()

    assert (root / "pyproject.toml").is_file()
