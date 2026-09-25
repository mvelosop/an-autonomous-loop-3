# Open work

Decisions taken and deliberately deferred, with the reasoning that produced
them. Not a constraint on any task — nothing here should be cited onto a plan.
It exists because the loop is worked on in bursts between blog posts, and the
reasoning behind a parked decision is the first thing to evaporate.

Each entry says what it is waiting on, so a stale one is visible.

---

## Bug — the driver's dependency gating is inert

**Found 2026-09-16**, in the `exploring-claude` SPA-207 run (loop brief
`B20260916-0045-implement-classification-backend-corrections`). Not yet fixed:
it wants its own commit and a scenario, and the run that found it was mid-flight.

`.loop/run.sh`'s next-ready-task selector reads:

```jq
[.tasks[]|select(.status=="done")|.id] as $d
| [.tasks[]|select(.status=="pending")
   | select(([.depends_on[]?|select(($d|index(.))==null)]|length)==0)][0].id
```

Inside `index(...)`, `.` is **the input to `index`** — which is `$d`, the
done-list — not the dependency being tested. So it evaluates `$d|index($d)`:
where does `$d` occur as a subsequence of itself. The answer is always `0`,
never `null`, so the missing-dependency list is **always empty** and every
pending task always passes the readiness check.

```
$ jq -nc '["T1","T2"] as $d | "T4" | $d|index(.)'
0                                   # expected null
$ jq -nc '["T1","T2","T3"] | index("T4")'
null                                # the literal form is correct
```

**What it means.** `depends_on` has never gated anything. Task selection is
really *"first pending task in array order"*. Plans list tasks in dependency
order, so the two agree almost always — which is why this survived the whole
scenario suite and several real runs.

**How it surfaced.** SPA-207's T4 hit its attempt ceiling and went `blocked`.
T10 depends on T4. The driver dispatched T10 anyway, with T4 unmet — the first
time a plan had a *hole* in the middle rather than a prefix of done tasks.

**The fix** — bind the dependency before testing it:

```jq
select([.depends_on[]? as $x | select(($d|index($x))==null)] | length == 0)
```

**What it is waiting on.** Nothing external — but it should land with a scenario
that fails on the old expression, which means a fixture plan whose ready task is
*not* first in array order (a blocked or out-of-order mid-plan task). Every
existing scenario's plan is ordered, so none of them can fail on this.

**Worth noting for the metrics work**: a run whose dependencies silently did not
hold is not obviously distinguishable, after the fact, from one whose plan was
simply ordered. Runs before the fix carry that ambiguity.

---

## The gate database — a project-specific convention the planner cannot see

**Parked 2026-09-16**, from `exploring-claude`'s SPA-207 run. Three findings
that turn out to be one design gap, so they are written together.

### What happened

SPA-207's T4 had to write an idempotent backfill migration. `exploring-claude`'s
the consumer's *migrations.guidelines.md* Rule 8 forbids the loop from authoring **or running**
any data-lossy `UPDATE`, and tells the reviewer to treat one as a halt. The
brief commissioned exactly that migration. Both agents behaved correctly and the
task deadlocked: the reviewer halted it, then two successive work sessions
refused to re-author it — while the deliverable, authored on attempt 1 and
committed by the driver, sat complete with its gate exiting 0.

Meanwhile the gate ran against `xc_dev`, the operator's real working database,
and a work session applied the migration to it **on its own initiative** — no
gate asked for it. Gates inspect the repo, not the database, so nothing could
have caught that.

### The part that makes it a loop problem

`exploring-claude` already had the answer and lost it. Its SPA-200 run
established a convention: every gate boots the app with `DB_NAME=xc_gate`, a
throwaway clone, so the loop never touches real data. That run's planner even
verified the override reaches the migration CLI. **Four plans later the
convention was gone** — SPA-207's ten verify commands contain zero `DB_NAME`
overrides, and `xc_gate` is stale by two migrations.

It decayed because it lived nowhere a planner reads. It is not in `CLAUDE.md`
(too specific), not in a guideline (it is not a coding convention), and
`.claude/loop-knowledge.md` currently describes **document roots only** — where
knowledge lives, not how the project is operated.

