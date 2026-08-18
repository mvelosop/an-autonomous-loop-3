# The loop — a user manual

End to end: brief in, working code out, with evidence of how it got there.

For the design *rationale*, read
[brief 0002](briefs/0002-next-generation-autonomous-loop.md). This is the
operating manual.

---

## 1. The mental model

Three kinds of session, each a **fresh `claude -p` with no memory of any
other**. Files are the entire continuity.

```
brief ──▶ PLAN ──▶ state.json ──▶ ┌─ pick next ready task
 (opus, once)                     │  WORK   does one task, proposes an outcome
                                  │  GATE   driver re-runs EVERY done task's verify
                                  │  REVIEW separate, read-only, independent verdict
                                  │  driver applies it, journals, commits
                                  └─ repeat
```

The one thing to internalise: **the driver decides everything mechanical.**
Which task is next, whether a task is really done, how many attempts it has
burned, when to stop. Agents do work and give opinions. They never set status
and never commit. If you are wondering "could an agent have faked this?", the
answer is almost always no, because it has no way to express the claim.

## 2. One-time setup

```bash
jq --version && uv --version && claude --version   # required
```

**Trust the workspace.** Run `claude` interactively in the repo once and accept
the trust dialog. Without it `claude -p` *silently ignores* `.claude/settings.json`,
so a run executes under the wrong permission surface. Preflight refuses to start
until this is done — it is the single most common way to waste a run.

## 3. Writing a brief

The brief is the highest-leverage artefact in the system. Everything downstream
is measured against gates the planner writes *from it*.

**Pin decisions, leave mechanics open.** Name the behaviour, the exit codes, the
output format, the worked example. Do not name the module layout — that is the
implementation's to choose, and pinning it buys nothing.

**Include a worked example with exact expected values.** It becomes the
end-to-end acceptance test, and it is the arbiter when two implementations
disagree.

**Write an out-of-scope list.** It is not decoration: it is how scope creep
becomes a measurable finding rather than a matter of taste.

**Say roughly how many tasks you expect.** It calibrates decomposition.

See [brief 0003](briefs/0003-runstat-cli.md) (greenfield) and
[brief 0004](briefs/0004-runstat-review.md) (incremental) as worked examples.

## 4. Planning, and checking the plan before you spend

```bash
LOOP_MAX_ITERATIONS=0 loop/run.sh docs/briefs/000N-....md
```

Runs the plan phase alone and stops at the budget (exit 4, resumable). ~$2–4.
**Do this on anything unfamiliar.** The plan authors every `verify` command, and
a weak one silently lowers the bar for the whole run.

Then read `loop/plan.md` and the top of the plan's journal. The planner's report
ends with **what it interpreted rather than read** — that list is your one cheap
chance to catch a misreading before every iteration inherits it.

To amend before running: edit `loop/state.json` (it is yours between runs; the
driver owns it during one), then `loop/render-plan.sh`. Record what you changed
in the journal — the loop will not know otherwise.

Continue with no state edit:

```bash
loop/run.sh
```

## 5. Running

```bash
loop/run.sh docs/briefs/000N-....md   # plan, then iterate
loop/run.sh                           # resume
```

Budgets are **per-run** and checked **between iterations**, so raising one and
re-running always works with no state edit. Defaults: 30 iterations, $40,
3 attempts per task, halt above 3.0 iterations-per-closed-task.

| Variable | Default |
| --- | --- |
| `LOOP_MAX_ITERATIONS` · `LOOP_COST_CEILING` | 30 · 40 |
| `LOOP_MAX_ATTEMPTS` · `LOOP_STALL_LIMIT` | 3 · 2 |
| `LOOP_CONVERGENCE_MAX` · `LOOP_CONVERGENCE_MIN` | 3.0 · 6 |
| `LOOP_PLAN_MODEL` · `LOOP_WORK_MODEL` | opus · sonnet |
| `LOOP_ARCHIVE_TRANSCRIPTS` | 0 |

Expect **~$1 per iteration** on a greenfield plan. Incremental work inverts the
profile — planning was 42% of run 3's cost, because the planner must read
existing code before it can write gates against it.

## 6. Watching it

After every iteration:

