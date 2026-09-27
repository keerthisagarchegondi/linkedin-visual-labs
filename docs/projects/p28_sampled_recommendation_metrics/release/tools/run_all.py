from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np


N = 10000

RANK_PROFILES = {
    "A": [100, 100, 100, 100, 100],
    "B": [40, 40, 8437, 9266, 4482],
    "C": [212, 2, 743, 5342, 1548],
}

M_GRID = [
    1, 2, 5, 10, 20, 50,
    99, 200, 500, 1000, 5000, 9999,
]

SEED = 20260923

MC_REPS = [
    1000,
    10000,
]


def full_metrics_for_rank(r: int) -> dict[str, float]:

    return {
        "AP": 1.0 / r,
        "AUC": (N - r) / (N - 1),
        "NDCG": 1.0 / math.log2(r + 1),
        "Recall@10": 1.0 if r <= 10 else 0.0,
    }


def binomial_expectation(
    r: int,
    m: int,
) -> dict[str, float]:

    p = (
        (r - 1)
        /
        (N - 1)
    )

    if p <= 0.0:

        xs = range(
            1
        )

        probs = [
            1.0
        ]

    elif p >= 1.0:

        xs = [
            m
        ]

        probs = [
            1.0
        ]

    else:

        log_p = math.log(
            p
        )

        log_q = math.log1p(
            -p
        )

        lg_m = math.lgamma(
            m + 1
        )

        xs = range(
            m + 1
        )

        probs = [
            math.exp(
                lg_m
                - math.lgamma(
                    x + 1
                )
                - math.lgamma(
                    m - x + 1
                )
                + x * log_p
                + (m - x) * log_q
            )
            for x in xs
        ]

    total_prob = math.fsum(
        probs
    )

    if not math.isclose(
        total_prob,
        1.0,
        rel_tol=0.0,
        abs_tol=1e-9,
    ):

        probs = [
            prob
            /
            total_prob
            for prob in probs
        ]

    ap = math.fsum(
        prob
        /
        (1 + x)
        for x, prob in zip(
            xs,
            probs,
        )
    )

    ndcg = math.fsum(
        prob
        /
        math.log2(
            x + 2
        )
        for x, prob in zip(
            xs,
            probs,
        )
    )

    recall = math.fsum(
        prob
        for x, prob in zip(
            xs,
            probs,
        )
        if x <= 9
    )

    auc = (
        1.0
        -
        p
    )

    return {
        "AP": ap,
        "AUC": auc,
        "NDCG": ndcg,
        "Recall@10": recall,
    }


def average_metric_dicts(
    rows: list[dict[str, float]],
) -> dict[str, float]:

    keys = rows[
        0
    ].keys()

    return {
        key: math.fsum(
            row[
                key
            ]
            for row in rows
        )
        /
        len(
            rows
        )
        for key in keys
    }


def full_model_results() -> dict:

    return {
        model: average_metric_dicts(
            [
                full_metrics_for_rank(
                    rank
                )
                for rank in ranks
            ]
        )
        for model, ranks in RANK_PROFILES.items()
    }


def sampled_model_results(
    m: int,
) -> dict:

    return {
        model: average_metric_dicts(
            [
                binomial_expectation(
                    rank,
                    m,
                )
                for rank in ranks
            ]
        )
        for model, ranks in RANK_PROFILES.items()
    }


def ordering(
    results: dict,
    metric: str,
    tolerance: float = 1e-12,
) -> str:

    values = {
        model: results[
            model
        ][
            metric
        ]
        for model in (
            "A",
            "B",
            "C",
        )
    }

    groups: list[list[str]] = []

    for model in sorted(
        values,
        key=lambda item: values[
            item
        ],
        reverse=True,
    ):

        if not groups:

            groups.append(
                [
                    model
                ]
            )

            continue

        representative = groups[
            -1
        ][
            0
        ]

        if abs(
            values[
                model
            ]
            -
            values[
                representative
            ]
        ) <= tolerance:

            groups[
                -1
            ].append(
                model
            )

        else:

            groups.append(
                [
                    model
                ]
            )

    return ">".join(
        "=".join(
            sorted(
                group
            )
        )
        for group in groups
    )


