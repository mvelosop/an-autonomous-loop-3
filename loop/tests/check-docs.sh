#!/usr/bin/env bash
# Documentation paths, checked rather than re-read.
#
# Two failure modes, and the second is the one that actually happens: a link
# that points nowhere, and a doc that still describes a layout the loop has
# moved on from. Four stale references accumulated in two days of work here.
#
#   loop/tests/check-docs.sh
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.." || exit 1
fail=0

# 1. every backticked path must resolve — relative to its own doc, to the repo
#    root, or as a bare filename that exists somewhere. NNN/<x> are templates.
python3 - <<'PY' || fail=1
import re, pathlib, sys
root = pathlib.Path('.').resolve()
names = {p.name for p in root.rglob('*') if '/.git/' not in str(p)}
docs = [p for p in root.rglob('*.md')
        if '/.git/' not in str(p) and 'docs/references' not in str(p)
        and 'loop/runs' not in str(p) and 'loop/journals' not in str(p)]
pat = re.compile(r'`([A-Za-z0-9_./-]+\.(?:md|sh|json|py|jsonl|toml))`')
bad = []
for d in docs:
    for m in pat.finditer(d.read_text()):
        r = m.group(1)
        if r.startswith(('~', 'http')) or 'NNN' in r or '<' in r: continue
        if (d.parent / r).exists() or (root / r).exists() or r.split('/')[-1] in names: continue
        bad.append((d.relative_to(root), r))
for d, r in bad: print(f"  dead path  {d}: {r}")
sys.exit(1 if bad else 0)
PY

# 2. layouts the loop has retired must not be described as current
retired=(
  "loop/journal.md|one journal per plan lives at loop/journals/<plan-id>.md"
  "loop/runs/<run-id>|run dirs are branch-scoped: loop/runs/<branch>/<run-id>"
  "loop/runs/<timestamp>|run dirs are branch-scoped: loop/runs/<branch>/<timestamp>"
)
for entry in "${retired[@]}"; do
  patt="${entry%%|*}"; why="${entry##*|}"
  hits="$(grep -rn -F "$patt" --include='*.md' . 2>/dev/null \
          | grep -v './docs/references/\|./loop/runs/\|./loop/journals/' || true)"
  if [[ -n "$hits" ]]; then
    echo "  retired layout '$patt' still documented — $why"
    echo "$hits" | sed 's/^/      /'; fail=1
  fi
done

[[ $fail -eq 0 ]] && echo "docs ok — every path resolves, no retired layout described" || echo "docs FAILED"
exit $fail
