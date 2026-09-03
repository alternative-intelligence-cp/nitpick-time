# The time model

The type set, and why each distinction exists. **This is the document that
decides every other one.** Almost every bad idea in a date library is a type
distinction it declined to make, and almost every good one is a conversion it
refused to perform implicitly.

---

## 1. Three scales, and they are not the same kind of thing

| Scale | Question it answers | Type |
|---|---|---|
| **monotonic** | how much time has passed since some earlier reading? | `Instant` |
| **absolute** | which point on the UTC timeline is this? | `Timestamp` |
| **civil** | what would a clock on a wall say? | `CivilDateTime` |

**Rule M-1 (TM-010) — these are three types and there is no implicit conversion
between any pair of them.** Every conversion that is possible at all is a named
function that takes whatever extra information it needs, and the conversions
that are *not* possible do not exist:

```
Instant   ──✗──►  Timestamp        no epoch, and no relationship to one (M-3)
Timestamp ──✓──►  CivilDateTime    given a zone, or as UTC
CivilDateTime ──►  Timestamp       given a zone, AND an answer for §6's edge cases
```

---

## 2. `Instant` — the monotonic scale

```nitpick
pub struct:Instant = { int64:ns; };      // opaque; the origin is arbitrary
```

**Rule M-2.** An `Instant` is a reading of `CLOCK_MONOTONIC`. Its origin is
whatever the kernel chose at boot, it is **not** an epoch, and it is not
comparable across processes or across a reboot.

**Rule M-3 (TM-010) — an `Instant` cannot be converted to a `Timestamp`, in
either direction, ever.** This is the load-bearing refusal of the whole model, and the
compiler's own runtime makes the argument for us, in the floor's source:

> *Wall clocks are excluded from the deadline path: NTP steps them, and a
> deadline that moves with the wall silently voids D-056's containment.*
> — `runtime/npkrt.ll`, the `npk_mono_now` block

A library that offers the conversion offers a caller the ability to write a
timeout against a clock that a network time daemon can move backwards by an
hour. Here that program does not compile.

**Rule M-4 — the only thing you can do with two `Instant`s is subtract them**,
and the result is a `Duration`:

```nitpick
pub func:instant_since = Duration(Instant:later, Instant:earlier);   // never fails*
pub func:instant_add   = Instant(Instant:t, Duration:d);
pub func:instant_cmp   = Ordering(Instant:a, Instant:b);
```

\* `instant_since` cannot overflow in practice — the monotonic clock's origin
is the boot, and `int64` nanoseconds is 292 years of uptime — but D-210 traps
if it somehow did, which is the correct outcome for a machine that has been up
since the Cretaceous.

**Rule M-5.** `Instant` is what a timeout, an elapsed measurement, a rate limit
and a benchmark use. `ntime` provides it so that those uses have a type; the
prelude's `Duration` is what they produce.

---

## 3. `Timestamp` — the absolute scale

```nitpick
pub struct:Timestamp = { int64:secs; uint32:nanos; };   // Unix epoch, UTC
```

- `secs` — SI seconds since `1970-01-01T00:00:00Z`, **ignoring leap seconds**
  (§5).
- `nanos` — `0 … 999_999_999`, always non-negative, so that a `Timestamp`
  before the epoch has a negative `secs` and a positive `nanos` and there is
  exactly one representation of every instant.

**Rule M-6 (TM-011) — the field order is semantic.** `#[derive(Ord)]` compares in
declaration order (TRAITS_REFERENCE §2.5), so seconds-then-nanoseconds is
exactly the comparison wanted. Reordering the fields silently changes what `<`
means, which is why `SAFETY.md` S-14 makes it a rule rather than a comment.

**Rule M-7 — the normalisation invariant.** `nanos < 1_000_000_000` always. It
is established by every constructor and re-established by every arithmetic
operation, and it is the first thing the property tests check, because a
denormalised `Timestamp` compares wrongly and prints wrongly and does so
without ever failing.

**Rule M-8 (TM-014) — the supported range** is the civil range of `CALENDAR.md` §2,
expressed in seconds:

| Bound | Value | Civil |
|---|---|---|
| minimum | `−377705203200` | `−9999-01-01T00:00:00Z` |
| maximum | `253402300799` | `+9999-12-31T23:59:59Z` |

Both fit `int64` with twenty-seven orders of magnitude to spare, so the range
is a *policy*, not a representation limit — and it is checked at every
constructor rather than left to the trap.

---

## 4. The civil types

