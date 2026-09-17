"""Project 7 command-line interface."""

from __future__ import annotations

import argparse
import json
import platform
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from .config import (
    default_config_path,
    load_config,
    repository_root,
)
from .contracts import (
    blocked_feature_names,
    deployment_feature_names,
)
from .data import (
    build_source_profile,
    load_official_dataset,
    source_paths,
    write_step1_evidence,
)
from .modeling import run_baselines

CLI_NAMESPACE = "prediction-integrity"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"python -m linkedin_visual_labs {CLI_NAMESPACE}",
        description="Prediction-Time Integrity Auditor.",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "audit-environment",
    )

    subparsers.add_parser(
        "show-config",
    )

    subparsers.add_parser(
        "source-profile",
    )

    subparsers.add_parser(
        "write-step1-evidence",
    )

    subparsers.add_parser(
        "run-step2-baseline",
        help=("Run deterministic Pipeline B/C baseline evaluation and write Step 2 evidence."),
    )

    return parser


def _environment_receipt() -> dict[str, object]:
    config = load_config()

    return {
        "status": "PASS",
        "package_id": config.project_id,
        "cli_namespace": CLI_NAMESPACE,
        "seed": config.seed,
        "dataset_id": config.dataset_id,
        "preferred_file": config.preferred_file,
        "target": config.target,
        "preserve_source_order": config.preserve_source_order,
        "repository_root": str(repository_root()),
        "config_path": str(default_config_path()),
        "python_version": platform.python_version(),
        "deployment_feature_count": len(deployment_feature_names()),
        "blocked_features": list(blocked_feature_names()),
    }


def _config_payload() -> dict[str, object]:
    config = load_config()

    return {
        "project_id": config.project_id,
        "seed": config.seed,
        "contract_version": config.contract_version,
        "dataset_id": config.dataset_id,
        "preferred_file": config.preferred_file,
        "target": config.target,
        "preserve_source_order": config.preserve_source_order,
        "chronological_split": {
            "train": config.chronological_split.train,
            "validation": config.chronological_split.validation,
            "test": config.chronological_split.test,
        },
        "random_seed": config.random_seed,
        "random_stratify": config.random_stratify,
    }


def _write_step2_payload(
    payload: dict[str, object],
) -> tuple[Path, Path]:
    root = repository_root() / "assets" / "p27_prediction_time_integrity_auditor"

    root.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_path = root / "baseline_results.json"

    split_path = root / "split_manifest.json"

    results_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            allow_nan=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    split_path.write_text(
        json.dumps(
            {
                "seed": payload["seed"],
                "splits": payload["splits"],
                "baseline_fingerprint_sha256": (payload["baseline_fingerprint_sha256"]),
            },
            indent=2,
            sort_keys=True,
            allow_nan=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    return (
        results_path,
        split_path,
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "audit-environment":
        print(
            json.dumps(
                _environment_receipt(),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "show-config":
        print(
            json.dumps(
                _config_payload(),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "source-profile":
        dataset = load_official_dataset()

        print(
            json.dumps(
                build_source_profile(dataset),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "write-step1-evidence":
        paths = write_step1_evidence(accessed_on=date.today().isoformat())

        local = source_paths()

        print(
            json.dumps(
                {
                    "status": "PASS",
                    "source_csv": str(local.extracted_csv),
                    "evidence": [str(path) for path in paths],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "run-step2-baseline":
        dataset = load_official_dataset(acquire=False)

        payload = run_baselines(dataset)

        results_path, split_path = _write_step2_payload(payload)

        print(
            json.dumps(
                {
                    "status": "PASS",
                    "baseline_fingerprint_sha256": (payload["baseline_fingerprint_sha256"]),
                    "evaluation_count": len(payload["evaluations"]),
                    "results_path": str(results_path),
                    "split_manifest_path": str(split_path),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
