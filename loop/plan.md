# Plan — 0003-runstat-cli

<!-- Rendered from loop/state.json by loop/render-plan.sh.
     Do NOT edit: regenerated on every state change, your edits will be lost.
     The source of truth is loop/state.json. -->

**Status:** running · **10/11 done** · iteration 10

**Brief:** `docs/briefs/0003-runstat-cli.md` · **Updated:** 2026-08-15T22:27:25Z

## Progress

- [x] **T1** — Scaffold the runstat package with uv, src layout and pytest
- [x] **T2** — Write the fixture-run generator for the brief's worked example
- [x] **T3** — Load a run directory strictly, failing loudly on malformed input
- [x] **T4** — Compute the eight run-level signals as numbers, and format them separately
- [x] **T5** — Build the CLI entry points and the summary command
- [x] **T6** — Add the signals command
- [x] **T7** — Add the compare command
- [x] **T8** — Enforce the exit-code and error-output contract across all commands
- [x] **T9** — Add the end-to-end worked-example acceptance test
- [x] **T10** — Write the README, with every documented example matching real output
- [ ] **T11** — Document the telemetry contract and the cross-check against the driver

## Tasks

### T1 — Scaffold the runstat package with uv, src layout and pytest

`done` · depends on: none

Nothing can be built until there is a project uv can install and a test suite pytest can collect. This task creates the packaging skeleton — pyproject.toml, src/runstat/, and one real test — so that every later task can be verified by running the installed package rather than by poking at loose files. It also fixes the names later tasks depend on: the distribution is runstat and the console script points at runstat.cli:main.

**Acceptance**

- pyproject.toml declares a project named runstat, requires-python >=3.13, an empty runtime dependency list, and pytest as the only dev dependency.
- The build is configured so that `uv run python -c "import runstat"` imports the package from src/runstat/ — an src/ layout that is actually installed, not a path hack.
- pyproject.toml declares the console script entry point `runstat = "runstat.cli:main"` (the module it names is written in a later task).
- tests/test_smoke.py contains at least one test that passes, so `uv run pytest -q` exits 0 rather than 5 for an empty suite.
- No runtime dependency outside the standard library is added anywhere.

<details><summary>verify command</summary>

```sh
uv run python -c "import runstat; print(runstat.__name__)" && uv run pytest -q
```

</details>

### T2 — Write the fixture-run generator for the brief's worked example

`done` · depends on: T1

Every later task is verified against the worked example in docs/briefs/0003-runstat-cli.md: seven sessions and three iterations.jsonl records with exact costs, turns and durations. Building that run directory once, as a reusable test helper, is what keeps the tests hermetic (nothing ever reads a real loop/runs/ directory) and what lets each later verify command construct the same input. The numbers here are the arbiter for the whole run, so they must match the brief's table exactly.

**Acceptance**

- tests/fixtures.py defines write_fixture_run(dest) taking a directory path, creating <dest>/20260814-101500/ with sessions/ and iterations.jsonl inside it, and returning the path to that run directory.
- The seven session files are named 001-plan.json, 002-work.json, 003-review.json, 004-work.json, 005-review.json, 006-work.json, 007-review.json, so they sort by name into phase order.
- Each session file is a JSON object carrying at least phase, iteration, total_cost_usd, num_turns, duration_ms, is_error and permission_denials, with the values from the brief's session table; all seven have is_error false and an empty permission_denials list.
- iterations.jsonl holds exactly the brief's three records, one JSON object per line, in iteration order.
- The helper writes only under the directory it is given and creates it if needed; a test in tests/test_fixtures.py exercises it via pytest's tmp_path and nothing else.

<details><summary>verify command</summary>

```sh
uv run python -c "
import sys,json,pathlib,tempfile
sys.path.insert(0,'tests')
from fixtures import write_fixture_run
r=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
assert r.name=='20260814-101500', r
f=sorted((r/'sessions').glob('*.json'))
assert [p.name for p in f]==['001-plan.json','002-work.json','003-review.json','004-work.json','005-review.json','006-work.json','007-review.json'], f
o=[json.loads(p.read_text()) for p in f]
assert [x['phase'] for x in o]==['plan','work','review','work','review','work','review']
assert [x['iteration'] for x in o]==[0,1,1,2,2,3,3]
assert [round(x['total_cost_usd'],2) for x in o]==[1.98,0.5,0.2,0.52,0.2,0.48,0.2]
assert [x['num_turns'] for x in o]==[12,6,3,7,3,5,3]
assert [x['duration_ms'] for x in o]==[141000,68000,24000,72000,24000,64000,24000]
assert all(x['is_error'] is False and x['permission_denials']==[] for x in o), o
rec=[json.loads(l) for l in (r/'iterations.jsonl').read_text().splitlines() if l.strip()]
assert [(x['iteration'],x['task'],x['outcome'],x['attempts'],x['tasks_done'],x['tasks_total']) for x in rec]==[(1,'T1','done',0,1,8),(2,'T2','gate_fail',1,1,8),(3,'T2','done',1,2,8)], rec
print('fixture ok')
"
```