Detailed in [`CALENDAR.md`](CALENDAR.md); named here because the model needs
them:

```nitpick
pub struct:CivilDate     = { int32:year; uint8:month; uint8:day; };
pub struct:CivilTime     = { uint8:hour; uint8:minute; uint8:second; uint32:nanos; };
pub struct:CivilDateTime = { CivilDate:date; CivilTime:time; };
```

**Rule M-9 — a `CivilDateTime` is not a point in time.** `2026-03-29T02:30:00`
does not exist in `Europe/London` and happens twice in `Europe/London` in
October. It becomes an instant only through a zone, and only with an answer
for §6's cases.

**Rule M-10 — a `CivilDateTime` may be compared and ordered**, and that
ordering is *lexicographic on the fields*, which is the ordering people expect
of a wall reading. It is **not** an ordering of instants, and the documentation
says so where it could mislead: two civil times an hour apart across a spring
transition are the same instant.

---

## 5. Leap seconds — the position, stated

**Rule M-11 — `ntime` uses UTC without leap seconds: every day is exactly
86 400 seconds, and `Timestamp ↔ civil` is a pure bijection** (TM-006).

This is the POSIX `time_t` model. It is chosen because:

- **It is what the machine provides.** `CLOCK_REALTIME` is stepped or smeared
  by NTP; there is no interface through which this library could obtain true
  TAI, so a leap-second table would describe a scale the clock is not on.
- **A leap-second table expires.** Leap seconds are announced about six months
  ahead. A compiled-in table would be a second dataset with a shorter shelf
  life than the tzdb, and a program built today would compute a *wrong* answer
  for a leap second announced tomorrow — worse than the one-second
  approximation it replaces.
- **The alternative breaks the bijection.** With a leap table,
  `Timestamp → civil` stops being a pure function of the timestamp and becomes
  a function of the table's version, which would take the whole library out of
  `SAFETY.md` §3's purity rule.

**Rule M-12 — the consequence, stated rather than hidden.** A `Duration`
computed between two `Timestamp`s that straddle a leap second is short by one
second against true elapsed SI time. As of this writing 27 leap seconds have
been inserted since 1972, all positive, so the maximum error over the whole era
is 27 seconds. Anything that needs SI-exact elapsed time uses `Instant`, which
is unaffected — **which is itself an argument for M-3's split**.

**Rule M-13 (TM-029) — `:60` is accepted on input and folded, never emitted.** RFC 3339
permits a `second` value of 60. `ntime` parses it, maps it to the same instant
as `:59` of that minute (the POSIX repeat), and sets `folded_leap` on the
returned `Parsed` record so a caller who cares can tell. It never *emits* `:60`.

This is the one place in the library where parsing is not injective, and it is
named here and re-stated in `FORMAT_MODEL.md` §6 so that the round-trip gate
(`TESTING.md` §4) can carry it as a documented exception rather than a
mysterious failure.

---

## 6. Zoned time, and the two edge cases

Detailed in [`ZONE_MODEL.md`](ZONE_MODEL.md). The model-level facts:

```nitpick
pub struct:ZonedDateTime = {
    Timestamp:instant;          // the answer, and the source of truth
    CivilDateTime:civil;        // the wall reading, cached
    int32:offset_secs;          // civil - UTC, in seconds
    ZoneId:zone;
};
```

**Rule M-14 — the instant is the source of truth** and the civil fields are a
cache of what that instant looks like in that zone. Every operation that could
make them disagree recomputes them. A `ZonedDateTime` whose civil fields do not
match its instant under its zone is an invariant violation, and the property
tests check it after every operation.

**Rule M-15 (TM-020) — converting `CivilDateTime` → instant has three outcomes**, and
the API makes the caller choose which it wants rather than picking:

| Outcome | When | `zoned_strict` | `zoned_earlier` / `zoned_later` | `zoned_compatible` |
|---|---|---|---|---|
| unique | the ordinary case | the instant | the instant | the instant |
| **ambiguous** | a fall-back transition: the wall reading happens twice | `ETimeZone` / `Ambiguous` | the chosen one | the **earlier** |
| **nonexistent** | a spring-forward gap: the wall reading never happens | `ETimeZone` / `Nonexistent` | the instant either side of the gap | shifted **forward** by the gap |

`zoned_compatible` is named for the behaviour ICU and Temporal call
"compatible", which is what most software wants and what nobody should get by
accident. **There is no default**: a caller writes one of the four names.

---

## 7. Spans

