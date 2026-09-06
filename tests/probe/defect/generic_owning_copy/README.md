# `generic_owning_copy` — TYPE-046 is not enforced inside a generic body

**A GENERIC function may read an owning element into a local WITHOUT `move`,
producing two owners of one heap body. The identical statement with the type
written out is refused.** `npkc` exits **0**, `llc` exits **0**, the program
links and runs, and reading through the second owner after the first has
dropped returns the allocator's `0xAA` poison.

Raised by cycle **0.0.5**, 2026-09-05, at pin `aaffb87` — and **reproduced
unchanged at `0dfddac`, `950bb1d` and `94874ce`**, so it is not a regression at
the new pin. This directory carries no open-question id: `O-N` is the
workbench registry's namespace and a worker cannot see what it has issued
(`../../../../../PLAYBOOK.md`). Cite this directory by path; the orchestrator
numbers it.

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

## The files

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

**It keeps it, for a stronger reason than the one it had.** TM-132 restricted
`Vec<T>` to a non-owning `T` because O-N17 blocked the element-drop path.
O-N17 has landed. The restriction stands anyway, because the compiler cannot
police the type it would be lifted to: a future `Vec<T>` function that reads an
owning element without `move` compiles, links, runs and exits 0, and **nothing
in this repository or the compiler would say a word.** TM-136 has the argument
and the alternatives declined.
