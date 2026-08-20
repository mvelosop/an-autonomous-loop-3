#!/usr/bin/env bash
# corpus-metrics.sh — machine-readable size metrics for an agent loop's
# INSTRUCTION CORPUS (prose a model interprets) and EXECUTABLE HARNESS
# (code a shell runs), emitted as JSON on stdout.
#
# Goal: compare two loop implementations on the same basis. The headline is
# not "how big" but WHERE THE CONTRACT LIVES — prose a reviewer reads vs.
# code that exits non-zero — and, inside the harness, PRODUCTION lines (run
# during a loop tick) vs. TEST lines (never run during a tick; they are
# evidence the harness works, not part of the machine).
#
# Portable across repo layouts: instruction dirs are detected under .claude/,
# harness dirs from a candidate list, so one copy measures any repo.
#
#   ./corpus-metrics.sh                                   # measure $PWD
#   ./corpus-metrics.sh --root ../other-repo --name theirs
#   ./corpus-metrics.sh --root . > metrics.json
#
# Reporting tool, not a gate: exits 0 on success, never edits a file.
#
# See README-corpus-metrics.md (alongside this script) for what each metric
# means and which ones are worth quoting.

set -euo pipefail

ROOT=""
NAME=""
INCLUDE_SELF="false"
SELF="$(basename "$0")"

usage() { sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --root) ROOT="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --include-self) INCLUDE_SELF="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "corpus-metrics.sh: unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="${ROOT:-$PWD}"
[ -d "$ROOT" ] || { echo "corpus-metrics.sh: no such directory: $ROOT" >&2; exit 2; }
ROOT="$(cd "$ROOT" && pwd)"
NAME="${NAME:-$(basename "$ROOT")}"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ROWS="$TMP/rows.tsv"; INSTR_LIST="$TMP/instr.txt"
: > "$ROWS"; : > "$INSTR_LIST"

# ---------------------------------------------------------------- helpers

# count <file> -> "lines words chars codelines"
count() {
  local f="$1" lines words chars code
  set -- $(wc -lwc < "$f")
  lines="$1"; words="$2"; chars="$3"
  # non-blank, non-comment — meaningful for shell/python, noise for prose
  code="$(grep -cvE '^[[:space:]]*(#|$)' "$f" 2>/dev/null || true)"
  [ -n "$code" ] || code=0
  printf '%s %s %s %s' "$lines" "$words" "$chars" "$code"
}

# row <category> <subcategory> <file> [in_loop]
row() {
  local cat="$1" sub="$2" f="$3" in_loop="${4:-null}" rel
  rel="${f#"$ROOT"/}"
  set -- $(count "$f")
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$cat" "$sub" "$rel" "$1" "$2" "$3" "$4" "$in_loop" >> "$ROWS"
}

# is_test <path> -> 0 when the file is test/fixture code
is_test() {
  case "$1" in
    */tests/*|*/test/*|*.fixture.sh|*/test-*.sh|*-test.sh|*_test.py|*/conftest.py) return 0 ;;
  esac
  return 1
}

# ------------------------------------------------- 1. instruction corpus

if [ -d "$ROOT/.claude/agents" ]; then
  find "$ROOT/.claude/agents" -type f -name '*.md' | sort | while IFS= read -r f; do
    row instructions agents "$f"
  done
fi

# SKILL.md bodies are the contract; references/templates/samples are support
if [ -d "$ROOT/.claude/skills" ]; then
  find "$ROOT/.claude/skills" -type f -name '*.md' | sort | while IFS= read -r f; do
    case "$(basename "$f")" in
      SKILL.md) row instructions skills_body "$f" ;;
      *)        row instructions skills_support "$f" ;;
    esac
  done
fi

# *.guidelines.md is the binding surface; other .md in that dir is an index
if [ -d "$ROOT/.claude/guidelines" ]; then
  find "$ROOT/.claude/guidelines" -type f -name '*.md' | sort | while IFS= read -r f; do
    case "$(basename "$f")" in
      *.guidelines.md) row instructions guidelines "$f" ;;
      *)               row other index "$f" ;;
    esac
  done
fi

# orchestration prose outside a segment dir — reported, not in the total
for f in "$ROOT/CLAUDE.md" "$ROOT/.claude/README.md" "$ROOT/.claude/project-adapter.md"; do
  [ -f "$f" ] && row other orchestration "$f"
done

# Call sites for `in_loop`: agents / skills / guidelines ONLY. CLAUDE.md and
# other orchestration prose are deliberately excluded — a script merely named
# there (e.g. per-machine setup) is not invoked by the loop.
awk -F'\t' '$1=="instructions" {print $3}' "$ROWS" > "$INSTR_LIST"

# ----------------------------------------------------- 2. harness (code)

HARNESS_DIRS=""
for d in .claude/scripts loop scripts bin tools; do
  [ -d "$ROOT/$d" ] && HARNESS_DIRS="$HARNESS_DIRS $d"
done

for d in $HARNESS_DIRS; do
  find "$ROOT/$d" -type f \( -name '*.sh' -o -name '*.py' -o -name '*.bash' \) | sort |
  while IFS= read -r f; do
    base="$(basename "$f")"
    # A measurement tool must not inflate its own measurement.
    if [ "$base" = "$SELF" ] && [ "$INCLUDE_SELF" != "true" ]; then continue; fi
    if is_test "$f"; then
      row harness tests "$f"
    else
      in_loop=false
      while IFS= read -r i; do
        [ -f "$ROOT/$i" ] || continue
        if grep -qF "$base" "$ROOT/$i" 2>/dev/null; then in_loop=true; break; fi
      done < "$INSTR_LIST"
      row harness production "$f" "$in_loop"
    fi
  done
