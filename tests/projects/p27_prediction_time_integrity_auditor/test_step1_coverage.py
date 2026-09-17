from __future__ import annotations

import io
import urllib.request
import zipfile
from dataclasses import replace
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest

from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor import (
    data as data_module,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.contracts import (
    EXPECTED_COLUMNS,
    build_feature_contract,
    validate_feature_contract,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.data import (
    LoadedDataset,
    SourcePaths,
)
from linkedin_visual_labs.projects.p27_prediction_time_integrity_auditor.models import (
    AvailabilityClass,
)


class _FakeResponse(io.BytesIO):
    status = 200

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _one_valid_row() -> dict[str, str]:
    return {
        "age": "31",
        "job": "admin.",
        "marital": "single",
        "education": "university.degree",
        "default": "no",
        "housing": "yes",
        "loan": "no",
        "contact": "cellular",
        "month": "may",
        "day_of_week": "mon",
        "duration": "120",
        "campaign": "1",
        "pdays": "999",
        "previous": "0",
        "poutcome": "nonexistent",
        "emp.var.rate": "1.1",
        "cons.price.idx": "93.994",
        "cons.conf.idx": "-36.4",
        "euribor3m": "4.857",
        "nr.employed": "5191.0",
        "y": "no",
    }


def test_feature_contract_rejects_wrong_length() -> None:
    records = build_feature_contract()

    with pytest.raises(
        ValueError,
        match="every input exactly once",
    ):
        validate_feature_contract(records[:-1])


def test_feature_contract_rejects_wrong_order() -> None:
    records = list(build_feature_contract())

    records[0], records[1] = (
        records[1],
        records[0],
    )

    with pytest.raises(
        ValueError,
        match="order must exactly match",
    ):
        validate_feature_contract(tuple(records))


def test_feature_contract_rejects_duration_policy() -> None:
    records = list(build_feature_contract())

    index = next(index for index, record in enumerate(records) if record.feature_name == "duration")

    records[index] = replace(
        records[index],
        availability_class=AvailabilityClass.PRE_DECISION,
        available_at_prediction=True,
        deployment_allowed=True,
    )

    with pytest.raises(
        ValueError,
        match="duration must be DURING_ACTION",
    ):
        validate_feature_contract(tuple(records))


def test_feature_contract_rejects_campaign_policy() -> None:
    records = list(build_feature_contract())

    index = next(index for index, record in enumerate(records) if record.feature_name == "campaign")

    records[index] = replace(
        records[index],
        availability_class=AvailabilityClass.PRE_DECISION,
        available_at_prediction=True,
        deployment_allowed=True,
    )

    with pytest.raises(
        ValueError,
        match="campaign must remain UNKNOWN",
    ):
        validate_feature_contract(tuple(records))


def test_download_helper_writes_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "download.zip"

    def fake_urlopen(
        request: object,
        *,
        timeout: int,
    ) -> _FakeResponse:
        assert request is not None
        assert timeout == 60
        return _FakeResponse(b"official-bytes")

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        fake_urlopen,
    )

    data_module._download_to_temp(destination)

    assert destination.read_bytes() == b"official-bytes"


def test_extract_preferred_csv_from_nested_archive(
    tmp_path: Path,
) -> None:
    csv_payload = (
        ";".join(EXPECTED_COLUMNS)
        + "\n"
        + ";".join(_one_valid_row()[column] for column in EXPECTED_COLUMNS)
        + "\n"
    ).encode("utf-8")

    nested_buffer = io.BytesIO()

    with zipfile.ZipFile(
        nested_buffer,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as nested:
        nested.writestr(
            "bank-additional/bank-additional-full.csv",
            csv_payload,
        )

    outer_path = tmp_path / "outer.zip"

    with zipfile.ZipFile(
        outer_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as outer:
        outer.writestr(
            "bank-additional.zip",
            nested_buffer.getvalue(),
        )

    destination = tmp_path / "bank-additional-full.csv"

    data_module._extract_preferred_csv(
        outer_path,
        destination,
    )

    assert destination.read_bytes() == csv_payload


def test_acquire_source_reuses_cached_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()

    archive = raw / "bank+marketing.zip"
    csv_path = raw / "bank-additional-full.csv"

    archive.write_bytes(b"cached-archive")

    csv_path.write_text(
        "cached-csv",
        encoding="utf-8",
    )

    paths = SourcePaths(
        raw_root=raw,
        outer_archive=archive,
        extracted_csv=csv_path,
    )

    monkeypatch.setattr(
        data_module,
        "source_paths",
        lambda: paths,
    )

    result = data_module.acquire_official_source()

    assert result == paths

    assert archive.read_bytes() == b"cached-archive"

    assert csv_path.read_text(encoding="utf-8") == "cached-csv"


def test_validate_rows_rejects_wrong_row_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_module,
        "EXPECTED_ROW_COUNT",
        2,
    )

    with pytest.raises(
        ValueError,
        match="row-count mismatch",
    ):
        data_module._validate_rows((_one_valid_row(),))


def test_validate_rows_rejects_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_module,
        "EXPECTED_ROW_COUNT",
        1,
    )

    row = _one_valid_row()
    row["y"] = "maybe"

    with pytest.raises(
        ValueError,
        match="Unexpected target values",
    ):
        data_module._validate_rows((row,))


def test_validate_rows_rejects_nonnumeric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_module,
        "EXPECTED_ROW_COUNT",
        2,
    )

    bad = _one_valid_row()
    bad["age"] = "not-a-number"

    positive = _one_valid_row()
    positive["y"] = "yes"

    with pytest.raises(
        ValueError,
        match="Non-numeric age",
    ):
        data_module._validate_rows((bad, positive))


