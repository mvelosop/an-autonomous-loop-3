---
name: executable-loop-harness
description: The loop's mechanical operations belong in a tested harness with schema-validated state, not in hand-parsed markdown described by prose contracts; the core is tech-agnostic (measured: 6% of the loop's contracts are stack-coupled, all of it the gate list) so it splits core/adapter/config, and the seam should be extracted at a second consumer rather than designed against one stack. Also records the result that generalizes furthest: no in-loop gate detects that the loop is globally stuck, so the operator must stay positioned to notice.
category: process
status: Proposed
decided: 2026-08-04
applies_to: any attempt to build an agentic development loop as tested code rather than prose — a second consumer repo or a greenfield project; also the framing for deciding whether a workflow change here should be a script or a rule. Not a plan for retrofitting this repo — see "How to apply".
---

# Executable loop harness

## Decision / Context

**Proposed, not accepted — for a new consumer repo, not a retrofit of this one.** (Originally scoped to "a greenfield project"; narrowed to *a second consumer repo* once the core/adapter measurement showed what actually needs proving — see Rule 6 and `## How to apply`.)

The autonomous loop's mechanical operations (which task is next, was the tick atomic, what survives archival, does this citation resolve) should live in a **tested harness over schema-validated state**, with agent contracts reduced to goal + what the harness enforces + where judgment is genuinely required. Today they live in prose that agents interpret and that hand-rolled string tools parse.

This note records the evidence for that architecture and its limits. It is written from plan 0136's measured outcome, which was a natural experiment: the plan shipped both scripts and prose contracts into the same corpus in the same run, so their failure profiles are directly comparable.

**Framing that must not be lost:** SparIQ's purpose is learning about agentic development by experimenting on a real application. Workflow investment is therefore a **first-class goal**, not overhead competing with product delivery. This note is not an argument for doing less workflow work. It is an argument about *which form* that work should take — script with a fixture, or prose with a reviewer.

### Genericity — core / adapter / config

**The loop is a state machine over process artifacts, not over code.** It never needs to understand the program under development; it needs to know whether a gate passed and what it printed. That makes a tech-agnostic core plausible, and the measurement bears it out — across the six core contract files (`implementer.md`, `reviewer.md`, `planner.md`, `next/SKILL.md`, `auto/SKILL.md`, `loop-contract-enforcement.guidelines.md`) at `fa1e1e43`: **679 lines, 46 of them stack-coupled — 6%.** Both orchestrators (`/next`, `/auto`) are **0%**. The coupling is concentrated in a single concept, the gate list: `pnpm test|typecheck|build|lint`, `turbo`, `dist/main.js` + `/healthz`, `depcruise`, `bruno`.

| Layer | Contents | Coupling |
|---|---|---|
| **Core** | plan state, queue order, atomicity, archival delta, verdict lifecycle, retry budget, citation resolution, V-tags, telemetry, insight capture/dedupe | none |
| **Adapter** | per-stack gate definitions: command, success predicate, output parser, artifact-proof strategy | all of it |
| **Config** | tiers/profiles, the guidelines corpus, agent-contract templates, branch conventions | per-repo |

**The strongest argument for extracting the core is that the core is the buggy part.** Every defect in `## Why`'s parsing table — the `awk` block terminator, the `sed` sentence split, zsh's `:P`, `str.index` matching a mention, the cumulative append — is core loop machinery. **None of it is application-specific.** So the code worth extracting and testing is precisely the code that has nothing to do with SparIQ; genericity here is not a tax paid for reuse, it is aimed straight at where the defects live.

**Four couplings are deeper than the 6% suggests**, and an adapter designed without them will be wrong:

1. **Smoke-start presumes a long-running HTTP server with a health endpoint.** A CLI, a library, a batch job, or a mobile app fits none of that. The adapter needs a general *"prove the artifact runs"* notion with per-kind strategies — this is where genericity actually costs.
2. **Cache-bypass is a class, not a `turbo` quirk.** The reviewer must force real execution or it replays the implementer's cached verdict as its own independent one (the reason `loop-contract-enforcement` Rule 16 existed before being folded into the reviewer contract). Every stack with a build cache — gradle, bazel, nx, sccache — has this. An adapter modelling only "run the test command" silently loses the loop's second opinion.
3. **The corpus is project-specific; only the mechanism is shared.** Citation resolution, category tagging, and amendment sweeps generalize. The guidelines themselves do not. Same shape as a linter: engine shipped, rules authored.
4. **Tiers and profiles encode a product philosophy, not a technical fact.** MVP-vs-final and `ui-pragmatic` are opinions about how one team builds. Config, never core.

## Rules / invariants

1. **Prefer a check to a rule.** When a workflow requirement can be expressed as a script with a fixture, write the script. Reserve instruction text for what genuinely cannot be mechanized — taste, scope, design judgment. A check can be demonstrated with a planted input and a recorded exit code; a paragraph can only be re-read, and re-reading always finds something.

