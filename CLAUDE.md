# CLAUDE.md

Guidance for Claude Code sessions working in this repository.

## What this is

`ntime` — a date, time and time-zone library for **Nitpick**, the
safety-critical systems language at `../../nitpick`.

**Status: cycle 0.3, the host boundary, IN PROGRESS — 0.3.0, the clocks,
DONE (2026-10-08): `src/host/` reads the machine's clocks; 0.3.1, the purity
boundary's instruments, DONE (2026-10-08): `check_purity`'s ban list reviewed, and
the library's emission read beside the spelling checks; and 0.3.2, the system
zone, is next. Cycle 0.2 CLOSED
(2026-10-02), archived at `meta/roadmap/done/0.2/` — instants and timestamps:
`Instant` and its two clocks, `Timestamp` and its one constructor, the
conversions to and from the civil scale in UTC with their exhaustive gate on
every run, and the `Duration` interop — after cycle 0.1, the civil calendar,
CLOSED 2026-09-26 and archived at `meta/roadmap/done/0.1/`.**

**After cycle 0.3.1: the purity boundary's instruments.** `check_purity`'s ban
list is the review's (TM-252): every bare-name builtin and every synchronous
public prelude function of the pinned compiler that reaches past the
program's own memory — forty-three names in seven classes, where cycle 0.0.3
guessed six, which a function calling `hardware_concurrency()`,
`read_stdin()`, `chain_depth()`, `arena_make()` or the prelude's `std_out()`
passed — each matched as a whole name called, so a pure `reopen` is no call
of `open`. *(The asynchronous prelude names that do and are not on it — the
functions `text_read_line`, `text_write_str` and `text_write_line`, and the
methods `ByteReader.seek` and `LineBufWriter.flush` — are callable only from
an `async func`, which `check_call_edges` refuses in `src/` unless it is
generic — and a generic one the arm bill refuses instead, its `await` or
spawn arming `DeadlineExceeded`, which no consumer owes: TM-252's dated
note, from the subcycle's verification, 2026-10-08, where this said "every
bare-name builtin and public prelude function", and from its fix's, where it
called the generic case a hole.)*
`check_host_isolation` reads every name `src/host/` makes public, `HostClock`
among them (TM-253).
And **the library's emission is read beside the spelling checks**, before
`opt`: `check_call_edges` follows every call a function of `src/` outside
`src/host/` makes in `npkc`'s output for the umbrella, through the prelude,
and holds what it reaches to a reviewed allowlist — the allocator, the string
floor, the error route and LLVM's arithmetic — so `check_purity` is no longer
the only thing that answers "did this module touch the kernel" (TM-250,
`meta/OPEN_QUESTIONS.md` O-X9 answered); and `check_wide_types` holds every
integer wider than `i64` in that emission to `SPAN_MODEL.md` §5's sites,
spelled or not, so a call's wide result is a finding (TM-251, O-X11
answered). Neither reads a generic function nobody instantiates in the
umbrella — `src/core/vec.npk`'s nine — which the spelling checks read.
*(Both read them since cycle 0.3.2, in the emission of
`tests/unit/generic_instances.npk`, which instantiates every generic function
`src/` declares — TM-254, `meta/OPEN_QUESTIONS.md` O-X12 answered.)* The
cycle README's two plants, a `mono_now()` in `src/cal/cal.npk` and a
`host_now_utc()` in `src/fmt/fmt.npk`, fail by name: a full run over a copy
holding both is RED, four checks naming them. The self-check plants 112
tree-check violations. A full invocation is **134 units green** at pin
`5fbaf4a`.

**After cycle 0.3.0: the clocks.** `src/host/` has a body. `host_now_utc`
reads `CLOCK_REALTIME` through `sys` into a 16-byte `timespec` and builds its
`Timestamp` through `timestamp_of`, whose refusal of a `secs` outside the range
is `HOST.md` H-8's range check; `host_now_instant` is the floor's `mono_now()`,
`never fails`; `host_now_boot` reads `CLOCK_BOOTTIME` and refuses, in a
private `timespec_ns`, a reading an `int64` of nanoseconds cannot hold before
it multiplies; and `host_clock_res` asks `clock_getres` — syscall 229, which
no file of the compiler names and the kernel's table does — about the clock a
`HostClock` names, `host`'s own enum, since `InstantClock` must not gain a
realtime clock (TM-248). The kernel's errno is forwarded verbatim, so `host`
declares no error: it owes **11** arms and the umbrella **13** still,
re-exporting 81 <!-- [[sweep: lib_reexports=81]] --> names. **`BUILD.md` B-17
draws `host` → `span`**, because both readings' types are sealed and only
`span` builds them (TM-247). **`tests/unit/host_clocks.npk` reads every clock
under `// stress: 40`** and asserts each reading ADVANCES — H-3's "two calls
are two syscalls", which a cached or computed reading fails — with ten of
fourteen one-line mutants of the module red at their exits and the four no
test can see named in its header and under H-3 (TM-249). **`instant_of` keeps
its name**: the author's answer to Q-7 (TM-248). And first, in a commit of its
own, **`check_int128_sites` reads a numeric literal's width suffix** as it
reads a type's name, so `(3i256 * 5i256) =>! int64` — a computation of
literals alone, which narrowed a constant in silence — is a finding outside
§5's sites (TM-246). *(What it reads is spellings: a wide value no width is
spelled for — a call's result — passes it, as it always has, and
`meta/OPEN_QUESTIONS.md` O-X11 holds that, dormant, for 0.3.1's planner — the
subcycle's verification, 2026-10-08. Answered at cycle 0.3.1: `check_wide_types`
reads the emission's types, TM-251.)* The self-check plants 95 tree-check
violations. A full invocation is **134 units green** at pin `5fbaf4a`.

**After cycle 0.2.4: cycle 0.2's close.** The cycle audit (ACCEPT, twenty-two
findings: eight contradictions, two dormant, five stale, seven cosmetic; no
memory fault and no silent wrong answer) was triaged in three subcycles, every
finding fixed but the two that are the workbench's: **0.2.4a**, the
instruments (TM-238 … TM-240), **0.2.4b**, the library's findings (TM-241 …
TM-245), and **0.2.4**, the close — `ROADMAP.md`'s two sentences that said
`check_purity` goes live at 0.3, and `src/host/host.npk`'s third, dated (the
audit's S4); cycle 0.2's records
moved to `meta/roadmap/done/0.2/`, the links the move broke in the move's own
commit and every plain mention after it; cycle 0.3's README given what cycle
0.2 hands it — `meta/OPEN_QUESTIONS.md` Q-7, which is the author's, and what
the next adoption owes; and `meta/roadmap/0.3/0.3.0.md` written. **Three
items reached the close after the audit, a row of the triage each.**
`check_int128_sites` reads a wide type's NAME and not a literal's width
suffix, so `(3i256 * 5i256) =>! int64` passes it — it compiles, and narrows
a constant in silence; an `int64` beside an `int256` literal is
`NITPICK-TYPE-007`, so only literals alone widen unnamed *(among spellings: a
call's result is wide with no width spelled where it is used, and no check of
spellings sees it — cycle 0.3.0's verification, `meta/OPEN_QUESTIONS.md`
O-X11)*, and `src/`'s one wide literal stands in a function §5 marks — handed
to 0.3.0's first step, whose plan drafts the decision. TM-241's
*"within 9 223 372 037 seconds"*
reads *"less than"*, by a dated note. And `meta/specs/GLOSSARY.md` notes
that *an instant* in prose is a point on the UTC timeline, what a
`Timestamp` holds — the workbench's question 22 — and leaves
`ZonedDateTime`'s field `instant` to cycle 0.6. The gate
stands as 0.2.2 left it, both members on every run. A full invocation is
**133 units green** at pin `5fbaf4a`.

