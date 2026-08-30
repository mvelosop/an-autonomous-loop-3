# Brief B007 — the installable loop: one directory, its own fence

- **Status:** implemented — this is a design record, not a plannable brief
- **Role:** makes the loop installable into a repo that already has a life of
  its own. Everything here is about the *consumer's* diff, not the loop's
  behaviour, which is unchanged.
- **Starting point:** extends `docs/briefs/0002-next-generation-autonomous-loop.md`
  — same loop, different residence.

---

## Why this brief exists

The loop was about to be installed into a mature pnpm monorepo that already has
its own agent workflow: four agents, nine skills, ten process guidelines, a
plan archive, and commits prefixed `[loop]`. Two loops, one repo. Installing
the loop as it stood would have landed a new top-level directory, mixed the
loop's shipped code with the consumer's own history in a single folder, and —
the part that would actually have hurt — merged a deny list into the target's
project settings.

That last one is worth naming precisely, because it is the failure that reads
as a design decision until the day it bites. Permissions **deny beats allow,
repo-wide, across every source**. The installer merged
`Bash(git commit:*)`, `Bash(git push:*)`, `WebFetch` and `WebSearch` into the
target's `.claude/settings.json`. The target's own settings explicitly allow
all four, because its agents commit and push. The install would have silently
disarmed the repo's existing workflow on day one, and nothing about the
symptom would have pointed back at the installer.

None of this is fixed by a plugin we are not building yet. It is fixed by
deciding where files live and who owns them.

## What was decided

**One directory, and one line through it.** The loop is `.loop/`. Above the
line — `run.sh`, `settings.json`, `manual.md`, `README.md`,
`brief-template.md`, `tests/` — is mechanism, replaced wholesale on upgrade.
Below it, `.loop/state/` (`state.json`, `plan.md`, journals, run telemetry) and
`.loop/tmp/` (the per-iteration handoffs and the run lock) belong to the
consumer repo and are never written by the installer.

A dot-directory rather than a visible one, because a top-level `run/`-style
folder in a monorepo gets swept by workspace globs, build tooling and lint
config, and because the consumer's root is theirs.

**The fence travels with the loop.** `.loop/settings.json` holds the loop's
allow and deny lists, and `.loop/run.sh` hands it to every session with
`--settings`. It is a first-class settings source that loads on top of whatever
`--setting-sources` resolved, so the fence binds loop sessions and nothing
else. **The installer no longer touches the target's `.claude/settings.json`
at all.** What remains the consumer's is the other half — the commands their
own gates run — and because that lives in a different file, an upgrade cannot
overwrite it.

**The boundary is checked, not documented.** The installer's copy manifest is
inverted: it names what to *leave alone* (`state`, `tmp`), never what to copy.
A list of what to copy goes stale the day a file is added — `amend.sh` was
added after the installer and silently shipped to nobody — and a list of what
to preserve cannot fail that way. `.loop/tests/scenarios/26-install-boundary.sh`
installs over a target carrying sentinel state, twice, and fails if a byte of
it moves.

**Documentation the consumer never received now ships.** The manual moved into
`.loop/` and the two worked briefs its "Writing a brief" section cites are
copied to `.loop/examples/` — a consumer following that pointer previously
found nothing. The installer names those briefs explicitly and dies if one is
missing, so a rename fails loudly instead of shipping an empty directory. The
loop's own reviewer-calibration *results* stopped shipping: the cases are
mechanism, the results are this repo's record.

**A brief derived from a design corpus is a different act.** Every session
downstream of a brief — planner, work and review all read it — is a fresh
`claude -p` with no memory, `--strict-mcp-config`, and web access denied. A
brief written from an existing design practice must therefore know which of
three rows it is in: what arbitrates lives *in* the brief, durable context is
*referenced* by repo-relative path, and anything living only in a tracker must
be *inlined*. The manual gained that section. `.loop/check-brief.sh` gained the
half of it that is checkable rather than advisable — it warns on issue keys and
tracker URLs, which name something no reader can open — and its path check
widened past `.md` to diagrams, schemas and directories.

## What was rejected

- **Two top-level dot-directories** (`.loop/` and a sibling for state). It buys
  a `rm -rf` upgrade and costs a second entry in the consumer's root. The
  inverted manifest plus a scenario buys the same guarantee for one directory.
- **Moving the skills into `.loop/skills/`** with a mirror back to
  `.claude/skills/`. Claude Code resolves skills only at `.claude/skills/`, so
  the mirror is mandatory, and duplicating them creates a new failure mode —
  editing the copy that gets overwritten — to solve a problem that was never
  duplication. What shipped `amend.sh` to nobody was a hand-kept list, and the
  installer globs both roots now.
- **Rewriting paths inside journals, run telemetry and calibration results.**
  Those are timestamped accounts of what happened, and the paths in them were
  accurate when written. They were moved and left alone; the migration's 36
  record-file entries are pure renames with zero content change.

## What stays the consumer's

The mapping from a repo's own design surfaces — its tracker, its decision
records, its design handoffs — onto a brief. The loop ships the contract
(`.loop/brief-template.md`) and the checker (`.loop/check-brief.sh`); a
consumer ships the skill that translates. The moment the loop names a tracker
it stops being stack-independent, which is the same seam `.loop/settings.json`
draws for permissions: the loop provides the slot, the consumer fills it.

## Out of scope

- The plugin. This brief exists precisely because the plugin is not being built
  yet, and it deliberately does not pre-empt its shape.
- Any change to what the loop *does*: the driver's iteration, the gate, the
  review contract and the state machine are untouched.
- The consumer-side brief-authoring skill itself.
- Migrating the existing branches. Their history keeps the old layout, which is
  correct — that is where those runs happened.

## Verification

The suite runs green, and two of its checks are new evidence rather than
description: the install-boundary scenario, and a retired-layout pattern in
`.loop/tests/check-docs.sh` that fails the suite if any document drifts back to
describing a top-level home. The installer was run end to end into a scratch
repository; the resulting footprint is `.loop/`, `.claude/skills/loop-*`, one
merged section in `CLAUDE.md`, and one line in `.gitignore`.
