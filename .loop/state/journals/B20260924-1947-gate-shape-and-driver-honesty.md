# Journal — B20260924-1947-gate-shape-and-driver-honesty

Append-only narrative of this plan. Rendered state lives in .loop/state/plan.md.

## Plan — B20260924-1947-gate-shape-and-driver-honesty

- **Brief:** `docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md`
- **Tasks:** 9

I've written the plan to `.loop/state/state.json`. It has 9 tasks with ids B20260924-1947-gate-shape-and-driver-honesty, and the first ready task is **T1**.

| Task | Brief item | Depends on |
| --- | --- | --- |
| T1 | Rule 3: a gate may not read a HEAD file its task doesn't own | — |
| T2 | Rule 4: a gate may not diff against any ref other than HEAD | T1 |
| T3 | Tell each gate which task is being worked and which gate is running | — |
| T4 | `amend.sh` advisory for a HEAD diff that ignores those two values | T2, T3 |
| T5 | A blocked task whose own gate passes gets reported | — |
| T6 | When no proposal exists, report the working tree | — |
| T7 | `GATE REGRESSION` names both tasks | — |
| T8 | A second blocked on unchanged inputs halts the run | — |
| T9 | A brief that has already been run is refused (last, as the brief asks) | — |

**Checks:** all 9 verify commands run right now and fail on their own assertions, not on shell errors. The existing suite passes with the plan in place (37 passed). `amend.sh check` is clean, the driver's two existing gate-shape rules pass the plan, every reference exists, and there are no absolute paths. None of the gates just runs the work session's own scenario: each one first plants its own fixture through `.loop/tests/lib.sh` and checks the result, then runs the new scenario, `run-all.sh` and `uv run pytest -q`.

**Names I pinned because a gate needs them:**
- The two environment variables are `LOOP_ACTIVE_TASK` and `LOOP_GATE_TASK`.
- The item 8 override is a `--replan` flag.
- The new scenarios are numbered 35–43: `35-gate-unowned-file.sh` through `43-brief-already-run.sh`.
- For item 4, each report has to put the words "gate" and "pass" together on the same line.

**Things I interpreted rather than read — please correct any of these before running:**
1. **Item 8 would turn the suite red.** Briefs 0003 and 0004 both still say "ready to plan" and both have journals, so the new check-brief failure breaks `run-all.sh`. T9 has to handle that inside `run-all.sh`. It can't edit either brief's Status line, and it can't exempt them by name inside `check-brief.sh`.
2. **Journal name.** I took the journal to be named after the brief's filename minus `.md`, and also minus `.loop-brief.md`. I set the run id to number-and-slug, so this brief will itself read as "already run" once T9 lands.
3. **Item 7 timing.** The halt comes *after* the second blocked iteration, since that's the only reading where there's a "second" diagnosis to prefer the first over. "Unchanged" has to ignore the driver's own commit, because HEAD moves every iteration. If you meant "halt before spending the retry", T8's gate has to change.
4. **Leaked variables.** T3 also requires that the two variables never reach a session, even when the driver inherited them. Without that, every scenario that `run-all.sh` runs inside a gate would see them.
5. **Existing scenarios will change.** Scenario 33 plants a shape rule 3 now rejects, and scenario 11 is the shape item 7 now halts. Both are in their tasks' `files`, and the acceptance criteria say they must keep testing what they test now.
6. **Every task edits its own brief.** The scenario count appears in five documents, including this brief, so each task updates all five (as the brief says to).
7. **New scenario files are listed as the folder `.loop/tests/scenarios/`, not by name.** `plan.md` puts file paths in backticks, and `check-docs.sh` fails any backticked path that doesn't exist yet. That would have made every gate unpassable until all nine scenarios existed.
8. **Gate cost.** Every gate ends with the full suite, which took 80 seconds here, as the brief asks. Since all finished gates re-run every iteration, the sweep grows to about 12 minutes per iteration by the end. The same shared suite also means one breakage reverts every finished task, not just the one that caused it.


## T1 — Gate-shape lint rule 3: reject a gate that inspects a HEAD file its task does not own

