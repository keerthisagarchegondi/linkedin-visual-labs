from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

PROFILE_ORDER = ("A", "B", "C")
METRIC_LABELS = {
    "ap": "Average Precision (AP)",
    "ndcg": "NDCG",
    "recall_at_10": "Recall@10",
    "auc": "AUC",
}

FIGURE_FILES = (
    "figure_1_ap_reversal.png",
    "figure_1_ap_reversal.svg",
    "figure_2_sample_size_sensitivity.png",
    "figure_2_sample_size_sensitivity.svg",
    "figure_3_negative_control_validation.png",
    "figure_3_negative_control_validation.svg",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected object at {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_inputs(
    release: dict[str, Any],
    validation: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    if release.get("results_frozen") is not True:
        raise RuntimeError("Step-4 results are not frozen.")

    if release.get("output_design_frozen") is not False:
        # Step-4 release package itself remains an immutable historical
        # record of its Step-4 state.
        raise RuntimeError("Unexpected mutation of Step-4 release_data.json.")

    if contract.get("status") != "FROZEN":
        raise RuntimeError("Step-5 output contract is not frozen.")

    if contract.get("results_frozen") is not True:
        raise RuntimeError("Step-5 contract does not preserve results freeze.")

    if contract.get("output_design_frozen") is not True:
        raise RuntimeError("Step-5 output design is not frozen.")

    figures = contract.get("static_figures")
    if not isinstance(figures, dict):
        raise RuntimeError("static_figures contract missing.")

    if figures.get("count") != 3:
        raise RuntimeError("Step-5 contract no longer requires exactly 3 figures.")

    rules = contract.get("implementation_rules")
    if not isinstance(rules, list):
        raise RuntimeError("implementation_rules missing.")

    if not any("Preview images must not be used as backgrounds" in str(rule) for rule in rules):
        raise RuntimeError("Preview-reference-only rule missing.")

    if release["ranking_reversal"]["ap_reproduced_at_m99"] is not True:
        raise RuntimeError("Frozen AP reversal is not present.")

    if validation["auc_negative_control"]["status"] != "PASS":
        raise RuntimeError("AUC negative control is not PASS.")

    if validation["high_precision_monte_carlo"]["all_accepted"] is not True:
        raise RuntimeError("High-precision MC validation is not PASS.")


def load_inputs(
    repo: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    frozen = repo / "assets" / "p28_sampled_recommendation_metrics" / "frozen"

    docs = repo / "docs" / "projects" / "p28_sampled_recommendation_metrics"

    release = _read_json(frozen / "release_data.json")
    validation = _read_json(frozen / "validation_results.json")
    contract = _read_json(docs / "OUTPUT_DESIGN_CONTRACT.json")

    _validate_inputs(
        release,
        validation,
        contract,
    )

    return (
        release,
        validation,
        contract,
    )


def profile_colors(
    contract: dict[str, Any],
) -> dict[str, str]:
    design = contract["dashboard"]["design_system"]

    colors = {
        "A": str(design["profile_A"]),
        "B": str(design["profile_B"]),
        "C": str(design["profile_C"]),
    }

    return colors


def figure_payloads(
    release: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    grid = [int(value) for value in release["contract"]["sample_size_grid"]]

    full = release["full_catalog"]

    sampled = release["sampled_m99"]

    sweep = release["sample_size_sweep"]

    sensitivity: dict[str, dict[str, list[float]]] = {}

    for metric in (
        "ap",
        "ndcg",
        "recall_at_10",
        "auc",
    ):
        sensitivity[metric] = {
            profile: [float(sweep[str(m)]["metrics"][profile][metric]) for m in grid]
            for profile in PROFILE_ORDER
        }

    high_precision = validation["high_precision_monte_carlo"]["profiles"]

    mc_rows: list[dict[str, Any]] = []

    for profile_payload in high_precision:
        profile = str(profile_payload["profile"])

        metric_payloads = profile_payload["metrics"]

        for metric in (
            "ap",
            "ndcg",
            "recall_at_10",
            "auc",
        ):
            entry = metric_payloads[metric]

            mc_rows.append(
                {
                    "profile": profile,
                    "metric": metric,
                    "analytical": float(entry["analytical_expectation"]),
                    "monte_carlo": float(entry["monte_carlo_mean"]),
                    "se": float(entry["monte_carlo_standard_error"]),
                    "accepted": bool(entry["accepted"]),
                }
            )

    return {
        "figure_1": {
            "full_ap": {
                profile: float(full["metrics"][profile]["ap"]) for profile in PROFILE_ORDER
            },
            "sampled_ap_m99": {
                profile: float(sampled["metrics"][profile]["ap"]) for profile in PROFILE_ORDER
            },
            "full_ordering": str(full["orderings"]["ap"]["text"]),
            "sampled_ordering": str(sampled["orderings"]["ap"]["text"]),
        },
        "figure_2": {
            "grid": grid,
            "metrics": {
                metric: sensitivity[metric]
                for metric in (
                    "ap",
                    "ndcg",
                    "recall_at_10",
                )
            },
            "crossover_intervals": [
                interval
                for interval in release["crossover_intervals"]
                if interval["metric"]
                in {
                    "ap",
                    "ndcg",
                    "recall_at_10",
                }
            ],
        },
        "figure_3": {
            "grid": grid,
            "auc": sensitivity["auc"],
            "full_auc": {
                profile: float(full["metrics"][profile]["auc"]) for profile in PROFILE_ORDER
            },
            "full_auc_ordering": str(full["orderings"]["auc"]["text"]),
            "sampled_auc_ordering": str(sampled["orderings"]["auc"]["text"]),
            "high_precision_mc": mc_rows,
            "source_mc_all_accepted": bool(
                validation["source_protocol_monte_carlo"]["all_accepted"]
            ),
            "high_precision_all_accepted": bool(
                validation["high_precision_monte_carlo"]["all_accepted"]
            ),
        },
    }


def _apply_common_style(
    ax: Axes,
) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.grid(
        axis="y",
        alpha=0.18,
        linewidth=0.8,
    )

    ax.set_axisbelow(True)


def _save(
    fig: Figure,
    output_base: Path,
) -> None:
    png_path = output_base.with_suffix(".png")

    svg_path = output_base.with_suffix(".svg")

    fig.savefig(
        png_path,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )

    fig.savefig(
        svg_path,
        bbox_inches="tight",
        facecolor="white",
    )

    # SVG_WHITESPACE_NORMALIZATION_V1
    #
    # Matplotlib can emit horizontal whitespace immediately before
    # newlines in generated SVG path data. It is visually inert but
    # fails Git's whitespace gate. Normalize only those line endings.
    svg_text = svg_path.read_text(encoding="utf-8")

    normalized_svg = "\n".join(line.rstrip(" \t") for line in svg_text.splitlines()) + "\n"

    svg_path.write_text(
        normalized_svg,
        encoding="utf-8",
        newline="\n",
    )

    plt.close(fig)


def render_figure_1(
    payload: dict[str, Any],
    colors: dict[str, str],
    output_dir: Path,
) -> None:
    full = payload["full_ap"]
    sampled = payload["sampled_ap_m99"]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(12, 6.8),
        constrained_layout=True,
    )

    fig.suptitle(
        "Sampling can reverse the AP model ordering",
        fontsize=19,
        fontweight="bold",
    )

    fig.text(
        0.5,
        0.955,
        ("Same frozen rank profiles; only the evaluation candidate set changes."),
        ha="center",
        va="top",
        fontsize=11,
    )

    panels = (
        (
            axes[0],
            full,
            "Full-catalog AP",
            payload["full_ordering"],
        ),
        (
            axes[1],
            sampled,
            "Expected sampled AP (m = 99)",
            payload["sampled_ordering"],
        ),
    )

    for (
        ax,
        values,
        title,
        ordering,
    ) in panels:
        sorted_profiles = sorted(
            PROFILE_ORDER,
            key=lambda profile: (
                values[profile],
                profile,
            ),
        )

        y_positions = list(range(len(sorted_profiles)))

        for y, profile in zip(
            y_positions,
            sorted_profiles,
            strict=True,
        ):
            value = values[profile]

            ax.hlines(
                y,
                0.0,
                value,
                color=colors[profile],
                alpha=0.30,
                linewidth=3,
            )

            ax.scatter(
                [value],
                [y],
                s=150,
                color=colors[profile],
                edgecolor="white",
                linewidth=1.2,
                zorder=3,
            )

            ax.text(
                value,
                y + 0.14,
                f"{profile}  {value:.5f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        ax.set_yticks(
            y_positions,
            labels=sorted_profiles,
        )

        ax.set_xlabel("Average Precision (higher is better)")

        ax.set_title(
            f"{title}\nOrdering: {ordering}",
            fontsize=13,
            fontweight="bold",
        )

        ax.set_xlim(left=0.0)

        _apply_common_style(ax)

    fig.text(
        0.5,
        0.025,
        (
            f"Full catalog: {payload['full_ordering']}    "
            f"→    Sampled m=99: {payload['sampled_ordering']}"
        ),
        ha="center",
        fontsize=13,
        fontweight="bold",
    )

    _save(
        fig,
        output_dir / "figure_1_ap_reversal",
    )


def render_figure_2(
    payload: dict[str, Any],
    colors: dict[str, str],
    output_dir: Path,
) -> None:
    grid = payload["grid"]

    metrics = payload["metrics"]

    intervals = payload["crossover_intervals"]

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(12, 12),
        constrained_layout=True,
    )

    fig.suptitle(
        "Sample-size sensitivity of expected sampled metrics",
        fontsize=19,
        fontweight="bold",
    )

    fig.text(
        0.5,
        0.965,
        (
            "Markers are computed frozen m values. "
            "Shaded bands indicate only adjacent-grid relation-change intervals."
        ),
        ha="center",
        va="top",
        fontsize=10.5,
    )

    metric_order = (
        "ap",
        "ndcg",
        "recall_at_10",
    )

    for ax, metric in zip(
        axes,
        metric_order,
        strict=True,
    ):
        for profile in PROFILE_ORDER:
            ax.plot(
                grid,
                metrics[metric][profile],
                marker="o",
                markersize=5,
                linewidth=2.0,
                color=colors[profile],
                label=profile,
            )

        metric_intervals = {
            (
                int(interval["lower_computed_m"]),
                int(interval["upper_computed_m"]),
            )
            for interval in intervals
            if interval["metric"] == metric
        }

        for lower, upper in sorted(metric_intervals):
            ax.axvspan(
                lower,
                upper,
                color="#6B7280",
                alpha=0.055,
                linewidth=0,
            )

        ax.set_xscale("log")

        ax.set_xticks(grid)

        ax.set_xticklabels(
            [str(m) for m in grid],
            rotation=0,
        )

        ax.set_ylabel(METRIC_LABELS[metric])

        ax.set_title(
            METRIC_LABELS[metric],
            loc="left",
            fontweight="bold",
        )

        _apply_common_style(ax)

    axes[-1].set_xlabel("Number of sampled negatives (m, log scale)")

    axes[0].legend(
        title="Profile",
        ncol=3,
        frameon=False,
        loc="best",
    )

    fig.text(
        0.5,
        0.012,
        ("No exact crossover is inferred between computed grid points."),
        ha="center",
        fontsize=10,
        style="italic",
    )

    _save(
        fig,
        output_dir / "figure_2_sample_size_sensitivity",
    )


def render_figure_3(
    payload: dict[str, Any],
    colors: dict[str, str],
    output_dir: Path,
) -> None:
    grid = payload["grid"]

    auc = payload["auc"]

    full_auc = payload["full_auc"]

    mc_rows = payload["high_precision_mc"]

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12, 11),
        constrained_layout=True,
    )

    fig.suptitle(
        "AUC is the negative control; Monte Carlo validates the analytical expectations",
        fontsize=17,
        fontweight="bold",
    )

    # --------------------------------------------------------------
    # Upper: AUC negative control.
    # --------------------------------------------------------------

    ax = axes[0]

    for profile in PROFILE_ORDER:
        ax.plot(
            grid,
            auc[profile],
            marker="o",
            markersize=5,
            linewidth=2.0,
            color=colors[profile],
            label=(f"{profile} sampled expectation"),
        )

        ax.axhline(
            full_auc[profile],
            linestyle="--",
            linewidth=1.4,
            color=colors[profile],
            alpha=0.75,
        )

    ax.set_xscale("log")

    ax.set_xticks(grid)

    ax.set_xticklabels([str(m) for m in grid])

    ax.set_xlabel("Number of sampled negatives (m, log scale)")

    ax.set_ylabel("AUC")

    ax.set_title(
        ("Negative control: sampled expected AUC matches full-catalog AUC"),
        loc="left",
        fontweight="bold",
    )

    ax.text(
        0.99,
        0.05,
        (
            "Full-catalog ordering: "
            f"{payload['full_auc_ordering']}\n"
            "Sampled m=99 ordering: "
            f"{payload['sampled_auc_ordering']}"
        ),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
        bbox={
            "boxstyle": "round,pad=0.45",
            "facecolor": "white",
            "edgecolor": "#D1D5DB",
            "alpha": 0.95,
        },
    )

    _apply_common_style(ax)

    ax.legend(
        frameon=False,
        ncol=3,
        loc="best",
    )

    # --------------------------------------------------------------
    # Lower: analytical vs MC parity.
    # --------------------------------------------------------------

    ax = axes[1]

    marker_by_metric = {
        "ap": "o",
        "ndcg": "s",
        "recall_at_10": "^",
        "auc": "D",
    }

    all_values: list[float] = []

    for row in mc_rows:
        analytical = float(row["analytical"])

        monte_carlo = float(row["monte_carlo"])

        se = float(row["se"])

        profile = str(row["profile"])

        metric = str(row["metric"])

        all_values.extend(
            [
                analytical,
                monte_carlo,
            ]
        )

        ax.errorbar(
            analytical,
            monte_carlo,
            yerr=se,
            fmt=marker_by_metric[metric],
            markersize=7,
            color=colors[profile],
            ecolor=colors[profile],
            alpha=0.9,
            capsize=2,
        )

    lower = min(all_values)
    upper = max(all_values)

    span = upper - lower
    padding = max(
        span * 0.06,
        0.01,
    )

    parity_min = max(
        0.0,
        lower - padding,
    )
    parity_max = min(
        1.02,
        upper + padding,
    )

    ax.plot(
        [
            parity_min,
            parity_max,
        ],
        [
            parity_min,
            parity_max,
        ],
        linestyle="--",
        linewidth=1.4,
        color="#6B7280",
        label="Perfect agreement",
    )

    ax.set_xlim(
        parity_min,
        parity_max,
    )

    ax.set_ylim(
        parity_min,
        parity_max,
    )

    ax.set_xlabel("Analytical expectation")

    ax.set_ylabel("10,000-run Monte Carlo mean")

    ax.set_title(
        ("Independent simulation check at m=99 (error bars = Monte Carlo SE)"),
        loc="left",
        fontweight="bold",
    )

    _apply_common_style(ax)

    profile_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor=colors[profile],
            markeredgecolor=colors[profile],
            label=f"Profile {profile}",
        )
        for profile in PROFILE_ORDER
    ]

    metric_handles = [
        Line2D(
            [0],
            [0],
            marker=marker_by_metric[metric],
            linestyle="None",
            color="#374151",
            label=METRIC_LABELS[metric],
        )
        for metric in (
            "ap",
            "ndcg",
            "recall_at_10",
            "auc",
        )
    ]

    ax.legend(
        handles=(profile_handles + metric_handles),
        frameon=False,
        ncol=4,
        fontsize=9,
        loc="best",
    )

    fig.text(
        0.5,
        0.012,
        (
            "Both the 1,000-run source-protocol simulation "
            "and the 10,000-run high-precision simulation passed "
            "the preregistered analytical agreement rule."
        ),
        ha="center",
        fontsize=10,
    )

    _save(
        fig,
        output_dir / "figure_3_negative_control_validation",
    )


