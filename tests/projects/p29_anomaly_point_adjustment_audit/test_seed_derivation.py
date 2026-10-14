from __future__ import annotations

from linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit.config import (
    UINT32_MAX,
    derive_seed,
    load_default_config,
)


def test_semantic_seed_is_stable_and_uint32() -> None:
    config = load_default_config()
    first = derive_seed(config, "condition_simulation", L=200, q=0.01, replicate=1)
    assert first == derive_seed(config, "condition_simulation", L=200, q=0.01, replicate=1)
    assert first != derive_seed(config, "condition_simulation", L=100, q=0.01, replicate=1)
    assert 0 <= first <= UINT32_MAX
