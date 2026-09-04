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