def render_all(
    repo: Path,
    output_dir: Path,
) -> dict[str, Any]:
    (
        release,
        validation,
        contract,
    ) = load_inputs(repo)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    colors = profile_colors(contract)

    payloads = figure_payloads(
        release,
        validation,
    )

    render_figure_1(
        payloads["figure_1"],
        colors,
        output_dir,
    )

    render_figure_2(
        payloads["figure_2"],
        colors,
        output_dir,
    )

    render_figure_3(
        payloads["figure_3"],
        colors,
        output_dir,
    )

    for filename in FIGURE_FILES:
        path = output_dir / filename

        if not path.is_file():
            raise RuntimeError(f"Missing figure artifact: {filename}")

        if path.stat().st_size <= 1000:
            raise RuntimeError(f"Suspiciously small figure artifact: {filename}")

    files_manifest: dict[str, dict[str, int | str]] = {}

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "project": ("p28_sampled_recommendation_metrics"),
        "step": 6,
        "status": "PASS",
        "generation_method": ("PROGRAMMATIC_MATPLOTLIB_FROM_FROZEN_DATA"),
        "preview_images_used": False,
        "results_frozen": True,
        "output_design_frozen": True,
        "scientific_source": ("assets/p28_sampled_recommendation_metrics/frozen/release_data.json"),
        "design_source": (
            "docs/projects/p28_sampled_recommendation_metrics/OUTPUT_DESIGN_CONTRACT.json"
        ),
        "profile_colors": colors,
        "figure_contract": {
            "count": 3,
            "figure_1": {
                "purpose": ("Full-catalog vs expected sampled AP reversal"),
                "full_ordering": (payloads["figure_1"]["full_ordering"]),
                "sampled_ordering_m99": (payloads["figure_1"]["sampled_ordering"]),
            },
            "figure_2": {
                "purpose": ("Sample-size sensitivity for AP, NDCG, Recall@10"),
                "sample_size_grid": (payloads["figure_2"]["grid"]),
                "exact_crossover_inference": False,
            },
            "figure_3": {
                "purpose": ("AUC negative control and high-precision MC validation"),
                "auc_ordering": (payloads["figure_3"]["full_auc_ordering"]),
                "source_mc_all_accepted": (payloads["figure_3"]["source_mc_all_accepted"]),
                "high_precision_all_accepted": (
                    payloads["figure_3"]["high_precision_all_accepted"]
                ),
            },
        },
        "files": files_manifest,
    }

    for filename in FIGURE_FILES:
        path = output_dir / filename

        files_manifest[filename] = {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }

    manifest_path = output_dir / "figure_manifest.json"

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return manifest
