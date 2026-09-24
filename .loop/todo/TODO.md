# Open work — index

Decisions taken and deliberately deferred, with the reasoning that produced them. Not a constraint
on any task — nothing here should be cited onto a plan. It exists because the loop is worked on in
bursts, and the reasoning behind a parked decision is the first thing to evaporate.

One file per entry, named `TDYYYYMMDD-HHMM-<slug>.todo.md`, indexed below. Each entry says what it
is waiting on, so a stale one is visible.

**Why one file per entry.** `docs/todo.md` reached 549 lines and twelve top-level sections before
this split. A single growing file makes an entry hard to cite, hard to close, and invisible to
anything that scans a directory — the same failure the consumer repo hit with unindexed documents.

## Entries

| Entry | Source | Waiting on |
| --- | --- | --- |
| [TD20260924-1720-gate-scope-and-regression-accounting](TD20260924-1720-gate-scope-and-regression-accounting.todo.md) | `exploring-claude`, SPA-220 run | Nothing — ruled on 2026-09-24; three of four are in `B20260924-1947`, see its `## Verdict` |
| [TD20260924-1955-plan-review-session](TD20260924-1955-plan-review-session.todo.md) | `docs/todo.md`, plus the nine-brief classification arc | A decision on the session's shape — its precondition is now satisfied |
| [TD20260924-2005-files-array-three-jobs](TD20260924-2005-files-array-three-jobs.todo.md) | `exploring-claude`, four runs of the classification arc | A decision on what `files` is for; cheap to defer |
| [TD20260924-2035-retire-the-consumed-brief](TD20260924-2035-retire-the-consumed-brief.todo.md) | `docs/todo.md`, plus a hand sweep of the consumer's nine briefs | Two decisions: which status field is authoritative, and plan-time vs run-end |
| [TD20260924-1725-windows-git-bash-support](TD20260924-1725-windows-git-bash-support.todo.md) | Visum (Windows machine) | Nothing — briefed as `B20260924-1640-add-windows-support` on `using-at-visum` |

## Not yet migrated

`docs/todo.md` still holds **ten** top-level entries written before this structure existed. They
are not duplicated here, so this index is **not yet a complete view of open work** — read both until
the migration lands. Migrating them is itself a TODO nobody has written yet, deliberately: the
entries should be migrated when each is next touched, not in one sweep that re-reads ten parked
decisions at once.

*§ Waiting on the first clean run* and *§ The planner must retire the brief it consumed* were both
migrated on 2026-09-24 under exactly that rule — each was next touched, so each moved, and
`docs/todo.md` carries a pointer in its place.
