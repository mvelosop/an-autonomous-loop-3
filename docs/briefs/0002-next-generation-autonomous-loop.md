# Brief 0002 — The next-generation autonomous loop

- **Status:** implemented — this is now a design record, not a plannable brief
- **Supersedes:** the "create a basic autonomous loop" prompt used to seed
`a-basic-autonomous-loop`, `an-autonomous-loop`, and `an-autonomous-loop-2`.

---

## Why this brief exists

Three runs were started from the same short prompt and produced three unrelated
systems. That is not a model problem — the prompt specified a *goal* and left
every *decision* open, and each decision had three or four defensible answers.
"Minimal" is a taste word, not a constraint.

This brief fixes that by pinning the decisions and leaving the mechanics open.
A re-run should reproduce the loop's **behaviour**, not its bytes.

Every decision below is either a measured result from a prior run or a rule from
[`executable-loop-harness`](../references/executable-loop-harness.md), vendored
into `docs/references/` so it can be read without the source repo. Provenance is
cited inline so a future reader can tell a finding from an opinion.

---

## 1. Goal

Build, in this repo, the Claude Code infrastructure for an agent to work
**unattended for an extended period** following a plan — and then run it on a
real target and keep the evidence.

The loop is the deliverable. The program it builds is the proof it ran.

## 2. What this optimizes for, in priority order

1. **It runs unattended, end to end.** A run that never executes teaches nothing.
   `an-autonomous-loop-2` had the better design on paper and halted at 0 of 8
   iterations; `a-basic-autonomous-loop` had the simpler one and shipped a
   working CLI in 6 tasks. Running beats elegant.
2. **Every claim has evidence on disk.** Run logs, per-iteration output, a
   journal, commits. Nothing asserted that isn't recorded.
3. **A reader can follow the whole thing.** This becomes a blog post. The driver
   should be readable in one sitting.
4. **Reusable machinery** — last, and only where it costs nothing to get.

Corollary: when a choice trades "runs reliably" against "architecturally
better", take the former and write down what you gave up.

---

## 3. Pinned decisions

| Concern | Decision | Provenance |
| --- | --- | --- |
| Driver | A bash script, run by the operator. Fresh `claude -p` session per phase. | All three priors converged here independently. |
| Continuity | Files in this repo only. No conversation memory between sessions. | All three priors. |
| State | One JSON file is the single source of truth. | `executable-loop-harness` Rule 3 — markdown-as-state is where the loop's bug corpus comes from. |
| Who owns mechanics | **The driver**, not the agent: select-next, run gates, count attempts, detect stall, compute run signals, halt. | `executable-loop-harness` Rules 1–2. |
| Verification | Driver re-runs the verify command of **every** done task after every iteration. | `an-autonomous-loop-2`'s design — its own planner flagged that per-task gates alone can't catch a later task regressing an earlier one. It never got to run. |
| Second opinion | A **separate driver-invoked read-only review session** per iteration. | Fixes the flaw in `a-basic-autonomous-loop`, where the verifier was dispatched *by* the working agent and so could be shaped or skipped. |
| Journal | Append-only markdown, written by agents, read by the next iteration. A view, never the source of truth. | `a-basic-autonomous-loop` — its "notes for next iteration" entries were genuinely load-bearing handoffs. |
| Models | **Opus** for the planning phase (once), **Sonnet** for work and review phases. | Task decomposition and verify-command quality dominate run outcome; iterations must stay cheap enough to re-run the experiment. |
| Demo toolchain | Python with `uv`, `src/` layout, `pytest`. | Both priors chose it; gates run in seconds and need no services. |
| Permission model | `--permission-mode auto` plus a project `settings.json` allowlist and denylist. | `a-basic-autonomous-loop` ran unattended on `auto` with no intervention. `acceptEdits` covers edits but still stops on the Bash calls a gate needs. |
| Telemetry | Every session's `--output-format json` result is kept, labelled by role. | `a-basic-autonomous-loop`'s `runs/` — the most informative artifact either prior produced. See §8. |
| Transcript archiving | Supported, **off by default**, enabled by one switch. | `a-basic-autonomous-loop` archived them; they are a privacy surface, so opt-in — the reason to keep them is retroactive data extraction. |

### The one tension in this list

A bash driver contradicts `executable-loop-harness` Rule 2 (mechanical
operations should be tested functions, not shell). It is accepted here because
priority 3 says the driver must be readable, and mitigated by two constraints
that remove the actual bug class the rule was written about:

