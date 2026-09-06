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

---

### TM-113 — `List<T>` moved into the prelude and became OWNING, so `Vec<T>`'s divergence from it widened
**2026-09-05. Read out of the compiler's source at the pinned commit
`0dfddac`**, not out of its working tree, which had already moved on to
`daa5057`. Nothing was compiled for this decision; it is a documentation
defect, like TM-108 whose paragraph it corrects.

**What was written.** Four documents and one probe cited `List<T>` as living at
the compiler's `src/frontend/list.npk`, and three of them quoted a comment on
its `items` field: *"WILD, DELIBERATELY"*.

**What is true at the pin, with the denominator stated.**

| Claim | Measured | How |
|---|---|---|
| `src/frontend/list.npk` exists | **no** | `git cat-file -e 0dfddac:src/frontend/list.npk` → fatal, exit 128 |
| `List<T>` is in the prelude | **yes** | `pub struct:List<T>` at `src/prelude/prelude.npk:2078` |
| `list_init<T>` still exists | **yes** | `pub func:list_init<T>` at `src/prelude/prelude.npk:2087`, floor-of-one intact, same reason in its own comment |
| *"WILD, DELIBERATELY"* appears | **0 times in 607 `.npk`** | `git grep -n 'WILD, DELIBERATELY' 0dfddac -- '*.npk'` → exit 1, 0 lines |
| `struct:Vec` appears | **0 times in 607 `.npk`** | `git grep -n 'struct:Vec' 0dfddac -- '*.npk'` → exit 1, 0 lines |

So one half of S-17b's nuance — *there is no compiler-prelude `Vec<T>`* — is
**re-confirmed**, and the other half was resting on a path and a quotation that
no longer exist. D-239 is the move; the prelude's own comment gives the reason
(the snapshot could not carry a prelude that declared it until D-205).

**The part that is not bookkeeping, and it is the reason this is a decision
rather than a find-and-replace.** The prelude's `List<T>` is now
**compiler-known and OWNING** (the compiler's D-247): the layout marks it
owning, and *a generated drop releases its `count` elements through `T`'s drop
and hands the block back*. `ntime`'s `Vec<T>` is an ordinary struct and gets
none of that. The two types still share a layout — three fields, `wild T->`
first — and they no longer share a lifetime story at all.

**Which makes S-17b's warning stronger rather than weaker.** It already said a
sibling library spelling its `Vec` differently gets a different safety property
with no diagnostic. The same is now true of the *compiler's own* `List<T>`, in
the opposite direction: a reader reasoning "our `Vec` is the compiler's `List`,
so its elements are handled" gets TM-106 exactly backwards. `ntime` owns the
bounds obligation (S-17b) **and** the element-lifetime obligation (TM-106), and
the second is the one the move made easier to lose.

**The decision.** *`SAFETY.md`'s S-17b nuance paragraph is amended in this
commit: the dead path and the vanished quotation are removed, the prelude
location and D-247's ownership are stated, and the measurement above is what
the paragraph now rests on. `tests/probe/probe06_generic_vec.npk`'s three
citations (lines 14, 92 and 107 as they stood) are corrected in place, because
they are comments. `meta/roadmap/0.0/README.md`'s live checklist line is
corrected.*

**Two sites are deliberately NOT corrected**, and this decision is where a
grep for the dead path is meant to land:

- **`meta/DECISIONS.md:884`, inside TM-108.** A settled decision's text is
  never rewritten (`CLAUDE.md`; the compiler's D-085/D-202 pattern). TM-108's
  reasoning is about a sentence that was *narrow and read as broad*, and its
  citation was true when it was written.
- **`meta/roadmap/0.0/0.0.0.md:1350`**, a closed subcycle's execution record.
  A record says what was known then. Rewriting it would destroy the only
  evidence of what 0.0.0 actually had in front of it.

*Alternatives declined:*

- **Edit all seven sites and record nothing.** The stale path was found because
  a sweep was run with its denominator stated; the *quotation* was found only
  because the sweep was re-run against the compiler at the pin rather than
  against its working tree. Neither instrument survives as a habit unless the
  finding is written down.
- **Amend TM-108 in place.** It is settled. This supersedes the citation, not
  the decision — TM-108's conclusion (the bounds check attaches to the type) is
  untouched and is re-confirmed by the `struct:Vec` row above.
- **Say only "the file moved".** That is the small half. The ownership change
  is the half that can make a later reader wrong about memory.

---

### TM-114 — `BUILD.md` §3's stage table was incomplete, and its `accept` row is the O-N11 shape
**2026-09-05. Read out of the compiler's `BUILD_REFERENCE.md` §7.1 at pin
`0dfddac`**, while writing the manifest's first `[[test]]` entries (0.0.1 step
3). Found because the subcycle's own step 3 and its own acceptance criterion
disagreed, and the specification was consulted to settle which was right.

**What was written.** `BUILD.md` §3 presented a seven-row stage table and said
the harness *"mirrors the compiler's stage vocabulary (`BUILD_REFERENCE.md`
§7.1)"*. It assigned `tests/conformance/` to the **`accept`** stage, which it
defined as *"accepted by `tools/check` in silence"*.

**What is true.** The compiler's §7.1 has **eleven** stages, and the one that is
missing from ours is the **default**: `compile`, held to a `kind` —

> `positive` **compiles, links, runs, and exits with the expected code**;
> `negative` fails to compile, emitting exactly the expected diagnostics;
> `diagnostic` compiles, emitting exactly the expected warnings

and its own example entry is, verbatim, `name = "conformance"`,
`stage = "compile"`, `kind = "positive"`, `path = "tests/conformance"`. Also
absent from ours: `resolve`, `runtime`, `verify` and `cost`.

**Why this is a defect and not a simplification.** 0.0.1's acceptance criterion
says `tests/conformance/import.npk` *"compiles, links, runs, exits 0"* — which
is `compile`/`positive` exactly, and is **strictly more** than `accept`'s
"accepted in silence". A conformance suite judged by acceptance alone is
precisely the shape O-N11 walked through: `npkc` accepted a root with `main`
and no `failsafe` at exit 0, and only the *link* refused it. So the weaker
reading was not merely less thorough — it was the one this repository already
has a defect reproduction for, sitting in
`tests/probe/defect/missing_failsafe/`.

**The decision.** *`BUILD.md` §3's table gains the `compile` row with its three
kinds and a note that four further stages exist upstream and are not used here
yet; `tests/conformance/` is `compile`/`positive`, and the `accept` row is kept
with the reason it is NOT what this library's conformance suite uses. The
manifest's two entries are written accordingly in this commit, and the
`conformance` entry carries the O-N11 reason next to it.*

*Alternatives declined:*

- **Use `accept` because §3 said so.** The specification is the authority over
  the code, not over the compiler it claims to mirror. Where our document
  disagrees with the thing it says it mirrors, ours is what is wrong.
- **Copy all eleven rows.** A stage this library has no way to run is a dormant
  row, and the audit hunts those. The four absent ones are named in a sentence
  and will be added by the cycle that can honour them.
- **Leave the plan's word `compile` as the discrepancy and use it silently.**
  The plan happened to be right, but nobody could have known that from these
  documents — which is the whole finding.

---

### TM-115 — a sweep states its denominator, and the tree is partitioned so nothing falls between buckets
**2026-09-05. Measured**, and prompted by a gap that had been open for two days
in the files least able to afford it.

**The gap.** Three tracked `.npk` carried **no `expect-` marker at all** —
`tests/probe/defect/missing_failsafe/case1`, `case2` and `case3`. Not a wrong
expectation: none. The expect-header sweep run at the 2026-09-04 re-pin covered
**36 of 42** tracked `.npk`; three of the six uncovered are support libraries
that correctly have none, and these three were the real gap.

**Why those three and not some harmless others.** They are the files whose
expected behaviour *completely changed* on 2026-09-04, when O-N11 was fixed and
an `npkc` `NITPICK-REACH-003` refusal replaced an `llc` failure. The general
finding they produced is that **a defect reproduction's header goes stale the
day its defect is fixed**, and that the sweep is the check for it. These three
sat outside the sweep — so the check could not see the files it most needed to.

**And the reason it could not be noticed: a sweep that matches nothing and a
sweep that ran over nothing print the same thing.** "Swept, no violations" and
"swept nothing" are byte-identical outputs. The same shape bit this workbench
at the root, where `grep` honours ignore files and the root `.gitignore` opens
with `/*/`, so a sweep from there sees none of the library checkouts and reports
silence.

**The decision.** *`harness/run.py` gains `check_expect_headers`, and it states
its denominator on every run, green or red. Every `.npk` in the tree is placed
in exactly one of three buckets and the partition is asserted:*

