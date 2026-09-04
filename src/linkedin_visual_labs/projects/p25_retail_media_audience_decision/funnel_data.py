"""Retailrocket behavioral funnel for Project 4 Step 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, cast

import pandas as pd

SOURCE_DATASET: Final[str] = "RETAILROCKET"

EVIDENCE_CLASS: Final[str] = "ANONYMIZED_RETAIL_BEHAVIOR_EVENT_EVIDENCE"

EXPECTED_ROWS: Final[int] = 2_756_101

FUNNEL_EVENTS: Final[
    tuple[
        str,
        ...,
    ]
] = (
    "view",
    "addtocart",
    "transaction",
)


ALIASES: Final[
    dict[
        str,
        tuple[
            str,
            ...,
        ],
    ]
] = {
    "timestamp": (
        "timestamp",
        "event_timestamp",
        "timestamp_ms",
    ),
    "visitor": (
        "visitor_id",
        "visitorid",
        "retail_visitor_id",
    ),
    "event": (
        "event",
        "event_type",
    ),
    "item": (
        "item_id",
        "itemid",
        "retail_item_id",
    ),
    "transaction": (
        "transaction_id",
        "transactionid",
    ),
}


@dataclass(frozen=True)
class RetailrocketSchema:
    """Resolved source-scoped Retailrocket fields."""

    timestamp: str
    visitor: str
    event: str
    item: str
    transaction: str | None


@dataclass(frozen=True)
class FunnelFrames:
    """Governed Retailrocket funnel outputs."""

    conversion_funnel: pd.DataFrame
    metadata: dict[str, object]


def _int_scalar(
    value: object,
) -> int:
    return int(
        cast(
            Any,
            value,
        )
    )


def _safe_rate(
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return float(numerator / denominator)


def _resolve(
    source: pd.DataFrame,
    concept: str,
    *,
    required: bool = True,
) -> str | None:
    lookup = {str(column).strip().lower(): str(column) for column in source.columns}

    for alias in ALIASES[concept]:
        if alias in lookup:
            return lookup[alias]

    if required:
        raise ValueError(
            f"Retailrocket normalized {concept} field missing; columns={list(source.columns)}"
        )

    return None


def resolve_retailrocket_schema(
    source: pd.DataFrame,
) -> RetailrocketSchema:
    """Resolve normalized source aliases without altering Step 2."""

    timestamp = _resolve(
        source,
        "timestamp",
    )

    visitor = _resolve(
        source,
        "visitor",
    )

    event = _resolve(
        source,
        "event",
    )

    item = _resolve(
        source,
        "item",
    )

    transaction = _resolve(
        source,
        "transaction",
        required=False,
    )

    if timestamp is None or visitor is None or event is None or item is None:
        raise ValueError("Required Retailrocket source field resolution failed.")

    return RetailrocketSchema(
        timestamp=timestamp,
        visitor=visitor,
        event=event,
        item=item,
        transaction=transaction,
    )


def canonicalize_retailrocket(
    source: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    RetailrocketSchema,
]:
    """Build a temporary canonical analysis frame."""

    schema = resolve_retailrocket_schema(source)

    selected = [
        schema.timestamp,
        schema.visitor,
        schema.event,
        schema.item,
    ]

    if schema.transaction is not None:
        selected.append(schema.transaction)

    frame = source.loc[
        :,
        selected,
    ].copy()

    rename = {
        schema.timestamp: "timestamp",
        schema.visitor: "visitor_id",
        schema.event: "event",
        schema.item: "item_id",
    }

    if schema.transaction is not None:
        rename[schema.transaction] = "transaction_id"

    frame = frame.rename(columns=rename)

    frame["event"] = frame["event"].astype("string").str.strip().str.lower()

    return (
        frame,
        schema,
    )


def build_funnel_frames(
    source: pd.DataFrame,
    *,
    expected_rows: int | None = EXPECTED_ROWS,
) -> FunnelFrames:
    """Build source-separated Retailrocket event-volume funnel."""

    if expected_rows is not None and len(source) != expected_rows:
        raise ValueError(
            "Frozen Retailrocket row count changed: "
            f"expected={expected_rows}, observed={len(source)}"
        )

    frame, schema = canonicalize_retailrocket(source)

    observed_events = set(frame["event"].dropna().astype(str))

    if observed_events != set(FUNNEL_EVENTS):
        raise ValueError(f"Retailrocket event vocabulary changed: {sorted(observed_events)}")

    unique_visitors = int(frame["visitor_id"].nunique())

    event_counts = {event: _int_scalar((frame["event"] == event).sum()) for event in FUNNEL_EVENTS}

    visitor_counts = {
        event: int(
            frame.loc[
                frame["event"] == event,
                "visitor_id",
            ].nunique()
        )
        for event in FUNNEL_EVENTS
    }

    views = event_counts["view"]

    carts = event_counts["addtocart"]

    transactions = event_counts["transaction"]

    if views + carts + transactions != len(frame):
        raise ValueError("Retailrocket event categories do not conserve source rows.")

    if not (views >= carts >= transactions > 0):
        raise ValueError("Retailrocket event-volume funnel ordering failed.")

    view_to_cart = _safe_rate(
        carts,
        views,
    )

    cart_to_transaction = _safe_rate(
        transactions,
        carts,
    )

    view_to_transaction = _safe_rate(
        transactions,
        views,
    )

    records = [
        {
            "source_dataset": SOURCE_DATASET,
            "evidence_class": EVIDENCE_CLASS,
            "stage_order": 1,
            "stage": "VIEW",
            "event_type": "view",
            "event_count": views,
            "unique_stage_visitors": visitor_counts["view"],
            "total_unique_visitors": unique_visitors,
            "share_of_view_events": 1.0,
            "view_to_cart_rate": view_to_cart,
            "cart_to_transaction_rate": cart_to_transaction,
            "view_to_transaction_rate": view_to_transaction,
            "rate_basis": "EVENT_VOLUME_RATIO",
        },
        {
            "source_dataset": SOURCE_DATASET,
            "evidence_class": EVIDENCE_CLASS,
            "stage_order": 2,
            "stage": "ADD_TO_CART",
            "event_type": "addtocart",
            "event_count": carts,
            "unique_stage_visitors": visitor_counts["addtocart"],
            "total_unique_visitors": unique_visitors,
            "share_of_view_events": view_to_cart,
            "view_to_cart_rate": view_to_cart,
            "cart_to_transaction_rate": cart_to_transaction,
            "view_to_transaction_rate": view_to_transaction,
            "rate_basis": "EVENT_VOLUME_RATIO",
        },
        {
            "source_dataset": SOURCE_DATASET,
            "evidence_class": EVIDENCE_CLASS,
            "stage_order": 3,
            "stage": "TRANSACTION",
            "event_type": "transaction",
            "event_count": transactions,
            "unique_stage_visitors": visitor_counts["transaction"],
            "total_unique_visitors": unique_visitors,
            "share_of_view_events": view_to_transaction,
            "view_to_cart_rate": view_to_cart,
            "cart_to_transaction_rate": cart_to_transaction,
            "view_to_transaction_rate": view_to_transaction,
            "rate_basis": "EVENT_VOLUME_RATIO",
        },
    ]

    conversion_funnel = pd.DataFrame(records)

    metadata: dict[str, object] = {
        "source_dataset": SOURCE_DATASET,
        "evidence_class": EVIDENCE_CLASS,
        "source_rows": len(frame),
        "source_schema": {
            "timestamp": schema.timestamp,
            "visitor": schema.visitor,
            "event": schema.event,
            "item": schema.item,
            "transaction": schema.transaction,
        },
        "analysis_unit": ("anonymous behavioral event"),
        "visitor_key": ("source-scoped anonymous visitor_id"),
        "total_unique_visitors": unique_visitors,
        "event_counts": event_counts,
        "funnel_stages": list(FUNNEL_EVENTS),
        "rate_basis": (
            "event-volume ratios; not claimed as person-level sequential conversion probabilities"
        ),
        "source_boundary_policy": (
            "Retailrocket behavioral events remain separate from Criteo "
            "media impression journeys; no cross-source identity or row join"
        ),
    }

    return FunnelFrames(
        conversion_funnel=conversion_funnel,
        metadata=metadata,
    )
