# Design decisions

Every settled design decision for `ntime`, with the reasoning, the alternatives
that were considered, and the date. **This is the file to read when something
in the specifications looks unusual**, because it is recorded why.

Referenced as `TM-nnn` from the specifications. `D-nnn` in those documents
refers to the **compiler's** `meta/specs/DECISIONS.md`; those are language
decisions and are not ours to amend.

**Rule: a settled decision's text is never rewritten.** A decision that turns
out to be wrong is superseded by a new one that says so and says why; the old
text stays, dated, because it records what was true when it was made. This is
the compiler's D-085/D-202 pattern.

**Numbering is allocation order, grouped by the batch that settled it.**
TM-001 … TM-030 are the founding batch, written with the specification set and
organised below by area. Later batches are appended whole with their own
heading, because a batch ratified together is a unit — the compiler's own
shape, where D-194 … D-200 and D-201 … D-209 are batches, not areas.

---

## Foundations

### TM-001 — the library is `ntime`; the repository is `nitpick-time`
**2026-09-03.** The module prefix, every public symbol's prefix, and the
eventual package name are `ntime`, matching the ecosystem's `n`-prefix
convention (`nfs`, `nproc`, `nio`, `nsys`, `ntui`). The repository keeps the
longer name because a repository name is a search term and `ntime` alone is
not one.

*Alternatives:* `time` (collides with a user's own module of that name, and
breaks a convention every other library follows); `nitpick_time` (verbose at
every import site).

### TM-002 — the specifications are the authority
**2026-09-03.** Code that disagrees with `meta/specs/` is a defect in the code.
A specification that is wrong is amended by a decision recorded here, never by
editing the text and moving on. The compiler's own cycle notes record the same
finding repeatedly — the compiler and the thing that describes it have to be
diffed, because reading either alone never reveals the gap — and
`TESTING.md` §2's checks are that diff, applied here.

### TM-003 — `harness/` builds and tests `ntime` until `npkg` can
**2026-09-03.** Measured at the compiler's 1.5.0: `npkg build` is the
compiler's own bootstrap ladder with no generic-project path, and
`[dependencies]` is parsed but the loader's dependency-root list is created
empty and never populated, so cross-repository imports do not resolve. A Python
harness drives `npkc`, `llc` and `ld.lld` directly, mirroring
`bootstrap/harness/`'s relationship to `npkg`, and retires the same way — both
running side by side with a parity check before the older is removed.

