from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.config import (
    default_config_path,
    load_config,
)


def _base_payload() -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(default_config_path().read_text(encoding="utf-8")),
    )


def _write_payload(
    tmp_path: Path,
    payload: dict[str, object],
) -> Path:
    path = tmp_path / "config.json"

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return path


def _project(
    payload: dict[str, object],
) -> dict[str, object]:
    return cast(
        dict[str, object],
        payload["project"],
    )


def _data(
    payload: dict[str, object],
) -> dict[str, object]:
    return cast(
        dict[str, object],
        payload["data"],
    )


def _splits(
    payload: dict[str, object],
) -> dict[str, object]:
    return cast(
        dict[str, object],
        payload["splits"],
    )


def _chronological(
    payload: dict[str, object],
) -> dict[str, object]:
    return cast(
        dict[str, object],
        _splits(payload)["chronological"],
    )


def _random_comparison(
    payload: dict[str, object],
) -> dict[str, object]:
    return cast(
        dict[str, object],
        _splits(payload)["random_comparison"],
    )


def test_frozen_config_loads() -> None:
    config = load_config()

    assert config.project_id == "p27_prediction_time_integrity_auditor"
    assert config.seed == 1729
    assert config.dataset_id == 222
    assert config.preferred_file == "bank-additional-full.csv"
    assert config.target == "y"
    assert config.preserve_source_order is True
    assert config.random_seed == 1729
    assert config.random_stratify is True

    assert config.chronological_split.train == 0.70
    assert config.chronological_split.validation == 0.15
    assert config.chronological_split.test == 0.15


def test_default_config_exists() -> None:
    assert default_config_path().is_file()


def test_rejects_non_mapping_project(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    payload["project"] = []

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        TypeError,
        match="project must be an object",
    ):
        load_config(path)


def test_rejects_empty_project_id(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _project(payload)["id"] = ""

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        TypeError,
        match="id must be a non-empty string",
    ):
        load_config(path)


def test_rejects_boolean_seed_as_integer(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _project(payload)["seed"] = True

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        TypeError,
        match="seed must be an integer",
    ):
        load_config(path)


def test_rejects_non_boolean_source_order(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _data(payload)["preserve_source_order"] = "yes"

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        TypeError,
        match="preserve_source_order must be a boolean",
    ):
        load_config(path)


def test_rejects_non_numeric_split(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _chronological(payload)["train"] = "0.70"

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        TypeError,
        match="train must be numeric",
    ):
        load_config(path)


def test_rejects_invalid_project_id(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _project(payload)["id"] = "wrong_project"

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        ValueError,
        match="Unexpected project id",
    ):
        load_config(path)


def test_rejects_invalid_project_seed(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _project(payload)["seed"] = 1730

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        ValueError,
        match="Unexpected project seed",
    ):
        load_config(path)


def test_rejects_invalid_random_seed(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _random_comparison(payload)["seed"] = 1730

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        ValueError,
        match="Unexpected random split seed",
    ):
        load_config(path)


def test_rejects_invalid_dataset_id(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _data(payload)["dataset_id"] = 999

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        ValueError,
        match="Unexpected dataset id",
    ):
        load_config(path)


def test_rejects_source_order_disabled(
    tmp_path: Path,
) -> None:
    payload = _base_payload()
    _data(payload)["preserve_source_order"] = False

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        ValueError,
        match="must preserve source order",
    ):
        load_config(path)


def test_rejects_split_that_does_not_sum_to_one(
    tmp_path: Path,
) -> None:
    payload = _base_payload()

    chronological = _chronological(payload)

    chronological["train"] = 0.70
    chronological["validation"] = 0.20
    chronological["test"] = 0.20

    path = _write_payload(
        tmp_path,
        payload,
    )

    with pytest.raises(
        ValueError,
        match=r"sum to 1\.0",
    ):
        load_config(path)
