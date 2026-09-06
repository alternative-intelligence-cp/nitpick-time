# Cycle 0.1 — The civil calendar

**`src/cal/`: the civil types, Hinnant's algorithms, and the exhaustive
sweep.** The most purely arithmetic cycle in the plan and the one with the
strongest gate.

> **`0.1.0.md` is written execution-grade at cycle 0.0's close** (0.0.6, step
> 6), so this cycle is openable by a session that was not present for the
> probes. That is the convention for every cycle: the opening subcycle file is
> written by the cycle before it.

## Why here

Because everything converts through it. `Timestamp ↔ civil`, every zone lookup,
every format and every parse ends up calling `date_to_days` or `days_to_date`.
Putting it first means every later cycle builds on something that has been
checked over its **whole domain** rather than sampled.

## Decisions in

TM-014 (the range and astronomical numbering), TM-015 (proleptic Gregorian
only), TM-016 (Hinnant's algorithms as given), TM-017 (`cal` declares
`ETimeValue` and nothing else), TM-026 (the sweep is the gate). All settled.
**Nothing in this cycle is blocked on a question.**

**Decisions OUT, taken at 0.1.0 because the work revealed them:** TM-147 (an
`error:` cannot carry a payload, so C-5's "`ETimeValue` with a `ValueFault`" is
amended to C-5b and the delivery mechanism is O-X8) and TM-148 (the struct
literal is an unchecked constructor the language will not let us remove, so
C-8's guarantee is about the values this library PRODUCES — C-8b, and
`check_civil_literal` covers the half that is enforceable). Both are
specification corrections measured at pin `aaffb87`, not compiler defects, and
**neither blocks 0.1.1**: `date_to_days` is branch-free arithmetic that is
total over every field value, so it is safe by construction rather than by
C-8's guarantee. That is worth knowing before writing it.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.1.0 | **The types** — `CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, and the validating constructors | **DONE 2026-09-06.** Every date `ntime` PRODUCES is a date that exists — and C-8b is why that sentence is no longer "a date that exists is a date that exists": the struct literal is an unchecked constructor the language will not let us remove (TM-148) |
| 0.1.1 | **The algorithms** — `date_to_days`, `days_to_date`, the leap rule, `days_in_month` | the published algorithms, cited, with their divisions by literals |
| 0.1.2 | **The sweep** — the exhaustive round trip and its three riders | the cycle's gate |
| 0.1.3 | **Derived fields** — weekday, day-of-year, ISO week date, ordinal date | computed, never stored |
| 0.1.4 | **The cross-oracle** — the Python corpus and the agreement test | agreement over years 1 … 9999 |
| 0.1.5 | **Close** | `done/0.1/`, `0.2.0.md` written |

## Checklist

### 0.1.0 — the types — **DONE 2026-09-06**
- [x] `CivilDate`, `CivilTime`, `CivilDateTime` with the field orders from `CALENDAR.md` §3 — **declaration order is comparison order** (C-6), and a test asserts it for each — `tests/unit/civil_order.npk`, per FIELD and with the DOMINANCE case for each, because a type whose fields were swapped still orders correctly on each field alone
- [x] `#[derive(Eq, Ord, Clone, Debug)]` on each, with probe 01's verdict cited in a comment — and **D-123 cited for declaration order, never D-051**, which is a real heading about `ostring` that `src/core/vec.npk` mis-cited for four subcycles (TM-143)
- [x] `Weekday` and `Month` as enums, Monday first (C-7), with `weekday_number()` 1…7 and the Sunday-first helper beside it — all seven values of both asserted, because the numbering is read off the enum's TAG rather than written as a seven-arm `pick`, so the test is what makes the tag mapping checked
- [x] **validating constructors only** (C-8): `civil_date(y, m, d)` returns `Result<CivilDate>` and refuses February 30th, month 13, day 0. **No unchecked constructor exists** — *in the module.* **AMENDED BY C-8b (TM-148): a CONSUMER can still write the struct literal**, measured at pin `aaffb87` — it compiles, links and runs at exit 0 with `month == 99`. `check_civil_literal` keeps `src/` inside the guarantee; nothing can keep a consumer inside it
- [x] `CivilTime` refuses hour 24 (C-9); the normalising acceptance belongs to the parser at 0.4, not here — and second 60 likewise
- [x] `ETimeValue` and `ValueFault` declared here and nowhere else — `check_error_budget` reports **1 of 3**, naming the two not yet declared
- [x] ~~`check_failsafe_arms` goes live: a program importing only `cal` owes exactly one arm~~ — **the prediction was WRONG BY EIGHT and the corrected item is the measurement.** `check_failsafe_arms` was already live at 0.0.3; what went live here is its first non-floor row. **A program importing only `cal` owes the arms `NITPICK-REACH-003` names, measured and recorded: NINE** — `cal.ETimeValue`, `Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak`, `DivByZero`, `DivOverflow`, `IntOverflow`, `OutOfBounds`. `9 = 4 (floor) + 1 (identity) + 4 (cal's own arithmetic, charged to the consumer)`. That is TM-107 exactly, `0.1.0.md` §4 predicted the falsification, and `SAFETY.md` S-4's totals column now carries the number with the command that produced it
- [x] **added, not planned:** `check_civil_literal`, commissioned with two planted violations and two controls — one of them the banned form in a COMMENT, since `src/lib.npk`'s own header spells it out in prose