def monte_carlo_model_results(
    m: int,
    repetitions: int,
    seed: int,
) -> dict:

    rng = np.random.default_rng(
        seed
    )

    model_outputs = {}

    for model_index, (
        model,
        ranks,
    ) in enumerate(
        RANK_PROFILES.items()
    ):

        metric_accumulator = {
            "AP": [],
            "AUC": [],
            "NDCG": [],
            "Recall@10": [],
        }

        for case_index, rank in enumerate(
            ranks
        ):

            p = (
                (rank - 1)
                /
                (N - 1)
            )

            x = rng.binomial(
                n=m,
                p=p,
                size=repetitions,
            )

            sampled_rank = (
                1
                +
                x
            )

            metric_accumulator[
                "AP"
            ].append(
                1.0
                /
                sampled_rank
            )

            metric_accumulator[
                "AUC"
            ].append(
                1.0
                -
                x
                /
                m
            )

            metric_accumulator[
                "NDCG"
            ].append(
                1.0
                /
                np.log2(
                    sampled_rank
                    +
                    1
                )
            )

            metric_accumulator[
                "Recall@10"
            ].append(
                (
                    sampled_rank
                    <=
                    10
                ).astype(
                    float
                )
            )

        model_outputs[
            model
        ] = {}

        for metric, arrays in metric_accumulator.items():

            per_rep = np.mean(
                np.stack(
                    arrays,
                    axis=0,
                ),
                axis=0,
            )

            model_outputs[
                model
            ][
                metric
            ] = {
                "mean": float(
                    np.mean(
                        per_rep
                    )
                ),
                "se": float(
                    np.std(
                        per_rep,
                        ddof=1,
                    )
                    /
                    math.sqrt(
                        repetitions
                    )
                ),
            }

    return model_outputs


def main() -> int:

    output_path = Path(
        sys.argv[
            1
        ]
    )

    full = full_model_results()

    sampled_99 = sampled_model_results(
        99
    )

    sweep = {}

    for m in M_GRID:

        result = sampled_model_results(
            m
        )

        sweep[
            str(
                m
            )
        ] = {
            "results": result,
            "orderings": {
                metric: ordering(
                    result,
                    metric,
                )
                for metric in (
                    "AP",
                    "AUC",
                    "NDCG",
                    "Recall@10",
                )
            },
        }

    monte_carlo = {}

    analytical_99 = sampled_99

    for repetitions in MC_REPS:

        mc = monte_carlo_model_results(
            m=99,
            repetitions=repetitions,
            seed=(
                SEED
                +
                repetitions
            ),
        )

        checks = []

        for model in (
            "A",
            "B",
            "C",
        ):

            for metric in (
                "AP",
                "AUC",
                "NDCG",
                "Recall@10",
            ):

                mean = mc[
                    model
                ][
                    metric
                ][
                    "mean"
                ]

                se = mc[
                    model
                ][
                    metric
                ][
                    "se"
                ]

                expectation = analytical_99[
                    model
                ][
                    metric
                ]

                tolerance = max(
                    5.0
                    *
                    se,
                    1e-3,
                )

                passed = (
                    abs(
                        mean
                        -
                        expectation
                    )
                    <=
                    tolerance
                )

                checks.append(
                    {
                        "model": model,
                        "metric": metric,
                        "mean": mean,
                        "se": se,
                        "expectation": expectation,
                        "tolerance": tolerance,
                        "pass": passed,
                    }
                )

        monte_carlo[
            str(
                repetitions
            )
        ] = {
            "checks": checks,
            "pass": all(
                check[
                    "pass"
                ]
                for check in checks
            ),
        }

    payload = {
        "catalog_size": N,
        "rank_profiles": RANK_PROFILES,
        "sample_size_grid": M_GRID,
        "seed": SEED,
        "monte_carlo_repetitions": MC_REPS,
        "full": {
            "results": full,
            "orderings": {
                metric: ordering(
                    full,
                    metric,
                )
                for metric in (
                    "AP",
                    "AUC",
                    "NDCG",
                    "Recall@10",
                )
            },
        },
        "sampled_m99": {
            "results": sampled_99,
            "orderings": {
                metric: ordering(
                    sampled_99,
                    metric,
                )
                for metric in (
                    "AP",
                    "AUC",
                    "NDCG",
                    "Recall@10",
                )
            },
        },
        "sweep": sweep,
        "monte_carlo": monte_carlo,
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        +
        "\n",
        encoding="utf-8",
    )

    print(
        output_path
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
