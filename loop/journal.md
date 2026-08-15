# Journal

Append-only narrative of this plan. Rendered state lives in loop/plan.md.

## Plan — 0003-runstat-cli

- **Brief:** `docs/briefs/0003-runstat-cli.md`
- **Tasks:** 9

`loop/state.json` is written and validated.

**Run:** `0003-runstat-cli` — **9 tasks**, dependencies forward-only.

| | task | gate |
| --- | --- | --- |
| T1 | Scaffold package (uv, src layout, pytest) | `import runstat` + full suite passes (≥1 test, so never exit 5) |
| T2 | Fixture-run generator for the worked example | asserts all seven sessions & three records against the brief's tables |
| T3 | Strict run-directory loader | good fixture loads; bad session / bad jsonl line / missing dir each raise `RunError` naming the file |
| T4 | The eight signals | exact `3, 2/8, 1.50, 1, 0, 1, 0, $4.08` + `n/a`, empty, and non-zero-streak cases |
| T5 | CLI entry points + `summary` | per-phase pairing from the brief's table, estimate wording, error/denial callout |
| T6 | `signals` command | exactly eight `key: value` lines, values asserted exactly |
| T7 | `compare` command | fixture vs. variant: iterations `3 → 2` delta `-1`, per-closed `1.50 → 2.00` |
| T8 | Exit-code & error contract | 0/1/2 across all commands, stdout empty on failure, no traceback |
| T9 | End-to-end worked-example test | `test_summary`, `test_signals`, `test_compare` must all exist and pass |

**First ready task: T1** (no dependencies).

All nine verify commands were run: each exits non-zero because its artifact doesn't exist, not because the command is malformed. Since a failing gate only exercises its first line, I also AST-parsed every embedded Python body in full and replayed T5/T6/T7's output-parsing logic against contract-compliant sample output — those three are satisfiable, not just currently failing.

**What I interpreted rather than read** (your chance to correct before the run starts):

1. **I pinned internal API names the brief leaves open** — `runstat.loader.load_run`/`RunError`, `runstat.signals.compute_signals`, `tests/fixtures.py::write_fixture_run(dest)`. Pre-authored gates need stable names before any code exists; the cost is that T3/T4 constrain structure, not just behaviour.
2. **`compute_signals` returns display strings**, not numbers (`'1.50'`, `'$4.08'`). This makes T4's gate assert the exact printed values and forces agreement with `run.sh`'s jq formulas, which brief 0002 §6 requires.
3. **Summary formats**: two-decimal dollars, whole-second wall times with an `s` suffix (`141s`). Taken from the brief's table; column order, padding and separators left free, per "assert on content, not alignment".
4. **The error/denial callout names the offending session file.** The brief says "called out" without saying how; naming the file is what makes a denial actionable.
5. **`compare` delta is run B minus run A.** The brief doesn't specify direction.
6. **A missing `iterations.jsonl` is zero records, not an error** — only *malformed* input is a hard failure. Exit 1 is triggered specifically by no session files, and I treat exit 1 as a "failure" for the empty-stdout rule.
7. **No README or docs task.** The brief doesn't ask for one, and adding it would be the scope-widening it warns about.


## Run ended — max_iterations

- **Run:** `20260815-191201` · 0 iteration(s) this run
- **Plan:** 0/9 done, 0 blocked
- **Signals:** 0 iterations · n/a per closed · 0 gate failure(s) · 0 review rejection(s) · 0 attempt(s) burned · streak 0 · ~$1.95

## Plan amended by the operator — 2026-08-15

Between runs, before any iteration. Task status is the driver's during a run;
the plan itself is the operator's between them.

- **T4 now returns numbers, not display strings.** `compute_signals` returns
  ints, floats and `None`; a separate `format_signals` produces the eight
  `(label, display)` pairs. The planner's original choice coupled formatting
  into the computation and forced `compare` to parse its own output back into
  numbers to get a delta.
- **T10 added — `README.md`.** Gated on truth, not existence: the gate replays
  the tool and requires every printed line to appear verbatim in the document.
- **T11 added — `docs/runstat.md`.** The telemetry contract and each signal's
  derivation. This is what keeps the driver and runstat from drifting, which
  brief 0002 acceptance item 6 requires.
- Brief 0003 updated to match, so a re-run produces the documentation too.

The planner had declined a README, reading the brief's out-of-scope list as
discouraging it. That was a defensible reading of a brief that simply never
asked; the brief now asks.

## T1 — Scaffold the runstat package with uv, src layout and pytest

