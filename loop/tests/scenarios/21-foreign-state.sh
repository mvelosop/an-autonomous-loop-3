#!/usr/bin/env bash
# A branch cut from main inherits whatever loop/state.json the last squash left
# there — another branch's plan, usually finished. Resuming it as if it were
# this branch's work would be silent nonsense: the loop would report a complete
# plan that has nothing to do with the brief in front of it.
#
# The rule that replaced "state must survive a merge in both directions":
#   - merging main INTO a branch preserves the branch's state (a merge concern,
#     documented in loop/README, deliberately not mechanised — see there)
#   - a run that FINDS foreign state resets it, or refuses
#
# Refusing without a brief matters as much as resetting with one: a stale branch
# stamp must never silently destroy a live plan.
. "$(dirname "$0")/../lib.sh"

fixture_new
fixture_plan "$PLAN_TWO"
fixture_stub_default
fixture_run docs/briefs/0003-runstat-cli.md
assert_exit 0

got="$(fx_state '.branch')"
want="$(git -C "$FX/repo" branch --show-current)"
[[ "$got" == "$want" ]] && ok "state stamped with its owning branch ($got)" \
  || bad "state.branch: got '$got', want '$want'"

note "pretending this state was inherited from another branch"
( cd "$FX/repo" && jq '.branch = "some-other-branch"' loop/state.json > s.tmp && mv s.tmp loop/state.json )

note "no brief given — must refuse rather than resume it"
fixture_run
assert_exit 1
assert_log "belongs to branch 'some-other-branch'"
assert_log "will not be resumed here"
[[ -f "$FX/repo/loop/state.json" ]] && ok "refusing left the state untouched" \
  || bad "refusing destroyed the state"

note "brief given — explicit intent to start a plan, so reset"
fixture_run docs/briefs/0003-runstat-cli.md
assert_exit 0
assert_log "resetting and planning fresh"
[[ "$(fx_state '.branch')" == "$want" ]] && ok "fresh plan is stamped with this branch" \
  || bad "reset plan carries the wrong branch"

# The log line above is printed BEFORE the reset, and a resume re-stamps the
# branch too — so neither distinguishes "reset and re-planned" from "quietly
# resumed the foreign plan". A plan session only runs when state is actually
# gone, so that is the assertion that gates it.
last="$(ls -dt "$FX/repo"/loop/runs/*/*/ | head -1)"
ls "$last"sessions/*-plan.json >/dev/null 2>&1 \
  && ok "a plan session ran — state was genuinely reset, not resumed" \
  || bad "no plan session in the last run: the foreign state was resumed, not reset"
finish