**After cycle 0.2.4b: the cycle audit's library findings.** **`timestamp_add`
checks its operand before it adds** — `t.secs` against the range,
`ETimeValue`, `YearRange` — so it answers or refuses whatever it is handed,
where a `secs` forged near `int64`'s ends trapped `IntOverflow` in the add, the
borrow or the carry before `timestamp_of` ran (TM-241). **`instant_since`
computes in `int128`** and refuses a difference past `Duration`'s range,
`Overflow`, where a pair `instant_of` builds trapped; `SPAN_MODEL.md` §5 has a
row for every site it said it had, six new, and `SAFETY.md` S-12 names its
exceptions — `instant_add` and the four `Duration` constructors, `never fails`,
the trap their check (TM-242). **M-3 says what the type enforces** — no
conversion function, no implicit conversion, no cast, no literal, no write —
and names what it cannot refuse: an `Instant` built by `instant_of` from a
`Timestamp`'s numbers, a construction in writing, which `probe20g` runs
(TM-243); whether that constructor should say it takes a raw reading is the
author's, `meta/OPEN_QUESTIONS.md` Q-7. **Every contract comment is written as
its live clause would be** — `result` where it wrote `answer`, a widening, a
`raw` — and measured: of forty-three, thirty-nine compile as live clauses at
the pin, and four wait on a `pure` callee; P-3 asks a contract of what checks a
range, and `civil_to_utc` and `instant_since` carry theirs (TM-244). **O-N34 is
restated here**: the refusal of the `#unreachable()` statement form is the
compiler's defect, not the language's rule (TM-245). A full invocation is
**133 units green** at pin `5fbaf4a`.

**After cycle 0.2.4a: the cycle audit's instruments.** Cycle 0.2's audit
(ACCEPT, twenty-two findings) found instruments that passed a planted violation
in silence, and each reads what its row says now. **`check_constants_named`
holds an owned number to its owner's PLACE** — `core`'s is
`src/core/limits.npk` alone, where `86400i64` in `src/core/bytes.npk` passed it
— **and every bound that file declares by its VALUE**: `253402300799i64`
written in place of `NTIME_SECS_MAX` is a finding, the folded
`NTIME_DURATION_NS_MIN` is read as −2⁶³, and the small values in
`nitpick-regex`'s `_SMALL` set are excepted — today `NTIME_PARSE_MAX`'s 128
alone (TM-238). **`check_no_view_returns` reads an optional as what it
holds**, so `uint8[]?` and `cstring?` are views (TM-239). **`check_int128_sites`
reads every integer wider than `int64`**, fourteen types, where an `int256`
intermediate passed it; and `TESTING.md` V-1 says what that check guards and
what no check does — S-15b's range check before every `=>!` is review's
(TM-240). The self-check plants 92 tree-check violations, each new one red
against the check before it, and `src/` changed in comments only. A full
invocation is **131 units green** at pin `5fbaf4a`.

**After cycle 0.2.3: the `Duration` interop.** `src/span/` adds four
constructors to the prelude's `Duration` — `duration_mins`, `duration_hours`,
`duration_days` and `duration_weeks`, each one line over `duration_secs`,
`never fails`, the prelude's trap past ±292 years their range check, and a
day exactly 86 400 × 10⁹ nanoseconds and NOT a calendar day — each held to
its exact product over its whole range, every 262nd argument for the minutes
and every one for the rest, and the trap asserted one past a day's two ends
(TM-233).
**`timestamp_add`** moves a `Timestamp` by a `Duration`: the truncating `/`
and `%` split it, one borrow or one carry re-establishes M-7, and
`timestamp_of` builds the answer, so its range check is the constructor's,
`ETimeValue`, `YearRange` (TM-234); **P-4's stand-in reaches it** through
a hundred thousand seeded additions held to an `int128` count of nanoseconds,
forged inputs and every boundary it decides, the forged the only cases that
see a `timestamp_add` writing its own `Timestamp` literal behind a range
check of its own (TM-235). **And
`timestamp_since`** gives the nominal span between two in `int128`, refused
past `Duration`'s two ends — `NTIME_DURATION_NS_MAX` and
`NTIME_DURATION_NS_MIN`, named in `src/core/limits.npk` — and taken at each
end exactly, from both sides (TM-236; `check_int128_sites` holds it to §5's
marked row). `timestamp_until` is cycle 0.7.3's, beside `date_until`
(TM-237). `span` owes **11** arms and the umbrella **13** still, and the
umbrella re-exports 76 names. A full
invocation is **131 units green** at pin `5fbaf4a`.

**After cycle 0.2.3a: the instruments.** The tree checks' family is one list:
`check_check_registry`, built first, reads `TESTING.md` §2's two tables,
`checks.LIVE`, `checks.PENDING` and the checks `run.py` drives outside step 5
from the tree's text and fails any drift between them, and V-1a's three
numbers — 20 rows, 17 live, 3 pending — are tagged and held to it (TM-227).
**`check_no_view_returns` is live**: no function in `src/` returns a slice, a
`cstring` or a type that holds one but `bytes_view`, whose exemption is
re-derived from its reason on every run (TM-228, `SAFETY.md` S-22). **O-X6 is
answered**: `SPAN_MODEL.md` §5's table names the `int128` sites in a column
of its own and N-20 states no count — three marked, `bytes_put_int`'s loop
measure among them, a site since cycle 0.1.0b that no row named — and
`check_int128_sites` is live against it (TM-229, TM-230). **And
`check_constants_named` reads a literal as the compiler's lexer does** —
every base, `_` wherever it stands, every width, a character literal's code
point, a bound after `..` — where sixteen spellings of 86 400 and
1 000 000 000 passed it, measured; part E's third half asks the pinned
compiler about every spelling (TM-231), and 1 000 000 000 is `core`'s alone,
read by name everywhere as 86 400 is (TM-232). The self-check plants 82
tree-check violations, and `src/` changed in comments only. A full
invocation is **126 units green** at pin `5fbaf4a`, 4 pending.

**After cycle 0.2.2: the conversions, and cycle 0.2's gate.** `src/span/`
converts between the absolute scale and the civil one, read as UTC — every day
86 400 seconds (M-11). `timestamp_to_utc(t)` gives a `Timestamp`'s civil
reading and never fails: its day number is a FLOOR division of the seconds —
`-1 s, 500 000 000 ns` is 1969-12-31T23:59:59.5, and a truncating `/` would
hand `civil_time` a second of −1 — and the two refusals no `Timestamp` can
meet are `?| #unreachable()` (`SAFETY.md` S-15c). `civil_to_utc(c)` gives the
`Timestamp` a civil reading names, through `timestamp_of`, so it fails
`ETimeValue` only for a reading forged through the opt-out, and is total over
every field value (TM-222). **The gate**: both sides of every day boundary in
the range — a day's first instant alone cannot tell a truncating split from a
flooring one — and every second of 512 days a seeded xorshift chooses, each
both ways, each direction handed a walk's value:
`tests/unit/sweep/every_day_boundary.npk` and `every_sampled_second.npk`,
7 304 484 dates and 44 236 800 seconds. With them the `sweep` stage costs about
43 s, so `BUILD.md` B-9's threshold is 60 s from here (TM-224). **P-4's
stand-in reaches `civil_to_utc`** through `tests/unit/civil_to_utc_edges.npk`,
whose refusing cases are forged in `wild` storage — the only cases that see a
conversion writing its own `Timestamp` literal, which passes everything else,
measured (TM-225) — and `tests/unit/utc_vectors.npk` holds sixteen instants to
their civil readings, `timestamp_order.npk`'s chain among them. **86 400
belongs to `core` alone** in `check_constants_named`'s owner map: `span`
divides by `NTIME_SECS_PER_DAY`, read by name, and `SAFETY.md` S-16 moved with
the map (TM-223). **And a point on the UTC scale is no longer called "a
wall-clock reading"** — `meta/specs/GLOSSARY.md`'s words for a civil one — at
the sites that did: six reworded, and TM-215 and TM-216 marked (TM-226).
`span` owes **11** arms and the umbrella **13** still, and
the umbrella re-exports 68 names. A full
invocation is **126 units green** at pin `5fbaf4a`.

