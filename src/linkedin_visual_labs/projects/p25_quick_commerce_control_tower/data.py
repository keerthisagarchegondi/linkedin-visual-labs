"""Verified M5 acquisition and wide-first aggregation; no synthetic fallback."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from http.client import HTTPException
from pathlib import Path
from typing import get_args
from urllib.error import URLError
from urllib.request import urlopen

import duckdb
import numpy as np
import pandas as pd

from linkedin_visual_labs.common.media import write_generation_manifest
from linkedin_visual_labs.common.paths import ensure_path_within
from linkedin_visual_labs.common.validation import ValidationError
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import (
    ResourceConfig,
    Store,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext

IDENTIFIERS = ("id", "item_id", "dept_id", "cat_id", "store_id", "state_id")
GRAIN = ["date", "store_id", "category"]
STORES = tuple(get_args(Store))
CALENDAR = (
    "date",
    "d",
    "weekday",
    "month",
    "event_name_1",
    "event_type_1",
    "snap_CA",
    "snap_TX",
    "snap_WI",
)


class DataError(ValidationError):
    """A data contract failed; the real-data path must stop."""


@dataclass(frozen=True)
class SourceFile:
    """One pinned raw input and its published checksum."""

    filename: str
    url: str
    md5: str
    observed_days: int | None


@dataclass(frozen=True)
class FileRecord:
    """Verified bytes and source provenance for one cache entry."""

    filename: str
    url: str
    md5: str
    sha256: str
    size_bytes: int
    acquired_at: str
    input_kind: str


@dataclass(frozen=True)
class HoldoutSplit:
    """One immutable date boundary shared by every series."""

    training: pd.DataFrame
    holdout: pd.DataFrame
    origin: pd.Timestamp


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    """Stream a checksum without loading the raw file into memory."""
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def demand_columns(path: Path, expected_days: int | None = None) -> list[str]:
    """Require the exact identifier prefix and a continuous ordered observed horizon."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream), [])
    if header[:6] != list(IDENTIFIERS):
        raise DataError("sales schema must begin with the six M5 identifier columns")
    days = header[6:]
    if not days or days != [f"d_{i}" for i in range(1, len(days) + 1)]:
        raise DataError("observed demand columns must be ordered d_1 through d_N without gaps")
    if expected_days is not None and len(days) != expected_days:
        raise DataError(f"expected {expected_days} observed days, found {len(days)}")
    return days


