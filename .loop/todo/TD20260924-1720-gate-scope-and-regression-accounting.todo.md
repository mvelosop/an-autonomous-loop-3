---
name: TD20260924-1720-gate-scope-and-regression-accounting
description: Four loop-mechanism defects the exploring-claude SPA-220 run surfaced — a scope guard that cannot tell whose diff it is reading, a regression message that names the innocent task, `blocked` accounted as pure loss, and journals nothing downstream reads
status: open
created: 2026-09-24
source: the `exploring-claude` consumer repo — the `## Insights` section of its run journal for `B20260919-2331-implement-spa-220` (that repo's `.loop/state/journals/`, not this one's)
waiting-on: Nothing. The `B20260924-1714` architect act ran 2026-09-24 and ruled on all four — see `## Verdict` at the end. Items 2, 3 and 4's mechanism half are carried by `docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`; item 1 is carried in a better form than this entry proposed; item 4's knowledge-root half belongs to the consumer repo
---
# Gate scope, and what the driver does with a regression

Four things, from one run. The first is the only one that is fully diagnosed and already has a
working fix to lift; the other three are recurrences with evidence.

## 1. A scope guard cannot tell whose diff it is reading

**The defect.** A plan's gate runners each opened with a scope check — "this task touches
`apps/api` and nothing else" — expressed as `git diff --name-only <plan-commit> -- <other stack>`.
That is correct while the task is in flight and wrong every iteration after, because **the driver
re-runs every done task's `verify` each iteration.** It fired twice, in two distinct forms:

- **Form A — the plan-commit baseline.** Once either stack closed its first task, the other stack's
  gate became unpassable. A work session did its whole task correctly, could not get a green verify,
  and reported `blocked` with an exactly-correct diagnosis of the gate defect. Cost: $0.64 discarded
  plus an operator intervention.
- **Form B — the `HEAD` baseline, which is the non-obvious half.** Baselining on `HEAD` instead fixes
  the committed case, because a work session structurally cannot commit. It does **not** fix the
  regression re-run: at that moment the only uncommitted work in the tree belongs to *whoever is
  being worked now*, so a backend gate read the active frontend task's three new untracked files as
  a stray and reverted three finished tasks a second time.

**The general form**, which the earlier statements of this lesson (SPA-208 journal Lesson 1,
B20260917-1546 Lesson 1) do not cover: **a gate re-run as a regression check has no session whose
scope it can speak to**, so any scope assertion it makes is answering a question nobody asked.

**The fix, already working.** Each runner derives the active task from `state.json` using the
driver's own selection rule — first pending task whose dependencies are all done — and runs the
scope check only when that is its own task. Implemented ad-hoc in the consumer repo's plan oracles
at `c1d5895d` and `233f4784` (exploring-claude). Nothing is weakened: every task's own gate still
asks the question of its own session, which is the only session it can speak to.

**What belongs here rather than there.** The fix currently lives in one plan's oracle scripts,
which means the next planner re-derives it or repeats the defect. This has now recurred across
**three** runs. Candidates, in increasing order of ambition:

1. Ship the discriminator in the loop's gate scaffolding so a planner inherits a helper, not a
   paragraph.
2. Have the driver pass the active task id to the `verify` command (an env var), removing the need
   to re-derive it from `state.json` at all. Cleaner, but changes the driver's contract with gates.
3. A `.loop/amend.sh check` warning when a task's `verify` script references paths that appear in
   **another** task's `files` — a mechanizable smell for exactly this class.

## 2. `GATE REGRESSION` names the innocent task

The driver prints `GATE REGRESSION T1 — reverting to pending` and charges T1 an attempt. When the
cause is T1's *own gate* misreading another task's work, that message names the one task that did
nothing wrong, and the operator has to disbelieve it before they can debug it. It cost two
interventions across this run to see past.

Minimum: when a gate fails during another task's iteration, say so in the message — the driver
already knows both ids (`"$id" != "$task"` is the condition it branches on).

## 3. `blocked` with a correct diagnosis is still accounted as pure loss

Recorded in the SPA-208 journal (Lesson 5) and again here. A session that hits an unsatisfiable
gate, refuses the available cheats, diagnoses the cause correctly and reports `blocked` is doing
exactly what `.loop/manual.md` rule 8 asks for — and the driver burns an attempt, advances the
no-progress streak toward `LOOP_STALL_LIMIT`, records `review: skipped`, and mentions none of it in
the run-end signals block. The loop's metrics punish the behaviour its contract asks for.

