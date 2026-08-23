"""Project-2 Step-10R real search-trace regression tests."""

from __future__ import annotations

from pathlib import Path

from linkedin_visual_labs.projects.p04_zombie_escape.search_trace import (
    METHOD_ALGORITHMS,
    RISK_SOURCES,
    SearchTraceBundle,
    build_search_traces,
    deterministic_trace_digest,
    trace_payload,
    validate_trace_bundle,
)
from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    CITY_ORDER,
    METHOD_ORDER,
    load_visual_payloads,
)


def _payloads() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    return load_visual_payloads(Path("outputs/p04_zombie_escape/data"))


def _bundle() -> SearchTraceBundle:
    (
        cities,
        predictions,
        routes,
        _evaluation,
    ) = _payloads()

    return build_search_traces(
        cities_payload=cities,
        predictions_payload=predictions,
        routes_payload=routes,
    )


def test_dijkstra_trace_contract() -> None:
    assert METHOD_ALGORITHMS["dijkstra"] == "dijkstra"

    assert RISK_SOURCES["dijkstra"] == "observed_risk"


def test_ml_trace_contract() -> None:
    assert METHOD_ALGORITHMS["ml"] == "astar"

    assert RISK_SOURCES["ml"] == "ml_predicted_risk"


def test_dl_trace_contract() -> None:
    assert METHOD_ALGORITHMS["dl"] == "astar"

    assert RISK_SOURCES["dl"] == "dl_predicted_risk"


def test_bundle_has_exactly_nine_traces() -> None:
    bundle = _bundle()

    assert len(bundle.traces) == (len(CITY_ORDER) * len(METHOD_ORDER))


def test_every_trace_matches_canonical_route() -> None:
    bundle = _bundle()

    for trace in bundle.traces:
        assert trace.canonical_route_match is True


def test_every_trace_starts_and_ends_correctly() -> None:
    bundle = _bundle()

    for trace in bundle.traces:
        assert trace.expansions[0].position == trace.start

        assert trace.expansions[-1].position == trace.destination

        assert trace.final_path[0] == trace.start

        assert trace.final_path[-1] == trace.destination


def test_every_final_route_edge_is_in_search_tree() -> None:
    bundle = _bundle()

    for trace in bundle.traces:
        tree_edges = {
            (
                edge.parent,
                edge.child,
            )
            for edge in trace.tree_edges
        }

        final_edges = {
            (
                trace.final_path[index],
                trace.final_path[index + 1],
            )
            for index in range(len(trace.final_path) - 1)
        }

        assert final_edges <= tree_edges


def test_non_final_tree_edges_are_rejected() -> None:
    bundle = _bundle()

    for trace in bundle.traces:
        final_edges = {
            (
                trace.final_path[index],
                trace.final_path[index + 1],
            )
            for index in range(len(trace.final_path) - 1)
        }

        for edge in trace.tree_edges:
            key = (
                edge.parent,
                edge.child,
            )

            if key in final_edges:
                assert edge.classification == "final_route"

            else:
                assert edge.classification == "explored_rejected"


def test_blocked_edges_have_blocked_classification() -> None:
    bundle = _bundle()

    for trace in bundle.traces:
        for edge in trace.blocked_edges:
            assert edge.classification == "blocked"


def test_trace_bundle_is_valid() -> None:
    (
        cities,
        predictions,
        routes,
        _evaluation,
    ) = _payloads()

    bundle = build_search_traces(
        cities_payload=cities,
        predictions_payload=predictions,
        routes_payload=routes,
    )

    validate_trace_bundle(
        bundle,
        cities_payload=cities,
    )


def test_trace_generation_is_deterministic() -> None:
    first = _bundle()
    second = _bundle()

    assert first == second

    assert deterministic_trace_digest(first) == deterministic_trace_digest(second)


def test_serialized_contract_contains_four_animation_classes() -> None:
    payload = trace_payload(
        SearchTraceBundle(
            schema_version=1,
            traces=(),
        )
    )

    raw_contract = payload["classification_contract"]

    assert isinstance(
        raw_contract,
        dict,
    )

    classes = {str(key) for key in raw_contract}

    assert classes == {
        "explored_active",
        "explored_rejected",
        "final_route",
        "blocked",
    }
