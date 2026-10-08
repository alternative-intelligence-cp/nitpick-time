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

*(Cycle 0.2.3, TM-233: written in `src/span/span.npk` as stated — each `raw
duration_secs` of its argument times the unit's seconds, `NTIME_SECS_PER_DAY`
by name — and held at every argument the hours', the days' and the weeks'
ranges hold, and every 262nd minute, by `tests/unit/duration_ctors.npk`; the
trap one past a day's two ends by two programs of their own.)*

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

| Site | Risk | Answer | `int128` |
|---|---|---|---|
| `duration_days(n)` | `n × 86 400 × 10⁹` overflows `int64` past ±106 751 days | D-210 traps; the constructor is `never fails` and the trap is the range check, as the prelude's own constructors are | no |
| `duration_mins(n)` | `n × 60 × 10⁹` overflows `int64` past ±153 722 867 minutes | as `duration_days`' | no |
| `duration_hours(n)` | `n × 3 600 × 10⁹` overflows `int64` past ±2 562 047 hours | as `duration_days`' | no |
| `duration_weeks(n)` | `n × 7 × 86 400 × 10⁹` overflows `int64` past ±15 250 weeks | as `duration_days`' | no |
| `instant_since(later, earlier)` | `later.ns − earlier.ns` overflows `int64` for two readings `instant_of` builds | computed in `int128` (M-20), checked against `Duration`'s range and narrowed once; past it, `ETimeValue`/`Overflow` | **yes** |
| `instant_add(t, d)` | `t.ns + d.ns` overflows `int64` 292 years from the clock's origin | D-210 traps; `never fails`, and the trap is the range check — a deadline's arithmetic (`TIME_MODEL.md` M-4, §9) | no |
| `timestamp_add(t, d)` | `secs + d.ns / 10⁹` leaves the supported range | checked, `ETimeValue`/`Overflow` | no |
| `timestamp_since(a, b)` | difference exceeds `Duration`'s ±292 y | computed in `int128` (M-20), checked against `Duration`'s range and narrowed once; past it, `ETimeValue`/`Overflow` (M-18) | **yes** |
| `timestamp_to_utc` | `secs × 10⁹` for the nanosecond field | never computed — the seconds and nanos are kept apart, which is why `Timestamp` is a pair and not an `int64` of nanoseconds | no |
| `civil_to_utc(c)` | `days × 86 400 + sod` | none — a day number from any `int32` year is at most 7.84 × 10¹¹ in magnitude (C-12), times 86 400 6.8 × 10¹⁶, and the second of the day at most 933 555 from three `uint8`s; `timestamp_of` checks the sum | no |
| `period_add` year/month step | `year + years` leaves `int32` or the range | computed in `int64`, checked, narrowed with `=>!` | no |
| `period_add` day step | day number leaves the range | checked against C-4's bounds | no |
| `period_add` ns step | `ns` sum overflows `int64` | computed in `int128`, checked, narrowed | **yes** |
| `date_to_days` | none — C-12 measured the intermediates | inspection | no |
| ISO week computation | none — bounded by ±366 | inspection | no |
| `bytes_put_int`'s loop measure | `0 − x` overflows `int64` at its minimum, the one input the function exists to get right | the measure is computed in `int128` and compared, never narrowed (TM-151) | **yes** |

*(Amended at cycle 0.2.3a, TM-229 — `../OPEN_QUESTIONS.md` O-X6, answered.
The `int128` column is new, and `check_int128_sites` reads it (TM-230). So is
the last row: a site in `src/core/bytes.npk` since cycle 0.1.0b that no row
named, found when cycle 0.2.3 was planned. `timestamp_since`'s row read
"checked, `ETimeValue`/`Overflow` (M-18)" — M-20 already put its arithmetic in
`int128`. And the fourth row named the conversion `timestamp_to_civil`, which
is `timestamp_to_utc` since cycle 0.2.2, TM-222.)* *(Cycle 0.2.3, TM-234:
`timestamp_add`'s check is `timestamp_of`'s, relayed, so the detail its
refusal would carry, when O-X8 delivers one, is `YearRange` — the range's own
name for a `secs` outside it; `Overflow` is `timestamp_since`'s, where
`Duration` cannot hold the answer.)*

*(Cycle 0.2.4b, TM-241 and TM-242 — the cycle audit's C1, C6 and C7.
`timestamp_add` checks its OPERAND first, `t.secs` against the range, so the
add, the borrow and the carry cannot trap whatever `t` holds; a forged `secs`
near `int64`'s ends trapped until then. And "every site is enumerated" was not
true: six rows are new — the three other `Duration` constructors, `instant_since`,
`instant_add` and `civil_to_utc` — and `instant_since`'s is marked, since it
computes in `int128` now, where its `int64` subtraction trapped on a pair
`instant_of` builds.)*

**Rule N-20 — the `int128` sites are the rows the table above marks in its
`int128` column, and no other.** A whole-tree check, `check_int128_sites`,
asserts that `int128` appears in `src/` only inside a marked row's function,
and that every marked function `src/` declares spells one. A wide type used
casually is a wide type nobody reasons about; used at named sites, each is an
obligation the table states beside it.

*(Amended at cycle 0.2.3a, TM-229 — O-X6's recommendation, taken. The rule
read "the `int128` sites are exactly three, they are named above, and a
whole-tree check asserts that `int128` appears nowhere else in `src/`", and
"used at three named sites it is three obligations", against a table that
marked one. Three rows are marked now: the count came out three, and it is
dropped anyway, because a number in a rule goes stale in silence.)*

*(Cycle 0.2.4a, TM-240 — the cycle audit's D1: `int128` in this rule is every
integer wider than `int64` — `int128` … `int4096`, `uint128` … `uint4096`,
`tbb128` and `tbb256` — because its reason is. An `int256` intermediate
narrowed by a bare `=>!` compiled, ran and passed every tree check, measured,
until `check_int128_sites` read all fourteen. The column keeps its name:
`int128` is the one width this library computes in.)*

*(Cycle 0.3.0, TM-246: and a numeric literal whose width suffix is one of those
fourteen — `3i256`, `7u128` — is a site as the type's name is. A computation of
literals alone widens with no type named, and `(3i256 * 5i256) =>! int64`
narrowed a constant to its low 64 bits in silence and passed the check until
then. `bytes_put_int`'s `0i128` is `src/`'s one such literal, in a function
the table marks.)*

*(Cycle 0.3.0's verification, 2026-10-08 — `../OPEN_QUESTIONS.md` O-X11: the
check reads SPELLINGS, so this rule is wider than it. A wide value no width is
spelled for — a call's result, `(raw wide()) * (raw wide())` in a function the
table does not mark, `wide` a marked `int256()` — is an intermediate this rule
forbids, and the check passes it, as it has since it went live. No function in
`src/` returns or takes a wide type, or calls one that returns one, so nothing
does it today.)*

**Rule N-20b (TM-105) — the range check at each of those sites is mandatory
library code, because the language provides no checked narrowing.** Measured at
cycle 0.0.0: `=>!` at a value that does not fit **truncates silently** (no trap,
no diagnostic, exit 0), and `=>` at a narrowing is **refused at compile time**,
`NITPICK-TYPE-009`. Every site in §5's table that narrows — the `int128` ones
above all, but the `int64`→`int32` year step equally — carries an explicit
runtime range test against the destination's bounds **before** the `=>!`, on the
same path, failing `ETimeValue`/`Overflow`. Nothing after the cast can tell that
anything happened, which is why the test cannot live there.

`VERIFICATION.md` P-5's `prove` documents the obligation; it does not discharge
it at run time. `SAFETY.md` S-15b states the rule for the whole library and
carries the shape, which is committed as `ns_add_checked` in
`tests/probe/probe02_int128.npk`.

**A defect in this section's own text, found while writing N-20b and not
guessed at.** N-20 says the `int128` sites "are exactly three … named above",
and §5's table marks **one** — `period_add`'s nanosecond step. The year/month
step is marked `int64` and the day step carries no widening at all. So the count
and the enumeration disagree, and `TESTING.md`'s `check_int128_sites`, which
0.2 puts on the harness, cannot be written against "the three sites §5 names"
until they are named. Recorded as **O-X6** with a recommendation rather than
settled here: choosing which three requires designing `period_add` and
`timestamp_since`, which no cycle has done yet, and a rule invented to make a
count come out right is worse than an acknowledged gap. **N-20b binds to every
narrowing site in the table regardless of the count**, so nothing waits on it.

*(Settled at cycle 0.2.3a, TM-229: the table is the authority, in its `int128`
column, and N-20 states no count. Choosing the sites took less design than
this paragraph expected — `TIME_MODEL.md` M-20 had already put
`timestamp_since`'s arithmetic in `int128`, and `period_add`'s row stands as
the founding table marked it. What it took was a measurement: `src/` held a
site no row named, `bytes_put_int`'s loop measure.)*

---

## 6. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