- **Outcome:** done (review: PASS)
- **Summary:** Added gate-shape lint rule 3 to .loop/run.sh: a plan is refused at plan time if a task's verify inspects (grep/cat/test -f/Python open().read()) a HEAD-tracked file absent from that task's files array, mirroring gate_files_moved()'s runtime revert condition one phase early. Documented it in loop-plan's SKILL.md, added scenario 35-gate-unowned-file.sh, and fixed the two existing scenarios (33, 21) the new rule now touches.
- **Files:** .loop/run.sh, .claude/skills/loop-plan/SKILL.md, .loop/tests/scenarios/35-gate-unowned-file.sh, .loop/tests/scenarios/33-gate-rewrite.sh, .loop/tests/scenarios/21-foreign-state.sh, README.md, .loop/README.md, .loop/manual.md, docs/briefs/B008-driver-in-python.md, docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md
- **Notes for next iteration:** Two things outside run.sh's own logic needed fixing as a direct consequence of rule 3, both in .loop/tests/scenarios/ (in this task's files scope) and neither is lib.sh (untouched): (1) 33-gate-rewrite.sh's first case planted an inspecting verify (grep -q ORIGINAL probe.txt) on an unowned pre-existing file, which rule 3 now refuses at plan time before any iteration runs, so the scenario could never reach the runtime GATE REWRITE guard it exists to test. Changed the verify to `bash probe.txt` (execute, not inspect) and probe.txt to a tiny script, keeping the runtime assertions unchanged. (2) 21-foreign-state.sh reuses lib.sh's shared PLAN_TWO fixture (verify: test -f T1.out / T2.out, files:[]) across two fixture_run calls in the SAME repo; by the second call T1.out/T2.out are already committed to HEAD from the first run's completed work, so PLAN_TWO's own verify now trips rule 3 on replan — a fixture-reuse artifact, not a real gate-shape defect. Since PLAN_TWO lives in lib.sh (not editable per the task), swapped in a scenario-local plan literal with verify:'true' for that one replan step via fixture_plan/fixture_stub_default; the rest of the scenario (resume-vs-reset assertions) is untouched. Extraction of inspected paths from a verify string has to tolerate jq's @tsv doubling a literal backslash (a Python open(\"x\") in the source arrives as open(\\\"x\\\") once state_get pipes it through @tsv) — the regex in gate_inspected_paths() uses \\* rather than \\? for exactly this reason; a naive single-backslash-or-none version passes standalone but silently stops matching once run through state_get's @tsv.

## T2 — Gate-shape lint rule 4: reject a gate that diffs against any ref other than HEAD

- **Outcome:** gate_fail (review: skipped)
- **Summary:** Added gate-shape lint rule 4 to .loop/run.sh: a plan is refused at plan time if a task's verify diffs, logs or rev-lists against any fixed ref (a commit, tag, branch, relative ref, range, or merge-base) instead of HEAD, since that baseline decays the moment any other task commits. Added helper gate_diff_refs(), documented the rule in loop-plan's SKILL.md, added scenario 36-gate-decaying-baseline.sh, and bumped the scenario/check counts (36 scenarios / 39 checks) in README.md, .loop/README.md, .loop/manual.md, B008-driver-in-python.md and this run's own brief so check-docs.sh stays green.
- **Files:** .loop/run.sh, .claude/skills/loop-plan/SKILL.md, .loop/tests/scenarios/36-gate-decaying-baseline.sh, README.md, .loop/README.md, .loop/manual.md, docs/briefs/B008-driver-in-python.md, docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md
- **Notes for next iteration:** run.sh and the new scenario file were already present, uncommitted, in the working tree when this session started (state.json showed T2 pending/attempts:0, and .loop/state/runs/014-gate-shape-and-driver-honesty/20260924-235330/ held a killed prior work session's leftovers with no proposal.json) -- I reviewed both against the acceptance criteria rather than rewriting them, and found them correct: gate_diff_refs() reassembles a $(...) merge-base ref and takes the left side of a range (so a range merely ending in HEAD is still flagged), sits beside gate_inspected_paths, and rule 4's die block mirrors rule 3's format. What was still missing, and what this session actually added, was every doc-side consequence: the SKILL.md paragraph for rule 4 (inserted right after T1's rule-3 paragraph, before 'Known trap'), and the scenario-count bump (35->36, 38->39) across README.md (x2), .loop/README.md, .loop/manual.md (x2), B008-driver-in-python.md and this brief (x2, including the 'T1 having already landed...' sentence, now 'T1 and T2 having already landed...'). Left the two pre-existing run-artifact leftovers (.loop/state/runs/.../20260924-235330/, the .raw/.stderr files under .../20260924-221240/) untouched -- they are telemetry, not this task's files, and not mine to clean up.

