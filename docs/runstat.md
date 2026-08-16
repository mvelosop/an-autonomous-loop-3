# `runstat` telemetry contract

This document is the shared reference for the run-directory layout and the
eight run-level signals. `runstat` (this repo, `src/runstat/`) computes them
post-hoc from an archived run directory; the loop driver described in
[brief 0002](briefs/0002-next-generation-autonomous-loop.md) computes the same
eight signals inline while a run is still in flight. Brief 0002's acceptance
item 6 requires the two implementations to agree exactly on a completed run, so
a derivation recorded in only one of them is how that agreement quietly
breaks. Whenever one implementation's derivation changes, this document and the
other implementation must change with it.

## Run directory layout

```
<run-id>/
  sessions/*.json      one per claude session, name-sortable
  iterations.jsonl     one JSON object per completed iteration
```

Session file names are name-sortable in run order — `001-plan.json`,
`002-work.json`, `003-review.json`, and so on — so reading `sessions/*.json` in
sorted-name order reproduces the order the sessions actually ran in.

## Session fields (`sessions/*.json`)

Each file is the raw `claude -p --output-format json` result for one session,
with two keys added by the driver. `runstat` reads:

| Field | Meaning |
| --- | --- |
| `phase` | `"plan"`, `"work"` or `"review"` — added by the driver |
| `iteration` | integer; `0` for the plan phase — added by the driver |
| `total_cost_usd` | that session's estimated cost |
| `num_turns` | number of turns the session took |
| `duration_ms` | wall-clock duration of the session, in milliseconds |
| `is_error` | whether the session ended in an error |
| `permission_denials` | list of tool calls the session was denied; empty when none |

## Iteration record fields (`iterations.jsonl`)

One JSON object per line, one line per completed iteration:

```json
{"iteration": 2, "task": "T2", "outcome": "gate_fail", "attempts": 1, "tasks_done": 1, "tasks_total": 8}
```

| Field | Meaning |
| --- | --- |
| `iteration` | the iteration number |
| `task` | the task id the iteration worked on |
| `outcome` | one of `done`, `gate_fail`, `review_fail`, `blocked` |
| `attempts` | cumulative attempts spent on this task so far |
| `tasks_done` | count of tasks closed as of this iteration |
| `tasks_total` | total task count in the plan |

`outcome` is always one of exactly four values:

- `done` — the task passed its gate and review.
- `gate_fail` — the task's verify command failed.
- `review_fail` — the gate passed but the review session rejected it.
- `blocked` — the work session could not complete the task.

## Signal derivations

All eight signals, in the order `runstat signals` prints them:

| Signal | Derivation |
| --- | --- |
| iterations | count of `iterations.jsonl` records |
| tasks closed | `tasks_done` / `tasks_total` from the **last** record |
| iterations per closed | iterations ÷ tasks closed, rounded to 2 decimals; the literal string `n/a` when zero tasks are closed |
| gate failures | count of records with `outcome: gate_fail` |
| review rejections | count of records with `outcome: review_fail` |
| attempts burned | count of records whose `outcome` is **not** `done` |
| no-progress streak | count of trailing records whose `tasks_done` did not increase over the previous record (the record before the first is treated as a baseline of 0) |
| estimated spend | sum of `total_cost_usd` across all session files |

### The attempts-burned trap

**`attempts burned` counts records whose `outcome` is not `done` — it is not
the sum of the per-record `attempts` field.** `attempts` is a cumulative
per-task counter: a task that fails its gate twice before finally passing
appears in `iterations.jsonl` as multiple records (`gate_fail`, `gate_fail`,
`done`), and each of those records carries the task's running `attempts`
total at that point. Summing the `attempts` field across records would add
that same task's cumulative count in more than once and double-count it.
Counting non-`done` records instead — one unit of "burned" per failed
iteration — gives the correct total no matter how many times a task retries.

## `compare`

`runstat compare` prints every signal above for two runs side by side with a
delta column: the second run's value minus the first's. Numeric signals get a
signed delta (an explicit leading `+` when positive); `tasks closed` is not
numeric and gets a blank delta rather than a placeholder.

## Agreement with the loop driver

This document, together with `src/runstat/signals.py`, is the single written
statement of these eight derivations. Brief 0002's driver computes the same
signals inline from the same `sessions/*.json` and `iterations.jsonl` layout,
and its acceptance item 6 requires its inline computation to agree with
`runstat`'s exactly on a completed run. If a derivation changes here, it must
change in the driver too, and vice versa — this file and brief 0002 name each
other as the two places that must not drift apart.
