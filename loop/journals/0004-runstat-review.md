# Journal — 0004-runstat-review

Append-only narrative of this plan. Rendered state lives in loop/plan.md.

## Plan — 0004-runstat-review

- **Brief:** `docs/briefs/0004-runstat-review.md`
- **Tasks:** 6

Plan written and self-checked.

## `loop/state.json` — `0004-runstat-review`

**6 tasks**, linear dependency chain. **First ready task: T1** (no dependencies).

| id | title | gate proves |
| --- | --- | --- |
| T1 | Add the review fixtures to `tests/fixtures.py` | the brief's three verdicts + a second, singly-incoherent run exist with exactly the brief's numbers |
| T2 | Load `reports/NNN-verdict.json` in the existing loader | `load_run(...).verdicts`, missing `reports/` ≠ malformed, plus the unchanged-commands check |
| T3 | `runstat review`: table, totals block, exit codes | the 7 non-coherence totals values exactly; exits 0/1/2 with empty stdout, named file, no traceback |
| T4 | Print every finding verbatim, grouped by iteration | both fixture findings appear under a heading naming iteration 2 and T2; the "no findings" line appears only when true |
| T5 | The five coherence checks | all five fire on a synthetic run, each named `check <n>` with iteration and task; `coherence: ok` on the good fixture; still exit 0 |
| T6 | Document `review` in both docs | replays the tool and requires every line of the documented transcript verbatim in real output |

Every verify command fails right now, each for the right reason (missing fixture builder → missing `verdicts` attribute → `argparse: invalid choice: 'review'`). The whole set runs in well under a second. I also wrote a throwaway stub implementation **outside the repo** (`/tmp`) and confirmed T3–T6 *pass* against it — a gate that can only fail is as broken as one that only passes.

## What I interpreted rather than read

**Names I pinned because a gate needed one** (the brief is silent on all of these):

- `write_review_fixture_run(dest)` and `write_incoherent_fixture_run(dest)` in `tests/fixtures.py`, both returning the run directory — every later gate imports them.
- `load_run(...).verdicts`, entries exposing `.iteration` (parsed from `NNN`), `.task`, `.verdict`, `.criteria` (the dicts as written), `.findings`. This mirrors the existing `Session`, but it is structure, not behaviour.
- Three output strings: violation lines contain the literal `check <n>` with the brief's numbering; the findings heading contains the word `iteration` plus the number and task id; the empty-run line contains `no findings`. Without these, "names check 1" and "a line saying so plainly" are not checkable.
- The `review` example in `docs/runstat-cli.md` must be a `$`-prefixed transcript of fixture run `20260817-120000` — the gate diffs its lines against real output, so a different example run would fail it.

**Judgment calls:**

- **The totals block arrives in two pieces.** The brief shows `coherence: ok` inside it, but coherence is T5. T3's gate asserts the other seven values and T3's goal says so explicitly, so a reviewer doesn't fail it for the missing line.
- **"Malformed verdict" includes a missing key**, not just unparseable JSON — otherwise a verdict without `criteria` would traceback rather than exit 2.
- **The fixture needs an `iterations.jsonl`.** The brief's fixture table lists only `reports/`, but check 5 compares against it and the worked example says `coherence: ok`, so I required records 1–3 naming T1, T2, T2.
- **A present-but-empty `reports/` is exit 1**, same as a missing one.
- **The unchanged-commands proof** is `uv run pytest -q` plus `git diff --quiet ba3d62f -- tests/test_worked_example.py tests/test_cli_contract.py`, on T2 and T6. Those two files pin the existing commands' output and exit codes; requiring them byte-identical to the current branch tip means new tests go in new files. **This hard-codes commit `ba3d62f`** — worth knowing if the branch is ever rebased.
- **Six tasks, the top of the brief's range.** I split the command's output three ways (table+totals / findings / coherence) so each gate is small and each failure points at one thing.
- I left `README.md` alone; the brief names only the two `docs/` files.


## T1 — Add the review fixtures to tests/fixtures.py

- **Outcome:** done (review: PASS)
- **Summary:** Added write_review_fixture_run and write_incoherent_fixture_run to tests/fixtures.py, materializing the brief's worked-example review run (three verdicts, one FAIL with two findings) and a second run with exactly one incoherent verdict.
- **Files:** tests/fixtures.py, tests/test_review_fixtures.py
- **Notes for next iteration:** write_review_fixture_run(dest) returns dest/20260817-120000 with reports/001-003-verdict.json plus a matching iterations.jsonl (records 1,2,3 -> T1,T2,T2), mirroring the field set write_fixture_run already uses for iteration records. write_incoherent_fixture_run(dest) treats dest itself as the run directory (no extra run-id subdirectory, since the brief doesn't pin a name for this fixture) and writes a single 001-verdict.json (PASS, second of three criteria met:false, all evidence non-empty, findings []) plus a one-line iterations.jsonl for iteration 1/T1 so check 5 (task mismatch) does not also fire. Tests for both builders live in the new tests/test_review_fixtures.py; the existing tests/test_fixtures.py (which only covers write_fixture_run) was left untouched.

## T2 — Load reports/NNN-verdict.json in the existing loader

- **Outcome:** done (review: PASS)
- **Summary:** Extended load_run to also read reports/NNN-verdict.json into a new Verdict dataclass exposed as Run.verdicts, ordered by file name, with reports/NNN-proposal.json never read.
- **Files:** src/runstat/loader.py, tests/test_loader_verdicts.py
- **Notes for next iteration:** Verdict is a new frozen dataclass (iteration, task, verdict, criteria, findings, path); Run gained a verdicts field as its fourth constructor arg (verified it's the only construction call site, so no other breakage). Missing/empty reports/ loads verdicts == []. A verdict file is read only via glob('*-verdict.json'), so proposal.json siblings are ignored even if malformed. Malformed JSON or a missing required key (task/verdict/criteria/findings) raises RunError naming the file, mirroring the existing session-file error style. New tests live in tests/test_loader_verdicts.py (test_loader.py untouched, per plan).
