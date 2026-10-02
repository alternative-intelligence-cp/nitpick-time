# Roadmap — the cycle map

The specification set (`meta/specs/`) is written and the decisions it rests on
are in `meta/DECISIONS.md`. This is the plan built on them.

**At cycle 0.1's close, 138 decisions are settled** — TM-001 … TM-030, the
founding batch written with the specification set, and 108 more, each batch
appended whole by the subcycle that settled it, the last TM-207 at the close.
**Eleven questions are open** in `../OPEN_QUESTIONS.md`, each with a
recommendation and the cycle that settles it or the reason it waits: four are
the compiler's — O-N1, O-N2, O-N3 and O-N25 — and seven ours: O-X1, O-B1,
O-X3, O-X4, O-X6, O-X8 and O-X9. **No cycle in this plan is blocked on a
decision** — but one CHECK is: `check_int128_sites` does not go live before
O-X6 is answered, and cycle 0.2's README puts the two in order. *(Re-derived at
cycle 0.1.5's second half — the cycle audit's S2. From the founding plan to
that close this paragraph read "One decision batch is settled, TM-001 …
TM-030" and counted seven open questions "open by design" — 132 decisions and
ten questions when the audit read it — with O-X6's hold on a check beside
it.)* *(Cycle 0.2.3a: O-X6 is answered, TM-229, and `check_int128_sites` is live,
TM-230 — the one check this paragraph said a question held. Re-derived then,
**eight** questions are open, three the compiler's — O-N1, O-N2 and O-N3 —
and five ours — O-X1, O-B1, O-X4, O-X8 and O-X9: O-N25 was answered at cycle
0.2.0a, TM-208, and O-X3 at 0.2.0, TM-216, and this count was not moved
with either.)*

## How this is organised

- **A cycle is a folder** — `0.0/`, `0.1/`, … — focused on **one topic**.
- **A subcycle is a file inside it** — `0.0.0.md`, `0.0.1.md`, … — one workable
  chunk of that topic, written execution-grade before its code is touched.
- **A finished cycle moves to `done/`**, so the active work stays easy to find.
- **Commit after every subcycle. Push at the end of every cycle.**
- **Every cycle's README carries a checklist.** Tick items as they land; the
  checklist is the cycle's state.

This convention is the compiler repository's, deliberately, so that a session
moving between them reads one thing. **Each cycle's opening subcycle file is
written at the previous cycle's close**, by the session that just learned what
that cycle taught; cycle 0.0 is the exception, written up front because there
is no previous cycle.

---

## The two constraints that shape everything

**`ntime` cannot be built by `npkg` today**, and cross-repository imports do
not resolve (`specs/BUILD.md` §1, `../OPEN_QUESTIONS.md` O-N1). Consequently:

> **`harness/` is the build and test runner, and every import is relative,
> until the compiler's tooling closes O-N1.**

And the one that shapes the *architecture*:

> **Every identity a reachable `fail` site raises costs every consumer a
> `failsafe` arm (REACH-002) — public or private; *"every public `error:`"* until
> 2026-09-27, the ecosystem audit's EC3, TM-213 —
> integer overflow traps (D-210), and there is no format-specifier language
> (D-053).**

The first capped the error budget at three (TM-017) and decided the module
decomposition — `cal` does not import `zone`, so a program doing calendar
arithmetic owes one IDENTITY arm (and, measured at compiler `c970483`, 11 arms
in all <!-- [[sweep: arms_cal=11]] -->, the floor and `cal`'s arithmetic
included — `specs/SAFETY.md` S-4;
this said "owes one arm" until cycle 0.1.5). The second made every range a checked bound rather
than a hope. The third replaced `strftime` with a typed layout (TM-009,
TM-023).

**A third constraint is this library's own luck:** it is almost entirely pure
arithmetic over a small domain, so several of its properties can be checked
**exhaustively** rather than sampled (TM-026). Where that is possible it is the
gate, and it is the reason cycle 0.1's gate is stronger than anything in the
sibling libraries.

---

## Phase 0 — the library, built bottom-up

