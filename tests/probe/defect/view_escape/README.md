# O-N9 — a `uint8[]` view escapes its owning frame, silently

**D-004's escape rule is enforced for `@`-borrows and not for slice views.**
Found by cycle 0.0.0 on 2026-09-03, against the pinned toolchain (compiler
commit `950bb1d`, LLVM 20.1.2). The transcript with every command's exit code
is [`TRANSCRIPT.txt`](TRANSCRIPT.txt); this file says what it means.

Nothing here is a workaround and nothing here is a probe. It is the
reproduction the ecosystem's rule requires: *never work around a compiler
defect — record it, stop, and raise it.*

---

## The contrast, which is the whole report

Six files. Cases 1 and 2 are **controls**: they are the rule working. Cases 3,
4 and 5 are the same programs with a `uint8[]` where the `@`-borrow was.

| # | File | What it returns out of the owning frame | `npkc` | runs |
|---|---|---|---|---|
| 1 | `case1_borrow_returned.npk` | `@x`, a local `int64` | **refused** `NITPICK-BORROW-001` | — |
| 2 | `case2_borrow_in_struct.npk` | `Keeper{ p: @x }` | **refused** `NITPICK-BORROW-001` | — |
| 3 | `case3_view_returned.npk` | `string_bytes(s)`, `s` a local `string` | **exit 0** | exit 0 |
| 4 | `case4_view_in_struct.npk` | `Holder{ view: string_bytes(s) }` | **exit 0** | exit 0 |
| 5 | `case5_read_after_free.npk` | the same, and then **reads it** | **exit 0** | **exit 170** |
| 6 | `case6_view_param_legal.npk` | nothing — the view is a *parameter* | exit 0 | exit 0 |

Cases 2 and 4 are the same program. The only difference is the type of the one
field the returned struct literal carries — `int64->` or `uint8[]` — and both
of them hold an address into the frame that is returning.

The diagnostic cases 1 and 2 get is exemplary, and it names the rule:

```
NITPICK-BORROW-001 …:15:10: a borrow cannot travel up: it is valid only for
the frame it was taken in, and this returns it out of that frame (D-004 rule 2)
```

## Why this is under-enforcement and not a design question

Because the compiler's own specification already says a slice is a borrow.
`TYPE_REFERENCE.md` §9.2.1, on `T[]`:

> **A slice is a second-class borrow** (D-004): it passes down the call stack
> and never up, cannot outlive the storage it views, and cannot cross a thread
> spawn or an `await`.

D-004 rule 2 is *"a borrow may not appear in the value of `pass`, `fail`, or
`return`."* Nothing has to be decided. The rule is written, it is enforced for
one spelling of a borrow and not for another, and the two spellings sit side by
side in this directory.

## What the caller actually reads — 170, and why that number

Case 5 returns the escaped view, dereferences it, and **exits with the byte it
read**, so the observation is a number and not a claim. It is **170** — and
170 is `0xAA`, which is the runtime's own free-poison. `runtime/npkrt.ll`'s
free path stores `i8 -86` into every byte of a freed payload:

```
4388:  store i8 -86, ptr %pp
```

