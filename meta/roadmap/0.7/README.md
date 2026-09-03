# Cycle 0.7 — Calendar arithmetic

> **Where the consumer lives (TM-103):** `date` **and** `crontab`/`at`, in [`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix) — **not** in this repository's
> `examples/`. A consumer is a real program with its own lifetime, and
> `examples/` would make one that outgrows this library move, and one that
> consumes several pick a parent. The import is by relative path until the
> compiler's dependency resolution lands, and the repository's GitHub
> description and topics are set in the same pass that creates it.

**`Period` addition, the clamping rules, `until`, rounding — and the dogfood
consumers.** The cycle where the library meets somebody using it.

## Decisions in

TM-012 (`Period` cannot be added to an instant), TM-021 (clamping, and neither
associative nor invertible), TM-022 (wall versus instant on a zoned value). All
settled.

**Open questions to settle:** Q-4 — the dogfood consumers. Recommendation on
file: a `date`-equivalent CLI **and** a small scheduler, because the CLI
exercises formatting breadth and the scheduler exercises DST edges, which is
where a date library is actually wrong.

## Subcycles

| # | Topic | Ends with |
|---|---|---|
| 0.7.0 | **`Period`** — the type, negation, `period_normalise`, the ISO 8601 duration format | a calendar span that is not a duration |
| 0.7.1 | **Addition** — the four steps, the clamping, the worked examples as tests | every example in `SPAN_MODEL.md` §3 |
| 0.7.2 | **Zoned addition** — wall for calendar steps, instant for nanoseconds | the 23- and 25-hour days |
| 0.7.3 | **`until` and rounding** — the inverse question, and truncation | `a + (b until a) == b` |
| 0.7.4 | **The consumers** — the CLI and the scheduler, written as consumers | a triaged findings list |
| 0.7.5 | **Close** | `done/0.7/`, `0.8.0.md` written |

## Checklist

### 0.7.0 — `Period`
- [ ] `Period { years, months, days, ns }` with mixed signs legal (N-6)
- [ ] **not normalised across unit boundaries** (N-5); `period_normalise` exists and nothing calls it implicitly
- [ ] the `ns` part normalised, because it is exact and has nothing to disagree with
- [ ] `period_to_iso` / `period_parse_iso` for `P1Y2M3DT4H5M6S`
- [ ] **`Period + Timestamp` and `Period + Instant` do not exist** (TM-012) — rejection tests assert the programs do not compile

### 0.7.1 — addition
- [ ] the order: years, months, days, nanoseconds, each clamped before the next (N-8)
- [ ] the year and month steps clamp the day to the last of the target month (N-9); the day step is exact and never clamps (N-11)
- [ ] **every row of `SPAN_MODEL.md` §3's worked-example tables is a test**, by name
- [ ] N-10's non-associativity and N-12's non-invertibility as **explicit tests that assert the surprising answer** — so that a later "fix" is a red run
- [ ] the arithmetic's range checks return `ETimeValue`/`Overflow` before D-210's trap (S-12)

### 0.7.2 — zoned addition
- [ ] calendar steps move the **wall clock**; the nanosecond step moves the **instant** (N-13, TM-022)
- [ ] the three rows of N-13's table as named tests, over a real zone and real transition dates
- [ ] a wall step landing in a gap or an ambiguity takes the resolution mode as a **parameter** (N-14); there is no default
- [ ] the `ZonedDateTime` invariant (M-14) re-checked after every addition

### 0.7.3 — `until` and rounding
- [ ] `date_until(a, b, unit)` yielding whole units and a remainder, defined so `a + result == b` **exactly** (N-15) — and a property test over a generated pair corpus asserting it
- [ ] `period_between` as the largest-unit-first decomposition, documented as **not** round-tripping through `period_normalise` (N-15)
- [ ] `truncate_to` and `round_to` over nanosecond … day (N-16)
- [ ] `RoundMode` with `HalfUp` as the plain `round_to`'s (N-17), and each mode tested at a tie
- [ ] truncating a `ZonedDateTime` to a day truncates the **wall** day (N-18)
- [ ] **units above `day` refused for rounding** (N-19), with a rejection test

### 0.7.4 — the consumers
- [ ] Q-4 decided and recorded
- [ ] a `date`-equivalent CLI: parse and format in every supported format, convert between zones, arithmetic on the command line
- [ ] a small scheduler: "the next N occurrences of this rule in this zone", which is the program that meets every DST edge in anger
- [ ] **written without changing the library**, so every friction is recorded rather than smoothed over as it appears
- [ ] every awkwardness written down as it is met, numbered, with the line that caused it
- [ ] each finding triaged: **defect** (the library is wrong), **gap** (a consumer reasonably needs something absent), or **cost** (the library is right and this is what the design costs)
- [ ] every `cost` written into the documentation, because an accepted cost nobody warned about is a defect in the documentation
- [ ] the defects fixed with regression tests; the gaps either closed here or recorded as post-1.0

## Gate

Every worked example in `SPAN_MODEL.md` §3 is a passing test, `a + (b until a)
== b` holds over a generated corpus, and the two consumers run — with a triaged
findings list.

## Watch for

- **The temptation to make the arithmetic associative.** N-10 and N-12 record
  that it is not, and that every alternative trades one surprise for a worse
  one. The tests assert the surprising answers deliberately.
- **The scheduler is the honest test.** A CLI exercises breadth; a scheduler
  exercises the case where "the same time tomorrow" is 23 hours away, which is
  the one that produces bug reports.
- **Write the consumers as a consumer.** The value of 0.7.4 is the *record* of
  what was awkward, and a friction smoothed over in the moment is a friction
  the next user meets too.