| Cycle | Topic | Gated on |
|---|---|---|
| ~~**0.0**~~ | **Foundations** — the language probes, the harness, `src/core/` — **CLOSED 2026-09-06, archived at [`done/0.0/`](done/0.0/README.md)** | — |
| ~~**0.1**~~ | **The civil calendar** — the types, Hinnant's algorithms, the exhaustive sweep — **CLOSED 2026-09-26, archived at [`done/0.1/`](done/0.1/README.md)** | 0.0 ✓ |
| **0.2** | **Instants and timestamps** — `Instant`, `Timestamp`, `Duration` interop — **IN PROGRESS**: [`0.2/0.2.0a.md`](0.2/0.2.0a.md), the adoption of compiler `5fbaf4a`, done; [`0.2/0.2.0b.md`](0.2/0.2.0b.md), `Vec<T: Copy>`, done; [`0.2/0.2.0.md`](0.2/0.2.0.md), `Instant`, done; [`0.2/0.2.1.md`](0.2/0.2.1.md), `Timestamp`, done; [`0.2/0.2.2.md`](0.2/0.2.2.md), the conversions and the gate, done; 0.2.3, the `Duration` interop, next | 0.1 ✓ |
| **0.3** | **The host boundary** — the clocks, the system-zone discovery, the test double | 0.2 |
| **0.4** | **Formatting and parsing** — the named formats, the typed layout, the round-trip gate | 0.2 |
| **0.5** | **The zone table** — the generator, the committed tables, the size measurement | 0.1 |
| **0.6** | **Zoned time** — offset lookup, the four resolution modes, the transition sweep | 0.4, 0.5 |
| **0.7** | **Calendar arithmetic** — `Period`, the clamping rules, `until`, rounding, the dogfood consumers | 0.6 |
| **0.8** | **Hardening** — the fuzz sweep, the stress sweep, the verification obligations, the audit | 0.7 |
| **1.0** | **Release** — documentation, the API freeze, the `failsafe` arm contract, versioning | 0.8 |

---

## What each cycle produces

### 0.0 — Foundations
The **language probes** first: small programs verifying that the shapes this
design depends on are spellable — a 16-byte `timespec` in a `buffer` handed to
`sys`, a `#[derive(Ord)]` struct whose comparison follows declaration order,
`int128` arithmetic with a narrowing `=>!`, a large `fixed` module-state table,
a payload enum in a `pick`. **A probe that fails changes the design**, and
finding that out on day one costs a day.

Then the harness (`harness/run.py`, its self-check, the stages, the tree
checks), the manifest's test table, CI, and `src/core/` — `Vec<T>`, `Bytes` and
the one file of named limits.

**Also here: the tzdb size spike.** `ZONE_MODEL.md` §3's ≈348 KiB is an
estimate from the *system* database; 0.0 runs the generator's core loop far
enough to emit a real table and report its size, so that TM-007's biggest
practical risk is measured on day one rather than at 0.5. Nothing is committed
from the spike but the number.

**CLOSED 2026-09-06 at pin `aaffb87`, archived at
[`done/0.0/`](done/0.0/README.md).** What it produced: 78 `.npk` in the tree,
62 suite units green in 62 s, 13 live tree checks each seen red on a planted
violation, 145 numbered decisions, and the tzdb measured at **475 006 B**
against a 348 KiB estimate that was wrong in four independent ways (TM-135).

