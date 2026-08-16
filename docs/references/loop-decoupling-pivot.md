---
name: loop-decoupling-pivot
description: Decouple the loop (mechanism) from the app (state + product) — tech guidelines move to docs/implementation/ as developer docs, the .claude loop extracts to a separate tech-independent repo (plugin-preferred) carrying a minimal fake-project fixture for unit/integration-testing the loop, and the blog's scheduler stays its own repo (never the loop's fixture); phased, guidelines-move-first.
category: process
status: Proposed
decided: 2026-08-08
applies_to: any change to where guidelines live, how agents cite them, the .claude directory's structure, or the loop's distribution/versioning; the guidelines-move pass; the eventual loop-repo extraction; deciding where a test substrate for loop changes lives.
---

# Loop decoupling pivot

## Decision / Context

**Proposed.** The loop and the application share one repo, which couples them in both directions: the loop's evolution commits interleave with product history, and rolling the loop back to an earlier version is entangled with the app's state. Observed cost (2026-08-08): the loop's attention has drifted toward its own improvement over the application's — the same convergence problem `CLAUDE.md`'s standing decision (2026-08-04) measured, now expressed as a repo-structure problem.

The pivot: **split mechanism from state.**

- **Mechanism** (agents, skills, `.claude/scripts/`, process guidelines, `META-ROADMAP.md`) extracts to a separate, tech-independent loop repo — versioned and pinnable, so "go back to a previous loop version" becomes changing a pointer, and trialing a replacement loop (e.g. the blog sample app's) is cheap and reversible.
- **State + product knowledge** (`PLAN.md`, `ROADMAP.md`, `plans/`, `docs/`, and the tech guidelines) stays in the consumer repo. Tech guidelines move from `.claude/guidelines/` to `docs/implementation/` — they are developer documentation for *this codebase*, per [[guideline-taxonomy]]'s existing process/tech split, and belong where developers look rather than inside the loop's directory.
- **The loop repo carries a minimal fake-project fixture** — a canned `PLAN.md`, a stub file tree, and scripted gates with planted pass/fail outcomes — as its unit/integration-test substrate. This gives the loop repo executable truth (tick mechanics, gate consumption, retry budget, halt behavior are testable deterministically) without binding it to a stack.
- **The blog's meetup scheduler is a separate repo that consumes the loop**, and doubles as the *realistic* trial ground for new loop versions. It is never the loop's in-repo fixture: the blog role wants the app to grow on camera under a deliberately naive loop, the fixture role wants it frozen, minimal, and always on the current loop — bundling them breaks both.

**Relationship to [[executable-loop-harness]]:** complementary, not competing. That note proposes *rebuilding* the loop as a tested harness for a new consumer, and measured the core/adapter split (6% stack-coupled, all in the gate list). This note extracts the *current prose loop* as-is into its own repo — creating the versioned home where a harness rebuild can later land as just another loop version, and forcing the gate seam that note's adapter layer needs anyway.

## Rules / invariants

1. **State stays, mechanism moves.** `PLAN.md`, `ROADMAP.md`, `plans/`, `docs/` (including the relocated tech guidelines) remain in the consumer repo; agents, skills, scripts, process guidelines, and `META-ROADMAP.md` belong to the loop repo. Anything that ticks per-plan is state; anything that defines *how* ticking works is mechanism.

2. **Tech guidelines live under `docs/implementation/`, mirroring the taxonomy.** Every `category: tech` guideline — including the `mvp/` tier variants, all seven of which are tech topics — moves to `docs/implementation/` (keeping the `mvp/` subfolder). Process guidelines do not move there; they are mechanism. Citation contracts (planner `Guidelines:` lines, implementer/reviewer read obligations) are unchanged except for paths.

3. **Archived plans keep their old citation paths.** `plans/` is frozen history; only forward-looking surfaces (agent contracts, skills, `CLAUDE.md`, guideline READMEs, `instruction-lint.sh` scan paths) are updated in the move.

4. **The move is grep-gated.** Done when `git grep -l '\.claude/guidelines/' -- ':!plans/'` returns only surfaces citing process guidelines, and every relocated file is cited by its new path. Mechanical, checkable, one pass — per the standing decision, not a finding loop.

5. **The loop consumes project-declared gates; it never hardcodes them.** The consumer repo declares its gate list (command, success predicate, artifact-proof strategy); the loop's contracts reference the declaration. This is the extraction of the one stack-coupled concept [[executable-loop-harness]] measured, and it is the only genuinely new design surface in the pivot — worth an `/architect` pass before the extraction phase.

6. **The fixture is a fake project, never a real application.** Scripted gates with planted outcomes, canned plan state, stub tree. Ceiling if a real-stack fixture is ever justified: hello-world tier. The scheduler and SparIQ are consumers, not fixtures.

7. **A full-tick e2e (spawning real agents) is an operator-run acceptance check, not a per-commit gate.** It costs tokens and is nondeterministic. The deterministic fixture tests (gate-declaration parsing, plan-state transitions, retry/halt logic) are the per-commit tier.

8. **Distribution is plugin-preferred.** A Claude Code plugin carries exactly what the loop is (skills + agents + hooks), versions per release, and keeps the consumer's `.claude/` thin and project-specific. Submodule is the fallback if plugin mechanics prove limiting; subtree and sync-scripts are rejected (drift, weak pinning).

## Why

- **The loop self-focuses when it lives with the app.** The standing decision (2026-08-04) showed instruction-text work doesn't converge in the loop (plan 0136: 26 findings / 13 tasks; plan 0133: 19 / 6, vs plan 0134's 1 / 6 on product code). Same-repo residence keeps that work adjacent and tempting; a separate repo makes loop work an explicit context switch with its own history.
- **Rollback and trialing need a pointer, not surgery.** In-repo, reverting the loop means untangling workflow commits from product commits. Pinned versions make "try the blog's loop on the scheduler, keep SparIQ on the known-good version" a two-line change.
- **Git history legibility.** Main's history should read as a product changelog; loop-evolution `[hygiene]` commits currently interleave with it.
- **Semantic home for tech docs.** The same argument `CLAUDE.md` makes for design notes: durable developer-facing knowledge belongs in `docs/`, not buried in `.claude/`. The taxonomy already marks which guidelines are developer docs (`category: tech`, `provenance:` tagged); the folder move just makes the split physical.
- **The fixture repairs the extracted repo's weakness.** Standalone, the loop repo would be a prose repo with `instruction-lint` as its only gate. A fake-project fixture converts loop changes from "prose with a reviewer" toward "script with a fixture" — [[executable-loop-harness]] Rule 1 applied to the loop's own repo.

