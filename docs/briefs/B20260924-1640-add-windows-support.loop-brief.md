# Brief — Windows Git Bash support for the bash driver (interim fix)

- **Status:** ready to plan
- **Starting point:** extends `.loop/run.sh` as it stands today (992-ish lines
  of bash) — this patches that driver, it does not replace it. `docs/briefs/B008-driver-in-python.md`
  already diagnosed the root cause and named this exact scope as deferred work:
  *"The interim fix to the bash driver. `jq -b`, the mask spellings and a
  preflight assertion land separately so Windows work can proceed today; this
  brief does not depend on them and does not carry them."* This brief is that
  deferred work, written up properly instead of staying as machine-local shims.

---

## What it is

On 2026-09-23 the loop was installed into a Windows repo (Git Bash, native
`jq.exe` on `PATH`) and hit the failure B008 describes: `jq.exe` writes `\r\n`,
the driver reads task ids with `while read -r id`, the trailing `\r` makes the
id match nothing, and the gate for that task is skipped **with no line in the
log** — the run's own summary said `gate failures: 0` while the regression gate
simply never ran. The workaround used to keep working that day was a
machine-local shim (`jq` → `jq-bin.exe -b`, kept outside any repo — see the
project's own memory record, not reproducible by anyone else who installs the
loop on Windows). This brief turns that shim into the loop's own fix, plus the
two adjacent Windows gaps found the same day: containment masking that only
strips one spelling of `$HOME`, and Windows tools that sit outside `PATH` by
default breaking the allow-rule syntax `.loop/settings.json` already uses.

## Behaviour contract

**1. Every `jq` invocation in the driver goes through one choke point.**
`.loop/run.sh` currently calls `jq` directly at ~30 call sites (`state_get()`,
inline `jq -e`, `jq -nc`, `jq -s`, the signal functions, …). This brief
replaces the ones that were reading task ids or other repo-controlled state
with a single wrapper — call it `jq_()` — that always passes `-b`
(`--binary`; a no-op on non-Windows jq builds, per jq's own docs, and the fix
the machine-local shim was standing in for). No bare `jq` call may remain in
`.loop/run.sh` for anything the driver parses back into bash — a call that
only formats a log line for a human is not required to move, but is not
disallowed from moving either. Whether the wrapper is a shell function, an
alias, or a variable holding `jq -b` is mechanics.

**2. Preflight asserts the fix actually works on this machine, not just that
`jq` exists.** The existing preflight loop (`for t in jq claude git; do … done`,
around line 422) checks presence only. Add a check that runs a real
round-trip through the wrapper from item 1 (e.g. emit a known string, read it
back with `read -r`) and fails if a `\r` survives — whether because this `jq`
build predates `-b`, ignores it, or is some other binary shadowing the name
entirely. On failure, preflight exits `1` and names exactly what it found and
where to read the background (`.loop/manual.md`'s Windows section from item
4), the same way every other preflight line does. This is what item 1 alone
does not guarantee: `-b` closes the common case, this check is what stops the
next platform-specific jq quirk from being invisible again.

**3. `mask()` covers every spelling of `$HOME` a Windows toolchain can
produce, not just the one Bash resolves to.** Today (`.loop/run.sh` line 171):

```bash
mask() { sed -e "s#${HOME}#~#g" -e "s#${USER_NAME}#USER#g"; }
```