- State is **JSON read and written with `jq` only**. No `grep`/`sed`/`awk` over
  markdown, ever. Every defect in the harness note's parsing table was a
  hand-rolled parser meeting a document format.
- State edits are **atomic**: write a temp file, then `mv` over the target.

If the driver's mechanics later grow past what this buys, extracting them into a
tested program is the next move — not more shell.

---

## 4. The loop

Three phases. Each is a **separate, fresh `claude -p` session** with no memory of
the others.

```
docs/briefs/NNNN-*.md            the input
        │
        │  PLAN phase — once, opus
        ▼
loop/state.json                  the plan, as structured state
        │
        │  ITERATE phase — repeat, sonnet
        ▼
  ┌───────────────────────────────────────────────────────┐
  │ 1. driver picks the next ready task from state        │
  │ 2. work session: does that ONE task, marks it done    │
  │ 3. driver runs the gate: EVERY done task's verify cmd │
  │ 4. review session: read-only, independent verdict     │
  │ 5. driver applies verdict, updates state, journals    │
  │ 6. driver computes run signals and checks stop conds  │
  └───────────────────────────────────────────────────────┘
```

**Plan phase.** Reads a brief, writes `loop/state.json`. The driver validates the
result before any iteration runs and refuses to start if validation fails:
valid JSON, every task has a non-empty `verify` command, every task has at least
one acceptance criterion, dependencies resolve to real task ids and are acyclic.
A plan that can't be validated is a planning failure, not an iteration failure.

**Work session.** Does exactly one task. Scope discipline is the rule that
matters most: do not start the next task even if it is trivial and the context
is right there. Running ahead desynchronizes the plan from reality, and it was
called out as the main failure mode in the priors.

**Gate.** The driver — not the agent — runs the `verify` command of every task
currently marked done. Any failure reverts that task to pending and costs it an
attempt. "Done" must survive a command the agent doesn't run and can't edit.

**Review session.** A separate read-only session. It sees the task, its
acceptance criteria, and the diff — not the work session's summary of itself.
It re-derives the verdict from the repo. It exists because the gate catches
mechanical failure and not judgment: a test that asserts nothing still passes.
Its verdict is authoritative. A FAIL reverts the task to pending and costs an
attempt. It must not write to anything except its own verdict output.

**Journal.** Every iteration appends one factual entry: task, outcome, files
changed, what the review confirmed, and anything the next iteration cannot see
from the code alone. Terse. No narration of process.

---

## 5. State — required content

The exact schema is left to the implementation. These fields must exist in some
form, because the driver's mechanics depend on them:

**Run level:** run id · source brief · status · iteration counter · timestamps.

**Task level:** id · title · a goal sentence explaining *why the task exists* ·
files it is expected to touch · dependencies · acceptance criteria as a list ·
a single runnable `verify` command · status · attempt count · notes.

Two properties are non-negotiable:

- **The `verify` command is authored in the plan phase, before implementation.**
  This is what keeps the gate from being circular. An agent that writes both the
  test and the gate is grading its own homework.
- **Status transitions are the driver's to make.** The work session proposes;
  the gate and the review dispose.

---

## 6. Stop conditions

A run ends on exactly these, each with a distinct exit code and a one-line
reason in the log:

1. **Complete** — no pending tasks remain.
2. **Blocked** — a task hit the attempt ceiling. Needs a human.
3. **Stalled** — N consecutive iterations changed no state.
4. **Max iterations** — the run's iteration budget is spent.
5. **Not converging** — a run-level signal crossed its threshold (see §7).
6. **Cost ceiling** — the run's spend budget is spent.
7. **Session error** — `claude` exited non-zero.

**Resumable by just re-running the driver:** complete, max-iterations, stalled,
cost-ceiling. **Requires a human decision first:** blocked, not-converging, and
session error — that is the point of them.

Two properties make resumption safe, and both are requirements, not
conveniences:

- **Budgets are checked at iteration boundaries, never mid-iteration.** A run
  stops between a completed iteration and the next one, so state is always
  coherent when the driver exits. A ceiling that can fire between the work
  session and the review session would leave a task committed but unreviewed,
  and resumption would have to reason about a half-done iteration.