Both times, the diagnosis was correct and was the most valuable artifact of its iteration. An
outcome that is *correct refusal* wants its own status, distinct from *failure to progress*.

## 4. Journals are not a knowledge root, so lessons are not inherited

The sharpest finding, and the one that explains why 1–3 recurred at all.

The SPA-220 planning session **did** read the prior run's journal: its oracle `README.md` credits
that journal's Lesson 4 by name and implements it. It then wrote the defect that is Lesson **1** of
the same journal, four lines below, recorded first and stated more explicitly. It did not fail to
read; it applied one lesson and walked past its neighbour.

The mechanism is structural. Lesson 4 had a **code** consequence the planner could copy from a file
it was already reading (the previous plan's oracle directory). Lesson 1 had only a **prose**
consequence, and the consumer repo's `.claude/loop-knowledge.md` declares eight knowledge roots of
which `.loop/state/journals/` is not one. So: **a lesson that left an artifact gets inherited; a
lesson that left a paragraph does not.**

Two consequences for the loop, not just for one consumer:

- The loop's own guidance on knowledge roots (`manual.md` § *Telling the planner where your
  knowledge lives*) should say that a repo's own run journals are a candidate root, and what a
  useful index over them looks like. Today nothing suggests it.
- Insight capture is operator discipline, not a loop step: across nine runs of the classification
  arc, only the **last three** journals have a `## Insights` section at all. If per-run insight
  capture is worth having, it needs a prompt in the loop.

---

## Verdict — the `B20260924-1714` architect act, 2026-09-24

The act mined all nine journals of the arc (not only the three with an
`## Insights` section) and put these four beside everything else it found. All
four survived. What changed is **item 1's shape** and **where item 4 splits**.

| | Ruling |
| --- | --- |
| **1** scope guard cannot tell whose diff it is reading | **Briefed, in a better form than the three candidates here.** Candidate 2 — the driver passing the active task id to `verify` — won, and became item 3 of the brief: the driver already holds the value the consumer's runners re-derived from `state.json`, so a planner should inherit it. Candidate 1 (ship the discriminator in gate scaffolding) is then unnecessary, and candidate 3 (`amend.sh` warns on a `verify` naming another task's `files`) was replaced by two **fatal lint rules** that catch the cause rather than smell it — a gate may not diff against a ref other than `HEAD`, and may not inspect a file the task does not own. |
| **2** `GATE REGRESSION` names the innocent task | **Briefed verbatim** as item 6. One line; `$task` is already in scope at `run.sh:888`. |
| **3** `blocked` with a correct diagnosis accounted as pure loss | **Briefed in two halves.** Item 4 makes a blocked task's own gate run so the driver can say *"the work satisfies its gate; the block is about something else"* — this repo's own parked idea, now with two more incidents behind it. Item 7 adds the mechanizable discriminator from the arc's later run: a repeat `blocked` on unchanged inputs halts with the first diagnosis. A distinct **status** for correct refusal is deliberately *not* briefed — a session's claim about its own work stays unverified, so the attempt is still charged; what was missing was signal, not absolution. |
| **4** journals are not a knowledge root | **Split, and the loop half is out of scope for the brief.** The consumer's `.claude/loop-knowledge.md` is the consumer's to fix and was handed to its documentation-restructuring brief. The `manual.md` guidance half is prose in the one place prose belongs and rides with that consumer-side change rather than opening a loop-brief for a paragraph. The second bullet — insight capture as operator discipline — was **decided against automating**: see `TD20260924-1955-plan-review-session.todo.md`. |

**What the act added that this entry did not have.** The four items above read as
four defects. Across fifteen runs they are better read as one: **five of the
arc's seven premature halts were an unsatisfiable plan, correctly diagnosed,
and none was a wrong implementation.** Two failures this entry never saw are the
sharpest evidence for that — a `verify` that grepped a file absent from its
task's `files`, unpassable by construction for four attempts; and a gate
demanding a repo-wide invariant the plan had not touched, blocked twice. Both
are plan defects with no judgement in them at all, which is why the brief leads
with lint rather than with accounting.