```
iterations · tasks closed · iterations per closed · gate failures
review rejections · attempts burned · no-progress streak · estimated spend
```

**Healthy is `iterations per closed` near 1.0.** Climbing means re-work; above
3.0 (after 6 iterations) the run halts itself. These exist because every other
mechanism judges a tick against its task, and nothing else judges the run
against the point of the run.

## 7. When it stops

| Status | Exit | What to do |
| --- | --- | --- |
| complete | 0 | read the journal, open a PR |
| preflight failed | 1 | fix what it named — it names one thing |
| blocked | 2 | a task burned its attempts; read its `notes` in `state.json` |
| stalled | 3 | two iterations with no recorded progress; read the run dir |
| max iterations | 4 | raise `LOOP_MAX_ITERATIONS`, re-run |
| not converging | 5 | **stop and look** — the run is going nowhere |
| cost ceiling | 6 | raise `LOOP_COST_CEILING`, re-run |
| session error | 7 | a `claude` session died; see the run dir |

Complete, max-iterations, stalled and cost-ceiling resume by just re-running.
Blocked, not-converging and session-error want a human first.

## 8. Reading what happened

| | |
| --- | --- |
| `loop/plan.md` | **where are we** — every task, status, attempts, criteria, gate |
| `loop/journals/<plan-id>.md` | **what happened** — planner's report,one entry per iteration, outcome and signals |
| `runstat summary <run-dir>` | per-phase cost, turns, wall time; flags errors and permission denials |
| `runstat signals <run-dir>` | the eight run-level signals |
| `runstat review <run-dir>` | what the reviews ruled, their findings, and coherence checks |
| `runstat compare <a> <b>` | two runs side by side |

Run dirs are `loop/runs/<branch>/<timestamp>/`.

## 9. Running several loops at once

**One loop per git worktree.**

```bash
git worktree add ../loop-006 006-some-plan
cd ../loop-006 && loop/run.sh docs/briefs/0006-....md
```

Git refuses to check one branch out twice, so separate worktrees are necessarily
separate branches. Two loops in **one** working tree share `loop/proposal.json`,
so one's review could pass a task on the other's evidence — the driver takes a
lock (`loop/.running`) and refuses.

## 10. Merging

Branches are **squash-merged and never deleted** — they hold the per-iteration
commits, which are the evidence each task was done by a separate fresh session.

`loop/state.json` belongs to the branch. Merging main *into* a branch must
preserve the branch's copy; main's copy is meaningless. This is deliberately not
mechanised — see `loop/README.md` for why `merge=ours` is a trap — so resolve by
hand:

```bash
git checkout --ours loop/state.json && loop/render-plan.sh
git add loop/state.json loop/plan.md
```

A branch that inherits foreign state resets it when you pass a brief, and
refuses when you do not. **The brief, not the branch, decides.**

## 11. Changing the loop itself

```bash
loop/tests/run-all.sh                                     # free, offline, always
loop/tests/reviewer-calibration/run-calibration.sh        # ~$1.20, calls a model
```

**Run the suite before and after any change to `loop/run.sh`.** And when you add
a test, prove it can fail — break the thing deliberately and watch it go red.
Three tests in this repo have looked green while testing nothing, each asserting
something true in both the good and the bad case.

Changing `.claude/skills/loop-review/SKILL.md`? Re-run the calibration and
compare against [the baseline](../loop/tests/reviewer-calibration/RESULTS.md).
A review contract that stops catching planted defects has regressed, whatever
its prose says.

## 12. Troubleshooting

| Symptom | Cause |
| --- | --- |
| Preflight: "workspace NOT trusted" | §2. Silently voids all permission rules. |
| "a loop is already running in this working tree" | Two loops, one tree. Use a worktree, or clear a stale `loop/.running`. |
| "state.json holds plan X for '\<other brief\>'" | The branch inherited another plan. Passing your brief resets it. |
| "belongs to branch … no way to tell" | Ambiguous with no brief. Pass one. |
| A scaffolding task can never pass | `uv run pytest` exits **5**, not 0, on zero tests collected. Gate on the artefact, not an empty suite. |
| Run halts "not converging" | Re-work loop. Read the failing task's `notes` — it is usually one gate that cannot be satisfied as written. |
