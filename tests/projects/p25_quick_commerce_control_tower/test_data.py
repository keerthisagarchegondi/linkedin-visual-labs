"""Independent aggregate truth, corruption rejection, and explicit mode integration."""

from __future__ import annotations

import io
import json
import shutil
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import URLError

import pandas as pd
import pytest
from typer.testing import CliRunner

from linkedin_visual_labs.cli import app
from linkedin_visual_labs.common.paths import discover_repository_root
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import data
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.config import (
    DEFAULT_CONFIG_PATH,
    load_commerce_config,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import (
    DataError,
    SourceFile,
    acquire_data,
    acquire_file,
    aggregate_demand,
    common_holdout,
    demand_columns,
    file_hash,
    prepare_data,
    read_calendar,
    validate_daily,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import (
    PipelineContext,
    build_pipeline_context,
)


def make_context(root: Path) -> PipelineContext:
    repository = discover_repository_root()
    (root / "src/linkedin_visual_labs").mkdir(parents=True)
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    (root / "configs").mkdir()
    shutil.copyfile(repository / DEFAULT_CONFIG_PATH, root / DEFAULT_CONFIG_PATH)
    for relative in (
        "tests/fixtures/p25_quick_commerce_control_tower",
        "sql/p25_quick_commerce_control_tower",
    ):
        shutil.copytree(repository / relative, root / relative)
    return build_pipeline_context(repository_root=root)


def test_pinned_source_config() -> None:
    source = load_commerce_config().acquisition
    assert source.record_id == "10203108"
    assert source.expected_observed_days == 1941
    assert source.sales_url.endswith("sales_train_evaluation.csv?download=1")
    assert source.calendar_url.endswith("calendar.csv?download=1")
    assert source.sales_md5 == "b806dfc9f30a745102b708c09951f6aa"
    assert source.calendar_md5 == "3ffeab2991b0c8e861d008b39ea4c95c"


def test_verified_download_cache_and_corruption(
    fixture_root: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = fixture_root / "sales_train_evaluation.csv"
    spec = SourceFile(source.name, "https://example.invalid/pinned", file_hash(source, "md5"), 112)
    calls: list[str] = []

    def download(url: str, timeout: float) -> io.BytesIO:
        assert timeout == 2.0
        calls.append(url)
        return io.BytesIO(source.read_bytes())

    monkeypatch.setattr(data, "urlopen", download)
    first = acquire_file(spec, tmp_path, timeout=2.0, attempts=2)
    second = acquire_file(spec, tmp_path, timeout=2.0, attempts=2)
    assert first == second
    assert calls == [spec.url]
    assert first.sha256 == file_hash(source)
    assert first.size_bytes == source.stat().st_size
    assert first.acquired_at
    (tmp_path / source.name).write_text("corrupt", encoding="utf-8")
    with pytest.raises(DataError, match="checksum"):
        acquire_file(spec, tmp_path, timeout=2.0, attempts=2)
    assert len(calls) == 1


def test_offline_local_input_and_metadata_rejection(fixture_root: Path, tmp_path: Path) -> None:
    source = fixture_root / "sales_train_evaluation.csv"
    spec = SourceFile(source.name, "https://example.invalid/pinned", file_hash(source, "md5"), 112)
    result = acquire_file(spec, tmp_path, timeout=1.0, attempts=1, local_file=source)
    assert result.input_kind == "local_verified_real"
    metadata = (tmp_path / source.name).with_suffix(".metadata.json")
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    payload["sha256"] = "incorrect"
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(DataError, match="provenance"):
        acquire_file(spec, tmp_path, timeout=1.0, attempts=1)


@pytest.mark.parametrize(
    "error", [OSError("interrupted transfer"), IncompleteRead(b"partial", 100)]
)
def test_incomplete_download_is_not_promoted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    attempts: list[int] = []

    class Interrupted(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            attempts.append(1)
            if len(attempts) % 2 == 0:
                raise error
            return b"partial bytes"

    def download(url: str, timeout: float) -> Interrupted:
        return Interrupted()

    monkeypatch.setattr(data, "urlopen", download)
    with pytest.raises(DataError, match="after 2 attempts") as failure:
        acquire_file(
            SourceFile("sales.csv", "https://example.invalid", "0" * 32, 112),
            tmp_path,
            timeout=1.0,
            attempts=2,
        )
    assert len(attempts) == 4
    assert str(error) in str(failure.value)
    assert not list(tmp_path.iterdir())


def test_real_mode_never_uses_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = make_context(tmp_path)

    def unavailable(url: str, timeout: float) -> io.BytesIO:
        raise URLError("offline test")

    monkeypatch.setattr(data, "urlopen", unavailable)
    with pytest.raises(DataError, match="offline test"):
        acquire_data(context)
    with pytest.raises(DataError, match="real cache missing"):
        prepare_data(context)
    assert not context.paths.output_root.exists()
    with pytest.raises(DataError, match="checksum"):
        acquire_data(context, tmp_path / "tests/fixtures/p25_quick_commerce_control_tower")


def test_fixture_output_is_isolated_and_deterministic(tmp_path: Path) -> None:
    context = make_context(tmp_path)
    output = prepare_data(context, fixture=True)
    initial_hash = file_hash(output)
    assert prepare_data(context, fixture=True) == output
    assert file_hash(output) == initial_hash
    assert output.parent.name == "fixture"
    assert not (context.paths.data / "demand_daily.parquet").exists()
    assert pd.read_parquet(output)["data_classification"].eq("synthetic_test_only").all()


def test_independent_expected_totals(daily: pd.DataFrame, fixture_root: Path) -> None:
    expected = pd.read_csv(fixture_root / "expected_aggregates.csv", parse_dates=["date"])
    pd.testing.assert_frame_equal(daily[expected.columns], expected, check_dtype=False)
    assert len(daily) == 2240
    assert daily["store_id"].nunique() == 10
    assert set(daily["category"]) == {"FOODS", "HOUSEHOLD"}
    assert daily.groupby(["store_id", "category"]).ngroups == 20
    assert daily["date"].nunique() == 112
    assert not daily.duplicated(["date", "store_id", "category"]).any()
    assert daily.loc[daily["d"].eq("d_17"), "demand"].eq(0).all()
    for state in ("CA", "TX", "WI"):
        subset = daily.loc[daily["state_id"].eq(state)]
        pd.testing.assert_series_equal(subset["snap"], subset[f"snap_{state}"], check_names=False)


def test_common_holdout(daily: pd.DataFrame) -> None:
    split = common_holdout(daily)
    assert len(split.training) == 1680
    assert len(split.holdout) == 560
    assert split.holdout["date"].nunique() == 28
    assert split.holdout.groupby("date").size().eq(20).all()
    assert split.holdout["d"].iloc[0] == "d_85"
    assert split.holdout["d"].iloc[-1] == "d_112"
    assert split.training["date"].max() == split.origin


@pytest.mark.parametrize(
    "mutation", ["duplicate", "gap", "missing", "negative", "state", "snap", "store", "category"]
)
def test_prepared_quality_rejections(daily: pd.DataFrame, mutation: str) -> None:
    broken = daily.copy()
    if mutation == "duplicate":
        broken = pd.concat([broken, broken.iloc[[0]]])
    elif mutation == "gap":
        broken = broken.loc[broken["date"] != broken["date"].iloc[20]]
    elif mutation == "missing":
        broken.loc[0, "demand"] = float("nan")
    elif mutation == "negative":
        broken.loc[0, "demand"] = -1
    elif mutation == "state":
        broken.loc[0, "state_id"] = "TX"
    elif mutation == "snap":
        broken.loc[0, "snap"] = 2
    elif mutation == "store":
        broken = broken.loc[broken["store_id"] != "CA_1"]
    else:
        broken = broken.loc[broken["category"] != "FOODS"]
    with pytest.raises(DataError):
        validate_daily(broken)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_identifier",
        "day_gap",
        "day_order",
        "negative",
        "null",
        "duplicate_item",
        "missing_store",
    ],
)
def test_raw_schema_and_values(fixture_root: Path, tmp_path: Path, mutation: str) -> None:
    source = pd.read_csv(fixture_root / "sales_train_evaluation.csv")
    if mutation == "missing_identifier":
        source = source.drop(columns="item_id")
    elif mutation == "day_gap":
        source = source.drop(columns="d_50")
    elif mutation == "day_order":
        columns = source.columns.tolist()
        columns[6], columns[7] = columns[7], columns[6]
        source = source[columns]
    elif mutation == "negative":
        source.loc[0, "d_1"] = -1
    elif mutation == "null":
        source.loc[0, "d_1"] = float("nan")
    elif mutation == "duplicate_item":
        source = pd.concat([source, source.iloc[[0]]])
    else:
        source = source.loc[source["store_id"] != "CA_1"]
    sales = tmp_path / "sales.csv"
    source.to_csv(sales, index=False)
    root = discover_repository_root()
    with pytest.raises(DataError):
        aggregate_demand(
            sales,
            fixture_root / "calendar.csv",
            sql_path=root / "sql/p25_quick_commerce_control_tower/aggregate_demand.sql",
            resources=load_commerce_config().resources,
            spill_directory=tmp_path / "spill",
        )


@pytest.mark.parametrize("mutation", ["date", "duplicate", "missing", "snap", "weekday", "schema"])
def test_invalid_calendar(fixture_root: Path, tmp_path: Path, mutation: str) -> None:
    calendar = pd.read_csv(fixture_root / "calendar.csv", keep_default_na=False)
    if mutation == "date":
        calendar.loc[0, "date"] = "invalid"
    elif mutation == "duplicate":
        calendar.loc[1, "d"] = "d_1"
    elif mutation == "missing":
        calendar = calendar.iloc[1:]
    elif mutation == "snap":
        calendar.loc[0, "snap_CA"] = 2
    elif mutation == "weekday":
        calendar.loc[0, "weekday"] = "Monday"
    else:
        calendar = calendar.drop(columns="event_name_1")
    path = tmp_path / "calendar.csv"
    calendar.to_csv(path, index=False)
    with pytest.raises(DataError):
        read_calendar(path, [f"d_{i}" for i in range(1, 113)])


def test_real_horizon_rejects_fixture(fixture_root: Path) -> None:
    with pytest.raises(DataError, match="1941"):
        demand_columns(fixture_root / "sales_train_evaluation.csv", 1941)


def test_source_schema_rejected_before_promotion(tmp_path: Path) -> None:
    local = tmp_path / "input.csv"
    local.write_text("wrong,header\n1,2\n", encoding="utf-8")
    target = tmp_path / "raw"
    spec = SourceFile("sales.csv", "https://example.invalid", file_hash(local, "md5"), 112)
    with pytest.raises(DataError, match="schema"):
        acquire_file(spec, target, timeout=1.0, attempts=1, local_file=local)
    assert not list(target.iterdir())


def test_missing_cache_metadata_is_rejected(fixture_root: Path, tmp_path: Path) -> None:
    local = fixture_root / "sales_train_evaluation.csv"
    spec = SourceFile(local.name, "https://example.invalid", file_hash(local, "md5"), 112)
    shutil.copyfile(local, tmp_path / local.name)
    with pytest.raises(DataError, match="metadata missing"):
        acquire_file(spec, tmp_path, timeout=1.0, attempts=1)


def test_optional_second_event_fields(fixture_root: Path, tmp_path: Path) -> None:
    calendar = pd.read_csv(fixture_root / "calendar.csv", keep_default_na=False)
    calendar.drop(columns=["event_name_2", "event_type_2"]).to_csv(
        tmp_path / "calendar.csv", index=False
    )
    result = read_calendar(tmp_path / "calendar.csv", [f"d_{i}" for i in range(1, 113)])
    assert result["event_name_2"].eq("").all()
    assert len(result) == 112


def test_cli_modes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = make_context(tmp_path)
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import cli

    monkeypatch.setattr(cli, "build_pipeline_context", lambda path: context)
    runner = CliRunner()
    result = runner.invoke(app, ["commerce", "prepare-data"])
    assert result.exit_code == 1
    assert "real cache missing" in result.output
    result = runner.invoke(app, ["commerce", "prepare-data", "--fixture"])
    assert result.exit_code == 0, result.output
    assert "SYNTHETIC TEST ONLY" in result.output
