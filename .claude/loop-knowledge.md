# Knowledge roots

**Read by the planning session.** This file is the repo's answer to a question
the loop cannot answer for it: *where does the knowledge live that a task might
be bound by, and how do I find out what is in it without reading everything?*

The loop fixes this path and nothing else about this file. It does not know what
an ADR is, or a use case, or a tier — those are conventions, and conventions
belong to the repo that has them. Delete this file and the loop still runs; the
planner simply cites nothing, which is the right behaviour for a repo with
nothing to cite.

## The roots

| Surface | Path | How to find what is in it |
| --- | --- | --- |
| Documentation for the demo target | `docs/` | Index at `docs/README.md`, one line per document saying what it binds |
| Vendored design notes and consumer-facing material | `docs/references/` | Index at `docs/references/README.md`, **and** every file carries a `description:` frontmatter line |

## What "discoverable" means

Either mechanism is enough, and both is better:

- **An index** at the root — one line per document, saying what it *binds*, not
  what it covers. Cheapest: the planner reads one file per root rather than N.
- **Per-file frontmatter** with a `description:` line. Better where files are
  added often and an index would go stale.

A root with neither leaves the planner guessing from filenames, which is why
preflight warns about it before a run spends anything.

## How to cite

Prefer the document that is *binding* over the one that is merely related. A
reference costs attention in every session that reads the task, so each one
carries a reason: not `docs/runstat.md`, but `docs/runstat.md` — *the signal
formulas this task must not diverge from*. When in doubt, cite: a work session
can skip a reference that turns out not to apply, but it cannot read one it was
never given.