def test_validate_rows_rejects_negative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_module,
        "EXPECTED_ROW_COUNT",
        2,
    )

    bad = _one_valid_row()
    bad["age"] = "-1"

    positive = _one_valid_row()
    positive["y"] = "yes"

    with pytest.raises(
        ValueError,
        match="Unexpected negative age",
    ):
        data_module._validate_rows((bad, positive))


def test_build_source_manifest_and_profile(
    tmp_path: Path,
) -> None:
    row = _one_valid_row()

    dataset = LoadedDataset(
        rows=(row,),
        source_order=(0,),
    )

    archive = tmp_path / "archive.zip"
    csv_path = tmp_path / "source.csv"

    archive.write_bytes(b"archive")

    csv_path.write_text(
        "csv",
        encoding="utf-8",
    )

    paths = SourcePaths(
        raw_root=tmp_path,
        outer_archive=archive,
        extracted_csv=csv_path,
    )

    manifest = data_module.build_source_manifest(
        paths,
        dataset,
        accessed_on="2026-09-17",
    )

    profile = data_module.build_source_profile(dataset)

    assert manifest["dataset_id"] == 222
    assert manifest["doi"] == "10.24432/C5K306"
    assert manifest["row_count"] == 1
    assert manifest["archive_sha256"]
    assert manifest["extracted_file_sha256"]

    assert profile["row_count"] == 1
    assert profile["input_count"] == 20
    assert profile["dataset_fingerprint_sha256"]


def test_load_official_dataset_requires_cached_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = SourcePaths(
        raw_root=tmp_path,
        outer_archive=tmp_path / "archive.zip",
        extracted_csv=tmp_path / "missing.csv",
    )

    monkeypatch.setattr(
        data_module,
        "source_paths",
        lambda: paths,
    )

    with pytest.raises(
        FileNotFoundError,
    ):
        data_module.load_official_dataset(acquire=False)


def test_feature_contract_rejects_duration_deployment_mismatch() -> None:
    records = list(build_feature_contract())

    index = next(index for index, record in enumerate(records) if record.feature_name == "duration")

    records[index] = replace(
        records[index],
        deployment_allowed=True,
    )

    with pytest.raises(
        ValueError,
        match="duration must be blocked",
    ):
        validate_feature_contract(tuple(records))


