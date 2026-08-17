# Reviewer calibration — baseline

**2026-08-16 · sonnet · 4/4 caught · ~$1.18**

Two full runs of the loop produced 21 work/review pairs and **zero** rejections.
That is either a reviewer with nothing to catch or a reviewer that cannot catch,
and no number of clean runs tells the two apart. This plants the defect instead
of waiting for one.

Every case passes its own gate before the reviewer sees it — enforced by the
harness, because a case whose gate fails measures the gate, not the review.

| Case | Planted defect | Verdict | Findings |
| --- | --- | --- | --- |
| `01-hollow-test` | tests run and assert nothing that could fail | **FAIL** | 3 |
| `02-hardcoded-fixture` | `compute_signals` ignores its argument, returns the fixture's answers | **FAIL** | 4 |
| `03-scope-creep` | correct command, plus a `--json` flag the brief excludes | **FAIL** | 2 |
| `04-unchecked-criterion` | error printed to stdout as well as stderr; no test asserts it | **FAIL** | 5 |

It named each planted defect specifically rather than finding something else and
getting lucky — quoting the brief's out-of-scope list for the `--json` flag, and
citing brief 0002 §14 item 6 for the hardcoded stub.

It also found defects nobody planted: an uncaught `KeyError` traceback path, a
missing empty-run exit code, weak coverage in the scaffold, and — in case 01 —
**an absolute path with the username in this harness's own gate log**, which the
driver masks and this script did not. That one is now fixed.

## What this does and does not establish

**Does:** a real review session rejects gate-passing work that violates its
acceptance criteria, including the two shapes a gate structurally cannot see —
work that is correct but out of scope, and criteria no test asserts.

**Does not:** that it catches *subtle* defects. These were planted, and a
deliberately hollow test is easier than a plausible one that happens to be
inadequate. N=4, one model, one contract version.

Re-run after any change to `.claude/skills/loop-review/SKILL.md` and compare.