**After cycle 0.2.1: `Timestamp`.** `src/span/` holds `Timestamp` beside
`Instant` — `{ sealed int64:secs; sealed uint32:nanos; }`, deriving `Eq`,
`Ord`, `Clone`, `Debug` and `Copy`, the derived `Ord` its comparison, seconds
first (M-6) — and one constructor, `timestamp_of(secs, nanos)`, which refuses
a `secs` outside the range (`ValueFault.YearRange`) and a `nanos` outside one
second (`NanoRange`) rather than carry it: one spelling per instant, M-7
(TM-219, TM-220). **`VERIFICATION.md` P-4's stand-in** is
`tests/unit/timestamp_construct.npk` — every boundary the constructor decides,
from both sides, 132 pairs — beside the seal's two probes, `probe21` and
`probe21b`; `tests/unit/timestamp_order.npk` asserts the order on the type, a
negative second with a positive remainder among its neighbours. **M-3 is
asserted at the type in both directions** — an `Instant` where a `Timestamp`
is taken, and the reverse, `NITPICK-TYPE-007` — **and through `=>!`**, which
refuses both, `NITPICK-TYPE-032`: six probes, one refusal each (TM-221).
`Instant`'s `ns` stays sealed and readable — the author's answer to the
workbench's question 15, recorded in TM-219. **And 0.2.0's unit had a mutant it
could not see**: exit 14 read only a `Monotonic` clock — tag 0, the vacant
value — so an `instant_add` that hard-coded `Monotonic` passed it; a `Boottime`
reading goes through `instant_add` and through the `Vec` now, and every exit
of the unit has been seen red on a mutant. `span` owes **11**
<!-- [[sweep: arms_span=11]] --> arms and the umbrella **13**
<!-- [[sweep: arms_lib=13]] --> still — no new identity — and the umbrella
re-exports 66 names. A full invocation is
**122 units green** at pin `5fbaf4a`.

**After cycle 0.2.0: `Instant`.** `src/span/` has a body: `Instant`, a
reading of one of two clocks — `{ sealed int64:ns; sealed InstantClock:clock; }`,
`InstantClock` an enum, `{ Monotonic; Boottime; }` — and four operations:
`instant_of`, the one constructor; `instant_since` and `instant_cmp`, which
refuse a pair from two clocks with `ETimeValue` (`ValueFault.ClockMismatch`,
appended); and `instant_add`, which keeps its clock (TM-215, TM-216;
`TIME_MODEL.md` M-2 and M-4 and `HOST.md` H-6 amended). **A timeout cannot be
written against a wall clock** *(by accident: `instant_of` takes any `int64`,
so an `Instant` built from a realtime reading's numbers is written, and runs —
cycle 0.2.4b, TM-243)*: a consumer can neither build an `Instant` by a
struct literal nor edit one — `NITPICK-TYPE-079`, `probe20` — and there is no
conversion to a `Timestamp` — `NITPICK-RESOLVE-002`, `probe20b` (TM-218). The
clock is read as the sealed field, so O-X3 is settled without an accessor.
**The S-6 generator was wrong, and only `span` could show it**: it named an
identity by the module whose `fail` site raised it, where the compiler names
it by the module that declares it, so `span` raising `cal`'s `ETimeValue` would
have published a `span.ETimeValue` that does not exist; it names the declaring
module now, and a fourth calibration specimen, `probe11_relay_lib`, was red
before the fix (TM-217). `span` owes **11** arms and the umbrella **13** still
— no new identity — and re-exports 64 names. A full invocation is **114 units
green** at pin `5fbaf4a`.

**After cycle 0.2.0b: `Vec<T: Copy>`** — `nitpick-regex`'s answer to the
question TM-194 left open, ported (its RX-188). The type is
`struct:Vec<T: Copy>` and every verb states the bound, so the compiler refuses
an owning element wherever it is written — at the type, at each turbofish and
at each verb's call — where until now only `vec_at`'s call was refused; the
restriction TM-132 made is the type's, and the four element drops `SAFETY.md`
S-18d rested it on are owed at no `T` the type admits (TM-214). **Nothing
changed at a `T` it admits**: of the tree's 128 `.npk`, the 89 that compile both
with the bound and without it emit byte-identical IR. Three verdicts moved:
TM-150's churn pair, which measured `vec_pop` and `vec_clear` at `T = string`,
is refused and retired — the instrument keeps its two known leaks, `probe06b`
and `probe12` — and `generic_owning_copy/case5` names six sites where it named
two. No element check is added: `Copy` states this library's element rule
whole, and a `Copy` element that holds a pointer is S-18e's and S-22's. A full
invocation is **111 units green** at pin `5fbaf4a`.

**After cycle 0.2.0a: the adoption of compiler `5fbaf4a`** — the compiler's
last landing before its pause, carrying its landings 67 … 82. At the new pin
the unchanged tree ran `RED -- 105 unit(s) of 113`, exactly the eight files
holding a `cstring` copy — fifteen, each `NITPICK-TYPE-046` once `cstring`
owns what `to_cstring` makes (the compiler's D-328) — so an `environ()`
element is read in place and `to_cstring`'s answer moved out of its `Result`
(TM-208). **The runner holds what the compiler's runners hold**: the manifest
pins `triple` and `datalayout`, the layout is held to what the pinned `opt`
derives and every emission's two `target` lines to both (`BUILD.md` B-1a,
TM-209); and a refusal names each code once PER SITE it is reported at
(B-7c, TM-210), which four headers did not. **`Pod` is retired into the
prelude's `Copy`**: `vec_at<T: Copy>`, the umbrella at 58 names (TM-211).
CI is pinned to `5fbaf4a` and ASSERTS the compiler's emission, `npkc.ll`,
against the pinned commit's row (TM-212, the ecosystem audit's EC6); the
budget's rule reads as the compiler charges it — every identity a reachable
`fail` site raises, public or private (TM-213, EC3); and TM-202's re-read is
this repository's reader only (ED1). The lexer moved a character literal's
width and nothing `lexical.py` mirrors; `NITPICK-BORROW-015` is in the pin and
reaches no file here; the hold on `for`, `loop` and `till` is lifted. The
self-check plants 12 of V-14's 13 cases. A full invocation is **113 units
green** at pin `5fbaf4a`.

**Before it, cycle 0.1's close:** `meta/roadmap/done/0.2/0.2.0.md` was written at
the close. **The close's second half triaged the cycle audit's nineteen
findings**, every one fixed but for the check half of one, which a decision
places on cycle 0.2.3, and the four the audit asked to be fixed rather than
declined are fixed: part E's program asks the pinned compiler about thirteen
named forms, each literal's value asserted, and is refused at the older pin, so
the block string's close — the one lexer move between the kept pins, which the
seven-form program passed at both — is a red run (TM-202); the error budget
counts identities qualified by their module, as the compiler does, and holds
each to the module `SAFETY.md` S-4 names for it (TM-203); S-22 names its one
exemption, `bytes_view`, whose lifetime is S-18e's, and its check is cycle
0.2.3's (TM-204); and `VERIFICATION.md` no longer says every index traps. Every
arm bill a page writes is tagged and held to the generated one — the calendar
costs 11 <!-- [[sweep: arms_cal=11]] --> and the umbrella 13
<!-- [[sweep: arms_lib=13]] --> (TM-205); the two whole-tree scanners read the
same under either decoding (TM-206); and `CALENDAR.md` C-12's totality is
asserted at its edges by `tests/unit/civil_total_edges.npk`, seen red on an
`int32` mutant and on nothing else. The self-check plants 44 tree-check
violations. `src/` changed in comments only. A full invocation is **113 units
green** at pin `c970483`.

