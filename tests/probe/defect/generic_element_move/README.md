# `generic_element_move` — O-N17, **FIXED at pin `aaffb87`**

**A generic function that moves *out of* an indexed element, at an owning `T`,
emitted a call to a `@npk.vacant.<dty>` helper that was never defined.** `npkc`
exited **0** and wrote the `.ll`; `llc` exited **1** and wrote no object.

Raised by cycle **0.0.4**, 2026-09-05, at pin `0dfddac`. **Fixed in the
compiler's 1.5.2d close and verified here by cycle 0.0.5 on 2026-09-05: all
five cases compile, assemble, link and run at exit 0.** `TRANSCRIPT.txt`
PART D has the landing run, appended rather than substituted; PART A is still
`0dfddac`'s record and still true of that toolchain. Both `case1` and `case5`
now carry `// expect-exit: 0` and neither is in `EXPECT_EXEMPT` any more.

> **THE FIX DOES NOT MAKE `Vec<T>` SAFE AT AN OWNING `T`, and cycle 0.0.5 went
> looking.** Two things measured in the same hour stand in the way. The
> library's own spelling of the drop loop — one hoisted `#wild_slice` binding
> and `move(s[i])` inside a loop — is **refused `NITPICK-MOVE-001`**, because
> moving out of an element invalidates the binding the element was reached
> through and the next iteration reads it again (it is refused at `T = int64`
> too, so it is a move-tracker rule and not an ownership one). And a **bare**
> read of an owning element in a generic body is accepted with no diagnostic at
> all, which is a second and worse defect: `../generic_owning_copy/`. TM-136
> keeps the restriction and says why the reason has changed rather than gone.

> **Filed first as `O-N12`, which was already taken** — that is
> `nitpick-regex`'s settled `>>>`/`string_repeat` question in the workbench
> registry, which ran O-N1…O-N16. **The id is `O-N17`**, assigned by the
> orchestrator, corrected across all 10 citations in this repository.
> `TRANSCRIPT.txt`'s header records the correction rather than hiding it.

**It blocked one row of `0.0.4.md` §2's API table — `vec_pop<T>` — and that row
was HELD, not written another way.** *(Superseded twice and both are recorded:
TM-132 measured the extent at **five** rows, and TM-136 found at 0.0.5 that
`vec_pop<T>`'s shipped body was wrong for an unrelated reason — a bare read
where a `move` belonged.)* Returning `NIL`, or restricting it to a
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

Two columns, because the whole point of this directory is that they differ.
`0dfddac` is PART A's record; `aaffb87` is PART D's.

| File | What it is | `0dfddac`: `npkc` / `llc` / run | `aaffb87`: `npkc` / `llc` / run |
|---|---|---|---|
| `case1_generic_move_out.npk` | **the defect** — generic, owning `T`, move out | 0 / **1** / — | 0 / 0 / **0** |
| `case2_concrete_move_out.npk` | control: the same move in a **concrete** function | 0 / 0 / 0 | 0 / 0 / 0 |
| `case3_generic_scalar.npk` | control: the same **generic** function at a scalar `T` | 0 / 0 / 0 | 0 / 0 / 0 |
| `case4_generic_move_in.npk` | control: generic, owning `T`, move **in** | 0 / 0 / 0 | 0 / 0 / 0 |
| `case5_generic_drop_loop.npk` | the **extent** — move out and drop in a loop (TM-132) | 0 / **1** / — | 0 / 0 / **0** |

`TRANSCRIPT.txt` has every command with its exit status **beside the artefact it
should have produced**, the emitted IR at the fault, and the arm-bill
measurement TM-129 rests on.

The three controls place the fault at exactly one combination — **generic**,
**owning**, **move-out** — and no two of them.

## Why `case1` carried no `expect-` marker, and why it carries one now

Because none was spellable. `expect-error:` was false — `npkc` accepted it.
`expect-exit:` was false — it never linked. It was named in `harness/run.py`'s
`EXPECT_EXEMPT` with that reason, which was the only honest bucket the header
sweep had (TM-115, V-1c).

**The sentence that used to be here said the gap would close itself, and it
would not have.** It read: *"the exemption list is diffed in both directions,
so when the defect lands, the exemption fails until somebody removes it."* That
diff checked **only that the named file still existed**. O-N17 landed at
`aaffb87`; `case1` and `case5` went from stopping at `llc` to running clean;
the full suite was **GREEN, 40 units, 0 failures**, with both stale entries in
place, and nothing anywhere said so. Found by cycle 0.0.5 while removing them
by hand. `check_exemptions_live` now records each exemption's **verdict** —
`npkc`, `llc`, `ld`, `run:<code>` or `none` — and re-derives it on every full
run, so the next expiry is a red run rather than a thing somebody notices.
TM-137.

This was the same bucket `missing_failsafe/case1_no_failsafe.npk` was in before
DEF-5 landed, and for the same reason — with one difference worth noting: that
file carried *no* marker and *no* exemption for two days, which is the hole
TM-115 was written about. This one was named from the hour it was committed,
and the hole that remained was in the exemption's own expiry.

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
