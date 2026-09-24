---
name: TD20260924-2035-retire-the-consumed-brief
description: Two directories carry a lifecycle field that nothing retires, so both accumulate entries that read live and are not — `docs/briefs/` measured at eight of nine stale, and `.loop/todo/` at one closed entry plus an index row disagreeing with its own file
status: open
created: 2026-09-24
source: migrated from `docs/todo.md` § *The planner must retire the brief it consumed* (parked 2026-09-16), with field evidence from the `exploring-claude` consumer's nine-brief classification arc, swept by hand 2026-09-24
waiting-on: The brief half only — which status field is authoritative, and whether the stamp happens at plan time or run-end. The `.loop/todo/` half is settled and enforced by `.loop/tests/check-todo.sh` (2026-09-24).
---
# A consumed document is not retired, in either directory

**This entry was widened on 2026-09-24.** It was written about briefs. The same
defect was then found one directory over, in `.loop/todo/` itself, which makes
the diagnosis the general thing and the brief the first instance:

> **A document carrying a lifecycle field, with no mechanism that retires it,
> accumulates entries that read live and are not.** The reader cannot tell
> without opening each one, which is the state both directories reached.

The two instances are not equally hard, and separating them is what unblocks
the cheaper one. See `## The second instance` below; the original brief-side
entry follows unchanged.

## The planner must retire the brief it consumed

A brief that has been planned still reads `ready to plan`. Nothing marks it
spent, so the state of a `docs/briefs/` directory several runs in does not say
which briefs are live — a question anyone opening it has, and which currently
needs git archaeology to answer.

**What the planning session should do**, at the end of a successful plan:

1. **Stamp the brief consumed.**
2. **Append a `## Consumed` section** recording what consumed it — the run id,
   the branch, and anything a future brief on the same surface would want.

The consumer side already has this convention for a *different* document: its
architect briefs carry a `## Consumed` section, opened by a blockquote saying
the section must be completed by the consuming act, then the date, the act, and
— most of the value — the **drift it found** between what the brief assumed and
what was actually shipped. Loop briefs have no equivalent, and the planner is
the session in the same position.

## Two things to settle first

**Which status field.** There are two, and they disagree. `.loop/check-brief.sh`
keys off the **body** line (`**Status:** ready to plan`). The YAML frontmatter
`status:` is read **nowhere in the loop** — `draft` / `consumed` / `superseded`
are a consumer convention only. So stamping the frontmatter alone changes
nothing the loop can see: a brief marked `status: consumed` there is still
checked, and still plannable, because its body still says otherwise. Whatever
the planner writes has to be the field something reads, or it is decoration.
Either collapse the two, or have the planner write both and say which wins.

**When, and therefore what it can say.** The planner runs once, *before* the
run. At that moment the only honest content is "consumed by run X on branch Y" —
the interesting part (what shipped, what the brief got wrong, what the run
discovered) is not known until the run ends. The architect-brief precedent writes
its `## Consumed` *after* the act, which is why those sections carry real
findings rather than a timestamp. So either the planner writes a thin stub and
something at run-end enriches it, or the stamping belongs at run-end and not to
the planner at all. Worth deciding before building, because the thin version is
nearly worthless and the rich version is not the planner's to write.

## Field evidence — the consumer repo, swept by hand 2026-09-24

Nine loop-briefs, all planned, all run, all merged. The sweep measured what this
entry predicted eight days earlier, and one thing it did not.

| | Count |
| --- | --- |
| Briefs still declaring themselves plannable in the **body** line | **8 of 9** |
| …of which had **already** been stamped `status: consumed` in frontmatter | **3** |
| Briefs carrying any record of what consumed them | **1** |
| Frontmatter values outside the declared `draft \| consumed \| superseded` set | **2** (`done`, `ready to plan`) |

**The three matter most.** Three briefs had been conscientiously marked
`status: consumed` by an operator who then moved on — and the loop could not see
it, exactly as the *Which status field* question above says. That is this entry's
prediction confirmed in the field, and it settles one half of the decision by
elimination: **a stamp that only touches frontmatter is not worth building.**
Whatever is built must write the body line, or collapse the two so there is only
one line to write.

**The vocabulary drifted, which the entry did not anticipate.** With no mechanism
stamping anything, operators invented values — one brief read `done`, another
`ready to plan`, neither in the declared set. An unenforced enum does not hold
for nine instances. If the planner is to write this field, the accepted values
belong somewhere a check can read them.

**What it actually cost.** Nothing, so far — nobody re-planned from a spent
brief. But exactly one of the nine carried a hand-written warning explaining
why that would hurt (`.loop/run.sh --plan-only` overwrites
`.loop/state/state.json` and re-derives merged work), and the operator had
written it themselves after thinking it through once. The other eight were one
mistaken command away from it, silently.

**That hazard is now closed independently of this decision**, by item 8 of
`docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`: a
brief declaring itself plannable while a journal of its own name already exists
is reported by `.loop/check-brief.sh` and refused by `.loop/run.sh`, with an
explicit override. That needs no field, no stamp and no vocabulary — it reads two
paths. So the **safety** half is handled and this entry is now purely about
**legibility**: making a `docs/briefs/` directory readable without git
archaeology, and carrying a run's findings back onto the brief that asked for
them.

