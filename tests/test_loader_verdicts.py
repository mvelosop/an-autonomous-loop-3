from fixtures import write_fixture_run, write_review_fixture_run

from runstat.loader import RunError, load_run


def test_loads_review_fixture_verdicts(tmp_path):
    run_dir = write_review_fixture_run(tmp_path)
    run = load_run(run_dir)

    assert [v.iteration for v in run.verdicts] == [1, 2, 3]
    assert [v.task for v in run.verdicts] == ["T1", "T2", "T2"]
    assert [v.verdict for v in run.verdicts] == ["PASS", "FAIL", "PASS"]
    assert [len(v.criteria) for v in run.verdicts] == [3, 3, 3]
    assert [len(v.findings) for v in run.verdicts] == [0, 2, 0]
    assert all(
        set(("criterion", "met", "evidence")) <= set(c)
        for v in run.verdicts
        for c in v.criteria
    )
    assert run.verdicts[0].path.name == "001-verdict.json"


def test_plain_fixture_has_no_verdicts_and_is_unaffected(tmp_path):
    run_dir = write_fixture_run(tmp_path)
    run = load_run(run_dir)

    assert run.verdicts == []
    assert len(run.sessions) == 7
    assert len(run.iterations) == 3


def test_empty_reports_directory_is_not_malformed(tmp_path):
    run_dir = tmp_path / "empty-reports"
    (run_dir / "reports").mkdir(parents=True)
    (run_dir / "sessions").mkdir(parents=True)

    run = load_run(run_dir)

    assert run.verdicts == []


def test_malformed_verdict_json_raises_naming_the_file(tmp_path):
    run_dir = write_review_fixture_run(tmp_path)
    bad = run_dir / "reports" / "002-verdict.json"
    bad.write_text("{ not json")

    try:
        load_run(run_dir)
    except RunError as exc:
        assert bad.name in str(exc)
    else:
        raise AssertionError("expected RunError")


def test_verdict_missing_required_key_raises_naming_the_file(tmp_path):
    run_dir = write_review_fixture_run(tmp_path)
    bad = run_dir / "reports" / "003-verdict.json"
    bad.write_text('{"task": "T2", "verdict": "PASS"}')

    try:
        load_run(run_dir)
    except RunError as exc:
        assert bad.name in str(exc)
    else:
        raise AssertionError("expected RunError")


def test_proposal_files_are_not_read(tmp_path):
    run_dir = write_review_fixture_run(tmp_path)
    (run_dir / "reports" / "001-proposal.json").write_text("{ not json at all")

    run = load_run(run_dir)

    assert [v.iteration for v in run.verdicts] == [1, 2, 3]