### What to build

**1. Let `loop-knowledge.md` carry operational facts, not just document roots.**
The planner needs to know "gates run against `xc_gate`, never `xc_dev`" the same
way it needs to know where ADRs live. Open question — and the reason this is
parked rather than done — is how far that goes before it becomes a second
`CLAUDE.md`. A named-commands table (`gate database`, `reset command`) is
probably the whole of it; anything more open-ended will rot the same way.
The consumer side is a *package.json* script the knowledge file can name, so
the fact is a command rather than a paragraph.

**2. A plan-time check that gates do not touch the real database.** Every
`verify` that boots the app or runs migrations must carry the gate-DB override.
Mechanical, fixture-testable, fails before the run spends anything. This is the
"prefer a check to a rule" case exactly: the convention existed as lore, was
never a gate, and decayed silently.

**3. Split Rule 8's authoring from its running** (consumer-side, but it only
works once 1 and 2 exist). Authoring a destructive migration is low-risk — it is
text, and its effect is provable against a disposable database. Applying one to
a database someone cares about is the actual risk. With a gate DB the loop may
author, apply and test freely, and Rule 8 stays **unrelaxed** for real data
rather than needing a carve-out.

### Why this is worth more than unblocking one task

**The migration tests currently run against a brand-new empty database.** A
backfill asserted only against planted fixtures never meets the shapes real data
has — so a whole class of error is invisible today. A gate database cloned from
real data closes that gap, and it is the same mechanism. That is the larger
prize here; unblocking T4 is incidental.

### What it is waiting on

A decision on how much operational surface `loop-knowledge.md` should carry
(item 1) — items 2 and 3 are straightforward once that is settled. Note also
that the gate DB needs a provisioning story: `exploring-claude`'s `xc_gate` was
cloned by hand in SPA-200 and nothing has refreshed it since, which is how it
ended up two migrations stale.

---

## Gate authoring — two defects SPA-207 surfaced

**Parked 2026-09-16.** Neither is a loop bug; both are things a planner got
wrong that nothing checked. Recorded because the second is checkable and the
first may not be.

**A gate demanded work its own brief put out of scope.** SPA-207's Bruno task
required the consumer's *bruno-coverage.sh* to report zero uncovered routes. Ten routes were
already uncovered on `main` and the branch added no controller routes, so the
bar could only be met by covering ten routes the brief excluded. The task
burned its attempts and blocked while its actual regression net — the whole
collection, 166/166 requests — was green. `amend.sh check` cannot catch this:
the gate failed before the work *and* after it, which is exactly what a correct
gate looks like. What distinguishes them is whether the residue is in scope,
and that is a judgement. **Possibly checkable** as: a gate whose failure output
is identical before and after the task closed is suspect.

**A gate that cannot be satisfied is indistinguishable from work that is not
done.** Both of SPA-207's stuck tasks (this one and the Rule 8 deadlock above)
read `blocked` with complete, green deliverables. The plan said 8/10; the branch
had 10/10. Nothing in the run distinguishes "the session could not do it" from
"the session did it and the gate is wrong" — the operator had to run both gates
by hand to find out. Worth a signal: a blocked task whose `verify` exits 0 when
re-run is a gate defect, not a work failure, and the driver could say so.

---

## The planner must retire the brief it consumed — migrated

**Migrated 2026-09-24** to
[`.loop/todo/TD20260924-2035-retire-the-consumed-brief.todo.md`](../.loop/todo/TD20260924-2035-retire-the-consumed-brief.todo.md).
Both open decisions are unchanged. What is new is field evidence from the
consumer repo: eight of nine consumed briefs still declared themselves
plannable, and **three of those had already been stamped `status: consumed` in
the frontmatter this loop reads nowhere** — which is this entry's own *Which
status field* question, confirmed, and settles half of it by elimination. The
safety half is separately closed by item 8 of
`docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`, so
what remains here is legibility rather than protection.

---