**Two things it got wrong and found itself**, both use-after-frees on the
public surface — `vec_pop<T>` (TM-136) and `bytes_view` (TM-139) — and both
found by READING, under a green suite and an independent verification. *(A
third shipped with them and was not found in the cycle: `bytes_take`'s answer
was a view typed as an owned `string`, found at cycle 0.1.4b by the heap
instrument's count, `SAFETY.md` S-18f.)* The
cycle's most durable output is why: **every gate this repository owns is a leak
gate, and a use-after-free is a wrong answer.** `done/0.0/0.0.6.md` §3 is the
findings list; `SAFETY.md` S-18e is the rule.

### 0.1 — The civil calendar
`src/cal/`: `CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`,
Hinnant's `days_from_civil`/`civil_from_days`, the leap rule, ISO week dates,
ordinal dates, and the range constants pinned by a test that recomputes them.

**The cycle's gate, and the strongest statement this library makes:** every day
number in `[−4 371 587, +2 932 896]` round-trips in both directions —
7 304 484 cases each way, run in full, plus monotonicity, the weekday cycle and
month lengths on the same sweep. *(The bound read −4 371 588 and the count
7 304 485 until cycle 0.1.1: the range's first day was one day early, TM-161.)* *(Since cycle 0.1.2 monotonicity is stated as
each date's day number being the previous one's plus one, TM-167; and since
cycle 0.1.3 the weekday cycle is asserted, with `weekday()`, as a count begun
at −9999-01-01's Monday, TM-165 and TM-174. Until 0.1.3 this note read "the
weekday cycle is asserted at 0.1.3, where `weekday()` is written".)*

**CLOSED 2026-09-26 at compiler `c970483`, archived at
[`done/0.1/`](done/0.1/README.md)** — twelve subcycles, the close's second
half with the cycle audit's triage. What it produced: `src/cal/`, its gate on
every full run — the round trips, monotonicity, month lengths and the weekday
cycle over the whole range, and every date of years 1 … 9999 agreeing with
Python's `datetime` (TM-179) — and `C-12`'s totality asserted at its edges;
two adoptions, to compiler `c3bdae2` and `c970483`; the access properties and
a `Vec` move-only by construction (TM-156, TM-193 … TM-198); six, then eight,
files' managed memory held to the runtime's own count (TM-184 … TM-188); two
compiler defects raised, O-N20 and O-N23, each landed and asserted with its old
verdict as the control; a harness that reads source as the compiler's lexer
does and matches tokens (TM-199, TM-200, TM-202, TM-206); and 113 units green.
The table row read *"IN PROGRESS: …"* with each subcycle's file linked, and
`done/0.1/README.md` keeps that list. `done/0.1/0.1.5.md`'s record holds what
the cycle found and taught.

### 0.2 — Instants and timestamps
`src/span/`: `Instant` with its clock tag, `Timestamp` with its normalisation
invariant, the `Duration` constructors `ntime` adds, `timestamp_since` with its
±292-year refusal, and `timestamp_until` in calendar units.

**The cycle's gate:** the `Timestamp` ↔ civil round trip over every day
boundary in the range plus every second of 512 randomly chosen days, and a
property test that `nanos < 1_000_000_000` after every operation.

### 0.3 — The host boundary
`src/host/`: `clock_gettime` through `sys` with the `timespec` laid out in a
`buffer`, the three clocks, `host_system_zone`'s four-step discovery, and the
test double in `tests/`.

**The cycle's gate:** `check_purity` goes live and is green, and has been *seen
to fail* against a deliberately planted `mono_now()` outside `src/host/`.

### 0.4 — Formatting and parsing
`src/fmt/`: the named formats in both directions, `FmtPart` and `Layout`,
`format_with` and `parse_with`, the `Parsed` record with its two `folded_`
flags, and `ParseError`.

**Written printer-first**, because for a parser the printer is the oracle. The
cycle's gate is the round-trip fixed point over a generated corpus, with
exactly two documented exceptions and a test asserting the exception list has
exactly two entries.

### 0.5 — The zone table
`tools/gen_tzdb.py`: the TZif reader (in Python, at generation time, never at
run time), the POSIX-rule parser, the four flat tables, the name pool, and the
committed output. Plus `check_tables_regenerate` and
`check_table_invariants`.

**The cycle's gate:** the tables regenerate byte-identically, every invariant
holds over the committed data in one pass, and **the real emitted size is
measured and recorded** against §3's estimate (O-X2).

### 0.6 — Zoned time
`ZonedDateTime`, the transition binary search, the POSIX-rule extrapolation
past the last transition, the four resolution modes, and fixed offsets.

**The cycle's gate:** the transition sweep — every transition in the table, ±1
second — plus the per-zone round trip over every hour from 1970 to 2040, plus
the cross-oracle against Python's `zoneinfo` at the same pinned release.

### 0.7 — Calendar arithmetic
`Period` addition with the clamping rules, `until` in units, `truncate_to` and
`round_to`, and the wall-versus-instant rule on zoned values.

Also the **dogfood consumers** (Q-4): a `date`-equivalent CLI and a small
scheduler, written as consumers rather than by the author, with every friction
recorded and triaged.

**The cycle's gate:** every worked example in `SPAN_MODEL.md` §3 is a test, and
the DST cases from N-13 are goldens.

### 0.8 — Hardening
The parser fuzzer to exhaustion, `// stress: 40` on everything that reads a
clock, `specs/VERIFICATION.md`'s obligation list reconciled against what the
code actually generates, and a full audit of every specification rule against
its implementation.

### 1.0 — Release
`docs/` written, the public API frozen and enumerated in `src/lib.npk`, the
`failsafe` arm contract published and generated, examples for every format, and
the version policy from TM-013 stated where a consumer will read it.

---

## Post-1.0, as a map rather than a plan

| Cycle | Topic |
|---|---|
| **1.1** | The system tzdb reader (TM-028) — opt-in, its own error identity, its own fuzzer; a **major** version because of the fourth identity |
| **1.2** | `aarch64` Linux — the syscall numbers differ, the structures do not (TM-008) |
| **1.3** | Intervals, and possibly recurrence rules (Q-2) — `Interval` before `RRULE` |
| **1.4** | Verified build — `ntime`'s obligations through the compiler's `npkg verify`, once that reaches libraries |
| **1.5** | The `nparse` dependency (O-X1), once O-N1 closes |

---

## Ordering notes

- **The probes come first, in 0.0.** The compiler's own experience is the
  argument: *a construct that parses is not a construct that works*, and three
  of its cycles were mostly repair to constructs an earlier cycle had
  "finished".
- **The harness comes first too**, because it is how every later cycle is
  tested, and a suite written after the code is a suite shaped by the code.
- **The tzdb size is measured in 0.0, not 0.5.** It is TM-007's biggest
  practical risk and the cheapest thing to de-risk: a spike that emits a table
  and reports its size costs an afternoon, and finding at 0.5 that the answer
  is 4 MiB would reopen a decision the whole library rests on.
- **The calendar comes before everything**, because `Timestamp`, zones and
  formatting all convert through it, and because its gate is exhaustive — so
  every later cycle builds on something that has been checked over its whole
  domain rather than sampled.
- **Formatting precedes zones** (0.4 before 0.6), which means RFC 3339 with a
  fixed offset lands first and zoned formatting comes at 0.6. That is the right
  order: the round-trip gate wants to exist before there are zone-shaped values
  to round-trip.
- **The printer precedes the parser inside 0.4**, for the same reason the
  sibling library writes its oracle before its renderer: the checker should
  already work when the thing it checks is written.
- **`check_purity` goes live at 0.3**, the cycle that creates the only impure
  module — the compiler's rule that instruments precede the constructs they
  guard, applied to the property this library's reproducibility rests on.
- **A decision precedes the cycle that needs it.** Each cycle's README lists
  its open questions; a cycle whose questions are open is not ready to start.

---

## What to expect, from the compiler's experience

**A construct that parses is not a construct that works.** Most of the
compiler's cycle 0.4 was repair, and every repair dated to the cycle that had
parsed the construct. Here: a `#[derive(Ord)]` that compiles is not one that
compares the way the field order implies, and probe 03 in cycle 0.0 exists to
find that out before `Timestamp` depends on it.

**An analysis right on straight-line code and wrong after a merge passes every
test written the easy way.** Here: a zone lookup right in the middle of a
transition range and wrong at its first and last element, and a parser right on
a whole string and wrong on a prefix. Both have a dedicated test shape — the
transition sweep hits every boundary, and the fuzzer feeds truncations.

**Every hole was found by a check that diffs two lists, and none by a test.**
`specs/TESTING.md` §2 is this library's list, and the plan schedules each check
in the cycle that creates what it diffs.

**A suite that only ever agrees with what it is handed is worse than no
suite.** The harness self-check (V-14) is not optional and runs first — and it
has a case for a *silently skipped sweep*, because "the exhaustive test did not
run" is this library's most plausible way to be green and wrong.

---

## The cycle-numbering convention

Cycle numbers sort lexically only up to `0.9`. This plan does not reach `0.10`,
but if a cycle is ever inserted the table above is authoritative over lexical
order, and renumbering to keep single digits is refused for the reason the
compiler refused it: it invalidates every cross-reference the moment it
happens.