def read_calendar(path: Path, days: list[str]) -> pd.DataFrame:
    """Validate the small calendar including target-date known-at-origin fields."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream), [])
    if len(header) != len(set(header)) or not set(CALENDAR).issubset(header):
        raise DataError("calendar schema missing required fields or contains duplicate columns")
    calendar = pd.read_csv(path, keep_default_na=False)
    for name in ("event_name_2", "event_type_2"):
        if name not in calendar:
            calendar[name] = ""
    if calendar["d"].duplicated().any():
        raise DataError("duplicate calendar day identifiers")
    calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
    if calendar["date"].isna().any() or calendar["date"].duplicated().any():
        raise DataError("invalid or duplicate calendar dates")
    if set(days) - set(calendar["d"]):
        raise DataError("incomplete calendar join")
    calendar = calendar.set_index("d").loc[days].reset_index()
    if not calendar["date"].equals(
        pd.Series(pd.date_range(calendar["date"].iloc[0], periods=len(days)))
    ):
        raise DataError("calendar dates must be continuous and ordered with observed d_N")
    if not (calendar["weekday"] == calendar["date"].dt.day_name()).all():
        raise DataError("weekday disagrees with calendar date")
    if not (pd.to_numeric(calendar["month"], errors="coerce") == calendar["date"].dt.month).all():
        raise DataError("month disagrees with calendar date")
    for state in ("CA", "TX", "WI"):
        values = pd.to_numeric(calendar[f"snap_{state}"], errors="coerce")
        if not values.isin([0, 1]).all():
            raise DataError("SNAP fields must contain only 0 or 1")
        calendar[f"snap_{state}"] = values.astype("int64")
    return calendar


def _validate_source(path: Path, spec: SourceFile) -> None:
    if file_hash(path, "md5") != spec.md5:
        raise DataError(f"published checksum mismatch: {spec.filename}")
    if spec.observed_days is not None:
        demand_columns(path, spec.observed_days)
    else:
        # Full observed-day join is checked after both input files are available.
        with path.open(encoding="utf-8-sig", newline="") as stream:
            header = next(csv.reader(stream), [])
        if not set(CALENDAR).issubset(header):
            raise DataError("calendar schema missing required fields")


def acquire_file(
    spec: SourceFile,
    raw_root: Path,
    *,
    timeout: float,
    attempts: int,
    local_file: Path | None = None,
) -> FileRecord:
    """Verify cache or atomically publish input; never silently replace corrupt caches."""
    raw_root.mkdir(parents=True, exist_ok=True)
    target = ensure_path_within(raw_root / spec.filename, raw_root)
    metadata = target.with_suffix(".metadata.json")
    if local_file is None and target.exists():
        try:
            record = FileRecord(**json.loads(metadata.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as exc:
            raise DataError(f"cache metadata missing or invalid: {metadata}") from exc
        _validate_source(target, spec)
        if (
            record.sha256 != file_hash(target)
            or record.size_bytes != target.stat().st_size
            or record.url != spec.url
            or record.md5 != spec.md5
            or record.filename != spec.filename
        ):
            raise DataError(f"cache provenance mismatch: {target}")
        return record
    temporary = target.with_suffix(".csv.part")
    last_error = "no acquisition attempt"
    for _ in range(attempts):
        try:
            if local_file is not None:
                with local_file.open("rb") as source, temporary.open("wb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
            else:
                with urlopen(spec.url, timeout=timeout) as response, temporary.open("wb") as output:
                    shutil.copyfileobj(response, output, length=1024 * 1024)
            _validate_source(temporary, spec)
            record = FileRecord(
                filename=spec.filename,
                url=spec.url,
                md5=spec.md5,
                sha256=file_hash(temporary),
                size_bytes=temporary.stat().st_size,
                acquired_at=datetime.now(UTC).isoformat(),
                input_kind="local_verified_real" if local_file else "downloaded_real",
            )
            temporary.replace(target)
            write_generation_manifest(asdict(record), metadata)
            return record
        except (OSError, URLError, HTTPException, DataError) as exc:
            last_error = str(exc)
        finally:
            temporary.unlink(missing_ok=True)
    raise DataError(f"acquisition failed for {spec.url} after {attempts} attempts: {last_error}")


def acquire_data(context: PipelineContext, local_directory: Path | None = None) -> list[FileRecord]:
    """Acquire exactly two pinned real M5 files, never fixtures or alternate mirrors."""
    config = context.configuration
    source = config.acquisition
    specs = (
        SourceFile(
            "sales_train_evaluation.csv",
            source.sales_url,
            source.sales_md5,
            source.expected_observed_days,
        ),
        SourceFile("calendar.csv", source.calendar_url, source.calendar_md5, None),
    )
    root = context.paths.repository_root
    raw = ensure_path_within(root / config.paths.raw_data, root)
    local = ensure_path_within(local_directory, root) if local_directory is not None else None
    records = [
        acquire_file(
            spec,
            raw,
            timeout=source.timeout_seconds,
            attempts=source.attempts,
            local_file=local / spec.filename if local is not None else None,
        )
        for spec in specs
    ]
    days = demand_columns(raw / specs[0].filename, source.expected_observed_days)
    read_calendar(raw / "calendar.csv", days)
    return records


def validate_daily(frame: pd.DataFrame) -> None:
    """Validate complete canonical grain and calendar/state consistency."""
    required = set(
        [
            *GRAIN,
            "state_id",
            "d",
            "demand",
            "weekday",
            "month",
            "snap",
            "snap_CA",
            "snap_TX",
            "snap_WI",
        ]
    )
    if not required.issubset(frame.columns) or frame.empty:
        raise DataError("prepared data missing required fields or rows")
    if frame[list(required)].isna().any().any() or frame.duplicated(GRAIN).any():
        raise DataError("missing values or duplicate canonical grain")
    if set(frame["store_id"]) != set(STORES) or set(frame["category"]) != {"FOODS", "HOUSEHOLD"}:
        raise DataError("prepared scope must be exactly 10 stores and two selected categories")
    combinations = frame[["store_id", "category"]].drop_duplicates()
    if len(combinations) != 20:
        raise DataError("prepared scope must contain exactly 20 series")
    values = frame["demand"].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise DataError("demand must be finite and nonnegative")
    dates = pd.DatetimeIndex(sorted(frame["date"].unique()))
    if not dates.equals(pd.date_range(dates[0], dates[-1])):
        raise DataError("prepared dates are not continuous")
    if not frame.groupby("date").size().eq(20).all():
        raise DataError("every date must contain all 20 series")
    if not frame["state_id"].eq(frame["store_id"].str[:2]).all():
        raise DataError("invalid store-state mapping")
    for state in ("CA", "TX", "WI"):
        subset = frame.loc[frame["state_id"].eq(state)]
        if (
            not subset["snap"].isin([0, 1]).all()
            or not subset["snap"].eq(subset[f"snap_{state}"]).all()
        ):
            raise DataError("invalid state-specific SNAP mapping")


def common_holdout(frame: pd.DataFrame, holdout_days: int = 28) -> HoldoutSplit:
    """Split once by observed dates, never independently by series."""
    validate_daily(frame)
    if holdout_days != 28:
        raise DataError("the common holdout must contain 28 dates")
    dates = sorted(frame["date"].unique())
    if len(dates) <= holdout_days:
        raise DataError("insufficient observed history for training and holdout")
    origin = pd.Timestamp(dates[-holdout_days - 1])
    training = frame.loc[frame["date"] <= origin].copy()
    holdout = frame.loc[frame["date"] > origin].copy()
    if len(holdout) != 560 or holdout["date"].nunique() != 28:
        raise DataError("holdout must contain 28 common dates and 560 observations")
    return HoldoutSplit(training=training, holdout=holdout, origin=origin)


def aggregate_demand(
    sales: Path,
    calendar: Path,
    *,
    sql_path: Path,
    resources: ResourceConfig,
    spill_directory: Path,
    expected_days: int | None = None,
) -> pd.DataFrame:
    """Scan CSV as wide data; materialize only 20 wide rows before UNPIVOT."""
    days = demand_columns(sales, expected_days)
    calendar_frame = read_calendar(calendar, days)
    spill_directory.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(
        config={
            "threads": resources.threads,
            "memory_limit": resources.memory_limit,
            "temp_directory": str(spill_directory.resolve()),
        }
    ) as connection:
        connection.read_csv(str(sales), header=True, all_varchar=True).create_view("raw_sales")
        identifiers = connection.execute(
            "SELECT id, item_id, dept_id, cat_id, store_id, state_id FROM raw_sales"
        ).fetchdf()
        if identifiers.isna().any().any() or any(
            identifiers[col].eq("").any() for col in identifiers
        ):
            raise DataError("missing source identifiers")
        if (
            identifiers["id"].duplicated().any()
            or identifiers.duplicated(["item_id", "store_id"]).any()
        ):
            raise DataError("duplicate item-store source rows")
        if set(identifiers["store_id"]) != set(STORES):
            raise DataError("source must contain exactly the ten M5 stores")
        if not identifiers["state_id"].eq(identifiers["store_id"].str[:2]).all():
            raise DataError("invalid source store-state mapping")
        # Validate values without constructing any item-by-day long table.
        invalid = " OR ".join(
            f"NOT coalesce(regexp_full_match({day}, '[0-9]+'), false)" for day in days
        )
        invalid_count = connection.execute(
            "SELECT count(*) FROM raw_sales WHERE cat_id IN ('FOODS','HOUSEHOLD') AND ("
            + invalid
            + ")"
        ).fetchone()
        if invalid_count is None or invalid_count[0]:
            raise DataError("source demand must be nonmissing nonnegative integer counts")
        sums = ", ".join(f"sum(CAST({day} AS BIGINT))::BIGINT AS {day}" for day in days)
        template = sql_path.read_text(encoding="utf-8")
        connection.execute(template.format(day_sums=sums))
        wide_count = connection.execute("SELECT count(*) FROM wide_aggregate").fetchone()
        if wide_count is None or wide_count[0] != 20:
            raise DataError("wide aggregation must materialize exactly 20 series")
        connection.register("calendar_data", calendar_frame)
        frame = connection.execute("""
            WITH long_demand AS (
                UNPIVOT wide_aggregate ON COLUMNS('^d_[0-9]+$') INTO NAME d VALUE demand
            )
            SELECT c.date, s.store_id, s.state_id, s.category, s.d, s.demand,
                   c.weekday, c.month, c.event_name_1, c.event_type_1,
                   c.event_name_2, c.event_type_2, c.snap_CA, c.snap_TX, c.snap_WI,
                   CASE s.state_id WHEN 'CA' THEN c.snap_CA WHEN 'TX' THEN c.snap_TX
                        WHEN 'WI' THEN c.snap_WI END AS snap
            FROM long_demand s LEFT JOIN calendar_data c ON s.d = c.d
            ORDER BY c.date, s.store_id, s.category
        """).fetchdf()
    validate_daily(frame)
    if len(frame) != 20 * len(days):
        raise DataError("aggregation cardinality does not match the validated source horizon")
    return frame


def prepare_data(context: PipelineContext, *, fixture: bool = False) -> Path:
    """Prepare a verified real cache, or an explicitly labeled isolated test-only fixture."""
    root = context.paths.repository_root
    records: list[FileRecord] = []
    if fixture:
        raw = root / "tests/fixtures/p25_quick_commerce_control_tower"
        expected_days = None
        classification = "synthetic_test_only"
        output = context.resolve_output_path("data/fixture/demand_daily.parquet")
    else:
        raw = root / context.configuration.paths.raw_data
        # Preparation is offline: never download implicitly or replace failed caches.
        if not all(
            (raw / name).is_file() for name in ("sales_train_evaluation.csv", "calendar.csv")
        ):
            raise DataError("verified real cache missing; run commerce acquire-data first")
        records = acquire_data(context)
        expected_days = context.configuration.acquisition.expected_observed_days
        classification = "public_real_m5"
        output = context.resolve_output_path("data/demand_daily.parquet")
    raw = ensure_path_within(raw, root)
    frame = aggregate_demand(
        raw / "sales_train_evaluation.csv",
        raw / "calendar.csv",
        sql_path=root / context.configuration.paths.sql / "aggregate_demand.sql",
        resources=context.configuration.resources,
        spill_directory=ensure_path_within(
            root / context.configuration.paths.cache / "duckdb_spill", root
        ),
        expected_days=expected_days,
    )
    split = common_holdout(frame)
    frame["data_classification"] = classification
    context.paths.create()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".parquet.part")
    try:
        frame.to_parquet(temporary, index=False)
        validate_daily(pd.read_parquet(temporary))
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    metadata = {
        "classification": classification,
        "record_id": context.configuration.acquisition.record_id if not fixture else None,
        "source_files": [asdict(record) for record in records],
        "rows": len(frame),
        "stores": frame["store_id"].nunique(),
        "series": 20,
        "categories": sorted(frame["category"].unique().tolist()),
        "observed_days": frame["date"].nunique(),
        "holdout_rows": len(split.holdout),
        "training_start": str(split.training["date"].min().date()),
        "training_end": str(split.origin.date()),
        "holdout_start": str(split.holdout["date"].min().date()),
        "holdout_end": str(split.holdout["date"].max().date()),
        "parquet_sha256": file_hash(output),
        "aggregation": "wide_sum_then_20_row_unpivot",
        "resources": context.configuration.resources.model_dump(),
    }
    write_generation_manifest(metadata, output.with_suffix(".metadata.json"))
    return output