**After cycle 0.1.5's first half: the harness reads source as the compiler
does, and the audit that closes the cycle was next.** Measured at
the close's planning, eight shapes of source made the harness disagree with
the compiler's lexer at `c970483`, and six of them passed a violation silently:
a lone CR in a `//` comment, a `//` inside a `/* */`, a `'"'` character
literal, a `//` in a template's text and an escaped `use` path each hid a
division, a clock call, a fourth `error:` or an import of `host` from the check
built to find it; the other two read a comment as code. **Since TM-199 every
`.npk` the harness opens is read by `harness/lexical.py`** — `nitpick-regex`'s
reader, ported statement for statement — as bytes, its comments and literals
by the compiler lexer's rules and its import paths decoded; **and since TM-200
every check matches TOKENS across the lexer's whitespace** over a file's whole
text, where `mono_now ()`, a `[` on the line after `v.items`, and `error` then
`:ETimeOops` on the next line had each hidden from a pattern matched against
one line. The self-check plants 40 tree-check violations (23 before) and, in
its part E, asks both the reader and the pinned compiler about one text of
every form, so a re-pin that moves the lexer is a red run *(the program held
seven forms and the one move between the kept pins passed it — the cycle
audit's C1, and TM-202)*. **And the close's corrections**: the public
`README.md` no longer says there is no code, nor that importing `ntime` costs
three arms — the calendar costs 11 and the umbrella 13 (`SAFETY.md` S-4); `tests/probe/README.md` lists every probe; and the two
checks cycle 0.0 deferred to this cycle, which it did not build, are re-homed
with their reasons (TM-201). No library code changed. A full invocation is
**112 units green** at pin `c970483`.

**After cycle 0.1.3c: `Vec` is move-only by construction** — the
author's answer to the workbench's question 9, and `nitpick-regex`'s design,
ported. `Vec<T>`'s last field is `hidden string[0]:move_only` — zero bytes,
and its element owns — so a copy of a `Vec`, one assigned over another, or a
copy of anything that holds one is `NITPICK-TYPE-046` where it is written
(TM-193, `SAFETY.md` S-18g); against the library before, each compiled and read
freed memory through its second handle. **`vec_at` takes `T: Pod` and reads
through a loan** (TM-194, S-18h): `Pod`'s `pod_copy` lends its `self`, so an
owning type cannot implement it as declared (`NITPICK-TYPE-047`), and
`vec_at` at an owning `T` — which used to REMOVE the element — is refused at
the call, `NITPICK-TYPE-017`, which `generic_owning_copy/case5` asserts now.
The loan is the marker's consequence: at `c970483` the address of a lent owner
is `NITPICK-TYPE-085`, so a pointer reader could not be handed a `Vec` its
caller holds on loan. **`Bytes.body` is `hidden`** (TM-195): a consumer's write
through its pointer is `NITPICK-TYPE-080`, and the capacity is
`bytes_capacity`. **TM-150's churn pair is committed** with `heap:` bounds
(TM-196) — two million push-then-pop cycles at `T = string` peak at 120 bytes,
the same with `vec_clear` at all 48 000 096 — and **A′ is `VERIFICATION.md`
rule P-1b** (TM-197), which strikes Q-6. **`Pod` is interim** (TM-198): the
compiler's D-327, ratified during this cycle and in no pin of ours yet, makes
`Copy` a prelude marker trait, and the re-pin that carries it replaces `Pod`
with it — a confined edit, the trait's one block, one bound, one call, one
umbrella line, three test impls *(made at cycle 0.2.0a, the adoption of
`5fbaf4a`: TM-211)*. The umbrella re-exports 59 names *(58 from then, and 64 since cycle 0.2.0)* —
`Pod` and `bytes_capacity` joined — and eight files' managed memory is held to
the runtime's count *(six since cycle 0.2.0b retired the churn pair,
TM-214)*<!-- [[sweep: heap_bounded=6]] -->. No arm bill moved. A
full invocation is **112 units green** at pin `c970483`.

