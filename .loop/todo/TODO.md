# Open work — index

Decisions taken and deliberately deferred, with the reasoning that produced them. Not a constraint
on any task — nothing here should be cited onto a plan. It exists because the loop is worked on in
bursts, and the reasoning behind a parked decision is the first thing to evaporate.

One file per entry, named `TDYYYYMMDD-HHMM-<slug>.todo.md`, indexed below — open entries first,
then closed. An open entry says what it is waiting on, so a stale one is visible; a closed one says
what discharged it, so the reasoning survives the decision.

**Why one file per entry.** `docs/todo.md` reached 549 lines and twelve top-level sections before
this split. A single growing file makes an entry hard to cite, hard to close, and invisible to
anything that scans a directory — the same failure the consumer repo hit with unindexed documents.

## Open

Each row states the entry's own `waiting-on` **verbatim** — not a summary of it. A summary and the
file it points at are two places holding one truth, and they drifted here within a day of this index
being created (see `TD20260924-2035`, § *The second instance*). The rule has a useful side effect: a
`waiting-on` has to read correctly in both places, so it cannot say "see below".

| Entry | Source | Waiting on |
| --- | --- | --- |
| [TD20260924-1725-windows-git-bash-support](TD20260924-1725-windows-git-bash-support.todo.md) | Visum (Windows machine) | The next final version. The interim bash fix is briefed and plannable today, but it ships in the release that carries the `TD20260924-1720` work (`docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`) rather than on its own — operator decision, 2026-09-24. The residue waits on the `B008-driver-in-python` brief. |
| [TD20260924-1955-plan-review-session](TD20260924-1955-plan-review-session.todo.md) | `docs/todo.md`, plus the consumer's nine-brief arc | A decision on the session's shape — what it emits, whether it may refuse a plan, and how it avoids becoming a prose reviewer. Its precondition is satisfied; only the design is open |
| [TD20260924-2005-files-array-three-jobs](TD20260924-2005-files-array-three-jobs.todo.md) | `exploring-claude`, four runs of the classification arc | Nothing external. It needs a decision on what `files` is FOR, which is cheap to defer and expensive to get wrong, so it is recorded rather than briefed |
| [TD20260924-2035-retire-the-consumed-brief](TD20260924-2035-retire-the-consumed-brief.todo.md) | `docs/todo.md`, plus a hand sweep of the consumer's nine briefs | The brief half only — which status field is authoritative, and whether the stamp happens at plan time or run-end. The `.loop/todo/` half is settled, not pending (by hand, 2026-09-24). |

## Closed

Kept in place, never moved or deleted: the reasoning behind a parked decision is
what this directory exists for, and that does not stop being true once the
decision is taken.

| Entry | Closed | Discharged by |
| --- | --- | --- |
| [TD20260924-1720-gate-scope-and-regression-accounting](TD20260924-1720-gate-scope-and-regression-accounting.todo.md) | 2026-09-24 | The `B20260924-1714` architect act ruled on all four items; three are carried by `docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`. See that entry's `## Verdict` |

## Status

`status: open` or `status: closed`. A partially-discharged entry stays **open**
and says which part is done — `TD20260924-1725` and `TD20260924-2035` both do.
A closed entry drops `waiting-on:` and gains `closed:` and `closed-by:`.

Nothing enforces this. Four entries do not justify a check; the trigger to write
one is the next time an index row and a file disagree.

## Not yet migrated

`docs/todo.md` still holds **ten** top-level entries written before this structure existed. They
are not duplicated here, so this index is **not yet a complete view of open work** — read both until
the migration lands. Migrating them is itself a TODO nobody has written yet, deliberately: the
entries should be migrated when each is next touched, not in one sweep that re-reads ten parked
decisions at once.

*§ Waiting on the first clean run* and *§ The planner must retire the brief it consumed* were both
migrated on 2026-09-24 under exactly that rule — each was next touched, so each moved, and
`docs/todo.md` carries a pointer in its place.