</details>

### T3 — Load a run directory strictly, failing loudly on malformed input

`done` · depends on: T1, T2

Both reports read the same two things off disk: sessions/*.json and iterations.jsonl. Putting that in one loader gives the commands a single definition of what a run is, and — more importantly — a single place where a malformed file becomes a hard error instead of a silent skip. The brief is explicit that undercounting silently is worse than refusing loudly, so the loader raises with the offending path rather than dropping a record.

**Acceptance**

- runstat.loader.load_run(path) returns an object exposing run_id (the run directory's own name), sessions (session records sorted by file name) and iterations (the iterations.jsonl records as dicts, in file order).
- Each session record exposes phase, iteration, total_cost_usd, num_turns, duration_ms, is_error, permission_denials and the path it was read from.
- runstat.loader.RunError is raised when the run directory does not exist, when any sessions/*.json file is not valid JSON, and when any non-blank line of iterations.jsonl is not valid JSON.
- The RunError message names the offending file — the session file's name for a bad session, iterations.jsonl for a bad record line.
- A run directory that exists but has no session files loads successfully with an empty sessions list; deciding what that means is the CLI's job, not the loader's. A missing iterations.jsonl is treated as zero records.
- Tests cover the good fixture and each malformed case, writing only inside tmp_path.

<details><summary>verify command</summary>

```sh
uv run python -c "
import sys,pathlib,tempfile
sys.path.insert(0,'tests')
from fixtures import write_fixture_run
from runstat.loader import load_run, RunError
r=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
run=load_run(r)
assert len(run.sessions)==7 and len(run.iterations)==3, (len(run.sessions),len(run.iterations))
assert [s.phase for s in run.sessions]==['plan','work','review','work','review','work','review']
assert [s.iteration for s in run.sessions]==[0,1,1,2,2,3,3]
assert [s.num_turns for s in run.sessions]==[12,6,3,7,3,5,3]
assert [s.duration_ms for s in run.sessions]==[141000,68000,24000,72000,24000,64000,24000]
assert round(sum(s.total_cost_usd for s in run.sessions),2)==4.08
assert all(s.is_error is False and s.permission_denials==[] for s in run.sessions)
assert [i['outcome'] for i in run.iterations]==['done','gate_fail','done']
assert run.iterations[2]['tasks_done']==2 and run.iterations[2]['tasks_total']==8
b=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
p=sorted((b/'sessions').glob('*.json'))[2]
p.write_text('{ not json')
try:
    load_run(b)
except RunError as e:
    assert p.name in str(e), e
else:
    raise AssertionError('malformed session file did not raise RunError')
c=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
j=c/'iterations.jsonl'
j.write_text(j.read_text()+'oops'+chr(10))
try:
    load_run(c)
except RunError as e:
    assert 'iterations.jsonl' in str(e), e
else:
    raise AssertionError('malformed iterations.jsonl line did not raise RunError')
try:
    load_run(pathlib.Path(tempfile.mkdtemp())/'nope')
except RunError:
    pass
else:
    raise AssertionError('missing run directory did not raise RunError')
print('loader ok')
"
```

</details>

### T4 — Compute the eight run-level signals as numbers, and format them separately

`done` · depends on: T3

Write runstat.signals.compute_signals(run), returning the eight signals as NUMBERS (ints, floats, and None for an undefined ratio) rather than display strings, plus format_signals(signals) returning the ordered (label, display) pairs the CLI prints. Keeping computation numeric is what lets compare do arithmetic on deltas instead of parsing its own output back into numbers; keeping formatting in one function is what keeps the printed values identical everywhere they appear.

**Acceptance**

- compute_signals returns a mapping with numeric keys: iterations, tasks_done, tasks_total, iterations_per_closed, gate_failures, review_rejections, attempts_burned, no_progress_streak, estimated_spend
- No value returned by compute_signals is a string
- iterations_per_closed is None when no task has closed, and a float otherwise
- attempts_burned counts records whose outcome is not 'done' — never the sum of the attempts field, which is a cumulative per-task counter
- no_progress_streak counts trailing records that did not increase tasks_done, and is 0 for an empty run
- format_signals returns exactly eight (label, display) pairs in the brief's order
- format_signals renders the fixture as 3, 2/8, 1.50, 1, 0, 1, 0, $4.08
- format_signals renders an undefined ratio as 'n/a' and money with two decimals and a leading $

<details><summary>verify command</summary>

```sh
uv run python - <<'PY'
import sys, pathlib, tempfile
sys.path.insert(0, 'tests')
from fixtures import write_fixture_run
from runstat.loader import load_run
from runstat.signals import compute_signals, format_signals

r = write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
s = compute_signals(load_run(r))
assert s['iterations'] == 3, s
assert s['tasks_done'] == 2 and s['tasks_total'] == 8, s
assert abs(s['iterations_per_closed'] - 1.5) < 1e-9, s
assert s['gate_failures'] == 1 and s['review_rejections'] == 0, s
assert s['attempts_burned'] == 1 and s['no_progress_streak'] == 0, s
assert abs(s['estimated_spend'] - 4.08) < 1e-9, s
assert not any(isinstance(v, str) for v in s.values()), s

assert format_signals(s) == [
    ('iterations', '3'),
    ('tasks closed', '2/8'),
    ('iterations per closed', '1.50'),
    ('gate failures', '1'),
    ('review rejections', '0'),
    ('attempts burned', '1'),
    ('no-progress streak', '0'),
    ('estimated spend', '$4.08'),
], format_signals(s)

b = write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
j = b / 'iterations.jsonl'
keep = [l for l in j.read_text().splitlines() if l.strip()][:-1]
j.write_text('\n'.join(keep) + '\n')
s2 = compute_signals(load_run(b))
assert s2['iterations'] == 2 and s2['tasks_done'] == 1, s2
assert abs(s2['iterations_per_closed'] - 2.0) < 1e-9, s2
assert s2['no_progress_streak'] == 1, s2
assert dict(format_signals(s2))['iterations per closed'] == '2.00', s2

c = write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
(c / 'iterations.jsonl').write_text('')
s3 = compute_signals(load_run(c))
assert s3['iterations'] == 0 and s3['tasks_done'] == 0 and s3['tasks_total'] == 0, s3
assert s3['iterations_per_closed'] is None, s3
assert s3['no_progress_streak'] == 0, s3
assert dict(format_signals(s3))['iterations per closed'] == 'n/a', s3
print('signals ok')
PY
```

</details>

### T5 — Build the CLI entry points and the summary command

`done` · depends on: T3

This is the first thing an operator actually runs. It brings up the argument parser, the console script and python -m runstat, and implements summary: a per-phase rollup of sessions, cost, turns and wall time with a total row. The error and denial callouts are not decoration — a permission denial nobody sees is a fence in the wrong place, so a session with is_error true or a non-empty permission_denials list has to be named in the output.

**Acceptance**

- Both `uv run runstat summary <run-dir>` and `uv run python -m runstat summary <run-dir>` work and produce the same output.
- summary prints one row per phase present (plan, work, review) plus a total row, each carrying session count, total cost, total turns and total wall time.
- On the brief's fixture the rows pair up exactly as the brief's table does: plan with $1.98 / 12 turns / 141s, work with $1.50 / 18 / 204s, review with $0.60 / 9 / 72s, and total with 7 sessions / $4.08 / 39 / 417s.
- Costs print to two decimals with a dollar sign; wall time prints as whole seconds with an s suffix (141s, not 141.0s and not 2m21s). Column widths, padding and separators are free choices.
- The output states somewhere that dollar figures are an estimate, not a bill.
- Any session with is_error true, or with a non-empty permission_denials list, is called out in the output by its session file name; the command still exits 0.
- Tests drive the CLI over the fixture inside tmp_path and assert on content, not on column alignment.

<details><summary>verify command</summary>

```sh
uv run python -c "
import sys,json,pathlib,tempfile,subprocess
sys.path.insert(0,'tests')
from fixtures import write_fixture_run
r=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
p=subprocess.run(['runstat','summary',str(r)],capture_output=True,text=True)
assert p.returncode==0, (p.returncode,p.stderr)
lines=[l for l in p.stdout.splitlines() if l.strip()]
def toks(l):
    return ''.join(ch if (ch.isdigit() or ch=='.') else ' ' for ch in l).split()
def row(name):
    c=[l for l in lines if name in l.lower() and any(ch.isdigit() for ch in l)]
    assert c, (name,p.stdout)
    return set(toks(c[-1]))
assert set(['1.98','12','141']) <= row('plan'), p.stdout
assert set(['1.50','18','204']) <= row('work'), p.stdout
assert set(['0.60','9','72']) <= row('review'), p.stdout
assert set(['7','4.08','39','417']) <= row('total'), p.stdout
assert 'estimat' in p.stdout.lower(), p.stdout
v=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
a=v/'sessions'/'004-work.json'
d=json.loads(a.read_text()); d['is_error']=True; a.write_text(json.dumps(d))
b=v/'sessions'/'006-work.json'
d=json.loads(b.read_text()); d['permission_denials']=[{'tool_name':'WebFetch'}]; b.write_text(json.dumps(d))
q=subprocess.run(['runstat','summary',str(v)],capture_output=True,text=True)
assert q.returncode==0, (q.returncode,q.stderr)
assert '004-work.json' in q.stdout and '006-work.json' in q.stdout, q.stdout
print('summary ok')
"
```

</details>

### T6 — Add the signals command

`done` · depends on: T4, T5

This is the command the operator reads after a run to decide whether it converged, and the one brief 0002 checks against the driver's own inline numbers. It is a thin printer over compute_signals: eight key: value lines, in the brief's order, with the brief's exact labels. The values are the contract; the padding between the colon and the value is not.

**Acceptance**

- `uv run runstat signals <run-dir>` prints exactly eight lines and nothing else, one per signal, in the brief's order.
- Each line is `<label>: <value>` using the labels iterations, tasks closed, iterations per closed, gate failures, review rejections, attempts burned, no-progress streak, estimated spend.
- On the brief's fixture the values are exactly 3, 2/8, 1.50, 1, 0, 1, 0 and $4.08.
- The values come from compute_signals — the command formats and prints, it does not recompute any derivation.
- The label estimated spend is what marks the money as an estimate; the command exits 0 on a readable run.
- A test drives the command over the fixture in tmp_path and asserts all eight values exactly.

<details><summary>verify command</summary>

```sh
uv run python -c "
import sys,pathlib,tempfile,subprocess
sys.path.insert(0,'tests')
from fixtures import write_fixture_run
r=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
p=subprocess.run(['runstat','signals',str(r)],capture_output=True,text=True)
assert p.returncode==0, (p.returncode,p.stderr)
lines=[l for l in p.stdout.splitlines() if l.strip()]
pairs=[(l.split(':',1)[0].strip(),l.split(':',1)[1].strip()) for l in lines]
assert pairs==[('iterations','3'),('tasks closed','2/8'),('iterations per closed','1.50'),('gate failures','1'),('review rejections','0'),('attempts burned','1'),('no-progress streak','0'),('estimated spend','\$4.08')], pairs
print('signals cmd ok')
"
```

</details>

### T7 — Add the compare command

`done` · depends on: T6

This is the repeatability check: two runs of the same plan side by side, so a large divergence in cost or iterations is visible as the finding it is. It reuses the same eight signals rather than inventing a second set, and adds a delta column. Only signals that are numbers get a delta — tasks closed is a pair like 2/8 and subtracting it would be meaningless, so its delta stays blank.

**Acceptance**

- `uv run runstat compare <run-a> <run-b>` prints all eight signals as rows, each showing the value for run A, the value for run B, and a delta.
- The delta is run B minus run A, signed, for signals whose values are numeric (including the dollar figure); it is blank for non-numeric signals such as tasks closed.
- Comparing the brief's fixture against a variant with its last iteration record removed shows iterations 3 then 2 with a delta of -1, and iterations per closed 1.50 then 2.00 with a positive delta.
- The command exits 0 when both run directories are readable.
- Both runs' signals are the ones compute_signals produces — compare does not define its own derivations.
- A test compares the fixture with a variant it builds inside tmp_path and asserts at least one numeric delta.

<details><summary>verify command</summary>

```sh
uv run python -c "
import sys,pathlib,tempfile,subprocess
sys.path.insert(0,'tests')
from fixtures import write_fixture_run
a=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
b=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
j=b/'iterations.jsonl'
keep=[l for l in j.read_text().splitlines() if l.strip()][:-1]
j.write_text(chr(10).join(keep)+chr(10))
p=subprocess.run(['runstat','compare',str(a),str(b)],capture_output=True,text=True)
assert p.returncode==0, (p.returncode,p.stderr)
out=p.stdout
low=out.lower()
for k in ['iterations','tasks closed','iterations per closed','gate failures','review rejections','attempts burned','no-progress streak','estimated spend']:
    assert k in low, (k,out)
lines=[l for l in out.splitlines() if l.strip()]
def toks(l):
    return ''.join(ch if (ch.isdigit() or ch=='.' or ch=='-' or ch=='+') else ' ' for ch in l).split()
it=[l for l in lines if l.strip().lower().startswith('iterations') and not l.strip().lower().startswith('iterations per')]
assert it, out
t=toks(it[-1])
assert '3' in t and '2' in t and any(x.startswith('-1') for x in t), (t,out)
pc=[l for l in lines if l.strip().lower().startswith('iterations per')]
assert pc, out
t2=toks(pc[-1])
assert '1.50' in t2 and '2.00' in t2, (t2,out)
tc=[l for l in lines if l.strip().lower().startswith('tasks closed')]
assert tc and '2/8' in tc[-1] and '1/8' in tc[-1], (tc,out)
print('compare ok')
"
```

</details>

### T8 — Enforce the exit-code and error-output contract across all commands

`done` · depends on: T5, T6, T7

The three commands exist by now, but their behaviour on bad input is what decides whether a report can be trusted: 0 on success, 1 for a valid run directory with no sessions, 2 for a usage error, a missing directory or malformed input. A partial result that looks complete is the exact failure this brief was written against, so a bad file is a hard stop naming the offending path. No traceback ever reaches the user and stdout stays empty whenever the command fails.

**Acceptance**

- Exit 2 for: a missing run directory, any malformed session file, any malformed iterations.jsonl line, an unknown subcommand, and a missing or extra positional argument.
- Exit 1 when the run directory exists and is well-formed but contains no session files.
- Exit 0 on success for all three commands.
- On every failing path stdout is completely empty and the explanation goes to stderr.
- The stderr message for malformed input names the offending file — the session file's name, or iterations.jsonl.
- No Python traceback ever reaches stderr, for any of these cases.
- Tests cover each exit code for each command where it applies, driving the CLI as a subprocess inside tmp_path.

<details><summary>verify command</summary>

```sh
uv run python -c "
import sys,pathlib,tempfile,subprocess
sys.path.insert(0,'tests')
from fixtures import write_fixture_run
base=pathlib.Path(tempfile.mkdtemp())
def cli(*a):
    return subprocess.run([sys.executable,'-m','runstat']+list(a),capture_output=True,text=True)
def bad(p,code):
    assert p.returncode==code, (p.returncode,code,p.stdout,p.stderr)
    assert p.stdout=='', p.stdout
    assert p.stderr.strip(), 'error path wrote nothing to stderr'
    assert 'Traceback' not in p.stderr, p.stderr
missing=str(base/'nope')
bad(cli('summary',missing),2)
bad(cli('signals',missing),2)
bad(cli('compare',missing,missing),2)
empty=base/'empty-run'
(empty/'sessions').mkdir(parents=True)
(empty/'iterations.jsonl').write_text('')
bad(cli('summary',str(empty)),1)
bad(cli('signals',str(empty)),1)
m=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
f=m/'sessions'/'003-review.json'
f.write_text('{ not json')
p=cli('summary',str(m))
bad(p,2)
assert '003-review.json' in p.stderr, p.stderr
n=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
j=n/'iterations.jsonl'
j.write_text(j.read_text()+'oops'+chr(10))
q=cli('signals',str(n))
bad(q,2)
assert 'iterations.jsonl' in q.stderr, q.stderr
bad(cli(),2)
bad(cli('bogus',str(m)),2)
bad(cli('summary'),2)
ok=write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
z=cli('signals',str(ok))
assert z.returncode==0 and z.stdout.strip(), (z.returncode,z.stderr)
print('contract ok')
"
```

</details>

### T9 — Add the end-to-end worked-example acceptance test

`done` · depends on: T8

Each earlier task was verified in isolation, which is exactly how an implementation drifts from the documented behaviour while every part still passes. This test replays the brief's transcript end to end against the installed CLI — summary, signals and compare over one fixture — so the whole is checked, not the pieces. The brief calls this the one test that catches that drift.

**Acceptance**

- tests/test_worked_example.py defines test_summary, test_signals and test_compare, each invoking the installed CLI as a subprocess rather than calling Python functions directly.
- test_summary asserts the brief's per-phase pairing — plan $1.98/12/141s, work $1.50/18/204s, review $0.60/9/72s, total 7/$4.08/39/417s — on content, not on column alignment, and asserts the estimate wording is present.
- test_signals asserts all eight key: value lines exactly, values included.
- test_compare builds a variant of the fixture and asserts at least one numeric delta.
- Every test writes only inside pytest's tmp_path; no test reads loop/runs/ or any other real run directory.
- The full suite `uv run pytest -q` passes.

<details><summary>verify command</summary>

```sh
uv run pytest -q tests/test_worked_example.py::test_summary tests/test_worked_example.py::test_signals tests/test_worked_example.py::test_compare
```

</details>

### T10 — Write the README, with every documented example matching real output

`done` · depends on: T9

Write README.md covering what runstat is, how to install and run it, the three commands, the exit-code contract, and the input layout it reads. Every example must show output captured from the tool as it actually behaves. A README whose examples have drifted from the code is worse than none, so the gate replays what the tool prints and requires each line to appear verbatim in the document.

**Acceptance**

- README.md documents runstat summary, runstat signals and runstat compare, each with a worked example
- Every line the signals command prints for the fixture run appears verbatim in the README
- The exit-code contract (0 success, 1 no sessions, 2 usage or malformed) is documented
- The input layout it reads (sessions/*.json and iterations.jsonl) is described
- Install and run instructions use uv
- Any dollar figure in the README is labelled an estimate

<details><summary>verify command</summary>

```sh
uv run python - <<'PY'
import pathlib, subprocess, sys, tempfile
sys.path.insert(0, 'tests')
from fixtures import write_fixture_run

t = pathlib.Path('README.md').read_text()
for cmd in ['runstat summary', 'runstat signals', 'runstat compare']:
    assert cmd in t, cmd
for token in ['sessions/', 'iterations.jsonl', 'uv']:
    assert token in t, token
assert 'estimate' in t.lower(), 'no estimate wording for money'
for code in ['0', '1', '2']:
    assert code in t
r = write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
p = subprocess.run(['runstat', 'signals', str(r)], capture_output=True, text=True)
assert p.returncode == 0, (p.returncode, p.stderr)
for line in [l.strip() for l in p.stdout.splitlines() if l.strip()]:
    assert line in t, 'README does not match real output: ' + line
print('readme ok')
PY
```

</details>

### T11 — Document the telemetry contract and the cross-check against the driver

`pending` · depends on: T9

Write docs/runstat.md: the on-disk telemetry contract runstat consumes, field by field, and how each of the eight signals is derived. This is the document that keeps the loop driver and runstat from drifting apart — brief 0002 acceptance item 6 requires them to agree, and a derivation recorded in only one of the two implementations is how that agreement quietly breaks.

**Acceptance**

- docs/runstat.md documents every field runstat reads from a session record and from an iterations record
- Each of the eight signals has its derivation stated
- The attempts-burned derivation explicitly warns against summing the cumulative attempts field
- The document states that loop/run.sh computes the same signals and that the two must agree
- Every signal label used in the document matches the label the CLI actually prints
- No absolute paths appear anywhere in the document

<details><summary>verify command</summary>

```sh
uv run python - <<'PY'
import pathlib, subprocess, sys, tempfile
sys.path.insert(0, 'tests')
from fixtures import write_fixture_run

t = pathlib.Path('docs/runstat.md').read_text()
for k in ['sessions/', 'iterations.jsonl', 'phase', 'iteration', 'total_cost_usd',
          'num_turns', 'duration_ms', 'is_error', 'permission_denials',
          'outcome', 'attempts', 'tasks_done', 'tasks_total']:
    assert k in t, k
assert 'run.sh' in t, 'does not mention the driver it must agree with'
assert '/Users/' not in t, 'absolute path in the document'
r = write_fixture_run(pathlib.Path(tempfile.mkdtemp()))
p = subprocess.run(['runstat', 'signals', str(r)], capture_output=True, text=True)
assert p.returncode == 0, (p.returncode, p.stderr)
labels = [l.split(':', 1)[0].strip() for l in p.stdout.splitlines() if l.strip()]
assert len(labels) == 8, labels
for lab in labels:
    assert lab in t, 'label not documented: ' + lab
print('docs ok')
PY
```

</details>

