from __future__ import annotations

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.validation import (
    validate_setup,
)


def test_canonical_setup_passes() -> None:
    assert validate_setup()["status"] == "PASS"
