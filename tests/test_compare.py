import pytest

from runstat.compare import compute_comparison
from runstat.loader import load_iterations, load_sessions


def test_compute_comparison_worked_example_vs_variant(worked_example_run, variant_run):
    rows = compute_comparison(
        load_sessions(worked_example_run), load_iterations(worked_example_run),
        load_sessions(variant_run), load_iterations(variant_run),
    )

    assert rows["iterations"] == (3, 2, -1)
    assert rows["iterations per closed"] == (pytest.approx(1.50), pytest.approx(2.00), pytest.approx(0.50))
    assert rows["gate failures"] == (1, 0, -1)
    assert rows["review rejections"] == (0, 1, 1)
    assert rows["attempts burned"] == (1, 1, 0)
    assert rows["no-progress streak"] == (0, 1, 1)
    assert rows["tasks closed"] == ("2/8", "1/8", None)

    spend_a, spend_b, spend_delta = rows["estimated spend"]
    assert spend_a == pytest.approx(4.08)
    assert spend_b == pytest.approx(3.65)
    assert spend_delta == pytest.approx(-0.43)


def test_compare_cli_worked_example_vs_variant(worked_example_run, variant_run, run_cli):
    code, out, err = run_cli(["compare", str(worked_example_run), str(variant_run)])

    assert code == 0
    assert err == ""
    for label in (
        "iterations", "tasks closed", "iterations per closed", "gate failures",
        "review rejections", "attempts burned", "no-progress streak", "estimated spend",
    ):
        assert label in out
    assert "$4.08" in out and "$3.65" in out
