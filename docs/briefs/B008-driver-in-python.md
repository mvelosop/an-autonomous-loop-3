# Brief B008 — the driver in Python: one language, two platforms

- **Status:** ready to plan
- **Starting point:** extends `docs/briefs/0002-next-generation-autonomous-loop.md`
  — same loop, same contract, different implementation language for the driver.
- **Role:** replaces `.loop/run.sh` with a Python driver that behaves
  identically, runs on macOS and Windows, and shares one implementation of the
  signal formulas with `runstat` instead of two that must agree by inspection.

---

## What it is

The driver is 992 lines of `bash` whose correctness depends on the byte-level
behaviour of the external binaries it pipes together. On 2026-09-23 the loop
was installed into a Windows repo and that dependency produced its worst
possible failure: **the regression gate stopped running, and the run reported
green.**

The mechanism is worth stating exactly, because it is the argument for this
brief. `jq.exe` — the native Windows build — opens stdout in text mode and
writes `T1\r\n`. The driver reads task ids with

```bash
while read -r id; do gate_targets+=("$id"); done \
  < <(state_get '.tasks[]|select(.status=="done")|.id')
```

so `id` is `"T1\r"`. `gate_ids` then looks up `select(.id==$id)|.verify`, finds
nothing, and its `[[ -n "$cmd" ]] || continue` skips the gate **without a word
in the log**. `03-gate-regression` failed while the run's own summary said
`gate failures: 0`. A one-character difference in a third-party binary's output
mode silently disarmed the feature the loop exists to have.

What this brief builds is a driver whose decisions do not travel through a
shell pipeline at all: JSON is parsed in-process, task ids are values rather
than lines of text, and the platform differences that remain are named in
preflight instead of discovered in production.

## Behaviour contract

**1. The loop's behaviour does not change.** Same three session kinds, same
state machine, same files in the same places (`.loop/state/`, `.loop/tmp`),
same one-commit-per-iteration, same fence handed to every session with
`--settings`. A reader of `.loop/README.md` should find it still true.

**2. Exit codes are the contract, unchanged:** `0` complete, `1` refused before
anything ran (preflight failed, or the plan has a task with no verify command),
`2` blocked, `3` stalled, `4` max iterations, `5` not converging, `6` cost
ceiling, `7` session error.

**3. The existing 39 scenarios are the acceptance suite.** They pass
*unmodified*, except for the single place in `.loop/tests/lib.sh` that invokes
the driver. A scenario whose assertions have to change is a behaviour change:
it gets named in the task's report and reviewed as such, never edited quietly
to match what the new driver happens to do. The suite stays free, offline and
deterministic.

**4. Cross-platform is a gate, not a claim.** The suite passes on macOS and on
Windows. The driver may invoke `git` and `claude`, always with arguments as a
list and never as a shell string; it may not invoke `jq`, `sed`, `awk`, `grep`
or `find` for anything it decides on. Where it reads another program's output
it declares the encoding and normalises newlines explicitly, rather than
inheriting whatever the platform does.

**5. Verify commands stay shell strings, and their meaning does not change.**
A plan's `verify` is authored for a POSIX shell, so the driver runs it with
`bash -c`. On Windows that means the Git Bash `bash` on `PATH`; if there is
none, preflight refuses with exit `1` and names it. Running a plan's verify
commands under `cmd.exe` because bash was missing would change what they mean,
which is worse than not running.

**6. Gate verdicts come from exit codes only.** Captured output is stored for
the human, normalised to LF, and never parsed to decide anything.

**7. Masking covers every form of the home path.** `$HOME`, the username, and —
on Windows — both the drive-letter spelling of the same directory
(`C:\Users\<name>`, and its forward-slash variant) and the POSIX one MSYS uses
(`/c/...`), because a value that passes through a native binary comes back in a
spelling the other does not match. `10-containment` passes on both platforms.

**8. One implementation of the signals.** The formulas live in one place that
both the driver and `runstat` import. Today `.loop/run.sh` and
`src/runstat/signals.py` compute them separately and brief 0002 acceptance item
6 requires the two to agree; after this, agreement is structural rather than
maintained. `12-signals-fixture` and brief 0003's hand-computed fixture remain
the arbiter.

**9. Preflight names every precondition it has.** Each check prints its own
line and a failure says what to do about it. The rule this comes from: the jq
bug was invisible because nothing asserted the assumption it broke. A
precondition that cannot be checked is not a precondition — it is a hope, and
it goes in the docs instead.

