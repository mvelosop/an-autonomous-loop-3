# Open work

Decisions taken and deliberately deferred, with the reasoning that produced
them. Not a constraint on any task — nothing here should be cited onto a plan.
It exists because the loop is worked on in bursts between blog posts, and the
reasoning behind a parked decision is the first thing to evaporate.

Each entry says what it is waiting on, so a stale one is visible.

---

## Waiting on the first clean run

**Parked 2026-09-11.** All three wait on the same thing: **one clean run in the
`exploring-claude` repo under the durable-artifact rule and the gate-rewrite
guard.** Both shipped in `1.0.0-rc.1` and neither has executed in a real
iteration. Tuning gates against no evidence of how the new rules behave is the
thing to avoid.

They are listed in the order they unlock each other.

### 1. Warn when a task's `verify` runs only files the task itself ships

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

### 2. Enforce "every pending gate fails now" in the driver

Already computed in `.loop/amend.sh` as an advisory. Cannot be made fatal until
(1) lands: the extension case above legitimately presents a partly-green gate,
and a fatal check would reject a correct plan.

### 3. A plan-review session

The missing third oracle. **Nothing independent audits a gate.** The review
session audits tests and structurally cannot audit gates — the gate is the ruler
it measures with, and `loop-review` opens by telling it the gate is settled.
What looks at a verify command today is: the planner's own self-check, two narrow
mechanical checks in `.loop/run.sh` (a gate must exist; one specific bad shape is
refused), an advisory in `.loop/amend.sh`, and a human reading `plan.md`.

Both of the loop's real gate incidents were gate-quality problems:

- **url-shortener T8** — the gate asserted the re-serialised text of a parsed
  structure contained a property name, but the correct output is a `$ref`. A
  correct implementation could not pass. This produced the gate-shape check and
  the whole second family of the reviewer calibration.
- **B0006** — roughly 97 KB of verify assertions, all passing, none of them
  wrong, several sharper than a hand-written test. The run still shipped nine
  HTTP routes with no coverage. The gates were *strong* and were still the wrong
  deliverable, which is the uncomfortable version: quality and sufficiency are
  different axes and only the second one mattered.

The economics are unusually good — once per run, not per iteration, against the
artifact that sets the bar for every iteration after it. And "would this gate
fail a non-implementation?" is a **substance** question about the gate, the class
review sessions demonstrably handle well. `--plan-only` already carves out the
slot; today the only thing filling it is the operator.

One encouraging data point: calibration cases `07` and `07b` weaken the plan's
acceptance criteria and its goal respectively, and the reviewer caught the defect
anyway in both runs, taking the invariant from the code's own docstring once the
plan stopped naming it. `.loop/tests/reviewer-calibration/RESULTS.md` concludes
**any one source is enough**. So there is resilience to a weak plan; it is just
not an audit of one.

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