Detailed in [`SPAN_MODEL.md`](SPAN_MODEL.md). Two types, and the distinction is
as load-bearing as M-1's:

- **`Duration`** — **the prelude's** `{ int64:ns }` (TM-004). An exact count of
  nanoseconds. Adding it to a `Timestamp` is exact arithmetic.
- **`Period`** — `{ int32:years; int32:months; int32:days; int64:ns }`. A
  calendar span. "One month" is not a number of nanoseconds, and what it means
  depends entirely on where you start.

**Rule M-16 (TM-012) — a `Period` cannot be added to a `Timestamp` or an
`Instant`.**
Only to a `CivilDate`, a `CivilDateTime` or a `ZonedDateTime`, because only
those know where they are on the calendar. This refusal is the type-system
answer to "add one month to an epoch second", which has no meaning and which
every library that allows it answers differently.

**Rule M-17 — `ntime` declares no `Duration` of its own** and never will. The
prelude's is the ecosystem's one span type: the deadline substrate takes it,
every I/O call takes it, and a second one would immediately become the type
everybody converts to and from. Where the prelude's range is insufficient —
§8 — the answer is a different *operation*, not a different span type.

---

## 8. The `Duration` range, and where it bites

**`Duration` is `int64` nanoseconds: ±292.277 years** (the prelude's own
comment says so). The library's civil range is ±9999 years. **These do not
match, and the mismatch is real** — and it is not a defect to be fixed by
widening `Duration`, which would change the deadline substrate's
representation for every consumer in the ecosystem to serve a case that wants
`Period` instead. Recorded as O-N3 so that the "fix" is refused once rather
than proposed repeatedly.

| Span | Nanoseconds | Fits `int64`? |
|---|---|---|
| the full civil range (7 304 485 days) | 6.31 × 10²⁰ | **no** |
| ±292 years | 9.22 × 10¹⁸ | yes, exactly |

**Rule M-18 — `timestamp_since(a, b) -> Result<Duration>` fails
`ETimeValue`/`Overflow` when the difference exceeds `Duration`'s range.** It
does not trap, it does not saturate, and it does not silently lose precision.
A caller differencing two timestamps 500 years apart is asking a question
`Duration` cannot answer, and the honest response is to say so.

**Rule M-19 — the calendar-scale answer is `Period`, not a wider `Duration`.**
`timestamp_until(a, b, unit)` yields the difference in whole days, months or
years, which is what a caller asking about a 500-year span actually wanted.

**Rule M-20 — internal arithmetic that could exceed `int64` nanoseconds
computes in `int128` and narrows once**, with `=>!` at a point where the value
is proven to fit (the D-210.3 idiom). Every such site is listed in
`SPAN_MODEL.md` §5 and carries a `prove` obligation
(`VERIFICATION.md` §4), because this is the single most likely place for this
library to be quietly wrong.

---

## 9. The conversion lattice, complete

Every conversion the library offers, and every one it refuses. This table is
normative: a conversion not on it does not exist.

| From | To | How | Fails? |
|---|---|---|---|
| `Instant` | `Instant` | `+ Duration` | traps on overflow only |
| `Instant`, `Instant` | `Duration` | `instant_since` | no |
| `Instant` | `Timestamp` | **refused** (M-3) | — |
| `Timestamp` | `Timestamp` | `+ Duration` | `ETimeValue` outside range |
| `Timestamp`, `Timestamp` | `Duration` | `timestamp_since` | `ETimeValue` past ±292 y (M-18) |
| `Timestamp`, `Timestamp` | `Period` | `timestamp_until` | no |
| `Timestamp` | `CivilDateTime` | `timestamp_to_utc` | no (in range by construction) |
| `Timestamp` + `ZoneId` | `ZonedDateTime` | `zone_at` | `ETimeZone` unknown zone |
| `CivilDateTime` | `Timestamp` | `civil_to_utc` | `ETimeValue` |
| `CivilDateTime` + `ZoneId` | `ZonedDateTime` | the four of M-15 | `ETimeValue`, `ETimeZone` |
| `CivilDateTime` | `Instant` | **refused** | — |
| `ZonedDateTime` | `Timestamp` | field read | no |
| `ZonedDateTime` | `CivilDateTime` | field read | no |
| `CivilDate` | `int64` days | `date_to_days` | no |
| `int64` days | `CivilDate` | `days_to_date` | `ETimeValue` outside range |
| `Period` + `Instant`/`Timestamp` | — | **refused** (M-16) | — |

---

## 10. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
