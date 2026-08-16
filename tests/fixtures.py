"""Test helper that materializes the brief's worked-example run directory.

Nothing in this repo reads a real loop/runs/ directory in tests: this is the
one place the brief's fixture numbers are written to disk, and every later
test builds on it via tmp_path.
"""

import json
from pathlib import Path

RUN_ID = "20260814-101500"

# (file name, phase, iteration, total_cost_usd, num_turns, duration_ms)
_SESSIONS = [
    ("001-plan.json", "plan", 0, 1.98, 12, 141000),
    ("002-work.json", "work", 1, 0.50, 6, 68000),
    ("003-review.json", "review", 1, 0.20, 3, 24000),
    ("004-work.json", "work", 2, 0.52, 7, 72000),
    ("005-review.json", "review", 2, 0.20, 3, 24000),
    ("006-work.json", "work", 3, 0.48, 5, 64000),
    ("007-review.json", "review", 3, 0.20, 3, 24000),
]

_ITERATIONS = [
    {"iteration": 1, "task": "T1", "outcome": "done", "attempts": 0, "tasks_done": 1, "tasks_total": 8},
    {"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8},
    {"iteration": 3, "task": "T2", "outcome": "done", "attempts": 1, "tasks_done": 2, "tasks_total": 8},
]


def write_fixture_run(dest: Path) -> Path:
    """Write the brief's worked-example run directory under dest, returning its path."""
    run_dir = dest / RUN_ID
    sessions_dir = run_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    for name, phase, iteration, cost, turns, duration_ms in _SESSIONS:
        record = {
            "phase": phase,
            "iteration": iteration,
            "total_cost_usd": cost,
            "num_turns": turns,
            "duration_ms": duration_ms,
            "is_error": False,
            "permission_denials": [],
        }
        (sessions_dir / name).write_text(json.dumps(record))

    lines = [json.dumps(record) for record in _ITERATIONS]
    (run_dir / "iterations.jsonl").write_text("\n".join(lines) + "\n")

    return run_dir