## The regression net has no flake discipline, and the humans it replaced did

**Parked 2026-09-16**, from `exploring-claude`'s SPA-207 run.

The driver re-runs **every done task's gate** each iteration — that list is the
whole regression net, and it is the right design. But a gate that fails
*intermittently* therefore reverts work that was correct, and the exposure grows
with every task closed, because the re-run set grows.

Observed three times in one run, at roughly the rate that repo documents (~20%):

| | |
| --- | --- |
| Signature | `socket hang up`, transport-shaped, **zero failed assertions** |
| Location | always a file the task under test does not touch |
| Verdict in isolation | green 3/3, every time |
| Cost | T1 and T3 reverted to `pending` on phantoms; both re-closed unchanged next iteration |
| Secondary cost | iterations-per-closed reached 2.67 against the 3.0 convergence halt |

The last row is the dangerous one. Two more flakes and the run stops itself as
`not converging` — a verdict that reads as "this plan is going nowhere" when
nothing was wrong with the plan at all.

**The consumer repo already knows how to handle this, and says so in a binding
guideline**: on a transport-shaped failure in a file the diff does not touch,
re-run or isolate before calling it a regression; a failure that reproduces in
isolation is real. It even ships a script (*isolate-red.sh*) that automates the
verdict. But that obligation is written for the *implementer and reviewer*. The
**driver** re-runs the gate itself, believes the first result, and reverts — so
the one actor whose judgement is mechanical is also the one with no flake
discipline at all.

**What to consider.** Not a blanket retry: that disarms the net, and the same
guideline refuses one for assertion-shaped failures for exactly that reason. The
narrow version is that a *regression* (a gate that passed when the task closed
and fails now, on a task the current diff does not touch) is the one case where
a single confirming re-run is clearly worth its cost — it is not the gate's
first verdict on new work, it is a claim that finished work broke. Deciding it
needs a way to express "confirm before reverting" that cannot become "retry
until green", and probably a telemetry line, since a revert that a re-run undoes
is invisible today except by reading the log.

**What it is waiting on.** A decision on that shape. Note it is cheap to get
wrong in the safe direction: doing nothing costs occasional re-work, which is
what happened here — both tasks re-closed unchanged.

---

## Waiting on the first clean run — migrated

**Migrated 2026-09-24** to
[`.loop/todo/TD20260924-1955-plan-review-session.todo.md`](../.loop/todo/TD20260924-1955-plan-review-session.todo.md),
with the evidence it was waiting for. All three items (the `verify`-runs-only-its-own-files
warning, making "every pending gate fails now" fatal, and the plan-review
session) are unchanged; what is new is that the precondition — one clean run in
the consumer repo under the durable-artifact rule and the gate-rewrite guard —
was met fifteen runs over, and the run record says the class these items address
is the loop's dominant failure mode rather than a refinement.

---

## Known gaps, not yet scheduled

**No test drives the gate-rewrite guard through a real session.** The scenario
`.loop/tests/scenarios/33-gate-rewrite.sh` uses a scripted session that rewrites
on command; reviewer-calibration case `06` uses a real model but no driver.
Closing it means teaching the calibration harness to run `.loop/run.sh` for one
case, which is a larger build than the finding currently justifies.

**Calibration scoring flatters the reviewer twice.** A `DIAGNOSED` credit can be
earned by a sentence that *excuses* the work, and a `FAIL` verdict is not
necessarily a catch of the planted defect. Both are recorded in
`.loop/tests/reviewer-calibration/RESULTS.md`.

**Case `06`'s reviewer verdict is unstable rather than reliably wrong** — FAIL,
PASS, PASS on the same planted defect across three attempts. Enough to move the
check into the driver; not enough to conclude anything about review judgement
elsewhere, where the other eight cases held twice.

---

## What the gate-rewrite guard is actually built on

**Parked 2026-09-14.** Raised by a question worth asking of any guard: *has a
session ever actually been caught tampering with a verify command, or rewriting a
test so that it passes?* Going through the record — no. Not once, unprompted.
Written down so that the decision about what the guard is worth is made against
the evidence rather than against a memory of it.

