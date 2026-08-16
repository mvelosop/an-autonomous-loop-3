def test_missing_run_dir_exits_2(tmp_path, run_cli):
    code, out, err = run_cli(["summary", str(tmp_path / "nope")])

    assert code == 2
    assert out == ""
    assert err.strip() != ""


def test_malformed_session_file_exits_2_and_names_the_file(worked_example_run, run_cli):
    (worked_example_run / "sessions" / "002-work.json").write_text("{")

    code, out, err = run_cli(["summary", str(worked_example_run)])

    assert code == 2
    assert out == ""
    assert "002-work.json" in err


def test_malformed_iterations_line_exits_2_and_names_the_file(worked_example_run, run_cli):
    run_dir = worked_example_run
    with (run_dir / "iterations.jsonl").open("a") as fh:
        fh.write("not json\n")

    code, out, err = run_cli(["signals", str(run_dir)])

    assert code == 2
    assert out == ""
    assert "iterations.jsonl" in err


def test_run_dir_with_no_sessions_exits_1(tmp_path, run_cli):
    run_dir = tmp_path / "empty"
    (run_dir / "sessions").mkdir(parents=True)
    (run_dir / "iterations.jsonl").write_text("")

    code, out, err = run_cli(["summary", str(run_dir)])

    assert code == 1
    assert out == ""
    assert err.strip() != ""


def test_no_subcommand_exits_2_with_usage(run_cli):
    code, out, err = run_cli([])

    assert code == 2
    assert out == ""
    assert err.strip() != ""


def test_unknown_subcommand_exits_2(run_cli):
    code, out, err = run_cli(["bogus"])

    assert code == 2
    assert out == ""
    assert err.strip() != ""


def test_compare_with_wrong_number_of_args_exits_2(worked_example_run, run_cli):
    code, out, err = run_cli(["compare", str(worked_example_run)])

    assert code == 2
    assert out == ""
    assert err.strip() != ""


def test_no_output_command_never_leaks_a_traceback(worked_example_run, run_cli):
    (worked_example_run / "sessions" / "003-review.json").write_text("not json at all")

    code, out, err = run_cli(["signals", str(worked_example_run)])

    assert code == 2
    assert out == ""
    assert "Traceback" not in err
