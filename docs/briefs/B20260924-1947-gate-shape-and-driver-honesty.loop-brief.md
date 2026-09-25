# Brief — three more bad gate shapes, a brief that outlived its run, and four things the driver knows but does not say

- **Status:** ready to plan
- **Starting point:** extends `.loop/run.sh` (1043 lines) and `.loop/amend.sh`
  (151 lines) as they stand. Two existing mechanisms grow: the **gate-shape
  lint** at `.loop/run.sh` lines 687–717, which today rejects two bad shapes
  and is fatal; `check()` in `.loop/amend.sh` lines 39–120, which today
  validates a plan's structure and warns on two smells; and
  `.loop/check-brief.sh`, which today validates a brief's structure and skips
  any brief not declaring itself plannable. Nothing here replaces any of them.
  No new phase, no new session, no new file format.

---

## Why this brief exists

The loop was driven through nine briefs of a single multi-slice feature in a
mature TypeScript monorepo: **15 driver runs, 94 iterations, 69 tasks closed.**
That is the first sustained production use of this loop, and it produced one
result that decides what to build next.

Seven of the 15 runs did not reach `complete`. Two were cost ceilings. The
other five halted on repeated non-progress (`stalled` ×4, `blocked` ×1), and in
**every one of the five the implementation was correct and the plan was not**:

| Task | Why no correct implementation could pass | Cost |
| --- | --- | --- |
| A | `verify` greps a key into the consumer's env-example file; that file is not in the task's `files`, so `gate_files_moved()` reverts the edit **before** the gate runs | 4 attempts, run ended `blocked` |
| B | acceptance requires a destructive data migration a binding consumer guideline forbids the loop to author | 3 attempts, `stalled` at 3/10 |
| C | `verify` demands zero uncovered request-collection routes **API-wide**; ten were already uncovered before the branch, and the plan shipped none of them | 2 attempts, `stalled` at 8/10 |
| D | two of one task's own acceptance criteria became mutually exclusive once an earlier task in the same run landed | 2 attempts, `stalled` at 6/7 |
| E | a scope guard baselined on the plan commit: once either stack closed its first task, the other stack's gate was unpassable | 1 `blocked` + **6** false task-reversions |

In all five the work session diagnosed the cause correctly, refused the
available cheats, and said so in its notes — rule 8 of `.loop/manual.md` paying
for itself, five times. In all five the driver's answer was to charge an attempt
and advance the stall streak until the run stopped. In all five an operator then
edited `.loop/state/state.json` and the run finished in **one to four**
iterations.

So the loop's sessions are not the weak link and neither is its review. **The
plan is, and nothing looks at a plan after the planner leaves.** The planner's
own checklist asks *"does every `verify` fail right now?"* — item 6 of
`.claude/skills/loop-plan/SKILL.md`. Nothing asks whether a **correct**
implementation could make it pass. Exactly one planner in the arc checked that
anyway, by building throwaway fake implementations and then breaking them 20
ways to confirm each gate caught it, and its run had no incident of this class.
Be careful how much weight that carries: **two other runs had none either, and
their planners did nothing of the kind** — three of the nine came through with
no `blocked` and no `gate_fail` at all. So the practice is a hypothesis worth
testing, not a measured result. The argument for this brief rests on the five
failures above, not on the one run that avoided them.

This brief does not build the general answer to that — an independent audit of a
plan is a judgement session whose shape is undecided, and it is parked
separately. This brief takes the part that needs **no judgement at all**: three
of the five failures above are the *same* authoring error, the lint that should
reject it already exists, and one of the three is not a matter of taste in any
degree — it is the driver's own revert rule, computable one phase earlier.

### The authoring error, named

The gate-shape lint's own comment states the method this brief follows:

> *"This is checkable precisely because the compliant form is essentially
> unique: navigate to the value and assert on it. The rule cannot be stated
> unambiguously in prose — so it is stated as a check instead."*

Its rule 2 already rejects one instance: a gate that greps a file under `src/`
*"asserts on source text rather than on what the program does."* Hold the three
cheap failures against that sentence and they are the same defect:

| Failure | What the gate asserted | What the program does? |
| --- | --- | --- |
| A | an env-example file contains a key | no — that a **file is documented** |
| E | `git diff <plan-commit> -- <other stack>` is empty | no — that **another part of the repo did not change** |
| D | one test file received **exactly one** edit | no — an **edit count** on a file |

