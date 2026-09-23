"""Project 8 command-line interface."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections.abc import Sequence

from .config import load_default_config
from .reference import load_reference_protocol
from .validation import validate_inputs


def _print_json(value: object) -> None:
    print(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
        )
    )


def audit_environment() -> int:
    config = load_default_config()
    reference = load_reference_protocol(config=config)

    _print_json(
        {
            "status": "PASS",
            "python": {
                "executable": sys.executable,
                "version": sys.version,
                "implementation": platform.python_implementation(),
            },
            "platform": platform.platform(),
            "project": {
                "package": "p28_sampled_recommendation_metrics",
                "n_items": reference.n_items,
                "reference_negative_draws": (reference.reference_negative_draws),
            },
        }
    )

    return 0


def validate_inputs_command() -> int:
    result = validate_inputs()
    _print_json(result)

    return 0 if result["status"] == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sampled-metrics",
        description=("Project 8 sampled recommendation metric replication"),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "audit-environment",
        help="Report Project 8 environment information.",
    )

    subparsers.add_parser(
        "validate-inputs",
        help="Validate frozen Project 8 source inputs.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "audit-environment":
        return audit_environment()

    if args.command == "validate-inputs":
        return validate_inputs_command()

    parser.error(f"unsupported Project 8 command: {args.command}")