| Bucket | Judged by | Today |
|---|---|---:|
| `src/**` | *"it compiles"* — check 2. A library module has no exit code and no diagnostic to expect | 7 |
| `tests/**` | a marker in its own header (B-5), or a NAMED entry in `EXPECT_EXEMPT` with its reason | 43 |
| anywhere else | **nothing — and that is a failure** | 0 |

*The three `missing_failsafe` cases are given their headers in this commit,
verified against the compiler rather than written from the transcript:
`case1` `expect-error: NITPICK-REACH-003` at `62:1`, `case3` the same at
`58:1`, `case2` `expect-exit: 0`. The count moves from 36 of 42 to 40 headered
+ 3 exempt of 43 under `tests/`, and the exemptions are the three
`tests/probe/support/` modules, each with the reason written beside it.*

**The exemption list is diffed in both directions.** An exemption naming a file
that is not in the tree is itself a failure — because an exemption that
outlives its file is how a later file with the same name gets excused without
anyone deciding to excuse it. That is the second list, and *"every hole was
found by a check that diffs two lists, and none by a test"*.

**Commissioned, positive and negative**, before it was trusted: green over the
real tree; red when a header is removed (the exact gap that existed); red on a
stale exemption; red on a `.npk` in neither bucket.

*Alternatives declined:*

- **Fix the three headers and stop.** That fixes the instance and leaves the
  instrument blind, which is how the instance happened.
- **Require a marker on `src/**` too.** A library module has nothing to
  expect; the check would be satisfied by a marker that means nothing, which is
  worse than no marker. Its expectation is that it compiles, and check 2 is it.
- **Exempt `src/**` as a pattern rather than partition the tree.** A pattern
  exemption silently excuses anything later placed there. The partition makes
  an unowned file a *finding*, which is the property that was missing.
- **Defer it to 0.0.3 with the other tree checks.** The deferral is what left
  the gap open; and the sweep needs no harness, only a denominator.

---

### TM-116 — a probe's precondition gets a dedicated exit code, or it is indistinguishable from a verdict
**2026-09-05. Measured** at pin `0dfddac`, on both files, across six values of
`TZ`.

**The defect.** `tests/probe/probe09b_environ_view_returned.npk` needs
`TZ=Europe/Kyiv` exported. Its header said only `expect-exit: 0`. Run bare it
exited **10** — which is its own `string_byte_length(hit) != 14`, a substantive
code from its own map meaning *the returned view is not the entry*. That is the
single question the probe exists to ask, so an unmet precondition and a real
failure of the language were the same signal.

**And the file held up as the model had a quieter version of the same defect.**
`probe09_environ_split.npk` documents its precondition and exits a dedicated
**30** when `TZ` is absent — which is right, and is why it was the model. But
`TZ` **present and set to something else** landed on its substantive codes.
Measured before the fix:

| `TZ` | probe09 | probe09b |
|---|---:|---:|
| unset | 30 *(dedicated)* | **10** *(substantive)* |
| `Europe/Kyiv` | 0 | 0 |
| `Europe/Kiev` — the old IANA spelling | **0** | **0** |
| `Europe/KIEV` | **34** *(substantive)* | **13** *(substantive)* |
| `UTC` | **31** *(substantive)* | **10** *(substantive)* |
| `America/New_York` | **31** *(substantive)* | **10** *(substantive)* |

**The `Europe/Kiev` row is the sharp one.** Both probes exited **0** under the
*wrong zone name*, because everything either one checks — an 11-byte value,
`'E'` at the front, `'u'` next, `'v'` at the end, `'/'` at offset 6, and for 09b
a 14-byte entry with `'E'` at index 3 and `'v'` at index 13 — is equally true
of `Kiev` and `Kyiv`. So probe09's assertion was weaker than its name implied,
and nothing in either file would ever have said so.

*(A claim reached this subcycle that `TZ=Europe/KIEV` still exited 0. It does
not: probe09 exits **34**, because `'V'` is not `'v'`. The underlying point was
right and the spelling that demonstrates it is the mixed-case `Europe/Kiev`.
Recorded because the difference is the whole reason claims get re-run.)*

**The decision.** *A probe with a precondition states it in its header and exits
a code no substantive assertion in that file uses. Both files now use the same
two numbers for the same two conditions, so the pair reads as one instrument:*

- **30** — the `TZ=` entry is **absent** from the environment.
- **39** — it is **present and is not `TZ=Europe/Kyiv`**.

*In `probe09b` the precondition is checked by `tz_index`, a helper that returns
an INDEX and never a view — deliberately, so that the check cannot be answered
by the very mechanism under test. In `probe09` the check sits between locating
`TZ` and the first assertion about it, so 31…35 are now verdicts. Measured
after the fix: both files give 30 unset, 0 at `Europe/Kyiv`, and 39 at
`Europe/KIEV`, `Europe/Kiev`, `UTC` and `America/New_York`.*

**What this does not fix, and it is 0.0.2's.** `// expect-exit: 0` plus a prose
`PRECONDITION:` line is not something a runner can honour: `BUILD.md` B-5's
marker grammar has `// argv:` and no way to state an environment variable, so
the harness will run both probes bare and see 30. Two probes now depend on
that being resolved, and the resolution is a marker, not a wrapper script.

*Alternatives declined:*

- **Give `probe09b` exit 30 only.** It would leave `TZ=UTC` landing on 10 —
  which is the case that actually occurs, since a machine with `TZ` set to
  something is far commoner than one with it unset.
- **Make the probes accept any zone name.** They would then assert nothing
  about the split, which is what they are for.
- **Check the precondition with `tz_entry`, the function under test.** It
  reintroduces the defect in one line: a failed experiment and an unmet
  precondition become the same event again.
- **Widen the check to accept `Europe/Kiev` as an alias.** The probe is not
  about zone naming; it is about `environ()`. An alias would be a second thing
  the file quietly tolerates.

---

## The harness batch — cycle 0.0.2, measured against pin `0dfddac`

Five decisions, all produced by building the runner `BUILD.md` describes and
finding where the description and the compiler disagree. Four of the five
correct something this repository had already written down.

### TM-117 — there is no separate compilation, so a program links with the runtime and nothing else
**2026-09-05. Measured** at pin `0dfddac`. **Corrects `meta/roadmap/0.0/0.0.2.md`
P-16 and its §2 pipeline diagram.**

**What was written.** 0.0.2's plan drew the last step of the pipeline as
`ld.lld(p.o, ntime.o, npkrt.o)`, and P-16 said *"one build of the library per
run, reused by every program: the library compiles once to an object; each test
program compiles and links against it. A per-test rebuild is the difference
between a two-minute suite and a forty-minute one."*

**What `npkc` actually does.** Its usage line is
`npkc <root.npk> [-o out.ll] [--obligations DIR] [--elide …] [--extra-picky=…]`
— one root in, one `.ll` out, and **no flag that emits a translation unit
separately**. It compiles the whole module graph the root reaches, the prelude
included, into that one file. Measured on the smallest pair in this tree:

    npkc tests/probe/support/probe11_arms_lib.npk   ->  608 `define`s
    npkc tests/probe/probe11_failsafe_arms.npk      ->  613 `define`s

and 608 of the 613 are the SAME names, including the library's own
`npk.probe11_arms_lib.zone_count` and `npk.probe11_arms_lib.zone_offset_strict`.
So the importing program's object already contains everything the imported
module's object contains.

**The link the plan drew is an error, and it was run rather than argued:**

    ld.lld -static p11.o npkrt.o           -> exit 0
    ld.lld -static p11.o armslib.o npkrt.o -> exit 1, 121 lines of diagnostic,
        first: duplicate symbol: npk.prelude.int8:ToString.to_string

**The decision.** *A `program`-stage test links its own object with `npkrt.o`
and nothing else. The library is still built exactly once per run — emitted,
optimised, assembled and symbol-scanned — but as a **check in its own right**
rather than as an input to anything, and `build/ntime.o` is never linked into a
test.*

**P-16's reason survives its remedy, so the cost is measured instead of
avoided.** Every program re-emits the prelude, and at 0.0.2's twenty-seven units
the suite takes **65 s**, about 2.6 s per program with both legs (the two
2 000 000-iteration container probes and the 30 000-row table probe are 4.0–4.3 s
each). `run.py` prints the per-unit and total wall time on every run, so the day
this becomes a problem it is a number rather than a feeling. **The remedy, if
one is ever needed, belongs to `npkc` and not to this harness** — a library
that reshaped its module graph to dodge a compiler limitation is exactly what
`CLAUDE.md`'s "never work around a compiler defect" forbids, and this is a
missing feature rather than a defect.

*Alternatives declined:*