- **Iteration and cost budgets are per-run, not per-plan.** They bound one
  driver invocation. Raising a limit and re-running therefore just works, with
  no state edit — the counters start fresh while the plan's own progress,
  attempts, and journal carry forward. Cumulative spend is still recorded in
  telemetry for analysis; it just isn't what the ceiling reads.

Consequence, and the reason to state it: **the budget is a runaway backstop, not
a convergence detector.** If a run is going nowhere, the §7 signal should be
what stops it, and stopping on money instead means the signal was set wrong.
Set the ceilings loose enough that hitting one is genuinely informative.

---

## 7. Run-level signals

This is the deep one, and no prior experiment addressed it.

> Every mechanism in the loop evaluates a tick against its task. Nothing
> evaluates the run against the point of the run.
> — [`executable-loop-harness`](../references/executable-loop-harness.md) Rule 7

Local correctness at every step composes into global stuckness with no in-loop
signal distinguishing the two. Every gate green, every review thorough, the run
going nowhere.

The driver must compute and print, after every iteration:

- iterations per closed task
- verify failures this run
- review rejections this run
- attempts burned across all tasks
- consecutive no-progress streak
- elapsed wall clock and estimated spend, split by phase (§8)

At least one of these must be wired to stop condition 5 with a configurable
threshold. Iterations-per-closed-task is the natural candidate.

These numbers are not decoration — they are the only thing that makes the run
visible from outside itself. Print them where the operator will see them.

---

## 8. Per-session telemetry

Every session runs with `--output-format json` and its result is kept verbatim
under a per-run directory, **labelled with the phase that produced it** — plan,
work, or review. This is what makes §7's signals computable at all; without it
the run is only as legible as its log lines.

`a-basic-autonomous-loop`'s `runs/<timestamp>/` was the most informative
artifact either prior produced, and the same fields carry over:

| Field | Why it earns its place |
| --- | --- |
| `total_cost_usd` | The cost ceiling and the per-phase split. Estimate, not a bill. |
| `num_turns` | A work session's turn count is the sharpest proxy for how hard a task actually was. Exp-1's tasks ran 4–8 turns; the one that ran 17 was the one that fought its tooling. |
| `duration_ms`, `duration_api_ms` | Separates thinking from waiting. Their gap is tool execution — mostly gates. |
| `usage` cache read/write, output tokens | What the context actually cost per session. Fresh-session-per-iteration is the design's central bet; this is the number that prices it. |
| `permission_denials` | A direct readout of whether the allowlist is right. A non-empty array means the agent tried something the settings blocked — the loop's own account of where it was fenced in. Never let this go unlooked-at. |
| `is_error`, `subtype`, `stop_reason` | Distinguishes a clean refusal from a crash from a truncation. |
| `session_id` | The join key to the transcript, if archiving is on. |

Three requirements on top of just keeping the files:

- **Label by phase.** With three sessions per iteration, a per-iteration total
  hides the question worth answering: what does the review session cost relative
  to the work it checks, and is it worth it? That is unanswerable from a lump
  sum and trivial from labelled rows.
- **Print a per-iteration line** as it happens — cost, turns, duration, error
  — so a watching operator sees drift without opening a file. Exp-1's one-line
  format is the reference.
- **Never let telemetry hold message content.** Counts, ids, timestamps, and
  durations only. The result JSON's `result` field carries the session's final
  text; that is fine to keep, but nothing should be added to it.

**Grounding the budget.** Exp-1 measured **~$0.50 per iteration** on sonnet for
a work-only session (5 iterations, $0.49–$0.69 each). A three-phase iteration
adds a review session, so expect **~$0.75–1.00 per iteration**, and a 9-task
plan with a few retries lands around **$15–20**.

Defaults, set deliberately loose per §6 — these are runaway backstops, and the
convergence signal is what should stop a bad run:

| Budget | Default | Reasoning |
| --- | --- | --- |
| Max iterations per run | **30** | ~3× the task count of a typical plan, so retries and re-work never trip it on a healthy run. |
| Cost ceiling per run | **$40** | ~2× the expected full-plan spend. |

Both are per-run (§6), so raising either and re-running needs no state edit. A
run that hits one of these is reporting something worth reading — not being
economized.

---

## 9. Hard rules

1. **All durable state stays in this repo.** Never write session state, memory,
   or config to `~/.claude` or any global location. Drift there is invisible and
   unrepeatable. This is the rule the whole experiment rests on.
