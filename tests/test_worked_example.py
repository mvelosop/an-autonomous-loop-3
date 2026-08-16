"""End-to-end acceptance test: the brief's worked example, replayed against
the installed CLI as a whole -- summary, signals and compare together, so
implementation drift that no single-task gate would catch shows up here.
"""

import subprocess

from fixtures import write_fixture_run


def _run(*args):
    return subprocess.run(["runstat", *args], capture_output=True, text=True)


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


def _drop_last_iteration(run_dir):
    iterations_path = run_dir / "iterations.jsonl"
    lines = [line for line in iterations_path.read_text().splitlines() if line.strip()]
    iterations_path.write_text("\n".join(lines[:-1]) + "\n")
    return run_dir


def test_summary(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = _run("summary", str(run_dir))

    assert result.returncode == 0, result.stderr
    assert {"1.98", "12", "141"} <= _row(result.stdout, "plan")
    assert {"1.50", "18", "204"} <= _row(result.stdout, "work")
    assert {"0.60", "9", "72"} <= _row(result.stdout, "review")
    assert {"7", "4.08", "39", "417"} <= _row(result.stdout, "total")
    assert "estimat" in result.stdout.lower()


def test_signals(tmp_path):
    run_dir = write_fixture_run(tmp_path)

    result = _run("signals", str(run_dir))

    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    pairs = [tuple(part.strip() for part in line.split(":", 1)) for line in lines]

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


def test_compare(tmp_path):
    run_a = write_fixture_run(tmp_path / "a")
    run_b = _drop_last_iteration(write_fixture_run(tmp_path / "b"))

    result = _run("compare", str(run_a), str(run_b))

    assert result.returncode == 0, result.stderr
    out = result.stdout
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
