#!/usr/bin/env bash
# Brief 0002 §6 promises budgets are per-run and checked at iteration
# boundaries, so raising one and re-running "just works" with no state edit.
# This is that promise, tested.
. "$(dirname "$0")/../lib.sh"
fixture_new
fixture_plan "$PLAN_TWO"
fixture_stub_default
LOOP_MAX_ITERATIONS=1 fixture_run docs/briefs/0003-runstat-cli.md
assert_exit 4
assert_run_status max_iterations
assert_status T1 done
assert_status T2 pending
note "re-running with no state edit"
fixture_run
assert_exit 0
assert_run_status complete
assert_status T2 done
finish
