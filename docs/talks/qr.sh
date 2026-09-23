#!/usr/bin/env bash
#
# Generate the deck's QR codes: one for the deck, one for its references slide.
#
#   docs/talks/qr.sh                      use the remembered address
#   docs/talks/qr.sh https://example.com/talk   set it and remember it
#
# The address is stored in qr.url, so `build.sh` can refresh the codes on every
# build without being told again. The references code points at the LAST slide,
# counted from the markdown — insert a slide and the anchor follows, which is
# the one thing nobody notices going stale.
#
# The codes are drawn dark-on-white with a quiet zone, so they scan against
# either palette — a white card on a dark slide, invisible on a light one.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

DECK="0001-autonomous-loop-meetup.md"
URL_FILE="qr.url"
DEFAULT_URL="https://miguelveloso.dev/blog/an-autonomous-loop/"

if [[ $# -gt 0 ]]; then
  printf '%s\n' "$1" >"$URL_FILE"
fi
DECK_URL="$(cat "$URL_FILE" 2>/dev/null || printf '%s' "$DEFAULT_URL")"

# Slides are what the front matter leaves behind, split on `---` lines. Bespoke
# addresses them by number from 1, so the last slide is the count itself.
last_slide() {
  python3 - "$DECK" <<'PY'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text()
body = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)  # drop front matter
print(len(re.split(r"(?m)^---$", body)))
PY
}

LAST="$(last_slide)"
REFS_URL="${DECK_URL}#${LAST}"

qr() {
  uv run --quiet --with segno python - "$1" "$2" <<'PY'
import sys, segno
url, dest = sys.argv[1], sys.argv[2]
segno.make(url, error='m').save(dest, kind='svg', scale=10, border=3,
                                dark='#0E1116', light='#FFFFFF')
PY
  echo "  $2 ← $1"
}

qr "$DECK_URL" assets/qr-deck.svg
qr "$REFS_URL" assets/qr-refs.svg