`.claude/skills/loop-plan/SKILL.md` already forbids all three in prose, under
`### What the gate cannot carry`: a requirement that is not an assertion over
what the program produces belongs in the acceptance criteria, where the review
session rules on it by reading the diff. Three planners wrote one anyway,
because nothing mechanical said no. The fix is three more lint rules, not more
prose — and each one earns a paragraph in the SKILL section that documents the
rules already there, so a planner learns the rule rather than being rejected by
it.

**Nothing is weakened by the stricter shape.** Failure A's env-example line was
a real requirement. Moved to acceptance criteria it is still enforced, by the
actor that can actually read provenance; `.loop/tests/reviewer-calibration/`
cases `07` and `07b` measured that the review catches a defect named anywhere
it reads, including when the plan's own wording is weakened. The gate checks
what the program does; the review checks how it was built.

### The other four

Four further changes are independent of gate quality and each earned by at
least two recurrences in the arc. They do not prevent a bad plan. They make one
cost a single iteration and a truthful message instead of three iterations and
an operator who has to disbelieve the driver first.

The sharpest is a silent data loss. When a work session dies before writing
`proposal.json`, `.loop/run.sh` line 836 records
`outcome="blocked"`, `summary="work session produced no proposal"`,
`notes="none"` — and then line 979's `git add -A` **commits whatever that dead
session left in the tree**, under a message labelling the iteration `blocked`.
The next session is told nothing. In the arc this ran three times consecutively
on one task, stalling a run at 2/6 while the task's finished deliverable sat
committed in the tree; a later run hit the same shape and found three untracked
files from a dead session by accident. The driver stages that diff itself. It
can say so.

### And one refusal that is upstream of all of it

A brief is the input to everything above, and the loop has no way to tell a
spent one from a live one. `.loop/brief-template.md` ships
`- **Status:** ready to plan`, `.loop/check-brief.sh` keys its skip rule off
exactly that line, and **nothing ever retires it** — so a brief reads plannable
forever, including after its run has shipped and merged.

Measured in the consumer repo on 2026-09-24, after nine briefs had been planned
and run: **eight of the nine still declared themselves plannable.** Three of
those eight had already been marked consumed in their YAML frontmatter, which
the loop reads nowhere, so the stamp changed nothing the loop could see — the
failure this repo's own parked note on brief retirement predicted in as many
words on 2026-09-16. The consequence is not cosmetic:
`.loop/run.sh --plan-only` against a spent brief **overwrites
`.loop/state/state.json` and re-derives work that is already on the main
branch.** One brief in the arc carried a hand-written warning about that; the
other eight did not.

Retiring a brief properly is a decision this brief does not take — who stamps
it, into which field, and at what point in the run are all open, and are parked
separately. Refusing to *pretend a spent brief is fresh* needs none of those
answers, and is one existence test.

## Behaviour contract

Exit codes throughout: `.loop/amend.sh check` exits **0** clean and **1** when
it reports a problem (warnings do not fail it, as today). `.loop/run.sh`
rejects a plan by calling `die`, which exits **1**, before any iteration
spends anything.

**1. Gate-shape lint rule 3 — a gate may not inspect a file the task does not
own.** Reject a plan at the same point as the two existing rules when a task's
`verify` string contains the path of a file that (a) exists in `HEAD` and (b)
is absent from that task's `files` array, **in an inspecting position** rather
than an executing one. Inspecting means the gate reads the file's bytes —
`grep`, `cat`, `test -f`, a language-level file read; executing means the gate
hands the path to a runner, which is normal and must stay allowed. Rule 2
already draws exactly this line for `src/` and its regex is the precedent to
extend.

This is **not a heuristic**. The condition is `gate_files_moved()`
(`.loop/run.sh` line 293) evaluated at plan time: that function reverts any
`HEAD`-existing file the current task's `verify` names and its `files` does
not, and the revert runs at line 857 — **before** the gate runs at line 865. So
a task in that shape is unpassable by construction, for any implementation,
forever. The two escape hatches are both correct outcomes: add the file to
`files`, or move the claim to `acceptance`.

**2. Gate-shape lint rule 4 — a gate may not diff against any ref other than
`HEAD`.** Reject a `verify` containing a `git diff` / `git log` /
`git rev-list` against a named commit, tag, branch or merge-base. A gate is
re-run for the life of the plan, so a baseline fixed at plan time decays: the
moment any other task commits, the assertion answers a question about a diff
that no longer belongs to the session being measured. Failure E is this twice
over. A diff against `HEAD` is **not** rejected by this rule — a work session
structurally cannot commit, so `git diff HEAD` still discriminates a session's
edits from committed history, which is what makes the loop's own gate-rewrite
guard sound.