with the reason in a comment beside it (D-183, the compiler's cycle 1.2.3):

> `0xAA` in every freed byte makes the very first stale read produce loud
> deterministic garbage instead: stage 2's one-in-242k-lines corruption becomes
> visible at every site, every run.

So the sequence is not "the bytes may be stale". The block was freed, the
runtime wrote its poison across it, and the caller read the poison back through
a **bounds check that passed** — because a slice is `{ ptr, len }` and only the
pointer died. Four consecutive runs give 170 every time.

That determinism is the runtime's doing, not the language's, and it is worth
being precise about what it buys: it makes the defect *visible* here, and it
would make it visible in a debug build of a real program. It does not make it
safe. The same escape into a block the allocator has since reused reads
whatever now lives there.

## What it would look like in this library

Every parser in `src/fmt/` takes a `uint8[]` (`FORMAT_MODEL.md`). A helper
that returns "the tail after the separator" — the single most natural thing to
write in a scanner — is one `pass` away from case 3. The length is right, so
every bound check passes; the bytes are `0xAA`, which parse as no digit, no
separator and no month name. The failure surfaces as **`ETimeParse` on valid
input**, at a call site that looks correct, and nothing points at the helper.

That is the argument for making it a **harness check** rather than a thing to
remember. `check_no_view_returns` — fail any function in `src/` whose return
type is a slice — is **proposed** for cycle 0.0.3's list and is not on it yet:
it is part of what Q-5 decides, and this dispatch deliberately landed nothing
that depends on that answer.

## What `ntime` does meanwhile — and what it is NOT doing

**The house rule: a view is a parameter, never a return value.** That is
compliance with a documented language rule, not a workaround for a defect, and
the distinction is the one W-11 turns on. Case 6 is the shape the library
writes: the view goes *down* into the scanner, and what comes back is a value
and an offset. A parser has no reason to return a slice of its input, so the
rule costs nothing — which is exactly why it is safe to adopt and would not be
safe to adopt if it cost something.

Contrast O-N4, in the sibling directory: there, no correct code avoids the
cost, so the library stopped rather than reshape itself. Here the correct code
is the code the design already called for.

**And the house rule is CONSERVATIVE, not the constraint — read `SAFETY.md`
S-22 and TM-109 before planning against it.** This was accepted as the
compiler's **DEF-3** (its cycle 1.5.1b step 2, proposed as its D-249), and the
fix distinguishes two shapes the one-sentence rule conflates. A returned view of
a **local** — every case in this directory — is refused; a returned view of a
**temporary**, `string_bytes(string_concat(a, b))`, is refused too and must have
its intermediate bound, which also fixes the separate leak that intermediate has
today; but a returned view whose borrows are all rooted at a **parameter** stays
legal, and is legal today, because a parameter's target lives in the caller or
older. The refusal is `NITPICK-BORROW-001` — the code a returned `@`-borrow
already gets — and DEF-3 adds **no new diagnostic code**. So a later cycle that
finds `src/fmt/` wanting to return a view of its own parameter is meeting this
repository's belt, not the language, and the question is whether to loosen S-22
by decision.

**What is not being done:** no `string_slice` copy is being inserted to dodge
the escape, no API is changing shape, and nothing in `src/` is being arranged
around the defect. If the disposition ever becomes "reshape the library", that
is a different decision and it needs a different reason.

## What is being asked

- `NITPICK-BORROW-001` at cases 3, 4 and 5, exactly as it fires at cases 1
  and 2.

Nothing in the language changes; `TYPE_REFERENCE.md` §9.2.1 already states the
rule this would enforce.

**Where it appears to be lost, offered as a starting point and not as a
diagnosis** — the analysis was read, not instrumented. The escape walk in
`src/frontend/analysis/escape.npk` is a *provenance* walk rooted at the two
expression kinds that produce a borrow, `ExprAddressOfExpr` and
`ExprBorrowExpr`; a call's result is a borrow only under "rule A", which the
file states as *"a call's result is a borrow if an argument was one and the
result can carry a pointer."* In `string_bytes(s)` the argument is an **owning
local**, not a borrow, so no argument is one, rule A does not fire, and the
result is never marked. The type table is not where it is lost:
`type_holds_pointer` answers `true` for `TY_SLICE` as it does for
`TY_POINTER` — but `verdict_borrowy` consults it only *after* the walk has
already said yes (`if (!walked) { pass false; }`), so the type test is a filter
and never a source. The missing rule looks like: **a slice derived from an
owning local is a borrow of that local**, whatever produced it.

Recorded as **O-N9** in
[`../../../../meta/OPEN_QUESTIONS.md`](../../../../meta/OPEN_QUESTIONS.md);
its disposition for this library is **Q-5**.

## For cycle 0.0.2

None of these six files is a `program`-stage entry. Two must not compile, three
compile and are wrong on purpose, and one is a control. They need an exclusion
with the reason next to it, exactly as `probe04_big_fixed_table.npk` does.
