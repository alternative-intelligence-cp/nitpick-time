# `generic_owning_copy` — TYPE-046 was not enforced inside a generic body (O-N19); at compiler `c3bdae2` it is

## Landed — cycle 0.1.0b, compiler `c3bdae2`

**The check this directory was written to demand is in the compiler.** Its
D-264 makes a bare type parameter MOVE-ONLY in the body that names it: a
generic body is checked ONCE for every type it is instantiated at, some of
which own storage, so the only sound answer for the type it does not know is
"owns". The bare copy below is now refused where it is written, at every
instantiation — the scalar one too. **Every file here is now asserted by an
`expect-` marker** and none is in `harness/run.py`'s `EXPECT_EXEMPT`; the
verdicts at the pin that raised it are each file's control (TM-154):

| File | at `aaffb87` — the control | at `c3bdae2` — the marker |
|---|---|---|
| `case1_generic_bare_copy.npk` | `npkc` 0, `llc` 0, `ld` 0, **run 0** — the defect | **refused `NITPICK-TYPE-046`** |
| `case2_concrete_bare_copy.npk` | refused `NITPICK-TYPE-046` | refused `NITPICK-TYPE-046` — unchanged |
| `case3_generic_scalar.npk` | run 0 — the scalar control | **refused `NITPICK-TYPE-046`** — D-264 checks the body, not the instantiation |
| `case4_use_after_free.npk` | **run 170** — the poison | **refused `NITPICK-TYPE-046`** |
| `case5_vec_at_destructive.npk` | run 11 | run 11 — unchanged: `pass` of a place still moves |

The `aaffb87` column was re-run at cycle 0.1.0b against the kept toolchain, on
the text as it stood before that subcycle (`case4`'s adopted loop carries a
`decreases` clause, which `aaffb87` does not parse); the `c3bdae2` column is
what the harness asserts on every full run. `TRANSCRIPT.txt`'s last section
has both, command by command. **Everything below this section is the record as
cycle 0.0.5 wrote it, in the tense that was true then.**

## The record, as raised

**A GENERIC function may read an owning element into a local WITHOUT `move`,
producing two owners of one heap body. The identical statement with the type
written out is refused.** `npkc` exits **0**, `llc` exits **0**, the program
links and runs, and reading through the second owner after the first has
dropped returns the allocator's `0xAA` poison.

Raised by cycle **0.0.5**, 2026-09-05, at pin `aaffb87` — and **reproduced
unchanged at `0dfddac`, `950bb1d` and `94874ce`**, so it is not a regression at
the new pin. This directory carried no open-question id when it was written:
`O-N` is the workbench registry's namespace and a worker cannot see what it has
issued (`../../../../../PLAYBOOK.md`). The orchestrator numbered it **O-N19**.

## The pair that is the whole finding

```nitpick
func:peek<T> = T(Vec<T>->:v, int64:i) never fails {
    T[]:s = #wild_slice<T>(v.items, v.count);
    T:answer = s[i];                       // case1: ACCEPTED at T = string
    pass answer;
};

func:peek_string = string(Vec<string>->:v, int64:i) never fails {
    string[]:s = #wild_slice<string>(v.items, v.count);
    string:answer = s[i];                  // case2: REFUSED, NITPICK-TYPE-046
    pass answer;
};
```

`case2`'s diagnostic says what `case1` does and is not told: *"`string` owns
storage that is released at scope exit, so it is move-only (D-183): copying it
here would leave two owners and one double free."*

## The files, at `aaffb87`

| File | What it is | `npkc` | `llc` | `ld` | run |
|---|---|---|---|---|---|
| `case1_generic_bare_copy.npk` | **the defect** — generic, owning `T`, bare read | 0 | 0 | 0 | **0** |
| `case2_concrete_bare_copy.npk` | control: the same statement, `string` spelled out | **1** | — | — | — |
| `case3_generic_scalar.npk` | control: the same generic function at `T = int64` | 0 | 0 | 0 | 0 |
| `case4_use_after_free.npk` | **the consequence** — first owner dropped, second read | 0 | 0 | 0 | **170** |
| `case5_vec_at_destructive.npk` | not a defect: `pass s[i]` moves implicitly, so the library's `vec_at<T>` **removes** the element | 0 | 0 | 0 | **11** |