**3. The driver tells a gate which task is being worked.** Export, for the
duration of the gate sweep, the id of the task this iteration is working and
the id of the task whose gate is currently running — they differ exactly when a
gate runs as a regression check. Names are mechanics; two distinct values are
the contract, both readable from a `verify` command as ordinary environment
variables, and absent (not empty-string-ambiguous) when the driver is not
running a gate.

This retires a workaround the arc had to invent. A gate re-run as a regression
check **has no session whose scope it can speak to**: at that moment the only
uncommitted work in the tree belongs to whoever is being worked now, so a
finished task's gate read the active task's new untracked files as a stray and
reverted three finished tasks — twice, six reversions, none a real regression.
The consumer's fix was for every gate runner to re-derive the active task from
`.loop/state/state.json` by reimplementing the driver's own selection rule
(first pending task whose dependencies are all done). The driver already holds
that value. A planner should inherit it, not re-derive it.

Because a `git diff HEAD` scope guard can still be wrong for this reason while
being permitted by rule 4, `check()` in `.loop/amend.sh` gains an **advisory**
(not fatal, like the two already there) naming any task whose `verify` diffs
against `HEAD` without reading either new variable.

**4. A `blocked` task whose gate passes on re-run is reported as a gate
defect.** Today `gate_targets` (`.loop/run.sh` line 864) is every `done` task
plus the current one *only if* `outcome == "done"`. So on `blocked` the current
task's own gate never runs, and the run cannot tell *"the session could not do
it"* from *"the session did it and the gate is wrong"*. Failures B and C both
read `blocked` with complete, green deliverables; the operator had to run both
gates by hand to find out. Include the current task in the sweep when the
outcome is `blocked`, and when its gate **passes**, say so in the iteration's
warning, in the task's `notes`, and in the run-end summary: the work satisfies
the gate and the reported block is about something else. Do not change the
status transition — a `blocked` outcome still charges an attempt, because a
session's claim about its own work is still unverified. This is a signal, not a
verdict.

**5. The no-proposal path reports the working tree.** When no valid
`proposal.json` exists (`.loop/run.sh` line 834), the driver must record
whether the tree changed, and name the paths, in the `summary` that reaches
`notes`, the journal and the run-end report — instead of today's fixed
`notes="none"`. The distinction that matters to the next session is *"nothing
happened"* versus *"a session did work and died before reporting it, and the
driver has committed that work"*. Both are real; only the second is currently
invisible, and it cost a run three consecutive iterations and a stall halt.
Whether the count, the paths, or both is mechanics; that a reader can tell the
two apart is the contract.

**6. `GATE REGRESSION` names the task being worked, not only the task being
reverted.** `.loop/run.sh` line 888 prints
`GATE REGRESSION <id> — reverting to pending` and charges `<id>` an attempt.
The loop only reaches that line when `<id>` is *not* the task being worked —
that inequality is the loop's own guard on the line above — so the driver
already holds both ids and prints the one that did nothing. When the cause is
that task's **own gate** misreading another task's work, the message names the
only task that is innocent, and an operator has to disbelieve it before they
can debug it. It cost two interventions in one run. Name both ids.

**7. A repeat `blocked` on unchanged inputs halts with the first diagnosis.**
When the previous iteration for this same task also ended `blocked`, and
neither `HEAD` nor any path in that task's `files` has changed since, the retry
cannot produce new information: a memoryless session given identical inputs
produced an identical conclusion, measured at $0.47 and 126 seconds in the arc.
Halt at that point, surfacing the **first** diagnosis rather than the second.
The discriminator is *whether anything changed between the two attempts*, not
`blocked` itself — a second independent session is the cheapest possible check
on a lazy or mistaken block, which is a real argument for retrying **once when
something changed** and no argument at all when nothing did.

**8. A brief that has already been run does not read as plannable.** A run
writes its journal to `.loop/state/journals/<brief stem>.md` — the brief's own
name, which is what makes this checkable without a new field, a new convention
or a stamp. When a brief declares itself plannable and a journal of its own name
already exists, `.loop/check-brief.sh` must report it, and `.loop/run.sh` must
**refuse** to plan from it rather than overwrite `.loop/state/state.json`.

The refusal must name the journal and say what re-planning would have destroyed,
and it must be overridable — deliberately re-planning a brief after an aborted
run is legitimate, and the loop must not make it impossible. An explicit
override is fine; a silent overwrite is not. This item does **not** mark, stamp,
rewrite or retire anything: it reads two paths and compares them.

**What is mechanics, throughout.** Where each check lives inside its function;
whether the lint rules are added as regex branches beside the existing two or
factored out; the variable and scenario file names; whether the tree report in
item 5 is a count, a path list or both; the exact wording of every message,
except that items 4, 5 and 6 must each name the thing the arc showed a reader
could not otherwise tell; and the shape of item 8's override, except that one
must exist and must be explicit.

