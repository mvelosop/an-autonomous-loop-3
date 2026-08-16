"""Command-line entry point for runstat."""

import argparse
import sys


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="runstat",
        description="Read a completed loop run's telemetry off disk and report what happened.",
    )
    subparsers = parser.add_subparsers(dest="command")

    summary = subparsers.add_parser(
        "summary", help="Per-phase rollup of a run's telemetry: sessions, cost, turns, wall time."
    )
    summary.add_argument("run_dir")

    signals = subparsers.add_parser(
        "signals", help="The eight run-level signals for a run."
    )
    signals.add_argument("run_dir")

    compare = subparsers.add_parser(
        "compare", help="Compare two runs' signals side by side, with deltas."
    )
    compare.add_argument("run_dir_a")
    compare.add_argument("run_dir_b")

    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2

    # Stub: implemented by later tasks in the plan.
    return 0


if __name__ == "__main__":
    sys.exit(main())
