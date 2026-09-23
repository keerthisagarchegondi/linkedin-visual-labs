from __future__ import annotations

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.identifiers import (
    evidence_id,
    experiment_id,
)


def test_experiment_identifier_is_stable() -> None:
    left = experiment_id(
        experiment_kind="reference",
        protocol={"m": 99, "seed": 20260923},
    )

    right = experiment_id(
        experiment_kind="reference",
        protocol={"seed": 20260923, "m": 99},
    )

    assert left == right


def test_evidence_identifier_changes_with_payload() -> None:
    left = evidence_id(
        evidence_kind="input",
        payload={"rank": 100},
    )

    right = evidence_id(
        evidence_kind="input",
        payload={"rank": 101},
    )

    assert left != right
