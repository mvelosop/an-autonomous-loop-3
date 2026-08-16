# runstat

`runstat` reads a completed loop run's telemetry off disk and reports what
happened: what each phase cost, whether the run was converging, and how two
runs compare.

**It has no runtime role in the loop.** The driver (see
`docs/briefs/0002-next-generation-autonomous-loop.md`) computes its own
signals inline while a run is in flight. `runstat` is strictly post-hoc
analysis over archived runs under `loop/runs/` — nothing in the driver
imports it or shells out to it.

## Install and run

`runstat` is a standard-library-only Python package managed with `uv`.

```
uv sync
```

Both entry points work:

```
uv run runstat --help
uv run python -m runstat --help
```

## Input layout

A run directory looks like this:

```
<run-id>/
  sessions/*.json      one per claude session, name-sortable
  iterations.jsonl     one JSON object per completed iteration
```

**`sessions/*.json`** is the raw `claude -p --output-format json` result, plus
two driver-added keys, `phase` (`"plan"`, `"work"` or `"review"`) and
`iteration` (integer, `0` for the plan phase). `runstat` reads five fields
from the result itself: `total_cost_usd`, `num_turns`, `duration_ms`,
`is_error`, `permission_denials`.

**`iterations.jsonl`** holds one object per line, for example:

```json
{"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8}
```

`outcome` is one of `done`, `gate_fail`, `review_fail`, `blocked`.

The examples below run against the two run directories checked in under
`tests/fixtures/runs/`, so they're reproducible verbatim.

## Commands

### `runstat summary <run-dir>`

Per-phase rollup: session count, total cost, total turns, total wall time,
plus a total row. Any session with `is_error` true, or a non-empty
`permission_denials`, is called out by file name — a denial the operator never
sees is a fence in the wrong place that nobody knows about. Dollar figures are
an estimate, not a bill.

```
$ uv run runstat summary tests/fixtures/runs/20260814-101500
plan      1  $1.98    12  141s
work      3  $1.50    18  204s
review    3  $0.60     9  72s
total     7  $4.08    39  417s

Dollar figures are an estimate, not a bill.
```

A run where every session has `is_error: false` and an empty
`permission_denials` prints no call-out. A flagged session is named directly
in the output, e.g. `004-work.json` and whether it reported an error or a
permission denial.

### `runstat signals <run-dir>`

The eight run-level signals from `docs/runstat.md`, as `key: value` lines:

```
$ uv run runstat signals tests/fixtures/runs/20260814-101500
iterations: 3
tasks closed: 2/8
iterations per closed: 1.50
gate failures: 1
review rejections: 0
attempts burned: 1
no-progress streak: 0
estimated spend: $4.08
```

`iterations per closed` prints the literal string `n/a` when zero tasks are
closed. `attempts burned` counts `iterations.jsonl` records whose `outcome` is
not `done` — it is not the sum of the per-record `attempts` field, which is a
cumulative per-task counter.

### `runstat compare <run-dir> <run-dir>`

Every signal from `signals`, for both runs, side by side with a delta column.
The delta is the second run minus the first, with an explicit leading `+`
when positive; `tasks closed` is not numeric, so its delta column is blank.

```
$ uv run runstat compare tests/fixtures/runs/20260814-101500 tests/fixtures/runs/20260815-090000
signal                     run A     run B  delta
iterations                     3         2  -1
tasks closed                 2/8       1/8  
iterations per closed       1.50      2.00  +0.50
gate failures                  1         0  -1
review rejections              0         1  +1
attempts burned                1         1  0
no-progress streak             0         1  +1
estimated spend            $4.08     $3.65  -$0.43
```

This is the repeatability check: two runs of the same plan should show
comparable signals, and a large divergence is the finding.

## Exit-code contract

Every command follows the same contract:

| Exit code | Meaning |
| --- | --- |
| `0` | success |
| `1` | the run directory is valid but has no sessions |
| `2` | usage error, missing run directory, or malformed input |

On any non-zero exit, stdout is empty, the error goes to stderr — naming the
offending path for a missing directory or malformed file — and no Python
traceback ever reaches the user. A malformed session file or
`iterations.jsonl` line is a hard failure, never a silently skipped record: a
partial report that looks complete is worse than a loud refusal.
