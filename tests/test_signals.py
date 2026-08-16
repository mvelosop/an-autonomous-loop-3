import pytest

from runstat.loader import load_iterations, load_sessions
from runstat.signals import compute_signals


def test_compute_signals_worked_example(worked_example_run):
    signals = compute_signals(
        load_sessions(worked_example_run), load_iterations(worked_example_run)
    )

    assert signals["iterations"] == 3
    assert signals["tasks closed"] == "2/8"
    assert signals["iterations per closed"] == pytest.approx(1.50)
    assert signals["gate failures"] == 1
    assert signals["review rejections"] == 0
    assert signals["attempts burned"] == 1
    assert signals["no-progress streak"] == 0
    assert signals["estimated spend"] == pytest.approx(4.08)


def test_signals_cli_worked_example(worked_example_run, run_cli):
    code, out, err = run_cli(["signals", str(worked_example_run)])

    assert code == 0
    assert err == ""
    values = dict(line.split(": ", 1) for line in out.splitlines())
    assert values == {
        "iterations": "3",
        "tasks closed": "2/8",
        "iterations per closed": "1.50",
        "gate failures": "1",
        "review rejections": "0",
        "attempts burned": "1",
        "no-progress streak": "0",
        "estimated spend": "$4.08",
    }


def test_iterations_per_closed_is_na_when_zero_tasks_closed(make_run_dir, run_cli):
    sessions = [dict(name="001-plan.json", phase="plan", iteration=0,
                      total_cost_usd=0.1, num_turns=1, duration_ms=1000)]
    iterations = [{"iteration": 1, "task": "T1", "outcome": "blocked",
                   "attempts": 1, "tasks_done": 0, "tasks_total": 8}]
    run_dir = make_run_dir(sessions, iterations)

    code, out, err = run_cli(["signals", str(run_dir)])

    assert code == 0
    assert "iterations per closed: n/a" in out


def test_attempts_burned_counts_non_done_outcomes_not_the_attempts_field(make_run_dir, run_cli):
    sessions = [dict(name="001-plan.json", phase="plan", iteration=0,
                      total_cost_usd=0.1, num_turns=1, duration_ms=1000)]
    iterations = [
        {"iteration": 1, "task": "T1", "outcome": "gate_fail", "attempts": 1, "tasks_done": 0, "tasks_total": 8},
        {"iteration": 2, "task": "T1", "outcome": "gate_fail", "attempts": 2, "tasks_done": 0, "tasks_total": 8},
        {"iteration": 3, "task": "T1", "outcome": "done", "attempts": 2, "tasks_done": 1, "tasks_total": 8},
    ]
    run_dir = make_run_dir(sessions, iterations)

    code, out, err = run_cli(["signals", str(run_dir)])

    assert code == 0
    assert "attempts burned: 2" in out


def test_no_progress_streak_counts_trailing_stalled_records(make_run_dir, run_cli):
    sessions = [dict(name="001-plan.json", phase="plan", iteration=0,
                      total_cost_usd=0.1, num_turns=1, duration_ms=1000)]
    iterations = [
        {"iteration": 1, "task": "T1", "outcome": "done", "attempts": 0, "tasks_done": 1, "tasks_total": 8},
        {"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8},
        {"iteration": 3, "task": "T2", "outcome": "gate_fail", "attempts": 2, "tasks_done": 1, "tasks_total": 8},
    ]
    run_dir = make_run_dir(sessions, iterations)

    code, out, err = run_cli(["signals", str(run_dir)])

    assert code == 0
    assert "no-progress streak: 2" in out
