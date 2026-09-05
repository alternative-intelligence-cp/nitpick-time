# A program with `main` and no `failsafe` compiles at exit 0 — **FIXED**

> ## STATUS, 2026-09-05, pin `0dfddac`
>
> **THE DEFECT DESCRIBED BELOW NO LONGER EXISTS.** `npkc` refuses both cases at
> `main`, `NITPICK-REACH-003`, **exit 1, and writes no `.ll` at all** — the
> refusal moved one step earlier, from `llc` into the frontend. This directory
> is now a **regression suite**: `case1` and `case3` assert that the refusal
> happens, `case2` that it does not misfire.
>
> | File | `npkc` | Identities the diagnostic lists | Header |
> |---|---|---:|---|
> | `case1_no_failsafe.npk` | **exit 1**, no `.ll` | **4** — `Unreachable`, `HeapOom`, `HeapBadRequest`, `WildLeak` | `expect-error: NITPICK-REACH-003` at `62:1` |
> | `case2_failsafe_present.npk` | exit 0, `.ll` written, links, **runs exit 0** | — | `expect-exit: 0` |
> | `case3_arm_contract_evaded.npk` | **exit 1**, no `.ll` | **6** — the four, plus `probe11_arms_lib.EProbeZone` and `IntOverflow` | `expect-error: NITPICK-REACH-003` at `58:1` |
>
> **Four, not six, for `case1`** (TM-112): it has no import, no arithmetic and
> no allocation, so its bill is `SAFETY.md` S-4b's unconditional floor. A board
> carried six; the six is real and belongs to `case3`.
>
> **These three files had no `expect-` header at all until 2026-09-05** — not a
> wrong one, none — so they sat outside the sweep that would have caught their
> expectations going stale on the very day the defect was fixed. That is
> **TM-115**, and the sweep now states its denominator.
>
> `TRANSCRIPT.txt` holds three recordings, newest first: **Part A** at
> `0dfddac`, **Part A0** at `94874ce`, **Part B** the 2026-09-03 original,
> verbatim. Every diagnostic is character-identical across all three except for
> the line numbers, which moved because the headers were added.
>
> **Everything below this box is the report as it was written on 2026-09-03**,
> when the defect was live. It is kept because it is the evidence O-N11 was
> real and the argument that got it accepted, and neither is re-creatable at
> this pin. Read it in the past tense.

**O-N11** — allocated by the workbench registry, and **accepted by the compiler
as its DEF-5**, committed at cycle 1.5.1b step 1b.

Found by cycle 0.0.0's probe 11 on 2026-09-03, against the pinned toolchain
(compiler commit `950bb1d`, LLVM 20.1.2). Every command and every exit code is
in [`TRANSCRIPT.txt`](TRANSCRIPT.txt); nothing below is a summary of something
that is not also quoted there.

---

## What happened, as written on 2026-09-03

`npkc` does not require a root file that declares `main` to declare
`failsafe`. It accepts one at **exit 0** and emits IR whose trap paths call
`@npk_failsafe`, which nothing defines. `llc` refuses that IR:

```
$ "$NPKC" tests/probe/defect/missing_failsafe/case1_no_failsafe.npk -o /tmp/c1.ll
exit=0
$ llc -O0 -filetype=obj -relocation-model=static /tmp/c1.ll -o /tmp/c1.o
llc: error: /tmp/c1.ll:4036:19: error: use of undefined value '@npk_failsafe'
  %t75 = call i32 @npk_failsafe(i32 -4102)
exit=1
```

The source file is four lines long. It has no import, no arithmetic and no
allocation.

## What the rule is

The compiler's own `meta/specs/DECISIONS.md`, **D-013 — "Exactly one `failsafe`
per program, supplied by the executable"**:

> **Libraries do not define `failsafe`.** It is required only for executables
> and must be provided by the end user. There is never more than one in a
> program.

So the rule exists, it is settled, and `npkc` does not enforce it.

## What the defect is NOT

**"`npkc` emits calls to an undefined `@npk_failsafe`" is not the defect**, and
saying so would send the compiler session after the wrong thing. An ordinary
library module does the same: `tests/probe/support/probe11_arms_lib.npk` has
neither `main` nor `failsafe`, compiles at exit 0, and emits the identical seven
calls to an undefined `@npk_failsafe`. That is harmless, because it emits no
`@main` either and nobody links a library module on its own. The transcript runs
that control and prints all four counts.

**The defect is a missing check**, and `npkc` already holds both halves of it:

- it knows `main` is there — it emits `define i32 @main` for `case1` and does
  not for the library module;
- it knows `failsafe` is absent — `reach_settle` in
  `src/frontend/analysis/reach.npk` tests `if (x.failsafe_decl == 0i32)
  { pass NIL; }` and returns early on precisely this case.

