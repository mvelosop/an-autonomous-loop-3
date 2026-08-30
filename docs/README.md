# Documentation

An index, so that a document can be found by what it is about rather than by
guessing at its filename. The planning session reads this file — see
`.claude/loop-knowledge.md` — and cites the relevant entries onto the tasks
that need them, so **a document with no line here is a document the loop will
not find**.

One line per document, describing what binds rather than what it covers.

## The demo target

| Document | What it binds |
| --- | --- |
| [`runstat-cli.md`](runstat-cli.md) | The `runstat` command surface: the four commands, their arguments, their exit codes, and the exact shape of what each prints. Anything changing a command's output or its failure behaviour must match this. |
| [`runstat.md`](runstat.md) | The telemetry contract and the derivation of all eight run-level signals. Load-bearing: `.loop/run.sh` computes the same eight inline in shell, so a formula that changes here must change there in the same commit, or the two silently disagree. |

## Inputs and records

| Path | What it holds |
| --- | --- |
| [`briefs/`](briefs/) | What a run is planned from. `B007` is the current numbering scheme; the design record for the loop itself is `0002`. |
| [`references/`](references/) | Documents whose paths resolve in a consumer repo rather than this one — vendored design notes, and material addressed to a consumer. Indexed and frontmatter-described; see its own [`README.md`](references/README.md). |

## Not here

The loop's own documentation lives with the loop: [`.loop/manual.md`](../.loop/manual.md)
end to end, [`.loop/README.md`](../.loop/README.md) for its mechanism, stop
conditions and tests. That is deliberate — the manual installs into a consumer
repo alongside the driver it documents, and a copy under `docs/` would drift
from the copy that ships.
