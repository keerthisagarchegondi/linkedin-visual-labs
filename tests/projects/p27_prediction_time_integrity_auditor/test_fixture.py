from __future__ import annotations

import csv
from pathlib import Path

EXPECTED_COLUMNS = [
    "age",
    "job",
    "marital",
    "education",
    "default",
    "housing",
    "loan",
    "contact",
    "month",
    "day_of_week",
    "duration",
    "campaign",
    "pdays",
    "previous",
    "poutcome",
    "emp.var.rate",
    "cons.price.idx",
    "cons.conf.idx",
    "euribor3m",
    "nr.employed",
    "y",
]


def test_fixture_shape_and_schema() -> None:
    path = Path(__file__).parent / "fixtures" / "bank_additional_tiny.csv"

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(
            csv.DictReader(
                handle,
                delimiter=";",
            )
        )

    assert len(rows) == 6
    assert list(rows[0]) == EXPECTED_COLUMNS
    assert {row["y"] for row in rows} == {"yes", "no"}


def test_fixture_is_clearly_nonbenchmark_scale() -> None:
    path = Path(__file__).parent / "fixtures" / "bank_additional_tiny.csv"

    assert path.stat().st_size < 10_000