done

# ------------------------------------------------------ 3. emit the JSON

COMMIT="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo null)"
BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo null)"
DIRTY="false"; [ -n "$(git -C "$ROOT" status --porcelain 2>/dev/null)" ] && DIRTY="true"
GENERATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

awk -F'\t' -v name="$NAME" -v root="$ROOT" -v commit="$COMMIT" -v branch="$BRANCH" \
           -v dirty="$DIRTY" -v generated="$GENERATED" '
function j(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); return s }
function seg(label, l, w, ch, c, f) {
  printf "      \"%s\": { \"files\": %d, \"lines\": %d, \"words\": %d, \"chars\": %d, \"est_tokens\": %d, \"code_lines\": %d }",
         label, f, l, w, ch, int(ch / 4 + 0.5), c
}
function ratio(a, b) { return (b == 0) ? "null" : sprintf("%.2f", a / b) }
{
  k = $1 "/" $2
  SL[k] += $4; SW[k] += $5; SH[k] += $6; SC[k] += $7; SF[k] += 1
  CL[$1] += $4; CW[$1] += $5; CH[$1] += $6; CC[$1] += $7; CF[$1] += 1
  if ($1 == "harness" && $2 == "production") {
    ik = ($8 == "true") ? "in_loop" : "operator"
    IL[ik] += $4; IW[ik] += $5; IH[ik] += $6; IC[ik] += $7; IF[ik] += 1
  }
  n += 1
  FILES[n] = sprintf("    { \"path\": \"%s\", \"category\": \"%s\", \"subcategory\": \"%s\", \"lines\": %d, \"words\": %d, \"chars\": %d, \"code_lines\": %d, \"in_loop\": %s }",
                     j($3), $1, $2, $4, $5, $6, $7, ($8 == "" ? "null" : $8))
}
END {
  sb = "instructions/skills_body"; ss = "instructions/skills_support"
  kl = SL[sb] + SL[ss]; kw = SW[sb] + SW[ss]; kh = SH[sb] + SH[ss]
  kc = SC[sb] + SC[ss]; kf = SF[sb] + SF[ss]

  printf "{\n"
  printf "  \"name\": \"%s\",\n", j(name)
  printf "  \"root\": \"%s\",\n", j(root)
  printf "  \"commit\": \"%s\",\n", j(commit)
  printf "  \"branch\": \"%s\",\n", j(branch)
  printf "  \"dirty\": %s,\n", dirty
  printf "  \"generated_at\": \"%s\",\n", j(generated)
  printf "  \"segments\": {\n"

  printf "    \"instructions\": {\n"
  seg("agents",         SL["instructions/agents"], SW["instructions/agents"], SH["instructions/agents"], SC["instructions/agents"], SF["instructions/agents"]); printf ",\n"
  seg("skills",         kl, kw, kh, kc, kf);                                                                                                                   printf ",\n"
  seg("skills_body",    SL[sb], SW[sb], SH[sb], SC[sb], SF[sb]);                                                                                               printf ",\n"
  seg("skills_support", SL[ss], SW[ss], SH[ss], SC[ss], SF[ss]);                                                                                               printf ",\n"
  seg("guidelines",     SL["instructions/guidelines"], SW["instructions/guidelines"], SH["instructions/guidelines"], SC["instructions/guidelines"], SF["instructions/guidelines"]); printf ",\n"
  seg("total",          CL["instructions"], CW["instructions"], CH["instructions"], CC["instructions"], CF["instructions"]);                                    printf "\n    },\n"

  printf "    \"harness\": {\n"
  seg("production",          SL["harness/production"], SW["harness/production"], SH["harness/production"], SC["harness/production"], SF["harness/production"]); printf ",\n"
  seg("production_in_loop",  IL["in_loop"],  IW["in_loop"],  IH["in_loop"],  IC["in_loop"],  IF["in_loop"]);                                                    printf ",\n"
  seg("production_operator", IL["operator"], IW["operator"], IH["operator"], IC["operator"], IF["operator"]);                                                   printf ",\n"
  seg("tests",               SL["harness/tests"], SW["harness/tests"], SH["harness/tests"], SC["harness/tests"], SF["harness/tests"]);                          printf ",\n"
  seg("total",               CL["harness"], CW["harness"], CH["harness"], CC["harness"], CF["harness"]);                                                        printf "\n    },\n"

  printf "    \"other\": {\n"
  seg("orchestration", SL["other/orchestration"], SW["other/orchestration"], SH["other/orchestration"], SC["other/orchestration"], SF["other/orchestration"]); printf ",\n"
  seg("index",         SL["other/index"], SW["other/index"], SH["other/index"], SC["other/index"], SF["other/index"]);                                         printf ",\n"
  seg("total",         CL["other"], CW["other"], CH["other"], CC["other"], CF["other"]);                                                                       printf "\n    }\n"
  printf "  },\n"

  printf "  \"ratios\": {\n"
  printf "    \"instruction_words_per_harness_word\": %s,\n",           ratio(CW["instructions"], CW["harness"])
  printf "    \"instruction_words_per_in_loop_harness_word\": %s,\n",   ratio(CW["instructions"], IW["in_loop"])
  printf "    \"test_lines_per_production_line\": %s,\n",               ratio(SL["harness/tests"], SL["harness/production"])
  printf "    \"test_share_of_harness_lines\": %s\n",                   ratio(SL["harness/tests"], CL["harness"])
  printf "  },\n"

  printf "  \"files\": [\n"
  for (i = 1; i <= n; i++) printf "%s%s\n", FILES[i], (i < n ? "," : "")
  printf "  ]\n}\n"
}
' "$ROWS"
