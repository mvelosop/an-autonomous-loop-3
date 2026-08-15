"""Argument parsing and dispatch for the runstat console script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .loader import RunError, load_run
from .signals import compute_signals, format_signals
from .summary import compute_summary, format_summary


def _cmd_summary(args: argparse.Namespace) -> int:
    run = load_run(args.run_dir)
    for line in format_summary(compute_summary(run)):
        print(line)
    return 0


def _cmd_signals(args: argparse.Namespace) -> int:
    run = load_run(args.run_dir)
    for label, display in format_signals(compute_signals(run)):
        print(f"{label}: {display}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="runstat")
    subparsers = parser.add_subparsers(dest="command")

    summary_parser = subparsers.add_parser(
        "summary", help="per-phase rollup of a run's sessions"
    )
    summary_parser.add_argument("run_dir", type=Path)
    summary_parser.set_defaults(func=_cmd_summary)

    signals_parser = subparsers.add_parser(
        "signals", help="the eight run-level convergence signals"
    )
    signals_parser.add_argument("run_dir", type=Path)
    signals_parser.set_defaults(func=_cmd_signals)

    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_usage(sys.stderr)
        return 2

    try:
        return args.func(args)
    except RunError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
