# The telemetry contract

`runstat` reads a completed loop run's telemetry off disk. This document is the
field-by-field contract for that input, and the derivation of each of the eight
run-level signals. It exists so `runstat` and `loop/run.sh` — which computes the
same eight signals inline, in shell, while a run is in flight — cannot drift
apart without the drift being visible in one place. Brief 0002's acceptance
item 6 requires the two to agree exactly on a completed run; if a formula
changes here, it must change in `loop/run.sh` too, and vice versa.

`runstat` itself never runs during a run. It is strictly post-hoc analysis over
an archived `<run-id>/` directory.

## On-disk layout

```
<run-id>/
  sessions/*.json            one per claude session, name-sortable
  iterations.jsonl           one JSON object per completed iteration
  reports/NNN-verdict.json   one per reviewed iteration, NNN matching it
  reports/NNN-proposal.json  present, deliberately not read
```

### `sessions/*.json`

Each file is the raw `claude -p --output-format json` result for one session,
with two keys added by the driver:

| Field | Meaning |
| --- | --- |
| `phase` | `"plan"`, `"work"` or `"review"` |
| `iteration` | Integer; `0` for the plan phase |

`runstat` reads five more fields from the result itself:

| Field | Meaning |
| --- | --- |
| `total_cost_usd` | The session's reported cost |
| `num_turns` | Turn count for the session |
| `duration_ms` | Wall-clock duration in milliseconds |
| `is_error` | Whether the session ended in error |
| `permission_denials` | List of tool calls the user denied; empty when none occurred |

A file that is not valid JSON is a hard failure (see below), not a skipped
record.

### `iterations.jsonl`

One JSON object per line, one line per completed iteration:

```json
{"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8}
```

| Field | Meaning |
| --- | --- |
| `iteration` | The iteration number this record reports on |
| `task` | The task id the iteration worked |
| `outcome` | One of `done`, `gate_fail`, `review_fail`, `blocked` |
| `attempts` | Cumulative attempt count **for that task** — not per record. See the attempts-burned trap below. |
| `tasks_done` | Count of tasks closed so far, after this iteration |
| `tasks_total` | Total tasks in the plan |

A missing `iterations.jsonl` is treated as zero records — that is a valid state
(a run that has not completed an iteration yet), not malformed input. A line
that is present but not valid JSON is a hard failure.

### `reports/NNN-verdict.json`

One file per reviewed iteration, `NNN` matching the iteration number. Not
every iteration has one: a gate failure skips review entirely, so `reports/`
is legitimately sparser than `iterations.jsonl`.

```json
{
  "task": "T3",
  "verdict": "PASS",
  "criteria": [
    {"criterion": "verbatim text from the task's acceptance list",
     "met": true,
     "evidence": "where the reviewer saw it"}
  ],
  "findings": [],
  "notes": "none"
}
```

| Field | Meaning |
| --- | --- |
| `task` | The task id this verdict rules on |
| `verdict` | `PASS` or `FAIL` |
| `criteria` | One entry per acceptance criterion the reviewer ruled on |
| `criteria[].criterion` | Verbatim text from the task's acceptance list |
| `criteria[].met` | Whether the reviewer judged this criterion satisfied |
| `criteria[].evidence` | Where the reviewer saw it |
| `findings` | List of one-line defect strings; empty on a pass |
| `notes` | Free-text reviewer commentary |

`reports/NNN-proposal.json`, the work session's own report on the same
iteration, is present alongside the verdict but is deliberately not read by
`runstat` — this tool is about the reviewer, not the work session's
self-report.

A **missing** `reports/` directory is not malformed input — it is a run with
no verdicts (`runstat review` exits `1`). A verdict file that **is present**
but is not valid JSON, or is missing any of `task`, `verdict`, `criteria` or
`findings`, is a hard failure, same as a malformed session file.

### The five coherence checks

`runstat review` treats each verdict as a set of independent statements that
should each be false; a violation is reported with its iteration and task, but
never changes the exit code — this command describes a finished run, and a run
cannot be un-run.

1. **A `PASS` with any criterion `met: false`** — the verdict contradicts its
   own rulings.
