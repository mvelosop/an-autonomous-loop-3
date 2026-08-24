# Brief B006 — Consultant CRM, the documentation experiment's sample app

- **Status:** draft — not ready to plan
- **Role:** the sample application the *documentation experiment* builds once and
  then modifies three times. It is a **measurement instrument**, not a product.
- **Starting point:** greenfield
- **Numbering:** first brief on the `BNNN` scheme. Brief numbers are authoring
  order; run numbers are execution order, and the two are independent. It
  starts at `B006` rather than `B005` because `0005` was already taken under
  the old scheme — two documents claiming "5" is the ambiguity the prefix
  exists to remove, so the sequence continues rather than restarting.

> **Why this is a draft.** The experiment design it serves is not settled, and
> at least one alternative sample domain is still under discussion. Everything
> below is the CRM option written out far enough to be compared against
> alternatives and costed. Flipping `Status:` to `ready to plan` is the only
> edit needed to put the v1 requirements in front of `loop/check-brief.sh` and
> then the planner.

---

## What it is

A single-user CRM for an independent consultant: the people you know, every
touchpoint with them, whether you are overdue to reach out, and the proposals
you have outstanding. Local, offline, one SQLite file, driven from a CLI.

It exists to answer one question — **does documentation produced up front beat
letting the planner read the code?** — so it is specified for *measurability*
first and usefulness second.

## Why this domain