2. **Never write an absolute home path into any tracked file, log, or commit
   message.** Repo-relative paths only. The driver masks `$HOME` and the
   username out of every byte it persists — as a backstop, not as the primary
   mechanism. Agents are told the rule; the driver enforces it.
3. **One task per iteration.**
4. **A task is done only when its verify command exits 0 *and* the review
   session passes it.** Claiming done without both just costs an attempt.
5. **Commit per task, locally. Never push.** The per-task commits are the
   evidence the run happened.
6. **No web access during a run.** `WebFetch`/`WebSearch` denied, so a run can't
   drift with the internet. Package installs are fine.
7. **The permission surface is declared in the repo and nowhere else.** Sessions
   run `--permission-mode auto` with `--setting-sources project` and
   `--strict-mcp-config`, so the project `settings.json` allow/deny lists are
   the whole fence and a run behaves the same on any machine. The denylist is
   the load-bearing half: `git push`, `git reset --hard`, `rm -rf`, `sudo`,
   `curl`, recursive `claude` invocations, and any read or write under
   `~/.claude`.
8. **Halting cleanly, with a clear account of what blocked you, is a success.
   Faking progress is the only real failure.**

---

## 10. Preflight

The driver refuses to start unless it has verified, and printed:

- **The workspace is trusted.** An untrusted workspace makes `claude -p`
  *silently ignore* `.claude/settings.json` permissions. This is what killed
  `an-autonomous-loop-2` — the run planned successfully and then executed zero
  iterations, and the only trace was one line in the log preamble. Fail loudly.
- Settings parse and the expected number of permission rules are live.
- Required tools exist (`jq`, `uv`, `claude`).
- Writable telemetry directory for this run.
- State validates, or a brief is available to plan from.
- Masking is active.

A preflight that passes silently is worth less than one that prints what it
checked.

---

## 11. Known traps

Each of these cost a prior run real time. Write the mitigation in, don't
rediscover them.

| Trap | Consequence | Mitigation |
| --- | --- | --- |
| Untrusted workspace | Permissions silently dropped; run does nothing | Preflight, §10 |
| `Write(path)` permission rules | Don't match file writes at all — only `Edit(path)` rules do | Use `Edit(...)` rules |
| Session transcripts | GC'd after ~30 days; contain absolute paths and full file contents | Opt-in archiving, outside the repo, never committable |
| `uv run pytest` with zero tests | Exits **5**, not 0 — a scaffolding task's verify command fails for the wrong reason | Author verify commands that account for it |
| Markdown as state | Hand-rolled parsers meeting a document format — the entire bug corpus | JSON + `jq` only |
| Reviewer sees a summary | A partial catch through a non-blocking channel is indistinguishable from no catch | Review session reads the diff, never the worker's report |

---

## 12. The demo target

The loop's first real run builds a **small command-line program** specified by
its own brief: `docs/briefs/0003-runstat-cli.md` — a post-hoc analyser for this
loop's own run telemetry. It pins one thing on this brief's implementation, the
on-disk telemetry layout (its *Input format* section); everything else about the
driver stays open, and nothing in the driver may depend on it at runtime.

Constraints that brief satisfies, so the run is a fair test of the loop rather
than of the target:

- Self-contained: standard library only, no network, no services.
- Deterministic and fast: the full test suite runs in seconds.
- 6–10 tasks, each independently verifiable by one command.
- A worked example in the brief that becomes an end-to-end acceptance test —
  the one test that catches an implementation whose parts each pass in isolation
  while the whole drifts from the documented behaviour.

Deliberately *not* the same kind of project as `exploring-claude`, which is a
long-running HTTP server. Per
[`executable-loop-harness`](../references/executable-loop-harness.md) Rule 6, the useful next
data point comes from a repo of a **different kind** — it is the artifact-proof
strategy ("prove the thing runs") that a single-stack design gets wrong.

---

## 13. Deliberately left open

The implementation decides all of this, and divergence here is fine:

- The exact JSON schema and field names.
- The driver's internal structure, log format, and CLI surface.
- How the skills and agent contracts are worded, and how many there are.
- The demo program itself.
- How the plan phase decomposes a brief into tasks.

If a re-run of this brief produces a different schema and a different task
breakdown but the same *behaviour* — same phases, same ownership, same stop
conditions, same evidence on disk — the brief did its job.

---

