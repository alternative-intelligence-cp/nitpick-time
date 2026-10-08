# Safety, errors, and purity

The constraints. Read this first: a date library looks like pure arithmetic
until it meets a machine, and the two rules that shape `ntime` most — the error
budget and the purity boundary — have no analogue in any other language's date
library, so there is nothing to copy.

---

## 1. What the language imposes

Each row is a language decision, not ours. The consequence column is what it
costs a library that does calendar arithmetic.

| Language rule | Where | Consequence for `ntime` |
|---|---|---|
| `failsafe`'s `pick` must **name** every error that can reach it | REACH-002 | ~~Every public `error:` we declare is an arm every consuming program owes.~~ **Every identity a REACHABLE `fail` site raises — public OR PRIVATE, qualified by the module that declares it — is an arm every consuming program owes; a declaration never raised costs nothing.** *(Corrected 2026-09-27, cycle 0.2.0a — the ecosystem audit's EC3, TM-213, re-measured at `5fbaf4a`: the arm is owed for every identity a REACHABLE `fail` site raises, PUBLIC OR PRIVATE, named by the module that declares it (`m.E`), and for no declaration nothing raises.)* §2. |
| Reachability is **import-scoped** | 1.4.8's `nsys` note | Module decomposition decides what a consumer's `failsafe` owes. §2. |
| Plain integer `+ - *` **traps** on overflow | D-210 | Every arithmetic path states its range and checks it **before** the trap fires. §4. *(Cycle 0.2.4b, TM-242: every path but S-12's named exceptions — `never fails` by decision, the four `Duration` constructors and `instant_add`, whose trap is their range check.)* |
| `/` and `%` by zero trap; signed `MIN / -1` traps | D-007, D-142 | The calendar algorithms divide constantly; every divisor is a nonzero literal or a proven value. §4. |
| Indexing **a type that carries a length** is bounds-checked and traps | D-070 | a slice `T[]`, a fixed array `T[N]` and a `simd<T, N>` lane trap; **a bare pointer does not** — and `Vec<T>.items` and `Bytes`' `buffer` body are both reached as one. §4, S-17b. |
| Owning values are **move-only** | TYPE-046 | No binding-to-binding copies of a `string` — nor, since cycle 0.1.3c, of a `Vec` or of anything holding one (S-18g), nor, since cycle 0.2.0a at compiler `5fbaf4a`, of a `cstring`, which owns what `to_cstring` makes (the compiler's D-328): an `environ()` element is read in place and `to_cstring`'s answer moved out of its `Result` (TM-208). **No `fixed` table holds an owning value** — the language lets one, then refuses the copy that reads a row out and, since compiler `c970483`, the move too (S-19b; through `c3bdae2` the move compiled and faulted, O-N20). §5. |
| Borrows are second class | D-004 | A view of the zone table cannot be returned or stored. §5. |
| A successful `exit 0` with live `wild` allocations **traps** | D-151 | Every `wild` byte is paired on every path. §5. |
| There are **no closures** | D-018 | A layout is data the formatter interprets, not a callback. FORMAT_MODEL.md. |
| There is **no format-specifier language** | D-053 | `strftime` is not merely absent, it is against the grain. FORMAT_MODEL.md §1. |
| `Ord` derives in **declaration order** | TRAITS_REFERENCE §2.5 | A struct's field order is semantic. §4. |
| `Hash` is not derivable where a field is a `string` | D-133 | The zone name is not a hashable field; the zone **id** is. |
| `Default` is not derivable | D-123 | There is no default date, and there was never going to be a good one. |
| Every blocking operation carries a **mandatory deadline** | D-056, D-176 | `ntime` blocks on nothing. §3. |
| The deadline substrate uses `CLOCK_MONOTONIC` and refuses a wall clock | D-176 | The reason `Instant` and `Timestamp` are different types. TIME_MODEL.md §2. |

---

## 2. The error budget

**Rule S-1 (TM-017).** REACH-002 makes every `error:` that can reach `failsafe` a named
arm the consuming program's `failsafe` must carry — and forgetting one is a
compile error. **The number of public error identities `ntime` declares is
therefore a hard budget, and it is three.**

| Error | Raised when |
|---|---|
| `ETimeValue` | a value is not a representable, real time — a year outside the supported range, February 30th, hour 24, an offset beyond ±18:00, or an arithmetic result that would leave the range |
| `ETimeParse` | input text did not match the format asked for |
| `ETimeZone` | a zone name is not in the compiled table, or a local time is ambiguous or nonexistent and the caller asked for the strict resolution |

**Rule S-2 — three is a ceiling, and it is deliberately tight.** A fourth is
added only by a recorded decision saying why a *shutdown handler* would treat
it differently from all three. It is also a **MAJOR** version change (TM-013):
a new identity is a new mandatory arm in every consumer, which the compiler
enforces.

**Rule S-3 — the caller's distinctions ride as detail fields, not as errors.**
"Out of range" and "not a real date" are one error to a `failsafe` and two
different things to a caller, so the caller's distinction is a field:

```nitpick
pub enum:ValueFault = {
    YearRange; MonthRange; DayRange; HourRange; MinuteRange;
    SecondRange; NanoRange; OffsetRange; DayOfMonth; Overflow;
    DayOfYear; WeekRange; WeekOfYear; WeekdayRange;
    ClockMismatch;
};
```

The same pattern carries `ParseError` (the byte offset, and what was expected)
and `ZoneFault` (`Unknown`, `Ambiguous`, `Nonexistent`). This is the playbook's
rule and it is what keeps the budget at three without losing information.

*(Amended at cycle 0.1.3, TM-173: the last four variants are new, appended so
every earlier one keeps its tag. They are the refusal rows of the two
constructors cycle 0.1.3 adds — `DayOfYear`, a day past the year's last, beside
`DayOfMonth`; `WeekRange`, a week below 1; `WeekOfYear`, a week past the
week-year's last; `WeekdayRange`, an ISO weekday outside 1 … 7 — and they
follow `DayRange` and `DayOfMonth`'s split: a fixed bound and a bound the year
decides are two variants. How a refusal hands its variant back is still
`../OPEN_QUESTIONS.md` O-X8.)* *(And at cycle 0.2.0, TM-216: `ClockMismatch`,
appended — `span`'s `instant_since` and `instant_cmp` refuse two readings of
two clocks. `span` raises `cal`'s identity, so `cal`'s enum carries its variant.)*

**Rule S-4 — module decomposition is part of the budget**, because REACH is
import-scoped:

| Module | Declares | Identity arms a consumer importing only this owes | TOTAL arms, MEASURED at the pin each run uses (at `aaffb87`) |
|---|---|---|---|
| `ntime/lib.npk` — **the umbrella**, the import a consumer writes | — (re-exports) | one arm today (`cal`'s) | **13** <!-- [[sweep: arms_lib=13]] --> (—) — generated since cycle 0.1.0b (TM-155): the floor of six, `cal.ETimeValue`, the four arithmetic arms, `DecreasesViolated` from `src/core/bytes.npk`'s measured loops, and — since cycle 0.1.0c (TM-156, TM-159) — `LimitViolated` from the `ListLen` on `src/core/`'s sealed lengths. It was **12** until then |
| `ntime/core.npk` | — | nothing | **6** <!-- [[sweep: arms_core=6]] --> (4) — the floor; `core` is not yet reachable as its own public module, and its code is billed through the umbrella's row |
| `ntime/cal.npk` | `ETimeValue` | one arm | **11** <!-- [[sweep: arms_cal=11]] --> (9) — measured 2026-09-06 and 2026-09-25 |
| `ntime/span.npk` | — (raises `cal`'s) | one arm | **11** <!-- [[sweep: arms_span=11]] --> (—) — since cycle 0.2.0, measured: `cal.ETimeValue`, which `span` raises for two clocks' readings (TM-216), since cycle 0.2.1 for a `secs` outside the range or a `nanos` outside one second handed to `timestamp_of` (TM-220), since cycle 0.2.2 for a civil reading `civil_to_utc` cannot convert, `timestamp_of`'s refusal relayed (TM-222), and since cycle 0.2.3 for a sum `timestamp_add` cannot keep in the range, relayed the same way (TM-234), and a difference `timestamp_since` cannot hold in a `Duration` (TM-236), and since cycle 0.2.4b for a `secs` handed to `timestamp_add` outside the range (TM-241) and a difference `instant_since` cannot hold (TM-242); the floor of six; and `cal`'s four arithmetic arms, which reach every importer of `span` because `span` imports `cal`. **No new identity**: the umbrella's row stays 13. *(A placeholder until cycle 0.2.0, the row read **6** (4), the floor, "meaningless until cycle 0.2 gives the module a body".)* |
| `ntime/zone.npk` | `ETimeZone` | two arms | placeholder; **6** <!-- [[sweep: arms_zone=6]] --> (4) today (cycle 0.3) |
| `ntime/fmt.npk` | `ETimeParse` | three arms | placeholder; **6** <!-- [[sweep: arms_fmt=6]] --> (4) today (cycle 0.4) |
| `ntime/host.npk` | — (forwards errnos) | one arm | **11** <!-- [[sweep: arms_host=11]] --> (—) — since cycle 0.3.0, measured (TM-248): `cal.ETimeValue`, which `host` relays from `timestamp_of` (H-8) and raises in `timespec_ns`; the floor of six; and `cal`'s four arithmetic arms, which reach `host` through `span`. A forwarded errno is a dynamic operand and arms nothing (S-5). **No new identity**: the umbrella's row stays 13. *(A placeholder until cycle 0.3.0, the row read "placeholder; **6** (4) today" — the floor.)* |

*(Amended at cycle 0.1.0b: the column read "MEASURED at pin `aaffb87`" with the
bracketed numbers, and had no umbrella row. At compiler `c3bdae2` every row
gained `StackExhausted` and `MachineFault`, the new floor (TM-155), and the
umbrella became a generated row because it is the import a consumer actually
writes.)* *(Re-measured at compiler `c970483` by cycles 0.1.4c and 0.1.5:
every row is unchanged.)* *(Since cycle 0.1.5's second half every total in
this column is TAGGED, and `check_denominators` holds each to the bill
`check_failsafe_arms` generates from source and diffs against
`NITPICK-REACH-003` on every run (TM-205) — so a bill that moves turns this
column red rather than stale. Until then nothing read the WRITTEN column: the
cycle audit's C6.)* *(And the "Declares" column is what `check_error_budget`
holds each identity to since the same half (TM-203): the compiler names an
identity by its declaring module — `cal.ETimeValue` — so a budgeted name
declared in a second module, or outside the module this column names, is a
second arm in every consumer, measured at `c970483` as `moda.ETimeValue` and
`modb.ETimeValue` for one name in two modules, and the check fails on either.)*
*(Cycle 0.2.4b — the cycle audit's K7: the totals column's header read
"MEASURED at pin `c3bdae2`" through the adoptions of `c970483` and `5fbaf4a`.
Every total is tagged and held to the bill generated at whichever pin a run
uses, so the header says that, and no pin.)*

**A program that only wants calendar arithmetic owes one IDENTITY arm.** That is
the decomposition working, and it is why `cal` does not import `zone`.

**AND IT OWES NINE ARMS ALTOGETHER — the totals column is now real for the one
module that has a body, and it is MEASURED rather than predicted**, which is
what S-4b promised cycle 0.1 would deliver. *(**Eleven** at compiler `c3bdae2`,
cycle 0.1.0b: the two new floor identities, `StackExhausted` and
`MachineFault`, and nothing else. The nine below is kept as the record at
`aaffb87`.)* Read out of `NITPICK-REACH-003`'s
own list by compiling a consumer that imports only `src/cal/cal.npk` and
declares no handler:

```
$NPKC arm_cal.npk -o arm_cal.ll     →  exit 1, no .ll written
NITPICK-REACH-003 … 9 identities: cal.ETimeValue, Unreachable, HeapOom,
  HeapBadRequest, WildLeak, DivByZero, DivOverflow, IntOverflow, OutOfBounds
```

`check_failsafe_arms` runs that generation on every full invocation and diffs
the list against the set computed from source **in both directions**, so this
row cannot go stale in silence. *(Cycle 0.1.5's second half, the cycle audit's
C6: that held of the GENERATED bill, and nothing compared it with the numbers
WRITTEN here and on the summary pages, none of which was tagged — a moved bill
would have left them stale under a green run. Each written total is tagged
now, and `check_denominators` holds it to the generated bill (TM-205).)*

**9 = 4 + 1 + 4**: the floor, plus `cal.ETimeValue`, plus the four system arms
`cal`'s own `%`, `+` and `MONTH_LENGTH[m - 1]` arm in the CONSUMER however pure
the consumer's code is (S-4b). **The cycle README's checklist predicted "exactly
one arm" and that prediction was wrong by eight** — recorded rather than
quietly corrected, because it is TM-107's lesson arriving in a checklist a
session would otherwise have ticked.

**AND THE ARM SET IS A SET, which this is the first measurement here to show.**
`tests/conformance/import.npk` — the consumer of the whole umbrella — went from
**8** to **9** when `cal` landed, not from 8 to 12: `src/core/` had already
armed `DivByZero`, `DivOverflow`, `IntOverflow` and `OutOfBounds`, and a second
module doing the same kind of arithmetic adds nothing. So S-4b's system-arm
half is **front-loaded** — it arrives with the first module that computes
anything and never grows again — while the identity half grows one per module
that declares *and raises*. `ETimeParse` (0.4) and `ETimeZone` (0.3) are the two
still to come, and `import.npk` is where each will first show.

*(Cycle 0.1.5's second half, the cycle audit's C7: "never grows again" is true
of the four ARITHMETIC arms and of nothing else. The machinery half grew twice
after this was written — `DecreasesViolated` with the first measured loop, at
cycle 0.1.0b (TM-155), and `LimitViolated` with the first limited field, at
0.1.0c (TM-159), two of the umbrella's four arms from 9 to 13, the floor's
two new identities the other two — and a `till` or `loop` with a COMPUTED step
arms `BadStep` (with a literal step too, through compiler `c3bdae2`: measured
at 0.1.2's planning, and the compiler's DEF-95, fixed at `c970483`). What is
front-loaded is the arithmetic; each new kind of machinery arrives with the
first module that writes it, as the table below says.)*

**Rule S-4b (TM-107) — the identity column is not the whole bill, and this table
is not yet the bill.** Measured at cycle 0.0.0 by
`tests/probe/probe11c_import_arm_cost.npk`: the reachable set is computed over
**every module in the program graph but the prelude**, and the *system* arms are
armed by the machinery any module's text contains — `DivByZero` and
`DivOverflow` by `/` or `%`, `IntOverflow` by plain-integer `+ - *`,
`OutOfBounds` by an index — on top of an unconditional floor of `Unreachable`,
`HeapOom`, `HeapBadRequest`, `WildLeak`, **`StackExhausted` and `MachineFault`**.
*(The floor was those first four until compiler `c3bdae2`; its cycle 1.5 made
the last two universal — D-305 checks every emitted function's stack, D-307
routes a hardware fault to `failsafe` — and cycle 0.1.0b read both out of the
`NITPICK-REACH-002` lines of every root in this tree that reaches the
reachability analysis, 61 of them, before writing them here. TM-155.)*

**And one more piece of machinery arms an arm since `c3bdae2`:**

| Machinery in a module's text | Arms | Measured |
|---|---|---|
| `/` or `%` | `DivByZero`, `DivOverflow` | cycle 0.0.0 |
| plain-integer `+ - *` | `IntOverflow` | cycle 0.0.0 |
| an index | `OutOfBounds` | cycle 0.0.0 |
| **a loop's `decreases` clause** | **`DecreasesViolated`** | cycle 0.1.0b, at `c3bdae2`: 20 of this tree's 61 roots, every one through this tree's own loops (the compiler's D-304) |
| **a `limit<R>` on a field** (or on a parameter or a local) — armed at its WRITES | **`LimitViolated`** | cycle 0.1.0c, at `c3bdae2`: the nine roots that consume `src/core/vec.npk` or `bytes.npk`, whose lengths carry the prelude's `ListLen` since that cycle (the compiler's D-308; TM-156, TM-159) |

`unbounded`, the other clause D-304 admits, checks nothing and arms nothing.
The generator's `limit` rule over-approximates in one direction: a `limit<`
on a field its module never writes would be billed and not demanded, and
`check_failsafe_arms` reports that in both directions (TM-159).

A miniature of `cal` that declares **no error at all** cost an importing program
whose own text contains no arithmetic **four extra arms**, and the twin that
imports nothing compiles with the floor arms alone — four at cycle 0.0.0, six at
`c3bdae2` (`tests/probe/probe11d_floor_only.npk`). `cal` divides by literals
only (S-16, C-11), indexes its month table (S-17), and adds,
so **a consumer that imports `ntime/cal.npk` owes `DivByZero`, `DivOverflow`,
`IntOverflow` and `OutOfBounds` however pure its own code is** — arms a correct
`ntime` can never enter, since every divisor is a nonzero literal and every index
is checked, and arms it must write anyway. *(Amended at cycle 0.1.1, TM-163: the
sentence read "`cal` divides by 4, 100, 400, 146097, 86400 and 1000000000
(S-16), indexes the month and zone tables" — a prediction written at cycle
0.0.0. At cycle 0.1.1 `cal` divides by eleven distinct literals — 4, 5, 7,
100, 153, 365, 400, 1 460, 36 524, 146 096 and 146 097, a list that is
`check_literal_divisors`' to keep and this note's only as a date-stamped
reading — by neither 86400 nor 1000000000, and indexes no zone table; the four
arms it predicted are the four it arms.)*

That is the compiler's deliberate direction rather than a defect
(`reach.npk`: *"Over-approximation is the safe direction"*), so what changes is
this document, not the library. **The totals column is generated at cycle 0.1**,
when `src/cal/` exists and the numbers can be measured instead of predicted;
nothing is guessed into it here. *(It was: measured at cycle 0.1.0 and a
generated row since 0.1.0b, TM-155, checked against the compiler on every run
by `check_failsafe_arms`.)*

**Rule S-4c (TM-107) — the arm is owed by the IMPORT, not by the call.**
`tests/probe/probe11e_unused_import_refused.npk` imports the module that raises
the identity, calls only its infallible half, and is still refused. And
`tests/probe/probe11f_declared_unraised.npk` shows the other end: a `pub error:`
**declared and never raised** arms nothing, because the set is computed from
`fail`, `?!` and `!!!` *sites*. So the decomposition in S-4 is doing more work
than its table suggests — splitting `zone` from `cal` saves arms even for a
consumer that touches only `zone`'s infallible half — and module boundaries are
the only granularity that exists. Avoiding a failing *function* buys nothing.

**Rule S-5.** Kernel errnos are **forwarded verbatim** (`fail r.err`), exactly
as `lib/nsys.npk` does. A forwarded errno is a dynamic operand and does not
enlarge the reachable set, so `host`'s `clock_gettime` failures cost no arm.

**Rule S-6.** The exact arm set a consuming program owes, per import, is
generated into the documentation and checked by a conformance test that builds
a program importing each public module and asserts its `failsafe` compiles with
exactly the documented arms and no more. An out-of-date arm list is the kind of
document that goes stale silently, so it is derived, not written.

**Rule S-6b (cycle 0.0.3) — the ORACLE is the compiler's own diagnostic, and the
generator is the thing under test.** `NITPICK-REACH-003` does not merely refuse a
program with `main` and no `failsafe`: it **lists the identities owed**. That
list is the truth, because it is what the consuming program will actually have
to write. So `check_failsafe_arms` generates, per public module, a program that
imports it and declares no handler, reads the identity list out of the refusal,
and requires it to **equal** the set computed from source — in both directions.

*The source computation is what S-6 publishes*, because a table a reader can be
shown the reason for (*"you owe `DivByZero` because `cal` divides"*) is worth
more than a number scraped out of a diagnostic; the compiler is what says
whether the reasoning is right. A disagreement is a defect in the generator,
never in the compiler, and it is a red run rather than a quiet drift.

**And this is what makes constraint 3 above mechanical rather than aspirational.**
"And no more" cannot be caught by any build — a superset of the required arms
compiles — so it is caught by a set equality asserted here. Measured at pin
`0dfddac` on the three specimens cycle 0.0.0 left behind, **re-measured at
compiler `c3bdae2` at cycle 0.1.0b** (the bracketed numbers are `0dfddac`'s),
and the arithmetic is written out because a number embedded in prose travels
with the prose:

| Module | Owes | = floor + | Which constraint it pins |
|---|---|---|---|
| *(nothing imported)* | **6** (4) | — | the floor: `Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak`, and since `c3bdae2` `StackExhausted` and `MachineFault` |
| `probe11_silent_lib` | **6** (4) | + 0 | **1** — it declares `pub error:EProbeSilent` and never raises it, and the identity is **absent** from the list |
| `probe11_arms_lib` | **7** (5) | + 1 | a `fail` SITE puts it in, module-qualified: `probe11_arms_lib.EProbeZone` |
| `probe11_calc_lib` | **10** (8) | + 4 | **2** — it declares no error at all; `DivByZero`, `DivOverflow` from its `/` and `%`, `IntOverflow` from its `+`, `OutOfBounds` from its one index |
| `probe11_relay_lib` *(since cycle 0.2.0)* | **7** (—) | + 1 | **4** — it RAISES `probe11_arms_lib`'s `EProbeZone`, which it imports, and the arm is `probe11_arms_lib.EProbeZone`: named by the module that declares it, not the one that raises it |

10 − 6 = 4 (and 8 − 4 = 4 at `0dfddac`) is S-4b's measured *"four extra
arms"*: the floor moved and the difference did not. None of the four
functions (three until cycle 0.2.0) is ever called by the generated program —
S-4c, the arm is owed by the **import**.

**Three constraints on that generator, all measured at cycle 0.0.0 (TM-107) and
each of which the obvious implementation gets wrong** — *and a fourth since
cycle 0.2.0, found at its planning:*

1. **It counts `fail`, `?!` and `!!!` sites, never `error:` declarations.** A
   declared, unraised identity costs a consumer nothing, so counting
   declarations overstates the bill for any module that declares ahead of
   raising.
2. **It includes the system arms the imported subgraph's arithmetic arms**
   (S-4b), or every row that imports `cal` is short by four.
3. **"and no more" is the harness's assertion, not the compiler's.** A superset
   of the required arms compiles: `tests/probe/probe07_negative_div.npk` names
   `(OutOfBounds)`, contains no index expression, and exits 0. So a published
   table that *over*states would never be caught by a build, which is precisely
   why this rule exists.
4. **It names an identity by the module that DECLARES it, not the module whose
   `fail` site raises it** *(cycle 0.2.0, TM-217)*. The two are one
   module while every module raises only its own; `span` raises `cal`'s
   `ETimeValue`, and the compiler lists `cal.ETimeValue` where the generator,
   until then, added a `span.ETimeValue` that does not exist — an
   overstatement, constraint 3's direction. Two modules declaring the name, or
   none, is a problem the generator reports, never a guess.

**And the check must not stop at `npkc`.** A program with `main` and **no**
`failsafe` was accepted by `npkc` at exit 0 and refused only by `llc`
(`../OPEN_QUESTIONS.md` O-N11, accepted as the compiler's DEF-5).

> **Amended at cycle 0.0.3.** This rule said *"— but not in the pinned
> toolchain, so this constraint stands"*. **That parenthetical is now false and
> was measured so**: at pin `0dfddac`,
> `tests/probe/defect/missing_failsafe/case1_no_failsafe.npk` is refused
> `NITPICK-REACH-003` by `npkc` itself, at exit 1 with no `.ll` written.
> **THE CONSTRAINT STANDS ANYWAY, AND FOR A BETTER REASON THAN THE ONE GIVEN:**
> the stage must not depend on which pin it runs against. A rule justified by
> "our compiler does not do this yet" evaporates the day it does, and takes the
> belt with it — which is exactly the moment nobody is watching.

So a conformance test that compiles to `.ll` and reads the exit code would pass
a program with no handler at all. It runs the full four steps, **or** asserts
`grep -c '^define i32 @npk_failsafe'` is 1 — and it does **both**:
`build_program`'s `require_failsafe` is redundant at this pin and is kept, and
cycle 0.0.3's self-check drives it through an `npkc` wrapper that renames the
define after emission (`TESTING.md` V-14 case 8). A belt that has never been
tested is not a belt.

---

## 3. Purity — the rule that makes this library testable

**Rule S-7 (TM-018).** **Every function in `ntime` outside `src/host/` is a
pure function of its arguments.** No syscall, no clock, no environment read, no file
read, no allocation that depends on anything but its inputs. Given the same
arguments it returns the same value, on every machine, forever.

**Rule S-8 — `src/host/` is the only impure module**, and it is small on
purpose. It contains exactly:

- `host_now_utc()` — `clock_gettime(CLOCK_REALTIME)` → `Timestamp`
- `host_now_instant()` — `mono_now()` → `Instant`
- `host_now_boot()` — `clock_gettime(CLOCK_BOOTTIME)` → `Instant`
- `host_clock_res(which)` — `clock_getres`
- `host_system_zone()` — reads `$TZ`, then `/etc/localtime`, and **says which
  it used**

and nothing else. Nothing elsewhere in the library calls any of them.

*(Cycle 0.3.0, TM-248: the fourth read `host_clock_resolution(which)`.
`HOST.md` H-1, the module's specification, and every other site call it
`host_clock_res`, which `src/host/host.npk` declares, over `HostClock`.)*

**Rule S-9 — the clock is a parameter, never an ambient.** A function that
needs "now" takes a `Timestamp` or an `Instant`. `ntime` provides `host_now_*`
so a caller can get one; the library itself never asks. This is the same rule
the sibling TUI library applies to its decoder's clock, and it is what makes
every behaviour in this library reproducible in a test to the nanosecond.

**Rule S-10 — a whole-tree check enforces §7.** `check_purity` greps `src/`
outside `src/host/` for `sys(`, `mono_now`, `environ`, `read_file`, `open` and
`write`, and fails on any hit. The rule is not a convention if nothing checks
it, and this is the check.

*(Cycle 0.3.1, TM-252: the list is the review's — every bare-name builtin
and every synchronous public prelude function at the pin that reaches past
the program's own memory, forty-three names in seven classes, each matched as
a call with no identifier character on its left; `TESTING.md` §2's row lists
them. The six above were cycle 0.0.3's guess, and a function calling
`hardware_concurrency()` or the prelude's `std_out()` passed them. And since
TM-250 a second reading holds the rule from the library's emission,
`check_call_edges`.)* *(Corrected 2026-10-08 by cycle 0.3.1's verification,
where the note said "every bare-name builtin and public prelude function":
the prelude's asynchronous `text_read_line`, `text_write_str` and
`text_write_line` reach the clock and are not on the list, nor are the
methods `ByteReader.seek` and `LineBufWriter.flush`. Each is callable only
from an `async func` — a synchronous call is `NITPICK-TYPE-043` — and a
non-generic `async func` in `src/` is a finding of `check_call_edges`; a
generic one nobody instantiates is in no emission, and passes every check,
measured — dormant, since no function of `src/` is asynchronous. TM-252's
dated note has the rest.)*

**Rule S-10b (TM-126) — it is a SOURCE-LEVEL check, it is LIVE, and it has been
SEEN TO FAIL.** Three separate claims, and each was missing:

- **Source-level, and nothing else can stand in for it.** The build's
  undefined-symbol scan cannot answer this question at all: `npk_sys6` is the
  runtime's own syscall trampoline and is in its allowlist by construction, so a
  module that issues a raw syscall passes the scan exactly as one that does not
  (`BUILD.md` B-2c, TM-118). **A green symbol scan cited as a purity result is
  the failure mode.** *(Amended at cycle 0.1.0b, TM-153: this bullet said the
  two undefined sets were **identical** — `nitpick-regex`'s RX-120, 29 symbols
  each way, "reproduced here". At compiler `c3bdae2` they are 5 and 8, the call
  adding `npk_chain_push`, `npk_raise` and `npk_sys6`, and at `aaffb87` they
  were already 2 and 5. The scan sees the call; it can never flag it, which is
  the half the rule rests on.)* *(Cycle 0.3.1, TM-250: a second reading
  stands BESIDE it, never in for it. `check_call_edges` reads `npkc`'s
  emission of the umbrella for every call a function outside `src/host/`
  makes — a call through a name no ban list knows is a call like any other
  there — and cannot read a generic function nobody instantiates in it, which
  this check reads as spelled. The symbol scan still answers neither.)*
- **Live from cycle 0.0.3**, not from 0.3. It runs over the six non-`host`
  files today and reports `0` findings with the denominator printed, which is
  the same answer `check_no_owning_fields` gives over an empty set and is
  equally worth having.
- **Commissioned.** The self-check plants `mono_now()` in a scratch `src/cal/`
  and requires the check to find it, then runs it over a control where
  `mono_now()` appears **in a comment** and requires silence. That second half
  is not decoration: `src/host/host.npk`'s own header names `mono_now()` while
  explaining this rule, and `src/lib.npk`'s names `host_now_utc` while showing
  the shape of a re-export line, so a check that read prose would fail this
  repository on its own documentation — and the first draft did. *(And at
  cycle 0.3.1 in the real module, once: a full run over a copy with a
  `mono_now()` appended to `src/cal/cal.npk` is RED, this check naming the
  file, the line and the name, and `check_call_edges` the function and
  `npk_mono_now` — `meta/roadmap/0.3/0.3.1.md`'s record; TM-252.)*

The matching statement for `check_host_isolation` is the same three, with
`src/lib.npk` as its one **named** exemption (V-1c) rather than a pattern.

**Rule S-11 — there is no implicit local time.** `ntime` has no
`now_in_local_zone()`. A program that wants local time calls
`host_system_zone()`, which tells it which mechanism answered, and then
converts explicitly. A library that reads `$TZ` behind the caller's back
produces a program whose output depends on an environment variable nobody
mentioned — the same objection the sibling library raised against inferring
behaviour from `$TERM`.

---

## 4. Arithmetic

**Rule S-12 — every range is stated, and checked before the trap.** D-210
makes an overflowing `+` a controlled stop, which is the right *floor* but the
wrong *answer* for a library: a caller adding a century to a far-future
timestamp should get `ETimeValue` with `Overflow`, not a trap. Every
arithmetic entry point checks its operands against the supported range and
returns the error; the trap remains as the belt for a path the check missed.
*(Cycle 0.2.3, TM-234: `timestamp_add`, the first arithmetic entry point,
answers that caller with `ETimeValue` through `timestamp_of`, whose range
check it relays — so the detail is `YearRange`, the range's own name;
`Overflow` is `timestamp_since`'s, past `Duration`'s range, TM-236.)*

*(Cycle 0.2.4b, TM-241 and TM-242 — the cycle audit's C1 and C6.
`timestamp_add` checked the sum and not its operand, so a `secs` forged near
`int64`'s ends trapped before `timestamp_of` ran; it checks the operand first
now. `instant_since` subtracted in `int64` and trapped on a pair `instant_of`
builds; it computes in `int128` and refuses past `Duration`'s range now,
`Overflow`. **The rule's exceptions, named:** an arithmetic entry point that is
`never fails` by decision, its trap its range check — the four `Duration`
constructors (`SPAN_MODEL.md` N-2, TM-233) and `instant_add` (`TIME_MODEL.md`
M-4, TM-216). A deadline computed from them needs no test, and past ±292 years
the trap is the prelude's own answer for a span no `Duration` holds. Every
fallible entry point checks before the trap.)*

**Rule S-13 (TM-014) — the supported range is `year −9999 … +9999`**, proleptic
Gregorian, astronomical year numbering (year 0 exists and is 1 BCE).
`CALENDAR.md` §2 gives the reasoning and the exact bounds in every unit.

**Rule S-14 (TM-011) — `Timestamp` is `{ int64:secs; uint32:nanos }` and the
field order is semantic.** `#[derive(Ord)]` compares in declaration order (TRAITS_REFERENCE
§2.5), so seconds-then-nanoseconds is exactly the comparison wanted, and
reordering the fields would silently change what `Ord` means. A rule rather
than a comment because it looks like a style question and is not. *(Cycle
0.2.1, TM-219: both fields are `sealed`, `Ord` is derived on the type, and
`tests/unit/timestamp_order.npk` asserts the order on it.)*

**Rule S-15 — intermediate arithmetic widens explicitly.** Nanoseconds across
the full year range exceed `int64`: ±9999 years is about 6.3 × 10^20
nanoseconds and `int64` holds 9.2 × 10^18. Any computation that would produce
nanoseconds across a calendar-scale span computes in `int128` and narrows with
`=>!` at a point where the value is known to fit, or refuses. **This is the
single most likely place for this library to be wrong**, and §5 of
`SPAN_MODEL.md` is the full statement.

**Rule S-15b (TM-105) — there is no checked narrowing, so the range check
before a narrowing is library code.** Measured at cycle 0.0.0 by
`tests/probe/probe02b_narrow_unchecked.npk` and
`tests/probe/probe02c_narrow_refused.npk`: `=>!` at a value that does not fit
**truncates silently** — no trap, no diagnostic, exit 0 — and the checked
spelling `=>` at a narrowing is **refused at compile time**,
`NITPICK-TYPE-009`. A narrowing is therefore refused where it is written or
unchecked when it runs, and there is no third spelling.

So: **every narrowing conversion in `ntime` is preceded, on the same path, by a
runtime range check against the destination type's bounds**, and the failure is
`ETimeValue`/`Overflow` rather than a trap. This is not belt and braces over a
language guarantee — S-15's own sentence ("narrows with `=>!` at a point where
the value is known to fit") is now the *obligation*, and the check is what
discharges it. `VERIFICATION.md` P-5's `prove` documents the obligation and
does not replace it: `prove` is a comment until the compiler's 1.5, and a
static obligation afterwards, while the check answers what happens to a caller
who violated the precondition.

The shape the rule requires is committed rather than described —
`tests/probe/probe02_int128.npk`'s `ns_add_checked`:

```nitpick
func:ns_add_checked = int64(int64:a, int64:b, int64:fallback) never fails {
    int128:wide = (a => int128) + (b => int128);
    if (wide > (I64_MAX => int128))                { pass fallback; }
    if (wide < ((0i64 - I64_MAX - 1i64) => int128)) { pass fallback; }
    pass (wide =>! int64);
};
```

Note the **widenings are spelled `=>`**, and deliberately: the checked cast is
legal in that direction and using it leaves exactly one `=>!` in the function —
the dangerous one. A file where every cast is `=>!` hides which is which.

**The failure this rule exists to prevent**, stated once so it is not
rediscovered: a positive `int128` narrowing to a negative `int64`, because what
`=>!` discards is everything above the destination's sign bit. In a time
library that is a future instant reported as long past, with no error anywhere.

**Rule S-15c (TM-171, cycle 0.1.3) — a narrowing of a value THIS LIBRARY
COMPUTED is checked the same way, and its failure is `#unreachable()`.** S-15b
answers a caller who broke a precondition, so its failure is an `ETimeValue`.
A value the library derives itself, whose range holds by construction, has no
caller to answer — and a `never fails` function has no error to return — so
the range check before the narrowing ends in the compiler's `#unreachable()`,
which traps through the floor's `Unreachable`: a controlled stop, and no new
arm. **Manufacturing an enum tag is a narrowing in this rule's sense.**
`intN =>! Enum` is permitted and unchecked (the compiler's D-140), and a tag
outside the enum's range is a value that is none of its variants: measured at
cycle 0.1.3, it makes every arm of an exhaustive `pick` miss and the statement
fall through, silently (`meta/roadmap/done/0.1/0.1.3.md` §2). The one site today is
`src/cal/cal.npk`'s `weekday_index`, whose modulus correction keeps every
index in 0 … 6; the check after it is what makes the correction's absence a
stop rather than a `Weekday` that is no weekday (`CALENDAR.md` C-13).
*(Cycle 0.2.2, TM-222: "the one site" was true until `src/span/span.npk`'s
`timestamp_to_utc`, which applies this rule's answer to a refusal rather than a
narrowing. The day number and the second of the day it computes lie in the
range by construction — a `Timestamp` is in it, and the floor keeps the second
in 0 … 86 399 — so the refusals of `days_to_date` and `civil_time` cannot meet
them, and each is `?| #unreachable()`: a controlled stop, and no new arm.)*

**Rule S-16.** Nothing divides by a value it has not proven nonzero on the same
path. The calendar algorithms divide by literals and nothing else — among them
4, 100, 400, 146097, 86400 and 1000000000, the six this rule was written with.
In `src/cal/` the rule is `CALENDAR.md` C-11, whose list of divisors is
`check_literal_divisors`' on every run.

*(Amended at cycle 0.1.1, TM-163. The sentence read "divide by literals (4, 100,
400, 146097, 86400, 1000000000) and nothing else" — a closed list, which
Hinnant's `civil_from_days` falsified on arrival with 5, 153, 365, 1 460,
36 524 and 146 096, and `weekday_number_sunday_first` with 7. The six stay
named because `check_constants_named`'s owner map cites this rule for 86400 and
1000000000, which `src/cal/` does not divide by yet: they are the conversions to
come, and this rule and that map move together when a second module wants
them.)*

*(Cycle 0.2.2, TM-223: the conversions came, and they are `span`'s, not
`cal`'s. `timestamp_to_utc` divides the seconds by `NTIME_SECS_PER_DAY`, read by
name from `src/core/limits.npk` — a `fixed` that `tests/unit/limits_named.npk`
holds to 24 × 60 × 60 on every run, divided by under the compiler's own zero
check, `DivByZero`, which every importer of `span` owes already (the IR at
`5fbaf4a`). The owner map moved with this rule, as the note above said: 86400
belongs to `core` alone, spelled once and read by name everywhere, and
1000000000 stays `cal`'s until cycle 0.2.3's nanosecond arithmetic decides.)*

*(Cycle 0.2.3a, TM-231 and TM-232: 1000000000 is `core`'s alone too — `cal`
reads it by name, `NTIME_NANOS_PER_SEC`, and so does `span`, so the one copy
is `src/core/limits.npk`'s. And a copy is a copy in any spelling: the owner
map's check reads a literal as the compiler's lexer does — every base, `_`
wherever it stands, every width, a character literal's code point — so
`1_000_000_000i64` or `15180hexi64` outside `core` is a finding, where until
then each passed.)*

*(Cycle 0.2.4a, TM-238 — the cycle audit's C3: "the one copy is
`src/core/limits.npk`'s" is now what the check holds. Until then it held a copy
to the module `core`, so `86400i64` in `src/core/bytes.npk` passed it. And the
record these notes keep, completed — the audit's K4: `timestamp_add` (cycle
0.2.3) divides a `Duration`'s nanoseconds by `NTIME_NANOS_PER_SEC`, read by
name, with `/` and `%`; the IR guards each with the compiler's zero check and
its `MIN / −1` check (`npk_trap` −4097 and −4098, at `5fbaf4a`), and
`tests/unit/limits_named.npk`'s exit 18 holds the divisor to 10⁹, so neither
can fire.)*

**Rule S-17.** Every index into the zone tables goes through one accessor pair,
and the accessor is where the bound is checked. Callers do not index raw
storage. This makes the bound one obligation to discharge in cycle 1.5 rather
than several hundred.

**Rule S-17b (TM-108) — the bounds check attaches to the TYPE, and neither of
this library's two containers carries one.** Until this rule, S-17 read as
tidiness laid on top of a language guarantee. It is not tidiness: for `Vec<T>`
and for `Bytes` the accessor is the *only* bounds check that exists.

D-070's guarantee attaches to types that carry a length — its own title is
"`T[]` is a slice: bounds live in the array type, **not the pointer type**",
and its body says the slice is "where out-of-bounds detection actually comes
from, and it is why pointers do not need to carry it". Read in the compiler's
emitter rather than in a summary: `ExprIndexExpr` in
`src/backend/ir/ir_expr.npk` switches on the indexed object's type kind and has
exactly four branches.

| Indexed type | Carries a length | Out-of-range index |
|---|---|---|
| slice `T[]` | yes — `{ptr, i64 len}` | **traps**, `OutOfBounds` |
| fixed array `T[N]` | yes — in the type | **traps**, `OutOfBounds` |
| `simd<T, N>` lane | yes — the lane count | **traps**, `OutOfBounds` |
| bare pointer `T->` | **no** | **reads**, silently |

The first three each call `emit_bounds_guard`; the pointer branch emits a
`getelementptr` and nothing else. And **a qualifier is not part of the type** —
`parse_type.npk`'s second header fact is that `wild`, `wildx`, `fixed` and the
borrow markers live on the declaration, not on the type node — so
`wild T->:items` is a bare pointer to the emitter, and takes the fourth row.

**`buffer` has no branch in that switch at all**, which is worth stating
because the sentence this rule replaces named it. A `buffer` is the managed
owning byte cell (compiler `TYPE_REFERENCE.md` §23, D-200); its `.ptr` member
is a `uint8->`, and §23's own example indexes it as `buf.ptr[0i64]` — *"byte
reads index the ptr"*. So a `buffer` is indexed **through the fourth row**.
There is no slice view of a `buffer` to reach for instead: `buffer_bytes`, a
borrow of the body, is listed under §23's *"deliberately NOT landed"*, to be
added by decision when a consumer exists.

**What that means table by table, which is the part that changes work here:**

- **The generated zone tables still trap** — but for a reason the old sentence
  did not give. S-19 makes them `fixed` module state, so they are `T[N]`, the
  second row. The old row's zone-table example was the one case it happened to
  get right, and it got it right by accident.
- **`Vec<T>` does not trap.** B-12 gives it `wild T->:items`, so `Layout`'s
  `Vec<FmtPart>` (`FORMAT_MODEL.md` §3) and every grown zone collection index a
  bare pointer. An out-of-range read is **a wrong value**, not a crash.
- **`Bytes` does not trap either**, and this is the wider blast radius: B-12
  makes it "an owning byte sink over `buffer`", and **every formatter writes
  into one**.

**What follows:**

- **S-17's accessor pair is load-bearing, and it now covers `src/core/` as
  well as the zone tables.** Every read and write of a `Vec` or a `Bytes` goes
  through its accessor, which checks against `count`/`len`, and a tree check
  fails on any `.items[` outside `src/core/vec.npk` or any `.ptr[` outside
  `src/core/bytes.npk`. That check belongs on cycle 0.0.3's list beside
  `check_layering`.
  *(Amended at cycle 0.1.0c, TM-156: **for `Vec` the pair is now the
  LANGUAGE's rule, and for `Bytes` it is still the library's.** `Vec<T>.items`
  is `hidden` — the compiler's D-314 — so outside `src/core/vec.npk` the bare
  pointer cannot even be read: `v.items[0i64]` is `NITPICK-TYPE-080` at compile
  time (`tests/probe/probe16b_vec_items_read_refused.npk`), and the tree check's
  `.items[` half is a belt behind the compiler. `Bytes`' `body` is `sealed`, not
  hidden, and D-313 lets a write THROUGH a sealed pointer field pass, so a
  consumer's `b.body.ptr[i] = x` still compiles and runs, unchecked, measured
  at `c3bdae2` — `check_raw_index`'s `.ptr[` half covers `src/` and nothing
  covers a consumer. That gap is the workbench's question 9, with the author.)*
  *(Amended at cycle 0.1.3c, TM-195: **for `Bytes` too the pair is the
  LANGUAGE's rule now.** The author answered question 9 on 2026-09-25, and
  `body` is `hidden`: outside `src/core/bytes.npk` every access to it is
  `NITPICK-TYPE-080`, the write through its pointer included
  (`tests/probe/probe16i_bytes_body_write_refused.npk`, which compiles against
  the library before and reads the consumer's byte), and a consumer reads the
  capacity through `bytes_capacity`. `check_raw_index`'s `.ptr[` half is now a
  belt behind the compiler, as its `.items[` half has been since 0.1.0c.)*
- **Signedness is half the check.** `count` is `int64`; an index derived from a
  narrower signed field can be negative, `i < count` accepts it, and the read
  goes backwards off the block. Every accessor checks `0 <= i` as well as
  `i < count` — **and TM-129 says how, which is not two comparisons.**
- **An unchecked index is a WRONG ANSWER, not a crash**, which inverts the
  failure mode §1 advertises. In a date library that is a wrong offset for one
  zone, or a formatted field taken from an unrelated heap word — silent, and
  reachable from caller-controlled bytes once `src/fmt/` parses.
- **`VERIFICATION.md`'s `Vec<T>` `at`/`set` row** (index `< count`, by contract
  and by Z3) stops being a restatement of a language guarantee and becomes the
  obligation that discharges this rule. *(That row stated only `< count` and the
  obligation is `0 <= i && i < count`. This footnote said it had been "corrected
  there at cycle 0.0.4" — in `0.0.4.md`, a roadmap execution record, which is
  not the specification. A specification known to be wrong, left standing, with
  the correction in a file nobody reads to find the rule, is F4. **The row in
  `VERIFICATION.md` now carries the full obligation**, corrected at cycle 0.0.6,
  and this footnote records that it once did not.)*

**Rule S-17c (TM-129) — the accessor puts the language's OWN guard back, rather
than reimplementing it.** Every `Vec<T>` accessor lays a length-carrying slice
over the block and indexes that:

```nitpick
T[]:s = #wild_slice<T>(v.items, v.count);   // over `count` for a LIVE element
pass s[i];
```

*(Since cycle 0.1.3c `vec_at` ends `pass raw s[i].pod_copy();` — it takes
`T: Pod`, S-18h — and the index its slice guards is the same `s[i]`. And
since cycle 0.2.0a it ends `pass s[i];` again, at the prelude's `T: Copy` —
TM-211.)*

**THE EXCEPTION IS `push`, AND IT IS PART OF THE RULE RATHER THAN A DEPARTURE
FROM IT (F2, TM-143).** This code block read *"over `count`, never over `cap`"*
until cycle 0.0.6, and three sites in the library lay the slice over `cap` —
`vec_push` and `bytes_push`/`bytes_extend`, each at its `#wild_slice` over `cap`
(cited by function since cycle 0.1.0b: the line numbers this sentence gave had
moved, and moved again when that subcycle added comments above them). Each
argues the exception in a source comment, and
`CLAUDE.md` forbids amending a specification by a comment, so the rule is
amended here instead. **The rule in full:**

> A slice for READING or OVERWRITING a live element is laid over `count`. A
> slice for APPENDING is laid over `cap`, because the valid index there is
> `count` itself, which a slice over `count` rejects — and the preceding
> `*_reserve` has just made `cap > count`, so the index is in range by
> construction and the guard is the belt.

A guard over `cap` in a READ accessor would accept an index into
allocated-but-dead space, which is exactly the distinction `probe13b` exists to
catch: it has room at `i == count` because `cap` is larger, and it still traps.
That is the sentence the original absolute was protecting, and it survives
intact — S-18c already carved `vec_push` out for the *drop* obligation on the
same argument, so this makes the two carve-outs one carve-out.

The index then takes the `TY_SLICE` branch and `emit_bounds_guard` runs, so the
check is the compiler's and cannot drift from D-070. **One unsigned compare
covers both ends**: `emit_bounds_guard` emits `icmp ult i64`, and
`index_as_i64` sign-extends a narrower index first, so — in the compiler's own
words — *"a negative index of any width becomes a huge unsigned value and ONE
unsigned compare rejects both `negative` and `past the end`."* A hand-written
`i >= 0` beside it would be dead code.

Committed and measured at pin `0dfddac`:
`tests/probe/probe13_vec_bounds_guard.npk` (in range, exit 0),
`probe13b_vec_index_past_end.npk` (`i == count` with room at that index —
**exit 94**), `probe13c_vec_index_negative.npk` (`i == -1` — **exit 94**, with
no `i >= 0` anywhere in the accessor), and
`probe13d_vec_bare_pointer_unchecked.npk` — the control, which does the same
read through `v.items[i]` and **exits 0 having returned a planted sentinel from
past the end**. Until `probe13d` this rule rested on a reading of the emitter
and nothing here had ever run an out-of-range `Vec` index.

*(Amended at cycle 0.1.4c, TM-190.)* At compiler `c970483` `probe13d`'s
accessor is written at `int64`, not generically: the compiler's DEF-104
refuses a generic `pass` of a `T` place read through a pointer, at every `T`
(`NITPICK-TYPE-047`), because at an owning `T` it would hand the caller a copy
of an element the container still owns. The claim is about the pointer and
not the generic — at `int64` the read is the same load — and it still returns
the sentinel from past the end without trapping, on both legs. This
library's own accessors are not reached: each reads through a `#wild_slice`
it lays over the block, and `vec_pop` spells `move`
(`meta/roadmap/done/0.1/0.1.4c.md` §1.3).

> **And the arm bill cannot tell the two spellings apart, which is why this
> went unnoticed.** `NITPICK-REACH-003` bills a consumer of the guarded
> accessor six identities — `Unreachable`, `HeapOom`, `HeapBadRequest`,
> `WildLeak`, `IntOverflow`, `OutOfBounds` — and bills the **bare-pointer**
> accessor **the same six**. So the reachability analysis arms `OutOfBounds`
> for an index that emits no guard at all: every consumer of an unguarded `Vec`
> is compelled to write an arm for a trap that *cannot fire*, while the read it
> is meant to protect returns a wrong value in silence. Adding the guard makes
> that arm honest; it does not add it.

*(Amended at cycle 0.1.0c, TM-156.)* **Since `items` is `hidden`, this rule's
guarded accessors are the ONLY index into a `Vec` another module can spell** —
the bare-pointer read `probe13d` makes on its own look-alike `Vec` is
`NITPICK-TYPE-080` on this library's, measured at `c3bdae2`. Inside
`src/core/vec.npk` the rule is still this document's discipline, since the
declaring module sees its own hidden field. For `Bytes` nothing changed at the
accessors, and a consumer can still index `body.ptr` directly (S-17b's
amendment above — until cycle 0.1.3c, which hid `body`). And `count`, `cap`
and `len` now carry the prelude's
`ListLen`, checked after every write: in a plain build that is one more check
correct code never trips, and in the verified build it makes every read of the
lengths a fact the slice producers' `bounds` rows can use (S-4b's `limit` row
is the arm it costs).

**And the nuance that makes this a claim about *this* library.** There is **no
compiler-prelude `Vec<T>` at all.** No `struct:Vec` exists anywhere in the
compiler's tree; `lib/nvec.npk` is D-200's small-vector tier over
`simd<flt64, N>` and not a container. The shared shape is a **convention** each
library adopts from the compiler's `List<T>`, which is exactly what B-12
records when it says the shape is the compiler's and the type is ours. So a
sibling library that later spells its `Vec` differently, with a managed body or
a slice field, gets a **different safety property with no diagnostic
anywhere**. Read that library's own declaration; do not carry this rule across.

**Where `List<T>` is, and the divergence that matters (TM-113, amended
2026-09-05 against pin `0dfddac`).** It is the compiler's
`src/prelude/prelude.npk`, a `pub
struct:List<T>` in the **prelude**; the `src/frontend/list.npk` this paragraph
used to cite was deleted when D-239 moved it, and the comment it used to quote
— *"WILD, DELIBERATELY"* — occurs **zero times in the compiler's 607 `.npk`
files** at that pin. The layout is still ours verbatim, three fields, `wild
T->:items` first. **The semantics are not, and the gap widened rather than
closed:** the prelude's `List<T>` is now **compiler-known and OWNING** (D-247),
so the layout marks it owning and *a generated drop releases its `count`
elements through `T`'s drop and hands the block back*. `ntime`'s `Vec<T>` is an
ordinary struct and gets none of that. So the two facts this section rests on
survive the move and one of them is now stronger: the bounds obligation is
`ntime`'s (S-17b), **and so is the whole element-lifetime obligation** — which
is TM-106 measured, and which a reader who reasons from "our `Vec` is the
compiler's `List`" would now get exactly backwards.

*(Cycle 0.1.5, of TM-193: two phrases above are inexact since cycle 0.1.3c's
marker. A `Vec<T>` has a FOURTH field, `hidden string[0]:move_only`, zero bytes,
and the layout walk marks a `Vec` OWNING for it — so "three fields" is four, and
"gets none of that" is true of the drop and not of the mark: the drop the
compiler generates for a `Vec` frees nothing, because its one owning field
holds no element and `items` is a bare pointer the walk does not follow
(`tests/probe/probe18_zero_length_owner.npk`). The conclusion stands: the
element-lifetime obligation is `ntime`'s.)*

*(Cycle 0.2.0b, TM-214: it is `ntime`'s, and the type discharges it —
`Vec<T: Copy>` admits no element with anything to drop, which the compiler
checks where the `Vec` is written (S-18d's amendment).)*

---

## 5. Resources

**Rule S-18.** `ntime` allocates only where it returns a `string` — formatting,
and the zone name lookup. Everything else is value arithmetic on the stack.
Growable storage is the library's own `Vec<T>` (`BUILD.md` §5), whose block is
`wild` and whose lifetime is its owner's scope; every `wild` byte is released
on every path, so `exit 0` never trips D-151.

**Rule S-18b (TM-106) — a `Vec<T>` over an owning `T` is emptied before its
block is freed, and `exit 0` does not check it.** D-151 watches `wild`
allocations; a `string`'s body is **managed**. So a `Vec<string>` whose block is
freed and whose elements are not is a leak that exits 0 — measured at cycle
0.0.0, re-measured unchanged at the 2026-09-04 re-pin, and **re-measured again
at pin `0dfddac` on 2026-09-05**: 125 184 KiB retained over 2 000 000 elements,
and `HeapOom` (exit 92) under a 64 MiB address-space cap. The committed pair is
`tests/probe/probe06b_element_leak.npk` and `probe06c_element_drop.npk`, which
differ in one line.

**The remedy half's cost, corrected (TM-128).** This rule read *"completes the
same two million iterations in **under 768 KiB** of address space"*, and that
figure is **not reproducible**: at `ulimit -v 768` — and at 1024, and at 2048 —
the program does not exec at all, and neither does `/bin/true`, which fails the
same way with *"failed to map segment from shared object"*. **About 2 MiB is
this machine's exec floor for any process**, so no run can be "clean at 768".
The measured bound is:

| | peak RSS | exit at `ulimit -v 65536` |
|---|---|---|
| leaking half | 125 184 KiB | **92**, `HeapOom` |
| corrected half | **1 660 KiB** | **0** |

**And the column that is NOT here is the correction (TM-131).** This rule
briefly carried a "smallest clean `ulimit -v`" of **3 072** for the corrected
half. That number is the machine's and not the library's: bisected point by
point, `probe06c` and **`/bin/true`** return the same exit at every cap and both
flip between **2688 and 2816 KiB**. So a low `ulimit -v` cannot measure this
program at all, and *"clean at 3 MiB"* is a gate `/bin/true` also passes.
**Quote the two columns above** — one shared 64 MiB cap with opposite outcomes,
and the peak-RSS pair — and take any address-space bound with a `/bin/true`
control **at the same cap**.

**Both figures may now be quoted, and that is a change too.** This rule used to
say *"quote the address-space bound and not a peak-RSS figure"*, because
`/usr/bin/time -f %M` reported `0 KiB` for these static binaries. It does not
report 0 for these: the gauge under-reports a *small* RSS, not this one. The two
numbers now check each other — 125 184 − 1 660 = 123 524 KiB over 2 000 000
orphaned elements is ≈ 63 bytes each, which is a 35-byte body in a 64-byte size
class — and a corroboration is worth more than a rule against one of the
numbers. **Take any address-space bound with a `/bin/true` control at the same
cap**, because below about 2 MiB every exit code on this machine is the
loader's.

**SINCE CYCLE 0.1.4b THE HARNESS ASSERTS THE PAIR ON EVERY RUN, AND THE
CONTROL HAS MOVED** (TM-184 … TM-186, `TESTING.md` V-17). `probe06b` carries
`heap: peak_live >= 70000000` — two million 35-byte bodies, every one live at
the peak — and `probe06c` `heap: count >= 2000000` and `heap: peak_live <=
64000`, so the leak, its remedy and a remedy emptied of its work are three
different verdicts; both run again under one shared 64 MiB cap, 92 against 0.
Measured at compiler `c3bdae2`, both legs: `probe06b` `peak_live=70000024`,
`probe06c` `peak_live=59`. **The `/bin/true` control above no longer controls
for this runtime**: at `c3bdae2` a program that allocates nothing takes
HeapOom below about 10.5 MiB, where `/bin/true` runs from 2.75 MiB, so the
harness's control is that floor program, built by the same toolchain.

Each element is moved into a scope that ends:

```nitpick
while (i < v.count) {
    string:owned = move(v.items[i]);   // dies at the bottom of this iteration
    i = i + 1i64;
}
```

A generic `vec_free<T>` cannot do this, so it is the **owner's** obligation at
each instantiation: moving an element out needs a destination of type `T`, and
a generic function has no scope in which a bare `T` may simply die. S-18's "so
`exit 0` never trips D-151" is therefore a statement about the block alone —
correct, and not the whole obligation.

*(Cycle 0.2.0b, TM-214: since `Vec<T: Copy>`, the library's `Vec` holds no
owning `T` — a `Vec<string>` is `NITPICK-TYPE-017` where it is written — so
this rule's obligation arises for no `Vec` of this library's, and S-18's
statement about the block is the whole of it. The rule stands as the measured
fact under the bound: a container of owning elements in `wild` storage leaks
what it does not drop, and `exit 0` cannot see it — `probe06b` and `probe06c`
pin it with a `Vec` of their own, and remain the instrument's leak and remedy
(`TESTING.md` V-17).)*

**Rule S-18c (TM-127) — OVERWRITING an element discards one too, so the
obligation covers `vec_set` and not only the three that sound like it does.**
S-18b and `0.0.4.md` §2 both name three entries that discard elements —
`vec_free`, `vec_clear`, `vec_truncate` — and `vec_set` is a fourth. It is the
least visible of the four precisely because the other three sound destructive
and it sounds like a replacement.

Measured with the committed pair `tests/probe/probe12_set_overwrite_leak.npk`
and `probe12b_set_overwrite_drop.npk`, which differ in one statement and **both
exit 0**: 2 000 000 overwrites of one occupied `Vec<string>` slot retain
**125 184 KiB** and take `HeapOom` under a 64 MiB cap, while the form that moves
the outgoing element into a dying scope first finishes in **1 596 KiB** and is
clean down to a 3 MiB cap. *(At pin `0dfddac`. At compiler `c3bdae2` it and a
program that allocates nothing take HeapOom below about 10.5 MiB, the
runtime's own floor; `probe12`'s header has the re-measured table. Since cycle
0.1.4b the harness asserts this pair as it does S-18b's: `peak_live >=
70000000` for the overwrite, `count >= 2000000` and `peak_live <= 81000` for
the remedy, and 92 against 0 under the 64 MiB cap — measured at `c3bdae2`,
`peak_live=70000059` against `94`.)*

**This is the `wild` qualifier behaving as specified, not a compiler defect**,
and two controls establish it against the contrary reading of the compiler's
D-186 (*"overwriting an owning field or managed element drops the old value"*):
the same overwrites into a **local binding** cost 1 660 KiB and drop correctly,
while the same overwrites written **directly at the site** with no call
anywhere cost the full 125 184 KiB. The property is the destination's — a
*managed* element drops, a `wild T->` element does not, because `wild` is the
manual regime — which is the same sentence that makes `vec_free` the caller's
job.

**`vec_push` is exempt, and the reason must be stated because the two lines of
code are identical**: it writes at `count`, which is past the last live element
by construction, so there is nothing there to discard.

> **The remedy is still not available generically, and the REASON CHANGED at
> cycle 0.0.5 (TM-136, S-18d below).** This paragraph read *"accepted by `npkc`
> at exit 0 and refused by `llc` — O-N17"* until cycle 0.0.6, and **that was
> false at pin `aaffb87`**: O-N17 is FIXED, all five of its reproduction cases
> link and run, and S-18d fifty lines below said so while this said the
> opposite. Both were live rules in the authority document (D3). What is true
> now: the drop loop as `vec.npk` would spell it — one hoisted `#wild_slice`
> binding with `move(s[i])` inside a `while` — is refused **`NITPICK-MOVE-001`**,
> because moving out of an element invalidates the binding the element was
> reached through and the next iteration reads it again. It is refused at
> `T = int64` as well, so it is a move-tracker rule and not an ownership one.
> Re-making the slice inside the loop body compiles, and so does
> `move(v.items[i])` through the bare pointer, which S-17c forbids here because
> it loses the bounds guard. So at an owning `T` a generic `vec_set<T>` today
> either leaks or does not compile, and both halves of the committed pair are
> written at the instantiation, which is where this rule already puts element
> lifetime. `tests/probe/defect/generic_element_move/`.

*(Cycle 0.2.0b, TM-214: `vec_set` is `vec_set<T: Copy>`, so the element it
overwrites has nothing to drop, and at an owning `T` it is not written —
`NITPICK-TYPE-017`. The pair above keeps its own `Vec` and is the measured fact
the bound rests on, and the instrument's second known leak.)*

**Rule S-18d (TM-136, amended by TM-150) — THE RESTRICTION STAYS, AND WHAT IT
RESTS ON NOW IS THE ELEMENT DROPS, WHICH NO COMPILER CHECK AND NO LEAK GATE
SEES.**

> **Amended at cycle 0.2.0b (TM-214) — THE COMPILER CHECKS IT NOW, AT THE
> TYPE.** `Vec` is `struct:Vec<T: Copy>`, and every one of its nine verbs states
> `T: Copy`: a generic body is checked once, against the bounds it declares, so
> with the struct bounded a verb without the bound is `NITPICK-TYPE-017` at its
> own definition (measured, all eight that lacked it). An owning `T` is refused
> wherever it is written — the type, each turbofish, each verb's call;
> `Vec<string>`, `Vec<Bytes>`, `Vec<Vec<int64>>` and `Vec<cstring>` each
> `NITPICK-TYPE-017` at all three — and `generic_owning_copy/case5` asserts six
> such sites. So the four drops below are owed at no `T` the type admits, which
> is the restriction, stated where the compiler reads it; this rule's title and
> the amendments under it are the record of how it was reached. **The bound is
> a little wider than the restriction**: a pointer, a slice, an optional and a
> fixed array own nothing, and each is refused as the element too, not being
> `Copy` — as is a struct of scalars until it claims `Copy`; a struct that
> claims it may hold any of the four. **At every `T` the
> type admits, no code changed**: of the tree's 128 `.npk`, the 89 that compile
> both without the bound and with it emit byte-identical IR, and three verdicts
> moved — the two halves of TM-150's churn pair, from compiling to refused, and
> `case5`, from two sites to six. **The churn pair is retired** (TM-196's two files):
> the `T` it measured cannot be written over this `Vec`, and the language fact
> it stood for is `probe06b`/`probe06c`'s and `probe12`/`probe12b`'s, each over
> a `Vec` of its own. **What `Copy` does not ask**: a `#[derive(Copy)]` struct
> holding a pointer or a slice is a legal element (measured) — it drops
> nothing, which is all this rule asks; where its view points is S-18e's rule
> and S-22's, wherever the view is held.

> **Amended at cycle 0.1.0b (TM-150).** This rule's title read *"THE
> RESTRICTION IS NOT ENFORCEABLE BY THE COMPILER"*, and its reason — below, as
> written — was that `NITPICK-TYPE-046` does not fire inside a generic function
> body. **At compiler `c3bdae2` it does**: the compiler's D-264 makes a bare type
> parameter move-only in the body that names it, so `T:answer = s[i]` is refused
> where it is written, at every instantiation (`generic_owning_copy/case1`,
> `case3` and `case4` assert it; `aaffb87`'s verdicts are their controls). A
> future `Vec<T>` function that reads an owning element without `move` no longer
> compiles. **What is still unenforced is the element drops:** at an owning `T`,
> `vec_set`, `vec_clear`, `vec_truncate` and `vec_free` each discard elements
> they do not drop — a leak that exits 0, because D-151 counts `wild` blocks and
> cannot see a managed body (TM-106) — and `vec_at<T>` still removes the element
> it reads (`pass` of a place moves; exit 11, the language as specified). So
> `Vec<T>` stays restricted to a non-owning `T`, on that one reason. `vec_pop<T>`
> is not among the four: its `move` hands the element to the caller, measured
> at `T = string` at `c3bdae2` (two million push-then-pop cycles, `peak_live`
> 120 bytes). The text below is the rule as it stood from cycle 0.0.5.

> **Amended at cycle 0.1.3c (TM-194, TM-196).** `vec_at<T>` no longer removes
> the element it reads: it takes `T: Pod` (S-18h), and at an owning `T` the
> call is refused, `NITPICK-TYPE-017` (`generic_owning_copy/case5`, which
> exited 11 on the removal until then). So the destructive read is gone from
> the list above and the restriction rests on the four drops alone, which no
> type here states — `struct:Vec<T: Pod>` would, and is declined for now
> (TM-194; the bound is the prelude's `T: Copy` since cycle 0.2.0a, TM-211). **TM-150's churn pair is a program with bounds**:
> `tests/unit/vec_churn_pop.npk` holds two million push-then-pop cycles at
> `T = string` to `peak_live <= 75000` (it measures 120) and
> `vec_churn_clear.npk`, `vec_clear` in the pop's place, to `peak_live >=
> 48000000` (it measures 48 000 096), each also under the 64 MiB cap (V-17).

*(Placed after S-18c since cycle 0.0.6. It was
above it for one subcycle, which is why the two paragraphs read as one
argument and their disagreement about O-N17 was invisible — F6, and the
cosmetic finding that made D3 possible.)* S-18b puts element lifetime at the instantiation
and TM-132 restricted `Vec<T>` to a non-owning `T` because O-N17 blocked the
generic drop path. **O-N17 is fixed** at pin `aaffb87` — all five reproduction
cases link and run. The restriction stands anyway, on a measurement taken in
the same hour: **`NITPICK-TYPE-046` does not fire inside a generic function
body** — raised as **O-N19** and accepted by the compiler as a soundness hole
in the checker (`../OPEN_QUESTIONS.md`). `T:answer = s[i]` at an owning `T` — a copy of an owner, which that
diagnostic exists to refuse — is accepted at exit 0, links, runs, and produces
two owners of one heap body; the identical statement with `string` written out
is refused. Reading through the second owner after the first has dropped
returns the allocator's `0xAA` poison, exit **170**
(`tests/probe/defect/generic_owning_copy/`, reproduced at all four pins this
workbench has used).

So a `Vec<T>` advertised as safe at an owning `T` would rest on the author
never writing a bare read, with **no compiler check and no leak gate behind
it** — D-151 counts `wild` blocks and cannot see a managed body (TM-106). Two
rows were already wrong when this was found: `vec_pop<T>` shipped the bare read
and now writes the `move`, and **`vec_at<T>` at an owning `T` REMOVES the
element** — `pass` of a place moves implicitly, `count` is untouched, and a
second read of the same index returns a length-0 string (exit **11**). The last
of those is the language behaving as specified; the first was ours.

**Rule S-18e (TM-139) — A VIEW INTO A GROWABLE CONTAINER IS VALID UNTIL THE
NEXT CALL THAT CAN GROW IT, AND NO GATE HERE CAN FIND A VIOLATION.**

`bytes_view` returns a slice over the sink's body. `bytes_reserve` grows by
allocating a fresh `buffer`, copying, and overwriting `b.body` — which **drops
the old one** (the compiler's D-186). So a view taken before a growth points
into released memory, and reading it returns the allocator's `0xAA` poison
(D-183): measured at pin `aaffb87`, the byte comes back **170**.

`bytes_view`'s own header claimed the opposite — *"valid exactly as long as the
`Bytes` is"* — from cycle 0.0.4 until this rule was written, and **both it and
`bytes_push` are on the public surface** (`src/lib.npk`). A consumer following
that comment wrote a use-after-free that compiles, links, runs and reads poison.

**THE STRUCTURAL POINT, WHICH IS WHY THIS IS A RULE AND NOT A COMMENT FIX.**
It is the second use-after-free cycle 0.0 shipped on this library's own surface
— `vec_pop<T>` at 0.0.4 was the first (S-18d) — *(and there was a third,
found at cycle 0.1.4b by a COUNT rather than by reading: `bytes_take`, S-18f)*
— and both were invisible for the
same reason: **every gate this repository owns is a leak gate.** D-151's exit-0
trap counts `wild` allocations and cannot see a managed body (TM-106);
`check_raw_index` is about indexing; the undefined-symbol scan is blind to it;
`check_purity` answers a different question. A leak is found by a gate. **A
use-after-free is found by a WRONG ANSWER, so it is found by a test that reads,
and by nothing else.** `tests/unit/bytes_view_lifetime.npk` is that test, with
its control: a view held across forty NON-growing pushes reads back correctly,
and the same program at a capacity that forces growth does not.

**The obligation this puts on `src/fmt/` at cycle 0.4** *(it said "0.3" until
cycle 0.1.5's second half; `src/fmt/` is cycle 0.4's, as S-18f below and the
module's own header say)*, which is where views into a `Bytes` will actually
be held:

- a function that returns or stores a view states the invalidation rule at the
  site, in the words above;
- inside the library, **a `#wild_slice` binding is made AFTER the `*_reserve`
  call in the same body, never before**. Both `src/core/` files obey it today —
  `vec_push` and `bytes_push` call reserve first and then lay the slice — and
  it is a lexical property a check can hold them to when there is a second file
  that needs one;
- `Vec<T>` does **not** have this shape and the reason is worth writing down
  rather than rediscovering: `vec_reserve` reallocates too — with `ralloc`
  since cycle 0.1.0b (TM-150), which invalidates the old pointer just as surely
  — but **no function in `vec.npk` returns a slice**, so there is no view for a
  caller to hold. `vec_at<T>` returns by value.

**Rule S-18f (TM-188) — no function hands back a `string` made by
`string_from_bytes`, because the type cannot tell a view from a copy.**
`string_from_bytes` wraps existing bytes as a VIEW — capacity 0, by the
compiler's own `BUILTIN_REFERENCE.md` row, at every pin this repository has
kept — and its answer is typed `string`, which a caller reads as owned.
`bytes_take` handed out exactly that from cycle 0.0.4 to 0.1.4b, under a
comment saying it copied. Measured at compiler `c3bdae2`, both legs: taken,
and then the sink cleared and refilled as that comment recommended, the answer
read the NEW bytes; taken, and then the sink grown, it read freed memory —
S-18e's use-after-free. **Nothing caught it**: `tests/unit/bytes_growth.npk`
read the answer only before either.

**It was found by COUNTING.** The runtime's `NPK_HEAP_STATS` reported 25
allocations for `bytes_growth` where its source makes 26 — a copy is an
allocation, and a view is not. So it is the third use-after-free cycle 0.0
shipped on this library's surface, beside `vec_pop<T>` (S-18d) and
`bytes_view` (S-18e), and the only one that reading had not found: a number an
instrument prints is derived from the source before a bound is put on it, and
one that disagrees is a finding (`TESTING.md` V-17).

`bytes_take` copies now — `string_concat` of the view and `""`, owned by that
builtin's own `Views` column — and `bytes_growth` asserts that its answer
survives both a reuse of the sink and a growth of it. **The obligation this
puts on `src/fmt/` at cycle 0.4**: a function whose answer is a `string`
returns a copy. And `FORMAT_MODEL.md` F-10's thin wrapper — fill a local
`Bytes`, hand back its text — cannot `pass bytes_take(@sink)` at `c3bdae2`
whatever `bytes_take` does, because the borrow tracker refuses the call's
answer as a borrow of `sink` (`NITPICK-BORROW-001`), while a take that
consumes the sink by `move` compiles and is correct on both legs; measured,
and carried to `meta/roadmap/0.4/README.md`.

**Rule S-18g (TM-193, cycle 0.1.3c) — `Vec<T>` is move-only by construction,
and so is everything that holds one.** Its last field is
`hidden string[0]:move_only`: a fixed array of no strings, zero bytes, whose
ELEMENT owns — so the compiler marks every `Vec<T>` owning (its D-183), and a
copy of an owner is `NITPICK-TYPE-046`. A copy of a `Vec`, one `Vec` assigned
over another, and a copy of a struct holding one are each refused where they
are written (`tests/probe/probe16f_vec_copy_refused.npk`, `probe16g`,
`probe16h`); against the library before, each compiled and read the
allocator's free poison through its second handle. The author's answer to the
workbench's question 9, 2026-09-25, and `nitpick-regex`'s design (its RX-161).
A transfer is `move(...)`, after which the source is refused
(`NITPICK-MOVE-001`); a `move Vec<T>:v` parameter takes ownership; and an
ordinary parameter is a LOAN, which for an owner is read-only at compiler
`c970483` — every write through it, `@v` included, is `NITPICK-TYPE-085` (the
compiler's DEF-102). So every function that changes a `Vec` takes `Vec<T>->`,
and `vec_at`, the one that only reads, takes a loan (S-18h).
`tests/unit/vec_moves.npk` runs every shape the property still allows. **It
costs nothing measured**: `#size_of<Vec<int64>>()` is 24 as before; no
module's arm bill moves; and the drop the compiler now generates for a `Vec`
walks the empty array and frees nothing, so the block is still `wild`,
`vec_free` is still its release, and a `Vec` never freed still traps
`WildLeak` at `exit 0` — S-18's guarantee is unchanged. `probe18` and
`probe18b` pin the language fact under the marker with no library code, and
redden first if a compiler changes it. **Not closed by it**: the four element
drops of S-18d, which no type here states. *(Closed since cycle 0.2.0b by the
type: `Vec<T: Copy>`, S-18d's amendment, TM-214. The marker is unchanged — a
`Vec` of `Copy` elements is still an owner, by its fourth field.)*

**Rule S-18h (TM-194, cycle 0.1.3c; restated for `Copy` by TM-211, cycle
0.2.0a) — the one verb that hands an element back
by value asks for a `T` that owns nothing, and the language decides which
types those are.** *Since cycle 0.2.0a (TM-211):* `vec_at<T: Copy>` hands back
a copy of the element under the prelude's marker `Copy` (the compiler's D-327),
which a type that owns anything cannot claim — `impl:string:Copy = { };` is
`NITPICK-TYPE-087` (`tests/probe/probe19_pod_owner_refused.npk`), and a derive
for a struct holding an owner is `NITPICK-DERIVE-006` — so `vec_at` at an owning
`T` is `NITPICK-TYPE-017` at the call (`generic_owning_copy/case5`). A consumer's
type that owns nothing claims it in one line, `impl:X:Copy = { };`
(`tests/unit/vec_at_pod.npk`); the scalars' impls are the prelude's, and this
library re-exports nothing for it. The guard is S-17c's slice, unchanged, and
the hole below is closed: an impl's `move` on a lent parameter is
`NITPICK-TYPE-014` since the compiler's DEF-116, and `Copy` has no method.
*Since cycle 0.2.0b (TM-214):* the bound is the type's and every verb's, not
`vec_at`'s alone — `struct:Vec<T: Copy>` (S-18d's amendment) — so at an owning
`T` the refusal comes first where the `Vec` is written, and `case5` names six
sites, its two `vec_at` calls among them.
*What the rule read until then, kept as its record:* `vec_at<T: Pod>` reads
through `Pod`'s `pod_copy`, a `never fails` method whose `self` is LENT. For an owning type the body the
trait admits, `pass self`, is `NITPICK-TYPE-047` — a lent owner cannot be
passed on — so no owning type implements it as declared
(`tests/probe/probe19_pod_owner_refused.npk`), and `vec_at` at an owning `T`
is `NITPICK-TYPE-017` at the call (`generic_owning_copy/case5`, which until
this rule measured the read REMOVING the element). A type that owns nothing
implements `Pod` in one line where it is declared: the nine scalar impls —
the integers to 64 bits and `bool` — are in `src/core/vec.npk`, and the
umbrella re-exports the trait, so a consumer's struct of integers or a payload
enum does too (`tests/unit/vec_at_pod.npk`). The guard is S-17c's slice,
unchanged. **The rule's one hole is the compiler's**: an impl that declares
its `self` `move` where the trait lends it is accepted at compiler `c970483`
— the compiler's DEF-116, fixed at no pin of ours — and through `vec_at` it
hands back a second owner of the element: a double free, 95, measured. No
impl in this library does it, and none may; `TYPE-047`'s own message
suggests that `move`, and it is the one suggestion here not to take. **And the
trait is interim** (TM-198): the compiler's D-327, ratified on 2026-09-26 and in
no pin of ours, makes `Copy` a prelude marker trait over every copyable scalar,
derivable for a struct of copyables; at the re-pin that carries it, `Pod` is
replaced by `Copy` — its block in `src/core/vec.npk`, one bound, one call, one
umbrella line and three test impls — and this rule is restated for it.

**Rule S-19.** The generated zone tables are `fixed` module state — read-only
memory, no initialisation at startup, nothing to leak, and nothing to race.

**Rule S-19b (TM-177, cycle 0.1.3b) — no `fixed` table holds an owning value:
not as its element, and not as a field of its element at any depth. The
reason is measured, and it is not that the language forbids one.** Measured
at every pin this repository has kept, `0dfddac` to `c3bdae2`
(`tests/probe/probe17*`, `tests/probe/defect/fixed_move_out/TRANSCRIPT.txt`):

| What a program does with an owning value in `fixed` storage | Verdict |
|---|---|
| declares it — `fixed string[2]`, `fixed Row[2]` whose `Row` holds a `string`, `fixed string` | compiles and runs (`probe17`) |
| reads a scalar field of a row; lends the value to a by-value parameter; `.clone()` | runs, both legs, and a second read sees the value (`probe17`) |
| copies a row or an element out by value — **the read S-17's accessor pair does** | **refused `NITPICK-TYPE-046`** (`probe17b`, `probe17c`) |
| moves it out — `move(NAMES[i])`, or a plain `pass NAMES[i]` | **compiles, and faults**: at -O0 the IR stores the vacancy into an LLVM `constant` global (SIGSEGV; `MachineFault`, 107, at `c3bdae2`), under `opt -O2` the store is deleted and the moved string's drop frees read-only bytes (`Unreachable`, 95); a `fixed` scalar moved out stops at 95 on both legs. **A compiler defect** — O-N20, the compiler's DEF-99, whose fix refuses the move as `NITPICK-TYPE-084` (its 1.6.0 step 3f, at no pin of ours yet) |

So a table whose rows own can be read neither by value nor by move, and the
zone tables hold OFFSETS into a name pool (`ZONE_MODEL.md` Z-7) — which was
the design already, and is now the rule for the reason that holds.
`check_no_owning_fields` enforces it over `src/`: since cycle 0.1.3b it sees an
owning ELEMENT and an owner at any depth, which it could not before. **A
`fixed` scalar of an owning type** — `ZONE_MODEL.md` Z-4's `TZDB_VERSION` — is
not a table and is outside the check; its hazard is the same defect, and
O-X10 holds it.

*(Amended at cycle 0.1.4c, TM-189 and TM-191.)* **At compiler `c970483` the
table's last row is refused**: a move out of `fixed` storage, or a plain
`pass` of it, is `NITPICK-TYPE-084` where it is written — the compiler's
DEF-99, O-N20 landed — in the declaring module and in one that imports a
`pub fixed` binding, measured (`meta/roadmap/done/0.1/0.1.4c.md` §1.4). The copy is
still `NITPICK-TYPE-046`, so a table whose rows own can still be read neither
by value nor by move — now because the compiler refuses both — and the rule
stands on that. Every read in the second row, a scalar field, a lend and
`.clone()`, is unchanged at `c970483`. **The `fixed` scalar's hazard is gone
with it**: Z-4's binding is read by lending or by `.clone()`, and O-X10 is
settled (TM-191).

*(§1's row read, until cycle 0.1.3b: "No binding-to-binding copies of a
`string`. **Every value in a table has no owning field.** §5." — and
`check_no_owning_fields`' own comment gave the reason as "an owning field is
one the language will not let a table hold", which was false at every kept
pin. Found when the workbench's `PLAYBOOK.md` §2 row that reason came from was
measured false on 2026-09-25, and re-measured here.)*

**Rule S-20.** `ntime` opens **no descriptor** except in `host_system_zone()`,
which reads `/etc/localtime`'s *link target*, closes what it opened before
returning, and holds nothing across a call.

**Rule S-21.** `ntime` spawns no processes, installs no signal handler, starts
no thread, and blocks on nothing.

**Rule S-22 (TM-109, amended by TM-110) — a view is a parameter, never a return
value; and this rule is a BELT, deliberately stricter than the language.** §1's
borrow row promises this rule here, and here it is, in both halves.

**The rule.** No function in `src/` returns a `uint8[]`, a `cstring`, or a
struct containing one. A parser takes a `uint8[]` and returns a value and an
offset — which is what `FORMAT_MODEL.md` already specifies, so the rule costs
this library nothing. `check_no_view_returns` on cycle 0.0.3's harness list is
what makes it enforced rather than remembered.

*(Amended at cycle 0.1.5's second half, TM-204 — the cycle audit's C3.)* **Both
sentences were false of this library from cycle 0.0.4.** `pub func:bytes_view
= uint8[] (Bytes->:b)` returns a view of a `Bytes`' body and the umbrella
re-exports it; and `check_no_view_returns` was never built — it is on no list,
which cycle 0.0.0's own record said (*"It is not on any list"*) while this
rule went on saying otherwise. **The rule is now: no function in `src/`
returns a `uint8[]`, a `cstring` or a struct containing one, EXCEPT a
container's own accessor over the container's own storage, reached through a
pointer parameter, named here beside the rule that governs its lifetime.** One
is named — **`bytes_view`**, whose view roots at a pointer-shaped binding, the
last row of the table below and legal in the language, and whose hazard is
not escape but growth: S-18e is its rule. Measured at that close, `src/`'s ten
files hold 40 `func` declarations, one declaring a view as its result —
`bytes_view` — and no struct holding one. **`check_no_view_returns` is cycle
0.2.3's**, built after `check_check_registry` (TM-201: the subcycle that adds a
check builds the registry check first), live, with a planted return red and
the named exemption re-derived — before cycle 0.4, whose parsers are the first
code that could want another view back. Until it is built, this sentence and
that census are the rule's whole enforcement.

*(Cycle 0.2.3a, TM-228: **built, and live.** What it reads as a view: a slice
of any element — the rule's `uint8[]` is one, and an `int64[]` returned out
of its owner's frame is the same hazard — a `cstring`, and a type that holds
one: a struct's field at any depth, a fixed array's element, a type argument
(`Vec<uint8[]>` — cycle 0.2.0b's question: a `Vec` of slice-holding structs
hands its caller views). A type parameter is no view at its declaration, and
a pointer is none: the rule is about slices. `bytes_view`'s exemption is
re-derived from its reason on every run — declared in `src/core/bytes.npk`,
returning a view, through a pointer to `Bytes`, which that file declares, and
named here — so the day any part of it is false, the run is red. At its first
run, `src/` declared 46 functions and one returned a view: `bytes_view`.)*

*(Cycle 0.2.4a, TM-239 — the cycle audit's C4: and an optional of one.
`uint8[]?` — "the rest, or none", the result a parser wants first — hands its
caller a view whenever it is not `NIL`, compiles at the pin in a consumer, and
passed the check, as `cstring?` did; the check reads a `T?` as its `T` now.)*

**Why it was written as a belt, and why it stays one.** O-N9 measured that
D-004's escape rule was **unenforced for slice views**: `string_bytes` on a
local `string` returned a `uint8[]` out of its owning frame at exit 0, and
reading it read freed memory, while the identical program with an `@`-borrow
was refused `NITPICK-BORROW-001`.

**O-N9 IS NOW DISCHARGED** (TM-110, 2026-09-04, measured against pin
`94874ce`): a view of a local returned is refused `NITPICK-BORROW-001`,
exactly as asked. The belt stays anyway, because what the language enforces is
**narrower** than what this rule forbids — see the last two rows below.

**It is stricter than the constraint, and this is the table to plan `src/fmt/`
against.** Every row was produced by compiling a file at pin `94874ce`; none
is predicted. The evidence column names it.

| Shape, returned out of its frame | Measured at `94874ce` | Evidence |
|---|---|---|
| a view of a **local** — `string_bytes(local)` | **refused** `NITPICK-BORROW-001` | `defect/view_escape/case3`–`case5` |
| a view of a **temporary** — `string_bytes(string_concat(a,b))` | **refused** `NITPICK-BORROW-012` | `probe10b` |
| a view of a **`move` parameter** | **refused** `NITPICK-BORROW-001` | `probe10c` |
| a view rooted at a plain **parameter** | **legal** | `probe10` §2, §3 |
| a view rooted at a **pointer-shaped binding** — a `wild` block, a `cstring`'s `.ptr`, a slice | **legal** | `probe10` §1, `probe09b` |

*(Re-measured at compiler `5fbaf4a`, cycle 0.2.0a — TM-208.)* A `cstring` that
OWNS — `to_cstring`'s answer, moved into a local — is no longer a pointer-shaped
root: a view of its `.ptr`, returned, is `NITPICK-BORROW-001` there, where at
`c970483` it compiled (its buffer never freed). An `environ()` element owns
nothing and is read in place, and a view of `env[j].ptr` returned from a
function taking `env` is legal — `probe09b`, whose root is now the parameter's
element and no longer a local copy, which a move-only `cstring` refuses.

**The rule keys on the ROOT'S SHAPE, not on parameterhood** — which is the
correction TM-110 makes to TM-109, and it took two probes to establish, because
one cannot separate the two readings. A view whose place roots at a
pointer-shaped binding aliases the **pointee**, which lives wherever the
pointer's provenance says; `view_is_frame_borrow`
(`src/frontend/analysis/escape.npk`) is the discriminator. A **`move`**
parameter is *not* a parameter for this purpose: it is consumed at the call and
dropped at the callee's frame exit.

**DEF-3 DOES add a diagnostic code, and this document said otherwise until
2026-09-04.** `NITPICK-BORROW-012` (`BORROW_VIEW_OF_TEMPORARY`) exists at this
pin and `probe10b` fires it. The earlier claim came from DEF-3's *plan*, which
its own step 2 overtook: every other refusal is shaped like "as if `@` had been
written at that argument" and so is `BORROW-001`, but `@` of a temporary cannot
be spelled, so no existing code's text was true of it. `check_codes_tested`
therefore **does** gain a code.

**The temporary row is doubly wrong today, and one edit fixes both halves.**
The inner `string_concat` result is an unbound temporary passed as an argument,
and nothing frees it — the compiler's D-183 debt, proposed as its D-246 and
scheduled in the same 1.5.1b. Binding the intermediate gives the view a named
owner *and* gives the temporary a place, so:

```nitpick
string:joined = string_concat(a, b);   // bind it: the view has an owner,
uint8[]:v = string_bytes(joined);      // and the temporary is no longer one
```

**So: keep the rule, and do not mistake it for the constraint.** A later cycle
that finds `src/fmt/` wanting to return a view of one of its own parameters is
meeting the belt, not the language, and the question to ask is whether to
loosen S-22 — a decision — rather than whether the compiler will allow it.

---

## 6. What an application owes

Stated once, here, and repeated in the public documentation:

1. Carry the `failsafe` arms your imports require (S-6 generates the list — one
   arm for calendar-only, three for everything).
2. Decide, explicitly, which clock you mean. A timeout is an `Instant`
   difference; a timestamp on a record is a `Timestamp`. `ntime` will not let
   you mix them, but it cannot choose for you.
3. If you want local time, ask for the system zone and handle the case where
   there is not one.
4. Know that the compiled tzdb has a version, and that a long-running program
   holds whatever release it was built with (`COMPAT.md` §3).

---

## 7. Open items

*(None. Every item this document raised is settled in `../DECISIONS.md`.)*