*Not a dependency violation:* zero-dependency governs the artifact, not the
workbench (the compiler's `ORCHESTRATION.md` §6 says so in as many words).

### TM-004 — the prelude's `Duration` is the one exact span type
**2026-09-03.** `ntime` uses `Duration` from `src/prelude/prelude.npk` —
`{ int64:ns }`, ±292.277 years — and declares no span type of its own for exact
time. It adds constructors (`duration_mins`, `duration_hours`, `duration_days`,
`duration_weeks`) and nothing else.

*Reasoning:* it is the ecosystem's one span type. D-176 makes it what every
deadline takes; every `Reader`/`Writer` method takes it; `sleep` takes it. A
second one would immediately become the type everybody converts to and from,
and the conversion would be the bug.

*The cost, accepted and stated:* `Duration`'s ±292 years does not cover the
library's ±9999-year civil range. `TIME_MODEL.md` §8 handles it by making
`timestamp_since` **fail** `ETimeValue`/`Overflow` past the range rather than
saturating, and by offering `timestamp_until` in calendar units — a different
*operation*, not a different span type.

*Alternatives:* an `ntime`-local wide duration in `int128` nanoseconds
(rejected: two span types, and every API taking a deadline would need the
narrow one anyway); a duration in seconds-plus-nanos like `Timestamp`
(rejected for the same reason, plus it would not be the type `sleep` takes).

### TM-005 — `ntime` declares its own storage primitives
**2026-09-03.** `Vec<T>`, `Bytes` and the named limits live in `src/core/` and
are ours. The compiler's `List<T>` is not imported: it is a compiler internal
whose own header says it exists for the compiler's tables, and reaching into
another project's `src/` couples this library's correctness to a file that is
not a published interface. `Vec<T>` is `List<T>`'s shape, deliberately, because
that shape is right and has been exercised across twenty-two families.

### TM-006 — UTC without leap seconds
**2026-09-03.** Every day is exactly 86 400 seconds; `Timestamp ↔ civil` is a
pure bijection; the library models no leap seconds and carries no leap table.
This is the POSIX `time_t` model.

*Reasoning:*
1. **It is what the machine provides.** `CLOCK_REALTIME` is stepped or smeared
   by NTP, and there is no interface through which this library could obtain
   true TAI — so a leap table would describe a scale the clock is not on.
2. **A leap table expires.** Leap seconds are announced about six months ahead.
   A compiled-in table would be a second dataset with a shorter shelf life than
   the tzdb, and a program built today would be *wrong* about a leap second
   announced tomorrow — worse than the one-second approximation it replaced.
3. **It would break purity.** With a table, `Timestamp → civil` stops being a
   pure function of the timestamp and becomes a function of the table's
   version, taking the whole library out of TM-018's rule.

*The residue, stated rather than hidden:* a `Duration` between two timestamps
straddling a leap second is short by one second against true elapsed SI time —
at most 27 seconds over the whole era since 1972. Anything needing SI-exact
elapsed time uses `Instant`, which is unaffected, **which is itself an argument
for TM-010's split.**

*Alternatives:* a compiled leap table (rejected above); TAI as a separate scale
with conversion (rejected: the conversion needs the same expiring table, and
nothing can produce a TAI reading on this platform anyway).

### TM-007 — the time-zone database is compiled in from a pinned release
**2026-09-03.** `ntime` generates its zone tables from a named IANA release and
commits them as Nitpick source. It does not read `/usr/share/zoneinfo`, does
not parse TZif at run time, and does not consult `$TZ` unless a program asks
(TM-019).

*Reasoning, in order of weight:*
1. **A TZif reader is an untrusted-input binary parser** inside a library whose
   claim is that it has none.
2. **Its answers would depend on machine state**, so the same program on two
   machines would disagree about what time it is — which takes the library out
   of TM-018's purity rule and makes every zoned test a test of the machine it
   ran on.
3. **The ecosystem has answered the analogous question twice already**: the
   compiler generates and commits its builtin and flag tables; `ntui` refused
   terminfo (T-003) and generates its Unicode tables (T-021). A third answer
   here would be an inconsistency, not a nuance.
4. **The size objection does not survive measurement.** Measured on the
   workbench against tzdata 2026c: 447 canonical zones, 26 838 transitions,
   2 484 local-time types — **≈ 348 KiB** in the representation
   `ZONE_MODEL.md` §3 specifies. That is a decision made against a number
   rather than a fear.

*The cost, stated:* the tzdb changes several times a year, and a program built
with release *R* believes *R* until it is rebuilt. TM-028 is the answer for
software where that is not acceptable, and it is deliberately not the default.

*Alternatives:* read the system database (rejected above); ship a subset of
zones (rejected: a build-configuration knob the ecosystem does not have, and
348 KiB does not justify one — though `ZONE_MODEL.md` O-Z1 keeps the question
open until 0.5 measures the real emitted size).

### TM-008 — Linux on x86-64 only, at 1.0
**2026-09-03.** `src/host/` is Linux syscalls with Linux numbers. Everything
outside it is platform-independent by construction (TM-018), so a port is a
rewrite of one module — but it is a cycle with its own decision rather than
something left half-done behind a conditional. `aarch64` Linux is the first
port to consider: the numbers differ, the structures do not.

### TM-009 — there is no format-specifier language
**2026-09-03.** No `strftime`, no `strptime`, no function that takes a pattern
as text and interprets it at run time. Named functions for the named formats
(RFC 3339, ISO 8601, RFC 5322, HTTP-date), and a **typed layout** — a
`Vec<FmtPart>` — for everything else.

*Reasoning:* D-053 removed `printf`/`scanf` from the language and its argument
transfers exactly — a format string fuses the output text, the layout
instruction and a type assertion into one literal, and every format defect is
that fusion coming apart. D-053 went further and explicitly **rejected adding
format specifiers to string interpolation**, on the grounds that it would
reintroduce "a second mini-language, with its own grammar, its own diagnostics,
and its own conformance surface … purely to save characters." A `strftime` here
would be exactly that mini-language.

*The consequence, and the guard:* there is no `layout_from_pattern("%Y-%m-%d")`
and there never will be, because adding it later would reintroduce everything
this removed. `check_no_format_string` makes the rule checkable rather than
remembered.

*Alternatives:* a compile-time-checked pattern via `comptime` (rejected: it is
still a grammar, still needs diagnostics, and the typed layout is the same
thing with the compiler's own type checker doing the work); method chains only
(rejected: a custom layout would be unreusable and unparseable — a layout has
to be a value so that one of them drives both directions, F-6).

---

## The type model

### TM-010 — three scales, three types, and no monotonic ↔ absolute conversion
**2026-09-03.** `Instant` (monotonic, no epoch), `Timestamp` (absolute UTC),
and the civil types are three separate types. There is **no conversion between
`Instant` and `Timestamp` in either direction, ever.**

*Reasoning:* the compiler's own runtime makes the argument, in the floor's
source at `npk_mono_now`: *"Wall clocks are excluded from the deadline path:
NTP steps them, and a deadline that moves with the wall silently voids D-056's
containment."* A library that offers the conversion offers a caller the ability
to write a timeout against a clock a network time daemon can move backwards by
an hour. Here that program does not compile.

*Corollary (TM-010.1):* `Instant` records which clock produced it —
`CLOCK_MONOTONIC` or `CLOCK_BOOTTIME`, which differ across suspend — and
`instant_since` refuses a pair from different clocks. The same argument, one
level down.

*Alternatives:* a single `Instant` type with an epoch flag (rejected: a mode
field selecting behaviour at run time, which D-072 rejected for channels for
the same reason); offering the conversion with a warning (there are no warnings
in this ecosystem, and a comment is not a type).

### TM-011 — `Timestamp` is `{ int64:secs; uint32:nanos }`, and field order is semantic
**2026-09-03.** Seconds since the Unix epoch plus a non-negative nanosecond
remainder in `[0, 999 999 999]`, so every instant has exactly one
representation.

*Field order is load-bearing:* `#[derive(Ord)]` compares in **declaration
order** (TRAITS_REFERENCE §2.5), so seconds-then-nanoseconds is exactly the
comparison wanted, and reordering the fields would silently change what `<`
means. Recorded as a decision rather than a comment because it looks like a
style question and is not.

*Why not `int64` nanoseconds:* it would cap the range at ±292 years from the
epoch — 1678 to 2262 — which is not a date library. Why not `int128`
nanoseconds: it would make every comparison and every arithmetic operation
double-width for a range nothing needs, and `int128` division emits libcalls
the floor has to provide.

### TM-012 — `Period` is a separate type and cannot be added to an instant
**2026-09-03.** `Period { years, months, days, ns }` is a calendar span.
`Duration` is an exact one. A `Period` may be added only to `CivilDate`,
`CivilDateTime` or `ZonedDateTime` — never to `Timestamp` or `Instant`.

*Reasoning:* "one month" is 28, 29, 30 or 31 days and "one day" is 23, 24 or 25
hours in a zone with DST, so a `Period` has no meaning without a starting point
on a calendar. Libraries that fuse the two are why "add one month to an epoch
second" has a different answer in every language. This refusal is the type
system answering a question that otherwise has no answer.

### TM-013 — versioning, and adding an error identity is a MAJOR version
**2026-09-03.**

- `0.x` until the compiler reaches its own 1.0 **and** the API has survived a
  real consumer. Before that, anything may move.
- Semantic versioning thereafter.
- **A tzdb release bump is a MINOR version, never a patch** (`COMPAT.md` K-4):
  it changes computed answers, which is not a bug fix and should not arrive in
  a patch.
- **Adding a public `error:` identity is a MAJOR version**, because REACH-002
  makes it a new mandatory `pick` arm in every consuming program's `failsafe` —
  a compiler-enforced source break in every consumer.

That last rule is the one thing about this ecosystem a consumer most needs to
know, and it is the practical teeth behind TM-017's budget of three: the budget
is not a style guide, it is what keeps the major version from moving.

### TM-014 — the supported range is year ±9999, astronomical numbering
**2026-09-03.** `year ∈ [−9999, +9999]`, proleptic Gregorian, with year 0
existing and meaning 1 BCE. Every constructor checks it and returns
`ETimeValue` before D-210's trap can fire.

*Reasoning:*
- **It is testable exhaustively.** 7 304 485 days is a few seconds of
  computation, so "every date round-trips" is a *gate* (TM-026) rather than an
  aspiration. A wider range would make the strongest test in this library
  impossible.
- **Four digits is what every text format carries.** RFC 3339 requires exactly
  four.
- **Astronomical numbering makes arithmetic uniform** with no gap to
  special-case, which is what ISO 8601 uses.
- The exact bounds — day numbers `−4 371 588 … +2 932 896`, seconds
  `−377 705 203 200 … +253 402 300 799` — are computed, not estimated, and
  cycle 0.1 pins them with a test that recomputes them.

*Alternatives:* Java's ±999 999 999 (rejected: not exhaustively testable, and
no text format can carry it); the `int64`-nanosecond range 1678–2262 (rejected:
not a date library); year 1 … 9999 with no year 0 (rejected: a gap in the
number line that every arithmetic path would have to special-case).

### TM-015 — proleptic Gregorian only, with no Julian cutover
**2026-09-03.** The Gregorian rules extended backwards past 1582, uniformly.

*Reasoning:* a cutover date is a **locale** property — Britain 1752, Russia
1918, Greece 1923 — so honouring it would make the calendar itself
zone-dependent and every date operation would need a zone. ISO 8601 specifies
proleptic Gregorian for exactly this reason. A caller doing historical work
needs a different library, and `COMPAT.md` §4 says so.

### TM-016 — Howard Hinnant's civil algorithms, used as given
**2026-09-03.** `date_to_days` / `days_to_date` are `days_from_civil` /
`civil_from_days`: branch-free, exact well past our range, defined for negative
years, with a published derivation. `ntime` cites the source in the module
header and does not reinvent them.

*Reasoning:* they are the best-known correct answer to a problem where "looks
right" and "is right" diverge at century boundaries and negative years, and
every division in them is by a nonzero literal — so D-007's trap is unreachable
by construction and the obligation is discharged by inspection, which matters
for `VERIFICATION.md`.

### TM-017 — the error budget is three
**2026-09-03.** `ETimeValue`, `ETimeParse`, `ETimeZone`, and nothing else.

*Reasoning:* REACH-002 makes every identity a mandatory `failsafe` arm in every
consumer, where forgetting one is a compile error. Three is what survives
asking, of each candidate, *"would a shutdown handler treat this differently
from the others?"* — "out of range" and "not a real date" would not, so they
are one error with a `ValueFault` detail field; every parse failure is one
error with a `ParseError` detail carrying the offset and what was expected.

*The decomposition is part of the budget*, because REACH is import-scoped:
`ntime/cal.npk` declares only `ETimeValue`, so **a program that only wants
calendar arithmetic owes one arm.** That is the whole reason `cal` does not
import `zone`.

*Alternatives:* one identity for everything (rejected: a `failsafe` genuinely
would treat an unknown zone differently from a malformed input, because one is
a programming error and the other is data); seven or eight, one per fault class
(rejected: it is the caller who cares about the distinction, and S-3's detail
fields carry it at no cost to any consumer).

### TM-018 — purity: only `src/host/` is impure, and a check enforces it
**2026-09-03.** Every function in `ntime` outside `src/host/` is a pure
function of its arguments — no syscall, no clock, no environment read, no file
read. `src/host/` contains exactly five functions and nothing else calls them.

*Reasoning:* it is what makes the library reproducible, testable to the
nanosecond without a double, and portable by rewriting one module. It is also
what makes TM-007's compiled tzdb *necessary* rather than merely tidy — a
runtime database read would put impurity in the middle of the library.

*The rule is not a convention because `check_purity` greps for it* (`sys(`,
`mono_now`, `environ`, `read_file`, `open`, `write` outside `src/host/`) and
fails the build. A rule nothing checks is a rule that decays.

### TM-019 — there is no implicit local time
**2026-09-03.** `ntime` has no `now_in_local_zone()`. A program that wants
local time calls `host_system_zone()`, which reports **which** mechanism
answered — `$TZ`, `/etc/localtime`'s link target, `/etc/timezone`, or nothing —
and then converts explicitly. Not finding one is `found: false`, not a silent
fallback to UTC.

*Reasoning:* a library that reads `$TZ` behind the caller's back produces a
program whose output depends on an environment variable nobody mentioned. It is
the same objection `ntui` raised against inferring behaviour from `$TERM`
(T-003), and the same objection D-076 raised against inferring buffering from
`isatty`. A program that needs local time and cannot find one should decide
what to do; a library that substitutes UTC has decided badly on its behalf.

### TM-020 — four zone-resolution modes, and no default
**2026-09-03.** Converting a civil reading to an instant in a zone has three
possible outcomes — unique, ambiguous (a fall-back transition), nonexistent (a
spring-forward gap) — and four named functions: `zoned_strict` (errors on
either edge), `zoned_earlier`, `zoned_later`, and `zoned_compatible` (the
earlier occurrence; shifted forward across a gap).

*Reasoning:* the caller has to type one of the names. A default here is a
silent choice about an hour of somebody's day, and which default is right
depends entirely on what the program is for — a calendar appointment and a log
timestamp want different answers. `zoned_compatible` is named for the behaviour
ICU and Temporal call "compatible" and is what most software wants, which is
exactly why it should be typed rather than assumed.

### TM-021 — calendar arithmetic clamps, and is neither associative nor invertible
**2026-09-03.** Adding a `Period` applies years, then months, then days, then
nanoseconds. The year and month steps **clamp** the day to the last day of the
target month; the day step is exact and never clamps.

The consequences are stated with worked examples in `SPAN_MODEL.md` §3 so that
nobody "fixes" them:

- `2026-01-31 + 1 month + 1 month` is `2026-03-28`, while
  `2026-01-31 + 2 months` is `2026-03-31`. Both are right.
- `2026-01-31 + 1 month − 1 month` is `2026-01-28`, not `2026-01-31`.

*Reasoning:* every alternative trades one surprise for a worse one. Carrying
the original day-of-month through the arithmetic would make the result depend
on history; refusing to clamp would make "the last day of next month"
inexpressible. Clamping is what ISO 8601, Temporal, `java.time` and every other
considered design chose, and the value of writing it down is that it stops
being rediscovered.

### TM-022 — on a zoned value, calendar steps move the wall clock and durations move the instant
**2026-09-03.** `ZonedDateTime + Period{days: 1}` is the same wall time
tomorrow, which may be 23 or 25 hours later. `ZonedDateTime + Duration` of 24
hours is 24 hours later, which may be a different wall time.

*Reasoning:* both are correct answers to different questions, and the type the
caller wrote is which question they asked. This is the rule most often got
wrong, and getting it wrong makes a daily alarm drift by an hour twice a year.

### TM-023 — the layout is a typed value, and `layout_from_pattern` will never exist
**2026-09-03.** A custom format is a `Vec<FmtPart>` built in code. `FmtPart` is
an enum the type checker sees, so a bad layout is a bad program rather than a
bad string. One layout drives both formatting and parsing, so a format and its
parser cannot drift.

*The guard is explicit* because the temptation is obvious: a
`layout_from_pattern("%Y-%m-%d")` would be a small convenience that
reintroduces the entire mini-language TM-009 removed, and `check_no_format_string`
exists to make adding one a red run rather than a review comment.

### TM-024 — no locale; month and weekday names are English
**2026-09-03.** `MonthName` yields `January`, `WeekdayAbbr` yields `Mon`.

*Reasoning:* localisation is a data problem the size of the tzdb with no
canonical source, varying by more than language (calendars, numerals,
ordering), and half-right is worse than absent. A program needing localised
names supplies its own table and formats the numeric parts with `ntime`. The
English names in RFC 5322 and HTTP-date are protocol constants, not locale.

### TM-025 — strict by default; leniency is a second function name, not a flag
**2026-09-03.** `parse_rfc3339` requires exactly RFC 3339;
`parse_rfc3339_lenient` accepts the common departures and lists each one in its
documentation comment.

*Reasoning:* a leniency flag makes the call site's behaviour depend on a value
a reader has to trace. Two names make it visible where it is used. The same
shape covers `parse_*_prefix` (trailing input allowed) versus the strict form
that requires end-of-input.

### TM-026 — the exhaustive sweep is the gate
**2026-09-03.** Where a property can be checked over its whole domain, it is,
and that is the cycle's gate. The civil round trip covers **every** day in the
supported range — 7 304 485 in each direction — and runs in seconds.

*Reasoning:* it is self-evidently the right property, it needs no external
corpus to trust, and it covers the negative years no external oracle reaches.
Sampling is what you do when you cannot enumerate. The cross-oracles
(`TESTING.md` §5) are supplements, kept separate precisely because they trust
somebody else's library.

### TM-027 — no dependencies, including on the sibling libraries
**2026-09-03.** `[dependencies]` is empty and stays empty. Not the compiler's
`src/`, not its `lib/`, not `nitpick-parse`, not `/usr/share/zoneinfo`, not
libc.

*The one real overlap is recorded rather than resolved:* `nitpick-parse`'s TOML
plugin needs the four TOML datetime types, which are `ntime`'s. Until
dependency resolution lands, each library carries its own scanner and **the two
share test vectors by committing the same corpus in both**, so a divergence is
a red run somewhere rather than a silent disagreement. Tracked as O-X1.

### TM-028 — reading the system tzdb is post-1.0, opt-in, and never the default
**2026-09-03.** Cycle 1.1 adds `ntime/tzif.npk`: a TZif reader with its own
bounds, its own fuzzer and its own error identity, which a program must import
and call on purpose. It produces `ZoneId`s into a separate, runtime-built table
so a program using both can say which answered.

*Reasoning:* it is the honest answer for a long-running server that must track
the current database, and it must not be the default because it would make
every other program's behaviour machine-dependent. Deferred past 1.0 because
1.0 should not ship a binary parser nobody has needed yet — and because its
error identity is a fourth, which TM-013 makes a major version, so it belongs
at a major boundary anyway.

### TM-029 — `:60` and `24:00:00` fold, and the exception list has exactly two entries
**2026-09-03.** RFC 3339 permits a second value of 60 and ISO 8601 permits
`24:00:00`. `ntime` accepts both on input, folds them (`:60` to `:59` of the
same minute, the POSIX repeat; `24:00:00` to `00:00:00` of the next day), never
emits either, and records the fact on the returned `Parsed` record.

*Reasoning:* refusing them would reject real input that real systems emit;
accepting them silently would hide a fact a caller might care about. The
`folded_leap` and `folded_hour24` fields are `SAFETY.md` S-3's detail-field
rule — a caller's distinction that a `failsafe` would not make.

*These are the only two places parsing is not injective*, so the format
round-trip gate carries them as a committed exception list, and **a test
asserts the list has exactly two entries** — a third arriving is a red run
rather than a quiet edit.

### TM-030 — no recursion anywhere
**2026-09-03.** The calendar algorithms are closed-form, the searches are
binary, the parsers are linear scans. `ntime` contains no recursive function
and no unbounded loop.

*Reasoning:* the language has no stack guard, so recursion on
attacker-controlled input is a denial of service — the playbook's
adversarial-input rule. Here the property is free rather than engineered, so it
is worth stating as a property and checking, rather than discovering later that
one function grew a recursive case.

---

# The second batch — ratified 2026-09-03

The four questions this plan put to the project's author, answered as
recommended, with one amendment on where a consumer lives.

### TM-100 — the tzdata release is the latest at cycle 0.5
**2026-09-03, settling Q-1.** Recorded in `src/zone/version.npk`; the workbench
currently carries 2026c, and the pass records what it actually pinned rather
than what was predicted.

**A bump is a minor version, not a patch** (TM-013), because a zone rule change
alters computed answers for dates the program already handled. That is the
honest classification and it is the cost of compiling the database in (TM-007):
the answers are deterministic across machines, and keeping them current is a
release rather than a background fact.

### TM-101 — intervals and recurrence are post-1.0, as cycle 1.3
**2026-09-03, settling Q-2.** An `Interval` and a recurrence rule are genuinely
useful and genuinely separable: everything they need is in the 1.0 surface, so
they are built on top without touching it.

**`Interval` before `RRULE`**, and they are not one cycle. RFC 5545's `RRULE`
is a small language with its own grammar, its own conformance surface and its
own edge cases — it deserves the scrutiny `FORMAT_MODEL.md` §1 gave format
strings, and bundling it with a two-field struct would deny it that.

### TM-102 — no humanised or relative formatting, at 1.0 or after
**2026-09-03, settling Q-3.** "3 hours ago" does not ship.

*Reasoning:* every product wants it and no two agree on the rounding policy or
the thresholds — is 90 minutes "an hour ago" or "2 hours ago"? — and the answer
is localisation-shaped (TM-024), which this library does not do. Shipping one
opinion means every consumer with a different one has to work around it.

`period_between` and the numeric parts are shipped instead: a program's own
two-line function then says what *that* program means, and is right for it.
This is a case where the library's job is to make the caller's version easy,
not to have a version.

### TM-103 — the dogfood consumers are `date` and `crontab`/`at`, in `nitpick-posix`
**2026-09-03, settling Q-4, with the author's amendment on location.** Two
programs, because they exercise different halves and the second half is where
date libraries are actually wrong:

- **`date`** exercises formatting and parsing breadth — every layout part,
  both directions, the round trip.
- **`crontab` / `at`** exercise **DST edges**: "the next run of this rule in
  this zone" is the question that produces a wrong answer twice a year, and no
  amount of round-trip testing finds it.

Both live in
[`nitpick-posix`](https://github.com/alternative-intelligence-cp/nitpick-posix),
not in this repository's `examples/`: consumers are real programs with their
own lifetimes and belong in the application workbench, and all three of these
are POSIX utilities, so they join the set rather than taking repositories of
their own.

### TM-104 — `date`'s `%` formatting is the utility's, not the library's
**2026-09-03. A consequence of TM-103 and TM-009 meeting, and the general shape
worth naming.**

POSIX `date` takes `+%Y-%m-%d`. TM-009 established that this library has **no
format-specifier language**, following D-053's removal of `printf` and its
explicit rejection of format specifiers as "a second mini-language purely to
save characters".

There is no conflict, and the resolution is the one to reuse everywhere:
**`date` parses the `%` grammar at run time and maps it onto this library's
typed layout.** The compatibility layer lives in the utility; the library stays
principled and is not asked to carry a syntax it rejected on purpose.

The contrast with `nitpick-regex`'s RX-102 is instructive and both are recorded
so the difference is visible: there, the standard requires a *capability* the
library structurally lacks, and the departure has to be stated. Here the
standard requires a *syntax*, and syntax is exactly what a compatibility layer
can absorb.

---

# The third batch — what the cycle 0.0.0 probes measured

Decisions forced by a probe rather than by a discussion. Each names the probe
that produced it, because the evidence is a file in this tree and a reader
should be able to re-run it.

### TM-105 — there is no checked narrowing, so every narrowing carries its own range check
**2026-09-03. Measured by `tests/probe/probe02b_narrow_unchecked.npk` and
`tests/probe/probe02c_narrow_refused.npk` against compiler commit `950bb1d`.**
This is cycle 0.0.0's first negative verdict and it changes library code that
has not been written yet, which is the whole point of running the probes first.

**What was assumed.** `SAFETY.md` S-15 and `TIME_MODEL.md` M-20 say that
calendar-scale nanosecond arithmetic "computes in `int128` and narrows with
`=>!` at a point where the value is known to fit", and `VERIFICATION.md` P-5
calls the `prove` at those sites "the single most valuable proof in the
library". Both sentences are compatible with two different worlds, and the plan
did not say which one it was written for: either `=>!` **checks** at run time
and traps when the value does not fit — in which case `prove` is a belt over a
brace and a missing range check costs a controlled stop — or it does not, in
which case the range check is the only thing there is.

**What is true.** It does not check. Two measurements, both committed:

- `=>!` from `int128` to `int64` at a value that does not fit **keeps the low
  64 bits and discards the rest, in silence** — no trap, no diagnostic, exit 0.
  Four shapes are pinned, and the third is the one to remember: **a positive
  `int128` narrows to a negative `int64`**, because what is discarded is
  everything above the destination's sign bit.
- The checked spelling `=>` at the same narrowing is **not** a runtime check
  either. It is refused where it is written, `NITPICK-TYPE-009`: *"`int128`
  does not fit in `int64`, so this conversion can lose information: the target
  is narrower than the source. Write `=>!` to accept that."*

So a narrowing conversion in this language is **refused at compile time, or
unchecked when it runs.** There is no third spelling. And the excellent
diagnostic above is itself the path a careless author takes to the silent
truncation: it names `=>!` as the way to proceed, which is correct, and says
nothing about the range check that must accompany it.

**The decision.** *Every narrowing conversion in `ntime` is preceded, on the
same path, by a runtime range check against the destination type's bounds, and
the check returns `ETimeValue`/`Overflow` rather than trapping.* The check is
**ordinary library code that must be written**. It is not a belt over a
language guarantee, because there is no language guarantee.

Stated as rules where the code will be written: `SAFETY.md` **S-15b** for the
arithmetic, and `SPAN_MODEL.md` **N-20b** for the `int128` sites §5 enumerates.
`tests/probe/probe02_int128.npk`'s `ns_add_checked` is the shape they require,
and it is committed so the shape is a file rather than a description.

**Why not rely on `prove`.** `VERIFICATION.md` P-5's `prove` is retained and is
still worth what it was worth — but until the compiler's cycle 1.5 makes
`prove` real it is a comment, and even afterwards it is a *static* obligation
discharged by a solver. A discharged proof and a runtime check answer different
questions: the proof says the narrowing cannot lose for any input the
precondition admits, and the check says what happens to a caller who violated
the precondition. A library whose public entry points take `int64` from a
caller it does not control needs the second regardless of the first.

**Why this is not a compiler defect and nothing is being worked around.**
`=>!` is *named* for being unchecked and `TYPE_REFERENCE.md` describes it that
way; the language is behaving as specified and D-210's trap covers plain
arithmetic, which is the case it was designed for. What was wrong was this
library's plan, which had read a guarantee into a cast that never offered one.
Correcting the plan is not a workaround.

*Alternatives declined:*

- **Rely on the trap.** There is none to rely on. This is the assumption the
  probe was written to test, and it failed.
- **Rely on `prove` alone.** It is a comment today and a static obligation
  afterwards; see above.
- **Forbid `int128` entirely and reshape the arithmetic to fit `int64`.**
  Nanoseconds across the ±9999-year range are 6.3 × 10²⁰ and `int64` holds
  9.2 × 10¹⁸ (`TIME_MODEL.md` §8), so the range does not fit and the
  reshaping would be a smaller supported range wearing a decision's clothes.
- **A helper that narrows and returns `Optional<int64>`.** Attractive, and it
  is what S-15b's rule amounts to in practice — but naming one helper here
  would settle the API shape of code no cycle has designed yet. The rule
  constrains every site; which function realises it is `src/`'s business, and
  0.0.4 decides it with `Vec<T>` and the other primitives.

### TM-106 — a `Vec<T>` over an owning `T` is emptied before its block is freed, and `exit 0` will not tell you otherwise
**2026-09-03. Measured by `tests/probe/probe06_generic_vec.npk`** against
compiler commit `950bb1d`.

**What was assumed.** `SAFETY.md` S-18 says growable storage is `Vec<T>`,
"whose block is `wild` and whose lifetime is its owner's scope; every `wild`
byte is released on every path, so `exit 0` never trips D-151". Cycle 0.0.4's
P-23 puts it more strongly: "every `Vec` has a `vec_free` and every scope that
made one calls it, **or `exit 0` traps under D-151**".

Both sentences are true of the **block**. Neither is true of the **elements**,
and the "so" in the first one is doing work it cannot do.

**What is true.** D-151 watches `wild` allocations. A `string`'s body is
**managed**, so a `Vec<string>` whose block is freed and whose elements are not
is a leak that **exits 0**. Measured at 2 000 000 iterations of {init, push one
35-byte string, free}:

| | peak RSS | exit |
|---|---:|---|
| block freed, elements orphaned | 125 184 KiB | **0** |
| elements moved out first, then the block freed | 0 KiB | 0 |

and, because a peak-RSS figure is arguable and an exit code is not, the same
pair under `ulimit -v 65536` — a 64 MiB address space:

| | exit |
|---|---|
| block freed, elements orphaned | **92 — `HeapOom`** |
| elements moved out first | **0** |

**The decision.** *Every `Vec<T>` instantiated at an owning `T` is emptied
before its block is freed, by moving each element into a scope that ends.* The
shape is ordinary code and is committed as `free_names` in probe 06:

```nitpick
int64:i = 0i64;
while (i < v.count) {
    string:owned = move(v.items[i]);   // dies at the bottom of this iteration
    i = i + 1i64;
}
v.count = 0i64;
```

**This is not a compiler defect and nothing is worked around.** A generic
`vec_free<T>` cannot do it: moving an element out needs a destination of type
`T`, and a generic function has no scope in which a bare `T` may simply die.
The language is behaving exactly as specified; what was wrong was this
library's reading of what `exit 0` proves.

**Three entries in cycle 0.0.4's API table silently carry this obligation** —
`vec_free`, `vec_clear` and `vec_truncate` all discard elements, and all three
of their stated postconditions speak only of `count`, `cap` and `items`. Each
needs an element-drop path for an owning `T`, or a stated restriction to
non-owning ones. `SAFETY.md` **S-18b** is the rule; 0.0.4 is where it is built.

**And the general lesson, which is bigger than `Vec`:** *`exit 0` proves no
`wild` allocation is live. It proves nothing about managed bodies.* Every
"the leak test exits 0, so nothing leaked" claim in this plan is a claim about
`wild` only, and a suite that tests owning containers needs a memory assertion
that D-151 does not provide — cycle 0.0.3's business.

*Alternatives declined:*

- **Make `Vec<T>`'s block managed rather than `wild`.** That changes B-12's
  shape away from the compiler's `List<T>`, which was chosen because it has
  been exercised across twenty-two families, and it would trade a stated
  obligation for an implicit one.
- **Restrict `Vec<T>` to non-owning `T`.** `Layout` holds `Vec<FmtPart>` (non-
  owning) but the zone name pool and any future string collection want the
  owning case, and forbidding it would push every such site back to a
  hand-written array — the ninety hand-written doubling sites D-209 exists to
  remove.
- **Say nothing and rely on review.** The measurement above is what review
  would have to catch, twice: once for the missing drop and once for the exit-0
  reasoning that hides it.

---

### TM-107 — an import's arm bill is its `fail` SITES plus its ARITHMETIC, and it is charged per module rather than per call
**2026-09-03. Measured by `tests/probe/probe11_failsafe_arms.npk` and its five
twins** against compiler commit `950bb1d`. The transcript with every exit code
is `tests/probe/probe11_arm_contract.txt`.

**What was assumed.** `SAFETY.md` S-4 publishes a table of what a consumer's
`failsafe` owes per imported module, and every cell in it is a count of **error
identities** — "nothing", "one arm", "two arms", "three arms". S-6 has a
conformance test generate that table and assert a program compiles "with
exactly the documented arms and no more".

**What is true.** The arm set REACH-002 requires is computed over **every
module in the program graph except the prelude** (`src/driver/pipeline.npk`'s
`rc0` loop), and it has two parts, only one of which is an identity:

1. **Identities**, from `fail`, `?!` and `!!!` **sites**. A `pub error:`
   declaration with no site arms nothing — probe 11f imports one and compiles
   with a floor-only `failsafe`. The charge arrives with the first `fail`.
2. **System arms**, from the *machinery any module's text contains*:
   `DivByZero` and `DivOverflow` wherever `/` or `%` appears, `IntOverflow`
   wherever plain-integer `+ - *` does, `OutOfBounds` wherever an index does —
   on top of the unconditional floor of `Unreachable`, `HeapOom`,
   `HeapBadRequest` and `WildLeak`, which probe 11d pins by compiling and
   running with exactly those four and nothing else.

**The measurement.** `probe11c_import_arm_cost.npk` contains no division, no
remainder, no index and no plain-integer arithmetic of its own; its `failsafe`
is `probe11d_floor_only.npk`'s, character for character, and 11d compiles and
runs at exit 0 with it. The only difference between the two files is one `use`
line and four calls. `npkc` exit 1, four diagnostics:

```
NITPICK-REACH-002 …: `failsafe` does not name `DivByZero`,   which can reach it (D-179)…
NITPICK-REACH-002 …: `failsafe` does not name `DivOverflow`, which can reach it (D-179)…
NITPICK-REACH-002 …: `failsafe` does not name `IntOverflow`, which can reach it (D-179)…
NITPICK-REACH-002 …: `failsafe` does not name `OutOfBounds`, which can reach it (D-179)…
```

**Four arms, from a module that declares no error at all.** `cal` divides by 4,
100, 400, 146097, 86400 and 1000000000, indexes the month tables, and adds, so
a consumer that imports it owes all four however pure its own text is.

**And the charge is levied by the IMPORT, not by the call.**
`probe11e_unused_import_refused.npk` imports the module that raises
`EProbeZone`, calls only its infallible half, and is still refused for the
missing arm. Module boundaries are the only granularity available; avoiding the
failing *function* buys nothing.

**The decision.** *`SAFETY.md` S-4's table states the **total** arm set per
import — identities and system arms together — and S-6's generator derives it
from `fail`/`?!`/`!!!` sites and from the arithmetic present in the imported
subgraph, never from `error:` declarations.* The table is published to
consumers as the bill; a bill that lists only identities understates every row
that imports arithmetic, and understates them unevenly — pure `core` adds
nothing, `cal` adds four.

**This is not a compiler defect and nothing is worked around.** `reach.npk`'s
own header states the direction: *"Over-approximation is the safe direction:
the walk may require an arm the backend's emitted guards never fire, never the
reverse."* Every divisor in `cal` is a nonzero literal (S-16) and every index
goes through S-17's checked accessor pair, so these are arms a correct `ntime`
can never enter. They are still arms the consumer must write, which makes them
a fact about the API rather than about the arithmetic.

**Two smaller facts the same probes pin**, both of which a generator would
otherwise get wrong:

- **A superset of the required arms is accepted.** `probe07_negative_div.npk`
  names `(OutOfBounds)` and contains no index expression, and compiles and runs
  at exit 0. So S-6's "and no more" cannot be enforced by the compiler; it is
  the harness's assertion, and without it a published table that overstates
  would never be caught by a build.
- **Both arm spellings work.** The bare `(EProbeZone)` satisfies the walk under
  a `use "…".*`, and the diagnostic recommends the qualified
  `probe11_arms_lib.EProbeZone`, which the walk matches by name pair with no
  resolution and no import at all.

**What is NOT yet measured, and where it lands.** These are `ntime`'s real
modules' numbers, and `src/` does not exist yet. S-4's table therefore carries
the *rule* now and its arithmetic column is filled at cycle 0.1, when `cal` is
written and the totals can be generated rather than predicted. Nothing is
guessed into the table in the meantime.

*Alternatives declined:*

- **Publish identities only and mention the system arms in prose.** The table
  is the thing a consumer copies; a caveat beside it is a caveat they compile
  without. The four arms are not optional and belong in the cell.
- **Restructure `cal` to avoid arming the system family.** It cannot be done —
  a calendar divides — and it would be a library contorted around a diagnostic
  rather than around a requirement.
- **Treat the over-approximation as a compiler defect and raise it.** It is the
  compiler's stated and deliberate design, written into `reach.npk`'s header,
  and the safe direction. Raising it would be asking for a less conservative
  analysis of trap reachability in a language whose whole proposition is that
  a trap is accounted for.

---

# The fourth batch — corrections the record forced

*Not measurements. Each of these is a sentence this repository had already
written, re-read against the compiler's source and found to promise more than
the language does.*

### TM-108 — the bounds check attaches to the type, so `Vec<T>` and `Bytes` are unchecked
**2026-09-03. Read out of the compiler's source** at commit `950bb1d`, against
the compiler's D-070. Nothing was compiled for this decision; it is a
documentation defect, not a measurement.

**What was written.** `SAFETY.md` §1 carried the row *"Array, slice and buffer
indexing is bounds-checked and traps | D-070 | A zone-table index out of range
is a crash, not a wrong offset."*

**The sentence was not false. It was narrow, and it was read as broad** — and
that distinction is the whole reason this decision exists rather than a one-line
fix. Taken literally it makes a true claim about arrays and slices, two of the
kinds the emitter actually guards. What it does is invite a reader to conclude
that *indexing* is checked in this language, and then to index a `Vec` or a
`Bytes` on the strength of it.

**What is true.** The compiler's `ExprIndexExpr` lowering
(`src/backend/ir/ir_expr.npk`) switches on the indexed object's type kind:
`TY_SLICE`, `TY_ARRAY` and `TY_SIMD` each call `emit_bounds_guard`;
`TY_POINTER` emits a `getelementptr` and nothing else; and there is **no
`TY_BUFFER` branch**. D-070 says so itself — its title is "`T[]` is a slice:
bounds live in the array type, **not the pointer type**", and its body gives the
slice as "where out-of-bounds detection actually comes from, and it is why
pointers do not need to carry it". `parse_type.npk`'s second header fact closes
it: qualifiers are not part of the type, so `wild T->:items` is a bare pointer
to the emitter.

**Three specific consequences, none of which the old row would have suggested:**

1. **`simd<T, N>` is guarded and nobody here knew it.** The row named three
   things and omitted one of the kinds that actually traps.
2. **`buffer` is named by the old row but reached by the pointer route.**
   `TYPE_REFERENCE.md` §23's own example is `buf.ptr[0i64]` — *"byte reads
   index the ptr"* — and `.ptr` is a `uint8->`. There is no slice view to reach
   instead: `buffer_bytes` sits under §23's "deliberately NOT landed".
3. **`Bytes`, not just `Vec`, is in the blast radius.** `BUILD.md` B-12 makes
   `Bytes` an owning byte sink over `buffer`, and every formatter writes into
   one. The library's two containers are both unchecked, and the specification
   said the opposite.

**The zone table, which is what the old row's example was about, still traps** —
S-19 makes the generated tables `fixed` module state, so they are `T[N]`. The
example was right by accident, and being right by accident is why the sentence
survived.

**The decision.** *The bounds check is a property of the indexed type, not of
indexing. `SAFETY.md` **S-17b** states the four kinds with a row each, says how
a `buffer` is reached, and records that `Vec<T>` and `Bytes` are unchecked; S-17's
accessor pair is promoted from tidiness to the library's only bounds check and
extended to `src/core/`; and the tree check that no `.items[` appears outside
`src/core/vec.npk` and no `.ptr[` outside `src/core/bytes.npk` goes on cycle
0.0.3's list.* Every accessor checks `0 <= i` as well as `i < count`, because an
index derived from a narrower signed field can be negative and `i < count`
accepts it.

**And the part that does not generalise.** There is **no compiler-prelude
`Vec<T>`**: no `struct:Vec` exists in the compiler's tree, and `lib/nvec.npk` is
D-200's small-vector tier over `simd<flt64, N>`, not a container. The shared
shape is a convention each library adopts from `List<T>`
(`src/frontend/list.npk`, `items` declared `wild T->` and commented "WILD,
DELIBERATELY"), which is what B-12 already says. So **this rule is a claim about
`ntime`'s `Vec` and `Bytes` and nothing else** — a sibling library that gives its
`Vec` a managed body or a slice field gets a different safety property, silently,
and a reader who carries S-17b across will be wrong with no diagnostic to tell
them.

*Alternatives declined:*

- **Correct the row and move on.** That is what the rule forbids, and it is how
  the sentence lasted this long. The row was cited in four repositories in the
  direction opposite to D-070's own title, and `check_refs.py` passed all four,
  because a wrong citation still resolves.
- **Call the old sentence false.** It is not, and calling it false invites a
  reader to distrust the rest of §1's table — which is otherwise sound. The
  useful diagnosis is "true about three named types, read as a general
  guarantee it never made", because that is the mistake that will recur.
- **Give `Vec<T>` a slice field so the language checks it.** It would work, and
  it would abandon B-12's shape — the compiler's `List<T>`, exercised across
  twenty-two families — to buy a check the accessor pair already owes. It would
  also make `Vec` unable to own its block.
- **Rely on cycle 1.5's `prove` obligations.** `VERIFICATION.md` P-5's `prove`
  is a comment until the compiler's 1.5 and a static obligation afterwards; it
  says nothing about what happens at run time to a caller who violated the
  precondition. Same argument as S-15b's.

---

### TM-109 — "a view is a parameter, never a return value" is a belt, and it is stricter than the language will be
> **SUPERSEDED IN PART by TM-110 (2026-09-04).** Its three-row table and its
> "no new diagnostic code" claim were read out of an unlanded plan and are
> wrong at the landed pin. The text below is left exactly as written, because
> it records what was believed on 2026-09-03; read TM-110 for what was
> measured. What survives unchanged: the house rule itself, and the reason it
> is kept as a belt.

**2026-09-03. Read out of the compiler's source and its written cycle 1.5.1b
plan** at commit `950bb1d`. Nothing was compiled for this decision.

**What was written.** This repository answered O-N9 with the house rule *"a
view is a parameter, never a return value"*, recorded in
`OPEN_QUESTIONS.md`'s Q-5 and in `tests/probe/defect/view_escape/README.md`,
and the author's ruling kept it as a belt rather than as the guarantee.

**Why it needs a decision rather than a note.** The rule is *one* sentence
covering *two* shapes, and it was written that way because at the time there
was no way to tell them apart — O-N9's six cases all root at a local. The
compiler's fix distinguishes them, so a later cycle reading the house rule
would take a strictness this library chose for a constraint the language
imposed, and would plan `src/fmt/` around a limit that is not there.

**What the compiler's fix actually does.** DEF-3 is the second commit of the
compiler's cycle 1.5.1b, proposed as its D-249: builtins gain a `Views` column
naming which argument's storage a result aliases (`string_bytes` its first,
`string_from_bytes` its pointer argument), and the escape analysis treats such
a call as a borrow **rooted where that argument is rooted** — as if `@` had
been written at the argument. Three consequences, each verified in the
compiler's own source rather than in a summary of it:

1. **A view of a local, returned, is refused.** As `string_bytes(local)` is
   today at exit 0 with no diagnostic.
2. **A view of a temporary, returned, is refused** — bind the intermediate
   first. And that same bind fixes a second, independent bug: the inner
   `string_concat` result is an unbound temporary passed as an argument and
   nothing frees it, the compiler's D-183 debt proposed as its D-246 and
   scheduled in the same subcycle.
3. **A view whose borrows are all rooted at a parameter, returned, stays
   legal** — and is legal *today*. `borrows_only_param_rooted`
   (`src/frontend/analysis/escape.npk`) is an existing second look taken before
   refusing, on the reasoning that a parameter's target lives in the caller or
   older, so each frame proves its own hop. It is the constructor pattern the
   compiler is built out of.

**The refusal is `NITPICK-BORROW-001`** — `BORROW_RETURNED` in
`src/frontend/analysis/analysis_codes.npk`, the same code a returned
`@`-borrow already gets. **DEF-3 adds no new diagnostic code**; its own plan
says `check_codes_tested` needs nothing new. This is recorded explicitly
because a plan that waits for a new code is waiting for nothing.

**The decision.** *`SAFETY.md` **S-22** carries the house rule, in the place
§1's borrow row already promised it, together with the statement that it is
deliberately stricter than the language will be and a three-row table of the
shapes DEF-3 distinguishes.* `meta/roadmap/0.4/README.md` — the cycle that
writes `src/fmt/` — carries the same warning where its planner will meet it. A
later cycle that finds `src/fmt/` wanting to return a view of its own parameter
is meeting the belt, and the question is whether to loosen S-22 by decision,
not whether the compiler permits it.

**What is deliberately NOT claimed.** Whether a view over a **locally allocated
`wild` block** may be returned — `string_from_bytes(buf, n)` where `buf` came
from `alloc` in this frame — is **not settled by anything on file**, and this
decision does not settle it. The compiler's plan lists
`string_from_bytes(local.ptr, local.len)` among the *new refusals*, and its
`wild_provenance` carve-out (`escape.npk`) belongs to the store rule (D-223,
`NITPICK-BORROW-011`) rather than to the return rule. So it is an open question
for the compiler, raised in `OPEN_QUESTIONS.md` under O-N9, and S-22 forbids it
meanwhile — which costs nothing, because no design in this repository returns
one.

*Alternatives declined:*

- **Write the loosening into S-22 now.** DEF-3 has not landed and this
  repository is pinned to a compiler that does not have it. A specification
  that describes an unlanded fix is a specification that is wrong for as long
  as the fix slips.
- **Drop the house rule once DEF-3 lands.** The rule costs this library
  nothing — `FORMAT_MODEL.md` already has parsers return a value and an offset
  — and `check_no_view_returns` is a cheaper thing to keep than an escape
  analysis is to re-verify at every re-pin.
- **Say only "the rule is conservative" without the table.** That is the
  sentence a later reader cannot act on. The three shapes are the content; the
  adjective is not.

---

## The re-pin batch — measured against `94874ce`

### TM-110 — the returned-view rule keys on the ROOT'S SHAPE, not on parameterhood; and DEF-3 does add a diagnostic code
**2026-09-04. Measured**, against pinned compiler `94874ce`, which carries
DEF-3 (the compiler's cycle 1.5.1b step 2, its D-249). **Supersedes TM-109 in
part.** Every claim below was produced by compiling a file, not by reading a
plan — which is the whole reason it differs from TM-109.

**Why this decision exists.** TM-109 was written on 2026-09-03 from the
compiler's source and its *written plan*, at a pin that did not have the fix.
It said so honestly — *"Nothing was compiled for this decision."* Two of its
claims did not survive measurement, and both would have shaped `src/fmt/`.

**What was measured.** `tests/probe/probe10_view_edges.npk` and its two
refusal twins, `tests/probe/probe09b_environ_view_returned.npk`, and the six
files of `tests/probe/defect/view_escape/` re-run at the new pin. The
transcripts are in `tests/probe/defect/view_escape/TRANSCRIPT.txt`, Part A.

**1. O-N9 is DISCHARGED.** Cases 3, 4 and 5 — a view of a local returned, in a
struct, and read after free — are now **refused `NITPICK-BORROW-001`**, the
same code and the same message cases 1 and 2 always got. Case 6, the shape
this library actually writes, still compiles and runs at exit 0. The ask
`view_escape/README.md` made was granted exactly.

**2. `NITPICK-BORROW-012` EXISTS, so DEF-3 DOES add a diagnostic code.** It is
`BORROW_VIEW_OF_TEMPORARY` in
`src/frontend/analysis/analysis_codes.npk`, and `probe10b` fires it:

> `NITPICK-BORROW-012 …:33:22: a view of a temporary: the value viewed here
> has no name and dies when its statement ends (D-246), so bind it first — the
> view is then a borrow of that binding, checked like any other (D-249)`

TM-109, `SAFETY.md` S-22, `OPEN_QUESTIONS.md`, `view_escape/README.md`,
`roadmap/0.4/README.md` and `roadmap/0.0/0.0.0.md` all stated the opposite,
because DEF-3's *plan* ended "`check_codes_tested` needs nothing new (no new
code)" and the plan was overtaken by its own step 2. **Why the code was needed
at all, which the plan had not foreseen:** DEF-3's other refusals are all
shaped like "as if `@` had been written at that argument" and so are
`BORROW-001`; but `@` of a temporary cannot be *spelled*, so no existing
code's text is true of it. It needed a root with no name, and that needed a
code of its own.

**3. The rule keys on the ROOT'S SHAPE, not on parameterhood.** This is the
correction that changes a plan. TM-109's third row said a returned view is
legal when its borrows are *rooted at a parameter*, and recorded a view over a
locally allocated `wild` block as an open sub-question the compiler had to
answer. **The sub-question is answered, and the answer is that it is legal.**

| Shape, returned out of its frame | Measured at `94874ce` | Evidence |
|---|---|---|
| a view of a **local** — `string_bytes(local)` | **refused** `NITPICK-BORROW-001` | `view_escape/case3`, `case4`, `case5` |
| a view of a **temporary** — `string_bytes(string_concat(a,b))` | **refused** `NITPICK-BORROW-012` | `probe10b` |
| a view of a **`move` parameter** | **refused** `NITPICK-BORROW-001` | `probe10c` |
| a view rooted at a plain **parameter** | **legal** | `probe10` §2, §3 |
| a view rooted at a **pointer-shaped binding** — a `wild` block from `alloc`, a `cstring`'s `.ptr`, a slice | **legal** | `probe10` §1, `probe09b` |

**Why one probe could not settle row 5, and why there are two.** `probe09b`
returns a view of a `cstring`'s `.ptr` and compiles — but its `cstring` comes
out of a `cstring[]` **parameter**, so the parameter-rooted reading and the
pointer-shaped reading both predict it compiles. `probe10` §1 removes the
confound: `blk` is a `wild int8->` from `alloc`, a local, with **no parameter
anywhere in its root chain**. It compiles. Parameterhood is therefore not the
rule; the root's shape is. The compiler states it in `escape.npk`'s own D-249
comment — a view whose place roots at a pointer-shaped binding *"aliases the
POINTEE, which lives wherever the pointer's provenance says"* — and
`view_is_frame_borrow` is the discriminator.

**A fourth row TM-109 did not have at all: a `move` parameter is not a
parameter for this purpose.** It is consumed at the call and dropped at the
callee's frame exit, so a view of it travels up into storage that frame just
freed. `vec_push<T>(Vec<T>->:v, move T:x)` already takes one (probe 06), so
this is not a hypothetical shape here.

**Three refinements from DEF-3's own whole-tree sweep, all exercised by
`probe10` and none of them in O-N9's six cases:** a view over `#ptr_add` looks
*through* to the pointer; a `for` over a range cannot carry a borrow whatever
its bound reads; and a struct literal is rooted where its **field values** are.

**The decision.** *`SAFETY.md` **S-22** keeps the house rule and replaces its
three-row table with the five measured rows above, marked as measured rather
than predicted. The rule stays a **belt**: it is still stricter than the
language, it still costs this library nothing, and `check_no_view_returns`
stays on 0.0.3's list.* Every site that said DEF-3 adds no new diagnostic code
is corrected in this commit.

**Why keep the belt now that the language enforces the rule.** Because what
the language now enforces is *narrower* than what S-22 forbids: rows 4 and 5
are legal, and S-22 forbids them anyway. A `src/fmt/` that returns a view of
its own parameter would compile and would be correct — and would also make
every future re-pin a re-verification of somebody else's escape analysis. The
belt costs nothing here (`FORMAT_MODEL.md` already returns a value and an
offset), so it stays. **What changes is that a later cycle wanting to loosen
it now knows exactly what it is loosening towards, and that the answer is a
decision rather than a compiler question.**

*Alternatives declined:*

- **Rewrite TM-109 rather than supersede it.** Against this file's own rule,
  and it would erase the more useful record: TM-109 is a worked example of a
  careful reading of an unlanded plan being wrong in two places. That is worth
  keeping precisely because the reading was competent.
- **Drop S-22 now that DEF-3 has landed.** Rows 1–3 are refused by the
  compiler, so the belt's remaining work is rows 4 and 5 — small, but free.
  Dropping it buys nothing and spends a re-verification at every re-pin.
- **Record the pointer-shaped row from `escape.npk`'s comment alone.** A
  comment is a claim about a code path; it is not evidence the path is
  reached. `probe10` §1 is four lines and settles it, and this ecosystem has
  been wrong often enough reading source without compiling.

### TM-111 — the payload-enum derives are fixed, and `case2`'s own header nearly hid it
**2026-09-04. Measured**, against pinned compiler `94874ce`, which carries the
compiler's DEF-4 as widened and ratified in its **D-250** (cycle 1.5.1b step
3b). **O-N10 is discharged.**

**What was measured**, running `tests/probe/defect/derive_payload_enum/`'s
three cases and `tests/probe/probe05b_derive_eq_refused.npk` through the full
four-step recipe:

| File | Was, at `950bb1d` | Now, at `94874ce` |
|---|---|---|
| `case1_eq_refused.npk` | `NITPICK-TYPE-034` inside `<derived-1>` | **compiles, runs, exit 0** |
| `probe05b_derive_eq_refused.npk` | `NITPICK-TYPE-034` | **compiles, runs, exit 0** |
| `case2_ord_ignores_payload.npk` | exit **221** — `Equal`, `Equal`, `Less` | exit **121** — `Less`, `Equal`, `Less` |
| `case3_hash_and_clone.npk` | exit 107 | exit 107, unchanged |

**A derive that compiles is not a derive that is right, so the quiet half was
checked separately.** `case1` only asserts that `#[derive(Eq)]` *builds*; it
never compares anything. A scratch program over the same declaration confirmed
the derived `eq` **distinguishes payloads**: `Literal(7).eq(Literal(9))` is
false, `Literal(7).eq(Literal(7))` is true, and `Literal(7).eq(Year4)` is
false. Without that check this decision would have rested on the same kind of
green O-N10 was originally about — a derive that is accepted and wrong.

**`case2`'s header contradicts itself, and the contradiction pointed the wrong
way.** Its line 3 says *"When O-N10 closes, the expected exit becomes 321 —
`Less`, `Equal`, `Less`"*. Those words encode as **121**, not 321: the file's
own legend is `1=Less 2=Equal 3=Greater` and the digits are `ab`, `aa`, `ac`.
The measured value is 121 — exactly what the words predict and not what the
number predicts. **So the committed prediction of the fix was itself wrong by
one digit, and a reader comparing 121 against 321 would have concluded the fix
was broken.** The number was a transcription slip on 2026-09-03; the words
were right.

**The decision.** *The four files' `expect-` headers are corrected to the
measured values in this commit, each with a dated note of what it said before
— never a silent edit. `case1_eq_refused.npk` and
`probe05b_derive_eq_refused.npk` change from `expect-error` to `expect-exit`,
and both stop being defect reproductions and become regression cases, which is
what their own headers said would happen when O-N10 closed.*

*Alternatives declined:*

- **Leave the headers and note the change in the record only.** A committed
  `expect-error: NITPICK-TYPE-034` on a file that compiles is a lie the 0.0.2
  harness will read as a plan. The headers are machine-facing.
- **Delete the two defect files now that the defect is gone.** They are the
  regression cases; deleting them is how the bug comes back.

### TM-112 — `main` without `failsafe` is refused, and the arm counts are FOUR and SIX
**2026-09-04. Measured**, against pinned compiler `94874ce`, which carries the
compiler's **DEF-5** (cycle 1.5.1b step 1b). **O-N11 is discharged.**

**The ask was granted in full, including the part that was a stretch.** O-N11
asked for a refusal naming D-013 and the file, *and* — because `reach_settle`
had just computed the set at the line where it returned early — for the
diagnostic to **list the arms the absent handler would owe**. It does:

> `NITPICK-REACH-003 …:30:1: `main` without `failsafe` (D-013): an executable
> supplies exactly one handler, the trap route calls it by name, and this
> program's would have to name every error that can reach it — 4 identities:
> Unreachable, HeapOom, HeapBadRequest, WildLeak — with `(*)` beneath them but
> not in for them (D-179)`

**The counts, measured rather than relayed.** A board carried **six** for
`case1`, from the compiler session's message. It is **four**.

| File | Identities owed | Which |
|---|---:|---|
| `case1_no_failsafe.npk` | **4** | `Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak` |
| `case3_arm_contract_evaded.npk` | **6** | the four, plus `probe11_arms_lib.EProbeZone` and `IntOverflow` |

`case1` has no import, no arithmetic and no allocation, so its bill is exactly
S-4b's unconditional floor — which is `probe11d_floor_only.npk`'s measured
result, arrived at independently. **The six was real and belonged to the other
file**, which imports the raiser and subtracts. This is a small thing recorded
at length because it is the third time in this subcycle a number was carried
between documents and attached to the wrong subject.

**S-4b is confirmed, not amended.** The floor it states, measured in 0.0.0 from
the *positive* direction by `probe11d_floor_only.npk`, is now confirmed from
the *negative* direction by a compiler that itemises the bill in a refusal.
Two independent instruments, same four names.

**The control still holds, and it is what makes REACH-003 the right check.**
An ordinary library module with neither `main` nor `failsafe`
(`tests/probe/support/probe11_arms_lib.npk`) is still accepted at exit 0. The
refusal is asked only of a root that declares `main`, which is precisely the
join O-N11 said `npkc` was failing to make.

**What does NOT change.** Cycle 0.0.3's harness must still not read `npkc`
exit 0 as "well-formed", and still gains its extra selfcheck case. That
constraint was *surfaced* by O-N11 but does not depend on it: `npkc` exit 0 is
not a claim about the IR, which is why the `llc` leg exists in the recipe at
all. Removing the leg because this defect is fixed would be the wrong lesson.

**The decision.** *Both transcripts are re-recorded in this commit as a Part A
(the re-recording at `94874ce`) above a Part B (the 2026-09-03 original, kept
verbatim), so the pair is readable as a before and after rather than as a
replacement.*

*Alternatives declined:*

- **Overwrite the transcripts with the new run.** A transcript claiming to be
  verbatim must show where it was touched. The defect reproduction is the
  evidence O-N11 was real, and it is not re-creatable at this pin.
- **Write the four/six counts into `SAFETY.md` §2's table.** S-4b already says
  the totals column is generated at cycle 0.1 from measurement, and these are
  two probe programs rather than the library. Nothing is guessed into it here.
