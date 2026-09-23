from __future__ import annotations

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.cli import (
    main,
)


def test_validate_inputs_command(
    capsys: object,
) -> None:
    assert main(["validate-inputs"]) == 0


def test_audit_environment_command(
    capsys: object,
) -> None:
    assert main(["audit-environment"]) == 0
