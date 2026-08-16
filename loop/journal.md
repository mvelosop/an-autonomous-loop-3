# Journal

Append-only narrative of this plan. Rendered state lives in loop/plan.md.

## Plan — 0003-runstat-cli

- **Brief:** `docs/briefs/0003-runstat-cli.md`
- **Tasks:** 10

`loop/state.json` is written and checked.

## Plan

**Run id:** `0003-runstat-cli` · **10 tasks** · first ready task: **T1** (T2 also has no dependencies)

| id | title | depends on |
| --- | --- | --- |
| T1 | Scaffold the package, console script + `python -m runstat` | — |
| T2 | Check in the two fixture run directories the gates read | — |
| T3 | `runstat summary` — per-phase rollup | T1, T2 |
| T4 | Call out error sessions and permission denials in summary | T3 |
| T5 | `runstat signals` — the eight run-level signals | T1, T2 |
| T6 | `runstat compare` — two runs side by side with deltas | T5 |
| T7 | Exit-code and error contract across all three commands | T3, T5, T6 |
| T8 | pytest suite, including the worked example end to end | T7 |
| T9 | `README.md` with examples replayed from the tool | T7 |
| T10 | `docs/runstat.md`, the telemetry contract | T7 |

All ten gates were run: each **fails now**, each for the right reason (missing module, missing fixture, missing file — no syntax errors). I also replayed the regex and shell logic of every gate against synthetic *correct* output to confirm they pass when the work is done, and against drifted output to confirm they don't: T2's checker passes on a hand-built correct fixture and fails on a missing one; T7's `chk` correctly rejects a wrong exit code, leaked stdout, empty stderr and a traceback; T9's README loop fails when one printed line is absent; T10's keyword sweep fails on a thin doc.

## Names I pinned that the brief did not

No internal module, function or exception name is pinned — every gate goes through the CLI or through data files, so structure stays open. What I did pin:

- **`tests/fixtures/runs/20260814-101500/`** — the worked example as checked-in data. Gates need a fixed input that exists before any code does.
- **`tests/fixtures/runs/20260815-090000/`** — the comparison variant, with contents I specified exactly (5 sessions, $3.65, 2 iteration records ending in a `review_fail`). The brief says the variant is *the implementation's* to construct; I took that choice for the gates so `compare` and the README examples are deterministic. The pytest suite can still build its own variant in `tmp_path`.
- **Delta direction:** second run minus first, positive deltas carry an explicit `+`. Unstated in the brief, and `compare` is ungateable without it.
- **`--help` must name all three subcommands**, and `[project.scripts]` must contain the key `runstat` with an empty runtime dependency list.
- **The test suite must contain at least ten tests** and assert the literal `4.08`. An arbitrary floor, but "there is a suite" is not gateable otherwise.

## What I interpreted rather than read

1. **"Every test writes inside `pytest`'s `tmp_path`."** I read this as constraining *writes*, not as forbidding read-only fixture data in the repo — so T2 checks in fixtures and T8 still requires every test to build its run directories in `tmp_path`. If you meant no checked-in fixtures at all, T2 and every gate that reads it need reworking.
2. **Exit 1 is a failure exit.** The brief pairs "1 = valid but no sessions" with "stdout stays empty on failure" without saying whether the empty-run case counts. I ruled that it does: exit 1 prints nothing on stdout and explains itself on stderr.
3. **README examples use the checked-in fixtures.** The brief requires the gate to replay the tool and match every printed line verbatim, but not against what input. Fixtures make it reproducible for a reader.
4. **`141s` is contract, not layout.** The brief says padding and column widths are the implementation's choice; I treated the whole-seconds-with-`s` rendering and the `phase, sessions, cost, turns, wall` column order as part of the numbers, not the layout.
5. **The "money is an estimate" rule** is satisfied for `signals` by the `estimated spend` label itself, and for `summary` by any line saying so — I did not pin its wording.


## T1 — Scaffold the runstat package with both entry points

- **Outcome:** done (review: PASS)
- **Summary:** Scaffolded the runstat package: pyproject.toml (src/ layout, empty runtime deps, pytest as sole dev dependency, console script entry point), src/runstat/__init__.py, and src/runstat/__main__.py with an argparse CLI advertising summary/signals/compare as stubs that return 0.
- **Files:** pyproject.toml, src/runstat/__init__.py, src/runstat/__main__.py, uv.lock
- **Notes for next iteration:** Used hatchling as the build backend with [tool.hatch.build.targets.wheel] packages = ["src/runstat"] to pick up the src/ layout; dev dependency declared via [dependency-groups] dev = ["pytest>=8"], the modern uv convention (not [tool.uv.dev-dependencies], which is legacy). Ran `uv sync` to create .venv and uv.lock — .venv is already gitignored, uv.lock is a new file the driver should commit alongside the source. Command stubs in __main__.py just parse args and return 0; `uv run pytest -q` currently exits 5 (no tests collected), which is expected and correct until T8 adds the suite — confirmed this matches the brief's explicit note about that exit code.
