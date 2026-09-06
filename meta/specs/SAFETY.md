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
| `failsafe`'s `pick` must **name** every error that can reach it | REACH-002 | Every public `error:` we declare is an arm every consuming program owes. §2. |
| Reachability is **import-scoped** | 1.4.8's `nsys` note | Module decomposition decides what a consumer's `failsafe` owes. §2. |
| Plain integer `+ - *` **traps** on overflow | D-210 | Every arithmetic path states its range and checks it **before** the trap fires. §4. |
| `/` and `%` by zero trap; signed `MIN / -1` traps | D-007, D-142 | The calendar algorithms divide constantly; every divisor is a nonzero literal or a proven value. §4. |
| Indexing **a type that carries a length** is bounds-checked and traps | D-070 | a slice `T[]`, a fixed array `T[N]` and a `simd<T, N>` lane trap; **a bare pointer does not** — and `Vec<T>.items` and `Bytes`' `buffer` body are both reached as one. §4, S-17b. |
| Owning values are **move-only** | TYPE-046 | No binding-to-binding copies of a `string`. **Every value in a table has no owning field.** §5. |
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
};
```

The same pattern carries `ParseError` (the byte offset, and what was expected)
and `ZoneFault` (`Unknown`, `Ambiguous`, `Nonexistent`). This is the playbook's
rule and it is what keeps the budget at three without losing information.

**Rule S-4 — module decomposition is part of the budget**, because REACH is
import-scoped:

| Module | Declares | Identity arms a consumer importing only this owes | TOTAL arms, MEASURED at pin `aaffb87` |
|---|---|---|---|
| `ntime/core.npk` | — | nothing | **4** — the floor; `core` is not yet reachable as its own public module, and the umbrella's bill is the row below the table |
| `ntime/cal.npk` | `ETimeValue` | one arm | **9** — measured 2026-09-06 |
| `ntime/span.npk` | — (raises `cal`'s) | one arm | placeholder; **4** today, and the number is meaningless until cycle 0.2 gives the module a body |
| `ntime/zone.npk` | `ETimeZone` | two arms | placeholder; **4** today (cycle 0.3) |
| `ntime/fmt.npk` | `ETimeParse` | three arms | placeholder; **4** today (cycle 0.4) |
| `ntime/host.npk` | — (forwards errnos) | one arm | placeholder; **4** today |

**A program that only wants calendar arithmetic owes one IDENTITY arm.** That is
the decomposition working, and it is why `cal` does not import `zone`.

**AND IT OWES NINE ARMS ALTOGETHER — the totals column is now real for the one
module that has a body, and it is MEASURED rather than predicted**, which is
what S-4b promised cycle 0.1 would deliver. Read out of `NITPICK-REACH-003`'s
own list by compiling a consumer that imports only `src/cal/cal.npk` and
declares no handler:

```
$NPKC arm_cal.npk -o arm_cal.ll     →  exit 1, no .ll written
NITPICK-REACH-003 … 9 identities: cal.ETimeValue, Unreachable, HeapOom,
  HeapBadRequest, WildLeak, DivByZero, DivOverflow, IntOverflow, OutOfBounds
```

`check_failsafe_arms` runs that generation on every full invocation and diffs
the list against the set computed from source **in both directions**, so this
row cannot go stale in silence.

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

**Rule S-4b (TM-107) — the identity column is not the whole bill, and this table
is not yet the bill.** Measured at cycle 0.0.0 by
`tests/probe/probe11c_import_arm_cost.npk`: the reachable set is computed over
**every module in the program graph but the prelude**, and the *system* arms are
armed by the machinery any module's text contains — `DivByZero` and
`DivOverflow` by `/` or `%`, `IntOverflow` by plain-integer `+ - *`,
`OutOfBounds` by an index — on top of an unconditional floor of `Unreachable`,
`HeapOom`, `HeapBadRequest` and `WildLeak`.

A miniature of `cal` that declares **no error at all** cost an importing program
whose own text contains no arithmetic **four extra arms**, and the twin that
imports nothing compiles with the four floor arms alone
(`tests/probe/probe11d_floor_only.npk`). `cal` divides by 4, 100, 400, 146097,
86400 and 1000000000 (S-16), indexes the month and zone tables (S-17), and adds,
so **a consumer that imports `ntime/cal.npk` owes `DivByZero`, `DivOverflow`,
`IntOverflow` and `OutOfBounds` however pure its own code is** — arms a correct
`ntime` can never enter, since every divisor is a nonzero literal and every index
is checked, and arms it must write anyway.

That is the compiler's deliberate direction rather than a defect
(`reach.npk`: *"Over-approximation is the safe direction"*), so what changes is
this document, not the library. **The totals column is generated at cycle 0.1**,
when `src/cal/` exists and the numbers can be measured instead of predicted;
nothing is guessed into it here.

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
`0dfddac` on the three specimens cycle 0.0.0 left behind, and the arithmetic is
written out because a number embedded in prose travels with the prose:

| Module | Owes | = floor + | Which constraint it pins |
|---|---|---|---|
| *(nothing imported)* | **4** | — | the floor: `Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak` |
| `probe11_silent_lib` | **4** | + 0 | **1** — it declares `pub error:EProbeSilent` and never raises it, and the identity is **absent** from the list |
| `probe11_arms_lib` | **5** | + 1 | a `fail` SITE puts it in, module-qualified: `probe11_arms_lib.EProbeZone` |
| `probe11_calc_lib` | **8** | + 4 | **2** — it declares no error at all; `DivByZero`, `DivOverflow` from its `/` and `%`, `IntOverflow` from its `+`, `OutOfBounds` from its one index |

8 − 4 = 4 is S-4b's measured *"four extra arms"*, and none of the three
functions is ever called by the generated program — S-4c, the arm is owed by the
**import**.

**Three constraints on that generator, all measured at cycle 0.0.0 (TM-107) and
each of which the obvious implementation gets wrong:**

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
- `host_clock_resolution(which)` — `clock_getres`
- `host_system_zone()` — reads `$TZ`, then `/etc/localtime`, and **says which
  it used**

and nothing else. Nothing elsewhere in the library calls any of them.

**Rule S-9 — the clock is a parameter, never an ambient.** A function that
needs "now" takes a `Timestamp` or an `Instant`. `ntime` provides `host_now_*`
so a caller can get one; the library itself never asks. This is the same rule
the sibling TUI library applies to its decoder's clock, and it is what makes
every behaviour in this library reproducible in a test to the nanosecond.

**Rule S-10 — a whole-tree check enforces §7.** `check_purity` greps `src/`
outside `src/host/` for `sys(`, `mono_now`, `environ`, `read_file`, `open` and
`write`, and fails on any hit. The rule is not a convention if nothing checks
it, and this is the check.

**Rule S-10b (TM-126) — it is a SOURCE-LEVEL check, it is LIVE, and it has been
SEEN TO FAIL.** Three separate claims, and each was missing:

- **Source-level, and nothing else can stand in for it.** The build's
  undefined-symbol scan cannot answer this question at all: `npk_sys6` is the
  runtime's own syscall trampoline and is in its allowlist by construction, so a
  module that issues a raw syscall has an *identical* undefined set to one that
  does not — measured in `nitpick-regex` as RX-120 (29 symbols each way, the
  diff empty) and reproduced here (`BUILD.md` B-2c, TM-118). **A green symbol
  scan cited as a purity result is the failure mode.**
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
  repository on its own documentation — and the first draft did.

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

**Rule S-13 (TM-014) — the supported range is `year −9999 … +9999`**, proleptic
Gregorian, astronomical year numbering (year 0 exists and is 1 BCE).
`CALENDAR.md` §2 gives the reasoning and the exact bounds in every unit.

**Rule S-14 (TM-011) — `Timestamp` is `{ int64:secs; uint32:nanos }` and the
field order is semantic.** `#[derive(Ord)]` compares in declaration order (TRAITS_REFERENCE
§2.5), so seconds-then-nanoseconds is exactly the comparison wanted, and
reordering the fields would silently change what `Ord` means. A rule rather
than a comment because it looks like a style question and is not.

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

