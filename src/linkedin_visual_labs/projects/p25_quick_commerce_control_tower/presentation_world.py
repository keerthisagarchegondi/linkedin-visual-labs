"""Deterministic analytical animation in a persistent ten-store network."""

from __future__ import annotations

import math
from typing import Any

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_canvas import (
    Canvas,
    allocation_example,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_evidence import (
    COLORS,
    NAMES,
    Evidence,
    number,
)
from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.presentation_story import Scene


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def positions(e: Evidence) -> dict[str, tuple[int, int]]:
    stores = sorted({r["store_id"] for r in e.tables["champions"]})
    return {
        store: (180 + ["CA", "TX", "WI"].index(store[:2]) * 340, 330 + int(store[-1]) * 75)
        for store in stores
    }


def transfers(e: Evidence) -> list[tuple[str, str, float]]:
    """Exact deterministic transport of allocated hours, not fabricated token counts."""
    _, pairs = allocation_example(e)
    donors: list[list[Any]] = [[s, p - o] for s, p, o in pairs if p > o]
    recipients: list[list[Any]] = [[s, o - p] for s, p, o in pairs if o > p]
    result: list[tuple[str, str, float]] = []
    for donor in donors:
        for recipient in recipients:
            amount = min(float(donor[1]), float(recipient[1]))
            if amount > 1e-8:
                result.append((str(donor[0]), str(recipient[0]), amount))
                donor[1] = float(donor[1]) - amount
                recipient[1] = float(recipient[1]) - amount
    if abs(sum(float(r[1]) for r in donors) - sum(float(r[1]) for r in recipients)) > 1e-6:
        raise ValueError("Transport must conserve allocated hours")
    return result


def world_canvas(e: Evidence, scene: Scene, progress: float) -> Canvas:
    """Keep stores stationary between beats; move evidence-bearing objects through them."""
    c = Canvas()
    p = max(0.0, min(1.0, progress))
    q = ease(p / 0.72)
    labor = scene.world == "labor"
    color = "#008b8d"
    c.text(
        "PUBLIC M5 / OPERATING DECISIONS" if labor else "PUBLIC M5 / FORECAST ARENA",
        48,
        40,
        980,
        30,
        22,
        "#1265ca",
        True,
    )
    c.text(scene.title, 48, 105, 984, 135, 43, bold=True)
    c.text("10 stores · 3 states · FOODS ●  HOUSEHOLD ◆", 48, 255, 984, 35, 23)
    nodes = positions(e)
    for i, state in enumerate(["California", "Texas", "Wisconsin"]):
        c.text(state, 60 + i * 340, 312, 285, 30, 22, "#52647a", True)
    for _store, (x, y) in nodes.items():
        c.draw.line((x, y, 540, 685), fill="#d3dfe8", width=2)
    example_date, pairs = allocation_example(e)
    pair_map = {s: (a, b) for s, a, b in pairs}
    chosen = sorted(e.tables["dri_exception_queue"], key=lambda r: r["priority_rank"])[:3]
    active = chosen[min(2, int(p * 3))]["store_id"] if scene.kind == "chase" else "TX_3"
    # Effects pass behind labels and opaque store cards.
    if scene.kind == "assignment":
        for index, row in enumerate(e.tables["champions"]):
            arrival = ease((p - index * 0.018) / 0.32)
            if 0 < arrival < 1:
                nx, ny = nodes[row["store_id"]]
                target_x = nx + (15 if row["category"] == "FOODS" else 63)
                badge_x = 540 + (target_x - 540) * arrival
                badge_y = 700 + (ny - 700) * arrival
                name = NAMES.get(row["champion_model"], "No eligible champion")
                c.draw.ellipse(
                    (badge_x - 11, badge_y - 11, badge_x + 11, badge_y + 11), fill=COLORS[name]
                )
    if scene.kind in ("transfer", "comparison"):
        for donor, recipient, amount in transfers(e):
            ax, ay = nodes[donor]
            bx, by = nodes[recipient]
            x, y = round(ax + (bx - ax) * q), round(ay + (by - ay) * q)
            c.draw.line((ax, ay, bx, by), fill="#89beb9", width=2)
            radius = 5 + min(8, int(math.sqrt(amount)))
            c.draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#008b8d")
    if scene.kind == "shock":
        local = (p * 2) % 1
        radius = 20 + int(450 * ease(local))
        c.draw.ellipse(
            (540 - radius, 500 - radius * 0.35, 540 + radius, 500 + radius * 0.35),
            outline="#bd6509",
            width=4,
        )
    for index, (store, (nx, ny)) in enumerate(nodes.items()):
        x, y = nx, ny
        if scene.kind == "world":
            x = round(540 + (nx - 540) * ease(min(1, p * 2.5)))
            y = round(685 + (ny - 685) * ease(min(1, p * 2.5)))
        warning = scene.kind in ("chase", "review") and store == active
        daily_rows = [
            r
            for r in e.tables["labor_allocations"]
            if r["date"] == example_date
            and r["store_id"] == store
            and r["scenario"] == "Base"
            and r["allocation_method"] == "proportional"
        ]
        if scene.kind == "distribution" and daily_rows:
            warning = bool(daily_rows[0].get("critical_store_day", False))
        if warning:
            radius = 35 + int(8 * (1 + math.sin(p * math.tau * 3)))
            c.draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius), outline="#b53843", width=3
            )
        c.draw.rounded_rectangle(
            (x - 116, y - 28, x + 116, y + 28),
            radius=10,
            fill="#fff3ef" if warning else "#ffffff",
            outline="#c8d7e3",
            width=2,
        )
        # Labels stay at final locations during the short entrance to avoid moving-text collisions.
        if scene.kind != "world" or p >= 0.4:
            c.text(store, x - 104, y - 10, 90, 26, 21, bold=True)
            if not labor:
                for j, category in enumerate(["FOODS", "HOUSEHOLD"]):
                    r = e.row("champions", store_id=store, category=category)
                    assigned = scene.kind in ("chase", "review", "loop") or (
                        scene.kind == "assignment" and q >= (index * 2 + j + 1) / 20
                    )
                    name = NAMES.get(r["champion_model"], "No eligible champion")
                    fill = COLORS[name] if assigned else "#d8e3eb"
                    bx = x + 15 + j * 48
                    c.draw.ellipse((bx - 15, y - 15, bx + 15, y + 15), fill=fill)
                    if assigned:
                        c.text(
                            {
                                "HGB": "H",
                                "MLP": "M",
                                "Holt-Winters": "W",
                                "No eligible champion": "!",
                                "Seasonal naïve": "N",
                            }[name],
                            bx - 8,
                            y - 10,
                            25,
                            25,
                            20,
                            "#ffffff",
                            True,
                        )
            else:
                a, b = pair_map[store]
                blend = (
                    q
                    if scene.kind in ("transfer", "comparison")
                    else (
                        1.0
                        if scene.kind
                        in (
                            "shock",
                            "objective",
                            "impact",
                            "missing_inputs",
                            "allocation_result",
                            "loop",
                        )
                        else 0.0
                    )
                )
                hours = a + (b - a) * blend
                if scene.kind == "conversion" and daily_rows:
                    hours = float(daily_rows[0].get("required_hours", hours)) * q
                if scene.kind == "shock":
                    shock_name = "+15% demand" if p < 0.5 else "-10% productivity"
                    shock_rows = [
                        r
                        for r in e.tables["labor_allocations"]
                        if r["date"] == example_date
                        and r["store_id"] == store
                        and r["scenario"] == shock_name
                        and r["allocation_method"] == "optimized"
                    ]
                    if shock_rows:
                        target_hours = float(shock_rows[0]["allocated_hours"])
                        hours = b + (target_hours - b) * ease(min(1, ((p * 2) % 1) / 0.7))
                if scene.kind == "distribution":
                    hours *= q
                c.text(
                    "Demand" if scene.kind == "world" else f"{hours:.1f} h",
                    x + 2,
                    y - 10,
                    105,
                    26,
                    20,
                    color,
                    True,
                )
        # Category-stream motion is illustrative, not a measured arrivals simulation.
        phase = (p * 2 + index / 10) % 1
        radius = 5
        if scene.kind == "shock" and p < 0.5:
            radius = 7
        px, py = x - 95 + 190 * phase, y - 37
        c.draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill="#008b8d")
        c.draw.rectangle(
            (x + 90 - 180 * phase - 4, y + 32, x + 90 - 180 * phase + 4, y + 40), fill="#bd6509"
        )
    c.draw.line((56, 700, 1024, 700), fill="#d3dfe8", width=2)
    if scene.kind == "world":
        if labor:
            settings = e.stages["operations"]["configuration"]["labor"]
            c.text(
                f"{settings['daily_network_hours']:g} labor hours/day",
                70,
                760,
                940,
                90,
                56,
                bold=True,
            )
            c.draw.rounded_rectangle((70, 885, 1010, 925), radius=10, fill="#15364e")
            c.text("FIXED CAPACITY POOL", 70, 955, 940, 45, 28)
        else:
            c.text("20 streams. Four contenders.", 70, 770, 940, 80, 46, bold=True)
            c.text("Who earns local ownership?", 70, 885, 940, 70, 38, color)
            c.text("Demand motion is illustrative; results are measured.", 70, 995, 940, 40, 23)
    elif scene.kind == "contenders":
        for i, (name, family) in enumerate(scene.items):
            x = 60 + i * 245
            y = 770 + round(75 * (1 - ease(p * 2 - i * 0.18)))
            c.draw.ellipse((x + 60, y - 24, x + 92, y + 8), fill=COLORS.get(name, "#62748d"))
            c.text(name, x, y + 24, 235, 60, 23, bold=True)
            c.text(family, x, y + 92, 230, 60, 21)
            c.draw.line((x + 75, y + 156, x + 75, 994), fill="#008b8d", width=3)
        c.draw.rectangle((70, 995, 70 + int(930 * q), 1025), fill="#e1b777")
        c.text("COMMON HOLDOUT · 25 APR \u2013 22 MAY 2016", 70, 1040, 940, 35, 24)
    elif scene.kind == "race":
        sample = e.visuals.get("forecast_example", [])
        if not sample:
            raise ValueError("Forecast animation requires canonical representative predictions")
        c.text(
            f"{sample[0]['store_id']} / {sample[0]['category']} · demand units/day",
            70,
            720,
            940,
            35,
            24,
        )
        values = [float(r[k]) for r in sample for k in ("actual_units", "forecast_units")]
        low, high = min(values) * 0.9, max(values) * 1.05
        c.draw.line((110, 780, 110, 1010, 990, 1010), fill="#52647a", width=2)
        c.text(f"{high:,.0f}", 45, 772, 95, 25, 20)
        c.text(f"{low:,.0f}", 45, 990, 95, 25, 20)
        for model, name in [("actual", "Actual"), *NAMES.items()]:
            rows = [
                r
                for r in sample
                if r["model_name"] == (sample[0]["model_name"] if model == "actual" else model)
            ]
            rows.sort(key=lambda r: r["date"])
            count = max(2, min(len(rows), int(len(rows) * q)))
            points = [
                (
                    110 + 880 * i / (len(rows) - 1),
                    1008
                    - 220
                    * (float(r["actual_units" if model == "actual" else "forecast_units"]) - low)
                    / (high - low),
                )
                for i, r in enumerate(rows[:count])
            ]
            c.draw.line(points, fill="#142e49" if model == "actual" else COLORS[name], width=4)
        c.text("Apr 25 → common 28-day holdout → May 22", 130, 1028, 850, 30, 22)
        for legend_index, legend_name in enumerate(["Actual", *NAMES.values()]):
            c.text(
                legend_name,
                70 + legend_index * 193,
                1070,
                190,
                30,
                20,
                COLORS.get(legend_name, "#142e49"),
                True,
            )
    elif scene.kind == "assignment":
        for i, name in enumerate(["HGB", "MLP", "Holt-Winters", "No eligible champion"]):
            x, y = 65 + (i % 2) * 500, 740 + (i // 2) * 120
            c.text(
                "Review required" if name == "No eligible champion" else name,
                x,
                y,
                450,
                40,
                28,
                COLORS[name],
                True,
            )
            c.text(str(round(e.counts[name] * q)), x, y + 48, 450, 60, 50, bold=True)
        c.text("Local ownership, subject to governance", 65, 1010, 950, 50, 32, color, True)
    elif scene.kind == "chase":
        for i, r in enumerate(chosen):
            y = 740 + i * 100
            c.text(r["store_id"] + " / " + r["category"], 65, y, 360, 35, 28, bold=True)
            value = float(r.get("shortfall_units", 0))
            max_value = max(float(row.get("shortfall_units", 0)) for row in chosen)
            width = 420 * value / max(1, max_value) * ease(p * 3 - i * 0.6)
            c.draw.rectangle((460, y, 460 + width, y + 25), fill="#b53843")
            c.text(f"{value:,.0f} shortfall units", 460, y + 34, 550, 35, 24)
        c.text("Next: review inputs and test recalibration", 65, 1060, 950, 40, 28, color, True)
    elif scene.kind == "review":
        c.text("Operating forecast portfolio", 65, 735, 950, 55, 36, color, True)
        c.text("NO ELIGIBLE CHAMPION", 65, 815, 950, 65, 48, "#b53843", True)
        c.text("TX_3 / FOODS", 65, 900, 950, 60, 42, bold=True)
        c.text("Separate planning contingency: seasonal naïve", 65, 1000, 950, 70, 30)
    elif scene.kind in ("conversion", "distribution"):
        date, _ = allocation_example(e)
        settings = e.stages["operations"]["configuration"]["labor"]
        if scene.kind == "conversion":
            for i, cat in enumerate(["FOODS", "HOUSEHOLD"]):
                x = 65 + i * 500
                rate = settings["productivity_units_per_hour"][cat]
                c.text(cat, x, 745, 450, 35, 28, bold=True)
                c.text(f"÷ {rate:g} units/hour", x, 795, 450, 55, 34, color, True)
                c.draw.line((x + 35, 870, x + int(390 * q), 870), fill=color, width=8)
            c.text("→ Sum required hours at each store", 65, 920, 950, 50, 35, bold=True)
        else:
            for _store, (x, y) in nodes.items():
                tx, ty = 540 + (x - 540) * q, 685 + (y - 685) * q
                c.draw.ellipse((tx - 8, ty - 8, tx + 8, ty + 8), fill=color)
            c.text("PROPORTIONAL → STORE WORKLOAD", 65, 765, 950, 65, 38, bold=True)
            c.text(
                f"{sum(a for _, a, _ in pairs):.2f} allocated hours",
                65,
                870,
                950,
                70,
                46,
                color,
                True,
            )
        c.text(f"Illustrative assumptions · Base example {date}", 65, 1030, 950, 45, 25)
    elif scene.kind == "comparison":
        c.text("Proportional → HiGHS optimized", 65, 760, 950, 60, 40, bold=True)
        c.text(
            f"{sum(a for _, a, _ in pairs):.2f} hours in each plan",
            65,
            850,
            950,
            65,
            44,
            color,
            True,
        )
        c.text("Same demand. Same capacity. Different distribution.", 65, 960, 950, 80, 30)
    elif scene.kind in ("transfer", "allocation_result"):
        for i, (label, text_value) in enumerate(scene.items):
            y = 750 + i * 148
            if i == 0:
                before = e.row(
                    "scenario_summary", scenario="Base", allocation_method="proportional"
                )["critical_store_days"]
                after = e.row("scenario_summary", scenario="Base", allocation_method="optimized")[
                    "critical_store_days"
                ]
                label += " · " + text_value
                text_value = f"{before + (after - before) * q:.0f}"
            c.text(label, 65, y, 950, 40, 28, "#b53843" if i else color, True)
            c.text(text_value, 65, y + 52, 950, 70, 49, bold=True)
        c.text(
            "SAME total hours · actual coverage worsened", 65, 1050, 950, 40, 28, "#b53843", True
        )
    elif scene.kind == "shock":
        scenario = "+15% demand" if p < 0.5 else "-10% productivity"
        local = (p * 2) % 1
        r = e.row("scenario_summary", scenario=scenario, allocation_method="optimized")
        pr = e.row("scenario_summary", scenario=scenario, allocation_method="proportional")
        c.text(scenario.upper(), 65, 750, 950, 60, 44, "#b53843", True)
        c.text(
            "Demand \u00d71.15" if p < 0.5 else "Workload \u00d7(1 / 0.90)", 65, 830, 950, 45, 32
        )
        base_required = e.row("scenario_summary", scenario="Base", allocation_method="optimized")[
            "required_hours"
        ]
        max_required = max(
            e.row("scenario_summary", scenario=s, allocation_method="optimized")["required_hours"]
            for s in ["Base", "+15% demand", "-10% productivity"]
        )
        shown_required = base_required + (r["required_hours"] - base_required) * ease(
            min(1, local / 0.7)
        )
        c.draw.rectangle(
            (65, 895, 65 + int(850 * base_required / max_required), 920), fill="#c8d7e3"
        )
        c.draw.rectangle(
            (65, 895, 65 + int(850 * shown_required / max_required), 920), fill="#bd6509"
        )
        c.text(f"{shown_required:,.0f} required hours / 28-day holdout", 65, 928, 950, 26, 22)
        c.text(
            f"Critical store-days: {pr['critical_store_days']} → {r['critical_store_days']}",
            65,
            960,
            950,
            55,
            36,
            bold=True,
        )
        c.text(
            "Fixed capacity · " + number(r["uncovered_hours"]) + " h uncovered",
            65,
            1040,
            950,
            40,
            28,
        )
    elif scene.kind == "impact":
        c.text("NEXT: CALIBRATE", 65, 750, 950, 100, 60, "#008b8d", True)
        c.text("Equal priorities move shortages.", 65, 885, 950, 60, 40, bold=True)
        c.text("Richer business inputs are needed.", 65, 980, 950, 65, 34)
        c.draw.line((65, 1070, 65 + int(930 * q), 1070), fill="#b53843", width=8)
    elif scene.kind == "missing_inputs":
        labels = [
            "Service priorities",
            "Actual productivity",
            "Shift constraints",
            "Shortage costs",
            "Inventory / replenishment",
        ]
        for i, label in enumerate(labels):
            y = 735 + i * 72
            c.draw.ellipse((65, y, 87, y + 22), fill=color if q > i / len(labels) else "#c8d7e3")
            c.text(label, 115, y, 880, 50, 34, bold=True)
    elif scene.kind == "objective":
        settings = e.stages["operations"]["configuration"]["labor"]
        c.text("Minimize labor cost + uncovered penalty", 65, 750, 950, 60, 36, bold=True)
        c.text(
            f"Cost {settings['cost_per_hour']:g}/hour · "
            f"penalty {settings['uncovered_hour_penalty']:g}/hour",
            65,
            840,
            950,
            55,
            32,
        )
        c.text("All priorities = 1 · same objective value", 65, 930, 950, 50, 32, color, True)
        c.draw.line((65, 1030, 65 + int(930 * q), 1030), fill=color, width=10)
    elif scene.kind == "loop":
        labels = (
            ["Forecast", "Diagnose", "Allocate", "Measure", "Experiment"]
            if labor
            else ["Forecast", "Select", "Diagnose", "Experiment"]
        )
        for i, label in enumerate(labels):
            x = 65 + i * int(950 / len(labels))
            c.text(label, x, 790, 190, 45, 23, bold=True)
            c.draw.line((x + 30, 880, min(1010, x + 220), 880), fill="#89beb9", width=4)
        x = round(80 + 920 * ((p * 1.5) % 1))
        c.draw.ellipse((x - 12, 868, x + 12, 892), fill=color)
        c.text(
            "Then optimize." if labor else "One network. Different demand patterns.",
            65,
            970,
            950,
            110,
            42,
            color,
            True,
        )
    c.text(scene.caption, 65, 1140, 950, 150, 30)
    c.validate()
    return c
