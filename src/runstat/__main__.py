"""Command-line entry point for runstat."""

import argparse
import sys

from runstat.compare import compute_comparison, format_comparison
from runstat.loader import MalformedInput, NoSessions, RunDirNotFound, load_iterations, load_sessions
from runstat.signals import compute_signals, format_signals
from runstat.summary import format_summary


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

    try:
        if args.command == "summary":
            sessions = load_sessions(args.run_dir)
            output = format_summary(sessions)

        elif args.command == "signals":
            sessions = load_sessions(args.run_dir)
            iterations = load_iterations(args.run_dir)
            output = format_signals(compute_signals(sessions, iterations))

        elif args.command == "compare":
            sessions_a = load_sessions(args.run_dir_a)
            iterations_a = load_iterations(args.run_dir_a)
            sessions_b = load_sessions(args.run_dir_b)
            iterations_b = load_iterations(args.run_dir_b)
            rows = compute_comparison(sessions_a, iterations_a, sessions_b, iterations_b)
            output = format_comparison(rows)
    except RunDirNotFound as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except MalformedInput as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except NoSessions as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:  # never let a traceback reach the user
        print(f"runstat: {exc}", file=sys.stderr)
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
