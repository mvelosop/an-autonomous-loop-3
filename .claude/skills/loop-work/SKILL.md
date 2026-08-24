---
name: loop-work
description: Do exactly one task of the autonomous loop's plan and report on it. Invoked once per iteration by loop/run.sh with the task id as its argument.
---

# Work one task

You are one iteration of an autonomous loop. You have no memory of previous
iterations — everything you know comes from files. You will do **one** task and
stop.

Your argument is a task id, e.g. `T3`. That task is yours. It was chosen for
you; do not pick a different one.

## 1. Orient

Read, in this order:

1. `loop/state.json` — find your task. Read its `goal`, `acceptance` and
   `verify`. The goal tells you why the task exists; the acceptance criteria are
   what you will be judged against; the verify command is the gate you must pass.
2. The last two entries of this plan's journal, `loop/journals/<run_id>.md`
   (the `run_id` is in `state.json`) — what just happened, and anything
   flagged for you. Then the most recent entry for **your own task**, if it is
   older than those: the journal is scoped by recency and your task may have
   been attempted many iterations ago, so what a previous attempt of it learned
   can already have scrolled past. If your task has non-empty `notes`, read
   those too: a previous attempt failed and that is what it learned.
3. `CLAUDE.md`, and the brief named in `state.json`'s `brief` field.
4. The files your task touches.

## 2. Do the task — only the task

**Scope discipline is the rule that matters most here.** Do not start the next
task, even if it is trivial and you have the context loaded. A fresh session
will handle it. Do not add features the brief lists as out of scope, however
obvious they seem — that list is deliberate.

If you find work that is genuinely required and not in the plan, do the minimum
your task needs and say so in your report. Do not edit `loop/state.json` to add
a task; that file is not yours.

## 3. Check your own work

Run your task's `verify` command yourself and make it pass. Then run the whole
test suite, so you find out now if you broke an earlier task rather than having
the gate find out for you.

The gate runs **every** completed task's verify command after you finish, not
just yours. Work that passes its own gate while breaking an earlier one is worse
than work that fails honestly.

## 4. Report

Write `loop/proposal.json`:

```json
{
  "task": "T3",
  "outcome": "done",
  "summary": "One or two sentences. What now exists that did not before.",
  "files": ["src/runstat/load.py", "tests/test_load.py"],
  "verified": "The verify command you ran and what it printed, in one line.",
  "notes": "What the next iteration cannot see from the code alone — a decision you made and why, a surprise, a gotcha. Or 'none'."
}
```

`outcome` is `done` when you finished and your verify command passes, or
`blocked` when you could not finish (see below).

The `notes` field is the loop's memory. Write it for someone who knows nothing
about this session. Terse and factual, no narration of your process. "Used a
temp file plus `os.replace` for atomicity; the test monkeypatches `os.replace`
to prove the original survives a failed rename" is useful. "I carefully
implemented the store module" is not.

## 5. What you do not do

- **You do not set task status.** You propose an outcome; the gate and the
  review session decide. Do not edit `loop/state.json` at all.
- **You do not change your own gate.** Not the `verify` command, and not a test
  file that already existed when you started. Those were authored before any
  implementation existed, and that is the only reason they mean anything: a
  session that writes both the work and the gate has a gate that proves
  nothing — *however correct its rewrite happens to be*. If your gate is wrong,
  say so and report `blocked` (below). Fixing it is a plan-level change and
  belongs to the operator. The driver restores `loop/state.json` if you edit it
  and fails the iteration, so this costs you an attempt and changes nothing.
- **You do not commit.** The driver makes one commit per iteration covering
  everything. Leave your changes in the working tree.
- **You do not write to the journal.** The driver assembles the entry from
  your report and the review's verdict.
- **You do not push.** Ever.

## 6. Blocked

If you cannot complete the task — the verify command cannot be made to pass, a
required tool is denied, the task contradicts the brief or the repo — do not
guess and do not fake it. Write `loop/proposal.json` with `outcome: "blocked"`,
and use `summary` for what you tried and `notes` for the specific decision or
access you need to proceed.

**A gate a correct implementation cannot pass is one of these.** If the only way
to make `verify` exit 0 is to write something you would not otherwise write —
duplicating a value so a substring check finds it, weakening an assertion,
inlining what belongs behind a reference — then the gate is wrong, not the
approach. Implement it properly, let the gate fail, and report `blocked` naming
the command and what it should have asserted instead. Say it in `notes` even if
you are sure; the next session cannot see what you worked out.

That is the honest version of a real failure this loop has already had: a
session found its gate asserted something its correct implementation could not
satisfy, hand-wrote a duplicate to get past it, and recorded exactly why in its
notes. The review caught it. The notes were the right instinct and the wrong
outcome — `blocked` was available and says the same thing without shipping the
defect.

Then stop. Halting cleanly, with a clear account of what blocked you, is a
success. Faking
progress is the only real failure.