Which lowers its urgency and sharpens its value. It is no longer protecting
anything; it is the loop-side counterpart of the `## Consumed` convention that
has demonstrably been the consumer's most useful brief section.

## The second instance — `.loop/todo/` itself, settled 2026-09-24

Found while asking whether `docs/briefs/` and `.loop/todo/` were redundant. They
are not — a brief is buildable now and is consumed by `loop-plan`, while an entry
here is explicitly *"not a constraint on any task"* — but both had grown the same
stale-lifecycle problem, and this directory had it within a day of being created.

**What was wrong.** `TD20260924-1720` had been fully ruled on — all four of its
items dispatched, three into a brief — and still read `status: open`. And the
index row for `TD20260924-1725` said *"Nothing — briefed"* while that entry's own
frontmatter said `status: briefed — interim fix ready to plan; residue open`. So
the directory titled **Open work — index** contained one entry that was not open,
and one row that disagreed with the file it pointed at.

That second one is worth naming separately: a summary in an index and a field in
the file are two places holding one truth, and they drifted within a day.

**Why this half is easy and the brief half is not.** Both open questions above
are brief-specific, and neither survives the move:

| | `docs/briefs/` | `.loop/todo/` |
| --- | --- | --- |
| *Which status field* | **two** — a body line the loop reads and frontmatter it does not | **one**; nothing to reconcile |
| *When, and by whom* | a session must write it, and the planner runs before the run knows anything worth recording | the operator closes it by hand, at the moment they decide; no automation, no timing problem |

So the shared part is the **diagnosis**, not the fix. Recording that is most of
this entry's value: it is why the brief half is still parked and this half took
ten minutes.

**The convention applied here** — minimal, and deliberately the same rule the
consumer repo settled for its own briefs on the same day, that a consumed
document stays where it is and is marked rather than moved:

- `status: open` or `status: closed`. A partially-discharged entry stays `open`
  and says which part is done.
- A closed entry replaces `waiting-on:` with `closed:` (a date) and `closed-by:`
  (what discharged it — a brief path, a commit, or `dropped: <reason>`).
- `TODO.md` lists open and closed separately, so **Open work — index** is true to
  its name, and an entry's row states its `waiting-on` **verbatim** rather than
  summarising it. The `1725` drift came from a summary.
- Files stay in place. Nothing is moved or deleted; the reasoning behind a parked
  decision is the thing this directory exists to keep, and that is no less true
  once the decision is taken.

**Not built — and the trigger fired before the ink was dry.** The plan was: no
check, because four entries do not justify one, and the honest trigger would be
*the next time an index row and a file disagree*.

That happened **in the same session**, within minutes. Widening this entry
changed its own `waiting-on`, the index row still carried the previous wording,
and a throwaway consistency script written to confirm the retirement caught it —
`BAD … verbatim=False` — on the one entry that exists to describe this failure.
Nothing else would have; the drift was a clause, and both versions read fine.

So the check is now **earned**, and it is small. Read each `TD*.todo.md`'s
frontmatter; assert that a `closed` entry appears under `## Closed` with
`closed:` and `closed-by:` and no `waiting-on:`, that every other entry appears
under `## Open` with a `waiting-on:`, and that each open entry's `waiting-on`
string appears **verbatim** in the index. That is the whole thing: five
assertions over frontmatter, no judgement, and a fixture is a directory with one
deliberately-drifted row.

One design note earned by writing the throwaway: the verbatim rule forces a
`waiting-on` to read correctly in **both** places, so it cannot say "see below".
That is a small constraint on how these are written, and it is the reason the
rule is verbatim rather than "a faithful summary" — a summary is what drifted.

**Written, 2026-09-24**, as `.loop/tests/check-todo.sh` — beside
`.loop/tests/check-docs.sh`, whose shape it copies: an optional root argument so
a scenario can point it at a planted tree, a skip on `.loop/.installed` because
this directory ships to consumers who do not own it, and a skip when there is no
`.loop/todo/` at all. Wired into `.loop/tests/run-all.sh` beside the other two
free offline checks. Its fixture is `.loop/tests/scenarios/34-todo-index-drift.sh`,
nine assertions over a planted directory: the consistent case passes, and each
defect is one thing moved in a tree a reader would call fine.

**The fixture earned its keep immediately, on itself.** The case for *a closed
entry that still says what it awaits* appended `waiting-on:` to the end of the
file — after the body, where a frontmatter parser never looks — so it asserted
nothing and reported `ok`. Writing the check found nothing; writing the attempt
to break it found that one of the breaks was not a break. That is the run
journal's own lesson at one more level down: **a check nobody tried to break is
a check nobody has tested**, and a fixture is a check.

One thing the check does not do, deliberately: it does not enforce a status
*vocabulary*. `closed` is the only value with mechanical consequences; everything
else is the open case, including a sentence describing a part-done entry. Two of
the current entries use exactly that, and turning `status:` into an enum would
reject them to no purpose. The brief half of this entry is where a vocabulary
question actually lives, because there a session has to write the value.