2. **A mechanical operation on loop state is a function with tests, not a recipe in prose.** Any step that computes something from `PLAN.md` (expected next task, flip classification, archival delta, V-tag reconciliation) is a pure function of (state, diff). Prose that describes how to compute it has no fixture and cannot converge.

3. **Loop state is structured and schema-validated; markdown is a rendered view, never the source of truth.** Hand-parsing a document format with `grep`/`sed`/`awk` is where the loop's mechanical bugs come from (see `## Why`). Schema validation is to loop state what typecheck is to code — the gate that makes a whole class of defect impossible rather than reviewable.

4. **The harness's own tests are its gate; the loop may run harness changes like any other code.** A workflow change that ships as tested code has an executable gate and is therefore loop-eligible. This is the corollary to `CLAUDE.md`'s standing decision (2026-08-04) that instruction-*text* changes are not.

5. **Judgment is not mechanized, and pretending otherwise is the failure mode.** *Does this diff do what the task said?* — scope, taste, whether a finding is worth a tick — stays with the reviewer. The harness shrinks the prose surface; it does not eliminate it.

6. **Do not fix the adapter boundary against a single stack — extract it at the second consumer.** An interface designed with N=1 encodes the author's assumptions as architecture, and the four couplings above are exactly the ones a single-stack design misses. Build the harness for one repo with the core/adapter seam *stated but unabstracted*; let the second consumer force the seam's real shape. Corollary: the cheap next experiment is **a second consumer repo, not a greenfield product** — a small repo of a different kind (a CLI, a static site with a build) tests whether the seam holds at a fraction of the cost of starting a new application.

7. **No in-loop gate detects that the loop is globally stuck; keep the operator positioned to notice.** Every gate can be green, every reviewer thorough and substantially right, and the run still be going nowhere — because gates and reviewers evaluate *this tick against this task*, and nothing in the loop evaluates *the run against the point of the run*. Design for this explicitly: surface run-level aggregates the operator can feel (findings per task, cascade depth, ticks per landed change, corpus delta), keep an out-of-loop checkpoint that asks "is this converging?" rather than "did this tick pass", and treat an operator's unease as **evidence**, not as something to be reassured away. A harness makes this cheaper, not unnecessary — structured state is what lets the aggregates be computed at all.

## Why

### The measured split

Plan 0136 shipped 13 tasks: some produced shell checks, some produced prose contracts, into the same corpus in the same run. Raw findings-per-task barely differed (1.4 script vs 1.7 prose). But attributing each finding to *what it was about* rather than to the task that shipped it gives a clean result, measured at `ad054a34`:

- **Every lint check landed correct on the first pass.** IL-6 and IL-7 were right first time; IL-4 needed one scoping fix and then held. Where those tasks drew findings, the findings were about the surrounding prose — a design note's unswept head, an unpinned count, a `**Done:**` record claiming a command output that could not have occurred.
- **Every three-deep cascade was in prose.** T4→F1→F4, T10-polish F1→F2→F3, T13→F1→F2/F3. Two reviewers had to be explicitly instructed to hold proportionality and stop raising wording nits, because nothing else would have stopped them.

A check ends the argument: given this input, expect this exit code, run it. A paragraph does not.

### The bug corpus is a parsing corpus

Nearly every mechanical defect the loop hit in that run was a hand-rolled parser meeting a document format:

| Defect | Tool | What broke |
|---|---|---|
| Fold-coverage read the whole task block | `awk` | no terminator on the `Done when:` block, so a task's own Context prose satisfied the check |
| Sentence split for keyed temporal claims | `sed` | `e.g. ` treated as a sentence boundary → false positive in a commit-blocking gate |
| `$SHA:PLAN.md` mangled | zsh | the `:P` realpath modifier fires on an unbraced `$var:`, *even inside double quotes* |
| Insights section located by substring | Python | `str.index('## Insights')` matched a mention inside a task body, not the heading |
| Run-2/run-3 archival | procedure | cumulative sections re-appended verbatim, nearly injecting untriaged duplicates over triaged originals |

None of these is a judgment failure. They are all consequences of markdown-as-state with untested extraction. Structured state with a schema removes the category.

### Convergence, not worth

The loop converges on product code because the gates are executable — plan 0134 closed 6 tasks with **1** finding. It does not converge on instruction text — plan 0136 drew **26 findings across 13 tasks** while its own thesis was *a gate behind every claim*, and shipped a regression anyway (logged as its missed bug M1). Plan 0133: 19 findings on 6 tasks.

This is a claim about mechanics, not about value. Workflow work is the project's point (see `## Decision`). The conclusion is that it should be *shaped* so the loop can verify it.

### The failure was invisible from inside the loop

This is the sharpest result of the run, and the one that generalizes furthest beyond tooling choice.