- **Link the library object anyway and pass `--allow-multiple-definition`.**
  It links, and it silently picks one of two copies of every prelude function.
  A suite whose correctness depends on which copy the linker chose is worse
  than a slow one.
- **Give each test its own module graph that excludes the library.** That is
  what already happens; the point of the entry was to test the library.
- **Wait for `npkg`.** O-N1/O-B1 are not on the compiler's 1.5 or 1.6 map, and
  a harness that cannot run until they land is not a harness.

### TM-118 — the runtime allowlist is derived from `npkrt.o`, not from `npkrt.ll`, and the scan cannot see a syscall
**2026-09-05. Measured** at pin `0dfddac`. **Corrects `BUILD.md` B-2 and
`meta/roadmap/0.0/0.0.2.md` P-14.**

**What was written.** Both said the undefined-symbol scan's allowlist is *"every
`define` in `runtime/npkrt.ll` plus `main`"*.

**That set is wrong in both directions.** Read at the compiler's `0dfddac`
against the `npkrt.o` this workbench actually links:

| | count |
|---|---:|
| `define`s in `runtime/npkrt.ll` | 166 |
| global defined symbols in `npkrt.o` | 111 |
| in the `.ll`, **not** global in the `.o` | **56** |
| global in the `.o`, **not** a `define` in the `.ll` | **2** |

The 56 are `internal` linkage — `npk_heap_init`, `npk_small_alloc`,
`npk_udivmod128` and 53 more — so they become local symbols the linker will not
resolve for anybody. **An allowlist holding them excuses a reference that then
fails at link**, which turns a build error into a link error a long way from its
cause. The 2 are `_start` and `npk_clone_raw`, which come from `module asm`
blocks (there are 28 in the file) and are invisible to any scan of `define`
lines; **an allowlist missing them fails a reference that would have linked.**

**And "plus `main`" is not enough either.** `src/lib.npk`'s object legitimately
references `@npk_failsafe`: `npkc` emits the prelude's trap paths into every
root, and the handler is the *program's* to supply. The first run of this scan
failed the library build on exactly that.

**The decision.** *The allowlist is derived from `$NPKRT`'s own ELF symbol
table, in two halves and both derived: what the runtime **provides** (its global
defined symbols) union what the runtime itself **requires** of the program (its
own undefined symbols, which are `main` and `npk_failsafe`). 113 symbols at this
pin. Nothing is written down, so nothing goes stale, and the list cannot
disagree with what the linker will accept because it is read from the artefact
the linker is given.*

**AND WHAT THE SCAN CANNOT SEE, STATED SO IT IS NOT CITED AS SOMETHING IT IS
NOT.** `npk_sys6` is the runtime's own generic syscall trampoline and is
therefore **in the allowlist by construction**, so a module that issues a raw
syscall and one that does not have **identical undefined sets**. This is
`nitpick-regex`'s RX-120 — measured there as a symbol diff coming out empty, 29
symbols each way — and it reproduces here: an `ntime` program's undefined set is
**29** symbols and `npk_sys6` is one of them whether or not anything calls it.
**A green symbol scan is not a purity result.** B-2's claim is "no C, ever", and
that is the whole of what it supports; `check_purity` (`TESTING.md` §2,
`SAFETY.md` S-10) is a **source-level** ban list over `src/` outside `src/host/`
and is the only thing that answers "did this module touch the kernel". It is
cycle 0.0.3's.

**The scan has been seen to fail.** Commissioned by hand at 0.0.2 against an
`npkc` wrapper that renamed one call target in the emitted IR: the run went red
at the library build and again at the program, naming
`ntime_c_helper_that_does_not_exist`, exit 1. The transcript is in
`meta/roadmap/0.0/0.0.2.md`.

*Alternatives declined:*

- **Read `runtime/npkrt.ll` and filter out `internal`.** It would give the
  right 111 and still miss the two `module asm` symbols, and it makes this
  harness depend on a path inside the **compiler's** repository — which B-10
  forbids for source and which the toolchain pin deliberately does not provide.
- **Write the list down and check it in.** P-14's own argument against itself:
  a written list goes stale the first time the floor gains a symbol, and the
  floor gained two between what the `.ll` shows and what the object provides.
- **Spawn `llvm-readelf` or `nm`.** A fourth tool outside the `[toolchain]`
  pin, whose text output nothing checks, under a rule that is law. P-13 already
  declined it and was right.
- **Claim the scan covers purity, since a syscall is rare.** It is exactly the
  claim RX-120 was raised to stop.

### TM-119 — a `program`-stage entry dispatches on the file's own header, which is a deliberate divergence from `npkg`'s `kind`
**2026-09-05. Settles O-X7.**

**The measurement, re-taken here rather than carried.** `tests/probe/*.npk` —
the plain non-recursive glob a `path` entry selects — is **26** files: **19**
carrying `// expect-exit:`, **7** carrying `// expect-error:`, none carrying
both, none carrying neither. The seven are `probe02c_narrow_refused`,
`probe02d_wide_literal_refused`, `probe10b_view_of_temporary_refused`,
`probe10c_view_of_move_param_refused`, `probe11b_arm_omitted_refused`,
`probe11c_import_arm_cost` and `probe11e_unused_import_refused`. A `[[test]]`
selects by **directory** and `kind` is per entry, so one entry cannot be true
about both halves.

**The decision.** *Within a `program`-stage entry the runner dispatches per
file, on the file's own header:*

- ***`expect-error:` present*** *— a refusal member. `npkc` must fail, and the
  **set** of codes it reports must **equal** the set the header names (B-7,
  D-237). Never assembled, never linked, never run.*
- ***`expect-exit:` present*** *— a run member. Emitted, scanned, assembled,
  linked and run at -O0, then again through `opt -O2` (B-3).*
- ***both*** *— a failure; they say contradictory things.*
- ***neither*** *— a failure and **not a skip**. It is the state the three*
  `missing_failsafe` *cases were in for two days (TM-115).*

