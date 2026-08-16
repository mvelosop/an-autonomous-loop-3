import pytest

from runstat.loader import load_sessions
from runstat.summary import compute_rollup


def test_compute_rollup_worked_example(worked_example_run):
    rollup = compute_rollup(load_sessions(worked_example_run))

    assert rollup["plan"] == {"sessions": 1, "cost": pytest.approx(1.98), "turns": 12, "wall_ms": 141000}
    assert rollup["work"]["sessions"] == 3
    assert rollup["work"]["cost"] == pytest.approx(1.50)
    assert rollup["work"]["turns"] == 18
    assert rollup["work"]["wall_ms"] == 204000
    assert rollup["review"]["sessions"] == 3
    assert rollup["review"]["cost"] == pytest.approx(0.60)
    assert rollup["review"]["turns"] == 9
    assert rollup["review"]["wall_ms"] == 72000


def test_summary_cli_worked_example(worked_example_run, run_cli):
    code, out, err = run_cli(["summary", str(worked_example_run)])

    assert code == 0
    assert err == ""
    for token in ("$1.98", "$1.50", "$0.60", "$4.08", "141s", "204s", "72s", "417s"):
        assert token in out
    assert "estimat" in out.lower()


def test_summary_calls_out_error_and_denial_sessions(make_run_dir, run_cli):
    sessions = [
        dict(name="001-work.json", phase="work", iteration=1, total_cost_usd=0.1,
             num_turns=1, duration_ms=1000, is_error=True),
        dict(name="002-work.json", phase="work", iteration=2, total_cost_usd=0.1,
             num_turns=1, duration_ms=1000, permission_denials=["Bash(git push:*)"]),
    ]
    run_dir = make_run_dir(sessions, [])

    code, out, err = run_cli(["summary", str(run_dir)])

    assert code == 0
    assert "001-work.json" in out
    assert "002-work.json" in out
    assert "denial" in out.lower()


def test_summary_clean_run_has_no_call_outs(worked_example_run, run_cli):
    code, out, err = run_cli(["summary", str(worked_example_run)])

    assert code == 0
    assert "denial" not in out.lower()
    assert "error" not in out.lower()
