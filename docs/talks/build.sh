#!/usr/bin/env bash
#
# Build the meetup deck. One command, so a missing flag cannot quietly produce
# a deck with the wrong theme or with the palette script printed as a slide.
#
#   docs/talks/build.sh            HTML (the presenting deck)
#
# The QR codes are regenerated on every build from the address in qr.url; set
# it once with `qr.sh <url>`.
#   docs/talks/build.sh watch      rebuild the HTML on every save
#   docs/talks/build.sh pdf        PDF, light palette, for handouts
#   docs/talks/build.sh all        HTML + PDF
#
# The markdown holds content and nothing else. The palette switch lives in
# palette.js and is injected into the built HTML here — which is why no
# renderer needs `--html`, and why previewing the markdown anywhere shows
# slides rather than a wall of JavaScript.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

DECK="0001-autonomous-loop-meetup.md"
OUT="${DECK%.md}"

# Prefer a marp that is already on disk: `npx -y` re-resolves the package on
# every run, which turns a sub-second build into minutes on a bad connection —
# not what you want ten minutes before a talk.
marp_bin() {
  local found
  found="$(command -v marp || true)"
  [[ -n "$found" ]] && { printf '%s' "$found"; return; }
  found="$(ls -t "$HOME"/.npm/_npx/*/node_modules/.bin/marp 2>/dev/null | head -1 || true)"
  [[ -n "$found" ]] && { printf '%s' "$found"; return; }
  printf 'npx'
}

BIN="$(marp_bin)"
if [[ "$BIN" == npx ]]; then
  MARP=(npx -y @marp-team/marp-cli@latest)
else
  MARP=("$BIN")
fi

# The input file goes FIRST, before any flag. `--theme-set` takes an array, so
# `marp --theme-set themes deck.md` swallows the deck into the theme list and
# marp then prints its usage and converts nothing — while the previous build
# sits on disk looking like a successful one.
THEME=(--theme-set themes)

# `--allow-local-files` is only needed to let the PDF renderer read the SVGs off
# disk. Passing it to an HTML build routes the whole thing through Chromium and
# turns 0.4s into minutes, so it stays out of build_html.

build_html() {
  # Refresh the QR codes first: the references code carries the last slide's
  # number, so adding a slide would otherwise leave it pointing at the wrong one
  # while still looking perfectly valid.
  ./qr.sh
  # </dev/null: marp waits on stdin when it is a pipe, which hangs the build
  # when this script runs from an editor, a hook, or a CI step.
  "${MARP[@]}" "$DECK" "${THEME[@]}" -o "$OUT.html" </dev/null
  python3 - "$OUT.html" palette.js <<'PY'
import pathlib, sys
page, script = (pathlib.Path(p) for p in sys.argv[1:3])
html = page.read_text()

tag = "<script>\n" + script.read_text() + "</script>\n</body>"
page.write_text(html.replace("</body>", tag, 1))
PY
  echo "  → $OUT.html — press t to switch palette"
}

# PDF bakes one palette, and a projector-lit room is not where you want the dark
# one. Build it from a copy whose slides carry `lightmode`.
build_pdf() {
  local tmp="${TMPDIR:-/tmp}/loop-deck-light.md"
  sed 's/^class: loop$/class: loop lightmode/' "$DECK" >"$tmp"
  "${MARP[@]}" "$tmp" "${THEME[@]}" --pdf --allow-local-files -o "$OUT.pdf" </dev/null
  rm -f "$tmp"
  echo "  → $OUT.pdf"
}

# Marp's own --watch would overwrite the injected script on every rebuild, so
# watch the sources here and run the real build each time one of them changes.
watch() {
  local sources=("$DECK" palette.js themes/loop.css)
  local last="" now
  echo "watching: ${sources[*]}  (ctrl-c to stop)"
  build_html
  while true; do
    now="$(stat -f '%m' "${sources[@]}" 2>/dev/null | tr '\n' ' ')"
    if [[ "$now" != "$last" && -n "$last" ]]; then
      printf '%s  ' "$(date '+%H:%M:%S')"
      build_html
    fi
    last="$now"
    sleep 1
  done
}

case "${1:-html}" in
  html)  build_html ;;
  pdf)   build_pdf ;;
  watch) watch ;;
  all)   build_html; build_pdf ;;
  *)     echo "usage: build.sh [html|watch|pdf|all]" >&2; exit 2 ;;
esac