The experiment's hypothesis is that documentation carries **decisions**, and
that code cannot. A domain whose difficulty is concentrated in policy rather
than in structure is therefore the sharper test. Structural invariants ("a copy
cannot be loaned twice") leave fingerprints a scanner can find — a unique index,
an existing guard. Policy invariants leave nothing:

- Does an *inbound* message mean you stayed in touch, or only an outbound one?
- Does chasing a proposal count as tending the relationship?
- Is an expired proposal a stored state or a computed one?

Every wrong answer produces an implementation that looks entirely reasonable
and passes any test its author would think to write. That is the failure this
experiment is built to detect.

The four categories of knowledge that are **not recoverable from code**, each of
which v1 must carry at least one instance of:

| Category | Instance in v1 |
| --- | --- |
| Prohibitions — absence leaves no trace to grep | Interactions are append-only; a merge is never reversed |
| Rationale behind a judgment call | Why cadence ignores inbound traffic |
| Cross-module invariants enforced far from where a change lands | The proposal-linked exclusion, honoured by cadence but deliberately *not* by the frequency report |
| Deliberate deviations from the local pattern | Expiry computed on read while every other state is stored |

---

# Part 1 — v1 requirements

## Entities

| Entity | Fields |
| --- | --- |
| **Contact** | `id`, `display_name`, `email`, `phone`, `tier`, `status`, `created_on` |
| **Interaction** | `id`, `contact_id`, `occurred_on`, `channel`, `direction`, `proposal_id` (nullable), `note` — **append-only** |
| **Tag** / **ContactTag** | `id`, `name` — many-to-many with Contact |
| **Relationship** | `id`, `from_contact_id`, `to_contact_id`, `kind` — directed |
| **FollowUp** | `id`, `contact_id`, `proposal_id` (nullable), `due_on`, `state`, `note` |
| **CadencePolicy** | `tier`, `interval_days` |
| **Proposal** | `id`, `contact_id`, `title`, `amount_cents`, `currency`, `state`, `sent_on`, `expires_on`, `decided_on` |

Enumerations: `tier` ∈ {`close`, `regular`, `occasional`} · `status` ∈
{`active`, `dormant`, `archived`} · `channel` ∈ {`call`, `email`, `meeting`,
`message`} · `direction` ∈ {`outbound`, `inbound`} · FollowUp `state` ∈ {`open`,
`snoozed`, `done`, `dropped`} · Proposal `state` ∈ {`draft`, `sent`, `accepted`,
`rejected`, `withdrawn`} — note that `expired` is **absent** from the stored
enumeration on purpose; see P3.

Default cadence policy: `close` 30 days · `regular` 90 · `occasional` 180.

## The policy decisions

These are the load-bearing part of the brief. Each is a decision with no code
footprint, and each is what the documentation arm will carry and the
code-scanning arm will have to guess.

- **P1 — Only outbound interactions reset the cadence clock.** Inbound traffic
  is recorded and reported but does not mean you stayed in touch. The point of
  the tool is prompting *you* to act.
- **P2 — A proposal follow-up does not reset the cadence clock.** Chasing is not
  tending. Mechanically: an interaction with a non-null `proposal_id` is
  excluded from the cadence computation.
- **P3 — Expiry is computed on read, never stored.** A proposal whose
  `expires_on` has passed with no decision reports as `expired` everywhere,
  without any write ever having occurred. There is no sweeper and no scheduled
  job. This deviates from every other state in the model, which is stored.
- **P4 — Merge is irreversible and audited.** The source contact is tombstoned,
  never deleted; its interactions are re-pointed to the target; tags union;
  relationships deduplicate. The operation is recorded.
- **P5 — Dormancy uses traffic in *either* direction.** A contact is `dormant`
  after 2× its tier interval with no interaction inbound or outbound. This is
  deliberately *not* P1's rule — dormancy asks whether the relationship is
  alive, cadence asks whether you have done your part.

**The asymmetries are the point.** P1/P2 filter; the frequency report
(below) deliberately does not. An implementation that applies one filter
uniformly across every consumer is wrong, and is exactly what an
undocumented implementation produces.

## Consumers — the ripple surface

Nine readers, because a domain change only hurts when several things downstream
have *different* correct answers. This is what makes the app a measuring
instrument rather than a demo.

| Command | What it computes |
| --- | --- |
| `crm overdue` | Contacts past their tier interval, per P1 + P2 |
| `crm contact show <id>` | One contact's full timeline |
| `crm report frequency` | Interaction counts per contact, ranked — **all** interactions, unfiltered |
| `crm report dormancy` | active / dormant / archived, per P5 |
| `crm search` | Filters, including `--contacted-since` |
| `crm export interactions` | CSV, one row per interaction |
| `crm contact merge <src> <dst>` | Re-points ownership, per P4 |
| `crm proposals awaiting` | Sent, undecided, unexpired — per P3 |
| `crm report pipeline` | Proposal value by state — per P3 |

Write commands: `crm contact add|edit|tag`, `crm interaction add`,
`crm relationship add`, `crm followup add|snooze|done|drop`,
`crm proposal add|send|accept|reject|withdraw`.

Putting **merge in v1** is deliberate: every later domain change then has to fix
merge too, and merge is where an undocumented implementation reliably goes wrong
in a way no obvious test catches.

## Behaviour contract

**Exit codes.** `0` success · `1` a referenced entity does not exist · `2` usage
error, malformed input, or an illegal state transition.

**Errors go to stderr; stdout stays empty on failure; no traceback ever reaches
the user.**

**The clock is an argument, never a syscall.** Every command that depends on
today's date accepts `--today YYYY-MM-DD`, and the whole codebase reads the
current date through exactly one seam. *This is a constraint with a design
consequence:* without it none of the cadence, dormancy or expiry behaviour is
gateable, and half the acceptance criteria become untestable.

**Money is integer minor units end to end.** `amount_cents` plus an ISO
currency; formatting happens once, at the edge.

**Interactions are append-only.** There is no `interaction edit` and no
`interaction delete`. Recording something that did not happen is corrected by
recording a correction.

**Illegal transitions exit 2.** Accepting a `draft`, sending an `accepted`,
re-deciding a decided proposal.

## Worked example

The end-to-end acceptance test. Every value is exact; it is what arbitrates when
two implementations disagree — and it is built so that the *plausible wrong*
implementation disagrees visibly.

Fixture, three contacts:

| id | name | tier | created_on |
| --- | --- | --- | --- |
| `c1` | Ada Lovelace | close (30d) | 2025-09-01 |
| `c2` | Grace Hopper | regular (90d) | 2025-10-01 |
| `c3` | Alan Turing | occasional (180d) | 2025-06-01 |

Four interactions:

| id | contact | occurred_on | channel | direction | proposal_id |
| --- | --- | --- | --- | --- | --- |
| `i1` | c1 | 2026-02-20 | meeting | outbound | — |
| `i2` | c2 | 2026-01-05 | email | inbound | — |
| `i3` | c3 | 2025-11-15 | call | outbound | — |
| `i4` | c2 | 2026-01-24 | email | outbound | `p1` |

One proposal: `p1` for c2, "Data pipeline audit", 450000 minor units EUR, sent
2026-01-10, expires 2026-02-10, no decision recorded.

With `--today 2026-03-01`:

```
$ crm overdue --today 2026-03-01
Grace Hopper      regular      overdue 61d      last outbound: never

$ crm proposals awaiting --today 2026-03-01
(none)

$ crm report pipeline --today 2026-03-01
sent        0    EUR       0.00
accepted    0    EUR       0.00
expired     1    EUR    4500.00

$ crm report frequency
Grace Hopper    2
Ada Lovelace    1
Alan Turing     1

$ crm report dormancy --today 2026-03-01
active     c1  c2
dormant    c3
```

Three places the naive implementation disagrees, and each is a policy decision
rather than a bug in the obvious sense:

- **`overdue`** — reading "last interaction of any kind" puts c2's last contact
  at 2026-01-24, 36 days ago, inside a 90-day interval, and reports nothing
  overdue. P1 discards `i2` (inbound) and P2 discards `i4` (proposal-linked), so
  c2 has *never* been contacted and is 61 days past due, counting from
  `created_on`.
- **`pipeline` / `proposals awaiting`** — reading the stored state reports `p1`
  as `sent` and awaiting a reply. P3 computes expiry on read: it expired on
  2026-02-10.
- **`frequency`** — applying P1/P2's filter here as well gives c2 a count of 0.
  Frequency answers "how much traffic", not "did I do my part", and counts all
  four interactions.

**Assert on content, not on column alignment.** Padding and column widths are
the implementation's choice; the values, labels and their pairing are the
contract.

---

# Part 2 — the initial plan of updates

v1 is the frozen baseline. The experiment then applies **domain changes**, not
additions — a change with no neighbour to copy is the only kind that punishes a
missing model, because every existing call site silently encodes the old
assumption and nothing marks which ones were load-bearing.

Each change gets its own brief and is run independently under every arm.

| # | Change | Ripple | Prediction |
| --- | --- | --- | --- |
| **U1** | **Interaction becomes multi-participant.** One event, N contacts. | All nine consumers, each with a *different* right answer | docs ≫ scan |
| **U2** | **Proposal recipient becomes multi-contact.** A proposal to a couple or a company. | Compounds with U1: whose cadence, whose follow-up clock, awaiting from whom | docs ≫ scan |
| **U3** | **Proposal supersession.** v2 replaces v1; a flat entity becomes a versioned chain. | Lifecycle, follow-up clock, pipeline reporting, merge | docs > scan |
| **U4** | **Preferred-name field, shown in display.** *(control)* | Local; the pattern is visible in five neighbours | scan ties or wins |

**U1 is the lead.** Stated in a sentence, and the answers diverge immediately:
cadence resets for all attendees; frequency counts once *per person*, not once
in total; export emits N rows sharing an event id, or one row — a decision, not
a fact; merging two attendees of the same event must not double-count it;
`--contacted-since` matches all of them. A no-docs implementation adds a join
table, keeps the old FK as "primary participant", passes every existing test,
and silently breaks cadence for everyone but one attendee.

**U4 earns its place by being expected to show nothing.** A slate on which the
treated arm wins everywhere is a slate that cannot distinguish a real effect
from a rigged one.

Each change also forces a **data migration** over existing rows — independently
checkable, and a natural hook for a migrations guideline citation.

## Rules that keep the experiment valid

Three, and violating any one voids the results:

1. **Every change branches from the same frozen v1.** Run them sequentially and
   the scanning arm's v1.1 structurally differs from the documented arm's, so
   U2 no longer measures U2 — it measures accumulated damage from U1.
   Three changes × three arms = nine branches from one commit.
2. **The architect's per-feature doc updates stay on the arm branch.** Merging
   them back into v1 leaks U1's design into U3's baseline.
3. **The requirement for each change is frozen before any arm runs**, and is
   handed to every arm byte-identically. It states **invariants and policy**;
   the documentation states **sites and rationale**. The scanning arm knows the
   target and must find every place it applies.

---

## Out of scope

For v1. A plan that adds any of these has widened its own scope, which is itself
worth knowing:

- Anything held back for the update slate — multi-participant interactions,
  multi-contact proposals, proposal supersession.
- HTTP API, web UI, or TUI. One CLI.
- Any sync with an external source: contacts, email, calendar, LinkedIn.
- Sending anything. No email, no notifications, no scheduled jobs.
- Multi-user, authentication, sharing, or per-user data isolation.
- Full-text search over notes. `search` filters on structured fields only.
- Undo, soft-delete-and-restore, or any reversal of a merge.
- Real contact data of real people, in fixtures or anywhere else.

## Constraints

- Python 3.13, `uv`, `src/` layout, `pytest`. SQLite via the standard library's
  `sqlite3`; **no runtime dependency outside the standard library**, and no ORM.
- Layered: domain / application / infrastructure, with a repository seam. The
  layering is not decoration — it is what the imported convention guidelines
  bind to, and an unlayered CLI leaves half of them with nothing to cite.
- The whole suite runs in **seconds**. Gates re-run every iteration, and the
  experiment runs this app eighteen times.
- Every test writes inside `pytest`'s `tmp_path`. No test touches a real
  database file.
- One clock seam, injected. No `date.today()` outside it.
- Fixtures use obviously synthetic people.
- Repo-relative paths in every file, log line and commit message.

## Shape

Roughly **twelve to sixteen tasks**, each independently verifiable by a single
command.

Two things the planner should get right, because they are what the priors got
wrong: a scaffolding task still needs a verify command that passes for the right
reason (`uv run pytest` with zero tests collected exits **5**, not 0), and each
verify command has to be authored before its implementation exists.

The nine consumers are the part most likely to be under-decomposed. Each has a
distinct rule and at least one asymmetry against its neighbours; folding several
into one task loses the property that makes this app worth building.

## Open questions

- **Which repository does the app live in?** A separate published repo keeps the
  experiment's provenance clean and keeps real data pressure away from this one.
  Unresolved.
- **Where does the imported guideline canon come from?** The architect skill is
  explicitly barred from authoring guidelines. A Python-flavoured canon needs
  sourcing or adapting before the BDUF act can cite it.
- **Is the CLI enough surface?** A thin HTTP layer would let more of the canon
  bind, at the cost of a larger v1 and a longer BDUF act.
- **Is this the right domain at all?** An alternative is under discussion.
