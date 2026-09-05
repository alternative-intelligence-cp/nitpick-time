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

| Module | Declares | Identity arms a consumer importing only this owes |
|---|---|---|
| `ntime/core.npk` | — | nothing |
| `ntime/cal.npk` | `ETimeValue` | one arm |
| `ntime/span.npk` | — (raises `cal`'s) | one arm |
| `ntime/zone.npk` | `ETimeZone` | two arms |
| `ntime/fmt.npk` | `ETimeParse` | three arms |
| `ntime/host.npk` | — (forwards errnos) | one arm |

**A program that only wants calendar arithmetic owes one IDENTITY arm.** That is
the decomposition working, and it is why `cal` does not import `zone`.

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
  `i < count`.
- **An unchecked index is a WRONG ANSWER, not a crash**, which inverts the
  failure mode §1 advertises. In a date library that is a wrong offset for one
  zone, or a formatted field taken from an unrelated heap word — silent, and
  reachable from caller-controlled bytes once `src/fmt/` parses.
- **`VERIFICATION.md`'s `Vec<T>` `at`/`set` row** (index `< count`, by contract
  and by Z3) stops being a restatement of a language guarantee and becomes the
  obligation that discharges this rule.

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
0.0.0 and **re-measured unchanged at the 2026-09-04 re-pin**: 125 184 KiB
retained over 2 000 000 elements, and `HeapOom` (exit 92) under a 64 MiB
address-space cap, while the corrected form completes the same two million
iterations in **under 768 KiB** of address space. The committed pair is
`tests/probe/probe06b_element_leak.npk` and `probe06c_element_drop.npk`, which
differ in one line. **Quote the address-space bound and not a peak-RSS figure**:
`/usr/bin/time -f %M` reports `0 KiB` for these static binaries — it does so
for a four-line program too — so the "0 KiB" this rule carried until the re-pin
was a broken gauge rather than a measurement. Each element is moved into a
scope that ends:

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
