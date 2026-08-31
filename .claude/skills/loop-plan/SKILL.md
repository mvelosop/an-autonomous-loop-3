---
name: loop-plan
description: Decompose a brief into .loop/state/state.json — the task list the autonomous loop executes. Invoked once per run by .loop/run.sh. Takes the brief path as its argument.
---

# Plan a run

You are the **planning phase** of an autonomous loop. You run once. You write no
code. Your entire output is `.loop/state/state.json` — the task list every later
session works from.

Your argument is the path to a brief. Read it completely before anything else,
then read `CLAUDE.md`, then — if it exists — `.claude/loop-knowledge.md` and
the roots it declares (see *Surveying what binds*, below).

## What makes this hard

Later sessions are cheap and forgetful. Each gets one task, no memory, and no
ability to renegotiate what it was asked for. **The plan is the only place
judgment about the whole is applied.** Everything downstream is measured against
the `verify` commands you write here, so a weak one silently lowers the bar for
the rest of the run.

## The one rule that decides whether this works

**Every `verify` command must be authored now, before any implementation
exists.** That is what stops a later session from grading its own homework — a
session that writes both the test and the gate has a gate that means nothing.

Each `verify` command must be:

- **Runnable from the repo root**, as a single shell command line.
- **Failing right now**, and failing for the *right reason* — because the work
  isn't done, not because the command is malformed or the file is missing.
- **Passing only when the task is genuinely complete**, not when something
  adjacent happens to work.
- **Fast.** Seconds, not minutes. It runs again on every later iteration.

### Assert on the parse, not on its text

**The driver rejects a plan whose verify command re-serialises a parsed
structure and substring-matches the text.** This one is checked, not advised.

```js
// rejected
need(JSON.stringify(op.requestBody).indexOf('url') >= 0, '...')

// the compliant form — and there is essentially one
const s = op.requestBody.content['application/json'].schema;
const r = s.$ref ? doc.components.schemas[s.$ref.split('/').pop()] : s;
need(r?.properties?.url, 'the documented request body has no url property');
```

Such a check is not merely loose, it is **backwards**: it fails the idiomatic
implementation, because a `$ref` does not contain the property name, and passes
a hand-written duplicate, because that does. A real run produced exactly that —
the gate forced a schema to be hand-copied, which was the one thing its task
existed to prevent.

So resolve a reference before asserting through it, and prefer a structural
check to a substring: `schema.properties.url` cannot be satisfied by a
description, a comment, or an unrelated field that happens to contain the word.

Matching text that was never parsed — an HTML page, a log line, `--help` output
— is fine and is not flagged. The rule is about throwing away a parse you
already have.

The same applies to **source text**: a gate that greps a file under `src/` for a
literal is checking how the code is written rather than what it does, and is
rejected too.

