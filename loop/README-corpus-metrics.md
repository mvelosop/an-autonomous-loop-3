# corpus-metrics.sh

Machine-readable size metrics for an agent loop's **instruction corpus** and
**executable harness**, emitted as JSON. Portable across repo layouts — one
copy measures any repo, so two loop implementations can be compared on the
same basis.

```bash
./corpus-metrics.sh                                     # measure $PWD
./corpus-metrics.sh --root ../other-repo --name theirs  # measure elsewhere
./corpus-metrics.sh --root . > metrics.json
```

Reporting tool, not a gate: exits 0 on success, never edits a file.

## What it separates, and why

### Instructions vs. harness

**Instructions** are prose a model reads and interprets — its effect depends on
a model's judgment at read time. **Harness** is code a shell executes — its
effect is an exit code.

The operational test is *can it fail?* A lint script exits non-zero and blocks a
commit. A guideline rule can only be followed, ignored, or read differently by
the next model. One is a gate; the other is guidance.

Note the containment: in the field's usual sense, "harness" (or *agent
scaffold*) is the **whole** apparatus around the model, instructions included.
This script uses the narrower sense — executable code only — because the split
is the thing being measured. When quoting figures outside this repo, say
*gates* and *instructions* rather than *harness* and *prose*, or a reader who
knows the term will read the containment backwards.

### Production vs. test (the one that matters)

Inside the harness, test lines **never run during a loop tick**. Delete them and
the loop behaves identically. They are not part of the machine; they are the
evidence the machine works, and the thing that makes it safely editable.

That is a category difference, not a smaller amount of the same thing — which
is why `test_lines_per_production_line` is the most informative single number
the script emits. A harness with more test code than production code is one you
can change without fear. A harness with a thin test layer over a large prose
corpus mostly *believes* it is verified.

### In-loop vs. operator

A production script is `in_loop: true` when its basename appears in any
agent / skill / guideline file — i.e. something in the corpus can actually
reach it. Scripts named only in `CLAUDE.md` or other orchestration prose are
deliberately **not** counted (a per-machine setup script is not a loop gate).

This answers "how much executable enforcement does the loop actually have"
mechanically, and it is usually much less than the raw harness total.

## Categories

| Category | Subcategory | Rule |
|---|---|---|
| `instructions` | `agents` | `.claude/agents/**/*.md` |
| | `skills_body` | `.claude/skills/**/SKILL.md` — the contract |
| | `skills_support` | other `.md` under `skills/` — references, templates, samples |
| | `guidelines` | `.claude/guidelines/**/*.guidelines.md` — the binding surface |
| `harness` | `production` | `*.sh` / `*.py` / `*.bash` under a harness dir |
| | `tests` | same, but under `tests/`, or `*.fixture.sh` / `*-test.sh` / `*_test.py` |
| `other` | `orchestration` | `CLAUDE.md`, `.claude/README.md`, `.claude/project-adapter.md` |
| | `index` | non-binding `.md` in `guidelines/` (README indexes) |

Harness dirs, first-found from: `.claude/scripts`, `loop`, `scripts`, `bin`,
`tools`. `other` is reported but **excluded from the instruction total**, so
totals stay comparable between repos that do and don't have a `CLAUDE.md`.

The script excludes **itself** by basename (`--include-self` to override) — a
measurement tool should not inflate its own measurement.

## Metrics per segment

| Field | Meaning |
|---|---|
| `files` | file count |
| `lines` | `wc -l` |
| `words` | `wc -w` |
| `chars` | `wc -c` |
| `est_tokens` | `chars / 4` — a rough proxy, see caveat below |
| `code_lines` | non-blank, non-comment. Meaningful for shell/Python, **noise for prose** — ignore it on instruction segments |

### On `words` and `est_tokens` — what they do and don't measure

Words are a reasonable proxy for how much a model must read to comply, and
`est_tokens` is a better one (English prose runs ~4 chars/token; markdown with
tables, headers and code fences runs denser, so treat it as ±20%). Both are
counts of *text volume*, and text volume is what competes for attention: long
contexts measurably degrade instruction-following, and rules dilute each other
as they accumulate.

But the corpus total is **not** the per-tick attention load. Skills load on
demand, guidelines load when cited, and only one agent definition is resident
at a time. So read the numbers this way:

- **Corpus words** = maintenance surface, and the ceiling on what could load.
  This is the number that ratchets — every new rule is surface for the next
  reader to hold and the next amendment to land on.
- **Resident tokens per tick** = the actual attention load. Smaller, varies by
  task, and this script does not compute it.

Quoting a corpus total as "what the model reads" overstates it. Quoting it as
"how much instruction this system has accumulated" is exactly right.

## Ratios

| Ratio | Reads as |
|---|---|
| `instruction_words_per_harness_word` | how far the contract leans toward prose vs. code |
| `instruction_words_per_in_loop_harness_word` | same, counting only code the loop can reach |
| `test_lines_per_production_line` | **> 1 means the harness is more tested than it is large** |
| `test_share_of_harness_lines` | fraction of harness code that is evidence, not behavior |

## Output

Top-level: `name`, `root`, `commit`, `branch`, `dirty`, `generated_at`, then
`segments`, `ratios`, and a per-file `files[]` array for re-aggregating.

`commit` + `dirty` exist so any number quoted in a write-up is **pinnable** —
re-running at that commit must reproduce it. A `dirty: true` reading is not
citable.

## What it doesn't measure

- **A driver.** The script counts code but not control flow. A loop whose
  `run.sh` invokes the model, and one where the model invokes the scripts, both
  show as "harness production" — the direction of control is not in the data.
  Check it by hand; it is often the biggest structural difference between two
  systems.
- Product code, product tests, ADRs, design notes, and non-shell tooling.
- Whether any of the instructions are any good.
