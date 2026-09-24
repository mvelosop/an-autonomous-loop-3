---
name: TD20260924-2035-retire-the-consumed-brief
description: A brief that has been planned and run still declares itself plannable, and the two status fields it carries disagree — measured at eight of nine briefs in the consumer repo, three of them already stamped in the field the loop reads nowhere
status: open
created: 2026-09-24
source: migrated from `docs/todo.md` § *The planner must retire the brief it consumed* (parked 2026-09-16), with field evidence from the `exploring-claude` consumer's nine-brief classification arc, swept by hand 2026-09-24
waiting-on: Two decisions, both below — which status field is authoritative, and whether the stamp happens at plan time or run-end. The mechanism is small either way; the thin version is nearly worthless, which is why this is not built
---
# The planner must retire the brief it consumed

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