**After cycle 0.1.4c: the adoption to compiler `c970483`** — the end
of the compiler's 1.6.0 chain, carrying its DEF-95 to DEF-106 and DEF-108. No
library code changed. **Two defects this repository raised have landed, and
each reproduction is now a regression test with its old verdicts as the
control**: a move out of `fixed` storage is refused `NITPICK-TYPE-084` (O-N20,
the compiler's DEF-99), so `tests/probe/defect/fixed_move_out/`'s three cases
carry that marker and none is exempt (TM-189); and an imported `fixed`
binding's type resolves in its declaring module (O-N23, DEF-105), so its
reproduction is committed at last, as `tests/probe/defect/fixed_import_scope/`
— seven cases, the loud form compiling and every silent one reading correctly
(TM-192). **The hold on cycle 0.5's version string lifts** (TM-191): a
consumer's `move` of an imported `pub fixed string`, and Z-6's obvious `pass`,
are refused where written, so Z-6 reads it by `.clone()`. **Measured first**:
at the new pin the unchanged tree was RED at 90 of 91, and a per-file sweep of
all 108 `.npk` at both pins moved exactly four — the three exemptions, and
`probe13d`, whose generic bare-pointer accessor the compiler's DEF-104 refuses
as a pass-out of a `T` place through a pointer (`NITPICK-TYPE-047`); it reads
at `int64` now and still returns its planted sentinel unguarded (TM-190).
`src/core/vec.npk` compiles unchanged: `vec_at` reads through a local
`#wild_slice`, and `vec_pop` already spelled `move`. No function anywhere falls
off its end (`NITPICK-FLOW-001`, DEF-108). CI pins `c970483` in the same
commit. A full invocation is **101 units green** at pin `c970483`.

**After cycle 0.1.4b: the managed-memory gate.** For the first time
the harness asserts MANAGED memory. D-151's exit-0 trap sees only `wild` blocks
(TM-106), and the `ulimit -v` pair that stood in for a gate since cycle 0.0.4
(TM-131) was measured by hand and never run. Now a `// heap:` marker holds the
runtime's own `NPK_HEAP_STATS` report — bytes requested, the high-water mark
of bytes live, allocations — to a file's bounds on both legs, and a `// cap:`
marker runs a program again under a 64 MiB address-space cap (`TESTING.md`
V-17). Six files carry bounds: each leaking
twin's high-water mark is at least its leak's arithmetic, so the instrument
meets a known leak on every run; each remedy's is under a ceiling and its
allocation count over a floor, so an emptied remedy is red; and the two `Bytes`
tests' ceilings catch a growth that keeps its old bodies, which
`bytes_growth` otherwise passes at exit 0. Every ceiling is the geometric mean
of the correct program's peak and a leak mutant's (TM-185), and every bound was
seen red on its mutant (`meta/roadmap/done/0.1/0.1.4b.md` §7). **The cap's control
moved**: at compiler `c3bdae2` a program that allocates nothing needs about
10.5 MiB before `main`, where `/bin/true` needs 2.75 MiB, so the control is
that floor program, built by the same toolchain (TM-186). **And the count found
a defect**: `bytes_take` handed back a VIEW of the sink typed as an owned
`string` — reused or grown, the sink rewrote or freed the caller's text —
from cycle 0.0.4 until now. It copies now, and `bytes_growth` asserts both
(TM-188, `SAFETY.md` S-18f). The self-check plants **8** of V-14's **9**
faults; no test file was added, so the unit count is 0.1.4's.

**After cycle 0.1.4: the civil cross-oracle.** Every date of years
1 … 9999 — 3 652 059 of them, the whole of Python's range — agrees with
Python's `datetime` in its year, month, day, day number, weekday, ISO week
date and day of the year (`CALENDAR.md` C-18, `TESTING.md` V-6, TM-179). The
corpus, `tests/fixtures/civil/civil_oracle.npk`, is written by
`tools/gen_civil_oracle.py` from `datetime` and nothing else — one row per
year: the day number of its 1 January, its length, and a digest of nine
fields of every one of its days (TM-180) — and a sixth `sweep` member,
`tests/unit/sweep/every_oracle_date.npk`, folds the same from `src/cal/`'s
answers and must equal every row (TM-182). **Exhaustive, where C-18 first
asked for a sample**: measured, explicit rows enough to mean anything are
33.7 MB of source and 44 s of `npkc`, and a sample taken every seventh day
meets every February 29th of a 400-multiple year or none of them; the digest
puts the whole range in 1.0 MB. **The negative half of the range has C-16's
round trips and nothing external** — Python stops at year 1, and a defect
confined to negative dates passes this member with the full count, measured.
The corpus is generated and never edited: the subcycle that changes its
generator regenerates it and compares it byte for byte (TM-183).
**A compiler defect, O-N23**, found at planning: an imported `fixed`
binding's declared type resolves in the IMPORTING module's scope, so a table
imported without its row type is refused `NITPICK-TYPE-001` at its own line,
and beside a same-named struct it silently takes that struct's layout. The
member imports `OracleYear` by name beside `ORACLE` (TM-181), which turns
the silent form into a `NITPICK-RESOLVE-001` refusal, and the defect holds
cycle 0.5's zone tables. Every check the member makes was seen to fail on a
mutant — `meta/roadmap/done/0.1/0.1.4.md` §7's twenty-one rows. No library code
changed. A full invocation is **91 units green** at pin `c3bdae2`; the six
sweeps cost 22.2 s of it.

**After cycle 0.1.3b: the owning-field check's premise,
re-measured.** `check_no_owning_fields` rested on *"an owning field is one the
language will not let a table hold"*, and **measured at every pin this
repository has kept, `0dfddac` to `c3bdae2`, that is false**: a `fixed` table
holds a `string` and a struct holding one, and reads that do not move them
work (`tests/probe/probe17_fixed_owning_reads.npk`). What the language refuses
is a COPY of an owning row or element — `NITPICK-TYPE-046`, the read
`SAFETY.md` S-17's accessor pair does (`probe17b`, `probe17c`) — and what it
does not stop is a MOVE out of `fixed` storage, which **compiles and faults**:
a compiler defect, reproduced with its control in
`tests/probe/defect/fixed_move_out/` and raised — the workbench registry's
O-N20, the compiler's DEF-99, whose refusal, `NITPICK-TYPE-084`, is at no pin
of ours yet. So the rule stands on the reason that holds (`SAFETY.md` S-19b,
TM-177), and the check now sees an owning ELEMENT, an owner two structs down,
and a field's type rather than its name — three blind spots, each planted and
seen red first. Cycle 0.5's version string (`ZONE_MODEL.md` Z-4, Z-6) is held
behind the defect (TM-178, `meta/OPEN_QUESTIONS.md` O-X10). No library code
changed. A full invocation is **90 units green** at pin `c3bdae2`.

**After cycle 0.1.3: the derived fields, and cycle 0.1's gate
complete.** `src/cal/` computes a date's **weekday**, its **day of the year**
and its **ISO week date** from its day number and stores none of them
(`CALENDAR.md` C-13 … C-15), and builds a date back from an ordinal date and
from an ISO week date — seven public names, `weekday`, `day_of_year`,
`ordinal_to_date`, `iso_week_year`, `iso_week_number`, `iso_weekday` and
`iso_week_to_date` (TM-169), so the umbrella re-exports 57. Hinnant's formula
is one private `days_from_civil` and `date_to_days` its one-line widening
(TM-170). **Every weekday goes through one private `weekday_index`**, whose
`%` correction is range-checked by an `#unreachable()` line before `weekday`
manufactures a `Weekday` tag with `=>!` — a tag the compiler does not check,
and one outside the enum makes an exhaustive `pick` fall through silently
(TM-171, `SAFETY.md` S-15c). **The gate is complete**: both round trips,
monotonicity, month lengths and — on `tests/unit/sweep/every_civil_date.npk`'s
walk — the weekday cycle, a count begun at −9999-01-01's Monday (C-17). Two
new `sweep` members check the ordinal and ISO week dates against walks of
their own rules over every date in the range, hand each constructor the
WALK's values rather than the values under test, and ask it to refuse one
past every bound (`TESTING.md` V-4b, TM-174): a round trip built from the
value under test passed three wrong implementations, measured. **Forty-one
vectors, derived three ways, carry C-14's boundary cases** — indexed by the
year that ENDS, because a common year beginning on a Saturday opens in week 52
or week 53 of the year before depending on that year (TM-175). `BUILD.md`
B-15's module-prefix rule is restated to what the specifications do (TM-176).
Every assertion was seen to fail on a mutant, `meta/roadmap/done/0.1/0.1.3.md` §7's
twenty-one rows. `cal` still owes **11** arms and the umbrella **13**, and the
contracts are comments — Q-6's A′, which the author chose on 2026-09-25. A
full invocation is **86 units green** at pin `c3bdae2`; the five sweeps cost
16.5 s of it.

**After cycle 0.1.2: the sweep.** `tests/unit/sweep/` holds cycle
0.1's gate (`CALENDAR.md` C-16) and two of its three riders (C-17), run in
full at -O0 and again under `opt -O2` on every full invocation: **every day
number in the range goes to its date and back** (`every_day_number.npk`);
**every civil date goes to its day number and back, each number exactly one
more than the last** (`every_civil_date.npk`, its dates generated by the leap
rule and the month table, never by `days_to_date`); and **every month's length
is the distance between consecutive month-firsts** (`every_month_length.npk`)
— 7 304 484, 7 304 484 and 239 988 cases, each program printing the count it
visited (TM-122, TM-166). **Every assertion in them was seen to fail on a
mutant** — `meta/roadmap/done/0.1/0.1.2.md` §5's fourteen-row matrix — and one
mutant, `days_to_date`'s negative-era correction one day late, breaks exactly
24 days of the range (the first of March of every negative 400-year era) and
is caught by the sweeps and by nothing else in the suite. C-17's riders are
stated in the form a wrong implementation fails (TM-167), and **the weekday
cycle moves to 0.1.3 with `weekday()`** (TM-165), so the cycle's gate
completes there. **Each sweep's declared domain is a measured denominator**,
`domain_<stem>` (TM-168): every live statement of it is tagged, so on a green
run the specification's number, the header's and what the program visited are
one number. The three sweeps cost 4.5 s together; no library code changed. A
full invocation is **81 units green** at pin `c3bdae2`.

**After cycle 0.1.1: the algorithms.** `date_to_days` and
`days_to_date` are Howard Hinnant's `days_from_civil` and `civil_from_days`,
transcribed line for line and cited in `src/cal/cal.npk`'s header (C-10,
TM-016); `date_to_days` is `never fails` and total, and `days_to_date` refuses
a day outside the range before its first addition and builds its answer
through `civil_date` (TM-162). **The range's first day was one day early from
the founding specification until this cycle**: −9999-01-01 is day **−4 371 587**, so the range
holds **7 304 484** days and `NTIME_SECS_MIN` is −377 705 116 800 (TM-161) —
found by `tests/unit/range_constants.npk`, which recomputes the constants from
the algorithm and was seen RED at the old value first, while
`tests/probe/probe07_negative_div.npk` had asserted the right number since
cycle 0.0.0 and nothing compared the two. **Every divisor in `src/cal/` is a
positive integer literal**, and `check_literal_divisors` says so on every run
(C-11, TM-163). Contracts are comments, per Q-6's recommended answer (TM-164),
and `cal` still owes **11** arms. A full invocation is **78 units green** at
pin `c3bdae2`.

**After cycle 0.1.0c: the access properties.** `Vec<T>`'s `items` is
`hidden` and its `count`/`cap` are `sealed limit<ListLen>`; `Bytes`' `body` and
`len` are sealed and `len` carries `ListLen` (TM-156) — so outside `src/core/`
the bare pointer cannot be named (`NITPICK-TYPE-080`) and the lengths cannot be
written (`NITPICK-TYPE-079`). **Every field of `CivilDate` and `CivilTime` is
sealed** (TM-157, `CALENDAR.md` C-8c): a consumer's struct literal or field
write is `TYPE-079`, so C-8's guarantee is the TYPE's again for every module
but `cal`, with `wild` storage reinterpreted by `=>!` the one opt-out.
`check_civil_literal` is retired (TM-158), `probe15` is the seal's regression
test, and `probe16`…`probe16e` pin the rest. **Nine roots owe `LimitViolated`**
(109), and the umbrella's arm bill is **13**, generated with a `limit` rule
(TM-159). **What the seal does not stop** is written where it bites: a
consumer can still write THROUGH `b.body.ptr` (D-313), and a whole-struct copy
of a `Vec` is a second handle on its block — the workbench's question 9, with
the author. O-N8 is discharged (TM-160). A full invocation is **75 units
green** at pin `c3bdae2`.

