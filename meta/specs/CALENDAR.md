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
| minimum day number (epoch 1970-01-01 = 0) | `−4 371 587` |
| maximum day number | `+2 932 896` |
| **total days in range** | **7 304 484** <!-- [[sweep: domain_every_day_number=7304484]] --> |
| minimum `Timestamp.secs` | `−377 705 116 800` |
| maximum `Timestamp.secs` | `+253 402 300 799` |

Those numbers are computed, not estimated, and cycle 0.1 pins them as named
constants with a test that recomputes them —
`tests/unit/range_constants.npk`, since cycle 0.1.1.

*(Amended at cycle 0.1.1, TM-161. The table read **−4 371 588**, **7 304 485**
and **−377 705 203 200** until then — each one day early. −4 371 588 is the
day number of **−10000-12-31**, the day before the range, which C-4 refuses:
the range holds 10 000 years below year 1, exactly 25 × 146 097 = 3 652 425
days, and year 1 begins at day −719 162, so −9999-01-01 is day −4 371 587.
The seconds and the total were derived from the wrong first day, so every
relation between them held and none could catch it. The recomputation did,
exiting 10 against the old constant before it moved.)*

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
directly; it needs a "no fault" variant, and that is the decision to take.
*(Amended at cycle 0.1.3, TM-173: this read "an eleventh 'no fault'
variant" — true of the ten `ValueFault` had until then. Cycle 0.1.3 appended
four, so the "no fault" variant would now be the fifteenth.)*

This is the language behaving as specified rather than a compiler defect, so
nothing here is raised upstream and nothing is worked around.

---

## 3. The types

```nitpick
pub struct:CivilDate = { sealed int32:year; sealed uint8:month; sealed uint8:day; };
pub struct:CivilTime = { sealed uint8:hour; sealed uint8:minute; sealed uint8:second; sealed uint32:nanos; };
pub struct:CivilDateTime = { CivilDate:date; CivilTime:time; };

pub enum:Weekday = { Monday; Tuesday; Wednesday; Thursday; Friday; Saturday; Sunday; };
pub enum:Month   = { January; February; March; April; May; June;
                     July; August; September; October; November; December; };
```

*(Amended at cycle 0.1.0c by C-8c, TM-157: the two validated types' fields
gained `sealed`. Until then the block read `{ int32:year; uint8:month;
uint8:day; }` and `{ uint8:hour; uint8:minute; uint8:second; uint32:nanos; }`
— the same fields, in the same order, and C-6 below is unchanged by it.)*

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
be read with it, and C-8c narrows that limit** — the last clause of this rule
used to read "which is what lets everything downstream skip the question", and
downstream cannot quite skip it.

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
  *(Amended by C-8c; `check_civil_literal` retired by TM-158's decision at
  cycle 0.1.0c, because `NITPICK-TYPE-079` now enforces its property for every
  module but `cal`. The sentence stays as the record of what held from 0.1.0
  to 0.1.0b.)*
- **Outside it, a function that would misbehave rather than merely mislead on
  a malformed `CivilDate` says so in its header**, and is written to be total
  where it can be. `date_to_days` (C-10) is branch-free arithmetic that is
  total over every field value, so it is safe by construction rather than by
  the guarantee — which is worth knowing before 0.1.1 rather than after.

`CivilDateTime` has no validating constructor and needs none: both its members
can only have come from one, so its literal checks nothing that was not already
checked.

**Rule C-8c (TM-157, cycle 0.1.0c) — THE FIELDS ARE SEALED, SO C-8 HOLDS OF THE
TYPE AGAIN, FOR EVERY MODULE BUT `cal`.** It narrows C-8b, whose text above
stays as the record of what was true at pin `aaffb87`.