**10. A consumer repo needs `uv`, and nothing else new.** The loop is vendored
into repos of any stack — it was verified on a Go repo with no Python present —
so requiring a system Python would be a regression. The driver runs under `uv`,
which provisions its own interpreter; preflight checks for `uv` and refuses
with exit `1` naming it. This swaps the consumer's dependency from
`bash` + `jq` to `uv`, and that trade is the point: `uv` is one tool, pinned
and self-contained, instead of two whose builds differ per platform.

**11. The operator's command still works.** `.loop/run.sh <brief>` plans and
iterates, `.loop/run.sh` resumes, `--plan-only`, `--check` and `--preflight`
keep their meanings. Whether that entry point becomes a shim or is renamed is
mechanics and belongs to whoever implements it.

## Worked example

The arbiter is the scenario the bug hid in, run on the platform that hid it,
with the offending binary still installed:

```
# Windows, Git Bash, native jq 1.8.2 (CRLF-emitting) on PATH
.loop/run.sh docs/briefs/0003-runstat-cli.md

  iteration 1  -> T1 done, T1.out created
  iteration 2  -> T2 done, and T2 deletes T1.out
               -> [loop]    GATE REGRESSION T1 — reverting to pending
               -> T1 status=pending, attempts=1
  iteration 3  -> T1 re-done
  -> exit 0, 2/2 done, gate failures: 1
```

The refusal path, which must cost nothing:

```
# no uv on PATH
.loop/run.sh docs/briefs/0003-runstat-cli.md
  -> [loop]   [ ] uv — the driver runs under uv; install it
  -> preflight failed
  -> exit 1, no state written, no run directory, no lock taken, no commit
```

And the agreement that stops being a coincidence:

```
.loop/run.sh                     -> [loop]   estimated spend: $11.67
uv run runstat <that run dir>    -> total: $11.67
                                    (identical to the cent, and to the
                                     iteration and per-closed figures)
```

The spend figure is generated, not fixed: the test threads whatever the run
produced rather than hardcoding a number.

## Out of scope

- **Any change to what the loop does.** The state machine, the attempt
  ceiling, the stop conditions, the review contract and the gate's semantics
  are being re-implemented, not redesigned. A better idea found along the way
  is a finding for a later brief.
- **The interim fix to the bash driver.** `jq -b`, the mask spellings and a
  preflight assertion land separately so Windows work can proceed today; this
  brief does not depend on them and does not carry them.
- **`runstat`'s CLI, output format or tests.** It gains an import boundary and
  loses nothing.
- **The reviewer-calibration harness.** It is bash, it calls a real model, and
  it stays exactly as it is.
- **`install.sh`.** It keeps being a shell script that copies files.
- **A Windows-native shell mode** — verify commands under `cmd.exe` or
  PowerShell, or per-plan shell selection.
- **The plugin for the skills**, and any change to the three skill contracts.
- **Re-running run 1 or run 2 under the new driver**, or migrating the
  evidence branches. Those commits are the record of what happened under the
  driver that ran them.

## Constraints

- Python 3.13, standard library only for the driver — no runtime dependencies.
  `uv`, `git` and `claude` are the only executables a consumer repo needs.
- The driver never shells out to decide something. `git` and `claude` are
  invoked with argument lists; their output is read with an explicit encoding.
- The suite stays free, offline and deterministic, and its runtime on macOS
  must not regress against the bash driver's.
- The bash driver stays in place and working until the Python one passes the
  whole suite; the swap is a single task and the last one.
- Repo-relative paths everywhere, in every file and commit message.
- Agents commit locally, one commit per iteration, and never push.

## Shape

10 to 14 tasks, each independently verifiable by a single command.

Three of them need a gate of their own, because no unit test covers what they
claim:

- **the cross-platform gate** — the full suite, run on Windows, with a native
  CRLF-emitting `jq` on `PATH`. This is the one that proves the brief. It
  cannot run on the planning machine if that machine is a Mac, so the task that
  owns it must state how it was verified and halt cleanly if it cannot be.
- **the signals gate** — driver and `runstat` over the same run directory,
  compared value by value, not eyeballed.
- **the containment gate** — `10-containment` on both platforms, since the
  Windows path spellings are the half that was never exercised.

The scaffolding task gates on something the driver produces — a preflight that
refuses correctly, exit code and all — not on an empty test run.