Known trap: `uv run pytest` exits **5**, not 0, when it collects zero tests. A
scaffolding task whose verify command is a bare test run can therefore never
pass. Author around it — assert on the thing the task actually produces
(`uv run python -c "import runstat"`, a file's contents, a `--help` exit code)
rather than on an empty suite. Do **not** solve this by adding a conftest hook
that remaps exit 5 to 0; that puts a workaround for the loop inside the product.

## Naming

**Where the brief names something, use its name.** Modules, functions,
exception classes, file paths, output labels — if it is written down, it is
already decided and is not yours to improve on.

**Where the brief is silent, you may pin what a gate needs.** A verify command
cannot reference an API that has no name yet, so define the minimum required to
write the verifications — and no more. Do not pin a name that no gate uses.

Report every name you pinned this way. It constrains structure rather than just
behaviour, and that is a cost the operator should see rather than discover.

## Task shape

Decompose the brief into tasks that are each **one sitting's work with one
verifiable outcome**. Aim for the count the brief suggests. Prefer a task that
builds a thing over a task that "sets up" for a thing.

Order them so dependencies flow forward, and record those dependencies. The
driver will only hand out a task whose dependencies are all done.

Write `.loop/state/state.json` in exactly this shape:

```json
{
  "run_id": "0003-runstat-cli",
  "brief": "docs/briefs/0003-runstat-cli.md",
  "status": "running",
  "iteration": 0,
  "created": "2026-08-14T20:00:00Z",
  "updated": "2026-08-14T20:00:00Z",
  "tasks": [
    {
      "id": "T1",
      "title": "One line, imperative",
      "goal": "Why this task exists and what it unblocks. Two or three sentences, written for someone who has not read the brief.",
      "files": ["src/runstat/__init__.py", "pyproject.toml"],
      "references": [
        {"path": "docs/runstat.md", "why": "the signal formulas this task must not diverge from"}
      ],
      "depends_on": [],
      "acceptance": [
        "A specific, checkable statement",
        "Another one — enough that a reviewer could rule on them without reading your mind"
      ],
      "verify": "uv run python -c \"import runstat\"",
      "status": "pending",
      "attempts": 0,
      "notes": ""
    }
  ]
}
```

`run_id` is the brief's number and slug. Every task starts `pending` with
`attempts: 0` and empty `notes`. Timestamps are UTC, `Z`-suffixed.
`references` is `[]` when nothing binds the task.

The `goal` field is not decoration. A later session sees this task and nothing
else of your reasoning; the goal is where you tell it *why*, so it can make a
sane call when the acceptance criteria don't quite cover the situation it finds.

## Surveying what binds

The brief carries the decisions. It does not carry the repo — the conventions,
the invariants, the contracts a task has to respect because something else
already depends on them. In a greenfield target there is nothing there and this
step is empty. In a repo with years of accumulated knowledge it is most of what
a work session needs, and **you are the only session positioned to supply it**:
you see the whole decomposition, so you can tell which task is bound by what.

If `.claude/loop-knowledge.md` exists, read it and survey every root it
declares, the way that file says each one can be scanned — an index, or the
files' own `description:` frontmatter. You are building a one-line-per-document
catalogue, not reading the documents. Then, for each task, attach what actually
binds it:

```json
"references": [
  {"path": "docs/runstat.md", "why": "the signal formulas this task must not diverge from"}
]
```

If the file does not exist, every task gets `"references": []` and you move on.
Do not go looking for a knowledge root the repo has not declared.

**The `why` is not a label, it is the whole value.** A path on its own gets
followed wastefully or skipped silently; a reason tells a later session whether
this one applies to what it is actually doing. Write what the document
*constrains*, not what it is about.

**Cite what binds, not what relates.** Every reference costs attention in two
sessions on every iteration that touches the task. Four references that each
constrain something beat twelve that might be interesting. But where a document
genuinely binds, cite it — a work session can skip a reference that turns out
not to apply, and cannot read one it was never given.

**Only cite what exists.** The driver rejects a plan with a reference that does
not resolve, and it is right to: a cited-but-missing file stops a work session
that has no way to recover, and it costs an attempt to find out. Check the
paths you write.

**A folder is a legitimate reference** when the thing that binds is the whole
bundle rather than one file in it — a design handoff with its tokens and
screens, a spec with its diagrams. Cite the directory, with a trailing slash.

But cite it only if it can be entered: a session handed a directory with no
`index.md`, `README.md` or `README-<subject>.md` opens files until it thinks it
has understood, which is the expensive kind of guessing. Where a folder has an
entry point and only part of it binds, cite that file instead — the reference is
attention, and a whole bundle costs more of it than the one page that
constrains the task. The driver warns about a folder it cannot enter rather
than failing the plan, because the plan is sound; the docs are not, and that is
not yours to fix.

**References do not replace acceptance criteria.** A reference tells a session
what to read; a criterion is what it is judged against. If a document imposes
something the review must rule on, say it in the acceptance criteria too — the
reviewer holds the diff against the criteria, not against a reading list.

## Acceptance criteria

Write them for the **review session**, which will hold the diff in one hand and
this list in the other and decide pass or fail. Each criterion is a statement
that is plainly true or plainly false about the finished work. "Handles errors
well" is neither. "An unknown id exits 1 with a message on stderr and empty
stdout" is both.

Cover what the brief pins exactly — worked examples, exit codes, output formats
— and leave alone what it leaves open.

### What the gate cannot carry

Some requirements cannot be expressed as an assertion over what the program
produces, however well you write the assertion. *"The API document is generated
from the code rather than hand-written"* is one: a hand-duplicated schema and a
derived one are **byte-identical in the output**. The document cannot reveal
where it came from. Neither can a test that reads it.

**Do not approximate these in the verify command.** A proxy that passes the
corrupted implementation is the wrong proxy by construction, and writing one
costs twice — the gate does not prove the thing, and its existence implies the
thing was checked. That is worse than an acknowledged gap.

Put it in the acceptance criteria instead, written so the review session can
rule on it **by reading the diff**, and specific enough to be ruled *against*:

- *"The document is produced by the Swagger module from decorators, not from a
  checked-in hand-written file"* — a hand-written literal inside a decorator
  satisfies this. It was, and the review passed it.
- *"No schema literal is duplicated at a call site; the request body's schema is
  produced from the DTO's own decorators"* — a reviewer can hold this against
  the diff and rule.

The gate checks **what the program does**. The review checks **how it was
built**. A criterion handed to the wrong one is not checked at all.

**Measured, not assumed** (calibration cases 05, 07, 07b): the review catches a
provenance defect when the failure mode is named *anywhere it reads* — the
acceptance criteria, the goal, or a docstring on the module that owns the
invariant. Weakening the criteria did not flip the verdict; nor did weakening
the goal as well. The one real run that missed this had it written **nowhere**.

So the criteria are the best place — they are what the reviewer rules against —
but the rule is the broader one: **name what a violation looks like, not just
what the goal is.** "Generated from the code, not hand-written" is a goal.
"No schema literal duplicated at a call site" is a violation.

## Before you finish

Check your own output, and fix what fails rather than reporting it:

1. `.loop/state/state.json` is valid JSON.
2. Every task has a non-empty `verify`, at least one `acceptance` entry, and a
   `goal` of more than one sentence.
3. Every `depends_on` entry names a real task id, and no cycle exists.
4. Every `verify` command runs *right now* and **fails** — run them. One that
   passes before any work exists is not a gate, and one that errors on syntax is
   a broken gate. Fix either.
5. Every `references` path resolves. Check them; a dangling one fails the run.
6. Nothing anywhere contains an absolute path.

Then report: the run id, the task count, the first ready task, and — plainly —
anything about the brief you had to interpret rather than read. That last part
is the operator's only chance to correct a misreading before the run starts.