**This is an extension of a mechanism the compiler's runner already has**, not
a new one: it already applies per-file membership rules inside a stage (*"a
`resolve`/`check` file with no `expect-error` is a fixture another file imports
and is skipped; a `compile`/`program` file some other file in its suite imports
is skipped"*). Ours differs in refusing rather than skipping, because a skip is
how a suite reports green while checking nothing.

**The cost, stated because it is the argument against.** `BUILD.md` §3 opens by
saying the harness mirrors the compiler's stage vocabulary *"so the eventual
move to `npkg` is a change of runner and not of suite"*, and this is a
divergence from that. It is written into `BUILD.md` §3 as **B-4c** so the day
`npkg` can build a library (O-N1, O-B1) the migration is a known item rather
than a discovery: either `npkg` grows the same rule, or the seven files move to
a directory of their own.

**It found something on its first run.** `probe02d_wide_literal_refused.npk`
reports **two** codes, `NITPICK-LEX-004` and `NITPICK-PARSE-002`; its prose said
in as many words that *"a harness entry for this file expects BOTH"* and its
header named only the first. The file that exists to state D-237's rule was the
file that broke it. Corrected in this commit.

*Alternatives declined:*

- **Move the seven into `tests/probe/refused/`.** It fits the schema exactly
  and needs no divergence — and it churns paths that `0.0.0.md`,
  `tests/probe/README.md`, `nitpick.toml` and several decisions cite by name,
  to buy conformance with a tool that cannot build this library and is not
  scheduled to. If `npkg` ever declines to grow the rule, this is the fallback
  and it stays cheap.
- **A second `[[test]]` entry with a `files` key.** The schema has no such key
  and `npkg` refuses a key the schema lacks, so the manifest would stop being
  a manifest.
- **Let the `probe` entry cover the nineteen and leave the seven to no
  entry.** Seven files no check owns, which is TM-115's failure exactly.

### TM-120 — a test states its environment in its header, and the harness constructs that environment rather than inheriting one
**2026-09-05. Measured** at pin `0dfddac`. **Extends `BUILD.md` B-5's marker
grammar** and discharges the half of TM-116 that TM-116 could not.

**The gap.** `probe09_environ_split` and `probe09b_environ_view_returned` need
`TZ=Europe/Kyiv`. TM-116 gave them dedicated exit codes so an unmet precondition
names itself — **30** absent, **39** present and wrong — and said plainly that
this *"is not something a runner can honour: B-5's marker grammar has `// argv:`
and no way to state an environment variable"*. Run bare, both are a red run the
harness cannot avoid.

**The decision, in two halves.**

*First: the marker.* **`// env: NAME=VALUE`**, one variable per line,
repeatable, in the header block. It joins `expect-exit`, `expect-error`,
`expect-error-at`, `expect-golden`, `stress` and `argv`. **A marker and not a
wrapper script**: the expectation belongs in the file with the test, which is
B-5's whole principle, and a wrapper is a second place for a test's truth to
live.

*Second, and it is the half nobody asked for: the environment is **constructed**,
never inherited.* A test program's environment is a fixed base plus its own
markers and **nothing from the harness's own environment**. Without this the
marker would be pointless: `probe09` exits 39 under `TZ=UTC`, so a developer
with `TZ` set in their shell and CI without it would get different verdicts from
the same tree — a suite whose answer depends on who ran it, which is what D-076
and B-4 exist to prevent.

**The base is NON-EMPTY, and that is measured rather than chosen.** Built with a
genuinely empty environment, `probe09_environ_split` exits **10** — its own
`env.len <= 0`, a substantive code meaning *`environ()` returned nothing*. That
is TM-116's failure through a second door: an unmet precondition arriving as a
verdict about the language. The probes were written against a shell environment,
which is never empty. The base is therefore one inert declared variable,
`NTIME_HARNESS=1`, which keeps `environ()` non-trivial and is identical on every
machine because it is declared here rather than inherited.

*Alternatives declined:*

- **A wrapper script, or an `env` key in `nitpick.toml`.** Both put a test's
  expectation somewhere other than the test. The manifest's `[[test]]` entries
  are per **directory**; these two probes want different environments from
  their twenty-four neighbours.
- **Inherit the environment and add the markers on top.** It is one line
  shorter and it makes every `environ()`-reading test's verdict a property of
  the operator's shell.
- **Empty base, and change probe09's exit 10 to a precondition code.** Exit 10
  is a real assertion about the language — *does `environ()` return the
  entries* — and rewriting a probe's assertion to suit the runner is the tail
  wagging the dog. A probe is never deleted (0.0.0 P-5) and its verdicts are a
  regression suite.
- **Pass `TZ` through from the harness's own environment when set.** The same
  defect, with an extra branch.

### TM-121 — the marker block is contiguous from line 1, and a marker-shaped line below it is a failure
**2026-09-05. Found by building the reader.**

**The hazard, and it is already in this tree.**
`tests/probe/defect/view_escape/case4_view_in_struct.npk:9` and
`case5_read_after_free.npk:15` each carry, in **prose**, the line

    // expect-error: NITPICK-BORROW-001".

— a wrapped continuation of a quoted sentence, at column zero, byte-identical to
a real marker but for the trailing `".`. Cycle 0.0.1's reader scanned the whole
leading comment for anything starting `// expect-`, so it would have read both
as markers.

**The decision.** *The marker block is the maximal run of marker lines starting
at **line 1**; it ends at the first line that is not one. The grammar is exact —
`//`, one space, a known key, a colon — so `//      expect-error: …` (six
spaces, the prose at `case3_view_returned.npk:17`) is not a marker and never
was. **A marker-shaped line below the block is reported and fails**, naming the
file and line.*

**Why a failure rather than a silent skip.** The line that matters is not the
prose already here; it is the `// stress: 40` somebody adds at line 20 of a file
next year, believing it took effect. That is a silent no-op, and a silent no-op
in an expectation is this repository's defining failure mode. The two prose
lines were indented by two spaces in this commit, which costs nothing and buys
a check that cannot be fooled.

*Alternatives declined:*

- **Accept markers anywhere in the leading comment.** It is what 0.0.1 did, and
  it makes the two prose lines above into expectations nobody wrote.
- **Warn instead of failing.** A warning in a green run is read by nobody.
- **Require the block to be the whole leading comment.** Every file here puts
  documentation under its markers, and that documentation is the most valuable
  thing in the directory.

---

## The self-check batch — cycle 0.0.3, measured against pin `0dfddac`

Five decisions, all produced by building `TESTING.md` V-14's self-check and
finding what a runner has to be able to do before it can be shown able to fail.
Two of them correct something this repository had already planned.

### TM-122 — a `sweep` declares its domain in its header and PRINTS the count it visited
**2026-09-05. New marker, `// sweep-count: N`.** `BUILD.md` B-5 and B-9,
`TESTING.md` V-14 case 7 and the new V-16.

**The problem, and it is this library's most plausible way to be green and
wrong.** `ntime`'s strongest claim is an exhaustive sweep — V-2 and V-3: every
day in `[−9999-01-01, +9999-12-31]`, both directions, 7 304 485 × 2 — and **an
exhaustive loop that returns after one iteration exits 0 exactly like one that
ran to the end.** No exit code distinguishes them. Neither does wall time, on a
sweep that takes seconds. Nothing *outside* the program can tell the difference,
because the only evidence that the work happened is inside the process that did
it.

**The decision.** *A `sweep` member declares `// sweep-count: N` — the size of
the domain it must visit — and writes exactly one line `swept <N>` to stdout.
The harness requires the two numbers to be equal. A sweep member with no
`sweep-count` is a failure, not a skip; so is a `sweep-count` on a member of any
other stage, because there it is an expectation that does nothing (V-1f).*

**Why the evidence has to come from the program.** Every alternative that keeps
the program silent measures something other than the work: a timer measures the
machine, a coverage counter measures the compiler, and an exit code measures
nothing at all. The program is the only witness, so the design makes it testify.

**The three ways a sweep does not run, and all three are covered**, which is the
point — the marker alone would leave two of them open:

1. **the entry selects no files** — `run.py`'s `run_entry` fails an entry whose
   glob matched nothing, which is the rule the manifest already carried;
2. **`--quick` skipped the stage** — announced through the same `Report` object
   as every other verdict, so the transcript and the summary cannot disagree,
   and the run refuses to print the unqualified word GREEN;
3. **the program ran and did no work** — this marker.

*Alternatives declined:*

- **Reuse `expect-golden` and commit a golden file per sweep.** It works, and it
  costs a committed file per sweep to assert one integer. The marker says the
  same thing where a reader of the test will see it.
- **Have the harness time the sweep and fail a suspiciously fast one.** That is
  a threshold on somebody's machine, which is the shape D-076 and B-4 exist to
  keep out of this suite.
- **Let a sweep member without the marker run as an ordinary `program`.** It is
  the skip that makes a suite green while checking nothing, and this library
  already lost two days to one (TM-115).

### TM-123 — the `parse` stage asks `$NPKC` and reads the CODE FAMILY, because there is no parse-only mode
**2026-09-05. Measured** at pin `0dfddac`. **Corrects `BUILD.md` §3 and
`meta/roadmap/0.0/0.0.3.md` §2**, both of which name the compiler's
`tools/parse_check` as this stage's tool.

**What the plan assumed.** That the three frontend tools — `tools/parse_check`,
`tools/check`, `tools/resolve_check` — would be *"built once per run from the
pinned checkout"*.

**What is actually there.** They are `.npk` **source files**.
`tools/parse_check.npk` is 131 lines that `use` twenty of the compiler's
`src/frontend/` modules; `tools/check.npk` imports the whole driver pipeline.
Building either means building the compiler — from a working tree that is
**ahead of our pin and moving** — which W-18 forbids, and which would put an
**unpinned parser** behind a stage whose three sibling tools are held to an
exact LLVM patch release (D-204). A stage that asserts less than its neighbours
about its own provenance is the wrong shape for the one stage whose subject is
every file in the tree.

**And `npkc` has no parse-only mode.** Its usage line at the pin is
`npkc <root.npk> [-o out.ll] [--obligations DIR] [--elide …]
[--extra-picky=no-wildx]`. No `--parse`, no `-fsyntax-only`.

**The decision.** *The `parse` stage roots every `.npk` in the tree at `$NPKC` —
the pinned artefact — once each, and reads the FAMILY of any diagnostic that
comes back. `NITPICK-LEX-*` is declared in the compiler's
`src/frontend/diag_codes.npk` and `NITPICK-PARSE-*` in `parse_codes.npk`; every
other family in that tree belongs to a later phase, so a file reported with one
of those necessarily parsed. A file must parse unless its own header names a
parse-phase code.*

**Why that rule is exactly right for this tree, and it is not obvious.** Twenty-
six files here must NOT compile, and they are refused at `TYPE-009`,
`BORROW-001`, `BORROW-012`, `REACH-002` and `REACH-003` — every one of which is
a phase that only runs on something that parsed. Exactly **one** file in the
tree is expected not to parse (`probe02d_wide_literal_refused.npk`, a literal
outside the 64-bit envelope), and the stage's job is to confirm that it is
exactly that one. Measured: **50 = 36 parse cleanly + 13 parse and are refused
later + 1 does not parse**.

**It is a whole-tree stage and not a `[[test]]` entry**, and an entry naming it
is refused by name. `BUILD.md` §3's own Directory column for `parse` reads
*"every `.npk` in the tree"*, and that is the stage's whole value here: of the
50 files, the library build roots 1, the suite roots 27 and 3 more are reached
by `use` from a suite root, so **19 are put in front of the compiler by nothing
else** — the six `src/` placeholders, which `src/lib.npk` does not reach because
it re-exports nothing yet, and the thirteen reproductions under
`tests/probe/defect/`, the directory whose files went two days with no
expectation at all (TM-115).

**The cost is real, measured, and shrinking.** 40.1 s for the 50 files, because
`npkc` runs its whole pipeline and every root re-emits the prelude (TM-117); a
file that does not parse costs 0.03 s, since it fails at once and writes
nothing. The prelude cost is the compiler's own item and is being cut, so the
simple design is the right one to hold: it depends on no other stage's
membership and cannot silently un-cover a file.

*Alternatives declined:*

- **Extract the compiler at the pin and build the three tools.** Correct in
  principle and unavailable in practice: it is building the compiler, and the
  pinned artefacts this workbench distributes are `npkc` and `npkrt.o`. If the
  toolchain pin ever ships the frontend tools too, this decision is superseded
  rather than worked around.
- **Parse only the files no other stage roots.** Half the cost and a coupling
  to the suite's membership, so a `[[test]]` entry gaining a directory would
  silently stop the parse stage covering it.
- **Skip the stage.** It is the only thing that opens nineteen files.

### TM-124 — `accept` is DECLINED, not unimplemented, and the manifest says which
**2026-09-05.** Carries `BUILD.md` B-4b and TM-114 into the runner.

**The tension.** `meta/roadmap/0.0/0.0.3.md` §2 lists `accept` among the stages
this subcycle adds. `BUILD.md` §3 marks it *"(not used by this library)"* and
B-4b explains at length why, and `TESTING.md` §1 says *"the stage exists
upstream; this library does not use it"*. **The specifications are the
authority** (TM-002), so the plan is the document that is wrong.

**The decision.** *`accept` is refused by name with its reason, in the same
schema check that refuses an unimplemented stage — but as a different kind of
refusal. An unimplemented stage says "not yet"; `accept` says "not here, and
here is what to use instead".*

**Why the distinction is worth a decision.** *"Not yet"* invites a later session
to implement it. `accept` stops at *"accepted in silence"*, and this repository
holds the reproduction of exactly what that misses: a root with `main` and no
`failsafe` was accepted by `npkc` at exit 0 and refused only by the linker
(`tests/probe/defect/missing_failsafe/`, O-N11, TM-112). A runner that
implemented the stage would be offering the shape B-4b exists to keep out of
reach. The message names `compile` with `kind = "positive"` — judged on the RUN
— as the thing to write instead.

### TM-125 — CI never uses `--quick`, and the reason is a property of THIS library
**2026-09-05. Settles O-X5**, as its recommendation proposed, and the reasoning
is recorded because a later session under time pressure will want to reopen it.

**The decision.** *`--quick` is for a developer iterating on one function. No
CI workflow in this repository may pass it, and none does.*

**Why, and the argument is not "sweeps are cheap".** They are — V-3 says the
civil sweep runs in seconds — but cheapness is a fact about today's domain
sizes and would stop being an argument the moment a sweep got slow, which is
precisely when somebody would want the flag. The durable reason is what the
sweeps ARE: `TESTING.md` V-2 makes the exhaustive gate *the* gate for every
property that can be checked over its whole domain, and V-3 calls the civil
sweep **the strongest statement this library makes**. A CI run that skipped it
would be a CI run that concluded nothing — so the badge would be asserting
something no run had checked, which is worse than having no badge.

**And it is enforced by shape rather than by policy.** A `--quick` run announces
twice that it concludes nothing, prints a `SKIP` line per skipped entry through
the same `Report` object as every other verdict, and **refuses to print the
unqualified word `GREEN`**. So a `--quick` run pasted into a review reads as
what it is.

*Alternatives declined:*

- **Allow `--quick` on pull requests and run the full suite on `main`.** It is
  the arrangement that lets a sweep regression land and be discovered by
  somebody else's merge, and the bisect then spans every commit in between.
- **Leave it to reviewer discipline.** The flag exists to be convenient; a rule
  that depends on nobody reaching for it under deadline is not a rule.

### TM-126 — a tree check is COMMISSIONED, not merely written; `check_purity` and `check_host_isolation` go live now
**2026-09-05. Supersedes the dormancy half of `meta/roadmap/0.0/0.0.3.md` P-21**
— which said `check_purity` and `check_host_isolation` are *"written now and
dormant"*, to go live at cycle 0.3 when `src/host/` exists.

**Why the plan said dormant, and what it got right.** P-21's reasoning is sound
and survives: *"writing them here means 0.3 turns them on rather than inventing
them, which is the compiler's rule that instruments precede the constructs they
guard."* The intent is that 0.3 inherits a working instrument.

**What building them showed.** `src/host/host.npk` already exists — as a
placeholder, but the check does not care — so both checks can RUN today, over
six files, and report `0` findings with the denominator printed. That is P-20's
own argument (*"`check_no_owning_fields` over an empty set is the right
answer"*) applied to these two, and there is no reason it applies to four of the
family and not to six.

**And a stronger thing became available.** The tree checks are pure functions of
a directory, so the self-check can plant a violation in a scratch tree and
require each check to find it — for nothing, in milliseconds, with no
compilation. **Nine planted violations, nine clean controls, on every full
invocation.** So `check_purity` is not merely live today; it has been *seen to
fail*, which is what 0.3's own note in `src/host/host.npk` asks for and which no
amount of dormancy would have delivered.

**The decision.** *Every tree check runs on every full invocation from the cycle
it can be written, and every one is commissioned in `selfcheck.py` §B against a
planted violation AND a clean control. A check that has never failed has never
been shown to work, and "written but not run" is the weakest state an instrument
can be in — weaker than absent, because absence is visible.*

**What 0.3 inherits instead.** Not a check to turn on: a check that is on, has a
denominator, and has been red. 0.3's job becomes the real one — planting a
`mono_now()` in `src/cal/` **and confirming the failing run says the right
thing about a real module**, rather than discovering on that day whether the
predicate works at all.

**And the boundary is stated wherever the check is described.** `check_purity`
is a **source-level** check. The build's undefined-symbol scan cannot answer the
question it answers: `npk_sys6` is the runtime's own syscall trampoline and is
in the allowlist by construction, so a module that issues a raw syscall has an
identical undefined set to one that does not — measured in `nitpick-regex` as
RX-120 (29 symbols each way, diff empty) and reproduced here (TM-118, B-2c). A
green symbol scan cited as a purity result is the failure mode, so the sentence
appears in `elf.py`, `checks.py`, `harness/README.md`, `BUILD.md` B-2c,
`TESTING.md` §2 and `CLAUDE.md` — six places, deliberately, because a reader
meets one of them at a time.

*Alternatives declined:*

- **Keep them dormant and print the dormancy** (the acceptance item as written).
  It is honest and it leaves two of the family unexercised for three cycles,
  which is exactly how an instrument arrives broken on the day it is needed.
- **Run them but do not commission them.** That is the state 0.0.2 ended in and
  named in its own §6: three checks commissioned by hand is not a runner.

---

### TM-127 — OVERWRITING a `Vec<T>` element discards one, so `vec_set` is the FOURTH entry that owes an element drop
**2026-09-05, cycle 0.0.4. Extends TM-106 and amends `SAFETY.md` S-18b and
`meta/roadmap/0.0/0.0.4.md` §2's note**, both of which name three
element-discarding entries and there are four.

**What the documents said.** `0.0.4.md` §2: *"Three of those entries discard
elements and none of their postconditions says so — `vec_free`, `vec_clear` and
`vec_truncate`."* S-18b states the same obligation against the same three, and
`probe06_generic_vec.npk`'s header lists the same three.

**The fourth is `vec_set`,** and it is the least visible of them: `vec_free`,
`vec_clear` and `vec_truncate` all *sound* like they discard something, and
`vec_set` sounds like it replaces one. It discards the element that was there,
and nothing drops it.

**Measured, 2 000 000 overwrites of one occupied `Vec<string>` slot at pin
`0dfddac`, with the committed pair `tests/probe/probe12_set_overwrite_leak.npk`
and `probe12b_set_overwrite_drop.npk`, which differ in one statement and BOTH
EXIT 0:**

| | peak RSS | `ulimit -v 65536` | `ulimit -v 3072` |
|---|---|---|---|
| overwritten in place | 125 184 KiB | **exit 92**, `HeapOom` | exit 92 |
| outgoing moved out first | 1 596 KiB | exit 0 | exit 0 |

**It is NOT a compiler defect, and two controls are what established that** —
the first reading was that it contradicts the compiler's D-186, whose title is
*"overwriting an owning field or managed element drops the old value"*:

- **Control A** — the same 2 000 000 overwrites into a **local binding**
  (`s = string_concat(…)`): **1 660 KiB**, clean under a 64 MiB cap. A binding
  drops its old body, exactly as D-186 says and as `PLAYBOOK.md` records.
- **Control B** — the same overwrites written **directly at the site**, no
  function call anywhere: **125 184 KiB**, `HeapOom` under the cap — identical
  to the leaking half.

So the property belongs to the **destination**, not to the call: D-186's
*managed* element drops and a `wild T->` element does not, because `wild` is
the manual regime and the manual regime does not drop for you. That is the same
sentence that makes `vec_free` the caller's job, and TM-106 is its other half.

**The decision.** *Every operation that overwrites or discards a `Vec<T>`
element owes an element drop at an owning `T` — `vec_free`, `vec_clear`,
`vec_truncate` **and `vec_set`**, and any later in-place update. `vec_push` is
exempt and the reason is worth stating, because the two lines of code are
identical: it writes at `count`, which is past the last live element by
construction, so there is nothing there to discard.*

**And the remedy is not available generically today** (O-N17): a generic
`vec_set<T>` that moves the outgoing element into a dying local is accepted by
`npkc` at exit 0 and refused by `llc`. Both halves of the committed pair are
therefore written at the instantiation (`Vec<string>`), which is where S-18b
already puts element lifetime — and which is why `vec_pop<T>`'s row is HELD
(blocked on O-N17, see `0.0.4.md` §2) rather than the subcycle choosing between
a `vec_set` that leaks and one that does not link. The rest of 0.0.4 was built:
the defect blocks one row of one table, not a layer.

*Alternatives declined:*

- **Treat it as a restatement of TM-106 and add nothing.** TM-106 is about a
  container being *freed*; a reader applying it to `set` has to make an
  inference the document does not offer, and the three-entry list actively
  discourages it by being explicit and short.
- **Say it in a comment on `vec_set`.** `CLAUDE.md`: a specification that turns
  out to be wrong is amended by a decision, never by a comment.

### TM-128 — the element-drop pair's "under 768 KiB" is not reproducible; the bound is a 3 MiB address space, and 2 MiB is the machine's floor
**2026-09-05, cycle 0.0.4. Corrects a number carried by `SAFETY.md` S-18b (1),
`meta/roadmap/0.0/README.md` (1), `meta/roadmap/0.0/0.0.4.md` §6 (1),
`tests/probe/probe06_generic_vec.npk` (2) and `meta/roadmap/0.0/0.0.0.md` (2)**
— and the arithmetic is written out because this decision first stated it
wrongly:

    7 sites in 5 files = 1 + 1 + 1 + 2 + 2

**This entry originally said "six sites in five files", which does not equal its
own enumeration.** Re-derived 2026-09-05 by the subcycle's second worker: the
sweep `grep -rn '768 KiB\|at 768\|768,\|under 768\|768 K'` over the whole
working tree outside `.git` and `.internal` returns **15 candidates**, and
because the property is *"asserts the old figure as a live claim"* rather than a
lexical one, **reading is the verdict**: **6 assert it** (the 7 above less
`SAFETY.md`, corrected in the same diff that wrote this decision) and **9 are
this correction's own text** — 15 = 6 + 9. One unrelated hit, the timestamp
`-2041768800i64` in `probe04b_emission_shape.npk`, is excluded by the pattern
and named here so the exclusion is reviewable rather than silent.

**The claim.** *"The corrected half completes 2 000 000 iterations in UNDER 768
KiB (clean at 768, `HeapOom` at 512)."* It was measured at pin `94874ce` and the
0.0.4 dispatch asked for it to be re-measured rather than inherited.

**What re-measuring found, at pin `0dfddac`, on `probe06c_element_drop`:**

    ulimit -v   131072  65536  32768  8192  4096  3072  2048  1024   768
    exit             0      0      0     0     0     0   127   127   127

**and the control that says what the 127s mean:** `/bin/true` under the same
caps also fails to exec — *"failed to map segment from shared object"* — at
2048, 1024 and 768, and succeeds at 4096. **So ~2 MiB is this machine's exec
floor for any process, and a run "clean at 768" is not something this mechanism
can produce.** The 512 figure is below the same floor.

**The corrected numbers,** and they are *better* than the ones they replace,
because one of them was never a measurement at all:

| | peak RSS | smallest clean `ulimit -v` |
|---|---|---|
| `probe06b_element_leak` | 125 184 KiB | 131 072 (92 at 65 536) |
| `probe06c_element_drop` | **1 660 KiB** | **3 072** |

**The leaking half is unchanged to the kilobyte** — 125 184 KiB, `HeapOom` at a
64 MiB cap — so S-18b's finding stands and only its remedy-side bound moves.

**And the peak-RSS figure for the remedy half is now real.** S-18b says to quote
the address-space bound and not a peak RSS, because `/usr/bin/time -f %M`
reported **0 KiB** for these static binaries at the earlier pin. It does not
report 0 here: it reports 1 660 KiB, and 1 596 KiB for TM-127's twin. The gauge
under-reports a *small* RSS; it does not under-report this one. So both figures
can now be quoted, and the arithmetic between them is checkable:

    125 184 − 1 660 = 123 524 KiB retained over 2 000 000 orphaned elements
                    ≈ 63 bytes each, for a 35-byte body in a 64-byte size class

which is the corroboration the old pair of numbers could not offer, since one
of them was zero.

**The decision.** *Quote **peak RSS 1 660 KiB and a 3 MiB address-space cap**
for the remedy half, never "under 768 KiB". Any future address-space bound in
this repository is taken with a `/bin/true` control at the same cap, because
below about 2 MiB every exit code on this machine is the loader's.*

**How the six sites are corrected, which differs by what the file is.** The two
specification-and-plan sites (`SAFETY.md` S-18b, `0.0.4.md` §6) and the cycle
checklist take the new numbers with this decision cited. The two record sites in
`0.0.0.md` and the two in `probe06_generic_vec.npk`'s header keep their original
text and gain a **dated note** saying what it previously said and how the
correction was obtained — `PLAYBOOK.md`'s rule, that a correction to a committed
transcript is *added* and never *substituted*.

*Alternatives declined:*

- **Silently update the number everywhere.** It would leave two committed
  transcripts asserting they faithfully record a run that reported something
  else, which is the specific failure that rule exists to prevent.
- **Record it as "unchanged, probably".** The dispatch asked for a
  re-measurement precisely because "probably unchanged" is what the re-pin
  discipline refuses, and here the assumption would have been wrong.

### TM-129 — the accessor reinstates the language's OWN bounds guard with `#wild_slice`, rather than two hand-written comparisons
**2026-09-05, cycle 0.0.4. Settles the mechanism `SAFETY.md` S-17b and cycle
0.0's checklist require, and amends S-17b to say HOW its `0 <= i` half is
discharged.**

**The obligation.** S-17b: `Vec<T>.items` is a bare pointer, `ExprIndexExpr`
emits `emit_bounds_guard` on `TY_SLICE`, `TY_ARRAY` and `TY_SIMD` and not on
`TY_POINTER`, so *"the accessor pair is the only bounds check that exists"* —
and *"Signedness is half the check … Every accessor checks `0 <= i` as well as
`i < count`."* The obvious implementation is two `if`s.

**The decision.** *Every `Vec<T>` accessor lays a length-carrying slice over the
block and indexes that:*

```nitpick
func:vec_at<T> = T(Vec<T>->:v, int64:i) never fails {
    T[]:s = #wild_slice<T>(v.items, v.count);
    pass s[i];
};
```

*The slice is laid over `count`, never over `cap`.*

**Four things measured before choosing it, at pin `0dfddac`, committed as
`tests/probe/probe13_vec_bounds_guard.npk` and its three twins:**

1. **It traps past the end** — `probe13b`, `i == count` with room at that index
   because `cap` is larger: **exit 94**, `OutOfBounds`.
2. **It traps on a negative index** — `probe13c`, `i == -1`: **exit 94**, and
   the accessor contains **no `i >= 0` comparison at all**. The mechanism is
   read out of the compiler rather than inferred: `emit_bounds_guard` emits a
   single `icmp ult i64` — *unsigned* — and `index_as_i64` sign-extends first,
   so the compiler's own comment applies verbatim: *"a negative index of any
   width becomes a huge unsigned value and ONE unsigned compare rejects both
   `negative` and `past the end` (D-070)."* **So S-17b's two halves are
   discharged by one compare, and the second hand-written `if` would be dead
   code a reader still had to maintain.**
3. **The unguarded spelling really does return a wrong value** — `probe13d`,
   the same read through `v.items[i]` with a sentinel planted in the slot past
   `count`: **exit 0, and the sentinel comes back as an element.** Until this
   probe, TM-108 and S-17b rested on a *reading* of the emitter and nothing in
   this repository had ever run an out-of-range `Vec` index.
4. **It costs a consumer nothing** — and this is the measurement that removes
   the only argument against it. `NITPICK-REACH-003` bills a program importing
   a `vec.npk` with the guarded accessor **six** identities, and one with the
   bare-pointer accessor **the same six**:

       6 = 4 (S-4b's floor) + 1 (IntOverflow, from `n * #size_of<T>()`)
                            + 1 (OutOfBounds, from the index)

**And item 4 is worth more than the decision it settles.** The reachability
analysis arms `OutOfBounds` for a **bare pointer** index — for which no guard is
emitted at all — so every consumer of an unguarded `Vec` is compelled to write
an arm for a trap that *cannot fire*, while the read it is meant to protect
returns a wrong value in silence. **The arm bill, which is the one artefact a
library author reads when asking what can go wrong, is byte-identical between
the safe spelling and the unsafe one.** That is why TM-108 went unnoticed as
long as it did, and it is the same name-versus-mechanism shape as the `exit 0`
leak gate and the undefined-symbol scan. Adding the guard makes the arm honest;
it does not add it.

**It works from an imported module, not only from a root** — measured, because
`src/core/vec.npk` will be imported and `#wild_slice` is documented
`wild`-context-only: a two-file consumer built end to end returns **exit 94**
from an out-of-range `vec_at`.

*Alternatives declined:*

- **Two explicit comparisons.** They are what the checklist literally describes,
  and they are a second implementation of D-070 that can drift from it. One of
  the two would also be provably dead (item 2), and dead code that looks
  load-bearing is worse than none.
- **`fail` an error identity on an out-of-range index.** `core` declares no
  error (`SAFETY.md` S-4) and the budget is three with a ceiling (S-2); an
  accessor is not where a fourth identity gets spent, and a precondition
  violation is a caller's bug rather than a runtime condition.
- **Return a fallback value.** It converts a caller's bug into a wrong answer,
  which is precisely the failure mode S-17b exists to remove.

### TM-130 — the ten `VerificationKeyword` spellings are reserved, and none of them was in any table here
**2026-09-05, cycle 0.0.4. Adds them to `BUILD.md` §7 and `CLAUDE.md`.**

**How it was found.** A local named `old` — the natural name for the element
`vec_set` is about to discard — refused to parse, and the diagnostic named the
punctuation rather than the name:

    NITPICK-PARSE-001 …:47:6: expected `;`, found `:`
    NITPICK-PARSE-001 …:47:28: expected `;`, found `)`

pointing at the **colon** in `T:old = move(…)`. This is the `stack` failure
mode `PLAYBOOK.md` §10 records — *"it does not fail where you wrote it"* — with
a different keyword and the same hour available to lose.

**The full set, measured one at a time** at pin `0dfddac` by declaring
`int64:<name> = 1i64;` and reading `npkc`'s status beside its artefact. **All
ten are refused, 10 of 10:**

`prove` · `assert_static` · `requires` · `ensures` · `acquires` · `gives` ·
`invariant` · `old` · `result` · `pure`

They are `LEXICAL_REFERENCE.md`'s `VerificationKeyword` production; `old`,
`result` and `pure` were added by the compiler's **D-221** at its 1.5.1, whose
own note records that adding them renamed *"two locals and one field"* in the
compiler itself. `old`'s token is `KwOld` and `result`'s is `KwResultValue`.

**What made it worth a decision rather than a fix.** **Nine of the ten appear in
no reserved-word table anywhere in this ecosystem**, and none of the ten appears
in either of this repository's two — `BUILD.md` §7's table (0 of 10) or
`CLAUDE.md`'s list (0 of 10). Only `gives` is listed, in `PLAYBOOK.md` §10.

**And two of them are actively invited by this library's own documents.**
`0.0.4.md` §2's API table writes `ensures v.count == old(v.count)`, and
`VERIFICATION.md` P-3 writes `ensures (result.year >= YEAR_MIN …)`. So a reader
meets `old` and `result` **as things to write**, in the contracts this cycle is
required to write as comments, and has no way to learn from these documents that
they cannot also be locals. The words are not merely reserved; they are reserved
*and* prominent *and* undocumented, which is the combination that costs an hour.

**The decision.** *`BUILD.md` §7's table and `CLAUDE.md` carry all ten, with the
substitutions this library uses: **`outgoing`** for a value being replaced,
**`answer`** for a computed result, and `prev`/`dying` where they read better.
A verification keyword is never a local name here.*

*Alternatives declined:*

- **List only `old`, the one that bit.** `state-impact-and-full-extent`: the
  next session hits `result`, which is likelier still.
- **Wait for the compiler's 1.5 to make them live and list them then.** They are
  live *as tokens* now, at this pin, which is the only thing that decides
  whether a file compiles.

### TM-131 — `ulimit -v` cannot measure the remedy half AT ALL, because its bound and `/bin/true`'s are the same bound; the element-drop gate is the LEAKING half's refusal and the peak-RSS pair
**2026-09-05, cycle 0.0.4. Refines TM-128, which is confirmed in every figure
it states, and corrects the inference TM-128 and `0.0.4.md` §6 draw from it.**

**What TM-128 established, re-measured independently here and reproduced to the
kilobyte** at pin `0dfddac`, each status paired with the artefact or gauge it
produced:

| | peak RSS | exit at `-v 65536` |
|---|---|---|
| `probe06b_element_leak` | **125 184 KiB** | **92**, `HeapOom` |
| `probe06c_element_drop` | **1 660 KiB** | **0** |

**What TM-128 did not test, and what it changes.** TM-128 bisected
`3072 → 2048` and found `/bin/true` failing below ~2 MiB, and concluded *"the
bound is a 3 MiB address space"*. Bisecting the gap shows the two curves are
**the same curve**:

    cap (KiB)   2560  2688  2816  2944  3008  3072
    /bin/true    127   127     0     0     0     0
    probe06c     127   127     0     0     0     0

**At every cap tested, `probe06c` and `/bin/true` return the SAME exit code**,
and both cross between **2688 and 2816 KiB**. So 3 MiB is not a fact about
`probe06c`; it is a fact about this machine's loader. `probe06c`'s own
requirement is **≤ 2816 KiB and not measurable by this mechanism**, which the
peak RSS corroborates: 1 660 KiB is *below the floor at which anything execs*.

**The decision, and it is about what the gate asserts.** *"`probe06c` is clean
at a 3 MiB cap" is not an assertion about `probe06c`* — `/bin/true` passes it
too, and so would a `probe06c` that had been silently emptied. **A gate that a
trivially correct program and a trivially empty one both pass is not a gate.**
So the element-drop pair is asserted by the two things that do discriminate:

1. **`probe06b` takes exit 92 at `ulimit -v 65536` and `probe06c` takes exit
   0 at the same cap.** One cap, two programs, opposite outcomes, and 64 MiB is
   twenty-three times the loader floor so neither result is the loader's.
2. **The peak-RSS pair, 125 184 KiB against 1 660 KiB**, whose difference is
   checkable against the thing being leaked:

       125 184 − 1 660 = 123 524 KiB over 2 000 000 orphaned elements
                       ≈ 63 bytes each, for a 35-byte body in a 64-byte class

*Never quote a low `ulimit -v` as a program's bound without the `/bin/true`
control **at the same cap**, and if the control fails with it, the number
measures the machine.* TM-128 already required the control; this entry is what
happens when it is run at every point rather than at the ends.

*Alternatives declined:*

- **Leave the 3 MiB figure as the gate and note the caveat.** The figure would
  stay in the acceptance as something to assert, and the next worker asserts it,
  and it passes for a reason unrelated to the library. That is the same
  name-versus-mechanism failure as the `exit 0` leak gate and the arm bill —
  the third in this repository, and the second found in this subcycle.
- **Report it as agreeing with TM-128 and move on.** The figures do agree; the
  conclusion drawn from them does not survive the two extra rows. Recording
  agreement would have carried the wrong gate forward under a confirmation.

### TM-132 — O-N17 blocks FIVE rows of the `Vec<T>` table and not one, because all five are one primitive; the library ships `Vec<T>` at a NON-OWNING `T` and says so
**2026-09-05, cycle 0.0.4. Establishes the extent of O-N17, amends `SAFETY.md`
S-18c and `0.0.4.md` §2's API table, and settles what `src/core/vec.npk` ships.**

**What was believed.** O-N17 was raised, and ratified at re-dispatch, as
blocking **one row** of `0.0.4.md` §2's nine-row table — `vec_pop<T>` — on the
argument that *"the defect blocks one row of one table, not a layer of the
library"*. That argument's conclusion survives. Its premise does not.

**What the primitive actually is.** Not "popping". It is

    T:x = move(v.items[i]);        // inside a GENERIC function, at an OWNING T

and **five of the nine rows are built on it** — `vec_pop` returns the moved
value, `vec_set` overwrites after it, and `vec_clear`, `vec_truncate` and
`vec_free` each drop in a loop around it. A loop is a different *caller*, not a
different primitive.

**Measured at pin `0dfddac`, every owning case with a non-owning control built
from the SAME source text, each status beside its artefact:**

| shape | `T` | `npkc` | `llc` | link+run |
|---|---|---|---|---|
| move out and return (`vec_pop`) | `string` | 0, `.ll` | **1, NO OBJECT** | — |
| move out and overwrite (`vec_set`) | `string` | 0, `.ll` | **1, NO OBJECT** | — |
| move out and drop, loop (`vec_clear`) | `string` | 0, `.ll` | **1, NO OBJECT** | — |
| move out and drop, countdown (`vec_truncate`) | `string` | 0, `.ll` | **1, NO OBJECT** | — |
| **all four, same source** | **`int64`** | **0** | **0, object** | **0, exit 0** |

Every owning failure is the same diagnostic, `use of undefined value
'@npk.vacant.<dty>'`. The controls are what make the boundary exact rather than
suspected: **generic × owning × move-out, and no two of the three.**

**So the four rows that are UNAFFECTED are `vec_init`, `vec_reserve`,
`vec_push` and `vec_at`** — and `vec_push` is unaffected for TM-127's reason,
that it writes past the last live element and so moves nothing out.

**The decision.** *`src/core/vec.npk` ships all nine rows **at a non-owning
`T`**, which is every use `ntime` has. `vec_pop<T>` ships too — it is correct at
a non-owning `T` and that is the only `T` this library instantiates. What is
**not** shipped, and is recorded as blocked rather than approximated, is the
**element-drop path at an owning `T`**: `SAFETY.md` S-18b already puts element
lifetime **at the instantiation**, and the sanctioned spellings are
`probe06_generic_vec.npk`'s `free_names` and `probe12b`'s `vec_set_string`,
both concrete and both measured clean.*

**Why this is a restriction and not a workaround (W-11).** The distinction is
whether library code is bent around the bug. None is: every function here is the
one that would have been written anyway, and the restriction was **already one
of the two options the plan offered** — `0.0.4.md` §2 required each
element-discarding entry to have *"an element-drop path for an owning `T` **or a
stated restriction to non-owning ones**"*, written before this defect was known.
The defect removes the first option; it did not invent the second. **What would
have been a workaround** is a generic `vec_clear<T>` that silently does not drop,
shipped without saying so — leaking at an owning `T`, passing `exit 0` because
D-151 cannot see a managed body (TM-106), and reading later as a design choice.

**The restriction is CHECKED and not merely stated**, which is the difference
between this and a house rule: `check_no_owning_fields` already refuses an
owning field in a table, and `src/core/vec.npk` carries the restriction in its
header beside the reproduction path.

*Alternatives declined:*

- **Hold all five rows and ship four.** It would leave `Vec<T>` without
  `vec_free`, so no `Vec` could be released at all, and D-151 would trap `exit
  0` on every program that made one. The defect would have taken the layer.
- **Report agreement with the one-row reading.** Two shapes were tested before
  the reading was questioned and both failed; a third (`vec_set`) was asserted
  by TM-127 and had never been run. Confirming "one row" would have shipped a
  generic `vec_clear<T>` that does not drop.

### TM-133 — `Bytes` has NO `free`, and the plan's operation list is corrected
**2026-09-05, cycle 0.0.4. Corrects `meta/roadmap/0.0/0.0.4.md` §3, which lists
`free` among `Bytes`' operations.**

**What the plan said.** §3: *"`init`, `push`, `extend`, `extend_str`,
`put_uint`, `put_int`, `len`, `view` …, `take` …, `clear`, `free`."*

**Why `free` cannot exist.** `Bytes`' body is a `buffer`, and the compiler's
`TYPE_REFERENCE.md` §23 lists `buffer_free` among the things **deliberately not
landed**: *"the managed drop IS the free; manual reclaim is the `wild` regime's
spelling"*. There is no reclaim function to call, so a `bytes_free` could only
be a no-op.

**And a no-op named `free` is worse than no function.** It teaches a caller to
pair something that needs no pairing, and — in a repository where `Vec<T>`'s
`vec_free` is genuinely mandatory and a missed one traps `WildLeak` at `exit 0`
— it would read as the same obligation applying to both types. That is exactly
the distinction P-24 exists to draw: `Vec<T>` is `wild` and manual, `Bytes` is
managed and automatic, and the two files differ because the regimes differ.

**The reclaim path is MEASURED rather than assumed**, because TM-127 found the
contrary behaviour one field-kind away. Overwriting the `body` field drops the
old buffer: 4096 rounds of allocate-copy-overwrite at 64 KiB each — **256 MiB
of churn — peaks at 1 660 KiB**. Three points on that axis are now measured and
they agree with D-186 as written:

| destination | overwritten | measured |
|---|---|---|
| managed local binding | **drops** | 1 660 KiB (TM-127 control A) |
| **managed struct field** | **drops** | **1 660 KiB (this decision)** |
| `wild T->` element | **does NOT drop** | 125 184 KiB (TM-127) |

**The decision.** *`Bytes` declares no `free`, and `src/core/bytes.npk`'s header
says why in the file rather than only here. `0.0.4.md` §3's list is corrected.*

*Alternatives declined:*

- **Ship a no-op `bytes_free` "for symmetry with `Vec`".** The symmetry is
  false; the types are in different memory regimes and that is the design.
- **Ship one that zeroes `len`.** That is `bytes_clear`, which exists and is
  named for what it does.

### TM-134 — `uint64`'s maximum is a CONSTANT spelling, not an expression; D-148 does not say so, and this cost a red run twice in one hour
**2026-09-05, cycle 0.0.4. A language fact, measured at pin `0dfddac`, that the
compiler's `LEXICAL_REFERENCE.md` states incompletely.**

**What the document says.** D-148: *"Values outside the envelope are constructed,
not spelled: `uint64` above 2⁶³−1 (`0u64 - 1u64` is the maximum) …"* And the
envelope really is the **signed** 64-bit one regardless of suffix — measured:
`9223372036854775807u64` scans, `9223372036854775808u64` is `NITPICK-LEX-004`,
and so is `18446744073709551615u64`.

**What it does not say.** *`0u64 - 1u64` works as a `fixed` initialiser and
TRAPS as a runtime statement.* Measured both ways, with the un-foldable form
(`0u64 - argv.len`) as the control:

| spelling | result |
|---|---|
| `fixed uint64:U64_MAX = 0u64 - 1u64;` | **correct value** — verified `/2 == int64 MAX` and `%10 == 5` |
| `uint64:u = 0u64 - 1u64;` in a body | **`IntOverflow`, exit 93** |
| `0u64 - z` where `z` comes from `argv` | **`IntOverflow`, exit 93** |

D-210 makes plain integer arithmetic trap, an unsigned `0 - 1` underflows, and
only the constant-folded form never executes the subtraction. Both facts are
correct on their own; the sentence that joins them is missing.

**It cost a red run TWICE IN ONE HOUR**, which is why it is a decision and not a
comment. `tests/unit/bytes_put_int.npk` exited 93 on its first green compile —
and the diagnosis was briefly that `put_int` was negating at `int64` MIN, which
is the failure that test exists to catch, so the wrong conclusion was the
*available* one. Then `tests/unit/limits_named.npk`, written minutes after the
first was fixed and documented, made the identical mistake.

**The decision.** *Where this library wants `uint64`'s maximum it declares a
`fixed` constant and uses the name. The expression is never written in a
function body. Both test files carry the reason at the declaration.*

**And the narrowing rule beside it, since they were met together:** there is no
checked narrowing (TM-105), so `d =>! uint8` is the only spelling and TM-105
requires the range check to be written by hand — in `bytes_put_uint` it is
written **by construction**, `d = x % 10u64` giving `d ∈ [0,9]`, and the comment
says so rather than leaving a bare `=>!`.

*Alternatives declined:*

- **Treat it as a compiler defect and stop.** It is not one: both behaviours
  follow from decisions that are individually correct and documented. What is
  wrong is a documentation gap in a sibling repository, which this library
  records and reports rather than fixes.
- **Use `9223372036854775807u64 * 2u64 + 1u64`.** It traps for the same reason,
  and it is arithmetic a reader has to verify instead of a name.