def test_feature_contract_rejects_campaign_deployment_mismatch() -> None:
    records = list(build_feature_contract())

    index = next(index for index, record in enumerate(records) if record.feature_name == "campaign")

    records[index] = replace(
        records[index],
        deployment_allowed=True,
    )

    with pytest.raises(
        ValueError,
        match="campaign must be blocked",
    ):
        validate_feature_contract(tuple(records))


def test_feature_contract_rejects_available_at_prediction_mismatch() -> None:
    records = list(build_feature_contract())

    records[0] = replace(
        records[0],
        available_at_prediction=False,
    )

    with pytest.raises(
        ValueError,
        match="Availability policy mismatch",
    ):
        validate_feature_contract(tuple(records))


def test_feature_contract_rejects_generic_deployment_mismatch() -> None:
    records = list(build_feature_contract())

    records[0] = replace(
        records[0],
        deployment_allowed=False,
    )

    with pytest.raises(
        ValueError,
        match="Deployment policy mismatch",
    ):
        validate_feature_contract(tuple(records))


def test_download_helper_rejects_non_200(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "download.zip"

    class BadResponse(_FakeResponse):
        status = 503

    def fake_urlopen(
        request: object,
        *,
        timeout: int,
    ) -> BadResponse:
        assert request is not None
        assert timeout == 60
        return BadResponse(b"error")

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        RuntimeError,
        match="Unexpected UCI HTTP status",
    ):
        data_module._download_to_temp(destination)

    assert not destination.exists()


def test_download_helper_rejects_empty_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "download.zip"

    def fake_urlopen(
        request: object,
        *,
        timeout: int,
    ) -> _FakeResponse:
        assert request is not None
        assert timeout == 60
        return _FakeResponse(b"")

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        fake_urlopen,
    )

    with pytest.raises(
        RuntimeError,
        match="Downloaded UCI archive is empty",
    ):
        data_module._download_to_temp(destination)

    assert not destination.exists()


def test_extract_rejects_missing_nested_archive(
    tmp_path: Path,
) -> None:
    outer_path = tmp_path / "outer.zip"

    with zipfile.ZipFile(
        outer_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as outer:
        outer.writestr(
            "other.txt",
            b"not-bank-data",
        )

    with pytest.raises(
        RuntimeError,
        match=r"Expected exactly one bank-additional\.zip",
    ):
        data_module._extract_preferred_csv(
            outer_path,
            tmp_path / "target.csv",
        )


def test_extract_rejects_missing_preferred_csv(
    tmp_path: Path,
) -> None:
    nested_buffer = io.BytesIO()

    with zipfile.ZipFile(
        nested_buffer,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as nested:
        nested.writestr(
            "bank-additional/other.csv",
            b"x\n1\n",
        )

    outer_path = tmp_path / "outer.zip"

    with zipfile.ZipFile(
        outer_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as outer:
        outer.writestr(
            "bank-additional.zip",
            nested_buffer.getvalue(),
        )

    with pytest.raises(
        RuntimeError,
        match="Expected exactly one preferred CSV",
    ):
        data_module._extract_preferred_csv(
            outer_path,
            tmp_path / "target.csv",
        )


def test_validate_rows_rejects_parser_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_module,
        "EXPECTED_ROW_COUNT",
        2,
    )

    bad = _one_valid_row()
    bad["job"] = None  # type: ignore[assignment]

    positive = _one_valid_row()
    positive["y"] = "yes"

    with pytest.raises(
        ValueError,
        match="contains null parser values",
    ):
        data_module._validate_rows((bad, positive))


def test_load_official_dataset_with_acquire_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_paths = data_module.source_paths()

    monkeypatch.setattr(
        data_module,
        "acquire_official_source",
        lambda: real_paths,
    )

    dataset = data_module.load_official_dataset(acquire=True)

    assert len(dataset.rows) == 41188
    assert dataset.source_order[0] == 0
    assert dataset.source_order[-1] == 41187
