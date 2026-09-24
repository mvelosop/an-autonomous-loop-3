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

