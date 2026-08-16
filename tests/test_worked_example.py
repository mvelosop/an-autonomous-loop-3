"""End-to-end acceptance test: the brief's worked example, driven through the CLI.

The one test that catches an implementation whose parts each pass in isolation
while the whole drifts from the documented behaviour (docs/briefs/0003-runstat-cli.md).
"""


def test_worked_example_summary_signals_and_compare(worked_example_run, variant_run, run_cli):
    summary_code, summary_out, summary_err = run_cli(["summary", str(worked_example_run)])
    assert summary_code == 0
    assert summary_err == ""
    for token in ("$1.98", "$1.50", "$0.60", "$4.08", "141s", "204s", "72s", "417s"):
        assert token in summary_out
    assert "estimat" in summary_out.lower()

    signals_code, signals_out, signals_err = run_cli(["signals", str(worked_example_run)])
    assert signals_code == 0
    assert signals_err == ""
    values = dict(line.split(": ", 1) for line in signals_out.splitlines())
    assert values == {
        "iterations": "3",
        "tasks closed": "2/8",
        "iterations per closed": "1.50",
        "gate failures": "1",
        "review rejections": "0",
        "attempts burned": "1",
        "no-progress streak": "0",
        "estimated spend": "$4.08",
    }

    compare_code, compare_out, compare_err = run_cli(
        ["compare", str(worked_example_run), str(variant_run)]
    )
    assert compare_code == 0
    assert compare_err == ""
    assert "-1" in compare_out  # iterations: 3 -> 2
    assert "$4.08" in compare_out and "$3.65" in compare_out
