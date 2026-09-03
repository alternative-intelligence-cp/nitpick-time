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

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.1.0 | **The types** — `CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, and the validating constructors | a date that exists is a date that exists |
| 0.1.1 | **The algorithms** — `date_to_days`, `days_to_date`, the leap rule, `days_in_month` | the published algorithms, cited, with their divisions by literals |
| 0.1.2 | **The sweep** — the exhaustive round trip and its three riders | the cycle's gate |
| 0.1.3 | **Derived fields** — weekday, day-of-year, ISO week date, ordinal date | computed, never stored |
| 0.1.4 | **The cross-oracle** — the Python corpus and the agreement test | agreement over years 1 … 9999 |
| 0.1.5 | **Close** | `done/0.1/`, `0.2.0.md` written |

## Checklist

### 0.1.0 — the types
- [ ] `CivilDate`, `CivilTime`, `CivilDateTime` with the field orders from `CALENDAR.md` §3 — **declaration order is comparison order** (C-6), and a test asserts it for each
- [ ] `#[derive(Eq, Ord, Clone, Debug)]` on each, with probe 01's verdict cited in a comment
- [ ] `Weekday` and `Month` as enums, Monday first (C-7), with `weekday_number()` 1…7 and the Sunday-first helper beside it
- [ ] **validating constructors only** (C-8): `civil_date(y, m, d)` returns `Result<CivilDate>` and refuses February 30th, month 13, day 0. **No unchecked constructor exists**
- [ ] `CivilTime` refuses hour 24 (C-9); the normalising acceptance belongs to the parser at 0.4, not here
- [ ] `ETimeValue` and `ValueFault` declared here and nowhere else
- [ ] `check_failsafe_arms` goes live: a program importing only `cal` owes exactly one arm

### 0.1.1 — the algorithms
- [ ] `date_to_days` / `days_to_date` as Hinnant's `days_from_civil` /
      `civil_from_days`, cited in the module header with the source
- [ ] every division by a nonzero **literal** (C-11), so D-007's obligation is discharged by inspection — and a test that greps the module for a division by a non-literal
- [ ] intermediates in `int64` (C-12)
- [ ] `is_leap_year` and `days_in_month`, applied uniformly across negative years
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
- **The validating constructor is the whole contract.** Everything downstream
  skips the question of whether a date is real because `CivilDate` cannot hold
  an unreal one. A single unchecked constructor added for convenience removes
  that guarantee everywhere at once.
- **`limit` and `end` are keywords**, and a range-bounds module wants both.
