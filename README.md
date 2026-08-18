# An autonomous loop

An experiment in agentic development: the minimum infrastructure for Claude to
work **unattended for an extended period** following a plan — and the evidence
that it did.

The loop is the deliverable. The program it builds is the proof it ran.

## Why this repo exists

Three earlier attempts were started from the same short prompt and produced
three unrelated systems. The prompt specified a *goal* and left every *decision*
open, and each decision had three or four defensible answers.

So the first artifact here is not code. It is
[**brief 0002**](docs/briefs/0002-next-generation-autonomous-loop.md), which
pins the decisions and leaves the mechanics open, so a re-run reproduces the
loop's **behaviour** rather than its bytes. Every decision in it is either a
measured result from a prior run or a rule from the vendored design notes in
[`docs/references/`](docs/references/).

## How the loop works

```
docs/briefs/NNNN-*.md
        │  plan phase — once, opus
        ▼
loop/state.json          tasks, acceptance criteria, verify commands
        │  iterate phase — repeat, sonnet
        ▼
  driver picks the next ready task
    → work session      does ONE task, proposes an outcome
    → gate              driver re-runs EVERY done task's verify command
    → review session    separate, read-only, independent verdict
    → driver            applies it, journals, commits
    → signals           printed; one of them can halt the run
```

Every session is a fresh `claude -p` with **no memory of any other**. Files are
the entire continuity. The driver owns every mechanical decision — which task is
next, whether a task is really done, attempts, when to stop; agents do the work
and give opinions, and never set status or commit.

Details: [`loop/README.md`](loop/README.md).

## What it built

[**`runstat`**](docs/runstat-cli.md) — a CLI that reads a finished run's
telemetry and reports what each phase cost, whether the run was converging, and
how two runs compare. The loop's first job was to build its own instrument.

- [Usage and worked examples](docs/runstat-cli.md)
- [The telemetry contract and each signal's derivation](docs/runstat.md)
- [The brief it was built from](docs/briefs/0003-runstat-cli.md)

## Results

**Run 1** — 11 tasks, 11 iterations, ~$11.67, exit 0.
**Run 2** — planned and built again from the same brief in an isolated
checkout with no access to run 1's history, journal or telemetry: 10 tasks, 10
iterations, exit 0.

Two independent decompositions, two different structures, identical loop
behaviour:

```
signal                   run 1    run 2
iterations                  11       10
tasks closed             11/11    10/10
iterations per closed     1.00     1.00
gate failures                0        0
review rejections            0        0
```

That is the repeatability claim this repo exists to make, and the numbers were
computed by `runstat` — the tool the loop built — agreeing to the cent with the
driver that ran it, which is brief 0002's acceptance item 6.

**Twenty-one work/review pairs produced zero rejections**, which is unreadable
on its own: a reviewer with nothing to catch and a reviewer that cannot catch
look identical from outside. So the defect was planted instead of waited for —
[reviewer calibration](loop/tests/reviewer-calibration/RESULTS.md) hands a real
review session work that passes its gate but violates its acceptance criteria.
**4 of 4 caught**, including the two shapes a gate structurally cannot see: work
that is correct but out of scope, and criteria no test asserts.

## Layout

| Path | What it is |
| --- | --- |
| `loop/run.sh` | the driver — the only thing you run |
| `loop/README.md` | how the loop works, its stop conditions and its tests |
| `loop/tests/` | 19 fixture scenarios, free and offline |
| `loop/tests/reviewer-calibration/` | planted-defect calibration (calls a real model) |
| `.claude/skills/` | the three session contracts: plan, work, review |
| `docs/briefs/` | the inputs a run is planned from |
| `docs/references/` | vendored design notes the briefs cite |
| `src/`, `tests/` | `runstat`, built by run 1 |

## Branches

`main` reads as one commit per milestone. The branches are **never deleted** —
they hold the loop's per-iteration commits, and those commits *are* the evidence
that each task was done by a separate, fresh session that could not see the
others. A squash on `main` destroys the only record of that.

| Branch | Holds |
| --- | --- |
| `001-an-autonomous-loop` | the harness and its fixture suite |
| `002-runstat` | run 1, one commit per iteration |
| `run2-blind` | run 2 — **deliberately never merged**; it is a second, independent implementation of the same brief, and merging it would overwrite run 1's. It exists so the comparison above stays reproducible. |
| `003-reviewer-calibration` | the planted-defect harness |

## Running it

**[→ The user manual](docs/manual.md)** — end to end: writing a brief, checking
the plan before you spend, watching a run, reading what happened, running
several at once, and changing the loop itself.

```bash
loop/run.sh docs/briefs/0003-runstat-cli.md   # plan, then iterate
loop/run.sh                                   # resume from existing state
loop/tests/run-all.sh                         # the loop's own tests (free)
```

Preflight refuses to start on a problem it can name — most importantly an
**untrusted workspace**, which makes `claude -p` silently ignore this repo's
permission settings. That failure cost an earlier experiment an entire run and
left one line in a log as its only trace.

## Rules that hold everywhere here

All durable state stays in this repo; nothing is written to `~/.claude` or any
global location. No tracked file names the machine it ran on — the driver masks
`$HOME` and the username out of everything it persists. Agents never push. See
[`CLAUDE.md`](CLAUDE.md).
