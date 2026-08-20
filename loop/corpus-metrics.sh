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
#   ./corpus-metrics.sh --tick                            # + per-tick resident estimate
#   ./corpus-metrics.sh --tick --plan loop/plan.md        # name the plan file explicitly
#   ./corpus-metrics.sh --tick --tick-role implementer    # estimate for one named role
#
# Reporting tool, not a gate: exits 0 on success, never edits a file.
#
# See README-corpus-metrics.md (alongside this script) for what each metric
# means and which ones are worth quoting.

set -euo pipefail

ROOT=""
NAME=""
INCLUDE_SELF="false"
TICK="false"
PLAN=""
TICK_ROLE=""
SELF="$(basename "$0")"

usage() { sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --root) ROOT="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --include-self) INCLUDE_SELF="true"; shift ;;
    --tick) TICK="true"; shift ;;
    --plan) PLAN="${2:-}"; TICK="true"; shift 2 ;;
    --tick-role) TICK_ROLE="${2:-}"; TICK="true"; shift 2 ;;
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

# ------------------------------------------- 2.5 per-tick resident estimate
#
# The corpus total is a MAINTENANCE-SURFACE number. It is not what any single
# model context holds. This section estimates the latter: what one loop tick
# actually loads.
#
#   base      = orchestration prose (always injected) + one role definition
#   citations = the guideline / design-note files a task's own citation lines
#               name, which agent contracts require be read IN FULL
#   resident  = base + citations, per role, per task
#
# Roles are listed, not chosen — which ones open a context per tick is
# repo-specific knowledge the script cannot infer. Read the per-role rows.

