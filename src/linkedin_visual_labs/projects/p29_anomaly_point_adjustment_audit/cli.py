"""Non-scientific Step 1 command line interface for Project 9."""

from __future__ import annotations

import argparse
import json
import platform
from collections.abc import Sequence

import numpy as np

from .config import (
    PROJECT_ID,
    default_config_path,
    default_config_source,
    load_default_config,
    repository_root,
)
from .experiment import run_pilot, run_prefreeze_sweep
from .presentation import render_presentation, validate_presentation
from .publication import build_publication, package_release, validate_publication
from .validation import current_branch, validate_setup

CLI_NAMESPACE = "anomaly-evaluation"


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"python -m linkedin_visual_labs {CLI_NAMESPACE}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "audit-environment",
        "validate-inputs",
        "show-contract",
        "run-pilot",
        "run-prefreeze-sweep",
        "render-presentation",
        "validate-presentation",
        "build-publication",
        "validate-publication",
        "package-release",
    ):
        subparsers.add_parser(command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_default_config()
    if args.command == "audit-environment":
        _print(
            {
                "status": "PASS",
                "project_id": PROJECT_ID,
                "config_path": str(default_config_path()),
                "config_source": default_config_source(),
                "repository_root": str(repository_root()),
                "python_version": platform.python_version(),
                "numpy_version": np.__version__,
                "branch": current_branch(),
                "scientific_contract_status": "FROZEN",
                "source_discrepancy_status": "UNRESOLVED",
                "publication_scope_status": "EDITORIAL_SCOPE_CHECK_NEEDED",
                "presentation_contract_status": "FROZEN",
            }
        )
        return 0
    if args.command == "validate-inputs":
        _print(validate_setup(config))
        return 0
    if args.command == "run-pilot":
        _print(run_pilot(config))
        return 0
    if args.command == "run-prefreeze-sweep":
        _print(run_prefreeze_sweep(config))
        return 0
    if args.command == "render-presentation":
        _print(render_presentation())
        return 0
    if args.command == "validate-presentation":
        _print(validate_presentation())
        return 0
    if args.command == "build-publication":
        _print(build_publication())
        return 0
    if args.command == "validate-publication":
        _print(validate_publication())
        return 0
    if args.command == "package-release":
        _print(package_release())
        return 0
    _print(
        {
            "project_id": PROJECT_ID,
            "config_source": default_config_source(),
            "experiment_status": "NOT_STARTED",
            "publication_scope_status": "EDITORIAL_SCOPE_CHECK_NEEDED",
            "source_discrepancy_status": "UNRESOLVED",
            "presentation_contract_status": "FROZEN",
            "primary_condition": {
                "L": config.primary_event_length,
                "q": config.primary_alert_probability,
            },
        }
    )
    return 0
