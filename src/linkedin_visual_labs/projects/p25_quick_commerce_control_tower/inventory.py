"""Independent synthetic on-hand snapshots, not replenishment or stockout probabilities."""

from __future__ import annotations

import numpy as np
import pandas as pd

from linkedin_visual_labs.common.random_state import create_namespaced_rng
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import GRAIN, DataError
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.models import (
    PROJECT_ID,
    InventoryConfig,
)


def risk_status(cover: float | None, config: InventoryConfig) -> str:
    if cover is None:
        return "Healthy"  # Explicit no-forecast-demand status accompanies this convention.
    if cover < config.expedite_below_days:
        return "Expedite"
    if cover < config.reorder_below_days:
        return "Reorder"
    if cover < config.monitor_below_days:
        return "Monitor"
    return "Healthy"


def inventory_proxy(planning: pd.DataFrame, config: InventoryConfig, seed: int) -> pd.DataFrame:
    frame = (
        planning[
            [
                *GRAIN,
                "forecast_units",
                "forecast_source_model",
                "champion_status",
                "contingency_used",
            ]
        ]
        .sort_values(GRAIN)
        .copy()
    )
    if (
        frame.duplicated(GRAIN).any()
        or frame[GRAIN].isna().any().any()
        or not np.isfinite(frame["forecast_units"].to_numpy(dtype=float)).all()
        or frame["forecast_units"].lt(0).any()
    ):
        raise DataError("inventory proxy requires unique complete finite nonnegative forecasts")
    rows: list[dict[str, object]] = []
    for (store, category), group in frame.groupby(["store_id", "category"], sort=True):
        group = group.sort_values("date").reset_index(drop=True)
        if len(group) != 28 or not group["date"].diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise DataError("inventory requires the complete continuous 28-day forecast window")
        for index, record in enumerate(group.to_dict(orient="records")):
            future = group.iloc[index : index + config.window_days]
            mean = float(future["forecast_units"].mean())
            date = pd.Timestamp(record["date"])
            rng = create_namespaced_rng(
                seed, f"{PROJECT_ID}:inventory:{store}:{category}:{date.date()}"
            )
            multiplier = float(rng.uniform(config.on_hand_days_min, config.on_hand_days_max))
            on_hand = float(np.floor(mean * multiplier))
            cover = on_hand / mean if mean > 0 else None
            rows.append(
                {
                    **{str(k): v for k, v in record.items()},
                    "synthetic_on_hand_units": on_hand,
                    "forecast_daily_mean": mean,
                    "window_days": len(future),
                    "configured_window_days": config.window_days,
                    "window_status": "full"
                    if len(future) == config.window_days
                    else "shortened_at_holdout_end",
                    "generation_days_multiplier": multiplier,
                    "days_of_cover": cover,
                    "cover_status": "undefined_zero_demand"
                    if mean == 0
                    else "low_forecast_demand"
                    if mean < config.low_demand_units_per_day
                    else "defined",
                    "risk_status": risk_status(cover, config),
                    "synthetic": True,
                    "illustrative": True,
                    "classification": "synthetic_illustrative_snapshot",
                }
            )
    return pd.DataFrame(rows).sort_values(GRAIN).reset_index(drop=True)
