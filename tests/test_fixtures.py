import json

from fixtures import write_fixture_run


def test_write_fixture_run(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    assert run_dir == tmp_path / "20260814-101500"

    session_files = sorted((run_dir / "sessions").glob("*.json"))
    assert [p.name for p in session_files] == [
        "001-plan.json",
        "002-work.json",
        "003-review.json",
        "004-work.json",
        "005-review.json",
        "006-work.json",
        "007-review.json",
    ]

    sessions = [json.loads(p.read_text()) for p in session_files]
    assert [s["phase"] for s in sessions] == [
        "plan", "work", "review", "work", "review", "work", "review",
    ]
    assert [s["iteration"] for s in sessions] == [0, 1, 1, 2, 2, 3, 3]
    assert [round(s["total_cost_usd"], 2) for s in sessions] == [
        1.98, 0.50, 0.20, 0.52, 0.20, 0.48, 0.20,
    ]
    assert [s["num_turns"] for s in sessions] == [12, 6, 3, 7, 3, 5, 3]
    assert [s["duration_ms"] for s in sessions] == [
        141000, 68000, 24000, 72000, 24000, 64000, 24000,
    ]
    assert all(s["is_error"] is False and s["permission_denials"] == [] for s in sessions)

    records = [
        json.loads(line)
        for line in (run_dir / "iterations.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert [
        (r["iteration"], r["task"], r["outcome"], r["attempts"], r["tasks_done"], r["tasks_total"])
        for r in records
    ] == [
        (1, "T1", "done", 0, 1, 8),
        (2, "T2", "gate_fail", 1, 1, 8),
        (3, "T2", "done", 1, 2, 8),
    ]


def test_write_fixture_run_creates_destination(tmp_path):
    dest = tmp_path / "nested" / "does-not-exist-yet"
    run_dir = write_fixture_run(dest)

    assert run_dir.is_dir()
    assert run_dir.parent == dest
