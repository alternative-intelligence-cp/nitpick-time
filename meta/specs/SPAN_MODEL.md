# Spans: `Duration` and `Period`

Two span types, and the rules for what each does to each other type. The
calendar-arithmetic rules in §3 are written with worked examples because every
library that leaves them implicit gets bug reports about them forever, and
because there is no universally correct answer — only a stated one.

---

## 1. `Duration` is the prelude's

**Rule N-1 (TM-004).** `ntime` uses the prelude's `Duration` and **declares no
span type of its own for exact time**:

```nitpick
pub struct:Duration = { int64:ns; };          // src/prelude/prelude.npk
pub func:duration_ns   = Duration(int64:n)  never fails;
pub func:duration_ms   = Duration(int64:ms) never fails;
pub func:duration_secs = Duration(int64:s)  never fails;
```

*Reasoning:* it is the ecosystem's one span type. The deadline substrate takes
it (D-176), every `Reader`/`Writer` method takes it, `sleep` takes it. A second
one would immediately become the type everybody converts to and from, and the
conversion would be the bug.

**Rule N-2 — `ntime` adds constructors, not a type.** `duration_mins`,
`duration_hours`, `duration_days` and `duration_weeks` are ours, all
`never fails`, all built on the prelude's, all with their multiplications in
`int64` where D-210's trap is the range check.

> `duration_days` is **exactly 86 400 × 10⁹ nanoseconds**, and that is a
> statement about `Duration`, not about calendars. A calendar day may be 23 or
> 25 hours long across a DST transition; `Period{ days: 1 }` is the thing that
> means "the same wall time tomorrow". §3 is the whole of that distinction.

**Rule N-3 — the range is ±292.277 years** and it is `Duration`'s, not ours.
`TIME_MODEL.md` §8 states where it bites and what happens: `timestamp_since`
returns `ETimeValue`/`Overflow` rather than saturating or trapping.

---

## 2. `Period` — the calendar span

```nitpick
pub struct:Period = {
    int32:years;
    int32:months;
    int32:days;
    int64:ns;        // the sub-day part, exact
};
```

**Rule N-4 (TM-012) — a `Period` is not convertible to a `Duration`** without a starting
point, and the library offers no function that pretends otherwise. "One month"
is 28, 29, 30 or 31 days. "One day" is 23, 24 or 25 hours in a zone with DST.

**Rule N-5 — a `Period` is not normalised across unit boundaries.**
`Period{ months: 13 }` is not silently rewritten to `Period{ years: 1,
months: 1 }`, because the two behave identically only by coincidence of the
current rules. `period_normalise()` exists and is explicit; nothing calls it
implicitly.

Within the sub-day part, `ns` **is** normalised: it is an exact nanosecond
count and there is nothing to disagree with.

