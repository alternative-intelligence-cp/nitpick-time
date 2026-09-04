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
| Array, slice and buffer indexing is bounds-checked and traps | D-070 | A zone-table index out of range is a *crash*, not a wrong offset. §4. |
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
`failsafe` is accepted by `npkc` at exit 0 and refused only by `llc`
(`../OPEN_QUESTIONS.md` O-N11, provisional), so a conformance test that compiles
to `.ll` and reads the exit code would pass a program with no handler at all.
It runs the full four steps, or asserts `grep -c '^define i32 @npk_failsafe'` is
1. This is a constraint on cycle 0.0.3's harness and is recorded in its
checklist.

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
0.0.0, 125 MiB retained over 2 000 000 elements, and `HeapOom` under a 64 MiB
address-space cap while the corrected form finishes clean. Each element is moved
into a scope that ends:

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
