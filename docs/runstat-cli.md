# runstat

A command-line tool that reads a completed [autonomous loop](CLAUDE.md) run's
telemetry off disk and reports what happened: what each phase cost, whether
the run was converging, and how two runs compare.

`runstat` is strictly post-hoc analysis over archived runs — it has no runtime
role in the loop itself.

## Install and run

```
uv sync
uv run runstat summary <run-dir>
```

`python -m runstat` works the same way:

```
uv run python -m runstat signals <run-dir>
```

## Input layout

A run directory looks like this:

```
<run-id>/
  sessions/*.json            one per claude session, name-sortable
  iterations.jsonl           one JSON object per completed iteration
  reports/NNN-verdict.json   one per reviewed iteration, NNN matching it
  reports/NNN-proposal.json  present, deliberately not read
```

Each `sessions/*.json` file is a `claude -p --output-format json` result with
two keys added by the driver, `phase` (`"plan"`, `"work"` or `"review"`) and
`iteration`. `runstat` reads `total_cost_usd`, `num_turns`, `duration_ms`,
`is_error` and `permission_denials` from it.

Each line of `iterations.jsonl` is one JSON object, for example:

```json
{"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8}
```

Each `reports/NNN-verdict.json` file is the review session's independent
verdict on iteration `NNN` — see `runstat review` below for its fields.
`reports/NNN-proposal.json`, the work session's own report on the same
iteration, is deliberately not read: this tool is about the reviewer, not the
work session's self-report.

## Commands

### `runstat summary <run-dir>`

Per-phase rollup: session count, total cost, total turns and total wall time,
plus a total row. Any session with `is_error` true, or a non-empty
`permission_denials`, is called out by file name.

```
$ uv run runstat summary loop/runs/20260814-101500
phase    sessions       cost   turns    wall
plan            1 $    1.98      12    141s
work            3 $    1.50      18    204s
review          3 $    0.60       9     72s
total           7 $    4.08      39    417s

Dollar figures are an estimate, not a bill.
```

### `runstat signals <run-dir>`

The eight run-level convergence signals, as `key: value` lines:

```
$ uv run runstat signals loop/runs/20260814-101500
iterations: 3
tasks closed: 2/8
iterations per closed: 1.50
gate failures: 1
review rejections: 0
attempts burned: 1
no-progress streak: 0
estimated spend: $4.08
```

### `runstat compare <run-dir> <run-dir>`

All eight signals for both runs side by side, with a delta column (run B minus
run A). The delta is signed for numeric signals and blank for `tasks closed`,
which is a pair rather than a number.

```
$ uv run runstat compare loop/runs/20260814-101500 loop/runs/20260815-093000
signal                      run a      run b      delta
iterations                      3          2         -1
tasks closed                  2/8        1/8           
iterations per closed        1.50       2.00      +0.50
gate failures                   1          1         +0
review rejections               0          0         +0
attempts burned                 1          1         +0
no-progress streak              0          1         +1
estimated spend             $4.08      $4.08     +$0.00

Dollar figures are an estimate, not a bill.
```

This is the repeatability check: two runs of the same plan should show
comparable signals, and a large divergence is the finding.

### `runstat review <run-dir>`

What the review sessions did, and whether their verdicts are coherent: a
per-iteration table, a totals block, every finding verbatim grouped by
iteration, and the five coherence checks (see `docs/runstat.md`).

```
$ uv run runstat review loop/runs/20260817-120000
iteration task   verdict criteria not met findings evidence
        1 T1     PASS           3       0        0      3/3
        2 T2     FAIL           3       1        2      3/3
        3 T2     PASS           3       0        0      3/3

reviews: 3
passed: 2
failed: 1
criteria ruled: 9
criteria not met: 1
findings: 2
evidence cited: 9/9
coherence: ok

iteration 2 (T2):
  missing error handling on empty input
  off-by-one in the range check

coherence checks: no violations
```

A run whose `reports/` verdicts recorded no findings at all prints a plain
`no findings recorded` line instead of the per-iteration groups. A run with
coherence violations prints `coherence: <n> violation(s)` in the totals block
and, after the findings section, one `check <n>: iteration <i> task <t>` line
per violation — it still exits `0`; violations are reported, never enforced.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | success |
| `1` | the run directory is valid but has no session files (`summary`, `signals`, `compare`) or no verdict files (`review`) |
| `2` | usage error, missing directory, or malformed input |

A malformed session file or `iterations.jsonl` line is a hard failure, never a
silent skip — it exits 2 with the offending file named on stderr. On every
failing path stdout stays empty and no Python traceback ever reaches the user.

## Money

Any dollar figure `runstat` prints is an estimate — `total_cost_usd` as
reported by `claude -p`, not a bill.