**Rule S-16.** Nothing divides by a value it has not proven nonzero on the same
path. The calendar algorithms divide by literals (4, 100, 400, 146097, 86400,
1000000000) and nothing else.

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

**THE EXCEPTION IS `push`, AND IT IS PART OF THE RULE RATHER THAN A DEPARTURE
FROM IT (F2, TM-143).** This code block read *"over `count`, never over `cap`"*
until cycle 0.0.6, and three sites in the library lay the slice over `cap` —
`vec_push` (`vec.npk:180`) and `bytes_push`/`bytes_extend`
(`bytes.npk:97,109`). Each argues the exception in a source comment, and
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

> **And the arm bill cannot tell the two spellings apart, which is why this
> went unnoticed.** `NITPICK-REACH-003` bills a consumer of the guarded
> accessor six identities — `Unreachable`, `HeapOom`, `HeapBadRequest`,
> `WildLeak`, `IntOverflow`, `OutOfBounds` — and bills the **bare-pointer**
> accessor **the same six**. So the reachability analysis arms `OutOfBounds`
> for an index that emits no guard at all: every consumer of an unguarded `Vec`
> is compelled to write an arm for a trap that *cannot fire*, while the read it
> is meant to protect returns a wrong value in silence. Adding the guard makes
> that arm honest; it does not add it.

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
clean down to a 3 MiB cap.

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

**Rule S-18d (TM-136) — THE RESTRICTION IS NOT ENFORCEABLE BY THE COMPILER,
AND THAT IS WHY IT STAYS.** *(Placed after S-18c since cycle 0.0.6. It was
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
— `vec_pop<T>` at 0.0.4 was the first (S-18d) — and both were invisible for the
same reason: **every gate this repository owns is a leak gate.** D-151's exit-0
trap counts `wild` allocations and cannot see a managed body (TM-106);
`check_raw_index` is about indexing; the undefined-symbol scan is blind to it;
`check_purity` answers a different question. A leak is found by a gate. **A
use-after-free is found by a WRONG ANSWER, so it is found by a test that reads,
and by nothing else.** `tests/unit/bytes_view_lifetime.npk` is that test, with
its control: a view held across forty NON-growing pushes reads back correctly,
and the same program at a capacity that forces growth does not.

**The obligation this puts on `src/fmt/` at cycle 0.3**, which is where views
into a `Bytes` will actually be held:

- a function that returns or stores a view states the invalidation rule at the
  site, in the words above;
- inside the library, **a `#wild_slice` binding is made AFTER the `*_reserve`
  call in the same body, never before**. Both `src/core/` files obey it today —
  `vec_push` and `bytes_push` call reserve first and then lay the slice — and
  it is a lexical property a check can hold them to when there is a second file
  that needs one;
- `Vec<T>` does **not** have this shape and the reason is worth writing down
  rather than rediscovering: `vec_reserve` reallocates identically, but **no
  function in `vec.npk` returns a slice**, so there is no view for a caller to
  hold. `vec_at<T>` returns by value.

**Rule S-19.** The generated zone tables are `fixed` module state — read-only
memory, no initialisation at startup, nothing to leak, and nothing to race.

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
