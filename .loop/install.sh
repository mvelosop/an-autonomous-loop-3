#!/usr/bin/env bash
#
# Install this loop into another repo.
#
#   .loop/install.sh /path/to/target-repo
#   .loop/install.sh --no-proof /path/to/target-repo   (skip the suite run)
#
# The loop is two things with different homes, which is why there is no clean
# submodule or plugin route: the SKILLS must sit at .claude/skills/ for Claude
# Code to resolve `/loop-work T3`, and the DRIVER is a shell script you run from
# your terminal. So it is vendored — but vendored deliberately, with a version
# stamp and a proof it works.
#
# Three classes of file, handled differently:
#
#   loop-owned    .loop/* except state/ and tmp/, .claude/skills/loop-*
#                 replaced wholesale — these ARE the loop
#   yours         .loop/state/, .loop/tmp/, CLAUDE.md, everything else
#                 state/ and tmp/ are never written here; CLAUDE.md is MERGED
#
# What this installer does NOT do any more: touch your .claude/settings.json.
# The loop's permission fence ships as .loop/settings.json and run.sh hands it
# to every session with --settings, so it binds loop sessions and nothing else.
# Merging a deny list into a repo's project settings would have bound the
# operator's own interactive work too — deny beats allow, repo-wide — which on
# a repo whose agents commit and push is a bad first day.
#
# Idempotent: re-run to update an existing install.

set -uo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROOF=1
[[ "${1:-}" == "--no-proof" ]] && { PROOF=0; shift; }
TARGET="${1:-}"

say()  { printf '\033[36m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[33m[install]\033[0m %s\n' "$*"; }
die()  { printf '\033[31m[install] %s\033[0m\n' "$*" >&2; exit 1; }

[[ -n "$TARGET" ]] || die "usage: .loop/install.sh /path/to/target-repo"
TARGET="$(cd "$TARGET" 2>/dev/null && pwd -P)" || die "no such directory: ${1}"
[[ "$TARGET" != "$SRC" ]] || die "target is the loop's own repo"
[[ -d "$TARGET/.git" ]] || die "$TARGET is not a git repository (the loop commits per iteration)"
command -v jq >/dev/null 2>&1 || die "jq is required"

say "installing the loop into $(basename "$TARGET")"

# ---- loop-owned: overwrite ------------------------------------------------

mkdir -p "$TARGET/.loop" "$TARGET/.claude/skills"

# The manifest is INVERTED on purpose. A list of what to copy goes stale the
# day a file is added — amend.sh was added after this installer and silently
# never shipped, so consumers got a manual documenting a file they did not
# have. A list of what to LEAVE ALONE cannot fail that way: a new mechanism
# file is picked up by the glob, and the only names spelled out here are the
# two the consumer owns.
CONSUMER_OWNED=(state tmp)

