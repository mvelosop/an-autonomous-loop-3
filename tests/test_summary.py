"""CLI-level tests for `runstat summary`, over the brief's fixture."""

import json
import subprocess
import sys

from fixtures import write_fixture_run


def _digit_tokens(line: str) -> set:
    return set(
        "".join(ch if (ch.isdigit() or ch == ".") else " " for ch in line).split()
    )


def _row(stdout: str, name: str) -> set:
    candidates = [
        line
        for line in stdout.splitlines()
        if name in line.lower() and any(ch.isdigit() for ch in line)
    ]
    assert candidates, (name, stdout)
    return _digit_tokens(candidates[-1])


def test_summary_matches_fixture_table(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "runstat", "summary", str(run_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert {"1.98", "12", "141"} <= _row(result.stdout, "plan")
    assert {"1.50", "18", "204"} <= _row(result.stdout, "work")
    assert {"0.60", "9", "72"} <= _row(result.stdout, "review")
    assert {"7", "4.08", "39", "417"} <= _row(result.stdout, "total")
    assert "estimat" in result.stdout.lower()


def test_summary_calls_out_error_and_denied_sessions(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    error_session = run_dir / "sessions" / "004-work.json"
    data = json.loads(error_session.read_text())
    data["is_error"] = True
    error_session.write_text(json.dumps(data))

    denied_session = run_dir / "sessions" / "006-work.json"
    data = json.loads(denied_session.read_text())
    data["permission_denials"] = [{"tool_name": "WebFetch"}]
    denied_session.write_text(json.dumps(data))

    result = subprocess.run(
        [sys.executable, "-m", "runstat", "summary", str(run_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "004-work.json" in result.stdout
    assert "006-work.json" in result.stdout


def test_summary_via_console_script(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = subprocess.run(
        ["runstat", "summary", str(run_dir)], capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr
    assert {"7", "4.08", "39", "417"} <= _row(result.stdout, "total")
