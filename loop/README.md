# The loop

```
docs/briefs/NNNN-*.md
        │
        │  loop/run.sh — plan phase, once, opus
        ▼
loop/state.json                 tasks, acceptance criteria, verify commands
        │
        │  iterate phase, sonnet
        ▼
  driver picks the next ready task
        → work session      does that ONE task, writes loop/proposal.json
        → gate              driver re-runs EVERY done task's verify command
        → review session    read-only, independent, writes loop/verdict.json
        → driver            applies the verdict, journals, commits
        → signals           printed; one of them can stop the run
```

Every session is a fresh `claude -p` with no memory of any other. The files are
the entire continuity, which is what makes a run resumable and repeatable.

## Run it

```bash
loop/run.sh docs/briefs/0003-runstat-cli.md   # plan, then iterate
loop/run.sh                                   # resume from existing state
```

Preflight refuses to start on a problem it can name — most importantly an
**untrusted workspace**, which makes `claude -p` silently ignore this repo's
permission settings. That failure cost a previous experiment an entire run and
left one line in a log as its only trace.

## Who decides what

| Decision | Owner |
| --- | --- |
| Which task is next | driver |
| Whether the code works | the task's `verify` command, run by the driver |
| Whether the task was actually *done* | review session |
| Status transitions, attempts, halting | driver |
| Doing the work | work session |

Agents never set status and never commit. The work session *proposes*; the gate
and the review *dispose*. One commit per iteration, made by the driver, covering
code, state, journal and telemetry together — so the history records what the
loop decided, not what an agent claimed.

## Stopping

| Status | Exit | Resumable by re-running? |
| --- | --- | --- |
| complete | 0 | — |
| preflight failed | 1 | after fixing what it named |
| blocked | 2 | no — a task burned its attempts, a human decides |
| stalled | 3 | yes, but find out why first |
| max iterations | 4 | yes |
| not converging | 5 | no — the run is going nowhere, look at it |
| cost ceiling | 6 | yes — raise `LOOP_COST_CEILING` |
| session error | 7 | no — a `claude` session failed |

Budgets are checked **between** iterations and are **per-run**, so raising one
and re-running needs no state edit. They are runaway backstops; the convergence
signal is what should stop a bad run.

## Signals

Printed after every iteration and at the end:

```
iterations · tasks closed · iterations per closed · gate failures
review rejections · attempts burned · no-progress streak · estimated spend
```

They exist because every gate can be green and every review thorough while the
run goes nowhere — each of those judges one tick against its task, and nothing
else judges the run against the point of the run
(`docs/references/executable-loop-harness.md` Rule 7). `iterations per closed`
is wired to the halt.

`runstat` recomputes these in Python from the same telemetry, and brief 0002's
acceptance item 6 requires the two to agree. **If you change a formula in
`run.sh`, change it in `runstat` too** — the fixture in brief 0003 is the
arbiter for both.

## Evidence

```
loop/runs/<run-id>/
  loop.log                     what the operator saw
  sessions/NNN-<phase>.json    every session's result, stamped with phase + iteration
  iterations.jsonl             one record per iteration — what runstat reads
  gates/<id>.log               latest gate output per task
  gates/NNN-<id>.fail.log      preserved copy of each failure
  reports/NNN-proposal.json    the work session's account of itself
  reports/NNN-verdict.json     the review session's verdict
```

Everything persisted passes through a mask that strips `$HOME` and the username.
Transcripts are **not** archived unless `LOOP_ARCHIVE_TRANSCRIPTS=1`; they hold
absolute paths and full file contents, and they never go inside the repo.

## Tuning

`LOOP_MAX_ITERATIONS` 30 · `LOOP_COST_CEILING` 40 · `LOOP_MAX_ATTEMPTS` 3 ·
`LOOP_STALL_LIMIT` 2 · `LOOP_CONVERGENCE_MAX` 3.0 · `LOOP_CONVERGENCE_MIN` 6 ·
`LOOP_PLAN_MODEL` opus · `LOOP_WORK_MODEL` sonnet
