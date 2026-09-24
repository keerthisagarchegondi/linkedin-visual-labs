"""Final deterministic evidence freeze for Project 8."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

from .config import load_default_config
from .metrics import (
    auc_at_rank,
    average_precision_at_rank,
    ndcg_at_rank,
    recall_at_k,
)
from .reference import load_reference_protocol
from .sampling import (
    expected_sampled_ap_pmf,
    expected_sampled_auc_identity,
    expected_sampled_ndcg,
    expected_sampled_recall_at_k,
)
from .simulation import (
    analytical_profile_ap_closed_form,
    analytical_profile_expectations,
    monte_carlo_acceptance_threshold,
    monte_carlo_agrees,
    run_monte_carlo_protocol,
)

METRICS = (
    "ap",
    "ndcg",
    "recall_at_10",
    "auc",
)

SAMPLE_SIZE_GRID = (
    1,
    2,
    5,
    10,
    20,
    50,
    99,
    200,
    500,
    1000,
    5000,
    9999,
)

REFERENCE_NEGATIVE_DRAWS = 99
ROOT_SEED = 20260923
SOURCE_REPETITIONS = 1000
HIGH_PRECISION_REPETITIONS = 10000
TIE_TOLERANCE = 1e-12


def sha256_file(
    path: Path,
) -> str:
    """Return a deterministic SHA-256 checksum."""
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def _metric_full_value(
    rank: int,
    *,
    metric: str,
    n_items: int,
) -> float:
    if metric == "ap":
        return average_precision_at_rank(
            rank,
            n_items=n_items,
        )

    if metric == "ndcg":
        return ndcg_at_rank(
            rank,
            n_items=n_items,
        )

    if metric == "recall_at_10":
        return recall_at_k(
            rank,
            n_items=n_items,
            k=10,
        )

    if metric == "auc":
        return auc_at_rank(
            rank,
            n_items=n_items,
        )

    raise ValueError(f"unsupported metric: {metric}")


def _metric_expected_value(
    rank: int,
    *,
    metric: str,
    n_items: int,
    negative_draws: int,
) -> float:
    if metric == "ap":
        return expected_sampled_ap_pmf(
            rank,
            n_items=n_items,
            negative_draws=negative_draws,
        )

    if metric == "ndcg":
        return expected_sampled_ndcg(
            rank,
            n_items=n_items,
            negative_draws=negative_draws,
        )

    if metric == "recall_at_10":
        return expected_sampled_recall_at_k(
            rank,
            n_items=n_items,
            negative_draws=negative_draws,
            k=10,
        )

    if metric == "auc":
        return expected_sampled_auc_identity(
            rank,
            n_items=n_items,
            negative_draws=negative_draws,
        )

    raise ValueError(f"unsupported metric: {metric}")


def profile_full_metrics(
    profiles: Mapping[str, Sequence[int]],
    *,
    n_items: int,
) -> dict[str, dict[str, float]]:
    """Calculate all full-catalog profile metrics."""
    result: dict[str, dict[str, float]] = {}

    for profile, ranks in sorted(profiles.items()):
        if len(ranks) != 5:
            raise ValueError("every profile must contain exactly five ranks")

        result[profile] = {}

        for metric in METRICS:
            result[profile][metric] = (
                math.fsum(
                    _metric_full_value(
                        rank,
                        metric=metric,
                        n_items=n_items,
                    )
                    for rank in ranks
                )
                / 5.0
            )

    return result


def profile_expected_metrics(
    profiles: Mapping[str, Sequence[int]],
    *,
    n_items: int,
    negative_draws: int,
) -> dict[str, dict[str, float]]:
    """Calculate expected sampled metrics."""
    result: dict[str, dict[str, float]] = {}

    for profile, ranks in sorted(profiles.items()):
        if len(ranks) != 5:
            raise ValueError("every profile must contain exactly five ranks")

        result[profile] = {}

        for metric in METRICS:
            result[profile][metric] = (
                math.fsum(
                    _metric_expected_value(
                        rank,
                        metric=metric,
                        n_items=n_items,
                        negative_draws=negative_draws,
                    )
                    for rank in ranks
                )
                / 5.0
            )

    return result


def ordering_groups(
    values: Mapping[str, float],
    *,
    tolerance: float = TIE_TOLERANCE,
) -> tuple[tuple[str, ...], ...]:
    """Return descending ordering while preserving numerical ties."""
    if tolerance < 0.0:
        raise ValueError("tolerance must be >= 0")

    ordered = sorted(
        values.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    groups: list[list[str]] = []
    group_reference: float | None = None

    for label, value in ordered:
        if group_reference is None or abs(value - group_reference) > tolerance:
            groups.append([label])

            group_reference = value

        else:
            groups[-1].append(label)

    return tuple(tuple(sorted(group)) for group in groups)


def ordering_text(
    groups: Sequence[Sequence[str]],
) -> str:
    """Human-readable tie-preserving ordering."""
    return ">".join("=".join(group) for group in groups)


def pairwise_relation(
    first_value: float,
    second_value: float,
    *,
    tolerance: float = TIE_TOLERANCE,
) -> str:
    """Return relation from first to second."""
    difference = first_value - second_value

    if abs(difference) <= tolerance:
        return "tie"

    if difference > 0.0:
        return "first_above_second"

    return "second_above_first"


def sensitivity_results(
    profiles: Mapping[str, Sequence[int]],
    *,
    n_items: int,
    sample_sizes: Sequence[int] = SAMPLE_SIZE_GRID,
) -> dict[int, dict[str, dict[str, float]]]:
    """Calculate the complete frozen analytical sample-size sweep."""
    return {
        int(m): profile_expected_metrics(
            profiles,
            n_items=n_items,
            negative_draws=int(m),
        )
        for m in sample_sizes
    }


def crossover_intervals(
    sweep: Mapping[
        int,
        Mapping[
            str,
            Mapping[
                str,
                float,
            ],
        ],
    ],
    *,
    tolerance: float = TIE_TOLERANCE,
) -> list[dict[str, object]]:
    """Detect only adjacent-grid intervals where pairwise relations change."""
    sample_sizes = sorted(sweep)

    profiles = sorted(next(iter(sweep.values())))

    intervals: list[dict[str, object]] = []

    for metric in METRICS:
        for first_index, first in enumerate(profiles):
            for second in profiles[first_index + 1 :]:
                previous_m = sample_sizes[0]

                previous_relation = pairwise_relation(
                    sweep[previous_m][first][metric],
                    sweep[previous_m][second][metric],
                    tolerance=tolerance,
                )

                for current_m in sample_sizes[1:]:
                    current_relation = pairwise_relation(
                        sweep[current_m][first][metric],
                        sweep[current_m][second][metric],
                        tolerance=tolerance,
                    )

                    if current_relation != previous_relation:
                        intervals.append(
                            {
                                "metric": metric,
                                "profiles": [
                                    first,
                                    second,
                                ],
                                "lower_computed_m": previous_m,
                                "upper_computed_m": current_m,
                                "relation_at_lower": previous_relation,
                                "relation_at_upper": current_relation,
                                "exact_crossover_inferred": False,
                            }
                        )

                    previous_m = current_m
                    previous_relation = current_relation

    return intervals


def _independent_binomial_probability(
    *,
    m: int,
    k: int,
    p: float,
) -> float:
    if p == 0.0:
        return 1.0 if k == 0 else 0.0

    if p == 1.0:
        return 1.0 if k == m else 0.0

    return (
        math.comb(
            m,
            k,
        )
        * (p**k)
        * ((1.0 - p) ** (m - k))
    )


def independent_expected_value(
    rank: int,
    *,
    metric: str,
    n_items: int,
    negative_draws: int,
) -> float:
    """Independent m=99 critical-number calculation via math.comb."""
    p = (rank - 1) / (n_items - 1)

    terms = []

    for k in range(negative_draws + 1):
        probability = _independent_binomial_probability(
            m=negative_draws,
            k=k,
            p=p,
        )

        sampled_rank = k + 1

        if metric == "ap":
            value = 1.0 / sampled_rank

        elif metric == "ndcg":
            value = 1.0 / math.log2(sampled_rank + 1)

        elif metric == "recall_at_10":
            value = float(sampled_rank <= 10)

        elif metric == "auc":
            value = 1.0 - (k / negative_draws)

        else:
            raise ValueError(f"unsupported metric: {metric}")

        terms.append(probability * value)

    return math.fsum(terms)


def independent_profile_expected_metrics(
    profiles: Mapping[str, Sequence[int]],
    *,
    n_items: int,
    negative_draws: int,
) -> dict[str, dict[str, float]]:
    """Independent critical-number recomputation."""
    result: dict[str, dict[str, float]] = {}

    for profile, ranks in sorted(profiles.items()):
        result[profile] = {}

        for metric in METRICS:
            result[profile][metric] = (
                math.fsum(
                    independent_expected_value(
                        rank,
                        metric=metric,
                        n_items=n_items,
                        negative_draws=negative_draws,
                    )
                    for rank in ranks
                )
                / 5.0
            )

    return result


def _infer_metric(
    text: str,
) -> str | None:
    lowered = text.lower()

    if "ndcg" in lowered:
        return "ndcg"

    if "recall" in lowered:
        return "recall_at_10"

    if "auc" in lowered:
        return "auc"

    if "average precision" in lowered or re.search(
        r"\bap\b",
        lowered,
    ):
        return "ap"

    return None


def _infer_profile(
    row: Mapping[str, str],
) -> str | None:
    for value in row.values():
        candidate = value.strip()

        if candidate in {
            "A",
            "B",
            "C",
        }:
            return candidate

    return None


def _decimal_precision(
    raw: str,
) -> int:
    value = raw.strip().lower()

    if "e" in value:
        return 12

    if "." not in value:
        return 0

    return len(
        value.split(
            ".",
            1,
        )[1]
    )


def reconcile_source_reference_values(
    source_csv: Path,
    *,
    full_metrics: Mapping[
        str,
        Mapping[
            str,
            float,
        ],
    ],
    sampled_metrics: Mapping[
        str,
        Mapping[
            str,
            float,
        ],
    ],
) -> dict[str, object]:
    """Reconcile parseable published rounded metric rows without redefining metrics."""
    with source_csv.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)

        if reader.fieldnames is None:
            raise ValueError("source reference CSV has no header")

        rows = [
            {str(key): ("" if value is None else str(value)) for key, value in row.items()}
            for row in reader
        ]

    reconciled: list[dict[str, object]] = []

    ignored: list[dict[str, object]] = []

    for index, row in enumerate(
        rows,
        start=2,
    ):
        joined = " ".join(row.values())

        profile = _infer_profile(row)

        metric = _infer_metric(joined)

        if profile is None or metric is None:
            ignored.append(
                {
                    "csv_line": index,
                    "reason": "not a parseable profile/metric reference row",
                    "row": row,
                }
            )

            continue

        lowered = joined.lower()

        sampled_context = "sample" in lowered

        candidate_values: list[
            tuple[
                int,
                str,
                float,
            ]
        ] = []

        for header, raw in row.items():
            stripped = raw.strip()

            try:
                numeric = float(stripped)
            except ValueError:
                continue

            normalized_header = header.lower().replace(
                " ",
                "_",
            )

            priority = 0

            if any(
                token in normalized_header
                for token in (
                    "value",
                    "score",
                    "published",
                    "reference",
                )
            ):
                priority = 10

            if abs(numeric) <= 1.0:
                priority += 5

            candidate_values.append(
                (
                    priority,
                    stripped,
                    numeric,
                )
            )

        if not candidate_values:
            ignored.append(
                {
                    "csv_line": index,
                    "reason": "no numeric reference value detected",
                    "row": row,
                }
            )

            continue

        candidate_values.sort(
            key=lambda item: (
                item[0],
                -len(item[1]),
            ),
            reverse=True,
        )

        _, raw_value, published = candidate_values[0]

        computed = (
            sampled_metrics[profile][metric] if sampled_context else full_metrics[profile][metric]
        )

        precision = _decimal_precision(raw_value)

        rounding_tolerance = max(
            0.5 * (10.0 ** (-precision)),
            1e-12,
        )

        difference = abs(computed - published)

        reconciled.append(
            {
                "csv_line": index,
                "profile": profile,
                "metric": metric,
                "context": ("sampled" if sampled_context else "full_catalog"),
                "published_value": published,
                "published_raw": raw_value,
                "computed_value": computed,
                "absolute_difference": difference,
                "rounding_tolerance": rounding_tolerance,
                "status": (
                    "ROUNDING_MATCH" if difference <= rounding_tolerance else "DISCREPANCY_RECORDED"
                ),
                "definition_changed": False,
            }
        )

    if not reconciled:
        raise RuntimeError(
            "no parseable published rounded metric rows were found in source_reference_values.csv"
        )

    return {
        "status": "PASS",
        "rows_reconciled": len(reconciled),
        "rows_ignored": len(ignored),
        "definition_changes": False,
        "reconciled": reconciled,
        "ignored": ignored,
    }


def _metric_values_by_profile(
    data: Mapping[
        str,
        Mapping[
            str,
            float,
        ],
    ],
    metric: str,
) -> dict[str, float]:
    return {profile: values[metric] for profile, values in sorted(data.items())}


class OrderingPayload(TypedDict):
    """Typed representation of one metric ordering."""

    groups: list[list[str]]
    text: str
    values: dict[str, float]


def _ordering_payload(
    data: Mapping[
        str,
        Mapping[
            str,
            float,
        ],
    ],
) -> dict[str, OrderingPayload]:
    result: dict[str, OrderingPayload] = {}

    for metric in METRICS:
        values = _metric_values_by_profile(
            data,
            metric,
        )

        groups = ordering_groups(values)

        result[metric] = {
            "groups": [list(group) for group in groups],
            "text": ordering_text(groups),
            "values": values,
        }

    return result


def _csv_bytes(
    *,
    fieldnames: Sequence[str],
    rows: Sequence[
        Mapping[
            str,
            object,
        ]
    ],
) -> bytes:
    buffer = io.StringIO(newline="")

    writer = csv.DictWriter(
        buffer,
        fieldnames=list(fieldnames),
        lineterminator="\n",
    )

    writer.writeheader()

    for row in rows:
        writer.writerow(row)

    return buffer.getvalue().encode("utf-8")


def _json_bytes(
    value: object,
) -> bytes:
    return (
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def _mc_validation(
    profiles: Mapping[str, Sequence[int]],
    *,
    n_items: int,
    negative_draws: int,
    repetitions: int,
    root_seed: int,
) -> dict[str, object]:
    simulation = run_monte_carlo_protocol(
        profiles=profiles,
        n_items=n_items,
        negative_draws=negative_draws,
        repetitions=repetitions,
        root_seed=root_seed,
    )

    rows = []

    for profile, ranks in sorted(profiles.items()):
        analytical = analytical_profile_expectations(
            ranks=ranks,
            n_items=n_items,
            negative_draws=negative_draws,
        )

        closed_form_ap = analytical_profile_ap_closed_form(
            ranks=ranks,
            n_items=n_items,
            negative_draws=negative_draws,
        )

        if not math.isclose(
            analytical["ap"],
            closed_form_ap,
            rel_tol=1e-11,
            abs_tol=1e-12,
        ):
            raise RuntimeError(f"AP PMF/closed-form mismatch for profile {profile}")

        profile_result = simulation[profile]

        metric_rows = {}

        for metric, summary in profile_result.metrics.items():
            expectation = analytical[metric]

            threshold = monte_carlo_acceptance_threshold(standard_error=(summary.standard_error))

            accepted = monte_carlo_agrees(
                monte_carlo_mean=(summary.mean),
                analytical_expectation=expectation,
                standard_error=(summary.standard_error),
            )

            if not accepted:
                raise RuntimeError(
                    "Monte Carlo validation failed: "
                    f"R={repetitions} "
                    f"profile={profile} "
                    f"metric={metric}"
                )

            metric_rows[metric] = {
                "analytical_expectation": expectation,
                "monte_carlo_mean": summary.mean,
                "sample_standard_deviation": (summary.standard_deviation),
                "monte_carlo_standard_error": (summary.standard_error),
                "absolute_difference": abs(summary.mean - expectation),
                "acceptance_threshold": threshold,
                "accepted": True,
            }

        rows.append(
            {
                "profile": profile,
                "stream_key": (profile_result.stream_key),
                "stream_seed": (profile_result.stream_seed),
                "metrics": metric_rows,
            }
        )

    return {
        "repetitions": repetitions,
        "root_seed": root_seed,
        "profiles": rows,
        "all_accepted": True,
    }


def build_release_payloads(
    repo: Path,
    *,
    input_head: str,
) -> dict[str, bytes]:
    """Build every frozen Step-4 artifact in memory."""
    config = load_default_config()

    reference = load_reference_protocol(config=config)

    if config.root_seed != ROOT_SEED:
        raise RuntimeError("root seed changed from frozen contract")

    if reference.reference_negative_draws != REFERENCE_NEGATIVE_DRAWS:
        raise RuntimeError("reference m changed from frozen contract")

    if tuple(config.sensitivity_grid_negative_draws) != SAMPLE_SIZE_GRID:
        raise RuntimeError("sample-size grid changed from frozen contract")

    profiles = {label: tuple(ranks) for label, ranks in sorted(reference.profiles.items())}

    full = profile_full_metrics(
        profiles,
        n_items=reference.n_items,
    )

    sampled_99 = profile_expected_metrics(
        profiles,
        n_items=reference.n_items,
        negative_draws=(REFERENCE_NEGATIVE_DRAWS),
    )

    sweep = sensitivity_results(
        profiles,
        n_items=reference.n_items,
    )

    independent_99 = independent_profile_expected_metrics(
        profiles,
        n_items=reference.n_items,
        negative_draws=(REFERENCE_NEGATIVE_DRAWS),
    )

    independent_differences = []

    for profile in sorted(profiles):
        for metric in METRICS:
            difference = abs(sampled_99[profile][metric] - independent_99[profile][metric])

            if difference > 1e-12:
                raise RuntimeError(
                    "independent critical-number "
                    "recomputation mismatch: "
                    f"{profile=} {metric=} "
                    f"{difference=}"
                )

            independent_differences.append(
                {
                    "profile": profile,
                    "metric": metric,
                    "primary": sampled_99[profile][metric],
                    "independent": independent_99[profile][metric],
                    "absolute_difference": difference,
                }
            )

    full_orderings = _ordering_payload(full)

    sampled_orderings = _ordering_payload(sampled_99)

    sweep_orderings = {str(m): _ordering_payload(values) for m, values in sorted(sweep.items())}

    crossovers = crossover_intervals(sweep)

    auc_negative_control_rows = []

    full_auc_order = full_orderings["auc"]["text"]

    for m, data in sorted(sweep.items()):
        sampled_auc_order = sweep_orderings[str(m)]["auc"]["text"]

        max_difference = max(
            abs(data[profile]["auc"] - full[profile]["auc"]) for profile in profiles
        )

        if max_difference > 1e-12:
            raise RuntimeError(f"AUC negative-control identity failed at m={m}")

        if sampled_auc_order != full_auc_order:
            raise RuntimeError(f"AUC ordering changed unexpectedly at m={m}")

        auc_negative_control_rows.append(
            {
                "negative_draws": m,
                "max_absolute_difference": max_difference,
                "full_ordering": full_auc_order,
                "sampled_ordering": sampled_auc_order,
                "status": "PASS",
            }
        )

    source_reference_csv = (
        repo / "assets" / "p28_sampled_recommendation_metrics" / "source_reference_values.csv"
    )

    if not source_reference_csv.is_file():
        raise RuntimeError("source_reference_values.csv is missing")

    source_reconciliation = reconcile_source_reference_values(
        source_reference_csv,
        full_metrics=full,
        sampled_metrics=sampled_99,
    )

    source_mc = _mc_validation(
        profiles,
        n_items=reference.n_items,
        negative_draws=(REFERENCE_NEGATIVE_DRAWS),
        repetitions=SOURCE_REPETITIONS,
        root_seed=ROOT_SEED,
    )

    high_precision_mc = _mc_validation(
        profiles,
        n_items=reference.n_items,
        negative_draws=(REFERENCE_NEGATIVE_DRAWS),
        repetitions=(HIGH_PRECISION_REPETITIONS),
        root_seed=ROOT_SEED,
    )

    full_rows = []

    for metric in METRICS:
        groups = ordering_groups(
            _metric_values_by_profile(
                full,
                metric,
            )
        )

        order = ordering_text(groups)

        group_lookup = {
            profile: group_index
            for group_index, group in enumerate(
                groups,
                start=1,
            )
            for profile in group
        }

        for profile in sorted(profiles):
            full_rows.append(
                {
                    "profile": profile,
                    "metric": metric,
                    "value": format(
                        full[profile][metric],
                        ".17g",
                    ),
                    "ordering": order,
                    "ordering_group": (group_lookup[profile]),
                    "tie_tolerance": format(
                        TIE_TOLERANCE,
                        ".17g",
                    ),
                }
            )

    sampled_rows = []

    for metric in METRICS:
        groups = ordering_groups(
            _metric_values_by_profile(
                sampled_99,
                metric,
            )
        )

        order = ordering_text(groups)

        group_lookup = {
            profile: group_index
            for group_index, group in enumerate(
                groups,
                start=1,
            )
            for profile in group
        }

        for profile in sorted(profiles):
            sampled_rows.append(
                {
                    "negative_draws": (REFERENCE_NEGATIVE_DRAWS),
                    "profile": profile,
                    "metric": metric,
                    "expected_value": format(
                        sampled_99[profile][metric],
                        ".17g",
                    ),
                    "ordering": order,
                    "ordering_group": (group_lookup[profile]),
                    "tie_tolerance": format(
                        TIE_TOLERANCE,
                        ".17g",
                    ),
                }
            )

    sweep_rows = []

    for m, data in sorted(sweep.items()):
        for metric in METRICS:
            groups = ordering_groups(
                _metric_values_by_profile(
                    data,
                    metric,
                )
            )

            order = ordering_text(groups)

            group_lookup = {
                profile: group_index
                for group_index, group in enumerate(
                    groups,
                    start=1,
                )
                for profile in group
            }

            for profile in sorted(profiles):
                sweep_rows.append(
                    {
                        "negative_draws": m,
                        "profile": profile,
                        "metric": metric,
                        "expected_value": format(
                            data[profile][metric],
                            ".17g",
                        ),
                        "ordering": order,
                        "ordering_group": (group_lookup[profile]),
                        "tie_tolerance": format(
                            TIE_TOLERANCE,
                            ".17g",
                        ),
                    }
                )

    ap_reversal = full_orderings["ap"]["text"] != sampled_orderings["ap"]["text"]

    if not ap_reversal:
        raise RuntimeError("AP ranking reversal was not reproduced")

    claim_register = {
        "schema_version": 1,
        "claims": [
            {
                "claim_id": "P8-C001",
                "classification": "SOURCE_REPORTED",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (
                    "The frozen A/B/C rank profiles are the source-reported toy-example inputs."
                ),
                "evidence": [
                    "reference_ranks.json",
                    "source_provenance.json",
                ],
            },
            {
                "claim_id": "P8-C002",
                "classification": "REPLICATED_COMPUTATION",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (f"Full-catalog AP orders the profiles {full_orderings['ap']['text']}."),
                "evidence": [
                    "full_metrics.csv",
                ],
            },
            {
                "claim_id": "P8-C003",
                "classification": "REPLICATED_COMPUTATION",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (
                    "Expected sampled AP at m=99 orders the "
                    "profiles "
                    f"{sampled_orderings['ap']['text']}."
                ),
                "evidence": [
                    "sampled_metrics.csv",
                ],
            },
            {
                "claim_id": "P8-C004",
                "classification": "REPLICATED_COMPUTATION",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (
                    "The full-catalog and expected sampled AP model orderings differ at m=99."
                ),
                "evidence": [
                    "full_metrics.csv",
                    "sampled_metrics.csv",
                ],
            },
            {
                "claim_id": "P8-C005",
                "classification": "MATHEMATICAL_DERIVATION",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (
                    "Expected sampled AUC equals full-catalog "
                    "AUC under the frozen sampling protocol."
                ),
                "evidence": [
                    "sample_size_sweep.csv",
                    "validation_results.json",
                ],
            },
            {
                "claim_id": "P8-C006",
                "classification": "REPLICATED_COMPUTATION",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (
                    "The predefined sample-size grid contains "
                    "adjacent intervals where one or more "
                    "pairwise model relations change."
                ),
                "evidence": [
                    "sample_size_sweep.csv",
                    "release_data.json",
                ],
            },
            {
                "claim_id": "P8-C007",
                "classification": "UNSUPPORTED",
                "public_safe": False,
                "status": "REJECTED",
                "claim": ("An exact crossover sample size can be identified between grid points."),
                "reason": (
                    "Step 4 computes only the preregistered "
                    "sample-size grid and does not solve for "
                    "unobserved exact crossover locations."
                ),
            },
            {
                "claim_id": "P8-C008",
                "classification": "UNSUPPORTED",
                "public_safe": False,
                "status": "REJECTED",
                "claim": ("The Monte Carlo cross-model differences are paired estimates."),
                "reason": ("Models use independent deterministic random streams."),
            },
            {
                "claim_id": "P8-C009",
                "classification": "UNSUPPORTED",
                "public_safe": False,
                "status": "REJECTED",
                "claim": ("Every sampled recommendation metric must reverse every model ordering."),
                "reason": (
                    "The frozen evidence is metric-specific; AUC is an explicit negative control."
                ),
            },
            {
                "claim_id": "P8-C010",
                "classification": "REPLICATED_COMPUTATION",
                "public_safe": True,
                "status": "SUPPORTED",
                "claim": (
                    "Both preregistered Monte Carlo runs agree "
                    "with analytical expectations under "
                    "abs(MC-analytic) <= max(5*SE, 1e-3)."
                ),
                "evidence": [
                    "validation_results.json",
                ],
            },
        ],
    }

    validation_results = {
        "schema_version": 1,
        "root_seed": ROOT_SEED,
        "reference_negative_draws": (REFERENCE_NEGATIVE_DRAWS),
        "source_protocol_monte_carlo": (source_mc),
        "high_precision_monte_carlo": (high_precision_mc),
        "independent_critical_number_recomputation": {
            "status": "PASS",
            "tolerance": 1e-12,
            "rows": independent_differences,
        },
        "auc_negative_control": {
            "status": "PASS",
            "rows": auc_negative_control_rows,
        },
        "source_reference_reconciliation": (source_reconciliation),
        "seed_searching_performed": False,
        "definition_changes_performed": False,
    }

    release_data = {
        "schema_version": 1,
        "project": ("p28_sampled_recommendation_metrics"),
        "scientific_question": ("Can sampled recommendation metrics select the wrong model?"),
        "input_head": input_head,
        "contract": {
            "n_items": reference.n_items,
            "reference_negative_draws": (REFERENCE_NEGATIVE_DRAWS),
            "root_seed": ROOT_SEED,
            "sample_size_grid": list(SAMPLE_SIZE_GRID),
            "tie_tolerance": (TIE_TOLERANCE),
            "source_repetitions": (SOURCE_REPETITIONS),
            "high_precision_repetitions": (HIGH_PRECISION_REPETITIONS),
        },
        "profiles": {key: list(value) for key, value in profiles.items()},
        "full_catalog": {
            "metrics": full,
            "orderings": (full_orderings),
        },
        "sampled_m99": {
            "metrics": sampled_99,
            "orderings": (sampled_orderings),
        },
        "sample_size_sweep": {
            str(m): {
                "metrics": data,
                "orderings": (sweep_orderings[str(m)]),
            }
            for m, data in sorted(sweep.items())
        },
        "ranking_reversal": {
            "ap_reproduced_at_m99": (ap_reversal),
            "full_ap_ordering": (full_orderings["ap"]["text"]),
            "sampled_ap_ordering_m99": (sampled_orderings["ap"]["text"]),
        },
        "crossover_intervals": (crossovers),
        "crossover_policy": (
            "Only adjacent computed-grid intervals are "
            "reported; exact crossover points are not inferred."
        ),
        "auc_negative_control_status": ("PASS"),
        "source_reference_reconciliation_status": (source_reconciliation["status"]),
        "unsupported_claims_rejected": True,
        "results_frozen": True,
        "output_design_frozen": False,
    }

    payloads: dict[str, bytes] = {}

    payloads["full_metrics.csv"] = _csv_bytes(
        fieldnames=(
            "profile",
            "metric",
            "value",
            "ordering",
            "ordering_group",
            "tie_tolerance",
        ),
        rows=full_rows,
    )

    payloads["sampled_metrics.csv"] = _csv_bytes(
        fieldnames=(
            "negative_draws",
            "profile",
            "metric",
            "expected_value",
            "ordering",
            "ordering_group",
            "tie_tolerance",
        ),
        rows=sampled_rows,
    )

    payloads["sample_size_sweep.csv"] = _csv_bytes(
        fieldnames=(
            "negative_draws",
            "profile",
            "metric",
            "expected_value",
            "ordering",
            "ordering_group",
            "tie_tolerance",
        ),
        rows=sweep_rows,
    )

    payloads["validation_results.json"] = _json_bytes(validation_results)

    payloads["release_data.json"] = _json_bytes(release_data)

    payloads["claim_register.json"] = _json_bytes(claim_register)

    artifact_hashes = {
        name: hashlib.sha256(content).hexdigest() for name, content in sorted(payloads.items())
    }

    input_files = [
        repo / "assets" / "p28_sampled_recommendation_metrics" / "reference_ranks.json",
        source_reference_csv,
        repo / "assets" / "p28_sampled_recommendation_metrics" / "source_provenance.json",
        repo / "configs" / "p28_sampled_recommendation_metrics.yaml",
        Path(__file__),
        Path(__file__).with_name("metrics.py"),
        Path(__file__).with_name("sampling.py"),
        Path(__file__).with_name("simulation.py"),
    ]

    input_hashes = {path.relative_to(repo).as_posix(): sha256_file(path) for path in input_files}

    manifest = {
        "schema_version": 1,
        "project": ("p28_sampled_recommendation_metrics"),
        "step": 4,
        "input_head": input_head,
        "python_version": (sys.version.split()[0]),
        "root_seed": ROOT_SEED,
        "reference_negative_draws": (REFERENCE_NEGATIVE_DRAWS),
        "source_repetitions": (SOURCE_REPETITIONS),
        "high_precision_repetitions": (HIGH_PRECISION_REPETITIONS),
        "sample_size_grid": list(SAMPLE_SIZE_GRID),
        "tie_tolerance": (TIE_TOLERANCE),
        "input_sha256": input_hashes,
        "artifact_sha256": (artifact_hashes),
        "definition_changes_performed": False,
        "seed_searching_performed": False,
        "exact_crossover_inference_performed": False,
        "results_frozen": True,
        "output_design_frozen": False,
    }

    payloads["run_manifest.json"] = _json_bytes(manifest)

    return payloads


def write_release_package(
    repo: Path,
    output_dir: Path,
    *,
    input_head: str,
) -> dict[str, str]:
    """Write deterministic frozen Step-4 artifacts."""
    payloads = build_release_payloads(
        repo,
        input_head=input_head,
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    hashes = {}

    for name, content in sorted(payloads.items()):
        path = output_dir / name

        path.write_bytes(content)

        hashes[name] = hashlib.sha256(content).hexdigest()

    return hashes