**After cycle 0.1.0b: the adoption to compiler `c3bdae2`** (the close of
its cycle 1.5). No new library behaviour; everything the new pin refused or
made false, corrected. **Every one of the tree's 48 loops states `decreases`**
(D-304) — 29 in the compiler's sweep tool's own proven shape and 19 by the
committed reading `meta/roadmap/done/0.1/decreases_read.txt`, none `unbounded`.
**The `failsafe` floor is six** — `StackExhausted` (exit 106) and
`MachineFault` (107) joined it — and a root that reaches a measured loop owes
`DecreasesViolated` (108); every root names exactly what `NITPICK-REACH-002`
asks, but for the three probes whose refusal is the point (`probe11b`,
`probe11c`, `probe11e`). `vec_reserve<T>` relocates with `ralloc`, because
D-264 refused its
element copy. **O-N18 and O-N19 have landed** and their reproductions are
asserted regression tests, each with its `aaffb87` verdict as its control. A
full invocation is **70 units green** at pin `c3bdae2`; the wall clock is
deliberately not quoted (`meta/roadmap/done/0.1/0.1.0.md` says why). The umbrella
has re-exported **48** names since cycle 0.1.0, and its arm bill — **12** — is a
generated row of `SAFETY.md` S-4 since this cycle.

**After cycle 0.0.5: the first library code, and the tzdb sized.**
TM-007's compiled-in database is **475 006 bytes** of read-only data for the
four tables and two pools, **489 310** with `POSIX_RULES` — measured, not
estimated, against a 348 KiB estimate that was wrong in four ways (TM-135).
That is inside the budget `0.0.5.md` §3 set in advance, with 4.4% to spare, so
TM-007 stands and O-X2 and O-Z1 close.

**After cycle 0.0.4: the first library code.** `src/core/` holds
`vec.npk` (`Vec<T>`, nine functions), `bytes.npk` (`Bytes`, eleven) and
`limits.npk` (thirteen named constants, eleven bounds and two unit
conversions, each with the rule that set it *("thirteen named bounds" until
cycle 0.2.4a, the cycle audit's K5)*). The umbrella re-exports **35** names,
one line each. The other five directories are
still placeholders that parse and are **replaced, not deleted**, by the cycle
named in each header — and `src/core/core.npk` survives as that directory's
LAYER NOTE, which is what the five point at. `harness/` is the runner
`BUILD.md` describes — nine stages, ten modules — and a full invocation was
**62 units green in about 62 s** at pin `aaffb87` at cycle 0.0.6's close. It
was **241 s** at
`0dfddac` on the same content; the compiler's 1.5.2d close made every emitted
module carry only the prelude functions it references, which took it to 43 s,
and cycle 0.0.6 put ~19 s back by asserting 21 more units.

**THREE things to know before touching `src/core/`, and the third is the one
cycle 0.0 paid most for.**

- **`Vec<T>` is for a NON-OWNING `T`, and since cycle 0.2.0b the TYPE says
  so: `Vec<T: Copy>`, every verb bounded, an owning `T` refused wherever it is
  written** (TM-214; the restriction is TM-132's, its reason changed at 0.0.5 —
  TM-136 — and again at 0.1.0b — TM-150). *Until 0.2.0b, as follows:*
  **O-N17 is FIXED** at pin `aaffb87`, and **O-N19 is FIXED at `c3bdae2`**:
  `NITPICK-TYPE-046` did not fire inside
  a generic function body, so `T:x = s[i]` at an owning `T` — a copy of an
  owner — compiled, linked, ran, and left two owners of one heap body (exit
  170 on the second read); the compiler's D-264 now refuses it where it is
  written, at every instantiation, and
  `tests/probe/defect/generic_owning_copy/` asserts that. It bit this file:
  `vec_pop<T>` shipped as that bare read at 0.0.4 and writes the `move`, still
  the right spelling. **The restriction now stands on one reason: four
  operations — `vec_set`, `vec_clear`, `vec_truncate`, `vec_free` — owe an
  element drop at an owning `T` and perform none**, a leak `exit 0` cannot
  see. And **`vec_at` at an owning `T` is REFUSED since cycle 0.1.3c** — it
  takes `T: Copy` (S-18h; `T: Pod` until cycle 0.2.0a, TM-211),
  `NITPICK-TYPE-017` at the call — where it used to
  REMOVE the element, `pass` of a place moving implicitly; element lifetime at
  an owning `T` still goes **at the instantiation**, where `SAFETY.md` S-18b
  and S-18d put it. **And a `Vec` is move-only** (S-18g): a copy is refused,
  a transfer is `move(...)`, and `vec_at` reads a loan, `vec_at(v, i)` — not
  `@v`. **Since 0.1.0c `items` is `hidden` and
  `count`/`cap` are `sealed limit<ListLen>`** (TM-156): nothing outside
  `vec.npk` can index the pointer or write a length, and a write inside it
  that breaks `ListLen` traps `LimitViolated`.
- **The bounds guard is the compiler's, not ours** (TM-129, S-17c). Each
  accessor lays a `#wild_slice` over `count` and indexes that, so
  `emit_bounds_guard` runs and one unsigned compare rejects both ends. The
  library now contains **no raw bare-pointer index at all**. The slice is over
  `cap` in the three APPENDING sites and that is part of the rule, not an
  exception to it (S-17c, amended at 0.0.6). **Since 0.1.0c it is the
  language's rule for `Vec`, and since 0.1.3c for `Bytes` too:** a consumer's
  `v.items[i]` and `b.body.ptr[i] = x` are both `NITPICK-TYPE-080` — the
  second compiled through the seal (D-313) until `body` was hidden (question 9).
- **A `bytes_view` view is invalidated by GROWTH** (TM-139, S-18e). It is valid
  until the next call that can grow the sink and no longer; reading it after
  one returns **170**, the allocator's poison. `bytes_view`'s header claimed
  the opposite from 0.0.4 to 0.0.6 and both it and `bytes_push` are public.
  **The structural half is the durable lesson: every gate this repository owns
  is a LEAK gate, and a use-after-free is found by a WRONG ANSWER.** Cycle 0.0
  shipped two of them — this and `vec_pop<T>` — and both were found by reading,
  under a green suite. `tests/unit/bytes_view_lifetime.npk` is the pair.
  **It shipped a third, and no reading found it**: `bytes_take` handed back a
  view of the body as an owned `string` until cycle 0.1.4b, found by the heap
  instrument's COUNT — 25 allocations where the source makes 26 (S-18f). It
  copies now.
  **`len` is `sealed` under `ListLen` since 0.1.0c, and `body` is `hidden`
  since 0.1.3c** (TM-156, TM-195): a consumer reads `b.len` and
  `bytes_capacity(@b)`, and writes neither.

**What 0.0.3 added, and the first item is the one that matters.**
`harness/selfcheck.py` runs **first** in every full invocation (`TESTING.md`
V-15) and plants **twelve** of V-14's thirteen faults (eight of nine from cycle
0.1.4b's case 9, TM-187, until cycle 0.2.0a's four, TM-209 and TM-210; seven
of eight before it) — case 6 is `PEND` until 0.5
and prints as pending — plus at least one violation per tree check, four
arm-bill specimens (three until cycle 0.2.0), and (since 0.0.6) the verdict mechanisms of TM-137 and
TM-141 and the whole-tree walk's nested-repository pruning (TM-146). Each
requires a red run that names it and a green control beside it, and the run
prints both counts. *(The counts are derived from the code rather than typed
here; "eight faults" was printed on every run for three cycles and only the
cycle Gate had it right — C3.)*
Before it, three of the harness's checks had been commissioned by hand and that
was three checks, not a runner. Then: the `parse`, `check`, `golden` and `sweep`
stages; `--quick`; and nine live tree checks — **nineteen today**
<!-- [[sweep: family_live=19]] -->: plus
`check_exemptions_live` (0.0.5, TM-137), `check_denominators` and
`run_defect_corpus` (0.0.6, TM-141/TM-142), `check_expect_headers`, which
existed all along and **was never in the count** — the row `TESTING.md` V-14c's
"every check is commissioned" was false about, found by V-1a's own arithmetic
not closing — `check_literal_divisors` (0.1.1, TM-163), and
`check_check_registry`, `check_no_view_returns` and `check_int128_sites` (0.2.3a,
TM-227, TM-228, TM-230), and `check_call_edges` and `check_wide_types`, which
read the library's emission (0.3.1, TM-250, TM-251). *(It was FOURTEEN
from cycle 0.1.0 to 0.1.0b — `check_civil_literal` joined — while this sentence
said thirteen; it was thirteen again after 0.1.0c retired that check (TM-158);
and it was fourteen from 0.1.1 to 0.2.3a, and seventeen from 0.2.3a to 0.3.1.
Re-derived from the run rather than carried: the `[5/9]` line reads `14 live`
— `checks.LIVE`'s thirteen and `check_failsafe_arms` — and `run.py` drives
the other five outside step 5, two of them over the library's emission at
step 7.)*

