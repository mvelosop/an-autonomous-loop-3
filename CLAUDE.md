# an-autonomous-loop-3

An experiment in autonomous agentic development. The loop is the deliverable;
the program it builds is the proof it ran.

Design: `docs/briefs/0002-next-generation-autonomous-loop.md`.
First target: `docs/briefs/0003-runstat-cli.md`.

## How the loop works

`loop/run.sh` drives three kinds of **fresh, separate `claude -p` session**. None
of them share memory. All continuity lives in files:

| Path | Role |
| --- | --- |
| `loop/state.json` | **Single source of truth.** Tasks, acceptance criteria, verify commands, status, attempts. |
| `loop/journal.md` | Append-only. One entry per iteration. A view, never the source of truth. |
| `loop/proposal.json` | Transient. The work session's report on the task it just did. |
| `loop/verdict.json` | Transient. The review session's independent verdict. |
| `loop/runs/<run-id>/` | Telemetry: one JSON per session, plus `iterations.jsonl`. |

One iteration: driver picks the next ready task → **work session** does it →
driver runs the **gate** (every done task's verify command) → **review session**
gives an independent verdict → driver applies it, journals, commits.

## Rules for any agent working here

1. **All durable state stays in this repo.** Never write session state, memory,
   or config to `~/.claude` or any other global location. Drift there is
   invisible and unrepeatable. This is the rule everything else rests on.
2. **Repo-relative paths only** — in files, logs, journal entries, and commit
   messages. Never `/Users/...`. Write `~/...` if you must show an absolute
   path. The driver masks `$HOME` and the username out of everything it
   persists, but that is a backstop, not your excuse.
3. **One task per iteration.** Do the task you were given and stop. Do not start
   the next one even if it is trivial and you have the context. Running ahead
   desynchronizes the plan from reality and is the main failure mode of
   autonomous loops.
4. **You do not set task status.** The work session *proposes*; the gate and the
   review *dispose*. Status transitions belong to the driver.
5. **You do not commit.** The driver makes exactly one commit per iteration,
   covering code, state, journal and telemetry together.
6. **A task is done only when its verify command exits 0 and the review session
   passes it.** Claiming done without both just costs an attempt.
7. **No web access.** `WebFetch`/`WebSearch` are denied so a run cannot drift
   with the internet. Package installs are fine.
8. **Halting cleanly with a good blocker report is a success. Faking progress is
   the only real failure.**

## Toolchain

Python 3.13 with `uv`, `src/` layout, `pytest`. Run things as `uv run pytest -q`
and `uv run <cli> ...`. The demo target has no runtime dependencies outside the
standard library.

## Git

Work happens on a `NNN-<slug>` branch, one per blog post. Agents commit
**locally only and never push** — pushing, opening PRs and merging are the
operator's, and the driver makes every commit anyway (rule 5).

A finished branch is **squash-merged** into `main`, so `main` reads as one
commit per post. **The branch is never deleted.** It holds the loop's
per-iteration commits, and those commits *are* the evidence the post is about —
that each task was done by a separate, fresh session that could not see the
others. A squash on `main` destroys the only record of that. Keep both: `main`
for reading, the branch for proof.