### 0.1.1 — the algorithms
- [ ] `date_to_days` / `days_to_date` as Hinnant's `days_from_civil` /
      `civil_from_days`, cited in the module header with the source
- [ ] every division by a nonzero **literal** (C-11), so D-007's obligation is discharged by inspection — and a test that greps the module for a division by a non-literal
- [ ] intermediates in `int64` (C-12)
- [x] ~~`is_leap_year` and `days_in_month`, applied uniformly across negative years~~ — **DONE AT 0.1.0**, because `civil_date` cannot refuse February 30th without them and a constructor that validates three of its four conditions is not a validating constructor (`0.1.0.md` §3 took that decision at planning). `tests/unit/leap_rule.npk` covers the four century cases, their negative mirrors, and −1/−4/−100/−400 by name. **The negative-year correction turned out NOT to be needed in the leap rule** — every clause compares a remainder against ZERO, and zero has no sign — but it IS still owed by `days_from_civil`'s `era`, which uses a non-zero remainder
- [ ] the range constants **recomputed by a test** rather than trusted from `limits.npk` (0.0.4's note)

### 0.1.2 — the sweep — THE GATE
- [ ] every day number in `[−4 371 588, +2 932 896]` satisfies `date_to_days(days_to_date(n)) == n` — 7 304 485 cases
- [ ] every date in the range satisfies `days_to_date(date_to_days(d)) == d` — 7 304 485 cases
- [ ] **monotonicity**: `date_to_days` strictly increasing over dates in order
- [ ] **the weekday cycle**: advances by exactly one mod seven per day, across every century and 400-year boundary
- [ ] **month lengths**: match the leap rule for every (year, month) in range — 239 976 cases
- [ ] the sweep is a `sweep`-stage test, runs in full on a full invocation, and `--quick` skipping it is caught by the self-check's case 7
- [ ] the wall-clock cost recorded; if it is over ~30 s, say so and decide whether to keep it in the default run

### 0.1.3 — derived fields
- [ ] `weekday()` derived from the day number (C-13), **never stored**
- [ ] `day_of_year()` and the ordinal-date round trip
- [ ] `iso_week_year`, `iso_week_number` (1…53), `iso_weekday`, by the standard rule (C-14)
- [ ] the ISO boundary cases as explicit tests: 1 January falling on each of the seven weekdays, in leap and common years — fourteen cases, each hand-checked
- [ ] the ISO week round trip on the same exhaustive sweep as 0.1.2

### 0.1.4 — the cross-oracle
- [ ] `tools/gen_civil_oracle.py` emitting `(y, m, d, day_number, weekday, iso_week, day_of_year)` rows from Python's `datetime`, committed under `tests/fixtures/civil/`
- [ ] the agreement test over every row
- [ ] **the limitation stated in the fixture's header**: Python covers years 1 … 9999 only, so the negative half has the self-consistency of 0.1.2 and nothing else (C-18)

## Gate

**Every day in the supported range round-trips, in both directions, in full.**
7 304 485 cases each way, plus monotonicity, the weekday cycle and month
lengths on the same sweep. This is the strongest statement `ntime` makes and it
costs seconds.

## Watch for

- **The negative years are where the bugs are.** Probe 07 pinned that `/`
  truncates toward zero, and Hinnant's algorithm carries the correction for it —
  but any *new* arithmetic written in this cycle has to carry it too. A
  reviewer's question for every division added here: what does this do at
  year −1?
- **`weekday` computed, not stored** (C-13), and the same for every other
  derived field. A stored derived field is a second representation of a fact
  the date already carries, and the two can disagree.
- **The validating constructor is the whole contract — and READ C-8b BEFORE
  RELYING ON IT.** Everything `ntime` returns is a real date because
  `civil_date` is the only thing in `src/` that builds one, and
  `check_civil_literal` is what keeps that true. But a CONSUMER can write
  `CivilDate{ … }` directly: measured at pin `aaffb87`, month 99 and day 99
  compile, link and run at exit 0 (TM-148). So the sentence "everything
  downstream skips the question" is **not** available to 0.1.1: write
  `date_to_days` to be total over every field value — Hinnant's is, by
  construction — rather than to be correct only on valid input. A single
  unchecked constructor added for convenience would remove the library-side
  half of the guarantee as well.
- **`limit` and `end` are keywords**, and a range-bounds module wants both.