## Worked example

`.loop/amend.sh check` and the driver's plan-time lint, against a plan
containing one task in each rejected shape. `docs/todo.md` is tracked in `HEAD`
and stands in for any pre-existing file:

```
# rule 3 — inspecting a HEAD-tracked file the task does not own
{ "id": "T1", "files": ["src/thing.py"],
  "verify": "grep -q TIMEOUT docs/todo.md && uv run pytest -q tests/test_thing.py" }

  -> .loop/run.sh  exit 1
     gate shape rejected -- fix the plan:
         T1  inspects docs/todo.md, which it does not own; the driver reverts
             that file before the gate runs, so no implementation can pass

# the same gate, with the file owned — accepted, nothing printed
{ "id": "T1", "files": ["src/thing.py", "docs/todo.md"],
  "verify": "grep -q TIMEOUT docs/todo.md && uv run pytest -q tests/test_thing.py" }

  -> exit 0

# executing that path rather than reading it — accepted
{ "id": "T1", "files": ["src/thing.py"],
  "verify": "uv run pytest -q tests/test_thing.py" }

  -> exit 0

# rule 4 — a baseline that decays
{ "id": "T2", "verify": "test -z \"$(git diff --name-only 4c911d7 -- docs)\"" }

  -> .loop/run.sh  exit 1
     gate shape rejected -- fix the plan:
         T2  diffs against 4c911d7 rather than HEAD; a gate re-runs for the
             life of the plan and that baseline decays on the next commit

# the same assertion against HEAD — accepted by the lint, advised by amend
{ "id": "T2", "verify": "test -z \"$(git diff --name-only HEAD -- docs)\"" }

  -> .loop/run.sh   exit 0
     .loop/amend.sh check  exit 0, with
       ! T2 diffs against HEAD without reading the active-task id; during
         another task's iteration the only uncommitted work is that task's
```

A brief whose run already happened. `.loop/state/journals/0003-runstat-cli.md`
exists in this repo and `docs/briefs/0003-runstat-cli.md` is the brief it came
from:

```
.loop/check-brief.sh docs/briefs/0003-runstat-cli.md
  -> exit 1
     ✗ already run — .loop/state/journals/0003-runstat-cli.md exists; this
       brief declares itself plannable and is not

.loop/run.sh --plan-only docs/briefs/0003-runstat-cli.md
  -> exit 1
     refusing to plan: .loop/state/journals/0003-runstat-cli.md already exists.
     Planning would overwrite .loop/state/state.json and re-derive work this
     brief already produced. Re-plan deliberately with <the override>.

# the same brief, with the override, and a brief that has never been run
  -> exit 0, plan written
```

Run-time, one iteration each. A session that leaves no proposal after editing
two files, where today the journal records `notes: none`:

```
   work session left no valid proposal
   T3 blocked — the working tree changed: 2 file(s) (src/thing.py,
      tests/test_thing.py); the driver has committed them under this iteration
```

A blocked task whose own gate passes, and a regression charged to an innocent
task during another's iteration:

```
   work session reported blocked
   T4 GATE PASSES while the session reports blocked — the work satisfies its
      own gate; the block is about something else. Read the proposal.
   GATE REGRESSION T1 — reverting to pending (failed during T4's iteration)
```

Every one of these is a scenario in the loop's own stubbed-`claude` suite under
`.loop/tests/scenarios/`, following the shape of the 33 already there: plant
the condition, run, assert the exit code and the message. Rule 3's fixture must
include the accepted cases above, not only the rejected one — a check nobody
tried to break is a check nobody has tested, and in the arc a first attempt at
a similar check reported four passes it should have failed because an unquoted
shell value did not word-split under the author's shell.

## Out of scope

- **A plan-review session.** The independent audit of a plan's gates — the
  general answer to the failure class this brief's first three items sample —
  is parked with its own evidence and needs a decision on its shape first.
  Nothing here adds a session, a phase or a model call.
- **Making `"every pending gate fails now"` fatal.** Already computed as an
  advisory in `check()` and deliberately not fatal: a task that *extends*
  existing coverage legitimately presents a partly-green gate. Unchanged here.
- **Flake discipline for the regression net.** A gate that fails
  intermittently reverts correct work; the arc saw it three times in one run,
  and it is parked separately because the fix needs a decision on how to
  express *"confirm before reverting"* without it becoming *"retry until
  green"*. Item 6 makes its message honest; it does not change what reverts.
