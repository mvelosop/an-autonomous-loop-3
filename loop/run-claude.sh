#!/usr/bin/env bash
#
# An operator session with loop-shaped telemetry.
#
#   loop/run-claude.sh [claude args...]
#
# Rule 7 says the operator has to stay positioned to notice that a run is going
# nowhere, because no in-loop gate can. That judgement is made in a session the
# loop never sees, and until now it left no trace: the loop's own sessions are
# measured to four decimal places while the sessions that decide whether the
# loop was worth running at all are invisible. This wraps one interactive
# `claude` so it lands in the same telemetry shape as a plan/work/review
# session, under its own run directory.
#
#   loop/runs/<branch>/<run-id>/sessions/operator.json
#
# Unlike run.sh's phases this is NOT fenced — no --setting-sources, no
# --strict-mcp-config, no forced model. It is your normal session, with your
# settings and your MCP servers, because its job is to think about the run
# rather than to be comparable with it. Read the telemetry accordingly: the
# token counts are exact, but they were spent under a different configuration.
#
# How it captures anything at all: an interactive session has no `--output-format
# json` to redirect, so the result is reconstructed afterwards from the session
# transcript at ~/.claude/projects/<cwd-slug>/<session-id>.jsonl. To know which
# transcript is ours we assign the id up front with --session-id rather than
# discovering it after the fact. Verified field-by-field against the thirteen
# sessions of run 004-runstat-review/20260817-233203: session_id, result,
# num_turns and all four usage counters reproduce exactly, duration_ms to
# within 55ms.
#
# What cannot be reconstructed
#   total_cost_usd    nowhere on disk — it lives in the session's memory and
#                     dies with it. Run /cost before you exit and paste it when
#                     asked, or the field is 0 and cost_source says so.
#   permission_denials  not recorded in the transcript. Always [].
#   ttft_ms, stop_reason, api_error_status  not recorded. Omitted, not faked.
#
# Exit code is claude's own, passed straight through.
#
# Env
#   LOOP_OPERATOR_COST    dollars, skips the prompt (use in non-interactive callers)
#   LOOP_OPERATOR_NOTE    one line of why-this-session, stored as .note
#   LOOP_ARCHIVE_TRANSCRIPTS=1   copy the transcript out of ~/.claude
#   LOOP_TRANSCRIPT_DIR   where to put it  (default ../loop-transcripts)

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

LOOP_DIR="$REPO/loop"

