"""The exit-code and error-output contract, driven as a subprocess.

0 on success, 1 for a well-formed run with no sessions, 2 for a usage error
or malformed input. Every failing path must leave stdout empty and name the
offending file on stderr, with no Python traceback.
"""

import subprocess
import sys

from fixtures import write_fixture_run


def _cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "runstat", *args], capture_output=True, text=True
    )


def _assert_fails(result, code):
    assert result.returncode == code, (result.returncode, code, result.stdout, result.stderr)
    assert result.stdout == "", result.stdout
    assert result.stderr.strip(), "error path wrote nothing to stderr"
    assert "Traceback" not in result.stderr, result.stderr


def test_missing_run_directory_exits_two(tmp_path):
    missing = str(tmp_path / "nope")
    _assert_fails(_cli("summary", missing), 2)
    _assert_fails(_cli("signals", missing), 2)
    _assert_fails(_cli("compare", missing, missing), 2)


def test_well_formed_run_with_no_sessions_exits_one(tmp_path):
    empty = tmp_path / "empty-run"
    (empty / "sessions").mkdir(parents=True)
    (empty / "iterations.jsonl").write_text("")

    _assert_fails(_cli("summary", str(empty)), 1)
    _assert_fails(_cli("signals", str(empty)), 1)


def test_malformed_session_file_exits_two_and_names_it(tmp_path):
    run_dir = write_fixture_run(tmp_path / "run")
    bad_session = run_dir / "sessions" / "003-review.json"
    bad_session.write_text("{ not json")

    result = _cli("summary", str(run_dir))
    _assert_fails(result, 2)
    assert "003-review.json" in result.stderr, result.stderr


def test_malformed_iterations_line_exits_two_and_names_it(tmp_path):
    run_dir = write_fixture_run(tmp_path / "run")
    iterations_path = run_dir / "iterations.jsonl"
    iterations_path.write_text(iterations_path.read_text() + "oops\n")

    result = _cli("signals", str(run_dir))
    _assert_fails(result, 2)
    assert "iterations.jsonl" in result.stderr, result.stderr


def test_no_subcommand_exits_two():
    _assert_fails(_cli(), 2)


def test_unknown_subcommand_exits_two(tmp_path):
    run_dir = write_fixture_run(tmp_path / "run")
    _assert_fails(_cli("bogus", str(run_dir)), 2)


def test_missing_positional_argument_exits_two():
    _assert_fails(_cli("summary"), 2)


def test_success_exits_zero_with_output(tmp_path):
    run_dir = write_fixture_run(tmp_path / "run")
    result = _cli("signals", str(run_dir))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
