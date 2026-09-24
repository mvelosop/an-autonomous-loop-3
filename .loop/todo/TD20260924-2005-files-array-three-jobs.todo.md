---
name: TD20260924-2005-files-array-three-jobs
description: A task's `files` array does three unrelated jobs — declare durable artifacts, seed a plan-time ownership warning, and key the runtime revert guard — and sessions across three runs edited files outside it with no consequence, because the guard only protects the paths a verify command happens to name
status: open
created: 2026-09-24
source: the `exploring-claude` consumer's nine-brief classification arc — per-task notes across four runs, none of which reached an `## Insights` section
waiting-on: Nothing external. It needs a decision on what `files` is FOR, which is cheap to defer and expensive to get wrong, so it is recorded rather than briefed
---
# `files` is three things, and nothing validates it as any of them

Recorded because the arc kept walking past it. No single incident is expensive;
the pattern is, and it is invisible from any one run.

## The three jobs

1. **A declaration of what outlives the run.**
   `.claude/skills/loop-plan/SKILL.md` § *What the gate does not outlive* makes
   this the point of `files`: a task that ships behaviour must list something
   durable, and its gate must run it. Explicitly **not** enforced — *"checking
   it mechanically means matching filename conventions, which is stack
   knowledge the driver deliberately does not carry."*
2. **Input to a plan-time ownership warning.** `check()` in `.loop/amend.sh`
   flags a task assigned a file that only *another* task's gate runs — a gate
   that task can weaken while not being measured by it.
3. **The key to the runtime revert guard.** `gate_files_moved()`
   (`.loop/run.sh` line 293) reverts any modified file that exists in `HEAD`,
   is named inside the task's `verify` string, and is absent from `files`.

Job 1 says `files` is a *promise about the future*. Job 3 treats it as a
*prediction of the diff*. Those are different documents, and no task in the arc
could satisfy both.

## What the arc did with it

Sessions edited files outside their `files` array **routinely**, and were
right to — the acceptance criteria required work the planner's list had not
anticipated. Four runs, at least eight tasks. Each session recorded it, and
each cited the previous one as precedent:

- *"Files touched beyond the task's listed three … the acceptance list requires
  editing"* — then the next task: *"not in this task's declared `files` but
  required — same precedent [the previous task] set for its own two hook
  files."*
- One task widened **six** files the declared list did not name, and checked its
  work by re-running the three earlier tasks' gates by hand.
- The explicit one, which is what makes this an entry rather than an
  observation: *"Two files outside this task's declared `files` needed forced
  edits to keep the regression net green … **neither is named as a literal
  substring inside the task's `verify` command string, so the driver's
  `gate_files_moved()` restore-on-tamper check does not touch them.**"*

That last session was not cheating. It read the guard, understood its keying,
and reported honestly that the guard did not apply. But it names the property:
**the guard protects exactly the files a verify command happens to mention, and
nothing else.** Coverage is a coincidence of how the gate was phrased.

And the same keying, from the other side, produced the arc's single most
expensive plan defect: a task whose `verify` named a file its `files` did not,
so the driver reverted every correct edit before running the gate — four
attempts, a run ending `blocked`, zero possible implementations. That half **is**
briefed, as a fatal plan-time lint rule in
`docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`,
because it needs no decision. This entry is the half that does.

## Why not just widen the guard

Because the narrowness is deliberate and the reasoning still holds: widening it
to any modified file would have the driver restore a file a later task
legitimately broke, hiding the regression that re-running every done task's gate
exists to catch. The comment at `.loop/run.sh` line 855 says so. So the answer
is not "protect more files".

## The decision to make

Pick what `files` is, and give the other two jobs their own mechanism:

- **If it is the durability declaration** (job 1), then it should not key a
  revert at all, and job 3 wants a different discriminator — most obviously the
  one the loop already trusts elsewhere: a work session structurally cannot
  commit, so *"modified and uncommitted"* identifies a session's edits without
  needing a list at all. That is the same insight that moved the gate-rewrite
  guard from the plan commit to `HEAD`.
- **If it is a prediction of the diff** (job 3), then it has to be maintainable
  mid-run, and today only the operator can change it — the one thing a session
  is structurally forbidden from touching is `.loop/state/state.json`. Three of
  the arc's five halts ended with an operator editing exactly that file.
- **If it stays both**, then the honest minimum is that the run-end report names
  every task whose actual diff fell outside its `files`, so the drift is at
  least visible. Cheap, and it would have surfaced this pattern in one run
  rather than four.

**Cost of deferring:** low and steady. Nothing broke. What it buys an attacker
or a careless session is the ability to weaken a gate it is not measured by,
which `check()`'s advisory already half-covers, and what it costs the operator
is that `.loop/state/plan.md`'s `files` column is not a true account of what a
run changed.