- **Widening the revert guard to cover files a `verify` does not name.** The
  guard is narrow on purpose — widening it would have the driver restore a file
  a later task legitimately broke, hiding the regression the gate re-run exists
  to catch. Item 1 acts at plan time precisely so the runtime guard need not
  change.
- **A cumulative cost ceiling across resumed runs.** `LOOP_COST_CEILING` is
  per-run, so a run stopped for an operator amendment silently gets a fresh
  budget. Real, and a different change: it needs somewhere to persist spend per
  *plan*.
- **Retiring or stamping a consumed brief.** Item 8 refuses to plan from a
  brief that has been run; it does not mark one. Who stamps it, into which of
  the two status fields, and whether that happens at plan time or run-end are
  open decisions parked in
  `.loop/todo/TD20260924-2035-retire-the-consumed-brief.todo.md`, and a thin
  stamp written at the wrong moment is close to worthless. Item 8 needs none of
  those answers, which is exactly why it is here and the rest is not.
- **Collapsing the two status fields.** The body `**Status:**` line and the YAML
  frontmatter `status:` disagree in practice and only the first is read by
  anything in the loop. Same parked decision.
- **Retiring `docs/todo.md`'s remaining entries** into `.loop/todo/`.
- **Anything in the consumer repository.** Its gate runners, its knowledge
  roots and its own guidelines are its business; this brief changes only the
  loop.

## Constraints

- Bash and `jq` only, as the driver already is. No new runtime dependency, no
  network, no external service.
- `.loop/run.sh` must stay a single file, and every check added to it must run
  in the plan phase or inside the existing gate sweep — no new phase.
- **Fast.** The three lint rules run once per plan, over strings already in
  memory. Items 3–7 add at most one `git` invocation per iteration. Nothing
  here may add a per-gate cost, because gates re-run every iteration.
- The driver stays the only actor that makes a status transition. Items 4 and 5
  add signal; neither may change a status, and item 7 halts the run rather than
  deciding a task's fate.
- Every message a human reads must survive `mask()` — no absolute paths, no
  usernames.
- Repo-relative paths everywhere. No absolute paths in any file or commit
  message.
- **Every task here adds a scenario, and that moves a number five documents
  claim.** `.loop/tests/check-docs.sh` computes the suite size as
  `scenarios + 3` and fails if any document states a different count — so the
  first task to land a scenario turns the broad gate red on a claim it did not
  touch, in `README.md` (twice), `.loop/README.md` and `.loop/manual.md`
  (twice), plus the two briefs that name the scenario count. At the time of
  writing the correct values are **44 checks** and **41 scenarios**, T1, T2,
  T3, T4, T5, T6 and T7 having already landed the first seven of the nine;
  each task after it adds one more of each.

  Named here because it is precisely this brief's own subject: a gate failing
  for something the task did not cause. It is not a defect — the count check
  exists because four documents once drifted to three different numbers in two
  days — so do not weaken or exempt it. Update the claims in the same commit as
  the scenario, and expect to do it in every task.

## Shape

**Eight to ten tasks**, each independently verifiable by a single command.

The three lint rules (items 1, 2 and the advisory half of 3) are naturally one
task each: same insertion point, but each needs its own planted fixture and
each carries its own paragraph into `.claude/skills/loop-plan/SKILL.md`. Items
4–7 are one task each, and item 3's env-var half is one, which is seven. Item 8
is one more, and it is the odd one out in placement: its check belongs to
`.loop/check-brief.sh` and its refusal to `.loop/run.sh`, so it touches two
files no other task here touches, and nothing else depends on it — take it first
or last, not in the middle. Split item 1 if the inspect-versus-execute
discrimination wants its accepted cases gated separately from its rejected one.

Items 1, 2 and 8 are one family — **a plan-time refusal computable from repo
state that the loop was not computing** — and items 4–7 are the other. A plan
that interleaves them will re-read the same two functions repeatedly; group
them.

Every task's durable artifact is a scenario under `.loop/tests/scenarios/`
registered with `.loop/tests/run-all.sh`, and its gate runs that scenario. The
lint tasks additionally have a cheap direct gate — a crafted `state.json` and
an asserted exit code — because a scenario that boots the whole driver is the
slower path to the same fact.

One task must carry a gate broad enough to notice a regression no other names:
the existing suite (`.loop/tests/run-all.sh` plus `uv run pytest -q`) is that
gate, and it is cheap enough to end every gate with. Three of these changes
touch code paths the existing 41 scenarios already exercise — a plan whose
gates only run its own new scenarios would let this brief break the driver's
existing behaviour and close green.
