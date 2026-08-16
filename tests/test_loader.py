from fixtures import write_fixture_run

from runstat.loader import RunError, load_run


def test_loads_good_fixture(tmp_path):
    run_dir = write_fixture_run(tmp_path)
    run = load_run(run_dir)

    assert run.run_id == "20260814-101500"
    assert len(run.sessions) == 7
    assert len(run.iterations) == 3
    assert [s.phase for s in run.sessions] == [
        "plan", "work", "review", "work", "review", "work", "review",
    ]
    assert [s.iteration for s in run.sessions] == [0, 1, 1, 2, 2, 3, 3]
    assert all(s.is_error is False and s.permission_denials == [] for s in run.sessions)
    assert run.sessions[0].path.name == "001-plan.json"
    assert [i["outcome"] for i in run.iterations] == ["done", "gate_fail", "done"]


def test_missing_run_directory_raises(tmp_path):
    try:
        load_run(tmp_path / "nope")
    except RunError:
        pass
    else:
        raise AssertionError("expected RunError")


def test_malformed_session_file_names_the_file(tmp_path):
    run_dir = write_fixture_run(tmp_path)
    bad = sorted((run_dir / "sessions").glob("*.json"))[2]
    bad.write_text("{ not json")

    try:
        load_run(run_dir)
    except RunError as exc:
        assert bad.name in str(exc)
    else:
        raise AssertionError("expected RunError")


def test_malformed_iterations_line_names_the_file(tmp_path):
    run_dir = write_fixture_run(tmp_path)
    iterations_path = run_dir / "iterations.jsonl"
    iterations_path.write_text(iterations_path.read_text() + "oops\n")

    try:
        load_run(run_dir)
    except RunError as exc:
        assert "iterations.jsonl" in str(exc)
    else:
        raise AssertionError("expected RunError")


def test_no_session_files_loads_empty(tmp_path):
    run_dir = tmp_path / "empty-run"
    (run_dir / "sessions").mkdir(parents=True)

    run = load_run(run_dir)

    assert run.sessions == []


def test_missing_iterations_file_is_zero_records(tmp_path):
    run_dir = tmp_path / "no-iterations"
    (run_dir / "sessions").mkdir(parents=True)

    run = load_run(run_dir)

    assert run.iterations == []