## Before starting a session here

Check **[`../BOARD.md`](../BOARD.md)** — it says whether this repository
is claimed by a stream, and by which. **One writer per repository, always.**
[`../WORKSTREAMS.md`](../WORKSTREAMS.md) is the dependency graph and the
stream partition: what gates this repository, what this repository gates, and
what to do when a cross-stream gate is not ready yet.

## Read these first, in this order

0. **`../PLAYBOOK.md`**, if you have the sibling checkouts — the shared house
   rules for every Nitpick library: the language constraints that bite, the
   error-budget rule, the repository and roadmap conventions, and the state of
   the tooling. It is a workbench document and lives beside the checkouts
   rather than inside one, because it belongs to none of them.
1. **`meta/specs/SAFETY.md`** — the constraints and where they come from.
2. **`meta/specs/TIME_MODEL.md`** — **the core.** Almost every bad idea in a
   date library is a type distinction it declined to make; this document is the
   set of distinctions and why each exists.
3. **`meta/specs/README.md`** — the index and the reading order for the rest.
4. **`meta/DECISIONS.md`** — every settled design decision with its reasoning.
   **Read this before proposing a change**, because it is recorded why.
5. **`meta/roadmap/ROADMAP.md`** — the cycle map; then the current cycle's
   `README.md`.
6. **`meta/OPEN_QUESTIONS.md`** — what is not settled, each with a
   recommendation.

## The rules that are not negotiable

- **The specifications are the authority** (TM-002). Code that disagrees with
  `meta/specs/` is a defect in the code. A specification that turns out to be
  wrong is amended by a decision recorded in `meta/DECISIONS.md`, in the same
  commit — never by editing the text and moving on, and never by a comment.