## How to apply

Phased; each phase is independently valuable and none forecloses a later choice:

1. **Guidelines move** (consumer repo, one operator-driven hygiene pass, Rule 4's grep gate). Update: agent contracts, `create-plan` SKILL, `CLAUDE.md` tier tables, guideline README index (splits into process index + a `docs/implementation/README.md`), `instruction-lint.sh` paths. Valuable even if no later phase happens.
2. **Gate seam design** (`/architect`-shaped, Rule 5). Output: the gate-declaration format and where it lives in a consumer repo. A first working version landed with phase 1: `.claude/project-adapter.md` declares universal gates (+ reviewer cache-bypass variants), artifact-proof strategy, task-specific gates, and knowledge roots, with adapter-wins precedence over the contract mirrors; per-kind artifact-proof strategies (CLI, library, batch — the deep couplings from [[executable-loop-harness]]) remain open for the `/architect` pass.
3. **Extraction.** Loop repo created (plugin-preferred, Rule 8), fixture built (Rule 6), v1 pinned = current behavior, SparIQ consumes v1. No behavior change intended at this phase. Seed material — concrete move inventory, plugin shape, open questions — lives in `docs/briefs/0001-loop-plugin-repo.md`; this note stays the decision record.
4. **Trialing.** Alternate loop versions (including the blog sample app's naive-loop lineage) run against the scheduler repo first; SparIQ re-pins only after a version proves out there.

Related: [[guideline-taxonomy]], [[executable-loop-harness]], [[process-corpus-budget]].