2. **A `PASS` with a non-empty `findings` list** — findings are what a `FAIL`
   is made of; on a pass they are a defect routed through a non-blocking
   channel, which is indistinguishable from no catch at all.
3. **A `FAIL` with no criterion `met: false` and no findings** — a rejection
   with no stated reason.
4. **Any criterion with empty `evidence`** — a ruling with nothing behind it.
5. **A verdict whose `task` disagrees with the iteration's task** in
   `iterations.jsonl`, where that iteration exists. A verdict for an iteration
   absent from `iterations.jsonl` cannot violate this check.

### Malformed input

A run directory that does not exist, a `sessions/*.json` file that fails to
parse, a non-blank `iterations.jsonl` line that fails to parse, or a
`reports/*-verdict.json` file that fails to parse or is missing a required
field — each is a hard failure. `runstat` never drops the offending record and
continues; undercounting a run's telemetry silently is worse than refusing
loudly. The error names the offending file: the session file's name,
`iterations.jsonl`, or the verdict file's name.

## The eight signals

All eight are derived from `sessions/*.json` and `iterations.jsonl` alone —
nothing else on disk feeds them. `compute_signals` in `src/runstat/signals.py`
returns them as numbers (ints, floats, or `None` for an undefined ratio);
`format_signals` turns those numbers into the `label: value` lines the
`signals` command prints, and the same labels appear as the row headers in
`compare`.

| Label | Derivation |
| --- | --- |
| `iterations` | Count of `iterations.jsonl` records. |
| `tasks closed` | `tasks_done` / `tasks_total` from the **last** `iterations.jsonl` record; `0/0` when there are no records. |
| `iterations per closed` | `iterations ÷ tasks_done`, to two decimals; `n/a` when `tasks_done` is `0` — there is nothing to divide by. |
| `gate failures` | Count of records whose `outcome` is `gate_fail`. |
| `review rejections` | Count of records whose `outcome` is `review_fail`. |
| `attempts burned` | Count of records whose `outcome` is **not** `done`. |
| `no-progress streak` | Count of trailing records whose `tasks_done` did not increase over the immediately preceding value (the record before the first one is treated as `tasks_done: 0`, so the very first record still counts as an increase over nothing); `0` for an empty run. |
| `estimated spend` | Sum of `total_cost_usd` across every session in `sessions/*.json` — **not** derived from `iterations.jsonl`. |

### The attempts-burned trap

`attempts burned` is the count of `iterations.jsonl` records whose `outcome` is
not `done`. It is **not** the sum of the `attempts` field. `attempts` is a
cumulative per-task counter — a task that fails its gate once and then
succeeds produces two records (`gate_fail` with `attempts: 1`, then `done` with
`attempts: 1`), and summing that field would count the same failed attempt
twice. Count records with a non-`done` outcome instead.

## Cross-check against the driver

`loop/run.sh` computes these same eight signals inline, in shell (see the
`sig_*` functions and `print_signals` in the `signals` section of that script),
so an operator watching a run in progress sees numbers that must match what
`runstat signals` reports once the run is archived. The two implementations
are independent — one Python, one `jq`/`awk` — deliberately, so that a bug in
one is unlikely to be reproduced identically in the other. Where they must
agree:

- `sig_iterations` counts lines in `iterations.jsonl`, same as `iterations` above.
- `sig_closed` / `sig_total` read `tasks_done` / `tasks_total` from the last
  record, same as `tasks closed` above.
- `sig_per_closed` divides iterations by tasks closed and prints `n/a` for
  zero closed, same as `iterations per closed` above.
- `sig_gate_fails` / `sig_review_fails` count `outcome` values, same as
  `gate failures` / `review rejections` above.
- `sig_attempts` counts records whose `outcome` is not `done`, with the same
  warning against summing the cumulative `attempts` field, same as
  `attempts burned` above.
- `sig_streak` counts trailing non-increasing `tasks_done` records the same
  way as `no-progress streak` above.
- `sig_spend` sums `total_cost_usd` across session files, same as
  `estimated spend` above.

If `runstat signals` and the driver's `print_signals` output ever disagree on
a completed run, that is a defect in one of the two — the fixture in
`docs/briefs/0003-runstat-cli.md` is the arbiter for both.