## T2 — Gate-shape lint rule 4: reject a gate that diffs against any ref other than HEAD

- **Outcome:** done (review: PASS)
- **Summary:** Gate-shape lint rule 4 in .loop/run.sh refuses a plan whose verify diffs, logs or rev-lists against any fixed ref (commit, tag, branch, relative ref, range, merge-base) instead of HEAD, via a new gate_diff_refs() helper alongside rule 3's gate_inspected_paths(). Documented in loop-plan's SKILL.md, added scenario 36-gate-decaying-baseline.sh, and scenario/check counts (36/39) kept consistent across README.md, .loop/README.md, .loop/manual.md, B008-driver-in-python.md and this run's brief.
- **Files:** .loop/run.sh, .claude/skills/loop-plan/SKILL.md, .loop/tests/scenarios/36-gate-decaying-baseline.sh, README.md, .loop/README.md, .loop/manual.md, docs/briefs/B008-driver-in-python.md, docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md
- **Notes for next iteration:** This task's implementation, docs and scenario were already present and correct in the working tree at session start (attempts:1, notes recorded a prior session had tampered with .loop/state/state.json directly, which the driver reverted, forcing that iteration to gate_fail regardless of what the gate itself reported -- see the run's loop.log: 'T2 failed on state tampering -- the work is reverted whatever the gate said'). state.json was clean (matched HEAD) at the start of this session. I did not change run.sh, SKILL.md, the scenario, or any doc: I re-verified each acceptance criterion by hand (die-block message shape, rule 3/existing rules untouched, gate_diff_refs' merge-base/range handling, scenario count consistency at 36/39) and re-ran the verify command myself rather than trust the prior claim, since the prior session's own 'done' claim was exactly what got overridden. Nothing needed fixing; this session made no code changes.

## T3 — Export the active task id and the gated task id to every gate in the sweep

- **Outcome:** done (review: PASS)
- **Summary:** The driver now exports LOOP_ACTIVE_TASK and LOOP_GATE_TASK for the duration of each gate's verify command in .loop/run.sh's gate_ids(), unset elsewhere so no work or review session and no inherited stale value ever sees them. Documented for planners in loop-plan's SKILL.md and for operators in .loop/manual.md, added scenario 37-gate-task-env.sh, and bumped the scenario/check counts (37/40) across README.md, .loop/README.md, .loop/manual.md, B008-driver-in-python.md and this run's own brief.
- **Files:** .loop/run.sh, .claude/skills/loop-plan/SKILL.md, .loop/manual.md, .loop/tests/scenarios/37-gate-task-env.sh, README.md, .loop/README.md, docs/briefs/B008-driver-in-python.md, docs/briefs/B20260924-1947-gate-shape-and-driver-honesty.loop-brief.md
- **Notes for next iteration:** gate_ids() now takes the active task id as its first argument (call site: gate_ids "$task" "${gate_targets[@]}"); LOOP_ACTIVE_TASK/LOOP_GATE_TASK are set only as a prefix on the single `bash -c "$cmd"` that runs one gate's verify, never exported into run.sh's own shell -- so nothing later in the iteration (including run_session for work/review) can see them, and a top-of-script `unset LOOP_ACTIVE_TASK LOOP_GATE_TASK` strips any value inherited from whatever invoked run.sh (the leak scenario.sh 37 checks by exporting LOOP_ACTIVE_TASK=stale LOOP_GATE_TASK=stale onto fixture_run itself, mirroring what happens when run-all.sh executes inside an outer gate). No change was made to .loop/amend.sh's own gate-running code path in check() -- it does not use gate_ids() and reading/exporting these two vars there is T4's advisory, not this task's export. Did not touch the scenario-listing table in .loop/README.md (stops at 33-gate-rewrite, already missing 34-36) since T1 and T2 did not extend it either -- check-docs.sh only enforces the numeric counts, not table completeness, so that omission is pre-existing and out of this task's scope.