`$HOME` inside Git Bash is already POSIX-style (drive mounted lower-case under
`/`, e.g. `C:\` becomes `/c`), but content the driver masks did not
necessarily pass through Git Bash to get its path spelling — a session's own
JSON, or `claude` itself, can emit the *same* directory three ways: the MSYS
mount (`/c` + the native path with back-slashes turned to forward-slashes),
the native back-slash spelling (`C:\Users\<user>`), and that same native path
with forward-slashes instead of back-slashes. `mask()` must strip all three
spellings of the same directory to `~`, plus the bare username as it already
does, on every platform (the extra substitutions are a no-op where those
spellings never occur). `.loop/tests/scenarios/10-containment.sh` is extended with a case that
emits all three spellings from a single fixture session and asserts all three
come out masked — not a new numbered scenario, since it is the same rule
("nothing persisted names the machine") the existing one already gates.

**4. `.loop/manual.md` gets a short "Windows (Git Bash)" section documenting
the `PATH` requirement for permission matching.** `.loop/settings.json` allow
rules are written as bare command names — `Bash(msbuild:*)`, `Bash(nuget:*)` —
which only match an invocation that resolves the same bare name via `PATH`.
On Windows, MSBuild and NuGet are commonly installed outside `PATH`
(`...\MSBuild\Current\Bin\MSBuild.exe`, a hand-placed `nuget.exe`), so a
brief's verify command that invokes them by absolute path silently falls
outside every allow rule written for the bare name, and a session invoking
them by bare name fails with "not found" instead. The fix here is
documentation, not driver code: state the rule (allow rules match the
resolved `PATH` name, so put a same-named shim on `PATH` rather than writing
the rule against an absolute path) so the next Windows install does not
rediscover it by trial and error the way this one did.

**5. Nothing else changes.** Same exit codes (`0`–`7`, unchanged meanings),
same state machine, same one-commit-per-iteration, same 33 scenarios in
`.loop/tests/scenarios/` passing unmodified on macOS/Linux except the one
extended in item 3. This is explicitly *not* the Python driver from B008 —
that brief's own scope statement already excludes this work from itself, and
this brief returns the favor.

## Worked example

The arbiter is the same scenario B008 used to diagnose the bug, now expected
to pass correctly instead of silently skipping:

```
# Windows, Git Bash, native jq 1.8.2 (CRLF-emitting) on PATH, no shim installed
.loop/run.sh docs/briefs/0003-runstat-cli.md

  iteration 1  -> T1 done, T1.out created
  iteration 2  -> T2 done, and T2 deletes T1.out
               -> [loop]    GATE REGRESSION T1 — reverting to pending
               -> T1 status=pending, attempts=1
  iteration 3  -> T1 re-done
  -> exit 0, 2/2 done, gate failures: 1
```

The refusal path, for a jq build where the round-trip still fails:

```
# a jq on PATH that ignores -b (or is shadowed by something else) and still
# emits \r
.loop/run.sh docs/briefs/0003-runstat-cli.md
  -> [loop]   [ ] jq round-trip via -b still returns a CR — this is the bug
               that hid gate failures on 2026-09-23; see .loop/manual.md#windows
  -> preflight failed
  -> exit 1, no state written, no run directory, no lock taken, no commit
```

The masking case, one fixture session emitting all three spellings of the same
path:

```
proposal.json summary field contains, verbatim, one path spelled three ways —
call the back-slash native form P = C:\Users\<user>\secret\file.py; the other
two are P with every \ turned to /, and that result with the leading "C:"
replaced by "/c":
  "wrote " + P + " and " + P-with-forward-slashes + " and " + P-msys-mounted

-> journal entry contains, for all three:
  "wrote ~\secret\file.py and ~/secret/file.py and ~/secret/file.py"

-> none of the three original spellings survive in any persisted file
```

## Out of scope

- **The Python driver rewrite** (`docs/briefs/B008-driver-in-python.md`).
  That brief explicitly excludes this one from its own dependencies; this one
  returns the favor and does not touch `runstat` or replace `.loop/run.sh`'s
  language.
- **Installing or vendoring build tools for a consumer repo** (MSBuild, NuGet,
  or anything else a brief's own verify commands need). Item 4 documents the
  `PATH`/allow-rule interaction; it does not add, download, or pin any tool.
- **`cmd.exe` or PowerShell support for verify commands.** Verify commands stay
  shell strings run under the Git Bash `bash` on `PATH`, exactly as today.
- **Re-running or repairing any prior run that hit the silent-gate bug before
  this fix existed** (this includes runs already completed and committed
  elsewhere). This brief prevents recurrence going forward; it does not
  retroactively re-verify history.
- **Any change to exit codes, the state machine, the review contract, or the
  signal formulas.** Those are B008's territory if they ever need to move.
- **A new numbered test scenario file.** The masking coverage in item 3
  extends `.loop/tests/scenarios/10-containment.sh`; it does not introduce a
  34th scenario for what is the same rule on a wider set of inputs.

## Constraints

- Bash only — this is a patch to the existing `.loop/run.sh`, not a rewrite,
  and introduces no new runtime dependency beyond what the driver already
  requires (`bash`, `jq`, `git`, `claude`).
- The wrapper from item 1 must be a no-op change in behaviour on macOS/Linux:
  every one of the 33 existing scenarios keeps passing unmodified there.
- The Windows-specific gate (native CRLF-emitting `jq.exe`, no shim) must
  actually be run on Windows Git Bash to verify items 1–3 — it cannot be
  eyeballed from a Unix machine. Whoever implements this has that environment
  available directly, so the task that owns this gate runs it for real rather
  than stating how it *would* be verified.
- Repo-relative paths everywhere, in every file and every commit message.
- Agents commit locally, one commit per iteration, and never push.

## Shape

3 to 5 tasks, each independently verifiable by a single command.

One of them needs a gate of its own, because no existing unit test covers it:
the cross-platform gate — the full `.loop/tests/run-all.sh` suite, run on
Windows Git Bash with a native, non-shimmed `jq` on `PATH`, both before item 1
(reproducing the silent skip) and after (showing `03-gate-regression.sh` and
the extended `10-containment.sh` both catch what they're supposed to). This is
the task that proves the brief; the others (the wrapper sweep, the preflight
check, the manual.md section) are ordinary single-command verifications
against the existing suite.
