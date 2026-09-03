# Cycle 0.2 — Instants and timestamps

**`src/span/`: `Instant`, `Timestamp`, and the `Duration` interop.** The types
that make the three scales three types.

## Decisions in

TM-004 (the prelude's `Duration` is the one exact span type), TM-010 (three
scales, no monotonic↔absolute conversion), TM-011 (`Timestamp`'s layout and
field order). All settled.

**Open questions to settle:** O-X3 — whether `Instant` exposes its clock kind
publicly. Recommendation on file: yes, read-only.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.2.0 | **`Instant`** — the type, the clock tag, `instant_since`, and the refusals | a timeout cannot be written against a wall clock |
| 0.2.1 | **`Timestamp`** — the type, the normalisation invariant, the range check | one representation per instant |
| 0.2.2 | **Conversion** — `timestamp_to_utc`, `civil_to_utc`, and the round trip | the second gate |
| 0.2.3 | **`Duration` interop** — the added constructors, `timestamp_add`, `timestamp_since` and its ±292-year refusal | the mismatch handled honestly |
| 0.2.4 | **Close** | `done/0.2/`, `0.3.0.md` written |

## Checklist

### 0.2.0 — `Instant`
- [ ] `Instant { int64:ns; uint8:clock }` with the clock tag from H-6
- [ ] `instant_since`, `instant_add`, `instant_cmp`
- [ ] **`instant_since` refuses a pair from different clocks** with `ETimeValue` (TM-010.1), and a test proves it
- [ ] **there is no `instant_to_timestamp` and no `timestamp_to_instant`** — a rejection test asserts that a program attempting the conversion does not compile, so the refusal is checked rather than merely absent
- [ ] O-X3 decided: `instant_clock(i)` read-only accessor, or not
- [ ] the compiler's `npk_mono_now` comment quoted in the module header, because it is the argument

### 0.2.1 — `Timestamp`
- [ ] `Timestamp { int64:secs; uint32:nanos }`, field order asserted against probe 01's verdict
- [ ] **the normalisation invariant** `nanos < 1_000_000_000` established by every constructor and re-established by every operation (M-7)
- [ ] a property test that no sequence of operations produces a denormalised value — this is `VERIFICATION.md` P-4's obligation, standing in
- [ ] the range check against `NTIME_SECS_MIN`/`MAX`, returning `ETimeValue` before D-210's trap
- [ ] a negative-`secs` timestamp with positive `nanos` compares correctly against its neighbours — the representation's one subtlety, and the test that catches getting it backwards

### 0.2.2 — conversion — THE GATE
- [ ] `timestamp_to_utc` and `civil_to_utc`, over `cal`'s algorithms
- [ ] the round trip over **every day boundary** in the range (7 304 485 cases)
- [ ] the round trip over **every second of 512 randomly chosen days**, with the seed committed so the run is reproducible (~44 M cases)
- [ ] a `sweep`-stage test, with the wall-clock cost recorded

### 0.2.3 — `Duration` interop
- [ ] `duration_mins`, `duration_hours`, `duration_days`, `duration_weeks`, all `never fails`, all over the prelude's constructors
- [ ] `duration_days` documented as **exactly 86 400 × 10⁹ ns** and explicitly *not* a calendar day (N-2's note)
- [ ] `timestamp_add(t, d)` with its range check
- [ ] **`timestamp_since` returns `ETimeValue`/`Overflow` past ±292 years** (M-18) — and the test computes the exact boundary rather than approximating it
- [ ] `timestamp_until(a, b, unit)` in whole days, months or years, as the calendar-scale answer (M-19)
- [ ] `check_int128_sites` goes live: `int128` at exactly the sites `SPAN_MODEL.md` §5 names

## Gate

The `Timestamp` ↔ civil round trip over every day boundary and 44 million
individual seconds, plus a property test that the normalisation invariant
survives every operation.

## Watch for

- **`timestamp_since`'s boundary is exact, not approximate.** ±292.277 years is
  9 223 372 036 854 775 807 nanoseconds; the test asserts at that value and at
  one more. An "about 292 years" check is a check that is wrong by a day.
- **The negative-seconds representation** is where a reader's intuition fails:
  `−1 secs, 500 000 000 nanos` is half a second *before* the epoch, not one and
  a half. There is one representation and the constructors enforce it.
- **The refusals need rejection tests.** M-3's "there is no conversion" is only
  true if a program attempting it fails to compile, and only checked if a test
  says so.
