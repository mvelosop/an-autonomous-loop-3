"""CLI-level tests for `runstat compare`, over the brief's fixture."""

import subprocess
import sys

from fixtures import write_fixture_run


def _drop_last_iteration(run_dir):
    iterations_path = run_dir / "iterations.jsonl"
    lines = [line for line in iterations_path.read_text().splitlines() if line.strip()]
    iterations_path.write_text("\n".join(lines[:-1]) + "\n")
    return run_dir


def test_compare_shows_all_signals_and_a_numeric_delta(tmp_path):
    run_a = write_fixture_run(tmp_path / "a")
    run_b = _drop_last_iteration(write_fixture_run(tmp_path / "b"))

    result = subprocess.run(
        [sys.executable, "-m", "runstat", "compare", str(run_a), str(run_b)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout
    low = out.lower()
    for label in [
        "iterations",
        "tasks closed",
        "iterations per closed",
        "gate failures",
        "review rejections",
        "attempts burned",
        "no-progress streak",
        "estimated spend",
    ]:
        assert label in low, (label, out)

    lines = [line for line in out.splitlines() if line.strip()]
    iterations_lines = [
        line
        for line in lines
        if line.strip().lower().startswith("iterations")
        and not line.strip().lower().startswith("iterations per")
    ]
    assert iterations_lines, out
    assert "3" in iterations_lines[-1] and "2" in iterations_lines[-1]
    assert "-1" in iterations_lines[-1]

    per_closed_lines = [
        line for line in lines if line.strip().lower().startswith("iterations per")
    ]
    assert per_closed_lines, out
    assert "1.50" in per_closed_lines[-1] and "2.00" in per_closed_lines[-1]

    tasks_closed_lines = [
        line for line in lines if line.strip().lower().startswith("tasks closed")
    ]
    assert tasks_closed_lines
    assert "2/8" in tasks_closed_lines[-1] and "1/8" in tasks_closed_lines[-1]

    assert "estimat" in low


def test_compare_exits_zero_on_two_readable_runs(tmp_path):
    run_a = write_fixture_run(tmp_path / "a")
    run_b = write_fixture_run(tmp_path / "b")

    result = subprocess.run(
        ["runstat", "compare", str(run_a), str(run_b)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