- **A settled decision's text is never rewritten.** Supersede it with a new
  numbered decision that says why (the compiler's D-085/D-202 pattern).
- **Three public error identities, and three is a ceiling** (TM-017). REACH-002
  makes every one an arm every consuming program's `failsafe` must name —
  and, sharper since cycle 0.2.0a (the ecosystem audit's EC3, TM-213), every
  identity a reachable `fail` site raises, a PRIVATE one too, so
  `check_error_budget` refuses any `error:` in `src/` it does not budget. A
  fourth needs a decision saying why a shutdown handler would treat it
  differently from all three — and it is a **major** version (TM-013).
- **Only `src/host/` is impure** (TM-018). No syscall, no clock, no environment
  read, no file read anywhere else. `check_purity` enforces it, and it is the
  single most important check in the suite — with `check_call_edges` beside it
  since cycle 0.3.1, reading the calls in the library's emission (TM-250).
- **`ntime` declares no `Duration`** (TM-004). The prelude's is the ecosystem's
  one span type. A second would immediately become the type everybody converts
  to and from.
- **There is no format string** (TM-009, TM-023). No `strftime`, no
  `layout_from_pattern`. A layout is a typed value, and
  `check_no_format_string` makes adding one a red run **from cycle 0.4, when it
  goes live** — until then it is a `PENDING` name, and a format-string function
  added today would leave the run green (`TESTING.md` V-1a; the cycle audit's
  C8, at 0.1.5's second half).
- **No dependencies** (TM-027). Not the compiler's `src/`, not its `lib/`, not
  `nitpick-parse`, not `/usr/share/zoneinfo`.
- **Never work around a compiler defect.** Record the reproduction, stop, and
  raise it. This is the compiler's own R6: a workaround buried in library code
  outlives the bug and is indefensible at verification time.

## The compiler constraints that shape everything

Full statement in `meta/specs/SAFETY.md` §1. The ones that bite hardest here:

- Plain integer overflow **traps**; division by zero traps; indexing traps.
  Every range is checked **before** the trap so the caller gets an answer —
  every range but `SAFETY.md` S-12's named exceptions, `never fails` by
  decision: the four `Duration` constructors and `instant_add`, whose trap is
  their range check *(cycle 0.2.4b, TM-242)*.
- `Ord` derives in **declaration order**, so a struct's field order is
  semantic (`Timestamp` is seconds-then-nanos for exactly this reason).
- **A `cstring` owns what `to_cstring` makes, and is move-only** — since
  compiler `5fbaf4a` (its D-328): a copy of one is `NITPICK-TYPE-046`. Read an
  `environ()` element in place, `env[k].ptr`, and move `to_cstring`'s answer
  out of its `Result`, `move(c.value)` (TM-208).
- Owning values are **move-only**, and a `fixed` table holds no owning value:
  the language allows one and refuses the copy that reads a row out — and,
  since compiler `c970483`, the move out of `fixed` storage too,
  `NITPICK-TYPE-084` (`SAFETY.md` S-19b; through `c3bdae2` the move compiled
  and faulted — a compiler defect raised at cycle 0.1.3b, O-N20, the
  compiler's DEF-99).
- There are **no closures** and **no format-specifier language** (D-018,
  D-053).
- `defer` does **not** run on a trap; `failsafe` is the only code guaranteed to
  run.
- An `async` function can never be `never fails`, so `raw await …` is
  unspellable — but `ntime` has no `async` function at all, and should not
  grow one.

**And the four that cycle 0.0.0 MEASURED rather than read**, each of which
changed a document:

- **There is no checked narrowing** (TM-105). `=>!` truncates in silence, and
  the checked `=>` at the same narrowing is refused at compile time
  (`NITPICK-TYPE-009`). Every narrowing therefore carries its own range check —
  written by you, in code.
- **`exit 0` says nothing about managed memory** (TM-106). D-151 watches `wild`
  allocations only. A `Vec<string>` whose block is freed and whose elements are
  not retained 125 MiB over two million elements **and exited 0**. What says
  something, since cycle 0.1.4b, is the runtime's own `NPK_HEAP_STATS` line,
  held to a `heap:` marker's bounds — and only for a file that carries one.
- **An import's arm bill is its `fail` SITES plus its ARITHMETIC**, charged per
  module, not per call (TM-107). Importing a module that declares no error at
  all still cost four arms. Avoiding a failing *function* buys nothing; module
  boundaries are the only granularity there is.
- **`Vec<T>` and `Bytes` are NOT bounds-checked** (TM-108). The check attaches
  to the *type*: slices, arrays and simd lanes trap, **a bare pointer does
  not**, and both of those are reached as one. The accessor pair is the only
  bound there is, and it checks `0 <= i` as well as `i < count`.

**And one about the compiler itself: `npkc` exit 0 is not well-formedness**
(TM-112). It accepted a root with `main` and no `failsafe` until DEF-5 landed.
Pair every exit code with the artefact it should have produced; a status that
disagrees with an artefact is the tell.

## Reserved words that read like ordinary names

`meta/specs/BUILD.md` §7 has the table. The ones this domain wants most:
`unit` (a rounding granularity), `end` (a range's upper bound), `limit` (a
bound), `in`, `on`, `mod` (a modulus), `fixed` (as in "fixed offset"), `range`,
`error`, `buffer`, `raw`, `move`, `any`, `is`, `never`, `fails`.

The substitutes this library uses, so the tree stays consistent: **`gran`** for
a rounding granularity, **`hi`**/**`lo`** for range bounds, **`rem`** for a
modulus result, **`zone_off`** for a fixed offset in seconds, **`bound`** for a
limit, **`src`** for an input byte slice, **`sink`** for an output `Bytes`.

**And the ten VERIFICATION keywords, none of which was in any table here until
cycle 0.0.4** (TM-130, `BUILD.md` B-18): `prove`, `assert_static`, `requires`,
`ensures`, `acquires`, `gives`, `invariant`, **`old`**, **`result`**, `pure`.
All ten measured refused as local names at pin `0dfddac`. The last three are
the compiler's D-221, and `old` and `result` are the dangerous pair, because
this library's own contract syntax uses them — `ensures v.count == old(v.count)`
— so you meet them as things to write. Use **`outgoing`** and **`answer`** as
locals; in a contract comment write `old` and `result`, as the live clause
takes them (TM-244).
**At compiler `c3bdae2` there are twelve**: D-304 added **`decreases`** and
**`unbounded`**, and the new field qualifiers **`sealed`** and **`hidden`** are
refused as local names the same way (cycle 0.1.0b; `BUILD.md` B-18).

And **`stack`**, which is not in this library's own list and is the one that
costs an hour: it is a memory qualifier beside `wild`, and using it as a local
name gives `PARSE-002` at the declaration followed by *"this `{` is never
closed"* pointing at `main`'s closing brace — so it reads as a brace imbalance
dozens of lines away and gets bisected as one. A sibling library lost about an
hour to it. **If a parse error claims an unclosed brace and the braces are
balanced, check whether a local is named after a qualifier before you touch the
braces.**

Three shapes that surprise a C or Rust habit: adjacent string literals do not
concatenate; `discard(x);` takes parentheses and `defer { … }` takes no
trailing semicolon; declarations end `};` and control-flow blocks do not.

**And a file's `mod:` name must equal its basename** — the loader reports
`NITPICK-RESOLVE-005` at line 1 and says nothing about the name. Since D-248 a
module name is an **identifier**, so a file named after a reserved word, or
beginning with a digit, is refused: hence `probeNN_topic.npk` and never
`NN_topic.npk`.

## Building and testing

**`npkg` cannot build this yet** (`meta/specs/BUILD.md` §1): it is the
compiler's own bootstrap ladder, and `[dependencies]` resolves to nothing.
`harness/run.py` is the runner until that changes (TM-003).

**What the harness is after 0.0.3.**

```
$ NPKC=… NPKRT=… python3 harness/run.py [--only SUBSTRING] [--quick]
                                        [--verdicts PATH] [--root DIR]
```

Eleven modules under `harness/` — `manifest`, `toolchain`, `elf`, `lexical`,
`build`, `stages`, `checks`, `arms`, `repro`, `selfcheck` — driven by `run.py`
in nine stages. **Every `.npk` it reads, it reads as the compiler does** —
through `lexical.py`, as bytes, with comments and literals by the lexer's rules
and import paths decoded — and **every check matches tokens, never lines**
(cycle 0.1.5; `TESTING.md` V-1k, V-1l). It proves it can fail; reads
`nitpick.toml` and hardcodes nothing;
holds `llc`, `opt` and `ld.lld` to the pinned patch release; sweeps every
`.npk` in the tree and prints the denominator; diffs the tree against the
documents describing it; roots every `.npk` at the real parser; builds the
library; proves the IR identical from two working directories; and runs each
test file at -O0 and again under `opt -O2`. `harness/README.md` is the guide
and carries the cost table.

**Four things it is easy to over-read, so they are written down.**

- **The library object is linked into nothing** (TM-117). There is no separate
  compilation: `npkc` emits the whole module graph a root reaches, so every
  program carries the prelude and `ld.lld p.o ntime.o npkrt.o` is a
  duplicate-symbol error. The library is built because *building it is a check*.
- **The undefined-symbol scan cannot FLAG a syscall** (TM-118, TM-153). `npk_sys6` is the
  runtime's own and is in the allowlist by construction. The scan supports
  B-2's "no C, ever" and nothing wider. **`check_purity` is SOURCE-level and is
  the only thing here that answers "did this module touch the kernel"** — never
  cite a green symbol scan for it (B-2c, S-10b, RX-120). *(One of two since
  cycle 0.3.1: `check_call_edges` reads the calls in the library's emission,
  TM-250 — every call a function outside `src/host/` makes, through the
  prelude, against a reviewed allowlist. Neither is the symbol scan.)*
- **The `parse` stage asks `npkc`, not the compiler's `tools/parse_check`**
  (TM-123): those are `.npk` source files, and building one is building the
  compiler from a tree ahead of our pin. It reads the diagnostic's code
  *family* instead — `LEX` and `PARSE` are the parse phase and everything else
  is later.
- **A `--only` or `--quick` run concludes nothing**, says so twice, and will
  not print the unqualified word `GREEN`. CI passes no flags and that is a rule
  (TM-125, B-9b), asserted by the workflow rather than left to review.

**Two probes need `TZ=Europe/Kyiv`** (09 and 09b). They now say so in their own
headers — `// env: TZ=Europe/Kyiv`, TM-120 — and the harness **constructs** each
program's environment rather than inheriting yours, so a `TZ` in your shell
cannot change a verdict. Run by hand without it they exit **30**; with the wrong
value, **39**. Neither number is a verdict about the language — that is the
point of them (TM-116).

The compiler binary is the **pinned toolchain** the board names
(`../BOARD.md`, W-18): `$NPKC` and `$NPKRT` are supplied to every session by the
orchestrator, or set by hand from `../.internal/toolchain/<commit>/`. Never build the
compiler from here and never read its `build/` directly — the guard refuses
the first, and the second is rebuilt under you. LLVM 20.1.2 exactly, pinned —
and the harness asks `llc`, `opt` and `ld.lld` rather than `llvm-config`, which
ships in a `-dev` package the build never invokes and which can report a
different installation from the one on `PATH`.

## Where things go

```
src/       the library, Nitpick only, layered per meta/specs/BUILD.md §6
  core/      Vec, Bytes, the named limits
  cal/       the civil calendar and its algorithms
  span/      Duration interop and Period
  zone/      the GENERATED tz tables and the offset lookup
  fmt/       formatting and parsing, and the typed layout
  host/      THE ONLY IMPURE MODULE — five functions, nothing else
tests/     probe, conformance, unit, golden, rejection, fixtures
harness/   the Python build and test runner, until npkg can
tools/     generators — the civil cross-oracle's corpus since cycle 0.1.4, the
           tzdb tables at 0.5; everything they emit is committed
examples/  runnable demonstrations, built and run by the harness
docs/      user-facing documentation, written at cycle 1.0
meta/      specs, decisions, open questions, the roadmap, research
.internal/ gitignored scratch — never commit anything from here
```

## When you find something

- A **compiler defect**: record the reproduction, stop, raise it. Do not work
  around it.
- A **specification error**: fix the specification and record the decision, in
  the same commit as the code that revealed it.
- A **finding that is neither**: write it into the current subcycle's execution
  record. This project's execution records are load-bearing; the compiler's
  cross-cycle patterns exist only because one writer kept them.