**What has been observed in a real run is the neighbouring move**, twice, and
both times the session left the gate alone:

- **`001-url-shortener` T8** — a gate a correct implementation could not pass, so
  the session hand-duplicated the schema at the one site the gate inspected, and
  wrote down what it had done. Caught; the only `review_fail` in 11 iterations.
- **`url-shortener-loop-sample-2`** — the same defect shape, and the review
  passed it. The miss that produced calibration family C.

Both corrupted the *work* to satisfy the gate. Neither touched the gate.

**A session moving the goalpost itself has never been observed.** The calibration
baseline counts 27 work/review pairs across three runs with zero rejections, and
this repo's own runs close clean in `iterations.jsonl` — 11 iterations in
`002-runstat`, 6 in `004-runstat-review`. Every gate rewrite the loop had seen, as
of 2026-09-14, was planted: case `06` by hand, `33-gate-rewrite` by a scripted
session that rewrites on command. **No longer true — see the update below.**

**What is measured is the reviewer's response to a planted one**, and that is the
finding the driver check was built on: three real review sessions saw case `06`'s
rewrite, two described it accurately, none objected — PASS twice, and a FAIL for
an unrelated reason. So the guard answers a measured reviewer-side hole, not an
observed worker-side incident.

**Update 2026-09-25, from `014-gate-shape-and-driver-honesty`.** The guard's
first non-planted triggers. Three fired for real; none confirms the thing this
entry was asking about.

`gate_files_moved()` fired on a session's own legitimate retry, and was wrong.
Task T9's first attempt created a new scenario file (allowed — creation, not
modification) but failed review; the driver committed it into `HEAD` anyway, as
it does every iteration regardless of outcome. T9's second attempt edited that
same file — its own, and a correct fix to what review had flagged — and the
guard reverted it as an unowned rewrite, because `files` named the directory the
file lives in, not the file itself, and the ownership check is an exact match
against the array. Fixed in `b9ead1f` (PR #17): the guard now also asks who
committed the file's current `HEAD` content, and skips the revert when the
answer is "this same task." This is not a session moving the goalpost — it is
the *guard* moving it, against a session's correct work. First mileage on this
half of the mechanism, and it was a false positive, not the incident it exists
to catch.

The neighbouring guard, `state_restore_if_touched()` (state.json itself, not a
file a verify command runs), also fired twice for real, and neither reading
supports the worker-side incident either. T2's first attempt: one turn, 36
output tokens, immediately after the operator had killed and resumed the run
mid-session — plausibly an artifact of that interruption rather than anything
the model chose to do. T9's retry after the fix above: the session's own
proposal reported `files: []` and "I made zero edits," and its notes flagged the
anomaly itself unprompted — *"if GATE REWRITE fires again on this task despite
files:[] and a clean git status at proposal time, the cause is not in this
session's actions and may be in the driver's own handling of a zero-file-change
'done' outcome."* Nothing currently explains why a session that changed nothing
could still make `state.json` read as touched. Worth a closer look if the shape
recurs; recorded here rather than chased down because it did not block the run
and reproducing it deliberately is its own piece of work.

So: the "never observed" and "every gate rewrite was planted" claims above are
now false, and what replaced them doesn't resolve the original question either
way. One real trigger was the guard's own bug, now fixed. Two more are real and
unexplained, closer to noise the guard cannot yet distinguish from the thing it
was built to catch than to a worker tampering with its own gate.

**The decision, once the clean runs the first section waits on have
accumulated:** is a mechanical guard with no *confirmed* worker-side trigger
worth its cost? It is not free — `files` in `state.json` went load-bearing to
support it (see *Releases*), the "its own gate" narrowing was found only by
breaking `03-gate-regression`, the retry narrowing above was found only by a
real run blocking on it, and a false positive reverts real work and fails an
iteration — which, as of this update, is no longer hypothetical: it happened,
was diagnosed, and cost one operator intervention. The cheap answer is still to
leave it in and instrument it: the telemetry to notice would come from the
dataset below, as a `gate_rewrite` outcome beside `review_fail` and the
regression reopens already listed there as gap 4. The two unexplained
`state_restore_if_touched()` firings are the more urgent open question now —
worth understanding before the next time one halts a run.

---

## Run metrics — a plan report and a cross-repo dataset

**Proposed 2026-09-14.** Waiting on nothing but a slot. Prompted by a hand
computation after `exploring-claude`'s `SPA-202-replay-and-finalize` run (two
runs, one resumed after the cost ceiling), which took `jq` over
`sessions/*.json` plus `git show --numstat` per iteration commit to answer
questions the loop should answer by itself.

