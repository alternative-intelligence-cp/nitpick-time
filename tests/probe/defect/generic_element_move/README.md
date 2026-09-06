# `generic_element_move` — O-N17

**A generic function that moves *out of* an indexed element, at an owning `T`,
emits a call to a `@npk.vacant.<dty>` helper that is never defined.** `npkc`
exits **0** and writes the `.ll`; `llc` exits **1** and writes no object.

Raised by cycle **0.0.4**, 2026-09-05, at pin `0dfddac`.

> **Filed first as `O-N12`, which was already taken** — that is
> `nitpick-regex`'s settled `>>>`/`string_repeat` question in the workbench
> registry, which ran O-N1…O-N16. **The id is `O-N17`**, assigned by the
> orchestrator, corrected across all 10 citations in this repository.
> `TRANSCRIPT.txt`'s header records the correction rather than hiding it.

**It blocks one row of `0.0.4.md` §2's API table — `vec_pop<T>` — and that row
is HELD, not written another way.** Returning `NIL`, or restricting it to a
scalar `T` "for symmetry with `vec_at`", would be a workaround buried in
library code that outlives the bug and reads, later, as a design choice nobody
would question. The rest of 0.0.4 was built; see `0.0.4.md` §2's table, where
the row carries its blocked status and the path back to here.

## Where the fault is, more precisely than the error text says

The `llc` diagnostic names one undefined symbol. The **sets** say more, and
they are what makes this actionable:

Re-derived from the retained `.ll` files at pin `0dfddac`, counting **distinct
symbols** and not lines — which matters, because the line counts are equal and
the sets are not:

| | defined | called | called ∖ defined |
|---|---|---|---|
| `case1_generic_move_out` | 5 | **4** | **`1876`** |
| `case2_concrete_move_out` | 5 | 3 | — |
| `case3_generic_scalar` | 5 | 3 | — |
| `case4_generic_move_in` | 5 | 3 | — |

**All four DEFINE the same five** — `3`, `96`, `98`, `1636`, `1737`. The three
controls each **CALL three of those five** (`3`, `98`, `1636`), every callee
among the defined set. `case1` **CALLS four**: the same three, plus `1876`,
which **it never defined**. Written out so it can be checked:

    case1:  5 defined = 3 called-and-defined + 2 defined-never-called (96, 1737)
            4 called  = 3 defined            + 1 UNDEFINED (1876)

`grep -c 'call void @"npk.vacant.'` gives **5** for `case1` and **5** for
`case2`, because one helper is called twice — so the count that first looked
reassuring is the one that hides this. The **paired** `@npk.drop.1876` is
referenced **0** times, while five distinct `npk.drop.*` bodies are defined:
the missing vacancy has no missing drop beside it.

So the definition pass is working: it registers and emits bodies for the types
it walks. The *call site* is synthesising a `dty` that the definition walk never
visits. **That points at the demand walk** — the thing that decides which types
need a vacancy helper — rather than at the emitter that writes them.

The compiler's own invariant (`src/backend/ir/ir_types.npk`,
`drop_type_register`'s header, D-225) is that registration and emission are
paired, and `vacant_fn_sym` registers before returning a symbol. That invariant
holds for every symbol the definition walk reaches; the generic move-out reaches
one it does not.

## The files

| File | What it is | `npkc` | `llc` | run |
|---|---|---|---|---|
| `case1_generic_move_out.npk` | **the defect** — generic, owning `T`, move out | 0 | **1** | — |
| `case2_concrete_move_out.npk` | control: the same move in a **concrete** function | 0 | 0 | 0 |
| `case3_generic_scalar.npk` | control: the same **generic** function at a scalar `T` | 0 | 0 | 0 |
| `case4_generic_move_in.npk` | control: generic, owning `T`, move **in** | 0 | 0 | 0 |

`TRANSCRIPT.txt` has every command with its exit status **beside the artefact it
should have produced**, the emitted IR at the fault, and the arm-bill
measurement TM-129 rests on.

The three controls place the fault at exactly one combination — **generic**,
**owning**, **move-out** — and no two of them.

## Why `case1` carries no `expect-` marker

Because none is spellable. `expect-error:` is false — `npkc` accepts it.
`expect-exit:` is false — it never links. It is named in `harness/run.py`'s
`EXPECT_EXEMPT` with that reason, which is the only honest bucket the header
sweep has (TM-115, V-1c), and the exemption list is diffed in both directions,
so **when the defect lands, the exemption fails until somebody removes it** and
gives the file its `// expect-exit: 0`. The gap closes itself.

This is the same bucket `missing_failsafe/case1_no_failsafe.npk` was in before
DEF-5 landed, and for the same reason — with one difference worth noting: that
file carried *no* marker and *no* exemption for two days, which is the hole
TM-115 was written about. This one is named from the hour it was committed.

## What it does **not** block

`ntime` has no planned `Vec<T>` at an owning `T`. `Layout`'s `Vec<FmtPart>`
(`FORMAT_MODEL.md` §3) is a payload-free enum but for `Literal(uint16)`; the
zone tables hold **offsets into a name pool** precisely so no row owns anything
(`check_no_owning_fields`, `ZONE_MODEL.md`). So the blocked capability is one
row of a table rather than a layer of the library — which is an argument for
raising it, not for routing around it.

## Why it was latent

The prelude's `List<T>` — the shape `BUILD.md` B-12 adopts because it "has been
exercised across twenty-two families" — has exactly **three** public functions
at this pin: `list_init`, `list_reserve`, `list_push`. No `list_pop`, no
`list_at`, no `list_set`, no `list_free`. Every move out of an element in the
compiler's own tree is in a *concrete* function, which is `case2`.

**So "exercised across twenty-two families" is a claim about the half of the
shape those families used.** B-12 is not wrong; it is narrower than it reads,
which is the same failure mode `PLAYBOOK.md` records for D-070's "indexing is
bounds-checked" — a true sentence about the things it names, read as a general
guarantee. Two of this repository's findings now have that shape, and both were
found by writing the unexercised half.
