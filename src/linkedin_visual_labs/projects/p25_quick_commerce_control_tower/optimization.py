"""Forecast-only continuous labor allocation with explicit feasibility and HiGHS status."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy.optimize import linprog  # type: ignore[import-untyped]

from linkedin_visual_labs.projects.p25_quick_commerce_control_tower.data import DataError


@dataclass(frozen=True)
class DayProblem:
    """Typed decision inputs deliberately exclude realized demand and model errors."""

    stores: tuple[str, ...]
    required_hours: tuple[float, ...]
    minimum_hours: tuple[float, ...]
    maximum_hours: tuple[float, ...]
    hourly_cost: tuple[float, ...]
    priority_weight: tuple[float, ...]
    capacity: float
    uncovered_penalty: float
    tolerance: float


@dataclass(frozen=True)
class DayAllocation:
    method: str
    status: str
    message: str
    hours: tuple[float, ...]
    uncovered: tuple[float, ...]
    objective: float | None


def validate_problem(problem: DayProblem) -> None:
    arrays = (
        problem.required_hours,
        problem.minimum_hours,
        problem.maximum_hours,
        problem.hourly_cost,
        problem.priority_weight,
    )
    if not problem.stores or len(set(problem.stores)) != len(problem.stores):
        raise DataError("planning stores must be nonempty and unique")
    if any(len(values) != len(problem.stores) for values in arrays):
        raise DataError("planning vectors must match store count")
    if any(not np.isfinite(values).all() or np.any(np.asarray(values) < 0) for values in arrays):
        raise DataError("planning vectors must be finite and nonnegative")
    if not np.isfinite([problem.capacity, problem.uncovered_penalty, problem.tolerance]).all():
        raise DataError("planning scalars must be finite")
    if problem.capacity < 0 or problem.uncovered_penalty <= 0 or problem.tolerance <= 0:
        raise DataError("invalid capacity, penalty, or solver tolerance")
    if np.any(np.asarray(problem.priority_weight) <= 0):
        raise DataError("priority weights must be positive")


def objective(problem: DayProblem, hours: tuple[float, ...]) -> float:
    h = np.asarray(hours)
    uncovered = np.maximum(np.asarray(problem.required_hours) - h, 0)
    return float(
        np.dot(problem.hourly_cost, h)
        + problem.uncovered_penalty * np.dot(problem.priority_weight, uncovered)
    )


def validate_allocation(problem: DayProblem, allocation: DayAllocation) -> None:
    h, u = np.asarray(allocation.hours), np.asarray(allocation.uncovered)
    tolerance = problem.tolerance
    if h.shape != (len(problem.stores),) or u.shape != h.shape or not np.isfinite([h, u]).all():
        raise DataError("invalid allocation vector")
    if (
        np.any(h < -tolerance)
        or np.any(u < -tolerance)
        or np.any(h < np.asarray(problem.minimum_hours) - tolerance)
        or np.any(h > np.asarray(problem.maximum_hours) + tolerance)
        or h.sum() > problem.capacity + tolerance
        or not np.allclose(
            u, np.maximum(np.asarray(problem.required_hours) - h, 0), rtol=0, atol=tolerance
        )
    ):
        raise DataError("allocation violates staffing, workload, or fixed capacity")
    if allocation.objective is None or not np.isclose(
        allocation.objective, objective(problem, allocation.hours), rtol=1e-10, atol=tolerance
    ):
        raise DataError("allocation objective does not reconcile")


def allocate_day(
    problem: DayProblem, method: Literal["proportional", "optimized"]
) -> DayAllocation:
    validate_problem(problem)
    lower, upper = np.asarray(problem.minimum_hours), np.asarray(problem.maximum_hours)
    required = np.asarray(problem.required_hours)
    if lower.sum() > problem.capacity or np.any(lower > upper):
        return DayAllocation(
            method,
            "infeasible",
            f"minimum_total={lower.sum():.9g}; "
            f"network_capacity={problem.capacity:.9g}; "
            f"bounds_reversed={bool(np.any(lower > upper))}",
            (),
            (),
            None,
        )
    if method == "proportional":
        hours = lower.copy()
        # Each saturation removes a store; at most n+1 rounds, with no forced oversupply.
        for _ in range(len(hours) + 1):
            remaining = max(problem.capacity - float(hours.sum()), 0)
            unmet = np.maximum(required - hours, 0)
            room = np.maximum(upper - hours, 0)
            weights = np.where(room > problem.tolerance, unmet, 0)
            if remaining <= problem.tolerance or weights.sum() <= problem.tolerance:
                break
            increments = np.minimum(np.minimum(room, unmet), remaining * weights / weights.sum())
            hours += increments
        message = "minimum-first proportional unmet-workload water filling"
    elif method == "optimized":
        n = len(problem.stores)
        costs = np.r_[
            problem.hourly_cost, problem.uncovered_penalty * np.asarray(problem.priority_weight)
        ]
        constraints = np.vstack([np.r_[np.ones(n), np.zeros(n)], np.c_[-np.eye(n), -np.eye(n)]])
        limits = np.r_[problem.capacity, -required]
        bounds = [(float(a), float(b)) for a, b in zip(lower, upper, strict=True)] + [
            (0.0, None)
        ] * n
        try:
            result = linprog(
                costs,
                A_ub=constraints,
                b_ub=limits,
                bounds=bounds,
                method="highs",
                options={
                    "primal_feasibility_tolerance": problem.tolerance,
                    "dual_feasibility_tolerance": problem.tolerance,
                },
            )
        except Exception as exc:
            return DayAllocation(
                method, "solver_failed", f"{type(exc).__name__}: {exc}", (), (), None
            )
        if not result.success:
            return DayAllocation(
                method,
                "solver_failed",
                f"HiGHS status {result.status}: {result.message}",
                (),
                (),
                None,
            )
        hours = np.asarray(result.x[:n], dtype=float)
        allocation = DayAllocation(
            method,
            "feasible",
            str(result.message),
            tuple(hours.tolist()),
            tuple(np.asarray(result.x[n:], dtype=float).tolist()),
            float(result.fun),
        )
        validate_allocation(problem, allocation)
        return allocation
    else:
        raise DataError("unknown allocation method")
    result_hours = tuple(float(x) for x in hours)
    allocation = DayAllocation(
        method,
        "feasible",
        message,
        result_hours,
        tuple(np.maximum(required - hours, 0).tolist()),
        objective(problem, result_hours),
    )
    validate_allocation(problem, allocation)
    return allocation
