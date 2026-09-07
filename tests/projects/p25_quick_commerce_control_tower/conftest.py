"""Offline data-layer fixtures; never download portfolio data in automated tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from linkedin_visual_labs.common.paths import discover_repository_root
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import aggregate_demand


@pytest.fixture(scope="module")
def fixture_root() -> Path:
    return discover_repository_root() / "tests/fixtures/p25_quick_commerce_control_tower"


@pytest.fixture(scope="module")
def daily(fixture_root: Path, tmp_path_factory: pytest.TempPathFactory) -> pd.DataFrame:
    root = discover_repository_root()
    return aggregate_demand(
        fixture_root / "sales_train_evaluation.csv",
        fixture_root / "calendar.csv",
        sql_path=root / "sql/p25_quick_commerce_control_tower/aggregate_demand.sql",
        resources=load_commerce_config().resources,
        spill_directory=tmp_path_factory.mktemp("duckdb-spill"),
        expected_days=112,
    )