TICK_JSON=""
if [ "$TICK" = "true" ]; then
  TICK_JSON="$TMP/tick.json"
  ALWAYS="$TMP/always.tsv"; ROLES="$TMP/roles.tsv"; CITES="$TMP/cites.tsv"
  : > "$ALWAYS"; : > "$ROLES"; : > "$CITES"

  # (a) always-resident: orchestration prose every role reads
  for f in "$ROOT/CLAUDE.md" "$ROOT/.claude/project-adapter.md"; do
    [ -f "$f" ] && { set -- $(count "$f"); printf '%s\t%s\t%s\n' "${f#"$ROOT"/}" "$2" "$3" >> "$ALWAYS"; }
  done

  # (b) roles: an agent definition, or a SKILL.md, is one context the loop opens
  if [ -d "$ROOT/.claude/agents" ]; then
    find "$ROOT/.claude/agents" -type f -name '*.md' | sort | while IFS= read -r f; do
      set -- $(count "$f")
      printf 'agent\t%s\t%s\t%s\t%s\n' "$(basename "$f" .md)" "${f#"$ROOT"/}" "$2" "$3" >> "$ROLES"
    done
  fi
  if [ -d "$ROOT/.claude/skills" ]; then
    find "$ROOT/.claude/skills" -type f -name 'SKILL.md' | sort | while IFS= read -r f; do
      set -- $(count "$f")
      printf 'skill\t%s\t%s\t%s\t%s\n' "$(basename "$(dirname "$f")")" "${f#"$ROOT"/}" "$2" "$3" >> "$ROLES"
    done
  fi

  # (c) citations: resolve each task's Guidelines: / Design notes: block
  if [ -z "$PLAN" ]; then
    for cand in PLAN.md loop/plan.md plan.md; do
      [ -f "$ROOT/$cand" ] && { PLAN="$cand"; break; }
    done
  fi
  if [ -n "$PLAN" ] && [ -f "$ROOT/$PLAN" ]; then
    awk '
      /^- \[[ x]\][[:space:]]*\*{0,2}T[0-9]+/ {
        if (match($0, /T[0-9]+/)) task = substr($0, RSTART, RLENGTH)
        incite = 0; next
      }
      /\*\*(Guidelines|Design notes):\*\*/ { incite = 1; next }
      /^[[:space:]]*\*\*[A-Za-z]/ { incite = 0; next }
      incite && /^[[:space:]]*$/ { incite = 0; next }
      incite && /^[[:space:]]*-[[:space:]]/ {
        line = $0
        while (match(line, /[A-Za-z0-9_@.\/-]+\.md/)) {
          if (task != "") print task "\t" substr(line, RSTART, RLENGTH)
          line = substr(line, RSTART + RLENGTH)
        }
      }
    ' "$ROOT/$PLAN" | sort -u | while IFS="$(printf '\t')" read -r task path; do
      if [ -f "$ROOT/$path" ]; then
        set -- $(count "$ROOT/$path")
        printf '%s\t%s\t%s\t%s\t1\n' "$task" "$path" "$2" "$3" >> "$CITES"
      else
        printf '%s\t%s\t0\t0\t0\n' "$task" "$path" >> "$CITES"
      fi
    done
  fi

  INSTR_W="$(awk -F'\t' '$1=="instructions"{w+=$5} END{print w+0}' "$ROWS")"
  INSTR_C="$(awk -F'\t' '$1=="instructions"{c+=$6} END{print c+0}' "$ROWS")"

  awk -v plan="${PLAN:-}" -v instr_w="$INSTR_W" -v instr_c="$INSTR_C" -v want="$TICK_ROLE" \
      -v alwaysf="$ALWAYS" -v rolesf="$ROLES" -v citesf="$CITES" '
  function j(s) { gsub(/\\/, "\\\\", s); gsub(/"/, "\\\"", s); return s }
  function tok(c) { return int(c / 4 + 0.5) }
  function pct(a, b) { return (b == 0) ? "null" : sprintf("%.3f", a / b) }
  BEGIN {
    while ((getline line < alwaysf) > 0) {
      split(line, a, "\t"); an++; ap[an] = a[1]; aw += a[2]; ac += a[3]
    }
    while ((getline line < rolesf) > 0) {
      split(line, r, "\t"); rn++
      rk[rn] = r[1]; rname[rn] = r[2]; rp[rn] = r[3]; rw[rn] = r[4]; rc[rn] = r[5]
    }
    while ((getline line < citesf) > 0) {
      split(line, c, "\t")
      if (!(c[1] in tseen)) { tn++; torder[tn] = c[1]; tseen[c[1]] = 1 }
      tw[c[1]] += c[3]; tc[c[1]] += c[4]; tf[c[1]] += 1
      if (c[5] == "0") { miss[c[2]] = 1 } else { distinct[c[2]] = 1 }
    }
    # per-task citation cost, sorted, for min / median / max
    for (i = 1; i <= tn; i++) { v[i] = tc[torder[i]]; vw[i] = tw[torder[i]] }
    for (i = 2; i <= tn; i++) {
      kc = v[i]; kw2 = vw[i]; k = i - 1
      while (k > 0 && v[k] > kc) { v[k+1] = v[k]; vw[k+1] = vw[k]; k-- }
      v[k+1] = kc; vw[k+1] = kw2
    }
    if (tn > 0) {
      mn = v[1]; mnw = vw[1]; mx = v[tn]; mxw = vw[tn]
      if (tn % 2) { md = v[(tn+1)/2]; mdw = vw[(tn+1)/2] }
      else { md = int((v[tn/2] + v[tn/2+1]) / 2); mdw = int((vw[tn/2] + vw[tn/2+1]) / 2) }
    }
    # Which role to estimate. --tick-role names one (agent preferred on a tie);
    # otherwise the heaviest agent context, else the heaviest role of any kind.
    # NB the heaviest agent is not necessarily a PER-TICK role (a planner runs
    # once per plan) — name the role you mean when it matters.
    hi = 0
    if (want != "") {
      for (i = 1; i <= rn; i++) if (rname[i] == want && rk[i] == "agent") hi = i
      if (hi == 0) for (i = 1; i <= rn; i++) if (rname[i] == want) hi = i
      if (hi == 0) { printf "corpus-metrics.sh: no such role: %s\n", want > "/dev/stderr"; exit 2 }
    }
    if (hi == 0) for (i = 1; i <= rn; i++) if (rk[i] == "agent" && rc[i] > rc[hi]+0) hi = i
    if (hi == 0) for (i = 1; i <= rn; i++) if (rc[i] > rc[hi]+0) hi = i

    printf "  \"tick\": {\n"
    printf "    \"plan_file\": %s,\n", (plan == "" ? "null" : "\"" j(plan) "\"")
    printf "    \"always_resident\": { \"files\": [", an
    for (i = 1; i <= an; i++) printf "%s\"%s\"", (i > 1 ? ", " : ""), j(ap[i])
    printf "], \"words\": %d, \"chars\": %d, \"est_tokens\": %d },\n", aw, ac, tok(ac)
    printf "    \"roles\": [\n"
    for (i = 1; i <= rn; i++) {
      printf "      { \"role\": \"%s\", \"kind\": \"%s\", \"path\": \"%s\", \"definition_tokens\": %d, \"base_tokens\": %d }%s\n",
             j(rname[i]), rk[i], j(rp[i]), tok(rc[i]), tok(rc[i] + ac), (i < rn ? "," : "")
    }
    printf "    ],\n"
    printf "    \"citations\": { \"tasks\": %d, \"distinct_files\": %d, \"per_task_tokens\": ", tn, length(distinct)
    if (tn > 0) printf "{ \"min\": %d, \"median\": %d, \"max\": %d }", tok(mn), tok(md), tok(mx)
    else printf "null"
    printf ", \"unresolved\": ["
    ui = 0
    for (m in miss) { printf "%s\"%s\"", (ui++ ? ", " : ""), j(m) }
    printf "] },\n"
    printf "    \"estimate\": {\n"
    printf "      \"role\": \"%s\",\n", (hi ? j(rname[hi]) : "")
    printf "      \"role_selected_by\": \"%s\",\n", (want != "" ? "--tick-role" : "heaviest agent context")
    printf "      \"floor_tokens\": %d,\n", tok(rc[hi] + ac)
    printf "      \"median_tokens\": %d,\n", tok(rc[hi] + ac + md)
    printf "      \"ceiling_tokens\": %d,\n", tok(rc[hi] + ac + mx)
    printf "      \"median_share_of_instruction_corpus\": %s\n", pct(rc[hi] + ac + md, instr_c)
    printf "    }\n"
    printf "  },\n"
  }' > "$TICK_JSON"
fi

# ------------------------------------------------------ 3. emit the JSON

COMMIT="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo null)"
BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo null)"
DIRTY="false"; [ -n "$(git -C "$ROOT" status --porcelain 2>/dev/null)" ] && DIRTY="true"
GENERATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

awk -F'\t' -v name="$NAME" -v root="$ROOT" -v commit="$COMMIT" -v branch="$BRANCH" \
           -v dirty="$DIRTY" -v generated="$GENERATED" -v tickfile="$TICK_JSON" '
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

  if (tickfile != "") { while ((getline tl < tickfile) > 0) print tl }

  printf "  \"files\": [\n"
  for (i = 1; i <= n; i++) printf "%s%s\n", FILES[i], (i < n ? "," : "")
  printf "  ]\n}\n"
}
' "$ROWS"
