# Brief 0005 — production metrics and improvement insights

- **Status:** ready to plan
- **Extends:** `docs/briefs/0004-runstat-review.md` — same tool, two more commands
- **Touches the loop itself:** yes. The driver records new fields and the review
  contract gains a channel. That is unusual and is called out where it happens.

---

## What it is

Two additions that answer questions the loop currently cannot:

1. **What did a run actually produce, and how much of it was rewritten?**
2. **What did the run learn about the loop itself?**

## Why

The eight run-level signals are all about *process*: iterations, closures,
failures, spend. Nothing measures output, so "was that a good run" collapses to
"did it finish", and rework is invisible unless a human reads the diffs.

The second gap is sharper. On the NestJS run the reviewer rejected a task
because the work session had hand-written an OpenAPI schema purely to satisfy a
gate's `JSON.stringify(...).includes('url')` check, reintroducing the drift the
task existed to prevent. That finding is really two statements: *this code is
wrong*, and *that gate invited this*. The second is an insight about the loop,
and today it is buried inside a code finding because there is nowhere else for
it to go.

**The review session is the best-positioned observer in the system.** It is the
only thing that holds the task, the gate, the brief and the diff at once. This
brief gives it somewhere to put what it notices.

---

## Part 1 — production and rework

### What the driver records

`iterations.jsonl` gains four fields per record, written by the driver at commit
time from its own commit:

| field | meaning |
| --- | --- |
| `sha` | the iteration's commit |
| `files` | files changed in it |
| `added` / `deleted` | lines added and deleted in it |

**The driver computes these, not `runstat`.** The driver already holds the SHA,
it keeps `runstat` post-hoc over a run directory with no git access, and the
numbers survive a later squash that would erase the per-iteration commits.

### `runstat production <run-dir>`

| line | derivation |
| --- | --- |
| lines by kind | net added minus deleted at the end of the run, split into **code**, **tests** and **docs** |
| test-to-code ratio | test lines over code lines, 2 decimals |
| churn ratio | total added across all iterations, over net lines produced |
| cost per KLOC | estimated spend over net KLOC produced |
| lines per iteration | net produced over iterations |

**Churn is the point.** A ratio of 1.0 means everything written survived to the
end. Higher means work was written and then rewritten, which is the code-level
analogue of `iterations per closed`, and would have made the NestJS rework
visible as a number rather than as something a human noticed by reading.

**Classifying a file as code, test or doc is a heuristic, and must be stated as
one.** Path segments and extensions are enough (`test`/`spec`/`__tests__` in the
path is a test; `.md`/`.rst`/`docs/` is a doc; the rest is code). Print the rule
in the output so a reader can see what was assumed. Do not add configuration for
it in this brief.

### Deliberately out of scope: coverage

Coverage is not measured, and the reason belongs in the code: **a test suite can
have complete coverage and assert nothing.** The calibration case where a
function returned the fixture's expected values, and the hollow-test case where
assertions could never fail, would both score perfectly. A number that a hollow
suite maximises is not a quality signal, and publishing it next to real ones
lends it credibility it has not earned.

---

## Part 2 — improvement insights

### What the review session records

`verdict.json` gains an **`observations`** list, alongside the existing
`findings`:

```json
{ "verdict": "PASS",
  "findings": [],
  "observations": [
    { "scope": "gate",
      "note": "this task's verify does a substring check on the serialised request body, so a correct $ref does not satisfy it and an inline schema does" }
  ] }
```

`scope` is one of **`gate`**, **`brief`**, **`loop`** or **`driver`**.
Observations never affect the verdict and never block.

### The rule that makes this safe

> **Anything wrong with the work is a finding, and it blocks. An observation is
> only ever about the machinery.**

This is not a style preference. In the corpus this loop was rebuilt from, a
reviewer noticed a real defect, recorded it as an insight rather than a finding,
and it merged: *a partial catch through a non-blocking channel is
indistinguishable, from inside, from no catch at all*. **Filing a defect as an
observation is a contract violation**, and the reviewer contract must say so in
those terms.

