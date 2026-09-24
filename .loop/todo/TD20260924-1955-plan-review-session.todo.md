---
name: TD20260924-1955-plan-review-session
description: The missing third oracle — nothing independent audits a gate, and fifteen production runs now say an unsatisfiable plan is the loop's dominant failure mode; plus the two smaller plan-time checks it unblocks, and why per-run insight capture belongs here rather than in a driver prompt
status: open
created: 2026-09-24
source: migrated from `docs/todo.md` § *Waiting on the first clean run* (parked 2026-09-11), with the evidence it was waiting for, from the `exploring-claude` consumer's nine-brief classification arc
waiting-on: A decision on the session's shape — what it emits, whether it may refuse a plan, and how it avoids becoming a prose reviewer. Its precondition is satisfied; only the design is open
---
# The missing third oracle, and what it now has to work with

Three items, in the order they unlock each other. They were parked together on
2026-09-11 waiting on **one clean run in the consumer repo under the
durable-artifact rule and the gate-rewrite guard**, both of which had shipped in
`1.0.0-rc.1` and neither of which had executed in a real iteration. Tuning gates
against no evidence of how the new rules behave was the thing to avoid.

**That wait is over, by a wide margin** — see `## The evidence that arrived`
below. What is still open is the third item's shape, which was always the real
blocker.

## 1. Warn when a task's `verify` runs only files the task itself ships

The planner-authored half of a gate — the `&& uv run python -c "…"` beside the
test file — is load-bearing for **two** invariants, and nothing checks it exists:

- It is the independent oracle when the session writes the test file the gate
  runs. Without it the gate is a self-report.
- It is what keeps *"the gate must fail before the work exists"* true for a task
  that **extends** existing coverage. There the test-file half is already green,
  so if the planner-authored half is absent the gate passes before any work and
  the invariant is silently gone.

Plan-time, in `.loop/amend.sh`. Heuristic — deciding whether a command does
anything besides run that file means looking for a second command or a path the
task does not own — so advisory, like the one-owner warning beside it.

## 2. Enforce "every pending gate fails now" in the driver

Already computed in `.loop/amend.sh` as an advisory. Cannot be made fatal until
(1) lands: the extension case above legitimately presents a partly-green gate,
and a fatal check would reject a correct plan.

## 3. A plan-review session

**Nothing independent audits a gate.** The review session audits tests and
structurally cannot audit gates — the gate is the ruler it measures with, and
`.claude/skills/loop-review/SKILL.md` opens by telling it the gate is settled.
What looks at a verify command today is: the planner's own self-check, a few
narrow mechanical checks in `.loop/run.sh` (a gate must exist; some bad shapes
are refused), advisories in `.loop/amend.sh`, and a human reading
`.loop/state/plan.md`.

The economics are unusually good — once per run, not per iteration, against the
artifact that sets the bar for every iteration after it. And *"would this gate
fail a non-implementation, and could a correct one pass it?"* is a **substance**
question about the gate, the class review sessions demonstrably handle well.
`--plan-only` already carves out the slot; today the only thing filling it is
the operator.

One encouraging data point: calibration cases `07` and `07b` weaken the plan's
acceptance criteria and its goal respectively, and the reviewer caught the
defect anyway in both runs, taking the invariant from the code's own docstring
once the plan stopped naming it. `.loop/tests/reviewer-calibration/RESULTS.md`
concludes **any one source is enough**. So there is resilience to a weak plan;
it is just not an audit of one.

## The evidence that arrived

Fifteen driver runs across nine briefs, 94 iterations, 69 tasks closed, against
a mature TypeScript monorepo. Seven runs did not reach `complete`; two of those
were cost ceilings. **In all five of the remaining halts the implementation was
correct and the plan was not**, the work session diagnosed the cause correctly,
and an operator edit to `.loop/state/state.json` was followed by a one-to-four
iteration finish.

