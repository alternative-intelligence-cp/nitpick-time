# ntime

Dates, times and time zones for **[Nitpick](https://github.com/alternative-intelligence-cp/nitpick)** —
the safety-critical systems language. No dependencies, no libc, no
`/usr/share/zoneinfo`, no C anywhere in the artifact. The time-zone database is
compiled in from a pinned IANA release, so the same program gives the same
answer on every machine.

> **Status: cycle 0.1, the civil calendar, CLOSED on 2026-09-26, archived at
> [`meta/roadmap/done/0.1/`](meta/roadmap/done/0.1/README.md)** — its code, its
> gate and its audit done — **and cycle 0.2, instants and timestamps, is next.**
> What exists: `src/core/` (`Vec<T>`,
> `Bytes` and the named limits) since cycle 0.0, and `src/cal/` — `CivilDate`,
> `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, the day-number algorithms,
> the weekday, the day of the year and the ISO week date — whose gate is
> exhaustive: every day of years −9999 … +9999 goes to its day number and back,
> both ways, on every full run, and every date of years 1 … 9999 agrees with
> Python's `datetime`. Instants, zones, formats and the clocks are still
> placeholders, each replaced by the cycle
> [`meta/roadmap/ROADMAP.md`](meta/roadmap/ROADMAP.md) names. The specification
> set is in [`meta/specs/`](meta/specs/) and the plan in
> [`meta/roadmap/`](meta/roadmap/), written the way the compiler's are — specs
> first, then a cycle map, then execution-grade subcycles, then code — against
> a compiler that is still moving, pinned by commit (`CLAUDE.md` names the pin:
> `5fbaf4a` since cycle 0.2.0a, the adoption that opened cycle 0.2).
>
> *(Until cycle 0.1.5 this block read "Status: planning. No code yet" — false
> since cycle 0.0.4 — and "the compiler itself is at cycle 1.5"; between the
> close's two halves, that cycle 0.1 "is in its close … and the audit that
> closes it is next".)*

---

## Why another date library

Because the mistakes date libraries make are the mistakes this language is
built to make unspellable, and because the ones it cannot make unspellable are
worth stating out loud instead of discovering.

**The clocks are different types, so you cannot confuse them.** A monotonic
reading and a wall-clock reading are not the same kind of thing: NTP steps the
wall clock and never the monotonic one, which is why the compiler's own
deadline substrate refuses to use a wall clock at all (D-176). `ntime` makes
that structural — an `Instant` has no epoch and yields only differences, a
`Timestamp` is an absolute point on the UTC scale, and **there is no conversion
between them**. A timeout measured against the wall clock is a bug you cannot
write here.

**Wall time and calendar time are also different types.** A `CivilDateTime` —
"2026-03-29 02:30" — is not a point in time until you say where. In most of
Europe that particular one does not exist, and in October the same wall reading
happens twice. `ntime` will not let you add a duration to a wall-clock reading
and pretend the answer is an instant; you convert through a zone, and the zone
tells you when the answer is ambiguous or missing rather than picking one
quietly.

**Exact spans and calendar spans are different types too.** A `Duration` is a
number of nanoseconds and adding it is exact. A `Period` is "one month", which
is not a number of nanoseconds and depends entirely on where you start.
Libraries that fuse them are the reason "add one month to 31 January" is a
famous question. Here the two cannot be added to the same things, and the rules
for what a `Period` does are written down with worked examples rather than
implied by an implementation.

**The zone database is compiled in and version-pinned.** Reading
`/usr/share/zoneinfo` means parsing a binary format from files the program does
not control, and it means the same program on two machines disagrees about what
time it is. `ntime` generates its tables from a named IANA release and commits
them as Nitpick source — the same choice the sibling TUI library made about
terminfo, for the same reasons, and the same one the compiler makes about every
generated table. Reading the system database is a post-1.0, opt-in module that
a program has to import on purpose.

**Overflow traps rather than wrapping.** Adding a century to a timestamp that
cannot hold one is a controlled stop in this language, not a silent journey to
the year 292 billion. The representable range is stated and checked at every
constructor, before the trap: a date outside it is refused, not built. *(This
said, until cycle 0.1.5, that the range would be "enforced by the type system
when the compiler's `limit<Rules>` lands". It landed at the compiler's 1.5.2,
and `ntime` uses it on its containers' lengths — TM-156 — while the calendar's
range stays the constructors' to refuse, `meta/specs/CALENDAR.md` C-8.)*

**Importing it costs a consumer at most three error identities — and one if all
you want is calendar arithmetic.** In this language every error identity a
library's reachable code can raise is a mandatory arm in every consuming
program's shutdown handler *("a library declares" until 2026-09-27: the
ecosystem audit's EC3, TM-213 — a declaration nothing raises costs nothing, and
a private one that is raised costs the arm)*, so the number is an API decision, not an implementation detail.
`ntime`'s is three. **The whole bill is larger**, because the language also
charges an arm for each kind of trap the imported code can reach — a division,
an overflow, an index, a loop's measure, a length's limit — on top of a floor
every program owes: measured at compiler `c970483`, a program importing only
the calendar owes **11** <!-- [[sweep: arms_cal=11]] --> arms, and one importing
the whole library **13** <!-- [[sweep: arms_lib=13]] -->. The table is
`meta/specs/SAFETY.md` S-4, generated and checked against the compiler on
every run — and since the close's second half the two numbers here are held to
it too, so a bill that moves turns this page's run red (TM-205). *(Until cycle 0.1.5 this paragraph said importing
`ntime` "costs a consumer three `failsafe` arms", which counted the identities
and not the bill.)*

---

## What it will provide

The **calendar** row exists since cycle 0.1; every other row is a later cycle
of [`meta/roadmap/ROADMAP.md`](meta/roadmap/ROADMAP.md).

| Layer | Contents |
|---|---|
| **calendar** | `CivilDate`, `CivilTime`, `CivilDateTime`, `Weekday`, `Month`, leap years, ISO week dates, ordinal dates — proleptic Gregorian, exact, and exhaustively tested over the whole supported range |
| **instants** | `Instant` (monotonic, no epoch) and `Timestamp` (absolute UTC, seconds and nanoseconds) |
| **spans** | the prelude's `Duration` for exact nanosecond spans, and `Period` for calendar spans, with the conversion rules stated |
| **zones** | the compiled-in IANA database, offset lookup, DST transitions, and explicit answers for ambiguous and nonexistent local times |
| **formatting** | RFC 3339, ISO 8601 (date, time, week date, ordinal date), RFC 5322, HTTP-date — as named functions, plus a **typed** layout for custom formats. There is no format-specifier language |
| **parsing** | the same formats in reverse, with a stated leniency policy and a round trip that is a fixed point |
| **host** | the one impure module: `clock_gettime` for the three clocks, and the system-zone discovery a program has to ask for |

---

## Layout

```
src/          # THE LIBRARY — Nitpick source only
  core/       #   growable storage, byte building, the named limits
  cal/        #   the civil calendar and its algorithms
  span/       #   Duration interop and Period
  zone/       #   the GENERATED time-zone tables and the offset lookup
  fmt/        #   formatting and parsing, and the typed layout
  host/       #   the only module that asks the machine anything
tests/        # probe, conformance, unit, golden, rejection, fixtures
examples/     # runnable demonstrations, built and run by the harness
harness/      # the Python build and test runner, until `npkg` can build a library
tools/        # generators — the civil cross-oracle's corpus since cycle 0.1.4, the tzdb
              # tables from cycle 0.5; everything they emit is committed
meta/specs/   # the design authority
meta/roadmap/ # the plan, in numbered cycles
docs/         # user-facing documentation, written at 1.0
```

## Specification

[`meta/specs/`](meta/specs/) is the authority on behaviour, and
[`meta/DECISIONS.md`](meta/DECISIONS.md) records every settled design decision
with its reasoning — start there when something looks unusual, because it is
recorded why.

## Plan

[`meta/roadmap/ROADMAP.md`](meta/roadmap/ROADMAP.md) is the cycle map. A cycle
is a folder, a subcycle is a file inside it, and a finished cycle moves to
`meta/roadmap/done/`.

## Requirements

Linux on x86-64, the Nitpick compiler, and LLVM 20.1.2 — the same toolchain the
compiler pins. Nothing else, at build time or at run time.

## Licence

Apache 2.0. See [`LICENSE`](LICENSE).