Observations are capped at a small number per review. Volume is how this channel
dies.

### `runstat insights <run-dir>...`

Aggregates, across one or many runs, the improvement signal the loop already
produces and never reads:

| source | already captured in |
| --- | --- |
| reviewer observations | `reports/*-verdict.json` (new) |
| permission denials | `sessions/*.json`, surfaced per-run but never aggregated |
| retry notes | the `notes` on a task that was reverted, in the journal |
| planner interpretations | the plan session's report, read once and buried |

Group by `scope`, and by source where there is no scope. Repetition is the
signal: the same observation across three runs is a defect in the loop, and one
observation once is an anecdote.

Accepting multiple run directories is the point of the command. A single run
tells you almost nothing here.

---

## Behaviour contract

Inherits brief 0003 exactly. **Exit codes:** `0` success, `1` valid but nothing
to report, `2` usage error or malformed input. errors on stderr, stdout empty on failure,
no traceback. A malformed record is a hard failure, never a silent skip.

**A run recorded before these fields existed is not malformed.** Older
`iterations.jsonl` records have no `added`/`deleted`, and older verdicts have no
`observations`. Treat them as absent, report what can be computed, and say
plainly which runs were missing data rather than silently averaging over a
smaller set.

---

## Worked example

**Fixture run.** Three iterations, whose records carry:

| iteration | task | outcome | files | added | deleted |
| --- | --- | --- | --- | --- | --- |
| 1 | T1 | done | 3 | 120 | 0 |
| 2 | T2 | review_fail | 2 | 80 | 10 |
| 3 | T2 | done | 2 | 60 | 70 |

Paths: `src/app.ts` (code), `tests/app.spec.ts` (test), `README.md` (doc).

`runstat production` reports exactly:

```
lines produced:       180
  code:               100
  tests:               60
  docs:                20
test-to-code ratio:  0.60
churn ratio:         1.44
lines per iteration:  60
cost per KLOC:    $22.22
```

Net produced is `(120+80+60) - (0+10+70) = 180`. Churn is total added `260` over
net `180`, which is `1.44`. Cost per KLOC uses the run's estimated spend.

`runstat insights` over a run whose verdicts carry two `gate` observations and
one `brief` observation, plus one permission denial, prints them grouped by
scope with the iteration and task each came from, and a count per group.

**A second fixture** has an `iterations.jsonl` with no `added`/`deleted` fields
at all, and `production` reports that the run predates the fields rather than
reporting zero.

## Out of scope

- Coverage, for the reason given above.
- Any judgement about whether a number is good. The loop reports; the operator
  decides. No thresholds, no grades, no halting on a production metric.
- Cross-run comparison of production. `compare` stays about signals.
- Configuring the code/test/doc classification.
- Acting on an observation. This brief captures and reports them; triage is the
  operator's, between runs.

## Constraints

- Standard library only at runtime; `pytest` the sole dev dependency.
- Reuse the existing loader and error types. One tool, one contract.
- Every existing test must still pass, unchanged, and the four existing commands
  must behave exactly as they do now.
- Changes to `.loop/run.sh` and `.claude/skills/loop-review/SKILL.md` are in
  scope for this brief. `.loop/tests/run-all.sh` must stay green, and any new
  driver behaviour needs a scenario.
- `docs/runstat.md` and `docs/runstat-cli.md` both cover the telemetry contract
  and the commands; both must cover the new fields and commands when done, with
  examples matching real output.

## Shape

Six to eight tasks. The loader, the error contract, the CLI skeleton and the
fixture machinery all exist, so extend them rather than rebuilding.

Two tasks touch the loop itself rather than `runstat`, and they are the ones to
gate carefully: the driver recording the new fields, and the reviewer contract
gaining `observations`. The reviewer change cannot be gated by running a review
session, so gate it on the contract stating the finding-versus-observation rule
and on the fixture suite still passing.