| | Why no correct implementation could pass | Cost | Auditable by a plan review? |
| --- | --- | --- | --- |
| A | `verify` greps a key into a file absent from the task's `files`; the driver reverts it before the gate runs | 4 attempts, `blocked` | **no — and it does not need to be.** Fully deterministic; briefed as a fatal lint rule |
| B | acceptance requires a migration a binding consumer guideline forbids the loop to author | 3 attempts, `stalled` | **yes, and only here.** Needs reading the task's cited references against its acceptance |
| C | `verify` demands a repo-wide invariant the plan did not touch and that was already violated on the main branch | 2 attempts, `stalled` | **yes, and only here.** `amend.sh` cannot see it: the gate fails before the work *and* after it, which is what a correct gate looks like. What distinguishes them is whether the residue is in scope |
| D | two of one task's own acceptance criteria became mutually exclusive once an earlier task landed | 2 attempts, `stalled` | **partly.** The contradiction was latent at plan time and a reviewer holding all tasks at once could see it; nothing else in the loop holds two tasks at once |
| E | scope guard baselined on the plan commit | 1 `blocked`, 6 false reversions | **no.** Briefed as a fatal lint rule plus an env var |

Two of the five are now covered without judgement, by
`docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`. **B, C
and D are the residue, and all three are exactly the substance question above.**
That is the argument this entry was missing on 2026-09-11: not that a plan
review would be nice, but that after the deterministic checks are taken out,
what remains is a class of failure with no mechanical discriminator and a
measured cost of eleven wasted iterations and five operator interventions in one
feature.

**One planner ran the right experiment, and it is weaker evidence than it
looks.** The `B20260915-0016` planner checked gate satisfiability voluntarily: it
built throwaway fake implementations to see whether each gate would pass work
that meets the brief, then broke them **20 ways** on purpose and confirmed every
break was caught (`.loop/state/journals/` of the consumer repo, that run's plan
section). Its run had no incident of this class, and it closed 8/8 with two
review rejections, so the effort did not come out of quality elsewhere.

**But it is not a controlled result, and the entry should not pretend otherwise.**
Three of the nine runs came through with no `blocked` and no `gate_fail`, and the
other two planners did nothing of the kind — one of them was the very run that
shipped nine uncovered HTTP routes, i.e. it avoided *this* class while walking
into a different one. So: n=1, no control, and the mechanism (a gate proven
passable cannot be unpassable) is sound a priori rather than measured. It is the
right experiment and it is on the board; it is not yet a finding.

What the five incidents above *do* establish, independently of it, is the cost of
having no such check: eleven wasted iterations and five operator interventions in
one feature.

## Two constraints any shape must carry

Both come from the arc rather than from first principles.

**It emits findings, never a status.** The session inherits the loop's founding
problem — a session's claims about its own work are unverifiable — so it must
emit findings and evidence the driver records, exactly as the per-task review
session does today. Whether the driver may *refuse* to start a run on its output
is the open question; refusing on judgement is a materially different contract
from every other check in the loop, all of which are deterministic.

**It does not replace the deterministic checks underneath it.** A tag scheme or
an audit makes coverage *look* settled, and that is exactly when it stops being
examined. The lint rules stay fatal and stay first.

## Insight capture — decided, 2026-09-24: not a driver prompt

The same architect act ruled on the adjacent question, because the answer lands
here rather than in the driver.

Across the nine briefs of the arc, only the **last three** journals have an
`## Insights` section at all, and all three were written by the operator *after*
the run. A prompt in the loop was the obvious fix and is the wrong one: the
three captured sets are the highest-value artifacts the arc produced, and every
one of them required holding the **whole run** — 15 iterations, the signals
block, the diffs and the operator's own interventions — which **no component of
the loop holds by design.** `.loop/manual.md` says so directly: *"No cross-phase
judgement. Nothing weighs … because nothing is holding both."*

A per-iteration prompt would produce per-task notes. Those already exist — the
arc wrote **94** of them — and they are precisely what nothing downstream reads.
Adding a ninety-fifth channel does not make the practice work.

So insight capture is a property of whatever ends up holding a whole run, which
today is the operator and may become the run-scoped half of item 3. Until that
shape is decided, it stays operator discipline, and saying so is more honest
than a prompt that produces volume instead of judgement.
