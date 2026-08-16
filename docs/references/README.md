# References

Verbatim copies of design notes from the `exploring-claude` repo, vendored here
so this repo's briefs cite something a reader can open — including a reader who
does not have the source repo.

**Do not edit these files.** They are snapshots. If one needs correcting, fix it
upstream and re-copy; a local edit would silently fork the record the briefs
cite.

| File | Source | Snapshot taken from | Status at snapshot |
| --- | --- | --- | --- |
| `executable-loop-harness.md` | `exploring-claude` · `docs/design-notes/` | `c09765ca` (2026-08-04) | Proposed |
| `loop-decoupling-pivot.md` | `exploring-claude` · `docs/design-notes/` | `57020103` (2026-08-09) | Proposed |

Both are marked **Proposed**, not Accepted — they are argued positions with
measured evidence behind them, not settled policy. `docs/briefs/0002-*` treats
them that way: it adopts specific rules, and where it departs from one it says
so and why (see its *The one tension in this list*).

Neither file contains an absolute path, so both are safe to commit as-is.

## Why these two

- **`executable-loop-harness.md`** — the primary source. Rules 1–3 (prefer a
  check to a rule; mechanical operations are functions, not prose; structured
  state with markdown as a rendered view), Rule 6 (extract the core/adapter seam
  at a *second consumer of a different kind*, which is why the demo target is a
  CLI), and Rule 7 (nothing in the loop evaluates the run against the point of
  the run — the origin of the run-level signals requirement). Also the parsing
  bug table and the invisible-from-inside-the-loop result.
- **`loop-decoupling-pivot.md`** — mechanism/state separation, and Rule 5's
  project-declared gates: the consumer repo declares its gate list and the loop
  never hardcodes it.
