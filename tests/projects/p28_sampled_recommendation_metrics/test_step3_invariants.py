from __future__ import annotations

import ast
from pathlib import Path

from linkedin_visual_labs.projects.p28_sampled_recommendation_metrics import simulation


def test_simulation_source_never_calls_builtin_hash() -> None:
    path = Path(simulation.__file__)

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    offending = []

    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        if (
            isinstance(
                node.func,
                ast.Name,
            )
            and node.func.id == "hash"
        ):
            offending.append(node.lineno)

    assert offending == []


def test_uncertainty_vocabulary_is_explicit() -> None:
    path = Path(simulation.__file__)

    text = path.read_text(encoding="utf-8")

    assert "standard_deviation" in text
    assert "standard_error" in text
    assert "standard_error =" in text

    assert ("standard_deviation / math.sqrt") in text.replace("\n", " ")


def test_no_seed_search_control_surface_exists() -> None:
    path = Path(simulation.__file__)

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    forbidden_parameter_names = {
        "seed_candidates",
        "seed_search",
        "retry_seed",
        "best_seed",
        "target_seed",
    }

    discovered = set()

    for node in ast.walk(tree):
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        for argument in (
            list(node.args.posonlyargs) + list(node.args.args) + list(node.args.kwonlyargs)
        ):
            discovered.add(argument.arg)

    assert (discovered & forbidden_parameter_names) == set()
