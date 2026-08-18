import json

from fixtures import write_incoherent_fixture_run, write_review_fixture_run


def test_write_review_fixture_run(tmp_path):
    run_dir = write_review_fixture_run(tmp_path)

    assert run_dir == tmp_path / "20260817-120000"

    verdict_files = sorted((run_dir / "reports").glob("*-verdict.json"))
    assert [p.name for p in verdict_files] == [
        "001-verdict.json",
        "002-verdict.json",
        "003-verdict.json",
    ]

    verdicts = [json.loads(p.read_text()) for p in verdict_files]
    assert [v["task"] for v in verdicts] == ["T1", "T2", "T2"]
    assert [v["verdict"] for v in verdicts] == ["PASS", "FAIL", "PASS"]
    assert [len(v["criteria"]) for v in verdicts] == [3, 3, 3]
    assert [sum(1 for c in v["criteria"] if not c["met"]) for v in verdicts] == [0, 1, 0]
    assert all(str(c["evidence"]).strip() for v in verdicts for c in v["criteria"])
    assert all(set(("criterion", "met", "evidence")) <= set(c) for v in verdicts for c in v["criteria"])
    assert [len(v["findings"]) for v in verdicts] == [0, 2, 0]
    assert all(isinstance(s, str) and s.strip() for v in verdicts for s in v["findings"])
    assert all(set(("task", "verdict", "criteria", "findings", "notes")) <= set(v) for v in verdicts)

    records = [
        json.loads(line)
        for line in (run_dir / "iterations.jsonl").read_text().splitlines()
        if line.strip()
    ]
    by_iteration = {r["iteration"]: r["task"] for r in records}
    assert by_iteration[1] == "T1"
    assert by_iteration[2] == "T2"
    assert by_iteration[3] == "T2"


def test_write_review_fixture_run_creates_destination(tmp_path):
    dest = tmp_path / "nested" / "does-not-exist-yet"
    run_dir = write_review_fixture_run(dest)

    assert run_dir.is_dir()
    assert run_dir.parent == dest


def test_write_incoherent_fixture_run(tmp_path):
    run_dir = write_incoherent_fixture_run(tmp_path / "incoherent")

    verdict_files = sorted((run_dir / "reports").glob("*-verdict.json"))
    assert len(verdict_files) == 1

    verdict = json.loads(verdict_files[0].read_text())
    assert verdict["verdict"] == "PASS"
    assert verdict["criteria"][1]["met"] is False
    assert all(c["met"] for i, c in enumerate(verdict["criteria"]) if i != 1)
    assert all(str(c["evidence"]).strip() for c in verdict["criteria"])
    assert verdict["findings"] == []

    records = [
        json.loads(line)
        for line in (run_dir / "iterations.jsonl").read_text().splitlines()
        if line.strip()
    ]
    iteration_number = int(verdict_files[0].name[:3])
    matching = next(r for r in records if r["iteration"] == iteration_number)
    assert matching["task"] == verdict["task"]
