# The civil calendar

The proleptic Gregorian calendar, its algorithms, and its exact bounds. This is
the most purely arithmetic part of the library and the part that can be tested
**exhaustively** rather than by sampling — which is why its gate is stronger
than anything else in the plan.

---

## 1. The calendar

**Rule C-1 (TM-015).** `ntime` implements the **proleptic Gregorian** calendar — the
Gregorian rules extended backwards past their 1582 adoption — and nothing else.
No Julian calendar, no Julian/Gregorian cutover, no local adoption dates.

*Reasoning:* a cutover is a **locale** property (Britain switched in 1752,
Russia in 1918, Greece in 1923), so honouring it would mean the calendar itself
became zone-dependent, and every date arithmetic would take a zone. ISO 8601
specifies proleptic Gregorian for exactly this reason, and every modern library
follows it. A caller who needs Julian dates for historical work needs a
different library, and `COMPAT.md` §4 says so.

**Rule C-2 (TM-014) — astronomical year numbering: year 0 exists and is 1 BCE.** Year
−1 is 2 BCE, and so on. Arithmetic is therefore uniform with no gap to special-
case, which is what ISO 8601 uses.

The cost is stated: `year 0` is not a year anybody writes outside ISO 8601, and
RFC 3339 has no way to express a negative year at all. Formatting refuses those
ranges rather than inventing a spelling (`FORMAT_MODEL.md` §4).

**Rule C-3 — the leap rule.** A year is a leap year when it is divisible by 4
and not by 100, or when it is divisible by 400. Applied uniformly across the
whole supported range, including negative years, because C-1 says proleptic.

---

## 2. The supported range

**Rule C-4 (TM-014).** `year ∈ [−9999, +9999]`, and every constructor checks it.

| Quantity | Value |
|---|---|
| minimum date | `−9999-01-01` |
| maximum date | `+9999-12-31` |
| minimum day number (epoch 1970-01-01 = 0) | `−4 371 588` |
| maximum day number | `+2 932 896` |
| **total days in range** | **7 304 485** |
| minimum `Timestamp.secs` | `−377 705 203 200` |
| maximum `Timestamp.secs` | `+253 402 300 799` |

Those numbers are computed, not estimated, and cycle 0.1 pins them as named
constants with a test that recomputes them.

*Reasoning for ±9999 rather than something wider:*

- **It is testable exhaustively.** 7.3 million days is a few seconds of
  computation, so "every date in the supported range round-trips" is a *gate*
  rather than an aspiration (§5). A wider range would make the strongest test
  in this library impossible.
- **Four digits is what every text format carries.** RFC 3339 requires exactly
  four; ISO 8601's expanded form needs prior agreement between the parties.
- **The tzdb has no opinion outside a much narrower window** anyway
  (`ZONE_MODEL.md` §6).
- **It is far wider than any real use** and the trap is still there if
  something escapes the check.

**Rule C-5 — a range violation is `ETimeValue` with a `ValueFault`, checked
before the trap.** D-210's trap is the belt; the check is the answer.
**Read C-5b before reading "with a `ValueFault`" as an error payload.**

**Rule C-5b (TM-147, cycle 0.1.0) — AN `error:` IDENTITY CANNOT CARRY A
PAYLOAD, so the `ValueFault` is a value the library computes and not something
attached to the error.**

Measured at pin `aaffb87`, and the probe is committed so the fact stays checked
rather than remembered: `pub error:ETimeValue(ValueFault);` is refused
`NITPICK-PARSE-001` at exit 1 with no `.ll` written
(`tests/probe/probe14_error_payload_refused.npk`). The compiler stops at the
`(` — an `ErrorDecl` is a NAME plus an optional explicit CODE, and the
explicit-code form is the prelude's alone. The other half of the same fact is
that a `Result<T>` is `{ T value, tbb32 err }`, so the error half of every
return in this language is a **code**: there is nowhere for a payload to live
even if the declaration admitted one.

C-5's sentence was written the way a reader coming from an exception language
or from Rust's `enum Error` would write it, and **it describes something the
language cannot express**. What survives is the part that matters: a range
violation is `ETimeValue`, and the caller's finer distinction is a `ValueFault`
— a payload-free enum with one variant per refusal row, declared in
`src/cal/cal.npk`.

**HOW a refusing constructor hands the `ValueFault` back is deliberately NOT
settled here.** It is `../OPEN_QUESTIONS.md` O-X8. Nothing in cycle 0.1 needs
it — `civil_date` and `civil_time` refuse correctly and completely without it —
and every candidate mechanism (a companion classifier function, an out
parameter, a richer success type) adds a public name, which by TM-013 is a
thing a MAJOR version is needed to take away. **A name added to settle a
question nobody has asked yet is a commitment taken by default.** The
recommendation, so a later session inherits an input rather than a
rediscovery, is a `never fails` companion classifier returning the fault
directly; it needs an eleventh "no fault" variant, and that is the decision to
take.

