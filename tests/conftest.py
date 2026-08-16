"""Shared fixtures: build run directories inside tmp_path, invoke the CLI in-process."""

import json

import pytest

from runstat.__main__ import main


def _write_session(sessions_dir, name, phase, iteration, total_cost_usd, num_turns,
                    duration_ms, is_error=False, permission_denials=None):
    data = {
        "phase": phase,
        "iteration": iteration,
        "total_cost_usd": total_cost_usd,
        "num_turns": num_turns,
        "duration_ms": duration_ms,
        "is_error": is_error,
        "permission_denials": permission_denials or [],
    }
    (sessions_dir / name).write_text(json.dumps(data))


def _write_iterations(run_dir, records):
    lines = [json.dumps(record) for record in records]
    text = "\n".join(lines)
    (run_dir / "iterations.jsonl").write_text(text + "\n" if lines else "")


@pytest.fixture
def make_run_dir(tmp_path):
    """Factory fixture: build a run directory of session files + iterations.jsonl under tmp_path."""
    counter = {"n": 0}

    def _make(sessions, iterations, name=None):
        counter["n"] += 1
        run_dir = tmp_path / (name or f"run{counter['n']}")
        sessions_dir = run_dir / "sessions"
        sessions_dir.mkdir(parents=True)
        for session in sessions:
            _write_session(sessions_dir, **session)
        _write_iterations(run_dir, iterations)
        return run_dir

    return _make


@pytest.fixture
def run_cli(capsys):
    """Invoke runstat's main() in-process, catching argparse's own SystemExit(2)."""

    def _run(argv):
        try:
            exit_code = main(argv)
        except SystemExit as exc:
            exit_code = exc.code
        captured = capsys.readouterr()
        return exit_code, captured.out, captured.err

    return _run


# The brief's worked example (docs/briefs/0003-runstat-cli.md), reused across test modules.
WORKED_EXAMPLE_SESSIONS = [
    dict(name="001-plan.json", phase="plan", iteration=0, total_cost_usd=1.98, num_turns=12, duration_ms=141000),
    dict(name="002-work.json", phase="work", iteration=1, total_cost_usd=0.50, num_turns=6, duration_ms=68000),
    dict(name="003-review.json", phase="review", iteration=1, total_cost_usd=0.20, num_turns=3, duration_ms=24000),
    dict(name="004-work.json", phase="work", iteration=2, total_cost_usd=0.52, num_turns=7, duration_ms=72000),
    dict(name="005-review.json", phase="review", iteration=2, total_cost_usd=0.20, num_turns=3, duration_ms=24000),
    dict(name="006-work.json", phase="work", iteration=3, total_cost_usd=0.48, num_turns=5, duration_ms=64000),
    dict(name="007-review.json", phase="review", iteration=3, total_cost_usd=0.20, num_turns=3, duration_ms=24000),
]

WORKED_EXAMPLE_ITERATIONS = [
    {"iteration": 1, "task": "T1", "outcome": "done", "attempts": 0, "tasks_done": 1, "tasks_total": 8},
    {"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8},
    {"iteration": 3, "task": "T2", "outcome": "done", "attempts": 1, "tasks_done": 2, "tasks_total": 8},
]

# A second, smaller run — the comparison variant, matching tests/fixtures/runs/20260815-090000.
VARIANT_SESSIONS = [
    dict(name="001-plan.json", phase="plan", iteration=0, total_cost_usd=2.10, num_turns=14, duration_ms=150000),
    dict(name="002-work.json", phase="work", iteration=1, total_cost_usd=0.60, num_turns=8, duration_ms=80000),
    dict(name="003-review.json", phase="review", iteration=1, total_cost_usd=0.20, num_turns=3, duration_ms=25000),
    dict(name="004-work.json", phase="work", iteration=2, total_cost_usd=0.55, num_turns=6, duration_ms=70000),
    dict(name="005-review.json", phase="review", iteration=2, total_cost_usd=0.20, num_turns=3, duration_ms=25000),
]

VARIANT_ITERATIONS = [
    {"iteration": 1, "task": "T1", "outcome": "done", "attempts": 0, "tasks_done": 1, "tasks_total": 8},
    {"iteration": 2, "task": "T2", "outcome": "review_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8},
]


@pytest.fixture
def worked_example_run(make_run_dir):
    return make_run_dir(WORKED_EXAMPLE_SESSIONS, WORKED_EXAMPLE_ITERATIONS, name="worked-example")


@pytest.fixture
def variant_run(make_run_dir):
    return make_run_dir(VARIANT_SESSIONS, VARIANT_ITERATIONS, name="variant")
