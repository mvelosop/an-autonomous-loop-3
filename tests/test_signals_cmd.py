"""CLI-level tests for `runstat signals`, over the brief's fixture."""

import subprocess
import sys

from fixtures import write_fixture_run


def test_signals_matches_fixture_exactly(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "runstat", "signals", str(run_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    pairs = [tuple(line.split(":", 1)) for line in lines]
    pairs = [(label.strip(), value.strip()) for label, value in pairs]

    assert pairs == [
        ("iterations", "3"),
        ("tasks closed", "2/8"),
        ("iterations per closed", "1.50"),
        ("gate failures", "1"),
        ("review rejections", "0"),
        ("attempts burned", "1"),
        ("no-progress streak", "0"),
        ("estimated spend", "$4.08"),
    ]


def test_signals_prints_exactly_eight_lines(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "runstat", "signals", str(run_dir)],
        capture_output=True,
        text=True,
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(lines) == 8, result.stdout


def test_signals_via_console_script(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = subprocess.run(
        ["runstat", "signals", str(run_dir)], capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr
    assert "estimated spend: $4.08" in result.stdout
