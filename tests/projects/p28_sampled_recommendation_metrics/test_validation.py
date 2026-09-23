from __future__ import annotations

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics.validation import (
    validate_inputs,
)


def test_validate_inputs_passes() -> None:
    result = validate_inputs()

    assert result["status"] == "PASS"
    assert result["findings"] == []
