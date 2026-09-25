# `fixed_array_len` — `.len` on a fixed-size array could not be lowered (O-N18); at compiler `c3bdae2` it can

## Landed — cycle 0.1.0b, compiler `c3bdae2`

**The compiler's DEF-22 fix (its cycle 1.5.2e) is at our pin.**
`case1_local_array_len.npk` compiles, links, runs and exits 0 at `c3bdae2`, and
now carries `// expect-exit: 0` as the fix's regression test; its
`EXPECT_EXEMPT` entry is deleted (TM-154). The control is the same text at the
kept `aaffb87` pin, re-run at 0.1.0b: `npkc` exit 1, no `.ll`,
`NITPICK-EMIT-002` — the verdict the exemption had recorded, and the one
`check_exemptions_live` saw move to `run:0` at the re-pin. **Everything below
is the record as cycle 0.0.4 wrote it, in the tense that was true then**; its
last section's "not yet numbered" was overtaken when the orchestrator issued
O-N18.

**`.len` on a `T[N]` is accepted by the frontend and refused by the emitter**
with `NITPICK-EMIT-002`, whose own text says *"a defect in the compiler rather
than in this program — report it with the construct at this position"*.

Found 2026-09-05 at pin `0dfddac` by cycle 0.0.4, writing `put_uint`'s
allocation-free digit buffer.

## The measurement

Each status beside the artefact it should have produced:

| spelling | `npkc` | `.ll` | code |
|---|---|---|---|
| local `uint8[20]`, `.len` | **1** | **NONE** | `NITPICK-EMIT-002` |
| module `fixed uint8[3]`, `.len` | **1** | **NONE** | `NITPICK-EMIT-002` |
| **slice** `uint8[]`, `.len` | 0 | wrote | — |
| local `uint8[20]`, indexed, no `.len` | 0 | wrote | — |

So it is `.len` **on the array type**, at either storage class, and it is not
indexing and not slices. The two controls are what place it there rather than
at "arrays are broken".

## What it costs this library, which is nearly nothing

`src/core/bytes.npk`'s digit buffer is a `uint8[20]` and never asks its length —
the bound is `NTIME_DIGITS_MAX`, a named constant in `src/core/limits.npk`,
which is what a reader should see anyway. So this is recorded because the
diagnostic asks to be, not because it blocked anything.

## Not yet numbered

The orchestrator assigns open-question ids. This subcycle's predecessor
assigned one itself and collided with a settled question in a sibling
repository, which cost a correction across ten sites in ten files. **Cite this
by path until an id is issued.**