This is the language behaving as specified rather than a compiler defect, so
nothing here is raised upstream and nothing is worked around.

---

## 3. The types

```nitpick
pub struct:CivilDate = { int32:year; uint8:month; uint8:day; };
pub struct:CivilTime = { uint8:hour; uint8:minute; uint8:second; uint32:nanos; };
pub struct:CivilDateTime = { CivilDate:date; CivilTime:time; };

pub enum:Weekday = { Monday; Tuesday; Wednesday; Thursday; Friday; Saturday; Sunday; };
pub enum:Month   = { January; February; March; April; May; June;
                     July; August; September; October; November; December; };
```

**Rule C-6 — field order is declaration order is comparison order** (M-6). Year
before month before day; hour before minute before second before nanos. A
derived `Ord` is then exactly the ordering wanted, and reordering the fields
would silently change it.

**Rule C-7 — `Weekday` starts at Monday**, matching ISO 8601, and
`weekday_number()` returns 1 … 7 with Monday = 1. A `Sunday = 0` convention is
available as `weekday_number_sunday_first()` because C libraries use it and a
caller porting code will look for it, but the enum's own order is ISO's.

**Rule C-8 — the components are validated, always.** `civil_date(y, m, d)`
returns `Result<CivilDate>` and refuses February 30th, month 13, day 0. There
is no unchecked constructor **in the module**: a `CivilDate` this library
produces is a date that exists. **C-8b is the limit of that sentence and must
be read with it** — the last clause of this rule used to read "which is what
lets everything downstream skip the question", and downstream cannot quite skip
it.

**Rule C-8b (TM-148, cycle 0.1.0) — THE GUARANTEE IS ABOUT THE VALUES THIS
LIBRARY PRODUCES, NOT ABOUT THE TYPE, BECAUSE THE LANGUAGE HAS NO PRIVATE
FIELD.**

Measured at pin `aaffb87`. A consumer that imports `cal` can write

```nitpick
CivilDate:fake = CivilDate{ year: 32000i32, month: 99u8, day: 99u8 };
```

and it **compiles (`npkc` exit 0, `.ll` written), links, and runs at exit 0**
with `fake.month == 99`. The struct literal is an unchecked constructor that
every consumer has and that this library did not write and cannot remove:
visibility in this language is per-declaration (`pub`) and there is no
per-field form, and `opaque struct:Name = { … };` is refused
`NITPICK-PARSE-001` — the bodyless `opaque struct:Name;` is the extern-driver
declaration and nothing else.

