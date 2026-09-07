"Verified canonical evidence and shared display values; never refit analytics."

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.pipeline import PipelineContext

NAMES = {
    "hist_gradient_boosting": "HGB",
    "mlp": "MLP",
    "holt_winters": "Holt-Winters",
    "seasonal_naive": "Seasonal naïve",
}
COLORS = {
    "HGB": "#008b8d",
    "MLP": "#bd6509",
    "Holt-Winters": "#7254c7",
    "Seasonal naïve": "#62748d",
    "No eligible champion": "#b53843",
}
RETROSPECTIVE = (
    "RETROSPECTIVE: selection and performance use the same holdout; no"
    "t an unbiased estimate of future performance."
)
LABOR_LIMIT = (
    "The constrained optimizer changed where shortages landed and redu"
    "ced configured critical store-days, but did not improve retrospec"
    "tive total actual-demand coverage under equal priorities."
)
INVENTORY_LABEL = "Synthetic illustrative inventory proxy"
NO_IMPACT = "No DoorDash data was used. No DoorDash operating impact is claimed."
RECOMMENDATIONS = (
    "Govern champions locally rather than force one global model.",
    (
        "Review WI_2 / FOODS, CA_1 / FOODS, and TX_3 / FOODS first through"
        " the Forecast Accuracy DRI queue."
    ),
    (
        "Treat the labor objective as a prototype: test differentiated, ev"
        "idence-based priorities or service penalties on a future untouche"
        "d window before adoption."
    ),
)