It never joins them into a diagnostic.

## Why it matters here rather than being untidy

Because the early return in `reach_settle` is the **whole** REACH-002 contract,
and deleting the `failsafe` discharges it in silence.

`case3_arm_contract_evaded.npk` imports a module that declares and raises
`EProbeZone`, calls the function that raises it, and has no `failsafe`. It
compiles at exit 0 with no diagnostic. The same program *with* a `failsafe` that
merely omits that one arm is
`tests/probe/probe11b_arm_omitted_refused.npk`, and it is refused:

```
NITPICK-REACH-002 …:60:5: `failsafe` does not name `probe11_arms_lib.EProbeZone`,
which can reach it (D-179): add the arm — `(*)` counts for nothing here, so a new
failure mode is always acknowledged before the program compiles again
```

That refusal is the mechanism behind `TM-017`'s error budget, `SAFETY.md` §2's
per-import arm table, `TM-013`'s rule that a fourth identity is a MAJOR version,
and `COMPAT.md` §6. Probe 11b proves the mechanism is real **for a program that
has a `failsafe`**. This directory records that it asks nothing of a program
that has none.

## What it blocks, what it inconveniences, and what it does not touch

Stated separately and plainly, because "blocking" and "annoying" want different
places in a schedule (WORKSTREAMS W-27).

**It BLOCKS nothing in this repository.** Every program `ntime` ships or tests
has a `failsafe`; a missing one is caught by `llc` in the very next step of the
same recipe, loudly, deterministically and for free. No cycle waits on this and
no design changes because of it. It is *not* in the class of O-N4 (which stops
0.0.5 and 0.5) or O-N9 (which the author ruled blocking for `src/fmt/`).

**It INCONVENIENCES cycle 0.0.3's harness, and the inconvenience arrives before
the harness is written, which is the cheap time for it.** Two consequences:

1. **`npkc` exit 0 does not mean "this program is well-formed".** A harness
   stage that compiles to `.ll` and stops — the obvious shape for a `parse` or
   `accept` stage — passes `case1`. `TESTING.md`'s `program` stage must run the
   full four steps, or a program-shaped stage must additionally assert
   `grep -c '^define i32 @npk_failsafe'` is 1. The cheap check is the grep.
2. **`selfcheck.py`'s seven cases should gain an eighth**: a program whose
   `failsafe` has been deleted must be caught by the harness. It is exactly the
   library's own "green and wrong" shape — a stage that reports success on a
   program that cannot be linked.

**It does NOT touch the arm contract where a `failsafe` exists.** Probes 11,
11b, 11c, 11d, 11e and 11f all behave exactly as `SAFETY.md` §2 requires, and
nothing in that section is weakened by this. It also does not touch any other
analysis, any code generation, or any measurement this cycle has taken.

## The ask

No language change. `npkc` refuses a root file that declares `main` and no
`failsafe`, with a diagnostic that names D-013 and the file. The information is
already computed; only the diagnostic is missing.

Two things worth having in the same change, offered rather than insisted on:

- the diagnostic could **list the arms the absent `failsafe` would owe**, since
  `reach_settle` has just computed exactly that set at the point where it
  currently returns early. That turns the worst version of this ("I deleted
  `failsafe` and got a symbol error from LLVM") into the best version ("here is
  the handler you owe, and here are its nine arms");
- it is close kin to `OPEN_DECISIONS.md` §4's outstanding item that **D-014's
  compiler-injected `ensures result > 0` on `failsafe` and the non-empty-body
  check "both currently exist nowhere"**. Those check a `failsafe` that is
  present; this checks that one is present at all. One pass over the root's
  declarations answers all three.

## The files

| File | `npkc` **in 2026-09-03** | `llc` **in 2026-09-03** | What it is for |
|---|---|---|---|
| `case1_no_failsafe.npk` | **exit 0** | exit 1 | the defect, minimal — `mod:` and `main`, nothing else |
| `case2_failsafe_present.npk` | exit 0 | exit 0, links, **runs exit 0** | the contrast — `case1` plus a floor `failsafe`, and the only difference between a file that links and one that does not |
| `case3_arm_contract_evaded.npk` | **exit 0** | exit 1 | why it matters — a program that owes `EProbeZone` and is asked for nothing |

**Those are the 2026-09-03 columns and they are history; the box at the top of
this file has the current ones.** The last line of this section used to read
"Deleted when the defect closes" — **and they are not deleted.** P-5: a probe is
never deleted, and a defect reproduction whose defect is fixed is the most
valuable kind of regression case, because it is the one shape nobody would
think to write from scratch.
