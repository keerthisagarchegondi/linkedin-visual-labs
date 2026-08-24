"""Revised Step 7R evaluation-output enrichment.

This module does NOT determine winners.

The canonical evaluation.py pipeline remains authoritative for:
- realized route metrics,
- city winners,
- normalized regret,
- overall winner,
- Oracle eligibility.

This module only appends:
- route-divergence descriptors,
- real search-efficiency descriptors from Step 10R.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Final

HEADLINE_METHODS: Final[
    tuple[
        str,
        ...,
    ]
] = (
    "dijkstra",
    "ml",
    "dl",
)

SHOWCASE_CITIES: Final[
    tuple[
        str,
        ...,
    ]
] = (
    "new_york",
    "chicago",
    "phoenix",
)


def _position(
    value: object,
) -> tuple[
    int,
    int,
]:
    if isinstance(
        value,
        dict,
    ):
        row = value.get("row")

        column = value.get("column")

        if isinstance(
            row,
            int,
        ) and isinstance(
            column,
            int,
        ):
            return (
                row,
                column,
            )

    if (
        isinstance(
            value,
            (
                list,
                tuple,
            ),
        )
        and len(value) == 2
        and isinstance(
            value[0],
            int,
        )
        and isinstance(
            value[1],
            int,
        )
    ):
        return (
            value[0],
            value[1],
        )

    raise ValueError(f"unsupported position: {value!r}")


def _path(
    route: object,
) -> tuple[
    tuple[
        int,
        int,
    ],
    ...,
]:
    if not isinstance(
        route,
        dict,
    ):
        raise ValueError("route must be a mapping")

    raw = route.get("path")

    if not isinstance(
        raw,
        list,
    ):
        raise ValueError("route.path must be a list")

    result = tuple(_position(item) for item in raw)

    if len(result) < 2:
        raise ValueError("route path must contain at least 2 cells")

    return result


def _edges(
    path: tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ],
) -> frozenset[
    tuple[
        tuple[
            int,
            int,
        ],
        tuple[
            int,
            int,
        ],
    ]
]:
    return frozenset(
        (
            path[index],
            path[index + 1],
        )
        for index in range(len(path) - 1)
    )


def _edge_jaccard(
    left: tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ],
    right: tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ],
) -> float:
    left_edges = _edges(left)

    right_edges = _edges(right)

    union = left_edges | right_edges

    if not union:
        return 1.0

    return len(left_edges & right_edges) / len(union)


def _route_separation(
    left: tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ],
    right: tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ],
) -> int:
    """
    Maximum Manhattan separation between nearest corresponding
    progress points after deterministic progress normalization.
    """
    samples = max(
        len(left),
        len(right),
    )

    if samples <= 1:
        return 0

    maximum = 0

    for index in range(samples):
        fraction = index / (samples - 1)

        left_index = round(fraction * (len(left) - 1))

        right_index = round(fraction * (len(right) - 1))

        left_point = left[left_index]

        right_point = right[right_index]

        distance = abs(left_point[0] - right_point[0]) + abs(left_point[1] - right_point[1])

        maximum = max(
            maximum,
            distance,
        )

    return maximum


def _routes_by_city_method(
    routes: dict[str, object],
) -> dict[
    tuple[
        str,
        str,
    ],
    tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ],
]:
    """
    Resolve headline routes through the canonical Project-2 route adapter.

    Do not duplicate routes.json serialization knowledge here.
    Step 10R already relies on visualization._method_route(), so Revised
    Step 7R uses the same resolver to remain synchronized with the existing
    route artifact contract.
    """
    from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
        _method_route,
    )

    result: dict[
        tuple[
            str,
            str,
        ],
        tuple[
            tuple[
                int,
                int,
            ],
            ...,
        ],
    ] = {}

    for city_id in SHOWCASE_CITIES:
        for method_id in HEADLINE_METHODS:
            route = _method_route(
                routes,
                city_id,
                method_id,
            )

            result[
                (
                    city_id,
                    method_id,
                )
            ] = _path(route)

    return result


def _trace_by_city_method(
    traces: dict[str, object],
) -> dict[
    tuple[
        str,
        str,
    ],
    dict[str, object],
]:
    raw = traces.get("traces")

    if not isinstance(
        raw,
        list,
    ):
        raise ValueError("search traces must contain traces list")

    result: dict[
        tuple[
            str,
            str,
        ],
        dict[str, object],
    ] = {}

    for trace in raw:
        if not isinstance(
            trace,
            dict,
        ):
            raise ValueError("trace entry must be a mapping")

        city_id = trace.get("city_id")

        method_id = trace.get("method_id")

        if not isinstance(
            city_id,
            str,
        ):
            raise ValueError("trace.city_id must be string")

        if not isinstance(
            method_id,
            str,
        ):
            raise ValueError("trace.method_id must be string")

        result[
            (
                city_id,
                method_id,
            )
        ] = trace

    return result


def _integer(
    value: object,
    *,
    field: str,
) -> int:
    if isinstance(
        value,
        bool,
    ):
        raise ValueError(f"{field} cannot be bool")

    if isinstance(
        value,
        int,
    ):
        return value

    raise ValueError(f"{field} must be int")


def _method_metrics(
    *,
    city_id: str,
    method_id: str,
    routes: dict[
        tuple[
            str,
            str,
        ],
        tuple[
            tuple[
                int,
                int,
            ],
            ...,
        ],
    ],
    traces: dict[
        tuple[
            str,
            str,
        ],
        dict[str, object],
    ],
) -> dict[str, object]:
    path = routes[
        (
            city_id,
            method_id,
        )
    ]

    comparisons: list[float] = []

    separations: list[int] = []

    for other_method in HEADLINE_METHODS:
        if other_method == method_id:
            continue

        other = routes[
            (
                city_id,
                other_method,
            )
        ]

        comparisons.append(
            _edge_jaccard(
                path,
                other,
            )
        )

        separations.append(
            _route_separation(
                path,
                other,
            )
        )

    trace = traces[
        (
            city_id,
            method_id,
        )
    ]

    expanded = _integer(
        trace.get("expanded_node_count"),
        field="expanded_node_count",
    )

    tree = _integer(
        trace.get("discovered_tree_edge_count"),
        field="discovered_tree_edge_count",
    )

    blocked = _integer(
        trace.get("blocked_edge_count"),
        field="blocked_edge_count",
    )

    raw_tree_edges = trace.get("tree_edges")

    if not isinstance(
        raw_tree_edges,
        list,
    ):
        raise ValueError("trace.tree_edges must be list")

    final_edges = sum(
        (
            isinstance(
                edge,
                dict,
            )
            and edge.get("classification") == "final_route"
        )
        for edge in raw_tree_edges
    )

    rejected_edges = sum(
        (
            isinstance(
                edge,
                dict,
            )
            and edge.get("classification") == "explored_rejected"
        )
        for edge in raw_tree_edges
    )

    expected_final = len(path) - 1

    if final_edges != expected_final:
        raise ValueError(
            f"{city_id}/{method_id}: trace final-route edge count does not match route path"
        )

    unique = all(similarity < 1.0 for similarity in comparisons)

    final_denominator = max(
        final_edges,
        1,
    )

    expanded_denominator = max(
        expanded,
        1,
    )

    return {
        "route_unique_vs_other_methods": (unique),
        "mean_edge_jaccard_vs_other_methods": (sum(comparisons) / len(comparisons)),
        "minimum_edge_jaccard_vs_other_methods": (min(comparisons)),
        "maximum_edge_jaccard_vs_other_methods": (max(comparisons)),
        "maximum_route_separation_vs_other_methods": (max(separations)),
        "expanded_node_count": (expanded),
        "search_tree_edge_count": (tree),
        "rejected_tree_edge_count": (rejected_edges),
        "final_route_edge_count": (final_edges),
        "blocked_edge_count": (blocked),
        "expansions_per_final_edge": (expanded / final_denominator),
        "tree_edges_per_final_edge": (tree / final_denominator),
        "search_efficiency_ratio": (final_edges / expanded_denominator),
    }


def build_method_metrics(
    *,
    routes_payload: dict[str, object],
    trace_payload: dict[str, object],
) -> dict[
    tuple[
        str,
        str,
    ],
    dict[str, object],
]:
    routes = _routes_by_city_method(routes_payload)

    traces = _trace_by_city_method(trace_payload)

    expected = {
        (
            city,
            method,
        )
        for city in SHOWCASE_CITIES
        for method in HEADLINE_METHODS
    }

    if not (expected <= set(routes)):
        missing = expected - set(routes)

        raise ValueError(f"missing headline routes: {sorted(missing)}")

    if not (expected <= set(traces)):
        missing = expected - set(traces)

        raise ValueError(f"missing search traces: {sorted(missing)}")

    return {
        pair: _method_metrics(
            city_id=pair[0],
            method_id=pair[1],
            routes=routes,
            traces=traces,
        )
        for pair in sorted(expected)
    }


def _first_existing_column(
    columns: list[str],
    candidates: tuple[
        str,
        ...,
    ],
) -> str:
    for candidate in candidates:
        if candidate in columns:
            return candidate

    raise ValueError(f"required column missing; candidates={candidates}; actual={columns}")


def _csv_value(
    value: object,
) -> str:
    if isinstance(
        value,
        bool,
    ):
        return "true" if value else "false"

    if isinstance(
        value,
        float,
    ):
        return f"{value:.12g}"

    return str(value)


def enrich_route_comparison(
    *,
    path: Path,
    metrics: dict[
        tuple[
            str,
            str,
        ],
        dict[str, object],
    ],
) -> None:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        rows = list(reader)

        columns = list(reader.fieldnames or [])

    city_column = _first_existing_column(
        columns,
        (
            "city_id",
            "city",
        ),
    )

    method_column = _first_existing_column(
        columns,
        (
            "method_id",
            "method",
            "planner",
        ),
    )

    enrichment_columns = [
        "route_unique_vs_other_methods",
        "mean_edge_jaccard_vs_other_methods",
        "minimum_edge_jaccard_vs_other_methods",
        "maximum_edge_jaccard_vs_other_methods",
        "maximum_route_separation_vs_other_methods",
        "expanded_node_count",
        "search_tree_edge_count",
        "rejected_tree_edge_count",
        "final_route_edge_count",
        "blocked_edge_count",
        "expansions_per_final_edge",
        "tree_edges_per_final_edge",
        "search_efficiency_ratio",
    ]

    output_columns = columns + [column for column in enrichment_columns if column not in columns]

    for row in rows:
        pair = (
            row[city_column],
            row[method_column],
        )

        if pair not in metrics:
            continue

        for key, value in metrics[pair].items():
            row[key] = _csv_value(value)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=output_columns,
            lineterminator="\n",
        )

        writer.writeheader()

        writer.writerows(rows)


def _metric_int(
    values: dict[str, object],
    field: str,
) -> int:
    """Read an integer enrichment metric with runtime type narrowing."""
    raw = values[field]

    if isinstance(
        raw,
        bool,
    ):
        raise ValueError(f"{field} cannot be bool")

    if isinstance(
        raw,
        int,
    ):
        return raw

    raise ValueError(f"{field} must be int; got {type(raw).__name__}")


def _metric_float(
    values: dict[str, object],
    field: str,
) -> float:
    """Read a numeric enrichment metric with runtime type narrowing."""
    raw = values[field]

    if isinstance(
        raw,
        bool,
    ):
        raise ValueError(f"{field} cannot be bool")

    if isinstance(
        raw,
        (
            int,
            float,
        ),
    ):
        return float(raw)

    raise ValueError(f"{field} must be numeric; got {type(raw).__name__}")


def enrich_overall_comparison(
    *,
    path: Path,
    metrics: dict[
        tuple[
            str,
            str,
        ],
        dict[str, object],
    ],
) -> None:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        rows = list(reader)

        columns = list(reader.fieldnames or [])

    method_column = _first_existing_column(
        columns,
        (
            "method_id",
            "method",
            "planner",
        ),
    )

    additional = [
        "mean_edge_jaccard_vs_other_methods",
        "mean_expanded_node_count",
        "mean_search_tree_edge_count",
        "mean_rejected_tree_edge_count",
        "mean_search_efficiency_ratio",
    ]

    output_columns = columns + [column for column in additional if column not in columns]

    for row in rows:
        method = row[method_column]

        if method not in HEADLINE_METHODS:
            continue

        city_metrics = [
            metrics[
                (
                    city,
                    method,
                )
            ]
            for city in SHOWCASE_CITIES
        ]

        if not city_metrics:
            raise ValueError(f"no city metrics for {method}")

        jaccard_total = 0.0
        expanded_total = 0
        tree_total = 0
        rejected_total = 0
        efficiency_total = 0.0

        for values in city_metrics:
            jaccard_total += _metric_float(
                values,
                "mean_edge_jaccard_vs_other_methods",
            )

            expanded_total += _metric_int(
                values,
                "expanded_node_count",
            )

            tree_total += _metric_int(
                values,
                "search_tree_edge_count",
            )

            rejected_total += _metric_int(
                values,
                "rejected_tree_edge_count",
            )

            efficiency_total += _metric_float(
                values,
                "search_efficiency_ratio",
            )

        count = len(city_metrics)

        row["mean_edge_jaccard_vs_other_methods"] = _csv_value(jaccard_total / count)

        row["mean_expanded_node_count"] = _csv_value(expanded_total / count)

        row["mean_search_tree_edge_count"] = _csv_value(tree_total / count)

        row["mean_rejected_tree_edge_count"] = _csv_value(rejected_total / count)

        row["mean_search_efficiency_ratio"] = _csv_value(efficiency_total / count)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=output_columns,
            lineterminator="\n",
        )

        writer.writeheader()

        writer.writerows(rows)


def enrich_summary(
    *,
    path: Path,
    metrics: dict[
        tuple[
            str,
            str,
        ],
        dict[str, object],
    ],
) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError("evaluation summary must be mapping")

    payload["revised_step_7r"] = {
        "winner_logic_changed": (False),
        "winner_source": ("canonical evaluation.py"),
        "route_divergence_is_descriptive_only": (True),
        "search_efficiency_is_descriptive_only": (True),
        "method_metrics": {
            (city + "/" + method): values
            for (
                (
                    city,
                    method,
                ),
                values,
            ) in sorted(metrics.items())
        },
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run_enrichment(
    *,
    data_directory: Path,
) -> None:
    routes_path = data_directory / "routes.json"

    traces_path = data_directory / "search_traces.json"

    summary_path = data_directory / "evaluation_summary.json"

    route_comparison_path = data_directory / "route_comparison.csv"

    overall_comparison_path = data_directory / "overall_comparison.csv"

    required = (
        routes_path,
        traces_path,
        summary_path,
        route_comparison_path,
        overall_comparison_path,
    )

    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)

    routes_payload = json.loads(routes_path.read_text(encoding="utf-8"))

    trace_payload = json.loads(traces_path.read_text(encoding="utf-8"))

    if not isinstance(
        routes_payload,
        dict,
    ):
        raise ValueError("routes payload must be mapping")

    if not isinstance(
        trace_payload,
        dict,
    ):
        raise ValueError("trace payload must be mapping")

    metrics = build_method_metrics(
        routes_payload=routes_payload,
        trace_payload=trace_payload,
    )

    enrich_route_comparison(
        path=route_comparison_path,
        metrics=metrics,
    )

    enrich_overall_comparison(
        path=overall_comparison_path,
        metrics=metrics,
    )

    enrich_summary(
        path=summary_path,
        metrics=metrics,
    )
