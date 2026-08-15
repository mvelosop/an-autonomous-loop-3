from fixtures import write_fixture_run

from runstat.loader import load_run
from runstat.signals import compute_signals, format_signals


def test_signals_on_fixture(tmp_path):
    run = load_run(write_fixture_run(tmp_path))
    signals = compute_signals(run)

    assert signals["iterations"] == 3
    assert signals["tasks_done"] == 2
    assert signals["tasks_total"] == 8
    assert abs(signals["iterations_per_closed"] - 1.5) < 1e-9
    assert signals["gate_failures"] == 1
    assert signals["review_rejections"] == 0
    assert signals["attempts_burned"] == 1
    assert signals["no_progress_streak"] == 0
    assert abs(signals["estimated_spend"] - 4.08) < 1e-9
    assert not any(isinstance(v, str) for v in signals.values())

    assert format_signals(signals) == [
        ("iterations", "3"),
        ("tasks closed", "2/8"),
        ("iterations per closed", "1.50"),
        ("gate failures", "1"),
        ("review rejections", "0"),
        ("attempts burned", "1"),
        ("no-progress streak", "0"),
        ("estimated spend", "$4.08"),
    ]


def test_signals_with_no_progress_streak(tmp_path):
    run_dir = write_fixture_run(tmp_path)
    iterations_path = run_dir / "iterations.jsonl"
    kept = [line for line in iterations_path.read_text().splitlines() if line.strip()][:-1]
    iterations_path.write_text("\n".join(kept) + "\n")

    signals = compute_signals(load_run(run_dir))

    assert signals["iterations"] == 2
    assert signals["tasks_done"] == 1
    assert abs(signals["iterations_per_closed"] - 2.0) < 1e-9
    assert signals["no_progress_streak"] == 1
    assert dict(format_signals(signals))["iterations per closed"] == "2.00"


def test_signals_on_empty_run(tmp_path):
    run_dir = write_fixture_run(tmp_path)
    (run_dir / "iterations.jsonl").write_text("")

    signals = compute_signals(load_run(run_dir))

    assert signals["iterations"] == 0
    assert signals["tasks_done"] == 0
    assert signals["tasks_total"] == 0
    assert signals["iterations_per_closed"] is None
    assert signals["no_progress_streak"] == 0
    assert dict(format_signals(signals))["iterations per closed"] == "n/a"