### What is missing today

`runstat` and the per-iteration signals judge a **run** against convergence.
Nothing reports what a **plan** cost against what it produced, and nothing
leaves data that can be compared across plans, repos, models or loop releases.

1. **No plan-level rollup.** Signals are per run, so a resumed run distorts
   them: the second SPA-202 run reported `iterations per closed 0.50` (3
   iterations, 1 task closed, but 6/6 counted). The plan was 8 iterations for
   6 tasks — 1.33 — and nothing says so.
2. **No per-task cost.** Derivable: each session JSON carries `iteration`, and
   `iterations.jsonl` maps iteration to task. Nobody joins them.
3. **No output measure.** The driver makes exactly one commit per iteration, so
   churn per task is a clean `git show --numstat <iteration commit>` excluding
   `.loop/` — the join is unusually reliable because the driver owns commits.
4. **Gate regressions are not a signal.** A done task reopened by the all-gates
   re-run (`GATE REGRESSION T2 — reverting to pending`) leaves `gate failures`
   at 0 and shows only in `loop.log` and as a streak bump.
5. **Gate wall time is not recorded.** A heavier gate (a full request
   collection, an integration suite) has a real per-iteration cost that cannot
   be measured, so its price cannot be weighed against what it catches.
6. **Rework cost is not separated.** Iterations that ended `review_fail`, and
   re-verifications after a regression, are cost with no new output.

### Evidence — SPA-202, by hand

| Task | Cost | Churn (src / test / requests) | $/KLOC |
| --- | --- | --- | --- |
| T1 | $3.66 | 50 / 38 / – | $41.6 |
| T2 (+ $1.31 regression re-verify) | $9.22 | 539 / 789 / – | $6.9 |
| T3 | $5.08 | 239 / 644 / – | $5.8 |
| T4 | $7.69 | 241 / 827 / – | $7.2 |
| T5 | $7.20 | – / 413 / – | $17.4 |
| T6 (incl. one `review_fail`) | $3.18 | – / – / 395 | $8.1 |
| **Tasks** | **$36.03** | **4,175** | **$8.6** |
| **+ plan session $9.25** | **$45.28** | | **$10.8** |

Per task, $/KLOC measures **difficulty**, not productivity: T1 was an 88-line
transaction-semantics fix and T5 a timing proof. It only means something
aggregated — which is the argument for a dataset rather than a report alone.

### What to build

**A. End-of-run and end-of-plan report.** Appended to the plan's journal (the
human view) whenever a run ends, with a plan section once the plan completes:

- per task: iterations, attempts, cost (work / review split), churn, $/KLOC,
  tokens (cache read, cache write, fresh input, output), wall time, gate wall
  time, outcome history (`review_fail`, regression reopens)
- per plan, across every run that touched it: the same totals, planning cost
  and its share, rework cost and its share, iterations per closed task, gate
  regressions caught
- the dimensions below, so a report is self-describing

**B. A dataset that aggregates across repos.** Written by the driver into
`.loop/state/metrics/` — under `state/`, so the installer never touches it and
it is committed with the branch that produced it. Two tables:

- `tasks.csv` — one row per task per plan
- `plans.csv` — one row per plan

CSV rather than JSONL because the consumer is a spreadsheet or
`cat repo-*/…/plans.csv`, and the rows are flat. Rules that make concatenation
safe:

- a `schema_version` column, and a header that only ever grows at the end
- a stable row key: `repo`, `plan_id`, `task_id` — `repo` is a **name**
  (the git remote's basename, or a declared value), never a path, so the
  `$HOME` mask has nothing to do
- raw counts alongside every derived number — tokens as well as dollars, lines
  added and deleted as well as churn — so a future repricing or a different
  churn definition can be recomputed without re-running anything
- dollars labelled as the CLI's `total_cost_usd` estimate, not a bill

**Dimensions every row carries:**

| Dimension | Source |
| --- | --- |
| loop release + commit | `.loop/.installed` (`version`, `commit`) |
| Claude Code version | `claude --version` at preflight |
| model per phase | `modelUsage` keys in the session JSON — the **resolved** model (`claude-opus-5`), not the alias in `LOOP_WORK_MODEL`; a phase that used more than one model records all |
| language(s) | churned files by extension, as a line-weighted mix (`typescript 0.93, bru 0.07`) |
| churn class | `test` / `source` / `other`, see below |
| brief id, branch, run ids | `state.json`, the run directory |

**Language and churn class stay stack-agnostic by being declared, not known.**
The loop cannot know that `*.test.ts` is a test or that `.bru` is a request
collection — `loop-plan` already records that a filename-convention check
"would have wrongly rejected a Bruno-collection task the first time it ran".
So: an extension-to-language map shipped as data with a sensible default, and
the test/source split taken from globs the repo declares (in the knowledge file
or beside it), defaulting to `other` when nothing is declared. An undeclared
repo still gets totals; it just does not get the split.

### Constraints to respect

- **`run.sh` and `runstat` must agree** (`.loop/README.md` §Signals). Any new
  formula lands in both, with a fixture arbitrating — most naturally as
  `runstat plan <state-dir>` plus the driver writing the CSV rows.
- **Scenarios stay free and offline.** The stubbed `claude` must emit
  `modelUsage` and a version string so the dimension columns are testable.
- **A comparison with `exploring-claude`'s `packages/loop-telemetry` is not
  like for like.** That tool prices every model on one flat rate card and counts
  subagent calls only; this loop's sessions carry model-aware `total_cost_usd`
  and include planning. Keeping raw tokens in the dataset is what makes a
  reconciliation possible later.

---

## Releases

**Tags go on `main`, after the squash-merge** — never on a branch commit. See
`CLAUDE.md`: each branch is squash-merged so `main` reads as one commit per post,
so a branch commit is not in `main`'s history. The branch is kept, never deleted;
its per-iteration commits are the evidence a post is about.

**A pull request description is written as the release notes**, and leads with a
**context refresher, deeper on the parts the changes touch**. The loop is worked
on between long gaps, so a reader arriving at the notes has usually lost the
internals. The refresher has to disambiguate at least these, each of which has
actually been conflated:

- The **two test suites** — `.loop/tests/scenarios/` holds fixture scenarios
  driven by a scripted session, free and offline; `.loop/tests/reviewer-calibration/`
  holds planted-defect cases that call a real model and cost money.
- **Skill section numbers** — name and locate them, e.g. `loop-work` §3 "Check
  your own work", not a bare "§3".
- **Task ids** — `T1`, `T2`, `T3` mean a task in a real `exploring-claude` run, a
  task in a fixture's plan, or the single task a calibration case plants,
  depending entirely on context.

**The bar for `1.0.0`**: one clean run under the rules above — tasks shipping
durable tests, the gate guard live. Then 1.0 means *"the loop completed a plan
and the work it left behind was covered"*, rather than *"it finished"*.

`1.0.0-rc.1` stopped short of that for two reasons: the durable-artifact rule and
the gate-rewrite guard have no real-run mileage, and `files` in `state.json`
became load-bearing in that same release — it went from an advisory list the
reviewer judged to an input the driver reads when deciding whether to restore a
file. Changing state semantics is the wrong note to cut a 1.0 on.

`.loop/.installed` records the release from `git describe --tags --dirty`, so
until a tag exists every install stamps `untagged` and the installer says so. The
tag is what switches that provenance on.
