"""Deterministic showcase-seed search for Project 2 Step 3R."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Final

import yaml

from linkedin_visual_labs.projects.p04_zombie_escape.showcase_divergence import (
    BENCHMARK_SEED,
    CANDIDATE_SHOWCASE_SEEDS,
    DL_SEED,
    ML_SEED,
    ORIGINAL_SHOWCASE_SEEDS,
    SHOWCASE_CITY_ORDER,
    TRAINING_SEED,
    VALIDATION_SEED,
    ShowcaseDivergenceSummary,
    divergence_payload,
    evaluate_showcase_divergence,
    search_contract_payload,
)
from linkedin_visual_labs.projects.p04_zombie_escape.visualization import (
    load_visual_payloads,
)

REPOSITORY_ROOT: Final[Path] = Path(__file__).resolve().parents[4]

CONFIG_PATH: Final[Path] = REPOSITORY_ROOT / "configs" / "p04_zombie_escape.yaml"

DATA_DIRECTORY: Final[Path] = REPOSITORY_ROOT / "outputs" / "p04_zombie_escape" / "data"

CONTRACT_PATH: Final[Path] = (
    REPOSITORY_ROOT / "configs" / "p04_zombie_escape_showcase_contract.json"
)


IMMUTABLE_SEEDS: Final[frozenset[int]] = frozenset(
    {
        TRAINING_SEED,
        VALIDATION_SEED,
        BENCHMARK_SEED,
        ML_SEED,
        DL_SEED,
    }
)


def _load_yaml(
    path: Path,
) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _write_yaml(
    path: Path,
    payload: object,
) -> None:
    path.write_text(
        yaml.safe_dump(
            payload,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _count_integer(
    value: object,
    target: int,
) -> int:
    if isinstance(
        value,
        bool,
    ):
        return 0

    if isinstance(
        value,
        int,
    ):
        return int(value == target)

    if isinstance(
        value,
        dict,
    ):
        return sum(
            _count_integer(
                child,
                target,
            )
            for child in value.values()
        )

    if isinstance(
        value,
        list,
    ):
        return sum(
            _count_integer(
                child,
                target,
            )
            for child in value
        )

    return 0


def _replace_integer(
    value: object,
    *,
    old: int,
    new: int,
) -> object:
    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        int,
    ):
        return new if value == old else value

    if isinstance(
        value,
        dict,
    ):
        return {
            key: _replace_integer(
                child,
                old=old,
                new=new,
            )
            for (
                key,
                child,
            ) in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            _replace_integer(
                child,
                old=old,
                new=new,
            )
            for child in value
        ]

    return value


def _immutable_seed_counts(
    payload: object,
) -> dict[int, int]:
    return {
        seed: _count_integer(
            payload,
            seed,
        )
        for seed in IMMUTABLE_SEEDS
    }


def _locate_original_showcase_seeds(
    payload: object,
) -> None:
    for (
        city_id,
        seed,
    ) in ORIGINAL_SHOWCASE_SEEDS.items():
        count = _count_integer(
            payload,
            seed,
        )

        if count != 1:
            raise RuntimeError(
                f"{city_id}: expected original showcase seed {seed} exactly once; found {count}"
            )


def _candidate_config(
    original: object,
    *,
    seeds: dict[str, int],
) -> object:
    candidate = deepcopy(original)

    for city_id in SHOWCASE_CITY_ORDER:
        candidate = _replace_integer(
            candidate,
            old=ORIGINAL_SHOWCASE_SEEDS[city_id],
            new=seeds[city_id],
        )

    return candidate


def _run(
    *arguments: str,
) -> None:
    environment = dict(os.environ)

    environment["PYTHONHASHSEED"] = "0"

    environment["OMP_NUM_THREADS"] = "1"

    environment["MKL_NUM_THREADS"] = "1"

    command = (
        sys.executable,
        "-m",
        "linkedin_visual_labs",
        "zombie",
        *arguments,
    )

    print()
    print(
        "$",
        " ".join(command),
        flush=True,
    )

    subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
    )


def _run_pipeline() -> None:
    """
    Run the existing Project-2 implementation.

    No showcase-only routing implementation is permitted here.
    """
    _run("generate-cities")

    _run("train-ml")

    _run("train-dl")

    _run("solve-routes")

    _run("evaluate")


def _evaluate_current_outputs() -> ShowcaseDivergenceSummary:
    (
        _cities,
        _predictions,
        routes,
        _evaluation,
    ) = load_visual_payloads(DATA_DIRECTORY)

    return evaluate_showcase_divergence(routes)


def _manifest(
    *,
    selected_index: int,
    selected_seeds: dict[str, int],
    attempts: list[dict[str, object]],
    summary: ShowcaseDivergenceSummary,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "step": "3R",
        "selection_policy": ("first_acceptable_candidate"),
        "candidate_order_was_frozen_before_search": True,
        "selected_candidate_index": (selected_index),
        "accepted_showcase_seeds": dict(selected_seeds),
        "immutable_seeds": {
            "training": TRAINING_SEED,
            "validation": VALIDATION_SEED,
            "benchmark": BENCHMARK_SEED,
            "ml": ML_SEED,
            "dl": DL_SEED,
        },
        "showcase_is_not_benchmark": True,
        "search_contract": (search_contract_payload()),
        "attempts": attempts,
        "accepted_divergence": (divergence_payload(summary)),
    }


def search(
    *,
    maximum_candidates: int | None,
) -> int:
    original_text = CONFIG_PATH.read_text(encoding="utf-8")

    original = _load_yaml(CONFIG_PATH)

    _locate_original_showcase_seeds(original)

    immutable_before = _immutable_seed_counts(original)

    candidates = (
        CANDIDATE_SHOWCASE_SEEDS
        if maximum_candidates is None
        else CANDIDATE_SHOWCASE_SEEDS[:maximum_candidates]
    )

    attempts: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="p04_step3r_") as temporary:
        backup_root = Path(temporary)

        data_backup = backup_root / "data"

        if DATA_DIRECTORY.exists():
            shutil.copytree(
                DATA_DIRECTORY,
                data_backup,
            )

        try:
            for (
                candidate_index,
                triple,
            ) in enumerate(candidates):
                seeds = {
                    "new_york": triple[0],
                    "chicago": triple[1],
                    "phoenix": triple[2],
                }

                print()
                print("=" * 72)

                print(
                    "STEP 3R CANDIDATE",
                    candidate_index,
                    seeds,
                )

                print(
                    "=" * 72,
                    flush=True,
                )

                candidate = _candidate_config(
                    original,
                    seeds=seeds,
                )

                if _immutable_seed_counts(candidate) != immutable_before:
                    raise RuntimeError("immutable training/benchmark seed contract changed")

                _write_yaml(
                    CONFIG_PATH,
                    candidate,
                )

                _run_pipeline()

                summary = _evaluate_current_outputs()

                attempt = {
                    "candidate_index": (candidate_index),
                    "seeds": seeds,
                    "accepted": (summary.accepted),
                    "divergence": (divergence_payload(summary)),
                }

                attempts.append(attempt)

                print()
                print(
                    "CANDIDATE RESULT:",
                    ("ACCEPT" if summary.accepted else "REJECT"),
                )

                for city in summary.cities:
                    print(
                        f"  {city.city_id:<10} "
                        f"unique="
                        f"{city.exact_unique_route_count} "
                        f"mean_jaccard="
                        f"{city.mean_edge_jaccard:.4f} "
                        f"visible_pairs="
                        f"{city.visibly_divergent_pair_count} "
                        f"max_sep="
                        f"{city.maximum_route_separation} "
                        f"accepted="
                        f"{city.accepted}"
                    )

                if not summary.accepted:
                    continue

                # ----------------------------------------------------------
                # First acceptable candidate wins.
                # ----------------------------------------------------------

                manifest = _manifest(
                    selected_index=(candidate_index),
                    selected_seeds=seeds,
                    attempts=attempts,
                    summary=summary,
                )

                CONTRACT_PATH.write_text(
                    json.dumps(
                        manifest,
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                print()
                print("PROJECT 2 — STEP 3R SEARCH: PASS")

                print(
                    "FIRST ACCEPTABLE CANDIDATE:",
                    candidate_index,
                )

                print(
                    "ACCEPTED SEEDS:",
                    seeds,
                )

                print(
                    "MANIFEST:",
                    CONTRACT_PATH,
                )

                return 0

        except BaseException:
            CONFIG_PATH.write_text(
                original_text,
                encoding="utf-8",
            )

            if data_backup.exists():
                if DATA_DIRECTORY.exists():
                    shutil.rmtree(DATA_DIRECTORY)

                shutil.copytree(
                    data_backup,
                    DATA_DIRECTORY,
                )

            raise

        # No candidate passed.
        CONFIG_PATH.write_text(
            original_text,
            encoding="utf-8",
        )

        if data_backup.exists():
            if DATA_DIRECTORY.exists():
                shutil.rmtree(DATA_DIRECTORY)

            shutil.copytree(
                data_backup,
                DATA_DIRECTORY,
            )

        print()
        print("PROJECT 2 — STEP 3R SEARCH: NO ACCEPTABLE CANDIDATE")

        return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically search frozen showcase seeds for visible planner-route divergence."
        )
    )

    parser.add_argument(
        "--maximum-candidates",
        type=int,
        default=None,
    )

    arguments = parser.parse_args()

    return search(maximum_candidates=(arguments.maximum_candidates))


if __name__ == "__main__":
    raise SystemExit(main())
