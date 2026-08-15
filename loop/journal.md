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