**Why this is a rule and not a footnote.** C-8's original last clause is cited
as the reason every later cycle may skip the validity question, and four live
sites carried that reading (this rule, `meta/roadmap/0.1/README.md`,
`meta/roadmap/0.1/0.1.0.md`, and `src/cal/cal.npk`'s own header) over 177
tracked files. It is the same shape this repository keeps meeting and named in
`SAFETY.md` S-18e: **a rule whose NAME describes a property while its MECHANISM
covers something narrower.** Stated correctly it is still a strong rule —
nothing this library returns is ever an unreal date — and stated incorrectly it
would license `date_to_days` at cycle 0.1.1 to be written as though its input
could not be February 30th.

**What follows, and both halves are obligations on later cycles:**

- **Inside `src/`, the constructor is the only builder**, and
  `check_civil_literal` fails the run on a `CivilDate{` or `CivilTime{` literal
  outside `src/cal/cal.npk`. That is the half that is enforceable, and it is
  the half that matters most: both use-after-frees cycle 0.0 shipped were this
  library defeating its own stated contract under a green suite (S-18d, S-18e).
- **Outside it, a function that would misbehave rather than merely mislead on
  a malformed `CivilDate` says so in its header**, and is written to be total
  where it can be. `date_to_days` (C-10) is branch-free arithmetic that is
  total over every field value, so it is safe by construction rather than by
  the guarantee — which is worth knowing before 0.1.1 rather than after.

`CivilDateTime` has no validating constructor and needs none: both its members
can only have come from one, so its literal checks nothing that was not already
checked.

**Rule C-9 (TM-029) — `CivilTime` admits `hour ∈ [0,23]`, `minute ∈ [0,59]`,
`second ∈ [0,59]`, `nanos ∈ [0, 999 999 999]`.** Hour 24 is refused —
ISO 8601 permits `24:00:00` as an end-of-day marker, and accepting it would
mean two spellings of one instant, which the ecosystem's blueprint rule refuses.
Parsing accepts it and normalises to `00:00:00` of the next day, with the fact
recorded on the `Parsed` record exactly as `:60` is (M-13).

---

## 4. The algorithms

**Rule C-10 (TM-016) — `date_to_days` and `days_to_date` are Howard Hinnant's
`days_from_civil` / `civil_from_days`.** They are branch-free, exact over a
range far wider than C-4's, defined for negative years, and have a published
proof. `ntime` uses them as given, cites the source in the module header, and
does not reinvent them.

The shape, for a reader who has not seen them:

```
days_from_civil(y, m, d):
    y -= (m <= 2)
    era = (y >= 0 ? y : y - 399) / 400
    yoe = y - era * 400                       // [0, 399]
    doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1   // [0, 365]
    doe = yoe * 365 + yoe/4 - yoe/100 + doy   // [0, 146096]
    return era * 146097 + doe - 719468
```

**Rule C-11 — every division in them is by a nonzero literal** (4, 5, 100, 400,
146097), so D-007's divide-by-zero trap is unreachable by construction and the
obligation is discharged by inspection. Stated because it is exactly the kind
of thing `VERIFICATION.md` has to be able to claim.

**Rule C-12 — the intermediate values are `int64`, and the reason is
measured.** `era * 146097` at year −9999 is about −4.4 × 10⁶, and `yoe * 365`
is at most 145 635 — nowhere near an `int32` limit, but the input `year` is
`int32` and the products are computed in `int64` so that a caller who somehow
supplies an out-of-range year gets the range check's error rather than a trap
inside the algorithm.

**Rule C-13 — weekday is derived, not stored.**
`weekday = (days + 3) mod 7` with a non-negative modulus correction, Monday =
0. Derived because a stored weekday is a second representation of a fact the
date already carries, and the two can disagree.

**Rule C-14 — ISO week dates are computed, not tabulated.** `iso_week_year`,
`iso_week_number` (1 … 53) and `iso_weekday` follow ISO 8601: week 1 is the
week containing the first Thursday of the year, weeks start on Monday, and the
week-year may differ from the calendar year at the boundaries. The three are
computed from the day number by the standard rule and the boundary cases —
1 January falling on each of the seven weekdays, in leap and common years — are
each a test.

**Rule C-15 — ordinal dates** (`day_of_year`, 1 … 366) are computed the same
way and round-trip with `CivilDate`.

---

## 5. The gate: exhaustive round trip

**Rule C-16 (TM-026).** The cycle-0.1 gate is:

> **Every day number in `[−4 371 588, +2 932 896]` satisfies
> `date_to_days(days_to_date(n)) == n`, and every date in the supported range
> satisfies `days_to_date(date_to_days(d)) == d`.**

That is 7 304 485 cases in each direction, run in full, not sampled. It is the
analogue of the sibling library's `GraphemeBreakTest.txt` gate, and it is
stronger: there is no external corpus to trust, because the property is
self-evidently the right one and the range is small enough to enumerate.

**Rule C-17 — three more exhaustive checks ride the same sweep**, because the
loop is already running:

1. **Monotonicity** — `date_to_days` is strictly increasing over dates in
   order.
2. **Weekday cycle** — the weekday advances by exactly one, modulo seven, per
   day, across the whole range including every century and 400-year boundary.
3. **Month lengths** — the day count per month matches C-3's leap rule for
   every year in range.

**Rule C-18 — a fourth check is a *sampled* cross-oracle**, and it is separate
because it trusts something external: a Python generator emits a few hundred
thousand `(y, m, d, days, weekday, iso_week)` rows using `datetime`, committed
under `tests/fixtures/civil/`, and the library must agree with every one.
Python's `datetime` only covers years 1 … 9999, so the negative half of the
range has C-16's self-consistency and nothing else — which is stated rather
than glossed, and is why C-16 is the gate and C-18 is a supplement.

---

## 6. What is deliberately absent

- **Non-Gregorian calendars** — Hebrew, Islamic, Japanese eras, Chinese.
  Each is a substantial library, each needs its own data, and each has its own
  edge cases. Recorded as absent, not forgotten (`COMPAT.md` §4).
- **The Julian/Gregorian cutover** — C-1.
- **Business-day and holiday arithmetic.** Holidays are per-jurisdiction data
  with a shorter shelf life than the tzdb and no canonical source. A caller
  supplies its own predicate; the library offers `date_add_days` and
  `weekday()` and that is enough to build one.
- **Week numbering other than ISO** (US weeks starting Sunday, the "week 1
  contains 1 January" rule). Two spellings of one concept, and ISO is the one
  with a standard.

---

## 7. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