At compiler `c3bdae2` a struct field may be `sealed` (the compiler's D-313):
read anywhere, written only by code in the module that declares the struct.
**Every field of `CivilDate` and `CivilTime` is sealed.** C-8b's premise — *"the
language has no private field"* — is false at this pin, and
`tests/probe/probe15_civil_literal_bypass.npk`, written at 0.1.0 to announce
exactly this day, is now refused. Measured at `c3bdae2`, each a consumer that
imports `cal`:

| What a consumer writes | Verdict | Pinned by |
|---|---|---|
| `CivilDate{ year: 32000i32, month: 99u8, day: 99u8 }` | **`NITPICK-TYPE-079`**, once per field named — three | `probe15` |
| `a.month = 13u8;` on a `CivilDate` from `civil_date` | **`NITPICK-TYPE-079`** | `probe16d` |
| `CivilTime{ hour: 24u8, … }` | **`NITPICK-TYPE-079`**, four | the cycle's record |
| `dt.date.month = 13u8;` through an unsealed `CivilDateTime` | **`NITPICK-TYPE-079`** — a write reaching a sealed field through a path is a write | the cycle's record |
| `CivilDate:v;` and then `v.month` | **`NITPICK-ASSIGN-001`** — no default value to read (D-010) | the cycle's record |
| a field READ — `d.month`, `t.hour`, every field of both types | compiles and runs | `probe16e`; `tests/unit/civil_construct.npk` reads every field |
| `d.cmp(e)` | compiles and runs | `tests/unit/civil_order.npk` |
| `d.clone()`, and a `CivilDateTime` literal from two constructed values | compile and run | the cycle's record |

**What remains outside the guarantee is `wild` storage reinterpreted by `=>!`**,
the language's opt-out for every checked property: eight bytes from `alloc`,
written through a `uint8` slice and read as a `wild CivilDate->`, yield month
99 at exit 0 (measured at `c3bdae2`). That is an author opting out, stated
rather than hidden, and it is why **C-8b's second bullet stands** — write
downstream functions total where they can be — because it costs nothing and
the opt-out exists. **C-8b's first bullet is retired with its check**:
`NITPICK-TYPE-079` enforces, for every module but `cal` — consumers and the rest
of `src/` alike — exactly the property `check_civil_literal` enforced over
`src/` (TM-158).

`CivilDateTime` is **not** sealed, for C-8b's closing reason: its members can
only have come from the constructors, and the seals below it hold through it.

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

**The source**, cited in `src/cal/cal.npk`'s header since cycle 0.1.1: Howard
Hinnant, *chrono-Compatible Low-Level Date Algorithms*,
`howardhinnant.github.io/date_algorithms.html` — the page dates itself
2021-09-01 and was read on 2026-09-25, the first row of
[`../research/CURRENCY.md`](../research/CURRENCY.md), with its digest in
[`../research/hinnant-date-algorithms.md`](../research/hinnant-date-algorithms.md).
The transcription was checked against the page line by line, not against the
digest. **Its one deviation is C-12's**: Hinnant's intermediates are
`unsigned`, and `ntime`'s are `int64`.

Since cycle 0.1.3 `days_from_civil` keeps his signature as well: it is a
private function of `src/cal/cal.npk` over the three integers, and
`date_to_days` is its one-line widening from a `CivilDate`'s sealed fields —
so the derived fields (C-13 … C-15) reach the day number of 1 January or
4 January of any year through the module's one copy of the formula (TM-170).

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

**Rule C-11 (TM-163) — every division in `src/cal/` is by a positive integer
literal.** Nonzero, so D-007's divide-by-zero trap is unreachable by
construction; and not −1, so its `MIN / −1` overflow is unreachable too. Both
obligations are discharged by inspection, which is exactly the kind of thing
`VERIFICATION.md` has to be able to claim. **The rule carries no list of
divisors**: `check_literal_divisors` reads every `/`, `%`, `/=` and `%=` in the
code of every `.npk` under `src/cal/` on every full run and fails on any other
divisor, so the list is the check's and cannot go stale.

*(Amended at cycle 0.1.1, TM-163. The rule read "every division in them is by a
nonzero literal (4, 5, 100, 400, 146097)" — `days_from_civil`'s four divisors
and one of `civil_from_days`' nine. The other eight, and the `%` of
`is_leap_year` and `weekday_number_sunday_first`, were in no list, so the list
was incomplete the day the second algorithm arrived. "Nonzero" became
"positive" because the check accepts only an unsigned literal, and a positive
divisor is what closes `MIN / −1` as well as the zero.)*

**Rule C-12 — the intermediate values are `int64`, and the reason is
measured.** `era * 146097` at year −9999 is −3 652 425 (`era` is −25), and
`yoe * 365` is at most 145 635 — nowhere near an `int32` limit, but the input
`year` is `int32` and the products are computed in `int64` so that NO field
value traps inside the algorithm: `date_to_days` is total over every `int32`
year and every pair of `uint8`s, with `|era| ≤ 5.4 × 10⁶` and
`|era × 146 097| ≤ 7.9 × 10¹¹` (TM-162), and `days_to_date` refuses a day
outside §2's range through its `Result` before its first addition.

*(Amended at cycle 0.1.1, TM-162. This rule read "`era * 146097` at year −9999
is about −4.4 × 10⁶" — that is the day number, not the product, which is
−3 652 425 — and ended "so that a caller who somehow supplies an out-of-range
year gets the range check's error rather than a trap inside the algorithm".
`date_to_days` has no range check to give: its argument is a `CivilDate`,
sealed since C-8c, and it is total instead. The range check is
`days_to_date`'s.)*

**Rule C-13 — weekday is derived, not stored.**
`weekday = (days + 3) mod 7` with a non-negative modulus correction, Monday =
0. Derived because a stored weekday is a second representation of a fact the
date already carries, and the two can disagree.

Since cycle 0.1.3 the modulus is taken in exactly one place,
`src/cal/cal.npk`'s private `weekday_index`, and `weekday`, `iso_weekday` and
C-14's week-1 Monday all call it. `weekday` returns a `Weekday` whose tag IS
the index — C-7's Monday-first order, stated once, by the enum — manufactured
with `=>!`, which the compiler does not check (its D-140). So the index is
range-checked on the same path, and one outside 0 … 6 stops the program
through `#unreachable()` instead of becoming a `Weekday` that is none of the
seven (`SAFETY.md` S-15c, TM-171). The correction leaves every index in range,
so the check never fires; what it does is turn the correction's absence from a
silent wrong answer into a controlled stop — measured, with and without it
(`meta/roadmap/0.1/0.1.3.md` §7, rows D1 and D2).

**Rule C-14 — ISO week dates are computed, not tabulated.** `iso_week_year`,
`iso_week_number` (1 … 53) and `iso_weekday` follow ISO 8601: week 1 is the
week containing the first Thursday of the year, weeks start on Monday, and the
week-year may differ from the calendar year at the boundaries. The three are
computed from the day number by the standard rule, and the boundary cases are
each a test: **for each of the fourteen shapes a year can have — its
1 January on each weekday, leap or common — that year's 1 January, its
31 December, and the 1 January after it.** `iso_week_to_date(iy, w, wd)` is
the round trip's other half. It refuses a week-year outside C-4's range, a
week below 1 or past the week-year's last — week 53 of a 52-week year is
refused, not read as week 1 of the next — and an ISO weekday outside 1 … 7,
each before any arithmetic on it; and it refuses the two days of 9999's last
week that fall after 9999-12-31.

The standard is ISO 8601-1:2019 with its Amendment 1:2022, whose clause
3.1.1.23 states the rule — *"the first calendar week of a calendar year is the
week including the first Thursday of that year"* — per
`meta/research/iso-8601-week-date.md`, as of 2026-09-25. `src/cal/cal.npk` computes week 1's Monday as the Monday on or
before 4 January, which is the same week — the first Thursday is one of
1 … 7 January, and the Monday-to-Sunday week around it holds the 4th exactly
then — and that form is derived, not quoted (TM-172). Since cycle 0.1.3 every
date in the range is checked against a walk of the rule read the calendar's
way, and handed back, by `tests/unit/sweep/every_iso_week_date.npk` — 7 304 484 dates <!-- [[sweep: domain_every_iso_week_date=7304484]] -->,
and the week after each of the 19 999 week-years' last is refused.

*(Amended at cycle 0.1.3, TM-175. The boundary sentence read: "the boundary
cases — 1 January falling on each of the seven weekdays, in leap and common
years — are each a test." That indexes the cases by the year that BEGINS, and
the week 1 January falls in is decided by the year that ENDS: measured over
every year from 2 to 9998, a common year beginning on a Saturday opens in
week 52 of the year before when that year was common (2011) and in week 53
when it was leap (2005), so fourteen cases chosen that way fix thirteen
answers and leave the fourteenth to whichever year was picked. Indexed by the
ending year's shape, nothing is left over. `tests/unit/derived_field_vectors.npk`
carries both: fourteen years, one of each shape, at both ends and at the next
1 January.)*

**Rule C-15 — ordinal dates** (`day_of_year`, 1 … 366) are computed the same
way and round-trip with `CivilDate`. `ordinal_to_date(y, doy)` is the round
trip's other half (TM-169): it refuses a year outside C-4's range and a day
below 1 or past the year's last, each before any arithmetic on it. Since cycle
0.1.3 every date in the range is checked against a count of its year's days,
and handed back, by `tests/unit/sweep/every_ordinal_date.npk` — 7 304 484 dates <!-- [[sweep: domain_every_ordinal_date=7304484]] -->, and the
day after each of the 19 999 years' last is refused.

---

## 5. The gate: exhaustive round trip

**Rule C-16 (TM-026).** The cycle-0.1 gate is:

> **Every day number in `[−4 371 587, +2 932 896]` satisfies
> `date_to_days(days_to_date(n)) == n`, and every date in the supported range
> satisfies `days_to_date(date_to_days(d)) == d`.**

*(Amended at cycle 0.1.1, TM-161: the interval's lower end read −4 371 588 and
the count below 7 304 485 — §2's first day, one day early. At the old bound
the first element of the sweep is −10000-12-31, which `days_to_date` cannot
return, so the gate would have failed on its first case.)*

That is 7 304 484 cases in each direction <!-- [[sweep: domain_every_day_number=7304484]] -->, run in full, not sampled. It is the
analogue of the sibling library's `GraphemeBreakTest.txt` gate, and it is
stronger: there is no external corpus to trust, because the property is
self-evidently the right one and the range is small enough to enumerate.
Since cycle 0.1.2 its two halves are `tests/unit/sweep/every_day_number.npk`
and `tests/unit/sweep/every_civil_date.npk`, run in full at -O0 and again under
`opt -O2` on every full invocation (`BUILD.md` B-9, TM-166).

**Rule C-17 (TM-167) — three more exhaustive checks ride the same sweep**,
because the loop is already running, and each is stated in the form a wrong
implementation fails:

1. **Monotonicity** — over the dates in order, each date's day number is the
   previous one's **plus one**, from −9999-01-01's `NTIME_DAY_MIN`.
2. **Weekday cycle** — each day's weekday equals a count begun at
   −9999-01-01's weekday, a **Monday**, and advanced by one per day, so it is
   in Monday … Sunday on every day of the range, every century and 400-year
   boundary included. *Asserted since cycle 0.1.3, on `tests/unit/sweep/every_civil_date.npk`'s
   walk (TM-165)*, where it rests on item 1's chain — the whole of what a
   weekday derived from the day number (C-13) needs from the calendar — and
   adds the derivation's own arithmetic. *(Until cycle 0.1.3 this sentence
   read "Asserted from cycle 0.1.3, where `weekday()` is written (TM-165); until
   then it rests on item 1's chain, …".)*
3. **Month lengths** — for every year in range and every month, the length
   `days_in_month` gives equals the distance from that month's first day to
   the next month's first day — for 9999-12, to `NTIME_DAY_MAX + 1`.

Since cycle 0.1.2 the first is asserted on `tests/unit/sweep/every_civil_date.npk`'s
walk and the third by `tests/unit/sweep/every_month_length.npk`; since cycle
0.1.3 the second is asserted on the first's walk.

*(Amended at cycle 0.1.2, TM-167. The three items read, verbatim:
"1. **Monotonicity** — `date_to_days` is strictly increasing over dates in
order." — "2. **Weekday cycle** — the weekday advances by exactly one, modulo
seven, per day, across the whole range including every century and 400-year
boundary." — "3. **Month lengths** — the day count per month matches C-3's
leap rule for every year in range." Each, as written, is passed by a mutant the
new form fails, measured (`meta/roadmap/0.1/0.1.2.md` §5 and §1.3): a leap rule
missing its 400-year day keeps every step strictly increasing — the civil walk
with a `>` chain exits 0 having visited 7 304 435 of the 7 304 484 days — and
breaks the plus-one chain; a weekday computed as `(n + 3) % 7` with the
truncating `%` and no correction advances by one, mod seven, on all 7 304 483
steps and differs from the count on the range's second day; and a month length
checked by building the month's LAST day with the length under test and
counting to it agrees with the century-rule, 400-year-rule and April-31
mutants, because `date_to_days` is total (C-12) and gives a February 29th that
should not exist the next day's number — while the distance between
month-firsts refuses all three.)*

**Rule C-18 (TM-179, cycle 0.1.4) — a fourth check is a cross-oracle over the
whole of Python's range**, and it is separate because it trusts something
external. `tools/gen_civil_oracle.py` reads Python's `datetime` for every date
it covers — 0001-01-01 to 9999-12-31, 3 652 059 dates <!-- [[sweep: domain_every_oracle_date=3652059]] --> — and commits one row
per year as `tests/fixtures/civil/civil_oracle.npk`: the year, the day number
of its 1 January, its length, and a digest of nine fields of every one of its
days — the year, month and day, the day number, the weekday, the ISO week
date's three fields and the day of the year (TM-180).
`tests/unit/sweep/every_oracle_date.npk` computes the same from this
library's answers and must equal every row (TM-182). Python's `datetime` only
covers years 1 … 9999, so the negative half of the range has C-16's
self-consistency and nothing else — which is stated rather than glossed, and
is why C-16 is the gate and C-18 is a supplement.

*(Amended at cycle 0.1.4, TM-179. The rule read: "a fourth check is a
*sampled* cross-oracle, and it is separate because it trusts something
external: a Python generator emits a few hundred thousand `(y, m, d, days,
weekday, iso_week)` rows using `datetime`, committed under
`tests/fixtures/civil/`, and the library must agree with every one."
Measured at planning: a few hundred thousand explicit rows is 33.7 MB of
generated source that `npkc` takes 44 s and 717 MB to compile once, and a
sample misses what falls between its rows — one taken every seventh day meets
every February 29th of a 400-multiple year or none of them, since 400 years
are exactly 20 871 weeks. A digest per year puts the whole of Python's range
in 1.0 MB and one second, so the agreement is checked over its whole domain,
as TM-026 asks wherever that is possible. `meta/roadmap/0.1/0.1.4.md` §2 and
§7 have the measurements.)*

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
