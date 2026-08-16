"""Argument parsing and dispatch for the runstat console script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compare import compute_compare, format_compare
from .errors import EmptyRunError
from .loader import RunError, load_run
from .signals import compute_signals, format_signals
from .summary import compute_summary, format_summary


def _require_sessions(run, run_dir) -> None:
    if not run.sessions:
        raise EmptyRunError(f"no session files: {run_dir}")


def _cmd_summary(args: argparse.Namespace) -> int:
    run = load_run(args.run_dir)
    _require_sessions(run, args.run_dir)
    for line in format_summary(compute_summary(run)):
        print(line)
    return 0


def _cmd_signals(args: argparse.Namespace) -> int:
    run = load_run(args.run_dir)
    _require_sessions(run, args.run_dir)
    for label, display in format_signals(compute_signals(run)):
        print(f"{label}: {display}")
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    run_a = load_run(args.run_dir_a)
    run_b = load_run(args.run_dir_b)
    _require_sessions(run_a, args.run_dir_a)
    _require_sessions(run_b, args.run_dir_b)
    for line in format_compare(compute_compare(run_a, run_b)):
        print(line)
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

    compare_parser = subparsers.add_parser(
        "compare", help="side-by-side signals for two runs, with a delta"
    )
    compare_parser.add_argument("run_dir_a", type=Path)
    compare_parser.add_argument("run_dir_b", type=Path)
    compare_parser.set_defaults(func=_cmd_compare)

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
    except EmptyRunError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