- **Outcome:** done (review: PASS)
- **Summary:** Added the runstat packaging skeleton: pyproject.toml (hatchling src-layout build, console script runstat = runstat.cli:main, empty runtime deps, pytest as the sole dev dependency), src/runstat/__init__.py, and tests/test_smoke.py with one passing test.
- **Files:** pyproject.toml, src/runstat/__init__.py, tests/test_smoke.py, uv.lock
- **Notes for next iteration:** Used hatchling as the build backend with [tool.hatch.build.targets.wheel] packages = ["src/runstat"] so `uv sync` actually installs the src/ package rather than relying on a path hack. Dev dependency declared via [dependency-groups] dev = ["pytest"] (uv's current convention, PEP 735) rather than the older [tool.uv.dev-dependencies]. `uv sync` created uv.lock and .venv; .venv/__pycache__/.pytest_cache were already covered by .gitignore, uv.lock is new and untracked. The console script runstat is registered but runstat.cli does not exist yet, so `uv run runstat` currently raises ModuleNotFoundError for runstat.cli -- expected until T5 writes that module; import runstat and pytest both work now, which is all this task's acceptance requires.

## T2 — Write the fixture-run generator for the brief's worked example

- **Outcome:** done (review: PASS)
- **Summary:** Added tests/fixtures.py with write_fixture_run(dest), which materializes the brief's worked-example run directory (20260814-101500, seven sessions, three iterations.jsonl records) under any given path, plus tests/test_fixtures.py exercising it via tmp_path.
- **Files:** tests/fixtures.py, tests/test_fixtures.py
- **Notes for next iteration:** write_fixture_run creates dest with parents=True/exist_ok=True before writing, so it works whether dest already exists (pytest's tmp_path) or not. No conftest.py or pytest.ini exists in the repo; pytest's default 'prepend' import mode adds tests/ to sys.path automatically because tests/ has no __init__.py, so tests/test_fixtures.py imports fixtures directly with `from fixtures import write_fixture_run` -- no sys.path hack needed inside the test file itself (the verify command's own inline script still does sys.path.insert(0,'tests') since it runs from outside pytest).

## T3 — Load a run directory strictly, failing loudly on malformed input

- **Outcome:** done (review: PASS)
- **Summary:** Added src/runstat/loader.py with load_run(path) and RunError: a strict loader that reads sessions/*.json and iterations.jsonl into a Run object, raising RunError naming the offending file for a missing run directory, a malformed session file, or a malformed iterations.jsonl line.
- **Files:** src/runstat/loader.py, tests/test_loader.py
- **Notes for next iteration:** Session and Run are frozen dataclasses; Session carries the fields the acceptance criteria list plus `path` (the pathlib.Path it was read from), used by the CLI's error callouts in later tasks. A missing sessions/ directory (not just an empty one) also yields sessions == [], since only the run directory itself is required to exist. Blank lines in iterations.jsonl are skipped before JSON-parsing, matching T2's fixture writer which trailing-newlines the file. RunError messages: 'run directory not found: <path>', 'malformed session file: <name>', 'malformed record in iterations.jsonl: <line!r>' -- all contain the substring the later CLI-contract task (T8) needs on stderr.

## T4 — Compute the eight run-level signals as numbers, and format them separately

- **Outcome:** done (review: PASS)
- **Summary:** Added src/runstat/signals.py with compute_signals(run), returning the eight signals as numbers (ints, floats, None for an undefined ratio), and format_signals(signals), returning the eight (label, display) pairs the CLI will print.
- **Files:** src/runstat/signals.py, tests/test_signals.py
- **Notes for next iteration:** no_progress_streak walks iterations.jsonl records in file order with a synthetic baseline of tasks_done=0 before the first record, flags each record as 'increased' if its tasks_done exceeds the immediately preceding value (baseline for the first record), then counts trailing non-increased records from the end. This baseline is what makes the empty-run case 0 and the two-record case (tasks_done 1,1) come out to 1, not 2 -- the very first record still counts as an increase over nothing. estimated_spend sums total_cost_usd across run.sessions, not iterations.jsonl. tasks_done/tasks_total come from the last iterations.jsonl record only (0/0 when there are no records).

## T5 — Build the CLI entry points and the summary command

- **Outcome:** done (review: PASS)
- **Summary:** Added the runstat CLI entry points (console script and python -m runstat) and the summary command: a per-phase rollup of sessions, cost, turns and wall time with a total row, plus callouts for any session with is_error true or a non-empty permission_denials list.
- **Files:** src/runstat/cli.py, src/runstat/__main__.py, src/runstat/summary.py, tests/test_summary.py
- **Notes for next iteration:** summary.py splits compute_summary(run)/format_summary(summary) the same way T4's signals.py splits compute/format, for the same reason: compute returns numeric rows so nothing downstream has to re-parse printed text. Row order is plan/work/review (only phases present) then any unrecognized phase sorted alphabetically, then a total row; duration_ms is summed and divided by 1000 with round() rather than // so a non-exact-second total wouldn't silently truncate (the fixture's totals are exact multiples of 1000 either way). cli.py's main() already catches loader.RunError and exits 2 with the message on stderr -- built for T5's own error path, not because T8 was pulled forward; T8 still owns the full exit-code contract (missing sessions -> 1, usage errors -> 2, no-traceback guarantee) and none of that is implemented here beyond this one RunError catch. build_parser() only registers the summary subcommand; signals/compare stay for T6/T7 to add via subparsers.add_parser.

## T6 — Add the signals command

- **Outcome:** done (review: PASS)
- **Summary:** Added the `signals` subcommand: a thin printer over the existing compute_signals/format_signals that prints exactly eight `label: value` lines in the brief's order.
- **Files:** src/runstat/cli.py, tests/test_signals_cmd.py
- **Notes for next iteration:** compute_signals/format_signals already existed from T4, so this task was pure CLI wiring: a _cmd_signals handler that loads the run, calls compute_signals then format_signals, and prints f'{label}: {display}' for each pair -- no header, no footer, no blank-line separators (unlike summary's output), matching the 'exactly eight lines and nothing else' acceptance criterion. Registered a new 'signals' subparser in build_parser() next to 'summary'. Did not touch src/runstat/signals.py -- it was already complete and correct for this task's needs.