## 14. Acceptance — how we know the experiment worked

1. A run completes a full plan unattended, with per-task commits.
2. The plan's journal reads as a coherent account of what happened, written by
   agents that never shared a session.
3. At least one task is caught by the gate or the review session and re-worked
   — the safety net is proven, not assumed.
4. Run-level signals are printed and a threshold is demonstrated to fire (force
   it if a healthy run never trips it).
5. Telemetry is complete: one labelled result record per session, a per-phase
   cost split, and `permission_denials` either empty or explained. A denial the
   operator can't account for means the fence is in the wrong place.
6. **`runstat signals` over the completed run reproduces the numbers the driver
   printed live.** Every signal, exactly. See below.
7. A second run from the same brief on a clean checkout produces the same
   *behaviour*: same phases, same stop conditions, comparable signals.
8. Nothing outside this repo was written to, and no tracked file names the
   machine it ran on.

Item 7 is the whole point. The prior experiments failed it before they started.

### On item 6

The driver computes the §7 signals inline, in `jq`, while a run is in flight —
that is **control plane**, and it carries authority: it decides whether the run
halts. `runstat` recomputes the same formulas in Python, afterwards, from
`iterations.jsonl` — that is **analysis plane**, with no authority over
anything. Keeping them separate is deliberate (see
`docs/briefs/0003-runstat-cli.md`, *What it is*): a driver that depended on
`runstat` could not compute a signal until iteration 8, would change its own
behaviour mid-run the moment `runstat` started working, and would lose its halt
logic to a gate failure on a `runstat` task.

The price of that separation is **two implementations of one formula, free to
drift**. This item is what makes the drift detectable, and it costs one command
at the end of a run. If the two disagree, one of them is wrong about whether the
run was converging — and since the driver's copy is the one wired to a halt
decision, that is worth knowing immediately rather than at the next post-mortem.

Which is right is settled by neither: `runstat`'s arithmetic is pinned to the
hand-computed fixture in brief 0003's worked example, so the fixture is the
arbiter, not whichever implementation is louder.

---

## 15. What it came to

Measured 2026-08-18, after three runs. §2 said the scale of the mature prose
loop was "deliberately not starting at", so here is where it actually landed:

| | this loop | `exploring-claude` |
| --- | --- | --- |
| **prose contracts** (skills + `CLAUDE.md`) | **391** | 3,280 |
| loop machinery (shell) | 1,115 | 1,816 |
| tests | 1,386 | 1,363 |

The number that matters is the first row. **Orchestration that lives in 3,280
lines of prose an agent interprets, lives here in 672 lines of `run.sh` that
tests exercise 24 ways for free.** The instructions are small because the
mechanics are code: nothing has to tell a session which task is next, whether a
gate passed, or how many attempts remain, because a session has no say in any
of it.

The shell totals are close, but they are not the same kind of shell.
`exploring-claude`'s scripts are helpers *around* a prose orchestrator; these
1,115 lines *are* the orchestrator.

**Not a like-for-like comparison of capability.** `exploring-claude` carries an
acceptance agent, telemetry extraction, a guidelines corpus and 139 archived
plans that this loop has no equivalent of. The claim is narrower and only about
shape: the same orchestration expressed as testable code rather than as prose
with a reviewer.

---

## 16. Sources

**Vendored into `docs/references/`** — readable without the source repo, with
snapshot provenance in that folder's `README.md`:

- [`executable-loop-harness.md`](../references/executable-loop-harness.md)
  — Rules 1, 2, 3, 6, 7; the parsing bug corpus; the invisible-from-inside-the-loop result.
- [`loop-decoupling-pivot.md`](../references/loop-decoupling-pivot.md)
  — mechanism/state split; project-declared gates.

**Not vendored** — consulted, too large or too repo-specific to copy:

- `~/source/personal/exploring-claude/.claude/` — the mature prose loop: ~4,500
  lines of contract plus ~3,200 lines of shell, and 139 archived plans. The
  scale this brief is deliberately not starting at.
- `~/source/personal/blog-posts/a-basic-autonomous-loop` — the run that shipped.
  Fresh sessions, journal-as-memory, stall detection, transcript archiving.
- `~/source/personal/blog-posts/an-autonomous-loop` — containment flags.
- `~/source/personal/blog-posts/an-autonomous-loop-2` — the external verify gate,
  structured task state, output masking; and the trust-dialog failure.