**Rule N-6 — the fields may be individually negative and mixed.**
`Period{ months: 1, days: −1 }` is legal and means what it says: add a month,
then subtract a day, in that order (§3's rule N-8). A library that forbids
mixed signs forbids the natural way to say "the day before this date next
month".

**Rule N-7 — `Period` addition is defined only on calendar-bearing types**
(M-16): `CivilDate`, `CivilDateTime`, `ZonedDateTime`. Never on `Timestamp`,
never on `Instant`.

---

## 3. Calendar arithmetic — the rules, with worked examples

**Rule N-8 (TM-021) — the order is years, then months, then days, then
nanoseconds**,
and each step is clamped before the next begins. Order matters and this one is
fixed.

**Rule N-9 — the year and month steps clamp the day.** Adding months to a date
whose day does not exist in the target month yields the **last day of the
target month**.

| Start | Add | Result | Why |
|---|---|---|---|
| `2026-01-31` | `1 month` | `2026-02-28` | February has 28 days in 2026 |
| `2024-01-31` | `1 month` | `2024-02-29` | 2024 is a leap year |
| `2026-01-31` | `2 months` | `2026-03-31` | March has 31 |
| `2024-02-29` | `1 year` | `2025-02-28` | 2025 is not a leap year |
| `2026-03-31` | `−1 month` | `2026-02-28` | clamping applies in both directions |

**Rule N-10 (TM-021) — clamping makes month arithmetic non-associative, and that is a
property of calendars, not a defect.** It is stated here so nobody "fixes" it:

```
2026-01-31 + 1 month + 1 month  =  2026-02-28 + 1 month  =  2026-03-28
2026-01-31 + 2 months           =  2026-03-31
```

These differ, and both are right. A library that made them agree would have to
carry the original day-of-month through the arithmetic, which produces a
different surprise (`2026-01-31 + 1 month − 1 month ≠ 2026-01-31` is replaced
by an operation whose result depends on history).

**Rule N-11 — the day step is exact and never clamps.** Days are added to the
day number, so `2026-02-28 + 1 day` is `2026-03-01` with no special case.

**Rule N-12 — subtraction is addition of the negated period**, and negation
negates every field. It follows that N-9's clamping applies, and therefore that
subtraction is **not** the inverse of addition:

```
2026-01-31 + 1 month = 2026-02-28
2026-02-28 − 1 month = 2026-01-28      (not 2026-01-31)
```

Also stated so nobody fixes it. Every library that has tried has produced a
worse surprise somewhere else.

**Rule N-13 (TM-022) — on a `ZonedDateTime`, the year/month/day steps operate
on the WALL clock and the nanosecond step operates on the INSTANT.** This is the rule
that makes "same time tomorrow" work across a DST transition, and it is the one
most often got wrong.

| Start (`Europe/London`) | Add | Result | Elapsed |
|---|---|---|---|
| `2026-03-28T12:00+00:00` | `Period{days: 1}` | `2026-03-29T12:00+01:00` | **23 hours** |
| `2026-03-28T12:00+00:00` | `Duration` of 24 h | `2026-03-29T13:00+01:00` | 24 hours |
| `2026-10-24T12:00+01:00` | `Period{days: 1}` | `2026-10-25T12:00+00:00` | **25 hours** |

Both columns are correct answers to different questions, and the type the
caller wrote is which question they asked.

**Rule N-14 — a wall-clock step that lands in a gap or an ambiguity is
resolved by the mode the caller supplies**, from `TIME_MODEL.md` M-15's four.
The period-addition entry points take the mode as a parameter; there is no
default.

**Rule N-15 — `until` is the inverse question, and it is asked in a unit.**
`date_until(a, b, Unit.Months)` yields whole months and a remainder, defined so
that `a + result == b` exactly. The largest-unit-first decomposition
(`period_between`) is built on it and is documented as *not* round-tripping
through `period_normalise`, for N-10's reason.

---

## 4. Rounding and truncation

**Rule N-16.** `truncate_to(unit)` and `round_to(unit)` are defined for
`Timestamp`, `CivilDateTime` and `ZonedDateTime`, over the units nanosecond,
microsecond, millisecond, second, minute, hour and day.

**Rule N-17 — rounding is half-away-from-zero**, stated because it is a choice.
Half-to-even is better for repeated statistical aggregation and worse for the
thing people actually do with times, which is read them. The mode is a
parameter (`RoundMode.HalfUp`, `HalfEven`, `Floor`, `Ceil`, `Trunc`) and
`HalfUp` is what the plain `round_to` uses.

**Rule N-18 — truncating a `ZonedDateTime` to a day truncates the WALL day**,
which may not be 24 hours from the previous one. Same distinction as N-13, same
reason to say it.

**Rule N-19 — units above `day` are refused for rounding.** "Round to the
nearest month" has no defensible definition (are months equal? which month is
the midpoint?), so the answer is a refusal rather than an arbitrary rule.

---

## 5. Where the arithmetic can overflow, and what happens

**This section is the single most likely place for this library to be quietly
wrong**, so every site is enumerated and each carries a `prove` obligation
(`VERIFICATION.md` §4).

| Site | Risk | Answer |
|---|---|---|
| `duration_days(n)` | `n × 86 400 × 10⁹` overflows `int64` past ±106 751 days | D-210 traps; the constructor is `never fails` and the trap is the range check, as the prelude's own constructors are |
| `timestamp_add(t, d)` | `secs + d.ns / 10⁹` leaves the supported range | checked, `ETimeValue`/`Overflow` |
| `timestamp_since(a, b)` | difference exceeds `Duration`'s ±292 y | checked, `ETimeValue`/`Overflow` (M-18) |
| `timestamp_to_civil` | `secs × 10⁹` for the nanosecond field | never computed — the seconds and nanos are kept apart, which is why `Timestamp` is a pair and not an `int64` of nanoseconds |
| `period_add` year/month step | `year + years` leaves `int32` or the range | computed in `int64`, checked, narrowed with `=>!` |
| `period_add` day step | day number leaves the range | checked against C-4's bounds |
| `period_add` ns step | `ns` sum overflows `int64` | computed in `int128`, checked, narrowed |
| `date_to_days` | none — C-12 measured the intermediates | inspection |
| ISO week computation | none — bounded by ±366 | inspection |

**Rule N-20 — the `int128` sites are exactly three**, they are named above,
and a whole-tree check asserts that `int128` appears nowhere else in `src/`.
A wide type used casually is a wide type nobody reasons about; used at three
named sites it is three obligations.

---

## 6. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