def sha256(path: Path) -> str:
    """Hash a file without loading raw datasets into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """JSON conversion preserves undefined numeric metrics as null."""
    return list(json.loads(frame.to_json(orient="records", double_precision=15)))


def number(value: Any, *, percent: bool = False, signed: bool = False) -> str:
    if value is None or pd.isna(value):
        return "undefined"
    value = float(value) * (100 if percent else 1)
    return format(value, "+,.2f" if signed else ",.2f") + ("%" if percent else "")


@dataclass(frozen=True)
class Evidence:
    tables: dict[str, list[dict[str, Any]]]
    stages: dict[str, dict[str, Any]]
    hashes: dict[str, str]
    visuals: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    def row(self, table: str, **matches: Any) -> dict[str, Any]:
        rows = [r for r in self.tables[table] if all(r[k] == v for k, v in matches.items())]
        if len(rows) != 1:
            raise ValueError(f"Expected one canonical {table} row: {matches}")
        return rows[0]

    @property
    def counts(self) -> dict[str, int]:
        return {
            name: sum(c["champion_model"] == key for c in self.tables["champions"])
            for key, name in NAMES.items()
        } | {
            "No eligible champion": sum(
                c["champion_model"] is None for c in self.tables["champions"]
            )
        }

    @property
    def portfolio(self) -> str:
        local = self.row("local_champion_portfolio", portfolio="local_champions")
        base = self.row("local_champion_portfolio", portfolio="seasonal_naive_same_coverage")
        gain = (base["wape"] - local["wape"]) * 100
        return (
            f"{number(local['wape'], percent=True)} local portfolio WAPE versus "
            f"{number(base['wape'], percent=True)} matched seasonal-naïve WAPE; "
            f"{gain:.2f} percentage-point improvement on identical "
            f"{local['covered_series']}-series coverage."
        )

    @property
    def executive(self) -> str:
        best = min(self.tables["network_scorecard"], key=lambda r: r["wape"])
        return (
            f"Best single network model: {NAMES[best['model_name']]} at "
            f"{number(best['wape'], percent=True)} WAPE. "
            "No single model passed eligibility across all 20 series. "
            + self.portfolio
            + " "
            + RETROSPECTIVE
            + (
                " WI_2 / FOODS is the highest-priority forecast exception. TX_3 / "
                "FOODS: No eligible champion—review required. "
            )
            + LABOR_LIMIT
        )


def load_evidence(context: PipelineContext) -> Evidence:
    "Fail closed on stale, tampered, incomplete or non-real upstream evidence."
    root = context.paths.data
    stages = {
        n: read_json(root / f"{n}.metadata.json")
        for n in ("demand_daily", "predictions", "evaluation", "operations")
    }
    hashes: dict[str, str] = {}
    tables: dict[str, list[dict[str, Any]]] = {}
    for stage in ("evaluation", "operations"):
        for name, expected in stages[stage]["artifact_sha256"].items():
            path = root / f"{name}.csv"
            actual = sha256(path)
            if actual != expected:
                raise ValueError(f"Canonical evidence hash mismatch: {name}")
            hashes[str(path)] = actual
            tables[name] = records(pd.read_csv(path))
    for name, stage, key in [
        ("predictions", "predictions", "predictions_sha256"),
        ("demand_daily", "demand_daily", "parquet_sha256"),
    ]:
        path = root / f"{name}.parquet"
        if sha256(path) != stages[stage][key]:
            raise ValueError(f"Upstream hash mismatch: {name}")
        hashes[str(path)] = sha256(path)
    for name in stages:
        path = root / f"{name}.metadata.json"
        hashes[str(path)] = sha256(path)
    op = stages["operations"]
    ev = stages["evaluation"]
    if (
        op["complete"] is not True
        or op["actuals_used_for_allocation"] is not False
        or op["deterministic_rerun"] != "PASS"
        or ev["deterministic_evaluation_rerun"] != "PASS"
        or ev["sql_python_reconciliation"] != "PASS"
        or op["evaluation_sha256"] != sha256(root / "evaluation.metadata.json")
        or op["champions_sha256"] != sha256(root / "champions.csv")
        or op["predictions_sha256"] != stages["predictions"]["predictions_sha256"]
        or ev["predictions_sha256"] != op["predictions_sha256"]
        or ev["prepared_sha256"] != stages["demand_daily"]["parquet_sha256"]
        or stages["demand_daily"]["classification"] != "public_real_m5"
        or op["configuration"] != context.configuration.model_dump(mode="json")
    ):
        raise ValueError("Incomplete or stale analytical provenance/configuration")
    importance = root / "hist_gradient_boosting_importance.parquet"
    if sha256(importance) != stages["predictions"].get("interpretation_sha256"):
        raise ValueError("Upstream hash mismatch: interpretation")
    hashes[str(importance)] = sha256(importance)
    tables["hist_gradient_boosting_importance"] = records(pd.read_parquet(importance))
    e = Evidence(tables, stages, hashes)
    validate_story(e)
    from linkedin_visual_labs.projects.p25_quick_commerce_control_tower import presentation_charts

    e.visuals.update(
        presentation_charts.display_tables(
            pd.read_parquet(root / "demand_daily.parquet"),
            pd.read_parquet(root / "predictions.parquet"),
            tables["dri_exception_queue"],
        )
    )
    return e


def validate_story(e: Evidence) -> None:
    "Protect this approved story from becoming stale if analytics change later."
    cells = e.tables["champions"]
    if len(cells) != 20 or len({(c["store_id"], c["category"]) for c in cells}) != 20:
        raise ValueError("Champion map needs 20 unique cells")
    if len({c["store_id"] for c in cells}) != 10 or {c["category"] for c in cells} != {
        "FOODS",
        "HOUSEHOLD",
    }:
        raise ValueError("Champion grid scope mismatch")
    if e.counts != {
        "HGB": 9,
        "MLP": 7,
        "Holt-Winters": 3,
        "Seasonal naïve": 0,
        "No eligible champion": 1,
    }:
        raise ValueError("Approved champion story has changed")
    if e.row("champions", store_id="TX_3", category="FOODS")["champion_model"] is not None:
        raise ValueError("Contingency must not be a champion")
    if any(c["review_flag"] for c in cells) or any(
        c["globally_eligible"] for c in e.tables["network_scorecard"]
    ):
        raise ValueError("Approved governance story has changed")
    for scenario in ("Base", "+15% demand", "-10% productivity"):
        a = e.row("scenario_summary", scenario=scenario, allocation_method="proportional")
        b = e.row("scenario_summary", scenario=scenario, allocation_method="optimized")
        if abs(a["objective"] - b["objective"]) > 1e-7 * max(1, abs(a["objective"])):
            raise ValueError("Equal-objective narrative no longer holds")
        ar = e.row("retrospective_summary", scenario=scenario, allocation_method="proportional")
        br = e.row("retrospective_summary", scenario=scenario, allocation_method="optimized")
        if br["actual_uncovered_hours"] <= ar["actual_uncovered_hours"]:
            raise ValueError("Retrospective limitation no longer matches evidence")
    if any(r["feasibility"] != "feasible" for r in e.tables["scenario_summary"]):
        raise ValueError("Constraint success narrative requires feasible scenarios")
    if not all(r["synthetic"] and r["illustrative"] for r in e.tables["inventory_proxy"]):
        raise ValueError("Inventory classification missing")
