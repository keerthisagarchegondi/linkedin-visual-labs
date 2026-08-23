"""Regression tests for Project 2 Revised Step 7R."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape.evaluation_enrichment import (
    HEADLINE_METHODS,
    SHOWCASE_CITIES,
    _edge_jaccard,
    _route_separation,
    build_method_metrics,
)

DATA = Path("outputs/p04_zombie_escape/data")


def _payload(
    filename: str,
) -> dict[str, object]:
    value = json.loads((DATA / filename).read_text(encoding="utf-8"))

    assert isinstance(
        value,
        dict,
    )

    return value


def test_jaccard_identical_path_is_one() -> None:
    path = (
        (
            0,
            0,
        ),
        (
            0,
            1,
        ),
        (
            0,
            2,
        ),
    )

    assert (
        _edge_jaccard(
            path,
            path,
        )
        == 1.0
    )


def test_jaccard_disjoint_edges_is_zero() -> None:
    left = (
        (
            0,
            0,
        ),
        (
            0,
            1,
        ),
    )

    right = (
        (
            1,
            0,
        ),
        (
            1,
            1,
        ),
    )

    assert (
        _edge_jaccard(
            left,
            right,
        )
        == 0.0
    )


def test_route_separation_identical_is_zero() -> None:
    path = (
        (
            0,
            0,
        ),
        (
            0,
            1,
        ),
        (
            0,
            2,
        ),
    )

    assert (
        _route_separation(
            path,
            path,
        )
        == 0
    )


def test_current_showcase_has_nine_method_metrics() -> None:
    metrics = build_method_metrics(
        routes_payload=_payload("routes.json"),
        trace_payload=_payload("search_traces.json"),
    )

    expected = {
        (
            city,
            method,
        )
        for city in SHOWCASE_CITIES
        for method in HEADLINE_METHODS
    }

    assert set(metrics) == expected


def test_current_search_efficiency_is_valid() -> None:
    metrics = build_method_metrics(
        routes_payload=_payload("routes.json"),
        trace_payload=_payload("search_traces.json"),
    )

    for values in metrics.values():
        raw_efficiency = values["search_efficiency_ratio"]

        raw_expanded = values["expanded_node_count"]

        raw_final_edges = values["final_route_edge_count"]

        assert isinstance(
            raw_efficiency,
            (
                int,
                float,
            ),
        )

        assert not isinstance(
            raw_efficiency,
            bool,
        )

        assert isinstance(
            raw_expanded,
            int,
        )

        assert not isinstance(
            raw_expanded,
            bool,
        )

        assert isinstance(
            raw_final_edges,
            int,
        )

        assert not isinstance(
            raw_final_edges,
            bool,
        )

        efficiency = float(raw_efficiency)

        assert 0.0 < efficiency <= 1.0

        assert raw_expanded > 0

        assert raw_final_edges > 0


def test_current_routes_are_not_identical() -> None:
    metrics = build_method_metrics(
        routes_payload=_payload("routes.json"),
        trace_payload=_payload("search_traces.json"),
    )

    for values in metrics.values():
        raw_jaccard = values["mean_edge_jaccard_vs_other_methods"]

        assert isinstance(
            raw_jaccard,
            (
                int,
                float,
            ),
        )

        assert not isinstance(
            raw_jaccard,
            bool,
        )

        assert float(raw_jaccard) < 1.0


def test_route_comparison_contains_step7r_fields() -> None:
    with (DATA / "route_comparison.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        columns = set(reader.fieldnames or [])

    assert {
        "mean_edge_jaccard_vs_other_methods",
        "expanded_node_count",
        "rejected_tree_edge_count",
        "final_route_edge_count",
        "search_efficiency_ratio",
    } <= columns


def test_overall_comparison_contains_step7r_fields() -> None:
    with (DATA / "overall_comparison.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        columns = set(reader.fieldnames or [])

    assert {
        "mean_edge_jaccard_vs_other_methods",
        "mean_expanded_node_count",
        "mean_search_tree_edge_count",
        "mean_rejected_tree_edge_count",
        "mean_search_efficiency_ratio",
    } <= columns


def test_summary_declares_enrichment_descriptive_only() -> None:
    summary = _payload("evaluation_summary.json")

    revised = summary["revised_step_7r"]

    assert isinstance(
        revised,
        dict,
    )

    assert revised["winner_logic_changed"] is False

    assert revised["route_divergence_is_descriptive_only"] is True

    assert revised["search_efficiency_is_descriptive_only"] is True
