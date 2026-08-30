# Prompt — build the `/loop-brief` skill in a consumer repo

Addressed to a Claude Code session running **in `exploring-claude`**, not here.
Every path it names resolves there.

## What this is for

The loop runs from a single file: `.loop/run.sh <brief-path>`. A repo with an
established design practice does not end its design act in a file — it ends in
tracker issues and cited artifacts, and a loop session can read neither. The
adapter between the two is a **consumer-side skill**, and this is the prompt
that builds one.

It stays consumer-side on purpose. The loop ships the contract
(`.loop/brief-template.md`), the checker (`.loop/check-brief.sh`) and the
authoring rules (`.loop/manual.md`); how a given repo's design surfaces map onto
them is that repo's business. The moment the loop names a tracker it stops being
stack-independent — the same seam `.loop/settings.json` draws for permissions.

Brief B007 records the decision. This is its worked example.

## This is a replacement, not an addition

The consumer's existing loop is being **retired**, not run alongside. So there
is no routing question — no deciding which work goes down which pipe. There is
one pipe.

`/architect` survives, because a design act is upstream of any loop and this
loop has none. Its hand-off retargets: from `/create-plan` to a brief.
Everything downstream of that — `/create-plan`, the tick driver, the four
agents, `PLAN.md` and the `plans/` archive — is what the new loop replaces.

The motivation matters here, because it constrains what a good migration looks
like. What sent the consumer looking for a new loop was **soft gates**: a review
that could pass work no command had proven. This loop's answer is that every
`verify` command is authored at plan time, before any implementation exists,
and the driver re-runs every done task's gate on every iteration. That is the
one property the migration exists to obtain, so it is the property to protect
when deciding what else to carry over.

**Replacement is a narrowing.** The new loop is a smaller machine: one brief,
one run, local commits, then it halts. It has no tracker, no pull requests, no
roadmap sequencing and no tiers. Those functions do not disappear — they lose
their home inside the loop and need one outside it, with the operator or with
the design act. Decide that before retiring anything, not after.

**Worth auditing while you do:** some of the old loop's machinery may exist
*because* the gate was soft — the verdict guards, the missed-bug logs, the
separate acceptance and pre-merge passes, the plan-section reconcilers. Against
a hard gate, some of that has nothing left to do. Not all of it, and the point
is to check rather than to assume, but a replacement is the one moment the
question is cheap to ask.

## Order of operations

Do not build this skill first. The skill's whole job is to produce a good brief,
and nobody knows yet what a good brief for *this* repo looks like.

1. Write **one brief by hand**, for a small real slice. `.loop/manual.md` and
   `.loop/examples/` are enough to do it.
2. Run it. This is the first real test of the loop on this stack — and the first
   thing that will bite is the gate list: verify commands here are `pnpm …`,
   which the loop's own fence does not allow, so they go in *your*
   `.claude/settings.json`, which the installer deliberately leaves to you.
3. **Then** build the skill, with a worked local example in hand rather than a
   template.
4. Retire the old loop once the new one has actually landed work.

One thing still to settle: **brief numbering** — whether the skill continues the
consumer's existing `docs/briefs/` sequence or starts its own.

## The prompt

````
Create a `/loop-brief` skill for this repo at `.claude/skills/loop-brief/SKILL.md`.

## The gap it fills

This repo now has the autonomous loop installed at `.loop/`. It runs from a single
file: `.loop/run.sh <brief-path>`. Our design process ends somewhere else — in
Linear sub-issues plus cited design artifacts — and the loop can read neither.
`/loop-brief` is the adapter between them.

## Read before writing anything

- `.loop/manual.md` — sections "Writing a brief" and "Deriving a brief from an
  existing design process". **That second section is the contract.** Cite it from
  the skill; do not restate it. It carries the three-row rule (what arbitrates
  lives in the brief / durable context is referenced by repo-relative path /
  tracker content must be inlined), plus strip-don't-inherit, declare-the-cut,
  and where out-of-scope comes from.
- `.loop/brief-template.md` — the shape to fill.
- `.loop/check-brief.sh` — the checks. Read the code, not just the output.
- `.loop/examples/0003-runstat-cli.md` (greenfield) and `0004-runstat-review.md`
  (incremental) — worked briefs that drove real runs.
- `.claude/skills/architect/SKILL.md` — where the input comes from. Step 6 emits
  ordered slice seeds; step 7 is the hand-off.
- `.claude/project-adapter.md` — the gate declaration. The brief's Constraints
  section points here.

## What it does

`/loop-brief <Linear issue key or slice label>`

1. **Gather.** Read the cited design artifacts — ADRs in `docs/decisions/`, notes
   in `docs/design-notes/`, the `docs/use-cases/` entry and any flow doc, the
   `docs/designer/handoffs/` bundle for UI-bearing work — plus the Linear issue
   and its parent.
2. **Dereference.** This is the skill's whole reason to exist. Everything
   downstream — planner, work *and* review sessions all read the brief — runs as
   a fresh `claude -p` with no memory, `--strict-mcp-config`, and WebFetch/
   WebSearch denied. Anything living only in Linear is invisible to all three.
   Inline it. Rewrite every surviving reference as a repo-relative path.
3. **Fill the template.** Behaviour contract from the frozen decisions, with the
   exact codes and formats a gate will assert. Worked example with concrete
   values. Out-of-scope from the sibling slices (step 6 already ordered them).
   Constraints from the stack and `.claude/project-adapter.md`. Task count.
4. **Check.** Run `.loop/check-brief.sh <path>` and fix what it reports. The skill
   is not done until it exits 0. Mark the brief `**Status:** ready to plan` — the
   checker skips anything else, so an unmarked brief passes vacuously.
5. **Present to the operator**, who owns the call and commits.

## Design constraints for the skill itself

- **Interactive, main-thread, operator-in-the-loop** — same posture as
  `/architect`, not a loop agent. Deciding what is frozen versus still open is a
  judgment call that needs to be able to ask.
- **Reference binding docs, don't copy them.** Tech guidelines in
  `docs/implementation/` and `.claude/guidelines/` reach the implementer and the
  reviewer through the brief, so duplicating them into acceptance criteria is
  waste that goes stale. But cite few and label each with *why* it is there — the
  brief is re-read every iteration by two sessions.
- **Strip mechanics.** ADRs and flow docs pin structure on purpose. The brief
  carries their decisions and drops their file layouts and class names.
  `check-brief.sh` warns above two internal symbols; that warning is a signal.
- Follow `.claude/guidelines/instruction-authoring.guidelines.md` and whatever
  `guideline-format` requires. Match the house style of the existing skills.

## Also make one small edit to `/architect`

Step 7 names `/create-plan` as the only consumer of the hand-off. It should be
able to name the loop instead, and step 6's slice seeds should record the three
things a Linear sub-issue doesn't carry but a brief needs: the frozen contract,
the worked example's concrete values, and the scope boundary. A paragraph, not a
new artifact tier — that's the difference between `/loop-brief` reconstructing
intent and transcribing it.

Do not put any of this in `.loop/`. That directory is replaced wholesale on
upgrade, and the moment the loop names Linear it stops being stack-independent.
````

## Adapting it to a different consumer

Three things are `exploring-claude`-specific and would change: the tracker
(Linear), the design-surface paths under `docs/`, and `/architect` as the
upstream act. Everything else — the dereferencing rule, the three rows, the exit
condition on `check-brief.sh` — follows from how the loop runs its sessions and
holds anywhere.