BRANCH="$(git branch --show-current 2>/dev/null)"
[[ -n "$BRANCH" ]] || BRANCH="detached-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BRANCH_SAFE="${BRANCH//\//-}"

# Same collision guard as run.sh: second-resolution stamps collide when you
# start a session, bounce off something, and start another in the same second.
RUN_STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_ID="$RUN_STAMP"
_n=1
while [[ -d "$LOOP_DIR/runs/$BRANCH_SAFE/$RUN_ID" ]]; do
  _n=$((_n + 1)); RUN_ID="$RUN_STAMP-$_n"
done
RUN_PATH="$BRANCH_SAFE/$RUN_ID"
RUN_DIR="$LOOP_DIR/runs/$RUN_PATH"
SESSIONS="$RUN_DIR/sessions"
OUT="$SESSIONS/operator.json"

# ---------------------------------------------------------------- helpers ---

# Hard rule 2's backstop, same as run.sh. An interactive session is a richer
# source of absolute paths than a headless one, not a poorer one.
USER_NAME="$(basename "$HOME")"
mask() { sed -e "s#${HOME}#~#g" -e "s#${USER_NAME}#USER#g"; }

say()  { printf '\033[36m[operator]\033[0m %s\n' "$(printf '%s' "$*" | mask)" | tee -a "$RUN_DIR/loop.log" >&2; }
warn() { printf '\033[33m[operator]\033[0m %s\n' "$(printf '%s' "$*" | mask)" | tee -a "$RUN_DIR/loop.log" >&2; }
die()  { printf '\033[31m[operator] %s\033[0m\n' "$(printf '%s' "$*" | mask)" >&2; exit 1; }
ts()   { date -u +%Y-%m-%dT%H:%M:%SZ; }

for t in jq claude git uuidgen; do
  command -v "$t" >/dev/null 2>&1 || die "missing: $t"
done

mkdir -p "$SESSIONS" || die "cannot create $SESSIONS"
: >"$RUN_DIR/loop.log"

# Lowercased: uuidgen is uppercase on macOS, and the transcript is named with
# the id exactly as claude received it.
SID="$(uuidgen | tr '[:upper:]' '[:lower:]')"

# ------------------------------------------------------------ the session ---

say "run   $RUN_PATH"
say "sid   $SID"
say "unfenced — your settings, your MCP servers"
warn "run /cost before you exit; it cannot be recovered afterwards"

STDERR="$RUN_DIR/operator.stderr"
STARTED="$(ts)"

# stdout is the TUI and must stay on the terminal. stderr is redirected because
# a crash trace is the one thing worth keeping from a session that dies, and it
# is replayed below if it turns out to be non-empty.
claude --session-id "$SID" "$@" 2>"$STDERR"
rc=$?

ENDED="$(ts)"
say "exit  $rc"

# ------------------------------------------------------- reconstruct result ---

TRANSCRIPT="$(find "$HOME/.claude/projects" -maxdepth 2 -name "$SID.jsonl" -print -quit 2>/dev/null)"

if [[ -z "$TRANSCRIPT" ]]; then
  warn "no transcript for $SID — --no-session-persistence, or the session never started"
  warn "nothing to reconstruct; leaving $RUN_PATH without a session file"
  [[ -s "$STDERR" ]] && { warn "stderr:"; mask <"$STDERR" >&2; } || rm -f "$STDERR"
  exit $rc
fi

# Cost is the only number a human has to supply. Ask once, accept nothing, and
# record which it was — a 0 that reads as measured is worse than an absent one.
COST="${LOOP_OPERATOR_COST:-}"
if [[ -z "$COST" && -t 0 ]]; then
  printf '\033[36m[operator]\033[0m total cost from /cost, in dollars (Enter to skip): ' >&2
  read -r COST
fi
if [[ -n "$COST" && ! "$COST" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
  warn "'$COST' is not a number — recording cost as unavailable"
  COST=""
fi
if [[ -n "$COST" ]]; then COST_SOURCE="operator-reported"; else COST=0; COST_SOURCE="unavailable"; fi

# The reconstruction. Slurped because every derived field is an aggregate over
# the whole file. Two subtleties, both load-bearing:
#
#   * assistant lines are deduplicated by requestId. One API response is split
#     across several lines (thinking, text, each tool_use), and they all carry
#     the same usage block — summing lines rather than requests roughly doubles
#     the output-token count.
#   * num_turns is every user message that is not isMeta. isMeta lines are
#     injections the harness makes on your behalf (a skill body, a hook's
#     output); counting them would inflate a session with skills over one
#     without. Matches the CLI exactly on all thirteen reference sessions.
jq -s \
  --arg sid "$SID" --arg branch "$BRANCH" --arg run "$RUN_PATH" \
  --arg started "$STARTED" --arg ended "$ENDED" \
  --arg cost_source "$COST_SOURCE" --argjson cost "$COST" \
  --argjson rc "$rc" --arg note "${LOOP_OPERATOR_NOTE:-}" '

def tms:
  capture("^(?<d>[^.Z]+)(\\.(?<f>[0-9]+))?Z?$")
  | ((.d + "Z") | fromdateiso8601) * 1000
    + (((.f // "0") + "000")[0:3] | tonumber);

. as $all
| ($all | map(select(.type == "assistant" and ((.isSidechain // false) | not)))) as $a
| ($a | group_by(.requestId) | map(.[0]))                                        as $req
| (if ($a | length) > 0 then ($a | last | .requestId) else null end)             as $lastreq
| ($a | map(select(.requestId == $lastreq)))                                     as $tail
| ($all | map(.timestamp // empty | tms))                                        as $t
|
{
  type:        "result",
  subtype:     (if $rc == 0 then "success" else "error" end),
  phase:       "operator",
  iteration:   0,
  is_error:    ($rc != 0),
  exit_code:   $rc,
  session_id:  $sid,
  branch:      $branch,
  run:         $run,
  started_at:  $started,
  ended_at:    $ended,

  result:      ($tail | map(.message.content[]? | select(.type == "text") | .text) | join("")),
  num_turns:   ($all | map(select(.type == "user" and ((.isMeta // false) | not))) | length),
  duration_ms: (if ($t | length) > 1 then (($t | max) - ($t | min)) else 0 end),

  # Reconstructed from a transcript, never from stdout. permission_denials is
  # present because runstat requires the key, and empty because the transcript
  # does not record denials -- it is not evidence that none happened.
  permission_denials: [],
  reconstructed_from: "transcript",

  total_cost_usd: $cost,
  cost_source:    $cost_source,

  usage: {
    input_tokens:                ($req | map(.message.usage.input_tokens // 0)                | add // 0),
    cache_creation_input_tokens: ($req | map(.message.usage.cache_creation_input_tokens // 0) | add // 0),
    cache_read_input_tokens:     ($req | map(.message.usage.cache_read_input_tokens // 0)     | add // 0),
    output_tokens:               ($req | map(.message.usage.output_tokens // 0)               | add // 0),
    requests:                    ($req | length)
  },

  modelUsage: ($req | group_by(.message.model // "unknown")
    | map({ key: (.[0].message.model // "unknown"), value: {
        inputTokens:              (map(.message.usage.input_tokens // 0)                | add // 0),
        outputTokens:             (map(.message.usage.output_tokens // 0)               | add // 0),
        cacheReadInputTokens:     (map(.message.usage.cache_read_input_tokens // 0)     | add // 0),
        cacheCreationInputTokens: (map(.message.usage.cache_creation_input_tokens // 0) | add // 0),
        requests:                 length } })
    | from_entries),

  version: ($a | last | .version?),
  cwd:     ($a | last | .cwd?)
}
| if $note == "" then . else . + {note: $note} end
' "$TRANSCRIPT" | mask >"$OUT"

if [[ ! -s "$OUT" ]]; then
  rm -f "$OUT"
  die "reconstruction failed; transcript kept at $(printf '%s' "$TRANSCRIPT" | mask)"
fi

jq -r '"      turns=\(.num_turns) dur=\(((.duration_ms // 0)/1000)|round)s out=\(.usage.output_tokens) tok  cost=$\(.total_cost_usd) (\(.cost_source))"' \
  "$OUT" | while read -r l; do say "$l"; done

# Same policy as run.sh: an empty stderr is noise, a non-empty one is the
# evidence you want, so keep it and put it in front of the operator now.
if [[ -s "$STDERR" ]]; then
  warn "stderr was not empty:"
  mask <"$STDERR" >"$STDERR.masked" && mv "$STDERR.masked" "$STDERR"
  sed 's/^/    /' "$STDERR" >&2
else
  rm -f "$STDERR"
fi

# Transcripts hold absolute paths and whole file contents, so this is opt-in and
# never writes inside the repo.
if [[ "${LOOP_ARCHIVE_TRANSCRIPTS:-0}" == "1" ]]; then
  dest="${LOOP_TRANSCRIPT_DIR:-$REPO/../loop-transcripts}/$RUN_PATH"
  case "$(cd "$dest" 2>/dev/null && pwd)" in
    "$REPO"|"$REPO"/*) warn "refusing to archive transcripts inside the repo" ;;
    *) mkdir -p "$dest" && cp "$TRANSCRIPT" "$dest/operator.jsonl" && say "transcript archived" ;;
  esac
fi

say "wrote loop/runs/$RUN_PATH/sessions/operator.json"
exit $rc
