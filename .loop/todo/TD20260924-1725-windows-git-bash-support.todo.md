---
name: TD20260924-1725-windows-git-bash-support
description: The loop on Windows/Git Bash — the interim bash fix is briefed and ready to plan; what stays open is the residue that brief deliberately excludes, and one finding that is not about Windows at all
status: briefed — interim fix ready to plan; residue open
created: 2026-09-24
source: Visum (Windows machine), 2026-09-23 install
waiting-on: Nothing for the interim fix. The residue waits on the `B008-driver-in-python` brief.
---
# Windows / Git Bash

## Already briefed — not open

Brief `B20260924-1640-add-windows-support`, under `docs/briefs/` on branch
**`using-at-visum`** (`63b8489`) — not on this branch, which is why it is named here without a
path. **Status `ready to plan`**. Four items: route every state-parsing
`jq` call through one `-b` wrapper; make preflight assert a real `\r`-free round-trip rather than
mere presence of `jq`; widen `mask()` to every `$HOME` spelling a Windows toolchain produces; and
document the `PATH`/allow-rule interaction for tools that sit outside `PATH` by default.

Run it with `.loop/run.sh --plan-only` against that brief on that branch. **Nothing in this TODO
blocks it.**

## The finding worth carrying beyond Windows

This is the part that should outlive the platform fix.

`jq.exe` writes `\r\n`. The driver reads task ids with `while read -r id`. The trailing `\r` made
the id match nothing, so **the gate for that task was skipped with no line in the log** — and the
run's own summary reported `gate failures: 0`. A gate that never ran was indistinguishable from a
gate that passed, in the one artifact an operator reads to decide whether a run went well.

That is not a Windows bug in its general form. It is: **the driver has no way to tell "this gate
passed" from "this gate did not run", and its summary reports the former for both.** Any future
cause — a shell quirk, a renamed task id, a malformed `verify` string, a `jq` build without `-b` —
produces the same silent hole. Item 2 of the brief closes the `\r` case specifically, by asserting
the round-trip at preflight. It does not close the class.

Worth deciding separately, and cheap: have `gate_ids()` count the gates it actually executed and
have the run-end signals block assert that count against the number of done tasks. A mismatch is
then loud instead of invisible. (The consumer repo hit the same *class* independently — a Python
interpreter probe returned false on every venv machine, so every gated spec skipped **silently**
while `pnpm test` stayed green. Different cause, identical shape: the absence of a result read as a
passing result.)

## Residue the interim brief deliberately excludes

Its own `## Out of scope` list, recorded here so none of it is mistaken for done:

- **The Python driver rewrite** — brief `B008-driver-in-python`. That is the real fix for
  the portability class; the interim brief patches the bash driver and returns B008's favour by not
  touching it. The two briefs are explicitly independent of each other.
- **`cmd.exe` / PowerShell verify commands.** Verify strings stay `bash` under Git Bash.
- **Installing or vendoring consumer build tools** (MSBuild, NuGet, …). Item 4 documents the
  `PATH`/allow-rule interaction; it adds, downloads and pins nothing.
- **Retroactively re-verifying runs that completed before the fix.** Any run made on Windows before
  this lands may carry a silently-skipped gate and a `gate failures: 0` summary that did not mean
  what it said. The brief prevents recurrence; it does not audit history. **If any such run's work
  was merged on the strength of that summary, it has not actually been gated** — worth knowing
  before trusting one.
- **Exit codes, the state machine, the review contract, the signal formulas.** B008's territory.