for item in "$SRC"/.loop/*; do
  name="$(basename "$item")"
  for keep in "${CONSUMER_OWNED[@]}"; do
    [[ "$name" == "$keep" ]] && continue 2
  done
  rm -rf "$TARGET/.loop/$name"
  cp -R "$item" "$TARGET/.loop/$name"
done
chmod +x "$TARGET"/.loop/*.sh

# One worked brief of each kind beats any amount of prose about brief-writing,
# and the manual's "Writing a brief" section ends by pointing at exactly these
# two. They used to live only in this repo, so a consumer following that
# pointer hit nothing. Named explicitly and checked, so a rename fails loudly
# rather than shipping an empty examples/ directory.
mkdir -p "$TARGET/.loop/examples"
for b in 0003-runstat-cli 0004-runstat-review; do
  [[ -f "$SRC/docs/briefs/$b.md" ]] || die "example brief docs/briefs/$b.md is missing — the manual cites it"
  cp "$SRC/docs/briefs/$b.md" "$TARGET/.loop/examples/$b.md"
done

# The calibration CASES are mechanism — a consumer can run them against their
# own model choice. The RESULTS are this repo's record of past runs, ~40 files
# of no use to anyone else, and shipping them puts our history in their diff.
rm -rf "$TARGET/.loop/tests/reviewer-calibration/results"

for s in loop-plan loop-work loop-review; do
  rm -rf "$TARGET/.claude/skills/$s"
  cp -R "$SRC/.claude/skills/$s" "$TARGET/.claude/skills/$s"
done
say "  .loop/ (driver, fence, manual, tests, examples) and .claude/skills/loop-* installed"

# ---- the fence, and what it does NOT touch -------------------------------
#
# .loop/settings.json travelled in with the wholesale copy above, and run.sh
# passes it to every session with --settings. Nothing is merged into the
# target's own settings: the loop's deny list binds loop sessions only, and
# the target's interactive work keeps whatever permissions it already had.
#
# What the target still owns is the other half — the commands its OWN gates
# run. The loop never names a test runner (each task carries its own verify
# command), so that list is the plan's, not the loop's, and guessing it is
# how you end up denying a repo the thing it needs. Report, do not assume.

TS="$TARGET/.claude/settings.json"
if [[ -f "$TS" ]] && ! jq -e . "$TS" >/dev/null 2>&1; then
  warn "  $TARGET/.claude/settings.json does not parse — sessions may run without your own permissions"
elif [[ -f "$TS" ]]; then
  say "  .claude/settings.json left untouched ($(jq '(.permissions.allow // []) | length' "$TS") allow rules, yours)"
else
  say "  .claude/settings.json absent — nothing to do; the fence ships in .loop/settings.json"
fi

TC="$TARGET/CLAUDE.md"
BEGIN='<!-- loop:begin -->'
END='<!-- loop:end -->'
rules="$(sed -n "/^## Rules for any session working here$/,/^## Toolchain$/p" "$SRC/CLAUDE.md" | sed '$d')"
block="$BEGIN
$rules
Loop docs: \`.loop/manual.md\` (start here) and \`.loop/README.md\`. Worked briefs:
\`.loop/examples/\`. State lives in \`.loop/state/state.json\`; the driver owns it.
$END"
if [[ -f "$TC" ]] && grep -q -- "$BEGIN" "$TC"; then
  python3 - "$TC" "$BEGIN" "$END" "$block" <<'PY'
import sys, pathlib, re
f, b, e, block = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
p = pathlib.Path(f); t = p.read_text()
p.write_text(re.sub(re.escape(b) + r".*?" + re.escape(e), lambda _: block, t, flags=re.S))
PY
  say "  CLAUDE.md loop section updated in place"
else
  printf '\n%s\n' "$block" >>"$TC"
  say "  CLAUDE.md loop section appended (nothing of yours changed)"
fi

# One line, not four. Every transient the loop produces lives under .loop/tmp/,
# so the boundary that keeps the installer out of consumer state is the same
# boundary git ignores.
for entry in ".loop/tmp/"; do
  grep -qxF "$entry" "$TARGET/.gitignore" 2>/dev/null || echo "$entry" >>"$TARGET/.gitignore"
done

# ---- provenance -----------------------------------------------------------

jq -n --arg s "$(basename "$SRC")" --arg c "$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null)" \
      --arg d "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  '{source:$s, commit:$c, installed:$d}' >"$TARGET/.loop/.installed"
say "  stamped .loop/.installed (source commit $(git -C "$SRC" rev-parse --short HEAD 2>/dev/null))"

# ---- prove it -------------------------------------------------------------
#
# The suite is the install test: it runs in the TARGET, against the copy that
# just landed there. --no-proof skips it, for a re-run that only refreshes the
# mechanism and for the scenario that checks this installer's own boundary.

if [[ "$PROOF" -eq 0 ]]; then
  say "skipping the suite run (--no-proof)"
else
  say "running the loop's own suite in the target — this is the install test"
  if ( cd "$TARGET" && .loop/tests/run-all.sh >/tmp/install-suite.log 2>&1 ); then
    say "  $(grep -oE '[0-9]+ passed' /tmp/install-suite.log | tail -1) — the install works"
  else
    warn "  suite did not pass; see /tmp/install-suite.log"
    grep -E '^  .\[31mFAIL' /tmp/install-suite.log | head -5
  fi
fi

cat <<NEXT

Installed. The whole footprint is .loop/ plus .claude/skills/loop-*, one
merged section in CLAUDE.md, and one line in .gitignore. Your
.claude/settings.json was not touched.

Two things are stack-specific and yours to set:

  1. .claude/settings.json — add the commands your gates need, e.g.
       "Bash(pnpm:*)"   "Bash(npm:*)"   "Bash(go:*)"   "Bash(cargo:*)"
     The loop itself never names a test runner: each task carries its own
     verify command, so the gate list is your plan's, not the loop's. The
     loop's own fence is separate and already in place (.loop/settings.json),
     so nothing you add here can be silently overwritten by an upgrade.

  2. CLAUDE.md — the loop section was added between the loop:begin/end
     markers. Add a toolchain note of your own above or below it.

Read .loop/manual.md before writing your first brief; .loop/examples/ has two
that drove real runs. Then:
  .loop/check-brief.sh <your-brief.md>
  claude                     # once, interactively, and accept the trust dialog
  .loop/run.sh <your-brief.md>
NEXT