`case3` places the fault at **generic × owning** and not at generic alone, the
same three-control shape `../generic_element_move/` used for O-N17.
`TRANSCRIPT.txt` has every command with its exit status beside the artefact it
produced, the emitted IR at the fault, and the same pair run at all four pins.

## Where the fault is, more precisely than the error text says

`require_move_if_owning`, in the compiler's `src/frontend/type_expr.npk`,
returns early unless **`type_drops`** is true of the expression's type and
`expr_is_place` is true of the expression. In a generic body the type is the
parameter `T`, whose drop-ness is not decided until monomorphisation, so
`type_drops` answers *no* and the guard never fires. The backend then
monomorphises at `string` and emits, for `T:answer = s[i]`, a bitwise

```llvm
%t22 = load { ptr, i64, i64 }, ptr %t21
store { ptr, i64, i64 } %t22, ptr %t10
```

with **no `store zeroinitializer` and no `npk.vacant` on the source slot** —
compare `case5`'s `vec_at<string>`, where `pass s[i]` emits both. Two spellings
of a read, two different lowerings, one of them silent.

**The mechanism was read at the pin and then PRODUCED**, in that order, because
finding the code path that returns early is not finding out what reaches it
(`../../../../../PLAYBOOK.md` §6). `case4` is the producing.

## Why this repository cares

`src/core/vec.npk`'s **`vec_pop<T>` is `case1`'s function**, and it shipped at
cycle 0.0.4. TM-136 records the correction; the row now writes the `move` that
was always the correct spelling, and the file's claim that "at an owning `T` a
copy is refused by TYPE-046" — false at all four pins — is gone.

**And the extent is separate from the existence.** Nine rows of `Vec<T>` at
`T = string`, each measured rather than reasoned about:

| row | body | at an owning `T` |
|---|---|---|
| `vec_init` | allocates a block | correct |
| `vec_reserve` | `into[i] = from[i]` | copies handles, old block freed → one owner. **Correct by accident**, and unenforced: 0 vacate and 0 drop calls in the whole emitted body |
| `vec_push` | `room[count] = move(x)` | correct |
| `vec_at` | `pass s[i]` | **destructive** — `case5`, exit 11 |
| `vec_set` | `s[i] = move(x)` | leaks the outgoing element — known, `SAFETY.md` S-18c |
| `vec_pop` | `T:answer = s[i]` | **duplicate owner** — `case1`/`case4` |
| `vec_truncate`, `vec_clear` | lower `count` | leak — known, S-18b |
| `vec_free` | `dalloc` only | leak — known, S-18b |

Two rows are new here, and both are worse than a leak: one silently removes,
one silently duplicates. The previously known failures were all leaks, which is
why "restricted to a non-owning `T`" had felt like a statement about tidiness.

## What it does to the restriction

> **At cycle 0.1.0b this section's reason closed and the restriction did not
> lift** (TM-150). At `c3bdae2` a `Vec<T>` function that reads an owning element
> without `move` is refused `NITPICK-TYPE-046`, so the compiler DOES police the
> type now. `Vec<T>` stays restricted to a non-owning `T` because four of its
> operations — `vec_set`, `vec_clear`, `vec_truncate`, `vec_free` — owe an
> element drop at an owning `T` and perform none (`../../../../src/core/vec.npk`'s
> header). `vec_reserve`'s row above no longer exists in that form either: it
> relocates with `ralloc`, a bitwise move of the whole block, because D-264
> refused its `into[i] = from[i]`.

**It keeps it, for a stronger reason than the one it had.** TM-132 restricted
`Vec<T>` to a non-owning `T` because O-N17 blocked the element-drop path.
O-N17 has landed. The restriction stands anyway, because the compiler cannot
police the type it would be lifted to: a future `Vec<T>` function that reads an
owning element without `move` compiles, links, runs and exits 0, and **nothing
in this repository or the compiler would say a word.** TM-136 has the argument
and the alternatives declined.