Across plan 0136, **every gate was green on every tick.** Typecheck, tests, smoke-start, and the instruction lint passed; the reviewers were thorough, re-executed each other's evidence rather than reading it, independently re-implemented a check to verify it, and correctly declined to over-raise when told to weigh proportionality. By every signal the loop produces about itself, the run was healthy.

It was not. It took three `/auto` runs and 26 findings to land 13 tasks, cascaded three deep on a single paragraph twice, and shipped a regression — `/next` step 3.5's atomicity check firing on the polish batch that `/auto` step 3.5 *mandates in the same pull request*. That regression (logged as missed bug **M1**) is the clearest instance: it passed every automated gate **and** a reviewer who **noticed the defect and recorded it as an `## Insights` entry rather than a finding** — so it did not block, and it merged. A partial catch through a non-blocking channel is indistinguishable, from inside, from no catch at all.

The structural reason: **every mechanism in the loop evaluates a tick against its task. Nothing evaluates the run against the point of the run.** Gates are per-tick by construction. The reviewer's contract is per-tick by design. The retry budget counts attempts within one task, so a run that spawns a fresh finding each tick never reaches its threshold — each finding is new, each `attempts` counter resets, and the loop will iterate indefinitely while reporting success. Local correctness at every step composed into global stuckness, and no in-loop signal distinguished the two.

What surfaced it was the operator asking *"why does this feel like a sand bunker?"* — an out-of-loop judgment with no mechanism behind it, arriving only after the plan had already merged its own regression. That is not a gap a better gate closes. It is an argument about **where the human stays positioned**, and it is why Rule 6 exists.

The corollary for a harness: structured state is what makes the run-level view computable at all. Findings per task, cascade depth, ticks per landed change, and corpus delta are all trivial queries over typed state and effectively unavailable over hand-parsed markdown — which is why this repo could only produce them by hand, after the fact, in response to a hunch.

## How to apply

**For a new consumer** (greenfield project or a second repo per Rule 6) — the sketch this note proposes, not a specification:

- Loop state in **YAML with a schema**, parsed into typed objects (in a TS harness: schema-first, e.g. Zod, so the runtime validator and the static type have one definition — the same move TS makes over JS). Schema validation runs as a gate.
- A `harness/` package exposing mechanical operations as tested functions — `expectedNextTask(snapshot)`, `classifyFlips(snapshot, diff)`, `residualsToArchive(plan, archive)`. `classifyFlips` is plan 0136's step 3.5, which cost four ticks and three findings as prose and is roughly forty lines with a test per shape (sanctioned fold, polish batch, zero-flip, unaccounted pair).
- **Markdown rendered from state** for human and mobile reading, never edited as the source of truth.
- Agent contracts reduced to goal, what the harness enforces, and where judgment is required.

**Carry over the fixture corpus.** This repo's plan archives — 136 recorded plans with real ticks, real findings, real edge cases — are the highest-value artifact for a greenfield attempt. A harness that reproduces the correct verdict across plan 0136's own thirty-odd ticks has been integration-tested against reality rather than against imagined cases. That is test data otherwise worth months.

**Do not retrofit this repo.** The migration would itself be a large instruction-corpus change, which is the shape `CLAUDE.md`'s standing decision exists to avoid.

**The venue is a second consumer, not necessarily a greenfield product.** The original framing — "try this on a new project" — overstates the entry cost. What the architecture actually needs proving is the **core/adapter seam** (Rule 6), and that needs a repo of a *different kind*, not a different product: a CLI, a library, anything without a long-running server to smoke-start. Build the core against one repo with the seam stated but unabstracted; let the second consumer force its real shape. That is a weekend-sized experiment rather than a new application.

**In this repo, meanwhile**, apply Rule 1 only: when a workflow need can be a script with a fixture, write the script (`.claude/scripts/`, an `instruction-lint.sh` check) rather than another rule. Related: [[process-corpus-budget]], [[guideline-taxonomy]], [[loop-telemetry]].

## Amendment history

### 2026-08-04 — extended twice on the day of authoring

Recorded as one entry because both additions landed the same day, before the note had been cited by any plan or acted on by any reader; neither reversed a decision, both added substance to a `Proposed` note.

- **The invisible-from-inside-the-loop result** (`## Why`, and Rule 7). Added after the observation that plan 0136's failure was undetectable from the loop's own signals — every gate green, every mechanism per-tick, nothing evaluating the run against the point of the run. This is the note's most transferable claim and was missing from the original draft, which argued only the script-vs-prose case.
- **The genericity architecture** (`## Decision / Context` → *Genericity*, and Rule 6). Added after measuring the loop's actual stack coupling at 6% and finding it concentrated entirely in the gate list, which makes a core/adapter/config split concrete rather than aspirational. Also narrowed the note's proposed venue from "a greenfield product" to "a second consumer repo" — the same seam gets tested for far less.
