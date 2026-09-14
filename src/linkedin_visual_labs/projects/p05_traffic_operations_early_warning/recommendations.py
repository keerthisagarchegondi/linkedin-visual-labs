"""Conditional prototype recommendations restricted to enabled review actions."""

from __future__ import annotations

from typing import Any

from .models import ActionType


def recommend(summary: dict[str, Any], enabled_actions: list[str]) -> dict[str, Any]:
    enabled = {ActionType(action) for action in enabled_actions}
    if enabled - {ActionType.MONITOR, ActionType.ESCALATE_FOR_REVIEW}:
        raise ValueError(
            "facility levers require independently reviewed context; absent for this source"
        )
    warning = summary.get("warning_timestamp")
    selected = ActionType.ESCALATE_FOR_REVIEW if warning is not None else ActionType.MONITOR
    action = selected if selected in enabled else None
    primary = summary.get("primary_driver")
    support = summary.get("supporting_drivers", [])
    ids = [str(v) for v in ([primary] if primary else []) + list(support)]
    return {
        "observed_pattern": "Multiple configured deterioration signals persisted."
        if warning is not None
        else "No qualifying warning; continue evidence review.",
        "supporting_metric_ids": ids,
        "likely_operational_issue": "Possible demand/discharge imbalance; cause not established."
        if warning is not None
        else "Insufficient evidence to identify an operating issue.",
        "recommended_action": None if action is None else action.value,
        "alternative_action": "MONITOR"
        if action == ActionType.ESCALATE_FOR_REVIEW and ActionType.MONITOR in enabled
        else None,
        "recommendation_classification": "ILLUSTRATIVE_RECOMMENDATION",
        "wording": "No action enabled; review configuration."
        if action is None
        else "Consider escalating the recorded deterioration for review."
        if action == ActionType.ESCALATE_FOR_REVIEW
        else "Consider monitoring the recorded metrics and their quality limitations.",
        "caveat": (
            "Prototype analytical review only. No road-control, staffing, overflow capacity "
            "or causal explanation has been validated."
        ),
        "evidence_timestamp": warning,
        "source_evidence": "data/warning_summary.json",
        "enabled_actions": sorted(a.value for a in enabled),
    }
